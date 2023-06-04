import torch
import torch.nn as nn
import torchvision
from torchvision import transforms, utils
from skimage import transform
from torch.utils.data import Dataset, DataLoader
import numpy as np
import matplotlib.pyplot as plt
from IPython.core.pylabtools import figsize
import time
import os
import re
import random
from imageio import imread
from pathlib import Path
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True
# %matplotlib inline

class GlobalCoarseNet(nn.Module):

    def __init__(self, init=True):
        super(GlobalCoarseNet, self).__init__()
# 304 * 228 * 3
        self.coarse1 = nn.Sequential(nn.Conv2d(in_channels=3, out_channels=96, kernel_size=11, stride=4),

                                     nn.ReLU(),
                                     nn.MaxPool2d(kernel_size=2))
# 37 * 27 * 96
        self.coarse2 = nn.Sequential(nn.Conv2d(in_channels=96, out_channels=256, kernel_size=5, padding=2),

                                     nn.ReLU(),
                                     nn.MaxPool2d(kernel_size=2))
# 16 * 11 * 256
        self.coarse3 = nn.Sequential(nn.Conv2d(in_channels=256, out_channels=384, kernel_size=3, padding=1),

                                     nn.ReLU())
# 16 * 11 * 384
        self.coarse4 = nn.Sequential(nn.Conv2d(in_channels=384, out_channels=384, kernel_size=3, padding=1),

                                     nn.ReLU())
# 16 * 11 * 384
        self.coarse5 = nn.Sequential(nn.Conv2d(in_channels=384, out_channels=256, kernel_size=3, padding=1),

                                     nn.ReLU(),
                                     nn.MaxPool2d(kernel_size=2))

        self.coarse6 = nn.Sequential(nn.Linear(in_features=10240, out_features=4096), # 256 * 8 * 5 = 10240
                                     nn.ReLU())
        self.coarse6 = nn.Linear(13824, 4096)

        self.coarse7 = nn.Sequential(nn.Linear(in_features=4096, out_features=4070))
# 74 * 55 = 4070

        if init:
            for m in self.modules():
                if isinstance(m, nn.Conv2d):
                    nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
                    m.bias.data.fill_(0)
                elif isinstance(m, nn.Linear):
                    nn.init.xavier_normal_(m.weight)
                    m.bias.data.fill_(0)



    def forward(self, x):
        x = self.coarse1(x)
        x = self.coarse2(x)
        x = self.coarse3(x)
        x = self.coarse4(x)
        x = self.coarse5(x)
        x = x.reshape(x.size(0), -1)
        x = self.coarse6(x)
        x = self.coarse7(x)
        x = x.reshape(x.size(0), 74, 55)
        return x


class LocalFineNet(nn.Module):

    def __init__(self, init=True):
        super(LocalFineNet, self).__init__()
# 304 * 228 * 3
        self.fine1 = nn.Sequential(nn.Conv2d(in_channels=3, out_channels=63, kernel_size=9, stride=2),

                                   nn.ReLU(),
                                   nn.MaxPool2d(kernel_size=2))
# 74 * 55 * 63
        self.fine2 = nn.Sequential(nn.Conv2d(in_channels=64, out_channels=64, kernel_size=5, padding=2),

                                   nn.ReLU())
# 74 * 55 * 64
        self.fine3 = nn.Conv2d(in_channels=64, out_channels=1, kernel_size=5, padding=2)
#
        if init:
            for m in self.modules():
                if isinstance(m, nn.Conv2d):
                    nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
                    m.bias.data.fill_(0)
                elif isinstance(m, nn.Linear):
                    nn.init.xavier_normal_(m.weight)
                    m.bias.data.fill_(0)

    def forward(self, x, global_output_batch):
        x = self.fine1(x)
        x = torch.cat((x, global_output_batch), dim=1)
        x = self.fine2(x)
        x = self.fine3(x)

        return x