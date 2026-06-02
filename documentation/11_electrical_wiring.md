---
status: stub
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# Electrical Wiring

Power, signal, and data wiring for a mechanically assembled boat. Picks up
from `10_mechanical_assembly.md` and leaves the boat ready for first boot
(`13_frontseat_first_boot.md`).

> **Status: stub.** Content to be lifted from `QC_Build_Checklist.md`
> (electrical section), expanded into step-by-step instructions with
> diagrams, with the checkbox items moved to `20_qc_signoff.md`.

---

## 1. Overview
_To do._

What this guide produces: a wired boat with clean power delivery, the
E-stop in the safety loop, all data connections terminated, and the radio
powered but not yet configured. Radio configuration is `12_doodle_labs_radio.md`.

## 2. Prerequisites
_To do._

Mechanical assembly complete. Tools (soldering iron, heat-shrink gun,
crimper, multimeter, connectivity tester). Parts (XT60s, JST connectors,
buck converters, fuses, e-tape, waterproof heat-shrink).

## 3. Context

### 3.1 Cable Management Principles
_To do._

Strain relief, no daisy-chaining on the radio power line, twisted pairs for
power runs, AWG sizing rationale. These boats are not handled gently —
build for it.

### 3.2 E-stop Safety Topology
_To do._

How the E-stop interrupts main power: 3-pin signal cable through the
contact block as an NC contact, spliced into the blue power wire so the
switches sit in series. Boat should not power on with E-stop disconnected.

### 3.3 Power Tree
_To do._

Diagram showing main battery → contactor → bus → XT60 splitters per
pontoon → loads. Buck converters annotated with input/output voltage and
fuse rating.

### 3.4 Data Path
_To do._

Diagram showing Pi (frontseat) USB ↔ USB-Ethernet adapter ↔ DoodleLabs EVK
board ↔ N-type antennas, plus Pi ↔ Navigator hat ↔ Bulgin ethernet to PABLO
plate.

## 4. Safety Wiring (E-stop)
_To do._

Step-by-step:

1. Wire the 3-pin signal cable to the contact block (verify NC pins).
2. Splice the 3-pin signal bulkhead into the blue power wire so the
   switches are in series.
3. Confirm the boat will not power on without the E-stop connected
   (verification in §9.1).
4. Seal solder joints with heat-shrink.

## 5. Main Power Path
_To do._

Step-by-step:

1. Connect the blue switch connector (2-pin JST) to the main power
   contactor; verify seating.
2. Inspect and seal all power-path solder joints.

## 6. Payload Power Delivery
_To do._

Step-by-step:

1. Terminate payload power #1 (3-pin power) as an XT60 using the black and
   red wires.
2. Terminate payload power #2 (3-pin power) as an XT60 using the black and
   red wires.
3. Install the XT60 Y-splitter for the starboard pontoon, connected to
   payload power #1.
4. Install the XT60 Y-splitter for the port pontoon, connected to payload
   power #2.

## 7. Radio Power
_To do._

Step-by-step:

1. Wire the 5 V buck converter for the DoodleLabs radio with a 2 A fuse on
   the battery-voltage side.
2. Wire the 5 V output of the buck converter into the DoodleLabs EVK board
   (confirm polarity per `12_doodle_labs_radio.md` §4.2 — 5 V only, no
   reverse-polarity protection).
3. Mount the buck converter close to the radio with short, twisted wires.

## 8. Data Wiring
_To do._

Step-by-step:

1. Run the 6 ft Ethernet cable through the cross tube; terminate into the
   DL EVK board.
2. Connect both antennas to the DL push-to-connect ports with strain relief.
3. Connect both antennas to the N-type bulkhead connectors. Verify both
   antennas are fully seated **before powering on**.
4. Connect the USB→Ethernet adapter to the 6 ft Ethernet cable; wrap in
   e-tape; plug into the Pi's upper USB 3.0 port.
5. Run the USB 3.0 cable through the cross tube; connect the UM982 data
   port to the Pi's lower USB 3.0 port.
6. Confirm UM982 antennas 1 and 2 are labeled; connect to the appropriate
   SMA ports.
7. Terminate the 8-pin Ethernet port as RJ45; run a connectivity test;
   connect to the Navigator's main Ethernet port.
8. Splice the Bulgin → Blue Trail Ethernet cable with waterproof
   heat-shrink; run a connectivity test.

## 9. Verification

### 9.1 E-stop Interlock
_To do._

Procedure: with E-stop disconnected, attempt to power on — boat should not
power. With E-stop connected and engaged, boat should not power. With
E-stop connected and released, boat should power normally.

### 9.2 Power Rail Voltages
_To do._

Measure at the buck converter outputs, at each pontoon's XT60 splitter,
and at the radio EVK input. Tolerances and expected values.

### 9.3 Data Connectivity
_To do._

Cable-level connectivity tests for each Ethernet run before applying boat
power.

## 10. Troubleshooting
_To do._

Common wiring issues: boat won't power on with E-stop OK (check contactor
JST seating), radio won't boot (check buck converter polarity and fuse),
intermittent backseat link (check Bulgin splice).
