# Source Code Submission 

### Team Members:
* August
* Austin
* Jackson Cockrum
* Max Wool


### Files for submission

* atbat_facts (BigQuery Table)

Description:

The core table storing comprehensive at-bat data from Statcast in BigQuery. Uses a denormalized structure where each row represents one plate appearance with game metadata, batter/pitcher information, at-bat outcome (events), and a nested ARRAY<STRUCT> containing the complete pitch sequence. Each pitch struct includes detailed tracking data: position metrics (release point, plate location, zone), movement characteristics (velocity, acceleration, spin), game state (count, outs, runners on base, score), and hit information when applicable (exit velocity, launch angle, hit distance). The table is partitioned by game_date and clustered by batter and game_id for efficient querying. This schema design enables analysis of complete at-bat sequences while maintaining query performance through BigQuery's nested/repeated field support.

* IngestAtBats.sh

Description:

Top-level orchestrator script for ingesting Statcast at-bat data into BigQuery. This script coordinates the full ingestion process by breaking date ranges into monthly chunks and processing them in parallel. It validates GCloud credentials, checks for existing data to avoid ingesting duplicate records, and manages parallel execution of monthly data ingestion jobs. 

* ProcessMonth.sh

Description:

Worker script that handles the complete data pipeline for ingesting one month of Statcast data into BigQuery. Orchestrates a four-step process: (1) downloads raw pitch-by-pitch data from Statcast for the specified month using GetData.sh, (2) cleans and validates the data using CleanData.sh/CleanData.py, (3) formats cleaned CSV data into nested JSON objects with pitches grouped by at-bat using FormatData.sh/FormatData.py, and (4) uploads the formatted data to BigQuery using UploadJSONtoBQ.sh. 

* CleanData.py

Description:

Python script that performs data cleaning and validation on raw Statcast CSV files. Removes unused columns, retains only fields required by the atbat_facts table schema, normalizes missing values, ensures numeric fields are parseable, and enforces deterministic column ordering. Drops rows with missing critical fields (game_id, batter, pitcher, etc.) and renames fields for consistency with the BigQuery schema.

* FormatData.py

Description:

Python script that transforms cleaned per-pitch CSV data into nested JSONL format suitable for BigQuery ingestion. Groups individual pitch records by at-bat (using game_id and at_bat_number), creating structured objects with at-bat-level metadata and a nested array of pitches. Implements data quality filters including dropping at-bats with multiple pitchers, validating required fields, and skipping pitches with missing NOT NULL values. The output JSONL format matches the atbat_facts table schema with properly nested pitch arrays.

* embedding_clustering_script.py

Description: 

This script references the atbat_sent_features table we have residing in BigQuery in Google Cloud. In this table, we have sentence embeddings which define the game state of each at-bat as well as the actual corresponding event outcomes of each at-bat. This script clusters at-bat outcomes into a 2D space based on the generated embeddings, helping us draw insights on the accuracy of the embeddings in describing the at-bat event outcomes.

* embedding_distance_script.py

Description:

After clustering has been performed using the previous script, this script checks the average distance between two clustered points with the same labeled event outcome vs the average distance between two points with random event outcomes. If clustering was successful, we would expect the average distance between points with same outcome to be significantly less than average distance between points with random event outcomes.
