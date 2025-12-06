import os
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import numpy as np

def make_embeddings(
        kind: str, 
        sentences:list, 
        encoder: SentenceTransformer 
        ):
    '''
    Creates the embedded representtions of the sentences passed.

    :param str kind: Kind of dataset sentences are from: train, dev, or test
    :param list sentences: Sentences to be encoded
    :param ```SentenceTransformer``` encoder: Encoder to encode the sentence
    '''
    path = f"data/{kind}_embeddings.dat"
    if not os.path.exists(path):
        print(f"Encoding {kind} sentences...")
        chunk_size = 10000
        embeddings = np.memmap(
            path,
            dtype="float32",
            mode="w+",
            shape=(1000000, 384)
        )
        
        for i in tqdm(range(0, len(sentences), chunk_size)):
            chunk = sentences[i:i+chunk_size].tolist()
            chunked_embeddings = encoder.encode(chunk, 
                                                batch_size=128, 
                                                show_progress_bar=False, 
                                                output_value= "sentence_embedding", 
                                                precision="float32", 
                                                convert_to_tensor=False
                                                )
            embeddings[i:(i+len(chunk))] = chunked_embeddings
            embeddings.flush()
    else:
        print(f'Loading {kind} sentence embeddings...') 
        embeddings = np.memmap(
            path, 
            dtype="float32",
            mode="r",
            shape=(1000000, 384)
        )
    embeddings = torch.from_numpy(embeddings) #
    return embeddings