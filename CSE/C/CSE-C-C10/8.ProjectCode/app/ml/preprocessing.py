"""Structured preprocessing pipeline."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.config import NUMERIC_FEATURES, BINARY_FEATURES, CATEGORICAL_FEATURES
from app.ml.dataset import map_target, clean_text


def prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates()
    df["label"] = map_target(df["status"])
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    # numeric coercion
    for c in NUMERIC_FEATURES + BINARY_FEATURES:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # categorical normalization
    for c in CATEGORICAL_FEATURES:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()
            df[c] = df[c].replace({"nan": "Unknown", "None": "Unknown", "": "Unknown"})
            df[c] = df[c].fillna("Unknown")
    # log funding to tame outliers (kept as extra derived col)
    df["log_funding_total_usd"] = np.log1p(df["funding_total_usd"].fillna(0).clip(lower=0))
    if "description" not in df.columns:
        df["description"] = ""
    df["description"] = df["description"].fillna("").astype(str).apply(clean_text)
    # outcome text mapping
    df["outcome"] = df["label"].apply(lambda v: "SUCCESS" if v == 1 else "FAILURE")
    return df


def build_preprocessor() -> ColumnTransformer:
    numeric = NUMERIC_FEATURES + ["log_funding_total_usd"]
    binary = BINARY_FEATURES
    cat = CATEGORICAL_FEATURES
    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    bin_pipe = Pipeline([("imputer", SimpleImputer(strategy="most_frequent"))])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    pre = ColumnTransformer([
        ("num", num_pipe, numeric),
        ("bin", bin_pipe, binary),
        ("cat", cat_pipe, cat),
    ])
    return pre


def feature_names(pre: ColumnTransformer) -> list[str]:
    names: list[str] = []
    try:
        for name, trans, cols in pre.transformers_:
            if name == "num":
                names.extend(list(cols))
            elif name == "bin":
                names.extend(list(cols))
            elif name == "cat":
                ohe = trans.named_steps["onehot"]
                names.extend(list(ohe.get_feature_names_out(cols)))
    except Exception:
        pass
    return names
