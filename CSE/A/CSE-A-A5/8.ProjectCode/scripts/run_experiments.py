"""Real-data experiments for the ThreatSense Engine (XGBoost + 1D CNN + Logistic-Regression stacking).

Re-uses the shipped pipeline code (preprocessor, XGBoost settings, PyTorch CNN, stacking) and runs it on
the real UNSW-NB15 flows downloaded by scripts/fetch_unsw_nb15.py:

  official   - train on the official 175,341-flow training set (85/15 fit/val), test on the official
               82,332-flow testing set; 5 seeds. Includes baselines, ablations, threshold sweep,
               per-attack-category recall and inference timing.
  paper      - the base paper's protocol: 9,000 balanced flows (4,500 per class), stratified 70/15/15,
               10 repetitions, mean +- std.
  shift      - the shipped (synthetic-trained) models scored on real flows, and real-trained models
               scored on the synthetic demo CSV.

Results go to experiments/unsw_nb15/<experiment>/metrics.json. Usage:
    python scripts/run_experiments.py [official] [paper] [shift]
"""
import sys

sys.modules["tensorflow"] = None  # force the PyTorch CNN backend (same as the shipped models)
import torch  # noqa: E402  (must be the first heavy import: on this Windows host torch's DLLs fail to load after numpy/pandas)
import json  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib  # noqa: E402
import xgboost as xgb  # noqa: E402
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, matthews_corrcoef,  # noqa: E402
                             precision_score, recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.tree import DecisionTreeClassifier  # noqa: E402

from cipherguard.ids.features import FEATURE_NAMES  # noqa: E402
from cipherguard.ids.preprocessing import build_preprocessor  # noqa: E402
from cipherguard.ids.train import train_cnn_torch, predict_torch  # noqa: E402

DATA = ROOT / "data" / "external" / "unsw_nb15"
OUT = ROOT / "experiments" / "unsw_nb15"
torch.set_num_threads(4)


def load_real():
    tr = pd.read_parquet(DATA / "train.parquet")
    te = pd.read_parquet(DATA / "test.parquet")
    for d in (tr, te):
        for c in ("proto", "service", "state"):
            d[c] = d[c].astype(str)
    return tr, te


def metrics(y, p, thr=0.5):
    pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, p)),
        "fpr": float(fp / max(fp + tn, 1)),
        "fnr": float(fn / max(fn + tp, 1)),
        "mcc": float(matthews_corrcoef(y, pred)),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }


def fit_models(Xf, yf, Xv, yv, seed, baselines=True):
    """Train the shipped models (same hyper-parameters as cipherguard/ids/train.py) + optional baselines."""
    t0 = time.time()
    spw = (yf == 0).sum() / max((yf == 1).sum(), 1)
    xg = xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.08, subsample=0.85, colsample_bytree=0.85,
                           scale_pos_weight=spw, eval_metric="logloss", random_state=seed, n_jobs=4)
    xg.fit(Xf, yf, verbose=False)
    t_xgb = time.time() - t0
    torch.manual_seed(seed)
    np.random.seed(seed)
    t0 = time.time()
    cnn = train_cnn_torch(Xf, yf, Xv, yv, Xf.shape[1], epochs=15)
    t_cnn = time.time() - t0
    meta = LogisticRegression().fit(np.column_stack([xg.predict_proba(Xv)[:, 1], predict_torch(cnn, Xv)]), yv)
    models = {"xgb": xg, "cnn": cnn, "meta": meta, "train_seconds": {"xgb": t_xgb, "cnn": t_cnn}}
    if baselines:
        models["lr"] = LogisticRegression(max_iter=300).fit(Xf, yf)
        models["dt"] = DecisionTreeClassifier(max_depth=12, random_state=seed).fit(Xf, yf)
        models["rf"] = RandomForestClassifier(n_estimators=100, max_depth=16, n_jobs=4, random_state=seed).fit(Xf, yf)
    return models


def score_all(models, X):
    px = models["xgb"].predict_proba(X)[:, 1]
    pc = predict_torch(models["cnn"], X)
    out = {"xgb": px, "cnn": pc, "mean": (px + pc) / 2,
           "stack": models["meta"].predict_proba(np.column_stack([px, pc]))[:, 1]}
    for k in ("lr", "dt", "rf"):
        if k in models:
            out[k] = models[k].predict_proba(X)[:, 1]
    return out


def summarise(runs):
    """runs: list of {model: metrics}. Returns {model: {metric: {mean, std}}}"""
    out = {}
    for model in runs[0]:
        out[model] = {}
        for k in runs[0][model]:
            if k == "confusion_matrix":
                continue
            v = np.array([r[model][k] for r in runs], dtype=float)
            out[model][k] = {"mean": float(v.mean()), "std": float(v.std(ddof=1)) if len(v) > 1 else 0.0}
    return out


def run_official(seeds=(42, 43, 44, 45, 46)):
    d = OUT / "official"
    d.mkdir(parents=True, exist_ok=True)
    (d / "models").mkdir(exist_ok=True)
    tr, te = load_real()
    yte = te["label"].values.astype(int)
    per_seed, extra = [], {}
    for seed in seeds:
        print(f"[official] seed {seed}", flush=True)
        fit_df, val_df = train_test_split(tr, test_size=0.15, stratify=tr["label"], random_state=seed)
        pre = build_preprocessor()
        Xf = pre.fit_transform(fit_df).astype(np.float32)
        Xv, Xt = pre.transform(val_df).astype(np.float32), pre.transform(te).astype(np.float32)
        yf, yv = fit_df["label"].values.astype(int), val_df["label"].values.astype(int)
        m = fit_models(Xf, yf, Xv, yv, seed)
        probs = score_all(m, Xt)
        res = {k: metrics(yte, p) for k, p in probs.items()}
        per_seed.append(res)
        print("   ", {k: round(v["accuracy"], 4) for k, v in res.items()}, flush=True)
        if seed == seeds[0]:
            p = probs["stack"]
            # thresholds
            thr = []
            for t in np.round(np.arange(0.05, 1.0, 0.05), 2):
                r = metrics(yte, p, t)
                thr.append({"threshold": float(t), **{k: r[k] for k in ("accuracy", "precision", "recall", "f1", "fpr", "fnr")}})
            # per attack category recall of the stacked model
            cats = {}
            for c in sorted(te["attack_cat"].unique()):
                mask = (te["attack_cat"] == c).values
                pred = (p[mask] >= 0.5).astype(int)
                cats[c] = {"n": int(mask.sum()),
                           "detected" if c != "Normal" else "correct_normal": int((pred == (0 if c == "Normal" else 1)).sum()),
                           "rate": float((pred == (0 if c == "Normal" else 1)).mean())}
            # roc curves (downsampled)
            roc = {}
            for k in ("xgb", "cnn", "stack"):
                f, t_, _ = roc_curve(yte, probs[k])
                idx = np.unique(np.linspace(0, len(f) - 1, 300).astype(int))
                roc[k] = {"fpr": f[idx].tolist(), "tpr": t_[idx].tolist()}
            # feature importance (XGBoost gain on the transformed matrix)
            names = list(pre.get_feature_names_out())
            imp = m["xgb"].get_booster().get_score(importance_type="gain")
            top = sorted(((names[int(k[1:])], float(v)) for k, v in imp.items()), key=lambda kv: -kv[1])[:15]
            # inference timing (in-process, stacked engine path = preprocess + xgb + cnn + meta)
            timing = {}
            for n in (1, 100, 1000):
                sub = te.iloc[:n]
                ts = []
                for _ in range(15 if n > 1 else 60):
                    t0 = time.perf_counter()
                    X = pre.transform(sub).astype(np.float32)
                    score_all({k: m[k] for k in ("xgb", "cnn", "meta")}, X)
                    ts.append((time.perf_counter() - t0) * 1000)
                timing[str(n)] = {"median_ms": float(np.median(ts)), "p95_ms": float(np.percentile(ts, 95))}
            extra = {"thresholds": thr, "per_category": cats, "roc": roc, "feature_importance_gain": top,
                     "inference_timing_ms": timing, "train_seconds": m["train_seconds"],
                     "n_features_after_encoding": int(Xf.shape[1])}
            np.savez_compressed(d / "test_probs_seed42.npz", y=yte, **{k: v.astype(np.float32) for k, v in probs.items()})
            joblib.dump(pre, d / "models" / "preprocessor.joblib")
            joblib.dump(m["xgb"], d / "models" / "xgb_model.joblib")
            joblib.dump(m["meta"], d / "models" / "stacking_meta.joblib")
            torch.save(m["cnn"].state_dict(), d / "models" / "cnn_model.pt")
    out = {"protocol": "official UNSW-NB15 training set (85/15 fit/val) -> official testing set",
           "train_rows": int(len(tr)), "fit_rows": int(len(fit_df)), "val_rows": int(len(val_df)), "test_rows": int(len(te)),
           "test_attack_rate": float(yte.mean()), "seeds": list(seeds),
           "summary": summarise(per_seed), "seed42": per_seed[0], "per_seed": per_seed, **extra}
    (d / "metrics.json").write_text(json.dumps(out, indent=2))
    print("[official] done", flush=True)
    return out


def run_paper(seeds=range(10)):
    d = OUT / "paper_protocol"
    d.mkdir(parents=True, exist_ok=True)
    tr, _ = load_real()
    runs = []
    for seed in seeds:
        print(f"[paper] seed {seed}", flush=True)
        sub = pd.concat([tr[tr.label == 0].sample(4500, random_state=seed), tr[tr.label == 1].sample(4500, random_state=seed)])
        a, rest = train_test_split(sub, test_size=0.30, stratify=sub["label"], random_state=seed)
        v, t = train_test_split(rest, test_size=0.50, stratify=rest["label"], random_state=seed)
        pre = build_preprocessor()
        Xa = pre.fit_transform(a).astype(np.float32)
        Xv, Xt = pre.transform(v).astype(np.float32), pre.transform(t).astype(np.float32)
        m = fit_models(Xa, a["label"].values.astype(int), Xv, v["label"].values.astype(int), seed)
        probs = score_all(m, Xt)
        runs.append({k: metrics(t["label"].values.astype(int), p) for k, p in probs.items()})
        print("   ", {k: round(v_["accuracy"], 4) for k, v_ in runs[-1].items()}, flush=True)
    out = {"protocol": "9,000 balanced flows (4,500 per class) sampled from the official training set, stratified 70/15/15, repeated 10 times",
           "split_sizes": {"train": 6300, "val": 1350, "test": 1350}, "seeds": list(seeds),
           "summary": summarise(runs), "per_seed": runs}
    (d / "metrics.json").write_text(json.dumps(out, indent=2))
    print("[paper] done", flush=True)
    return out


def run_shift():
    """Shipped synthetic-trained engine on real flows, and real-trained models on the synthetic demo CSV."""
    from cipherguard.ids.inference import ThreatSenseEngine
    from cipherguard.ids.synthetic import generate_synthetic
    d = OUT / "shift"
    d.mkdir(parents=True, exist_ok=True)
    _, te = load_real()
    eng = ThreatSenseEngine(models_dir=ROOT / "models")
    eng.load()
    yreal = te["label"].values.astype(int)
    res = eng.predict_proba(te[FEATURE_NAMES].copy())
    out = {"shipped_on_real_official_test": {
        "rows": int(len(te)),
        "stack": metrics(yreal, np.array(res["ensemble_proba"])),
        "xgb": metrics(yreal, np.array(res["xgb_proba"])),
        "cnn": metrics(yreal, np.array(res["cnn_proba"])),
        "predicted_attack_rate": float(np.mean(res["ensemble_pred"])),
    }}
    fresh = generate_synthetic(n_normal=3000, n_attack=3000, seed=7)
    yf = fresh["label"].values.astype(int)
    r2 = eng.predict_proba(fresh[FEATURE_NAMES].copy())
    out["shipped_on_fresh_synthetic_seed7"] = {"rows": int(len(fresh)), "stack": metrics(yf, np.array(r2["ensemble_proba"]))}
    # real-trained (official seed-42 weights) on the synthetic demo CSV
    md = OUT / "official" / "models"
    if (md / "xgb_model.joblib").exists():
        pre = joblib.load(md / "preprocessor.joblib")
        xg, meta = joblib.load(md / "xgb_model.joblib"), joblib.load(md / "stacking_meta.joblib")
        from cipherguard.ids.train import CNN1D_Torch
        sd = torch.load(md / "cnn_model.pt", map_location="cpu")
        cnn = CNN1D_Torch(sd["fc1.weight"].shape[1] // 64 * 4)
        cnn.load_state_dict(sd)
        cnn.eval()
        syn = pd.read_csv(ROOT / "data" / "raw" / "synthetic_demo.csv")
        for c in ("proto", "service", "state"):
            syn[c] = syn[c].astype(str)
        X = pre.transform(syn).astype(np.float32)
        ps = score_all({"xgb": xg, "cnn": cnn, "meta": meta}, X)
        out["real_trained_on_synthetic_demo_csv"] = {"rows": int(len(syn)), "stack": metrics(syn["label"].values.astype(int), ps["stack"])}
    out["synthetic_label_noise"] = {"flipped_rows": 300, "of": 12000, "max_accuracy_if_classes_separable": 0.975}
    (d / "metrics.json").write_text(json.dumps(out, indent=2))
    print("[shift] done", flush=True)
    return out


if __name__ == "__main__":
    todo = sys.argv[1:] or ["official", "paper", "shift"]
    t0 = time.time()
    if "official" in todo:
        run_official()
    if "paper" in todo:
        run_paper()
    if "shift" in todo:
        run_shift()
    print(f"all done in {time.time() - t0:.0f}s")
