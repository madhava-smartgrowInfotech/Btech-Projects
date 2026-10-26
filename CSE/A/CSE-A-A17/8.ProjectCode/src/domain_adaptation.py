"""
domain_adaptation.py
-----------------------
Implements a practical, explainable domain-adaptation technique for
tabular retail demand forecasting: IMPORTANCE-WEIGHTED DOMAIN ADAPTATION.

THE IDEA IN PLAIN LANGUAGE
---------------------------
We have a SOURCE domain (e.g. sales_channel_id = 2) with lots of training
data, and a TARGET domain (e.g. sales_channel_id = 1) we actually care
about but which may behave differently (different price points, product
mix, customer habits, etc.) -- this difference is called "distribution
shift".

If we train only on source data, the model may perform poorly on target
data because it learned patterns specific to the source domain.

Instead of throwing away the source data, we re-weight it: source rows
that "look like" they could belong to the target domain get a HIGHER
weight during training, and source rows that look very source-specific
get a LOWER weight. This nudges the model to pay more attention to the
part of the source data that's actually relevant to the target domain.

THE MATH (kept simple)
------------------------
1. Build a binary dataset: source rows labeled 0, target rows labeled 1
   (using only the FEATURE columns, not the demand target).
2. Train a Logistic Regression "domain classifier" to predict this label.
   If it can't tell source from target apart (accuracy near 50%), there's
   little distribution shift. If it easily tells them apart (accuracy near
   100%), the shift is large.
3. For each source row, ask the classifier: P(this row looks like target).
   Call this p. The importance weight is:

        weight = p / (1 - p)

   Intuition: if a source row looks very "target-like" (p close to 1),
   its weight becomes large -- it's treated as if it were more like a
   target example. If a source row looks nothing like target (p close
   to 0), its weight shrinks toward 0 -- the model mostly ignores it.
4. Train XGBoost on the source data using these weights via
   `sample_weight`, then evaluate on real target data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def split_domains(df: pd.DataFrame, domain_col: str, source_value, target_value) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    WHAT: Splits the feature table into source-domain and target-domain
          subsets based on a chosen column (e.g. sales_channel_id).
    WHY:  The user picks which real-world split represents "source" vs
          "target" (channel, department, time period, etc.) from the UI.
    """
    source_df = df[df[domain_col] == source_value].copy()
    target_df = df[df[domain_col] == target_value].copy()
    return source_df, target_df


def train_domain_classifier(
    source_features: pd.DataFrame, target_features: pd.DataFrame
) -> tuple[LogisticRegression, float]:
    """
    WHAT: Trains a Logistic Regression classifier to distinguish source (0)
          from target (1) rows, using only the model's feature columns.
    WHY:  Its accuracy tells us HOW DIFFERENT the two domains actually
          are. Its predicted probabilities become our importance weights.
    """
    X = pd.concat([source_features, target_features], axis=0)
    y = np.array([0] * len(source_features) + [1] * len(target_features))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)

    acc = accuracy_score(y_test, clf.predict(X_test))
    return clf, acc


def compute_instance_weights(
    domain_classifier: LogisticRegression, source_features: pd.DataFrame, clip_max: float = 20.0
) -> np.ndarray:
    """
    WHAT: Converts domain-classifier probabilities into per-row importance
          weights: weight = p_target / (1 - p_target).
    WHY:  Rows the classifier is unsure about (or thinks look "target-like")
          get up-weighted; clearly source-only rows get down-weighted.
    HOW:  We clip the ratio to `clip_max` to avoid a handful of rows (where
          p is very close to 1) dominating the loss function and making
          training unstable.
    """
    p_target = domain_classifier.predict_proba(source_features)[:, 1]
    p_target = np.clip(p_target, 1e-6, 1 - 1e-6)  # avoid divide-by-zero
    weights = p_target / (1 - p_target)
    weights = np.clip(weights, 0, clip_max)
    return weights


def domain_shift_summary(source_features: pd.DataFrame, target_features: pd.DataFrame) -> pd.DataFrame:
    """
    WHAT: Builds a per-feature comparison table (mean/std in each domain,
          and the absolute difference in means) for the "Domain Shift
          Analysis" page.
    WHY:  Gives a concrete, numeric answer to "what actually changed
          between source and target?" rather than just an accuracy number.
    """
    common_cols = [c for c in source_features.columns if c in target_features.columns]

    rows = []
    for col in common_cols:
        s_mean, s_std = source_features[col].mean(), source_features[col].std()
        t_mean, t_std = target_features[col].mean(), target_features[col].std()
        rows.append(
            {
                "feature": col,
                "source_mean": s_mean,
                "target_mean": t_mean,
                "mean_diff": abs(s_mean - t_mean),
                "source_std": s_std,
                "target_std": t_std,
            }
        )

    summary = pd.DataFrame(rows).sort_values("mean_diff", ascending=False)
    return summary


def train_adapted_model(source_X, source_y, weights, params: dict | None = None):
    """Convenience wrapper: trains XGBoost on source data using the computed instance weights."""
    from src.xgboost_model import train_xgboost

    return train_xgboost(source_X, source_y, params=params, sample_weight=weights)
