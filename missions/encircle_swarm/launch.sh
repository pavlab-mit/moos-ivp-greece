#!/bin/bash -e
#--------------------------------------------------------------
#   encircle_swarm launch script (Hellenic Naval Academy basin)
#   Launches a shoreside + N SIM vehicles that all encircle ONE
#   common circle. pEncircle spaces them, so each vehicle slots
#   seamlessly into the ring as it deploys. Use --stagger to bring
#   the vehicles online one at a time to see the join happen.
#--------------------------------------------------------------

ME=$(basename "$0")
TIME_WARP=1
JUST_MAKE=""
VERBOSE=""
XMODE="SIM"
MISSION_NAME=""
HIGH_RES=""
AMT=4
STAGGER=0

# a-f fleet; per-vehicle start pos set in launch_vehicle.sh. Ports
# increment per vehicle. All share the single encircle circle.
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
        echo "  --amt=N            Number of vehicles (1-6, default 4)"
        echo "  --stagger=SECS     Seconds between vehicle launches (default 0)"
        echo "  --xmode=MODE       XMODE=BBOAT or SIM (default: SIM)"
        echo "  --high-res         Use high-res satellite TIFF"
        exit 0
    elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then
        TIME_WARP=$ARGI
    elif [ "${ARGI}" = "--just_make" -o "${ARGI}" = "-j" ]; then
        JUST_MAKE="-j"
    elif [ "${ARGI}" = "--verbose" ]; then
        VERBOSE="--verbose"
    elif [ "${ARGI:0:6}" = "--amt=" ]; then
        AMT="${ARGI#--amt=}"
    elif [ "${ARGI:0:10}" = "--stagger=" ]; then
        STAGGER="${ARGI#--stagger=}"
    elif [ "${ARGI:0:8}" = "--xmode=" ]; then
        XMODE="${ARGI#--xmode=}"
    elif [ "${ARGI}" = "--high-res" ]; then
        HIGH_RES="--high-res"
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
    ./launch_vehicle.sh --mname=$MISSION_NAME $VERBOSE $JUST_MAKE $TIME_WARP
    exit 0
fi

#---------------------------------------------------------------
#  SIM: shoreside first, then N vehicles (optionally staggered) so
#       each one joins the ring as it comes online.
#---------------------------------------------------------------
read -r -a VNAME_ARR <<< "$ALL_VNAMES"
read -r -a COLOR_ARR <<< "$COLORS"

CSV_VNAMES=""
for ((IX=0; IX<AMT; IX++)); do
    CSV_VNAMES="${CSV_VNAMES:+$CSV_VNAMES,}${VNAME_ARR[$IX]}"
done

echo "$ME: Launching Shoreside (vnames=$CSV_VNAMES) ..."
./launch_shoreside.sh --auto --mname=$MISSION_NAME --vnames=$CSV_VNAMES $VERBOSE $HIGH_RES $JUST_MAKE $TIME_WARP

for ((IX=0; IX<AMT; IX++)); do
    VNAME="${VNAME_ARR[$IX]}"
    MPORT=$((BASE_MPORT + IX))
    PSHARE=$((BASE_PSHARE + IX))
    COLOR="${COLOR_ARR[$IX]:-coral}"
    echo "$ME: Launching $VNAME (SIM, mport=$MPORT, pshare=$PSHARE, color=$COLOR)"
    ./launch_vehicle.sh --mname=$MISSION_NAME --vname=$VNAME --color=$COLOR \
        --mport=$MPORT --pshare=$PSHARE --sim --auto $VERBOSE $JUST_MAKE $TIME_WARP
    if [ "$JUST_MAKE" != "-j" ] && [ "$STAGGER" != "0" ] && [ "$IX" -lt "$((AMT-1))" ]; then
        echo "$ME: ... waiting ${STAGGER}s before next vehicle"
        sleep "$STAGGER"
    fi
done

[ "$JUST_MAKE" = "-j" ] && exit 0

uMAC targs/targ_shoreside.moos
kill -- -$$ 2>/dev/null || true
