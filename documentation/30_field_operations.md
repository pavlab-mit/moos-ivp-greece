---
status: draft
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-04
owner: JWenger
---

# Field Operations

The working guide for a QC'd boat: from arriving on site through a day of
on-water operation and back to packed up. It picks up where
[`20_qc_signoff.md`](20_qc_signoff.md) leaves off and assumes everything in
§§01–02 and §§10–17 is already done.

---

## 1. Overview

A field session runs in seven stages: shoreside infrastructure setup, boat
assembly/init, dockside testing, pre-launch, operations, shutdown, and pack-up.
This guide walks them in order. Stages 5 and 6 loop: between runs you swap
PABLOs and batteries and return to Stage 2 rather than fully breaking down.

The steps describe **current practice** — what we actually do, rooted in how we
run at the MIT Sailing Pavilion and projected onto the Greece site. Where the
better way differs from the current way, the target is called out separately:

> **Best practice.** Callouts in this style mark the aspirational version of a
> step. They are the goal, not necessarily what happens today.

Greece-specific values that can't be pinned down until we are on site (the
operating envelope, storage layout, return point) are collected as open items
in §13.

## 2. Prerequisites

- Each boat has passed [`20_qc_signoff.md`](20_qc_signoff.md).
- Shoreside infrastructure built and configured
  ([`02_shoreside_infrastructure.md`](02_shoreside_infrastructure.md)).
- Operators familiar with the RC controller
  ([`15_rc_controller.md`](15_rc_controller.md)) and the auto-launch behavior
  ([`16_software_build.md` §3.3](16_software_build.md#33-the-autolaunch-service-model)).
- Batteries charged; chase boat(s) and PFDs available.

## 3. Context

### 3.1 Site, Operating Region, and Traffic

The Greece operating envelope — wind, sea state, daylight window, and permitted
areas — is site-specific and **TBD** (§13). Determine and brief the expected
operating region at the start of each session before any boat goes in.

Watch for boat traffic continuously the entire time vehicles are in the water,
not just at launch. When running a large number of vehicles, a dedicated
traffic spotter and a configured geofence on the operating region are part of
how we run, not optional extras.

### 3.2 Roles

- **Pilot** — holds the RC controller; manual control on launch and recovery,
  and the failsafe takeover at any time.
- **Shoreside operator** — laptops, mission control (`pMarineViewer`), and
  logs.
- **Chase boat operator(s)** — on station before launch.
- **Traffic spotter** — when the vehicle count is high (§3.1).

A single operator can run a single boat by combining the pilot and shoreside
roles, but the chase boat and traffic watch still need to be covered.

### 3.3 Comms Plan

Operators stay in voice contact on site (pilot ↔ shoreside ↔ chase boat). Agree
a backup channel for when the mesh link or a radio is flaky, and a clear verbal
call for "take manual control now."

### 3.4 Auto vs. Manual Launch

Each boat's `bb-init` decides at power-on whether to auto-launch the mission
([`16_software_build.md` §3.3](16_software_build.md#33-the-autolaunch-service-model)):

- **Auto** — power on sitting flat and level; once the battery and attitude
  gates pass, `bb-init` launches `fs-mission` on its own.
- **Manual** — power on while holding the boat raised so the attitude gate does
  not trip; the boat stays in standby (idle LED heartbeat) and the mission is
  launched by hand when ready.

## 4. Stage 1 — Shoreside Infrastructure Setup

1. Power on Starlink; confirm a clear sky view and that it comes online.
2. Set up tents / awnings.
3. Confirm chase boat operators are on station and PFDs are distributed.
4. Power on the RB5009 and the shoreside DoodleLabs Wearable (10.1.0.3).
5. Confirm internet from the field laptop over the wAP ax (`Shoreside-5GHz`).

> **Best practice.** Power the RB5009 first so routing and DHCP are up before
> the radio joins.

> **Best practice.** Run a short pre-session safety brief — operating region,
> roles, the "take manual control" call, and a comms check with the chase
> boat — before any boat is powered.

## 5. Stage 2 — Boat Assembly / Init

1. Confirm batteries are charged; charge if needed.
2. Load batteries into the boats running that day.
3. Decide auto vs. manual launch for each boat (§3.4) and power on accordingly.
4. Confirm the frontseat is on the network — ping it from the laptop for now:

   ```bash
   $ ping 10.1.0.<BOAT_ID>
   ```

> **Best practice.** A fleet status page that shows each boat's network/health
> at a glance, instead of pinging boats one at a time.

## 6. Stage 3 — Dockside Testing

1. Confirm the PABLO (backseat) is online.
2. Launch the backseat mission.
3. Confirm the backseat appears on the shoreside `pMarineViewer`.
4. Check the navigation solution (GPS fix + heading) and battery voltage.
5. Resolve any run or configuration warnings (frontseat and backseat appcasts)
   before proceeding.

## 7. Stage 4 — Pre-Launch

The last gate before the water; this is where the RC control check lives.

1. PABLO mounted and secure.
2. Hatches sealed and all clips closed.
3. Cable connections secure and tightened; unused ones capped/plugged.
4. Thrusters respond to RC inputs (boat in RC mode).
5. Visual inspection — nothing looks different or amiss.

> **Best practice.** Make step 5 a defined sweep: hull and seams intact, prop
> clear of line and debris, antennas seated, no water in the hatch wells, nav
> light functional.

## 8. Stage 5 — Operations

### 8.1 Launch and Handoff

1. Confirm the expected operating region is briefed (§3.1).
2. Put the boats in the water, usually stern / thrusters first.
3. RC each boat to a safe starting position.
4. Flip the RC controller into autonomy mode.
5. Hit deploy on shoreside.

### 8.2 Monitor

Watch continuously: boat traffic, battery voltages, comms/link quality
(DoodleLabs Associated Stations RSSI), and vehicle locations and behaviors
(`pMarineViewer`, `pBB_Health`). With a large fleet, the traffic spotter and
geofence from §3.1 are in use here.

> **Best practice.** Set a battery-voltage return threshold and recall boats
> before the pack runs low. A running boat will not return or stand down on its
> own as voltage drops — the `bb-init` voltage gate only governs the launch
> decision at power-on, not a mission already underway.

### 8.3 Recovery

1. On mission complete, the vehicles return (when the mission is configured to).
2. Take RC control near the return point and slowly pilot to the dock or shore.
3. Retrieve the boat.

## 9. Stage 6 — Shutdown

1. Offload the backseat logs.
2. Keep the boat in RC mode and exit the backseat mission.
3. Safely shut down the PABLO (run on the PABLO over SSH):

   ```bash
   sudo shutdown now
   ```

4. Remove the PABLO from the boat; take the battery pack out of the battery box.
5. **Decide: is this the last run of the day?** If not, load fresh
   PABLOs/batteries and return to **Stage 2**. If so, continue the full
   breakdown below.
6. Determine whether the frontseat logs were captured / are needed; offload if
   so.
7. Power off the boat, then turn off the main power switch (run on the Pi over
   SSH):

   ```bash
   sudo shutdown now
   ```

8. Hose off the boats to clear salt; dry where applicable.
9. Remove the batteries for charging.
10. Store the boats in their designated locations/configuration (**TBD**, §13).

## 10. Stage 7 — Pack-Up

Largely Stage 1 in reverse:

1. Power off the shoreside DoodleLabs Wearable and the RB5009.
2. Stow Starlink.
3. Strike the tents / awnings.
4. Release the chase boat(s).
5. Load out; note any defects in the boat logbook.

> **Best practice.** Hold a short end-of-day debrief — what worked, what broke,
> defects to track, and anything to change next session.

## 11. Verification (End-of-Day)

- Backseat (and any needed frontseat) logs synced.
- Defects logged.
- Batteries on chargers.
- Boats rinsed, dried, and stowed.
- Shoreside infrastructure either powered down (Stage 7) or deliberately left
  running in a known-good state.

## 12. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Laptop has no internet on `Shoreside-5GHz` | Starlink not online, or RB5009 powered after the radio | Confirm Starlink sky view/online; power-cycle with the RB5009 first (§4). |
| Boat doesn't answer `ping` | Frontseat still booting, or off-network | Wait for boot; confirm BOAT_ID/IP ([`01_fleet_and_network_reference.md`](01_fleet_and_network_reference.md)). |
| Backseat absent from `pMarineViewer` | PABLO offline or mission not launched | Confirm PABLO online and the backseat mission launched (§6). |
| Boat auto-launches when you wanted manual | Powered on flat instead of raised | Power-cycle while holding it raised so the attitude gate stays tripped (§3.4). |
| Link drops mid-mission | Range / RSSI / mesh flakiness | Watch RSSI; bring the boat back toward range; switch to the backup comms call. |
| Need to bring a boat under control now | Any in-water anomaly | Pilot calls it and flips the RC controller out of autonomy. |

## 13. Open Items (Greece)

Values that can only be set on site:

- [ ] Operating envelope: wind, sea state, daylight window, permitted areas
      (§3.1).
- [ ] Defined operating region / geofence for the site.
- [ ] Return point(s) — dock vs. shore — for recovery (§8.3).
- [ ] Boat and battery storage locations/configuration (§9).
- [ ] On-site comms channels, primary and backup (§3.3).

## 14. Operator Checklist Card

One-page reference for the field (to be laminated):

- **Power-up order:** Starlink → RB5009 → Wearable → confirm laptop internet →
  boats.
- **On-network check:** `$ ping 10.1.0.<BOAT_ID>`.
- **Launch:** in water (stern first) → RC to start position → autonomy mode →
  deploy.
- **Failsafe:** flip the RC controller out of autonomy to take manual control.
- **Shutdown:** offload logs → `sudo shutdown now` (PABLO, then boat) → main
  switch off → rinse → batteries to charge.

## 15. Change Log

Append-only log of changes to this procedure. One line per change: date —
change — author.

- 2026-06-02 — Initial draft; field session structured into seven stages
  (shoreside setup → pack-up) from current operator practice (MIT Sailing
  Pavilion) projected onto the Greece site. Steps reflect current practice;
  best-practice callouts mark targets; Greece-specific unknowns collected in
  §13. — JWenger
