#!/bin/bash
#--------------------------------------------------------------
#   Script:  launch_difftuner.sh
#  Mission:  blueboat_dynamics
#   Opens the pDiffThrustPID_v2 web tuner (pDiffThrustTuner, a pymoos2 app).
#   The tuner is a SHORESIDE app, so it defaults to the shoreside targ
#   (DB 9000, publish_suffix=_ALL -> qbridge routes updates to the vehicle).
#   Pass a bare port to instead connect DIRECTLY to a vehicle DB (no bridges,
#   handy for sim): vehicles start at 9001 (asha), 9002 (bama), ...
#
#   Usage:  ./launch_difftuner.sh [PORT | targ.moos] [WEBPORT]
#     ./launch_difftuner.sh                       # shoreside (9000) via targ_shoreside.moos
#     ./launch_difftuner.sh 9001                  # direct to first vehicle DB
#     ./launch_difftuner.sh targs/targ_shoreside.moos
#
#   Python: set DIFF_PYTHON to a python with pymoos2, else probes.
#--------------------------------------------------------------
ME=$(basename "$0")
MDIR=$(cd "$(dirname "$0")" && pwd)
ARG="${1:-$MDIR/targs/targ_shoreside.moos}"   # shoreside targ (9000, _ALL) by default
WEBPORT="${2:-8080}"

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

if [ -f "$ARG" ] || [[ "$ARG" == *.moos ]]; then
    TARG="$ARG"                          # shoreside: targ_shoreside.moos carries publish_suffix=_ALL
    [ -f "$TARG" ] || { echo "$ME: targ not found: $TARG"; exit 1; }
else
    mkdir -p "$MDIR/targs"
    TARG="$MDIR/targs/targ_difftuner.moos"
    cat > "$TARG" <<EOF
ServerHost = localhost
ServerPort = $ARG
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
fi

( sleep 1; command -v open >/dev/null 2>&1 && open "http://localhost:$WEBPORT" ) &
exec "$PYBIN" "$TUNER" "$TARG"
