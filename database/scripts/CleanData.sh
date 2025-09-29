#!/bin/bash
#  
# Purpose: Cleans raw baseball data CSV file using existing Python cleaning logic
# Note: Wrapper for dataProcesser.clean_data() method. Optionally deletes original raw file.
#
##########
usage="./CleanData.sh [raw_data_file_path] [optional: --delete-raw]"
example="./CleanData.sh /tmp/baseball_raw_2024-01-01_2024-01-31.csv --delete-raw"
