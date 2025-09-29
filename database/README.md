This file is currently acting as a TODO and planning page for the database setup, but later it will contain the instrcuctions for ingesting and querying data to/from the database

## TODOs
* Setup google cloud creditenals and project for the DB (plus requisite scripts)
* Define a solid schema for the table (this schema could be subject to change)
* write out the basic skeletons for all the scripts
* implement and test the scripts
* Do a full run through of ingesting one season of data using the scripts 
* write up instructions on how to use the scripts

## Baic "ETL" Pipeline plan
while this wont be an actual "pipeline" we will have a collection of scripts that facilitate data ingest and cleaning

###  Pipeline Scripts
* ETLPipeline.sh
    * accepts two params: start date (inclusive) and end date (exclusive)
    * will have an option where the user can provide a csv list of features they would like to exclude
* GetData.sh
    * accepts the same params/opts as ETLPipline.sh
    * pulls raw data down into a csv file (probably in the /tmp directory)
    * Once data is pulled will make a call to the Clean data script
    * this will probably be a wrapper for a python script
* CleanData.sh
    * accepts the location of a raw data file as the only param
    * will be a wrapper for a python script so we can leverage the code already written
    * Puts the clean data into a new csv file (maybe optionally have it delete old data)
* IngestData.sh
    * accepts the location of a cleaned data file as input and the BigQuery table name
    * sends the csv file to the opensearch database 
    * maybe optionally remove cleaned data file once 

### Utility Scripts ###
* VerifyData.sh
    - takes data file and table name as input
    - ensure all rows/columns match schema of table
    - maybe optionally remove bad rows
* CheckIfIngested.sh
    - checks if data for a certain time range has already been ingested
    - either need to query the table or maintain a list of data thats been ingested
* QueryTable.sh
    - accepts table name and path to SQL file as params
    - runs the query in the SQL file against the database
* VerifyLogin.sh
    - just verifies if your google cloud credintals/config are valid
* SetupEnironment.sh
    - installs all the dependinces needed for google cloud
* CheckDBUsage.sh
    - script to check if we are within the Google Big Query free tier limits for both the storage and compute layers
* CreateTable.sh
    - given a SQL file with a schema defintion and a table name param
    - if the table DNE create it