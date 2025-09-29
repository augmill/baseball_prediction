#!/bin/bash
#  
# Purpose: Validates data file against BigQuery table schema and optionally removes bad rows
# Note: Checks row/column compatibility before ingestion to prevent BigQuery errors.
#
##########
usage="./VerifyData.sh [data_file_path] [bigquery_table_name] [optional: --remove-bad-rows]"
example="./VerifyData.sh /tmp/baseball_clean_2024-01-01.csv baseball_games --remove-bad-rows"
