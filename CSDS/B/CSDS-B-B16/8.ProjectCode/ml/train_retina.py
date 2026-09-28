"""Train the LeNet hypertensive-retinopathy classifier on 2-level Haar wavelet sub-bands (CPU).

Usage: python ml/train_retina.py [--epochs 60]
Outputs: models/lenet_hr.pt, models/lenet_hr.json, experiments/retina/metrics.json, experiments/retina/split.json
"""
import argparse
import time
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, Dataset

from common import ROOT, SEED, binary_metrics, hr_image_dir, hr_label_csv, write_json, youden_threshold

from app.services.lenet import LeNet
from app.services.preprocess import preprocess
from app.services.wavelet import feature_stack

CACHE = ROOT / "data" / "raw" / "cache_hr_256.npz"
EXP = ROOT / "experiments" / "retina"


def _prep(path: str):
    pre = preprocess(cv2.imread(path, cv2.IMREAD_COLOR))
    q = pre["quality"]
    return pre["input"].astype(np.float16), (q["sharpness"], q["brightness"], q["clipped_fraction"])


def load_cache(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    if CACHE.exists():
        z = np.load(CACHE, allow_pickle=True)
        if list(z["names"]) == list(df["Image"]):
            return z["x"], z["q"]
    img_dir = hr_image_dir()
    paths = [str(img_dir / n) for n in df["Image"]]
    t = time.time()
    with ProcessPoolExecutor() as ex:
        out = list(ex.map(_prep, paths, chunksize=8))
    x = np.stack([o[0] for o in out])
    q = np.array([o[1] for o in out], dtype=np.float32)
    np.savez(CACHE, x=x, q=q, names=np.array(df["Image"]))
    print(f"Preprocessed {len(paths)} images in {time.time() - t:.0f}s")
    return x, q


class WaveletSet(Dataset):
    def __init__(self, x, y, augment: bool):
        self.x, self.y, self.augment = x, y, augment
        self.rng = np.random.default_rng(SEED)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        img = self.x[i].astype(np.float32)
        if self.augment:
            if self.rng.random() < 0.5:
                img = img[:, ::-1]
            angle = self.rng.uniform(-20, 20)
            scale = self.rng.uniform(0.95, 1.08)
            m = cv2.getRotationMatrix2D((128, 128), angle, scale)
            img = cv2.warpAffine(np.ascontiguousarray(img), m, (256, 256), borderValue=float(img.min()))
            img = img * self.rng.uniform(0.9, 1.1) + self.rng.normal(0, 0.03, img.shape).astype(np.float32)
        return torch.from_numpy(feature_stack(np.ascontiguousarray(img))), torch.tensor(float(self.y[i]))


@torch.no_grad()
def predict(model, loader) -> np.ndarray:
    model.eval()
    return np.concatenate([torch.sigmoid(model(xb)).numpy() for xb, _ in loader])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=60)
    args = ap.parse_args()
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    torch.set_num_threads(max(1, torch.get_num_threads()))

    df = pd.read_csv(hr_label_csv())
    df.columns = ["Image", "label"]
    x, q = load_cache(df)
    y = df["label"].to_numpy()

    idx = np.arange(len(y))
    tr, rest = train_test_split(idx, test_size=0.3, stratify=y, random_state=SEED)
    va, te = train_test_split(rest, test_size=0.5, stratify=y[rest], random_state=SEED)
    write_json(EXP / "split.json", {"train": df["Image"].iloc[tr].tolist(), "val": df["Image"].iloc[va].tolist(),
                                    "test": df["Image"].iloc[te].tolist()})

    qs = {name: {p: round(float(np.percentile(q[:, k], p)), 2) for p in (1, 5, 50, 95, 99)}
          for k, name in enumerate(["sharpness", "brightness", "clipped_fraction"])}
    print("Quality stats (percentiles):", qs)

    train_dl = DataLoader(WaveletSet(x[tr], y[tr], True), batch_size=32, shuffle=True)
    val_dl = DataLoader(WaveletSet(x[va], y[va], False), batch_size=64)
    test_dl = DataLoader(WaveletSet(x[te], y[te], False), batch_size=64)

    model = LeNet()
    pos_weight = torch.tensor((y[tr] == 0).sum() / max(1, (y[tr] == 1).sum()), dtype=torch.float32)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    best_auc, best_state, history = -1.0, None, []
    t0 = time.time()
    for ep in range(1, args.epochs + 1):
        model.train()
        total = 0.0
        for xb, yb in train_dl:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            total += loss.item() * len(yb)
        sched.step()
        vp = predict(model, val_dl)
        vm = binary_metrics(y[va], vp)
        history.append({"epoch": ep, "train_loss": round(total / len(tr), 4), "val_auc": vm["roc_auc"],
                        "val_accuracy": vm["accuracy"]})
        print(f"epoch {ep:2d} loss {total / len(tr):.4f} val_auc {vm['roc_auc']:.3f} val_acc {vm['accuracy']:.3f}"
              f" ({time.time() - t0:.0f}s)")
        if vm["roc_auc"] > best_auc:
            best_auc = vm["roc_auc"]
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    vp = predict(model, val_dl)
    threshold = youden_threshold(y[va], vp)
    test_metrics = binary_metrics(y[te], predict(model, test_dl), threshold)

    (ROOT / "models").mkdir(exist_ok=True)
    torch.save(best_state, ROOT / "models" / "lenet_hr.pt")
    write_json(ROOT / "models" / "lenet_hr.json", {
        "architecture": "LeNet (3 conv + 3 FC) on 8-channel 2-level Haar wavelet stack, 128x128",
        "input": "CLAHE green channel, 256x256, per-image standardised",
        "threshold": round(threshold, 4), "best_val_auc": best_auc, "epochs": args.epochs, "optimizer": "Adam",
    })
    write_json(EXP / "metrics.json", {
        "model": "LeNet on Haar wavelet sub-bands",
        "dataset": "Hypertension & Hypertensive Retinopathy Dataset (HRDC task 2), 712 fundus images",
        "split": {"train": len(tr), "val": len(va), "test": len(te)},
        "epochs": args.epochs, "train_seconds": round(time.time() - t0, 1),
        "threshold": round(threshold, 4), "best_val_auc": best_auc,
        "test": test_metrics, "history": history, "quality_stats": qs,
    })
    print("Test:", {k: v for k, v in test_metrics.items() if k != "roc_curve"})


if __name__ == "__main__":
    main()
