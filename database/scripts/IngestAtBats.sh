#!/bin/bash
#  
# Purpose: Top-level orchestrator for ingesting Statcast at-bat data into BigQuery.
#
# Coordinates the full ingestion process by breaking date ranges into monthly chunks
# and processing them in parallel using helper scripts.
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./IngestAtBats.sh [-d] <project.dataset.table> <start date (MM-YYYY)> <end date (MM-YYYY)> [max parallel degree]"
example="Example: ./IngestAtBats.sh baseball-prediction-473623.statcast_data.atbat_facts 04-2024 06-2024 6"

# Parse dry-run flag
DRY_RUN=false
while getopts ":hd" opt; do
   case $opt in
      h) 
        echo "$usage"
        echo "$example"
        exit 0
        ;;
      d)
        DRY_RUN=true
        ;;
     \?)
        echo "Invalid option: -$OPTARG"
        echo "$usage"
        exit 1
        ;;
   esac
done
shift $((OPTIND-1))

# Verify authentication
auth_check=$("./CheckGCloudCredintals.sh")
if [ $? -ne 0 ]; then
   echo "$auth_check"
   exit 1
fi

# Validate arguments
if [ $# -lt 3 ] || [ $# -gt 4 ]; then
   echo "$usage"
   echo "$example"
   exit 1
fi

# Parse arguments
full_table="$1"
start_month="$2"
end_month="$3"
max_parallel="${4:-4}"  # Default to 4 parallel processes

# Parse project.dataset.table
IFS="." read -ra parts <<< "$full_table"
if [ ${#parts[@]} -eq 3 ]; then
    project_id="${parts[0]}"
    data_set="${parts[1]}"
    table="${parts[2]}"
elif [ ${#parts[@]} -eq 2 ]; then
    project_id=$(gcloud config get-value project 2>/dev/null)
    data_set="${parts[0]}"
    table="${parts[1]}"
else
    echo "Error: Invalid table format. Expected [project.]dataset.table"
    exit 1
fi

# Validate date formats
if ! [[ "$start_month" =~ ^[0-9]{2}-[0-9]{4}$ ]]; then
    echo "Error: Start date format is invalid. Expected MM-YYYY."
    exit 1
fi

if ! [[ "$end_month" =~ ^[0-9]{2}-[0-9]{4}$ ]]; then
    echo "Error: End date format is invalid. Expected MM-YYYY."
    exit 1
fi

# Validate max parallel degree
if ! [[ "$max_parallel" =~ ^[0-9]+$ ]] || [ "$max_parallel" -lt 1 ]; then
    echo "Error: Max parallel degree must be a positive integer."
    exit 1
fi

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

# Convert MM-YYYY to YYYY-MM for easier manipulation
start_year="${start_month:3:4}"
start_mon="${start_month:0:2}"
end_year="${end_month:3:4}"
end_mon="${end_month:0:2}"

# Generate list of months to process
months_to_process=()
current_year=$start_year
current_mon=$start_mon

while [ "$current_year" -lt "$end_year" ] || { [ "$current_year" -eq "$end_year" ] && [ "$current_mon" -le "$end_mon" ]; }; do
    months_to_process+=("$current_year-$current_mon")
    
    # Increment month
    current_mon=$((10#$current_mon + 1))
    if [ $current_mon -gt 12 ]; then
        current_mon=1
        current_year=$((current_year + 1))
    fi
    current_mon=$(printf "%02d" $current_mon)
done

echo "=========================================="
echo "  At-Bat Data Ingestion"
echo "=========================================="
echo "Target: $data_set.$table"
echo "Date Range: $start_month to $end_month"
echo "Months to process: ${#months_to_process[@]}"
echo "Max parallel degree: $max_parallel"
if [ "$DRY_RUN" = true ]; then
    echo "MODE: DRY RUN (no data will be ingested)"
fi
echo ""

# Check which months already have data
months_to_ingest=()
months_to_skip=()

echo "Checking existing data in BigQuery..."
for month in "${months_to_process[@]}"; do
    year="${month:0:4}"
    mon="${month:5:2}"
    
    # Determine last day of month
    case "$mon" in
        01|03|05|07|08|10|12) last_day="31" ;;
        04|06|09|11) last_day="30" ;;
        02) 
            if [ $((year % 4)) -eq 0 ] && { [ $((year % 100)) -ne 0 ] || [ $((year % 400)) -eq 0 ]; }; then
                last_day="29"
            else
                last_day="28"
            fi
            ;;
    esac
    
    start_date="${year}-${mon}-01"
    end_date="${year}-${mon}-${last_day}"
    
    # Query BigQuery to check if data exists
    existing_count=$(bq query --use_legacy_sql=false --format=csv --project_id="$project_id" \
        "SELECT COUNT(*) as count FROM \`${project_id}.${data_set}.${table}\` 
         WHERE game_date >= '$start_date' AND game_date <= '$end_date'" 2>/dev/null | tail -n 1)
    
    if [ $? -eq 0 ] && [ "$existing_count" != "count" ] && [ "$existing_count" -gt 0 ] 2>/dev/null; then
        echo "  $month: SKIP (found $existing_count existing at-bats)"
        months_to_skip+=("$month")
    else
        echo "  $month: INGEST"
        months_to_ingest+=("$month")
    fi
done

echo ""
echo "Summary:"
echo "  Months to ingest: ${#months_to_ingest[@]}"
echo "  Months to skip: ${#months_to_skip[@]}"
echo ""

# Exit if dry run
if [ "$DRY_RUN" = true ]; then
    echo "Dry run complete. No data was ingested."
    exit 0
fi

# Exit if nothing to ingest
if [ ${#months_to_ingest[@]} -eq 0 ]; then
    echo "No months to ingest. All data already exists."
    exit 0
fi

# Create temporary directory for logs
LOG_DIR="/tmp/ingest_logs_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo "Starting parallel ingestion (max $max_parallel concurrent processes)..."
echo "Logs will be written to: $LOG_DIR"
echo ""

# Function to process a single month (will be called by xargs)
process_month() {
    local month="$1"
    local dataset_table="$2"
    local log_dir="$3"
    local script_dir="$4"
    
    log_file="${log_dir}/${month}.log"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting $month" > "$log_file"
    
    cd "$script_dir" || exit 1
    
    if ./ProcessMonth.sh "$dataset_table" "$month" >> "$log_file" 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $month" >> "$log_file"
        echo "✓ $month"
        return 0
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] FAILED: $month" >> "$log_file"
        echo "✗ $month"
        return 1
    fi
}

export -f process_month

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Process months in parallel using xargs
printf "%s\n" "${months_to_ingest[@]}" | \
    xargs -P "$max_parallel" -I {} bash -c "process_month '{}' '${data_set}.${table}' '$LOG_DIR' '$SCRIPT_DIR'"

XARGS_EXIT=$?

echo ""
echo "=========================================="
echo "  Ingestion Complete"
echo "=========================================="

# Count successes and failures
success_count=0
failure_count=0

for month in "${months_to_ingest[@]}"; do
    if grep -q "SUCCESS: $month" "${LOG_DIR}/${month}.log" 2>/dev/null; then
        success_count=$((success_count + 1))
    else
        failure_count=$((failure_count + 1))
    fi
done

echo "Results:"
echo "  Successfully ingested: $success_count months"
echo "  Failed: $failure_count months"
echo "  Skipped (already exists): ${#months_to_skip[@]} months"
echo ""

if [ $failure_count -gt 0 ]; then
    echo "Failed months:"
    for month in "${months_to_ingest[@]}"; do
        if ! grep -q "SUCCESS: $month" "${LOG_DIR}/${month}.log" 2>/dev/null; then
            echo "  - $month (see ${LOG_DIR}/${month}.log)"
        fi
    done
    echo ""
fi

echo "Logs saved to: $LOG_DIR"
echo ""

if [ $failure_count -gt 0 ]; then
    exit 1
else
    exit 0
fi
