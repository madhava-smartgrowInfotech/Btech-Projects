"""
baseline_models.py
--------------------
Simple baseline models to compare XGBoost against, plus the chronological
train/test split utility used by every model in this project.

WHY chronological split instead of random train_test_split:
This is a time-series forecasting problem. If we randomly shuffled rows
into train/test, the model could "see the future" -- e.g. train on a
Tuesday in week 10 and test on a Monday in week 9, which never happens
in real deployment (you never have next week's data when forecasting
this week). A chronological split (train = earlier dates, test = later
dates) mimics how the model will actually be used in production.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def chronological_split(
    df: pd.DataFrame, date_col: str = "t_dat", train_fraction: float = 0.8
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    WHAT: Splits `df` into train/test sets based on date, not randomly.
    HOW:  Sort unique dates, take the first `train_fraction` of them for
          training, the remainder for testing.

    Returns (train_df, test_df).
    """
    df = df.sort_values(date_col)
    unique_dates = df[date_col].drop_duplicates().sort_values()
    split_idx = int(len(unique_dates) * train_fraction)
    split_date = unique_dates.iloc[split_idx]

    train_df = df[df[date_col] < split_date]
    test_df = df[df[date_col] >= split_date]
    return train_df, test_df


def split_summary(train_df: pd.DataFrame, test_df: pd.DataFrame, date_col: str = "t_dat") -> dict:
    """Returns a small dict describing the date ranges of each split, for display in the UI."""
    return {
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "train_start": train_df[date_col].min() if not train_df.empty else None,
        "train_end": train_df[date_col].max() if not train_df.empty else None,
        "test_start": test_df[date_col].min() if not test_df.empty else None,
        "test_end": test_df[date_col].max() if not test_df.empty else None,
    }


def moving_average_forecast(train_df: pd.DataFrame, test_df: pd.DataFrame, window: int = 7) -> np.ndarray:
    """
    WHAT: A naive baseline -- predicts each test row's demand as the
          article's average demand over its last `window` days in the
          training set (falling back to the article's overall training
          mean, then the global mean, if not enough history exists).
    WHY:  Any "real" model (XGBoost) should beat this simple baseline;
          if it doesn't, that's an important, honest finding to report.
    """
    recent_avg = (
        train_df.sort_values("t_dat")
        .groupby("article_id")["demand"]
        .apply(lambda s: s.tail(window).mean())
    )
    overall_avg = train_df.groupby("article_id")["demand"].mean()
    global_avg = train_df["demand"].mean()

    def predict_row(article_id):
        if article_id in recent_avg.index and not np.isnan(recent_avg[article_id]):
            return recent_avg[article_id]
        if article_id in overall_avg.index:
            return overall_avg[article_id]
        return global_avg

    return test_df["article_id"].map(predict_row).values


def train_random_forest(X_train, y_train, n_estimators: int = 200, max_depth: int = 10):
    """Optional baseline: RandomForestRegressor, useful as a second sanity check."""
    from sklearn.ensemble import RandomForestRegressor

    model = RandomForestRegressor(
        n_estimators=n_estimators, max_depth=max_depth, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model


def train_lightgbm(X_train, y_train, **params):
    """
    Optional baseline: LightGBM. Import is guarded so the app still works
    if lightgbm isn't installed in the deployment environment.
    """
    try:
        import lightgbm as lgb
    except ImportError:
        return None

    default_params = dict(n_estimators=300, max_depth=8, learning_rate=0.05, random_state=42)
    default_params.update(params)
    model = lgb.LGBMRegressor(**default_params)
    model.fit(X_train, y_train)
    return model
