---
status: stub
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# Fleet and Network Reference

Authoritative reference for the Greece deployment: which boats exist, their
identifiers, IP assignments, and the shoreside infrastructure they connect
to. Every other doc in this folder assumes these values.

> **Status: stub.** Content to be migrated from `greece_specific_networking.md`
> and re-organized as a pure reference (no procedures).

---

## 1. Overview
_To do._

Brief description of the Greece site, the operating model (one shore site,
N boats), and the role of this document as the source of truth for IDs and
IPs.

## 2. Fleet Roster
_To do._

Per-boat table: vname, BOAT_ID, hull serial, owner. The IP-derivation
formula belongs in §4.

## 3. Shoreside Inventory
_To do._

Per-device table: RB5009, wAP ax, shoreside DoodleLabs Wearable, Starlink,
field laptops. Each row has role, model, management IP, MAC, location.

## 4. Addressing Scheme
_To do._

The deterministic formula: for `BOAT_ID=N`, shore IP is `10.1.0.N`, eth0
subnet `10.N.1.0/24`, wlan0 subnet `10.N.2.0/24`, radio mgmt `10.N.3.0/30`.
Worked examples for two boats.

## 5. Per-Boat IP Plan
_To do._

Materialized table for every active BOAT_ID: shore IP, eth0 gateway,
backseat IP, wlan0 gateway, radio mgmt /30 ends.

## 6. RB5009 Static Routes
_To do._

Required `/ip route` entries for the RB5009 to reach each boat's internal
subnets. One row per boat per internal subnet.

## 7. Network Topology
_To do._

Top-down diagram showing shore (RB5009 + wAP ax + shore radio + Starlink)
linked via DoodleLabs mesh to the boat fleet (one block per boat with its
Pi + radio + backseat).

## 8. Per-Boat Onboard Topology
_To do._

Drilldown diagram for a single boat: Pi with three NICs, eth0 to backseat,
wlan0 to field Wi-Fi clients, USB-Ethernet uplink to boat radio. NAT and
forwarding rule summary.

## 9. Traffic Flows
_To do._

Walk through five representative flows: shore laptop → backseat,
backseat → internet, backseat → radio mgmt, Wi-Fi client → backseat,
boat-to-boat.

## 10. Glossary of Identifiers
_To do._

`BOAT_ID`, `BOAT_NAME`, `vname`, `UPLINK_IP`, `UPLINK_GW`, `WIFI_COUNTRY`.
What each is, where it's set, what consumes it.

## 11. Change Log
_To do._

Append-only log of fleet-level changes: boat added/retired, shore device
replaced, IP plan revised.
