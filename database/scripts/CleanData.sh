#!/bin/bash
#  
# Purpose: Cleans raw pybaseball statcast CSV data.
#
# Note: Should be used in conjunction with the GetData.sh script
# Note: Wrapper for Python CleanData.py
# Note: Places the cleaned data files in the /tmp directory.
#
# TODOS: Add option to delete raw data file after processing
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./CleanData.sh [path to raw data file]"
example="Example: ./CleanData.sh s2025-10-09_e2025-10-09_raw.csv"

while getopts ":h" opt; do
   case $opt in
      h) 
        echo "$usage"
        echo "$example"
        exit 0
        ;;
     \?)
        echo "$usage"
        echo "$example"
        exit 1
        ;;
   esac
done

if [ $# -ne 1 ]; then
    echo "$usage"
    echo "$example"
    exit 1
fi

raw_file="$1"

if [ ! -f "$raw_file" ]; then
    echo "Error: file $raw_file does not exist. Exiting..."
    exit 1
fi

clean_file=$(echo "$raw_file" | sed 's/_raw\.csv/_clean.csv/')

res=$(python3 "./CleanData.py" "$raw_file")
if [ $? -ne 0 ]; then
    echo "$res"
    echo "Error: CleanData.py failed. Exiting..."
    rm "$clean_file"
    exit 1
fi

echo "Data from $raw_file has been successfully cleaned and saved to $clean_file"
exit 0