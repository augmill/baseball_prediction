# import sys
# sys.path.append('~/code/baseball_prediction')
# print(sys.path)

from modeling.model import * 
from modeling.utils import *
from modeling.CustomDataset import *
from torch import optim
import optuna
import gc
from optuna.pruners import HyperbandPruner
# from torchmetrics import Precision
from optuna.exceptions import TrialPruned

seed=42
if torch.cuda.is_available():
    device = 'cuda' 
    torch.backends.cudnn.benchmark = True
    torch.cuda.empty_cache()

else: device = 'cpu'

# device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
prep(seed, device=device) #device = 'gpu'
data = make_dataset(
    start_date="2017-01-01", 
    label_col="events"#, 
    #seed=seed
)
print('Loaded')
in_dim = data.__getitem__(1)[0].shape[0] # may need to be 1
out_dim = 384 # rename
# check 8 better when streamlined
batch_size = 128#8, 16, 32, 64, 128
num_classes = data.get_num_classes() + 1
print('Making dataloaders')
train_loader, dev_loader, test_loader = make_loaders(
    data=data, 
    seed=seed,
    batch_size=batch_size
)
print('Made')

# print(next(iter(train_loader))[0].shape)

def objective(trial):
    losses = []
    # macro_precision = Precision(task="multiclass", average="macro", num_classes=num_classes)
    # weighted_precision = Precision(task="multiclass", average="weighted", num_classes=num_classes)  
    # num_heads = trial.suggest_int('num_heads', 1, 10, step=2) #embed (head?) as in dim? dim must be div by num_head
    # NOTE make head dim a new param 

    # # Categorical for specific discrete values
    # batch_size = trial.suggest_categorical('batch_size', [16, 32, 64, 128, 256])

    num_heads = 4 # 1
    ff_dim = 4 * 32

    # ff_dim = trial.suggest_int('ff_dim', 32, 256, step=32) #4 * 32
    convert_drop = trial.suggest_float('convert_drop', 0, 1, log=False)
    convert_trans_drop = trial.suggest_float('convert_trans_drop', 0, 1, log=False)
    # convert_num_layers = trial.suggest_int('convert_num_layers', 1, 10, step=1)
    convert_num_layers = 4
    convert_lr = trial.suggest_float('convert_lr', 1e-3, 1e-1, log=True)
    convert_decay = trial.suggest_float('convert_decay', 1e-10, 1e-1, log=True)
    max_norm_value = 1
    dim_inner = 32 #trial.suggest_int('dim_inner', 64, 512, step=32) # ff * num_heads
    convert_epochs = 5
    sub_convert = Convertion(
        dim_in=in_dim, 
        dim_out=out_dim, 
        in_num_heads=num_heads, 
        in_ff_dim=ff_dim, 
        drop=convert_drop, 
        in_trans_drop=convert_trans_drop,
        in_dim_inner = dim_inner,
        in_num_layers=convert_num_layers,
        out_num_heads=1, 
        out_ff_dim=1,
        out_trans_drop=1
    ).to(device=device)

    sub_convert = torch.compile(sub_convert, mode="reduce-overhead")

    convert_optim = optim.AdamW(params=sub_convert.parameters(), lr=convert_lr, weight_decay=convert_decay) # may want to add weight decay
    convert_loss_fn = nn.CosineEmbeddingLoss()

    # epoch_sims = []
    best_val = -1
    for step in range(convert_epochs):
        # macro_precision.reset()
        # weighted_precision.reset()

        sims = []
        for i, batch in enumerate(train_loader):
            # print(batch[0].shape)
            sub_convert.train()
            # loss = encode_training(batch[0].to(device), batch[2].to(device), opt, max_norm_value, loss_fn) # model, , mod_to_train
            logits = sub_convert(batch[0].to(device))
            loss = convert_loss_fn(logits, nn.functional.normalize(batch[2].to(device)), torch.ones(logits.shape[0])) # + (0.01 * nn.MSELoss(logits, targets))
            # loss = 1 - (targets - logits).sum(dim=1).mean()
            convert_optim.zero_grad()
            loss.backward()
            # gradiant clipping https://docs.pytorch.org/docs/stable/generated/torch.nn.utils.clip_grad_norm_.html
            torch.nn.utils.clip_grad_norm_(sub_convert.parameters(), max_norm=max_norm_value)
            convert_optim.step()
            losses.append(loss.detach().item())

        
        sub_convert.eval()
        with torch.no_grad():
            for batch in dev_loader:
                logits = sub_convert(batch[0].to(device))
                # embeds = batch[2].to(device)
                norm_embeds = nn.functional.normalize(batch[2].to(device))
                # sims.append(nn.functional.cosine_similarity(logits, norm_embeds).mean()) 
                # losses.append(sum(sim)/len(sim))
                sim = nn.functional.cosine_similarity(logits, norm_embeds).mean().detach().item()
                sims.append(sim)
            val = sum(sims)/len(sims)
        print(f'epoch {step+1} sim: {val}')
        if val > best_val: 
            best_val = val
        # epoch_sims.append(val)
        trial.report(val, i)
        if trial.should_prune():
            raise TrialPruned()

    del sub_convert
    gc.collect() 
    torch.cuda.empty_cache()

    # return sum(epoch_sims)/len(epoch_sims)
    return best_val

# Configure the Hyperband Pruner
hyperband_pruner = HyperbandPruner( #optuna.pruners.
    min_resource=1,       # Minimum resource (e.g., epochs) allocated to a trial
    reduction_factor=3    # Factor by which the number of trials is reduced at each stage
)

# study = optuna.create_study(direction='maximize', pruner=hyperband_pruner)
# study.optimize(objective, n_trials=30)

# print("Best hyperparameters:", study.best_trial.params)
# print("Best validation accuracy:", study.best_trial.value)