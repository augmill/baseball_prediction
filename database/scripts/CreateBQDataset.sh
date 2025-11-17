#!/bin/bash
#  
# Purpose: Creates a new BigQuery dataset
#
# TODOS: add an option to specify a location
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./CreateBQDataSet.sh [ data set name ]"
example="Example: ./CreateBQDataSet.sh my_dataset"

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

data_set="$1"

# Verify Input
auth_check=$("./CheckGCloudCredintals.sh")
if [ $? -ne 0 ]; then
   echo "$auth_check"
   exit 1
fi

# Check if data set already exists
data_set_check=$("./CheckIfBQDataSetExists.sh" "$data_set")
if [ $? -ne 0 ]; then
    echo "$data_set_check"
    echo "Error: CheckIfBQDataSetExists.sh failed. Exiting..."
    exit 1
elif [[ "$data_set_check" != "No" ]]; then
    echo "Error: dataset in $dataset already exists. Exiting..."
    return 1
fi

# create the new data set
res=$(bq mk --dataset "$data_set")
if [ $? -ne 0 ]; then
    echo "$res"
    echo "Error: failed to create new data set $data_set. Exiting..."
    exit 1
fi