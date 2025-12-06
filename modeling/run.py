from modeling.CustomDataset import * 
from modeling.model import *

seed = 42
torch.manual_seed(seed)
random.seed(seed) #NOTE: may be unnecessary 
torch.set_default_dtype(torch.float64) 
pd.options.mode.chained_assignment = None

in_date = "2017-01-01" 
train_data, dev_data, test_data, num_classes, class_weights = make_datasets(in_date, "events", seed)

in_dim = train_data.__getitem__(1)[0].shape[0] # may need to be 1
out_dim = 384 # rename
num_heads = 2 # check 8 better when streamlined
ff_dim = int((in_dim * (2/3)) + out_dim)
drop = 0.5

epochs = 10
batch_size = 128#8, 16, 32, 64, 128

train_loader = DataLoader(train_data, batch_size=batch_size)
dev_loader = DataLoader(dev_data, batch_size=batch_size) 
test_loader = DataLoader(test_data, batch_size=batch_size)

num_heads = 2 
ff_dim = int((in_dim * (2/3)) + out_dim)
convert_drop = 0 # 0.5 for non-cosine 
sub_convert = Convertion(in_dim, out_dim, num_heads, ff_dim, convert_drop)
convert_lr = 1e-3 
convert_decay = 1e-4
convert_optim = optim.AdamW(params=sub_convert.parameters(), lr=convert_lr, weight_decay=convert_decay) # may want to add weight decay
convert_loss_fn = nn.CosineEmbeddingLoss() 
sub_convert = fit(
    sub_convert, 
    convert_optim, 
    convert_loss_fn, 
    train_loader, 
    dev_loader, 
    num_classes, 
    5, 
    mod_to_train=4)

sub_in = (out_dim + in_dim)
sub_drop = 0.3
sub_class = Classification(sub_in, num_classes, sub_drop)
class_lr = 1e-3 
class_decay = 1e-4
class_optim = optimizer = optim.AdamW(params = sub_class.parameters(), lr=class_lr, weight_decay=class_decay) 
class_loss_fn = nn.CrossEntropyLoss(weight = class_weights) 
sub_class = fit(
    model=sub_class, 
    opt=class_optim, 
    loss_fn=class_loss_fn, 
    train_data=train_loader, 
    val_data=dev_loader, 
    num_classes=num_classes,
    epochs=2, 
    mod_to_train=2)

model = Multi(sub_convert, sub_class, drop, concat=False) #in_dim, sub_class, False
print(f"Model parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad)}")

lr = 1e-4
class_decay = 1e-4

optimizer = optim.AdamW(params = model.parameters(), lr=lr, weight_decay=class_decay) 
loss_fn = nn.CrossEntropyLoss(weight = class_weights)
model = fit(model, optimizer, loss_fn, train_loader, dev_loader, num_classes, 10)

# classification for just game state
game_drop = 0.3
game_class = Classification(in_dim, num_classes, game_drop) 
game_lr = 1e-3
game_decay = 1e-4
game_optim = optimizer = optim.AdamW(params = game_class.parameters(), lr=game_lr, weight_decay=game_decay) 
game_loss_fn = nn.CrossEntropyLoss(weight = class_weights) 
game_class = fit(
    model=game_class, 
    opt=game_optim, 
    loss_fn=game_loss_fn, 
    train_data=train_loader, 
    val_data=dev_loader, 
    num_classes=num_classes,
    epochs=5, 
    mod_to_train=0)
