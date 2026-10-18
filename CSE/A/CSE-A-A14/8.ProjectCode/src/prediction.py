"""
prediction.py
--------------
Wraps the trained preprocessor + model to score arbitrary customer
dataframes with churn probabilities, and provides batch-prediction /
what-if scoring helpers.
"""

from __future__ import annotations
import numpy as np
import pandas as pd


def score_customers(df_features: pd.DataFrame, preprocessor, model) -> np.ndarray:
    """Return churn probability (0-100 scale) for each row of
    df_features (raw, untransformed feature columns)."""
    X_t = preprocessor.transform(df_features)
    proba = model.predict_proba(X_t)[:, 1]
    return np.round(proba * 100, 2)


def score_single_customer(customer_row: pd.Series, feature_cols: list, preprocessor, model) -> float:
    df_row = pd.DataFrame([customer_row[feature_cols]])
    return float(score_customers(df_row, preprocessor, model)[0])


def validate_columns_for_prediction(new_df: pd.DataFrame, required_cols: list) -> list:
    """Check that a newly-uploaded dataframe (for batch prediction) has
    the columns the trained model expects. Returns a list of problems."""
    problems = []
    missing = [c for c in required_cols if c not in new_df.columns]
    if missing:
        problems.append(f"Missing expected column(s): {', '.join(missing)}")
    return problems


def build_batch_predictions(
    new_df: pd.DataFrame, feature_cols: list, preprocessor, model,
    id_col: str | None, thresholds: dict, top_driver_lookup=None,
) -> pd.DataFrame:
    """Score a batch of new customers and assemble the standard output
    table: customerID, churn_probability, predicted_churn, risk_category,
    top_risk_factor_1..3 (if a SHAP explainer / top_driver_lookup fn is
    supplied)."""
    from utils import assign_risk_series

    work = new_df.copy()
    proba = score_customers(work[feature_cols], preprocessor, model)
    out = pd.DataFrame()
    out["customerID"] = work[id_col] if id_col and id_col in work.columns else np.arange(len(work))
    out["churn_probability"] = proba
    out["predicted_churn"] = np.where(proba >= 50, "Yes", "No")
    out["risk_category"] = assign_risk_series(out["churn_probability"], thresholds)

    if top_driver_lookup is not None:
        drivers = [top_driver_lookup(work.iloc[i]) for i in range(len(work))]
        for k in range(3):
            out[f"top_risk_factor_{k+1}"] = [d[k] if len(d) > k else "" for d in drivers]
    else:
        for k in range(3):
            out[f"top_risk_factor_{k+1}"] = ""

    return out.sort_values("churn_probability", ascending=False).reset_index(drop=True)
