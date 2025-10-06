#!/bin/bash
#  
# Purpose: Creates a new BigQuery table from a SQL file contaings 
#          the DDL for the table
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./CreateBQTable.sh [ data set name ] [ table name] [ path to SQL file]"
example="Example: ./CreateBQTable.sh my_dataset my_new_table ./table_ddl.sql"

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

if [ $# -ne 3 ]; then
   echo "$usage"
   echo "$example"
   exit 1
fi

data_set="$1"
table="$2"
ddl_file="$3"

# Verify Input
auth_check=$("./CheckGCloudCredintals.sh")
if [ $? -ne 0 ]; then
   echo "$auth_check"
   exit 1
fi

# Check that data set exists
ds_check=$("./CheckIfBQDataSetExists.sh" "$data_set")
if [ $? -ne 0 ]; then
    echo "$ds_check"
    echo "Error: CheckIfBQDataSetExists.sh failed. Exiting..."
    exit 1
elif [[ "$ds_check" != "Yes" ]]; then
    echo "Error: dataset $data_set does not exist. Exiting..."
    exit 1
fi

# Check that a table with the same name does not already exist
table_check=$("./CheckIfBQTableExists.sh" "$data_set" "$table")
if [ $? -ne 0 ]; then
    echo "$table_check"
    echo "Error: CheckIfBQTableExists.sh failed. Exiting..."
    exit 1
elif [[ "$table_check" != "No" ]]; then
    echo "Error: table $table already exists in dataset $data_set. Exiting..."
    exit 1
fi

# Check that SQL file exists
if [ ! -f $ddl_file ]; then
    echo "Error: DDL file $ddl_file does not exist. Exiting..."
    exit 1
fi

table_ddl=$(cat "$ddl_file")
if [ -z "$table_ddl" ]; then
    echo "Error: DDL file $ddl_fike is empty. Exiting..."
    exit 1
fi

echo "Creating table $table in BigQuery dataset $data_set..."
res=$(bq query --project_id="baseball-prediction-473623" --dataset_id="$data_set" --nouse_legacy_sql "$table_ddl")
if [ $? -ne 0 ]; then
    echo "$res"
    echo "Error: failed to create the table $table. Exiting..."
    exit 1
fi

echo "Finished creating table $data_set.$table"