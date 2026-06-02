# PAVLAB RadioLink AT9S Pro RC Controller Guide

> **Radios covered:** RadioLink AT9S Pro transmitter · RadioLink R9DS receiver
> **MOOS app:** `iRCReader` (reads SBUS, publishes `RC_CH*` to MOOSDB)
> **Host board:** Raspberry Pi 4 + Blue Robotics Navigator hat
> **Last updated:** June 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Hardware at a Glance](#2-hardware-at-a-glance)
3. [Transmitter (AT9S Pro)](#3-transmitter-at9s-pro)
   - [Layout](#31-layout)
   - [Power and Charging](#32-power-and-charging)
   - [Channel Map (PAVLAB)](#33-channel-map-pavlab)
   - [Throttle Spring-Return Modification](#34-throttle-spring-return-modification)
   - [Failsafe Configuration](#35-failsafe-configuration)
4. [Receiver (R9DS)](#4-receiver-r9ds)
   - [Setting the Receiver to SBUS Mode](#41-setting-the-receiver-to-sbus-mode)
   - [Binding to the Transmitter](#42-binding-to-the-transmitter)
   - [Receiver Wiring to the Navigator Board](#43-receiver-wiring-to-the-navigator-board)
5. [SBUS Protocol Notes](#5-sbus-protocol-notes)
6. [iRCReader MOOS Application](#6-ircreader-moos-application)
   - [What It Does](#61-what-it-does)
   - [MOOS Configuration Block](#62-moos-configuration-block)
   - [Published Variables](#63-published-variables)
   - [Connection State Model](#64-connection-state-model)
   - [Disconnected Fallback Values](#65-disconnected-fallback-values)
   - [Downstream Consumers](#66-downstream-consumers)
   - [AppCast Report](#67-appcast-report)
7. [First-Time Setup Procedure](#7-first-time-setup-procedure)
8. [Troubleshooting](#8-troubleshooting)
9. [Quick Reference Card](#9-quick-reference-card)

---

## 1. Overview

PAVLAB uses a **RadioLink AT9S Pro** 2.4 GHz transmitter paired with a **RadioLink R9DS** receiver to provide direct manual control of the Blue Boat. The receiver outputs SBUS over a serial line into the Raspberry Pi's primary UART (`/dev/ttyS0`) by way of the Blue Robotics Navigator hat, and the `iRCReader` MOOS app decodes the stream and publishes per-channel values to the MOOSDB. Downstream apps — notably `iBBNavigatorInterface` — gate manual thrust on RC link freshness and use the channel-6 mode switch to flip the boat between RC and autonomy modes.

There are three distinct things that must be true for the system to work end-to-end:

1. The receiver must be wired correctly to the Navigator's RC input (§4.3).
2. The receiver must be in SBUS mode, not PWM (§4.1).
3. The transmitter must be set to the right channel assignments (§3.3) and the right failsafe values (§3.5).

A fourth, ergonomic must-have for boat operations is the throttle spring-return mod (§3.4): out of the box the AT9S Pro left stick is ratcheted, which is wrong for boat use because letting go of the stick leaves the throttle wherever you last set it instead of centering it to zero thrust.

---

## 2. Hardware at a Glance

| Component | Model | Role |
|---|---|---|
| Transmitter | RadioLink AT9S Pro | 2.4 GHz DSSS+FHSS, 10 ch (switchable to 12), 2.8″ color LCD, 8x AA batteries |
| Receiver | RadioLink R9DS | 9 PWM / 10 SBUS+PWM, 3.6–12 V, 43×24×15 mm    |
| Host board | Raspberry Pi 4 + Blue Robotics Navigator | Reads SBUS on `/dev/ttyS0`, runs `iRCReader` |
| Cable | 3-pin servo lead | SBUS signal, +5 V, GND, receiver → Navigator RC IN |

The AT9S Pro / R9DS combination supports up to 12 channels; PAVLAB uses 9 of them (4 sticks + 5 switches) plus the two SBUS digital flags (CH17 / CH18) when assigned.

---

## 3. Transmitter (AT9S Pro)

### 3.1 Layout

```
   AT9S Pro — Top-Down View

    ┌─────────────────────────────────────────────┐
    │   [CH5 3-pos]                  [CH8 3-pos]  │  ← Top corners: big switches
    │   [CH6 2-pos sm] [CH7 2-pos lg]             │
    │                                [CH9 2-pos sm]│
    │                                              │
    │   ┌───────────────────────────────────────┐ │
    │   │            2.8" Color LCD             │ │
    │   └───────────────────────────────────────┘ │
    │                                              │
    │     ┌─────┐                    ┌─────┐      │
    │     │ L   │                    │  R  │      │
    │     │stick│                    │stick│      │
    │     │CH3/4│                    │CH1/2│      │
    │     └─────┘                    └─────┘      │
    │                                              │
    │   [Trim]   [VR knobs]   [Sliders]   [Trim]  │
    └─────────────────────────────────────────────┘
```

| Control | Channel | Type |
|---|---|---|
| Right stick L↔R | CH1 | Joystick, ±100% |
| Right stick F↔B | CH2 | Joystick, ±100% |
| Left stick F↔B | CH3 | Joystick (throttle), ±100% |
| Left stick L↔R | CH4 | Joystick, ±100% |
| Top-left big switch | CH5 | 3-position |
| Top-left small switch | CH6 | 2-position |
| Top-left big switch (other) | CH7 | 2-position |
| Top-right big switch | CH8 | 3-position |
| Top-right small switch | CH9 | 2-position |

This is the mapping the `iRCReader` app expects — see §3.3 for how to set it on the transmitter and §6.3 for the published `RC_CH*` variables.

### 3.2 Power and Charging

Some AT9S Pro have a built-in **3S 1800 mAh Li-ion** pack with a JST 2-pin lead. Advertised runtime is roughly 12 hours of continuous use. The same JST connector accepts 8×AA or 2S–4S LiPo/LiFe, the lab opts for the AA battery option.

Power on with the front rocker switch. The boot screen shows the current model memory slot — confirm it is the Blue Boat profile before binding.

### 3.3 Channel Map (PAVLAB)

The R9DS receiver is a 9-channel SBUS receiver. PAVLAB uses CH1–CH9. The remaining channels (CH10–CH16) come through as raw SBUS values but are not interpreted by `iRCReader`.

**Required setup on the AT9S Pro:**

1. Power on the transmitter.
2. Go to **Mode → Basic → System → CH-SELECT** and confirm channel count matches the receiver. The R9DS bundled with AT9S Pro is a 9-channel SBUS receiver; verify the transmitter is in the matching mode.
3. Go to **Mode → Basic → AUX-CH** (auxiliary channel assignment) and assign:
   - CH5 → top-left **3-position** switch
   - CH6 → top-left **small 2-position** switch (the mode switch — see §6.6 below)
   - CH7 → top-left **big 2-position** switch
   - CH8 → top-right **big 3-position** switch
   - CH9 → top-right **small 2-position** switch
4. Verify the assignments by going to the **Monitor** screen and toggling each switch — you should see the corresponding channel bar move.

**Why the assignments matter.** `iRCReader` hard-codes the mapping between physical control type (3-pos vs 2-pos) and channel number (see `RCReader.cpp`). If the wrong physical control is on CH5–CH9, the published `RC_CH5–RC_CH9` values won't represent what the operator expects, and downstream consumers — in particular `iBBNavigatorInterface`, which reads `RC_CH6` as the RC/autonomy mode switch — will misbehave.

### 3.4 Throttle Spring-Return Modification

> **Why this matters.** Out of the box the AT9S Pro's left stick (CH3 throttle) is **ratcheted** — when you let go, it stays put. For boat operation you want it **spring-centered** to zero thrust so releasing the stick stops the boat. This is the same convention used by aircraft rudder/aileron sticks and is non-negotiable for safe manual operation.

The modification is internal to the transmitter and requires partially disassembling the case. It involves **adding a centering spring and a lever arm** to the throttle gimbal — these parts are not normally installed at the factory.

**High-level procedure:**

1. Power off the transmitter and remove the battery.
2. Unscrew the back cover. Note the screw sizes/locations as you go — they are not all the same length.
3. Locate the left stick gimbal assembly. The throttle ratchet is a small metal arm that bears against a toothed wheel on the up/down axis.
4. **Disable the ratchet** — back out the ratchet tensioning screw until the arm no longer engages the wheel.
5. **Install the centering spring and lever arm** onto the up/down axis of the gimbal. The spring's two ends should anchor against a fixed point on the gimbal frame and against the moving lever arm so that the lever rests in the center position when the stick is released.
6. Reassemble the case, power on, and verify on the **Monitor** screen that the throttle channel returns to its midpoint (~992 raw / 0% scaled) when you release the stick.
7. If the throttle still doesn't center cleanly, check that the ratchet screw is fully backed off and that the spring isn't binding on the case.

> **Tip:** Photograph each step during disassembly. The gimbal hardware is small and order-sensitive on reassembly. Keep the removed ratchet hardware — restoring the ratchet later is just the reverse of step 4.

After the mod, also re-verify the failsafe values (§3.5) — taking the transmitter apart can knock CH3 trim slightly off center, which the existing failsafe capture would not reflect.

### 3.5 Failsafe Configuration

The AT9S Pro sets the **transmitter-side** failsafe values that the receiver will fall back to if the RF link drops. The receiver in turn raises the SBUS failsafe flag, which `iRCReader` propagates to MOOSDB as `RC_FAILSAFE`.

**To set failsafe:**

1. **Mode → Basic → FAIL SAFE**.
2. For each channel, choose **HOLD** (keep last value) or **F/S** (use a captured value).
3. To capture a value: move the sticks/switches to the desired safe position, then press the F/S field for that channel — the current value is written.

**Recommended PAVLAB settings:**

| Channel | Failsafe action | Why |
|---|---|---|
| CH1, CH2, CH4 (sticks) | F/S, captured at center | Zero command on lateral/rotational axes |
| CH3 (throttle) | F/S, captured at center (zero thrust) | Boat coasts to a stop, doesn't run away |
| CH5–CH9 (switches) | HOLD or F/S to lowest position | Last operator command, or known-safe default |

The Pi-side parser also independently asserts `RC_FAILSAFE` and zeros out joystick commands when the link is lost (§6.5), so the transmitter failsafe is a second line of defense rather than the primary protection.

---

## 4. Receiver (R9DS)

The R9DS is a small 9/10-channel 2.4 GHz receiver with two antennas, telemetry, and an LED indicator on the case. It powers from 3.6–12 V via any of the channel headers and outputs either PWM (per-channel) or SBUS (single serial line, all channels) depending on its mode.

### 4.1 Setting the Receiver to SBUS Mode

> **Critical.** PAVLAB requires the R9DS in **SBUS** mode. In PWM mode the SBUS pin outputs nothing and `iRCReader` will report no frames.

The R9DS toggles between PWM and SBUS+PWM modes with a **double-press** of the **ID SET** button on the side of the receiver, within ~1 second:

1. With the receiver powered on, find the **ID SET** button (small recessed button on the side).
2. Quickly press it **twice** within one second.
3. Watch the LED:
   - **Red solid** = PWM mode (default from factory)
   - **Purple / red + blue solid** = SBUS + PWM mode (what PAVLAB uses)
4. The mode is non-volatile — it persists across power cycles.

If you ever see the receiver come up in PWM mode after replacing it or after a factory reset, double-press ID SET to flip it back to SBUS.

### 4.2 Binding to the Transmitter

Binding pairs a specific transmitter to a specific receiver so that other AT9S Pro units cannot accidentally drive your boat.

1. Power on both transmitter and receiver, keeping them within ~50 cm of each other.
2. Press and hold the **ID SET** button on the R9DS for **>1 second**, then release.
3. The receiver LED starts flashing.
4. When the LED goes **solid**, binding is complete.
5. Power-cycle both units and confirm the receiver LED comes up solid on next power-on — that means the bind is stored.

If the receiver had been in PWM mode before binding, re-check the SBUS toggle (§4.1) afterward — depending on firmware, binding may reset the output mode.

### 4.3 Receiver Wiring to the Navigator Board

The receiver wires to the **Blue Robotics Navigator** hat's dedicated RC input header with a standard 3-pin servo lead.

```
  R9DS Receiver                            Navigator Hat
  ┌──────────────────┐                    ┌──────────────────┐
  │                  │                    │                  │
  │  SBUS pin ───────┼──── SIG (yellow) ──┼─► RC IN  SIG     │
  │  V+ pin   ───────┼──── +5V (red)   ───┼─► RC IN  +5V     │
  │  GND pin  ───────┼──── GND (black) ───┼─► RC IN  GND     │
  │                  │                    │                  │
  └──────────────────┘                    └──────────────────┘
```

**Wiring rules:**

- Use the receiver's **SBUS output pin**, not one of the PWM channel pins. On the R9DS the SBUS pin is labeled and is separate from CH1–CH9.
- The cable is a standard 3-pin servo lead: signal / V+ / GND. Match the colors at both ends.
- **Power:** the receiver draws 38–45 mA at 5 V. The Navigator's RC IN +5 V rail can supply this directly — no external BEC required for the receiver alone.
- **Polarity matters.** Reversing +5 V and GND will damage the receiver. Verify orientation against the receiver's pin labels before powering on.

**Navigator board protocol jumper.** The Navigator has a back-side jumper that selects between **SBUS (inverted)** and **UART (non-inverted)** signaling on the RC input. PAVLAB uses SBUS, so the jumper must be in the **SBUS** position (this is the factory default). If the jumper has been moved to UART for another project, the receiver will appear to be wired correctly but `iRCReader` will see only garbage — re-solder the jumper to SBUS.

> **Why the inversion matters.** SBUS is conventionally an **inverted** UART signal (idle low). The Pi's hardware UART expects non-inverted (idle high). The Navigator's RC input includes a hardware inverter on the SBUS path, which is why a bare Pi GPIO UART wired straight to a receiver won't work without external inversion hardware.

After wiring and powering on, the R9DS LED should be solid (bound, SBUS mode). On the Pi, `iRCReader` should start publishing `RC_FRAME_VALID=true` and `RC_CONNECTED=true` within a few seconds of the transmitter being powered on.

---

## 5. SBUS Protocol Notes

SBUS is Futaba's serial RC-data protocol, adopted by RadioLink and most modern receiver manufacturers. The Pi-side parser (`sbus_handler.cpp`) implements the protocol directly over `/dev/ttyS0`.

| Parameter | Value |
|---|---|
| Baud rate | **100,000** (non-standard; the parser uses a Linux `TCSETS2` ioctl to set this) |
| Framing | **8E2** (8 data bits, even parity, 2 stop bits) |
| Signal level | Inverted UART (idle low) — the Navigator handles this in hardware |
| Frame size | 25 bytes |
| Frame rate | ~70 Hz (analog mode); ~14 ms per frame |
| Start byte | `0x0F` |
| End byte | `0x00` (also `0x04`, `0x14`, `0x24`, `0x34` for SBUS2 telemetry slots) |
| Channels | 16 × 11-bit proportional + 2 × 1-bit digital |
| Channel raw range | 172–1812 (corresponds to ~880–2120 µs PWM); mid = 992 |
| Flags byte (byte 23) | bit 0: CH17, bit 1: CH18, bit 2: frame-lost, bit 3: failsafe |

The 11-bit channel values are bit-packed across bytes 1–22 of the frame. The parser rejects any frame where any channel value falls outside the [172, 1812] canonical Futaba range — this catches misaligned/corrupted frames.

---

## 6. iRCReader MOOS Application

### 6.1 What It Does

`iRCReader` opens `/dev/ttyS0`, starts a dedicated reader thread that pulls SBUS frames at full rate (~70 Hz), and on each MOOS iteration publishes the latest decoded channel values and connection state to the MOOSDB. The reader thread and the main MOOS thread share state through a mutex; the reader thread does the parsing, and the MOOS thread does the publishing.

Source layout:

```
src/iRCReader/                         ← MOOS app (this guide's focus)
  ├── main.cpp                         ← CLI entry, --help / --example / --interface
  ├── RCReader.cpp / .h                ← MOOS app: subscriptions, iterate, appcast
  ├── RCReader_Info.cpp / .h           ← Help text (currently sparse)
  └── CMakeLists.txt
src/01_libraries/lib_sbus/             ← SBUS parser library
  ├── sbus_handler.cpp / .h            ← Frame decoding, UART config, hysteresis
  └── (linked into iRCReader)
```

### 6.2 MOOS Configuration Block

From `missions/blueboat_frontseat/plugs/blueboat_fs/plug_iRCReader.moos`:

```
ProcessConfig = iRCReader
{
  AppTick    = 16
  CommsTick  = 16
}
```

That's it — the app reads no other config. The only undocumented optional parameter is:

| Parameter | Default | Effect |
|---|---|---|
| `debug` | `false` | When `true`, writes raw frame-arrival events to a timestamped `.dbg` file in the working directory. Useful for diagnosing receiver-side issues. |

`AppTick = 16` means `Iterate()` runs at 16 Hz, which is the publish rate for `RC_CH*` regardless of the underlying ~70 Hz SBUS frame rate. The reader thread polls the UART every 1 ms and caches the latest values; `Iterate()` snapshots and publishes them.

### 6.3 Published Variables

**On every iteration (whether connected or not):**

| Variable | Type | Description |
|---|---|---|
| `RC_FRAME_VALID` | `"true"/"false"` | Per-frame validity — instantaneous, no debounce. True iff the most recent SBUS frame was free of failsafe / frame-lost flags AND the link is not stale. Gate per-cycle commands (e.g., thrust) on this. |
| `RC_CONNECTED` | `"true"/"false"` | Debounced connection state. Requires **3 consecutive valid frames** (~42 ms at 70 Hz) to flip false→true; flips true→false on a single bad frame. Use this for mode switching, UI, and event logging. |

**Only when `RC_CONNECTED=true`:**

| Variable | Type | Description |
|---|---|---|
| `RC_CH1` | `double` | Right stick L/R, scaled to ±100 |
| `RC_CH2` | `double` | Right stick F/B, scaled to ±100 |
| `RC_CH3` | `double` | Left stick F/B (throttle), scaled to ±100 |
| `RC_CH4` | `double` | Left stick L/R, scaled to ±100 |
| `RC_CH5` | `int (1–3)` | Top-left big 3-position switch |
| `RC_CH6` | `int (1–2)` | Top-left small 2-position switch (**RC/autonomy mode switch**) |
| `RC_CH7` | `int (1–2)` | Top-left big 2-position switch |
| `RC_CH8` | `int (1–3)` | Top-right big 3-position switch |
| `RC_CH9` | `int (1–2)` | Top-right small 2-position switch |
| `RC_CH10` … `RC_CH16` | raw `uint16` (172–1812) | Raw SBUS values, unmapped |
| `RC_CH17` | `"true"/"false"` | SBUS digital flag, bit 0 |
| `RC_CH18` | `"true"/"false"` | SBUS digital flag, bit 1 |
| `RC_FRAME_LOST` | `"true"/"false"` | Receiver-reported frame-lost flag (mirror of SBUS bit 2) |
| `RC_FAILSAFE` | `"true"/"false"` | Receiver-reported failsafe flag (mirror of SBUS bit 3) |

### 6.4 Connection State Model

The SBUS handler tracks two distinct booleans deliberately, because two different consumers want two different semantics:

```
   isFrameValid() ─────► RC_FRAME_VALID   (per-frame, no debounce)
        │                  └─► gates per-cycle commands (thrust)
        │
   isControllerConnected() ─► RC_CONNECTED  (debounced)
        │                       └─► gates mode switches, UI, logging
        ▼
   updateConnectionStatus() ── staleness backstop
        │  Invalidates BOTH if:
        │   - >500 ms since last valid frame, OR
        │   - >20 consecutive frame errors since last good frame
```

The hysteresis is **asymmetric** by design:

- **Disconnect is fast** — one bad frame drops `RC_CONNECTED` to false immediately.
- **Reconnect is slow** — requires 3 consecutive good frames to flip back to true, preventing a flapping link from looking healthy.

### 6.5 Disconnected Fallback Values

When `RC_CONNECTED=false`, `iRCReader` publishes safe defaults rather than withholding mail:

| Channels | Fallback value | Rationale |
|---|---|---|
| `RC_CH1`–`RC_CH4` (joysticks) | `0.0` | Zero thrust / zero command on all axes |
| `RC_CH5`–`RC_CH9` (switches) | `1` (lowest position) | "Operator unavailable" token, not a commanded state |
| `RC_CH10`–`RC_CH16` (raw) | `SBUS_MID_VALUE` (992) | No command bias |

> **Important.** These are *"operator unavailable" tokens*, not commanded positions. Any consumer that needs to **latch** operator state across dropouts MUST gate its reads on `RC_CONNECTED` rather than trusting `RC_CHx` as fresh operator input. `iBBNavigatorInterface` follows this rule for the CH6 mode switch: it ignores `RC_CH6` mail when `RC_CONNECTED=false`, so the safe-default `CH6=1` published here does **not** auto-flip the vehicle out of RC mode on signal loss.

### 6.6 Downstream Consumers

| Consumer | What it reads | What it does |
|---|---|---|
| `iBBNavigatorInterface` | `RC_CH1`–`RC_CH4` (thrust), `RC_CH6` (mode switch), `RC_CONNECTED`, `RC_FRAME_VALID` | Routes manual thrust to the motors when in RC mode; uses CH6 to flip between RC and autonomy. Watchdog (`RC_DEADMAN`) refreshes only on `RC_CONNECTED=true`. |
| `pBB_Health` | `RC_CONNECTED`, `RC_FAILSAFE`, `RC_FRAME_VALID` | Reports RC link state in the boat health summary. |

The deadman behavior is important: the watchdog timestamp is refreshed only on `RC_CONNECTED=true` transitions, so the disconnected-fallback publishes (§6.5) do **not** defeat the watchdog.

### 6.7 AppCast Report

The `iRCReader` appcast (visible in `pMarineViewer` or via `uMS`) shows live state — useful for diagnosing receiver / link issues:

```
============================================
RC Controller Status
============================================
Frame Valid (per-frame):    YES
RC Connected (debounced):   YES

Failsafe Active: NO
Time Since Last Frame: 14.3 ms
Consecutive Frame Losses:   0
Consecutive Good Frames:    1247

Channel | Description               | Raw Value | Mapped Value
--------|---------------------------|-----------|-------------
1       | Right Stick L/R           | 992       | 0.0%
2       | Right Stick F/B           | 992       | 0.0%
3       | Left Stick F/B            | 172       | -100.0%   ← throttle at zero
4       | Left Stick L/R            | 992       | 0.0%
5       | Top Left Switch (3-pos)   | 992       | 2
6       | Top Left Small SW (2-pos) | 172       | 1         ← RC mode
7       | Top Left Big SW (2-pos)   | 172       | 1
8       | Top Right Big SW (3-pos)  | 1812      | 3
9       | Top Right Small SW (2-pos)| 172       | 1
...
Flags:
Channel 17: OFF
Channel 18: OFF
Frame Lost: NO
Failsafe: NO
```

The two most useful numbers when debugging are **Time Since Last Frame** (should stay under ~20 ms in a healthy link) and **Consecutive Frame Losses** (should stay at 0).

---

## 7. First-Time Setup Procedure

Follow this sequence when setting up a new transmitter+receiver pair, or after a major hardware change:

1. **Power on the transmitter.** Confirm the correct model memory slot, battery level, and that all switches read sane positions on the Monitor screen.
2. **Set channel count and assignments** (§3.3). Verify each switch moves the expected channel.
3. **Set failsafe values** (§3.5). Center sticks; capture.
4. **Put the receiver in SBUS mode** (§4.1). Double-press ID SET; verify LED color.
5. **Bind transmitter to receiver** (§4.2). Hold ID SET >1 s; wait for solid LED.
6. **Wire the receiver to the Navigator** (§4.3). Verify polarity; confirm SBUS jumper on Navigator is in the SBUS position.
7. **Power on the boat.** SSH in and check that `iRCReader` is publishing:
   ```bash
   uXMS RC_CONNECTED RC_FRAME_VALID RC_CH3 RC_CH6
   ```
   You should see `RC_CONNECTED=true` and `RC_CH3` changing as you move the throttle stick.
8. **Bench test the throttle spring-return** (§3.4). With the boat's motors **safed**, move the throttle stick fully forward and release — it should snap back to center, and `RC_CH3` should return to ~0.
9. **End-to-end mode switch test.** Toggle the CH6 mode switch and verify the boat transitions between RC and autonomy modes per `iBBNavigatorInterface` behavior.
10. **Range test on the water** before any real mission. Walk the transmitter out to the expected maximum operating range; the appcast should remain healthy throughout.

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `RC_CONNECTED` stays `false`, no frames arriving | Receiver in PWM mode | Double-press ID SET (§4.1) to toggle to SBUS |
| `RC_CONNECTED` stays `false`, but receiver LED is solid | Navigator protocol jumper in UART position | Re-solder the jumper to SBUS position (§4.3) |
| Frames arrive but channel values are garbage | Wrong baud rate / framing on the UART | Confirm `/dev/ttyS0` is not being used by `serial-getty` or another process; check `sbus_handler` initialization warning in the appcast |
| `RC_CH6` reads `1` but switch is in position 2 | Switch assigned to wrong channel on the transmitter | Re-verify AUX-CH assignments (§3.3) |
| Throttle stays where I left it after releasing the stick | Throttle ratchet still engaged | Perform the spring-return mod (§3.4); back out the ratchet screw |
| Boat keeps moving after I drop the transmitter | Failsafe not set, or failsafe captures non-zero throttle | Re-do failsafe with throttle stick **centered** (§3.5); verify with `RC_FAILSAFE=true` on the appcast when the TX is powered off |
| `Time Since Last Frame` climbs while TX is on | RF range limit, interference, or antenna damage | Bring TX closer; inspect antennas; check for 2.4 GHz interference sources (WiFi, microwaves, Doodle Labs mesh) |
| `Consecutive Frame Losses` slowly accumulates | Marginal link or noisy power | Check that receiver power isn't shared with high-current devices (motors); look for ground loops |
| `RC_CONNECTED` flickers true→false repeatedly | Marginal link | Asymmetric hysteresis is biting — link is bad enough that 3 good frames in a row is hard. Improve antenna placement / range |
| Receiver doesn't bind | Transmitter not in correct channel mode | Set CH-SELECT to match the receiver's channel count before binding |
| Throttle returns past center after spring mod | Spring tension uneven or lever arm misaligned | Re-open and re-seat the spring/lever; check that the gimbal isn't binding on case |

---

## 9. Quick Reference Card

```
╔══════════════════════════════════════════════════════════════════╗
║              PAVLAB RC CONTROLLER QUICK REFERENCE                ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  HARDWARE                                                        ║
║  ────────                                                        ║
║  TX:        RadioLink AT9S Pro (2.4 GHz, 10/12 ch)               ║
║  RX:        RadioLink R9DS (SBUS mode)                           ║
║  Host:      Pi 4 + Blue Robotics Navigator hat                   ║
║  UART:      /dev/ttyS0 @ 100000 baud, 8E2, inverted              ║
║                                                                  ║
║  CHANNEL MAP                                                     ║
║  ───────────                                                     ║
║  CH1  Right stick L/R                                            ║
║  CH2  Right stick F/B                                            ║
║  CH3  Left stick F/B  (THROTTLE — needs spring-return mod)       ║
║  CH4  Left stick L/R                                             ║
║  CH5  Top-left big 3-pos switch                                  ║
║  CH6  Top-left small 2-pos switch  ← RC/AUTONOMY MODE            ║
║  CH7  Top-left big 2-pos switch                                  ║
║  CH8  Top-right big 3-pos switch                                 ║
║  CH9  Top-right small 2-pos switch                               ║
║                                                                  ║
║  RECEIVER MODE                                                   ║
║  ─────────────                                                   ║
║  PAVLAB needs SBUS mode (purple/red+blue LED).                   ║
║  Toggle: double-press ID SET on R9DS within 1 second.            ║
║                                                                  ║
║  BIND                                                            ║
║  ────                                                            ║
║  1. Power both within 50 cm                                      ║
║  2. Hold R9DS ID SET button >1 sec, release                      ║
║  3. Wait for solid LED                                           ║
║                                                                  ║
║  WIRING (RX → Navigator)                                         ║
║  ───────────────────────                                         ║
║  R9DS SBUS pin  → Navigator RC IN signal                         ║
║  R9DS V+        → Navigator RC IN +5 V                           ║
║  R9DS GND       → Navigator RC IN GND                            ║
║  Navigator back-side jumper: SBUS position (default)             ║
║                                                                  ║
║  KEY MOOS VARIABLES                                              ║
║  ───────────────────                                             ║
║  RC_FRAME_VALID    per-frame, gates thrust                       ║
║  RC_CONNECTED      debounced, gates mode switches                ║
║  RC_CH1..RC_CH4    joysticks, ±100                               ║
║  RC_CH5..RC_CH9    switches, 1..2 or 1..3                        ║
║  RC_FAILSAFE       receiver-reported failsafe                    ║
║                                                                  ║
║  HEALTH CHECK (SSH on boat)                                      ║
║  ──────────────────────────                                      ║
║  uXMS RC_CONNECTED RC_FRAME_VALID RC_CH3 RC_CH6                  ║
║                                                                  ║
║  SUPPORT: https://www.radiolink.com/at9spro                      ║
║  SOURCE:  src/iRCReader/ + src/01_libraries/lib_sbus/            ║
╚══════════════════════════════════════════════════════════════════╝
```

---

**Reference documents:**

- [RadioLink AT9S Pro product page](https://www.radiolink.com/at9spro)
- [RadioLink R9DS manual](https://www.radiolink.com/r9ds_manual)
- [Blue Robotics Navigator hardware setup](https://bluerobotics.com/learn/navigator-hardware-setup/)
- [Blue Robotics community: Radio Control on Navigator using SBUS](https://discuss.bluerobotics.com/t/radio-control-on-navigator-using-sbus/12953)
- Source: `moos-ivp-blueboat/src/iRCReader/` and `moos-ivp-blueboat/src/01_libraries/lib_sbus/`
