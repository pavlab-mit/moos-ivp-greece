#!/usr/bin/env python3
"""
cam-monitor / cam_control.py  --  HTTP control service for the Tapo PTZ camera.

Runs on the shoreside Pi next to the fleet-monitor services. The dashboard's
Camera tab calls these endpoints; this service drives the camera over **ONVIF**
(port 2020) using the Camera-Account credentials -- the path proven to work on
this fleet (RTSP for video, ONVIF for control). The video itself does NOT go
through here; that is go2rtc (WebRTC). This service is control only:
pan / tilt + presets.

Why ONVIF and not the Tapo (pytapo) API: the pytapo local API needs the TP-Link
*cloud* account, which this deployment never set up -- it returns "Invalid
authentication data" and repeated attempts trip the camera's lockout. ONVIF uses
the same Camera-Account creds as RTSP and is known-good here. (Spotlight and IR
are only reachable via pytapo, so they are intentionally not exposed.)

PTZ behavior (ported from the proven ptz_gui.py):
  * PAN  -> discrete ONVIF RelativeMove. Continuous pan overshoots into 360s on
            this camera, so each press is one bounded step that can't run away.
  * TILT -> brief ONVIF ContinuousMove + Stop. Behaves well and respects limits.

LOCKOUT SAFETY: even though ONVIF creds are known-good, the session guard from
the original design is kept: one ONVIF session reused for all requests, at most
one (re)connect per LOGIN_MIN_INTERVAL_S, and after MAX_CONSEC_FAILS failures it
stops touching the camera for COOLDOWN_S and returns HTTP 503 -- never a storm,
never credential guessing.

Endpoints (JSON in/out, permissive CORS for the trusted LAN):
    GET  /cam/status                       -> {online, cooldown, model, ...}
    POST /cam/ptz   {"pan":-1|0|1,"tilt":-1|0|1,"size":1|2|3}
    GET  /cam/presets                       -> [{"token":..,"name":..}, ...]
    POST /cam/preset {"action":"goto","token":..} | {"action":"save","name":..}
                     | {"action":"delete","token":..}

Run (with the venv that has onvif-zeep):
    ./venv/bin/python cam_control.py --cam-ip 10.1.0.15 --onvif-port 2020 --port 8082
"""

import argparse
import glob
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# --- lockout-safety knobs (kept conservative) -----------------------------
LOGIN_MIN_INTERVAL_S = 15.0
MAX_CONSEC_FAILS     = 2
COOLDOWN_S           = 180.0
STATUS_TTL_S         = 5.0

# --- PTZ step sizes (size 1/2/3 -> small/normal/large) ---------------------
TILT_SPEED   = 0.6                       # ONVIF continuous-move velocity (-1..1)
TILT_TIME    = {1: 0.25, 2: 0.5, 3: 0.9}  # seconds of tilt per press
PAN_MAG      = {1: 0.03, 2: 0.07, 3: 0.14}  # ONVIF relative-move translation per press


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


def find_wsdl():
    """onvif-zeep ships its WSDL files under site-packages/wsdl. Locate them
    relative to this venv so ONVIFCamera can find the service definitions."""
    here = os.path.dirname(os.path.abspath(__file__))
    hits = glob.glob(os.path.join(here, "venv", "lib", "python*",
                                  "site-packages", "wsdl"))
    if hits:
        return hits[0]
    try:                                  # fall back to the installed package
        import onvif
        cand = os.path.join(os.path.dirname(onvif.__file__), "wsdl")
        if os.path.isdir(cand):
            return cand
    except Exception:
        pass
    return None


class CoolingDown(Exception):
    """Raised when we are deliberately not touching the camera (lockout guard)."""


# ---------------------------------------------------------------------------
# ONVIF session -- one connection, reused; throttled + cooled-down on failure
# ---------------------------------------------------------------------------

class CamSession:
    def __init__(self, ip, port, user, pw):
        self.ip, self.port, self.user, self.pw = ip, port, user, pw
        self._lock = threading.Lock()
        self._ptz = None
        self._token = None
        self._consec_fails = 0
        self._cooldown_until = 0.0
        self._last_login_attempt = 0.0
        self._info = None
        self._info_ts = 0.0

    def _connect(self):
        from onvif import ONVIFCamera
        cam = ONVIFCamera(self.ip, self.port, self.user, self.pw, find_wsdl())
        media = cam.create_media_service()
        ptz = cam.create_ptz_service()
        token = media.GetProfiles()[0].token
        # cache a bit of device info for /cam/status (best-effort)
        try:
            di = cam.create_devicemgmt_service().GetDeviceInformation()
            self._info = {"model": getattr(di, "Model", None),
                          "name": getattr(di, "Manufacturer", None),
                          "firmware": getattr(di, "FirmwareVersion", None)}
            self._info_ts = time.time()
        except Exception:
            pass
        return ptz, token

    def _ensure(self):
        now = time.time()
        if now < self._cooldown_until:
            raise CoolingDown(f"cooling down {int(self._cooldown_until - now)}s "
                              f"after repeated camera failures")
        if self._ptz is not None:
            return self._ptz, self._token
        since = now - self._last_login_attempt
        if since < LOGIN_MIN_INTERVAL_S:
            raise CoolingDown(f"connect throttled, wait {int(LOGIN_MIN_INTERVAL_S - since)}s")
        self._last_login_attempt = now
        try:
            self._ptz, self._token = self._connect()
            self._consec_fails = 0
            return self._ptz, self._token
        except Exception:
            self._note_failure()
            raise

    def _note_failure(self):
        self._ptz = None
        self._token = None
        self._consec_fails += 1
        if self._consec_fails >= MAX_CONSEC_FAILS:
            self._cooldown_until = time.time() + COOLDOWN_S
            print(f"[cam] {self._consec_fails} consecutive failures -> "
                  f"cooldown {COOLDOWN_S:.0f}s (NOT retrying)", file=sys.stderr)

    def call(self, fn):
        with self._lock:
            ptz, token = self._ensure()
            try:
                result = fn(ptz, token)
                self._consec_fails = 0
                return result
            except CoolingDown:
                raise
            except Exception:
                self._note_failure()
                raise

    # -- PTZ primitives (the proven pan-discrete / tilt-continuous split) ----
    def pan(self, direction, size):
        mag = PAN_MAG.get(size, PAN_MAG[2]) * direction
        def _do(ptz, token):
            req = ptz.create_type("RelativeMove")
            req.ProfileToken = token
            req.Translation = {"PanTilt": {"x": mag, "y": 0.0}}
            ptz.RelativeMove(req)
        self.call(_do)

    def tilt(self, direction, size):
        dur = TILT_TIME.get(size, TILT_TIME[2])
        def _do(ptz, token):
            req = ptz.create_type("ContinuousMove")
            req.ProfileToken = token
            req.Velocity = {"PanTilt": {"x": 0.0, "y": direction * TILT_SPEED}}
            ptz.ContinuousMove(req)
            time.sleep(dur)
            ptz.Stop({"ProfileToken": token})
        self.call(_do)

    def presets(self):
        def _do(ptz, token):
            out = []
            for p in ptz.GetPresets({"ProfileToken": token}):
                out.append({"token": getattr(p, "token", None),
                            "name": getattr(p, "Name", None)})
            return out
        return self.call(_do)

    def goto_preset(self, tk):
        self.call(lambda ptz, token: ptz.GotoPreset(
            {"ProfileToken": token, "PresetToken": tk}))

    def save_preset(self, name):
        self.call(lambda ptz, token: ptz.SetPreset(
            {"ProfileToken": token, "PresetName": name}))

    def remove_preset(self, tk):
        self.call(lambda ptz, token: ptz.RemovePreset(
            {"ProfileToken": token, "PresetToken": tk}))

    def status(self):
        now = time.time()
        cooling = now < self._cooldown_until
        out = {
            "online": self._ptz is not None and not cooling,
            "cooldown": cooling,
            "cooldown_s": max(0, int(self._cooldown_until - now)),
            "consec_fails": self._consec_fails,
            "cam_ip": self.ip,
        }
        if not cooling and (self._ptz is None or now - self._info_ts > STATUS_TTL_S):
            try:
                self.call(lambda ptz, token: ptz.GetStatus({"ProfileToken": token}))
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
    session: CamSession = None

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

    def log_message(self, fmt, *args):
        sys.stderr.write("[cam] %s\n" % (fmt % args))

    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        if self.path.startswith("/cam/status"):
            return self._send(200, self.session.status())
        if self.path.startswith("/cam/presets"):
            return self._guard(lambda: {"presets": self.session.presets()})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path.startswith("/cam/ptz"):
            return self._guard(lambda: self._ptz(self._body_json()))
        if self.path.startswith("/cam/preset"):
            return self._guard(lambda: self._preset(self._body_json()))
        return self._send(404, {"error": "not found"})

    def _guard(self, fn):
        try:
            return self._send(200, {"ok": True, "result": fn()})
        except CoolingDown as e:
            return self._send(503, {"ok": False, "cooling_down": True, "error": str(e)})
        except Exception as e:
            return self._send(502, {"ok": False, "error": f"{e.__class__.__name__}: {e}"})

    def _ptz(self, b):
        pan = int(b.get("pan", 0))
        tilt = int(b.get("tilt", 0))
        size = int(b.get("size", 2))
        if pan:
            self.session.pan(1 if pan > 0 else -1, size)
        if tilt:
            self.session.tilt(1 if tilt > 0 else -1, size)
        return {"pan": pan, "tilt": tilt, "size": size}

    def _preset(self, b):
        action = str(b.get("action", "")).lower()
        if action == "goto":
            tk = str(b.get("token"))
            self.session.goto_preset(tk)
            return {"goto": tk}
        if action == "save":
            name = str(b.get("name", "")).strip() or "preset"
            self.session.save_preset(name)
            return {"saved": name}
        if action == "delete":
            tk = str(b.get("token"))
            self.session.remove_preset(tk)
            return {"deleted": tk}
        raise ValueError("action must be goto|save|delete")


def main():
    ap = argparse.ArgumentParser(description="Tapo camera ONVIF control service (lockout-safe)")
    ap.add_argument("--cam-ip", default=os.environ.get("CAM_IP", "10.1.0.15"))
    ap.add_argument("--onvif-port", type=int, default=int(os.environ.get("ONVIF_PORT", "2020")))
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8082)
    args = ap.parse_args()

    user, pw = load_creds()
    Handler.session = CamSession(args.cam_ip, args.onvif_port, user, pw)

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"cam-control on {args.host}:{args.port} -> ONVIF {args.cam_ip}:{args.onvif_port} "
          f"(lazy connect; lockout-safe). Ctrl-C to stop.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
