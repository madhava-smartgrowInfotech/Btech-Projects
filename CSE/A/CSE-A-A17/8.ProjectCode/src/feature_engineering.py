"""
feature_engineering.py
------------------------
Builds all model input features on top of the daily demand table.

IMPORTANT (data leakage):
Lag and rolling features must be computed PER ARTICLE, in chronological
order, using only *past* values. We use pandas' `.shift()` before any
rolling calculation, which guarantees the feature for day D never sees
day D's own demand.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


LAG_DAYS = [1, 7, 14, 28]
ROLLING_MEAN_WINDOWS = [7, 14, 28]
ROLLING_STD_WINDOWS = [7, 28]


def add_time_features(df: pd.DataFrame, date_col: str = "t_dat") -> pd.DataFrame:
    """
    WHAT: Adds calendar-based features (year, month, day-of-week, etc.)
    WHY:  Retail demand is strongly seasonal/weekly -- these features let
          the model learn "weekends sell more" or "December is high demand"
          without us hand-coding those rules.
    """
    out = df.copy()
    dt = out[date_col]

    out["year"] = dt.dt.year
    out["month"] = dt.dt.month
    out["day"] = dt.dt.day
    out["day_of_week"] = dt.dt.dayofweek  # 0 = Monday
    out["week_of_year"] = dt.dt.isocalendar().week.astype(int)
    out["day_of_year"] = dt.dt.dayofyear
    out["quarter"] = dt.dt.quarter
    out["is_weekend"] = (out["day_of_week"] >= 5).astype(int)
    out["is_month_start"] = dt.dt.is_month_start.astype(int)
    out["is_month_end"] = dt.dt.is_month_end.astype(int)

    # Cyclical encodings: turns "December (12) is next to January (1)"
    # into something the model can actually understand (raw 12 vs 1 looks
    # maximally *different* to a tree model's splits, but sin/cos makes
    # the wrap-around explicit).
    out["month_sin"] = np.sin(2 * np.pi * out["month"] / 12)
    out["month_cos"] = np.cos(2 * np.pi * out["month"] / 12)
    out["dow_sin"] = np.sin(2 * np.pi * out["day_of_week"] / 7)
    out["dow_cos"] = np.cos(2 * np.pi * out["day_of_week"] / 7)

    return out


def add_lag_rolling_features(
    df: pd.DataFrame,
    group_col: str = "article_id",
    date_col: str = "t_dat",
    target_col: str = "demand",
) -> pd.DataFrame:
    """
    WHAT: Adds lag_1/7/14/28 and rolling mean/std features.
    WHY:  Past demand is usually the single strongest predictor of near-
          future demand.
    HOW:  Sort each article's rows by date, then use `.shift(n)` (lag) and
          `.shift(1).rolling(w)` (rolling stats computed on values strictly
          BEFORE the current day) so no future information leaks into the
          row's own features.
    """
    out = df.sort_values([group_col, date_col]).copy()
    grouped_target = out.groupby(group_col)[target_col]

    for lag in LAG_DAYS:
        out[f"lag_{lag}"] = grouped_target.shift(lag)

    # shift(1) first so the rolling window never includes today's demand
    shifted = out.groupby(group_col)[target_col].shift(1)
    out["_shifted_demand"] = shifted

    for window in ROLLING_MEAN_WINDOWS:
        out[f"rolling_mean_{window}"] = (
            out.groupby(group_col)["_shifted_demand"]
            .transform(lambda s: s.rolling(window, min_periods=1).mean())
        )

    for window in ROLLING_STD_WINDOWS:
        out[f"rolling_std_{window}"] = (
            out.groupby(group_col)["_shifted_demand"]
            .transform(lambda s: s.rolling(window, min_periods=1).std())
        )

    out = out.drop(columns=["_shifted_demand"])

    # Rows at the very start of an article's history won't have enough
    # history for lag_28 etc. -- fill remaining NaNs with 0, which is a
    # reasonable "no prior sales observed" default for a tree model.
    lag_roll_cols = [c for c in out.columns if c.startswith(("lag_", "rolling_"))]
    out[lag_roll_cols] = out[lag_roll_cols].fillna(0)

    return out


def encode_categoricals(df: pd.DataFrame, categorical_cols: list[str]) -> tuple[pd.DataFrame, dict]:
    """
    WHAT: Converts categorical text columns (product_type_name, colour...)
          into integer codes that XGBoost can consume.
    WHY:  XGBoost needs numeric input. We use simple label encoding
          (category -> integer) rather than one-hot, since one-hot on
          high-cardinality columns (like `prod_name`) would explode the
          feature space.
    HOW:  pandas `.astype('category').cat.codes`. We keep a mapping dict
          so we can decode / apply the same mapping to new data later.
    """
    out = df.copy()
    mappings: dict[str, dict] = {}

    for col in categorical_cols:
        if col not in out.columns:
            continue
        out[col] = out[col].astype("category")
        mappings[col] = dict(enumerate(out[col].cat.categories))
        out[col] = out[col].cat.codes

    return out, mappings


def build_feature_table(
    daily_demand: pd.DataFrame,
    categorical_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """
    WHAT: Runs the full feature engineering pipeline in the correct order.
    WHY:  Convenience wrapper used by the "Feature Engineering" dashboard
          page and by the model training step.
    """
    if categorical_cols is None:
        categorical_cols = [
            c
            for c in [
                "product_type_name",
                "product_group_name",
                "colour_group_name",
                "department_name",
                "section_name",
                "garment_group_name",
            ]
            if c in daily_demand.columns
        ]

    df = add_time_features(daily_demand)
    df = add_lag_rolling_features(df)
    df, mappings = encode_categoricals(df, categorical_cols)

    return df, mappings


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """
    WHAT: Returns the list of columns that should be fed into the model
          (i.e. everything except identifiers/date/target).
    """
    exclude = {"t_dat", "article_id", "demand"}
    return [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]
