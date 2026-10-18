"""Dataset loading and preparation for training.

Expects DATA_DIR to contain one sub-folder per class (A, B, ..., Z, space,
del, nothing), each holding raw color images captured via the data
collection tab (or dropped in from an external dataset such as the Kaggle
"ASL Alphabet" dataset, which uses the same folder layout).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical

from . import config
from .preprocessing import normalize_for_model, segment_hand


def class_counts() -> dict[str, int]:
    counts = {}
    for cls in config.CLASSES:
        folder = config.DATA_DIR / cls
        if folder.exists():
            counts[cls] = len(list(folder.glob("*.png"))) + len(list(folder.glob("*.jpg")))
        else:
            counts[cls] = 0
    return counts


def available_classes() -> list[str]:
    """Classes that currently have at least one collected image."""
    return [c for c, n in class_counts().items() if n > 0]


@dataclass
class Dataset:
    x_train: np.ndarray
    y_train: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    labels: list[str]


def load_dataset(progress_cb=None) -> Dataset:
    """Load every collected image, run it through the preprocessing
    pipeline, and split into train/val/test sets.

    progress_cb(done, total) is called periodically if provided.
    """
    labels = available_classes()
    if not labels:
        raise RuntimeError(
            "No training data found. Use the 'Collect Data' tab to capture "
            "images for at least two classes before training."
        )

    images: list[np.ndarray] = []
    targets: list[int] = []

    all_paths = []
    for idx, cls in enumerate(labels):
        folder = config.DATA_DIR / cls
        paths = sorted(list(folder.glob("*.png")) + list(folder.glob("*.jpg")))
        all_paths.extend((p, idx) for p in paths)

    total = len(all_paths)
    for i, (path, idx) in enumerate(all_paths):
        raw = cv2.imread(str(path))
        if raw is None:
            continue
        mask = segment_hand(raw)
        model_input = normalize_for_model(mask)
        images.append(model_input)
        targets.append(idx)
        if progress_cb and (i % 25 == 0 or i == total - 1):
            progress_cb(i + 1, total)

    x = np.array(images, dtype="float32")
    y = to_categorical(np.array(targets), num_classes=len(labels))

    x_train, x_temp, y_train, y_temp = train_test_split(
        x, y, test_size=config.VALIDATION_SPLIT + config.TEST_SPLIT,
        random_state=config.RANDOM_SEED, stratify=y,
    )
    relative_test = config.TEST_SPLIT / (config.VALIDATION_SPLIT + config.TEST_SPLIT)
    x_val, x_test, y_val, y_test = train_test_split(
        x_temp, y_temp, test_size=relative_test,
        random_state=config.RANDOM_SEED, stratify=y_temp,
    )

    return Dataset(x_train, y_train, x_val, y_val, x_test, y_test, labels)


def save_labels(labels: list[str]) -> None:
    with open(config.LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump(labels, f, indent=2)


def load_labels() -> list[str]:
    if not config.LABELS_PATH.exists():
        return []
    with open(config.LABELS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
