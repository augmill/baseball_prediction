#!/bin/bash
#  
# Purpose: Cleans raw Statcast CSV data prior to formatting and upload.
#
# Validates and prunes columns, normalizes missing values, and ensures
# numeric fields are parseable. Outputs a clean CSV suitable for downstream processing.
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./CleanData.sh <input_raw_csv> <output_clean_csv>"
example="Example: ./CleanData.sh tmp/raw/pitches_2024-05-12.csv tmp/clean/pitches_2024-05-12.csv"

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

if [ $# -ne 2 ]; then
    echo "$usage"
    echo "$example"
    exit 1
fi

input_raw_csv="$1"
output_clean_csv="$2"

if [ ! -f "$input_raw_csv" ]; then
    echo "Error: Input file '$input_raw_csv' does not exist."
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use PYTHON env var if set, otherwise default to python3
PYTHON_CMD="${PYTHON:-python3}"

# Run the Python cleaning script
$PYTHON_CMD "$SCRIPT_DIR/CleanData.py" "$input_raw_csv" "$output_clean_csv"

if [ $? -ne 0 ]; then
    echo "Error: CleanData.py failed."
    exit 1
fi

exit 0