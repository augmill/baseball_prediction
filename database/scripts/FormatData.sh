#!/bin/bash
#  
# Purpose: Formats cleaned Statcast CSV into nested JSONL for BigQuery ingestion.
#
# Groups individual pitch records into per-at-bat objects that match the
# atbat_facts table schema, including the pitches[] array.
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./FormatData.sh <input_clean_csv> <output_jsonl>"
example="Example: ./FormatData.sh tmp/clean/pitches_2024-05-12.csv tmp/json/atbats_2024-05-12.jsonl"

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

input_clean_csv="$1"
output_jsonl="$2"

if [ ! -f "$input_clean_csv" ]; then
    echo "Error: Input file '$input_clean_csv' does not exist."
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the Python formatting script
python3 "$SCRIPT_DIR/FormatData.py" "$input_clean_csv" "$output_jsonl"

if [ $? -ne 0 ]; then
    echo "Error: FormatData.py failed."
    exit 1
fi

exit 0
