---
status: draft
applies_to: Greece shoreside collector (fleet connectivity + telemetry)
last_updated: 2026-06-03
owner: JWenger
---

# Fleet Monitor — Collector (Subsystems A + B)

## 1. Overview

`collect.py` is a shoreside process that consolidates two views of every active
boat into one JSON snapshot the dashboard reads. **Subsystem A** (connectivity)
probes the fleet over ICMP to answer whether each boat is on the network and
whether its backseat (the pablo) is up at its assigned IP. **Subsystem B**
(telemetry) receives the `BB_STATUS` datagrams that each boat's front-seat
`pBB_Status` app pushes — battery, fused control mode, mission state, and more —
and merges them per boat. It is meant for the operator standing up shoreside
monitoring at the Greece site. This is the data-collection half only; the
web/dashboard layer is a separate piece that consumes the snapshot.

The two subsystems are independent by design: A probes *outward* and works even
when all boat software is dead; B receives *inward* and only carries data while
the front-seat mission is running. A boat can therefore be `present` (A) with no
telemetry (B), which correctly reads as "reachable, but the status app isn't
running."

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
so `fleet.json` lists only boat IDs and names and cannot drift from the address
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
some other path — can pin any rung directly in `fleet.json` by giving it as an
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

### 3.5 Snapshot handoff

Each sweep rewrites the snapshot atomically (temp file plus `os.replace`), so a
reader never observes a half-written file. The snapshot is the only contract
between this process and the dashboard; nothing else is shared.

## 4. Configure

Edit `fleet.json`. Set the active boats and tune the sweep:

```json
{
  "shore_radio_ip": "10.1.0.3",
  "ping_interval_s": 2.0,
  "ping_timeout_s": 1.0,
  "history_window": 30,
  "snapshot_path": "fleet_status.json",
  "telemetry_port": 9300,
  "telemetry_stale_s": 5.0,
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

## 5. Run

Run on the collector Pi. A single sweep, printed, then exit:

```text
./collect.py --once
```

Continuous loop using `./fleet.json`, printing a table each cycle:

```text
./collect.py
```

Options:

- `--config <path>` — use a config file other than `./fleet.json`.
- `--snapshot <path>` — override `snapshot_path` (e.g. `/run/fleetmon/status.json`).
- `--interval <seconds>` — override `ping_interval_s`.
- `--once` — one sweep then exit.
- `--quiet` — write the snapshot but print no table.

## 6. Install as a Service

Run as a `systemd` unit on the collector Pi so it survives reboots. Create
`/etc/systemd/system/fleet-monitor.service`:

```ini
[Unit]
Description=Shoreside fleet collector (connectivity + telemetry)
After=network-online.target

[Service]
WorkingDirectory=/home/pi/moos-ivp-greece/shoreside/fleet-monitor
ExecStart=/home/pi/moos-ivp-greece/shoreside/fleet-monitor/collect.py \
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

- Run `./collect.py --once` with at least one reachable boat and confirm the
  printed table shows that boat as `present` with a non-`--` uplink RTT.
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

## 9. Quick Reference

- Addresses, for `BOAT_ID = N`: uplink `10.1.0.N`, frontseat `10.N.1.1`,
  backseat `10.N.1.100`, shore radio `10.1.0.3`.
- States: `present` (both up) · `frontseat_only` (uplink up, backseat down) ·
  `offline` (uplink down).
- Telemetry (B): boats push `BB_STATUS` to `telemetry_port` (default 9300);
  attributed by source IP, each entry carries `age_s` + `fresh`.
- Start a sweep: `./collect.py --once`. Run the service:
  `sudo systemctl enable --now fleet-monitor.service`.
- Snapshot: `fleet_status.json` (or the `--snapshot` path), rewritten atomically
  every `ping_interval_s`; each boat carries A `rungs` + B `telemetry`.
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

`index.html` is a single self-contained page (vanilla JS, no dependencies) that
polls `fleet_status.json` and renders one card per boat: connectivity state,
link quality, backseat reachability, and telemetry (mode, battery, mission),
with badges for low battery, stale telemetry, the mode/helm `override`
disagreement, and the `fault_at` rung. The theme is Solarized, auto-switching
light/dark by time of day with a manual toggle. The header shows a fleet summary
and a connection indicator: a failed fetch reads as "disconnected from
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
