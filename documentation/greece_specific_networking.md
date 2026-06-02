# BlueBoat — Greece Field Network Documentation

**Last updated:** June 2026
**Platform:** BlueBoat USV
**Onboard computer:** Raspberry Pi
**Deployment:** Greece field site

---

## 1. Overview

Each BlueBoat in the Greece fleet runs a Raspberry Pi as its onboard computer, managing three network interfaces: a **USB Ethernet uplink** to shore via a DoodleLabs radio, a **wired Ethernet port** (`eth0`) for the backseat payload computer, and an **onboard Wi-Fi access point** (`wlan0`) for wireless field devices. The Pi acts as a router, DHCP server, and firewall between these three domains.

The entire network configuration is driven by a single per-boat config file (`/etc/boat-network.conf`) and three setup scripts that generate systemd-networkd configs, iptables rules, and hostapd settings from it.

On the shore side, the Greece site uses a **Mikrotik RB5009** as the central router at **10.1.0.1**, with a **wAP ax** Wi-Fi access point at **10.1.0.2**, and a **DoodleLabs Wearable Mesh Rider** radio at **10.1.0.3** serving as the shoreside link to the boat fleet. Uplink to the internet is provided by **Starlink** plugged into the RB5009's 2.5G WAN port. The shoreside backbone is **10.1.0.0/24** — different from the lab's 192.168.1.0/24.

### Key Differences from Lab BlueBoat Setup

The Greece deployment uses the same per-boat networking architecture as the lab (systemd-networkd, iptables, hostapd, DoodleLabs link), but the shoreside infrastructure is entirely different:

| Aspect | Lab (Pavlab) | Greece |
|---|---|---|
| Shore subnet | 192.168.1.0/24 | 10.1.0.0/24 |
| Router | Linksys (192.168.1.1) | Mikrotik RB5009 (10.1.0.1) |
| Internet uplink | Lab WAN | Starlink |
| Shoreside radio | DoodleLabs Shoreside (192.168.1.130) | DoodleLabs Wearable (10.1.0.3) |
| Shore Wi-Fi | (lab Wi-Fi) | wAP ax at 10.1.0.2 (Shoreside-5GHz / Shoreside-2GHz) |
| Boat uplink IPs | 192.168.1.131–136 | 10.1.0.31–36 |
| Boat names | zoe, yip, xai, wes, via, uma | asha, bama, chip, dale, ewan, flex |

Per-boat addressing (eth0 at 10.N.1.0/24, wlan0 at 10.N.2.0/24, radio mgmt /30 at 10.N.3.0/30) is unchanged — the BOAT_ID still drives the internal subnets. Only `UPLINK_IP`, `UPLINK_GW`, and `BOAT_NAME` change per deployment.

## 2. Fleet Inventory and IP Assignments

Each Greece boat keeps the same **BOAT_ID** scheme as the lab fleet (31–36), so internal addressing is identical to the lab counterparts. Only the boat names and shore uplink IPs change.

| Vname | BOAT_ID | Uplink IP (Shore) | eth0 Gateway | Backseat IP | wlan0 Gateway | Radio Mgmt (Pi) | Radio Mgmt (Device) |
|---|---|---|---|---|---|---|---|
| asha-bb | 31 | 10.1.0.31 | 10.31.1.1 | 10.31.1.100 | 10.31.2.1 | 10.31.3.1 | 10.31.3.2 |
| bama-bb | 32 | 10.1.0.32 | 10.32.1.1 | 10.32.1.100 | 10.32.2.1 | 10.32.3.1 | 10.32.3.2 |
| chip-bb | 33 | 10.1.0.33 | 10.33.1.1 | 10.33.1.100 | 10.33.2.1 | 10.33.3.1 | 10.33.3.2 |
| dale-bb | 34 | 10.1.0.34 | 10.34.1.1 | 10.34.1.100 | 10.34.2.1 | 10.34.3.1 | 10.34.3.2 |
| ewan-bb | 35 | 10.1.0.35 | 10.35.1.1 | 10.35.1.100 | 10.35.2.1 | 10.35.3.1 | 10.35.3.2 |
| flex-bb | 36 | 10.1.0.36 | 10.36.1.1 | 10.36.1.100 | 10.36.2.1 | 10.36.3.1 | 10.36.3.2 |

> **Addressing formula:** For any boat with BOAT_ID=**N**, its shore IP is **10.1.0.N**, its eth0 subnet is 10.**N**.1.0/24, its wlan0 subnet is 10.**N**.2.0/24, and its radio management /30 is 10.**N**.3.0/30.

### 2.1 Shoreside Inventory

| Device | IP | Role |
|---|---|---|
| Mikrotik RB5009 | 10.1.0.1 | Site router, DHCP server (pool 10.1.0.100–10.1.0.200), default gateway |
| MikroTik wAP ax | 10.1.0.2 | Field Wi-Fi for laptops/tablets — SSIDs `Shoreside-5GHz` and `Shoreside-2GHz` |
| DoodleLabs Wearable Mesh Rider | 10.1.0.3 | Shoreside radio (links to onboard DoodleLabs radios) |
| Starlink | DHCP from Starlink | Internet uplink to RB5009 WAN |

### 2.2 RB5009 Port Map

| Port | Speed | Connected device |
|---|---|---|
| 1 | 2.5G | Starlink uplink (WAN) |
| 2 | 1G | wAP ax |
| 3 | 1G | DoodleLabs Wearable (shoreside radio) |
| 4–8 | 1G | Spare |

## 3. Network Architecture (Per Boat)

### 3.1 Physical Devices and Interfaces

Each BlueBoat has two networked devices and three logical network domains:

**Raspberry Pi (Router/Frontseat)** — The onboard computer with three network interfaces:

- **IF_UPLINK** (`enx*`, USB Ethernet): Connects to the DoodleLabs radio. Carries two addresses — the shore-facing IP (e.g., 10.1.0.31/24) and a secondary /30 alias for radio management (e.g., 10.31.3.1/30). Default route points to 10.1.0.1 (RB5009). No DHCP server on this interface.
- **IF_ETH** (`eth0`, wired Ethernet): The onboard wired LAN. Static IP at 10.**N**.1.1/24. Runs a DHCP server that hands out exactly one lease at .100 (the backseat). IP forwarding enabled.
- **IF_WLAN** (`wlan0`, Wi-Fi AP): An onboard Wi-Fi access point run by hostapd. Static IP at 10.**N**.2.1/24. Runs a DHCP server with a pool from .10 to .249 (240 addresses). IP forwarding enabled. SSID defaults to the boat's vname (e.g., `asha-bb`).

**Backseat (Payload Computer)** — Connected via Ethernet to the Pi's `eth0`. Receives 10.**N**.1.100 via DHCP. Gateway is the Pi at 10.**N**.1.1.

**DoodleLabs Radio (on boat)** — The wireless radio linking the boat to shore. Its management IP is 10.**N**.3.2 on the /30 radio management subnet. It's reachable from the Pi (and from backseat/Wi-Fi clients via NAT) at that address.

### 3.2 Onboard Network Topology

```
                      ┌───────────────────────────────────────────┐
                      │           Raspberry Pi                     │
                      │                                           │
                      │   enx* (USB ETH)    eth0        wlan0     │
                      │   ┌───────────┐  ┌────────┐  ┌─────────┐ │
                      │   │10.1.0.N   │  │10.N.1.1│  │10.N.2.1 │ │
                      │   │  /24      │  │  /24   │  │  /24    │ │
                      │   │10.N.3.1   │  │ DHCP   │  │ DHCP    │ │
                      │   │  /30      │  │ server │  │ server  │ │
                      │   └─────┬─────┘  └───┬────┘  └────┬────┘ │
                      │         │            │             │      │
                      │   IP forwarding + iptables NAT/firewall   │
                      └─────────┼────────────┼─────────────┼──────┘
                                │            │             │
                    ┌───────────┘    ┌───────┘             └───────┐
                    │ (USB ETH)      │ (Ethernet)         (Wi-Fi AP)
                    ▼                ▼                          ▼
         ┌──────────────────┐  ┌──────────────┐    ┌────────────────┐
         │  DoodleLabs      │  │  Backseat    │    │  Wi-Fi Clients │
         │  Radio (boat)    │  │  10.N.1.100  │    │  10.N.2.10-249 │
         │  10.N.3.2/30     │  │  (DHCP)      │    │  (DHCP)        │
         └────────┬─────────┘  └──────────────┘    │  SSID: <vname> │
                  │                                └────────────────┘
            ~~~~ Wireless ~~~~
            (DoodleLabs link)
                  │
         ┌────────┴───────────┐
         │  DoodleLabs        │
         │  Wearable (shore)  │
         │  10.1.0.3          │
         └────────┬───────────┘
                  │ (Ethernet, RB5009 port 3)
         ┌────────┴───────────┐         ┌──────────────────┐
         │  Mikrotik RB5009   │── port 1 ─┤  Starlink (WAN) │
         │  10.1.0.1          │         └──────────────────┘
         │  DHCP .100–.200    │
         └────────┬───────────┘
                  │ (port 2)
         ┌────────┴───────────┐
         │  wAP ax            │
         │  10.1.0.2          │
         │  Shoreside-5GHz    │
         │  Shoreside-2GHz    │
         └────────────────────┘
```

### 3.3 Addressing Scheme (Per Boat)

For a boat with BOAT_ID=**N**:

| Subnet | CIDR | Purpose | Pi Address | Client Addresses |
|---|---|---|---|---|
| Shore uplink | 10.1.0.0/24 | Greece site backbone | 10.1.0.N | — |
| Wired LAN | 10.N.1.0/24 | Backseat + wired payload | 10.N.1.1 | .100 (DHCP, 1 lease) |
| Wi-Fi AP | 10.N.2.0/24 | Wireless field devices | 10.N.2.1 | .10–.249 (DHCP, 240 leases) |
| Radio mgmt | 10.N.3.0/30 | Point-to-point to DoodleLabs radio | 10.N.3.1 | 10.N.3.2 (radio, static) |

### 3.4 Network Configuration (systemd-networkd)

The Pi uses `systemd-networkd` for all interface configuration. The `setup-network-configs.sh` script generates three `.network` unit files from `boat-network.conf`:

**`10-uplink.network`** (IF_UPLINK / enx*):
- Primary address: **10.1.0.N**/24 (Greece shore network)
- Secondary address: 10.**N**.3.1/30 (radio management alias)
- Gateway: **10.1.0.1** (RB5009)
- DNS: 8.8.8.8, 8.8.4.4
- No DHCP server, no IP forwarding on this interface

**`20-eth0-internal.network`** (eth0):
- Address: 10.**N**.1.1/24
- DHCPServer: PoolOffset=100, PoolSize=1 (single lease at .100)
- Lease times: 10s default, 60s max
- IPForward=yes, MulticastDNS=yes

**`30-wlan0-internal.network`** (wlan0):
- Address: 10.**N**.2.1/24
- DHCPServer: PoolOffset=10, PoolSize=240 (.10 through .249)
- Lease times: 1h default, 12h max
- IPForward=yes, MulticastDNS=yes

### 3.5 Wi-Fi Access Point (hostapd)

Each BlueBoat runs hostapd on `wlan0` to create an onboard Wi-Fi network. The `render-hostapd.sh` script generates `/etc/hostapd/hostapd.conf` from the boat config:

- SSID: boat vname (e.g., `asha-bb`)
- Mode: 802.11n (2.4 GHz, hw_mode=g)
- Channel: 6 (configurable per boat — coordinate to avoid co-channel interference with the wAP ax 2.4 GHz radio at shore)
- Auth: open by default (WPA2-PSK available via config)
- Country: **GR** (set `WIFI_COUNTRY="GR"` in `boat-network.conf` for Greek deployment to comply with local regulatory domain)

### 3.6 Routing and Firewall (iptables)

The `setup-boat-routing.sh` script configures IP forwarding and iptables rules:

**Forwarding (sysctl):**
- `net.ipv4.ip_forward=1`
- `net.ipv4.conf.all.rp_filter=2` (loose reverse path filtering, needed because the uplink NIC carries multiple subnets)

**iptables FORWARD chain** (default policy: DROP):
1. ESTABLISHED/RELATED traffic is always allowed
2. eth0 ↔ wlan0 bidirectional forwarding (internal LAN cross-talk)
3. eth0/wlan0 → uplink to radio management subnet (10.N.3.0/30) and back
4. eth0/wlan0 → uplink for general shore/internet access, and return traffic

**iptables NAT (POSTROUTING):**
1. **Radio management SNAT**: Traffic from internal nets destined for the radio management /30 is SNATed to the Pi's radio management IP (10.N.3.1), so the radio sees a source address on its own /30
2. **Internet egress MASQUERADE**: All traffic from 10.N.0.0/16 exiting the uplink is masqueraded behind the Pi's shore IP (10.1.0.N)

## 4. Shoreside Infrastructure

### 4.1 Mikrotik RB5009 (Site Router)

The RB5009 is the central router for the Greece deployment. It runs RouterOS and is statically configured at **10.1.0.1/24** on its bridge of LAN ports.

- **WAN (port 1, 2.5G):** DHCP client toward Starlink. Provides the internet default route for the site.
- **LAN bridge (ports 2–8):** 10.1.0.0/24, DHCP server pool 10.1.0.100–10.1.0.200 for ad-hoc clients (laptops over wAP ax, etc.). Static reservations for the boats are documented in §2.1; the boats themselves use static `UPLINK_IP` and don't request DHCP.
- **NAT:** masquerade out the Starlink WAN for internet egress.
- **Static routes:** see §4.4 — needed so shoreside clients can reach each boat's internal subnets.

### 4.2 MikroTik wAP ax (Shoreside Field Wi-Fi)

The wAP ax provides Wi-Fi for laptops, phones, and tablets at the field site. It is wired to RB5009 port 2 and bridged onto the 10.1.0.0/24 LAN (so clients pull addresses from the RB5009's DHCP pool).

- **Management IP:** 10.1.0.2
- **SSIDs:** `Shoreside-5GHz` and `Shoreside-2GHz`
- **Mode:** AP bridge (no separate routing; transparent L2 to RB5009)

Clients associated with either SSID land directly on 10.1.0.0/24 and can reach the boat fleet through the RB5009's static routes.

### 4.3 DoodleLabs Wearable (Shoreside Mesh Rider)

The DoodleLabs Wearable Mesh Rider acts as the shoreside endpoint of the boat radio link, analogous to the lab's DoodleLabs Shoreside radio.

- **Management IP:** 10.1.0.3
- **Wired:** RB5009 port 3
- **Wireless:** mesh-linked to each boat's onboard DoodleLabs radio. Each boat's Pi appears on this segment at its `UPLINK_IP` (10.1.0.N) as if it were directly on the wired LAN.

> The Wearable replaces the rack-mount shoreside radio used in the lab. It's the same Mesh Rider protocol, just in a portable form factor suitable for field deployment.

### 4.4 RB5009 Static Routes for BlueBoats

The RB5009 needs static routes for each boat's internal subnets so anyone on 10.1.0.0/24 can reach the backseats and Wi-Fi clients on the boats. Each boat requires routes for its eth0 and wlan0 subnets:

| Route Name | Destination | Gateway (Pi Uplink IP) |
|---|---|---|
| bb-asha-eth | 10.31.1.0/24 | 10.1.0.31 |
| bb-asha-wlan | 10.31.2.0/24 | 10.1.0.31 |
| bb-bama-eth | 10.32.1.0/24 | 10.1.0.32 |
| bb-bama-wlan | 10.32.2.0/24 | 10.1.0.32 |
| bb-chip-eth | 10.33.1.0/24 | 10.1.0.33 |
| bb-chip-wlan | 10.33.2.0/24 | 10.1.0.33 |
| bb-dale-eth | 10.34.1.0/24 | 10.1.0.34 |
| bb-dale-wlan | 10.34.2.0/24 | 10.1.0.34 |
| bb-ewan-eth | 10.35.1.0/24 | 10.1.0.35 |
| bb-ewan-wlan | 10.35.2.0/24 | 10.1.0.35 |
| bb-flex-eth | 10.36.1.0/24 | 10.1.0.36 |
| bb-flex-wlan | 10.36.2.0/24 | 10.1.0.36 |

> Alternatively, install a single summary route **10.0.0.0/8 via the appropriate boat** for the connected boats only, or per-boat **10.N.0.0/16** routes. Take care that 10.1.0.0/24 (shore) is the connected interface and not steered to a boat.

On RouterOS this is, per boat:

```
/ip route add dst-address=10.31.1.0/24 gateway=10.1.0.31 comment="bb-asha-eth"
/ip route add dst-address=10.31.2.0/24 gateway=10.1.0.31 comment="bb-asha-wlan"
# ... repeat for each boat
```

## 5. Traffic Flow

### 5.1 Field Laptop → Backseat

1. Laptop on `Shoreside-5GHz` gets 10.1.0.150 via DHCP from RB5009.
2. Laptop sends a packet to asha's backseat at 10.31.1.100. Default gateway is 10.1.0.1.
3. RB5009 matches static route: 10.31.1.0/24 → gateway 10.1.0.31.
4. Packet goes out RB5009 port 3 to the DoodleLabs Wearable, wirelessly to asha's onboard DoodleLabs radio.
5. Radio delivers the packet to the Pi's uplink interface (10.1.0.31).
6. Pi's iptables FORWARD chain allows uplink→eth0. IP forwarding routes the packet out eth0 to 10.31.1.100 (backseat).
7. Return path: Backseat → Pi (gateway 10.31.1.1) → MASQUERADE via uplink → DoodleLabs → RB5009 → laptop.

### 5.2 Backseat → Internet (via Starlink)

1. Backseat (10.31.1.100) sends a packet to 8.8.8.8.
2. Gateway is 10.31.1.1 (Pi).
3. Pi forwards via uplink; iptables MASQUERADE rewrites source to 10.1.0.31.
4. Packet goes via DoodleLabs to shore → RB5009 → masqueraded out the Starlink WAN → internet.

### 5.3 Backseat → DoodleLabs Radio Management

1. Backseat (10.31.1.100) sends a packet to the onboard radio at 10.31.3.2.
2. Pi forwards eth0→uplink. iptables SNAT rewrites source to 10.31.3.1 (so the radio sees a /30-local source).
3. Radio responds to 10.31.3.1 (Pi's /30 alias on the uplink NIC).
4. Pi forwards the response back to 10.31.1.100.

### 5.4 Wi-Fi Client → Backseat (cross-subnet)

1. Wi-Fi client (10.31.2.15) sends a packet to backseat at 10.31.1.100.
2. Client's gateway is 10.31.2.1 (Pi wlan0).
3. Pi's iptables allows wlan0→eth0 forwarding. Packet routed out eth0 to backseat.
4. Return: Backseat → Pi (10.31.1.1) → forwards wlan0 → Wi-Fi client.

### 5.5 Boat-to-Boat (e.g., asha backseat → bama backseat)

1. asha backseat (10.31.1.100) sends a packet to 10.32.1.100. Gateway is 10.31.1.1 (asha Pi).
2. asha Pi forwards via uplink. iptables MASQUERADE rewrites source to 10.1.0.31 (because the destination isn't in the radio mgmt /30, the egress NAT rule applies).
3. DoodleLabs link → Wearable → RB5009. RB5009 matches static route 10.32.1.0/24 → 10.1.0.32 and forwards back over the same DoodleLabs link to bama's Pi.
4. bama Pi receives the packet on its uplink and forwards it out eth0 to 10.32.1.100.
5. Return is symmetric: bama → asha via 10.1.0.31, then back through asha's NAT state.

> **Note:** Because of MASQUERADE on egress, boat-to-boat connections look like they originate from the source boat's `UPLINK_IP`, not from the backseat's `10.N.1.100`. If end-to-end addressing matters (e.g., for shared MOOSDB inspection), connect from a shoreside laptop on 10.1.0.0/24 instead — those flows don't get masqueraded.

## 6. Configuration Scripts

All scripts live in `/etc/` or `/usr/local/bin/` on the Pi and are driven by `/etc/boat-network.conf`.

| Script | Purpose | What it generates |
|---|---|---|
| `boat-network.conf` | Per-boat config (edit this only) | N/A — sourced by all scripts |
| `setup-network-configs.sh` | Interface addressing + DHCP | `10-uplink.network`, `20-eth0-internal.network`, `30-wlan0-internal.network` in `/etc/systemd/network/` |
| `render-hostapd.sh` | Wi-Fi AP config | `/etc/hostapd/hostapd.conf` |
| `setup-boat-routing.sh` | IP forwarding + iptables | sysctl drop-in + iptables rules saved to `/etc/iptables/rules.v4` |

**To configure a Greece boat:** Edit `boat-network.conf` and set:

```bash
BOAT_ID=31                       # or 32..36
BOAT_NAME="asha-bb"              # match BOAT_ID per §2
UPLINK_MODE="static"
UPLINK_IP="10.1.0.31"            # 10.1.0.<BOAT_ID>
UPLINK_PREFIXLEN=24
UPLINK_GW="10.1.0.1"             # RB5009
WIFI_COUNTRY="GR"
```

Then run `setup-network-configs.sh` followed by `setup-boat-routing.sh`. See the first boot guide (`image/first_boot.md`) for the full procedure.

## 7. Useful Commands

- `ip a` — Show all interface addresses (verify uplink has both 10.1.0.N and the /30 alias)
- `ip route` — Show routing table (default should be `via 10.1.0.1`)
- `networkctl status eth0` / `networkctl status wlan0` — Check DHCP server status
- `ping 10.1.0.1` — Test reachability of the RB5009
- `ping 10.N.3.2` — Test connectivity to the onboard DoodleLabs radio
- `curl http://10.N.3.2` — Access radio management HTTP interface
- `curl http://10.1.0.3` — Access the shoreside DoodleLabs Wearable web UI
- `journalctl -u systemd-networkd` — Debug network config issues
- `journalctl -u hostapd` — Debug Wi-Fi AP issues
- `iptables -L -v -n` — View current firewall/forwarding rules
- `iptables -t nat -L -v -n` — View NAT rules
- `tcpdump -ni eth0 icmp` / `tcpdump -ni wlan0 icmp` / `tcpdump -ni <uplink> icmp` — Trace packets across interfaces
