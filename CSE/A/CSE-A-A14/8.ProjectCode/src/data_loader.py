"""
data_loader.py
---------------
Handles reading uploaded CSV files, auto-detecting the target/id
columns and numerical/categorical feature columns, and running basic
data-quality checks (missing values, duplicates, insufficient rows).

None of the functions here talk to Streamlit directly -- they return
plain Python / pandas objects so they can be unit tested and reused
from any page.
"""

from __future__ import annotations
import io
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

from utils import safe_numeric

CANDIDATE_TARGET_NAMES = ["churn", "target", "label", "exited", "is_churn", "churned"]
CANDIDATE_ID_NAMES = ["customerid", "customer_id", "id", "custid"]

# Columns that are TotalCharges-like: numeric but sometimes stored as
# strings with blanks in the public Telco dataset.
NUMERIC_LOOKING_OBJECT_HINTS = ["totalcharges", "monthlycharges", "charges", "amount"]


@dataclass
class DatasetProfile:
    n_rows: int
    n_cols: int
    target_col: str | None
    id_col: str | None
    numeric_cols: list = field(default_factory=list)
    categorical_cols: list = field(default_factory=list)
    missing_summary: pd.Series = None
    n_duplicates: int = 0
    warnings: list = field(default_factory=list)


def load_csv(file_obj) -> pd.DataFrame:
    """Read a CSV from a Streamlit UploadedFile or a file path/buffer."""
    if hasattr(file_obj, "read"):
        raw = file_obj.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        df = pd.read_csv(io.StringIO(raw))
    else:
        df = pd.read_csv(file_obj)
    df.columns = [c.strip() for c in df.columns]
    return df


def detect_target_column(df: pd.DataFrame) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for name in CANDIDATE_TARGET_NAMES:
        if name in lower_map:
            return lower_map[name]
    return None


def detect_id_column(df: pd.DataFrame) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for name in CANDIDATE_ID_NAMES:
        if name in lower_map:
            return lower_map[name]
    # fallback: a column that is entirely unique strings
    for c in df.columns:
        if df[c].dtype == object and df[c].nunique() == len(df):
            return c
    return None


def coerce_numeric_looking_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Some numeric columns (notably TotalCharges in the classic Telco
    dataset) are stored as text with occasional blank strings. Detect and
    coerce these so downstream preprocessing treats them as numeric."""
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == object:
            lc = c.lower()
            if any(h in lc for h in NUMERIC_LOOKING_OBJECT_HINTS):
                coerced = safe_numeric(df[c])
                # Only replace if a healthy majority actually parsed as numbers
                if coerced.notna().mean() > 0.8:
                    df[c] = coerced
    return df


def detect_column_types(df: pd.DataFrame, target_col: str | None, id_col: str | None):
    feature_df = df.drop(columns=[c for c in [target_col, id_col] if c and c in df.columns])
    numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = feature_df.select_dtypes(exclude=[np.number]).columns.tolist()
    # SeniorCitizen is often 0/1 numeric but semantically categorical -- keep
    # it numeric for the model (it works fine either way with scaling off).
    return numeric_cols, categorical_cols


def profile_dataset(df: pd.DataFrame, target_col: str | None = None, id_col: str | None = None) -> DatasetProfile:
    warnings = []
    target_col = target_col or detect_target_column(df)
    id_col = id_col or detect_id_column(df)

    if target_col is None:
        warnings.append("Could not automatically detect a churn/target column. Please select one manually.")

    n_duplicates = int(df.duplicated().sum())
    if n_duplicates > 0:
        warnings.append(f"{n_duplicates} duplicate rows detected.")

    missing_summary = df.isna().sum()
    missing_summary = missing_summary[missing_summary > 0].sort_values(ascending=False)
    if len(missing_summary) > 0:
        warnings.append(f"{len(missing_summary)} column(s) contain missing values.")

    if len(df) < 50:
        warnings.append("Dataset has very few rows (<50) -- model quality and SHAP explanations may be unreliable.")

    numeric_cols, categorical_cols = detect_column_types(df, target_col, id_col)

    return DatasetProfile(
        n_rows=len(df),
        n_cols=len(df.columns),
        target_col=target_col,
        id_col=id_col,
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
        missing_summary=missing_summary,
        n_duplicates=n_duplicates,
        warnings=warnings,
    )


def normalize_target(df: pd.DataFrame, target_col: str) -> pd.Series:
    """Convert a variety of churn label encodings (Yes/No, 1/0, True/False,
    Churned/Retained ...) into a clean binary 0/1 integer series. Returns
    the series plus the label that was treated as the positive ("churn")
    class, so the UI can display it consistently.
    """
    s = df[target_col]
    positive_tokens = {"yes", "1", "true", "churned", "churn", "y"}

    if s.dtype == object or s.dtype == bool:
        s_str = s.astype(str).str.strip().str.lower()
        binary = s_str.isin(positive_tokens).astype(int)
        return binary
    else:
        uniq = sorted(s.dropna().unique().tolist())
        if set(uniq) <= {0, 1}:
            return s.astype(int)
        # Fallback: treat the max value as the positive/churn class
        return (s == max(uniq)).astype(int)


def validate_dataset_for_training(df: pd.DataFrame, target_col: str) -> list:
    """Run pre-training sanity checks; returns a list of human-readable
    error strings (empty list means the dataset is trainable)."""
    errors = []
    if df is None or len(df) == 0:
        errors.append("Dataset is empty.")
        return errors
    if target_col not in df.columns:
        errors.append(f"Target column '{target_col}' not found in dataset.")
        return errors
    if len(df) < 30:
        errors.append("Dataset has fewer than 30 rows -- not enough data to train reliably.")
    y = normalize_target(df, target_col)
    class_counts = y.value_counts()
    if len(class_counts) < 2:
        errors.append("Target column has only one class present -- cannot train a classifier.")
    elif class_counts.min() < 5:
        errors.append("One of the target classes has fewer than 5 examples -- training/splitting will be unreliable.")
    return errors

