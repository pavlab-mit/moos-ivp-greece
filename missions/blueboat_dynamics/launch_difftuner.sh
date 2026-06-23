#!/bin/bash
#--------------------------------------------------------------
#   Script:  launch_difftuner.sh
#  Mission:  blueboat_dynamics
#   Opens the pDiffThrustPID_v2 web tuner (pDiffThrustTuner,
#   a pymoos2 app) connected directly to one MOOSDB. For SIM
#   no broker/bridges are needed -- the tuner shares the DB
#   with the controller.
#
#   Usage:  ./launch_difftuner.sh [PORT] [WEBPORT]
#     ./launch_difftuner.sh              # DB 9001, web 8080
#     ./launch_difftuner.sh 9001 8081    # explicit
#
#   Python: set DIFF_PYTHON to a python with pymoos2, else probes.
#--------------------------------------------------------------
ME=$(basename "$0")
PORT="${1:-9001}"
WEBPORT="${2:-8080}"
MDIR=$(cd "$(dirname "$0")" && pwd)

TUNER=""
for C in \
    "$DIFF_TUNER" \
    "$MDIR/../../../moos-ivp-blueboat/src/pDiffThrustTuner/pDiffThrustTuner.py" \
    "$MDIR/../../moos-ivp-blueboat/src/pDiffThrustTuner/pDiffThrustTuner.py" \
    "$HOME/moos/moos-ivp-blueboat/src/pDiffThrustTuner/pDiffThrustTuner.py" ; do
    [ -n "$C" ] && [ -f "$C" ] && { TUNER="$C"; break; }
done
[ -z "$TUNER" ] && { echo "$ME: pDiffThrustTuner.py not found. Set DIFF_TUNER."; exit 1; }

PYBIN=""
for C in "$DIFF_PYTHON" python3 python ; do
    [ -z "$C" ] && continue
    command -v "$C" >/dev/null 2>&1 && "$C" -c "import pymoos2" >/dev/null 2>&1 && { PYBIN="$C"; break; }
done
[ -z "$PYBIN" ] && { echo "$ME: no python with pymoos2 found. Set DIFF_PYTHON."; exit 1; }

mkdir -p "$MDIR/targs"
TARG="$MDIR/targs/targ_difftuner.moos"
cat > "$TARG" <<EOF
ServerHost = localhost
ServerPort = $PORT
Community  = difftuner

ProcessConfig = pDiffThrustTuner
{
  AppTick        = 8
  CommsTick      = 8
  web_port       = $WEBPORT
  history        = 90
  publish_suffix =
}
EOF

( sleep 1; command -v open >/dev/null 2>&1 && open "http://localhost:$WEBPORT" ) &
exec "$PYBIN" "$TUNER" "$TARG"
