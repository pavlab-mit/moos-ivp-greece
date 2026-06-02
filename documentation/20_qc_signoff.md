---
status: stub
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# QC Sign-off Checklist

The pre-deployment checklist for a Greece BlueBoat. Every box must be
checked off before the boat goes near the water. This document is
**purely a checklist** — every item references back to the build guide
that explains how to do it.

> **Status: stub.** Items below are migrated from `QC_Build_Checklist.md`
> and re-organized to reference numbered guides. The build instructions
> that used to live in the old checklist have moved into
> `10_mechanical_assembly.md` and `11_electrical_wiring.md`.

---

## 1. How to Use This Checklist

- Run through every section in order; do not skip.
- If an item fails, return to the referenced build guide.
- Two-operator sign-off recommended for the final water-readiness check
  in §6.

---

## 2. Mechanical
_(See `10_mechanical_assembly.md`.)_

### 2.1 Default Configuration
- [ ] Black cross bars secured to torque spec.
- [ ] Cross tube secured and sealed.
- [ ] Props installed.
- [ ] Identification stickers applied.
- [ ] Battery velcro installed.

### 2.2 Rails and Mounts
- [ ] 8020 rails mounted with bushings, fasteners secure.
- [ ] 8020 endcaps installed.
- [ ] PABLO plate installed.
- [ ] GPS antenna mounts secured (port side).
- [ ] E-stop installed (starboard rear) and sealed (RTV + dielectric
      grease).
- [ ] DoodleLabs radio installed on adapter plate with heat sink and buck
      converter.
- [ ] Unicore module installed, no movement.

### 2.3 Passthroughs
_(All tight, molycoated, dielectric grease on exposed contacts.)_

- [ ] Front-right M14: 60″ coax / N-type.
- [ ] Rear-right M14: nav light.
- [ ] Front-left M14: potted GPS passthrough.
- [ ] Rear-left M14: 12/24″ coax / N-type.
- [ ] Right M10s: front (payload power #1), right (on/off), rear (E-stop
      signal), left (PABLO Ethernet).
- [ ] Left M10s: front (payload power #1), right (battery balance),
      rear blank, left blank.

---

## 3. Electrical
_(See `11_electrical_wiring.md`.)_

### 3.1 Safety
- [ ] 3-pin signal cable correctly connected to contact block (NC contact
      verified).
- [ ] 3-pin signal bulkhead spliced into the blue power wire such that
      switches are in series.
- [ ] **Boat does not power on with E-stop disconnected.**
- [ ] **Boat does not power on with E-stop engaged.**
- [ ] Blue switch connector (2-pin JST) seated on main power contactor.
- [ ] All solder joints sealed with heat-shrink.

### 3.2 Power Delivery
- [ ] Payload power #1 terminated as XT60 (black + red).
- [ ] Payload power #2 terminated as XT60 (black + red).
- [ ] XT60 Y-splitter installed for starboard pontoon → payload power #1.
- [ ] XT60 Y-splitter installed for port pontoon → payload power #2.
- [ ] 5 V buck converter for DoodleLabs wired with 2 A fuse to battery
      voltage.
- [ ] 5 V buck converter wired into DL EVK board (correct polarity).

### 3.3 Data
- [ ] 6 ft Ethernet cable through cross tube, connected to DL EVK board.
- [ ] Both antennas seated in DL push-to-connect ports with strain relief.
- [ ] Both antennas connected to N-type bulkheads, fully seated.
- [ ] USB → Ethernet adapter connected, wrapped in e-tape, plugged into
      upper USB 3.0 port.
- [ ] USB 3.0 cable through cross tube, UM982 data port → lower USB 3.0
      port.
- [ ] UM982 antennas 1 and 2 labeled and connected to correct SMA ports.
- [ ] 8-pin Ethernet port terminated as RJ45; connectivity test passed;
      connected to Navigator's main Ethernet port.
- [ ] Bulgin → Blue Trail Ethernet cable spliced with waterproof
      heat-shrink; connectivity test passed.

---

## 4. Software / Image
_(See `13_frontseat_first_boot.md` and `16_software_build.md`.)_

### 4.1 Image
- [ ] Image installed per the first-boot guide.
- [ ] Hostname set correctly.
- [ ] Boat boots cleanly.

### 4.2 Build
- [ ] `moos-ivp-blueboat` cloned and built.
- [ ] `moos-ivp-greece` cloned and built.
- [ ] `bb-init.service` and `fs-mission.service` installed and enabled.

---

## 5. Networking, Radio, GPS, Autonomy

### 5.1 Networking
_(See `13_frontseat_first_boot.md` and `01_fleet_and_network_reference.md`.)_

- [ ] Network configured per the first-boot guide.
- [ ] BOAT_ID, vname, and radio mgmt IP / MAC recorded in the fleet
      reference spreadsheet.
- [ ] Boat reaches the internet from the Pi.
- [ ] Backseat DHCPs into `10.<BOAT_ID>.1.100`.
- [ ] Backseat reaches the internet.

### 5.2 Radio
_(See `12_doodle_labs_radio.md`.)_

- [ ] Radio configured per the DoodleLabs guide.
- [ ] Firmware up to date.
- [ ] Radio reachable at `10.<BOAT_ID>.3.2` from the Pi.
- [ ] Shoreside radio sees the boat radio's MAC in Associated Stations.

### 5.3 GPS
_(See `14_um982_gps.md` and `17_calibration.md`.)_

- [ ] GPS configured per the UM982 guide.
- [ ] Clean fix for position and heading.
- [ ] Heading and velocity update when the boat is moved.
- [ ] Calibration values recorded (`17_calibration.md`).

### 5.4 Autonomy
_(See `15_rc_controller.md`, `16_software_build.md`,
`17_calibration.md`.)_

- [ ] Repositories pulled and rebuilt.
- [ ] Auto-launch scripts installed.
- [ ] Boat auto-launches when flat; goes idle when raised.
- [ ] IMU and magnetometer calibrated; files in the correct locations.
- [ ] `fs-mission` launches without warnings or errors.
- [ ] Community name correct.
- [ ] RC controller bound, in SBUS mode, mode switch tested.

---

## 6. Final Water-Readiness Sign-off

- [ ] All sections above complete.
- [ ] Operator #1: __________________________  Date: __________
- [ ] Operator #2: __________________________  Date: __________

Boat cleared for water testing.
