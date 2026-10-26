"""Real-data experiments for the documentation run.

The shipped app was trained on a synthetic fallback dataset (the Kaggle CSV was not available when
the models were built).  This script re-runs the SAME pipeline (app.ml.preprocessing + app.ml.models,
same 5 x 80/20 StratifiedShuffleSplit, seed 42) on the real public "Startup Success Prediction"
table (923 US start-ups, structured columns only) and adds ROC-AUC, class-imbalance, threshold,
feature-importance and synthetic-to-real transfer studies.

    .venv\\Scripts\\python.exe scripts\\run_experiments.py

Writes evaluation/real_results.json.  Does not touch models/ or the running app.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.inspection import permutation_importance  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,  # noqa: E402
                             confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedShuffleSplit  # noqa: E402
from sklearn.utils import resample  # noqa: E402

from app.config import N_SPLITS, RANDOM_STATE, TEST_SIZE  # noqa: E402
from app.ml.models import get_models  # noqa: E402
from app.ml.preprocessing import build_preprocessor, feature_names, prepare_frame  # noqa: E402

REAL_CSV = ROOT / "data" / "real" / "startup_data.csv"
OUT = ROOT / "evaluation" / "real_results.json"

INDUSTRY_MAP = {  # Kaggle category_code -> the app's industry_type vocabulary
    "software": "Software", "web": "Software", "enterprise": "Software", "network_hosting": "Software",
    "search": "Software", "security": "Software", "analytics": "Software", "semiconductor": "Software",
    "ecommerce": "E-Commerce", "mobile": "Mobile", "games_video": "Media", "advertising": "Media",
    "social": "Media", "music": "Media", "photo_video": "Media", "news": "Media", "public_relations": "Media",
    "biotech": "Biotech", "medical": "HealthTech", "health": "HealthTech",
    "cleantech": "CleanTech", "hardware": "Software", "education": "EdTech",
}
STATE_KEEP = {"CA", "NY", "MA", "TX", "WA", "IL", "CO", "FL", "PA", "OR"}
METRICS = ["accuracy", "balanced_accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]


def load_real() -> pd.DataFrame:
    raw = pd.read_csv(REAL_CSV)
    df = pd.DataFrame({
        "age_first_funding_year": raw["age_first_funding_year"],
        "age_last_funding_year": raw["age_last_funding_year"],
        "age_first_milestone_year": raw["age_first_milestone_year"],
        "age_last_milestone_year": raw["age_last_milestone_year"],
        "relationships": raw["relationships"], "funding_rounds": raw["funding_rounds"],
        "funding_total_usd": raw["funding_total_usd"], "milestones": raw["milestones"],
        "avg_participants": raw["avg_participants"],
        "has_VC": raw["has_VC"], "has_angel": raw["has_angel"], "has_roundA": raw["has_roundA"],
        "has_roundB": raw["has_roundB"], "has_roundC": raw["has_roundC"], "has_roundD": raw["has_roundD"],
        "is_top500": raw["is_top500"],
        "state": raw["state_code"].where(raw["state_code"].isin(STATE_KEEP), "Other"),
        "industry_type": raw["category_code"].map(INDUSTRY_MAP).fillna("Other"),
        "description": "",
        "status": raw["status"],
    })
    return prepare_frame(df)


def score(y, pred, proba) -> dict:
    return {
        "accuracy": accuracy_score(y, pred), "balanced_accuracy": balanced_accuracy_score(y, pred),
        "precision": precision_score(y, pred, zero_division=0), "recall": recall_score(y, pred, zero_division=0),
        "f1": f1_score(y, pred, zero_division=0), "roc_auc": roc_auc_score(y, proba),
        "pr_auc": average_precision_score(y, proba),
    }


def agg(rows: list[dict]) -> dict:
    return {k: {"mean": float(np.mean([r[k] for r in rows])), "std": float(np.std([r[k] for r in rows]))}
            for k in METRICS}


def proba_of(model, X) -> np.ndarray:
    return model.predict_proba(X)[:, 1]


def model_zoo() -> dict:
    zoo = get_models()
    zoo["HistGradientBoosting"] = HistGradientBoostingClassifier(
        max_iter=300, max_depth=4, learning_rate=0.05, l2_regularization=1.0, random_state=RANDOM_STATE)
    return zoo


def main() -> None:
    t0 = time.time()
    df = load_real()
    y_all = df["label"].to_numpy()
    n = len(df)
    out: dict = {"dataset": {
        "rows": int(n), "success": int((y_all == 1).sum()), "failure": int((y_all == 0).sum()),
        "success_share": float((y_all == 1).mean()), "source": "Startup Success Prediction (Kaggle, manishkc06), 923-row CSV",
        "text_available": False,
        "protocol": f"{N_SPLITS} x StratifiedShuffleSplit({int((1 - TEST_SIZE) * 100)}/{int(TEST_SIZE * 100)}), seed {RANDOM_STATE}",
    }}
    sss = StratifiedShuffleSplit(n_splits=N_SPLITS, test_size=TEST_SIZE, random_state=RANDOM_STATE)

    # ---- 1. model comparison (same preprocessing + hyper-parameters as the app) ----------------
    per: dict[str, list[dict]] = {}
    cms: dict[str, list[np.ndarray]] = {}
    thr_probs: list[tuple[np.ndarray, np.ndarray]] = []  # LR (y_test, p) for the threshold sweep
    rf_probs: list[tuple[np.ndarray, np.ndarray]] = []
    fnames: list[str] = []
    imp_lr, imp_rf, imp_perm = [], [], []
    for tr, te in sss.split(np.zeros(n), y_all):
        dtr, dte = df.iloc[tr].reset_index(drop=True), df.iloc[te].reset_index(drop=True)
        pre = build_preprocessor()
        Xtr, Xte = pre.fit_transform(dtr), pre.transform(dte)
        fnames = feature_names(pre)
        for name, m in model_zoo().items():
            m.fit(Xtr, y_all[tr])
            p = proba_of(m, Xte)
            pred = (p >= 0.5).astype(int)
            per.setdefault(name, []).append(score(y_all[te], pred, p))
            cms.setdefault(name, []).append(confusion_matrix(y_all[te], pred))
            if name == "Logistic Regression":
                thr_probs.append((y_all[te], p)); imp_lr.append(np.abs(m.coef_.ravel()))
            if name == "Random Forest":
                rf_probs.append((y_all[te], p)); imp_rf.append(m.feature_importances_)
                pi = permutation_importance(m, Xte, y_all[te], scoring="roc_auc", n_repeats=5,
                                            random_state=RANDOM_STATE)
                imp_perm.append(pi.importances_mean)
    out["models"] = {m: {**agg(r), "confusion_matrix_mean": np.mean(cms[m], axis=0).tolist(),
                         "confusion_matrix_last": cms[m][-1].tolist()} for m, r in per.items()}
    out["best_by_balanced_accuracy"] = max(out["models"], key=lambda k: out["models"][k]["balanced_accuracy"]["mean"])
    out["best_by_roc_auc"] = max(out["models"], key=lambda k: out["models"][k]["roc_auc"]["mean"])

    # ---- 2. feature importance ----------------------------------------------------------------
    def top(vals, k=12):
        v = np.mean(vals, axis=0)
        order = np.argsort(-v)[:k]
        return [{"feature": fnames[i], "value": float(v[i])} for i in order]
    out["feature_importance"] = {"logistic_abs_coef": top(imp_lr), "random_forest_gini": top(imp_rf),
                                 "random_forest_permutation_auc": top(imp_perm)}

    # ---- 3. class imbalance: none / class_weight / random oversampling ------------------------
    imb: dict[str, dict[str, list[dict]]] = {}
    for tr, te in sss.split(np.zeros(n), y_all):
        dtr, dte = df.iloc[tr].reset_index(drop=True), df.iloc[te].reset_index(drop=True)
        pre = build_preprocessor()
        Xtr, Xte = pre.fit_transform(dtr), pre.transform(dte)
        ytr, yte = y_all[tr], y_all[te]
        # oversample the MINORITY class (here: failure) to parity
        minority = int(np.argmin(np.bincount(ytr)))
        idx_min, idx_maj = np.where(ytr == minority)[0], np.where(ytr != minority)[0]
        up = resample(idx_min, replace=True, n_samples=len(idx_maj), random_state=RANDOM_STATE)
        idx_os = np.concatenate([idx_maj, up])
        for tag, kw in [("Logistic Regression", dict(max_iter=1000)), ("Random Forest", None)]:
            for strat in ("none", "class_weight", "oversample"):
                if tag == "Logistic Regression":
                    m = LogisticRegression(max_iter=1000, class_weight="balanced" if strat == "class_weight" else None)
                else:
                    from sklearn.ensemble import RandomForestClassifier
                    m = RandomForestClassifier(n_estimators=300, min_samples_leaf=2, n_jobs=-1, random_state=RANDOM_STATE,
                                               class_weight="balanced" if strat == "class_weight" else None)
                if strat == "oversample":
                    m.fit(Xtr[idx_os], ytr[idx_os])
                else:
                    m.fit(Xtr, ytr)
                p = proba_of(m, Xte)
                imb.setdefault(tag, {}).setdefault(strat, []).append(score(yte, (p >= 0.5).astype(int), p))
    out["imbalance"] = {t: {s: agg(r) for s, r in d.items()} for t, d in imb.items()}

    # ---- 4. decision-threshold sweep (Logistic Regression, pooled test predictions) -----------
    ys = np.concatenate([a for a, _ in thr_probs]); ps = np.concatenate([b for _, b in thr_probs])
    sweep = []
    for t in np.round(np.arange(0.2, 0.81, 0.05), 2):
        pr = (ps >= t).astype(int)
        sweep.append({"threshold": float(t), "precision": float(precision_score(ys, pr, zero_division=0)),
                      "recall": float(recall_score(ys, pr, zero_division=0)), "f1": float(f1_score(ys, pr, zero_division=0)),
                      "balanced_accuracy": float(balanced_accuracy_score(ys, pr))})
    out["threshold_sweep_logreg"] = sweep
    ys2 = np.concatenate([a for a, _ in rf_probs]); ps2 = np.concatenate([b for _, b in rf_probs])
    out["threshold_sweep_rf"] = [{"threshold": float(t),
        "precision": float(precision_score(ys2, (ps2 >= t).astype(int), zero_division=0)),
        "recall": float(recall_score(ys2, (ps2 >= t).astype(int), zero_division=0)),
        "f1": float(f1_score(ys2, (ps2 >= t).astype(int), zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(ys2, (ps2 >= t).astype(int)))}
        for t in np.round(np.arange(0.2, 0.81, 0.05), 2)]
    # calibration of pooled LR probabilities (10 bins)
    bins = np.linspace(0, 1, 11)
    cal = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mk = (ps >= lo) & (ps < hi if hi < 1 else ps <= hi)
        if mk.sum():
            cal.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": int(mk.sum()), "mean_pred": float(ps[mk].mean()), "observed": float(ys[mk].mean())})
    out["calibration_logreg"] = cal

    # ---- 5. Random Forest size study (parameter analysis) --------------------------------------
    from sklearn.ensemble import RandomForestClassifier
    rf_study = {}
    for ne in (50, 100, 300, 600):
        rows = []
        for tr, te in sss.split(np.zeros(n), y_all):
            pre = build_preprocessor()
            Xtr, Xte = pre.fit_transform(df.iloc[tr]), pre.transform(df.iloc[te])
            m = RandomForestClassifier(n_estimators=ne, min_samples_leaf=2, class_weight="balanced", n_jobs=-1,
                                       random_state=RANDOM_STATE).fit(Xtr, y_all[tr])
            p = proba_of(m, Xte); rows.append(score(y_all[te], (p >= 0.5).astype(int), p))
        rf_study[str(ne)] = agg(rows)
    out["rf_n_estimators"] = rf_study

    # ---- 6. base-paper style protocol: single 70:30 split, 5 seeds ----------------------------
    from sklearn.model_selection import train_test_split
    bp = {}
    for name in ("Logistic Regression", "Random Forest", "HistGradientBoosting"):
        rows = []
        for seed in range(5):
            tr, te = train_test_split(np.arange(n), test_size=0.30, stratify=y_all, random_state=seed)
            pre = build_preprocessor(); Xtr, Xte = pre.fit_transform(df.iloc[tr]), pre.transform(df.iloc[te])
            m = model_zoo()[name].fit(Xtr, y_all[tr]); p = proba_of(m, Xte)
            rows.append(score(y_all[te], (p >= 0.5).astype(int), p))
        bp[name] = agg(rows)
    out["split_70_30"] = bp

    # ---- 7. synthetic -> real transfer (structured features only) ------------------------------
    try:
        from app.ml.dataset import generate_synthetic
        syn = prepare_frame(generate_synthetic())
        pre_s = build_preprocessor(); Xs = pre_s.fit_transform(syn); Xr = pre_s.transform(df)
        transfer = {}
        for name in ("Logistic Regression", "Random Forest"):
            m = model_zoo()[name].fit(Xs, syn["label"].to_numpy()); p = proba_of(m, Xr)
            transfer[name] = {k: float(v) for k, v in score(y_all, (p >= 0.5).astype(int), p).items()}
        out["synthetic_to_real"] = {"train_rows": int(len(syn)), "test_rows": int(n), "results": transfer}
        # in-synthetic reference with the same structured-only features (5 splits)
        ys_ = syn["label"].to_numpy(); ref = {}
        for name in model_zoo():
            rows = []
            for tr, te in sss.split(np.zeros(len(syn)), ys_):
                pre = build_preprocessor(); Xtr, Xte = pre.fit_transform(syn.iloc[tr]), pre.transform(syn.iloc[te])
                m = model_zoo()[name].fit(Xtr, ys_[tr]); p = proba_of(m, Xte)
                rows.append(score(ys_[te], (p >= 0.5).astype(int), p))
            ref[name] = agg(rows)
        out["synthetic_structured_only"] = ref
    except Exception as exc:  # noqa: BLE001
        out["synthetic_to_real_error"] = str(exc)

    out["runtime_seconds"] = round(time.time() - t0, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {OUT}  ({out['runtime_seconds']} s)")
    for m, r in out["models"].items():
        print(f"{m:24s} acc {r['accuracy']['mean']:.3f} bal {r['balanced_accuracy']['mean']:.3f} "
              f"f1 {r['f1']['mean']:.3f} auc {r['roc_auc']['mean']:.3f}")


if __name__ == "__main__":
    main()
