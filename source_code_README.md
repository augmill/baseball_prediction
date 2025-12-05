# Source Code Submission 

### Team Members:
* August
* Austin
* Jackson Cockrum
* Max Wool

### Files for submission

* embedding_clustering_script.py

Description: 

This script references the atbat_sent_features table we have residing in BigQuery in Google Cloud. In this table, we have sentence embeddings which define the game state of each at-bat as well as the actual corresponding event outcomes of each at-bat. This script clusters at-bat outcomes into a 2D space based on the generated embeddings, helping us draw insights on the accuracy of the embeddings in describing the at-bat event outcome.

* embedding_distance_script.py

Description:

After clustering has been performed using the previous script, this script checks the average distance between two clustered points with the same labeled event outcome vs the average distance between two points with random event outcomes. If clustering was successful, we would expect the average distance between points with same outcome to be significantly less than average distance between points with random event outcomes.
