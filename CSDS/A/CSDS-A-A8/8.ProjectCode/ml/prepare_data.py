"""Prepare the LGG brain-MRI data.

Reads the Kaggle LGG folders (data/raw/lgg/kaggle_3m/<patient>/*.tif), resizes every slice to 128x128,
splits by patient (seeded 80/20) and writes:
  data/raw/lgg128.npz          full arrays for training (git-ignored)
  data/sample/lgg/*.png        ~200 committed sample slices (256x256 originals + masks) from test patients
  data/sample/lgg/manifest.csv

If the full dataset is not present, run scripts/download_data.py first.
"""
import csv
import os
import random
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(os.getenv("BIOSIGHT_ROOT", Path(__file__).resolve().parents[1]))
RAW = Path(os.getenv("LGG_RAW", ROOT / "data" / "raw" / "lgg" / "kaggle_3m"))
OUT = ROOT / "data" / "raw" / "lgg128.npz"
SAMPLE = ROOT / "data" / "sample" / "lgg"
SEED = 42
SIZE = 128


def main():
    patients = sorted(p for p in RAW.iterdir() if p.is_dir())
    rng = random.Random(SEED)
    order = patients[:]
    rng.shuffle(order)
    n_test = int(round(0.2 * len(order)))
    test_ids = {p.name for p in order[:n_test]}

    xs, ys, pid, split, src = [], [], [], [], []
    for p in patients:
        for img_path in sorted(p.glob("*.tif")):
            if img_path.stem.endswith("_mask"):
                continue
            mask_path = img_path.with_name(img_path.stem + "_mask.tif")
            if not mask_path.exists():
                continue
            img = Image.open(img_path).convert("RGB")
            mask = Image.open(mask_path).convert("L")
            xs.append(np.asarray(img.resize((SIZE, SIZE), Image.BILINEAR), dtype=np.uint8))
            ys.append((np.asarray(mask.resize((SIZE, SIZE), Image.NEAREST)) > 127).astype(np.uint8))
            pid.append(p.name)
            split.append("test" if p.name in test_ids else "train")
            src.append(str(img_path.relative_to(RAW)))

    X, Y = np.stack(xs), np.stack(ys)
    split = np.array(split)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT, X=X, Y=Y, patient=np.array(pid), split=split, src=np.array(src))
    pos = Y.reshape(len(Y), -1).max(1) > 0
    print(f"slices={len(X)} train={int((split == 'train').sum())} test={int((split == 'test').sum())} "
          f"tumour-positive={int(pos.sum())} patients={len(patients)} test_patients={n_test}")

    # committed sample: 140 tumour-positive + 60 negative slices from test patients
    SAMPLE.mkdir(parents=True, exist_ok=True)
    test_idx = np.where(split == "test")[0]
    pos_idx = [i for i in test_idx if pos[i]]
    neg_idx = [i for i in test_idx if not pos[i]]
    rng2 = random.Random(SEED)
    chosen = sorted(rng2.sample(pos_idx, min(140, len(pos_idx))) + rng2.sample(neg_idx, min(60, len(neg_idx))))
    with open(SAMPLE / "manifest.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "mask_file", "patient", "source_slice", "tumour_pixels_256"])
        for i in chosen:
            s = Path(src[i])
            name = s.stem
            img = Image.open(RAW / s).convert("RGB")
            mask = Image.open(RAW / s.with_name(s.stem + "_mask.tif")).convert("L")
            img.save(SAMPLE / f"{name}.png", optimize=True)
            mask.save(SAMPLE / f"{name}_mask.png", optimize=True)
            w.writerow([f"{name}.png", f"{name}_mask.png", pid[i], str(s).replace("\\", "/"),
                        int((np.asarray(mask) > 127).sum())])
    print(f"sample slices written: {len(chosen)} -> {SAMPLE}")


if __name__ == "__main__":
    main()
