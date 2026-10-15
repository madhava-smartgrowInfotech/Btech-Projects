"""Re-measure everything the project documents report, from the shipped code and data.

    python scripts/measure_results.py

Writes docs/experiments/measured.json. Nothing here changes the shipped models: the saved
joblib files are only loaded for evaluation, and all extra training happens in memory.

Sections written to the JSON
  dataset        size, balance, URL length statistics
  reproduce      saved models re-scored on the deterministic 80/20 split (must equal models/metrics.json)
  cv5            5-fold stratified cross-validation of the three classifiers on all 40,000 URLs
  roc            ROC curve points for the three models
  thresholds     precision / recall / FPR of the selected model at several probability cut-offs
  verdict_bands  the deployed safe / suspicious / phishing split (0.35 / 0.60 + reputation discount)
  ablation       feature-group and key-feature ablations for the selected model
  learning       F1 against the share of training data used
  crowd          effect of adding community-confirmed examples (the retraining loop) on unseen URLs
  latency        feature extraction, model scoring and end-to-end API timings
  samples        verdicts for a hand-written set of URLs
  errors         the most confident false positives and false negatives of the selected model
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import tempfile
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import (accuracy_score, f1_score, precision_score, recall_score,
                             roc_auc_score, roc_curve)
from sklearn.model_selection import StratifiedKFold, train_test_split

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from phishguard import config  # noqa: E402

config.TI_DATABASE = Path(tempfile.gettempdir()) / "phishguard_measure.db"
if config.TI_DATABASE.exists():
    os.remove(config.TI_DATABASE)
config.AUTO_RETRAIN_EVERY = 10 ** 9

from phishguard.data import build_matrices, load_dataset  # noqa: E402
from phishguard.detector import Detector  # noqa: E402
from phishguard.features import FEATURE_NAMES, extract_features, featurize_urls  # noqa: E402
from phishguard.threat_intel import ThreatIntel  # noqa: E402
from phishguard.train import build_models, evaluate  # noqa: E402

OUT = ROOT / "docs" / "experiments"
OUT.mkdir(parents=True, exist_ok=True)
R: dict = {}
IDX = {n: i for i, n in enumerate(FEATURE_NAMES)}


def prf(y, pred):
    return {"accuracy": round(float(accuracy_score(y, pred)), 4),
            "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y, pred, zero_division=0)), 4)}


def main():
    t0 = time.time()
    df = load_dataset()
    R["dataset"] = {
        "rows": int(len(df)), "phishing": int(df.label.sum()), "legitimate": int((df.label == 0).sum()),
        "unique_urls": int(df.url.nunique()),
        "with_scheme": int(df.url.str.contains("://").sum()),
        "length_mean": round(float(df.url.str.len().mean()), 1),
        "length_median": float(df.url.str.len().median()),
        "length_max": int(df.url.str.len().max()),
        "length_mean_phishing": round(float(df[df.label == 1].url.str.len().mean()), 1),
        "length_mean_legitimate": round(float(df[df.label == 0].url.str.len().mean()), 1),
        "csv_bytes": int(config.DATASET_CSV.stat().st_size),
    }
    print("dataset", R["dataset"])

    t = time.time()
    X_all = featurize_urls(df["url"].tolist())
    feat_secs = time.time() - t
    y_all = df["label"].to_numpy()
    R["dataset"]["featurize_seconds_40k"] = round(feat_secs, 1)
    X_tr, X_te, y_tr, y_te = build_matrices(df)
    R["split"] = {"train": int(len(y_tr)), "test": int(len(y_te)),
                  "test_phishing": int(y_te.sum()), "test_legitimate": int((y_te == 0).sum())}

    # ---- reproduce metrics.json from the saved model files ---------------------------------
    saved = json.loads(config.METRICS_JSON.read_text())
    models, rep, probs = {}, {}, {}
    for n, path in config.MODEL_FILES.items():
        loaded, refit = None, False
        try:
            loaded = joblib.load(path)
            e = evaluate(loaded, X_te, y_te)
        except Exception as exc:  # a joblib file written by another scikit-learn version
            print("could not score saved", n, "->", type(exc).__name__, exc)
            loaded = build_models()[n]
            loaded.fit(X_tr, y_tr)
            e = evaluate(loaded, X_te, y_te)
            refit = True
        models[n] = loaded
        probs[n] = loaded.predict_proba(X_te)[:, 1]
        rep[n] = {"measured": {k: e[k] for k in ("accuracy", "precision", "recall", "f1", "roc_auc")},
                  "confusion_matrix": e["confusion_matrix"], "refit_in_memory": refit,
                  "matches_metrics_json": all(abs(e[k] - saved["models"][n][k]) < 1e-9
                                              for k in ("accuracy", "precision", "recall", "f1", "roc_auc"))}
    R["reproduce"] = rep
    print("reproduce", {n: v["matches_metrics_json"] for n, v in rep.items()})

    # ---- ROC points -------------------------------------------------------------------------
    roc = {}
    for n, p in probs.items():
        fpr, tpr, _ = roc_curve(y_te, p)
        keep = np.unique(np.linspace(0, len(fpr) - 1, 120).astype(int))
        roc[n] = {"fpr": [round(float(x), 4) for x in fpr[keep]],
                  "tpr": [round(float(x), 4) for x in tpr[keep]],
                  "auc": round(float(roc_auc_score(y_te, p)), 4)}
    R["roc"] = roc

    # ---- thresholds (selected model) ----------------------------------------------------------
    best = saved["best_model"]
    R["best_model"] = best
    pb = probs[best]
    thr = []
    for th in (0.2, 0.3, 0.35, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        pred = (pb >= th).astype(int)
        tn = int(((pred == 0) & (y_te == 0)).sum())
        fp = int(((pred == 1) & (y_te == 0)).sum())
        d = prf(y_te, pred)
        d.update(threshold=th, fpr=round(fp / max(fp + tn, 1), 4), fp=fp,
                 fn=int(((pred == 0) & (y_te == 1)).sum()))
        thr.append(d)
    R["thresholds"] = thr

    # ---- deployed verdict bands (reputation discount + 0.35 / 0.60) --------------------------
    pop = X_te[:, IDX["is_popular_domain"]] == 1
    common = X_te[:, IDX["is_common_tld"]] == 1
    tldlen = X_te[:, IDX["tld_length"]]
    reputable = pop & (common | (tldlen > 2))
    adj = np.where(reputable, pb * 0.4, pb)
    band = np.where(adj >= config.PHISHING_THRESHOLD, "phishing",
                    np.where(adj >= config.SUSPICIOUS_THRESHOLD, "suspicious", "safe"))
    bands = {}
    for cls, name in ((1, "phishing_urls"), (0, "legitimate_urls")):
        sel = y_te == cls
        bands[name] = {b: int((band[sel] == b).sum()) for b in ("phishing", "suspicious", "safe")}
    bands["reputation_discount_applied_to"] = int(reputable.sum())
    bands["phishing_only_as_positive"] = prf(y_te, (band == "phishing").astype(int))
    bands["suspicious_as_positive"] = prf(y_te, (band != "safe").astype(int))
    bands["plain_model_at_0.5"] = prf(y_te, (pb >= 0.5).astype(int))
    R["verdict_bands"] = bands
    print("bands", bands)

    # ---- 5-fold CV ------------------------------------------------------------------------------
    cv = {}
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.RANDOM_STATE)
    for n in ("random_forest", "xgboost", "logistic_regression"):
        accs, f1s, aucs, precs, recs = [], [], [], [], []
        for tr, te in skf.split(X_all, y_all):
            m = build_models()[n]
            m.fit(X_all[tr], y_all[tr])
            e = evaluate(m, X_all[te], y_all[te])
            accs.append(e["accuracy"]); f1s.append(e["f1"]); aucs.append(e["roc_auc"])
            precs.append(e["precision"]); recs.append(e["recall"])
        cv[n] = {k: {"mean": round(float(np.mean(v)), 4), "std": round(float(np.std(v)), 4)}
                 for k, v in (("accuracy", accs), ("precision", precs), ("recall", recs),
                              ("f1", f1s), ("roc_auc", aucs))}
        cv[n]["fold_f1"] = [round(float(x), 4) for x in f1s]
        print("cv", n, cv[n]["f1"])
    R["cv5"] = cv

    # ---- ablations (selected model) ------------------------------------------------------------
    groups = {"lexical": FEATURE_NAMES[:23], "structural": FEATURE_NAMES[23:32], "domain": FEATURE_NAMES[32:]}

    def fit_eval(cols):
        ix = [IDX[c] for c in cols]
        m = build_models()[best]
        m.fit(X_tr[:, ix], y_tr)
        p = m.predict_proba(X_te[:, ix])[:, 1]
        d = prf(y_te, (p >= 0.5).astype(int))
        d["roc_auc"] = round(float(roc_auc_score(y_te, p)), 4)
        d["n_features"] = len(ix)
        return d

    ab = {
        "lexical only": fit_eval(groups["lexical"]),
        "structural only": fit_eval(groups["structural"]),
        "domain only": fit_eval(groups["domain"]),
        "lexical + structural": fit_eval(groups["lexical"] + groups["structural"]),
        "lexical + domain": fit_eval(groups["lexical"] + groups["domain"]),
        "all 47": fit_eval(FEATURE_NAMES),
        "without is_popular_domain": fit_eval([c for c in FEATURE_NAMES if c != "is_popular_domain"]),
        "without is_common_tld": fit_eval([c for c in FEATURE_NAMES if c != "is_common_tld"]),
        "without both": fit_eval([c for c in FEATURE_NAMES if c not in ("is_popular_domain", "is_common_tld")]),
    }
    R["ablation"] = ab
    print("ablation", {k: v["f1"] for k, v in ab.items()})

    # ---- learning curve ---------------------------------------------------------------------------
    rng = np.random.RandomState(config.RANDOM_STATE)
    order = rng.permutation(len(y_tr))
    lc = []
    for frac in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        n = int(len(order) * frac)
        sel = order[:n]
        m = build_models()[best]
        m.fit(X_tr[sel], y_tr[sel])
        p = m.predict_proba(X_te)[:, 1]
        d = prf(y_te, (p >= 0.5).astype(int))
        d.update(fraction=frac, train_rows=n)
        lc.append(d)
    R["learning"] = lc
    print("learning", [(d["train_rows"], d["f1"]) for d in lc])

    # ---- crowd feedback experiment -----------------------------------------------------------------
    crowd = []
    base_model = models[best]
    for k in (250, 500, 1000, 2000):
        b_f1, n_f1, b_acc, n_acc, b_fn, n_fn = [], [], [], [], [], []
        for seed in range(3):
            r = np.random.RandomState(100 + seed)
            perm = r.permutation(len(y_te))
            c_idx, h_idx = perm[:k], perm[k:]
            Xc, yc = X_te[c_idx], y_te[c_idx]
            Xh, yh = X_te[h_idx], y_te[h_idx]
            p0 = base_model.predict(Xh)
            b_f1.append(f1_score(yh, p0)); b_acc.append(accuracy_score(yh, p0))
            b_fn.append(int(((p0 == 0) & (yh == 1)).sum()))
            reps = int(round(config.CROWD_SAMPLE_WEIGHT))
            Xn = np.vstack([X_tr, np.repeat(Xc, reps, axis=0)])
            yn = np.concatenate([y_tr, np.repeat(yc, reps)])
            m = build_models()[best]
            m.fit(Xn, yn)
            p1 = m.predict(Xh)
            n_f1.append(f1_score(yh, p1)); n_acc.append(accuracy_score(yh, p1))
            n_fn.append(int(((p1 == 0) & (yh == 1)).sum()))
        crowd.append({"confirmed_urls": k, "heldout_urls": int(len(y_te) - k),
                      "f1_before": round(float(np.mean(b_f1)), 4), "f1_after": round(float(np.mean(n_f1)), 4),
                      "acc_before": round(float(np.mean(b_acc)), 4), "acc_after": round(float(np.mean(n_acc)), 4),
                      "missed_before": round(float(np.mean(b_fn)), 1), "missed_after": round(float(np.mean(n_fn)), 1),
                      "f1_delta_std": round(float(np.std(np.array(n_f1) - np.array(b_f1))), 4)})
        print("crowd", crowd[-1])
    R["crowd"] = crowd

    # ---- latency ------------------------------------------------------------------------------------
    urls = df["url"].sample(2000, random_state=1).tolist()
    t = time.perf_counter()
    for u in urls:
        extract_features(u)
    fe_ms = (time.perf_counter() - t) / len(urls) * 1000
    ti = ThreatIntel()
    det = Detector(ti)
    t = time.perf_counter()
    for u in urls[:500]:
        det.ml_probability(u)
    ml_ms = (time.perf_counter() - t) / 500 * 1000
    t = time.perf_counter()
    models[best].predict_proba(X_te)
    batch_ms = (time.perf_counter() - t) / len(X_te) * 1000
    from backend.server import build_app
    c = build_app(ti, det).test_client()
    lat = []
    for u in urls[:300]:
        t = time.perf_counter()
        r = c.get("/api/check", query_string={"url": u})
        lat.append((time.perf_counter() - t) * 1000)
        assert r.status_code == 200
    ls = sorted(lat)
    R["latency"] = {
        "feature_extraction_ms_per_url": round(fe_ms, 3),
        "single_url_score_ms": round(ml_ms, 3),
        "batch_scoring_ms_per_url": round(batch_ms, 4),
        "api_check_ms_mean": round(statistics.mean(lat), 2),
        "api_check_ms_median": round(statistics.median(lat), 2),
        "api_check_ms_p95": round(ls[int(len(lat) * 0.95)], 2),
        "api_check_ms_max": round(max(lat), 2),
        "api_requests_timed": len(lat),
        "model_file_bytes": {n: p.stat().st_size for n, p in config.MODEL_FILES.items()},
        "best_model_file_bytes": config.BEST_MODEL_FILE.stat().st_size,
        "train_seconds_from_metrics": {n: saved["models"][n]["train_seconds"] for n in saved["models"]},
    }
    print("latency", R["latency"])

    # ---- sample verdicts ----------------------------------------------------------------------------
    samples = [
        "http://secure-paypal-login.account-verify.tk/signin?user=a",
        "http://192.168.1.5/wp-admin/bank/update.php",
        "http://paypal.com.verify-login.tk/signin?user=a&pwd=b",
        "http://bit.ly/3xYz9Ab",
        "http://apple-id-locked.support-center.xyz/unlock/account.html",
        "http://netflix-billing-update.com/payment/verify",
        "https://github.com/anthropics",
        "https://www.wikipedia.org/wiki/Phishing",
        "https://www.irctc.co.in/nget/train-search",
        "https://docs.python.org/3/library/urllib.html",
        "https://www.amazon.in/gp/cart/view.html",
        "http://free-prize-winner-lucky.top/claim.exe",
        "https://stackoverflow.com/questions/11227809",
        "http://example-bank-secure.info/login.php?session=9f3a",
    ]
    out = []
    for u in samples:
        r = det.check(u, log=False)
        out.append({"url": u, "verdict": r["verdict"], "probability": r["probability"],
                    "decided_by": r["decided_by"], "red_flags": r["red_flags"]})
    R["samples"] = out

    # ---- error analysis -------------------------------------------------------------------------------
    te_urls = df["url"].tolist()
    _, te_idx = train_test_split(np.arange(len(df)), test_size=config.TEST_SIZE,
                                 random_state=config.RANDOM_STATE, stratify=y_all)
    te_u = [te_urls[i] for i in te_idx]
    fp_idx = np.where((pb >= 0.5) & (y_te == 0))[0]
    fn_idx = np.where((pb < 0.5) & (y_te == 1))[0]
    fp_top = fp_idx[np.argsort(-pb[fp_idx])][:8]
    fn_top = fn_idx[np.argsort(pb[fn_idx])][:8]
    R["errors"] = {
        "false_positives": [{"url": te_u[i][:110], "p": round(float(pb[i]), 3)} for i in fp_top],
        "false_negatives": [{"url": te_u[i][:110], "p": round(float(pb[i]), 3)} for i in fn_top],
        "fp_total": int(len(fp_idx)), "fn_total": int(len(fn_idx)),
    }
    R["wall_seconds"] = round(time.time() - t0, 1)
    (OUT / "measured.json").write_text(json.dumps(R, indent=2), encoding="utf-8")
    print("saved", OUT / "measured.json", "in", R["wall_seconds"], "s")


if __name__ == "__main__":
    main()
