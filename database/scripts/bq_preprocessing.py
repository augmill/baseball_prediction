import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.feature_extraction import FeatureHasher
from google.cloud import bigquery
import sys
from datetime import datetime
from typing import Optional

class BigQueryPreprocessor:
    def __init__(self, project_id: str = "baseball-prediction-473623", dataset_id: str = "statcast_data"):
        """
        Initialize BigQuery client and set project/dataset information
        
        :param str project_id: GCP project ID
        :param str dataset_id: BigQuery dataset ID
        """
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.source_table = "atbat_facts"
        self.target_table = "atbat_features"

        self.key = {}
        
    def extract_data_from_bq(self, start_date: str, end_date: str, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Extract data from the atbat_facts table in BigQuery
        
        :param str start_date: Start date filter (YYYY-MM-DD format) - REQUIRED
        :param str end_date: End date filter (YYYY-MM-DD format) - REQUIRED
        :param int limit: Optional limit on number of rows to process
        :returns pd.DataFrame: Raw data from BigQuery
        """
        print("Extracting data from BigQuery atbat_facts table...")
        
        # Build the query to flatten the pitches array and get the data in the format expected by preprocessing
        query = f"""
        SELECT 
            -- Game Info
            game_id,
            game_date,
            game_type,
            home_team,
            away_team,
            
            -- At-bat Info
            at_bat_number,
            inning,
            inning_topbot,
            events,
            
            -- Batter/Pitcher Info
            batter,
            stand,
            pitcher,
            p_throws,
            
            -- Pitch Data (flattened from array)
            pitch.pitch_type,
            pitch.pitch_name,
            pitch.pitch_number,
            pitch.description,
            pitch.type,
            pitch.sz_top,
            pitch.sz_bot,
            pitch.des,
            
            -- Position Info
            pitch.release_pos_x,
            pitch.release_pos_y,
            pitch.release_pos_z,
            pitch.plate_x,
            pitch.plate_z,
            pitch.zone,
            
            -- Movement Info
            pitch.release_speed,
            pitch.effective_speed,
            pitch.vx0,
            pitch.vy0,
            pitch.vz0,
            pitch.ax,
            pitch.ay,
            pitch.az,
            pitch.pfx_x,
            pitch.pfx_z,
            pitch.release_extension,
            pitch.release_spin,
            pitch.spin_axis,
            
            -- Game State
            pitch.balls,
            pitch.strikes,
            pitch.outs_when_up,
            pitch.on_3b,
            pitch.on_2b,
            pitch.on_1b,
            pitch.home_score,
            pitch.away_score,
            pitch.bat_score,
            pitch.fld_score,
            pitch.post_home_score,
            pitch.post_away_score,
            pitch.post_bat_score,
            pitch.if_fielding_alignment,
            pitch.of_fielding_alignment,
            
            -- Hit Info
            pitch.hit_location,
            pitch.bb_type,
            pitch.hc_x,
            pitch.hc_y,
            pitch.hit_distance,
            pitch.launch_speed,
            pitch.launch_angle,
            pitch.launch_speed_angle,
            
            -- Stats
            pitch.woba_value,
            pitch.woba_denom,
            pitch.babip_value,
            pitch.iso_value,
            pitch.estimated_ba_using_speedangle,
            pitch.estimated_woba_using_speedangle,
            pitch.delta_home_win_exp,
            pitch.delta_run_exp
            
        FROM `{self.project_id}.{self.dataset_id}.{self.source_table}`,
        UNNEST(pitches) as pitch
        WHERE game_date >= '{start_date}' 
          AND game_date <= '{end_date}'
        """
            
        # Add limit if provided
        if limit:
            query += f" LIMIT {limit}"
            
        print(f"Executing query: {query[:200]}...")
        
        # Execute query and return as DataFrame
        df = self.client.query(query).to_dataframe()
        print(f"Extracted {len(df)} rows from BigQuery")
        
        return df

    def datetime(self, column: pd.Series) -> pd.Series: 
        """
        Converts datetime data to usable type for machine learning
        
        :param pd.Series column: Column to convert
        :returns pd.Series: Converted column
        """
        print(f"Converting {' '.join(column.name.split(sep='_'))} to ints...")
        try:
            # Convert date objects to string first, then remove dashes
            converted = column.dt.strftime('%Y%m%d').astype(int)
            return converted
        except Exception as e:
            print(f"Error converting datetime: {e}")
            return column

    def hash_features(self, column: pd.Series) -> list:
        """
        Converts nominal data to a hashed feature vector using sklearn.feature_extraction.FeatureHasher
        
        :param pd.Series column: Column to convert
        :returns list: List of hashed feature vectors
        """
        print(f"Converting {' '.join(column.name.split(sep='_'))} to hashed features...")
        self.key[f"{column.name}_hash"] = []
        self.key[f"{column.name}_label"] = []
        column = column.astype(str)
        num_feats = len(column.unique())
        hash_feats = num_feats if num_feats % 2 == 0 else num_feats +1 
        hasher = FeatureHasher(n_features=hash_feats, input_type="dict")
        data = [{column.name: item} for item in column]
        feats = [[int(val) for val in list(item)] for item in hasher.fit_transform(data).toarray()]

        i = 0
        while len(self.key[f"{column.name}_label"]) < num_feats:
            if data[i][column.name] not in self.key[f"{column.name}_label"]:
                self.key[f"{column.name}_label"].append(data[i][column.name])
                self.key[f"{column.name}_hash"].append(feats[i])
            i += 1

        return feats

    def binarize(self, column: pd.Series) -> pd.Series:
        """
        Binarizes nominal data that has only two options e.g. right and left
        
        :param pd.Series column: Column to convert
        :returns pd.Series: Converted column
        """
        print(f"Binarizing {' '.join(column.name.split(sep='_'))}...")
        vars = column.astype("category").cat
        col = vars.codes
        self.key[column.name] = vars.categories.tolist()
        return col

    def is_player(self, column: pd.Series) -> pd.Series:
        """
        Makes each value just a bool i.e. 0 or 1 as to whether or not a player is on that base
        
        :param pd.Series column: The column to convert
        :returns pd.Series: Converted column
        """
        print(f"Converting {' '.join(column.name.split(sep='_'))} to bools...")
        return column.notna().astype(int)
    
    def expand(self, df: pd.DataFrame, cols: list) -> pd.DataFrame: 
        """
        Expands the values in the columns that hash_features altered into their own columns
        
        :param pd.DataFrame df: Dataframe to change
        :param list cols: Columns to expand
        :returns pd.DataFrame: Updated dataframe
        """
        print("Expanding hashed feature columns...")
        for col in cols:
            vals = [str(item) for item in list(df[col])]
            vals_out = []
            for item in vals:
                vals_out.append([int(val.strip()) for val in str(item).replace("[", "").replace("]", "").split(",")])
            df[col] = vals_out
            inter = df[col].apply(pd.Series)
            inter.columns = [f'{col}{i}' for i in range(inter.shape[1])]
            df = pd.concat([df.iloc[:, :df.columns.get_loc(col)], inter, df.iloc[:, df.columns.get_loc(col)+1:]], axis=1)
        return df
    
    def events_process(self, column: pd.Series) -> pd.Series:
        name = column.name
        print(f"Converting {name} column")
        self.key[f"{name}_reg"] = column.astype("category").cat.categories.tolist()
        key = ["other", "single", "double", "triple", "homerun", "strikeout", "out", "multi_out", "walk", "awarded_first", "field_play"]
        self.key[f"{name}_shift"] = key
        column = column.astype("category").cat.codes
        col = []
        for label in column:
            # label = int(label)
            if label in [4, 6, 7, 12, 14]: # out
                col.append(key.index("out"))
            elif label == 16: # single
                col.append(key.index("single"))
            elif label == 1: # double 
                col.append(key.index("double"))
            elif label == 10: # homerun 
                col.append(key.index("homerun"))
            elif label in [2, 8, 13, 15, 18, 20]: # multi out
                col.append(key.index("multi_out"))
            elif label in [3, 5]: # field play 
                col.append(key.index("field_play"))
            elif label == 19: # triiple
                col.append(key.index("triple"))
            elif label == 17:
                col.append(key.index("strikeout"))
            elif label in [0, 9]: # awarded first
                col.append(key.index("awarded_first"))
            elif label in [11, 22]: # walk
                col.append(key.index("walk"))
            else: # other 
                col.append(key.index("other"))
        return col


    def process_cols(self, df: pd.DataFrame, cols: list, func) -> pd.DataFrame: 
        """
        Applies the given function to each of the columns
        
        :param pd.DataFrame df: Dataframe to change
        :param list cols: Columns to altered 
        :param function func: Function to alter cols (can only take pd.Series)
        :returns pd.DataFrame: Updated dataframe
        """
        for col in cols:
            if col in df.columns:
                df[col] = func(df[col])
            else:
                print(f"Warning: Column {col} not found in dataframe")
        return df
    
    def push_key(self, write_disposition: str = "WRITE_TRUNCATE") -> None:
        """
        Pushes generated key to a table in bigquery inspired by Jackson Cockrum's load_to_bq
        
        :param str write_disposition: How to handle existing data (WRITE_TRUNCATE, WRITE_APPEND, WRITE_EMPTY) 
        """
        self.key = {key : pd.Series(item) for key, item in self.key.items()}
        try:
            df = pd.DataFrame(self.key)
            print(df)
        except Exception as e:
            print(e)
            sys.exit(1)

        print(f"Loading keys to BigQuery table feat_key_table...")

        table_id = f"{self.project_id}.{self.dataset_id}.{"feat_key_table"}"

        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
            autodetect=False,  # We'll use the schema from our DDL
        )
        
        # Load the dataframe
        job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result() 

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all preprocessing transformations to the dataframe
        
        :param pd.DataFrame df: Raw dataframe from BigQuery
        :returns pd.DataFrame: Processed dataframe ready for ML
        """
        print("Starting data preprocessing...")
        
        # Define column categories for processing
        nominals = ["game_type", "bb_type", "pitch_name", "if_fielding_alignment", "of_fielding_alignment"]
        binaries = ["stand", "p_throws", "inning_topbot"]
        players = ["on_3b", "on_2b", "on_1b"]
        remove = ["Unnamed: 0", "spin_dir", "spin_rate_deprecated", "break_angle_deprecated", "break_length_deprecated", 
          "tfs_deprecated", "tfs_zulu_deprecated", "umpire",
          "pitch_type", "player_name", "sv_id", "hit_distance_sc", 
          "game_pk", "fielder_2", "fielder_3", "fielder_4", "fielder_5", "fielder_6", "fielder_7", "fielder_8", 
          "fielder_9",  "estimated_ba_using_speedangle", "estimated_woba_using_speedangle", "woba_value", 
          "babip_value", "launch_speed_angle", "delta_home_win_exp", "delta_run_exp", "bat_speed", "swing_length",
          "estimated_slg_using_speedangle", "delta_pitcher_run_exp", "home_win_exp", "bat_win_exp", 
          "pitcher_days_until_next_game", "batter_days_until_next_game", "api_break_z_with_gravity", "api_break_x_arm",
          "api_break_x_batter_in", "arm_angle", "attack_angle", "attack_direction", "swing_path_tilt", 
          "intercept_ball_minus_batter_pos_x_inches", "intercept_ball_minus_batter_pos_y_inches", "launch_speed",
          "launch_angle", "hc_x", "hc_y", "woba_denom", "hit_location", "hyper_speed", "type", "hit_distance", 
          "post_home_score", "post_away_score", "post_bat_score", "description", "iso_value"] 

        # Apply transformations
        df["game_date_int"] = self.datetime(df["game_date"])
        # Keep original game_date for partitioning
        df = self.process_cols(df, nominals, self.hash_features)
        df = self.process_cols(df, binaries, self.binarize)
        df = self.process_cols(df, players, self.is_player)
        df = self.process_cols(df, ["events"], self.events_process)
        self.push_key(write_disposition="WRITE_TRUNCATE")
        df = self.expand(df, nominals)
        
        # Remove unwanted columns (only if they exist)
        existing_remove_cols = [col for col in remove if col in df.columns]
        if existing_remove_cols:
            df.drop(columns=existing_remove_cols, inplace=True)
            print(f"Removed {len(existing_remove_cols)} unwanted columns")

        # Clean data
        df.dropna(subset=['events'], inplace=True)
        df.dropna(axis=0, inplace=True)
        
        print(f"Preprocessing complete. Final dataset shape: {df.shape}")
        return df

    def load_to_bq(self, df: pd.DataFrame, write_disposition: str = "WRITE_TRUNCATE") -> None:
        """
        Load processed data to BigQuery atbat_features table
        
        :param pd.DataFrame df: Processed dataframe to load
        :param str write_disposition: How to handle existing data (WRITE_TRUNCATE, WRITE_APPEND, WRITE_EMPTY)
        """
        print(f"Loading {len(df)} rows to BigQuery table {self.target_table}...")
        
        # Add empty embedding_vector column (will be populated later by ML pipeline)
        df['embedding_vector'] = None
        
        # Define the destination table
        table_id = f"{self.project_id}.{self.dataset_id}.{self.target_table}"
        
        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
            autodetect=False,  # We'll use the schema from our DDL
        )
        
        # Load the dataframe
        job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for the job to complete
        
        print(f"Successfully loaded data to {table_id}")

def validate_date_format(date_string: str) -> bool:
    """
    Validate that date string is in YYYY-MM-DD format
    
    :param str date_string: Date string to validate
    :returns bool: True if valid format, False otherwise
    """
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def main():
    """
    Main execution function
    Usage: python bq_preprocessing.py START_DATE END_DATE
    Example: python bq_preprocessing.py 2023-04-01 2023-10-31
    """
    # Check for correct number of arguments
    if len(sys.argv) != 3:
        print("Usage: python bq_preprocessing.py START_DATE END_DATE")
        print("Example: python bq_preprocessing.py 2023-04-01 2023-10-31")
        print("Dates must be in YYYY-MM-DD format")
        sys.exit(1)
    
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    
    try:
        # Validate date formats
        if not validate_date_format(start_date):
            print(f"Error: Invalid start date format: {start_date}. Use YYYY-MM-DD format.")
            sys.exit(1)
            
        if not validate_date_format(end_date):
            print(f"Error: Invalid end date format: {end_date}. Use YYYY-MM-DD format.")
            sys.exit(1)
            
        # Validate date range
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start_dt > end_dt:
            print("Error: Start date must be before or equal to end date")
            sys.exit(1)
            
        print(f"Processing data from {start_date} to {end_date}")
            
        # Initialize preprocessor with hardcoded project/dataset
        preprocessor = BigQueryPreprocessor(
            project_id="baseball-prediction-473623", 
            dataset_id="statcast_data"
        )
        
        # Extract data from BigQuery with required date range
        df = preprocessor.extract_data_from_bq(
            start_date=start_date,
            end_date=end_date
        )
        
        if len(df) == 0:
            print("Warning: No data found for the specified date range")
            sys.exit(0)
        
        # Process the data
        processed_df = preprocessor.process_data(df)

        # Load to BigQuery (always truncate/replace)
        preprocessor.load_to_bq(processed_df, write_disposition="WRITE_TRUNCATE")
        
        print(f"ETL pipeline completed successfully! Processed {len(processed_df)} rows.")
        
    except KeyboardInterrupt:
        print("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error in ETL pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()