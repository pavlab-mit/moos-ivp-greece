#!/bin/bash 
#-------------------------------------------------------
#   Script: get_scout.sh                                    
#   Author: Michael Benjamin  
#     Date: May 2025     
#-------------------------------------------------------
#  Part 1: Declare global var defaults
#-------------------------------------------------------
VAPP=""

#-------------------------------------------------------
#  Part 2: Check for and handle command-line arguments
#-------------------------------------------------------
for ARGI; do
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ]; then
	echo "get_scout.sh [SWITCHES]                           "
	echo "                                                  " 
	echo "Synopsis                                          " 
	echo "  Provisional script to determine the location of "
	echo "  BHV_Scout behavior based on the pGenRescue user " 
	exit 0;	
    elif [ "${VUSER}" = "" ]; then
	VAPP=$ARGI
    else 
	echo "get_scout.sh: Bad Arg:[$ARGI]. Exit Code 1."
	exit 1
    fi
done

#-------------------------------------------------------
#  Part 2: Do the cleaning!
#-------------------------------------------------------
ROOT_DIR="/Users/mikerb/Research/autotest/harnesses_athens"

if [[ "${VAPP}" == *"kostas"* ]]; then
    echo "$ROOT_DIR/20-moos-ivp-vasileios2/lib"

elif [[ "${VAPP}" == *"vagsgr"* ]]; then
    echo "$ROOT_DIR/15-moos-ivp-gkarolos"

elif [[ "${VAPP}" == *"xeqtor"* ]]; then
    echo "$ROOT_DIR/07-moos-ivp-goni"

elif [[ "${VAPP}" == *"kosCharisis"* ]]; then
    echo "$ROOT_DIR/05-moos-ivp-kosCharisis"

elif [[ "${VAPP}" == *"stathes1"* ]]; then
    echo "$ROOT_DIR/21-moos-ivp-nikosspap"
    
elif [[ "${VAPP}" == *"jjacke13"* ]]; then
    echo "$ROOT_DIR/03-moos-ivp-geochrys"
    
elif [[ "${VAPP}" == *"GeorgeDimitropoulos"* ]]; then
    echo "$ROOT_DIR/"

elif [[ "${VAPP}" == *"dkoupats"* ]]; then
    echo "$ROOT_DIR/08-moos-ivp-k2017"
    
    
fi
