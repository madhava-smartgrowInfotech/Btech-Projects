"""Reproducible experiment run for the project documentation.

Uses the project's own src/ functions (same preprocessing, same model registry, same split rule as the
app's Model Training page) on data/customer_churn.csv and writes experiments/churn_synthetic/metrics.json.

    python scripts/run_experiments.py
"""
import json
import os
import platform
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(os.cpu_count() or 1))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import sklearn  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402

from data_loader import detect_id_column, detect_target_column, detect_column_types, normalize_target, profile_dataset  # noqa: E402
from evaluation import evaluate_model  # noqa: E402
from explainability import global_importance, clean_feature_label  # noqa: E402
from preprocessing import build_preprocessor, class_distribution, clean_missing_and_duplicates, get_feature_names, train_test_split_data  # noqa: E402
from prediction import score_customers  # noqa: E402
from risk_segmentation import risk_distribution_summary  # noqa: E402
from train_models import MODEL_REGISTRY, train_selected_models, select_best_model  # noqa: E402
from utils import DEFAULT_RISK_THRESHOLDS, assign_risk_series  # noqa: E402

OUT_DIR = os.path.join(ROOT, "experiments", "churn_synthetic")
os.makedirs(OUT_DIR, exist_ok=True)
ALL = list(MODEL_REGISTRY)
METRICS = ("accuracy", "precision", "recall", "f1_score", "roc_auc")


def pick(m):
    return {k: round(float(m[k]), 4) for k in METRICS}


df = pd.read_csv(os.path.join(ROOT, "data", "customer_churn.csv"))
profile = profile_dataset(df)
target, idc = profile.target_col, profile.id_col
df, clean = clean_missing_and_duplicates(df)
num, cat = detect_column_types(df, target, idc)
feats = num + cat
y = normalize_target(df, target)

out = {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "environment": {"python": platform.python_version(), "sklearn": sklearn.__version__, "pandas": pd.__version__,
                    "numpy": np.__version__, "os": platform.platform(), "cpu_count": os.cpu_count()},
    "dataset": {
        "file": "data/customer_churn.csv", "origin": "synthetic, produced by src/sample_data.py (seed 42)",
        "rows": int(len(df)), "columns": int(df.shape[1]), "duplicates_removed": clean["duplicates_removed"],
        "missing_cells": clean["missing_before"], "target": target, "id_col": idc,
        "numeric_features": num, "categorical_features": cat, "n_features_raw": len(feats),
        "class_distribution": class_distribution(y),
        "churn_rate_pct": round(100 * float(y.mean()), 2),
    },
}
out["dataset"]["class_distribution"]["counts"] = {str(k): int(v) for k, v in out["dataset"]["class_distribution"]["counts"].items()}
out["dataset"]["class_distribution"]["percentages"] = {str(k): float(v) for k, v in out["dataset"]["class_distribution"]["percentages"].items()}

# ---------------------------------------------------------------- A. app defaults: 80/20 split, seed 42
X_train, X_test, y_train, y_test = train_test_split_data(df[feats], y, test_size=0.2)
pre = build_preprocessor(num, cat)
Xtr = pre.fit_transform(X_train)
Xte = pre.transform(X_test)
fnames = get_feature_names(pre)
out["split"] = {"test_size": 0.2, "random_state": 42, "stratified": True, "train_rows": int(len(X_train)),
                "test_rows": int(len(X_test)), "test_churners": int(y_test.sum()),
                "encoded_feature_count": int(Xtr.shape[1])}

by_strategy = {}
trained_cache = {}
for strategy in ("class_weight", "smote", "none"):
    t0 = time.perf_counter()
    models, results = {}, {}
    for name in ALL:
        t1 = time.perf_counter()
        m, r = train_selected_models(Xtr, y_train.values, Xte, y_test.values, [name], imbalance_strategy=strategy)
        models.update(m)
        results.update(r)
        results[name]["fit_seconds"] = time.perf_counter() - t1
    rows = {}
    for name, r in results.items():
        cm = np.asarray(r["confusion_matrix"]).tolist()
        rows[name] = {**pick(r), "confusion_matrix": cm, "fit_and_eval_seconds": round(r["fit_seconds"], 3)}
    by_strategy[strategy] = {
        "models": rows,
        "best_by_f1": select_best_model(results, "f1_score"),
        "best_by_roc_auc": select_best_model(results, "roc_auc"),
        "best_by_recall": select_best_model(results, "recall"),
        "wall_seconds": round(time.perf_counter() - t0, 2),
    }
    trained_cache[strategy] = (models, results)
out["app_default_split"] = by_strategy

# ---------------------------------------------------------------- B. repeated stratified 5-fold CV (3 required models, class_weight)
folds = []
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
per_model = {n: {k: [] for k in METRICS} for n in ("Logistic Regression", "Decision Tree", "Random Forest")}
for tr, te in skf.split(df[feats], y):
    p = build_preprocessor(num, cat)
    a = p.fit_transform(df[feats].iloc[tr])
    b = p.transform(df[feats].iloc[te])
    _, res = train_selected_models(a, y.iloc[tr].values, b, y.iloc[te].values, list(per_model), imbalance_strategy="class_weight")
    for n, r in res.items():
        for k in METRICS:
            per_model[n][k].append(float(r[k]))
out["cross_validation_5fold_class_weight"] = {
    n: {k: {"mean": round(float(np.mean(v)), 4), "std": round(float(np.std(v, ddof=1)), 4)} for k, v in d.items()}
    for n, d in per_model.items()
}

# ---------------------------------------------------------------- C. five random splits (seeds 0-4), 3 required models
seeds = {n: {k: [] for k in METRICS} for n in per_model}
for seed in range(5):
    a_tr, a_te, b_tr, b_te = __import__("sklearn.model_selection", fromlist=["train_test_split"]).train_test_split(
        df[feats], y, test_size=0.2, random_state=seed, stratify=y)
    p = build_preprocessor(num, cat)
    _, res = train_selected_models(p.fit_transform(a_tr), b_tr.values, p.transform(a_te), b_te.values, list(seeds),
                                   imbalance_strategy="class_weight")
    for n, r in res.items():
        for k in METRICS:
            seeds[n][k].append(float(r[k]))
out["repeated_random_splits_5_seeds_class_weight"] = {
    n: {k: {"mean": round(float(np.mean(v)), 4), "std": round(float(np.std(v, ddof=1)), 4)} for k, v in d.items()}
    for n, d in seeds.items()
}

# ---------------------------------------------------------------- D. best model (class_weight): importance, risk bands, latency
models, results = trained_cache["class_weight"]
best = select_best_model(results, "f1_score")
model = models[best]
imp = global_importance(model, Xte, y_test.values, fnames, best)
out["best_model"] = {"name": best, "selection_metric": "f1_score", "strategy": "class_weight"}
out["importance"] = {
    k: [{"feature": clean_feature_label(r.feature), "importance": round(float(r.importance), 5)} for r in v.head(10).itertuples()]
    for k, v in imp.items()
}
proba = score_customers(df[feats], pre, model)
risk = assign_risk_series(pd.Series(proba), DEFAULT_RISK_THRESHOLDS)
rt = pd.DataFrame({"churn_probability": proba, "risk_category": risk})
rt["risk_category"] = pd.Categorical(rt["risk_category"], categories=["Low Risk", "Medium Risk", "High Risk", "Critical Risk"], ordered=True)
out["risk_bands_default_thresholds"] = {"thresholds": DEFAULT_RISK_THRESHOLDS, **{k: v for k, v in risk_distribution_summary(rt).items()}}
out["risk_bands_default_thresholds"]["counts"] = {k: int(v) for k, v in out["risk_bands_default_thresholds"]["counts"].items()}

# the app scores a held-out customer for single-customer pages: time it (model + preprocessor only)
one = df[feats].iloc[[0]]
score_customers(one, pre, model)
t = []
for _ in range(200):
    s = time.perf_counter()
    score_customers(one, pre, model)
    t.append((time.perf_counter() - s) * 1000)
out["inference_latency_ms"] = {"single_customer_median": round(float(np.median(t)), 2), "single_customer_p95": round(float(np.percentile(t, 95)), 2),
                               "runs": 200, "model": best}
s = time.perf_counter()
score_customers(df[feats], pre, model)
out["inference_latency_ms"]["full_dataset_1000_rows_ms"] = round((time.perf_counter() - s) * 1000, 1)

with open(os.path.join(OUT_DIR, "metrics.json"), "w", encoding="utf8") as fh:
    json.dump(out, fh, indent=2)
print("wrote", os.path.join(OUT_DIR, "metrics.json"))
print(json.dumps({k: out[k] for k in ("best_model", "split")}, indent=2))
for s, d in by_strategy.items():
    print(s, d["best_by_f1"])
    for n, r in d["models"].items():
        print("  ", n, {k: r[k] for k in METRICS})
