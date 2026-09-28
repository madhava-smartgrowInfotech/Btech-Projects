import torch
from torch import nn


class LeNet(nn.Module):
    """LeNet-style CNN over the 8-channel Haar wavelet stack (8 x 128 x 128)."""

    def __init__(self, in_ch: int = 8):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_ch, 16, 5), nn.BatchNorm2d(16), nn.ReLU(), nn.MaxPool2d(2),  # 62
            nn.Conv2d(16, 32, 5), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),     # 29
            nn.Conv2d(32, 48, 3), nn.BatchNorm2d(48), nn.ReLU(),                      # 27 (Grad-CAM layer)
        )
        self.pool = nn.MaxPool2d(2)                                                   # 13
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Dropout(0.4),
            nn.Linear(48 * 13 * 13, 120), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(120, 84), nn.ReLU(),
            nn.Linear(84, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.pool(self.features(x))).squeeze(1)
