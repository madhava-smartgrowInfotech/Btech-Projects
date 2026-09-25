"""Stage 2 (final): trains the 18-label multi-label classifier on real basic-labeled
FER2013 images UNION synthetic compound-labeled images from the trained cEmoGAN.
Feature-extractor weights are initialized from the stage 1 backbone (transfer
learning) before fine-tuning the full network on the combined dataset.
Run from backend/: python -m app.ml.train_final_classifier
"""
import time

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from app.config import CHECKPOINT_DIR, CLASSIFIER_CHECKPOINT
from app.ml.classifier_model import EmotionCNN
from app.ml.dataset import load_split
from app.ml.synthesize_compound import load_generator, synthesize
from app.ml.taxonomy import ALL_LABELS, BASIC_EMOTIONS, NUM_LABELS

DEVICE = torch.device("cpu")


def to_tensor(images: np.ndarray) -> torch.Tensor:
    x = images.astype(np.float32) / 255.0
    x = (x - 0.5) / 0.5
    return torch.from_numpy(x).unsqueeze(1)


def real_to_multihot(labels: np.ndarray) -> np.ndarray:
    """labels are basic-class indices 0..6 -> 18-dim vector with only that basic bit set."""
    out = np.zeros((len(labels), NUM_LABELS), dtype=np.float32)
    out[np.arange(len(labels)), labels] = 1.0
    return out


def main(epochs: int = 5, batch_size: int = 256, lr: float = 5e-4, synth_per_class: int = 200):
    print("Loading real FER2013 data...")
    train_imgs, train_labels = load_split("train.pt")
    test_imgs, test_labels = load_split("test.pt")

    print("Synthesizing compound-emotion training data from cEmoGAN...")
    generator = load_generator()
    synth_imgs, synth_labels = synthesize(generator, n_per_class=synth_per_class)

    real_multihot = real_to_multihot(train_labels)
    combined_imgs = np.concatenate([train_imgs, synth_imgs], axis=0)
    combined_labels = np.concatenate([real_multihot, synth_labels], axis=0)
    print(f"combined training set: {len(combined_imgs)} (real={len(train_imgs)} synthetic={len(synth_imgs)})")

    train_ds = TensorDataset(to_tensor(combined_imgs), torch.from_numpy(combined_labels))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    test_ds = TensorDataset(to_tensor(test_imgs), torch.from_numpy(test_labels))
    test_loader = DataLoader(test_ds, batch_size=256)

    model = EmotionCNN(out_dim=NUM_LABELS).to(DEVICE)
    backbone_path = CHECKPOINT_DIR / "stage1_backbone.pt"
    if backbone_path.exists():
        backbone_state = torch.load(backbone_path, map_location=DEVICE)
        feature_state = {k: v for k, v in backbone_state.items() if k.startswith("features.")}
        model.load_state_dict(feature_state, strict=False)
        print("Initialized feature extractor from stage1 backbone.")

    criterion = nn.BCEWithLogitsLoss()
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

        # Validation: top-1 predicted BASIC label vs real ground truth (only basic
        # labels exist in the real test set; compound bits have no ground truth here).
        model.eval()
        correct = 0
        basic_idx = list(range(len(BASIC_EMOTIONS)))
        with torch.no_grad():
            for xb, yb in test_loader:
                probs = torch.sigmoid(model(xb))
                pred = probs[:, basic_idx].argmax(dim=1)
                correct += (pred == yb).sum().item()
        val_acc = correct / len(test_ds)
        print(f"epoch {epoch}/{epochs} loss={train_loss:.4f} basic_val_acc={val_acc:.4f} ({time.time()-t0:.1f}s)")

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), CLASSIFIER_CHECKPOINT)
    print(f"Saved {CLASSIFIER_CHECKPOINT}")

    log_path = CHECKPOINT_DIR / "training_log.txt"
    with log_path.open("a") as f:
        f.write(f"[final 18-label classifier] real={len(train_imgs)} synthetic={len(synth_imgs)} "
                f"epochs={epochs} labels={ALL_LABELS} final_basic_val_acc={val_acc:.4f}\n")

    return val_acc


if __name__ == "__main__":
    main()
