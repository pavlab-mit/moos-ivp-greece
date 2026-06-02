---
status: stub
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# DoodleLabs Mesh Rider Radio Configuration

Configuration for the boat's onboard Mini-OEM (RM-1700-22M3) and the
shoreside Wearable (RM-1700-22W3) such that the boat radio meshes with the
shore radio and presents the Pi's uplink as a transparent Ethernet bridge.

> **Status: stub.** Content to be lifted from `Doodle_Labs_Radio_Guide.md`,
> stripped of PAVLAB-specific identifiers, and re-flavored for the Greece
> mesh (`{{RADIO_MESH_ID}}`, `{{RADIO_MESH_PASSWORD}}`).

---

## 1. Overview
_To do._

What this guide produces: a boat-side Mini-OEM and a shore-side Wearable
both joined to the Greece mesh, with the Wearable's web UI reachable at
10.1.0.3 and the Mini-OEM reachable at 10.N.3.2 from the Pi.

## 2. Prerequisites
_To do._

Radios powered (electrical wiring complete). Laptop with Chrome/Firefox.
USB-C cable for the Wearable; Ethernet adapter for the Mini-OEM EVK.
Credentials populated in `00_secrets.md`.

## 3. Context

### 3.1 Form Factors and Where They Live
_To do._

Mini-OEM inside the boat pontoon (bare board, 5 V only, MMCX→N-type via
bulkheads). Wearable as the shoreside endpoint (TNC antennas, USB-PD,
battery pack).

### 3.2 The Mesh as a Transparent Bridge
_To do._

Mental model: the radios are a distributed Ethernet switch. Computers don't
see the radios; they see each other. The 10.223.x.y management addresses
are unrelated to the data plane.

### 3.3 IP Addressing Scheme
_To do._

Three addresses per radio: 10.223.x.y (from MAC, primary management), DHCP
(if available), 192.168.153.1 (fallback, same on every radio — never use
with two radios on the same network). How to compute 10.223.x.y from the
MAC label.

### 3.4 PAVLAB Note
_To do._

> **Lab note.** Older copies of this guide reference the `pavlab` mesh ID
> and PAVLAB passwords. Those are not used in Greece; refer to
> `00_secrets.md` for the current Greece values.

## 4. Hardware Reference

### 4.1 Wearable (RM-1700-22W3)
_To do._

Hardware tour: TNC antennas, GPS SMA, USB-C PWR-IN, USB-C ETH (host),
battery pack, LEDs, buttons. Power-on procedure. GPS module presence.

### 4.2 Mini-OEM (RM-1700-22M3)
_To do._

Hardware tour: MMCX antennas, JST pinouts for power / USB / Ethernet / UART
/ GPIO. **Critical:** 5 V ± 5% only, no reverse-polarity protection.
Thermal management against the pontoon as a heat sink.

## 5. Connect to a Radio for Configuration
_To do._

Step-by-step:

1. Connect physically (Wearable: USB-C to ETH port; Mini-OEM: Ethernet to
   Port 2).
2. Note the 10.223.x.y address from the label.
3. Set the laptop static IP to 10.223.0.5 / 255.255.0.0 (or any unused
   address in /16).
4. Open `https://<radio-ip>`; accept the self-signed certificate.
5. Log in with `{{RADIO_WEBGUI_PASSWORD}}`.

## 6. Configure the Boat-Side Mini-OEM
_To do._

Step-by-step using the Setup Wizard:

1. **Profile:** General.
2. **Active Frequency Band:** _to choose_ (current Greece value: TBD).
3. **Scenario:** Mesh.
4. **Mesh ID:** `{{RADIO_MESH_ID}}`.
5. **Wireless Password:** `{{RADIO_MESH_PASSWORD}}`.
6. **Channel:** _to choose_ (coordinate with shore Wi-Fi).
7. **Bandwidth:** 20 MHz initially; push wider from Networkwide Config if
   needed.
8. **Operating Distance:** _to set per site_.
9. **Number of Devices:** N boats + 1 shore.
10. Set Network Configuration → Additional Static IPv4 on BR-WAN to
    `10.1.0.<BOAT_ID>` / `255.255.255.0`; disable DHCP on BR-WAN.
11. Save Configuration.

Then in Link Optimization → Wireless (Mesh Rider tab):

- TPC: **Off**.
- Aggressive TPC: Off.
- Country: _confirm Greek regulatory domain_.
- Mode: N.
- Transmit Power: driver default.
- RX/TX antennas: both enabled (2×2 MIMO).
- Encryption: WPA2-PSK / AES-128 (CCMP).

## 7. Configure the Shoreside Wearable
_To do._

Same Setup Wizard fields as §6, with these differences:

- Network Configuration → Additional Static IPv4 on BR-WAN: `10.1.0.3` /
  `255.255.255.0`.
- Wi-Fi block: AP mode, SSID `{{SHORESIDE_WIFI_SSID}}`, password
  `{{RADIO_WIFI_AP_PASSWORD}}`. (Note: this is the Wearable's onboard
  Wi-Fi, distinct from the shoreside wAP ax — see
  `02_shoreside_infrastructure.md`.)

## 8. Verification
_To do._

1. Dashboard → Associated Stations shows the other radio with non-zero RSSI.
2. From a laptop on the shore LAN: `ping 10.1.0.<BOAT_ID>` succeeds (the
   boat Pi's uplink).
3. From the boat Pi: `ping 10.1.0.1` succeeds.
4. Mini-OEM web UI reachable at `https://10.<BOAT_ID>.3.2` from the Pi.

## 9. Firmware, Backup, Recovery
_To do._

- Backup before any change: Device Manager → Firmware → Create Backup.
- Firmware upgrade procedure (deselect Keep Settings for major jumps).
- Factory reset procedure for Wearable and Mini-OEM.
- Configclone for rapid provisioning of additional Mini-OEMs.

## 10. Troubleshooting
_To do._

| Symptom | Likely cause | Fix |
|---|---|---|
| Can't reach radio | Wrong subnet | Set laptop to `10.223.x.y/16` matching label. |
| Login fails | Wrong password | Use `{{RADIO_WEBGUI_PASSWORD}}` from `00_secrets.md`. |
| Radios don't see each other | Mesh ID / password mismatch | Verify Setup Wizard on both. |
| Bandwidth setting doesn't persist | Single-radio change | Push from Link Optimization → Networkwide Configuration. |
| Mini-OEM won't boot | Wrong voltage / polarity | **Verify 5 V ± 5%**; board may be damaged. |

## 11. Quick Reference
_To do._

At-a-glance card: connect procedure, default credentials by key, key
settings, factory reset shortcuts.
