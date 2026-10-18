"""
explainability.py
-------------------
Provides GLOBAL explanations ("what generally drives churn across all
customers") and LOCAL explanations ("why is THIS customer predicted to
churn") using SHAP where available, with safe fallbacks (permutation
importance / model coefficients) so the app still works on machines
where SHAP fails to install (a common issue on student laptops with
older C compilers).

Public functions
-----------------
get_shap_explainer(model, X_train_transformed, model_kind)
global_importance(model, X_test_transformed, y_test, feature_names, explainer=None)
local_explanation(explainer, model, x_row_transformed, feature_names, top_n=5)
"""

from __future__ import annotations
import numpy as np
import pandas as pd

try:
    import shap  # noqa: F401
    SHAP_AVAILABLE = True
except Exception:
    SHAP_AVAILABLE = False


TREE_MODEL_NAMES = {"Decision Tree", "Random Forest", "Gradient Boosting", "Hist Gradient Boosting"}


def get_shap_explainer(model, X_train_sample, model_name: str):
    """Build the appropriate SHAP explainer for the model type. Returns
    None if SHAP is unavailable or construction fails (caller should
    fall back to permutation/coefficient-based explanations)."""
    if not SHAP_AVAILABLE:
        return None
    try:
        if model_name in TREE_MODEL_NAMES:
            return shap.TreeExplainer(model)
        elif model_name == "Logistic Regression":
            return shap.LinearExplainer(model, X_train_sample)
        else:
            # Generic fallback: KernelExplainer is slow -- only use a small
            # background sample.
            bg = shap.sample(X_train_sample, min(50, X_train_sample.shape[0]))
            return shap.KernelExplainer(model.predict_proba, bg)
    except Exception:
        return None


def _shap_values_for_positive_class(explainer, X):
    """Normalize SHAP's various return shapes (list-per-class vs single
    array) into a single 2D array of contributions toward the positive
    (churn) class."""
    raw = explainer.shap_values(X)
    if isinstance(raw, list):
        # list of arrays, one per class -> take class 1 (churn)
        vals = raw[1] if len(raw) > 1 else raw[0]
    else:
        vals = raw
        if vals.ndim == 3:
            # shape (n_samples, n_features, n_classes)
            vals = vals[:, :, 1] if vals.shape[2] > 1 else vals[:, :, 0]
    return np.array(vals)


def global_importance(model, X_test_transformed, y_test, feature_names, model_name: str, explainer=None, max_shap_rows: int = 200):
    """Compute global feature importance from up to three sources:
    - model's built-in feature_importances_ (tree models) or |coef_| (LR)
    - permutation importance on the test set
    - mean |SHAP value| across a sample of the test set (if SHAP works)

    Returns a dict of DataFrames, each with columns [feature, importance],
    sorted descending, so the UI can show whichever are available.
    """
    from sklearn.inspection import permutation_importance

    out = {}

    # 1) Built-in importance
    if hasattr(model, "feature_importances_"):
        out["model_importance"] = pd.DataFrame({
            "feature": feature_names, "importance": model.feature_importances_
        }).sort_values("importance", ascending=False)
    elif hasattr(model, "coef_"):
        out["model_importance"] = pd.DataFrame({
            "feature": feature_names, "importance": np.abs(model.coef_).ravel()
        }).sort_values("importance", ascending=False)

    # 2) Permutation importance (model-agnostic, works for every model type)
    try:
        n = min(300, X_test_transformed.shape[0])
        idx = np.random.RandomState(42).choice(X_test_transformed.shape[0], n, replace=False)
        Xs = X_test_transformed[idx] if not hasattr(X_test_transformed, "iloc") else X_test_transformed.iloc[idx]
        ys = y_test[idx] if not hasattr(y_test, "iloc") else y_test.iloc[idx]
        perm = permutation_importance(model, Xs, ys, n_repeats=5, random_state=42, n_jobs=-1)
        out["permutation_importance"] = pd.DataFrame({
            "feature": feature_names, "importance": perm.importances_mean
        }).sort_values("importance", ascending=False)
    except Exception:
        pass

    # 3) SHAP global importance
    if explainer is not None:
        try:
            n = min(max_shap_rows, X_test_transformed.shape[0])
            Xs = X_test_transformed[:n]
            shap_vals = _shap_values_for_positive_class(explainer, Xs)
            mean_abs = np.abs(shap_vals).mean(axis=0)
            out["shap_importance"] = pd.DataFrame({
                "feature": feature_names, "importance": mean_abs
            }).sort_values("importance", ascending=False)
        except Exception:
            pass

    return out


def local_explanation(explainer, model, x_row_transformed, feature_names, top_n: int = 5):
    """Explain a single customer's prediction. Returns
    (top_positive: list[(feature, value)], top_negative: list[(feature, value)])
    where 'positive' means the feature pushed the prediction TOWARD
    churn and 'negative' means it pushed AWAY from churn.

    Falls back to a coefficient/importance x value heuristic if SHAP is
    unavailable, so the app remains functional either way.
    """
    x_row_transformed = np.atleast_2d(x_row_transformed)

    if explainer is not None:
        try:
            shap_vals = _shap_values_for_positive_class(explainer, x_row_transformed)[0]
            pairs = list(zip(feature_names, shap_vals))
            pairs.sort(key=lambda p: p[1], reverse=True)
            top_pos = [(f, v) for f, v in pairs if v > 0][:top_n]
            top_neg = [(f, v) for f, v in pairs if v < 0][-top_n:][::-1]
            return top_pos, top_neg, "shap"
        except Exception:
            pass

    # ---- Fallback: importance-weighted feature value heuristic ----
    if hasattr(model, "feature_importances_"):
        base_importance = model.feature_importances_
    elif hasattr(model, "coef_"):
        base_importance = model.coef_.ravel()
    else:
        base_importance = np.ones(len(feature_names))

    contrib = base_importance * x_row_transformed[0]
    pairs = list(zip(feature_names, contrib))
    pairs.sort(key=lambda p: p[1], reverse=True)
    top_pos = [(f, v) for f, v in pairs if v > 0][:top_n]
    top_neg = [(f, v) for f, v in pairs if v < 0][-top_n:][::-1]
    return top_pos, top_neg, "approximate"


def clean_feature_label(raw_name: str) -> str:
    """Turn a ColumnTransformer output name like
    'cat__Contract_Month-to-month' into a friendlier 'Contract: Month-to-month'."""
    name = raw_name
    for prefix in ("num__", "cat__"):
        if name.startswith(prefix):
            name = name[len(prefix):]
    if "_" in name:
        # Try to split at the last underscore that looks like a category split
        parts = name.split("_", 1)
        return f"{parts[0]}: {parts[1]}" if len(parts) == 2 else name
    return name
