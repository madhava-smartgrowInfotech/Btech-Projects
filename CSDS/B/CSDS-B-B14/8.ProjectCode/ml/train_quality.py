"""Train the water-quality stacking ensemble (RF, XGBoost, GBM, Decision Tree -> logistic meta-learner)."""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, StackingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.quality import FEATURES  # noqa: E402

SEED = 42


def members():
    return [
        ("random_forest", RandomForestClassifier(n_estimators=300, min_samples_leaf=2, random_state=SEED, n_jobs=-1)),
        ("xgboost", XGBClassifier(n_estimators=300, learning_rate=0.05, max_depth=5, subsample=0.8,
                                  colsample_bytree=0.8, random_state=SEED, n_jobs=4, eval_metric="logloss")),
        ("gradient_boosting", GradientBoostingClassifier(n_estimators=200, max_depth=3, random_state=SEED)),
        ("decision_tree", DecisionTreeClassifier(max_depth=6, min_samples_leaf=10, random_state=SEED)),
    ]


def scores(y, p):
    return {"accuracy": round(accuracy_score(y, p >= 0.5), 4), "f1": round(f1_score(y, p >= 0.5), 4),
            "roc_auc": round(roc_auc_score(y, p), 4)}


def main():
    df = pd.read_csv(ROOT / "data" / "water_potability.csv")
    X, y = df[FEATURES], df["Potability"].astype(int)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
    model = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("stack", StackingClassifier(estimators=members(), final_estimator=LogisticRegression(max_iter=1000),
                                     cv=5, stack_method="predict_proba", n_jobs=1)),
    ])
    model.fit(Xtr, ytr)
    p = model.predict_proba(Xte)[:, 1]
    metrics = {"dataset": "Kaggle Water Potability", "rows": len(df), "test_rows": len(Xte),
               "stacking_ensemble": scores(yte, p), "members": {}}
    imp = model.named_steps["impute"]
    Xte_i = imp.transform(Xte)
    for name, est in zip([n for n, _ in members()], model.named_steps["stack"].estimators_):
        metrics["members"][name] = scores(yte, est.predict_proba(Xte_i)[:, 1])
    print(json.dumps(metrics, indent=1))

    rng = np.random.default_rng(SEED)
    bg = imp.transform(Xtr)[rng.choice(len(Xtr), 100, replace=False)]
    # presets: real test-set lab samples (most confident not potable, most confident potable, borderline)
    te = Xte.copy()
    te["p"] = p
    te["y"] = yte.values
    te = te.dropna(subset=FEATURES)
    picks = [("Lab sample A (reservoir outlet)", te[te.y == 0].sort_values("p").iloc[0]),
             ("Lab sample B (treated supply)", te[te.y == 1].sort_values("p").iloc[-1]),
             ("Lab sample C (borderline)", te.iloc[(te.p - 0.5).abs().argsort().iloc[0]])]
    presets = [{"name": n, "values": {f: round(float(r[f]), 4) for f in FEATURES}, "actual": int(r.y)} for n, r in picks]
    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump({"model": model, "background": bg, "imputer_median": imp.statistics_.copy(),
                 "member_names": [n for n, _ in members()], "presets": presets}, ROOT / "models" / "quality_stack.joblib",
                compress=3)
    out = ROOT / "experiments" / "quality_metrics.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(metrics, indent=1))


if __name__ == "__main__":
    main()
