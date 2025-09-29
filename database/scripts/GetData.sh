#!/bin/bash
#  
# Purpose: Pulls raw statcast data from pybaseball for a specified date range and saves to temporary CSV file
#
# Note: Both start date and end date are inclusive
# Note: Wrapper for Python GetData.py
# Note: Places the raw data files in the /tmp directory.
#
# TODOS: Add option to exclude specific features via CSV list
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./GetData.sh [ start date (YYYY-MM-DD) ] [ end date (YYYY-MM-DD) ]"
example="Example: ./GetData.sh 2024-01-01 2024-01-31"

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

start_date="$1"
end_date="$2"

# Validate dates are the correct format
if ! [[ "$start_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "Error: Start date format is invalid. Expected YYYY-MM-DD."
    exit 1
elif ! [[ "$end_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "Error: End date format is invalid. Expected YYYY-MM-DD."
    exit 1
fi

# Create file to hold raw data
raw_file="/tmp/s${start_date}_e${end_date}_raw.csv"
touch "$raw_file" #TODO does this need an error check?

# Run python script to pull data 
res=$(python3 "./GetData.py" "$start_date" "$end_date" "$raw_file")
if [ $? -ne 0 ]; then
    echo "$res"
    echo "Error, GetData.py failed. Exiting..."
    exit 1
fi

data_size=$(du -sh "$raw_file" | awk '{print $1}')
echo "Downloaded $data_size to $raw_file"
exit 0
