"""Model definitions + training helpers."""
from __future__ import annotations

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier


def get_models():
    models = {
        "Logistic Regression": LogisticRegression(solver="lbfgs", class_weight="balanced", max_iter=1000, C=1.0),
        "Decision Tree": DecisionTreeClassifier(max_depth=8, min_samples_split=10, min_samples_leaf=5,
                                                class_weight="balanced", random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                                min_samples_leaf=2, n_jobs=-1, random_state=42),
    }
    try:
        from xgboost import XGBClassifier
        models["XGBoost"] = XGBClassifier(
            n_estimators=400, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
            eval_metric="logloss", n_jobs=-1, random_state=42)
    except Exception:
        from sklearn.ensemble import HistGradientBoostingClassifier
        models["XGBoost (fallback HGB)"] = HistGradientBoostingClassifier(
            max_iter=400, max_depth=6, learning_rate=0.05, l2_regularization=1.0, random_state=42)
    return models
