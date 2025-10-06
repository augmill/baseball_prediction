#!/bin/bash
#  
# Purpose: Verifies gcloud is installed and configured with the correct project
#
# Author: Jackson Cockrum
##############################################################
usage="Usage: ./CheckGCloudCredintals.sh"
example="Example: ./CheckGCloudCredintals.sh"

# TODO: add -v opt to all scripts to skip verification
# TODO: add in actual project id 
EXPECTED_PROJECT="baseball-prediction-473623"

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

if [ $# -ne 0 ]; then
   echo "$usage"
   echo "$example"
   exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
   echo "Error: gcloud CLI is not installed or not in PATH."
   echo "Please install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
   exit 1
fi

# Check if gcloud is authenticated
auth_status=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [ -z "$auth_status" ]; then
   echo "Error: No active gcloud authentication found."
   echo "Please run: gcloud auth login"
   exit 1
fi

# Check if a project is configured
current_project=$(gcloud config get-value project 2>/dev/null)
if [ -z "$current_project" ] || [ "$current_project" = "(unset)" ]; then
   echo "Error: No gcloud project is configured."
   echo "Please run: gcloud config set project YOUR_PROJECT_ID"
   exit 1
fi

# Check if the project matches the expected project (if not placeholder)
if [ "$EXPECTED_PROJECT" != "baseball-prediction-473623" ]; then
   if [ "$current_project" != "$EXPECTED_PROJECT" ]; then
      echo "Error: gcloud is configured for project '$current_project' but expected '$EXPECTED_PROJECT'."
      echo "Please run: gcloud config set project $EXPECTED_PROJECT"
      exit 1
   fi
fi

# Check if Application Default Credentials are set (for BigQuery access)
if ! gcloud auth application-default print-access-token &> /dev/null; then
   echo "Warning: Application Default Credentials not found."
   echo "You may need to run: gcloud auth application-default login"
   echo "Continuing with user credentials..."
fi

echo "gcloud credentials verified successfully."
echo "Active account: $auth_status"
echo "Current project: $current_project"
exit 0