from torch.autograd import Variable
import torch
import torch.nn  as nn
from torchvision.models import alexnet, vgg
import torch.nn.functional as F
import math
import gc
from PIL import Image


class GNet(nn.Module):
    def __init__(self):
        super(GNet, self).__init__()

        self.pad1 = nn.ReflectionPad2d(3)
        self.conv1 = nn.Conv2d(3, 32, 7, 2)
        self.in1 = nn.InstanceNorm2d(32)
        # relu

        self.pad2 = nn.ReflectionPad2d(1)
        self.conv2 = nn.Conv2d(32, 64, 3, 2)
        self.in2 = nn.InstanceNorm2d(64)
        # relu

        self.pad3_1 = nn.ReflectionPad2d(1)
        self.con3_1 = nn.Conv2d(64, 64, 3, 1)

        self.pad3_2 = nn.ReflectionPad2d(1)
        self.con3_2 = nn.Conv2d(64, 64, 3, 1)
        self.in3 = nn.InstanceNorm2d(64)

        self.deconv = nn.Sequential(
            nn.ConvTranspose2d(64, 128, 3, 2, 1, 1, bias=False),
            nn.InstanceNorm2d(128),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(128, 3, 3, 2, 1, 1, bias=False),
            nn.ReflectionPad2d(3),
            nn.Conv2d(3, 3, 7),
            nn.Tanh()
        )
        self._initialize_weights()

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                m.weight.data.normal_(0, 0.01)
                m.bias.data.zero_()

    def forward(self, x):
        y1 = F.relu(self.in1(self.conv1(self.pad1(x))))
        y2 = F.relu(self.in2(self.conv2(self.pad2(y1))))
        y3 = self.in3(self.con3_2(self.pad3_2(self.con3_1(self.pad3_1(y2)))))
        y3_cat_y2 = y2 + y3
        output = self.deconv(y3_cat_y2)
        output = torch.clamp(2 * output + x, -1, 1)
        return output


class Preprocess:
    def __init__(self):
        pass

    def __call__(self, pil_img):
        a, b = pil_img.size
        a, b = int(a * 4), int(b * 4)
        pil_img = pil_img.resize((a, b), Image.BICUBIC)
        return pil_img
