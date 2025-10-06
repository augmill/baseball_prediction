#!/bin/bash
#  
# Purpose: Checks if a BigQuery dataset exists
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./CheckIfBQDataSetExists.sh [ data set name ]"
example="Example: ./CheckIfBQDataSetExists.sh my_dataset"

#TODO: add -v opt to all scripts to skip verification

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

# Check if dataset exists
dataset_exists=$(bq ls -d | grep -w "$data_set")

if [ -n "$dataset_exists" ]; then
   echo "Yes"
   exit 0
else
   echo "No"
   exit 0
fi