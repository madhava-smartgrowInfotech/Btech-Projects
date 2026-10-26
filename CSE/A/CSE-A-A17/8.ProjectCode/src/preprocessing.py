"""
preprocessing.py
------------------
Cleans and merges the three raw H&M tables into a single transaction-level
DataFrame that is ready for demand aggregation.

Design goal: never silently drop large amounts of data. We fix what we can
(missing categoricals -> "Unknown", missing numerics -> median) and only
drop rows that are truly unusable (e.g. no article_id, no date, negative
price).
"""

from __future__ import annotations

import pandas as pd
import numpy as np


def clean_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    WHAT: Cleans the raw transactions table.
    WHY:  Raw retail data commonly has duplicate rows, bad dates, and
          invalid prices that would corrupt demand aggregation.
    HOW:
        1. Parse t_dat into a real datetime.
        2. Drop rows with missing article_id / customer_id / t_dat
           (these rows cannot be used at all).
        3. Drop rows with negative or zero price (data entry errors) --
           but keep a record of how many were removed.
        4. Drop exact-duplicate transaction rows.
        5. Sort chronologically.
    """
    df = transactions.copy()

    # 1. Parse dates
    df["t_dat"] = pd.to_datetime(df["t_dat"], errors="coerce")

    # 2. Drop rows that are missing essential identifiers
    essential = ["t_dat", "article_id", "customer_id"]
    df = df.dropna(subset=essential)

    # 3. Validate price: must be a positive number
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df[df["price"] > 0]

    # 4. Remove exact duplicate transaction rows
    df = df.drop_duplicates()

    # 5. Sort chronologically -- this matters a lot for lag/rolling features later
    df = df.sort_values("t_dat").reset_index(drop=True)

    return df


def clean_articles(articles: pd.DataFrame) -> pd.DataFrame:
    """
    WHAT: Fills missing categorical attributes with 'Unknown' rather than
          dropping products, since a product missing e.g. `detail_desc`
          is still a valid, sellable product.
    """
    df = articles.copy()
    categorical_cols = df.select_dtypes(include="object").columns
    for col in categorical_cols:
        df[col] = df[col].fillna("Unknown")
    df = df.drop_duplicates(subset="article_id")
    return df


def clean_customers(customers: pd.DataFrame) -> pd.DataFrame:
    """WHAT: Light cleaning for the optional customers table."""
    if customers.empty:
        return customers
    df = customers.copy()
    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors="coerce")
        df["age"] = df["age"].fillna(df["age"].median())
    categorical_cols = df.select_dtypes(include="object").columns
    for col in categorical_cols:
        df[col] = df[col].fillna("Unknown")
    df = df.drop_duplicates(subset="customer_id")
    return df


def merge_datasets(
    transactions: pd.DataFrame,
    articles: pd.DataFrame,
    customers: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    WHAT: Left-joins transactions -> articles (-> customers if provided).
    WHY:  We need product attributes (category, department, colour...)
          attached to every transaction row for feature engineering.
    HOW:  Left join on article_id (and customer_id) so we never lose
          transaction rows even if a product/customer record is missing.
    """
    merged = transactions.merge(articles, on="article_id", how="left")

    # Any article attributes that failed to match get "Unknown" rather
    # than NaN, so downstream grouping doesn't silently drop them.
    obj_cols = merged.select_dtypes(include="object").columns
    for col in obj_cols:
        merged[col] = merged[col].fillna("Unknown")

    if customers is not None and not customers.empty:
        merged = merged.merge(customers, on="customer_id", how="left")

    merged = merged.sort_values("t_dat").reset_index(drop=True)
    return merged


def data_quality_report(
    raw_transactions: pd.DataFrame,
    cleaned_transactions: pd.DataFrame,
    merged: pd.DataFrame,
) -> dict:
    """
    WHAT: Produces the summary statistics shown on the "Data Upload /
          Exploration" page.
    WHY:  The examiner / project guide will want to see evidence the
          data was inspected and cleaned properly, not just used blindly.
    """
    report = {
        "raw_rows": len(raw_transactions),
        "cleaned_rows": len(cleaned_transactions),
        "rows_removed": len(raw_transactions) - len(cleaned_transactions),
        "columns": merged.shape[1],
        "missing_values_total": int(merged.isna().sum().sum()),
        "duplicate_rows": int(merged.duplicated().sum()),
        "date_min": cleaned_transactions["t_dat"].min() if not cleaned_transactions.empty else None,
        "date_max": cleaned_transactions["t_dat"].max() if not cleaned_transactions.empty else None,
        "num_customers": cleaned_transactions["customer_id"].nunique() if not cleaned_transactions.empty else 0,
        "num_products": cleaned_transactions["article_id"].nunique() if not cleaned_transactions.empty else 0,
        "num_transactions": len(cleaned_transactions),
    }
    return report
