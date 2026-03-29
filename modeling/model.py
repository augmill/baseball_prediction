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
        # num_heads: int,
        # ff_dim: int,
        # trans_drop: float,
        in_num_heads: int, 
        in_ff_dim: int,
        drop: float,
        in_trans_drop: float,
        out_num_heads: int, 
        out_ff_dim: int,
        out_trans_drop: float,
        in_dim_inner: int = 32, # Small data: d_model ≈ 32–64 Medium: 64–128 Large / complex interactions: 128–256
        in_num_layers: int = 1,
        out_dim_inner: int = 32, # Small data: d_model ≈ 32–64 Medium: 64–128 Large / complex interactions: 128–256
        out_num_layers: int = 1,
        dim_hidden: int = 462,
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
        self.in_dim_inner = in_dim_inner
        self.in_num_heads = in_num_heads
        self.dim_hidden = dim_hidden
        self.drop = drop
        self.dropout = nn.Dropout(drop) # batch norm over dropout?
        self.trans_drop = in_trans_drop
        self.out_dim_inner = out_dim_inner
        self.out_num_heads = out_num_heads
        self.trans_drop = out_trans_drop

        self.embed = nn.Linear(1, in_dim_inner)
        self.embed.apply(init_weights)
        self.pooling = lambda x : x.mean(dim=-1) #1dpool? # putting -1 gettings batch, dim_in, 1 gets batch, inner_dim
        self.hidden_proj = (in_dim_inner * dim_out)
        self.projection = nn.Linear(self.hidden_proj, dim_out)
        self.projection.apply(init_weights)
        self.in_projection = nn.Linear(dim_in, self.hidden_proj)
        self.in_projection.apply(init_weights)

        self.gelu = nn.GELU()
        self.relu = nn.ReLU()
        self.leaky = nn.LeakyReLU(0.1)
        self.in_layer = nn.TransformerEncoderLayer(
            d_model=in_dim_inner, 
            nhead=in_num_heads, 
            dim_feedforward=in_ff_dim, #ff_dim, 
            activation="gelu", 
            dropout=in_trans_drop,
            batch_first=True    
        )
        self.in_transformer = nn.TransformerEncoder(self.in_layer, in_num_layers)
        self.normalize = lambda x : nn.functional.normalize(x)

        self.out_layer = nn.TransformerEncoderLayer(
            d_model=dim_out, #out_dim_inner
            nhead=out_num_heads,
            dim_feedforward=out_ff_dim,
            activation='relu',
            dropout=out_trans_drop,
            batch_first=True
        )

        self.out_transformer = nn.TransformerEncoder(self.out_layer, out_num_layers)
        self.ln = nn.LayerNorm(in_dim_inner)

    def forward(self, input: torch.Tensor) -> torch.Tensor: 
        x = input.unsqueeze(-1)
        x = self.embed(x)
        x_skip = self.leaky(x)
        x = self.in_transformer(x_skip)
        x = x + x_skip 
        x = self.ln(x)
        x = self.pooling(x)
        x = self.leaky(x)
        x = x + input
        x = self.in_projection(x)
        x = self.leaky(x)
        x = self.projection(x)
        self.normalize(x)

        return x

        # return self.normalize(self.encode(input))

        #decent results came from this?

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
        x = x + input
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
        self.layer1.apply(init_weights)
        self.relu = nn.ReLU()
        self.leaky = nn.LeakyReLU(0.1)
        self.dropout = nn.Dropout(self.drop)
        self.hidden = nn.Linear(self.dim_hidden, self.dim_hidden)
        self.hidden.apply(init_weights)
        self.layer2 = nn.Linear(self.dim_hidden, self.dim_out)
        self.layer2.apply(init_weights)

        self.ln = nn.LayerNorm(self.dim_hidden)

        # self.classify = nn.Sequential(
        #     # self.dropout,
        #     self.layer1,
        #     self.leaky, 
        #     self.dropout,
        #     self.layer2
        # )
        self.hidden_layers = nn.ModuleList([
            nn.Linear(self.hidden, self.hidden) for _ in range(self.num_hidden)
        ])
        for layer in self.hidden_layers:
            layer.apply(init_weights)
        # for module in [self.layer1, self.hidden, self.layer2]:
        #     module.apply(init_weights)

    def forward(self, input: torch.Tensor):
        x = self.layer1(input)
        for layer in self.hidden_layers: # change to using module list
            x = self.ln(x)
            x = self.leaky(x)
            # x = self.dropout(x)
            x = layer(x)
        x = self.ln(x)
        x = self.leaky(x)
        # x = self.dropout(x)
        x = self.layer2(x)
        # print(input.dtype)
        # return self.classify(input)
        return x

class Multi(nn.Module):
    def __init__(
        self, 
        # dim_in: int,
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
        # self.dim_in = dim_in#convert.dim_in
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
