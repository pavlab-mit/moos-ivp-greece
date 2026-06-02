---
status: stub
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# Shoreside Infrastructure

How to build out the shoreside network for the Greece deployment: Mikrotik
RB5009 router, wAP ax access point, DoodleLabs Wearable shore radio, and
Starlink uplink. Done once per deployment, not per boat.

> **Status: stub.** Content to be lifted from
> `greece_specific_networking.md` §4 (shoreside) and §6 (config scripts),
> with deeper procedural detail than the original (which was reference-
> only).

---

## 1. Overview
_To do._

What this guide produces: a working shoreside backbone at `10.1.0.0/24`
with Starlink WAN, the wAP ax bridging field Wi-Fi onto the LAN, and the
DoodleLabs Wearable acting as the shoreside endpoint of the mesh.

## 2. Prerequisites
_To do._

- RB5009 (RouterOS), wAP ax, Starlink kit, DoodleLabs Wearable on hand.
- Power on site (mains or generator).
- Credentials populated in `00_secrets.md`.
- Field laptop with Ethernet for first-touch RB5009 config.

## 3. Context

### 3.1 Topology
_To do._

Brief on the shore architecture: Starlink → RB5009 (port 1, WAN) → bridge
of ports 2–8 (LAN, `10.1.0.0/24`) → wAP ax (port 2) and DoodleLabs
Wearable (port 3). The wAP ax provides field Wi-Fi for laptops; the
Wearable meshes with each boat's Mini-OEM.

### 3.2 Why `10.1.0.0/24`
_To do._

Greece backbone is `10.1.0.0/24`. Per-boat internals use `10.N.x.0/24`
where `N = BOAT_ID`. The shore-side `10.1.0.0/24` and per-boat
`10.N.x.0/24` ranges are disjoint by construction.

### 3.3 Internet Egress and DNS
_To do._

Starlink provides WAN. RB5009 masquerades out the WAN port. DNS chosen
per-deployment (defaults to public resolvers).

## 4. Hardware Layout

### 4.1 RB5009 Port Map
_To do._

| Port | Speed | Role |
|---|---|---|
| 1 | 2.5G | Starlink WAN |
| 2 | 1G | wAP ax |
| 3 | 1G | DoodleLabs Wearable (shore) |
| 4–8 | 1G | Spare |

### 4.2 Physical Layout
_To do._

Mount points, cable runs, weatherproofing, power source. Photographs (to
be added during build).

## 5. RB5009 Configuration
_To do._

Step-by-step initial config from a laptop on Ethernet:

1. Reset to factory defaults.
2. Set admin password to `{{SHORE_RB5009_PASSWORD}}`.
3. Configure WAN on port 1 (DHCP client toward Starlink).
4. Configure LAN bridge on ports 2–8, address `10.1.0.1/24`.
5. DHCP server pool `10.1.0.100–10.1.0.200`.
6. NAT: masquerade out WAN.
7. Static routes per boat (see §6).
8. Confirm internet from a wired laptop on the LAN.

## 6. Per-Boat Static Routes
_To do._

For every active boat, install two static routes (eth0 and wlan0
subnets) pointing to the boat's uplink IP. Reference the values in
`01_fleet_and_network_reference.md` §6.

```text
/ip route add dst-address=10.<N>.1.0/24 gateway=10.1.0.<N> comment="bb-<vname>-eth"
/ip route add dst-address=10.<N>.2.0/24 gateway=10.1.0.<N> comment="bb-<vname>-wlan"
```

## 7. wAP ax Configuration
_To do._

Step-by-step:

1. Connect wAP ax to RB5009 port 2.
2. Reach management UI; set admin password to `{{SHORE_WAPAX_PASSWORD}}`.
3. Set management IP to `10.1.0.2`.
4. Configure SSIDs `Shoreside-5GHz` and `Shoreside-2GHz`, password
   `{{SHORESIDE_WIFI_PASSWORD}}`.
5. Mode: AP bridge (transparent L2 to RB5009).
6. Verify a laptop on either SSID pulls a `10.1.0.x` lease and can reach
   the internet.

## 8. Shoreside DoodleLabs Wearable
_To do._

Step-by-step (refer to `12_doodle_labs_radio.md` for the full Wearable
procedure):

1. Connect Wearable to RB5009 port 3.
2. Reach Wearable UI at its 10.223.x.y label address; log in with
   `{{SHORE_DOODLE_WEBGUI_PASSWORD}}`.
3. Setup Wizard: mesh ID `{{RADIO_MESH_ID}}`, password
   `{{RADIO_MESH_PASSWORD}}`, same channel/band as boats.
4. Network Configuration → Additional Static IPv4 on BR-WAN:
   `10.1.0.3 / 255.255.255.0`.
5. Disable Wearable Wi-Fi AP unless intentionally serving as backup
   field Wi-Fi (preferred to keep the wAP ax as the sole field AP).

## 9. Starlink
_To do._

Step-by-step:

1. Set up Starlink dish per its install guide; confirm internet from a
   laptop directly attached to Starlink.
2. Connect Starlink Ethernet output to RB5009 port 1.
3. Verify RB5009 WAN gets a lease.
4. Verify internet from a laptop on `Shoreside-5GHz`.

## 10. Verification
_To do._

- Field laptop on `Shoreside-5GHz`: gets a `10.1.0.x` lease, reaches the
  internet, reaches each active boat's `UPLINK_IP`.
- From RB5009: `/ip route print` shows all per-boat static routes
  active.
- Shoreside Wearable Dashboard shows each boat radio as an Associated
  Station with non-zero RSSI.

## 11. Troubleshooting
_To do._

- No internet shoreside: check Starlink direct first, then RB5009 WAN
  lease.
- Field laptop can ping boat Pi but not backseat: per-boat static routes
  missing.
- Shore radio not associating with boats: mesh ID / password / channel
  mismatch — verify against `00_secrets.md`.

## 12. Daily Power-up / Power-down
_To do._

Order of operations to start the day (Starlink → RB5009 → wAP ax →
shore radio) and to end it.
