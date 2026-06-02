---
status: stub
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-02
owner: TBD
---

# Software Build and Systemd Services

How to clone, build, and install the BlueBoat autonomy software on a
first-booted Pi, and how to install and enable the systemd services that
launch it.

> **Status: stub.** Content split out of `first_boot.md` §§10–11. Adds
> coverage of `moos-ivp-greece`, deploy-key management, and per-boat
> systemd unit overrides.

---

## 1. Overview
_To do._

What this guide produces: `moos-ivp-blueboat` and `moos-ivp-greece` cloned
and built, deploy keys swapped in, `bb-init.service` and `fs-mission.service`
installed and enabled.

## 2. Prerequisites
_To do._

- Pi first-booted (`13_frontseat_first_boot.md`) and reachable from shore.
- Internet connectivity from the Pi (verified in
  `13_frontseat_first_boot.md` §12).
- Deploy keys available in `00_secrets.md`:
  `{{MOOS_IVP_BLUEBOAT_DEPLOY_KEY}}`, `{{MOOS_IVP_GREECE_DEPLOY_KEY}}`.

## 3. Context

### 3.1 Two Repos, One Boat
_To do._

Why `moos-ivp-blueboat` (platform) and `moos-ivp-greece` (course/missions)
are separate. Build dependency direction.

### 3.2 Per-Boat Deploy Keys
_To do._

Each boat gets its own SSH key pair. Public half lives in the repo's
Deploy Keys; private half on the boat. Key rotation procedure on operator
turnover.

### 3.3 Systemd Service Model
_To do._

`bb-init.service` brings up bring-up tasks (e.g., logging, sensor init).
`fs-mission.service` launches the frontseat MOOS mission. Dependency
graph (which units want/require which).

## 4. Install Deploy Keys
_To do._

Step-by-step:

1. Generate or retrieve the boat's key pair from `00_secrets.md`.
2. Copy private half to `~/.ssh/id_ed25519` on the Pi (chmod 600).
3. Copy public half to `~/.ssh/id_ed25519.pub`.
4. Add public half to each repo as a deploy key (read-only unless writes
   needed).
5. Test: `ssh -T git@github.com` (or the configured host).

## 5. Clone and Build `moos-ivp-blueboat`
_To do._

Step-by-step:

1. `cd ~`
2. `[ -d moos-ivp-blueboat ] || git clone <repo-url> moos-ivp-blueboat`
3. `cd moos-ivp-blueboat && git pull`
4. `./build.sh`
5. Smoke-test: `which iBBNavigatorInterface`.

## 6. Clone and Build `moos-ivp-greece`
_To do._

Step-by-step:

1. `cd ~`
2. `[ -d moos-ivp-greece ] || git clone <repo-url> moos-ivp-greece`
3. `cd moos-ivp-greece && git pull`
4. `./build.sh`
5. Smoke-test a built binary.

## 7. Install Systemd Services
_To do._

Step-by-step:

1. Verify unit files exist:
   `ls moos-ivp-blueboat/scripts/systemd/`.
2. Copy to `/etc/systemd/system/`:
   - `bb-init.service`
   - `fs-mission.service`
3. `sudo systemctl daemon-reload`
4. `sudo systemctl enable bb-init.service fs-mission.service`
5. Confirm: `systemctl status` on both (don't start yet — they may want
   mission context).

## 8. Per-Boat Service Overrides (if needed)
_To do._

How to use `systemctl edit <unit>` to apply per-boat overrides without
editing the upstream unit file. When that's appropriate vs. when the
override belongs in `/etc/boat-network.conf` or a mission plug.

## 9. Verification
_To do._

- `systemctl is-enabled bb-init.service fs-mission.service` returns
  `enabled` for both.
- `systemctl status bb-init.service` shows the unit loaded with no
  errors.
- After a reboot, the units start as expected (if intended).

## 10. Troubleshooting
_To do._

- Build fails on missing `moos-ivp`: confirm sibling/parent checkout.
- Deploy key auth fails: check `ssh -T`, permissions on private key,
  agent forwarding state.
- Service stuck in `activating`: inspect `journalctl -u <unit> -n 200`.

## 11. Rebuild / Update Cycle
_To do._

The routine when pulling new code: `git pull`, `./build.sh`,
`systemctl restart fs-mission.service`. When a full reboot is needed vs.
a service restart.
