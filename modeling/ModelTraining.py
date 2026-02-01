import torch 
from torch import nn
from torch import optim
from torchmetrics import Precision
from torch.utils.data import DataLoader
from torchinfo import summary
import matplotlib.pyplot as plt
from tqdm.autonotebook import tqdm

class ModelTraining():
    def __init__(
        self, 
        model: nn.Module, 
        num_classes:int, 
        batch_size:int, 
        mod_to_train: int = 0
    ):
        self.model = model
        self.loss = []
        self.loss_name = ''
        self.metric = [[], []]
        self.best_metric = [-1, -1]
        self.batch_size = batch_size 
        self.mod_to_train = mod_to_train
        self.macro_precision = Precision(task="multiclass", average="macro", num_classes=num_classes)
        self.weighted_precision = Precision(task="multiclass", average="weighted", num_classes=num_classes)
        self.metric_names = []
 
        if self.mod_to_train in [0, 2, 3]:
            self.metric_names.append('Macro Precision')
            self.metric_names.append('Weighted Precision')
        elif self.mod_to_train in [1, 4]: 
            self.metric_names.append('Cosine Similarity')
            self.metric_names.append('Mean Squared Error Loss')

    def training(
        self, 
        # model:nn.Module,
        input, 
        targets, 
        opt, 
        loss_fn,
        # mod_to_train: int = 0, 
        max_norm_value: float = 1.0,

    ):  
        """
        Determines model logits and loss

        :param data: Input data
        :param targets: Target labels
        :param optim opt: Training optimizer
        :param loss_fn: Loss function
        :param int mod_to_train: 0 mixed, 1 encode, 2 class alone, 3 class for concat input, 4 encode with cosine
        :param float max_norm_value: Value for gradient clipping 
        """
        logits = self.model(input)
        try: loss = loss_fn(logits, targets)
        except: loss = loss_fn(logits, targets, torch.ones(logits.shape[0])) # should only happen if cosine
        # if mod_to_train in [0, 1, 2, 3]:
        #     loss = loss_fn(logits, targets) #.long()
        # elif mod_to_train == 4:
        #     loss = loss_fn(logits, targets, torch.ones(logits.shape[0]))
        # else: 
        #     raise KeyError(mod_to_train)
        opt.zero_grad()
        loss.backward()
        # gradiant clipping https://docs.pytorch.org/docs/stable/generated/torch.nn.utils.clip_grad_norm_.html
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=max_norm_value)
        opt.step()
        return loss.detach().item() #, model

    def training_loop(
        self,
        # model:nn.Module, 
        opt:optim, 
        loss_fn, 
        data:DataLoader, 
        # mod_to_train: int = 0, 
        max_norm_value: float = 1.0
    ):
        """
        :param ```nn.Module``` model: Model to train
        :param optim opt: Training optimizer
        :param loss_fn: Training loss function
        :param ```DataLoader``` data: Training data
        :param int mod_to_train: 0 mixed, 1 encode, 2 class alone, 3 class for concat input, 4 encode with cosine
        :param float max_norm_value: Value for gradient clipping 
        """
        losses = []
        self.model.train()
        if self.mod_to_train == 0: # mixed
            # for batch in tqdm(data, desc = "Training"):
            for batch in data:
                # inputs = batch[0]
                # targets = batch[1]
                loss = self.training(batch[0], batch[1], opt, loss_fn, max_norm_value) # model, , mod_to_train 
                losses.append(loss)
        elif self.mod_to_train in [1, 4]: # encode
            # for batch in tqdm(data, desc = "Training"): 
            for batch in data:
                # inputs = batch[0]
                # targets = batch[2]
                loss = self.training(batch[0], batch[2], opt, loss_fn, max_norm_value) # model, , mod_to_train
                losses.append(loss)
        elif self.mod_to_train == 2: # just class
            # for batch in tqdm(data, desc = "Training"):
            for batch in data:
                # inputs = batch[2]
                # targets = batch[1]
                loss = self.training(batch[2], batch[1], opt, loss_fn, max_norm_value) # model, , mod_to_train
                losses.append(loss)
        elif self.mod_to_train == 3: # class with concat input
            # for batch in tqdm(data, desc = "Training"):
            for batch in data: 
                # inputs = torch.concat([batch[0],batch[2]], dim=1)
                # targets = batch[1]
                loss = self.training(torch.concat([batch[0],batch[2]], dim=1), batch[1], opt, loss_fn, max_norm_value) # model, , mod_to_train
                losses.append(loss)
        else: raise KeyError(self.mod_to_train)
        # print(f"Training loss: {sum(losses)/len(losses)}")
        self.loss.append(sum(losses)/len(losses))

    def validation(
        self, 
        # model:nn.Module, 
        data:DataLoader, 
        # macro: Precision, 
        # weighted: Precision, 
        cosine_sim: nn.functional = lambda x, y : nn.functional.cosine_similarity(x, y),
        MSE = nn.MSELoss(), 
        # mod: int = 0
    ): 
        """
        :param ```nn.Module``` model: Model to validate
        :param ```DataLoader``` data: Validation data
        :param ```torchmetrics.Precision``` macro: Macro precision (only optional if using )
        :param ```torchmetrics.Precision``` macro: Weighted precision
        :param ```nn.functional```, optional cosine_sim: Cosine similarity used for ```Convertion``` models
        :param optional MSE: Mean squared error loss used for the ```Convertion``` models 
        :param int mod_to_train: 0 mixed, 1 encode, 2 class alone, 3 class for concat input, 4 encode with cosine
        
        :return list: List of the loss metrics
        """
        losses = []
        self.macro_precision.reset()
        self.weighted_precision.reset()
        self.model.eval()
        with torch.no_grad():
            if self.mod_to_train == 0: # mixed
                # for batch in tqdm(data, desc = "Validating"):
                for batch in data:
                    logits = self.model(batch[0])
                    labels = batch[1]
                    # self.macro_precision.update(torch.argmax(logits, dim=1), labels)
                    # self.weighted_precision.update(torch.argmax(logits, dim=1), labels)
                    self.macro_precision.update(logits, labels)
                    self.weighted_precision.update(logits, labels)
                losses.append(self.macro_precision.compute())
                losses.append(self.weighted_precision.compute())
            elif self.mod_to_train in [1, 4]: # encode
                sim = []
                # loss = nn.MSELoss()
                # for batch in tqdm(data, desc = "Validating"):
                for batch in data:
                    logits = self.model(batch[0])
                    embeds = batch[2]
                    losses.append(MSE(logits, embeds))
                    sim.append(cosine_sim(logits, embeds))
                # average = torch.mean(torch.cat(sim, dim=0))
                # print(f"Cosine similarity: {average}")
                # losses = [sum(losses)/len(losses)]
                losses.append(torch.mean(torch.cat(sim, dim=0)))
                losses.append(sum(losses)/len(losses))
            elif self.mod_to_train == 2: # just class
                # for batch in tqdm(data, desc = "Validating"):
                for batch in data:
                    logits = self.model(batch[2])
                    labels = batch[1]
                    # self.macro_precision.update(torch.argmax(logits, dim=1), labels)
                    # self.weighted_precision.update(torch.argmax(logits, dim=1), labels)
                    self.macro_precision.update(logits, labels)
                    self.weighted_precision.update(logits, labels)
                losses.append(self.weighted_precision.compute())
            elif self.mod_to_train == 3: # class with concat input
                # for batch in tqdm(data, desc = "Validating"):
                for batch in data:
                    logits = self.model(torch.concat([batch[0],batch[2]], dim=1))
                    labels = batch[1]
                    # self.macro_precision.update(torch.argmax(logits, dim=1), labels)
                    # self.weighted_precision.update(torch.argmax(logits, dim=1), labels)
                    self.macro_precision.update(logits, labels)
                    self.weighted_precision.update(logits, labels)
                losses.append(self.macro_precision.compute())
                losses.append(self.weighted_precision.compute())
        return losses

    def fit(
        self,
        # model:nn.Module, 
        opt:optim, 
        loss_fn, 
        train_data:DataLoader, 
        val_data:DataLoader, 
        # num_classes:int, 
        epochs:int, 
        # batch_size: int,
        max_norm_value: float = 1.0,
        # mod_to_train: int = 0
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
        self.loss_name = loss_fn._get_name()
        self.epochs = epochs
        # print(f'batch: {self.batch_size}')
        print(summary(self.model, input_size=(self.batch_size, self.model.dim_in))) 
        # macro_precision = Precision(task="multiclass", average="macro", num_classes=num_classes)
        # weighted_precision = Precision(task="multiclass", average="weighted", num_classes=num_classes)
        # cosine_sim = lambda x, y : nn.functional.cosine_similarity(x, y)
        # MSE = nn.MSELoss()
        print()
        print(F"\n\nFitting {self.model._get_name()} model...")
        # for epoch in range(epochs):
        for _ in tqdm(range(epochs), desc="Epochs"): 
            # print("-"*25, f"Epoch: {epoch+1}", "-"*25)
            self.training_loop(opt, loss_fn, train_data, max_norm_value=max_norm_value) #self.model, , self.mod_to_train
            # print()
            metrics = self.validation(val_data) # self.model, macro_precision, weighted_precision, cosine_sim, MSE, mod_to_train
            # self.loss.append(losses)
            self.metric[0].append(metrics[0])
            self.metric[1].append(metrics[1])
            # if len(losses) == 1:
            #     print(F"Validation loss: {losses[0]}")
            # elif len(losses) == 2:
            #     print(F"Validation Macro precision: {losses[0]}\nValidation Weighted precision: {losses[1]}")
            # else: raise ValueError()
            self.save_best(metrics[0], metrics[1])
            self.macro_precision.reset()
            self.weighted_precision.reset() 
        return self.model
    
    # def plot_acc

    def plot_loss(
        self, 
        # epochs: int,
        # title: str
    ):
        # plt.figure(figsize=())
        # ax, fig = 
        plt.plot([i+1 for i in range(self.epochs)], self.loss)
        plt.title(f'{self.model._get_name()} Training Loss')
        plt.xlabel('Epochs')
        plt.ylabel(f'{self.loss_name}')
        plt.show()
        # pass

    def plot_metrics(
        self, 
        # epochs: int
    ):
        # plt.plot([i for i in range(epochs)], self.loss)
        fig, ax1 = plt.subplots() #figsize
        # for i, metric in enumerate(self.metric()):
        ax1.plot([j+1 for j in range(self.epochs)], self.metric[0], label=self.metric_names[0], color='tab:red')
        ax1.set_xlabel('Epochs')
        ax1.set_ylabel(self.metric_names[0], color='tab:red') #, color='tab::red'
        ax1.tick_params(axis='y', color='tab:red') # color
        ax2 = ax1.twinx()


        ax2.plot([j+1 for j in range(self.epochs)], self.metric[1], label=self.metric_names[1], color='tab:blue')
        # ax2.set_xlabel('Epochs')
        ax2.set_ylabel(self.metric_names[1], color='tab:blue') #, color='tab::red'
        ax2.tick_params(axis='y', color='tab:blue') # color 

        fig.tight_layout() 
        # plt.title(title) 

        # ax1.ylabel(self.metric_names[0])
        # ax2.ylabel(self.metric_names[1])


        
        # plt.xlabel('Epochs')
        # plt.ylabel(self.loss_name)
        plt.title(f'{self.model._get_name()} Validation Metrics')
        plt.show()

    def save_best(self, metric1, metric2):
        # print(f'met1: {metric1}\nself: {self.best_metric[0]}')
        if (metric1 > self.best_metric[0] and metric2 >= self.best_metric[1]) or (metric2 > self.best_metric[1] and metric1 >= self.best_metric[0]):
            self.best_metric[0] = metric1
            self.best_metric[1] = metric2
            # self.best_mod = self.model.state_dict()
            torch.save(self.model.state_dict(), f'best_models/best_{self.model._get_name()}_model.pt')


    def learned_params(self):
        for name, param in self.model.named_parameters():
            if param.grad is not None: 
                print(name, param.grad)

    def check_preds(self, data):
        self.model.eval()
        with torch.no_grad():
            output = self.model(torch.stack([feat for feat, _, _ in data]))
        print(torch.bincount(torch.argmax(output, dim=1)))

# print([label for feat, label, sent in dev_data])

    
    # def check_preds(self, num_classes, dataloader, mod_to_train): 
    #     macro_precision = Precision(task="multiclass", average="macro", num_classes=num_classes)
    #     weighted_precision = Precision(task="multiclass", average="weighted", num_classes=num_classes)
    #     result = self.validation(
    #         dataloader,
    #         macro_precision,
    #         weighted_precision,
    #         mod_to_train=mod_to_train
    #     )
    #     print(result)