#!/bin/bash
#  
# Purpose: Monitors BigQuery usage to ensure staying within free tier limits
# Note: Checks both storage and compute usage against Google Cloud free tier quotas.
#
##########
usage="./CheckDBUsage.sh [optional: --project-id your-project-id]"
example="./CheckDBUsage.sh --project-id my-baseball-analytics-project"
