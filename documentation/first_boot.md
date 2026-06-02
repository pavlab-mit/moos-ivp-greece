# BlueBoat — First Boot Guide

How to bring up a new BlueBoat from a cloned/donor SD card image. Covers both the lab fleet and the Greece field deployment. Greek-specific notes are flagged inline with **[Greece]**.

---

## 0. Before You Start

**You will need:**

- The donor image (e.g., `yip-backup.img` from `image/`).
- An SD card (32 GB or larger recommended; class 10 / A2 if available).
- An SD card reader on your laptop.
- The new boat's intended **BOAT_ID**, **BOAT_NAME**, and **UPLINK_IP**.
  - Lab fleet: see `blueboat_network_documentation.md` §2.
  - Greece fleet: see `greece_specific_networking.md` §2.
- A way to talk to the Pi for first-touch configuration. The two reliable options are:
  1. **Wi-Fi (recommended):** join the donor boat's onboard AP (SSID is the donor's `BOAT_NAME`, e.g., `wes-bb`). You'll be at `10.<donor>.2.X`, Pi at `10.<donor>.2.1`.
  2. **Ethernet:** plug your laptop directly into the Pi's `eth0`. You'll DHCP a single lease at `10.<donor>.1.100`. The backseat normally occupies that lease, so unplug the backseat first.
- Optional but useful: a USB-C keyboard + micro-HDMI cable in case something goes wrong with networking and you need console access.

**Conventions in this guide:**

- `<donor>` = the BOAT_ID of the image you cloned from (e.g., 34 for a Wes-derived image).
- `<new>` = the BOAT_ID of the boat you're setting up.
- Commands are run **on the Pi** unless otherwise noted.

---

## 1. Flash the Image

On your laptop:

1. Insert the SD card into your reader.
2. Flash the donor image. Either:
   - **Raspberry Pi Imager:** "Use custom" → select the donor `.img` → choose the SD card → Write. Skip the OS customization screen (we want the image as-is).
   - **CLI (Linux/macOS):**
     ```bash
     # IDENTIFY THE RIGHT DISK FIRST — wrong target erases your laptop.
     diskutil list        # macOS
     lsblk                # Linux
     # Then (example for /dev/disk4 on macOS or /dev/sdX on Linux):
     sudo dd if=yip-backup.img of=/dev/rdiskN bs=4m status=progress
     ```
3. Eject the SD card cleanly.

---

## 2. First Boot from the Donor Image

1. Insert the SD card into the new Pi.
2. Power up. Give it ~60 seconds.
3. The Pi will come up as the **donor boat** — same hostname, same SSID, same internal addressing. That's expected; we're about to change it.

---

## 3. Connect to the New Pi

Pick one method. Wi-Fi is recommended because it survives the eth0 reconfiguration in §6 without you having to re-plug anything.

**Option A — Wi-Fi (recommended):**

1. On your laptop, join the SSID matching the donor `BOAT_NAME` (e.g., `wes-bb`). It's an open network unless the donor was configured otherwise.
2. Confirm you got a DHCP lease in `10.<donor>.2.0/24`.
3. SSH in:
   ```bash
   ssh pi@10.<donor>.2.1
   # default password: raspberry
   ```

**Option B — Ethernet:**

1. Disconnect the backseat from the Pi's `eth0`.
2. Plug your laptop into `eth0`.
3. You should DHCP into `10.<donor>.1.100`.
4. SSH:
   ```bash
   ssh pi@10.<donor>.1.1
   ```

> **First-time SSH:** if you've SSHed to a boat at this IP before (a previous donor), your `known_hosts` will complain. Either `ssh-keygen -R 10.<donor>.2.1` or accept the new key — this is a freshly imaged Pi.

---

## 4. Change Hostname

The hostname needs to change before anything else so logs, mDNS, and prompts reflect the new boat.

```bash
sudo vim /etc/hostname
# Replace donor name with new name, e.g. asha-bb
sudo vim /etc/hosts
# Update the 127.0.1.1 line to match — e.g.
#   127.0.1.1   asha-bb
sudo reboot
```

After reboot, SSH back in (still at the donor's IP — network hasn't changed yet) and confirm:

```bash
hostnamectl
# Static hostname: asha-bb
```

---

## 5. Expand the Filesystem

Donor images are often shrunk to fit the source SD card. Expand the root partition to fill the new card:

```bash
sudo raspi-config
# → 6 Advanced Options
# → A1 Expand Filesystem
# → Finish → reboot when prompted
```

Confirm after reboot:

```bash
df -h /
# Should reflect the full SD card size, not the donor image size.
```

---

## 6. Update `/etc/boat-network.conf`

This is the heart of the per-boat configuration. Open it:

```bash
sudo vim /etc/boat-network.conf
```

Set these fields for the new boat:

| Field | Lab fleet | Greece fleet |
|---|---|---|
| `BOAT_ID` | e.g. `31` (Zoe) — see lab doc §2 | e.g. `31` (asha) — see Greece doc §2 |
| `BOAT_NAME` | `"zoe-bb"` | `"asha-bb"` |
| `UPLINK_MODE` | `"static"` | `"static"` |
| `UPLINK_IP` | `"192.168.1.131"` (192.168.1.(100+BOAT_ID)) | `"10.1.0.31"` (10.1.0.BOAT_ID) |
| `UPLINK_PREFIXLEN` | `24` | `24` |
| `UPLINK_GW` | `"192.168.1.1"` (Linksys) | `"10.1.0.1"` (RB5009) |
| `UPLINK_DNS` | `("8.8.8.8" "8.8.4.4")` | `("8.8.8.8" "8.8.4.4")` |
| `WIFI_COUNTRY` | `"US"` | `"GR"` |

Leave everything else (interface names, internal subnet derivation, DHCP pools, Wi-Fi auth) as the donor had it unless you have a specific reason to change.

**[Greece]** Double-check `WIFI_COUNTRY="GR"` — it affects which channels hostapd is allowed to use. Wrong country code is a common reason hostapd refuses to start.

Sanity-check the file by sourcing it in a shell:

```bash
bash -n /etc/boat-network.conf   # syntax check
( source /etc/boat-network.conf && echo "ID=$BOAT_ID NAME=$BOAT_NAME UPLINK=$UPLINK_IP GW=$UPLINK_GW" )
```

The output should match what you just set.

---

## 7. Apply the Network Config

Run the config generator. You're about to lose connectivity on whichever path you're using, so warn anyone else on the boat.

```bash
sudo /usr/local/bin/setup-network-configs.sh
```

What this does:

- Regenerates `10-uplink.network`, `20-eth0-internal.network`, `30-wlan0-internal.network` under `/etc/systemd/network/`.
- Regenerates `/etc/hostapd/hostapd.conf` (via `render-hostapd.sh`).
- Restarts `systemd-networkd` and `hostapd`.

**What you'll observe:**

- If you were on **Wi-Fi**, the donor SSID disappears and the new boat's SSID (`<new>-bb`) appears. Re-join that AP. Your new lease is in `10.<new>.2.0/24` and the Pi is at `10.<new>.2.1`.
- If you were on **Ethernet**, the Pi's `eth0` jumps from `10.<donor>.1.1` to `10.<new>.1.1`. Renew DHCP on your laptop (cycle the link or `sudo dhclient -r eth0 && sudo dhclient eth0`) and SSH to `pi@10.<new>.1.1`.

Confirm the change:

```bash
ip -br a
# Expect:
#   enx<mac>   UP    10.1.0.<new>/24    10.<new>.3.1/30      [Greece]
#   enx<mac>   UP    192.168.1.<100+new>/24   10.<new>.3.1/30  [Lab]
#   eth0       UP    10.<new>.1.1/24
#   wlan0      UP    10.<new>.2.1/24
ip route
# Default route via the correct gateway (10.1.0.1 Greece / 192.168.1.1 lab)
```

Reboot once and confirm the config persists:

```bash
sudo reboot
```

After reboot, SSH back in (now using the **new** addressing) and re-run `ip -br a` and `ip route` to confirm.

---

## 8. Apply Routing and Firewall Rules

```bash
sudo /usr/local/bin/setup-boat-routing.sh
```

This sets `net.ipv4.ip_forward=1`, loose reverse-path filtering, installs the iptables FORWARD and NAT rules, and persists them to `/etc/iptables/rules.v4`. Safe to re-run.

Quick checks:

```bash
sudo iptables -L FORWARD -v -n
sudo iptables -t nat -L POSTROUTING -v -n
sysctl net.ipv4.ip_forward          # should be 1
sysctl net.ipv4.conf.all.rp_filter  # should be 2
```

---

## 9. Verify End-to-End Connectivity

From the Pi:

```bash
ping -c 3 <uplink_gw>           # Greece: 10.1.0.1, Lab: 192.168.1.1
ping -c 3 8.8.8.8               # internet (via Starlink / lab WAN)
ping -c 3 10.<new>.3.2          # onboard DoodleLabs radio
curl -I http://10.<new>.3.2     # radio HTTP UI reachable
```

From the backseat (after plugging Ethernet back in):

```bash
ip a                            # should be 10.<new>.1.100
ip route                        # default via 10.<new>.1.1
ping -c 3 10.<new>.1.1
ping -c 3 <uplink_gw>
ping -c 3 8.8.8.8
```

From a shoreside laptop (lab or Greece), after the shore router's static routes for this boat are in place:

```bash
ping <uplink_ip>                # the Pi
ping 10.<new>.1.100             # the backseat
```

**[Greece]** Before shoreside connectivity will work, add the two static routes on the RB5009 for this boat (see `Network/Greece/blueboat_network_documentation.md` §4.4):

```
/ip route add dst-address=10.<new>.1.0/24 gateway=10.1.0.<new> comment="bb-<name>-eth"
/ip route add dst-address=10.<new>.2.0/24 gateway=10.1.0.<new> comment="bb-<name>-wlan"
```

For the lab: add the equivalent static routes on the Linksys (web UI → Advanced Routing).

---

## 10. Build `moos-ivp-blueboat`

```bash
cd ~
# If the donor image already has a clone, skip the clone:
[ -d moos-ivp-blueboat ] || git clone <repo-url> moos-ivp-blueboat
cd moos-ivp-blueboat
git pull
./build.sh
```

Smoke-test the build:

```bash
which iBBNavigatorInterface   # or whichever binary is built fresh
```

---

## 11. Systemd Services (`bb-init` and `fs-mission`)

The unit templates live in `moos-ivp-blueboat/scripts/systemd/`. Confirm they exist and are correct for this boat:

```bash
ls moos-ivp-blueboat/scripts/systemd/
# Expect: bb-init.service and fs-mission.service (or .service templates)
```

Install (if not already installed by the donor image):

```bash
sudo cp moos-ivp-blueboat/scripts/systemd/bb-init.service /etc/systemd/system/
sudo cp moos-ivp-blueboat/scripts/systemd/fs-mission.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bb-init.service
sudo systemctl enable fs-mission.service
```

Verify status (don't necessarily start them yet — they may want a mission context):

```bash
systemctl status bb-init.service
systemctl status fs-mission.service
```

---

## 12. General Cleanup

Strip donor cruft so this Pi is clean for the new boat.

**Remove stale MOOS trees:**

```bash
cd ~
# These should not exist on a current BlueBoat:
rm -rf moos-ivp-seascout moos-ivp-diasho-usv moos-ivp-pavlab 2>/dev/null
# Confirm:
ls -d moos-ivp-* 2>/dev/null
```

**Trim SSH authorized keys and deploy keys:**

```bash
cat ~/.ssh/authorized_keys
# Remove keys belonging to people who shouldn't have access. Leave only:
#   - deploy keys for this boat
#   - keys for current operators
```

For repo deploy keys, swap in this boat's deploy key (the exact mechanism is TBD per the project's deploy-key plan):

```bash
ls -la ~/.ssh/
# Look for id_ed25519 / id_rsa pairs. The pair tied to the donor boat should be
# replaced with this boat's pair, and the public half added to the repo as a
# deploy key.
```

**Clear donor identity from bash history / known_hosts (optional but tidy):**

```bash
> ~/.bash_history
> ~/.ssh/known_hosts
```

**Change the default `pi` password** (still `raspberry` on a fresh donor):

```bash
passwd
```

---

## 13. Final Verification Checklist

Run through this before declaring the boat ready:

- [ ] `hostnamectl` shows the new hostname.
- [ ] `df -h /` shows the full SD card capacity.
- [ ] `/etc/boat-network.conf` has the new `BOAT_ID`, `BOAT_NAME`, `UPLINK_IP`, `UPLINK_GW`, `WIFI_COUNTRY`.
- [ ] `ip -br a` shows uplink at the new shore IP and `10.N.3.1/30`, `eth0` at `10.N.1.1`, `wlan0` at `10.N.2.1`.
- [ ] `ip route` default points to the correct gateway (RB5009 / Linksys).
- [ ] hostapd is up and the new SSID is broadcasting.
- [ ] Backseat DHCPs into `10.N.1.100` and can reach the gateway and internet.
- [ ] `ping 10.N.3.2` reaches the onboard DoodleLabs radio.
- [ ] Shoreside router has static routes for `10.N.1.0/24` and `10.N.2.0/24` → boat uplink IP.
- [ ] A shoreside laptop can ping the backseat through the radio link.
- [ ] `bb-init.service` and `fs-mission.service` are enabled and `systemctl status` is clean.
- [ ] No `moos-ivp-seascout`, `moos-ivp-diasho-usv`, or `moos-ivp-pavlab` directories left.
- [ ] Only intended SSH keys in `~/.ssh/authorized_keys`.
- [ ] Default `pi` password has been changed (or follows the project's chosen scheme).

---

## 14. Troubleshooting

**Can't see the new SSID after step 7:**

- Check hostapd: `sudo systemctl status hostapd` and `sudo journalctl -u hostapd -n 50`. Common cause: wrong `WIFI_COUNTRY` or a channel not legal in that country.
- Re-render: `sudo /usr/local/bin/render-hostapd.sh && sudo systemctl restart hostapd`.

**Pi has no default route:**

- `ip route` shows nothing on `default`? Confirm `UPLINK_GW` is set and re-run `setup-network-configs.sh`.
- Confirm the uplink interface actually matched `IF_UPLINK="enx*"` — `networkctl` will tell you which `.network` file each interface bound to.

**Backseat can't reach the internet:**

- `iptables -t nat -L POSTROUTING -v -n` — is the MASQUERADE rule present and incrementing? If not, re-run `setup-boat-routing.sh`.
- `sysctl net.ipv4.ip_forward` must be `1`.

**Shoreside laptop can ping the Pi but not the backseat:**

- Shore router static route is missing or wrong. On the RB5009 / Linksys, verify the `10.N.1.0/24` route exists and points to the boat's uplink IP.

**Radio mgmt (10.N.3.2) unreachable:**

- The radio's own IP may not be set. The Pi only owns 10.N.3.1; the device at 10.N.3.2 has to be statically configured on the DoodleLabs side.
- Check the secondary address is actually on the uplink NIC: `ip a show dev <uplink>` should list both 10.1.0.N (or 192.168.1.X) and 10.N.3.1.

**[Greece] No internet via Starlink:**

- Check RB5009 WAN status (port 1): `/ip address print` should show a Starlink-assigned address. If not, Starlink is not up or its DHCP lease lapsed — power-cycle Starlink and the RB5009 WAN port.
- From the Pi: `ping 10.1.0.1` should work even when the WAN is down — that confirms the boat→shore link is healthy and the problem is upstream of the RB5009.
