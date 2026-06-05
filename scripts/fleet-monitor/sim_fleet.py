#!/usr/bin/env python3
"""
sim_fleet.py  --  Fleet simulator for dashboard development.

Produces the SAME fleet_status.json the real collector (collect.py) writes, so a
dashboard built against this simulator works unchanged against a live boat
network. No boats, no mesh, no sudo required.

Two ways to use it:

  1. Snapshot mode (default): writes fleet_status.json directly, with boats
     evolving over time -- states flip, batteries drain, modes change, telemetry
     goes stale. Point the dashboard at the file.

         ./sim_fleet.py                 # dynamic, evolving fleet
         ./sim_fleet.py --static        # fixed tableau (one of each case)
         ./sim_fleet.py --once          # write one snapshot and exit

  2. UDP mode: also emit real BB_STATUS datagrams to a running collect.py, to
     exercise the actual Subsystem-B receiver end to end.

         ./sim_fleet.py --udp 127.0.0.1:9300

The BB_STATUS line is byte-compatible with what the front-seat pBB_Status app
sends, and the snapshot schema mirrors collect.py exactly (verified in tests).
"""

import argparse
import json
import os
import random
import socket
import sys
import time
from datetime import datetime, timezone

# Addressing (identical formula to collect.py / the fleet reference doc).
def uplink_ip(n):    return f"10.1.0.{n}"
def frontseat_ip(n): return f"10.{n}.1.1"
def backseat_ip(n):  return f"10.{n}.1.100"

SHORE_RADIO_IP = "10.1.0.3"
LOW_VOLT = 22.0
MODES = ["AUTO", "HOLD", "MANUAL", "NO_HELM", "ALLSTOP"]
RADIO_STALE_S = 6.0


def _synth_mac(bid):
    """Deterministic fake boat-radio MAC, used when fleet.json has no real MAC
    filled in yet -- lets the dashboard's Radio tab populate during dev."""
    return f"02:00:00:00:{bid & 0xff:02x}:01"


def _iso(ts):
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, timezone.utc).astimezone().strftime("%H:%M:%S")


# ---------------------------------------------------------------------------
# Per-boat simulated state
# ---------------------------------------------------------------------------

class SimBoat:
    def __init__(self, bid, name, rng):
        self.id = bid
        self.name = name
        self.rng = rng
        # connectivity
        self.link_up = True
        self.backseat_up = True
        self.fwd_ok = True            # Pi forwarding plane (frontseat rung)
        self.rtt = rng.uniform(28, 75)
        self.loss = 0.0
        # telemetry / autonomy
        self.tele_on = True           # pBB_Status running on the front seat
        self.tele_age = 0.0           # seconds since last "sent" frame
        self.mode = rng.choice(["AUTO", "HOLD", "NO_HELM"])
        self.volt = rng.uniform(24.4, 25.2)
        self.int_t = rng.uniform(30, 38)
        self.int_kpa = rng.uniform(99.5, 101.0)
        self.lat = 37.4360 + rng.uniform(-0.002, 0.002)   # Greece-ish
        self.lon = 24.9460 + rng.uniform(-0.002, 0.002)
        # RF / mesh (Subsystem C) -- shore radio's view of this boat's radio
        self.mac = None               # filled by main(): real map or synthesized
        self.rssi = rng.uniform(-58, -47)
        self.mcs = rng.randint(11, 15)
        self.tq = rng.randint(210, 255)
        self.hop = "direct"
        self.pl_ratio = rng.uniform(0.0, 0.06)
        self.tx_retries = rng.randint(0, 4)
        self.tx_failed = 0
        self.inactive = rng.randint(0, 120)

    # -- dynamic evolution -------------------------------------------------
    def step(self, dt):
        r = self.rng.random
        # connectivity random walk
        if self.link_up and r() < 0.01:
            self.link_up = False
        elif not self.link_up and r() < 0.20:        # recover faster than drop
            self.link_up = True
        if self.link_up:
            if r() < 0.015:
                self.backseat_up = not self.backseat_up
            if r() < 0.005:
                self.fwd_ok = not self.fwd_ok
            else:
                self.fwd_ok = True
        # link quality jitter
        self.rtt = max(8.0, self.rtt + self.rng.uniform(-6, 6))
        self.loss = round(max(0.0, min(40.0, self.loss + self.rng.uniform(-3, 3))), 1)
        # battery slowly drains while "running"
        self.volt = max(20.5, self.volt - 0.02 * dt - self.rng.uniform(0, 0.01))
        # enclosure wander
        self.int_t = min(60, max(25, self.int_t + self.rng.uniform(-0.4, 0.5)))
        self.int_kpa += self.rng.uniform(-0.05, 0.05)
        # autonomy mode transitions
        if r() < 0.03:
            self.mode = self.rng.choice(MODES)
        # telemetry hiccup: occasionally goes stale while still pingable
        if self.tele_on and r() < 0.01:
            self.tele_age = 8.0       # force a stale window
        else:
            self.tele_age = self.tele_age + dt if self.tele_age > dt else 0.0
        if r() < 0.008:
            self.tele_on = not self.tele_on
        # RF random walk; MCS / TQ / loss all track signal strength (q: 0..1).
        self.rssi = max(-92.0, min(-40.0, self.rssi + self.rng.uniform(-2.5, 2.5)))
        q = (self.rssi + 90.0) / 50.0
        self.mcs = max(0, min(15, int(round(q * 15 + self.rng.uniform(-1.5, 1.5)))))
        self.tq = max(0, min(255, int(round(q * 255 + self.rng.uniform(-25, 25)))))
        self.pl_ratio = max(0.0, min(0.9, (1 - q) * 0.4 + self.rng.uniform(-0.05, 0.05)))
        self.tx_retries = self.rng.randint(0, int((1 - q) * 40) + 1)
        self.tx_failed = self.rng.randint(0, int((1 - q) * 8))
        self.inactive = self.rng.randint(0, 60)
        # weak links sometimes route through another boat (multi-hop)
        self.hop = "relay" if (q < 0.4 and r() < 0.5) else "direct"

    def radio_record(self):
        """Shore radio's station+mesh record for this boat, or None when the
        boat's link is down (the shore radio simply doesn't hear it)."""
        if not self.link_up:
            return None
        rssi = round(self.rssi)
        return {
            "mac": self.mac,
            "rssi": rssi,
            "rssi_ant": [rssi - self.rng.randint(0, 4), rssi - self.rng.randint(0, 4)],
            "mcs": int(self.mcs),
            "pl_ratio": round(self.pl_ratio, 4),
            "tx_retries": int(self.tx_retries),
            "tx_failed": int(self.tx_failed),
            "inactive": int(self.inactive),
            "tq": int(self.tq),
            "hop_status": self.hop,
            "last_seen_msecs": self.rng.randint(0, 800),
            "heard": True,
        }

    # -- derived autonomy fields from mode --------------------------------
    def _autonomy(self):
        mode = self.mode
        helm, deploy, mission, allstop, failsafe = "NONE", "false", "false", "false", "false"
        rc, des = "conn", 0
        if mode == "AUTO":
            helm, deploy, mission = "DRIVE", "true", "true"
            des = int(self.rng.uniform(20, 60))
        elif mode == "HOLD":
            helm, deploy = "PARK", "true"
        elif mode == "MANUAL":
            # pilot override: front seat ignores helm. Model the helm still in
            # DRIVE so the dashboard sees the (useful) mode/helm disagreement.
            helm, deploy, mission = "DRIVE", "true", "true"
            des = int(self.rng.uniform(20, 80))
        elif mode == "ALLSTOP":
            helm, allstop = "DRIVE", "true"
        elif mode == "NO_HELM":
            helm = "NONE"
        return helm, deploy, mission, allstop, failsafe, rc, des

    def status_line(self):
        helm, deploy, mission, allstop, failsafe, rc, des = self._autonomy()
        applied = des if self.mode in ("AUTO", "MANUAL") else 0
        batt = "LOW" if self.volt < LOW_VOLT else "OK"
        f = [
            f"vname={self.name}", f"utc={time.time():.2f}",
            f"mode={self.mode}", f"mission={mission}",
            f"helm={helm}", f"deploy={deploy}",
            f"volt={self.volt:.1f}", f"curr={self.rng.uniform(2,8):.1f}",
            f"power={self.volt*self.rng.uniform(2,8):.0f}", f"batt={batt}",
            f"rc={rc}", f"failsafe={failsafe}",
            f"deadman={'true' if self.mode=='MANUAL' else 'false'}",
            f"des_l={des}", f"des_r={des}", f"thr_l={applied}", f"thr_r={applied}",
            f"allstop={allstop}",
            f"rpi_t={self.int_t-5:.1f}", f"int_t={self.int_t:.1f}",
            f"int_kpa={self.int_kpa:.2f}",
            "fix=RTK_FIX", f"sats={int(self.rng.uniform(18,28))}",
            f"hdop={self.rng.uniform(0.6,1.2):.2f}",
            f"lat={self.lat:.7f}", f"lon={self.lon:.7f}",
            f"spd={self.rng.uniform(0,2.2):.2f}", f"hdg={self.rng.uniform(0,359):.1f}",
            "stale=none",
        ]
        return ",".join(f)


# ---------------------------------------------------------------------------
# Simulated shore radio (Subsystem C source)
# ---------------------------------------------------------------------------

class SimShoreRadio:
    """The shoreside DoodleLabs radio's own state: noise floor, channel
    activity, and a little system load. `ok` flips occasionally to exercise the
    'radio API unreachable / stale' path in the dashboard."""
    def __init__(self, rng):
        self.rng = rng
        self.noise = rng.uniform(-99, -94)
        self.activity = 0
        self.cpu = [0.12, 0.10, 0.09]
        self.freemem = 14_700_000
        self.ok = True

    def step(self, dt):
        self.noise = max(-103.0, min(-80.0, self.noise + self.rng.uniform(-1.5, 1.5)))
        self.activity = 1 if self.rng.random() < 0.5 else 0
        self.cpu = [round(max(0.02, c + self.rng.uniform(-0.05, 0.05)), 2) for c in self.cpu]
        self.freemem = int(max(10_000_000, min(16_000_000,
                          self.freemem + self.rng.uniform(-200_000, 200_000))))
        if self.ok and self.rng.random() < 0.003:        # rare API blip
            self.ok = False
        elif not self.ok and self.rng.random() < 0.5:
            self.ok = True


# ---------------------------------------------------------------------------
# Snapshot assembly (must match collect.py's schema exactly)
# ---------------------------------------------------------------------------

def _rung(ip, alive, rtt, loss):
    return {"ip": ip, "alive": alive,
            "rtt_ms": round(rtt, 1) if alive else None,
            "avg_rtt_ms": round(rtt, 1) if alive else None,
            "loss_pct": loss if alive else 0.0}


def _radio_block(boats, shore_radio, radio_enabled, mapped_names, now):
    """Mirror collect.py's Collector._radio_block output: a top-level radio
    summary plus a name->record map. Boats whose name is in `mapped_names` are
    attributed to a boat; any others the radio hears land in `unmapped`."""
    if not radio_enabled:
        return {"enabled": False}, {}

    ok = shore_radio.ok
    polled = now - (0.4 if ok else 7.5)        # not ok -> data goes stale
    age = round(now - polled, 1)
    per_boat, unmapped, station_count = {}, [], 0
    for b in boats:
        rec = b.radio_record()
        if rec:
            station_count += 1
        if b.name in mapped_names:
            per_boat[b.name] = rec
        elif rec:
            unmapped.append(rec)

    block = {
        "enabled": True,
        "ok": ok,
        "fresh": bool(ok and age < RADIO_STALE_S),
        "api_ip": SHORE_RADIO_IP,
        "polled_ts": polled,
        "polled_iso": _iso(polled),
        "age_s": age,
        "station_count": station_count,
        "mapped_count": sum(1 for v in per_boat.values() if v),
        "unmapped": unmapped,
        "oper_chan": 13,
        "oper_freq": 2472,
        "chan_width": "20",
        "noise": round(shore_radio.noise, 1),
        "activity": shore_radio.activity,
        "lna_status": "1",
        "cpu_load": shore_radio.cpu,
        "freemem": shore_radio.freemem,
    }
    return block, per_boat


def build_snapshot(boats, shore_ok, tele_port, tele_stale_s, last_present,
                   shore_radio=None, radio_enabled=False, mapped_names=frozenset()):
    now = time.time()
    radio_block, radio_by_boat = _radio_block(
        boats, shore_radio, radio_enabled, mapped_names, now)
    boats_out = []
    for b in boats:
        up, fs, bs = b.link_up, (b.link_up and b.fwd_ok), b.backseat_up and b.link_up
        if not up:
            state = "offline"
            fault = "shore_radio" if not shore_ok else "uplink"
        elif not bs:
            state = "frontseat_only"
            fault = "frontseat" if not fs else "backseat"
        else:
            state = "present"
            fault = None
            last_present[b.name] = now

        rungs = {
            "uplink":    _rung(uplink_ip(b.id),    up, b.rtt, b.loss),
            "frontseat": _rung(frontseat_ip(b.id), fs, b.rtt + 0.5, b.loss),
            "backseat":  _rung(backseat_ip(b.id),  bs, b.rtt + 1.0, b.loss),
        }

        tele = None
        if up and b.tele_on:
            line = b.status_line()
            fields = dict(tok.split("=", 1) for tok in line.split(",") if "=" in tok)
            recv = now - b.tele_age
            tele = {
                "received_ts": recv, "received_iso": _iso(recv),
                "age_s": round(b.tele_age, 1),
                "fresh": b.tele_age < tele_stale_s,
                "src_ip": uplink_ip(b.id), "matched": True,
                "fields": fields, "raw": line,
            }

        boats_out.append({
            "name": b.name, "id": b.id, "state": state, "fault_at": fault,
            "rungs": rungs,
            "last_present_ts": last_present.get(b.name),
            "last_present_iso": _iso(last_present.get(b.name)),
            "telemetry": tele,
            "radio": radio_by_boat.get(b.name),
        })

    return {
        "ts": now, "iso": _iso(now),
        "shore_radio": _rung(SHORE_RADIO_IP, shore_ok, 1.2, 0.0),
        "shore_ok": shore_ok,
        "telemetry_port": tele_port,
        "telemetry_count": sum(1 for x in boats_out
                               if x["telemetry"] and x["telemetry"]["fresh"]),
        "radio": radio_block,
        "boats": boats_out,
    }


def write_snapshot(path, snap):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(snap, fh, indent=2)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def load_roster(path):
    try:
        cfg = json.load(open(path))
        # The simulator derives every fake rung IP from the integer BOAT_ID, so
        # it can only model formula-addressed boats. Boats that pin explicit
        # IPs (no 'id') are real-deployment escape hatches -- skip them here
        # rather than crash; the live collector handles them.
        roster = []
        for b in cfg.get("boats", []):
            if b.get("id") is None:
                print(f"sim: skipping manual-IP boat {b.get('name','?')!r} "
                      f"(no id to simulate)", file=sys.stderr)
                continue
            roster.append((int(b["id"]), b["name"]))
        return roster
    except Exception:
        return [(31, "asha"), (32, "bama"), (33, "chip"),
                (34, "dale"), (35, "ewan"), (36, "flex")]


def load_radio_cfg(path):
    """Return (enabled, name->mac map) from fleet.json's radio block. Mirrors
    collect.py: only non-blank MACs count as 'mapped'."""
    try:
        rc = json.load(open(path)).get("radio", {}) or {}
        macs = {n: m.lower() for n, m in (rc.get("macs") or {}).items() if m}
        return bool(rc.get("enabled", True)), macs
    except Exception:
        return True, {}


def assign_macs(boats, mapped):
    """Give every boat a MAC and decide which names are 'mapped'. If fleet.json
    has real MACs, honor them exactly (unfilled boats stay unmapped, exercising
    the dashboard's 'fill the MAC' path). If NONE are filled (the default), fall
    back to synthesized MACs for all boats so the Radio tab is populated in dev.
    Returns the set of mapped boat names."""
    if mapped:
        for b in boats:
            b.mac = mapped.get(b.name) or _synth_mac(b.id)
        return set(mapped)
    for b in boats:                       # dev fallback: synthesize + map all
        b.mac = _synth_mac(b.id)
    return {b.name for b in boats}


def apply_static(boats):
    """A fixed, varied tableau -- one boat per interesting case. Great for
    building and screenshotting the dashboard deterministically."""
    by = {b.name: b for b in boats}
    def setb(i, **kw):
        if i < len(boats):
            b = boats[i]
            for k, v in kw.items():
                setattr(b, k, v)
    # 0: healthy auto mission
    setb(0, link_up=True, backseat_up=True, mode="AUTO", volt=24.6, tele_on=True, tele_age=0.4)
    # 1: manual override (mode/helm disagreement), fresh
    setb(1, link_up=True, backseat_up=True, mode="MANUAL", volt=24.1, tele_on=True, tele_age=0.3)
    # 2: frontseat_only -- backseat down
    setb(2, link_up=True, backseat_up=False, mode="NO_HELM", tele_on=True, tele_age=0.5)
    # 3: offline
    setb(3, link_up=False, backseat_up=False, tele_on=False)
    # 4: present, no mission (front seat up, telemetry fresh, NO_HELM)
    setb(4, link_up=True, backseat_up=True, mode="NO_HELM", volt=25.0, tele_on=True, tele_age=0.2)
    # 5: low battery + telemetry stale while still pingable
    setb(5, link_up=True, backseat_up=True, mode="HOLD", volt=21.3, tele_on=True, tele_age=9.0)
    # RF variety for the Radio tab: strong/direct, weak/relay, mid, offline...
    setb(0, rssi=-48, mcs=15, tq=250, hop="direct", pl_ratio=0.01, tx_retries=1, tx_failed=0)
    setb(1, rssi=-71, mcs=9,  tq=150, hop="direct", pl_ratio=0.10, tx_retries=12, tx_failed=1)
    setb(2, rssi=-58, mcs=13, tq=205, hop="direct", pl_ratio=0.04, tx_retries=4, tx_failed=0)
    setb(3, rssi=-90, mcs=0,  tq=0,   hop="direct")   # offline -> not heard anyway
    setb(4, rssi=-52, mcs=14, tq=240, hop="direct", pl_ratio=0.02, tx_retries=2, tx_failed=0)
    setb(5, rssi=-83, mcs=4,  tq=88,  hop="relay",  pl_ratio=0.28, tx_retries=33, tx_failed=6)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Fleet simulator for dashboard dev")
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--config", default=os.path.join(here, "fleet.json"),
                    help="roster source (id/name); liveness is simulated")
    ap.add_argument("--snapshot", default=os.path.join(here, "fleet_status.json"))
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--telemetry-stale-s", type=float, default=5.0)
    ap.add_argument("--telemetry-port", type=int, default=9300)
    ap.add_argument("--static", action="store_true", help="fixed varied tableau")
    ap.add_argument("--once", action="store_true", help="one snapshot then exit")
    ap.add_argument("--udp", default=None, metavar="HOST:PORT",
                    help="also send real BB_STATUS datagrams to a collector")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    roster = load_roster(args.config)
    boats = [SimBoat(bid, name, rng) for bid, name in roster]
    radio_enabled, mapped = load_radio_cfg(args.config)
    mapped_names = assign_macs(boats, mapped)
    shore_radio = SimShoreRadio(rng)
    if args.static:
        apply_static(boats)

    sock = dest = None
    if args.udp:
        host, _, port = args.udp.partition(":")
        dest = (host, int(port or args.telemetry_port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    last_present = {}
    shore_ok = True
    print(f"sim_fleet: {len(boats)} boats -> {args.snapshot}"
          + (f"  + UDP {dest[0]}:{dest[1]}" if dest else "")
          + ("  [static]" if args.static else "  [dynamic]"))

    try:
        while True:
            if not args.static:
                if rng.random() < 0.002:           # rare shore-radio blip
                    shore_ok = not shore_ok
                elif not shore_ok and rng.random() < 0.5:
                    shore_ok = True
                for b in boats:
                    b.step(args.interval)
                shore_radio.step(args.interval)

            snap = build_snapshot(boats, shore_ok, args.telemetry_port,
                                  args.telemetry_stale_s, last_present,
                                  shore_radio=shore_radio,
                                  radio_enabled=radio_enabled,
                                  mapped_names=mapped_names)
            write_snapshot(args.snapshot, snap)

            if sock:
                for b in boats:
                    if b.link_up and b.tele_on:
                        try:
                            sock.sendto(b.status_line().encode(), dest)
                        except OSError:
                            pass

            present = sum(1 for x in snap["boats"] if x["state"] == "present")
            tele = snap["telemetry_count"]
            print(f"[{snap['iso']}] {present}/{len(boats)} present, "
                  f"{tele} telemetry fresh"
                  + ("" if shore_ok else "  SHORE RADIO DOWN"))

            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
