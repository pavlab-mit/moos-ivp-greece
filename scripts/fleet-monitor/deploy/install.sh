#!/usr/bin/env bash
#
# install.sh -- install the fleet-monitor collector + dashboard as systemd
# services on the shoreside Pi. Path- and user-agnostic: it detects where this
# repo is checked out and which user to run as, so it works wherever you cloned.
#
# Usage (from anywhere):
#   sudo ./deploy/install.sh                 # run as the invoking (sudo) user
#   sudo RUN_USER=pi ./deploy/install.sh     # force a specific service user
#   sudo PORT=8080 ./deploy/install.sh       # override dashboard port (default 80)
#
# On the default port 80 the dashboard answers a bare IP in the browser
# (http://10.1.0.10/) -- no port, no /index.html. Ports below 1024 need
# CAP_NET_BIND_SERVICE, which this installer grants the dashboard service.
#
# After install:
#   systemctl status fleet-collector fleet-dashboard
#   journalctl -u fleet-collector -f
#   sudo systemctl restart fleet-collector   # <-- apply fleet.json edits
#
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "error: must run as root (use: sudo $0)" >&2
  exit 1
fi

# --- detect install location (the fleet-monitor dir = parent of this script) ---
DIR="$(cd "$(dirname "$0")/.." && pwd)"

# --- detect the unprivileged user to run as (never run the services as root) ---
RUN_USER="${RUN_USER:-${SUDO_USER:-}}"
if [[ -z "$RUN_USER" || "$RUN_USER" == "root" ]]; then
  echo "error: refusing to run services as root; set RUN_USER=<user>" >&2
  exit 1
fi

PY="$(command -v python3 || true)"
if [[ -z "$PY" ]]; then
  echo "error: python3 not found on PATH" >&2
  exit 1
fi

PORT="${PORT:-80}"

# Ports below 1024 are privileged; grant the (non-root) service the one
# capability it needs to bind them. Above 1024 no capability is required.
if [[ "$PORT" -lt 1024 ]]; then
  BIND_CAP="AmbientCapabilities=CAP_NET_BIND_SERVICE"
  DASH_URL="http://<pi-ip>/"
else
  BIND_CAP=""
  DASH_URL="http://<pi-ip>:$PORT/"
fi

echo "Installing fleet-monitor services:"
echo "  directory : $DIR"
echo "  run as    : $RUN_USER"
echo "  python    : $PY"
echo "  dashboard : $DASH_URL"
echo

# --- collector: probes the fleet, writes fleet_status.json every cycle ---
cat > /etc/systemd/system/fleet-collector.service <<EOF
[Unit]
Description=Fleet-monitor connectivity collector (Subsystem A)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$DIR
ExecStart=$PY $DIR/collect.py --quiet
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

# --- dashboard: static file server over the same dir (serves index.html + snapshot) ---
cat > /etc/systemd/system/fleet-dashboard.service <<EOF
[Unit]
Description=Fleet-monitor dashboard (static HTTP server)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$DIR
ExecStart=$PY -m http.server $PORT --bind 0.0.0.0
$BIND_CAP
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable fleet-collector.service fleet-dashboard.service
# restart (not just `enable --now`): on a re-run the services are already
# active, and `--now` would NOT restart them -- so a changed port/ExecStart
# would never take effect. An explicit restart always applies the new unit.
systemctl restart fleet-collector.service fleet-dashboard.service

echo
echo "Done. Both services are enabled (start on boot) and running now."
systemctl --no-pager --lines=0 status fleet-collector.service fleet-dashboard.service || true
