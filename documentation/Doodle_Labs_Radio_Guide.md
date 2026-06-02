# PAVLAB Doodle Labs Mesh Rider Radio Guide

> **Radios covered:** Wearable (RM-1700-22W3) · Mini-OEM (RM-1700-22M3)
> **Web GUI version observed:** MeshRider Web 3.1.0
> **Last updated:** June 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Radio Comparison at a Glance](#2-radio-comparison-at-a-glance)
3. [Wearable Radio (RM-1700-22W3)](#3-wearable-radio-rm-1700-22w3)
   - [Hardware Tour](#31-hardware-tour)
   - [Ports and Cables](#32-ports-and-cables)
   - [Battery and Power](#33-battery-and-power)
   - [LEDs and Buttons](#34-leds-and-buttons)
   - [GPS Module](#35-gps-module)
   - [Wi-Fi Radio](#36-wi-fi-radio)
4. [Mini-OEM Radio (RM-1700-22M3)](#4-mini-oem-radio-rm-1700-22m3)
   - [Hardware Tour](#41-hardware-tour)
   - [Connector Pinouts](#42-connector-pinouts)
   - [Power Supply Integration](#43-power-supply-integration)
   - [Thermal Management](#44-thermal-management)
5. [Connecting to a Radio](#5-connecting-to-a-radio)
   - [IP Addressing Explained](#51-ip-addressing-explained)
   - [Host Machine Setup](#52-host-machine-setup)
   - [Accessing the Web GUI](#53-accessing-the-web-gui)
   - [SSH Access](#54-ssh-access)
6. [Radio Configuration](#6-radio-configuration)
   - [Web GUI Navigation (Sidebar)](#61-web-gui-navigation-sidebar)
   - [Setup Wizard](#62-setup-wizard)
   - [Default PAVLAB Configuration](#63-default-pavlab-configuration)
   - [Mesh Configuration Page](#64-mesh-configuration-page)
   - [Link Optimization → Wireless](#65-link-optimization--wireless)
   - [Link Optimization → Networkwide Configuration](#66-link-optimization--networkwide-configuration)
   - [Link Optimization → Traffic Prioritization](#67-link-optimization--traffic-prioritization)
   - [Wearable Wi-Fi AP Setup](#68-wearable-wi-fi-ap-setup)
   - [Network Configuration](#69-network-configuration)
   - [Utilities → Hotspot Wizard](#610-utilities--hotspot-wizard)
7. [Mesh Network Deployment](#7-mesh-network-deployment)
   - [How the Mesh Works](#71-how-the-mesh-works)
   - [Network Topology Diagram](#72-network-topology-diagram)
   - [First-Time Test Procedure](#73-first-time-test-procedure)
8. [Firmware, Backup, and Recovery](#8-firmware-backup-and-recovery)
   - [Configuration Backup](#81-configuration-backup)
   - [Firmware Upgrade](#82-firmware-upgrade)
   - [Factory Reset](#83-factory-reset)
   - [Configuration Cloning](#84-configuration-cloning)
9. [Radio API and Custom Interfaces](#9-radio-api-and-custom-interfaces)
   - [JSON-RPC API Overview](#91-json-rpc-api-overview)
   - [UCI Configuration Interface](#92-uci-configuration-interface)
   - [IP Advertiser Discovery](#93-ip-advertiser-discovery)
   - [GPS Data Access](#94-gps-data-access)
   - [Front-Seat Integration (Blue Boats)](#95-front-seat-integration-blue-boats)
10. [Troubleshooting and Working Notes](#10-troubleshooting-and-working-notes)
11. [Quick Reference Card](#11-quick-reference-card)

---

## 1. Overview

The PAVLAB uses Doodle Labs Mesh Rider radios to provide robust, low-latency mesh networking between shore stations and autonomous surface vehicles (Blue Boats). The radios operate on ISM bands (900 MHz and 2.4 GHz) and form a self-healing, peer-to-peer mesh network that acts as a transparent Layer-2 bridge — devices on either end communicate as though they are on the same Ethernet switch.

We operate two form factors:

| Role | Model | Form Factor | Use Case |
|------|-------|-------------|----------|
| **Shore / Operator** | RM-1700-22W3 | Wearable | Carried by operator or mounted at shore station. Includes battery pack, Wi-Fi AP, and GPS. |
| **Vehicle / Boat** | RM-1700-22M3 | Mini-OEM | Embedded inside Blue Boat pontoon. Bare board with JST connectors, powered by 5 V buck converter. |

Both radios share the same Mesh Rider OS (based on OpenWrt), the same web GUI, and the same 2x2 MIMO dual-band RF platform (902–928 MHz and 2400–2482 MHz). The key differences are physical form factor, power input, and available interfaces.

---

## 2. Radio Comparison at a Glance

| Specification | Wearable (22W3) | Mini-OEM (22M3) |
|---|---|---|
| **Dimensions** | 134.3 × 63.0 × 17.0 mm, 311 g | 47 × 28 × 5 mm (baseband) + 46 × 51 × 6.5 mm (RF), 36.5 g |
| **Power Input** | 6–24 V DC (USB-PD) or battery pack | **5 V ± 5% only** (JST connector) |
| **Power Consumption (2.4 GHz)** | Avg 3 W, Peak 4.5 W | Avg 3 W, Peak 4.5 W |
| **Antenna Connectors** | 2× TNC-Female | 2× MMCX-Female |
| **Ethernet** | Via USB (Ethernet-over-USB) | JST connector (100 Base-T) |
| **USB Device Port** | Yes (USB-C) | Yes (JST) |
| **USB Host Port** | Yes (USB-C) | Yes (JST) |
| **Wi-Fi Radio** | Yes (5 GHz AP/Client) | No |
| **GPS** | Yes (U-Blox MAX M8Q) | No |
| **UART** | Yes (via OEM connector) | Yes (JST, 115200 baud, 3.3 V TTL) |
| **GPIOs** | 1 | 3 |
| **Ingress Protection** | IP67 (waterproof) | IP50 (dust protected, no liquid) |
| **Operating Temp** | −40 °C to +85 °C | −40 °C to +85 °C |
| **Max RF Power** | 1.6 W (32 dBm) | 1.6 W (32 dBm) |
| **Max Throughput (UDP, 20 MHz)** | 82.8 Mbps | 87 Mbps |
| **Encryption** | 128-bit AES (full speed) / 256-bit AES (12 Mbps max) | Same |
| **MTBF** | >235k hours (25 years) | >235k hours (25 years) |

---

## 3. Wearable Radio (RM-1700-22W3)

### 3.1 Hardware Tour

The Wearable is a rugged, IP67-rated unit designed for handheld or body-worn use. It ships with a detachable battery pack, two gooseneck TNC antennas, and a breakout board.

```
  Wearable Radio — Front and Top View (Version A1XXX)
  ┌─────────────────────────────────┐
  │  [ANT 0 TNC]        [ANT 1 TNC]│  ← Top: Mesh Rider antennas
  │         [GPS SMA]               │  ← Top: GPS antenna (SMA)
  │                                 │
  │   ┌───┐  ┌───┐  ┌───┐          │
  │   │WiFi│  │BATT│  │RSSI│         │  ← Front: LED indicators
  │   └───┘  └───┘  └───┘          │
  │                                 │
  │   (TURBO)           (ON)        │  ← Front: Buttons
  │                                 │
  │   ┌──────────────────────┐      │
  │   │  MAC / IP label      │      │  ← Front: Identification sticker
  │   │  barcode             │      │
  │   └──────────────────────┘      │
  │                                 │
  │   ┌────────┐    ┌────────┐      │
  │   │USB-C   │    │USB-C   │      │  ← Bottom: PWR-IN (Device) + ETH (Host)
  │   │PWR-IN  │    │ETH     │      │
  │   │(Dev)   │    │(Host)  │      │
  │   └────────┘    └────────┘      │
  └─────────────────────────────────┘
         ↕ Battery attaches below
  ┌─────────────────────────────────┐
  │   [Battery Pack]                │
  │   USB-C charging port (side)    │
  │   ON/OFF button (side)          │
  └─────────────────────────────────┘
```

**Hardware version notes:** The Draper Wearable is a A1XXX (Oct 2023, with inverted antenna port and USB-C locking), the PAVLAB radio is a B1XXX (Mar 2025, with programmable Button 1 / Button 2 replacing Turbo/ON).

### 3.2 Ports and Cables

| Port | Label | Function | Notes |
|------|-------|----------|-------|
| Bottom-left USB-C | **PWR-IN** (USB-Device) | Power delivery + USB data connection to radio | Can power radio directly without battery. Also provides USB-device connectivity. |
| Bottom-right USB-C | **ETH** (USB-Host) | Primary Ethernet-over-USB connection | **Preferred port for laptop connection.** Most compatible/native experience. |
| Battery USB-C | Charging port | Battery charging only + power delivery to radio | Do NOT use for data — charging only. |
| Top TNC × 2 | CH0, CH1 | Mesh Rider antenna connections | **Both must be connected before powering on.** |
| Top SMA × 1 | GPS | GPS antenna (active, supplied) | Needs clear sky view. Secure SMA connector. |

> **Important:** While both USB ports on the radio support data connections, **always prefer the ETH (USB-Host) port** for connecting to your laptop. It provides the most compatible Ethernet-over-USB experience. Only use PWR-IN for data if necessary.

### 3.3 Battery and Power

**Using the battery pack (recommended for field use):**

1. Fully charge the battery first using a 20 W+ USB-PD charger connected to the battery's USB-C port.
2. Align the battery legs with the holes in the radio casing.
3. Slide the battery into place and rotate the locking mechanism until it clicks.
4. Press and hold the battery ON/OFF button for **4–5 seconds** until the LEDs begin blinking (slow 1200 ms blink = booting).
5. Wait for LEDs to go steady — the radio is now operational.

**Direct USB power (bench testing):**

Connect a USB-C cable with sufficient power (USB-PD compliant, 20 W minimum) to the **PWR-IN** port. The radio boots automatically — no button press needed.

> **Tip:** For reliability during extended operations, always use the battery pack and keep it charged. Direct USB power is best for bench testing only.

### 3.4 LEDs and Buttons

**LED indicators (A1XXX version):**

| LED | Meaning |
|-----|---------|
| **Power LED** | Steady = On. Slow blink (1200 ms) = Booting. Fast blink (600 ms) = Factory reset pending. |
| **Wi-Fi indicator** | Shows Wi-Fi signal strength / activity |
| **BATT indicator** | Battery level status |
| **RSSI / Mesh Rider indicator** | Mesh Rider RF signal strength |
| **Turbo LED** | Steady = 2x2 MIMO mode. Off = 1x1 SISO (power saving) |

**Buttons (A1XXX):**

| Button | Action | Result |
|--------|--------|--------|
| **ON** (Power) | 4-second press | Toggle radio On ↔ Off |
| **Turbo** | 2-second press | Toggle 1x1 SISO ↔ 2x2 MIMO |
| **Both held** | Hold until fast blink (600 ms), then release | Factory reset |

**B1XXX version:** The Turbo and ON buttons are replaced by **Button 1** and **Button 2**, which are fully programmable. Their behavior can be monitored and customized via the API.

### 3.5 GPS Module

The Wearable includes a U-Blox MAX M8Q GPS receiver supporting multiple constellations (GPS, GLONASS, BeiDou, Galileo, SBAS, QZSS) with 2.5 m accuracy and 10 Hz max fix rate.

**Setup:** Simply connect the supplied active GPS antenna to the SMA port on top. No software configuration required — it works out of the box. The antenna needs a clear view of the sky.

**Viewing GPS data:**

- **Web GUI:** Dashboard → GPS Information section shows latitude, longitude, altitude, and update time.
- **SSH:** GPS data is available at `/var/run/gps/` (files: `latitude`, `longitude`, `altitude`, `time`).
- **GPSD:** Enabled by default on port 2947. Use `gpspipe -w -n 5` for JSON output, or `cgps` for a terminal display.

**Configuration (if needed):**

Navigate to **Utilities → GPS Receiver** in the web GUI to enable/disable GPSD, change the listening port (default `2947`), pick the GPS device (default `/dev/GPS`), or configure u-blox AssistNow.

The GPS receiver page has three sections:

- **Main Configuration** — GPSD Enabled toggle, Listening Port, GPS Device.
- **Network & Time Settings** — *Bind to all interfaces* (off by default; required for remote GPSD access, and a firewall rule may also need enabling) and *Update local date and time* (off by default; when on, the radio's system clock is set from GPS once a fix is available).
- **u-blox AssistNow Settings** — disabled by default; speeds up cold-start fixes when enabled.

```
# Check GPS config via SSH:
root@smartradio:~# uci show gpsd
gpsd.core.enabled='1'
gpsd.core.device='/dev/GPS'
gpsd.core.port='2947'
gpsd.core.listen_globally='0'   # Set to '1' for remote access
```

### 3.6 Wi-Fi Radio

The Wearable includes a built-in 5 GHz Wi-Fi radio bridged to the Mesh Rider interface. This allows laptops and smart devices to connect wirelessly.

**Default AP settings (out of the box):**

| Setting | Value |
|---------|-------|
| SSID | `DoodleLabsWiFi-<last 6 hex of MAC>` |
| Password | `DoodleSmartRadio` |
| Mode | Access Point |
| Frequency | 5 GHz |

**PAVLAB Wearable AP settings (per-unit — values vary):**

PAVLAB Wearables are configured individually rather than from a single template, so the SSID and password are not uniform across units. Examples observed:

| Unit (mgmt IP) | SSID | Channel observed |
|---|---|---|
| `10.223.64.151` | `DoodleLabsAP` | 56 (5280 MHz) |
| `10.223.71.187` | `DRAPER WEARABLE` | 44 (5220 MHz) |

The Wi-Fi channel is set to **Auto**, so each radio's AP picks a least-congested 5 GHz channel at boot — expect different channels even on identically-configured units.

The Wi-Fi password used by PAVLAB-provisioned units is `Hovergroup!123`. Units inherited from previous projects (e.g., Draper) may retain their original credentials — check the radio's Setup Wizard page to confirm.

> **Note:** Even when connected via Wi-Fi, you will likely still need to set a static IP on your laptop (the radio is unlikely to run DHCP by default).

**Client mode (Hotspot Wizard):** The Wi-Fi can also connect to an external hotspot. Navigate to **Utilities → Hotspot Wizard** (formerly labeled "EUD Wizard"), enable the Hotspot Wizard toggle, scan for networks in the Network Discovery panel, and click Connect on the target. The radio will run a DHCP server for the mesh network and apply NAT between mesh and hotspot. See §6.10 for details.

---

## 4. Mini-OEM Radio (RM-1700-22M3)

### 4.1 Hardware Tour

The Mini-OEM is a bare-board radio designed for embedded integration. In the Blue Boats, it mounts inside a pontoon and connects to external antennas via SMA-to-N-Type bulkhead adapters.

```
  Mini-OEM Board — Top View (2023 Update)

       Port 4 (Power, 6-pin JST)
         ↓
  Port 3 → ┌─────────────────────────┐ ← Port 6 (GPIO, 4-pin JST)
  (UART)   │  ┌───────────────────┐  │
  Port 2 → │  │                   │  │ ← Port 5 (USB-Host, 4-pin JST)
  (ETH)    │  │   RF Front End    │  │
  Port 1 → │  │                   │  │
  (USB-Dev)│  └───────────────────┘  │
           │                         │
           │    ○ ANT1 (MMCX)        │
           │                         │
           │    ○ ANT0 (MMCX)        │
           └─────────────────────────┘
```

All data connectors use JST GHS series (SM4B-GHS-TB for 4-pin, SM6B-GHS-TB for 6-pin). Antenna connectors are Molex 73414-0100 (MMCX female).

### 4.2 Connector Pinouts

**Port 1 — USB Device (4-pin JST SM4B-GHS-TB)**

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | NC | Not Connected |
| 2 | USB-Dev-D− | Ethernet over USB only |
| 3 | USB-Dev-D+ | Ethernet over USB only |
| 4 | GND | Ground |

**Port 2 — Ethernet (4-pin JST SM4B-GHS-TB)**

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | ETH1_RX_N | Receive − |
| 2 | ETH1_RX_P | Receive + |
| 3 | ETH1_TX_N | Transmit − |
| 4 | ETH1_TX_P | Transmit + |

> No GND wire needed with Ethernet — signals are differential and auto MDI-X.

**Port 3 — UART + Reset (4-pin JST SM4B-GHS-TB)**

| Pin | Signal | Voltage | Notes |
|-----|--------|---------|-------|
| 1 | GND | GND | |
| 2 | RESET | 2.8 V | Default high; pull low to reset |
| 3 | UART_RX | 3.3 V | Input to radio |
| 4 | UART_TX | 3.3 V | Output from radio (115200 baud) |

**Port 4 — Power (6-pin JST SM6B-GHS-TB)**

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | +5 V | Input supply |
| 2 | +5 V | Input supply |
| 3 | +5 V | Input supply |
| 4 | GND | |
| 5 | GND | |
| 6 | GND | |

> ⚠️ **CRITICAL: 5 V ONLY. No reverse polarity protection.** Double-check voltage and polarity before connecting. Applying incorrect voltage will permanently damage the board.

**Port 5 — USB Host (4-pin JST SM4B-GHS-TB)**

| Pin | Signal | Voltage | Notes |
|-----|--------|---------|-------|
| 1 | +5 V Out | 5 V | Power output for USB peripherals |
| 2 | USB-Host-D+ | Diff | |
| 3 | USB-Host-D− | Diff | |
| 4 | GND | | |

**Port 6 — GPIO (4-pin JST SM4B-GHS-TB)**

| Pin | Signal | Voltage |
|-----|--------|---------|
| 1 | GPIO2 | 2.8 V |
| 2 | GPIO1 | 2.8 V |
| 3 | GPIO0 | 2.8 V |
| 4 | GND | |

### 4.3 Power Supply Integration

The Mini-OEM is extremely sensitive to power quality. Follow these guidelines:

```
  Recommended Power Supply Topology

  ┌─────────┐    Twisted pair    ┌─────┐    Short wires    ┌──────────┐
  │  Main   │ ──────────────── → │ BEC │ ────────────── → │ Mini-OEM │
  │ Battery │                    │(5V) │                   │  Radio   │
  └─────────┘                    └─────┘                   └──────────┘
                                   ↑
                          Use a Buck Converter
                          (BEC) for clean 5V

  ✗ Do NOT daisy-chain other devices on the same power line
  ✗ Do NOT use long wires (act as inductors, cause voltage swings)
  ✓ Keep BEC close to the radio
  ✓ Twist power wires for EMI/EMC
  ✓ Use AWG 26 or thicker wire (handles 2.2 A)
  ✓ Ensure power supply ripple < 100 mW
```

**For Blue Boat integration:** Power is supplied via a 5 V buck converter from the vehicle's main battery for additional power smoothing. The radio connects to external dual antennas through SMA → N-Type bulkheads mounted in each pontoon.

### 4.4 Thermal Management

Most heat is generated by the RF Front End. For the Mini-OEM, attach the largest flat metal surface of the RF board to a suitable heat sink. In the Blue Boat, the pontoon structure serves as a heat sink. Use thermal paste or thermally conductive tape for good coupling.

---

## 5. Connecting to a Radio

### 5.1 IP Addressing Explained

Every Mesh Rider Radio has **three default IP addresses:**

| Address | Subnet | Purpose |
|---------|--------|---------|
| `10.223.x.y/16` | Unique per radio | Primary management address. Calculated from MAC. Printed on barcode label. |
| DHCP client | Dynamic | Assigned when a DHCP server exists on the network. |
| `192.168.153.1/24` | Same for ALL radios | Initial config only. **Never use when multiple radios are on the network.** |

**How the 10.223.x.y address is calculated:** Take the last two octets of the radio's MAC address and convert each from hex to decimal. For a PAVLAB Wearable with MAC `00:30:1A:3C:40:97`: `x = decimal(0x40) = 64` and `y = decimal(0x97) = 151`, giving `10.223.64.151`. A second PAVLAB unit with MAC `00:30:1A:3B:47:BB` resolves to `10.223.71.187` by the same rule. This address is printed on the radio's label.

> **Fallback rule:** If you ever lose connectivity during configuration, always go back to the `10.223.x.y` address from the label. It's the most reliable way to reconnect.

### 5.2 Host Machine Setup

To connect your laptop to a radio, you need to set a static IP in the `10.223.0.0/16` subnet:

**Example configuration:**

| Device | IP Address | Subnet Mask |
|--------|-----------|-------------|
| Radio | `10.223.64.151` | `255.255.0.0` |
| Laptop | `10.223.64.100` | `255.255.0.0` |

**Steps (varies by OS):**

1. Connect your laptop to the radio via USB-C (Wearable: use **ETH USB-H** port) or Ethernet (Mini-OEM: Port 2).
2. A new network adapter should appear (e.g., "LAN9500A USB 2.0 to Ethernet 10/100 Adapter").
3. Open network adapter properties → Internet Protocol Version 4 (TCP/IPv4) → Properties.
4. Select "Use the following IP address" and enter your static IP (e.g., `10.223.0.5`) with subnet mask `255.255.0.0`.
5. Click OK.

**Alternative method (if you don't know the 10.223 address):**

1. Set your IP to `192.168.153.10/24`.
2. SSH into `192.168.153.1` and run:
   ```
   ssh -q -o stricthostkeychecking=no root@192.168.153.1
   inet 10.223.170.187/16 brd 10.223.255.255 scope global br-wan
   ```
3. Note the `10.223.x.y` address, then switch your laptop to that subnet.

### 5.3 Accessing the Web GUI

1. Open **Chrome or Firefox** (avoid Safari — known compatibility issues).
2. Navigate to `https://<RADIO_IP>` (e.g., `https://10.223.64.151`).
3. Accept the self-signed certificate warning.
4. At the login page, enter the password and press **Login**. PAVLAB radios use the Doodle Labs default password: **`DoodleSmartRadio`**. (Earlier firmware shipped with no password; current PAVLAB units all have the default set.)
5. You'll land on the **Dashboard** page. The current Web GUI is **MeshRider Web 3.1.0** (version is shown in the footer of the login screen).

### 5.4 SSH Access

```bash
ssh root@<RADIO_IP>
# No password required by default
# Example:
ssh root@10.223.64.151
```

The radio runs OpenWrt Linux. From here you can access UCI configuration, the filesystem, and command-line tools.

---

## 6. Radio Configuration

### 6.1 Web GUI Navigation (Sidebar)

The MeshRider Web 3.1.0 sidebar (open via the hamburger icon, top-left) is the primary way to reach every configuration page. Top-level items:

| Sidebar item | What it covers |
|---|---|
| **Dashboard** | Live status: Mesh Rider, Wi-Fi, GPS, Associated Stations. Read-only. |
| **Setup Wizard** | One-page combined configuration for Mesh Rider radio, Wi-Fi radio, and network settings (§6.2). |
| **Mesh Configuration** | Mesh-protocol tuning (OGM interval, loop avoidance, broadcasts) and a Peer Filter sub-tab (§6.4). |
| **Link Optimization** | Three sub-pages: *Wireless* (full per-band tuning, §6.5), *Networkwide Configuration* (mesh-wide band push, §6.6), *Traffic Prioritization* (QoS rules, §6.7). |
| **License Features** | Optional add-on licenses. Not used at PAVLAB. |
| **Utilities** | Includes *GPS Receiver* (§3.5) and *Hotspot Wizard* (§6.10), plus other helpers. |
| **Device Manager** | Firmware operations, backup, factory reset (§8). |
| **Logout** | Ends the session. |

The header above the sidebar shows the connected radio's IP (e.g., `Mesh Rider Radio — 10.223.64.151`), which is useful to confirm you're configuring the unit you think you are when multiple tabs are open.

### 6.2 Setup Wizard

The **Setup Wizard** page (sidebar → *Setup Wizard*) is the single-page wizard that configures the most-touched radio parameters at once. It is *not* labeled "Simple Configuration" in current firmware — that's an older name.

The page is laid out as a top profile selector with three blocks underneath:

- **Profile Selection** — Profile dropdown plus a **Load Defaults** button that resets the wizard to that profile's recommended values. Useful for recovering from a botched config.
- **Active Frequency Band** — single dropdown that drives both the Mesh Rider and Wi-Fi blocks below.
- **Mesh Rider Radio Configuration** (left column) and **Wi-Fi Radio Configuration** (right column), side-by-side, with **Network Configuration** beneath the Wi-Fi column.

Click **Save Configuration** (bottom-right) when done — applying takes about a minute. The TPC / Aggressive TPC / Optimize-for-Latency toggles are *not* on this page; see §6.5 and §6.7.

### 6.3 Default PAVLAB Configuration

Set these values across the Setup Wizard, Link Optimization → Wireless (§6.5), and Link Optimization → Traffic Prioritization (§6.7):

**Setup Wizard (Mesh Rider column):**

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Profile** | General | |
| **Active Frequency Band** | 2450v4 MHz | Stick with 2.4 GHz — Draper radios are not full dual band. |
| **Scenario** | Mesh | |
| **Mesh ID** | `pavlab` | All radios on the same mesh must share this. |
| **Wireless Password** | `hovergroup` | |
| **Channel** | **13 (2472 MHz)** | The dashboard reports Channel 13 / 2472 MHz. (Older versions of this doc said "Channel 12 (2472 MHz)" — incorrect; Ch 12 = 2467 MHz, Ch 13 = 2472 MHz.) |
| **Bandwidth** | 20 MHz | Higher BW (e.g., 40 MHz) is preferred but the per-radio setting doesn't always persist — push it network-wide from Link Optimization → Networkwide Configuration (§6.6). |
| **Operating Distance** | 1000 meters | |
| **Number of Devices** | 3 to 5 | |

**Link Optimization → Wireless (Mesh Rider tab):**

| Parameter | Value | Notes |
|-----------|-------|-------|
| **TPC** | **Off** | Transmit Power Control — leave off for maximum power output. **This setting matters significantly.** |
| **Aggressive TPC** | Off | |
| **Country** | `GV - Government` | Government region; explains why Ch 13 is available. |
| **Mode** | `N` | 802.11n. |
| **Transmit Power** | `driver default` | |
| **RX/TX Antennas** | Both enabled (1 and 2) | 2×2 MIMO. |
| **Encryption** | `WPA2-PSK / AES-128 (CCMP)` | Confirms the 128-bit AES (full speed) spec from §2. |

**Link Optimization → Traffic Prioritization:**

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Optimize C&C and Voice for URLLC** | On | Prioritizes low-latency control traffic. |
| **Optimize Video Streaming** | On (default) | PAVLAB does not currently stream video over the mesh; this could be turned off without impact. |
| **Optimize for Robustness** | On | |
| **Optimize for Latency over throughput** | On | Prevents major lag spikes (the "Optimize for Latency" toggle in older docs). |
| **Enable Automatic C&C Queue Detection** | Off | |

### 6.4 Mesh Configuration Page

Sidebar → **Mesh Configuration**. Two tabs: *Mesh Configuration* and *Peer Filter*.

**Mesh Configuration tab — current observed values (defaults):**

| Section | Setting | Current value |
|---|---|---|
| General Settings | Originator Message (OGM) Interval | 5000 ms |
| General Settings | Bridge Loop Avoidance | Off |
| General Settings | Group-aware multicast-to-unicast routing | Off |
| Broadcast Settings | Number of Self-broadcasts | 1 |
| Broadcast Settings | Number of Re-broadcasts | 1 |

These are knobs on the underlying B.A.T.M.A.N.-adv mesh protocol. Defaults work fine at PAVLAB scale; they're the right place to experiment if mesh convergence or multicast behavior ever becomes a problem.

**Peer Filter tab:** lets you whitelist or block specific peer MAC addresses from joining the mesh. **Currently unused** at PAVLAB (no entries). Useful if we ever want to lock the mesh to a known set of radios.

### 6.5 Link Optimization → Wireless

Sidebar → **Link Optimization → Wireless**. Two top-level tabs: *Mesh Rider* and *Wi-Fi*. Each tab has five sections:

1. **Frequency Configuration** — mirrors the Setup Wizard fields (Frequency Band, Channel, Bandwidth) but with its own **Apply** button for quick changes without touching the rest of the wizard.
2. **General Settings** — Distance Optimization (meters), TPC, Aggressive TPC, Mesh ID. **This is where the TPC toggles actually live** despite §6.3 listing them with the rest of the PAVLAB defaults.
3. **Radio Frequency Settings** — Operating Mode (e.g., `N`), Country code (PAVLAB: `GV - Government`), and Transmit Power (PAVLAB: `driver default`).
4. **Antenna Configuration** — RX Antennas 1/2 and TX Antennas 1/2 toggles. Both enabled in both directions = 2×2 MIMO.
5. **Wireless Security** — Encryption dropdown (PAVLAB: `WPA2-PSK / AES-128 (CCMP)`) and password.

> The UI notes: *"Depending on the driver, you may also need to configure any TX antenna as RX for this option to function properly."* Worth keeping in mind if you ever experiment with disabling antennas.

### 6.6 Link Optimization → Networkwide Configuration

Sidebar → **Link Optimization → Networkwide Configuration**.

**Manual Band Configuration** (left) lets you set Frequency Band, Channel, and Bandwidth and push the change across **every** radio in the mesh in one shot. **Current Wireless Status** (right) is read-only confirmation of what the local radio currently reports.

This page is the right tool for changing channel or bandwidth — single-radio changes from the Setup Wizard or Wireless page sometimes fail to propagate (the long-standing "bandwidth doesn't persist" gotcha).

### 6.7 Link Optimization → Traffic Prioritization

Sidebar → **Link Optimization → Traffic Prioritization**. Two columns: General Settings and Classification Rules.

**General Settings (currently observed values):**

| Setting | Value |
|---|---|
| Enable Differentiated Services | On |
| Optimize C&C and Voice for URLLC | On |
| Optimize Video Streaming | On |
| Video bad link threshold | −95 dBm |
| Video bad link drop | 90 % |
| Optimize for Robustness | On |
| Optimize for Latency over throughput | On |
| Enable Automatic C&C Queue Detection | Off |

**Classification Rules (Doodle Labs defaults, retained):**

| # | Source | Dest | Protocol | Port | DSCP | Comment |
|---|---|---|---|---|---|---|
| 1 | All | All | UDP | 2000 | Voice, C&C (CS6) | `socat raw` |
| 2 | All | All | UDP | 14550 | Voice, C&C (CS6) | `QGC/MAVlink` |

> **PAVLAB note:** these rules are Doodle Labs defaults — we are **not** actively relying on them. We don't currently stream video over the mesh, so *Optimize Video Streaming* could be turned off without losing anything. Document this state for the team; don't change it without a reason.

### 6.8 Wearable Wi-Fi AP Setup

Wearable Wi-Fi is configured on the Setup Wizard (right column, alongside the Mesh Rider config) — **not** on a separate page. For fine-tuning (encryption, antenna, power), switch to **Link Optimization → Wireless → Wi-Fi tab** (§6.5).

| Parameter | Value |
|-----------|-------|
| **Select Scenario** | Access Point |
| **SSID** | per-unit — see §3.6 (varies, e.g., `DoodleLabsAP` or `DRAPER WEARABLE`) |
| **Password** | `Hovergroup!123` (PAVLAB-provisioned units) |
| **Channel** | Auto |

Because Channel is set to Auto, observed channels vary by unit (44 / 5220 MHz and 56 / 5280 MHz were both seen across PAVLAB Wearables).

### 6.9 Network Configuration

Set on the Setup Wizard, beneath the Wi-Fi block. Each radio gets a unique network identity for its role (shore station vs. boat).

**Example — Shore station Wearable (10.223.64.151):**

| Parameter | Value |
|-----------|-------|
| Additional Static IPv4 on BR-WAN | `192.168.1.130` |
| Additional Static IPv4 Netmask | `255.255.255.0` |
| DHCP on BR-WAN | Disabled |
| Enable Automatic C&C Queue Detection | Off |


### 6.10 Utilities → Hotspot Wizard

Sidebar → **Utilities → Hotspot Wizard**. (Formerly labeled "EUD Wizard" in older firmware.) Lets a Wearable join an external Wi-Fi hotspot and NAT mesh traffic out through it.

**Hotspot Configuration:**

| Setting | Default | Purpose |
|---|---|---|
| Enable Hotspot Wizard | Off | Master toggle for hotspot client mode. |
| Internet Access Verification | Off | Pings out after associating to confirm real internet. |
| Auto AP Fallback | Off | If hotspot drops, switch radio back to AP mode automatically. |
| Advanced Logging | On | Detailed connection-event log for debugging. |
| Network Discovery Mode | On | Continuously scan for nearby networks. |

**Network Configuration:** Static IP Configuration toggle (off by default — let DHCP handle it).

**Advanced Timing Configuration:** Connection Timeout (120 s default) — how long to wait before declaring the hotspot dead and falling back.

**Network Discovery panel (right):** live list of nearby SSIDs with RSSI, security, and channel. Click *Connect* on the target to join. Observed at PAVLAB: `yip-bb` (Open, Ch 6), `t4t`, `robotswarm-5G`, `kayak-local-5ghz`, plus our own `pavlab` mesh showing up as WPA3 on Ch 13.

---

## 7. Mesh Network Deployment

### 7.1 How the Mesh Works

The Doodle Labs mesh operates as a **transparent Layer-2 bridge** (think: distributed Ethernet switch). This is the key mental model:

```
  ┌──────────┐                                        ┌──────────┐
  │  Shore   │  Ethernet                    Ethernet   │  Boat    │
  │  Laptop  │ ◄──────► ┌──────┐  RF Link  ┌──────┐ ◄──────►│ Computer │
  │192.168.1 │          │Radio │ ◄════════► │Radio │          │192.168.1 │
  │  .100    │          │Shore │  Mesh Net  │Boat  │          │  .50     │
  └──────────┘          └──────┘            └──────┘          └──────────┘
                        10.223.    ═══════   10.223.
                        64.151     Wireless   64.152

  The computers don't know they're communicating via radio.
  They just see each other on the 192.168.1.x subnet.
  The radios' own 10.223.x.y addresses are separate and
  only needed for radio management.
```

The radios' own IP addresses (10.223.x.y) do **not** need to be on the same subnet as the computers they connect. The mesh simply passes traffic through — it's a "black box network."

### 7.2 Network Topology Diagram

```
                            PAVLAB Mesh Network Topology

                    ┌─────────────────────────────┐
                    │        Shore Station         │
                    │                              │
                    │  ┌────────┐    ┌──────────┐  │
                    │  │ Laptop │◄──►│ Wearable │  │
                    │  │  .100  │USB │  Radio   │  │
                    │  └────────┘    │  .130    │  │
                    │                └────┬─────┘  │
                    └─────────────────────┼────────┘
                                          │
                                     RF Mesh Link
                                  (2.4 GHz, Ch 13/2472 MHz)
                                          │
                          ┌───────────────┼───────────────┐
                          │               │               │
                    ┌─────┴─────┐   ┌─────┴─────┐   ┌────┴──────┐
                    │  Boat #1  │   │  Boat #2  │   │  Boat #3  │
                    │           │   │           │   │           │
                    │ ┌───────┐ │   │ ┌───────┐ │   │ ┌───────┐ │
                    │ │ Mini  │ │   │ │ Mini  │ │   │ │ Mini  │ │
                    │ │ Radio │ │   │ │ Radio │ │   │ │ Radio │ │
                    │ │  .3.2 │ │   │ │  .3.2 │ │   │ │  .3.2 │ │
                    │ └───┬───┘ │   │ └───┬───┘ │   │ └───┬───┘ │
                    │     │     │   │     │     │   │     │     │
                    │ ┌───┴───┐ │   │ ┌───┴───┐ │   │ ┌───┴───┐ │
                    │ │Front  │ │   │ │Front  │ │   │ │Front  │ │
                    │ │Seat   │ │   │ │Seat   │ │   │ │Seat   │ │
                    │ │  1.100│ │   │ │ .1.100│ │   │ │ 1.100 │ │
                    │ └───────┘ │   │ └───────┘ │   │ └───────┘ │
                    └───────────┘   └───────────┘   └───────────┘

     All can reach 192.168.1.x/24 subnet via shoreside radio
     Mesh radios bridged on 10.223.0.0/16 (management only)
     Mesh ID: pavlab  |  Password: hovergroup
```

### 7.3 First-Time Test Procedure

Follow this sequence when setting up a new mesh network:

1. **Configure radios individually.** Power on one radio at a time. Connect via the 10.223 address. Apply the PAVLAB default configuration. Verify settings saved.

2. **Power on both radios simultaneously.** Check the **Dashboard → Associated Stations** tab — it should show the other radio as connected. The RSSI indicator should show signal strength.

3. **Test end-to-end connectivity.** Set up two computers on the same subnet (e.g., `192.168.2.10` and `192.168.2.20`), each connected to a different radio. Ping between them:
   ```bash
   ping 192.168.2.20
   ```

4. **Spacing:** Keep radios at least **5 meters apart** during bench testing to prevent receiver saturation (especially with TPC off).

---

## 8. Firmware, Backup, and Recovery

### 8.1 Configuration Backup

**Web GUI method:**

Navigate to **Device Manager → Firmware** → click **Create Backup** under Backup Operations.

**Legacy method:**

Click Advanced Settings (bottom-left) → System → Backup/Flash Firmware → Generate Archive.

### 8.2 Firmware Upgrade

Firmware can be upgraded Over The Air (OTA) or via Ethernet.

**Web GUI method:**

1. Navigate to `https://<IP>/cgi-bin/luci/admin/system/flashops`
2. Or go to **Device Manager → Firmware** → **Firmware Operations**.
3. **De-select** "Keep Settings" (important for clean upgrades).
4. Click the upload area, select your firmware `.bin` file.
5. Click **Flash Image**. After verification, click **Proceed**.
6. **DO NOT power cycle until the update completes.**

**SSH method:**

```bash
# Copy firmware to the radio
scp -O firmware-sysupgrade.bin root@<IP>:/tmp/

# SSH in and run the upgrade
ssh root@<IP>
sysupgrade -n /tmp/firmware-sysupgrade.bin

# Wait for completion. DO NOT POWER CYCLE.
```

> The `-n` flag does a clean upgrade without preserving settings. Use this for major version jumps.

### 8.3 Factory Reset

Factory reset differs by radio model:

**Wearable (current generation):**

Hold down both the **Turbo** and **Power** buttons together for more than 5 seconds (LEDs will blink fast at 600 ms). Release and wait for the radio to reset.

**Mini-OEM:**

After the radio has been powered on for at least 2 minutes (fully booted), press and hold the **Reset button** on the evaluation board for 10 seconds, then release. If no eval board, pull the **Reset pin** (Port 3, Pin 2) to ground for 10 seconds.

**Web GUI method:**

Navigate to **Device Manager → Firmware** → click **Factory Reset**.

> **Note:** If the factory reset doesn't restore the device, contact `technical_support@doodlelabs.com`.

### 8.4 Configuration Cloning

Doodle Labs provides `configclone.sh` for rapidly replicating configurations across multiple radios while avoiding conflicts (unique IPs, security keys).

```bash
# SSH into the source radio
ssh root@<source-radio-ip>

# Create a backup (prompts for conflict settings)
configclone.sh -b
# Output: /tmp/backup.tar.gz

# Copy to your computer
scp root@<source-ip>:/tmp/backup.tar.gz ./

# Copy to destination radio
scp backup.tar.gz root@<dest-ip>:/tmp/backup.tar.gz

# SSH into destination and restore
ssh root@<dest-ip>
configclone.sh -r    # Interactive restore
# Or: configclone.sh -k  (skip conflicting parameters)
# Or: configclone.sh -o  (overwrite conflicting parameters)
```

---

## 9. Radio API and Custom Interfaces

### 9.1 JSON-RPC API Overview

The Mesh Rider radios expose a JSON-RPC API over HTTP that can be used for programmatic configuration and monitoring. The API is accessible at:

```
https://<RADIO_IP>/ubus
```

This API follows the OpenWrt ubus convention and supports authentication, system queries, and configuration changes. The radios can be managed via:

- **Web GUI** (HTTPs) — visual interface
- **SSH** — command-line access
- **JSON-RPC** — programmatic API access
- **Android/Linux/Windows App** — Doodle Labs companion apps

### 9.2 UCI Configuration Interface

UCI (Unified Configuration Interface) is the primary configuration system on the radio. All settings can be read and modified via SSH:

```bash
# Show all wireless settings
uci show wireless

# Show mesh rider settings
uci show smartradio

# Show wearable-specific settings (Wearable only)
uci show wearable

# Example wearable config output:
# wearable.main.gps_enable='1'
# wearable.main.gps_antenna='1'
# wearable.main.mesh_rider_antennas='1'
# wearable.main.auto_temp_ctrl='1'
# wearable.main.turbo_mode='1'
# wearable.main.throughput_cap='6'

# Show network configuration
uci show network

# Apply changes after modification
uci commit
/etc/init.d/network restart
```

### 9.3 IP Advertiser Discovery

The radio runs an IP advertiser daemon that responds to UDP broadcasts, making it easy to discover all radios on the network programmatically:

```bash
# From a Linux host on the network:
echo "Hello" | socat - udp-datagram:10.223.255.255:11111,broadcast

# Response (JSON):
# {"ingress":["bat0"],"IPaddr":["10.223.187.2/16","192.168.153.1/24","192.168.1.130/24"]}
```

This returns the ingress interface and all IP addresses configured on the responding radio. Useful for auto-discovery of radios in scripts.

### 9.4 GPS Data Access

**File-based access (simple, low overhead):**

```bash
# Via SSH on the radio:
cat /var/run/gps/latitude
cat /var/run/gps/longitude
cat /var/run/gps/altitude
cat /var/run/gps/time
```

**GPSD JSON stream (richer data):**

```bash
# On the radio:
gpspipe -w -n 5

# Returns JSON objects:
# {"class":"TPV","device":"/dev/GPS","mode":3,"time":"...","lat":...,"lon":...,"alt":...}
# {"class":"SKY","device":"/dev/GPS","xdop":0.72,"ydop":0.96,...}
```

**Remote access:** Enable `listen_globally` in the GPS config, then connect to port 2947 from any machine on the mesh:

```bash
# On your laptop:
gpspipe -w -n 5 <radio-ip>:2947
```

### 9.5 Front-Seat Integration (Blue Boats)

On the Blue Boats, the front-seat computer forwards packets to the radio's API to retrieve link quality information (RSSI, throughput, associated stations). This allows the autonomy software to be aware of communication link health.

The front-seat accesses the radio API via the same JSON-RPC/ubus interface, typically querying:

- **Link quality metrics** (RSSI, noise floor, MCS rate)
- **Associated stations** (which radios are in the mesh)
- **GPS coordinates** (if available on the connected radio)
- **System status** (temperature, voltage, uptime)

**Reading temperature and voltage via CLI:**

```bash
# On the Wearable radio:
cat /tmp/run/pancake.txt
# Output: { "Temperature": "33", "VIN VOLTAGE": "185" }
# Actual voltage = VIN_VOLTAGE / 20.2 (e.g., 185/20.2 = 9.16V)
# Temperature is in °C
```

---

## 10. Troubleshooting and Working Notes

**Common issues and solutions:**

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Can't reach radio at all | Wrong subnet on laptop | Set laptop to `10.223.x.y/16` matching radio's label |
| Radio doesn't appear in browser | Using Safari | Switch to Chrome or Firefox |
| Login fails | Wrong password | PAVLAB radios use `DoodleSmartRadio` (Doodle Labs default), not blank |
| Radios don't see each other | Different Mesh ID or password | Verify Setup Wizard settings match on all radios (Mesh ID `pavlab`, password `hovergroup`) |
| Poor range / intermittent link | TPC is on | Disable TPC in Link Optimization → Wireless for maximum power output |
| Bandwidth setting doesn't persist | Single-radio change didn't propagate | Push from Link Optimization → Networkwide Configuration (§6.6) instead of the per-radio page |
| Radio unresponsive after config change | Network misconfiguration | Factory reset (see Section 8.3) and reconfigure |
| Mini-OEM won't boot | Incorrect voltage or polarity | **Verify 5 V ± 5% and correct polarity.** Board may be damaged. |
| Slow throughput | 1x1 SISO mode (Turbo off) | Press Turbo button for 2 sec to switch to 2x2 MIMO |
| GPS shows "unavailable" | No sky view / antenna disconnected | Ensure GPS antenna has clear sky view. Check SMA connection. |

**Working notes for future investigation:**

- *Mesh tuning knobs (§6.4):* OGM interval is at 5000 ms, broadcasts at 1/1, loop avoidance and group-aware multicast-to-unicast routing are both off. These are the right defaults to experiment with if mesh convergence or multicast behavior becomes problematic.
- *Frequency band:* stick with 2.4 GHz for now (Draper radios aren't full dual band), but 900 MHz may offer better range in some scenarios.
- *Optimize for Latency:* already on (toggle lives in Traffic Prioritization, §6.7) — confirmed correct.
- *Optimize Video Streaming:* on by default, but PAVLAB doesn't stream video over the mesh — could be turned off without impact.
- *Bandwidth that won't stick:* use Link Optimization → Networkwide Configuration (§6.6) to push BW/channel changes across the mesh in one shot; single-radio changes are the cause of the long-standing "doesn't persist" gotcha.
- *Wi-Fi AP SSID inconsistency:* PAVLAB Wearables are individually provisioned, so SSIDs differ (`DoodleLabsAP`, `DRAPER WEARABLE`). Worth deciding whether to standardize and re-provision.
- *Web GUI password:* PAVLAB uses the Doodle Labs default (`DoodleSmartRadio`). Consider setting a unique PAVLAB password if these radios ever go on a less-trusted network.
- *Peer Filter (§6.4):* unused. Available as a defense-in-depth tool if we ever want to lock the mesh to a known MAC list.
- *Configclone:* `configclone.sh` remains the right tool for rapidly provisioning new radios with a known-good configuration.

---

## 11. Quick Reference Card

```
╔══════════════════════════════════════════════════════════════════╗
║                PAVLAB DOODLE LABS QUICK REFERENCE                ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  CONNECT TO RADIO                                                ║
║  ─────────────────                                               ║
║  1. Plug into ETH (USB-Host) port on Wearable                   ║
║     or Ethernet (Port 2) on Mini-OEM                             ║
║  2. Set laptop IP: 10.223.64.100  Mask: 255.255.0.0             ║
║  3. Browse to: https://<radio-ip-from-label>                     ║
║  4. Login with password: DoodleSmartRadio                        ║
║                                                                  ║
║  PAVLAB CREDENTIALS                                              ║
║  ──────────────────                                              ║
║  Web GUI password:     DoodleSmartRadio (Doodle Labs default)    ║
║  SSH user:             root (no password)                        ║
║  Mesh ID:              pavlab                                    ║
║  Mesh password:        hovergroup                                ║
║  Wi-Fi AP SSID:        varies per unit (DoodleLabsAP /           ║
║                        DRAPER WEARABLE — see §3.6)               ║
║  Wi-Fi AP password:    Hovergroup!123                            ║
║                                                                  ║
║  KEY SETTINGS (Setup Wizard + Link Optimization)                 ║
║  ─────────────────────────────────────────────                   ║
║  Band: 2450v4 MHz  │  Channel: 13 (2472 MHz)  │  BW: 20 MHz      ║
║  Distance: 1000m   │  TPC: OFF    │  Devices: 3-5                ║
║  Country: GV - Government  │  Mode: N  │  Encryption: WPA2 AES   ║
║                                                                  ║
║  POWER ON                                                        ║
║  ────────                                                        ║
║  Wearable: Hold battery button 4 sec (wait for LEDs)             ║
║  Mini-OEM: Apply 5V to Port 4 (auto-boot) ⚠️ 5V ONLY           ║
║                                                                  ║
║  FACTORY RESET                                                   ║
║  ─────────────                                                   ║
║  Wearable: Hold Turbo + Power until fast blink, release          ║
║  Mini-OEM: Hold Reset pin low for 10 sec after 2 min boot        ║
║                                                                  ║
║  SSH COMMANDS                                                    ║
║  ────────────                                                    ║
║  ssh root@<ip>                   # Connect                       ║
║  uci show wireless               # View radio config             ║
║  uci show network                # View network config           ║
║  cat /var/run/gps/latitude       # Read GPS lat                  ║
║  cat /tmp/run/pancake.txt        # Temp & voltage (Wearable)     ║
║  sysupgrade -n /tmp/fw.bin       # Flash firmware                ║
║  configclone.sh -b               # Backup config                 ║
║                                                                  ║
║  EMERGENCY FALLBACK IP                                           ║
║  ────────────────────                                            ║
║  192.168.153.1/24 (same on ALL radios — single radio only!)     ║
║                                                                  ║
║  SUPPORT: technical_support@doodlelabs.com                       ║
║  DOCS:    https://techlibrary.doodlelabs.com                     ║
╚══════════════════════════════════════════════════════════════════╝
```

---

**Reference documents:**

- [Wearable Datasheet (RM-1700-22W3)](https://techlibrary.doodlelabs.com/nano-oem-dual-band-mesh-rider-radio-915-mhz-and-2450-mhz-ism-bands-1)
- [Mini-OEM Datasheet (RM-1700-22M3)](https://techlibrary.doodlelabs.com/mini-oem-dual-band-mesh-rider-radio-915-mhz-and-2450-mhz-ism-bands)
- [Mesh Rider OS Getting Started](https://techlibrary.doodlelabs.com)
- [Hardware Integration Guidelines](https://techlibrary.doodlelabs.com)
- [Wearable User Guide](https://techlibrary.doodlelabs.com)
- [GPS Guide](https://techlibrary.doodlelabs.com)
- [Backup, Reset, and Upgrade](https://techlibrary.doodlelabs.com)
- [Wearable/OEM Configuration](https://techlibrary.doodlelabs.com)
