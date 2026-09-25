"""Self-supervised JEPA pretraining of the seed-image patch encoder on the
synthetic (unlabelled, from the encoder's point of view) image corpus.

Run after generate_dataset.py: `python ml/train_encoder.py`
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset

from app.core.config import DATASET_CSV, DATASET_DIR, EMBEDDING_DIM, ENCODER_WEIGHTS_PATH, IMAGE_SIZE
from app.core.encoder import JepaEncoder
from app.core.feature_extraction import preprocess_for_encoder

EPOCHS = 6
BATCH_SIZE = 64
LR = 2e-3


class SeedImageDataset(Dataset):
    def __init__(self, df: pd.DataFrame, images_dir: Path):
        self.paths = [images_dir / fname for fname in df["image"]]

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        img_bgr = cv2.imread(str(self.paths[idx]))
        chw = preprocess_for_encoder(img_bgr, IMAGE_SIZE)
        return torch.from_numpy(chw)


def main():
    df = pd.read_csv(DATASET_CSV)
    images_dir = DATASET_DIR / "images"
    dataset = SeedImageDataset(df, images_dir)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = JepaEncoder(embed_dim=EMBEDDING_DIM).to(device)
    trainable_params = list(model.context_encoder.parameters()) + list(model.predictor.parameters())
    optimizer = torch.optim.AdamW(trainable_params, lr=LR, weight_decay=1e-4)

    model.train()
    start = time.time()
    for epoch in range(EPOCHS):
        total_loss = 0.0
        n_batches = 0
        for batch in loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            loss = model(batch)
            loss.backward()
            optimizer.step()
            model.update_target()
            total_loss += loss.item()
            n_batches += 1
        avg_loss = total_loss / max(n_batches, 1)
        print(f"epoch {epoch + 1}/{EPOCHS} - jepa loss {avg_loss:.5f} - elapsed {time.time() - start:.1f}s")

    torch.save(model.state_dict(), ENCODER_WEIGHTS_PATH)
    print(f"Saved encoder weights to {ENCODER_WEIGHTS_PATH}")


if __name__ == "__main__":
    main()
