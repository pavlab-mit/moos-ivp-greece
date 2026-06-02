# UM982 Configuration Recommendations for BlueBoat

## Context

- **Receiver:** Unicore UM982 on ArduSimple simpleRTK3B Compass
- **Platform:** Blue Robotics BlueBoat (autonomous surface vessel)
- **Navigation stack:** Custom (not ArduPilot)
- **Connection:** USB (appears as /dev/ttyACM0 or /dev/ttyUSB0), COM1 baud rate set to **230400**
- **Primary mode:** Standalone (no RTK), with possible NTRIP support later
- **Target nav rate:** 10 Hz without excessive noise
- **Antenna config:** Dual-antenna, heading from rear → front antenna baseline

---

## 1. Recommended Messages for Custom Parser

### Primary Strategy: Unicore Proprietary ASCII (Recommended)

The Unicore proprietary messages give you far more data per message than NMEA, with built-in uncertainty estimates, solution status enums, and satellite diagnostics. They use a `#` prefix and 32-bit CRC instead of NMEA's simple XOR checksum.

#### BESTNAVA @ 10 Hz — Position, Velocity, and Quality

Command: `BESTNAVA 0.1`

This is your **primary navigation message**. Key fields your parser should extract:

| Field | Description | Why You Need It |
|-------|-------------|-----------------|
| sol status | Solution status enum (SOL_COMPUTED, INSUFFICIENT_OBS, etc.) | Gate all downstream processing |
| pos type | SINGLE, PSRDIFF, L1_FLOAT, L1_INT, NARROW_INT, etc. | Know your fix quality |
| lat, lon | WGS84 degrees (Double precision) | Position |
| hgt | Height above MSL, meters | Altitude |
| undulation | Geoid-ellipsoid separation | For ellipsoidal height if needed |
| lat σ, lon σ, hgt σ | Standard deviations in meters | **Real-time accuracy estimate** |
| diff_age | Age of differential corrections, seconds | Monitor NTRIP health (future) |
| sol_age | Solution age, seconds | Detect stale solutions |
| #SVs / #solnSVs | Satellites tracked / used | Sky quality indicator |
| hor spd | Horizontal speed over ground, m/s | Velocity |
| trk gnd | Track over ground, True North, degrees | Course (velocity-derived heading) |
| vert spd | Vertical speed, m/s | Heave sensing |
| Horspd std, Verspd std | Speed standard deviations, m/s | Velocity quality |
| ext sol stat | Extended solution status flags | Detailed diagnostics |

**ASCII output example:**
```
#BESTNAVA,97,GPS,FINE,2190,364787000,0,0,18,1;SOL_COMPUTED,SINGLE,
40.0789783,116.2365145,63.03,-0.001,0.000,-0.003,WGS84,0.0000,
0.0000,0.0000,"0",0.000,0.000,46,0,0,0,0,00,00,INSUFFICIENT_OBS,
NONE,0.000,0.000,0.0000,0.000000,0.0000,00000000*f4ac8d54
```

#### UNIHEADINGA @ 10 Hz — Dual-Antenna Heading

Command: `UNIHEADINGA 0.1`

This is your **primary heading message**. Key fields:

| Field | Description | Why You Need It |
|-------|-------------|-----------------|
| sol_stat | Solution status | Gate heading validity |
| pos_type | Position/solution type | Know if heading is fixed/float |
| length | Baseline length, meters | **Sanity check** — should be constant |
| heading | 0–360°, clockwise from True North | **Your heading** |
| pitch | ±90° | Boat pitch angle |
| hdgstddev | Heading standard deviation, degrees | **Heading quality metric** |
| ptchstddev | Pitch standard deviation, degrees | Pitch quality |
| #SVs / #solnSVs | Satellites tracked / used for heading | Heading sky quality |
| #obs | Sats above elevation mask | Geometric quality |
| #multi | Sats with L2 above mask | Multi-frequency quality |

**Critical parser logic:**
- Only trust heading when `sol_stat == SOL_COMPUTED`
- Monitor `length` — if it drifts significantly from your known baseline, something is wrong
- Use `hdgstddev` to weight heading in your navigation filter

#### BESTVELA @ 10 Hz — Velocity

Command: `BESTVELA 0.1`

Velocity over ground, course, and vertical speed. Key fields:

| Field | Description | Why You Need It |
|-------|-------------|-----------------|
| sol_status | Solution status | Gate velocity validity |
| vel_type | DOPPLER_VELOCITY, etc. | Velocity computation method |
| latency | Seconds | Subtract from time for true velocity time |
| hor_spd | Horizontal speed, m/s | Ground speed |
| trk_gnd | Track over ground, degrees True North | Course / COG |
| vert_spd | Vertical speed, m/s (+ = up) | Heave sensing |

Your parser derives North/East velocity components from `hor_spd` and `trk_gnd`.

### Diagnostic Messages @ 1 Hz

| Command | Message | Purpose |
|---------|---------|---------|
| `STADOPA 1` | Solution-aware position DOP | DOP of actual position solution type (preferred over PSRDOPA) |
| `STADOPHA 1` | Solution-aware heading DOP | DOP specific to the heading solution geometry |
| `RTKSTATUSA 1` | RTK status | Correction health, base station ID (critical when NTRIP added) |

**Note on DOP messages:** STADOPA is preferred over PSRDOPA because it reports DOP values for the actual solution type in use (including RTK when active), while PSRDOPA always reports pseudorange-only DOP. STADOPHA provides the same DOP metrics but specifically for the dual-antenna heading solution — this tells you whether satellite geometry is good for heading, which is independent of position geometry quality. The parser falls back to PSRDOPA if STADOPA is not available.

**Optional additional messages** (not parsed by iUnicoreGPS but useful for debugging):

| Command | Message | Purpose |
|---------|---------|---------|
| `BESTSATA 1` | Satellite details | Per-satellite status, C/N0, used/tracked |

### Alternative: GPHPD @ 10 Hz (Single Combined Message)

If you want to minimize parser complexity, consider **GPHPD** instead of BESTNAVA + UNIHEADINGA separately. It's a Unicore extended NMEA message that packs position, heading, pitch, velocity, and baseline into one sentence:

Command: `GPHPD 0.1`

| Field | Description |
|-------|-------------|
| GPSWeek, GPSTime | Precise GPS time |
| Heading | Dual-antenna heading, 0–360° |
| Pitch | ±90° |
| Track | Course over ground |
| Latitude, Longitude | WGS84 degrees, 7 decimal places |
| Altitude | WGS84 meters |
| Ve, Vn, Vu | East/North/Up velocity, m/s |
| Baseline | Antenna baseline length, meters |
| NSV1, NSV2 | Master/slave antenna satellite counts |

**Trade-off:** GPHPD is simpler to parse but lacks the detailed uncertainty fields (σ values, DOP, solution status enums) that BESTNAVA and UNIHEADINGA provide. For a custom navigation stack that does its own filtering, the uncertainty estimates from the proprietary messages are extremely valuable.

**Recommendation:** Use BESTNAVA + UNIHEADINGA for full data. Add GPHPD only if you want a quick-and-dirty fallback or debug view.

---

## 2. Receiver Mode Configuration

### MODE ROVER UAV (Keep Default)

The UM982 default is `MODE ROVER UAV`, which is actually the best fit for BlueBoat:

- **UAV mode** is optimized for dynamic platforms with moderate to high dynamics
- **SURVEY mode** assumes quasi-static operation — bad for a moving boat
- **AUTOMOTIVE mode** applies constraints for road vehicles (height constraints, lane-level assumptions) — inappropriate for marine

```
MODE ROVER UAV
```

While a boat has lower dynamics than a UAV, UAV mode doesn't add noise — it simply doesn't over-constrain the solution the way AUTOMOTIVE would. The UM982's internal Kalman filter will adapt to the actual dynamics it observes.

---

## 3. Heading Configuration

### Antenna Baseline Length

You need to measure and configure the exact distance between your two antenna phase centers on the BlueBoat. This is critical for heading accuracy (spec: 0.2° / 1m baseline).

```
CONFIG HEADING LENGTH <baseline_cm> <error_margin_cm>
```

Example for a 50cm baseline with ±1cm tolerance:
```
CONFIG HEADING LENGTH 50 1
```

If you use `FIXLENGTH` (default), the receiver assumes a fixed baseline and uses it as a constraint. This is correct for a rigid BlueBoat mounting. **Do not use FIXLENGTH without setting the actual length.**

### Heading Offset

If your antennas are not aligned with the boat's forward axis, you need to configure the offset. The heading convention is: rear antenna → front antenna.

```
CONFIG HEADING OFFSET <heading_offset> <pitch_offset>
```

Example: If antennas are rotated 90° from the keel line:
```
CONFIG HEADING OFFSET 90.0 0.0
```

If antennas are aligned fore-aft along the keel (rear=master, front=slave), no offset is needed (0.0 is default).

### Heading Reliability

Controls the stringency of heading validation. Range 1–4, where higher = stricter.

```
CONFIG HEADING RELIABILITY 3
```

Value 3 is recommended for marine: strict enough to reject bad solutions but not so aggressive that you get unnecessary dropouts in moderate conditions.

---

## 4. Navigation Rate

### 10 Hz Is Solid on USB

There is **no global `CONFIG NAVRATE` command** on the UM982. The navigation output rate is set **per message** using the output rate parameter. When you request `BESTNAVA 0.1`, the receiver computes and outputs at 10 Hz. All your 10 Hz messages will drive the internal PVT engine at that rate.

The UM982 supports up to 50 Hz, but:
- **10 Hz** is well within USB bandwidth even with multiple messages
- At default SIGNALGROUP 4/5 (all constellations, dual-frequency), 10 Hz is comfortably supported
- Going to 20 Hz is possible with SIGNALGROUP 3/6 (fewer constellations per antenna but more channels per remaining constellation) — not recommended unless you have a specific need

### Bandwidth Estimate at 10 Hz

| Message | Rate | Approx bytes/sec |
|---------|------|-------------------|
| BESTNAVA | 10 Hz | ~3,500 |
| UNIHEADINGA | 10 Hz | ~2,000 |
| BESTVELA | 10 Hz | ~1,500 |
| BESTSATA | 1 Hz | ~1,000 |
| STADOPA | 1 Hz | ~500 |
| STADOPHA | 1 Hz | ~500 |
| RTKSTATUSA | 1 Hz | ~500 |
| **Total** | | **~9,500 B/s** |

At the configured COM1 baud rate of **230400** (~23,040 B/s), this fits with ~2x headroom. USB CDC ACM typically ignores the baud rate parameter entirely on the host side, so 230400 is effectively just the value stored in the receiver — the USB link runs at native USB speeds regardless. If the UM982 is ever wired over a real UART instead of USB, the host must match 230400.

---

## 5. Noise Reduction: Heading Smoothing

This is directly relevant to your concern about noise at 10 Hz.

### CONFIG SMOOTH HEADING

```
CONFIG SMOOTH HEADING <seconds>
```

- Range: 0–100 seconds (per UPrecise app — units are seconds, not epochs)
- Default: 0 (no smoothing)

**Current setting:**
```
CONFIG SMOOTH HEADING 1
```

This applies a 1-second smoothing window to heading output. It reduces jitter without introducing significant latency for a boat moving at typical BlueBoat speeds (1–3 m/s).

If you find heading still too noisy, increase to 2–3 seconds. If you're doing your own Kalman filtering downstream, keep this at 0 and handle smoothing in your nav stack.

---

## 6. Standalone Optimization

Since you'll primarily operate without RTK corrections:

### PVTALG MULTI

```
CONFIG PVTALG MULTI
```

This forces dual-frequency position computation even in standalone mode. Default is SINGLE, which only uses L1. MULTI uses L1+L2+L5, which:
- Reduces ionospheric error (the dominant standalone error source)
- Improves position precision from ~2.5m to ~1.5m CEP
- No downside on the UM982 which has plenty of channels

### Elevation Mask

```
MASK 10
```

Default is 5°. The `MASK` command takes the elevation angle directly (range -90° to 90°). Raising to 10° eliminates low-elevation satellites that contribute more multipath and atmospheric error than useful geometry. On a boat (low horizon, potential wave reflections), 10° is a good starting point.

### CN0 Mask

```
MASK CN0 35
```

Rejects satellites with carrier-to-noise ratio below 35 dB-Hz. On water with good sky view, this is conservative enough to keep good satellites while rejecting reflected signals.

---

## 7. Constellation and Signal Configuration

### Keep Default SIGNALGROUP 4/5

```
CONFIG SIGNALGROUP 4 5
```

This is the default for UM982 and provides the best balance:
- **4 frequency channels on master antenna** (GPS L1/L2, BDS B1/B2, GLONASS L1/L2, Galileo E1/E5)
- **5 frequency channels on slave antenna**
- Supports all major constellations on both antennas
- Fully supports 10 Hz with good margin

Only change this if you need 20 Hz (use 3/6) or want to reduce power (use 5/0, but loses heading capability).

---

## 8. SBAS Configuration

### Disable SBAS (Keep Default)

```
CONFIG SBAS DISABLE
```

SBAS (WAAS/EGNOS) is already disabled by default on UM982. Keep it disabled because:
- SBAS corrections are L1-only and can actually degrade a dual-frequency receiver's solution
- When you add NTRIP later, RTCM corrections are far superior
- SBAS satellites waste tracking channels

---

## 9. Future NTRIP Readiness

When you're ready to add NTRIP:

1. Your custom stack feeds RTCM data to the UM982 via USB
2. No receiver configuration change needed — just send RTCM bytes to the serial port
3. BESTNAVA will automatically show `pos type` changing from SINGLE → PSRDIFF → L1_FLOAT → NARROW_INT as corrections converge
4. RTKSTATUSA will show correction health
5. Consider adding: `RTCSTATUSA ONCHANGED` for correction link monitoring

The CONFIG STANDALONE feature can maintain cm-level accuracy temporarily after RTK loss — useful for intermittent NTRIP:
```
CONFIG STANDALONE ENABLE
```

---

## 10. Complete Configuration Command Sequence

Send these commands to the UM982 via USB serial. Each command should be terminated with `\r\n`. Wait for `$command,response,OK*xx` acknowledgment before sending the next.

```
# ========================================
# UM982 BlueBoat Configuration Script
# ========================================

# --- Reset to clean state (optional, careful!) ---
# FRESET

# --- Receiver Mode ---
MODE ROVER UAV

# --- Heading Configuration ---
# IMPORTANT: Set your actual baseline length in cm
CONFIG HEADING FIXLENGTH
CONFIG HEADING LENGTH 62.23 1
CONFIG HEADING RELIABILITY 3

# --- Standalone Optimization ---
CONFIG PVTALG MULTI
MASK 10
MASK CN0 35

# --- Noise Reduction ---
CONFIG SMOOTH HEADING 1

# --- Signal Configuration (keep default) ---
CONFIG SIGNALGROUP 4 5

# --- SBAS (keep disabled) ---
CONFIG SBAS DISABLE

# --- Primary Output Messages @ 10 Hz ---
BESTNAVA 0.1
UNIHEADINGA 0.1
BESTVELA 0.1

# --- Diagnostic Messages @ 1 Hz ---
STADOPA 1
STADOPHA 1
RTKSTATUSA 1
BESTSATA 1

# --- Save Configuration to Flash ---
SAVECONFIG
```

### Notes on the Command Sequence

1. **FRESET** — Full factory reset. Only use if you want a clean slate. Erases all saved config.
2. **Baseline length** — You MUST measure and update `CONFIG HEADING LENGTH` with your actual antenna separation in centimeters.
3. **SAVECONFIG** — Persists everything to flash so it survives power cycles.
4. **No UNLOGALL needed** — the UM982 doesn't output anything by default on USB until you request messages.
5. **Implicit port binding** — Log commands like `BESTNAVA 0.1` bind to the port they were issued from. When this script is sent over COM1 (the USB CDC port on the simpleRTK3B), `CONFIG` will echo them back as `BESTNAVA COM1 0.1`, etc. To stream a log to a different port, use the explicit form `BESTNAVA COM2 0.1`.
6. **MASK CN0 is stored per-signal** — Issuing `MASK CN0 35` once expands internally into one record per supported signal (L1CA, L2P, L2C, L5, B1I/Q, B2I/Q, B3I/Q, R1–R3, E1, E5A/B, E6C, BD3B1C/B2A/B2B, L1C, Q1CA, Q1C, Q2C, Q5, IRNSS, SBAS). `CONFIG` will echo many lines but you only need to send the one-line form.

---

## 11. Parser Quick Reference

### BESTNAVA Parsing

Messages start with `#BESTNAVA,` followed by a standard header, then a `;` separator before the data fields. The header contains GPS week, milliseconds, and other metadata.

**Header format:** `#BESTNAVA,<port>,<timeref>,<timestatus>,<week>,<ms>,<reserved>,<reserved>,<reserved>,<version>;`

**Data fields after `;`:** `<sol_status>,<pos_type>,<lat>,<lon>,<hgt>,<undulation>,<datum>,<lat_σ>,<lon_σ>,<hgt_σ>,"<stn_id>",<diff_age>,<sol_age>,<#SVs>,<#solnSVs>,<reserved>,<reserved>,<reserved>,<ext_sol_stat>,<sig_mask1>,<sig_mask2>,<sol_status2>,<vel_type>,<latency>,<diff_age2>,<hor_spd>,<trk_gnd>,<vert_spd>,<verspd_std>,<horspd_std>*<CRC>`

### UNIHEADINGA Parsing

**Header:** Same format as BESTNAVA

**Data fields after `;`:** `<sol_status>,<pos_type>,<length>,<heading>,<pitch>,<reserved>,<hdgstddev>,<ptchstddev>,"<stn_id>",<#SVs>,<#solnSVs>,<#obs>,<#multi>,<reserved>,<ext_sol_stat>,<sig_mask1>,<sig_mask2>*<CRC>`

### Key Solution Status Values

| ASCII Value | Meaning | Action |
|-------------|---------|--------|
| SOL_COMPUTED | Solution is valid | Use data |
| INSUFFICIENT_OBS | Not enough satellites | Reject / coast |
| NO_CONVERGENCE | Solution hasn't converged | Wait |
| COV_TRACE | Covariance trace too high | Use with caution |
| COLD_START | Receiver still initializing | Wait |

### Key Position Type Values (Standalone)

| ASCII Value | Meaning |
|-------------|---------|
| NONE | No solution |
| SINGLE | Autonomous GNSS (your typical standalone mode) |
| PSRDIFF | Pseudorange differential (SBAS/DGNSS) |
| L1_FLOAT | L1 carrier float (RTK converging) |
| NARROW_INT | Full RTK fix (best) |

---

## 12. What to Measure on the Boat

Before deploying, you need:

1. **Antenna baseline length** — Measure center-to-center distance between the two antenna mounting points, in centimeters. Accuracy matters: ±1cm.
2. **Antenna orientation** — Confirm which antenna is master (rear) and which is slave (front). The heading vector points from master to slave.
3. **Heading offset** — If the antenna baseline is not parallel to the boat's keel, measure the angle offset.
4. **Mounting height** — Not critical for configuration, but useful for your nav stack's datum handling.

---

## Summary of Key Decisions

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Nav rate | 10 Hz (set per-message with 0.1 rate) | Good update rate without excessive bandwidth |
| Primary messages | BESTNAVA + UNIHEADINGA + BESTVELA | Full position, heading, and velocity data |
| Diagnostic messages | STADOPA + STADOPHA + RTKSTATUSA + BESTSATA @ 1 Hz | Position DOP, heading DOP, RTK correction health, per-satellite C/N0 |
| COM1 baud rate | 230400 | Sufficient bandwidth (~2x headroom); USB CDC ignores baud on host side |
| Mode | ROVER UAV | Best dynamic model for a boat |
| PVTALG | MULTI | Dual-frequency standalone for better precision |
| Heading smoothing | 1 second | Reduce 10 Hz jitter without lag |
| Elevation mask | 10° | Reject low-elevation multipath on water |
| CN0 mask | 35 dB-Hz | Reject weak/reflected signals |
| SIGNALGROUP | 4/5 (default) | All constellations, dual-freq, 10 Hz capable |
| SBAS | Disabled | Not useful with dual-frequency receiver |
| Heading reliability | 3 | Good balance for marine environment |

---

## Verified Against

This configuration has been verified against a physical UM982 module with the following firmware:

- **Receiver:** UM982
- **Firmware:** R4.10 Build 11826
- **Build date:** 2023-11-24
- **Hardware ID:** HRPT00-S10C-P
- **Verification date:** 2026-05-12

`CONFIG`, `MODE`, `MASK`, `VERSION`, and `UNILOGLIST` query output from the live module matches the command sequence in §10.
