"""
Preprocessing pipeline for ThreatSense Engine.
Handles both real UNSW-NB15 CSVs and synthetic demo data.
"""
import json
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from .features import FEATURE_NAMES, CATEGORICAL_FEATURES, LABEL_COL, ATTACK_COL

NUMERIC_FEATURES = [f for f in FEATURE_NAMES if f not in CATEGORICAL_FEATURES]

def build_preprocessor() -> ColumnTransformer:
    numeric = MinMaxScaler()
    # OneHot with handle_unknown=ignore for robustness to unseen categories
    cat = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    pre = ColumnTransformer(
        transformers=[
            ("num", numeric, NUMERIC_FEATURES),
            ("cat", cat, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return pre

def load_csv_smart(path: Path) -> pd.DataFrame:
    """
    Try to load UNSW-NB15 CSV regardless of header quirks.
    UNSW files sometimes have no header or have id column. We handle both.
    """
    # Try reading first row to detect header
    df = pd.read_csv(path, low_memory=False)
    cols_lower = [str(c).lower() for c in df.columns]
    # If expected feature names present, assume header row is correct
    if "proto" in cols_lower and "service" in cols_lower:
        # Normalize column names to lowercase without spaces
        df.columns = [str(c).strip().lower() for c in df.columns]
        # Map various label names
        if "label" not in df.columns and "label" not in cols_lower:
            for cand in ["label", "class", "attack"]:
                if cand in cols_lower:
                    df = df.rename(columns={df.columns[cols_lower.index(cand)]: "label"})
        return df
    else:
        # No header case: assign our schema (drop extra)
        # Read again without header
        df2 = pd.read_csv(path, header=None, low_memory=False)
        # Heuristic: if columns count matches, assign
        # UNSW training set has 49 cols; we map first N then label
        # Fallback: treat as already synthetic format with header missing -> use synthetic header
        n = len(df2.columns)
        # Try to map to our ALL_COLUMNS truncated
        from .features import ALL_COLUMNS
        if n == len(ALL_COLUMNS):
            df2.columns = ALL_COLUMNS
            return df2
        elif n == len(FEATURE_NAMES) + 2:  # without id
            df2.columns = FEATURE_NAMES + [LABEL_COL, ATTACK_COL]
            return df2
        else:
            # Unknown; return as-is and let caller handle
            return df2

def prepare_dataframes(dfs: list[pd.DataFrame]) -> tuple[np.ndarray, np.ndarray, ColumnTransformer]:
    """
    Combine dataframes, fit preprocessor, return X, y.
    """
    combined = pd.concat(dfs, ignore_index=True)
    # Ensure required columns present
    for f in FEATURE_NAMES:
        if f not in combined.columns:
            combined[f] = 0
    # Label handling
    if LABEL_COL not in combined.columns:
        raise ValueError(f"CSV missing '{LABEL_COL}' column (0=normal,1=attack)")
    # Coerce label to binary
    y = combined[LABEL_COL].values
    # Handle string labels like 'Normal' / 'Attack' or attack_cat present
    if y.dtype == object:
        y_str = np.array([str(v).lower() for v in y])
        y = np.where(np.isin(y_str, ["1", "attack", "anomaly", "malicious", "true"]), 1, 0)
        # If many zeros and attack_cat column exists, use it
        if ATTACK_COL in combined.columns:
            ac = combined[ATTACK_COL].astype(str).str.lower()
            mask_attack = ~ac.isin(["normal", "benign", "-", "nan", "none", ""])
            y = np.where(mask_attack, 1, y)
    y = y.astype(int)

    # Ensure categorical columns are string
    for c in CATEGORICAL_FEATURES:
        combined[c] = combined[c].astype(str)

    pre = build_preprocessor()
    X = pre.fit_transform(combined)
    return X, y, pre

def transform_with_preprocessor(df: pd.DataFrame, pre: ColumnTransformer) -> np.ndarray:
    for f in FEATURE_NAMES:
        if f not in df.columns:
            df[f] = 0
    for c in CATEGORICAL_FEATURES:
        if c not in df.columns:
            df[c] = "-"
        df[c] = df[c].astype(str)
    return pre.transform(df)
