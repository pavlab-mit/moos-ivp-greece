---
status: draft
applies_to: Greece shoreside collector (fleet connectivity + telemetry + RF)
last_updated: 2026-06-04
owner: JWenger
---

# Fleet Monitor — Collector (Subsystems A + B + C)

## 1. Overview

`collect.py` is a shoreside process that consolidates three views of every active
boat into one JSON snapshot the dashboard reads. **Subsystem A** (connectivity)
probes the fleet over ICMP to answer whether each boat is on the network and
whether its backseat (the pablo) is up at its assigned IP. **Subsystem B**
(telemetry) receives the `BB_STATUS` datagrams that each boat's front-seat
`pBB_Status` app pushes — battery, fused control mode, mission state, and more —
and merges them per boat. **Subsystem C** (RF/mesh quality) polls *only* the
shoreside DoodleLabs radio's JSON-RPC API for its linkstate and reads, per boat,
the radio's view of that boat's link — RSSI, MCS, batman-adv mesh TQ, and
direct/relay hop. It is meant for the operator standing up shoreside monitoring
at the Greece site. This is the data-collection half only; the web/dashboard
layer is a separate piece that consumes the snapshot.

The three subsystems are independent by design: A probes *outward* and works even
when all boat software is dead; B receives *inward* and only carries data while
the front-seat mission is running; C reaches *sideways* to one radio and works
whenever that radio is up. A boat can therefore be `present` (A) with no
telemetry (B), which correctly reads as "reachable, but the status app isn't
running" — or `present` with a sagging RF link (C), the early warning that ICMP
reachability alone can't give you.

## 2. Prerequisites

- A **collector Pi** wired into the RB5009 on `10.1.0.0/24`, with a **static IP
  outside the DHCP pool** (the pool is `.100–.200`, so e.g. `10.1.0.10`) so the
  dashboard URL never moves.
- The RB5009 static routes to each boat's `10.<id>.1.0/24` in place (see
  [`01_fleet_and_network_reference.md` §6](../../documentation/01_fleet_and_network_reference.md#6-rb5009-static-routes)).
- Python 3 (standard library only — no `pip install`) and the system `ping`
  binary, both present by default on Raspberry Pi OS.
- For Subsystem B: each boat's front-seat mission running `pBB_Status` with
  `tx_ip` set to this collector and `tx_port` matching `telemetry_port` below.
- For Subsystem C: the shore radio reachable from the collector at its API IP
  (`10.1.0.3` by default — already the shore-radio ping rung), with JSON-RPC
  enabled (default on June-2024+ firmware) and credentials set in `fleet.<site>.json`.
  No boat-side setup and no extra RB5009 routes are needed — we poll the shore
  radio only, and it already hears every boat radio on the mesh.
- This repository checked out on the collector Pi.

## 3. Context

### 3.1 Why probe from a dedicated collector

Every boat's traffic crosses the DoodleLabs mesh, the scarcest and least
reliable link on the network. If each laptop probed boats directly, that probe
traffic would cross the mesh once per viewer. A single collector makes the mesh
carry one probe stream regardless of how many people are watching, and the wired
gigabit backbone fans the result out to laptops for free. Centralizing also
separates failure domains: a laptop that cannot reach the collector knows the
problem is local, not the fleet.

Nothing runs on the boats for this. Because the collector probes from outside, it
keeps reporting during boot, before any mission launches, and even when all
boat-side software is dead — which is exactly when its answer matters most.

### 3.2 Addressing

All probe addresses derive by formula from `BOAT_ID`
(see [`01_fleet_and_network_reference.md` §4](../../documentation/01_fleet_and_network_reference.md#4-addressing-scheme)),
so `fleet.<site>.json` lists only boat IDs and names and cannot drift from the address
plan. Each sweep walks a short ladder of rungs per boat:

| Rung | Address | Tests |
|---|---|---|
| `shore_radio` | `10.1.0.3` | Shore DoodleLabs, fleet-wide. If down, every boat reads offline. |
| `uplink` | `10.1.0.<id>` | Boat powered, mesh link up, Pi alive — *"on the network"*. |
| `frontseat` | `10.<id>.1.1` | Pi internal interface; disambiguation only. |
| `backseat` | `10.<id>.1.100` | The pablo — *"backseat at its IP"*. |

> **Note.** The RB5009 routes each boat's `10.<id>.1.0/24`, so the three per-boat
> rungs are reachable from shore. It does not route the radio-management `/30`
> (`10.<id>.3.0/30`), so the boat-radio rung is omitted on purpose — reaching
> `10.1.0.<id>` already implies the radio and mesh path are healthy. Adding
> `/ip route add dst-address=10.<id>.3.0/30 gateway=10.1.0.<id>` on the RB5009
> would let a `radio` rung be added later to isolate "radio up but Pi down".

**Manual override (boats off the address plan).** A boat that doesn't follow the
formula — a static lease, a different subnet, a frontseat/backseat reached over
some other path — can pin any rung directly in `fleet.<site>.json` by giving it as an
IP string instead of relying on `id`:

```json
{ "name": "odd", "active": true,
  "uplink": "10.1.0.40", "frontseat": "192.168.5.1", "backseat": "192.168.5.100" }
```

An explicit `uplink` / `frontseat` / `backseat` always wins over the `BOAT_ID`
formula, so you can mix them (keep `id`, override just one rung) or drop `id`
entirely and pin every rung the boat needs. Telemetry attribution still works —
it keys on whatever the boat's resolved `uplink` IP is. (The simulator only
models formula-addressed boats, so it skips manual-IP entries.)

### 3.3 Connectivity states

The `uplink` and `backseat` rungs drive a three-state result; `frontseat` and
`shore_radio` refine where a break sits.

| State | Meaning | Condition |
|---|---|---|
| `present` | Fully reachable; hand off to Subsystem B. | `uplink` up and `backseat` up. |
| `frontseat_only` | Pi and mesh healthy, pablo down or unplugged. | `uplink` up, `backseat` down. |
| `offline` | Boat off or mesh link down. | `uplink` down. |

`fault_at` localizes the break to one rung: `shore_radio` (shore-side, whole
fleet), `uplink`, `frontseat` (Pi forwarding plane suspect), or `backseat`
(pablo host down while forwarding still works).

### 3.4 Telemetry receiver (Subsystem B)

The collector binds a UDP socket on `telemetry_port` and listens for `BB_STATUS`
datagrams pushed by each boat's front-seat `pBB_Status`. Each datagram is a
single comma-separated `key=value` line (`mode`, `mission`, `volt`, `batt`,
`helm`, `stale`, and the rest). The collector attributes a datagram to a boat by
its **source IP** — a boat's shore uplink is `10.1.0.<id>`, which is also the
source address of its packets, so the sender identifies itself with no
configuration. If a packet arrives from an address that isn't a known uplink,
the collector falls back to the payload's own `vname` field so a misaddressed
boat still appears rather than vanishing.

Telemetry is timestamped on receipt and carries an `age_s` and a `fresh` flag
(`age_s < telemetry_stale_s`). Because A and B are independent, the snapshot can
show a boat `present` (A) with `telemetry: null` or `fresh: false` (B) — that is
the correct reading of "reachable, but `pBB_Status` isn't sending".

### 3.5 RF/mesh quality (Subsystem C)

The collector polls **only the shoreside DoodleLabs radio** over its JSON-RPC
(ubus) API at `radio.api_ip`: it logs in once, then reads
`/tmp/linkstate_current.json` each `radio.poll_interval_s`. We poll the shore
radio alone — not each boat radio — for the same reason A uses one collector:
the shore radio's own station and mesh tables already list *every* boat radio it
hears, so one HTTP call per poll yields shore→fleet RF quality, and no extra
RB5009 route into the radio-management `/30`s is required. The poll runs in a
worker thread on its own cadence; a dead or unreachable radio just lets the data
go stale (`radio.ok:false`) and never disturbs A or B. Pure standard library
(`urllib` + `ssl`), so the no-`pip` rule still holds; the radio's self-signed
cert means TLS verification is disabled (encrypted link, radio trusted by
network position).

**Linkstate file vs. fallback.** The Doodle Labs `linkstate` daemon writes the
consolidated `/tmp/linkstate_current.json` (PHY + batman-adv mesh in one file)
only when **Enable Link Status Log** is turned on in the radio's web GUI (Link
Status Configuration). It's off by default on the pavlab units, so the daemon
runs and emits ubus events but writes no file, and the collector's read returns
"not found". Turning that toggle on is the cleanest fix — the collector then
reads the file directly and gets every field (including `pl_ratio`).

When the file is absent the collector reconstructs the same record itself, so
monitoring works either way: per-neighbor RSSI, per-antenna RSSI, MCS, and tx
retries/failed from `iwinfo assoclist`; channel/noise from `iwinfo info`;
load/free memory from `system info`; and batman-adv mesh `tq` (0–255) plus
direct/relay `hop` by parsing `batctl o`. The fallback is automatic and needs no
config; set `radio.mesh_device` (default `wlan0`) only if the mesh interface is
named differently. The only field the fallback can't supply is `pl_ratio`
(packet-loss ratio), which reads as `—`; if `batctl` is missing on a unit, `tq`
and `hop` read `—` too.

Each station is joined back to a boat **by MAC**. The mapping lives in one place
— `radio.macs` in `fleet.<site>.json` — to be filled in once at the site. Until a
boat's MAC is filled, that boat shows no RF data and any station the shore radio
hears for it surfaces in the snapshot's `radio.unmapped` list (and the
dashboard's "unmapped" table), so nothing is hidden; filling the MAC snaps it to
the boat. Per boat, Subsystem C reports `rssi` (+ per-antenna `rssi_ant`), `mcs`,
batman-adv `tq` (0–255) with `hop_status` (`direct`/`relay`) and
`last_seen_msecs`, plus `pl_ratio`, `tx_retries`/`tx_failed`, and `inactive`.
The shore radio's own `noise` floor, channel/frequency/width, `activity`, CPU
load, and free memory ride along at the top level. Because C is independent, a
boat can be `present` (A) yet show a weak or relayed RF link (C) — the early
warning that a link is degrading before ICMP starts dropping.

### 3.6 Snapshot handoff

Each sweep rewrites the snapshot atomically (temp file plus `os.replace`), so a
reader never observes a half-written file. The snapshot is the only contract
between this process and the dashboard; nothing else is shared.

## 4. Configure

There is one config file per site — `fleet.greece.json` and `fleet.mit.json` —
and `collect.py --config` is **required**, so you always pick the fleet
explicitly and never probe the wrong one by forgetting a flag. Edit the file for
your site; set the active boats and tune the sweep:

```json
{
  "shore_radio_ip": "10.1.0.3",
  "ping_interval_s": 2.0,
  "ping_timeout_s": 1.0,
  "history_window": 30,
  "snapshot_path": "fleet_status.json",
  "telemetry_port": 9300,
  "telemetry_stale_s": 5.0,
  "radio": {
    "enabled": true,
    "api_ip": "10.1.0.3",
    "username": "user",
    "password": "DoodleSmartRadio",
    "poll_interval_s": 2.0,
    "timeout_s": 4.0,
    "stale_s": 6.0,
    "macs": {
      "asha": "", "bama": "", "chip": "",
      "dale": "", "ewan": "", "flex": ""
    }
  },
  "boats": [
    { "id": 31, "name": "asha", "active": true },
    { "id": 32, "name": "bama", "active": true }
  ]
}
```

Toggle `active` to add or drop a boat. `history_window` is how many recent sweeps
feed the rolling `loss_pct` and `avg_rtt_ms` per rung. `telemetry_port` must
match each boat's `pBB_Status` `tx_port`; `telemetry_stale_s` is how long after
the last datagram a boat's telemetry is still considered `fresh`.

The **`radio`** block configures Subsystem C. Set `enabled:false` to turn it off
entirely. `api_ip` is the shore radio's JSON-RPC address (the same `10.1.0.3`
shore rung); `username`/`password` default to the June-2024+ firmware login.
`poll_interval_s`, `timeout_s`, and `stale_s` tune the poll cadence, per-request
timeout, and how long after the last good poll the RF data is still `fresh`.
**`macs` is the one thing to fill in at Greece** — map each boat name to its
boat-radio MAC (lowercase, colon-separated). Leave an entry blank until you know
it: that boat simply shows no RF data, and any station the shore radio hears for
it appears under `radio.unmapped` until the MAC is supplied. The MAC map is the
single source of attribution; nothing else changes when you fill it in.

> **Per-site files.** `fleet.greece.json` uses the formula addressing above
> (shore uplink `10.1.0.<id>`, shore radio `10.1.0.3`). `fleet.mit.json` shares
> the same internal `10.<id>.x` plan but the lab uses a different shore network,
> so each boat pins an explicit `uplink` (`192.168.1.<100+id>`) and the shore
> radio is `192.168.1.130` — an illustration of the §3.2 manual-override escape
> hatch. Keep each site's boat roster and `radio.macs` in its own file.

## 5. Run

Run on the collector Pi. `--config` is required — name your site's file. A
single sweep, printed, then exit:

```text
./collect.py --config fleet.greece.json --once
```

Continuous loop, printing a table each cycle (swap in `fleet.mit.json` at MIT):

```text
./collect.py --config fleet.greece.json
```

Options:

- `--config <path>` — **required**; the site fleet config (`fleet.greece.json`, `fleet.mit.json`).
- `--snapshot <path>` — override `snapshot_path` (e.g. `/run/fleetmon/status.json`).
- `--interval <seconds>` — override `ping_interval_s`.
- `--once` — one sweep then exit.
- `--quiet` — write the snapshot but print no table.

## 6. Install as a Service

Run as a `systemd` unit on the collector Pi so it survives reboots. The easiest
path is the bundled installer, which writes both the collector and dashboard
units and picks the site config for you (`FLEET` defaults to `greece`):

```text
sudo ./deploy/install.sh                 # Greece collector + dashboard
sudo FLEET=mit ./deploy/install.sh       # MIT collector + dashboard
```

To do it by hand instead, create `/etc/systemd/system/fleet-monitor.service`
(note `--config` is required — name the site file):

```ini
[Unit]
Description=Shoreside fleet collector (connectivity + telemetry + RF)
After=network-online.target

[Service]
WorkingDirectory=/home/pi/moos-ivp-greece/scripts/fleet-monitor
ExecStart=/home/pi/moos-ivp-greece/scripts/fleet-monitor/collect.py \
          --config /home/pi/moos-ivp-greece/scripts/fleet-monitor/fleet.greece.json \
          --quiet --snapshot /run/fleetmon/status.json
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

Enable and start it:

```text
sudo systemctl daemon-reload
sudo systemctl enable --now fleet-monitor.service
```

> **Note.** A dead collector only blanks the dashboard; it never touches
> missions, so restarting it is always safe.

## 7. Verification

- Run `./collect.py --config fleet.greece.json --once` with at least one
  reachable boat and confirm the printed table shows that boat as `present`
  with a non-`--` uplink RTT.
- Confirm the snapshot exists and parses: `python3 -m json.tool fleet_status.json`
  should print without error and list each active boat with a `state` field.
- Unplug a backseat (or stop its host) and confirm that boat flips to
  `frontseat_only` with `fault_at: backseat` within one or two sweeps, while its
  `uplink` rung stays alive.
- For Subsystem B, with a boat running `pBB_Status`, confirm its row shows a
  `telemetry` cell (e.g. `AUTO 24.3V`) and that the boat's snapshot entry has a
  `telemetry` object with `fresh: true`. Stop `pBB_Status` and confirm it flips
  to `fresh: false` within `telemetry_stale_s`, while connectivity stays
  `present`.
- For Subsystem C, confirm the printed header shows `radio fresh (noise …)` and
  the snapshot's top-level `radio.ok` is `true`. With a boat's MAC filled into
  `radio.macs`, confirm that boat's entry has a `radio` object with a real
  `rssi`/`tq`; with a MAC left blank, confirm the boat's `radio` is `null` and
  its station appears under `radio.unmapped`. Power the shore radio down and
  confirm `radio.ok` goes `false` within `stale_s` while A and B keep running.

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| All boats `offline`, `shore_ok` false | Shore DoodleLabs down or unplugged from RB5009 port 3 | Restore the shore radio; verify `10.1.0.3` pings from the collector. |
| One boat `offline`, others fine | Boat powered down or its mesh link dropped | Check the boat; nothing to fix shoreside. |
| Boat stuck `frontseat_only` | Backseat off, unplugged from `eth0`, or no DHCP lease | Power/seat the pablo; confirm it holds `10.<id>.1.100`. |
| Backseat reachable but flips `frontseat_only` with `fault_at: frontseat` | Pi forwarding plane or route issue | Check the boat Pi's `eth0` and the RB5009 route to `10.<id>.1.0/24`. |
| `ERROR: ping not found on PATH` | `iputils-ping` missing | `sudo apt install iputils-ping`. |
| Boat `present` but `telemetry` null | `pBB_Status` not running, or `tx_ip`/`tx_port` wrong | Check the front-seat mission; confirm `tx_port` == `telemetry_port`. |
| `telemetry port N unavailable` on start | Another process holds the port | Free the port or change `telemetry_port` (and each boat's `tx_port`). |
| Telemetry shows but `matched:false` | Boat's source IP isn't its `10.1.0.<id>` uplink | Expected off-site; on the mesh it attributes by uplink IP automatically. |
| Radio tab empty / `radio.ok:false` | Shore radio unreachable, JSON-RPC off, or wrong creds | Verify `https://10.1.0.3/ubus` reachable; enable JSON-RPC; check `radio.username`/`password`. |
| Boats listed under "unmapped" | Their MACs aren't in `radio.macs` yet | Fill each boat's boat-radio MAC into `radio.macs` (lowercase). |
| Boat `present` but `radio` null | MAC blank, or shore radio doesn't currently hear it | Fill the MAC; if filled, check the boat radio's mesh link. |
| `radio` STALE in header | Polls failing after a good start (radio rebooted, link flapping) | Transient is fine; if persistent, check the shore radio and `timeout_s`. |

## 9. Quick Reference

- Config: one file per site (`fleet.greece.json`, `fleet.mit.json`);
  `--config` is required.
- Addresses (Greece), for `BOAT_ID = N`: uplink `10.1.0.N`, frontseat `10.N.1.1`,
  backseat `10.N.1.100`, shore radio `10.1.0.3`. (MIT: uplink `192.168.1.(100+N)`,
  shore radio `192.168.1.130`, same internal `10.N.x`.)
- States: `present` (both up) · `frontseat_only` (uplink up, backseat down) ·
  `offline` (uplink down).
- Telemetry (B): boats push `BB_STATUS` to `telemetry_port` (default 9300);
  attributed by source IP, each entry carries `age_s` + `fresh`.
- RF/mesh (C): poll the shore radio's JSON-RPC linkstate at `radio.api_ip`;
  join stations to boats by `radio.macs`; per boat: `rssi`, `mcs`, mesh `tq`
  (0–255), `hop_status`. Fill `radio.macs` at the site; blanks → `radio.unmapped`.
- Start a sweep: `./collect.py --config fleet.greece.json --once`. Install the
  service: `sudo ./deploy/install.sh` (or `sudo FLEET=mit ./deploy/install.sh`).
- Snapshot: `fleet_status.json` (or the `--snapshot` path), rewritten atomically
  every `ping_interval_s`; each boat carries A `rungs` + B `telemetry` + C `radio`,
  plus a top-level `radio` summary.
- Dashboard: `index.html`, served over HTTP (`python3 -m http.server 8000`),
  polls the snapshot. Dev loop: `./sim_fleet.py &` then the server.

## 10. Development without a boat network

`sim_fleet.py` produces the same `fleet_status.json` schema as `collect.py`, so a
dashboard can be built entirely offline and will run unchanged against the live
collector (the schema match is enforced by a test).

```text
./sim_fleet.py --static      # fixed tableau: one boat per case (build/screenshot)
./sim_fleet.py               # dynamic: states flip, batteries drain, telemetry goes stale
./sim_fleet.py --once        # write one snapshot and exit
```

To exercise the real Subsystem-B receiver in `collect.py` instead of writing the
snapshot directly, send live `BB_STATUS` datagrams to a running collector:

```text
./sim_fleet.py --udp 127.0.0.1:9300
```

Off the mesh the sender's source IP isn't a `10.1.0.<id>` uplink, so telemetry
attributes by the payload `vname` (`matched: false`) — expected, and harmless.

## 11. Dashboard

`index.html` is a single self-contained page (vanilla JS, no dependencies) with
two tabs in the header. The **Fleet** tab renders one card per boat: connectivity
state, link quality, backseat reachability, and telemetry (mode, battery,
mission), with badges for low battery, stale telemetry, the mode/helm `override`
disagreement, and the `fault_at` rung. RF/mesh data is deliberately kept off the
Fleet tab to avoid clutter. The **Radio** tab is the single home for Subsystem C:
a shore-radio panel (status, noise floor, channel/frequency/width, activity, CPU
load, free memory, stations heard) above a per-boat table of RSSI (with bar),
antennas, MCS, mesh TQ (with bar), direct/relay hop, packet loss, and tx
retry/fail — plus an "unmapped" table listing any station whose MAC isn't yet in
`radio.macs`. Boats the shore radio can't hear read "not heard"; radio-subsystem
health (live/stale/unreachable) shows in the shore-radio panel here, not in the
Fleet header. The theme is Solarized, auto-switching light/dark by time of day
with a manual toggle; the active tab is remembered. The header shows a fleet
summary and a connection indicator: a failed fetch reads as "disconnected from
collector" (a *local* link problem), and an old snapshot warns the collector may
be stalled — both distinct from any individual boat being down.

Serve it over HTTP — do not open it as a `file://` URL, since browsers block the
snapshot fetch there. On the collector Pi (or a dev machine), from this
directory:

```text
python3 -m http.server 8000
```

Then open `http://localhost:8000/` (or `http://<collector-ip>:8000/`).

To develop against the simulator, run both from this directory:

```text
./sim_fleet.py &
python3 -m http.server 8000
```

URL parameters: `?src=<path>` overrides the snapshot location (default
`fleet_status.json`); `?poll=<seconds>` sets the refresh interval (default 2).
