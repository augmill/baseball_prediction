#!/bin/bash
#  
# Purpose: Uploads CSV data to a Biq Query table
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./UploadCSVtoBQ.sh [ data set name ] [ table name ] [ path to data file ]"
example="Example: ./UploadCSVtoBQ.sh my_dataset my_table /tmp/my_cleaned_data.csv"

#TODO: add -v opt to all scripts to skip verification
#TODO maybe add a way to verify data isnt duplicated in the DB

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
data_file="$3"

# Verify Input
auth_check=$("./CheckGCloudCredintals.sh")
if [ $? -ne 0 ]; then
   echo "$auth_check"
   exit 1
fi

data_set_check=$("./CheckIfBQDataSetExists.sh" "$data_set")
if [ $? -ne 0 ]; then
   echo "$data_set_check"
   echo "Error: CheckIfBQDataSetExists.sh failed. Exiting..."
   exit 1
elif [[ "$data_set_check" != "Yes" ]]; then
   echo "Error: dataset $data_set does not exist. Exiting..."
   exit 1
fi

table_check=$("./CheckIfBQTableExists.sh" "$data_set" "$table")
if [ $? -ne 0 ]; then
   echo "$table_check"
   echo "Error: CheckIfBQTableExists.sh failed. Exiting..."
   exit 1
elif [[ "$table_check" != "Yes" ]]; then
   echo "Error: table $table does not exist. Exiting..."
   exit 1
fi

if [ ! -f "$data_file" ]; then
   echo "Error: file $data_file does not exist. Exiting..."
   exit 1
fi

echo "Uploading CSV file $data_file to BigQuery table $data_set.$table..."

upload_result=$(bq load \
   --source_format=CSV \
   --skip_leading_rows=1 \
   --allow_quoted_newlines \
   --allow_jagged_rows \
   --project_id=$(gcloud config get-value project) \
   "$data_set.$table" \
   "$data_file" 2>&1)

if [ $? -ne 0 ]; then
   echo "Error: Failed to upload CSV to BigQuery table."
   echo "$upload_result"
   exit 1
fi

echo "$upload_result"
echo "Successfully uploaded $data_file to $data_set.$table"
