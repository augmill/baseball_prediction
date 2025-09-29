#!/bin/bash
#  
# Purpose: Ingests cleaned CSV data into BigQuery table
# Note: Requires valid Google Cloud credentials. Optionally removes cleaned file after ingestion.
#
##########
usage="./IngestData.sh [cleaned_data_file_path] [bigquery_table_name] [optional: --delete-clean]"
example="./IngestData.sh /tmp/baseball_clean_2024-01-01_2024-01-31.csv baseball_games --delete-clean"
