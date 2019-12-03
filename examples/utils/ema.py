import sys;

sys.path.append("../../")

import torch
from torch import nn
import torch.nn.functional as F
import torchvision
from booster.evaluation import Classification
from booster.pipeline import Pipeline
from booster.training import training_step, validation_step
from booster.utils import EMA

# load data
dataset = torchvision.datasets.MNIST('../../data', train=True, download=True,
                                     transform=torchvision.transforms.ToTensor())
loader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True)


# define model
class Classifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return x

# init model and evaluator
model = Classifier()
ema = EMA(model, 0.9995)
evaluator = Classification(10)

# fuse model + evaluator
pipeline = Pipeline(model, evaluator)
eval_pipeline = Pipeline(ema.model, evaluator)

# optimizer
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

# evaluate model
data = next(iter(loader))
diagnostics = training_step(pipeline, data, optimizer, 0, ema=ema)
diagnostics = validation_step(eval_pipeline, data)

print(diagnostics)
