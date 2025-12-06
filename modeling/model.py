'''
The larger model framework: create game state embeddings that are used to predict the at-bat outcome, another step could be 
using the des column we could make outcome sentence embeddings and learn weights to convert them to the sentence embedding and 
either with or without the game state one predict: what granularity of prediction do we want hit vs no hit; out vs on base vs 
homerun; etc. prob between 2 and 8 classes.
'''

import torch 
from torch import nn
from torch import optim
from torchmetrics import Precision
from torch.utils.data import DataLoader
# from torch.utils.data import Dataset
from modeling.CustomDataset import * #baseball_prediction.modeling.
from tqdm.autonotebook import tqdm
# import tensorflow as tf
import numpy as np

# https://stackoverflow.com/questions/49433936/how-do-i-initialize-weights-in-pytorch
def init_weights(model):
    """
    From `this example`__ helps initialize the weights of the various layers
    """
    # NOTE: add instances for other types 
    if isinstance(model, nn.Linear):
        torch.nn.init.kaiming_uniform_(model.weight, nonlinearity='relu')
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
        self.num_heads = num_heads
        self.layer = nn.TransformerEncoderLayer(d_model=dim_out, nhead=num_heads, dim_feedforward=ff_dim, activation="relu", dropout=drop)
        self.encode = nn.Sequential(
            nn.Linear(dim_in, dim_out),
            nn.GELU(), 
            nn.TransformerEncoder(self.layer, num_layers),
            nn.GELU()
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
        self.dropout = nn.Dropout(self.drop)
        self.hidden = nn.Linear(self.dim_hidden, self.dim_hidden)
        self.layer2 = nn.Linear(self.dim_hidden, self.dim_out)
        self.classify = nn.Sequential(
            self.layer1,
            self.relu, 
            self.dropout,
            # self.hidden,
            # self.relu,
            # self.dropout,
            # self.hidden,
            # self.relu,
            # self.dropout,
            # self.hidden,
            # self.relu,
            # self.dropout,
            self.layer2
        )
        self.classify.apply(init_weights)

    def forward(self, input: torch.Tensor):
        # print(input.dtype)
        return self.classify(input)

class Multi(nn.Module):
    def __init__(self, convert: Convertion, classify: Classification, drop: float, concat: bool = True): # dim_in: int, dim_out: int, num_heads: int, ff_dim: int, drop: float, num_classes: int,
        """
        Initialize ```torch.nn.Module``` that stacks other ```torch.nn.Modules```

        :param ```torch.nn.Module``` convert: The module to handle conversion 
        :param ```torch.nn.Module``` classify: The module to projection to classification size 
        :param bool concat: Tells the module whether or not it should attach the original input to the output of the first layer before being passed to the second 
        """
        super().__init__()
        self.concat = concat
        self.conversion_layer = convert
        self.clasifier_layer = classify
        self.relu = nn.ReLU()
        self.drop = nn.Dropout(drop)

    def forward(self, input: torch.Tensor):
        out = torch.cat([input,self.conversion_layer(input)], dim=1) if self.concat else self.conversion_layer(input)
        return self.clasifier_layer(out)
    
    

def training(model:nn.Module, input, targets, opt, loss_fn, mod_to_train: int = 0, max_norm_value: float = 1.0):
    """
    Determines model logits and loss

    :param data: Input data
    :param targets: Target labels
    :param optim opt: Training optimizer
    :param loss_fn: Loss function
    :param int mod_to_train: 0 mixed, 1 encode, 2 class alone, 3 class for concat input, 4 encode with cosine
    :param float max_norm_value: Value for gradient clipping 
    """
    logits = model(input)
    if mod_to_train in [0, 1, 2, 3]:
        loss = loss_fn(logits, targets) #.long()
    elif mod_to_train == 4:
        loss = loss_fn(logits, targets, torch.ones(logits.shape[0]))
    else: 
        raise KeyError(mod_to_train)
    opt.zero_grad()
    loss.backward()
    # gradiant clipping https://docs.pytorch.org/docs/stable/generated/torch.nn.utils.clip_grad_norm_.html
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=max_norm_value)
    opt.step()
    return loss.detach().item()#, model
        


def training_loop(model:nn.Module, opt:optim, loss_fn, data:DataLoader, mod_to_train: int = 0, max_norm_value: float = 1.0):
    """
    :param ```nn.Module``` model: Model to train
    :param optim opt: Training optimizer
    :param loss_fn: Training loss function
    :param ```DataLoader``` data: Training data
    :param int mod_to_train: 0 mixed, 1 encode, 2 class alone, 3 class for concat input, 4 encode with cosine
    :param float max_norm_value: Value for gradient clipping 

    """
    losses = []
    model.train()

    if mod_to_train == 0: # mixed
        for batch in tqdm(data, desc = "Training"):
            inputs = batch[0]
            targets = batch[1]
            loss = training(model, inputs, targets, opt, loss_fn, mod_to_train, max_norm_value)
            losses.append(loss)
    elif mod_to_train in [1, 4]: # encode
        for batch in tqdm(data, desc = "Training"): 
            inputs = batch[0]
            targets = batch[2]
            loss = training(model, inputs, targets, opt, loss_fn, mod_to_train, max_norm_value)
            losses.append(loss)
    elif mod_to_train == 2: # just class
        for batch in tqdm(data, desc = "Training"):
            inputs = batch[2]
            targets = batch[1]
            loss = training(model, inputs, targets, opt, loss_fn, mod_to_train, max_norm_value)
            losses.append(loss)
    elif mod_to_train == 3: # class with concat input
        for batch in tqdm(data, desc = "Training"):
            inputs = torch.concat([batch[0],batch[2]], dim=1)
            targets = batch[1]
            loss = training(model, inputs, targets, opt, loss_fn, mod_to_train, max_norm_value)
            losses.append(loss)
    else: raise KeyError(mod_to_train)
    print(f"Training loss: {sum(losses)/len(losses)}")


def validation(
        model:nn.Module, 
        data:DataLoader, 
        macro: Precision, 
        weighted: Precision, 
        mod: int = 0
    ): 
    """
    :param ```nn.Module``` model: Model to validate
    :param ```DataLoader``` data: Validation data
    :param ```torchmetrics.Precision``` macro: Macro precision 
    :param ```torchmetrics.Precision``` macro: Weighted precision
    :param int mod_to_train: 0 mixed, 1 encode, 2 class alone, 3 class for concat input, 4 encode with cosine
    """
    losses = []
    macro.reset()
    weighted.reset()
    model.eval()
    with torch.no_grad():
        if mod == 0: # mixed
            for batch in tqdm(data, desc = "Validating"):
                logits = model(batch[0])
                labels = batch[1]
                macro.update(torch.argmax(logits, dim=1), labels)
                weighted.update(torch.argmax(logits, dim=1), labels)
            losses.append(macro.compute())
            losses.append(weighted.compute())
        elif mod in [1, 4]: # encode
            sim = []
            loss = nn.MSELoss()
            for batch in tqdm(data, desc = "Validating"):
                logits = model(batch[0])
                labels = batch[2]
                losses.append(loss(logits, labels))
                sim.append(nn.functional.cosine_similarity(logits, labels))
            average = torch.mean(torch.cat(sim, dim=0))
            print(f"Cosine similarity: {average}")
            losses = [sum(losses)/len(losses)]
        elif mod == 2: # just class
            for batch in tqdm(data, desc = "Validating"):
                logits = model(batch[2])
                labels = batch[1]
                macro.update(torch.argmax(logits, dim=1), labels)
                weighted.update(torch.argmax(logits, dim=1), labels)
            losses.append(macro.compute())
            losses.append(weighted.compute())
        elif mod == 3: # class with concat input
            for batch in tqdm(data, desc = "Validating"):
                logits = model(torch.concat([batch[0],batch[2]], dim=1))
                labels = batch[1]
                macro.update(torch.argmax(logits, dim=1), labels)
                weighted.update(torch.argmax(logits, dim=1), labels)
            losses.append(macro.compute())
            losses.append(weighted.compute())
    return losses

def fit(
        model:nn.Module, 
        opt:optim, 
        loss_fn, 
        train_data:DataLoader, 
        val_data:DataLoader, 
        num_classes:int, 
        epochs:int, 
        mod_to_train: int = 0
        ): 
    """
    :param ```nn.Module``` model: Model to train and validate 
    :param optim opt: Training optimizer
    :param loss_fn: Training loss function (note used for validation)
    :param ```DataLoader``` data: Training data
    :param ```DataLoader``` data: Validation data
    :param int num_classes: Number of possible class labels
    :param int epochs: Number of epochs to complete
    :param int mod_to_train: 0 mixed, 1 encode, 2 class alone, 3 class for concat input, 4 encode with cosine
    """

    macro_precision = Precision(task="multiclass", average="macro", num_classes=num_classes)
    weighted_precision = Precision(task="multiclass", average="weighted", num_classes=num_classes)
    print(F"\n\nFitting {model._get_name()} model...")
    for epoch in range(epochs):
        print("-"*25, f"Epoch: {epoch+1}", "-"*25)
        training_loop(model, opt, loss_fn, train_data, mod_to_train)
        print()
        losses = validation(model, val_data, macro_precision, weighted_precision, mod_to_train)
        if len(losses) == 1:
            print(F"Validation loss: {losses[0]}")
        elif len(losses) == 2:
            print(F"Validation Macro precision: {losses[0]}\nValidation Weighted precision: {losses[1]}")
        else: raise ValueError()
        macro_precision.reset()
        weighted_precision.reset() 
    return model
        
