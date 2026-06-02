---
status: draft
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: JWenger
---

# Shoreside Infrastructure

How to build out the shoreside network for the Greece deployment: Mikrotik
RB5009 router, wAP ax access point, DoodleLabs Wearable shore radio, and
Starlink uplink. Done once per deployment, not per boat.

---

## 1. Overview

This guide produces a working shoreside backbone on `10.1.0.0/24`: Starlink
provides the internet WAN into the RB5009, the RB5009 routes and serves DHCP
for the site, the wAP ax bridges field Wi-Fi onto the LAN, and the DoodleLabs
Wearable acts as the shoreside endpoint of the boat mesh. It is intended for
the person standing up the shore site at the start of a deployment. Per-boat
configuration is covered in the build sequence (`10_…`–`17_…`); this doc stops
at the shore equipment and the routes that let shore clients reach the boats.

All addresses and routes referenced here are defined in
[`01_fleet_and_network_reference.md`](01_fleet_and_network_reference.md). This
doc does not re-derive them.

## 2. Prerequisites

- RB5009 (running RouterOS), wAP ax, Starlink kit, and DoodleLabs Wearable on
  hand.
- Site power available (mains or generator) sufficient for all four devices.
- Credentials populated in `00_secrets.md` (see `00_secrets.template.md` for
  the keys: `SHORE_RB5009_PASSWORD`, `SHORE_WAPAX_PASSWORD`,
  `SHORESIDE_WIFI_PASSWORD`, `SHORE_DOODLE_WEBGUI_PASSWORD`, `RADIO_MESH_ID`,
  `RADIO_MESH_PASSWORD`).
- A field laptop with a wired Ethernet port for first-touch RB5009 and wAP ax
  configuration.
- The active fleet roster and per-boat IP plan from
  `01_fleet_and_network_reference.md` §2 and §5, so you know which boats need
  routes.

## 3. Context

### 3.1 Topology

The shore network is a single Layer-2 LAN behind one router. Starlink feeds
the RB5009's WAN port (port 1). The RB5009's remaining ports (2–8) form a
bridge carrying the `10.1.0.0/24` LAN. The wAP ax hangs off port 2 as a
transparent bridge, providing field Wi-Fi for laptops and tablets; clients on
it land directly on `10.1.0.0/24`. The DoodleLabs Wearable hangs off port 3
and meshes wirelessly with each boat's onboard Mini-OEM radio, so every boat's
Pi appears on the shore LAN at its `UPLINK_IP` (10.1.0.N). The full topology
diagram is in `01` §7.

### 3.2 Why `10.1.0.0/24`

The Greece backbone is `10.1.0.0/24`. Each boat's internal subnets are
`10.N.x.0/24` where `N = BOAT_ID`. Because the shore network is `10.1.0.0/24`
and boats use `10.N.x.0/24` with `N` in 31–36, the shore range and every
per-boat range are disjoint by construction — there is no overlap to manage.
This also differs deliberately from the lab's `192.168.1.0/24` so that lab and
field configs never collide if equipment is moved between them.

### 3.3 Internet Egress and DNS

Starlink is the only WAN. The RB5009 takes a DHCP lease on its WAN port from
Starlink and masquerades all LAN traffic out that port for internet egress.
DNS is chosen per deployment; public resolvers (e.g. 8.8.8.8 / 8.8.4.4) are
the default unless the site requires otherwise. It is important to note that 
starlink is used in this example to be fully self-sufficient but any WAN 
connection that assigns an ip to the RB5009 would work.

## 4. Hardware Layout

### 4.1 RB5009 Port Map

| Port | Speed | Role |
|---|---|---|
| 1 | 2.5G | Starlink WAN |
| 2 | 1G | wAP ax |
| 3 | 1G | DoodleLabs Wearable (shore) |
| 4–8 | 1G | Spare |

### 4.2 Physical Layout

Mount the RB5009, wAP ax, and Wearable so that cable runs are short and the
Wearable has the clearest possible line of sight to the operating area. Record
mount points, cable runs, power source, and any weatherproofing applied.

> **Note.** Photographs of the as-built shore setup should be added here
> during the build.

## 5. RB5009 Configuration

Connect the field laptop to a LAN port (2–8) and reach the router's
management interface. Then:

1. Reset to factory defaults so you start from a known state.
2. Set the admin password to `{{SHORE_RB5009_PASSWORD}}`.
3. Configure the WAN on port 1 as a DHCP client toward Starlink.
4. Configure the LAN bridge across ports 2–8 with address `10.1.0.1/24`.
5. Enable a DHCP server on the LAN bridge with pool `10.1.0.100–10.1.0.200`.
6. Enable NAT (masquerade) out the WAN port for internet egress.
7. Add the per-boat static routes (see §6).
8. Confirm internet access from a wired laptop on the LAN before moving on.

> **Note.** Exact RouterOS commands are intentionally not reproduced here;
> follow current MikroTik documentation for the installed RouterOS version and
> record the commands actually used during the build.

## 6. Per-Boat Static Routes

For every active boat, install two static routes — one for its `eth0` subnet
and one for its `wlan0` subnet — pointing at the boat's uplink IP. The
authoritative list is in
[`01_fleet_and_network_reference.md` §6](01_fleet_and_network_reference.md#6-rb5009-static-routes);
add only the routes for boats actually deployed.

The RouterOS form, per boat, is:

```text
/ip route add dst-address=10.<N>.1.0/24 gateway=10.1.0.<N> comment="bb-<vname>-eth"
/ip route add dst-address=10.<N>.2.0/24 gateway=10.1.0.<N> comment="bb-<vname>-wlan"
```

> **Note.** Keep `10.1.0.0/24` as the connected shore interface — never route
> it to a boat. A per-boat `10.N.0.0/16` summary route is an acceptable
> substitute for the two /24 routes if preferred.

## 7. wAP ax Configuration

1. Connect the wAP ax to RB5009 port 2.
2. Reach its management UI and set the admin password to
   `{{SHORE_WAPAX_PASSWORD}}`.
3. Set its management IP to `10.1.0.2`.
4. Configure the two field SSIDs, `Shoreside-5GHz` and `Shoreside-2GHz`, both
   with password `{{SHORESIDE_WIFI_PASSWORD}}`.
5. Run it in AP-bridge mode so it is transparent Layer-2 to the RB5009 (no
   routing or DHCP on the wAP ax itself).
6. Verify a laptop on either SSID pulls a `10.1.0.x` lease from the RB5009 and
   can reach the internet.

> **Note.** Coordinate the wAP ax 2.4 GHz channel with the boats' onboard
> Wi-Fi APs to avoid co-channel interference (the boats default to channel 6).

## 8. Shoreside DoodleLabs Wearable

This is the shore end of the boat mesh. For the full Wearable procedure see
[`12_doodle_labs_radio.md`](12_doodle_labs_radio.md); the shore-specific steps
are:

1. Connect the Wearable to RB5009 port 3.
2. Reach the Wearable's MeshRider UI at its factory label address and log in
   with `{{SHORE_DOODLE_WEBGUI_PASSWORD}}`.
3. In the setup wizard, set mesh ID `{{RADIO_MESH_ID}}` and password
   `{{RADIO_MESH_PASSWORD}}`, using the same channel and band as the boat
   radios.
4. Add a static IPv4 address `10.1.0.3 / 255.255.255.0` on the WAN bridge so
   the Wearable is reachable on the shore LAN.
5. Disable the Wearable's own Wi-Fi AP unless it is intentionally serving as a
   backup field Wi-Fi — keeping the wAP ax as the sole field AP is preferred.

## 9. Starlink

1. Set up the Starlink dish per its own install guide and confirm internet
   from a laptop attached directly to Starlink.
2. Connect Starlink's Ethernet output to RB5009 port 1.
3. Confirm the RB5009 WAN port obtains a DHCP lease from Starlink.
4. Confirm internet from a laptop on `Shoreside-5GHz`.

## 10. Verification

- A field laptop on `Shoreside-5GHz` gets a `10.1.0.x` lease, reaches the
  internet, and can reach each active boat's `UPLINK_IP`.
- On the RB5009, the routing table shows every per-boat static route as
  active.
- The Wearable's dashboard shows each boat radio as an associated station with
  non-zero RSSI.

## 11. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No internet anywhere on shore | Starlink down, or RB5009 WAN has no lease | Test internet on a laptop directly on Starlink first; then check the RB5009 WAN lease. |
| Laptop can ping a boat's Pi but not its backseat | Per-boat static routes missing or wrong | Confirm both `eth0` and `wlan0` routes for that boat exist and point at the right uplink IP (`01` §6). |
| Shore radio not associating with boats | Mesh ID, password, channel, or band mismatch | Verify the Wearable's mesh settings against `00_secrets.md` and the boat radios. |
| Field laptop gets no Wi-Fi lease | wAP ax not bridged, or DHCP not reaching it | Confirm the wAP ax is in AP-bridge mode and wired to RB5009 port 2. |

## 12. Daily Power-up / Power-down

**Power-up (in order):** Starlink → RB5009 → wAP ax → DoodleLabs Wearable.
Wait for Starlink to acquire internet before expecting WAN on the RB5009.

**Power-down (reverse order):** Wearable → wAP ax → RB5009 → Starlink.

## 13. Change Log

Append-only log of shoreside changes (device replaced, IP plan revised, config
updated). One line per change: date — change — author.

- 2026-06-02 — Initial draft; sections fleshed out from `greece_specific_networking.md` §4 with descriptive procedure steps. — JWenger
