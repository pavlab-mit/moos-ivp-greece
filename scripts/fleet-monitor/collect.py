#!/usr/bin/env python3
"""
fleet-monitor / collect.py  --  Subsystem A: connectivity collector.

Runs on the shoreside collector Pi (wired into the RB5009 on 10.1.0.0/24).
For each active boat it pings, from shore, a short ladder of addresses and
derives a connectivity state. Writes a JSON snapshot the dashboard reads.

NOTHING runs on the boats for this -- it is pure external probing, so it keeps
answering during boot, before any mission launches, and when all boat software
is dead (which is exactly when you most want it).

Subsystem C (optional) adds RF/mesh quality by polling ONLY the shoreside
DoodleLabs radio's JSON-RPC API for its linkstate -- the shore radio's own
station + mesh tables already list every boat radio it hears (RSSI, MCS,
batman-adv TQ, direct/relay hop), so one HTTP call per poll yields shore->fleet
link quality. Stations are joined to boats by MAC (filled in fleet.json at the
site). It is independent of A and B and degrades quietly if the radio is down.

Addressing is derived from BOAT_ID per
documentation/01_fleet_and_network_reference.md (§4):

    shore uplink (Pi)  10.1.0.<id>     <- "is the boat on the network"
    eth0 gw (Pi)       10.<id>.1.1     <- Pi internal iface (disambiguation)
    backseat (pablo)   10.<id>.1.100   <- "is the backseat up at its IP"
    shore DoodleLabs   10.1.0.3        <- fleet-wide shore-radio rung

Routing note: the RB5009 has static routes to each boat's 10.<id>.1.0/24, so
all three per-boat rungs above are reachable from shore. It does NOT route the
radio-mgmt /30 (10.<id>.3.0/30), so the boat-radio rung is intentionally left
out -- reaching 10.1.0.<id> already implies the radio/mesh path is healthy.

State machine (per boat):
    offline         shore uplink (10.1.0.N) unreachable -> boat off / link down
    frontseat_only  uplink up, backseat (10.N.1.100) down -> pablo down/unplugged
    present         uplink up and backseat up -> fully reachable; hand off to B

Usage:
    ./collect.py                       # loop using ./fleet.json
    ./collect.py --once                # single sweep, print, exit
    ./collect.py --config /path/fleet.json --snapshot /run/fleetmon/status.json
    ./collect.py --quiet               # no per-cycle table (snapshot only)
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Address derivation -- single source of truth is BOAT_ID (see module docstring)
# ---------------------------------------------------------------------------

def uplink_ip(n: int) -> str:    return f"10.1.0.{n}"     # boat's shore presence
def frontseat_ip(n: int) -> str: return f"10.{n}.1.1"     # Pi eth0 gateway
def backseat_ip(n: int) -> str:  return f"10.{n}.1.100"   # pablo

# Per-boat ladder, shallow -> deep. Each entry: (rung_key, ip_fn).
# 'uplink' and 'backseat' drive the state machine; 'frontseat' only
# disambiguates "Pi forwarding plane down" from "backseat host down".
BOAT_LADDER = [
    ("uplink",    uplink_ip),
    ("frontseat", frontseat_ip),
    ("backseat",  backseat_ip),
]


def resolve_rungs(b: dict) -> dict:
    """Map each ladder rung to a concrete IP for one boat config entry.

    Normal boats carry an 'id' and every rung is derived from the address plan
    (see module docstring). A boat that doesn't fit the mold -- static lease,
    different subnet, a backseat reached over some other path -- can instead pin
    any rung by naming it directly in the config, e.g.

        { "name": "weird", "active": true,
          "uplink": "10.1.0.40", "frontseat": "192.168.5.1", "backseat": "192.168.5.100" }

    An explicit rung key always wins over the formula, so 'id' and overrides can
    be mixed (pin just the backseat, derive the rest). A boat with no 'id' must
    pin every rung it needs.
    """
    n = b.get("id")
    rungs = {}
    for rung, ip_fn in BOAT_LADDER:
        if b.get(rung):                       # explicit override for this rung
            rungs[rung] = str(b[rung])
        elif n is not None:
            rungs[rung] = ip_fn(int(n))
        else:
            raise ValueError(
                f"boat {b.get('name', '?')!r}: no 'id' and no explicit "
                f"'{rung}' address to fall back on")
    return rungs


RTT_RE = re.compile(r"time[=<]\s*([\d.]+)\s*ms")


# ---------------------------------------------------------------------------
# Probe history -- rolling window per target for loss% and average RTT
# ---------------------------------------------------------------------------

@dataclass
class TargetHistory:
    window: int
    results: deque = field(default_factory=deque)   # bools: alive?
    rtts: deque = field(default_factory=deque)       # floats: successful RTTs

    def record(self, alive: bool, rtt_ms):
        if len(self.results) >= self.window:
            self.results.popleft()
        self.results.append(alive)
        if rtt_ms is not None:
            if len(self.rtts) >= self.window:
                self.rtts.popleft()
            self.rtts.append(rtt_ms)

    @property
    def loss_pct(self) -> float:
        if not self.results:
            return 0.0
        misses = sum(1 for r in self.results if not r)
        return round(100.0 * misses / len(self.results), 1)

    @property
    def avg_rtt_ms(self):
        return round(sum(self.rtts) / len(self.rtts), 1) if self.rtts else None


# ---------------------------------------------------------------------------
# Pinger -- one ICMP echo via the system `ping` (setuid; no root, no pip deps)
# ---------------------------------------------------------------------------

# The deadline flag differs by platform: Linux iputils uses -w <seconds>
# (total deadline), BSD ping on macOS uses -t <seconds>. The collector runs on
# the Linux shore Pi in production; the macOS arm only matters for local dev.
_PING_DEADLINE_FLAG = "-t" if sys.platform == "darwin" else "-w"

async def ping_once(ip: str, timeout_s: float):
    """Return (alive: bool, rtt_ms: float | None)."""
    deadline = max(1, int(timeout_s + 0.999))  # flag wants whole seconds
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping", "-n", "-c", "1", _PING_DEADLINE_FLAG, str(deadline), ip,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print("ERROR: `ping` not found on PATH", file=sys.stderr)
        return (False, None)

    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_s + 1.0)
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        return (False, None)

    if proc.returncode != 0:
        return (False, None)
    m = RTT_RE.search(out.decode(errors="replace"))
    return (True, float(m.group(1)) if m else None)


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------

class Collector:
    def __init__(self, cfg: dict):
        self.shore_radio_ip = cfg.get("shore_radio_ip", "10.1.0.3")
        self.interval = float(cfg.get("ping_interval_s", 2.0))
        self.timeout = float(cfg.get("ping_timeout_s", 1.0))
        self.window = int(cfg.get("history_window", 30))
        self.snapshot_path = cfg.get("snapshot_path", "fleet_status.json")
        self.boats = [b for b in cfg.get("boats", []) if b.get("active", True)]
        # Resolve each boat's rung IPs once: derived from BOAT_ID, or pinned
        # explicitly for boats that don't fit the address plan (see resolve_rungs).
        for b in self.boats:
            b["rung_ips"] = resolve_rungs(b)
        self._hist = {}  # ip -> TargetHistory
        self._last_present = {}  # boat name -> ts

        # --- Subsystem B: telemetry receiver (pBB_Status UDP push) ---
        self.telemetry_port = int(cfg.get("telemetry_port", 9300))
        self.telemetry_stale_s = float(cfg.get("telemetry_stale_s", 5.0))
        # Reverse map: a boat's shore uplink IP is the source address of its
        # BB_STATUS datagrams, so the source IP alone identifies the boat.
        self._by_uplink = {b["rung_ips"]["uplink"]: b for b in self.boats}
        self._telemetry = {}  # boat name -> {ts, src_ip, fields, raw, matched}

        # --- Subsystem C: RF/mesh quality from the shore DoodleLabs radio ---
        # We poll ONLY the shore radio's JSON-RPC API and read its linkstate;
        # the shore radio's station + mesh tables already list every boat radio
        # it hears, so one HTTP call per poll yields shore->fleet RF quality.
        # Each station is joined back to a boat by MAC (filled in fleet.json at
        # the site). Stdlib only -- no `requests`, no `pip` (see README §2).
        rc = cfg.get("radio", {}) or {}
        self.radio_enabled = bool(rc.get("enabled", False))
        self.radio_api_ip = rc.get("api_ip", self.shore_radio_ip)
        self.radio_user = rc.get("username", "user")
        self.radio_pass = rc.get("password", "DoodleSmartRadio")
        self.radio_interval = float(rc.get("poll_interval_s", 2.0))
        self.radio_timeout = float(rc.get("timeout_s", 4.0))
        self.radio_stale_s = float(rc.get("stale_s", 6.0))
        # name -> mac, only for boats whose MAC is actually filled in. A blank
        # entry is simply absent here, so the boat reads "no RF data" and its
        # station (if heard) surfaces as unmapped until the MAC is supplied.
        self.mac_by_name = {n: m.lower() for n, m in (rc.get("macs") or {}).items() if m}
        self._radio_token = None         # cached ubus session id (re-login on loss)
        self._radio_stations = {}        # mac -> merged station/mesh record
        self._radio_summary = {}         # shore-radio's own sysinfo/noise/channel
        self._radio_ts = None            # epoch of last good poll
        self._radio_ok = False           # did the last poll reach + parse the radio

    def _hist_for(self, ip: str) -> TargetHistory:
        if ip not in self._hist:
            self._hist[ip] = TargetHistory(self.window)
        return self._hist[ip]

    async def _probe(self, ip: str) -> dict:
        alive, rtt = await ping_once(ip, self.timeout)
        h = self._hist_for(ip)
        h.record(alive, rtt)
        return {"ip": ip, "alive": alive, "rtt_ms": rtt,
                "avg_rtt_ms": h.avg_rtt_ms, "loss_pct": h.loss_pct}

    def store_telemetry(self, src_ip: str, raw: str):
        """Record a BB_STATUS datagram. Called by the UDP protocol on receipt.

        Attribution is by source IP (the boat's shore uplink, 10.1.0.<id>);
        if the sender isn't a known uplink we fall back to the payload's own
        vname field so a misaddressed boat still shows up rather than vanishing.
        """
        fields = {}
        for tok in raw.strip().split(","):
            if "=" in tok:
                k, v = tok.split("=", 1)
                fields[k.strip()] = v.strip()
        boat = self._by_uplink.get(src_ip)
        name = boat["name"] if boat else fields.get("vname", "unknown")
        self._telemetry[name] = {
            "received_ts": time.time(),
            "src_ip": src_ip,
            "matched": boat is not None,
            "fields": fields,
            "raw": raw.strip(),
        }

    def _telemetry_for(self, name: str, now: float):
        """Latest telemetry for a boat, annotated with age/freshness, or None."""
        t = self._telemetry.get(name)
        if t is None:
            return None
        age = round(now - t["received_ts"], 1)
        return {
            "received_ts": t["received_ts"],
            "received_iso": _iso(t["received_ts"]),
            "age_s": age,
            "fresh": age < self.telemetry_stale_s,
            "src_ip": t["src_ip"],
            "matched": t["matched"],
            "fields": t["fields"],
            "raw": t["raw"],
        }

    # -----------------------------------------------------------------------
    # Subsystem C: shore-radio linkstate poller (JSON-RPC over ubus)
    # -----------------------------------------------------------------------

    def _radio_poll_blocking(self):
        """One JSON-RPC round-trip to the shore radio: log in if needed, then
        read /tmp/linkstate_current.json. Returns the parsed linkstate dict, or
        None on any failure (and drops the cached token so we re-login next
        time). Pure stdlib (urllib + ssl) to honor the no-`pip` rule; the radio
        serves a self-signed cert, so certificate verification is disabled --
        the link is encrypted but the radio is trusted by network position."""
        import urllib.request
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        url = f"https://{self.radio_api_ip}/ubus"

        def rpc(params):
            body = json.dumps({"jsonrpc": "2.0", "id": 1,
                               "method": "call", "params": params}).encode()
            req = urllib.request.Request(
                url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.radio_timeout, context=ctx) as r:
                return json.loads(r.read().decode())

        try:
            if not self._radio_token:
                login = rpc(["0" * 32, "session", "login",
                             {"username": self.radio_user, "password": self.radio_pass}])
                self._radio_token = login["result"][1]["ubus_rpc_session"]

            resp = rpc([self._radio_token, "file", "read",
                        {"path": "/tmp/linkstate_current.json", "base64": 0}])
            code = resp.get("result", [99])[0]
            if code != 0:                      # 6=perm denied / session expired etc.
                self._radio_token = None       # force a fresh login next poll
                return None
            return json.loads(resp["result"][1]["data"])
        except Exception:
            self._radio_token = None
            return None

    @staticmethod
    def _to_float(v):
        try:
            return round(float(v), 1)
        except (TypeError, ValueError):
            return None

    def _parse_linkstate(self, ls: dict):
        """Split a linkstate blob into (per-mac station records, shore summary).

        Stations come from two arrays keyed by the same MAC: `sta_stats` (PHY:
        rssi, per-antenna rssi, mcs, packet-loss ratio, tx retries/failures) and
        `mesh_stats` (batman-adv: tq 0-255, direct/relay hop, last-seen). We
        merge them by MAC into one record per neighbor."""
        stations = {}
        for s in ls.get("sta_stats", []) or []:
            mac = str(s.get("mac", "")).lower()
            if not mac:
                continue
            pl = s.get("pl_ratio")
            stations[mac] = {
                "mac": mac,
                "rssi": s.get("rssi"),
                "rssi_ant": s.get("rssi_ant"),
                "mcs": s.get("mcs"),
                "pl_ratio": round(pl, 4) if isinstance(pl, (int, float)) else None,
                "tx_retries": s.get("tx_retries"),
                "tx_failed": s.get("tx_failed"),
                "inactive": s.get("inactive"),
            }
        for m in ls.get("mesh_stats", []) or []:
            mac = str(m.get("orig_address", "")).lower()
            if not mac:
                continue
            rec = stations.setdefault(mac, {"mac": mac})
            rec["tq"] = m.get("tq")
            rec["hop_status"] = m.get("hop_status")
            rec["last_seen_msecs"] = m.get("last_seen_msecs")

        si = ls.get("sysinfo", {}) or {}
        cpu = si.get("cpu_load")
        # OpenWrt reports load average in 1<<16 fixed point; scale to a float.
        load = ([round(x / 65536.0, 2) for x in cpu]
                if isinstance(cpu, list) else None)
        summary = {
            "oper_chan": ls.get("oper_chan"),
            "oper_freq": ls.get("oper_freq"),
            "chan_width": ls.get("chan_width"),
            "noise": self._to_float(ls.get("noise")),
            "activity": ls.get("activity"),
            "lna_status": ls.get("lna_status"),
            "cpu_load": load,
            "freemem": si.get("freemem"),
        }
        return stations, summary

    async def _do_radio_poll(self):
        """Run one (blocking) radio poll in a thread and stash the result."""
        loop = asyncio.get_event_loop()
        ls = await loop.run_in_executor(None, self._radio_poll_blocking)
        if ls is None:
            self._radio_ok = False
            return
        self._radio_stations, self._radio_summary = self._parse_linkstate(ls)
        self._radio_ts = time.time()
        self._radio_ok = True

    async def _radio_loop(self):
        """Poll the shore radio on its own cadence, independent of the ping
        sweep. A dead/unreachable radio just leaves the last data going stale --
        it never disturbs Subsystems A or B."""
        while True:
            t0 = time.time()
            try:
                await self._do_radio_poll()
            except Exception as e:
                self._radio_ok = False
                print(f"[{_iso(time.time())}] radio poll error: {e}", file=sys.stderr)
            await asyncio.sleep(max(0.5, self.radio_interval - (time.time() - t0)))

    def _radio_block(self, now: float):
        """Assemble the snapshot's top-level `radio` object and a name->record
        map for the per-boat merge. Returns ({}, {}) cheaply when disabled."""
        if not self.radio_enabled:
            return {"enabled": False}, {}

        age = round(now - self._radio_ts, 1) if self._radio_ts else None
        ok = self._radio_ok and self._radio_ts is not None
        fresh = bool(ok and age is not None and age < self.radio_stale_s)
        stations = self._radio_stations or {}

        # Join each filled-in MAC to its boat; collect the leftovers.
        per_boat, claimed = {}, set()
        for name, mac in self.mac_by_name.items():
            rec = stations.get(mac)
            if rec:
                claimed.add(mac)
                per_boat[name] = {**rec, "heard": True}
            else:
                per_boat[name] = None          # mapped, but not heard right now
        unmapped = [rec for mac, rec in stations.items() if mac not in claimed]

        block = {
            "enabled": True,
            "ok": ok,
            "fresh": fresh,
            "api_ip": self.radio_api_ip,
            "polled_ts": self._radio_ts,
            "polled_iso": _iso(self._radio_ts),
            "age_s": age,
            "station_count": len(stations),
            "mapped_count": sum(1 for v in per_boat.values() if v),
            "unmapped": unmapped,
        }
        block.update(self._radio_summary or {})
        return block, per_boat

    async def sweep(self) -> dict:
        # Build the full probe set (shore radio + every rung of every boat) and
        # fire them all concurrently -- one cycle is ~1 + 3*len(boats) pings.
        jobs = {("shore", "shore_radio"): self._probe(self.shore_radio_ip)}
        for b in self.boats:
            for rung, ip in b["rung_ips"].items():
                jobs[(b["name"], rung)] = self._probe(ip)

        results = await asyncio.gather(*jobs.values())
        keyed = dict(zip(jobs.keys(), results))

        now = time.time()
        shore = keyed[("shore", "shore_radio")]
        shore_up = shore["alive"]
        radio_block, radio_by_boat = self._radio_block(now)

        boats_out = []
        for b in self.boats:
            name = b["name"]
            rungs = {rung: keyed[(name, rung)] for rung, _ in BOAT_LADDER}

            up = rungs["uplink"]["alive"]
            fs = rungs["frontseat"]["alive"]
            bs = rungs["backseat"]["alive"]

            if not up:
                state = "offline"
                # If the shared shore radio is down, the break is shore-side,
                # not this boat -- flag it so the whole fleet isn't misread.
                fault = "shore_radio" if not shore_up else "uplink"
            elif not bs:
                state = "frontseat_only"
                # uplink up but backseat unreachable: if the Pi's own internal
                # iface is also down, the forwarding plane is the suspect;
                # otherwise the backseat host itself is down.
                fault = "frontseat" if not fs else "backseat"
            else:
                state = "present"
                fault = None
                self._last_present[name] = now

            boats_out.append({
                "name": name,
                "id": b.get("id"),
                "state": state,
                "fault_at": fault,
                "rungs": rungs,
                "last_present_ts": self._last_present.get(name),
                "last_present_iso": _iso(self._last_present.get(name)),
                "telemetry": self._telemetry_for(name, now),  # Subsystem B, or None
                "radio": radio_by_boat.get(name),             # Subsystem C, or None
            })

        return {
            "ts": now,
            "iso": _iso(now),
            "shore_radio": shore,
            "shore_ok": shore_up,
            "telemetry_port": self.telemetry_port,
            "telemetry_count": sum(
                1 for b in boats_out
                if b["telemetry"] and b["telemetry"]["fresh"]),
            "radio": radio_block,                             # Subsystem C summary
            "boats": boats_out,
        }

    def write_snapshot(self, snap: dict):
        path = self.snapshot_path
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        tmp = f"{path}.tmp.{os.getpid()}"
        with open(tmp, "w") as f:
            json.dump(snap, f, indent=2)
        os.replace(tmp, path)  # atomic: dashboard never sees a half-written file

    async def start_receiver(self):
        """Bind the UDP telemetry port. Failure is non-fatal -- A keeps running
        without B rather than taking the whole collector down."""
        loop = asyncio.get_event_loop()
        try:
            await loop.create_datagram_endpoint(
                lambda: BTelemetryProtocol(self),
                local_addr=("0.0.0.0", self.telemetry_port))
            return True
        except OSError as e:
            print(f"[{_iso(time.time())}] telemetry port {self.telemetry_port} "
                  f"unavailable ({e}); running A-only", file=sys.stderr)
            return False

    async def run(self, once: bool, quiet: bool):
        await self.start_receiver()  # B listener runs for the process lifetime
        if self.radio_enabled:
            # Prime once so the very first sweep (and --once) already carries RF
            # data; then let it refresh on its own task for the continuous loop.
            await self._do_radio_poll()
            if not once:
                asyncio.ensure_future(self._radio_loop())
        while True:
            t0 = time.time()
            try:
                snap = await self.sweep()
                self.write_snapshot(snap)
                if not quiet:
                    print(_render_table(snap))
            except Exception as e:  # never let one bad cycle kill the daemon
                print(f"[{_iso(time.time())}] sweep error: {e}", file=sys.stderr)
            if once:
                return
            await asyncio.sleep(max(0.0, self.interval - (time.time() - t0)))


# ---------------------------------------------------------------------------
# Subsystem B: telemetry receiver (pBB_Status pushes BB_STATUS via UDP)
# ---------------------------------------------------------------------------

class BTelemetryProtocol(asyncio.DatagramProtocol):
    def __init__(self, collector: "Collector"):
        self._collector = collector

    def datagram_received(self, data: bytes, addr):
        try:
            line = data.decode("utf-8", errors="replace")
            self._collector.store_telemetry(addr[0], line)
        except Exception as e:  # a malformed packet must never crash the loop
            print(f"[{_iso(time.time())}] bad telemetry from {addr}: {e}",
                  file=sys.stderr)


# ---------------------------------------------------------------------------
# Presentation helpers
# ---------------------------------------------------------------------------

def _iso(ts):
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, timezone.utc).astimezone().strftime("%H:%M:%S")


_GLYPH = {"present": "OK ", "frontseat_only": "FS ", "offline": "-- "}

def _render_table(snap: dict) -> str:
    lines = []
    shore = "up" if snap["shore_ok"] else "DOWN"
    sr = snap["shore_radio"]
    srtt = f'{sr["rtt_ms"]}ms' if sr["rtt_ms"] is not None else "--"
    radio = snap.get("radio") or {}
    radio_note = ""
    if radio.get("enabled"):
        if radio.get("ok"):
            rn = radio.get("noise")
            radio_note = (f'  radio {"fresh" if radio.get("fresh") else "STALE"}'
                          f' (noise {rn}dBm, {radio.get("station_count",0)} sta)')
        else:
            radio_note = "  radio UNREACHABLE"
    lines.append(f'[{snap["iso"]}] shore radio {shore} ({srtt})  '
                 f'{sum(1 for b in snap["boats"] if b["state"]=="present")}/'
                 f'{len(snap["boats"])} present{radio_note}')
    lines.append(f'  {"boat":6} {"state":15} {"fault":10} '
                 f'{"uplink":>10} {"backseat":>10}  {"rf":>14}  telemetry')
    for b in snap["boats"]:
        up = b["rungs"]["uplink"]
        bs = b["rungs"]["backseat"]
        up_s = f'{up["rtt_ms"]}ms' if up["rtt_ms"] is not None else "--"
        if up["loss_pct"]:
            up_s += f'/{up["loss_pct"]}%L'
        bs_s = f'{bs["rtt_ms"]}ms' if bs["rtt_ms"] is not None else "--"
        lines.append(f'  {_GLYPH.get(b["state"],"?")}{b["name"]:5} '
                     f'{b["state"]:15} {str(b["fault_at"] or ""):10} '
                     f'{up_s:>10} {bs_s:>10}  {_radio_cell(b.get("radio")):>14}  '
                     f'{_telemetry_cell(b["telemetry"])}')
    return "\n".join(lines)


def _radio_cell(r) -> str:
    """Compact C summary for the live table: RSSI + batman TQ, or a dash."""
    if not r:
        return "-"
    rssi = r.get("rssi")
    tq = r.get("tq")
    parts = []
    if rssi is not None:
        parts.append(f'{rssi}dBm')
    if tq is not None:
        parts.append(f'tq{tq}')
    return " ".join(parts) if parts else "heard"


def _telemetry_cell(t) -> str:
    """Compact B summary for the live table: mode + battery, or staleness."""
    if t is None:
        return "-"
    f = t["fields"]
    summ = f'{f.get("mode","?")} {f.get("volt","?")}V'
    if f.get("mission") == "true":
        summ += " MISSION"
    if not t["fresh"]:
        summ = f'(stale {t["age_s"]}s) ' + summ
    return summ


def load_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description="Shoreside connectivity collector (Subsystem A)")
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--config", default=os.path.join(here, "fleet.json"))
    ap.add_argument("--snapshot", default=None, help="override snapshot_path from config")
    ap.add_argument("--interval", type=float, default=None, help="override ping_interval_s")
    ap.add_argument("--once", action="store_true", help="single sweep then exit")
    ap.add_argument("--quiet", action="store_true", help="suppress per-cycle table")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.snapshot:
        cfg["snapshot_path"] = args.snapshot
    if args.interval is not None:
        cfg["ping_interval_s"] = args.interval

    try:
        c = Collector(cfg)
    except ValueError as e:
        print(f"config error: {e}", file=sys.stderr)
        sys.exit(1)
    if not c.boats:
        print("No active boats in config; nothing to probe.", file=sys.stderr)
        sys.exit(1)
    try:
        asyncio.run(c.run(once=args.once, quiet=args.quiet))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
