"""Extra measurements for the documentation run (does not touch models/ or data/).

Re-evaluates the project's own pipeline (same split, same four algorithms, same settings as train_models.py)
and adds what train_models.py does not report: ROC-AUC, confusion matrices, 5-fold CV, a multi-seed split study,
a decision-threshold sweep, permutation importance, hyper-parameter sensitivity, timings and a check that the
shipped .pkl files reproduce models/training_report.json.

    venv\\Scripts\\python scripts\\run_experiments.py        ->  docs/experiments/results.json
"""
import json
import os
import sys
import time
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score, recall_score,
                             roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "docs", "experiments")
os.makedirs(OUT, exist_ok=True)

SEED = 42
DISEASES = {
    "diabetes": ("data/diabetes.csv", "Outcome"),
    "heart": ("data/heart.csv", "target"),
    "liver": ("data/liver.csv", "Dataset"),
    "kidney": ("data/kidney.csv", "classification"),
}
BUILDERS = {
    "Logistic Regression": lambda: LogisticRegression(max_iter=1000, random_state=SEED),
    "Decision Tree": lambda: DecisionTreeClassifier(max_depth=6, random_state=SEED),
    "Random Forest": lambda: RandomForestClassifier(n_estimators=200, max_depth=8, random_state=SEED),
    "SVM": lambda: SVC(kernel="rbf", C=1.0, probability=True, random_state=SEED),
}
REPORT = json.load(open(os.path.join(ROOT, "models", "training_report.json")))


def metrics(y, pred, score):
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, score)),
    }


def split(df, target, feats, seed=SEED):
    X, y = df[feats].values, df[target].values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=seed, stratify=y)
    sc = StandardScaler().fit(Xtr)
    return sc.transform(Xtr), sc.transform(Xte), ytr, yte, sc


def score_of(model, X):
    return model.predict_proba(X)[:, 1]


results = {}
for d, (csv, target) in DISEASES.items():
    print("==", d, flush=True)
    df = pd.read_csv(os.path.join(ROOT, csv))
    feats = [c for c in df.columns if c != target]
    R = {"rows": int(len(df)), "n_features": len(feats), "features": feats,
         "positive": int((df[target] == 1).sum()), "negative": int((df[target] == 0).sum()),
         "missing_cells": int(df.isna().sum().sum()), "duplicate_rows": int(df.duplicated().sum())}
    Xtr, Xte, ytr, yte, scaler = split(df, target, feats)
    R["train_rows"], R["test_rows"] = int(len(ytr)), int(len(yte))
    R["test_positive"] = int(yte.sum())

    # 1. hold-out metrics + confusion matrices + timings, and agreement with the shipped report
    holdout, cms, fitted, times = {}, {}, {}, {}
    for name, b in BUILDERS.items():
        m = b()
        t0 = time.perf_counter()
        m.fit(Xtr, ytr)
        times[name] = {"fit_s": time.perf_counter() - t0}
        t0 = time.perf_counter()
        for _ in range(20):
            m.predict(Xte)
        times[name]["predict_ms_per_row"] = (time.perf_counter() - t0) / 20 / len(yte) * 1000
        pred = m.predict(Xte)
        holdout[name] = metrics(yte, pred, score_of(m, Xte))
        cms[name] = confusion_matrix(yte, pred).tolist()
        fitted[name] = m
    R["holdout"], R["confusion"], R["timing"] = holdout, cms, times
    R["report_match"] = {n: abs(holdout[n]["f1"] - REPORT[d]["all_results"][n]["f1"]) < 1e-4 and
                         abs(holdout[n]["accuracy"] - REPORT[d]["all_results"][n]["accuracy"]) < 1e-4
                         for n in BUILDERS}
    best = REPORT[d]["best_model"]
    R["best_model"] = best

    # shipped pickles reproduce the report
    shipped = joblib.load(os.path.join(ROOT, "models", f"{d}_model.pkl"))
    ssc = joblib.load(os.path.join(ROOT, "models", f"{d}_scaler.pkl"))
    sp = shipped.predict(ssc.transform(df[feats].values[
        train_test_split(np.arange(len(df)), test_size=0.2, random_state=SEED, stratify=df[target].values)[1]]))
    R["shipped_accuracy"] = float(accuracy_score(yte, sp))
    R["shipped_f1"] = float(f1_score(yte, sp))

    # 2. stratified 5-fold CV (scaler fitted inside each fold via manual loop)
    cv = {}
    skf = StratifiedKFold(5, shuffle=True, random_state=SEED)
    X, y = df[feats].values, df[target].values
    for name, b in BUILDERS.items():
        accs, f1s, aucs = [], [], []
        for tr, te in skf.split(X, y):
            sc = StandardScaler().fit(X[tr])
            m = b().fit(sc.transform(X[tr]), y[tr])
            p = m.predict(sc.transform(X[te]))
            accs.append(accuracy_score(y[te], p))
            f1s.append(f1_score(y[te], p))
            aucs.append(roc_auc_score(y[te], score_of(m, sc.transform(X[te]))))
        cv[name] = {"accuracy_mean": float(np.mean(accs)), "accuracy_std": float(np.std(accs)),
                    "f1_mean": float(np.mean(f1s)), "f1_std": float(np.std(f1s)),
                    "auc_mean": float(np.mean(aucs)), "auc_std": float(np.std(aucs))}
    R["cv5"] = cv

    # 3. seed study: 10 different 80/20 splits, all four models
    seeds = {n: {"accuracy": [], "f1": []} for n in BUILDERS}
    winners = []
    for s in range(10):
        a, b_, c, e, _ = split(df, target, feats, seed=s)
        f1_by = {}
        for name, bld in BUILDERS.items():
            m = bld().fit(a, c)
            p = m.predict(b_)
            seeds[name]["accuracy"].append(float(accuracy_score(e, p)))
            seeds[name]["f1"].append(float(f1_score(e, p)))
            f1_by[name] = f1_score(e, p)
        winners.append(max(f1_by, key=f1_by.get))
    R["seed_study"] = {n: {"accuracy_mean": float(np.mean(v["accuracy"])), "accuracy_std": float(np.std(v["accuracy"])),
                            "f1_mean": float(np.mean(v["f1"])), "f1_std": float(np.std(v["f1"]))} for n, v in seeds.items()}
    R["seed_winners"] = {n: winners.count(n) for n in BUILDERS}

    # 4. decision-threshold sweep of the selected model
    mb = fitted[best]
    sc_te = score_of(mb, Xte)
    sweep = []
    for t in np.round(np.arange(0.2, 0.81, 0.05), 2):
        p = (sc_te >= t).astype(int)
        sweep.append({"threshold": float(t), "precision": float(precision_score(yte, p, zero_division=0)),
                      "recall": float(recall_score(yte, p)), "f1": float(f1_score(yte, p)),
                      "accuracy": float(accuracy_score(yte, p))})
    R["threshold_sweep"] = sweep
    # ROC curve points for the selected model
    from sklearn.metrics import roc_curve
    fpr, tpr, _ = roc_curve(yte, sc_te)
    R["roc"] = {"fpr": fpr.round(4).tolist(), "tpr": tpr.round(4).tolist()}
    roc_all = {}
    for name, m in fitted.items():
        f_, t_, _ = roc_curve(yte, score_of(m, Xte))
        roc_all[name] = {"fpr": f_.round(4).tolist(), "tpr": t_.round(4).tolist()}
    R["roc_all"] = roc_all

    # 5. permutation importance of the selected model (accuracy drop, 20 repeats) and LR coefficients
    pi = permutation_importance(mb, Xte, yte, n_repeats=20, random_state=SEED, scoring="accuracy")
    R["perm_importance"] = sorted(
        [{"feature": f, "mean": float(m_), "std": float(s_)} for f, m_, s_ in zip(feats, pi.importances_mean, pi.importances_std)],
        key=lambda r: -r["mean"])
    lr = fitted["Logistic Regression"]
    R["lr_coef"] = sorted([{"feature": f, "coef": float(c)} for f, c in zip(feats, lr.coef_[0])], key=lambda r: -abs(r["coef"]))

    # 6. hyper-parameter sensitivity (test accuracy)
    sens = {"dt_depth": {}, "rf_trees": {}, "svm_C": {}}
    for k in (2, 3, 4, 6, 8, 10, 12):
        m = DecisionTreeClassifier(max_depth=k, random_state=SEED).fit(Xtr, ytr)
        sens["dt_depth"][k] = float(accuracy_score(yte, m.predict(Xte)))
    for k in (10, 25, 50, 100, 200, 400):
        m = RandomForestClassifier(n_estimators=k, max_depth=8, random_state=SEED).fit(Xtr, ytr)
        sens["rf_trees"][k] = float(accuracy_score(yte, m.predict(Xte)))
    for k in (0.1, 0.3, 1, 3, 10, 100):
        m = SVC(kernel="rbf", C=k, random_state=SEED).fit(Xtr, ytr)
        sens["svm_C"][k] = float(accuracy_score(yte, m.predict(Xte)))
    R["sensitivity"] = sens

    # 7. train-vs-test gap (over-fitting check)
    R["train_accuracy"] = {n: float(accuracy_score(ytr, m.predict(Xtr))) for n, m in fitted.items()}
    results[d] = R

json.dump(results, open(os.path.join(OUT, "results.json"), "w"), indent=1)
print("saved", os.path.join(OUT, "results.json"))
for d, R in results.items():
    print(d, "report_match", all(R["report_match"].values()), "shipped acc", round(R["shipped_accuracy"], 4),
          "best", R["best_model"], {n: round(v["roc_auc"], 3) for n, v in R["holdout"].items()})
