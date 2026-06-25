#!/bin/bash
#--------------------------------------------------------
# Script: get_robot_info_greece.sh
#   Date: June 8th, 2026
#     By: Jeremy Wenger
#  About: A script for getting the pablo robot info based
#         on the IP address. When pablos are connected to 
#         robots, e.g., BlueBoats, they have one
#         of a known set of IP addrs.
#--------------------------------------------------------
#  Part 1: A convenience function for producing terminal
#          debugging/status output depending on verbosity.
#--------------------------------------------------------
vecho() { if [ "$VERBOSE" != "" ]; then echo "$ME: $1"; fi }

#--------------------------------------------------------
#  Part 2: Initialize global variables
#--------------------------------------------------------
ME=`basename "$0"`
VNAME=""
FSEAT=""
VEHICLE_TYPE=""
RADIO_IP=""
COLOR="yellow"
ACTION="name"
HINT_COLOR="coral"
HERON="heron"
BBOAT="blueboat"


#--------------------------------------------------------
#  Part 2: Check for and handle command-line arguments
#--------------------------------------------------------
for ARGI; do
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ]; then
        echo "$ME  [OPTIONS]                                       "
        echo "                                                     "
        echo "Synopsis:                                            "
        echo "  Get a Pablo info based on Heron IP Address. When a "
        echo "  pablo is connected to the frontseat of a Heron it  "
        echo "  will have a set IP address specific to the vname.  "
        echo "  This script will get the IP address from the system"
        echo "  answer either (a) the IP address itself, (b) the   "
        echo "  vehicle name, or (c) the front seat IP address from"
        echo "  the perspective of the pablo.                      "
        echo "  These three pieces of info are all need within the "
        echo "  the launch_vehicle.sh scripts for in-water missions"
        echo "                                                     "
        echo "  --help, -h            Display this help message    "
	    echo "  --name, -n            Get vehicle name             "
	    echo "  --type, -t            Get vehicle type             "
	    echo "  --radio               Get Radio IP address         "
	    echo "  --fseat, -f           Get Frontseat IP address     "
	    echo "  --color, -c           Get Vehicle color            "
	    echo "  --return, -r          Get Vehicle return point     "
	    echo "  --ip, -ip             Get IP address               "
	    echo "  --hint=<value>        Non-empty hint is the answer "
        echo "                                                     "
        echo "Returns:                                             "
        echo "  0: Success                                         "
        echo "  1: Bad cmd line argument                           "
        echo "  2: Linux hostname did not succeed                  "
        echo "  3: Unspecified requested action                    "
        echo "  4: Detected IP address not of known robot          "
        echo "                                                     "
        echo "Returns:                                             "
        echo "  0: Success                                         " 
        exit 0;
    elif [ "${ARGI}" = "--name" -o "${ARGI}" = "-n" ]; then
	ACTION="name"
    elif [ "${ARGI}" = "--type" -o "${ARGI}" = "-t" ]; then
	ACTION="type"
    elif [ "${ARGI}" = "--TYPE" -o "${ARGI}" = "-T" ]; then
	ACTION="type"
	HERON="M300"
	BBOAT="BBOAT"
    elif [ "${ARGI}" = "--fseat" -o "${ARGI}" = "-f" ]; then
	ACTION="fseat"
    elif [ "${ARGI}" = "--color" -o "${ARGI}" = "-c" ]; then
	ACTION="color"
    elif [ "${ARGI}" = "--return" -o "${ARGI}" = "-r" ]; then
	ACTION="return"
    elif [ "${ARGI}" = "--ip" -o "${ARGI}" = "-ip" ]; then
	ACTION="ip"
    elif [ "${ARGI}" = "--radio" ]; then
	ACTION="radio"
    elif [ "${ARGI:0:7}" = "--hint=" ]; then
        HINT_COLOR="${ARGI#--hint=*}"
    else
	echo "$ME: Bad Arg:[$ARGI]. Exit Code 1."
	exit 1
    fi
done

#---------------------------------------------------------------
# Silently check that hostname succeeds and return "" if so.
# Should work on all linux systems
#---------------------------------------------------------------
hostname -I >& /dev/null
if [ $? != 0 ]; then
    echo "hostname -I failed. Exit Code 2"
    #exit 2
fi

IP_ADDR=`hostname -I | cut -d ' ' -f 1`

#---------------------------------------------------------------
# Part 3: Match IP address to BlueBoat name
#---------------------------------------------------------------

#ASHA AND EWAN FOR GREEN 
#BAMA AND CHIP FOR ORANGE

if [ "${IP_ADDR}" = "10.31.1.100" ]; then
    VNAME="asha";
    FSEAT="10.31.1.1"
    RADIO_IP="10.31.3.2"
    VEHICLE_TYPE=$BBOAT
    COLOR="green"
    RPOINT="-16,-13"
elif [ "${IP_ADDR}" = "10.32.1.100" ]; then
    VNAME="bama";
    FSEAT="10.32.1.1"
    RADIO_IP="10.32.3.2"
    VEHICLE_TYPE=$BBOAT
    COLOR="orange"
    RPOINT="-20,-17.2"
elif [ "${IP_ADDR}" = "10.33.1.100" ]; then
    VNAME="chip";
    FSEAT="10.33.1.1"
    RADIO_IP="10.33.3.2"
    VEHICLE_TYPE=$BBOAT
    COLOR="orange"
    RPOINT="-24,-21.4"
elif [ "${IP_ADDR}" = "10.34.1.100" ]; then
    VNAME="dale";
    FSEAT="10.34.1.1"
    RADIO_IP="10.34.3.2"
    VEHICLE_TYPE=$BBOAT
    COLOR="maroon"
    RPOINT="-28,-25.6"
elif [ "${IP_ADDR}" = "10.35.1.100" ]; then
    VNAME="ewan";
    FSEAT="10.35.1.1"
    RADIO_IP="10.35.3.2"
    VEHICLE_TYPE=$BBOAT
    COLOR="green"
    RPOINT="-32,-29.8"
elif [ "${IP_ADDR}" = "10.36.1.100" ]; then
    VNAME="flex";
    FSEAT="10.36.1.1"
    RADIO_IP="10.36.3.2"
    VEHICLE_TYPE=$BBOAT
    COLOR="violet"
    RPOINT="-36,-34"
else
    exit 4
fi

#---------------------------------------------------------------
# Part 4: Depending on the action, output results
#---------------------------------------------------------------
if [ "${ACTION}" = "name" ]; then
    echo -n $VNAME
elif [ "${ACTION}" = "type" ]; then
    echo -n $VEHICLE_TYPE
elif [ "${ACTION}" = "fseat" ]; then
    echo -n $FSEAT
elif [ "${ACTION}" = "ip" ]; then
    echo -n $IP_ADDR
elif [ "${ACTION}" = "radio" ]; then
    echo -n $RADIO_IP
elif [ "${ACTION}" = "color" ]; then
    if [ "${HINT_COLOR}" != "coral" ]; then
	echo -n $HINT_COLOR
    else
	echo -n $COLOR
    fi
elif [ "${ACTION}" = "return" ]; then
    echo -n $RPOINT
else
    echo -n ""
    exit 3
fi

echo ""
exit 0
