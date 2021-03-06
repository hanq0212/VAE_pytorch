# Referred by https://github.com/EmilienDupont/neural-function-distributions

import json
import os
import sys
import time
import torch
import torch.backends.cudnn as cudnn

from training.training import Trainer
from dataloader.dataloader import mnist, CelebA
from models.vanilla_vae import VanillaVAE


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Get config file from command line arguments
if len(sys.argv) != 2:
    raise(RuntimeError("Wrong arguments, use python main.py <config_path>"))
config_path = sys.argv[1]

# Open config file
with open(config_path) as f:
    config = json.load(f)

if config["path_to_data"] == "":
    raise(RuntimeError("Path to data not specified. Modify path_to_data attribute in config to point to data."))

if config["train"] > 0:
    # Create a folder to store experiment results
    timestamp = time.strftime("%Y-%m-%d_%H-%M")
    directory = "{}_{}".format(timestamp, config["id"])
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Save config file in experiment directory
    with open(directory + '/config.json', 'w') as f:
        json.dump(config, f)

else:
    directory = config["test"]["test_path"]


# For reproducibility
# torch.manual_seed(config["training"]["manual_seed"])
# np.random.seed(config["training"]["manual_seed"])
# cudnn.deterministic = True
cudnn.benchmark = True

# Get config parameters
# Data Loader
if config["dataset"] == "mnist":
    distribution = 'gaussian'
    path_to_data = config["path_to_data"]
    resolution = config["resolution"]
    latent_dim = config["latent_dim"]
    hidden_dims = config["hidden_dims"]
    encoder_configs = config["encoder"]["layer_configs"]
    decoder_configs = config["decoder"]["layer_configs"]
    fc_configs = config["fc_mu_var"]
    training = config["training"]
    test = config["test"]

    if config["train"] > 0:
        train = True
        batch_size = training["batch_size"]
    else:
        train = False
        batch_size = test["batch_size"]

    dataloader, num_train_imgs = mnist(path_to_data = path_to_data, 
                        batch_size = batch_size,
                        size = resolution,
                        train= train, 
                        download = False)
elif config["dataset"] == 'CelebA':
    distribution = 'gaussian'
    path_to_data = config["path_to_data"]
    resolution = config["resolution"]
    latent_dim = config["latent_dim"]
    hidden_dims = config["hidden_dims"]
    encoder_configs = config["encoder"]["layer_configs"]
    decoder_configs = config["decoder"]["layer_configs"]
    fc_configs = config["fc_mu_var"]
    training = config["training"]
    test = config["test"]

    if config["train"] > 0:
        train = True
        batch_size = training["batch_size"]
    else:
        train = False
        batch_size = test["batch_size"]

    dataloader, num_train_imgs = CelebA(path_to_data = path_to_data, 
                        batch_size = batch_size,
                        size = resolution,
                        train= train)

else:
    raise(RuntimeError("Requested Dataset unfounds"))


# Model Construction
if config["model"] == "VanillaVAE":
    VAE = VanillaVAE(encoder_configs, decoder_configs, fc_configs, latent_dim).to(device)
    print("\nVanilla VAE")
    print(VAE)
    print("Number of parameters: {}".format(count_parameters(VAE)))
elif config["model"] == "BetaVAE":
    BetaVAE = VanillaVAE(encoder_configs, decoder_configs, fc_configs, latent_dim).to(device)
    print("\nBetaVAE")
    print(BetaVAE)
    print("Number of parameters: {}".format(count_parameters(BetaVAE)))



#Trainer
trainer = Trainer(device, BetaVAE, distribution,
                name = config["model"], 
                data_loader = dataloader, 
                batch_size = batch_size, 
                num_train_imgs = num_train_imgs,
                kld_weight = training["kld_weight"], 
                directory = directory,
                max_iters = training["max_iters"],
                resume_iters = training["resume_iters"],
                capacity_iters = training["capacity_iters"],
                restored_model_path = training["restored_model_path"],
                beta = training["beta"],
                gamma = training["gamma"],
                max_capacity = training["max_capacity"],
                loss_type = training["loss_type"],
                lr = training["lr"],
                weight_decay = training["weight_decay"],
                beta1 = training["beta1"],
                beta2 = training["beta2"],
                milestones = training["milestones"],
                scheduler_gamma = training["scheduler_gamma"],
                print_freq = training["print_freq"],
                sample_freq = training["sample_freq"],
                model_save_freq = training["model_save_freq"],
                test_iters = test["test_iters"],
                test_dim = test["test_dim"],
                test_seed = test["test_seed"],
                start = test["start"],
                end = test["end"],
                steps = test["steps"])

if train:
    trainer.train()
else:
    trainer.test()