#!/bin/bash
#  
# Purpose: Pulls raw baseball data for specified date range and saves to temporary CSV file
# Note: Wrapper for Python dataProcesser class. Creates temporary files in /tmp directory.
#
##########
usage="./GetData.sh [start_date] [end_date] [optional: --exclude-features feature1,feature2,feature3]"
example="./GetData.sh 2024-01-01 2024-01-31 --exclude-features weather"
