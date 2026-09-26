"""Objective 1 - collect and preprocess a dataset of phishing and legitimate URLs.

The repository ships `data/urls_sample.csv` (40,000 URLs, balanced) sampled
from the public "Using machine learning to detect malicious URLs" dataset.
`download_full_dataset()` can fetch the whole ~420k-row file if wanted.
"""
from __future__ import annotations

import urllib.request

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from . import config
from .features import featurize_urls, normalize_url


def load_dataset(path=None, max_rows: int | None = None) -> pd.DataFrame:
    """Return a cleaned DataFrame with columns url (str) and label (0/1)."""
    path = path or config.DATASET_CSV
    df = pd.read_csv(path, on_bad_lines="skip")
    df = df.dropna(subset=["url", "label"])
    if df["label"].dtype == object:
        df["label"] = df["label"].astype(str).str.strip().str.lower().map(
            {"bad": 1, "phishing": 1, "malicious": 1, "1": 1, "good": 0, "benign": 0,
             "legitimate": 0, "0": 0}
        )
        df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    df["url"] = df["url"].astype(str).str.strip()
    df = df[df["url"].str.len() > 3].drop_duplicates("url")
    if max_rows and len(df) > max_rows:
        per_class = max_rows // 2
        parts = [g.sample(min(len(g), per_class), random_state=config.RANDOM_STATE)
                 for _, g in df.groupby("label")]
        df = pd.concat(parts).sample(frac=1, random_state=config.RANDOM_STATE)
    return df.reset_index(drop=True)


def download_full_dataset(dest=None) -> str:
    dest = str(dest or config.DATA_DIR / "urls_full.csv")
    print(f"Downloading {config.FULL_DATASET_URL} -> {dest}")
    urllib.request.urlretrieve(config.FULL_DATASET_URL, dest)
    return dest


def build_matrices(df: pd.DataFrame):
    """Feature-extract a dataframe and split into train/test arrays."""
    X = featurize_urls(df["url"].tolist())
    y = df["label"].to_numpy()
    return train_test_split(
        X, y, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE, stratify=y
    )


def dataset_summary(df: pd.DataFrame) -> dict:
    return {
        "rows": int(len(df)),
        "phishing": int(df["label"].sum()),
        "legitimate": int((df["label"] == 0).sum()),
        "example_phishing": df[df.label == 1]["url"].head(3).tolist(),
        "example_legitimate": df[df.label == 0]["url"].head(3).tolist(),
    }


__all__ = ["load_dataset", "download_full_dataset", "build_matrices", "dataset_summary",
           "normalize_url", "np"]
