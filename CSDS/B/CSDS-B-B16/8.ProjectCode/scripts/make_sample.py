"""Build the committed fundus sample (data/sample/fundus) from the held-out test split.

Usage: python scripts/make_sample.py
Picks 10 positive and 10 negative test images (seeded), resizes them to 1024 px on the long side
(to keep the repository small) and writes labels.csv. These are sample data for demonstration.
"""
import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml"))
from common import SEED, hr_image_dir, hr_label_csv  # noqa: E402

OUT = ROOT / "data" / "sample" / "fundus"
PER_CLASS = 10


def main():
    labels = pd.read_csv(hr_label_csv())
    labels.columns = ["Image", "label"]
    test = json.loads((ROOT / "experiments" / "retina" / "split.json").read_text())["test"]
    t = labels.set_index("Image").loc[test].reset_index()
    rng = np.random.default_rng(SEED)
    picks = []
    for lab in (1, 0):
        names = sorted(t[t.label == lab].Image)
        picks += [(n, lab) for n in rng.choice(names, PER_CLASS, replace=False)]
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    rows = []
    for n, lab in sorted(picks):
        img = cv2.imread(str(hr_image_dir() / n))
        s = 1024 / max(img.shape[:2])
        if s < 1:
            img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(OUT / n), img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        rows.append({"image": n, "hypertensive_retinopathy": lab})
    with (OUT / "labels.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["image", "hypertensive_retinopathy"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} sample images to {OUT}")


if __name__ == "__main__":
    main()
