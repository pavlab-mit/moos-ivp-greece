#!/bin/bash -e
#--------------------------------------------------------------
#   survey_athens launch script (Hellenic Naval Academy basin)
#   Launches vehicle (BBOAT or SIM) with optional shoreside.
#--------------------------------------------------------------

ME=$(basename "$0")
TIME_WARP=1
JUST_MAKE=""
VERBOSE=""
VNAME="asha"
XMODE="SIM"
MISSION_NAME=""
HIGH_RES=""

#---------------------------------------------------------------
#  Parse command-line arguments
#---------------------------------------------------------------
for ARGI; do
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ]; then
        echo "$ME [OPTIONS] [time_warp]"
        echo "  --help, -h         Show this help"
        echo "  --just_make, -j    Make targ files only, no launch"
        echo "  --verbose          Verbose output"
        echo "  --vname=NAME       Vehicle name (default: asha for SIM)"
        echo "  --xmode=MODE       XMODE=BBOAT or SIM (default: SIM)"
        echo "  --high-res         Use high-res satellite TIFF"
        exit 0
    elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then
        TIME_WARP=$ARGI
    elif [ "${ARGI}" = "--just_make" -o "${ARGI}" = "-j" ]; then
        JUST_MAKE="-j"
    elif [ "${ARGI}" = "--verbose" ]; then
        VERBOSE="--verbose"
    elif [ "${ARGI:0:8}" = "--vname=" ]; then
        VNAME="${ARGI#--vname=}"
    elif [ "${ARGI:0:8}" = "--xmode=" ]; then
        XMODE="${ARGI#--xmode=}"
    elif [ "${ARGI}" = "--high-res" ]; then
        HIGH_RES="--high-res"
    else
        echo "$ME: Unknown arg: $ARGI"
        exit 1
    fi
done

[ -z "$MISSION_NAME" ] && MISSION_NAME=$(mhash_gen)
mkdir -p logs/${MISSION_NAME}

#---------------------------------------------------------------
#  Launch vehicle
#---------------------------------------------------------------
echo "$ME: Launching $VNAME (XMODE=$XMODE, MISSION_NAME=$MISSION_NAME)"
VEHICLE_ARGS="--mname=$MISSION_NAME --vname=$VNAME $VERBOSE $JUST_MAKE"
[ "$XMODE" = "SIM" ] && VEHICLE_ARGS="$VEHICLE_ARGS --sim --auto"

./launch_vehicle.sh $VEHICLE_ARGS $TIME_WARP

[ "$JUST_MAKE" = "-j" ] && exit 0

#---------------------------------------------------------------
#  SIM only: launch shoreside + uMAC (vehicle was launched with --auto)
#  BBOAT: launch_vehicle runs uMAC and blocks; we never get here
#---------------------------------------------------------------
if [ "$XMODE" = "SIM" ]; then
    echo "$ME: Launching Shoreside ..."
    ./launch_shoreside.sh --auto --mname=$MISSION_NAME $VERBOSE $HIGH_RES $TIME_WARP
    uMAC targs/targ_shoreside.moos
    kill -- -$$ 2>/dev/null || true
fi
