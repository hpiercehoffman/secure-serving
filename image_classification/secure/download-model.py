import torch
from torchvision import models

model = models.resnet18(pretrained=True)
torch.save(model, 'resnet18_pretrained.pth')

print("Model saved successfully as 'resnet18_pretrained.pth'")
