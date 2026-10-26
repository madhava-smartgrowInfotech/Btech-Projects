"""Build a class-balanced CIFAKE subset in the folder layout the training scripts expect.

Source: CIFAKE (Bird & Lotfi, 2023) via the Hugging Face mirror
`dragonintelligence/CIFAKE-image-dataset` (100,000 train / 20,000 test, 32x32 JPEG,
mirror labels 0 = FAKE, 1 = REAL). Train and validation are drawn without overlap from the
official train split; the test subset comes only from the official test split.

  python scripts/prepare_cifake.py --train-per-class 3000 --val-per-class 600 --test-per-class 1000
"""
import argparse
import io
import os

import numpy as np
import pandas as pd
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "cifake_raw")
OUT = os.path.join(BASE, "data", "cifake")
MIRROR_FAKE, MIRROR_REAL = 0, 1


def dump(df, idx, split, cls, start=0):
    folder = os.path.join(OUT, split, cls)
    os.makedirs(folder, exist_ok=True)
    for n, i in enumerate(idx):
        Image.open(io.BytesIO(df.iloc[i]["image"]["bytes"])).convert("RGB").save(
            os.path.join(folder, f"{cls}_{start + n:05d}.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-per-class", type=int, default=3000)
    ap.add_argument("--val-per-class", type=int, default=600)
    ap.add_argument("--test-per-class", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = np.random.RandomState(args.seed)

    train_df = pd.read_parquet(os.path.join(RAW, "train.parquet"))
    test_df = pd.read_parquet(os.path.join(RAW, "test.parquet"))
    for cls, mirror_label in (("real", MIRROR_REAL), ("fake", MIRROR_FAKE)):
        pool = rng.permutation(np.where(train_df["label"].values == mirror_label)[0])
        n_tr, n_va = args.train_per_class, args.val_per_class
        dump(train_df, pool[:n_tr], "train", cls)
        dump(train_df, pool[n_tr:n_tr + n_va], "val", cls)
        tpool = rng.permutation(np.where(test_df["label"].values == mirror_label)[0])
        dump(test_df, tpool[:args.test_per_class], "test", cls)
        print(cls, "train", n_tr, "val", n_va, "test", args.test_per_class, flush=True)


if __name__ == "__main__":
    main()
