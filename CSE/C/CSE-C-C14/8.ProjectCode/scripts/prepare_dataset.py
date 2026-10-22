"""Dataset preparation for VeriVision AI.

Attempts, in order:
  1. Kaggle API download of CIFAKE (needs kaggle credentials / kaggle package).
  2. Deterministic local fallback generation (clearly labelled synthetic/demo data).

Resulting layout:
  data/train/{real,fake}  data/val/{real,fake}  data/test/{real,fake}
"""
import io
import os
import random
import shutil
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

SEED = int(os.environ.get("VERIVISION_SEED", "42"))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")

KAGGLE_DATASET = "birdy654/cifake-real-and-ai-generated-synthetic-images"

FALLBACK_COUNTS = {
    "train": int(os.environ.get("VERIVISION_FALLBACK_TRAIN_PER_CLASS", "500")),
    "val": int(os.environ.get("VERIVISION_FALLBACK_VAL_PER_CLASS", "100")),
    "test": int(os.environ.get("VERIVISION_FALLBACK_TEST_PER_CLASS", "100")),
}


def _rng(seed):
    return random.Random(seed), np.random.RandomState(seed)


def _make_real_image(rng_py, rng_np, size=96):
    """Smooth photographic-style image: soft gradient + blurred shapes + mild noise."""
    w = h = size
    x = np.linspace(0, 1, w)[None, :].repeat(h, axis=0)
    y = np.linspace(0, 1, h)[:, None].repeat(w, axis=1)
    base = np.zeros((h, w, 3), dtype=np.float32)
    for c in range(3):
        a, b, d = rng_np.uniform(40, 200), rng_np.uniform(-60, 60), rng_np.uniform(-60, 60)
        base[:, :, c] = a + b * x + d * y
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(img, "RGBA")
    for _ in range(rng_py.randint(3, 7)):
        cx, cy = rng_py.randint(0, w), rng_py.randint(0, h)
        r = rng_py.randint(6, 26)
        col = tuple(int(v) for v in rng_np.uniform(30, 230, size=3)) + (rng_py.randint(60, 140),)
        if rng_py.random() < 0.5:
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
        else:
            draw.rectangle([cx - r, cy - r, cx + r, cy + r], fill=col)
    img = img.filter(ImageFilter.GaussianBlur(radius=rng_py.uniform(0.6, 1.6)))
    arr = np.array(img).astype(np.float32) + rng_np.normal(0, 4.0, (h, w, 3))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _make_fake_image(rng_py, rng_np, size=96):
    """Synthetic-style image: same base plus GAN-like artifacts (checkerboard,
    banding, high-frequency speckle) that a CNN can learn."""
    img = _make_real_image(rng_py, rng_np, size=size)
    arr = np.array(img).astype(np.float32)
    h, w, _ = arr.shape
    # Checkerboard artifact field
    yy, xx = np.mgrid[0:h, 0:w]
    checker = (((xx // 4) + (yy // 4)) % 2).astype(np.float32) * rng_py.uniform(10, 26)
    arr += checker[:, :, None]
    # Horizontal banding
    band = (np.sin(yy / 2.5) * rng_py.uniform(4, 10)).astype(np.float32)
    arr += band[:, :, None]
    # Speckle
    arr += rng_np.normal(0, 9.0, (h, w, 3))
    # Over-saturation push
    arr[:, :, 0] = np.clip(arr[:, :, 0] * rng_py.uniform(1.0, 1.25), 0, 255)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def generate_fallback():
    """Deterministic synthetic/demo dataset with identical real/fake schema."""
    rng_py, rng_np = _rng(SEED)
    for split, per_class in FALLBACK_COUNTS.items():
        for cls in ("real", "fake"):
            folder = os.path.join(DATA_DIR, split, cls)
            os.makedirs(folder, exist_ok=True)
            for f in os.listdir(folder):
                p = os.path.join(folder, f)
                if os.path.isfile(p):
                    os.remove(p)
            for i in range(per_class):
                maker = _make_real_image if cls == "real" else _make_fake_image
                img = maker(rng_py, rng_np)
                img.save(os.path.join(folder, f"{cls}_{split}_{i:05d}.png"))
    marker = os.path.join(DATA_DIR, "FALLBACK_DATA_README.txt")
    with open(marker, "w", encoding="utf-8") as fh:
        fh.write(
            "DEMO DATA NOTICE\nThis directory contains deterministic SYNTHETIC demo data "
            "generated locally because the public CIFAKE dataset could not be downloaded "
            "in this environment (no network access or missing Kaggle credentials).\n"
            "Do NOT treat metrics trained on this data as representative of real-world "
            "detector performance.\n"
        )
    total = sum(FALLBACK_COUNTS.values()) * 2
    print(f"Fallback demo dataset generated: {total} images under {DATA_DIR}")
    return "fallback"


def try_kaggle_download():
    """Try Kaggle API; returns extracted dir or raises."""
    try:
        import kaggle
    except ImportError:
        raise RuntimeError("kaggle package not installed")
    os.makedirs(RAW_DIR, exist_ok=True)
    print(f"Downloading {KAGGLE_DATASET} via Kaggle API ...", flush=True)
    kaggle.api.dataset_download_files(KAGGLE_DATASET, path=RAW_DIR, unzip=True)
    return RAW_DIR


def organize_cifake(extracted):
    """Map CIFAKE's FAKE/REAL folders into stratified 70/15/15 splits."""
    rng = random.Random(SEED)
    real, fake = [], []
    for root, _dirs, files in os.walk(extracted):
        for f in files:
            if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
                continue
            p = os.path.join(root, f)
            low = p.lower()
            if os.sep + "fake" in low or "/fake" in low or "fake" in os.path.basename(os.path.dirname(p)).lower():
                fake.append(p)
            elif os.sep + "real" in low or "/real" in low or "real" in os.path.basename(os.path.dirname(p)).lower():
                real.append(p)
    if not real or not fake:
        raise RuntimeError("Could not locate REAL/FAKE folders in downloaded data.")
    rng.shuffle(real)
    rng.shuffle(fake)

    def split_list(items):
        n = len(items)
        n_train = int(n * 0.70)
        n_val = int(n * 0.15)
        return items[:n_train], items[n_train:n_train + n_val], items[n_train + n_val:]

    for split in ("train", "val", "test"):
        for cls in ("real", "fake"):
            folder = os.path.join(DATA_DIR, split, cls)
            os.makedirs(folder, exist_ok=True)
            for f in os.listdir(folder):
                p = os.path.join(folder, f)
                if os.path.isfile(p):
                    os.remove(p)
    for cls_name, items in (("real", real), ("fake", fake)):
        tr, va, te = split_list(items)
        for split_name, subset in (("train", tr), ("val", va), ("test", te)):
            dest = os.path.join(DATA_DIR, split_name, cls_name)
            for i, src in enumerate(subset):
                ext = os.path.splitext(src)[1].lower() or ".jpg"
                shutil.copy(src, os.path.join(dest, f"{cls_name}_{split_name}_{i:05d}{ext}"))
    print(f"CIFAKE organized: real={len(real)} fake={len(fake)}")
    return "cifake"


def main():
    force_fallback = os.environ.get("VERIVISION_FORCE_FALLBACK", "") == "1"
    if not force_fallback:
        try:
            extracted = try_kaggle_download()
            try:
                return organize_cifake(extracted)
            except Exception as exc:
                print(f"CIFAKE organization failed ({exc}); using fallback.")
        except Exception as exc:
            print(f"Kaggle download unavailable ({exc}); using fallback demo data.")
    else:
        print("VERIVISION_FORCE_FALLBACK=1; generating fallback demo data.")
    return generate_fallback()


if __name__ == "__main__":
    result = main()
    print(f"Dataset source: {result}")
