import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.feature_extraction import FeatureHasher

def datetime(column: pd.Series) -> pd.Series: 
    """
    Converts ```datetime``` data to usable type for machine learning

    :param ```pd.Series``` column: Column to convert

    :returns ```pd.Series```: Converted column
    """
    print(f"Converting {' '.join(column.name.split(sep='_'))} to ints...")
    try:
        for i, value in enumerate(tqdm(column.values, desc=f"Processing {column.name}")):
            column[i] = value.replace("-", "")
        return column
    except Exception as e:
        print(e) 
        return column
    

def hash_features(column: pd.Series) -> pd.DataFrame:
    """
    Converts nominal data to a hashed feeature vector using ```sklearn.feature_extraction.FeatureHasher```

    :param ```pd.Series``` column: Column to convert

    :returns ```pd.Series```: Converted column
    """
    print(f"Converting {' '.join(column.name.split(sep='_'))} to hashed features...")
    column = column.astype(str)
    hasher = FeatureHasher(n_features=len(column.unique()), input_type="dict") #len(df[col].unique())
    data = [{column.name:item} for item in column]
    return [[int(val) for val in list(item)] for item in hasher.fit_transform(data).toarray()]


def binarize(column: pd.Series) -> pd.Series:
    """
    Binarizes nominal data that has only two options e.g. right and left

    :param ```pd.Series``` column: Column to convert

    :returns ```pd.Series```: Converted column
    """
    print(f"Binarizing {' '.join(column.name.split(sep='_'))}...")
    return column.astype("category").cat.codes

def is_player(column: pd.Series):
    """
    Makes each value just a bool i.e. 0 or 1 as to whether or not a player is on that base

    :param ```pd.Series``` column: The column to convert

    :returns ```pd.Series```: Converted column
    """
    print(f"Converting {' '.join(column.name.split(sep='_'))} to bools...")
    for item in column: 
        if not pd.isna(item): return 1 
        else: return 0

def expand(df: pd.DataFrame, cols: list) -> pd.DataFrame: 
    """
    Expands the values in the columns that ```hash_features``` altered into their own columns

    :param ```pd.DataFrame``` df: Dataframe to change
    :param list cols: Columns to expand

    :returns ```pd.DataFrame```: Updated dataframe
    """
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

def process_cols(df: pd.DataFrame, cols: list, func) -> pd.DataFrame: 
    """
    Applies the given function to each of the columns

    :param ```pd.DataFrame``` df: Dataframe to change
    :param list cols: Columns to altered 
    :param function func: Function to alter ```cols``` (can only take ```pd.Series```)

    :returns ```pd.DataFrame```: Updated dataframe
    """
    for col in cols:
        df[col] = func(df[col])
    return df

# usage example 
nominals = ["game_type", "bb_type", "pitch_name", "type", "if_fielding_alignment", "of_fielding_alignment"]
binaries = ["stand", "p_throws", "inning_topbot", "events"] #events has more than 2 but we want similar functionality to get class labels
players = ["on_3b", "on_2b", "on_1b"]
remove = ["Unnamed: 0", "spin_dir", "spin_rate_deprecated", "break_angle_deprecated", "break_length_deprecated", 
          "tfs_deprecated", "tfs_zulu_deprecated", "umpire",
          "pitch_type", "home_team", "away_team", "sv_id", "hit_distance_sc", 
          "game_pk", "fielder_2", "fielder_3", "fielder_4", "fielder_5", "fielder_6", "fielder_7", "fielder_8", 
          "fielder_9",  "estimated_ba_using_speedangle", "estimated_woba_using_speedangle", "woba_value", 
          "babip_value", "launch_speed_angle", "delta_home_win_exp", "delta_run_exp", "bat_speed", "swing_length",
          "estimated_slg_using_speedangle", "delta_pitcher_run_exp", "home_win_exp", "bat_win_exp", 
          "pitcher_days_until_next_game", "batter_days_until_next_game", "api_break_z_with_gravity", "api_break_x_arm",
          "api_break_x_batter_in", "arm_angle", "attack_angle", "attack_direction", "swing_path_tilt", 
          "intercept_ball_minus_batter_pos_x_inches", "intercept_ball_minus_batter_pos_y_inches", "launch_speed",
          "launch_angle", "hc_x", "hc_y", "woba_denom", "hit_location", "hyper_speed",
          "description"]

df = pd.read_csv("../data/raw_data.csv")
df["game_date"] = datetime(df["game_date"])
df = process_cols(df, nominals, hash_features)
df = process_cols(df, binaries, binarize)
df = process_cols(df, players, is_player)
df = expand(df, nominals)
df.drop(columns=remove, inplace=True)

# NOTE: 
"""
running up to here will make a dataframe that should have most of the data that is relevent if reading in straight for statcast

these next couple were useful for me to make sure everything had a value and I was only looking at at-bats but if there is a better way that is easier 
for you to do these they may be unhelpful 
""" 
df.dropna(subset=['events'], inplace=True)
df.dropna(axis=0, inplace=True)


# NOTE: if you want to export as a csv but I imagine this is unhelpful for you 
# df.to_csv("../data/updated.csv") 