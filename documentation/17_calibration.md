---
status: draft
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-04
owner: TBD
---

# Calibration

Per-boat sensor calibration: the GPS dual-antenna distance, the gyro bias, and
the magnetometer (hard- and soft-iron). The recorded values feed
`14_um982_gps.md` and `iBBNavigatorInterface`'s per-vehicle calibration files.

---

## 1. Overview

This guide produces three calibrations for one boat: the GPS antenna baseline
distance entered into the UM982, a gyro-bias file, and a magnetometer
calibration file. The two on-Pi files are read by `iBBNavigatorInterface` at
mission start; the antenna distance lives in the receiver's own config and in
the fleet reference.

The goal is a boat whose reported heading and position can be trusted on the
water. Keep this light — measure, record in the documented location, and
validate with the applets in §7.

## 2. Prerequisites

- Mechanical and electrical build complete; the Navigator hat (with IMU and
  magnetometer) and the UM982 powered.
- UM982 streaming, with the preliminary config from
  [`14_um982_gps.md` §5](14_um982_gps.md#5-apply-the-configuration). The
  antenna distance measured here is back-filled into that config.
- `moos-ivp-blueboat` built ([`16_software_build.md` §5](16_software_build.md#5-repoint-the-remote-and-build-moos-ivp-blueboat)),
  so the validation applets (`test_gnss_heading`, `bb_attitude`) and
  `iBBNavigatorInterface` are on `PATH`.
- A flat, open area away from large metal structures for the gyro and
  magnetometer work, with clear sky view for the GPS check.
- The boat's `VNAME` (used in the calibration file paths, §3.2).

## 3. Context

### 3.1 What Calibration Covers

Three independent things:

- **GPS antenna distance** — the center-to-center baseline between the two
  GNSS antennas. The UM982 derives heading from the vector between them, so it
  needs the true separation. See
  [`14_um982_gps.md` §3.3](14_um982_gps.md#33-heading-geometry).
- **Gyro bias** — the small nonzero rate each gyro axis reports while the boat
  is perfectly still. Subtracted at runtime so a stationary boat reads zero
  turn rate.
- **Magnetometer** — hard-iron (a fixed offset from nearby magnetized metal)
  and soft-iron (a distortion of the field's shape from nearby ferrous mass).
  Both are corrected so the AHRS heading is true.

### 3.2 Where Calibration Values Live

`iBBNavigatorInterface` reads two per-vehicle files, both keyed by `VNAME`, and
configured in `plug_iBBNavigatorInterface.moos`:

| Value | File | Format |
|---|---|---|
| Magnetometer (hard + soft iron) | `/home/pi/mag_cal/$(VNAME)/mag/mag_cal_nav.dat` | `b = bx,by,bz` (hard-iron offset)<br>`A = a11,a12,a13,a21,a22,a23,a31,a32,a33` (soft-iron 3×3) |
| Gyro / accel bias | `/home/pi/mag_cal/$(VNAME)/imu/imu_cal.txt` | `gyro_bias = gx,gy,gz`<br>`accel_bias = ax,ay,az` |

`iBBNavigatorInterface` surfaces these paths itself: if a file is missing or
unreadable it raises a run-warning naming the exact path it tried (visible in
the app's AppCast via `uMAC`), so the expected location is discoverable from a
running boat. The magnetometer file is required for a trustworthy heading; the
IMU file is optional (commented out in the plug by default — uncomment
`imu_cal_file` once a gyro bias is recorded).

The GPS antenna distance is **not** an on-Pi file. It lives in the UM982's own
configuration (`CONFIG HEADING LENGTH`) and is recorded for the fleet in
[`01_fleet_and_network_reference.md` §2](01_fleet_and_network_reference.md#2-fleet-roster).

> **Note.** Re-run the relevant calibration whenever its inputs change:
> the antenna distance if either antenna is reseated or the GPS is replaced;
> the gyro bias if the IMU is remounted; the magnetometer whenever magnetic
> loads near the boat change (new battery, relocated electronics).

## 4. GPS Antenna Distance

Run on the boat; the receiver commands follow
[`14_um982_gps.md` §5](14_um982_gps.md#5-apply-the-configuration).

1. Identify the antennas: the **rear** antenna is master, the **front** is
   slave; heading points master → slave.
2. Measure the center-to-center distance between the two antenna phase centers,
   in centimeters, to ±1 cm.
3. Record the value (cm) in
   [`01_fleet_and_network_reference.md` §2](01_fleet_and_network_reference.md#2-fleet-roster).
4. Enter it into the receiver:

   ```text
   CONFIG HEADING LENGTH <baseline_cm> 1
   ```

5. Confirm the receiver accepted it — the `length` field in `UNIHEADINGA` must
   match the measured distance (validation in §7).

> **Note.** If the antenna baseline is not parallel to the keel, a heading
> offset also applies; that is a `CONFIG HEADING OFFSET` value, kept with the
> GPS config rather than here. See
> [`14_um982_gps.md` §5](14_um982_gps.md#5-apply-the-configuration).

## 5. Gyro Bias

The `bb_attitude` applet can dump raw gyro reads; the average of those reads
while the boat is still is the bias to record. Run on the boat.

1. Place the boat level and completely still on a stable surface.
2. Sample raw IMU output for a few seconds:

   ```bash
   bb_attitude --raw -v -d 5
   ```

3. Average each gyro axis (X, Y, Z) over the run. Those three averages are the
   gyro bias.
4. Write them to the IMU calibration file (create the directory if needed):

   ```bash
   mkdir -p /home/pi/mag_cal/$VNAME/imu
   nano /home/pi/mag_cal/$VNAME/imu/imu_cal.txt
   # contents:
   #   gyro_bias = <gx>,<gy>,<gz>
   #   accel_bias = 0,0,0
   ```

5. Enable the file by uncommenting `imu_cal_file` in
   `plug_iBBNavigatorInterface.moos` (it points at this path).

> **Note.** Accelerometer bias is left at zero unless a separate accel
> calibration is performed; the gyro bias is the value that matters for
> heading stability.

## 6. Magnetometer

Hard- and soft-iron calibration produces the offset vector `b` and the matrix
`A` stored in `mag_cal_nav.dat` (§3.2). The fit itself is done with an
external ellipsoid-fit routine — there is no in-repo tool for it yet — so this
section documents the capture and the output, not a specific fitting program.

1. Move the boat to an open area, away from vehicles, rebar, and large metal
   structures. Keep the full boat assembled (batteries and electronics
   installed) so the calibration captures the boat's own magnetic signature.
2. Collect magnetometer samples while slowly rotating the boat through as many
   orientations as practical (full yaw circles, plus pitch and roll tilts).
3. Fit the samples to recover the hard-iron offset (`b`) and the soft-iron
   matrix (`A`).
4. Write the result to the per-vehicle file:

   ```bash
   mkdir -p /home/pi/mag_cal/$VNAME/mag
   nano /home/pi/mag_cal/$VNAME/mag/mag_cal_nav.dat
   # contents:
   #   b = <bx>,<by>,<bz>
   #   A = <a11>,<a12>,<a13>,<a21>,<a22>,<a23>,<a31>,<a32>,<a33>
   ```

5. Confirm `mag_ak_cal_file` in `plug_iBBNavigatorInterface.moos` points at
   this path (it does by default).

> **Note.** Local magnetic declination is a separate, fleet-wide value
> (`declination_deg` in the plug — `-14.058` for the Greece site), not part of
> the per-boat magnetometer fit.

## 7. Validation

Run on the boat. Each calibration has an applet that shows whether it took.

**GPS distance and position/heading** — `test_gnss_heading` reads the UM982
directly and prints heading, baseline length, carrier solution, and position:

```bash
test_gnss_heading -p /dev/ttyUSB0 -b 230400
```

Expect: carrier solution `FIXED` (or `NARROW_INT`) under open sky; the reported
baseline length matches the §4 measurement within a few centimeters; position
sits where the boat actually is. (Cross-check against
[`14_um982_gps.md` §6](14_um982_gps.md#6-verification): `UNIHEADINGA`
`hdgstddev` < 1° static, `length` matches.)

**Gyro and AHRS heading** — `bb_attitude` shows fused attitude and gyro rates:

```bash
bb_attitude -d 5 -v
```

Expect: with the boat still, the gyro rates sit near zero (bias removed); roll
and pitch read level; yaw is stable. Use `--raw` to compare pre-bias reads.

**End-to-end via `iBBNavigatorInterface`** — with the mission running, open the
AppCast to read the live AHRS table (Roll, Pitch, Yaw, Heading, Gyro X/Y/Z,
Yaw Rate) and confirm no calibration-file run-warnings. From the mission
directory:

```bash
uMAC targs/targ_$VNAME.moos
```

Expect: the AHRS table populated and updating; `AHRS Running = true`; no
"Could not open … calibration file" warning. While slowly turning the boat by
hand, the AHRS heading should track the GPS heading from `test_gnss_heading` to
within a few degrees.

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `test_gnss_heading` baseline ≠ measured | Loose antenna, or wrong `CONFIG HEADING LENGTH` | Re-tighten and re-measure; re-issue the command (§4). |
| No GPS heading solution | Poor sky view on the slave antenna | Move to open sky; check the slave coax ([`14_um982_gps.md` §7](14_um982_gps.md#7-troubleshooting)). |
| Stationary boat shows nonzero turn rate | Gyro bias not recorded or `imu_cal_file` still commented out | Record bias (§5); uncomment `imu_cal_file`; restart the mission. |
| AHRS heading off by a roughly constant angle vs. GPS | Magnetometer hard-iron offset, or stale `mag_cal_nav.dat` | Re-run the magnetometer fit (§6). |
| AHRS heading distorted (varies with which way it points) | Soft-iron distortion / calibration done near metal | Recalibrate in a clean open area, boat fully assembled (§6). |
| "Could not open … calibration file" in AppCast | File missing or wrong path/`VNAME` | Confirm the file exists at the path the warning names (§3.2). |

## 9. Change Log

Append-only log of changes to this procedure. One line per change: date —
change — author.

- 2026-06-04 — Initial draft. Scoped to gyro bias, magnetometer, and GPS
  antenna distance. Documents the per-vehicle cal-file locations
  (`/home/pi/mag_cal/$(VNAME)/…`) and formats from
  `plug_iBBNavigatorInterface.moos`, and validation via `test_gnss_heading`,
  `bb_attitude`, and the `iBBNavigatorInterface` AppCast. Magnetometer fit
  left to an external routine (no in-repo tool yet). — JWenger
