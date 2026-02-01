import torch
from torch.utils.data import Dataset

# import pandas as pd
# pd.set_option('display.max_colwidth', 1000)

def normalize_data(data, traindev_indicies: list): 
    """
    Normalizes the dataset using the subset of data found from the indicies to calculate the mean and standard deviation

    :param Dataset data: Datset to get the values from
    :param list indicies: The values of the subset
    """
    traindev = torch.stack([data.values[i] for i in traindev_indicies])
    mean = torch.mean(traindev, dim=0)
    std = torch.std(traindev, dim=0) + 1e-8
    return (data.values - mean) / std 

def calc_loss_weights(
    data: Dataset,
    alpha: float
):
    """
    Calculates the class weights for the loss function 

    :param Dataloader dataloader: Data from which to calculate the weights 
    :param float alpha: Value by which to scale
    """
    # class_counts = torch.bincount(torch.tensor([int(label) for feats, labels, sents in train_loader for label in labels]))
    # return sum(class_counts) / (len(class_counts) * class_counts)
    # NOTE: view(-1) infers based off dividing the amount by the other dimension 
    # so in this case it will flatten it to the number of objects
    # class_counts = torch.bincount(torch.cat([labels.view(-1) for _, labels, _ in train_loader]))
    class_counts = torch.bincount(torch.tensor(data.labels))
    return (1- torch.pow(alpha, class_counts)) / (1 - alpha)
# maybe add mean 

# def convert_to_dataframe(dataset):
#     """
#     Converts a PyTorch Dataset to a pandas DataFrame.
#     Assumes each item in the dataset is a tuple/list (data, label).
#     """
#     data_list = []
#     # Iterate through the dataset
#     for i in range(len(dataset)):
#         # Retrieve the data and label for each item
#         data, label, sent = dataset[i]
#         # Convert tensors to Python values (if they are tensors)
#         if isinstance(data, torch.Tensor):
#             data = data.detach().numpy()
#         if isinstance(label, torch.Tensor):
#             label = label.detach().numpy()
        
#         # You may need to flatten or format multi-dimensional data/labels
#         # depending on your specific use case. For simple data, this works.
#         # Example for simple numeric data:
#         data_list.append({'Data': data, 'Label': label, 'Sents': sent})
    
#     # Create the DataFrame
#     df = pd.DataFrame(data_list)
#     return df