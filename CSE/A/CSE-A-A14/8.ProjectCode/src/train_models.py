"""
train_models.py
------------------
Trains and compares several classification models (Logistic Regression,
Decision Tree, Random Forest, and optionally Gradient Boosting /
HistGradientBoosting) on the preprocessed data, using a shared
train/test split so comparisons are fair.

Every model is wrapped so it exposes predict_proba, which the rest of
the application relies on for churn-probability scoring.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier

from evaluation import evaluate_model


MODEL_REGISTRY = {
    "Logistic Regression": lambda class_weight=None: LogisticRegression(
        max_iter=2000, class_weight=class_weight, random_state=42
    ),
    "Decision Tree": lambda class_weight=None: DecisionTreeClassifier(
        max_depth=8, min_samples_leaf=10, class_weight=class_weight, random_state=42
    ),
    "Random Forest": lambda class_weight=None: RandomForestClassifier(
        n_estimators=300, max_depth=12, min_samples_leaf=5,
        class_weight=class_weight, random_state=42, n_jobs=-1
    ),
    "Gradient Boosting": lambda class_weight=None: GradientBoostingClassifier(
        n_estimators=200, max_depth=3, learning_rate=0.08, random_state=42
    ),
    "Hist Gradient Boosting": lambda class_weight=None: HistGradientBoostingClassifier(
        max_depth=6, learning_rate=0.08, random_state=42
    ),
}

REQUIRED_MODELS = ["Logistic Regression", "Decision Tree", "Random Forest"]
OPTIONAL_MODELS = ["Gradient Boosting", "Hist Gradient Boosting"]


def train_selected_models(
    X_train, y_train, X_test, y_test,
    model_names: list,
    imbalance_strategy: str = "class_weight",   # "none" | "class_weight" | "smote"
):
    """Train each requested model and evaluate it on the held-out test
    set. Returns (trained_models: dict, results: dict[name -> metrics]).

    imbalance_strategy:
      - "class_weight": pass class_weight='balanced' to models that support it
      - "smote": oversample the (already-preprocessed, numeric) X_train via SMOTE
      - "none": train as-is
    """
    trained_models = {}
    results = {}

    X_tr, y_tr = X_train, y_train
    if imbalance_strategy == "smote":
        from preprocessing import apply_smote
        X_tr, y_tr = apply_smote(X_train, y_train)

    class_weight = "balanced" if imbalance_strategy == "class_weight" else None

    for name in model_names:
        if name not in MODEL_REGISTRY:
            continue
        builder = MODEL_REGISTRY[name]
        # Gradient boosting variants don't accept class_weight
        try:
            model = builder(class_weight=class_weight)
        except TypeError:
            model = builder()

        model.fit(X_tr, y_tr)
        trained_models[name] = model
        results[name] = evaluate_model(model, X_test, y_test)

    return trained_models, results


def select_best_model(results: dict, metric: str = "f1_score"):
    """Pick the model with the highest value of `metric` (not accuracy
    alone, per project requirement -- default is F1)."""
    if not results:
        return None
    best_name = max(results, key=lambda k: results[k][metric])
    return best_name
