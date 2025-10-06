# Database Documentation

## Overview

BigQuery is Google's fully managed, serverless data warehouse. It allows users to run SQL queries on large datasets quickly and cost-effectively using Google's cloud infrastructure. In this project, BigQuery serves as our central repository for storing and querying our data.

To use any of our BigQuery scripts you will need a Google Cloud account and you will need to have gcloud installed on your system. BiqQuery also has a CLI tool that comes with your gcloud installation and it also has a python client as well. 

### Helpful Links
* BigQuery Documentation: https://cloud.google.com/bigquery/docs
* BigQuery Python Client Documentation: https://cloud.google.com/python/docs/reference/bigquery/latest
* BigQuery CLI tool Documentation: https://cloud.google.com/bigquery/docs/reference/bq-cli-reference


## Google Cloud Setup Instructions

1. Go to https://cloud.google.com/ and press the `Start free` button
2. Sign in to a Google account and follow the setup steps
3. You might have to enter a credit card, but you shouldn't be charged as long as you don't enable billing beyond the free tier. TODO: test this
4. Follow these directions to install gcloud to your system: https://cloud.google.com/sdk/docs/install
5. After installation, authenticate with Google Cloud: `gcloud auth login`
6. Set the project: `gcloud config set project baseball-prediction-473623`
7. For Python scripts using the BigQuery client, run: `gcloud auth application-default login`

**Note:** I will need to grant you some permissions so you can use the project so send me(Jackson) a text when you have your account setup.

## Database Scripts Documentation

This document provides documentation for all scripts in the `scripts/` directory.

**Note:** Currently all the scripts use relative paths to call their helper scripts, so you'll need to be in the `/scripts` directory when using them.

| Name | Usage | Example | Description | Notes |
|------|-------|---------|-------------|-------|
| CheckGCloudCredintals.sh | `./CheckGCloudCredintals.sh` | `./CheckGCloudCredintals.sh` | Verifies gcloud is installed and configured with the correct project. | Checks for gcloud CLI installation, authentication, project configuration, and application default credentials. Exits with error if any check fails. |
| CheckIfBQDataSetExists.sh | `./CheckIfBQDataSetExists.sh [data set name]` | `./CheckIfBQDataSetExists.sh my_dataset` | Checks if a BigQuery dataset exists. | Outputs "Yes" if exists, "No" otherwise. Requires gcloud credentials. |
| CheckIfBQTableExists.sh | `./CheckIfBQTableExists.sh [data set name] [table name]` | `./CheckIfBQTableExists.sh my_dataset my_table` | Checks if a BigQuery table exists in the specified dataset. | Outputs "Yes" if exists, "No" otherwise. Requires gcloud credentials and dataset to exist. |
| CleanData.py | `python3 ./CleanData.py <raw data file>` | `python3 ./CleanData.py /tmp/s2025-10-09_e2025-10-09_raw.csv` | Cleans raw statcast data from pybaseball by converting non-numeric columns to ordinal values. | Processes CSV files, handles missing values, and saves cleaned data to /tmp with "_clean.csv" suffix. Uses multipledispatch for key handling. |
| CleanData.sh | `./CleanData.sh [path to raw data file]` | `./CleanData.sh s2025-10-09_e2025-10-09_raw.csv` | Cleans raw pybaseball statcast CSV data using CleanData.py. | Wrapper script that calls CleanData.py and places cleaned files in /tmp. Should be used with GetData.sh. |
| CreateBQDataset.sh | `./CreateBQDataset.sh [data set name]` | `./CreateBQDataset.sh my_dataset` | Creates a new BigQuery dataset. | Checks if dataset already exists before creating. Requires gcloud credentials. |
| CreateBQTable.sh | `./CreateBQTable.sh [data set name] [table name] [path to SQL file]` | `./CreateBQTable.sh my_dataset my_new_table ./table_ddl.sql` | Creates a new BigQuery table from a SQL DDL file. | Executes the DDL query to create the table. Requires dataset to exist and gcloud credentials. |
| GetData.py | `python3 ./GetData.py <start_date> <end_date> <file_path>` | `python3 ./GetData.py 2024-01-01 2024-01-31 /tmp/data.csv` | Pulls raw statcast data from pybaseball for a date range and saves to CSV. | Uses pybaseball's statcast function. Dates in YYYY-MM-DD format. |
| GetData.sh | `./GetData.sh [start date (YYYY-MM-DD)] [end date (YYYY-MM-DD)]` | `./GetData.sh 2024-01-01 2024-01-31` | Pulls raw statcast data from pybaseball for a date range and saves to /tmp CSV file. | Wrapper for GetData.py. Both dates inclusive. Validates date format. |
| UploadCSVtoBQ.sh | `./UploadCSVtoBQ.sh [data set name] [table name] [path to data file]` | `./UploadCSVtoBQ.sh my_dataset my_table /tmp/my_cleaned_data.csv` | Uploads CSV data to a BigQuery table. | Uses bq load command with CSV format options. Requires dataset and table to exist, and gcloud credentials. |

## Database Script TODOs
* remove relative paths from all scripts
* the CleanData.py script needs some work I just kind of hacked it together so its not that good atm
* add a -v option to all the helper scripts so the caller can tell it to skip verification
* need to write a script to run queries from SQL files
