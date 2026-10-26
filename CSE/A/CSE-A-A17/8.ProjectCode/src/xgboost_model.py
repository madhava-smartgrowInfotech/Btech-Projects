"""
xgboost_model.py
-------------------
Trains the main XGBoost demand-forecasting model, and provides a
hyperparameter tuning routine that respects chronological order
(using sklearn's TimeSeriesSplit instead of regular KFold, so tuning
never trains on future data and validates on the past).
"""

from __future__ import annotations

import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit


DEFAULT_PARAMS = dict(
    n_estimators=300,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42,
    n_jobs=-1,
)


def train_xgboost(X_train, y_train, params: dict | None = None, sample_weight=None) -> XGBRegressor:
    """
    WHAT: Trains a single XGBoost regressor with the given parameters.
    WHY:  XGBoost handles the mix of numeric + encoded-categorical
          features well and is fast even on large tabular datasets.
    HOW:  Straightforward .fit(). `sample_weight` is optional and is what
          the domain-adaptation module uses to re-weight source-domain
          rows that look more "target-like".
    """
    final_params = dict(DEFAULT_PARAMS)
    if params:
        final_params.update(params)

    model = XGBRegressor(**final_params)
    model.fit(X_train, y_train, sample_weight=sample_weight)
    return model


def tune_xgboost(
    X_train,
    y_train,
    n_iter: int = 15,
    cv_splits: int = 3,
) -> tuple[XGBRegressor, dict]:
    """
    WHAT: Searches over a range of XGBoost hyperparameters to find a
          better-performing configuration than the defaults.
    WHY:  The suggested starting parameters are a reasonable guess, not
          guaranteed optimal -- tuning can meaningfully improve accuracy.
    HOW:  RandomizedSearchCV with TimeSeriesSplit as the cross-validation
          strategy. TimeSeriesSplit creates folds where each validation
          fold is always *later in time* than its training fold -- this
          is what keeps tuning free of time-series leakage (a regular
          KFold would randomly mix past/future rows and give an overly
          optimistic, leaky score).
    """
    param_distributions = {
        "n_estimators": [100, 200, 300, 400, 500],
        "max_depth": [4, 6, 8, 10, 12],
        "learning_rate": [0.01, 0.03, 0.05, 0.1, 0.2],
        "subsample": [0.6, 0.7, 0.8, 0.9, 1.0],
        "colsample_bytree": [0.6, 0.7, 0.8, 0.9, 1.0],
        "min_child_weight": [1, 3, 5, 7],
    }

    base_model = XGBRegressor(objective="reg:squarederror", random_state=42, n_jobs=-1)
    tscv = TimeSeriesSplit(n_splits=cv_splits)

    search = RandomizedSearchCV(
        base_model,
        param_distributions=param_distributions,
        n_iter=n_iter,
        cv=tscv,
        scoring="neg_root_mean_squared_error",
        random_state=42,
        n_jobs=-1,
    )
    search.fit(X_train, y_train)

    return search.best_estimator_, search.best_params_


def get_feature_importance(model: XGBRegressor, feature_names: list[str], top_n: int = 20):
    """Returns a sorted (feature, importance) list, top_n only, for the Feature Importance chart."""
    importances = model.feature_importances_
    pairs = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    return pairs[:top_n]
