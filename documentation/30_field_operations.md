---
status: stub
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# Field Operations

The working guide for a QC'd boat: pre-launch, launch, in-water operations,
mission control, and recovery. This document picks up where
`20_qc_signoff.md` leaves off and assumes everything in §§01–02 and
§§10–17 is already done.

> **Status: stub.** Brand-new document. Content to be drafted from
> existing operator practice; nothing in the originals covers this.

---

## 1. Overview
_To do._

What this guide produces: a repeatable on-water session, from arrival on
site through boat-in-water through mission through recovery and shutdown.

## 2. Prerequisites
_To do._

- Boat passes `20_qc_signoff.md`.
- Shoreside infrastructure up (`02_shoreside_infrastructure.md`).
- Operator(s) familiar with the RC controller (`15_rc_controller.md`).

## 3. Context

### 3.1 Site and Weather Constraints
_To do._

Greece-site-specific operating envelope: wind, sea state, daylight,
permitted areas. Where to look these up.

### 3.2 Roles
_To do._

Pilot (RC + recovery), shoreside operator (laptops, mission control,
logs). Single-operator scenarios.

### 3.3 Comms Plan
_To do._

How operators talk to each other on site. Backup comms when the mesh is
flaky.

## 4. Pre-Launch
_To do._

Step-by-step:

1. Power up shoreside infrastructure
   (`02_shoreside_infrastructure.md` §_TBD_).
2. Set up the field laptop on `Shoreside-5GHz`; verify DHCP lease in
   `10.1.0.0/24`.
3. Power on the RC transmitter; confirm the boat profile is loaded.
4. Power on the boat (battery + master switch); E-stop in safe state.
5. Wait for boot. From the laptop: `ping 10.1.0.<BOAT_ID>` succeeds.
6. SSH to the boat; confirm `fs-mission.service` is active.
7. Check GPS: `BESTNAVA` showing `SOL_COMPUTED`, heading stable.
8. Confirm `RC_CONNECTED=true` on the appcast; mode switch in RC.

## 5. Launch
_To do._

Step-by-step:

1. Carry boat to water with both operators.
2. Last visual: antennas seated, hatches closed, props clear.
3. Place in water; release.
4. Pilot takes manual control in RC mode for the first 10–30 s; confirm
   responsiveness on all axes.

## 6. Running a Mission
_To do._

Step-by-step:

1. From shoreside, launch the mission as `<TBD>`.
2. Confirm community visible in `pMarineViewer`.
3. Switch boat to autonomy via CH6.
4. Watch behavior; pilot remains hands-on, ready to flip back to RC.

## 7. In-Water Health Monitoring
_To do._

What to watch from shore: link quality (Doodle Labs Associated Stations
RSSI), boat health appcast (`pBB_Health`), GPS solution type, battery
voltage if telemetered.

## 8. Recovery
_To do._

Step-by-step:

1. Flip CH6 to RC mode.
2. Pilot drives boat to recovery point.
3. Lift boat; immediately raise to break the "flat" detection so
   `fs-mission` goes idle.
4. Power off boat (master switch).
5. Power off TX.

## 9. Shutdown
_To do._

Step-by-step:

1. Pull logs from the boat (path TBD).
2. Note any defects in the boat's logbook.
3. Charge batteries.
4. Stow boat.

## 10. Verification (End-of-Day)
_To do._

- Logs successfully synced.
- Defects logged.
- Batteries on charger.
- Shoreside infrastructure either left running with known good state or
  shut down per `02_shoreside_infrastructure.md`.

## 11. Troubleshooting
_To do._

In-water failure modes: link loss (auto failsafe behavior), GPS fix loss,
unexpected mode switches, motor stall.

## 12. Operator Checklist Card
_To do._

One-page laminated reference: power-up order, key SSH and ping commands,
emergency procedure on link loss.
