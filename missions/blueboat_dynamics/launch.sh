#!/bin/bash -e
#--------------------------------------------------------------
#   Script:  launch.sh
#  Mission:  blueboat_dynamics (Hellenic Naval Academy basin)
#   Launches a shoreside + N SIM vehicles drawn from a fixed
#   fleet roster. Vehicle naming, colors, and ports follow the
#   same convention as the encircle_swarm mission.
#--------------------------------------------------------------
on_exit() { echo; echo "$ME: Halting all apps"; kill -- -$$ 2>/dev/null || true; }
trap on_exit SIGINT

ME=$(basename "$0")
TIME_WARP=1
JUST_MAKE=""
VERBOSE=""
XMODE="SIM"
MISSION_NAME=""
AMT=1
STAGGER=0
MAX_SPD="2"
CONTROLLER="default"   # default | km (pBBPID) | rt (pDiffThrustPID_v2)
TUNER=""        # non-empty => open the pBBPID tuner; value = target vname

# a-f fleet; per-vehicle start pos set in launch_vehicle.sh. Ports
# increment per vehicle.
ALL_VNAMES="asha bama chip dale ewan flex"
COLORS="coral dodger_blue green orange yellow white"
BASE_MPORT=9001
BASE_PSHARE=9201

#---------------------------------------------------------------
for ARGI; do
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ]; then
        echo "$ME [OPTIONS] [time_warp]"
        echo "  --help, -h         Show this help"
        echo "  --just_make, -j    Make targ files only, no launch"
        echo "  --verbose          Verbose output"
        echo "  --amt=N            Number of vehicles (1-6, default 1)"
        echo "  --stagger=SECS     Seconds between vehicle launches (default 0)"
        echo "  --xmode=MODE       XMODE=BBOAT or SIM (default: SIM)"
        echo "  --controller=C     Controller: default | km | rt (default: default)"
        echo "  --max_spd=N        Max helm/sim speed (default 2)"
        echo "  --tuner            Open pBBPID tuner GUI on shoreside (km only)"
        exit 0
    elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then
        TIME_WARP=$ARGI
    elif [ "${ARGI}" = "--just_make" -o "${ARGI}" = "-j" ]; then
        JUST_MAKE="-j"
    elif [ "${ARGI}" = "--verbose" -o "${ARGI}" = "-v" ]; then
        VERBOSE="--verbose"
    elif [ "${ARGI:0:6}" = "--amt=" ]; then
        AMT="${ARGI#--amt=}"
    elif [ "${ARGI:0:10}" = "--stagger=" ]; then
        STAGGER="${ARGI#--stagger=}"
    elif [ "${ARGI:0:8}" = "--xmode=" ]; then
        XMODE="${ARGI#--xmode=}"
    elif [ "${ARGI:0:10}" = "--max_spd=" ]; then
        MAX_SPD="${ARGI#--max_spd=}"
    elif [ "${ARGI:0:13}" = "--controller=" ]; then
        CONTROLLER="${ARGI#--controller=}"
    elif [ "${ARGI}" = "--tuner" ]; then
        TUNER="__first__"
    elif [ "${ARGI:0:8}" = "--tuner=" ]; then
        TUNER="${ARGI#--tuner=}"
    else
        echo "$ME: Unknown arg: $ARGI"; exit 1
    fi
done

if [ "$AMT" -lt 1 -o "$AMT" -gt 6 ]; then
    echo "$ME: --amt must be in [1,6]. Exit."; exit 1
fi

[ -z "$MISSION_NAME" ] && MISSION_NAME=$(mhash_gen)
mkdir -p logs/${MISSION_NAME}

#---------------------------------------------------------------
#  BBOAT: identity auto-detected on the vehicle; launch one boat
#---------------------------------------------------------------
if [ "$XMODE" = "BBOAT" ]; then
    echo "$ME: Launching field BlueBoat (MISSION_NAME=$MISSION_NAME)"
    ./launch_vehicle.sh --mname=$MISSION_NAME --controller=$CONTROLLER \
        $VERBOSE $JUST_MAKE $TIME_WARP
    exit 0
fi

#---------------------------------------------------------------
#  SIM: shoreside first, then N vehicles (optionally staggered)
#---------------------------------------------------------------
read -r -a VNAME_ARR <<< "$ALL_VNAMES"
read -r -a COLOR_ARR <<< "$COLORS"

CSV_VNAMES=""
for ((IX=0; IX<AMT; IX++)); do
    CSV_VNAMES="${CSV_VNAMES:+$CSV_VNAMES,}${VNAME_ARR[$IX]}"
done

# The pBBPID tuner runs on the SHORESIDE (as a pAntler process); it pipes
# gains to the vehicle(s) and scopes telemetry bridged back from them.
TUNER_ARG=""
[ -n "$TUNER" ] && TUNER_ARG="--tuner"

echo "$ME: Launching Shoreside (vnames=$CSV_VNAMES) ..."
./launch_shoreside.sh --auto --sim --mname=$MISSION_NAME --vnames=$CSV_VNAMES \
    --controller=$CONTROLLER $TUNER_ARG $VERBOSE $JUST_MAKE $TIME_WARP

for ((IX=0; IX<AMT; IX++)); do
    VNAME="${VNAME_ARR[$IX]}"
    MPORT=$((BASE_MPORT + IX))
    PSHARE=$((BASE_PSHARE + IX))
    COLOR="${COLOR_ARR[$IX]:-coral}"
    echo "$ME: Launching $VNAME (SIM, mport=$MPORT, pshare=$PSHARE, color=$COLOR)"
    ./launch_vehicle.sh --mname=$MISSION_NAME --vname=$VNAME --color=$COLOR \
        --mport=$MPORT --pshare=$PSHARE --max_spd=$MAX_SPD --controller=$CONTROLLER \
        --sim --auto $VERBOSE $JUST_MAKE $TIME_WARP
    if [ "$JUST_MAKE" != "-j" ] && [ "$STAGGER" != "0" ] && [ "$IX" -lt "$((AMT-1))" ]; then
        echo "$ME: ... waiting ${STAGGER}s before next vehicle"
        sleep "$STAGGER"
    fi
done

[ "$JUST_MAKE" = "-j" ] && exit 0

uMAC targs/targ_shoreside.moos
kill -- -$$ 2>/dev/null || true
