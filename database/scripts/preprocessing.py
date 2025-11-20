import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.feature_extraction import FeatureHasher

def datetime(column: pd.Series) -> pd.Series: 
    """
    Converts ```datetime``` data to usable type for machine learning

    :param ```pd.Series``` column: The column to convert

    :returns ```pd.Series```: returns converted ```pd.Series``` 
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

    :param ```pd.Series``` column: The column to convert

    :returns ```pd.Series```: returns converted ```pd.Series``` 
    """
    print(f"Converting {' '.join(column.name.split(sep='_'))} to hashed features...")
    column = column.astype(str)
    hasher = FeatureHasher(n_features=len(column.unique()), input_type="dict") #len(df[col].unique())
    data = [{column.name:item} for item in column]
    return [[int(val) for val in list(item)] for item in hasher.fit_transform(data).toarray()]


def binarize(column: pd.Series) -> pd.Series:
    """
    Binarizes nominal data that has only two options e.g. right and left

    :param ```pd.Series``` column: The column to convert

    :returns ```pd.Series```: returns converted ```pd.Series``` 
    """
    print(f"Binarizing {' '.join(column.name.split(sep='_'))}...")
    return column.astype("category").cat.codes

def is_player(column: pd.Series):
    """
    Makes each value just a bool i.e. 0 or 1 as to whether or not a player is on that base

    :param ```pd.Series``` column: The column to convert

    :returns ```pd.Series```: returns converted ```pd.Series``` 
    """
    print(f"Converting {' '.join(column.name.split(sep='_'))} to bools...")
    for item in column: 
        if not pd.isna(item): return 1 
        else: return 0

def expand(df: pd.DataFrame, cols: list) -> pd.DataFrame: 
    """
    Expands the values in the columns that ```hash_features``` altered into their own columns

    :param ```pd.DataFrame``` df: the dataframe whose columns are to be changed
    :param list cols: the list of columns to expand

    :returns ```pd.DataFrame```: returns the dataframe with updated values
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

    :param ```pd.DataFrame``` df: the dataframe whose columns are to be changed
    :param list cols: the list of columns to apply the function to 
    :param function func: the function to apply to the list, the function must take only ```pd.Series```

    :returns ```pd.DataFrame```: returns the dataframe with updated values
    """
    for col in cols:
        df[col] = func(df[col])
    return df

nominals = ["game_type", "bb_type", "pitch_name", "type", "if_fielding_alignment", "of_fielding_alignment"]
binaries = ["stand", "p_throws", "inning_topbot", "events"] #events has more than 2 but we want similar 
players = ["on_3b", "on_2b", "on_1b"]

df = pd.read_csv("../data/raw_data.csv")
df["game_date"] = datetime(df["game_date"])
df = process_cols(df, nominals, hash_features)
df = process_cols(df, binaries, binarize)
df = process_cols(df, players, is_player)
df = expand(df, nominals)

# df.to_csv("../data/updated.csv") if you want to export as a csv 