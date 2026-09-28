"""Train the Random Forest heart-disease risk model.

Usage: python ml/train_heart.py
Outputs: models/heart_rf.joblib, experiments/heart/metrics.json, experiments/heart/split.json
Note: the Kaggle CSV has 1025 rows but only ~302 unique patients (rows are repeated), so duplicates are
removed before splitting to avoid the same patient appearing in both train and test.
The Kaggle "target" column is inverted relative to the UCI Cleveland source (target=1 means no disease;
verified by matching all 302 unique rows against processed.cleveland.data), so disease = 1 - target.
"""
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

from common import ROOT, SEED, binary_metrics, write_json

from app.services.heart import FEATURES

DATA = ROOT / "data" / "heart" / "heart.csv"
EXP = ROOT / "experiments" / "heart"


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA).drop_duplicates().reset_index(drop=True)
    df["disease"] = 1 - df["target"]
    return df


def split(df: pd.DataFrame):
    idx = np.arange(len(df))
    return train_test_split(idx, test_size=0.25, stratify=df["disease"], random_state=SEED)


def make_model() -> RandomForestClassifier:
    return RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=3, random_state=SEED, n_jobs=-1)


def main():
    raw_rows = len(pd.read_csv(DATA))
    df = load()
    tr, te = split(df)
    X, y = df[FEATURES], df["disease"].to_numpy()
    cv = cross_val_score(make_model(), X.iloc[tr], y[tr], cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
                         scoring="roc_auc")
    model = make_model().fit(X.iloc[tr], y[tr])
    test = binary_metrics(y[te], model.predict_proba(X.iloc[te])[:, 1], 0.5)
    importances = sorted(zip(FEATURES, model.feature_importances_), key=lambda t: -t[1])

    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump(model, ROOT / "models" / "heart_rf.joblib")
    write_json(EXP / "split.json", {"train": tr.tolist(), "test": te.tolist()})
    write_json(EXP / "metrics.json", {
        "model": "Random Forest (300 trees, max depth 6)",
        "dataset": f"Heart Disease Dataset: {raw_rows} rows, {len(df)} unique after removing duplicates",
        "split": {"train": len(tr), "test": len(te)},
        "cv_roc_auc_mean": round(float(cv.mean()), 4), "cv_roc_auc_std": round(float(cv.std()), 4),
        "test": test,
        "feature_importance": [{"feature": f, "importance": round(float(v), 4)} for f, v in importances],
    })
    print(f"CV AUC {cv.mean():.3f} +/- {cv.std():.3f}")
    print("Test:", {k: v for k, v in test.items() if k != "roc_curve"})


if __name__ == "__main__":
    main()
