#!/bin/bash
#  
# Purpose: Executes SQL query from file against specified BigQuery table
# Note: Requires valid Google Cloud credentials and properly formatted SQL file.
#
##########
usage="./QueryTable.sh [bigquery_table_name] [sql_file_path]"
example="./QueryTable.sh baseball_games ../queries/get_team_stats.sql"
