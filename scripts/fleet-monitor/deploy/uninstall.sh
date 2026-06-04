#!/usr/bin/env bash
#
# uninstall.sh -- stop, disable, and remove the fleet-monitor systemd services.
#
# Usage:
#   sudo ./deploy/uninstall.sh
#
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "error: must run as root (use: sudo $0)" >&2
  exit 1
fi

for svc in fleet-collector.service fleet-dashboard.service; do
  systemctl disable --now "$svc" 2>/dev/null || true
  rm -f "/etc/systemd/system/$svc"
done

systemctl daemon-reload
echo "Removed fleet-collector and fleet-dashboard services."
