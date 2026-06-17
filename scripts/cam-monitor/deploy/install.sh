#!/usr/bin/env bash
#
# install.sh -- set up the cam-monitor services (camera control API + go2rtc
# WebRTC relay) on the shoreside Pi. Path/user-agnostic, like the fleet-monitor
# installer.
#
# IMPORTANT (lockout safety): this script sets up and ENABLES the services but
# does NOT start them. Tapo cameras ban a client IP after repeated failed
# logins, and go2rtc reconnects to RTSP on its own -- so wrong creds left
# running could trip a lockout. Confirm credentials first, then start manually:
#
#     sudo systemctl start cam-go2rtc cam-control
#
# Usage (from anywhere):
#   sudo ./deploy/install.sh
#   sudo RUN_USER=mgr CAM_IP=10.1.0.15 CONTROL_PORT=8082 ./deploy/install.sh
#   sudo GO2RTC_ARCH=arm64 ./deploy/install.sh      # override arch autodetect
#
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "error: must run as root (use: sudo $0)" >&2; exit 1
fi

DIR="$(cd "$(dirname "$0")/.." && pwd)"          # the cam-monitor dir
RUN_USER="${RUN_USER:-${SUDO_USER:-}}"
if [[ -z "$RUN_USER" || "$RUN_USER" == "root" ]]; then
  echo "error: refusing to run services as root; set RUN_USER=<user>" >&2; exit 1
fi
CAM_IP="${CAM_IP:-10.1.0.15}"
CONTROL_PORT="${CONTROL_PORT:-8082}"

echo "cam-monitor install:"
echo "  directory   : $DIR"
echo "  run as      : $RUN_USER"
echo "  camera IP   : $CAM_IP"
echo "  control port: $CONTROL_PORT"
echo

# --- credentials must exist (never auto-created with real values) ----------
if [[ ! -f "$DIR/credentials.env" ]]; then
  cp "$DIR/credentials.env.example" "$DIR/credentials.env"
  chown "$RUN_USER" "$DIR/credentials.env"; chmod 600 "$DIR/credentials.env"
  echo "!! created $DIR/credentials.env from the example."
  echo "!! EDIT it with the real Camera-Account creds before starting services."
  echo
fi

# --- Python venv with pytapo (control service dependency) ------------------
if [[ ! -x "$DIR/venv/bin/python" ]]; then
  echo "creating venv + installing pytapo ..."
  sudo -u "$RUN_USER" python3 -m venv "$DIR/venv"
  sudo -u "$RUN_USER" "$DIR/venv/bin/pip" install --quiet --upgrade pip
  sudo -u "$RUN_USER" "$DIR/venv/bin/pip" install --quiet pytapo
else
  echo "venv already present (skipping)"
fi

# --- go2rtc static binary (RTSP->WebRTC) -----------------------------------
GO2RTC_ARCH="${GO2RTC_ARCH:-}"
if [[ -z "$GO2RTC_ARCH" ]]; then
  case "$(uname -m)" in
    aarch64|arm64) GO2RTC_ARCH="arm64" ;;
    armv7l|armv6l) GO2RTC_ARCH="armv7" ;;
    x86_64|amd64)  GO2RTC_ARCH="amd64" ;;
    *) echo "error: unknown arch $(uname -m); set GO2RTC_ARCH" >&2; exit 1 ;;
  esac
fi
mkdir -p "$DIR/bin"
if [[ ! -x "$DIR/bin/go2rtc" ]]; then
  URL="https://github.com/AlexxIT/go2rtc/releases/latest/download/go2rtc_linux_${GO2RTC_ARCH}"
  echo "downloading go2rtc ($GO2RTC_ARCH) ..."
  curl -fL -o "$DIR/bin/go2rtc" "$URL"
  chmod +x "$DIR/bin/go2rtc"
  chown "$RUN_USER" "$DIR/bin/go2rtc"
else
  echo "go2rtc binary already present (skipping)"
fi
"$DIR/bin/go2rtc" --version 2>/dev/null | head -1 || echo "(go2rtc --version check skipped)"

# --- systemd units (enabled, NOT started) ----------------------------------
cat > /etc/systemd/system/cam-go2rtc.service <<EOF
[Unit]
Description=cam-monitor go2rtc (RTSP -> WebRTC relay)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$DIR
EnvironmentFile=$DIR/credentials.env
ExecStart=$DIR/bin/go2rtc -config $DIR/go2rtc.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/cam-control.service <<EOF
[Unit]
Description=cam-monitor camera control API (lockout-safe pytapo wrapper)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$DIR
EnvironmentFile=$DIR/credentials.env
ExecStart=$DIR/venv/bin/python $DIR/cam_control.py --cam-ip $CAM_IP --port $CONTROL_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cam-go2rtc.service cam-control.service >/dev/null

echo
echo "Done. Services are ENABLED but NOT started (lockout safety)."
echo
echo "Next:"
echo "  1) Edit creds:   sudoedit $DIR/credentials.env   (Camera-Account user/pass)"
echo "  2) Open ports on the Pi/LAN if firewalled: 1984/tcp, 8555/tcp, $CONTROL_PORT/tcp"
echo "  3) Start:        sudo systemctl start cam-go2rtc cam-control"
echo "  4) Verify video: http://<pi-ip>:1984/stream.html?src=tapo"
echo "     Verify ctrl:  curl http://<pi-ip>:$CONTROL_PORT/cam/status"
echo "  5) If a login ever fails repeatedly, STOP and wait out the camera's"
echo "     lockout window before retrying -- do not loop logins."
