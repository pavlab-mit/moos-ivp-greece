---
status: draft
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-04
owner: TBD
---

# Mechanical Assembly

How to assemble a Greece BlueBoat from kit to a structurally complete vehicle
ready for electrical wiring (`11_electrical_wiring.md`).

---

## 1. Overview

This guide takes a BlueBoat from kit parts to a structurally complete hull:
crossbars, crosstube, weedless propellers, rails and plates, sensor and radio
mounts, and all bulkhead passthroughs installed and sealed. It stops short of any
electrical work — no wiring, termination, or power-on happens here. When this
guide is complete the boat is mechanically finished and ready for
`11_electrical_wiring.md`.

It is written for the person building a boat at the bench. Verification
criteria appear in §8; the formal sign-off checkboxes live in
[`20_qc_signoff.md`](20_qc_signoff.md).

## 2. Prerequisites

**Tools.** The BlueBoat hex drivers/keys (2.5 mm, 4 mm, 5 mm), the two
BlueBoat wrenches, an M10/M14 bulkhead wrench, RTV sealant, dielectric grease,
and molycoat (anti-seize). The kit's Molykote 111 is used on the crosstube
O-rings.

**Parts.** The stock BlueBoat kit (frame crossbars and brackets, crosstube
with C-nuts and -129 O-rings, weedless propellers (LH/RH), sticker set, and
battery Velcro strips), plus the Greece additions: 8020 rails and end caps,
PABLO plate, GPS antenna mounts, E-stop, the DoodleLabs adapter plate with heat
sink and buck converter, and the Unicore (UM982) module.

Confirm the full kit is present against the parts inventory before starting.
Specific part numbers, sources, and fastener specs are collected in §10. The
stock-boat assembly steps follow the Blue Robotics
[BlueBoat Assembly Guide](https://bluerobotics.com/learn/blueboat-assembly/).

## 3. Context

### 3.1 Why Sealing and Strain Relief Matter

These boats operate in salt water, under sun, and are not handled gently in
transport or launch. Every fastener and passthrough is a potential ingress
point, so passthroughs are coated with molycoat (to prevent galling and to
seal the threads) and exposed contacts get a light layer of dielectric grease
(to resist corrosion). The E-stop is sealed internally with RTV plus
dielectric grease because it sits exposed at the stern. Batteries are held
with Velcro strips so they cannot shift under wave loading yet remain
serviceable. Assume anything not positively secured will eventually work loose.

### 3.2 Passthrough Layout

The hull has four M14 passthroughs (one at each corner) and two banks of M10
passthroughs (port and starboard). Each carries a specific cable; the full
assignment is in §7. A labeled top-down photo of the as-built passthrough
layout should be added here (see §10).

## 4. Hull and Default Configuration (Blue Robotics Build Guide)

Follow the Blue Robotics
[BlueBoat Assembly Guide](https://bluerobotics.com/learn/blueboat-assembly/);
the specs below are the values to hold to.

1. Join the hulls to the frame. Tighten all twelve M6 flanged button head
   screws (four M6x14 under the brackets, eight M6x20) to ¼–½ turn past snug.
2. Install the crosstube: apply Molykote 111 to the two -129 O-rings and seat
   one in each barb groove, insert the STBD/PORT cable ends into the rear of
   each hull, thread the C-nuts onto the barbs and tighten with the two
   BlueBoat wrenches, then secure the crosstube to the rear crossbar with the
   hook-and-loop strap.
3. Install the weedless propellers with their M3x8 socket head cap screws —
   LH on the port M200 motor, RH on the starboard — into the threaded holes
   (not the rotor ventilation holes). Confirm each is fully seated.
4. Apply the sticker set: propeller caution stickers above each propeller, the
   on/off sticker by the starboard power switch, and the identification sticker
   in the starboard hatch-lid depression.
5. Apply battery Velcro strips around each end of every battery.

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

Carries the 60″ coax (N-type). Seat, hand-tighten the C-nut with the bulkhead
wrench, molycoat, and grease the exposed contact.

### 7.2 Rear-Right M14 — Nav Light

Carries the nav light cable. Seat, hand-tighten the C-nut with the bulkhead
wrench, molycoat.

### 7.3 Front-Left M14 — Potted GPS Passthrough

The potted GPS passthrough. Seat and hand-tighten the C-nut with the bulkhead
wrench; do not disturb the potting.

### 7.4 Rear-Left M14 — 12/24″ Coax / N-type

Carries the 12/24″ coax (N-type). Seat, hand-tighten the C-nut with the
bulkhead wrench, molycoat, and grease the exposed contact.

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

- Frame: all twelve M6 screws at ¼–½ turn past snug; hulls hold position with
  no flex at the brackets.
- Crosstube: C-nuts tight, no rotation on the barbs; hook-and-loop strap
  secured to the rear crossbar.
- Propellers: correct hand per side (LH port, RH starboard), M3x8 screws tight,
  fully seated.
- Passthroughs: every bulkhead C-nut hand-tight with the bulkhead wrench, no
  rotation when a cable is attached; exposed contacts greased.
- E-stop test-fit (mechanical only; the full electrical test is in
  [`11_electrical_wiring.md` §9.1](11_electrical_wiring.md#91-e-stop-interlock)).
- No play in the radio or Unicore mounts.

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Hulls wont remain vertical | tension on cam clamps not set correctly | tighten the backing nut on the cam clamps, re-tighten set screw |
| Passthrough spins when attaching cable | passthrough was not appropriately tightened | Back out, inspect threads, and seal, tighten appropriately |

## 10. Needs from Builder

Open items that only the person building the boat can supply. Fill these in as
the build is documented:

- [ ] Part numbers and sources for all kit parts (§2).
- [ ] Fastener specs for the Greece additions (8020 rails, PABLO plate, sensor
      and radio mounts) — the stock-boat specs are in §4.
- [ ] Specific RTV / dielectric grease / molycoat products used.
- [ ] Labeled top-down passthrough-layout photo or diagram (§3.2).
- [ ] As-built photos for the key assembly steps (crosstube seal, E-stop
      sealing, radio/Unicore mounts, passthroughs).
- [ ] Confirm the "battery balance lead" assignment on the Left M10 Right
      position (carried over from the checklist with a query).

## 11. Change Log

Append-only log of changes to this procedure. One line per change: date —
change — author.

- 2026-06-02 — Initial draft; mechanical steps converted to prose from
  `QC_Build_Checklist.md`, using Blue Robotics
  [BlueBoat Assembly Guide](https://bluerobotics.com/learn/blueboat-assembly/)
  terminology (crossbars, crosstube, weedless propellers, Velcro strips) and
  specs (frame screws ¼–½ turn past snug, bulkhead C-nuts hand-tightened). Open
  items collected in §10. — JWenger
