#!/bin/bash
#--------------------------------------------------------------
#   <TEMPLATE>
#   Script: post_process.sh
#   Author: Raymond Turrisi
#   LastEd: October 2024
#    Brief: 
#        A template mission post processing script
#        1) gets rid of irrelevant log files 
#        2) uses thin_logdirs as defined in 
#           moos-ivp-pavlab/scripts to get rid of all the 
#           variables which are typically not used in analysis,
#        3) uses mdm and the wrapper script to extract all the 
#           data from all the subdirectories and get them into 
#           csv's and jsons
#        4) uses an example plotting script after using the data
#           the data extracted from the alogs with mdm
#--------------------------------------------------------------

# Activate Python virtual environment
source ~/moos/venv/bin/activate

mission_directory=$1

rm -rf $mission_directory/*/*.blog $mission_directory/*/*.ylog $mission_directory/*/*.slog

eval thin_logdirs $mission_directory/

mdm_tree_root=$mission_directory/

eval ./mdm/mw_directory_conversion.sh $mdm_tree_root

# Run post-processing plotting scripts
echo "Running vehicle trajectory plot..."
python3 pyplots/vehicle_trajectory_plot.py ${mdm_tree_root}

echo "Running side scan diagnostics plot..."
python3 pyplots/omniscan_sidescan_diagnostics_plot.py ${mdm_tree_root}

echo "Running incremental waterfall generation with enhanced processing..."
# Full PINGMapper-inspired pipeline: SRC -> EGN -> Gamma correction
python3 pyplots/omniscan_incremental_waterfalls.py ${mdm_tree_root} --pings-per-waterfall 1000 --slant-range-correction --egn --gamma 1

echo "Running enriched waterfall generation (with vehicle state data)..."
# Enriched waterfalls use vehicle_state.csv for altitude, position, heading when available
python3 pyplots/omniscan_enriched_waterfalls.py ${mdm_tree_root} --pings-per-waterfall 1000 --slant-range-correction --egn --gamma 1.1

echo "Running nav comparison analysis..."
for alog in $(find ${mdm_tree_root} -name "*.alog" -type f); do
    python3 pyplots/nav_comparison.py ${alog}
done

echo "Running offline EKF analysis..."
for alog in $(find ${mdm_tree_root} -name "*.alog" -type f); do
    python3 pyplots/offline_ekf.py ${alog}
done

echo "Running magnetometer analysis..."
python3 pyplots/mag_analysis.py ${mdm_tree_root}

echo "Post-processing complete. Results saved to ${mdm_tree_root}"