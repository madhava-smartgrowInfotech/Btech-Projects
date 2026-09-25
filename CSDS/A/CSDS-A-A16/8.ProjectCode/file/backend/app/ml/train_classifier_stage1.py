"""Stage 1: train the basic 7-class CNN backbone on real FER2013 images.
Run from backend/: python -m app.ml.train_classifier_stage1
"""
import time

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from app.config import CHECKPOINT_DIR
from app.ml.classifier_model import EmotionCNN
from app.ml.dataset import class_weights, load_split
from app.ml.taxonomy import NUM_BASIC

CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
DEVICE = torch.device("cpu")


def to_tensor(images: np.ndarray) -> torch.Tensor:
    x = images.astype(np.float32) / 255.0
    x = (x - 0.5) / 0.5
    return torch.from_numpy(x).unsqueeze(1)  # N x 1 x H x W


def main(epochs: int = 5, batch_size: int = 256, lr: float = 1e-3):
    print("Loading FER2013 train/test splits...")
    train_imgs, train_labels = load_split("train.pt")
    test_imgs, test_labels = load_split("test.pt")
    print(f"train={len(train_imgs)} test={len(test_imgs)}")

    train_ds = TensorDataset(to_tensor(train_imgs), torch.from_numpy(train_labels))
    test_ds = TensorDataset(to_tensor(test_imgs), torch.from_numpy(test_labels))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=256)

    weights = torch.from_numpy(class_weights(train_labels))
    model = EmotionCNN(out_dim=NUM_BASIC).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        model.train()
        total_loss = 0.0
        for xb, yb in train_loader:
            optimizer.zero_grad()
            out = model(xb)
            loss = criterion(out, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * xb.size(0)
        train_loss = total_loss / len(train_ds)

        model.eval()
        correct = 0
        with torch.no_grad():
            for xb, yb in test_loader:
                pred = model(xb).argmax(dim=1)
                correct += (pred == yb).sum().item()
        val_acc = correct / len(test_ds)
        print(f"epoch {epoch}/{epochs} loss={train_loss:.4f} val_acc={val_acc:.4f} ({time.time()-t0:.1f}s)")

    ckpt_path = CHECKPOINT_DIR / "stage1_backbone.pt"
    torch.save(model.state_dict(), ckpt_path)
    print(f"Saved {ckpt_path}")

    log_path = CHECKPOINT_DIR / "training_log.txt"
    with log_path.open("a") as f:
        f.write(f"[stage1 basic classifier] train={len(train_imgs)} test={len(test_imgs)} "
                f"epochs={epochs} final_val_acc={val_acc:.4f}\n")

    return val_acc


if __name__ == "__main__":
    main()
