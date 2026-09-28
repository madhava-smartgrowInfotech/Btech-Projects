"""Download PaySim (Kaggle: ealaxi/paysim1, CC BY-SA 4.0) and write a seeded 100k-row sample.

The full 470 MB CSV lands in data/raw/ (git-ignored); the sample in data/sample/ is committed.
Kaggle credentials: set KAGGLE_USERNAME / KAGGLE_KEY in .env (or ~/.kaggle/kaggle.json).
Public datasets can usually be fetched without them.

Usage: python scripts/download_data.py [--rows 100000] [--seed 42]
"""
import argparse
import csv
import glob
import os
import shutil

import numpy as np
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=100000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    load_dotenv(os.path.join(ROOT, ".env"))
    import kagglehub

    path = kagglehub.dataset_download("ealaxi/paysim1")
    src = glob.glob(os.path.join(path, "*.csv"))[0]
    raw_dir = os.path.join(ROOT, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    raw = os.path.join(raw_dir, "paysim.csv")
    if not os.path.exists(raw):
        shutil.copyfile(src, raw)

    with open(raw, newline="") as f:
        total = sum(1 for _ in f) - 1
    keep = set(np.random.default_rng(a.seed).choice(total, min(a.rows, total), replace=False).tolist())
    out = os.path.join(ROOT, "data", "sample", "paysim_sample.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    n_fraud = 0
    with open(raw, newline="") as f, open(out, "w", newline="") as g:
        r, w = csv.reader(f), csv.writer(g)
        w.writerow(next(r))
        for i, row in enumerate(r):
            if i in keep:
                w.writerow(row)
                n_fraud += int(row[9])
    print(f"PaySim rows: {total:,}; sample: {len(keep):,} rows ({n_fraud} fraud) -> {out}")


if __name__ == "__main__":
    main()
