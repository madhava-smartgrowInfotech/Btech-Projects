"""Loads the FER2013 pickle files (data/train.pt, data/test.pt) downloaded from
Hugging Face (Jeneral/fer-2013). Each file is a plain-pickled list of
{"img_bytes": <jpeg bytes>, "labels": <emotion string>} — note the dataset's own
label spelling ("neutral" before "sad") differs from our BASIC_EMOTIONS order, so
everything is remapped through the string name, never a raw index.
"""
import io
import pickle
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.ml.classifier_model import IMG_SIZE
from app.ml.taxonomy import BASIC_INDEX, NUM_BASIC

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _load_pickle(name: str) -> list[dict]:
    path = DATA_DIR / name
    with path.open("rb") as f:
        return pickle.load(f)


def _decode(img_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(img_bytes)).convert("L")
    arr = np.array(img, dtype=np.uint8)
    return cv2.resize(arr, (IMG_SIZE, IMG_SIZE))


def load_split(name: str, cap_per_class: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Returns (images uint8 [N,H,W], basic_label_index int64 [N])."""
    examples = _load_pickle(name)
    per_class_count = {k: 0 for k in BASIC_INDEX}
    images, labels = [], []
    for ex in examples:
        label = ex["labels"]
        if label not in BASIC_INDEX:
            continue
        if cap_per_class is not None and per_class_count[label] >= cap_per_class:
            continue
        images.append(_decode(ex["img_bytes"]))
        labels.append(BASIC_INDEX[label])
        per_class_count[label] += 1
    return np.stack(images), np.array(labels, dtype=np.int64)


def class_weights(labels: np.ndarray) -> np.ndarray:
    counts = np.bincount(labels, minlength=NUM_BASIC).astype(np.float32)
    counts[counts == 0] = 1.0
    weights = counts.sum() / (NUM_BASIC * counts)
    return weights
