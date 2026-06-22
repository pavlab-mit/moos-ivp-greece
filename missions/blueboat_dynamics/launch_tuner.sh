#!/bin/bash
#--------------------------------------------------------------
#   Script:  launch_tuner.sh
#  Mission:  blueboat_dynamics
#   Opens the pBBPID live tuner/scope (uBBPIDTuner.py, a pymoos2
#   GUI from moos-ivp-blueboat) against ONE vehicle's MOOSDB.
#
#   Usage:  ./launch_tuner.sh [VNAME | INDEX | PORT]
#     ./launch_tuner.sh            # asha  (port 9001)
#     ./launch_tuner.sh bama       # by fleet name
#     ./launch_tuner.sh 2          # 3rd vehicle (index, 0-based)
#     ./launch_tuner.sh 9003       # explicit MOOSDB port
#
#   Python: set BBPID_PYTHON to a python that has pymoos2 + matplotlib,
#   otherwise the script probes a few common locations.
#--------------------------------------------------------------
ME=$(basename "$0")
HOST="localhost"
HISTORY=30

# Fleet roster + base port must match launch.sh
ALL_VNAMES="asha bama chip dale ewan flex"
BASE_MPORT=9001

#--- Resolve target port from arg (vname / index / port) ------
ARG="${1:-asha}"
PORT=""
if [[ "$ARG" =~ ^[0-9]+$ ]]; then
    if [ "$ARG" -ge 9000 ]; then
        PORT="$ARG"                       # explicit port
    else
        PORT=$((BASE_MPORT + ARG))        # index
    fi
else
    IX=0
    for V in $ALL_VNAMES; do
        if [ "$V" = "$ARG" ]; then PORT=$((BASE_MPORT + IX)); break; fi
        IX=$((IX + 1))
    done
fi
if [ -z "$PORT" ]; then
    echo "$ME: could not resolve '$ARG' to a port. Roster: $ALL_VNAMES"; exit 1
fi

#--- Locate the tuner script (moos-ivp-blueboat/scripts) ------
MDIR=$(cd "$(dirname "$0")" && pwd)
TUNER=""
for CAND in \
    "$BBPID_TUNER" \
    "$MDIR/../../../moos-ivp-blueboat/scripts/uBBPIDTuner.py" \
    "$MDIR/../../moos-ivp-blueboat/scripts/uBBPIDTuner.py" \
    "$HOME/MOOS/moos-ivp-blueboat/scripts/uBBPIDTuner.py" ; do
    [ -n "$CAND" ] && [ -f "$CAND" ] && { TUNER="$CAND"; break; }
done
if [ -z "$TUNER" ]; then
    echo "$ME: could not find uBBPIDTuner.py. Set BBPID_TUNER to its path."; exit 1
fi

#--- Pick a python that can import pymoos2 --------------------
PYBIN=""
for CAND in "$BBPID_PYTHON" "$HOME/base/bin/python3" python3 python ; do
    [ -z "$CAND" ] && continue
    if command -v "$CAND" >/dev/null 2>&1 && \
       "$CAND" -c "import pymoos2, matplotlib" >/dev/null 2>&1; then
        PYBIN="$CAND"; break
    fi
done
if [ -z "$PYBIN" ]; then
    echo "$ME: no python with pymoos2+matplotlib found. Set BBPID_PYTHON."; exit 1
fi

echo "$ME: tuner -> $HOST:$PORT  (python=$PYBIN)"
exec "$PYBIN" "$TUNER" --host "$HOST" --port "$PORT" --history "$HISTORY"
