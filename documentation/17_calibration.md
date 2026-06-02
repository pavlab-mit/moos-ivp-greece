---
status: stub
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# Calibration

Per-boat physical and sensor calibrations: GPS antenna baseline and heading
offset, IMU, and magnetometer. Output values feed
`14_um982_gps.md` and the mission configuration.

> **Status: stub.** This is a brand-new document; nothing in the
> originals covers calibration as a coherent procedure.

---

## 1. Overview
_To do._

What this guide produces: measured and recorded calibration values for
this boat, stored in the agreed-on locations (mission config, fleet
reference, on-Pi calibration files).

## 2. Prerequisites
_To do._

- Mechanical + electrical complete.
- UM982 powered and streaming (preliminary config from
  `14_um982_gps.md` §5; baseline value will be back-filled here).
- IMU and magnetometer present on the Navigator hat.
- Clear sky view and a flat open area for IMU/mag work.

## 3. Context

### 3.1 What "Calibration" Covers Here
_To do._

GPS: antenna baseline length and heading-offset angle. IMU: accelerometer
zero, gyro bias. Magnetometer: hard- and soft-iron calibration.

### 3.2 Where Calibration Values Live
_To do._

Per-boat config files on the Pi (paths TBD), referenced by mission plugs.
Headline values (baseline length, heading offset) also captured in
`01_fleet_and_network_reference.md` for fleet-level visibility.

### 3.3 When to Re-calibrate
_To do._

Any time antennas are reseated, the GPS module is replaced, the IMU is
remounted, magnetic loads near the boat change (new battery, new
electronics).

## 4. GPS Antenna Baseline
_To do._

Step-by-step:

1. Identify master (rear) and slave (front) antennas.
2. Measure center-to-center distance, in centimeters, to ±1 cm.
3. Record value in `01_fleet_and_network_reference.md`.
4. Issue `CONFIG HEADING LENGTH <baseline_cm> 1` (see
   `14_um982_gps.md` §5).
5. Verify the UNIHEADINGA `length` field matches the measurement.

## 5. Heading Offset
_To do._

Step-by-step:

1. Determine whether the antenna baseline is parallel to the keel.
2. If not, measure the angle offset (degrees, clockwise from keel
   forward).
3. Issue `CONFIG HEADING OFFSET <heading_offset> 0.0`.
4. Compare UM982 heading to a known reference (compass, fixed dock
   orientation).

## 6. IMU Calibration
_To do._

Procedure for accelerometer zero and gyro bias. Required orientations,
duration, where the resulting file is written.

## 7. Magnetometer Calibration
_To do._

Procedure for hard- and soft-iron calibration. Open area away from metal.
Slow rotations on all axes. Validation against known headings.

## 8. Storing Calibration Files
_To do._

File paths on the Pi (TBD). Permissions. Backup procedure so a re-imaged
Pi doesn't lose calibration.

## 9. Verification
_To do._

- UNIHEADINGA `hdgstddev` < 1° in static conditions.
- IMU acceleration on a level surface within ±0.01 g of expected.
- Magnetometer heading matches GPS heading to within a few degrees while
  the boat moves.

## 10. Troubleshooting
_To do._

Drift in heading, persistent bias in IMU, distorted magnetometer (nearby
metal, unbalanced loads).
