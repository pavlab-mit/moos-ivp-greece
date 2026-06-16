#!/bin/bash
#Example directory conversion script

target_directory="$1"
destination_directory="${1}/data_mdm"

python3 -m mdm -d $target_directory/ \
    -o $destination_directory \
    -t csv json \
    -x mdm/mw_ix.cfg \
    --moos \
    --topic_mapping mdm/mw_moos_topic_mapping.cfg 