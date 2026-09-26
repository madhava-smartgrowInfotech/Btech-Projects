"""Stage 2 - train and compare Random Forest, XGBoost and Logistic Regression.

Objective 3 of the project: the three classifiers are trained on the same
feature matrix and compared on accuracy, precision, recall, F1-score
(and ROC-AUC). The best model by F1 is saved as `models/best_model.joblib`
and is what the detector uses at run time.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import config
from .features import FEATURE_NAMES

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:  # pragma: no cover
    from sklearn.ensemble import GradientBoostingClassifier
    HAS_XGB = False


def build_models() -> dict:
    models = {
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=None, min_samples_leaf=1, n_jobs=-1,
            class_weight="balanced", random_state=config.RANDOM_STATE,
        ),
        "logistic_regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, C=1.0, class_weight="balanced",
                               random_state=config.RANDOM_STATE),
        ),
    }
    if HAS_XGB:
        models["xgboost"] = XGBClassifier(
            n_estimators=400, max_depth=8, learning_rate=0.08, subsample=0.9,
            colsample_bytree=0.9, eval_metric="logloss", n_jobs=-1,
            random_state=config.RANDOM_STATE,
        )
    else:  # fallback if xgboost isn't installed
        models["xgboost"] = GradientBoostingClassifier(
            n_estimators=300, max_depth=5, random_state=config.RANDOM_STATE)
    return models


def evaluate(model, X_test, y_test) -> dict:
    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    return {
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, proba)), 4),
        "false_positive_rate": round(float(fp / max(fp + tn, 1)), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def feature_importances(model, top=15) -> list[dict]:
    est = model
    if hasattr(model, "steps"):  # pipeline (logistic regression)
        est = model.steps[-1][1]
    if hasattr(est, "feature_importances_"):
        imp = np.asarray(est.feature_importances_, dtype=float)
    elif hasattr(est, "coef_"):
        imp = np.abs(np.asarray(est.coef_).ravel())
    else:
        return []
    imp = imp / (imp.sum() or 1)
    order = np.argsort(imp)[::-1][:top]
    return [{"feature": FEATURE_NAMES[i], "importance": round(float(imp[i]), 4)} for i in order]


def train_all(X_train, y_train, X_test, y_test, meta: dict | None = None, verbose=True) -> dict:
    """Train every model, evaluate, persist artefacts and return the metrics dict."""
    config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    results, trained = {}, {}
    for name, model in build_models().items():
        t0 = time.time()
        if verbose:
            print(f"  training {name} ...", end=" ", flush=True)
        model.fit(X_train, y_train)
        m = evaluate(model, X_test, y_test)
        m["train_seconds"] = round(time.time() - t0, 1)
        m["top_features"] = feature_importances(model)
        results[name] = m
        trained[name] = model
        joblib.dump(model, config.MODEL_FILES[name])
        if verbose:
            print(f"acc={m['accuracy']:.4f} prec={m['precision']:.4f} "
                  f"rec={m['recall']:.4f} f1={m['f1']:.4f} ({m['train_seconds']}s)")

    best = max(results, key=lambda k: (results[k]["f1"], results[k]["roc_auc"]))
    joblib.dump({"name": best, "model": trained[best], "features": FEATURE_NAMES},
                config.BEST_MODEL_FILE)

    previous = load_metrics()
    version = (previous.get("model_version", 0) + 1) if previous else 1
    summary = {
        "model_version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "best_model": best,
        "n_features": len(FEATURE_NAMES),
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
        "xgboost_available": HAS_XGB,
        "models": results,
    }
    if meta:
        summary.update(meta)
    config.METRICS_JSON.write_text(json.dumps(summary, indent=2))
    if verbose:
        print(f"  best model: {best}  (saved to {config.BEST_MODEL_FILE.name}, version {version})")
    return summary


def load_metrics() -> dict:
    if config.METRICS_JSON.exists():
        return json.loads(config.METRICS_JSON.read_text())
    return {}
