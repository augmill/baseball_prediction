#!/bin/bash
#  
# Purpose: Creates BigQuery table from SQL schema definition if it doesn't exist
# Note: Reads schema from SQL file and creates table only if it doesn't already exist.
#
##########
usage="./CreateTable.sh [sql_schema_file_path] [bigquery_table_name]"
example="./CreateTable.sh ../schemas/baseball_games_schema.sql baseball_games"
