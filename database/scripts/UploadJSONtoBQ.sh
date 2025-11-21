#!/bin/bash
#  
# Purpose: Uploads structured JSON data to a Biq Query table
#
# Note: Data must be Newline-Delimited JSON (one JSON object per row)
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./UploadJSONtoBQ.sh [ data set name ] [ table name ] [ path to data file ]"
example="Example: ./UploadJSONtoBQ.sh my_dataset my_table /tmp/my_cleaned_data.json"

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

echo "Uploading JSON file $data_file to BigQuery table $data_set.$table..."

upload_result=$(bq load \
   --source_format=NEWLINE_DELIMITED_JSON \
   --project_id=$(gcloud config get-value project) \
   "$data_set.$table" \
   "$data_file" 2>&1
)

if [ $? -ne 0 ]; then
    echo "$upload_result"
    echo "Error: Failed to upload JSON data to BigQuery table."
    exit 1
fi

echo "$upload_result"
echo "Successfully uploaded $data_file to $data_set.$table"
