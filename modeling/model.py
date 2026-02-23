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
    def __init__(
        self, 
        dim_in: int,
        dim_out: int, 
        num_heads: int, 
        ff_dim: int,
        drop: float,
        trans_drop: float,
        dim_inner: int = 32, # Small data: d_model ≈ 32–64 Medium: 64–128 Large / complex interactions: 128–256
        num_layers: int = 1 
    ):
        """
        Initialize ```torch.nn.Module``` that converts a game state embedding to sentence embedding 
        using ```torch.nn.TransformerEncoder```
        
        :param int dim_in:  Dimention of input vector (the game state embedding) 
        :param int dim_out: Dimention of output vector (sentence_embedding)
        :param int num_heads: Number of heads or attention mechanisms in the trasnformer layers
        :param int ff_dim: Dimention of each feedforward network in the trasnformer layers
        :param float drop: The dropout outside of the transformer
        :param float trans_drop: The dropout rate for the transformer layers
        :param int num_layers: Number of transformer layers in the encoder 
        """
        super().__init__()
        self.dim_in = dim_in
        self.dim_out = dim_out
        self.dim_inner = dim_inner
        self.num_heads = num_heads
        self.drop = drop
        self.dropout = nn.Dropout(drop) # batch norm over dropout?
        self.trans_drop = trans_drop

        self.embed = nn.Linear(1, dim_inner)
        self.pos_embed = nn.Parameter(torch.randn(1, 78, dim_inner))

        # self.projection = nn.Linear(dim_inner, dim_out)
        self.projection = nn.Linear(dim_inner, 34)
        # self.projection = nn.Linear(ff_dim, dim_out)
        self.gelu = nn.GELU()
        self.relu = nn.ReLU()
        self.leaky = nn.LeakyReLU(0.1)
        self.layer = nn.TransformerEncoderLayer(
            d_model=dim_in, 
            nhead=num_heads, 
            dim_feedforward=ff_dim, #ff_dim, 
            activation="relu", 
            dropout=trans_drop,
            batch_first=True    
        )
        self.transformer = nn.TransformerEncoder(self.layer, num_layers)
        self.pooling = lambda x : x.mean(dim=1)
        self.normalize = lambda x : nn.functional.normalize(x)


        self.num_hidden = num_layers
        self.layer1 = nn.Linear(dim_in, ff_dim)
        self.hidden = nn.Linear(ff_dim, ff_dim)
        self.layer2 = nn.Linear(ff_dim, dim_out)
        self.bn = nn.BatchNorm1d(ff_dim)
        # self.final_bn = nn.BatchNorm1d(dim_out)


        self.encode = nn.Sequential(
            # self.dropout,
            self.projection, #NOTE: need to chnage so i do not have two of the same layer and i/o dims are good
            # self.gelu,
            # self.relu,
            # self.leaky, 
            self.transformer,
            # self.gelu,
            self.dropout,
            self.projection,
            # self.gelu
            # self.normalize
        )
        self.encode.apply(init_weights)

        # for module in [self.layer1, self.hidden, self.layer2]:
        #     module.apply(init_weights)

    def forward(self, input: torch.Tensor) -> torch.Tensor: 
        # x = input.unsqueeze(-1)
        # x = self.embed(x)

        # x = self.embed(input.unsqueeze(-1))
        # x += self.pos_embed
        # return self.normalize(self.projection(self.pooling(self.transformer(x))))
    
        # x = self.transformer(x)
        # x = self.pooling(x)
        # x = self.dropout(x)
        # x = self.projection(x)
        # x = self.normalize(x)
        # x = self.encode(input)

        return self.normalize(self.encode(input))

        x = self.layer1(input)
        x = self.bn(x)
        x = self.leaky(x)
        # x = self.dropout(x)
        for _ in range(self.num_hidden):
            x = self.hidden(x)
            x = self.bn(x)
            x = self.leaky(x)
            # x = self.dropout(x)
        # x = self.dropout(x)
        x = self.layer2(x)
        self.normalize(x)
        return x

class Classification(nn.Module): 
    def __init__( 
            self, 
            dim_in: int, 
            dim_out: int,
            drop: int,
            num_hidden: int = 0
            ):
        """
        Initialize ```torch.nn.Module``` that reshapes a vector so that classification can be done

        :param int dim_in: Dimention of input vector
        :param int dim_out: Dimention of output vector 
        :param int drop: Dropout value 
        :param int num_hidden: Number of extra hidden layer beyond the default 1
        """
        super().__init__()
        self.dim_in = dim_in
        self.dim_out = dim_out
        self.dim_hidden = int((self.dim_in * (2/3)) + self.dim_out)
        self.drop = drop
        self.num_hidden = num_hidden
        self.layer1 = nn.Linear(self.dim_in, self.dim_hidden)
        self.relu = nn.ReLU()
        self.leaky = nn.LeakyReLU(0.1)
        self.dropout = nn.Dropout(self.drop)
        self.hidden = nn.Linear(self.dim_hidden, self.dim_hidden)
        self.layer2 = nn.Linear(self.dim_hidden, self.dim_out)
        # self.classify = nn.Sequential(
        #     # self.dropout,
        #     self.layer1,
        #     self.leaky, 
        #     self.dropout,
        #     self.layer2
        # )
        for module in [self.layer1, self.hidden, self.layer2]:
            module.apply(init_weights)

    def forward(self, input: torch.Tensor):
        x = self.layer1(input)
        for _ in range(self.num_hidden): # change to using module list
            x = self.leaky(x)
            x = self.dropout(x)
            x = self.hidden(x)
        x = self.leaky(x)
        x = self.dropout(x)
        x = self.layer2(x)
        # print(input.dtype)
        # return self.classify(input)
        return x

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
        # maybe make this like a skip connection rather than concatonate? 
        out = torch.cat([input,self.conversion_layer(input)], dim=1) if self.concat else self.conversion_layer(input)
        # out = self.relu(out)
        # out = self.dropout(out)
        return self.clasifier_layer(out)
