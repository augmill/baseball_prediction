'''
The larger model framework: create game state embeddings that are used to predict the at-bat outcome, another step could be 
using the des column we could make outcome sentence embeddings and learn weights to convert them to the sentence embedding and 
either with or without the game state one predict: what granularity of prediction do we want hit vs no hit; out vs on base vs 
homerun; etc. prob between 2 and 8 classes.
'''

import torch 
from torch import nn
# from torch import optim
# from torchmetrics import Precision
# from torch.utils.data import DataLoader
# from torch.utils.data import Dataset
# from modeling.CustomDataset import * #baseball_prediction.modeling.
# from tqdm.autonotebook import tqdm
# import tensorflow as tf
# import numpy as np

# https://stackoverflow.com/questions/49433936/how-do-i-initialize-weights-in-pytorch
def init_weights(model):
    """
    From `this example`__ helps initialize the weights of the various layers
    """
    # NOTE: add instances for other types 
    if isinstance(model, nn.Linear):
        torch.nn.init.kaiming_uniform_(model.weight, nonlinearity='leaky_relu') # , nonlinearity='relu' or 'leaky_relu'
        # torch.nn.init.xavier_uniform_(model.weight)
        model.bias.data.fill_(0.01) # starting bias
    # elif isinstance(model, nn.TransformerEncoder)

class Convertion(nn.Module): # may want to add concat = True which will have the features split for each layer and concated
    def __init__(self, 
                 dim_in: int,
                 dim_out: int, 
                 num_heads: int, 
                 ff_dim: int,
                 drop: float,
                 num_layers: int = 1 
                ):
        """
        Initialize ```torch.nn.Module``` that converts a game state embedding to sentence embedding 
        using ```torch.nn.TransformerEncoder```
        
        :param int dim_in:  Dimention of input vector (the game state embedding) 
        :param int dim_out: Dimention of output vector (sentence_embedding)
        :param int num_heads: Number of heads or attention mechanisms in the trasnformer layers
        :param int ff_dim: Dimention of each feedforward network in the trasnformer layers
        :param float drop: The dropout rate for the transformer layers
        :param int num_layers: Number of transformer layers in the encoder 
        """
        super().__init__()
        self.dim_in = dim_in
        self.dim_out = dim_out
        self.num_heads = num_heads
        self.drop = drop
        self.dropout = nn.Dropout(drop)
        self.projection = nn.Linear(dim_in, dim_out)
        self.gelu = nn.GELU()
        self.relu = nn.ReLU()
        self.leaky = nn.LeakyReLU(0.1)
        self.layer = nn.TransformerEncoderLayer(d_model=dim_out, nhead=num_heads, dim_feedforward=ff_dim, activation="relu", dropout=drop)
        self.transformer = nn.TransformerEncoder(self.layer, num_layers)
        # self.normalize = nn.functional.normalize()
        self.encode = nn.Sequential(
            self.dropout,
            self.projection,
            self.leaky, 
            self.transformer,
            self.gelu
            # self.normalize
        )
        self.encode.apply(init_weights)

    def forward(self, input: torch.Tensor, num_layers: int = 1) -> torch.Tensor: 
        return self.encode(input)

class Classification(nn.Module): 
    def __init__( 
            self, 
            dim_in: int, 
            dim_out: int,
            drop: int
            ):
        """
        Initialize ```torch.nn.Module``` that reshapes a vector so that classification can be done

        :param int dim_in: Dimention of input vector
        :param int dim_out: Dimention of output vector 
        :param int drop: Dropout value 
        """
        super().__init__()
        self.dim_in = dim_in
        self.dim_out = dim_out
        self.dim_hidden = int((self.dim_in * (2/3)) + self.dim_out)
        self.drop = drop
        self.layer1 = nn.Linear(self.dim_in, self.dim_hidden)
        self.relu = nn.ReLU()
        self.leaky = nn.LeakyReLU(0.1)
        self.dropout = nn.Dropout(self.drop)
        self.hidden = nn.Linear(self.dim_hidden, self.dim_hidden)
        self.layer2 = nn.Linear(self.dim_hidden, self.dim_out)
        self.classify = nn.Sequential(
            # self.dropout,
            self.layer1,
            self.leaky, 
            self.dropout,
            self.layer2
        )
        self.classify.apply(init_weights)

    def forward(self, input: torch.Tensor):
        # print(input.dtype)
        return self.classify(input)

class Multi(nn.Module):
    def __init__(
        self, 
        convert: Convertion, 
        classify: Classification, 
        drop: float, 
        freeze: bool = False,
        concat: bool = True
    ): # dim_in: int, dim_out: int, num_heads: int, ff_dim: int, drop: float, num_classes: int,
        """
        Initialize ```torch.nn.Module``` that stacks other ```torch.nn.Modules```

        :param ```torch.nn.Module``` convert: The module to handle conversion 
        :param ```torch.nn.Module``` classify: The module to projection to classification size 
        :param bool concat: Tells the module whether or not it should attach the original input to the output of the first layer before being passed to the second 
        """
        super().__init__()
        self.dim_in = convert.dim_in
        self.concat = concat
        self.conversion_layer = convert
        self.clasifier_layer = classify
        self.relu = nn.ReLU()
        self.leaky = nn.LeakyReLU(0.1)
        self.dropout = nn.Dropout(drop)
        if freeze == True:
            for param in self.conversion_layer.parameters():
                param.requires_grad = False
    def forward(self, input: torch.Tensor):
        out = torch.cat([input,self.conversion_layer(input)], dim=1) if self.concat else self.conversion_layer(input)
        # out = self.relu(out)
        # out = self.dropout(out)
        return self.clasifier_layer(out)
