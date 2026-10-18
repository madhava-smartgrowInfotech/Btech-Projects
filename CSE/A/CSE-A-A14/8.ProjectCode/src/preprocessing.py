"""
preprocessing.py
------------------
Builds a scikit-learn ColumnTransformer + Pipeline for consistent
preprocessing across training and inference, and provides helpers for
missing-value treatment, duplicate handling, train/test splitting and
class-imbalance handling (class_weight or SMOTE).

Design notes
------------
* Numeric features -> median imputation + StandardScaler
* Categorical features -> most-frequent imputation + OneHotEncoder
* SMOTE (if selected) is applied ONLY to the training split, never to
  the test split, and never before the split -- this avoids leakage.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split


def clean_missing_and_duplicates(df: pd.DataFrame, drop_duplicates: bool = True) -> tuple[pd.DataFrame, dict]:
    """Drop exact duplicate rows and report on remaining missingness.
    Actual imputation of missing values happens inside the ColumnTransformer
    (so it is fit only on the training data), not here.
    """
    report = {}
    n_before = len(df)
    if drop_duplicates:
        df = df.drop_duplicates()
    report["duplicates_removed"] = n_before - len(df)
    report["rows_remaining"] = len(df)
    report["missing_before"] = int(df.isna().sum().sum())
    return df, report


def build_preprocessor(numeric_cols: list, categorical_cols: list) -> ColumnTransformer:
    numeric_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    transformers = []
    if numeric_cols:
        transformers.append(("num", numeric_pipeline, numeric_cols))
    if categorical_cols:
        transformers.append(("cat", categorical_pipeline, categorical_cols))

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
    return preprocessor


def get_feature_names(preprocessor: ColumnTransformer) -> list:
    """Return human-readable output feature names after the
    ColumnTransformer has been fit (numeric names unchanged, categorical
    names expanded to one-hot column names)."""
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:
        names = []
        for name, trans, cols in preprocessor.transformers_:
            if name == "remainder":
                continue
            if hasattr(trans, "named_steps") and "onehot" in trans.named_steps:
                ohe = trans.named_steps["onehot"]
                names.extend(ohe.get_feature_names_out(cols).tolist())
            else:
                names.extend(cols)
        return names


def train_test_split_data(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42):
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)


def apply_smote(X_train_transformed, y_train, random_state: int = 42):
    """Apply SMOTE oversampling to the (already-transformed, numeric)
    training data only. Requires imbalanced-learn to be installed."""
    from imblearn.over_sampling import SMOTE
    smote = SMOTE(random_state=random_state)
    X_res, y_res = smote.fit_resample(X_train_transformed, y_train)
    return X_res, y_res


def class_distribution(y: pd.Series) -> dict:
    counts = y.value_counts().to_dict()
    total = len(y)
    return {
        "counts": counts,
        "percentages": {k: round(100 * v / total, 2) for k, v in counts.items()},
        "imbalance_ratio": round(max(counts.values()) / max(min(counts.values()), 1), 2),
    }
