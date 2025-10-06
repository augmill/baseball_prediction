#!/bin/bash
#  
# Purpose: Checks if a BigQuery table exists
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./CheckIfBQTableExists.sh [ data set name ] [ table name ]"
example="Example: ./CheckIfBQTableExists.sh my_dataset my_table"

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

if [ $# -ne 2 ]; then
   echo "$usage"
   echo "$example"
   exit 1
fi

data_set="$1"
table="$2"

# Verify Input
auth_check=$("./CheckGCloudCredintals.sh")
if [ $? -ne 0 ]; then
   echo "$auth_check"
   exit 1
fi

# Check if dataset exists first
data_set_check=$("./CheckIfBQDataSetExists.sh" "$data_set")
if [ $? -ne 0 ]; then
   echo "$data_set_check"
   echo "Error: CheckIfBQDataSetExists.sh failed. Exiting..."
   exit 1
elif [[ "$data_set_check" != "Yes" ]]; then
   echo "No"
   exit 0
fi

# Check if table exists
table_exists=$(bq ls --project_id=$(gcloud config get-value project) "$data_set" | grep -w "$table")

if [ -n "$table_exists" ]; then
   echo "Yes"
   exit 0
else
   echo "No"
   exit 0
fi