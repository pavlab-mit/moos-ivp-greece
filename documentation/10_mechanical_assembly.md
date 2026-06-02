---
status: draft
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# Mechanical Assembly

How to assemble a Greece BlueBoat from kit to a structurally complete vehicle
ready for electrical wiring (`11_electrical_wiring.md`).

---

## 1. Overview

This guide takes a BlueBoat from kit parts to a structurally complete hull:
cross bars, cross tube, props, rails and plates, sensor and radio mounts, and
all bulkhead passthroughs installed and sealed. It stops short of any
electrical work — no wiring, termination, or power-on happens here. When this
guide is complete the boat is mechanically finished and ready for
`11_electrical_wiring.md`.

It is written for the person building a boat at the bench. Verification
criteria appear in §8; the formal sign-off checkboxes live in
[`20_qc_signoff.md`](20_qc_signoff.md).

## 2. Prerequisites

**Tools.** Allen keys, a torque driver, RTV sealant, dielectric grease, and
molycoat (anti-seize).

**Parts.** Black cross bars, cross tube, propellers, 8020 rails and end caps,
PABLO plate, GPS antenna mounts, E-stop, the DoodleLabs adapter plate with
heat sink and buck converter, the Unicore (UM982) module, identification
stickers, and battery velcro.

Confirm the full kit is present against the parts inventory before starting.
Specific part numbers, sources, and torque values are collected in §10.

## 3. Context

### 3.1 Why Sealing and Strain Relief Matter

These boats operate in salt water, under sun, and are not handled gently in
transport or launch. Every fastener and passthrough is a potential ingress
point, so passthroughs are coated with molycoat (to prevent galling and to
seal the threads) and exposed contacts get a light layer of dielectric grease
(to resist corrosion). The E-stop is sealed internally with RTV plus
dielectric grease because it sits exposed at the stern. Batteries are held
with velcro so they cannot shift under wave loading yet remain serviceable.
Assume anything not positively secured will eventually work loose.

### 3.2 Passthrough Layout

The hull has four M14 passthroughs (one at each corner) and two banks of M10
passthroughs (port and starboard). Each carries a specific cable; the full
assignment is in §7. A labeled top-down photo of the as-built passthrough
layout should be added here (see §10).

## 4. Hull and Default Configuration (Blue Robotics Build Guide)

1. Secure the black cross bars.
2. Install the cross tube and seal it.
3. Screw on the propellers and confirm they are fully seated and secure.
4. Apply the identification stickers.
5. Attach the velcro for the battery mounts.

## 5. Rails and Plates

1. Mount the 8020 rails with their bushings and confirm they are secure.
2. Install the 8020 end caps.
3. Install the PABLO plate.

## 6. Sensor and Radio Mounts

1. Secure the GPS antenna mounts on the port side.
2. Install the E-stop at the starboard rear and seal it internally with RTV
   and dielectric grease.
3. Install the DoodleLabs radio on its adapter plate together with the heat
   sink and buck converter.
4. Install the Unicore (UM982) module so that it cannot shift.

## 7. Passthroughs

Every passthrough must be tight and secure, coated with a healthy amount of
molycoat. Add a light layer of dielectric grease to any exposed contacts.

### 7.1 Front-Right M14 — 60″ Coax / N-type

Carries the 60″ coax (N-type). Seat, torque, molycoat, and grease the exposed
contact.

### 7.2 Rear-Right M14 — Nav Light

Carries the nav light cable. Seat, torque, molycoat.

### 7.3 Front-Left M14 — Potted GPS Passthrough

The potted GPS passthrough. Seat and torque; do not disturb the potting.

### 7.4 Rear-Left M14 — 12/24″ Coax / N-type

Carries the 12/24″ coax (N-type). Seat, torque, molycoat, and grease the
exposed contact.

### 7.5 Right M10s

| Position | Carries | Connector |
|---|---|---|
| Front | Payload power #1 | 3-pin power |
| Right | On/off switch | — |
| Rear | E-stop | 3-pin signal |
| Left | PABLO Ethernet | 8-pin |

### 7.6 Left M10s

| Position | Carries | Connector |
|---|---|---|
| Front | Payload power #1 | 3-pin power |
| Right | Battery balance lead | 8-pin |
| Rear | Blank | — |
| Left | Blank | — |

## 8. Verification

Before moving to electrical wiring, confirm:

- All fasteners torqued to spec.
- All passthroughs seated and sealed.
- E-stop test-fit (mechanical only; the full electrical test is in
  `11_electrical_wiring.md`).
- No play in the radio or Unicore mounts.

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Hulls wont remain vertical | tension on cam clamps not set correctly | tighten the backing nut on the cam clamps, re-tighten set screw |
| Passthrough spins when attaching cable | passthro was not appropriately tightened | Back out, inspect threads, and seal, tighten appropriately |

## 10. Needs from Builder

Open items that only the person building the boat can supply. Fill these in as
the build is documented:

- [ ] Part numbers and sources for all kit parts (§2).
- [ ] Specific RTV / dielectric grease / molycoat products used.
- [ ] Labeled top-down passthrough-layout photo or diagram (§3.2).
- [ ] As-built photos for the key assembly steps (cross tube seal, E-stop
      sealing, radio/Unicore mounts, passthroughs).
- [ ] Confirm the "battery balance lead" assignment on the Left M10 Right
      position (carried over from the checklist with a query).

## 11. Change Log

Append-only log of changes to this procedure. One line per change: date —
change — author.

- 2026-06-02 — Initial draft; mechanical steps converted to prose from
  `QC_Build_Checklist.md`, open items collected in §10. — JWenger
