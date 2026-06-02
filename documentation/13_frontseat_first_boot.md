---
status: stub
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# Frontseat First Boot

How to bring up a new Raspberry Pi as a Greece BlueBoat frontseat from a
cloned/donor SD image. By the end of this doc the boat has a unique
hostname, correct network configuration, working routing/NAT, and can be
reached from shore via the DoodleLabs link.

> **Status: stub.** Content to be lifted from `first_boot.md`, stripped of
> Lab-vs-Greece dual-tracking (Greece-only), and re-flowed to put context
> in §3 and procedures in §§4+. Radio configuration is a prerequisite, not
> a parallel task — see `12_doodle_labs_radio.md`.

---

## 1. Overview
_To do._

What this guide produces: a fresh Pi with the correct hostname, networking,
firewall, and routing, that can be reached from shore through the already-
configured DoodleLabs link.

## 2. Prerequisites
_To do._

- Donor SD image (e.g., `yip-backup.img`).
- 32 GB+ SD card.
- The new boat's `BOAT_ID`, `BOAT_NAME`, `UPLINK_IP` from
  `01_fleet_and_network_reference.md`.
- DoodleLabs radio configured (`12_doodle_labs_radio.md`) and powered.
- A way to reach the Pi: Wi-Fi to the donor's AP, or Ethernet on `eth0`
  with the backseat unplugged.
- Credentials populated in `00_secrets.md`.
- Optional: USB-C keyboard + micro-HDMI cable for console fallback.

## 3. Context

### 3.1 Why the Donor Image Approach
_To do._

We image from a known-good donor rather than installing from scratch so the
toolchain, MOOS build, systemd services, and per-boat scripts come along
for free. The cost is a handful of donor-identity items that must be reset
(hostname, network config, SSH keys, history). Those resets are the body of
this guide.

### 3.2 Convention Used Below
_To do._

`<donor>` = `BOAT_ID` of the source image (e.g., 34 for a Wes-derived image).
`<new>` = `BOAT_ID` of the boat you're setting up.
Commands run on the Pi unless otherwise noted.

### 3.3 What Stays vs. What Changes
_To do._

Table: hostname, `/etc/boat-network.conf`, `~/.ssh/authorized_keys`, deploy
keys, `pi` password — change. systemd-networkd scripts, hostapd render
script, MOOS tree, build artifacts — stay (regenerated from the new
config).

## 4. Flash the Image
_To do._

Step-by-step:

1. Insert SD card into laptop.
2. Flash with Raspberry Pi Imager (custom image) or `dd`. Identify the
   target disk carefully — wrong target erases the laptop.
3. Eject cleanly.

## 5. First Boot from the Donor Image
_To do._

Step-by-step:

1. Insert SD into the new Pi; power up.
2. Wait ~60 s. The Pi comes up as the donor (same hostname, same SSID,
   same internal addressing). Expected; about to change.

## 6. Connect to the New Pi
_To do._

Two options. Wi-Fi is recommended because it survives the `eth0`
reconfiguration in §8 without re-plugging.

### 6.1 Wi-Fi (recommended)
_To do._

1. Join the SSID matching the donor's `BOAT_NAME` (e.g., `wes-bb`).
2. Confirm DHCP lease in `10.<donor>.2.0/24`.
3. `ssh pi@10.<donor>.2.1` using `{{PI_DEFAULT_PASSWORD}}`.

### 6.2 Ethernet
_To do._

1. Unplug backseat from `eth0`.
2. Plug laptop into `eth0`.
3. DHCP into `10.<donor>.1.100`.
4. `ssh pi@10.<donor>.1.1`.

> **Tip.** If `known_hosts` complains, the donor image previously claimed
> this address — `ssh-keygen -R 10.<donor>.2.1` or accept the new key.

## 7. Change Hostname
_To do._

Step-by-step:

1. `sudo vim /etc/hostname` — replace donor name with new (`<vname>-bb`).
2. `sudo vim /etc/hosts` — update `127.0.1.1` line.
3. `sudo reboot`.
4. SSH back in (still at the donor's IP — network hasn't changed yet).
5. `hostnamectl` to confirm.

## 8. Expand Filesystem
_To do._

`sudo raspi-config` → 6 Advanced Options → A1 Expand Filesystem → reboot.
Verify with `df -h /`.

## 9. Update `/etc/boat-network.conf`
_To do._

Step-by-step:

1. `sudo vim /etc/boat-network.conf`.
2. Set `BOAT_ID`, `BOAT_NAME`, `UPLINK_MODE="static"`, `UPLINK_IP`,
   `UPLINK_PREFIXLEN=24`, `UPLINK_GW="10.1.0.1"`, `UPLINK_DNS`,
   `WIFI_COUNTRY="GR"`.
3. Sanity-check: `bash -n /etc/boat-network.conf` and source it to echo
   the values.

## 10. Apply Network Config
_To do._

Step-by-step:

1. `sudo /usr/local/bin/setup-network-configs.sh` (regenerates the three
   `.network` files and `/etc/hostapd/hostapd.conf`, restarts services).
2. **You will lose connectivity on the current path.** Reconnect:
   - Wi-Fi: rejoin the new SSID `<vname>-bb`; new lease in
     `10.<new>.2.0/24`; Pi at `10.<new>.2.1`.
   - Ethernet: renew DHCP; SSH to `pi@10.<new>.1.1`.
3. Verify with `ip -br a` and `ip route`.
4. `sudo reboot` and re-verify after reboot.

## 11. Apply Routing and Firewall Rules
_To do._

Step-by-step:

1. `sudo /usr/local/bin/setup-boat-routing.sh`.
2. Verify: `iptables -L FORWARD -v -n`, `iptables -t nat -L POSTROUTING
   -v -n`, `sysctl net.ipv4.ip_forward`, `sysctl
   net.ipv4.conf.all.rp_filter`.

## 12. Verify End-to-End Connectivity
_To do._

From the Pi: ping `10.1.0.1`, `8.8.8.8`, and the radio at `10.<new>.3.2`.
From the backseat (re-plugged): ping the Pi, the uplink gateway, the
internet. From a shoreside laptop: ping the Pi and the backseat after the
RB5009 static routes are in place (see `01_fleet_and_network_reference.md`
§6).

## 13. Replace Default Password and SSH Keys
_To do._

Step-by-step:

1. `passwd` — change from `{{PI_DEFAULT_PASSWORD}}` to
   `{{PI_FIELD_PASSWORD}}`.
2. Edit `~/.ssh/authorized_keys` — remove keys for users who shouldn't
   have access; leave only current operators + deploy keys.
3. Swap deploy keys per `16_software_build.md`.

## 14. Clean Up Donor Cruft
_To do._

Step-by-step:

1. Remove stale MOOS trees (`moos-ivp-seascout`, `moos-ivp-diasho-usv`,
   `moos-ivp-pavlab`).
2. Clear donor identity: `> ~/.bash_history`, `> ~/.ssh/known_hosts`.

## 15. Verification
_To do._

Final sanity checks before declaring the Pi ready (full QC happens in
`20_qc_signoff.md`):

- `hostnamectl` shows the new name.
- `df -h /` reflects the full SD card.
- `/etc/boat-network.conf` matches the fleet plan.
- `ip -br a` and `ip route` look correct.
- hostapd is up; new SSID is broadcasting.
- Backseat DHCPs into `10.<new>.1.100`.
- Pi can ping `10.<new>.3.2` (radio).

## 16. Troubleshooting
_To do._

- New SSID not visible: check hostapd, `WIFI_COUNTRY`, channel legality.
- No default route: `UPLINK_GW` unset, or wrong NIC matched
  `IF_UPLINK="enx*"`.
- Backseat can't reach internet: MASQUERADE missing, `ip_forward=0`.
- Shoreside can ping Pi but not backseat: RB5009 static route missing.
- Radio at `10.<new>.3.2` unreachable: radio not addressed; check the
  uplink NIC has both 10.1.0.N and 10.<new>.3.1.
