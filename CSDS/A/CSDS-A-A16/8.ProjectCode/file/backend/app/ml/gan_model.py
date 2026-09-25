import torch
import torch.nn as nn

NOISE_DIM = 100


class ConditionalGenerator(nn.Module):
    """cEmoGAN-style generator: noise z + emotion condition vector -> 64x64 face.
    The condition is a soft vector over the 7 basic emotions; a blended condition
    (two active components) is used to synthesize compound-expression faces."""

    def __init__(self, cond_dim: int, noise_dim: int = NOISE_DIM):
        super().__init__()
        in_dim = noise_dim + cond_dim
        self.net = nn.Sequential(
            nn.ConvTranspose2d(in_dim, 256, 4, 1, 0), nn.BatchNorm2d(256), nn.ReLU(True),   # 4x4
            nn.ConvTranspose2d(256, 128, 4, 2, 1), nn.BatchNorm2d(128), nn.ReLU(True),       # 8x8
            nn.ConvTranspose2d(128, 64, 4, 2, 1), nn.BatchNorm2d(64), nn.ReLU(True),         # 16x16
            nn.ConvTranspose2d(64, 32, 4, 2, 1), nn.BatchNorm2d(32), nn.ReLU(True),          # 32x32
            nn.ConvTranspose2d(32, 1, 4, 2, 1), nn.Tanh(),                                    # 64x64
        )

    def forward(self, z, cond):
        x = torch.cat([z, cond], dim=1).unsqueeze(-1).unsqueeze(-1)
        return self.net(x)


class ConditionalDiscriminator(nn.Module):
    def __init__(self, cond_dim: int):
        super().__init__()
        self.cond_dim = cond_dim
        self.img_net = nn.Sequential(
            nn.Conv2d(1, 32, 4, 2, 1), nn.LeakyReLU(0.2, True),                # 32x32
            nn.Conv2d(32, 64, 4, 2, 1), nn.BatchNorm2d(64), nn.LeakyReLU(0.2, True),  # 16x16
            nn.Conv2d(64, 128, 4, 2, 1), nn.BatchNorm2d(128), nn.LeakyReLU(0.2, True),  # 8x8
            nn.Conv2d(128, 256, 4, 2, 1), nn.BatchNorm2d(256), nn.LeakyReLU(0.2, True),  # 4x4
        )
        self.cond_proj = nn.Linear(cond_dim, 4 * 4)
        self.out = nn.Linear(256 * 4 * 4 + 4 * 4, 1)

    def forward(self, img, cond):
        feat = self.img_net(img).flatten(1)
        cond_flat = self.cond_proj(cond)
        return self.out(torch.cat([feat, cond_flat], dim=1))
