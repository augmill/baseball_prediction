from pybaseball import statcast
import pandas as pd
from multipledispatch import dispatch
from tqdm import tqdm

class dataProcesser():
    def __init__(self, start: str, end: str):
        self.data = statcast(start_dt=start, end_dt=end)
        self.make_csv("raw_data")
        self.data = self.data.reset_index()
        self.keys = {}
        self.empty = pd.DataFrame

    # def remove_unneeded():

    @dispatch(str)
    def convert_to_ordinal(self, col_name) -> bool:
        '''
        Converts data that is not numeric to numeric by assigning each option a trivial value. Creates a key and uses it.\n
        Returns a boolean representing whether or not the data was converted.\n
        NOTE: This function uses the multiple dispatch package so the pop up shown may not represent the correct function. One 
        uses a pre-existing key and the other does not.
        '''
        print(f"Converting {' '.join(col_name.split(sep='_'))} with no key...")
        var = 1 # NOTE: changed to 1 so that 0 can be for empty values 
        key = {}
        data = self.data[col_name]
        try:
            # with open("data/keys.jsonl") as file:
            for i, value in enumerate(tqdm(data)):
                if pd.isna(value):
                    continue
                try: self.data.at[i, col_name] = key[value]
                except: 
                    key[value] = var
                    var += 1
                    self.data.at[i, col_name] = key[value]
            self.keys[col_name] = key
            # file.dump(key)
            # file.write("\n")
            return True
        except Exception as e:
            print(e)
            return False
        
    @dispatch(str, bool) #NOTE: does self effect this?
    def convert_to_ordinal(self, col_name, key_exists) -> bool:
        '''
        Converts data that is not numeric to numeric by assigning each option a trivial value. Requires the key to convert but is
        passes a trival bool in order to know that the key should be used.\n
        Returns a boolean representing whether or not the data was converted.\n
        NOTE: This function uses the multiple dispatch package so the pop up shown may not represent the correct function. One 
        uses a pre-existing key and the other does not.
        '''
        print(f"Converting {' '.join(col_name.split(sep='_'))} with key...")
        data = self.data[col_name]
        try:
            for i, value in enumerate(tqdm(data)):
                if type(value) == pd.NA:
                    continue
                self.data.iloc[i, col_name] = self.data.keys[value]
            return True
        except Exception as e:
            print(e)
            return False

    def clean_data(self) -> bool:
        '''
        Goes over all the columns in the data and confirms they do not have empties but also whether or not they are of a viable type ie 
        not of type string.\n
        Returns bool representing if the data is usebale with the data stored in the object and, if true, also assigned to a CSV file 
        for storage.
        '''
        # NOTE: we need to have a case to handle "des" given it is never specific
        skip = []
        try:
            for col in self.data.columns:
                if pd.NA in self.data[col]:
                    self.empty[col] = self.data[col] #check
                    skip.append(col)
            for col in self.data.select_dtypes(include="object").columns:
                if col not in self.keys.keys():
                    if not self.convert_to_ordinal(col):
                        return False
                else:
                    if not self.convert_to_ordinal(col, self.keys[col]):
                        return False
            self.make_csv("converted_data")
            return True
        except Exception as e:
            print(e)
            return False

    def convert_key(self, col_name: str, key_as_sent: str) -> bool:
        '''
        Adds a columns key to the dictionary of keys (column: {key}) using the format from baseball savant e.g. "W = World Series". \n 
        Nothing whether or not it was converted as a bool
        '''
        try:
            # equations = [sent.strip() for sent in key.split(sep=",")] # letter = sent
            # key = {letter[0]: i for i, letter in enumerate(sent.strip() for sent in key_as_sent.split(sep=","))}
            # key["savant"] = key_as_sent # NOTE: allows us to maintain the original value to know what they are
            self.keys[col_name] = {letter[0]: i for i, letter in enumerate(sent.strip() for sent in key_as_sent.split(sep=","))}
            return True
        except:
            return False
        
    def make_csv(self, file_name: str) -> None:
        '''
        Creates a csv file for the current state of the data stored in the created dataProcesser
        object. Does not need .csv in the file name.\n
        Nothing is returned as it just creates a file.
        '''
        self.data.to_csv(f"data/{file_name}.csv")

        
    