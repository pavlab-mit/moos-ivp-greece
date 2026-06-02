---
status: draft
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: JWenger
---

# DoodleLabs Mesh Rider Radio Configuration

Configuration for the boat's onboard Mini-OEM (RM-1700-22M3) and the shoreside
Wearable (RM-1700-22W3) such that the boat radio meshes with the shore radio
and presents the Pi's uplink as a transparent Ethernet bridge.

This document is the Greece working guide: the context you need, the
connect-and-configure procedure, the radio inventory, and a concise
firmware / recovery / troubleshooting reference. For the full vendor-level
hardware reference (every connector pinout, the JSON-RPC / UCI / GPS API,
detailed LED/button tables), see
[`12b_doodle_labs_radio_reference.md`](12b_doodle_labs_radio_reference.md).

---

## 1. Overview

This guide produces a boat-side Mini-OEM and a shore-side Wearable both joined
to the Greece mesh, with the Wearable's web UI reachable at `10.1.0.3` and each
boat's Mini-OEM reachable at `10.N.3.2` from its Pi. Both radios run the same
Mesh Rider OS (OpenWrt-based) and the same web GUI; they differ in form factor,
power input, and interfaces.

The mesh is a transparent Layer-2 bridge — see §3.2. Addresses on the data
plane (`10.1.0.0/24` shore, `10.N.x.0/24` per boat) come from
[`01_fleet_and_network_reference.md`](01_fleet_and_network_reference.md); the
radios' own `10.223.x.y` management addresses are separate (§3.3).

## 2. Prerequisites

- Radios powered — electrical wiring complete
  ([`11_electrical_wiring.md`](11_electrical_wiring.md)). The Mini-OEM runs
  from port fuse board V1-A via a 5 V buck converter.
- A laptop with **Chrome or Firefox** (avoid Safari — known GUI issues) and the
  ability to set a static IP.
- USB-C cable for the Wearable (use the **ETH / USB-Host** port); Ethernet
  adapter for the Mini-OEM EVK (Port 2).
- Credentials populated in `00_secrets.md`: `{{RADIO_WEBGUI_PASSWORD}}`,
  `{{RADIO_SSH_PASSWORD}}`, `{{RADIO_MESH_ID}}`, `{{RADIO_MESH_PASSWORD}}`,
  `{{RADIO_WIFI_AP_PASSWORD}}`, `{{SHORE_DOODLE_WEBGUI_PASSWORD}}`.

## 3. Context

### 3.1 Form Factors and Where They Live

| Role | Model | Form factor | Where it lives |
|---|---|---|---|
| Boat | RM-1700-22M3 (Mini-OEM) | Bare board, JST connectors | Inside the boat pontoon; **5 V only**; MMCX → N-type via bulkheads |
| Shore | RM-1700-22W3 (Wearable) | Rugged IP67 unit | Shore station; TNC antennas, USB-PD / battery, onboard Wi-Fi + GPS |

Both are 2×2 MIMO dual-band (902–928 MHz and 2400–2482 MHz). The Mini-OEM has
no Wi-Fi and no GPS; the Wearable has both.

### 3.2 The Mesh as a Transparent Bridge

The radios form a self-healing Layer-2 mesh — think of them as a single
distributed Ethernet switch. Computers on each end communicate as if on the
same switch and never address the radios directly. The radios' own
`10.223.x.y` management addresses are unrelated to the data plane: traffic
between a shore laptop and a boat backseat rides the mesh transparently, using
the `10.1.0.0/24` and `10.N.x.0/24` addresses defined in `01`.

### 3.3 IP Addressing Scheme

Every Mesh Rider radio has three default addresses:

| Address | Subnet | Purpose |
|---|---|---|
| `10.223.x.y/16` | Unique per radio | Primary management address, computed from the MAC and printed on the label. |
| DHCP client | Dynamic | Used if a DHCP server exists on the network. |
| `192.168.153.1/24` | Same on **every** radio | Fallback for initial config only — never use with two radios on one network. |

**Computing `10.223.x.y` from the MAC.** Take the last two octets of the MAC,
convert each from hex to decimal: `x = decimal(2nd-to-last octet)`,
`y = decimal(last octet)`. Example: MAC `00:30:1A:3C:40:97` →
`x = 0x40 = 64`, `y = 0x97 = 151` → `10.223.64.151`. This address is on the
label; the per-radio values for the Greece fleet are in §5.

> **Fallback rule.** If you lose connectivity mid-config, return to the
> `10.223.x.y` address from the label — it is the most reliable way back in.

### 3.4 Legacy / PAVLAB Note

> **Lab note.** The reference guide (`12b_doodle_labs_radio_reference.md`) is
> PAVLAB-flavored and references the `pavlab` mesh ID, `hovergroup` password,
> and shore address `192.168.1.130`. None of those are used in Greece — the
> Greece mesh uses `{{RADIO_MESH_ID}}` / `{{RADIO_MESH_PASSWORD}}` and shore
> address `10.1.0.3`. Treat the legacy guide as hardware/API reference only.

## 4. Hardware Reference

Concise tour only; full pinouts, LED/button tables, and the GPS/Wi-Fi detail
are in [`12b_doodle_labs_radio_reference.md`](12b_doodle_labs_radio_reference.md) §3–§4.

### 4.1 Wearable (RM-1700-22W3)

Two TNC antennas (both must be connected before power-on) and a GPS SMA on top;
two USB-C ports on the bottom — **PWR-IN** (power + USB-device) and **ETH**
(USB-host, the preferred laptop port). Powers from the battery pack (hold the
battery button ~4–5 s) or directly from a 20 W+ USB-PD source on PWR-IN
(auto-boots). Includes a 5 GHz Wi-Fi AP and a U-Blox GPS.

### 4.2 Mini-OEM (RM-1700-22M3)

Bare board with JST connectors: Port 1 USB-device, Port 2 Ethernet (100Base-T),
Port 3 UART+Reset, Port 4 power (6-pin), Port 5 USB-host, Port 6 GPIO. Two MMCX
antenna connectors to the pontoon bulkheads. Ensure the RF board is mounted with its heat sink (thermal paste/tape).

> **Critical.** Port 4 is **5 V ± 5% only, with no reverse-polarity
> protection.** Verify voltage and polarity before connecting — wrong voltage
> permanently destroys the board.

## 5. Radio Inventory

Per-radio identifiers for the Greece fleet. The management `10.223.x.y` address
is computed from the MAC (§3.3); the operational management IP (`10.N.3.2`) is
the address the Pi uses on the radio-management /30 (see `01` §5). Fill MAC and
computed `10.223` values as radios are assigned.

| Role | vname | BOAT_ID | Model | MAC | Default mgmt (10.223.x.y) | Operational mgmt |
|---|---|---|---|---|---|---|
| Boat | asha-bb | 31 | RM-1700-22M3 | TBD | TBD | 10.31.3.2 |
| Boat | bama-bb | 32 | RM-1700-22M3 | TBD | TBD | 10.32.3.2 |
| Boat | chip-bb | 33 | RM-1700-22M3 | TBD | TBD | 10.33.3.2 |
| Boat | dale-bb | 34 | RM-1700-22M3 | TBD | TBD | 10.34.3.2 |
| Boat | ewan-bb | 35 | RM-1700-22M3 | TBD | TBD | 10.35.3.2 |
| Boat | flex-bb | 36 | RM-1700-22M3 | TBD | TBD | 10.36.3.2 |
| Shore | — | — | RM-1700-22W3 | TBD | TBD | 10.1.0.3 |

## 6. Connect to a Radio for Configuration

1. Connect physically — Wearable: USB-C laptop cable into the **ETH**
   (USB-host) port if on mac use USB-C to ethernet adapters; Mini-OEM: Ethernet into **Port 2**.
2. Read the `10.223.x.y` address from the radio's label (or compute it from the
   MAC per §3.3).
3. Set the laptop to a static IP in `10.223.0.0/16` — e.g. `10.223.0.5`,
   mask `255.255.0.0`.
4. Browse to `https://<radio-ip>` and accept the self-signed certificate.
5. Log in with `{{RADIO_WEBGUI_PASSWORD}}`. You land on the Dashboard.

> **Tip.** If you don't know the `10.223` address: set the laptop to
> `192.168.153.10/24`, SSH to `192.168.153.1` (user `root`,
> `{{RADIO_SSH_PASSWORD}}`), read the `br-wan` inet address, then switch the
> laptop to that subnet.

## 7. Configure the Boat-Side Mini-OEM

In the **Setup Wizard** (Mesh Rider column):

| Parameter | Value |
|---|---|
| Profile | General |
| Active Frequency Band | `2450v4 MHz` *(placeholder — verify for Greece, see warning)* |
| Scenario | Mesh |
| Mesh ID | `{{RADIO_MESH_ID}}` |
| Wireless Password | `{{RADIO_MESH_PASSWORD}}` |
| Channel | `13 (2472 MHz)` *(placeholder — verify for Greece)* |
| Bandwidth | 20 MHz (push wider from Networkwide Configuration if needed) |
| Operating Distance | set per site (PAVLAB used 1000 m) |
| Number of Devices | active boats + 1 shore |

Then under Network Configuration:

- Additional Static IPv4 on BR-WAN: `10.1.0.<BOAT_ID>` / `255.255.255.0`.
- DHCP on BR-WAN: disabled.
- Save Configuration (apply takes ~1 minute).

In **Link Optimization → Wireless** (Mesh Rider tab):

| Parameter | Value |
|---|---|
| TPC | **Off** (leave off for full power output) |
| Aggressive TPC | Off |
| Country | `GV - Government` *(placeholder — verify Greek regulatory domain)* |
| Mode | N (802.11n) |
| Transmit Power | driver default |
| RX/TX antennas | both enabled (2×2 MIMO) |
| Encryption | WPA2-PSK / AES-128 (CCMP) |

> **Critical.** The frequency band, channel, and country code above are carried
> over from PAVLAB (`2450v4` / Ch 13 / `GV - Government`) as starting
> placeholders. They are **not confirmed legal for Greece.** Verify the Greek
> regulatory domain and update all three before fielding the radios; revisit
> §13 when resolved.

## 8. Configure the Shoreside Wearable

Same Setup Wizard and Link Optimization values as §7, with these differences:

- Network Configuration → Additional Static IPv4 on BR-WAN: `10.1.0.3` /
  `255.255.255.0`; DHCP on BR-WAN disabled.
- Log in with `{{SHORE_DOODLE_WEBGUI_PASSWORD}}` (usually the same as
  `{{RADIO_WEBGUI_PASSWORD}}`, tracked separately in case it diverges).
- The Wearable's onboard 5 GHz Wi-Fi AP is **disabled by default for Greece** —
  the wAP ax is the field Wi-Fi (see
  [`02_shoreside_infrastructure.md`](02_shoreside_infrastructure.md) §8). If it
  is intentionally enabled as a backup AP, set its SSID per site and password
  `{{RADIO_WIFI_AP_PASSWORD}}`.

## 9. Verification

1. Dashboard → Associated Stations shows the other radio with non-zero RSSI.
2. From a laptop on the shore LAN: `ping 10.1.0.<BOAT_ID>` succeeds (the boat
   Pi's uplink).
3. From the boat Pi: `ping 10.1.0.1` succeeds (the RB5009).
4. The Mini-OEM web UI is reachable at `https://10.<BOAT_ID>.3.2` from the Pi.

> **Tip.** Keep radios at least ~5 m apart during bench testing to avoid
> receiver saturation (especially with TPC off).

## 10. Firmware, Backup, and Recovery

- **Backup first.** Device Manager → Firmware → Create Backup, before any
  change.
- **Firmware upgrade.** Device Manager → Firmware → Firmware Operations;
  de-select "Keep Settings" for major version jumps; flash and **do not power
  cycle** until complete. (SSH alternative: `sysupgrade -n /tmp/fw.bin`.)
- **Factory reset.** Wearable: hold Turbo + Power until fast blink, release.
  Mini-OEM: after ≥2 min boot, hold the Reset pin (Port 3 pin 2) low for 10 s.
  Web GUI: Device Manager → Firmware → Factory Reset.
- **Config cloning.** Use `configclone.sh` to provision additional Mini-OEMs
  from a known-good unit. Full procedure in
  [`12b_doodle_labs_radio_reference.md`](12b_doodle_labs_radio_reference.md) §8.4.

## 11. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Can't reach radio | Wrong subnet | Set laptop to `10.223.x.y/16` matching the label. |
| Radio not in browser | Using Safari | Switch to Chrome or Firefox. |
| Login fails | Wrong password | Use `{{RADIO_WEBGUI_PASSWORD}}` from `00_secrets.md`. |
| Radios don't see each other | Mesh ID / password mismatch | Verify the Setup Wizard on both radios. |
| Bandwidth won't persist | Single-radio change | Push from Link Optimization → Networkwide Configuration. |
| Poor / intermittent link | TPC on | Disable TPC in Link Optimization → Wireless. |
| Mini-OEM won't boot | Wrong voltage / polarity | **Verify 5 V ± 5%** and polarity; the board may be damaged. |

## 12. Quick Reference

- **Connect:** plug into ETH (Wearable) / Port 2 (Mini-OEM) → laptop
  `10.223.0.5` / `255.255.0.0` → `https://<radio-ip>` → log in
  `{{RADIO_WEBGUI_PASSWORD}}`.
- **Mesh:** ID `{{RADIO_MESH_ID}}`, password `{{RADIO_MESH_PASSWORD}}`.
- **BR-WAN static IP:** boat `10.1.0.<BOAT_ID>`, shore `10.1.0.3`, mask
  `255.255.255.0`, DHCP off.
- **Key RF (placeholders, verify for Greece):** band `2450v4`, Ch 13, BW
  20 MHz, TPC off, Mode N, Country `GV - Government`, WPA2-PSK / AES-128.
- **Fallback IP:** `192.168.153.1/24` (same on all radios — one radio at a
  time only).
- **SSH:** `ssh root@<ip>` (`{{RADIO_SSH_PASSWORD}}`).

## 13. Change Log

Append-only log of changes to this procedure. One line per change: date —
change — author.

- 2026-06-02 — Initial draft from the radio reference guide, re-flavored for
  the Greece mesh; deep hardware/API reference left in
  `12b_doodle_labs_radio_reference.md` and linked. PAVLAB band/channel/country
  carried as placeholders pending Greek regulatory verification (§7). Radio
  inventory table added (§5). — JWenger
