import torch
# import random
import numpy as np
import pandas as pd
from torch.utils.data import Dataset
from modeling.make_embeddings import *
# from modeling.data_pull import *
from collections import Counter 
import re

pd.options.mode.chained_assignment = None

# NOTE: used just when uploading sentences 
# from database.scripts.bq_preprocessing import BigQueryPreprocessor 

# https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html
class CustomDataset(Dataset):
    '''
    label_col: the column to predict on 
    '''
    # NOTE: do we need num_classes
    def __init__(
            self, 
            df: pd.DataFrame, 
            label_col, 
            kind,
            encoder: SentenceTransformer
            ): 
        """
        Unique dataset of type ```Dataset```

        :param ```pd.DataFrame``` df: Dataframe to be made into a dataset
        :param str label_col: Class label to predict
        :param str kind: Kind of dataset sentences are from ie train, dev, test
        :param ```SentenceTransformer``` encoder: Encoder to encode the sentence
        """ 
        # self.df = df
        self.labels = [torch.tensor(label) for label in df[label_col]] 
        self.sentences = make_embeddings(kind, df['des'], encoder) 
        print(len(self.labels))
        print(self.sentences.shape)
        df.drop(columns=['des', label_col, 'batter', 'pitcher', 'home_team', 'away_team'], inplace=True)
        self.values = torch.tensor(df.to_numpy(dtype=np.float32)) 
        # normalize 
        self.weights = self.create_class_weights()

    def __len__(self):
        """Finds the length of the dataset"""
        return len(self.labels)
    
    def __getitem__(self, idx:int): 
        """Retrieves the value, label, and embedded sentence at a given index."""
        value = self.values[idx]
        label = self.labels[idx]
        sent = self.sentences[idx]
        return value, label, sent
    
    def get_classes(self):
        """Retrieves the classes for the data."""
        return pd.Series(self.labels).apply(lambda x: x.item()).unique().tolist()
    
    def get_num_classes(self): 
        """Retrieves the number of classes for the data."""
        return torch.tensor(self.get_classes(), dtype=torch.long).max().item()
    
    def create_class_weights(self):
        sampler_counter = Counter()
        sampler_counter.update(int(label) for label in self.labels)
        sampler_max = max(sampler_counter.values())
        # print(sampler_counter) 
        weighted_counter = {cls: min(((sampler_max/val) ** 0.3), 5) for cls, val in sampler_counter.items()}
        # print(weights)
        return [weighted_counter[int(label)] for label in self.labels]

def weight_classes(data: CustomDataset): 
    """
    Determines class weights for the dataset
    
    :param data: Weights are determined for this dataset
    :type data: CustomDataset
    """
    # class_counts = torch.bincount(data.labels)
    class_counter = Counter()
    class_counter.update([int(label) for label in data.labels])
    weights = []
    for i in range(data.get_num_classes()):
        try: odd = 1.0/class_counter[i]
        except: odd = 1  
        weights.append(odd)
    weights.insert(0, 0.5)
    return torch.tensor(weights)

def make_dataset(
        start_date: str,
        label_col: str, 
        # seed: int, :param int seed: Seed for randomization 
        # splits: list = [0.8, 0.1, 0.1], :param list splits: Splits for [Train, Dev, Test]
        # sample: bool = False, 
        # upload: bool = False
        ) -> Dataset: #-> tuple: Creates train, dev, and test datasets :returns ```tuple``` of datasets:
    """
    Creates or loads in the dataset
    
    :param str start_date: The date to start at from the larger dataset (DD-MM-YYYY)
    :param str label_col: Class label to predict
    
     
    :return DataSet: 
    
    """
    file_date = start_date.replace("-", "_")
    path = f'data/{file_date}_dataset.pt'
    if os.path.exists(path):
        print(f"Loading {start_date} dataset...")
        dataset = torch.load(path, weights_only=False)
        # NOTE: below used when uploading sentences 
        # if upload:
        #     data = {"game_id": dataset.values[:, 0], "at_bat_number": dataset.values[:, 10], 
        #         "pitch_number": dataset.values[:, 36], 
        #         "events": [label.item() for label in dataset.labels],
        #         "sentence_embeddings": [sent.numpy() for sent in dataset.sentences]}
        #     df = pd.DataFrame(data)
        #     processor = BigQueryPreprocessor(
        #         project_id="baseball-prediction-473623", 
        #         dataset_id="statcast_data"
        #     )
        #     processor.load_to_bq(df, write_disposition="WRITE_TRUNCATE")   
    else: 
        # NOTE: if we want to use get data, we have to use big query which will cause us problems as it will 
        # downgrade mlflow 
        print(f"Creating {start_date} dataset...")
        # NOTE: the code below was used to create the sampled dataset 
        if os.path.exists(f"data/{file_date}_data.csv"): 
            df = pd.read_csv(f"data/{file_date}_data.csv")
        else: 
            df = 'd'#get_data(start_date) 
            df.to_csv(f"data/{file_date}_data.csv")
        df = df[df['des'].str.contains("\.")]
        # print(len(df))
        # print(df['des'][:10])
        # if sample: 
        #     class_counter = Counter()
        #     class_counter.update(int(event) for event in df["events"])
        #     print(class_counter)
        #     for i in range(len(df['events'].unique())):
        #         print(class_counter[i])
        #         # NOTE: 
        #         class_counter[i] = 1.0/np.sqrt(class_counter[i])
        #     print(class_counter)
        #     df['weight'] = df['events'].map(class_counter)
        #     # NOTE: 
        #     # NOTE: top 2 at about 200k, for next smallest make sample as large as smaller 
        #     # class, 
        #     df = df.sample(1000000, weights='weight', random_state=seed)
        #     df.drop(columns=["weight"], inplace=True)
        # this might be to find the class weights post sampling 
        # counter = Counter()
        # counter.update(int(event) for event in df["events"])
        # print(f"non-sample counter: {counter}")
        # removes any instances of stats or numbers being in the natural language sentences
        df['des'] = df['des'].apply(lambda x: re.sub(r"\([0-9]+\)", "", x))
        df["game_date"] = df["game_date"].apply(lambda x: str(x).replace("-", ""))
        df.drop(columns=["game_date_int", "embedding_vector"], inplace = True)
        df.to_csv(f"data/{file_date}_sampled_data.csv")
        df = pd.read_csv(f"data/{file_date}_sampled_data.csv")

        encoder= SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

        dataset = CustomDataset(df, label_col, file_date, encoder)
        torch.save(dataset, path)
    # if len(splits) != 3:
    #     splits = [0.8, 0.1, 0.1]

    # class_weights = weight_classes(dataset)
    
    # train_data, dev_data, test_data = torch.utils.data.random_split(dataset, splits)

    # return train_data, dev_data, test_data, (dataset.get_num_classes() + 1), class_weights

    return dataset
