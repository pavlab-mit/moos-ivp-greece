---
status: draft
applies_to: Greece BlueBoat fleet (2026)
last_updated: 2026-06-04
owner: JWenger
---

# Software Build and Systemd Services

How to clone, build, and install the BlueBoat autonomy software on a
first-booted Pi, and how to install the systemd services that run it on each
boot.

---

## 1. Overview

This guide takes a first-booted Pi (`13_frontseat_first_boot.md`) to a boat
that builds its own software and decides, at every power-on, whether to launch
the mission. It produces: `moos-ivp-blueboat` and `moos-ivp-greece` cloned and
built; the two read-only deploy keys installed so the boat can pull both repos;
and the three autolaunch units (`bb-init.service`, `fs-mission.service`,
`bb-led-idle.service`) installed, with `bb-init` enabled to run at boot.

The three units are not three things you start by hand. Only `bb-init` is
enabled. It runs once at boot, checks the battery and attitude gates, pulls and
rebuilds if the repo changed, and then — and only then — starts the mission and
the status LED itself. Sections 3.3 and 11 explain that model; the procedures
below just put the pieces in place.

## 2. Prerequisites

- Pi first-booted (`13_frontseat_first_boot.md`) and reachable from shore.
- Internet connectivity from the Pi, verified in
  [`13_frontseat_first_boot.md` §12](13_frontseat_first_boot.md#12-verify-end-to-end-connectivity).
- `moos-ivp` core checked out and built on the Pi (inherited from the donor
  image), and the build toolchain (`cmake`, `make`, `g++`) present.
  `moos-ivp-blueboat` links against the core tree.
- A GPIO control tool for the status LED — either `pinctrl` (ships with recent
  Raspberry Pi OS / `raspi-utils`) or `raspi-gpio`. The LED service shells out
  to whichever is present (§3.4). Confirm with `command -v pinctrl raspi-gpio`;
  if neither resolves, install one:

  Run on the Pi:

  ```bash
  sudo apt-get update
  sudo apt-get install -y raspi-gpio
  ```

- Both deploy keys available in `00_secrets.md`:
  `{{MOOS_IVP_BLUEBOAT_DEPLOY_KEY}}` and `{{MOOS_IVP_GREECE_DEPLOY_KEY}}`.
  These are fleet-wide and read-only — see §3.2.

## 3. Context

### 3.1 Two Repos, One Boat

A boat builds two repositories. `moos-ivp-blueboat` is the platform: the
BlueBoat drivers, the front-seat mission, and the autolaunch scripts and units
(`scripts/bb_init.sh`, `scripts/bb_led.sh`, `scripts/systemd/`).
`moos-ivp-greece` is the course layer: Greece-specific missions and
configuration. The platform repo is what the autolaunch machinery lives in and
rebuilds at boot; the Greece repo rides alongside it.

Both depend on the `moos-ivp` core tree being present and built first, since
they link against its libraries and call its binaries (`pAntler`, `nsplug`,
and so on). On a boat cloned from the donor image, the core is already there.

### 3.2 Deploy Keys — Fleet-Wide and Read-Only

Keys are **not** per boat. The fleet uses two SSH deploy keys, one per repo,
shared across every boat and added **read-only** to each repository's *Deploy
keys* settings (the "Allow write access" box left unchecked). A boat only ever
pulls, so read-only is all it needs; sharing one key per repo across the fleet
means there is one key to rotate per repo, not one per hull.

Two keys are required because a single GitHub deploy key can be attached to
only one repository. So `{{MOOS_IVP_BLUEBOAT_DEPLOY_KEY}}` is the deploy key on
`moos-ivp-blueboat` and `{{MOOS_IVP_GREECE_DEPLOY_KEY}}` is the deploy key on
`moos-ivp-greece`. Both private halves live on every boat.

Because both keys authenticate to the same host (`github.com`), the boat needs
an SSH `config` that maps each repo to its own key via host aliases — otherwise
SSH offers the wrong key and GitHub refuses it. Section 4 sets that up.

> **Note.** Rotating a key is a fleet-wide operation: replace the value in
> `00_secrets.md`, redistribute the private half to every boat, and swap the
> public half in the repo's Deploy keys. No per-boat bookkeeping.

### 3.3 The Autolaunch Service Model

Three units live in `moos-ivp-blueboat/scripts/systemd/`, but they do not have
equal status:

| Unit | Enabled at boot? | Started by | Role |
|---|---|---|---|
| `bb-init.service` | **Yes** (`enable`) | systemd, at boot | Runs `bb_init.sh` once: checks battery + attitude gates, pulls/rebuilds if changed, then launches the mission or the idle LED. |
| `fs-mission.service` | No | `bb_init.sh`, on demand | The front-seat MOOS mission. Started only after the gates pass. |
| `bb-led-idle.service` | No | `bb_init.sh`, on demand | The idle "still alive" status-LED heartbeat. Started when the boat stands by; stopped when the mission launches. |

`bb-init` is the brain. It is a `Type=oneshot` unit that runs as root, stays
`active (exited)` after it finishes so its decision survives for inspection
over SSH, and owns the lifecycle of the other two. The other two are deliberately
**not** enabled and **not** ordered after `bb-init`: `bb_init.sh` starts them
with a synchronous `systemctl start`, and an `After=bb-init` dependency would
deadlock (bb-init stays "activating" until its script returns, while the script
blocks waiting for a start job systemd won't run until bb-init is active).

This is why §7 copies all three units but enables only `bb-init`. Enabling
`fs-mission` or `bb-led-idle` would have them race `bb_init` at boot, which is
exactly what the gate logic exists to prevent.

### 3.4 The Status LED and the GPIO Tool

The status LED is driven on the Navigator's PWM0 / fan header, which is wired
straight to the Pi's GPIO18 (BCM) — not to the PCA9685 PWM driver or the
Navigator user LEDs. `scripts/bb_led.sh` drives that pin as a plain GPIO via
`pinctrl` (preferred) or `raspi-gpio` (fallback), so the LED works even when the
C++ build is broken — it needs no compiled binary. That is also why §2 lists a
GPIO tool, not a library, as the dependency.

The LED code stays in `moos-ivp-blueboat` for now; this doc only ensures the
tool it depends on is installed. If GPIO18 is claimed by a `dtoverlay` (for
example a PWM fan), that use and the status LED conflict — pick one.

## 4. Install Deploy Keys

Both keys go on every boat. Run all of this on the Pi.

1. Retrieve both keypairs from `00_secrets.md`:
   `{{MOOS_IVP_BLUEBOAT_DEPLOY_KEY}}` and `{{MOOS_IVP_GREECE_DEPLOY_KEY}}`.

2. Write the private halves with distinct names and lock down permissions:

   ```bash
   mkdir -p ~/.ssh && chmod 700 ~/.ssh
   # paste the blueboat private key here
   nano ~/.ssh/id_blueboat
   # paste the greece private key here
   nano ~/.ssh/id_greece
   chmod 600 ~/.ssh/id_blueboat ~/.ssh/id_greece
   ```

3. Add a host alias per repo so each pull uses the right key. Append to
   `~/.ssh/config`:

   ```text
   Host github-blueboat
       HostName github.com
       User git
       IdentityFile ~/.ssh/id_blueboat
       IdentitiesOnly yes

   Host github-greece
       HostName github.com
       User git
       IdentityFile ~/.ssh/id_greece
       IdentitiesOnly yes
   ```

   ```bash
   chmod 600 ~/.ssh/config
   ```

4. Confirm the public half of each key is registered as a **read-only** deploy
   key on the matching repository (blueboat key → `moos-ivp-blueboat`, greece
   key → `moos-ivp-greece`). This is a fleet-wide setup step, done once per repo
   — not per boat.

5. Test both aliases. A successful deploy-key auth greets you by repo and exits
   non-zero (GitHub never grants a shell):

   ```bash
   ssh -T git@github-blueboat
   ssh -T git@github-greece
   # Expect: "Hi pavlab-mit/moos-ivp-blueboat! You've successfully authenticated,
   #          but GitHub does not provide shell access."
   ```

## 5. Repoint the Remote and Build `moos-ivp-blueboat`

The repo is already on the boat — it came with the donor image. It does not
need to be cloned; it needs its `origin` repointed at the §4 host alias so
pulls use the fleet read-only deploy key. Then pull and build. Run on the Pi.

1. Repoint `origin` at the blueboat alias (substitute the org):

   ```bash
   git -C ~/moos-ivp-blueboat remote set-url origin \
     git@github-blueboat:pavlab-mit/moos-ivp-blueboat.git
   ```

2. Pull and build:

   ```bash
   cd ~/moos-ivp-blueboat && git pull && ./build.sh
   ```

3. Smoke-test that a binary built and is on `PATH`:

   ```bash
   which iUnicore
   ls ~/moos-ivp-blueboat/bin
   ```

> **Note.** Only if the repo is somehow absent, clone it once with the alias:
> `git clone git@github-blueboat:pavlab-mit/moos-ivp-blueboat.git ~/moos-ivp-blueboat`.

## 6. Repoint the Remote and Build `moos-ivp-greece`

Same pattern with the greece alias. Run on the Pi.

1. Repoint `origin` at the greece alias:

   ```bash
   git -C ~/moos-ivp-greece remote set-url origin \
     git@github-greece:pavlab-mit/moos-ivp-greece.git
   ```

2. Pull and build:

   ```bash
   cd ~/moos-ivp-greece && git pull && ./build.sh
   ```

3. Smoke-test a built binary from `~/moos-ivp-greece/bin`.

> **Note.** Only if the repo is somehow absent, clone it once with the alias:
> `git clone git@github-greece:pavlab-mit/moos-ivp-greece.git ~/moos-ivp-greece`.

## 7. Install Systemd Services

All three units ship in `moos-ivp-blueboat/scripts/systemd/`. Install all
three; enable only `bb-init`. Run on the Pi.

1. Confirm the unit files are present:

   ```bash
   ls ~/moos-ivp-blueboat/scripts/systemd/
   # Expect: bb-init.service  fs-mission.service  bb-led-idle.service
   ```

2. Copy all three into place:

   ```bash
   sudo cp ~/moos-ivp-blueboat/scripts/systemd/bb-init.service     /etc/systemd/system/
   sudo cp ~/moos-ivp-blueboat/scripts/systemd/fs-mission.service  /etc/systemd/system/
   sudo cp ~/moos-ivp-blueboat/scripts/systemd/bb-led-idle.service /etc/systemd/system/
   ```

3. Reload the unit definitions:

   ```bash
   sudo systemctl daemon-reload
   ```

4. Enable **only** `bb-init`. `bb_init.sh` starts the other two on demand
   (§3.3) — do not enable them.

   ```bash
   sudo systemctl enable bb-init.service
   ```

   > **Critical.** Do **not** `enable` or boot-start `fs-mission.service` or
   > `bb-led-idle.service`. Enabling them races the gate logic in `bb-init` and
   > can launch the mission before the battery/attitude checks pass.

5. Confirm enable state (don't start anything by hand):

   ```bash
   systemctl is-enabled bb-init.service        # -> enabled
   systemctl is-enabled fs-mission.service     # -> disabled (or static)
   systemctl is-enabled bb-led-idle.service    # -> disabled (or static)
   ```

## 8. Per-Boat Service Overrides (if needed)

Per-boat configuration lives in `Environment=` lines inside
`bb-init.service` — `bb_init.sh` has a built-in default for every `BOAT_*`
variable, so only override what differs on this boat. The unit file ships with
the full list commented out (battery floor `BOAT_VOLT_MIN`, pitch gate
`BOAT_PITCH_LIMIT`, LED pin `BOAT_LED_GPIO` / `BOAT_LED_ACTIVE_HIGH`, branch
pin `BOAT_GIT_BRANCH`, pull/build toggles, and so on).

Apply overrides with a drop-in rather than editing the copied unit, so a later
`cp` of an updated upstream unit doesn't clobber them:

```bash
sudo systemctl edit bb-init.service
```

In the editor, add only the lines that differ, for example a calibrated
low-battery floor:

```text
[Service]
Environment=BOAT_VOLT_MIN=14.2
```

Then `sudo systemctl daemon-reload`.

> **Note.** `bb-led-idle.service` is a separate unit and does **not** inherit
> `bb-init`'s `Environment=` lines. If this boat overrides the LED pin or
> polarity, set `BOAT_LED_GPIO` / `BOAT_LED_ACTIVE_HIGH` in a drop-in for
> `bb-led-idle.service` too, matching `bb-init`.

A setting only belongs here if it's per-boat *service* behavior. Network
identity belongs in `/etc/boat-network.conf`
([`13_frontseat_first_boot.md` §9](13_frontseat_first_boot.md#9-update-etcboat-networkconf)); mission
parameters belong in a mission plug.

## 9. Verification

- Both repos built:

  ```bash
  ls ~/moos-ivp-blueboat/bin ~/moos-ivp-greece/bin
  ```

- Deploy keys authenticate for both repos:

  ```bash
  ssh -T git@github-blueboat
  ssh -T git@github-greece
  ```

- A GPIO tool is present for the status LED:

  ```bash
  command -v pinctrl raspi-gpio
  ```

- Only `bb-init` is enabled:

  ```bash
  systemctl is-enabled bb-init.service     # -> enabled
  systemctl status bb-init.service         # loaded, no config errors
  ```

- After a reboot, `bb-init` runs and reaches its standby/launch decision:

  ```bash
  journalctl -u bb-init.service -b
  cat /run/bb_boot/status 2>/dev/null
  ```

  A standing-by boat shows the idle LED heartbeat (10 s slow flash, then a
  double-blink every 30 s).

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `build.sh` fails on missing `moos-ivp` | Core tree absent or unbuilt | Confirm `~/moos-ivp` exists and is built; check `PATH` includes `~/moos-ivp/bin`. |
| `git pull` rejected / "Permission denied (publickey)" | Wrong key offered, or remote not using the host alias | Confirm the remote URL uses `github-blueboat`/`github-greece` (§4–§6); test `ssh -T git@github-blueboat`. |
| Auth works for one repo, fails the other | Only one deploy key registered, or `IdentitiesOnly` missing | Confirm both public halves are read-only deploy keys on their repos; keep `IdentitiesOnly yes` in `~/.ssh/config`. |
| `bb_led.sh: no GPIO tool found` in the journal | Neither `pinctrl` nor `raspi-gpio` installed | `sudo apt-get install -y raspi-gpio` (§2). |
| Status LED never lights | GPIO18 claimed by a `dtoverlay`, or wrong pin/polarity | Free GPIO18 (§3.4), or set `BOAT_LED_GPIO` / `BOAT_LED_ACTIVE_HIGH` in drop-ins for both `bb-init` and `bb-led-idle` (§8). |
| Mission launches before gates pass | `fs-mission`/`bb-led-idle` were enabled | `sudo systemctl disable fs-mission.service bb-led-idle.service`; only `bb-init` is enabled (§7). |
| `bb-init` stuck `activating` | A unit was ordered `After=bb-init` | Remove any `After=bb-init` dep; the launched units must not be ordered after their launcher (§3.3). |
| Service issues generally | — | `journalctl -u <unit> -b -n 200`. |

## 11. Rebuild / Update Cycle

On a normal boot, `bb-init` does the update for you: once the gates pass, it
fetches the current branch and, if `HEAD` moved, rebuilds before launching — a
failed *pull* (offline) continues with the existing build, but a failed *build*
aborts the launch rather than run a partial build.

> **Critical.** Never restart or relaunch the mission in a power cycle where it
> has already run. The ESCs initialize exactly once per power-up; a second
> initialization attempt misbehaves. So **never** run
> `systemctl restart fs-mission.service`, and never manually relaunch the
> mission after it (or `bb-init`) has already launched it this power-up. If the
> mission has run — by `bb-init` or by hand — the boat **must be fully
> power-cycled** before it runs again. A soft `reboot` of the Pi is not enough
> if vehicle power (and the ESCs) stays up: `bb-init` would relaunch into
> already-initialized ESCs.

To pick up new code, run the update on the Pi while the mission is **not**
running:

```bash
cd ~/moos-ivp-blueboat && git pull && ./build.sh
```

Then fully power-cycle the boat. On the next clean power-up, `bb-init` re-runs
its full decision (gates → pull/rebuild → launch) against fresh ESC state. This
is the only supported way to bring a new build into a running mission: cut
vehicle power and bring the boat back up.

## 12. Change Log

Append-only log of changes to this procedure. One line per change: date —
change — author.

- 2026-06-04 — Initial draft from `first_boot.md` §§10–11 stub. Documents the
  three-unit autolaunch model (`bb-init` enabled; `fs-mission` and
  `bb-led-idle` on-demand via `bb_init.sh`); fleet-wide read-only deploy keys
  (one per repo, `pavlab-mit`) with per-repo SSH host aliases; `pinctrl` /
  `raspi-gpio` status-LED dependency; repoint-remote (not clone) build flow.
  Critical ESC rule: never restart `fs-mission.service` — power-cycle the boat.
  — JWenger
