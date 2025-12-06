from google.cloud import bigquery 
import pandas as pd 
import os 
# "/Users/augustmilliken/.config/gcloud/application_default_credentials.json"
# https://stackoverflow.com/questions/45003833/how-to-run-a-bigquery-query-in-python
# "../../../.config/gcloud/application_default_credentials.json"

def get_data(start_date: str) -> pd.DataFrame:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/augustmilliken/.config/gcloud/application_default_credentials.json"

    client = bigquery.Client(project='baseball-prediction-473623')
    sql_query = f"""
        SELECT 
            *
        FROM
            statcast_data.atbat_features
        WHERE
            game_date >= "{start_date}";
    """

    try: 
        return client.query(sql_query).to_dataframe()

    except Exception as e: 
        print(f"An error occurred: {e}")