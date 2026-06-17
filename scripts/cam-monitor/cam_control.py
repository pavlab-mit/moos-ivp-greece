#!/usr/bin/env python3
"""
cam-monitor / cam_control.py  --  HTTP control service for the Tapo PTZ camera.

Runs on the shoreside Pi alongside the fleet-monitor services. The dashboard's
Camera tab calls these endpoints; this service talks to the camera over the
proprietary local API (pytapo) using the Camera-Account credentials. The video
itself does NOT go through here -- that is go2rtc (WebRTC). This service is
control only: pan/tilt, spotlight, IR/night-vision, and presets.

LOCKOUT SAFETY (read this before touching the camera):
    Tapo cameras ban a client IP after a few failed logins. This service is
    built so it can never become a login storm:
      * It logs in ONCE and reuses that pytapo session for every request.
      * It never tries more than one login per LOGIN_MIN_INTERVAL_S seconds.
      * After MAX_CONSEC_FAILS consecutive failures it stops touching the camera
        for COOLDOWN_S and returns HTTP 503 "cooling down" -- it does not retry.
      * It only ever uses the configured Camera-Account creds. It never guesses,
        rotates, or brute-forces anything.
    If you change credentials, restart the service; do not let anything else
    hammer the camera while you debug.

Endpoints (JSON in, JSON out; permissive CORS for the trusted LAN):
    GET  /cam/status                      -> {online, cooldown, model, ...}
    POST /cam/ptz      {"pan":deg,"tilt":deg}   relative move (pan is discrete)
    POST /cam/light    {"on": true|false}       white spotlight
    POST /cam/ir       {"mode":"on|off|auto"}   night-vision / infrared
    GET  /cam/presets                      -> [{"id":..,"name":..}, ...]
    POST /cam/preset   {"action":"goto","id":..} | {"action":"save","name":..}

Run (with the venv that has pytapo):
    ./venv/bin/python cam_control.py --cam-ip 10.1.0.15 --port 8082

Credentials resolve from (first wins): env CAM_USER/CAM_PASS, then
credentials.env in this directory. Never passed to the browser.
"""

import argparse
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# --- lockout-safety knobs (deliberately conservative) ---------------------
LOGIN_MIN_INTERVAL_S = 15.0   # never attempt a new login more often than this
MAX_CONSEC_FAILS     = 2      # this many failures in a row -> enter cooldown
COOLDOWN_S           = 180.0  # during cooldown the camera is not touched at all
STATUS_TTL_S         = 5.0    # cache device info; don't poll the camera faster


# ---------------------------------------------------------------------------
# Credentials (env first, then credentials.env) -- never logged, never sent out
# ---------------------------------------------------------------------------

def load_creds():
    here = os.path.dirname(os.path.abspath(__file__))
    vals = {}
    envfile = os.path.join(here, "credentials.env")
    if os.path.exists(envfile):
        with open(envfile) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    vals[k.strip()] = v.strip()
    user = os.environ.get("CAM_USER") or vals.get("CAM_USER")
    pw = os.environ.get("CAM_PASS") or vals.get("CAM_PASS")
    if not user or not pw:
        print("FATAL: CAM_USER / CAM_PASS not set (env or credentials.env).",
              file=sys.stderr)
        sys.exit(2)
    return user, pw


class CoolingDown(Exception):
    """Raised when we are deliberately not touching the camera (lockout guard)."""


# ---------------------------------------------------------------------------
# Camera session -- one login, reused; throttled + cooled-down on failure
# ---------------------------------------------------------------------------

class CamSession:
    def __init__(self, ip, user, pw):
        self.ip, self.user, self.pw = ip, user, pw
        self._cam = None
        self._lock = threading.Lock()      # serialize all camera access
        self._consec_fails = 0
        self._cooldown_until = 0.0
        self._last_login_attempt = 0.0
        self._info = None                  # cached getBasicInfo basic dict
        self._info_ts = 0.0

    # -- internal: ensure we have a live session, honoring the guards --------
    def _ensure(self):
        now = time.time()
        if now < self._cooldown_until:
            raise CoolingDown(f"cooling down {int(self._cooldown_until - now)}s "
                              f"after repeated camera-auth failures")
        if self._cam is not None:
            return self._cam
        # need a (re)login -- throttle attempts hard
        since = now - self._last_login_attempt
        if since < LOGIN_MIN_INTERVAL_S:
            raise CoolingDown(f"login throttled, wait "
                              f"{int(LOGIN_MIN_INTERVAL_S - since)}s")
        from pytapo import Tapo            # imported lazily so --help etc. work
        self._last_login_attempt = now
        try:
            self._cam = Tapo(self.ip, self.user, self.pw)
            self._consec_fails = 0          # success resets the failure streak
            return self._cam
        except Exception as e:
            self._note_failure()
            raise

    def _note_failure(self):
        self._cam = None
        self._consec_fails += 1
        if self._consec_fails >= MAX_CONSEC_FAILS:
            self._cooldown_until = time.time() + COOLDOWN_S
            print(f"[cam] {self._consec_fails} consecutive failures -> "
                  f"cooldown {COOLDOWN_S:.0f}s (NOT retrying)", file=sys.stderr)

    def call(self, fn):
        """Run fn(cam) under the lock with one session. On failure, invalidate
        the session (so the next call may re-login, subject to the throttle) and
        re-raise. Never loops or retries here."""
        with self._lock:
            cam = self._ensure()
            try:
                result = fn(cam)
                self._consec_fails = 0
                return result
            except CoolingDown:
                raise
            except Exception:
                self._note_failure()
                raise

    def status(self):
        """Light status: session/cooldown state plus cached device info. Only
        touches the camera at most once per STATUS_TTL_S."""
        now = time.time()
        cooling = now < self._cooldown_until
        out = {
            "online": self._cam is not None and not cooling,
            "cooldown": cooling,
            "cooldown_s": max(0, int(self._cooldown_until - now)),
            "consec_fails": self._consec_fails,
            "cam_ip": self.ip,
        }
        if not cooling and (self._info is None or now - self._info_ts > STATUS_TTL_S):
            try:
                info = self.call(lambda c: c.getBasicInfo()["device_info"]["basic"])
                self._info = {
                    "model": info.get("device_model"),
                    "name": info.get("device_alias"),
                    "firmware": info.get("sw_version"),
                }
                self._info_ts = now
                out["online"] = True
            except CoolingDown as e:
                out["note"] = str(e)
            except Exception as e:
                out["online"] = False
                out["note"] = f"camera unreachable: {e.__class__.__name__}"
        if self._info:
            out.update(self._info)
        return out


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    session: CamSession = None     # set on the server instance below
    pan_step = 15
    tilt_step = 15

    # -- helpers ------------------------------------------------------------
    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _body_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode() or "{}")
        except Exception:
            return {}

    def log_message(self, fmt, *args):       # quieter, no creds ever
        sys.stderr.write("[cam] %s\n" % (fmt % args))

    # -- routing ------------------------------------------------------------
    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        s = self.session
        if self.path.startswith("/cam/status"):
            return self._send(200, s.status())
        if self.path.startswith("/cam/presets"):
            return self._guard(lambda: self._presets())
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path.startswith("/cam/ptz"):
            return self._guard(lambda: self._ptz(self._body_json()))
        if self.path.startswith("/cam/light"):
            return self._guard(lambda: self._light(self._body_json()))
        if self.path.startswith("/cam/ir"):
            return self._guard(lambda: self._ir(self._body_json()))
        if self.path.startswith("/cam/preset"):
            return self._guard(lambda: self._preset(self._body_json()))
        return self._send(404, {"error": "not found"})

    def _guard(self, fn):
        """Run a camera action, translating the lockout guard into HTTP 503 and
        any other camera error into HTTP 502 -- never a crash, never a retry."""
        try:
            return self._send(200, {"ok": True, "result": fn()})
        except CoolingDown as e:
            return self._send(503, {"ok": False, "cooling_down": True, "error": str(e)})
        except Exception as e:
            return self._send(502, {"ok": False, "error": f"{e.__class__.__name__}: {e}"})

    # -- actions ------------------------------------------------------------
    def _ptz(self, b):
        pan = int(b.get("pan", 0))
        tilt = int(b.get("tilt", 0))
        # pan/tilt are RELATIVE degrees; pytapo moveMotor is a bounded discrete
        # move, so there is no continuous-pan overshoot to worry about here.
        self.session.call(lambda c: c.moveMotor(pan, tilt))
        return {"pan": pan, "tilt": tilt}

    def _light(self, b):
        on = bool(b.get("on"))
        self.session.call(lambda c: c.setForceWhitelampState(on))
        return {"light": "on" if on else "off"}

    def _ir(self, b):
        mode = str(b.get("mode", "auto")).lower()
        if mode not in ("on", "off", "auto"):
            raise ValueError("mode must be on|off|auto")
        self.session.call(lambda c: c.setDayNightMode(mode))
        return {"ir": mode}

    def _presets(self):
        presets = self.session.call(lambda c: c.getPresets())
        items = [{"id": k, "name": v} for k, v in (presets or {}).items()]
        self._send(200, {"ok": True, "result": items})

    def _preset(self, b):
        action = str(b.get("action", "")).lower()
        if action == "goto":
            pid = str(b.get("id"))
            self.session.call(lambda c: c.setPreset(pid))
            return {"goto": pid}
        if action == "save":
            name = str(b.get("name", "")).strip() or "preset"
            self.session.call(lambda c: c.savePreset(name))
            return {"saved": name}
        raise ValueError("action must be goto|save")


def main():
    ap = argparse.ArgumentParser(description="Tapo camera control service (lockout-safe)")
    ap.add_argument("--cam-ip", default=os.environ.get("CAM_IP", "10.1.0.15"))
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8082)
    ap.add_argument("--pan-step", type=int, default=15)
    ap.add_argument("--tilt-step", type=int, default=15)
    args = ap.parse_args()

    user, pw = load_creds()
    Handler.session = CamSession(args.cam_ip, user, pw)
    Handler.pan_step = args.pan_step
    Handler.tilt_step = args.tilt_step

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"cam-control on {args.host}:{args.port} -> camera {args.cam_ip} "
          f"(lazy login; lockout-safe). Ctrl-C to stop.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
