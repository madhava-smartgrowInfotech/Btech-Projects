"""cEmoGAN-style conditional GAN: learns to generate a 64x64 face conditioned on
an emotion vector. Trained on a balanced subset of real FER2013 images (capped per
class for CPU speed). Run from backend/: python -m app.ml.train_gan
"""
import time

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from app.config import CHECKPOINT_DIR
from app.ml.dataset import load_split
from app.ml.gan_model import ConditionalDiscriminator, ConditionalGenerator, NOISE_DIM
from app.ml.taxonomy import NUM_BASIC

CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
DEVICE = torch.device("cpu")


def to_tensor(images: np.ndarray) -> torch.Tensor:
    x = images.astype(np.float32) / 255.0
    x = (x - 0.5) / 0.5
    return torch.from_numpy(x).unsqueeze(1)


def one_hot(labels: np.ndarray) -> torch.Tensor:
    return torch.nn.functional.one_hot(torch.from_numpy(labels), NUM_BASIC).float()


def main(epochs: int = 10, batch_size: int = 64, lr: float = 2e-4, cap_per_class: int = 400):
    print("Loading balanced subset for GAN training...")
    imgs, labels = load_split("train.pt", cap_per_class=cap_per_class)
    print(f"GAN training samples: {len(imgs)}")

    ds = TensorDataset(to_tensor(imgs), one_hot(labels))
    loader = DataLoader(ds, batch_size=batch_size, shuffle=True, drop_last=True)

    G = ConditionalGenerator(cond_dim=NUM_BASIC).to(DEVICE)
    D = ConditionalDiscriminator(cond_dim=NUM_BASIC).to(DEVICE)
    opt_g = torch.optim.Adam(G.parameters(), lr=lr, betas=(0.5, 0.999))
    opt_d = torch.optim.Adam(D.parameters(), lr=lr, betas=(0.5, 0.999))
    bce = nn.BCEWithLogitsLoss()

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        d_loss_total = g_loss_total = 0.0
        for real_imgs, cond in loader:
            bs = real_imgs.size(0)
            real_labels = torch.full((bs, 1), 0.9)
            fake_labels = torch.zeros((bs, 1))

            # --- Discriminator ---
            z = torch.randn(bs, NOISE_DIM)
            fake_imgs = G(z, cond).detach()
            d_real = D(real_imgs, cond)
            d_fake = D(fake_imgs, cond)
            d_loss = bce(d_real, real_labels) + bce(d_fake, fake_labels)
            opt_d.zero_grad()
            d_loss.backward()
            opt_d.step()

            # --- Generator ---
            z = torch.randn(bs, NOISE_DIM)
            gen_imgs = G(z, cond)
            g_pred = D(gen_imgs, cond)
            g_loss = bce(g_pred, torch.full((bs, 1), 0.9))
            opt_g.zero_grad()
            g_loss.backward()
            opt_g.step()

            d_loss_total += d_loss.item()
            g_loss_total += g_loss.item()

        n_batches = len(loader)
        print(f"epoch {epoch}/{epochs} d_loss={d_loss_total/n_batches:.4f} "
              f"g_loss={g_loss_total/n_batches:.4f} ({time.time()-t0:.1f}s)")

    g_path = CHECKPOINT_DIR / "generator.pt"
    torch.save(G.state_dict(), g_path)
    print(f"Saved {g_path}")

    log_path = CHECKPOINT_DIR / "training_log.txt"
    with log_path.open("a") as f:
        f.write(f"[cEmoGAN] samples={len(imgs)} epochs={epochs} "
                f"final_d_loss={d_loss_total/n_batches:.4f} final_g_loss={g_loss_total/n_batches:.4f}\n")


if __name__ == "__main__":
    main()
