#!/bin/bash
#  
# Purpose: Master ETL script that orchestrates data extraction, cleaning, and ingestion for a date range
# Note: Calls GetData.sh -> CleanData.sh -> IngestData.sh in sequence. Supports feature exclusion via CSV list.
#
##########
usage="./ETLPipeline.sh [start_date] [end_date] [optional: --exclude-features feature1,feature2,feature3]"
example="./ETLPipeline.sh 2024-01-01 2024-01-31 --exclude-features weather,attendance"
