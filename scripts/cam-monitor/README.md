---
status: draft
applies_to: Greece shoreside camera (Tapo C510GW) live view + control
last_updated: 2026-06-17
owner: JWenger
---

# Cam Monitor — Tapo camera view + control for the dashboard

Live video and pan/tilt/light/IR control for the shoreside **Tapo C510GW**
(`10.1.0.15`), surfaced as a **Camera** tab in the fleet-monitor dashboard. Two
small services run on the shoreside Pi next to the fleet-monitor services:

| Service | What it does | Port |
|---|---|---|
| `cam-go2rtc` | Pulls the camera's RTSP **once** and republishes it to every viewer as **WebRTC** (sub-second, H.264 passthrough — no transcode). | 1984 (player/API), 8555 (WebRTC) |
| `cam-control` | Lockout-safe HTTP wrapper around the Tapo control API (`pytapo`) — pan/tilt, spotlight, IR, presets. | 8082 |

Browsers can't play RTSP and the dashboard is a static page, so both pieces are
needed. Centralizing the single RTSP pull in go2rtc also sidesteps the camera's
limit on simultaneous RTSP clients — the same "probe once on the Pi" logic as the
fleet collector.

## ⚠️ Camera lockout safety — read first

Tapo cameras **ban a client IP after a few failed logins**. Everything here is
built to never become a login storm:

- `cam_control.py` logs in **once** and reuses the session for all requests;
  it never attempts more than one login per 15 s; after 2 consecutive failures
  it stops touching the camera for 180 s and returns HTTP 503, never retrying.
- It only ever uses the configured Camera-Account creds — **no guessing,
  rotating, or brute-forcing**.
- `go2rtc` reconnects to RTSP on its own, so the installer **enables but does
  not start** the services. Confirm the creds are right *before* starting, and
  if a login fails repeatedly, **stop and wait out the lockout** rather than
  looping.

## Prerequisites

- The Pi reachable on the shoreside LAN (`10.1.0.0/24`), camera at `10.1.0.15`.
- Camera-Account creds (Tapo app → Advanced Settings → Camera Account) — the
  same user/pass used for RTSP/ONVIF/pytapo, **not** the TP-Link cloud login.
- Internet on the Pi for first install (pip + the go2rtc binary download).
- Python 3 + `python3-venv`, `curl`, and the fleet-monitor dashboard already
  deployed (this adds a tab to its `index.html`).

## Install

```bash
cd scripts/cam-monitor
cp credentials.env.example credentials.env   # then edit with real creds
chmod 600 credentials.env
sudo RUN_USER=mgr ./deploy/install.sh
```

The installer creates a `venv` (with `pytapo`), downloads the `go2rtc` binary
into `bin/`, writes both systemd units, and **enables but does not start** them.

## Start (after confirming creds)

```bash
sudo systemctl start cam-go2rtc cam-control
systemctl status cam-go2rtc cam-control
```

If the Pi has a firewall, open `1984/tcp`, `8555/tcp`, and `8082/tcp` on the LAN.

## Verify

- Video: open `http://<pi-ip>:1984/stream.html?src=tapo` — you should see live
  video within ~1 s. (`go2rtc` also has a status page at `http://<pi-ip>:1984/`.)
- Control: `curl http://<pi-ip>:8082/cam/status` → JSON with `"online": true`
  and the camera model. A safe one-shot move: 
  `curl -X POST http://<pi-ip>:8082/cam/ptz -d '{"pan":15,"tilt":0}'`.
- Dashboard: open the dashboard, click the **Camera** tab — video plus a PTZ
  pad, spotlight, IR, and presets. The control buttons hit `cam-control`; the
  video is the go2rtc WebRTC stream.

## Control API (used by the dashboard)

| Method + path | Body | Action |
|---|---|---|
| `GET /cam/status` | — | session/cooldown state + device info |
| `POST /cam/ptz` | `{"pan":deg,"tilt":deg}` | relative move (pan is discrete/bounded) |
| `POST /cam/light` | `{"on":true\|false}` | white spotlight |
| `POST /cam/ir` | `{"mode":"on\|off\|auto"}` | night-vision / infrared |
| `GET /cam/presets` | — | list saved presets |
| `POST /cam/preset` | `{"action":"goto","id":..}` / `{"action":"save","name":..}` | recall / save |

Responses are JSON. A `503 {"cooling_down":true}` means the lockout guard is
deliberately holding off — wait it out, don't hammer.

## Dashboard integration

The Camera tab lives in `../fleet-monitor/index.html`. It lazy-loads the WebRTC
stream only while the tab is open (and tears it down when you leave), and talks
to `cam-control` on the same host. Override host/ports for dev with URL params:
`?camhost=`, `?ctrlport=`, `?go2rtcport=`, `?camsrc=tapo|tapo_sd`.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Camera tab: "control unreachable" | `cam-control` not running or port blocked | `systemctl status cam-control`; open `8082/tcp`. |
| Status shows "cooling down Ns" | lockout guard after auth failures | Confirm creds in `credentials.env`; wait out the cooldown; restart `cam-control`. |
| Video area stays "connecting…" | `cam-go2rtc` down, or bad RTSP creds | `http://<pi>:1984/` to check the stream; verify creds; check `8555/tcp`. |
| go2rtc log spams RTSP auth errors | wrong Camera-Account creds | **Stop go2rtc**, fix creds, then start — repeated RTSP auth can trip the camera lockout. |
| Pan spins too far | step too large | use the 5°/15° step buttons; control uses bounded relative moves (no continuous pan). |

## Files

- `cam_control.py` — lockout-safe control service (stdlib HTTP + `pytapo`).
- `go2rtc.yaml` — RTSP→WebRTC relay config (creds via env, not in the file).
- `deploy/install.sh` — venv + go2rtc + systemd units (enable, not start).
- `credentials.env.example` — copy to `credentials.env` (gitignored) and fill in.
