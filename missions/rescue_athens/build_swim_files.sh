#!/bin/bash 
#-------------------------------------------------------------- 
#   Script: build_swim_files.sh  
#   Author: Michael Benjamin   
#   LastEd: April 2023
#-------------------------------------------------------------- 
#  Part 1: Define a convenience function for producing terminal
#          debugging/status output depending on the verbosity.
#-------------------------------------------------------------- 
vecho() { if [ "$VERBOSE" != "" ]; then echo "$ME: $1"; fi }


#-------------------------------------------------------------- 
#  Part 2: Set Global variables
#-------------------------------------------------------------- 
OPA1="28.4,16.7:35.4,28.2:11,42.5:3.6,30.8"
OPA2="28.4,16.7:38.4,33.4:27.6,52.2:-0.4,58:-12.3,40.1"
OPA3="28.4,16.7:38.4,33.4:39,56:21.2,67.8:-7.8,67.9:-25.5,47.5"
OPA4="28.4,16.7:38.4,33.4:42.8,61.5:29,89.1:-9,91.5:-34.9,52.8"


gen_swimmers --poly=$OPA1 --swimmers=5  --sep=3 > athens_00.txt
gen_swimmers --poly=$OPA1 --swimmers=5  --sep=3 > athens_01.txt
gen_swimmers --poly=$OPA2 --swimmers=7  --sep=5 > athens_02.txt
gen_swimmers --poly=$OPA3 --swimmers=9  --sep=6 > athens_03.txt
gen_swimmers --poly=$OPA4 --swimmers=11 --sep=7 > athens_04.txt
