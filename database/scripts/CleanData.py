"""
Used by CleanData.sh to clean raw statcast data from pybaseball

TODO: this cleaning script needs some work
"""
import pandas as pd
from multipledispatch import dispatch
from tqdm import tqdm
import sys
import os

class dataCleanProcessor():
    def __init__(self, raw_data_file_path: str):
        """
        Initialize the data cleaner with a raw CSV file path.
        
        Args:
            raw_data_file_path: Path to the raw CSV file containing statcast data
        """
        if not os.path.exists(raw_data_file_path):
            raise FileNotFoundError(f"Raw data file not found: {raw_data_file_path}")
        
        try:
            self.data = pd.read_csv(raw_data_file_path)
            self.data = self.data.reset_index(drop=True)
            self.keys = {}
            self.empty = pd.DataFrame()
            self.raw_file_path = raw_data_file_path
        except Exception as e:
            raise Exception(f"Error loading CSV file: {e}")

    @dispatch(str)
    def convert_to_ordinal(self, col_name) -> bool:
        '''
        Converts data that is not numeric to numeric by assigning each option a trivial value. Creates a key and uses it.\n
        Returns a boolean representing whether or not the data was converted.\n
        NOTE: This function uses the multiple dispatch package so the pop up shown may not represent the correct function. One 
        uses a pre-existing key and the other does not.
        '''
        print(f"Converting {' '.join(col_name.split(sep='_'))} with no key...")
        var = 0
        key = {}
        data = self.data[col_name]
        try:
            for i, value in enumerate(tqdm(data, desc=f"Processing {col_name}")):
                if pd.isna(value):
                    continue
                try: 
                    self.data.at[i, col_name] = key[value]
                except: 
                    key[value] = var
                    var += 1
                    self.data.at[i, col_name] = key[value]
            self.keys[col_name] = key
            return True
        except Exception as e:
            print(e)
            return False
        
    @dispatch(str, bool)
    def convert_to_ordinal(self, col_name, key_exists) -> bool:
        '''
        Converts data that is not numeric to numeric by assigning each option a trivial value. Requires the key to convert but is
        passes a trivial bool in order to know that the key should be used.\n
        Returns a boolean representing whether or not the data was converted.\n
        NOTE: This function uses the multiple dispatch package so the pop up shown may not represent the correct function. One 
        uses a pre-existing key and the other does not.
        '''
        print(f"Converting {' '.join(col_name.split(sep='_'))} with key...")
        data = self.data[col_name]
        try:
            for i, value in enumerate(tqdm(data, desc=f"Processing {col_name} with key")):
                if pd.isna(value):
                    continue
                self.data.at[i, col_name] = self.keys[col_name][value]
            return True
        except Exception as e:
            print(e)
            return False

    def clean_data(self) -> bool:
        '''
        Goes over all the columns in the data and confirms they do not have empties but also whether or not they are of a viable type ie 
        not of type string.\n
        Returns bool representing if the data is usable with the data stored in the object and, if true, also assigned to a CSV file 
        for storage.
        '''
        # NOTE: we need to have a case to handle "des" given it is never specific
        skip = []
        try:
            for col in self.data.columns:
                if self.data[col].isna().any():
                    self.empty[col] = self.data[col]
                    skip.append(col)
            
            for col in self.data.select_dtypes(include="object").columns:
                if col not in skip:  # Skip columns with too many NAs
                    if col not in self.keys.keys():
                        if not self.convert_to_ordinal(col):
                            return False
                    else:
                        if not self.convert_to_ordinal(col, True):
                            return False
            
            self.make_csv("converted_data")
            return True
        except Exception as e:
            print(e)
            return False

    def convert_key(self, col_name: str, key_as_sent: str) -> bool:
        '''
        Adds a columns key to the dictionary of keys (column: {key}) using the format from baseball savant e.g. "W = World Series". \n
        Returns whether or not it was converted as a bool
        '''
        try:
            self.keys[col_name] = {letter[0]: i for i, letter in enumerate(sent.strip() for sent in key_as_sent.split(sep=","))}
            return True
        except Exception as e:
            print(f"Error converting key for {col_name}: {e}")
            return False
        
    def make_csv(self, file_name: str) -> str:
        '''
        Creates a csv file for the current state of the data stored in the created dataCleanProcessor
        object. Does not need .csv in the file name.\n
        Returns the path to the created CSV file.
        '''
        # Generate output file name based on input file
        if file_name == "converted_data":
            # Create clean file name from raw file name
            base_name = os.path.basename(self.raw_file_path)
            clean_name = base_name.replace("_raw.csv", "_clean.csv")
            output_path = os.path.join("/tmp", clean_name)
        else:
            output_path = f"/tmp/{file_name}.csv"
        
        self.data.to_csv(output_path, index=False)
        return output_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 ./CleanData.py <raw data file>")
        sys.exit(1)
    
    raw_file_path = sys.argv[1]
    
    try:
        processor = dataCleanProcessor(raw_file_path)
        if processor.clean_data():
            # Generate the expected output file name for the shell script
            base_name = os.path.basename(raw_file_path)
            clean_name = base_name.replace("_raw.csv", "_clean.csv")
            output_path = os.path.join("/tmp", clean_name)
            print(f"Data cleaning completed successfully. Output saved to {output_path}")
        else:
            print("Data cleaning failed")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

