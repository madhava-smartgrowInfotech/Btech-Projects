"""Train the Random Forest health-risk models (CPU, a few seconds).

Only features that can be read from a FHIR record are used, so the model can score
real patients in the unified record:
  heart:    age, sex, resting systolic BP, total cholesterol, fasting glucose > 120
  diabetes: pregnancies, glucose, diastolic BP, BMI, age
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

ROOT = Path(__file__).resolve().parents[1]
SEED = 42

SPECS = {
    "heart": {
        "csv": ROOT / "data" / "heart" / "heart.csv",
        "features": ["age", "sex", "trestbps", "chol", "fbs"],
        "labels": {"age": "Age", "sex": "Sex (male)", "trestbps": "Systolic blood pressure",
                   "chol": "Total cholesterol", "fbs": "Fasting glucose > 120 mg/dL"},
        "target": "target", "zero_is_missing": [],
    },
    "diabetes": {
        "csv": ROOT / "data" / "diabetes" / "diabetes.csv",
        "features": ["Pregnancies", "Glucose", "BloodPressure", "BMI", "Age"],
        "labels": {"Pregnancies": "Pregnancies", "Glucose": "Blood glucose", "BloodPressure": "Diastolic blood pressure",
                   "BMI": "Body mass index", "Age": "Age"},
        "target": "Outcome", "zero_is_missing": ["Glucose", "BloodPressure", "BMI"],
    },
}


def load(spec):
    with open(spec["csv"]) as f:
        header = f.readline().strip().split(",")
    raw = np.genfromtxt(spec["csv"], delimiter=",", skip_header=1, missing_values="?", filling_values=np.nan)
    cols = {h: raw[:, i] for i, h in enumerate(header)}
    X = np.column_stack([cols[f] for f in spec["features"]]).astype(float)
    y = (cols[spec["target"]] > 0).astype(int)
    for i, f in enumerate(spec["features"]):
        if f in spec["zero_is_missing"]:
            X[X[:, i] == 0, i] = np.nan
    keep = ~np.isnan(y)
    return X[keep], y[keep]


def train(name):
    spec = SPECS[name]
    X, y = load(spec)
    medians = np.nanmedian(X, axis=0)
    X = np.where(np.isnan(X), medians, X)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
    model = RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=3, random_state=SEED, n_jobs=-1)
    model.fit(Xtr, ytr)
    prob = model.predict_proba(Xte)[:, 1]
    pred = (prob >= 0.5).astype(int)
    cv = cross_val_score(RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=3, random_state=SEED, n_jobs=-1),
                         X, y, cv=StratifiedKFold(5, shuffle=True, random_state=SEED), scoring="roc_auc")
    metrics = {
        "model": "RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=3)",
        "dataset": spec["csv"].name, "rows": int(len(y)), "positive_rate": round(float(y.mean()), 3),
        "features": spec["features"],
        "test": {"accuracy": round(accuracy_score(yte, pred), 3), "precision": round(precision_score(yte, pred), 3),
                 "recall": round(recall_score(yte, pred), 3), "f1": round(f1_score(yte, pred), 3),
                 "roc_auc": round(roc_auc_score(yte, prob), 3)},
        "cv5_roc_auc_mean": round(float(cv.mean()), 3), "cv5_roc_auc_std": round(float(cv.std()), 3),
        "feature_importance": {f: round(float(v), 3) for f, v in zip(spec["features"], model.feature_importances_)},
    }
    model.fit(X, y)  # final model on all rows
    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump({"model": model, "features": spec["features"], "labels": spec["labels"],
                 "medians": medians.tolist()}, ROOT / "models" / f"{name}_rf.joblib")
    return metrics


def main():
    out = {name: train(name) for name in SPECS}
    (ROOT / "experiments").mkdir(exist_ok=True)
    (ROOT / "experiments" / "metrics.json").write_text(json.dumps(out, indent=2))
    json.dump(out, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
