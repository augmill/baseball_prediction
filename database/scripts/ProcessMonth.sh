#!/bin/bash
#  
# Purpose: Ingests one month of data into BQ.
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./ProcessMonth.sh <dataset.table> <month (YYYY-MM)>"
example="Example: ./ProcessMonth.sh statcast_data.atbat_facts 2024-04"

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

# Verify authentication
auth_check=$("./CheckGCloudCredintals.sh")
if [ $? -ne 0 ]; then
   echo "$auth_check"
   exit 1
fi

if [ $# -ne 2 ]; then
   echo "$usage"
   echo "$example"
   exit 1
fi

# Parse arguments
IFS="." read -ra parts <<< "$1"
data_set="${parts[0]}"
table="${parts[1]}"
month="$2"

# Validate month format
if ! [[ "$month" =~ ^[0-9]{4}-[0-9]{2}$ ]]; then
    echo "Error: Month format is invalid. Expected YYYY-MM."
    exit 1
fi

# Extract year and month
year="${month:0:4}"
month_num="${month:5:2}"

# Determine last day of month
case "$month_num" in
    01|03|05|07|08|10|12) last_day="31" ;;
    04|06|09|11) last_day="30" ;;
    02) 
        # Check for leap year
        if [ $((year % 4)) -eq 0 ] && { [ $((year % 100)) -ne 0 ] || [ $((year % 400)) -eq 0 ]; }; then
            last_day="29"
        else
            last_day="28"
        fi
        ;;
    *)
        echo "Error: Invalid month number: $month_num"
        exit 1
        ;;
esac

start_date="${year}-${month_num}-01"
end_date="${year}-${month_num}-${last_day}"

# Check that dataset exists
data_set_check=$("./CheckIfBQDataSetExists.sh" "$data_set")
if [ $? -ne 0 ]; then
    echo "$data_set_check"
    echo "Error: CheckIfBQDataSetExists.sh failed. Exiting..."
    exit 1
elif [[ "$data_set_check" != "Yes" ]]; then
    echo "Error: dataset $data_set does not exist. Exiting..."
    exit 1
fi

# Check that table exists
table_check=$("./CheckIfBQTableExists.sh" "$data_set" "$table")
if [ $? -ne 0 ]; then
    echo "$table_check"
    echo "Error: CheckIfBQTableExists.sh failed. Exiting..."
    exit 1
elif [[ "$table_check" != "Yes" ]]; then
    echo "Error: table $table does not exist. Exiting..."
    exit 1
fi

# Check if data for this month already exists
echo "Checking if data for $month already exists in $data_set.$table..."
existing_count=$(bq query --use_legacy_sql=false --format=csv \
    "SELECT COUNT(*) as count FROM \`$(gcloud config get-value project).$data_set.$table\` 
     WHERE game_date >= '$start_date' AND game_date <= '$end_date'" 2>&1 | tail -n 1)

if [ $? -eq 0 ] && [ "$existing_count" != "count" ] && [ "$existing_count" -gt 0 ]; then
    echo "Warning: Found $existing_count at-bats already loaded for $month."
    read -p "Do you want to continue and potentially create duplicates? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborting."
        exit 0
    fi
fi

# Define file paths
RAW_FILE="/tmp/${year}-${month_num}_raw.csv"
CLEAN_FILE="/tmp/${year}-${month_num}_clean.csv"
JSON_FILE="/tmp/${year}-${month_num}.jsonl"

echo "Processing $month ($start_date to $end_date)..."

# Step 1: Download raw data
echo "[1/4] Downloading raw data..."
if ! "./GetData.sh" "$start_date" "$end_date"; then
    echo "Error: GetData.sh failed."
    exit 1
fi

# Move file to expected location if GetData.sh uses different naming
if [ ! -f "$RAW_FILE" ]; then
    GETDATA_FILE="/tmp/s${start_date}_e${end_date}_raw.csv"
    if [ -f "$GETDATA_FILE" ]; then
        mv "$GETDATA_FILE" "$RAW_FILE"
    else
        echo "Error: Raw data file not found."
        exit 1
    fi
fi

# Check if file has data (more than just header)
LINE_COUNT=$(wc -l < "$RAW_FILE" 2>/dev/null || echo "0")
if [ "$LINE_COUNT" -le 1 ]; then
    echo "No data found for $month (likely off-season)."
    rm -f "$RAW_FILE"
    exit 0
fi

# Step 2: Clean data
echo "[2/4] Cleaning data..."
if ! "./CleanData.sh" "$RAW_FILE" "$CLEAN_FILE"; then
    echo "Error: CleanData.sh failed."
    rm -f "$RAW_FILE"
    exit 1
fi

# Step 3: Format data
echo "[3/4] Formatting data to JSONL..."
if ! "./FormatData.sh" "$CLEAN_FILE" "$JSON_FILE"; then
    echo "Error: FormatData.sh failed."
    rm -f "$RAW_FILE" "$CLEAN_FILE"
    exit 1
fi

# Step 4: Upload to BigQuery
echo "[4/4] Uploading to BigQuery..."
if ! "./UploadJSONtoBQ.sh" "$data_set" "$table" "$JSON_FILE"; then
    echo "Error: UploadJSONtoBQ.sh failed."
    rm -f "$RAW_FILE" "$CLEAN_FILE" "$JSON_FILE"
    exit 1
fi

# Cleanup
echo "Cleaning up temporary files..."
rm -f "$RAW_FILE" "$CLEAN_FILE" "$JSON_FILE"

echo ""
echo "Successfully processed and uploaded data for $month to $data_set.$table"
exit 0
