---
status: stub
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# RC Controller (AT9S Pro + R9DS)

How to set up and bind the RadioLink AT9S Pro transmitter and R9DS receiver
to the BlueBoat, including the SBUS wiring to the Navigator hat, the
throttle spring-return modification, and verification against the
`iRCReader` MOOS app.

> **Status: stub.** Content to be lifted from `ATS9Pro.md`, stripped of
> PAVLAB references (the channel-mapping convention itself is unchanged for
> Greece; verify with the team before assuming the lab → Greece migration
> is purely cosmetic).

---

## 1. Overview
_To do._

What this guide produces: a transmitter+receiver pair bound, in SBUS mode,
wired to the Navigator, with `iRCReader` publishing fresh `RC_*` mail to
the MOOSDB. End-to-end mode-switch tested.

## 2. Prerequisites
_To do._

- Mechanical + electrical complete.
- Pi has booted (`13_frontseat_first_boot.md`).
- `moos-ivp-blueboat` built (`16_software_build.md`) so `iRCReader` is
  available.

## 3. Context

### 3.1 Three Independent Must-Haves
_To do._

(1) Receiver wired correctly to Navigator RC IN. (2) Receiver in SBUS mode,
not PWM. (3) Transmitter channel assignments and failsafe values correct.
Plus the throttle spring-return mod (§5) for safe boat operation.

### 3.2 Channel Map
_To do._

Table of CH1–CH9 → physical control. CH6 is the RC/autonomy mode switch
and `iBBNavigatorInterface` reads it specifically.

### 3.3 SBUS Wire Protocol
_To do._

Inverted UART, 100 000 baud, 8E2, 25-byte frames. The Navigator hat
inverts the signal in hardware; a bare Pi GPIO UART won't work without
external inversion.

### 3.4 Connection State Model
_To do._

`RC_FRAME_VALID` (per-frame, no debounce) gates per-cycle commands like
thrust. `RC_CONNECTED` (debounced, 3 good frames to reconnect, 1 bad to
disconnect) gates mode switches. Disconnect fallback values are "operator
unavailable" tokens — consumers must gate on `RC_CONNECTED`.

## 4. Transmitter Setup
_To do._

### 4.1 Power and Battery
_To do._

8×AA option. Power on with the front rocker switch; confirm model memory
slot is the BlueBoat profile before binding.

### 4.2 Channel Assignment
_To do._

Mode → Basic → System → CH-SELECT (match receiver channel count).
Mode → Basic → AUX-CH:

- CH5 → top-left big 3-position switch.
- CH6 → top-left small 2-position switch (mode switch).
- CH7 → top-left big 2-position switch.
- CH8 → top-right big 3-position switch.
- CH9 → top-right small 2-position switch.

Verify each on the Monitor screen.

### 4.3 Failsafe
_To do._

Mode → Basic → FAIL SAFE. Capture with sticks centered, throttle at zero.
Switches: HOLD or F/S to lowest position. Re-verify after the spring mod
(§5).

## 5. Throttle Spring-Return Modification
_To do._

> **Critical.** Out of the box the left stick is ratcheted. For boat
> operation it must spring-center to zero throttle.

Step-by-step:

1. Power off; remove battery.
2. Unscrew back cover; track screws by location.
3. Locate left stick gimbal; identify ratchet arm on up/down axis.
4. Back out the ratchet tensioning screw until disengaged.
5. Install centering spring + lever arm on the up/down axis.
6. Reassemble; power on; verify on Monitor that CH3 returns to mid (~992
   raw / 0 % scaled) when released.
7. Re-capture failsafe (§4.3) since the centering point may have shifted.

> **Tip.** Photograph each step. Gimbal hardware is small and order-
> sensitive on reassembly.

## 6. Receiver Setup

### 6.1 SBUS Mode
_To do._

Double-press the ID SET button within ~1 s. LED color: solid red = PWM
(wrong), purple/red+blue = SBUS+PWM (correct). Non-volatile.

### 6.2 Bind to Transmitter
_To do._

1. Power both within 50 cm.
2. Hold receiver ID SET >1 s, release.
3. Wait for solid LED.
4. Power-cycle both; confirm LED comes up solid on next boot.
5. If receiver came up in PWM after binding (firmware-dependent),
   re-toggle SBUS per §6.1.

### 6.3 Wire to Navigator
_To do._

3-pin servo lead from receiver SBUS pin to Navigator RC IN. Match colors
both ends (SIG/+5V/GND). Verify polarity before powering on — reversed
+5V/GND will damage the receiver. Confirm Navigator back-side jumper is in
SBUS position (factory default).

## 7. Verification
_To do._

On the Pi:

```bash
uXMS RC_CONNECTED RC_FRAME_VALID RC_CH3 RC_CH6
```

Expect: `RC_CONNECTED=true`, `RC_CH3` changes with throttle, `RC_CH6`
flips with the mode switch.

Bench-test the spring-return: with motors safed, move throttle forward,
release — `RC_CH3` should return to ~0.

Bench-test failsafe: power off TX; expect `RC_FAILSAFE=true` and
`RC_CH3=0` on the appcast.

Range test on the water before any real mission.

## 8. Troubleshooting
_To do._

(Migrate the symptom table from `ATS9Pro.md` §8.)

## 9. Quick Reference
_To do._

(Migrate the reference card from `ATS9Pro.md` §9.)
