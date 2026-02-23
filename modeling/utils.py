import torch
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from torch.utils.data import WeightedRandomSampler

def prep(seed: int, device: str = 'cpu') -> torch.Generator:
    """Seeds all relevant parts of the process and sets default torch dtype and returns a torch generator"""
    torch.set_default_device(device)
    torch.manual_seed(seed)
    torch.set_num_threads(4)
    # random.seed(seed) #NOTE: may be unnecessary 
    g = torch.Generator().manual_seed(seed) #NOTE: may be unnecessary
    torch.set_default_dtype(torch.float32) 
    return g


def count_classes(
    data: Dataset
) -> torch.Tensor:
    """
    Counts the number of instances of each class 

    :param data: Raw dataset to count classes from

    :return `torch.Tensor': Class counts
    """
    torch_counts = torch.bincount(torch.tensor(data.labels))
    # print(torch_counts)
    return torch_counts


def make_sampler_weights(
    data: Dataset,
    alpha: float = 0.5
) -> torch.Tensor:
    """
    Calculates the class weights for sampling 

    :param float: alpha: Alpha value for the class weights calculation

    :return `torch.Tensor': Weights for sampling
    """
    torch_weights = (1.0 / count_classes(data).float()) ** alpha
    # print(torch_weights)
    return torch_weights[data.labels]


def normalize_data(data: Dataset, traindev_indicies: list) -> torch.Tensor: 
    """
    Normalizes all of the dataset's input using a subset of data found from the indicies of the non-test inputs 
    to calculate the mean and standard deviation that is applied to have a z-score normalization

    :param Dataset data: Datset to get the values from
    :param list indicies: The values of the subset

    :return `torch.Tensor`: Dataset's normalized input  
    """
    local_data = data
    traindev = torch.stack([local_data.values[i] for i in traindev_indicies])
    mean = torch.mean(traindev, dim=0)
    std = torch.std(traindev, dim=0) + 1e-8
    return (local_data.values - mean) / std 


def make_loaders(
    data: Dataset,
    seed: int,
    batch_size: int,
    splits: list = [0.1, 0.11111111],
    shuffled: bool = True,
    # sample_weights: list = None,
    sampled: bool = False #,
    # gen: torch.Generator = None
) -> tuple: 
    """
    Creates the `DataLoader` objects for train, validation, and test

    :param Dataset data: Dataset to make the DataLoaders from
    :param int seed: Seed for reproducability
    :param batch_size: Batch size for the DataLoader
    :param list, optional splits: Splits for the train/dev set and the test set and then for the train 
    and dev sets (defaults to 0.1 and 0.11111111 meaning the test set is 10% of orginal dataset and then the dev set is about 10% of original as it is 11.111111% of the train and dev 90% from the first split)
    :param bool, optional shuffled: Whether or not the DataLoaders should shuffle, defaults to `True`
    :param bool, optional sampled: Whether or not a `WeightedRandomSampler` should be made and passed to the 
    Dataloader where replacement is `True` and the train sample will be reduced to 800000 samples

    :return tuple: Train, validation, and test sets
    """

    local_data = data

    traindev_indicies, test_indicies = train_test_split(
        list(range(len(local_data))), 
        test_size=splits[0], # 0.1
        stratify=local_data.labels,
        shuffle=shuffled,
        random_state=seed
    )

    local_data.values = normalize_data(local_data, traindev_indicies)

    train_indicies, dev_indicies = train_test_split(
        traindev_indicies, 
        test_size=splits[1], # 0.11111111
        stratify= [local_data.labels[i] for i in traindev_indicies],
        shuffle=shuffled,
        random_state=seed
    )

    train_data = torch.utils.data.Subset(local_data, train_indicies)
    dev_data = torch.utils.data.Subset(local_data, dev_indicies)
    test_data = torch.utils.data.Subset(local_data, test_indicies)

    if not sampled:
        train_loader = DataLoader(train_data, batch_size=batch_size) 
        dev_loader = DataLoader(dev_data, batch_size=batch_size) 
        test_loader = DataLoader(test_data, batch_size=batch_size) 

    else:
        sample_weights = make_sampler_weights(local_data)
        train_weights = sample_weights[train_indicies]
        train_sampler = WeightedRandomSampler(train_weights, num_samples=800000, replacement=True)
        # dev_weights = sample_weights[dev_indicies]
        # dev_sampler = WeightedRandomSampler(dev_weights, num_samples=100000, replacement=True)
        # test_weights = sample_weights[test_indicies]
        # test_sampler = WeightedRandomSampler(test_weights, num_samples=100000)
        train_loader = DataLoader(train_data, batch_size=batch_size, sampler=train_sampler) 
        # dev_loader = DataLoader(dev_data, batch_size=batch_size, sampler=dev_sampler) 
        # test_loader = DataLoader(test_data, batch_size=batch_size, sampler=test_sampler)
        dev_loader = DataLoader(dev_data, batch_size=batch_size) 
        test_loader = DataLoader(test_data, batch_size=batch_size)

    return train_loader, dev_loader, test_loader


def calc_loss_weights(
    data: Dataset,
    alpha: float, 
    normalize: bool = False
) -> torch.Tensor:
    """
    Calculates the class weights for the loss function 

    :param Dataloader dataloader: Data from which to calculate the weights 
    :param float alpha: Value by which to scale
    :param bool normalize: Whether or not to do mean normalization to the weights

    :return `torch.Tensor`: Class loss weights
    """
    # NOTE: view(-1) infers based off dividing the amount by the other dimension 
    # so in this case it will flatten it to the number of objects
    class_counts = torch.bincount(torch.tensor(data.labels))
    weights = (1- torch.pow(alpha, class_counts)) / (1 - alpha)
    if not normalize: return weights
    else: return weights
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