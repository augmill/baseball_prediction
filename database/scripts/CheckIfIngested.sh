#!/bin/bash
#  
# Purpose: Checks if data for specified date range has already been ingested into the table
# Note: Queries BigQuery table to prevent duplicate data ingestion.
#
##########
usage="./CheckIfIngested.sh [start_date] [end_date] [bigquery_table_name]"
example="./CheckIfIngested.sh 2024-01-01 2024-01-31 baseball_games"
