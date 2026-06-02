---
status: draft
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# RC Controller (AT9S Pro + R9DS)

How to set up and bind the RadioLink AT9S Pro transmitter and R9DS receiver to
the BlueBoat, including the SBUS wiring to the Navigator hat, the throttle
spring-return modification, and verification against the `iRCReader` MOOS app.

For deep `iRCReader` / SBUS internals, the source of truth is the code:
`moos-ivp-blueboat/src/iRCReader/` and `src/01_libraries/lib_sbus/`.

---

## 1. Overview

This guide produces a transmitter+receiver pair bound, in SBUS mode, wired to
the Navigator, with `iRCReader` publishing fresh `RC_*` mail to the MOOSDB and
the mode switch tested end-to-end. The R9DS outputs SBUS into the Pi's UART
(`/dev/ttyS0`) via the Navigator hat; `iRCReader` decodes it and publishes
per-channel `RC_CH*` values that `iBBNavigatorInterface` consumes.

## 2. Prerequisites

- Mechanical and electrical assembly complete.
- The Pi has booted ([`13_frontseat_first_boot.md`](13_frontseat_first_boot.md)).
- `moos-ivp-blueboat` built ([`16_software_build.md`](16_software_build.md)) so
  `iRCReader` is available.

## 3. Context

### 3.1 Three Independent Must-Haves

Three things must all be right, plus the throttle mod: (1) the receiver wired
correctly to Navigator RC IN, (2) the receiver in SBUS mode (not PWM), and
(3) the transmitter channel assignments and failsafe values correct. The
throttle spring-return modification (§5) is required for safe boat operation.

### 3.2 Channel Map

Channel numbers are **fixed**: `iRCReader` hard-codes the mapping between
control type (3-pos vs 2-pos) and channel number, and `iBBNavigatorInterface`
reads CH6 as the RC/autonomy mode switch. Do not reassign channel numbers — the
switch *labels* below are the human-facing names; the channel-to-control
binding is set in firmware.

| Channel | Control | Type | Name (function · hardware label) | `RC_CH*` range |
|---|---|---|---|---|
| CH1 | Right stick L/R | stick | **STEERING** | ±100 |
| CH2 | Right stick F/B | stick | — (unassigned) | ±100 |
| CH3 | Left stick F/B | stick | **THROTTLE** (needs spring-return mod, §5) | ±100 |
| CH4 | Left stick L/R | stick | — (unassigned) | ±100 |
| CH5 | switch | 3-position | unassigned (**SWE**) | 1–3 |
| CH6 | switch | 2-position | **MODE** — RC / autonomy (**SWA**) | 1–2 |
| CH7 | switch | 2-position | unassigned (**SWB**) | 1–2 |
| CH8 | switch | 3-position | unassigned (**SWC**) | 1–3 |
| CH9 | switch | 2-position | unassigned (**SWD**) | 1–2 |

> **Note.**  Of the AUX switches, only **SWA (CH6, MODE)** has
> a function in the boat software today — `iBBNavigatorInterface` reads `RC_CH6`
> to flip between RC and autonomy. SWB/SWC/SWD/SWE are mapped to channels but are
> reserved (no consumer yet).

### 3.3 SBUS Wire Protocol

SBUS is an inverted UART at 100000 baud, 8E2, in 25-byte frames. The Navigator
hat inverts the signal in hardware; a bare Pi GPIO UART will not work without
external inversion.

### 3.4 Connection State Model

`RC_FRAME_VALID` (per-frame, no debounce) gates per-cycle commands like thrust.
`RC_CONNECTED` (debounced — 3 good frames to reconnect, 1 bad frame to
disconnect) gates mode switches. The disconnect fallback values are "operator
unavailable" tokens, so consumers must gate on `RC_CONNECTED` rather than trust
a stale `RC_CHx` as fresh input.

## 4. Transmitter Setup

### 4.1 Power and Battery

Power on with the front rocker switch (8×AA option). Confirm the model-memory
slot is the BlueBoat profile before binding.

### 4.2 Channel Assignment

1. **Mode → Basic → System → CH-SELECT** — match the receiver channel count.
2. **Mode → Basic → AUX-CH** — assign CH5–CH9 to their switches per the §3.2
   channel map. (Channel numbers are fixed; only confirm each channel lands on
   the intended switch.)
3. Verify each assignment on the **Monitor** screen — toggle each switch and
   confirm the matching channel bar moves.

### 4.3 Failsafe

**Mode → Basic → FAIL SAFE.** Capture with sticks centered and throttle at
zero. Set switches to HOLD or F/S at the lowest position. Re-verify after the
spring mod (§5).

## 5. Throttle Spring-Return Modification

> **Critical.** Out of the box the left stick is ratcheted. For boat operation
> it must spring-center to zero throttle.

1. Power off; remove the battery.
2. Unscrew the back cover; track screws by location.
3. Locate the left-stick gimbal; identify the ratchet arm on the up/down axis.
4. Back out the ratchet tensioning screw until disengaged.
5. Install the centering spring + lever arm on the up/down axis.
6. Reassemble; power on; verify on Monitor that CH3 returns to mid (~992 raw /
   0 % scaled) when released.
7. Re-capture failsafe (§4.3) — the centering point may have shifted.

> **Tip.** Photograph each step. Gimbal hardware is small and order-sensitive
> on reassembly.

## 6. Receiver Setup

### 6.1 SBUS Mode

Double-press the ID SET button within ~1 s. LED color: solid red = PWM
(wrong); purple / red+blue = SBUS+PWM (correct). The setting is non-volatile.

### 6.2 Bind to Transmitter

1. Power both within 50 cm.
2. Hold the receiver ID SET button >1 s, then release.
3. Wait for a solid LED.
4. Power-cycle both; confirm the LED comes up solid on the next boot.
5. If the receiver came up in PWM after binding (firmware-dependent), re-toggle
   SBUS per §6.1.

### 6.3 Wire to Navigator

Run a 3-pin servo lead from the receiver SBUS pin to Navigator RC IN, matching
colors at both ends (SIG / +5 V / GND). Confirm the Navigator back-side
jumper is in the SBUS position (factory default).

## 7. Verification

On the Pi:

```bash
uXMS RC_CONNECTED RC_FRAME_VALID RC_CH3 RC_CH6
```

Expect `RC_CONNECTED=true`, `RC_CH3` changing with throttle, and `RC_CH6`
flipping with the MODE switch.

- **Spring-return:** with motors safed, move the throttle forward and release —
  `RC_CH3` should return to ~0.
- **Failsafe:** power off the TX; expect `RC_FAILSAFE=true` and `RC_CH3=0` on
  the appcast.
- **Range:** range-test on the water before any real mission.

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `RC_CONNECTED` stays false, no frames | Receiver in PWM mode | Double-press ID SET to toggle SBUS (§6.1). |
| `RC_CONNECTED` false but receiver LED solid | Navigator protocol jumper in UART position | Move the jumper to SBUS position (§6.3). |
| Channel values garbage | Wrong baud/framing on the UART | Confirm `/dev/ttyS0` isn't held by `serial-getty`; check the `sbus_handler` warning in the appcast. |
| `RC_CH6` reads 1 but switch is in position 2 | Switch on wrong channel | Re-verify AUX-CH assignments (§4.2). |
| Throttle stays put after release | Ratchet still engaged | Do the spring-return mod (§5). |
| Boat moves after dropping the TX | Failsafe unset or captured non-zero throttle | Re-do failsafe with throttle centered (§4.3); confirm `RC_FAILSAFE=true` with TX off. |
| `RC_CONNECTED` flickers true↔false | Marginal link (asymmetric hysteresis) | Improve antenna placement / range. |
| Receiver won't bind | TX channel mode mismatch | Set CH-SELECT to match the receiver channel count, then bind. |

## 9. Quick Reference

- **Hardware:** AT9S Pro TX, R9DS RX (SBUS mode), Pi 4 + Navigator hat,
  `/dev/ttyS0` @ 100000 8E2 inverted.
- **Receiver SBUS:** double-press ID SET within 1 s (purple / red+blue LED).
- **Bind:** power both within 50 cm → hold R9DS ID SET >1 s → wait for solid LED.
- **Wiring:** R9DS SBUS pin → Navigator RC IN (SIG / +5 V / GND); back-side
  jumper in SBUS position.
- **Key MOOS vars:** `RC_FRAME_VALID` (gates thrust), `RC_CONNECTED` (gates
  mode), `RC_CH1`–`RC_CH4` (sticks ±100), `RC_CH5`–`RC_CH9` (switches),
  `RC_FAILSAFE`.
- **Health check:** `uXMS RC_CONNECTED RC_FRAME_VALID RC_CH3 RC_CH6`.

## 10. Needs from Builder

Switch labels and channel mapping are confirmed (§3.2). Remaining open items:

- [ ] Document the MODE switch (SWA) orientation — out / up = autonomy in/down = manual
- [ ] Assign functions to the reserved switches (SWE/SWB/SWC/SWD) if/when the
      software starts consuming them; update §3.2 when it does.

## 11. Change Log

Append-only log of changes to this procedure. One line per change: date —
change — author.

- 2026-06-02 — Initial draft (Greece-only) from the legacy AT9S Pro guide.
  Channel map reworked to a function + hardware-label naming scheme; CH6=MODE
  filled, remaining switch functions/labels/positions flagged in §10. — JWenger
