"""Extra experiments for the project documents (run in the project venv).

Everything is computed on the seeded synthetic dataset the product ships with, using the same
80/20 split and 80/20 calibration split as ml/train.py. Writes experiments/extra/metrics.json.

    venv\\Scripts\\python scripts\\run_experiments.py
"""
import json
import sys
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ml"))
from app.services.features import FEATURES, FLAGS, VITALS  # noqa: E402
import make_data  # noqa: E402

SEED = 7307
OUT = ROOT / "experiments" / "extra"
OUT.mkdir(parents=True, exist_ok=True)


def xgb():
    return XGBClassifier(n_estimators=220, max_depth=4, learning_rate=0.1, subsample=0.9, colsample_bytree=0.9,
                         objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=4)


def ece(proba, y, bins=10):
    conf, pred = proba.max(1), proba.argmax(1)
    hit = (pred == y).astype(float)
    edges = np.linspace(0, 1, bins + 1)
    total, rows = 0.0, []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.sum():
            total += m.sum() / len(y) * abs(hit[m].mean() - conf[m].mean())
            rows.append({"lo": round(lo, 2), "hi": round(hi, 2), "n": int(m.sum()),
                         "confidence": round(float(conf[m].mean()), 4), "accuracy": round(float(hit[m].mean()), 4)})
    return float(total), rows


def brier(proba, y):
    onehot = np.eye(proba.shape[1])[y]
    return float(((proba - onehot) ** 2).sum(1).mean())


def summary(y, pred, proba=None):
    d = {"accuracy": round(float(accuracy_score(y, pred)), 4),
         "within_one": round(float((np.abs(pred - y) <= 1).mean()), 4),
         "macro_f1": round(float(f1_score(y, pred, average="macro")), 4),
         "qwk": round(float(cohen_kappa_score(y, pred, weights="quadratic")), 4)}
    if proba is not None:
        top2 = np.argsort(-proba, 1)[:, :2]
        d["top2"] = round(float(np.mean([t in r for t, r in zip(y, top2)])), 4)
    return d


def main():
    out = {}
    df = pd.read_csv(ROOT / "data" / "sample" / "triage_synthetic.csv")
    X, y = df[FEATURES], df["priority"] - 1
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
    X_fit, X_cal, y_fit, y_cal = train_test_split(X_tr, y_tr, test_size=0.2, stratify=y_tr, random_state=SEED)
    yt = y_te.to_numpy()
    out["dataset"] = {"rows": int(len(df)), "n_fit": int(len(X_fit)), "n_cal": int(len(X_cal)), "n_test": int(len(X_te)),
                      "features": len(FEATURES), "priority_share": {str(k): round(float(v), 4) for k, v in
                                                                    (df["priority"].value_counts(normalize=True).sort_index()).items()},
                      "archetype_share": {k: round(float(v), 4) for k, v in df["arch"].value_counts(normalize=True).items()}}

    # ---- A. model comparison, same split ----
    models = {
        "Logistic regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
        "Decision tree": DecisionTreeClassifier(max_depth=8, random_state=SEED),
        "Random forest": RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=4),
        "Extra trees": ExtraTreesClassifier(n_estimators=300, random_state=SEED, n_jobs=4),
        "k-nearest neighbours": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=15)),
        "MLP": make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=600, random_state=SEED)),
        "HistGradientBoosting": HistGradientBoostingClassifier(random_state=SEED),
        "XGBoost (shipped config)": xgb(),
    }
    comp = {}
    for name, m in models.items():
        t0 = time.time()
        m.fit(X_fit, y_fit)
        fit_s = time.time() - t0
        p = m.predict_proba(X_te)
        comp[name] = {**summary(yt, p.argmax(1), p), "fit_seconds": round(fit_s, 2)}
        print(name, comp[name], flush=True)
    out["model_comparison"] = comp

    # 5-fold CV accuracy on all 6,000 rows for the headline families
    cv = {}
    skf = StratifiedKFold(5, shuffle=True, random_state=SEED)
    for name in ("Logistic regression", "Random forest", "XGBoost (shipped config)"):
        s = cross_val_score(models[name], X, y, cv=skf, scoring="accuracy", n_jobs=1)
        cv[name] = {"mean": round(float(s.mean()), 4), "std": round(float(s.std()), 4), "folds": [round(float(v), 4) for v in s]}
        print("cv", name, cv[name], flush=True)
    out["cv5_accuracy"] = cv

    # ---- shipped model (as served) ----
    bundle = joblib.load(ROOT / "models" / "triage_model.joblib")
    raw = bundle["base"].predict_proba(X_te)
    cal = bundle["calibrated"].predict_proba(X_te)
    out["shipped"] = {"calibrated": summary(yt, cal.argmax(1), cal), "uncalibrated": summary(yt, raw.argmax(1), raw)}

    # ---- B. modality ablation ----
    abl = {}
    for name, cols in (("Vitals only (8)", VITALS), ("Report only (28)", FLAGS), ("Fused (36)", FEATURES)):
        m = xgb().fit(X_fit[cols], y_fit)
        p = m.predict_proba(X_te[cols])
        abl[name] = {**summary(yt, p.argmax(1), p), "inputs": len(cols)}
        print("ablation", name, abl[name], flush=True)
    # report sub-groups: text flags only vs lab flags only added to vitals
    lab = [f for f in FLAGS if f.startswith("lab_")]
    txt = [f for f in FLAGS if not f.startswith("lab_")]
    for name, cols in (("Vitals + text flags (30)", VITALS + txt), ("Vitals + lab flags (14)", VITALS + lab)):
        m = xgb().fit(X_fit[cols], y_fit)
        p = m.predict_proba(X_te[cols])
        abl[name] = {**summary(yt, p.argmax(1), p), "inputs": len(cols)}
        print("ablation", name, abl[name], flush=True)
    out["ablation"] = abl

    # ---- C. calibration ----
    e_raw, bins_raw = ece(raw, yt)
    e_cal, bins_cal = ece(cal, yt)
    out["calibration"] = {"ece_uncalibrated": round(e_raw, 4), "ece_isotonic": round(e_cal, 4),
                          "brier_uncalibrated": round(brier(raw, yt), 4), "brier_isotonic": round(brier(cal, yt), 4),
                          "mean_confidence_uncalibrated": round(float(raw.max(1).mean()), 4),
                          "mean_confidence_isotonic": round(float(cal.max(1).mean()), 4),
                          "bins_uncalibrated": bins_raw, "bins_isotonic": bins_cal}
    print("calibration", {k: v for k, v in out["calibration"].items() if not k.startswith("bins")}, flush=True)

    # ---- D. confidence threshold / coverage ----
    pred, conf = cal.argmax(1), cal.max(1)
    thr = []
    for t in (0.0, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95):
        m = conf >= t
        thr.append({"threshold": t, "coverage": round(float(m.mean()), 4), "n": int(m.sum()),
                    "accuracy": round(float((pred[m] == yt[m]).mean()), 4) if m.sum() else None,
                    "within_one": round(float((np.abs(pred[m] - yt[m]) <= 1).mean()), 4) if m.sum() else None})
    out["confidence_threshold"] = thr

    # ---- E. safety view: under/over-triage, high-risk detection ----
    diff = pred - yt  # >0 predicted less urgent than label (under-triage)
    hi_true, hi_pred = yt <= 1, pred <= 1
    out["safety"] = {
        "under_triage_any": round(float((diff > 0).mean()), 4), "over_triage_any": round(float((diff < 0).mean()), 4),
        "under_triage_2plus": round(float((diff >= 2).mean()), 4), "over_triage_2plus": round(float((diff <= -2).mean()), 4),
        "p1_predicted_p3_or_lower_urgency": int(((yt == 0) & (pred >= 2)).sum()), "p1_support": int((yt == 0).sum()),
        "high_risk_recall": round(float((hi_pred & hi_true).sum() / hi_true.sum()), 4),
        "high_risk_precision": round(float((hi_pred & hi_true).sum() / max(hi_pred.sum(), 1)), 4),
        "high_risk_support": int(hi_true.sum()),
    }
    # P1/P2 recall if the high-risk flag is raised whenever P(1)+P(2) >= 0.4
    pr = cal[:, 0] + cal[:, 1]
    out["safety"]["high_risk_recall_at_pr_0_4"] = round(float(((pr >= 0.4) & hi_true).sum() / hi_true.sum()), 4)
    out["safety"]["high_risk_precision_at_pr_0_4"] = round(float(((pr >= 0.4) & hi_true).sum() / max((pr >= 0.4).sum(), 1)), 4)

    # ---- F. robustness to missing / mis-read report flags ----
    rng = np.random.default_rng(SEED)
    rob = []
    for drop in (0.0, 0.1, 0.2, 0.3, 0.5, 1.0):
        Xp = X_te.copy()
        mask = rng.random(Xp[FLAGS].shape) < drop
        Xp[FLAGS] = np.where(mask & (Xp[FLAGS].to_numpy() == 1), 0, Xp[FLAGS].to_numpy())
        p = bundle["calibrated"].predict_proba(Xp)
        rob.append({"drop_rate": drop, **summary(yt, p.argmax(1), p)})
    out["robustness_dropped_flags"] = rob

    # ---- G. label-noise ceiling: how well could anyone do? ----
    seen = []
    orig = make_data.severity
    make_data.severity = lambda r: (seen.append(orig(r)) or seen[-1])
    regen = make_data.generate()
    make_data.severity = orig
    clean = make_data.to_priority(np.array(seen))
    same = bool((regen["priority"].to_numpy() == df["priority"].to_numpy()).all())
    out["noise_ceiling"] = {"regenerated_matches_csv": same,
                            "oracle_accuracy_knowing_clean_severity": round(float((clean == df["priority"].to_numpy()).mean()), 4),
                            "oracle_within_one": round(float((np.abs(clean - df["priority"].to_numpy()) <= 1).mean()), 4)}
    print("ceiling", out["noise_ceiling"], flush=True)

    # ---- H. split stability: 5 different seeds for the shipped recipe ----
    st = []
    for s in (1, 2, 3, 4, 5):
        a, b, c, d = train_test_split(X, y, test_size=0.2, stratify=y, random_state=s)
        a1, _, c1, _ = train_test_split(a, c, test_size=0.2, stratify=c, random_state=s)
        m = xgb().fit(a1, c1)
        pp = m.predict_proba(b)
        st.append({"seed": s, **summary(d.to_numpy(), pp.argmax(1), pp)})
    out["seed_stability"] = {"runs": st, "accuracy_mean": round(float(np.mean([r["accuracy"] for r in st])), 4),
                             "accuracy_std": round(float(np.std([r["accuracy"] for r in st])), 4),
                             "macro_f1_mean": round(float(np.mean([r["macro_f1"] for r in st])), 4)}

    # ---- I. global SHAP importance on the test set ----
    import shap
    ex = shap.TreeExplainer(bundle["base"])
    sv = ex.shap_values(X_te)
    arr = np.stack([np.asarray(s) for s in sv], -1) if isinstance(sv, list) else np.asarray(sv)
    imp = np.abs(arr).mean(axis=(0, 2))
    order = np.argsort(-imp)
    out["shap_global"] = [{"feature": FEATURES[i], "mean_abs_shap": round(float(imp[i]), 4)} for i in order[:15]]

    (OUT / "metrics.json").write_text(json.dumps(out, indent=2))
    print("written", OUT / "metrics.json")


if __name__ == "__main__":
    main()
