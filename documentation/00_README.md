---
status: stub
applies_to: Greece BlueBoat fleet (2026 Summer Course)
last_updated: 2026-06-02
owner: TBD
---

# Documentation — Greece BlueBoat Deployment

This folder contains everything needed to take a Greece BlueBoat from a pile of
parts to a vehicle running autonomy on the water. The docs are intended to be
read in numeric order for a first-time build, and used by section number for
reference thereafter.

---

## 1. How to Read This Folder

Numeric prefixes encode read order:

- **`00_…`** — Reference and meta-documentation. Read once, refer back as
  needed.
- **`01_…`–`02_…`** — Deployment-level docs (fleet/IP plan, shoreside
  infrastructure). Built once per Greece site, not per boat. Everything
  downstream assumes these values.
- **`10_…`–`17_…`** — Per-boat build sequence. Top-to-bottom is the
  recommended order for a new boat.
- **`20_…`** — Per-boat verification (QC sign-off). Run before the boat
  goes near water.
- **`30_…`** — Field operations. Once the boat is QC'd, this is the
  working guide.
- **`99_…`** — Optional appendices (troubleshooting index, glossary).

---

## 2. Recommended Read Order

### Deployment (once per Greece site)

1. `01_fleet_and_network_reference.md` — plan the fleet: BOAT_IDs, names,
   IP assignments.
2. `02_shoreside_infrastructure.md` — build the shore network: RB5009,
   wAP ax, Starlink, shoreside DoodleLabs Wearable.

### Per-boat build

For a brand-new boat, work through these in order:

3. `10_mechanical_assembly.md` — hulls, rails, mounts, passthroughs.
4. `11_electrical_wiring.md` — power, signal, and data wiring.
5. `12_doodle_labs_radio.md` — radio configuration. Done before first boot
   so the Pi can be verified end-to-end against the radio link in step 6.
6. `13_frontseat_first_boot.md` — Raspberry Pi image, hostname, network,
   basic bring-up.
7. `14_um982_gps.md` — UM982 GNSS receiver configuration and verification.
8. `15_rc_controller.md` — AT9S Pro / R9DS transmitter and receiver setup.
9. `16_software_build.md` — `moos-ivp-blueboat` clone, build, and systemd
   services.
10. `17_calibration.md` — IMU, magnetometer, and heading-baseline
    calibration.

### Per-boat verification

11. `20_qc_signoff.md` — final pre-deployment checklist.

### Operations

12. `30_field_operations.md` — on-water procedures.

---

## 3. File Index

| File | Status | Purpose |
|---|---|---|
| `00_README.md` | stub | This file. |
| `00_style_guide.md` | stub | Conventions for doc authors. |
| `00_secrets.template.md` | stub | Credential keys, no values. |
| `00_secrets.md` *(gitignored)* | — | Real credential values, local-only. |
| `01_fleet_and_network_reference.md` | stub | Fleet inventory, IPs, network architecture. |
| `02_shoreside_infrastructure.md` | stub | RB5009, wAP ax, Starlink, shore radio. |
| `10_mechanical_assembly.md` | stub | Hulls, rails, mounts, passthroughs. |
| `11_electrical_wiring.md` | stub | Power, signal, data wiring. |
| `12_doodle_labs_radio.md` | stub | DoodleLabs Wearable + Mini-OEM configuration. |
| `13_frontseat_first_boot.md` | stub | Pi bring-up from cloned SD image. |
| `14_um982_gps.md` | stub | UM982 GNSS receiver configuration. |
| `15_rc_controller.md` | stub | AT9S Pro + R9DS setup. |
| `16_software_build.md` | stub | moos-ivp-blueboat build, deploy keys, systemd. |
| `17_calibration.md` | stub | IMU, magnetometer, GPS baseline. |
| `20_qc_signoff.md` | stub | Pre-deployment checklist. |
| `30_field_operations.md` | stub | Launch, mission, recovery. |

Originals from the BlueBoat documentation project are also present in this
folder (un-numbered names). They remain in place as reference while the
numbered docs are filled out, and will be removed once the new flow is
complete.

---

## 4. Authoring

Before editing, read `00_style_guide.md`. The short version:

- Procedures: imperative, numbered steps with verifiable success criteria.
- Context: prose, in a clearly separated section, ahead of any procedure.
- Secrets: reference by key (e.g., `{{PI_DEFAULT_PASSWORD}}`); resolved in
  `00_secrets.md`. Never inline a real password.
- File names: snake_case with numeric prefix.

---

## 5. Status Legend

| Status | Meaning |
|---|---|
| `stub` | File exists; content not yet written. |
| `draft` | Content present but not reviewed; expect changes. |
| `review` | Content present and ready for review. |
| `stable` | Reviewed and considered current. |
