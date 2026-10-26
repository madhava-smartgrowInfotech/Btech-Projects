"""Documentation-run experiments for SentinelFlow (real measurements only).

Stages (run from 8.ProjectCode with the project .venv python):
    python scripts/run_experiments.py real       # shipped model + retrained models on real CICIDS2017 Friday-DDoS flows
    python scripts/run_experiments.py hybrid     # product training recipe (real flows + window augmentation), tested on flows AND windows
    python scripts/run_experiments.py windows    # shipped model through the window pipeline at 2/5/10 s windows (simulator generator)
    python scripts/run_experiments.py latency    # per-window processing latency and decision time
    python scripts/run_experiments.py all

Input: the Friday-WorkingHours-Afternoon-DDos CSV of CICIDS2017 (path in env CICIDS_CSV or --csv). Output: JSON files in
results/experiments/. The product artifacts in models/ and results/ are NEVER overwritten.
"""
import argparse
import collections
import json
import os
import sys
import time
import warnings

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,  # noqa: E402
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.naive_bayes import GaussianNB  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402
from sklearn.tree import DecisionTreeClassifier  # noqa: E402

from ml.features import FEATURE_COLUMNS  # noqa: E402
from ml.preprocessing import clean_dataframe, extract_label_series, map_to_common_schema  # noqa: E402
from monitoring.interface_manager import local_ip_set  # noqa: E402
from monitoring.simulator import TrafficSimulator  # noqa: E402
from monitoring.traffic_aggregator import aggregate_packets  # noqa: E402
from security import distributed_analysis, severity  # noqa: E402

OUT = os.path.join(BASE, "results", "experiments")
os.makedirs(OUT, exist_ok=True)
SHIPPED = os.path.join(BASE, "models", "sentinelflow_rf.joblib")


def dump(name, obj):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)
    print("wrote", name)


def scores(y, p, proba=None):
    tn, fp, fn, tp = confusion_matrix(y, p, labels=[0, 1]).ravel()
    out = {
        "accuracy": float(accuracy_score(y, p)),
        "precision": float(precision_score(y, p, zero_division=0)),
        "recall": float(recall_score(y, p, zero_division=0)),
        "f1": float(f1_score(y, p, zero_division=0)),
        "fpr": float(fp / max(fp + tn, 1)),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "n": int(len(y)),
    }
    if proba is not None:
        try:
            out["roc_auc"] = float(roc_auc_score(y, proba))
        except Exception:
            out["roc_auc"] = None
    return out


def load_real(csv):
    raw = pd.read_csv(csv, low_memory=False)
    raw = clean_dataframe(raw)
    labels_raw = raw["label"].astype(str).str.strip()
    y = (extract_label_series(raw) == "ATTACK").astype(int).reset_index(drop=True)
    X = map_to_common_schema(raw).reset_index(drop=True)[FEATURE_COLUMNS]
    return X, y, labels_raw.value_counts().to_dict(), int(len(raw))


def sim_windows(n, window_s, seed, p_attack):
    """Windows from the product's own simulator generator, aggregated through the product's aggregator."""
    sim = TrafficSimulator(seed=seed)
    local = set(local_ip_set()) | {"192.168.1.20"}
    rows, ys, styles, ctxs = [], [], [], []
    for _ in range(n):
        is_attack = sim._rng.random() < p_attack
        pk = sim._make_window(is_attack)
        feats, ctx = aggregate_packets(pk, float(window_s), local)
        rows.append([feats[c] for c in FEATURE_COLUMNS])
        ys.append(int(is_attack))
        if not is_attack:
            styles.append("benign")
        else:
            src = pk[0]["src"]
            styles.append("flood" if src.startswith("10.66") else "carpet" if src.startswith("172.16") else "slow")
        ctxs.append(ctx)
    return pd.DataFrame(rows, columns=FEATURE_COLUMNS), np.array(ys), np.array(styles), ctxs


# ---------------------------------------------------------------- stage: real
def stage_real(csv):
    t0 = time.time()
    X, y, label_counts, n_raw = load_real(csv)
    res = {"dataset": "CICIDS2017 Friday-WorkingHours-Afternoon-DDos (MachineLearningCSV, HF mirror c01dsnap/CIC-IDS2017)",
           "rows": n_raw, "label_counts": label_counts, "benign": int((y == 0).sum()), "attack": int((y == 1).sum())}

    # 1) shipped (synthetic-trained) model on every real flow
    shipped = joblib.load(SHIPPED)
    p = shipped.predict(X)
    res["shipped_on_real_all"] = scores(y, p, shipped.predict_proba(X)[:, 1])
    # shipped on a 20 % stratified sample (same size class as its own test)
    _, Xte, _, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    res["shipped_on_real_20pct"] = scores(yte, shipped.predict(Xte), shipped.predict_proba(Xte)[:, 1])

    # 2) retrain on real flows, same hyper-parameters as the product
    def rf(seed):
        return RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=seed, n_jobs=-1)

    per_seed = []
    for seed in (42, 1, 2, 3, 4):
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=seed, stratify=y)
        t = time.time()
        m = rf(seed).fit(Xtr, ytr)
        tt = time.time() - t
        s = scores(yte, m.predict(Xte), m.predict_proba(Xte)[:, 1])
        s["seed"] = seed
        s["train_seconds"] = round(tt, 2)
        per_seed.append(s)
        if seed == 42:
            res["real_rf_seed42"] = s
            res["real_rf_importance"] = {c: float(v) for c, v in zip(FEATURE_COLUMNS, m.feature_importances_)}
            joblib.dump(m, os.path.join(OUT, "_real_rf_tmp.joblib"), compress=3)
            res["real_rf_model_mb"] = round(os.path.getsize(os.path.join(OUT, "_real_rf_tmp.joblib")) / 1e6, 2)
            os.remove(os.path.join(OUT, "_real_rf_tmp.joblib"))
    res["real_rf_per_seed"] = per_seed
    for k in ("accuracy", "precision", "recall", "f1", "fpr"):
        v = [s[k] for s in per_seed]
        res["real_rf_%s_mean" % k] = float(np.mean(v))
        res["real_rf_%s_std" % k] = float(np.std(v))

    # 3) block split: first 70 % of the file in order -> train, last 30 % -> test (row order is roughly capture order)
    cut = int(len(X) * 0.7)
    m = rf(42).fit(X.iloc[:cut], y.iloc[:cut])
    res["real_rf_block_split"] = scores(y.iloc[cut:], m.predict(X.iloc[cut:]), m.predict_proba(X.iloc[cut:])[:, 1])
    res["block_split_test_benign_share"] = float((y.iloc[cut:] == 0).mean())

    # 4) baselines on the same split (seed 42), echoing the base paper's classifier comparison
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    sub = np.random.default_rng(42).choice(len(Xtr), size=min(60000, len(Xtr)), replace=False)
    base = {}
    for name, mk in [
        ("DecisionTree", lambda: DecisionTreeClassifier(random_state=42, class_weight="balanced")),
        ("RandomForest(200)", lambda: rf(42)),
        ("HistGradientBoosting", lambda: HistGradientBoostingClassifier(random_state=42)),
        ("GaussianNB", lambda: GaussianNB()),
        ("LogisticRegression(scaled)", lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=300, class_weight="balanced"))),
    ]:
        t = time.time()
        mm = mk().fit(Xtr, ytr)
        tt = time.time() - t
        t = time.time()
        pr = mm.predict(Xte)
        it = time.time() - t
        pb = mm.predict_proba(Xte)[:, 1]
        s = scores(yte, pr, pb)
        s["train_seconds"] = round(tt, 2)
        s["predict_seconds_test_set"] = round(it, 3)
        base[name] = s
    res["baselines_seed42"] = base

    # 5) ablation: sent-only / received-only / rates-only / counts-only
    groups = {
        "all_10": FEATURE_COLUMNS,
        "sent_only": [c for c in FEATURE_COLUMNS if "sent" in c],
        "received_only": [c for c in FEATURE_COLUMNS if "received" in c],
        "counts_and_bytes_only": ["received_packets", "received_bytes", "sent_packets", "sent_bytes"],
        "rates_only": [c for c in FEATURE_COLUMNS if "per_second" in c],
        "no_rates": [c for c in FEATURE_COLUMNS if "per_second" not in c],
    }
    abl = {}
    for g, cols in groups.items():
        mm = rf(42).fit(Xtr[cols], ytr)
        abl[g] = scores(yte, mm.predict(Xte[cols]), mm.predict_proba(Xte[cols])[:, 1])
        abl[g]["features"] = cols
    res["ablation_seed42"] = abl

    # 6) real-trained model applied to simulator windows (flow -> window domain gap)
    m42 = rf(42).fit(Xtr, ytr)
    cross = {}
    for ws in (2, 5, 10):
        Xw, yw, _, _ = sim_windows(1500, ws, 99, 0.5)
        cross["window_%ds" % ws] = scores(yw, m42.predict(Xw), m42.predict_proba(Xw)[:, 1])
    res["real_rf_on_sim_windows"] = cross
    res["elapsed_seconds"] = round(time.time() - t0, 1)
    dump("real_cicids2017.json", res)


# -------------------------------------------------------------- stage: hybrid
def stage_hybrid(csv):
    """The product's own training recipe if a real CICIDS2017 CSV had been in data/raw/."""
    t0 = time.time()
    from ml.train_model import generate_window_augmentation
    X, y, _, _ = load_real(csv)
    Xa, ya = generate_window_augmentation()
    Xh = pd.concat([X, Xa], ignore_index=True)
    yh = pd.concat([y, ya], ignore_index=True)
    if len(Xh) > 120000:  # same cap as train_model.py
        idx = np.random.default_rng(42).choice(len(Xh), size=120000, replace=False)
        Xh, yh = Xh.iloc[idx].reset_index(drop=True), yh.iloc[idx].reset_index(drop=True)
    Xtr, Xte, ytr, yte = train_test_split(Xh, yh, test_size=0.2, random_state=42, stratify=yh)
    m = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1).fit(Xtr, ytr)
    res = {"rows_after_cap": int(len(Xh)), "benign": int((yh == 0).sum()), "attack": int((yh == 1).sum()),
           "mixed_test": scores(yte, m.predict(Xte), m.predict_proba(Xte)[:, 1])}
    # held-out REAL flows the hybrid model never saw: use real rows not in training (re-split real only)
    Xr_tr, Xr_te, _, yr_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    res["hybrid_on_real_all_flows"] = scores(y, m.predict(X), m.predict_proba(X)[:, 1])
    res["note_real_flows_overlap"] = "hybrid_on_real_all_flows includes flows seen in training (about 80 % of the sampled rows)"
    # windows (fresh generator seed)
    win = {}
    for ws in (2, 5, 10):
        Xw, yw, _, _ = sim_windows(2000, ws, 2026, 0.5)
        win["window_%ds" % ws] = scores(yw, m.predict(Xw), m.predict_proba(Xw)[:, 1])
    res["hybrid_on_sim_windows"] = win
    res["elapsed_seconds"] = round(time.time() - t0, 1)
    dump("hybrid_recipe.json", res)


# -------------------------------------------------------------- stage: windows
def stage_windows():
    t0 = time.time()
    shipped = joblib.load(SHIPPED)
    out = {}
    for ws in (2, 5, 10):
        n = 4000
        Xw, yw, styles, ctxs = sim_windows(n, ws, 2026, 0.35)
        proba = shipped.predict_proba(Xw)[:, 1]
        pred = (proba >= 0.5).astype(int)
        # stateful pipeline: distributed risk (rolling baseline), persistence, severity
        base = collections.deque(maxlen=12)
        persistence = 0
        sev_labels, sev_scores, risk_scores = [], [], []
        for i in range(n):
            feats = {c: float(Xw.iloc[i][c]) for c in FEATURE_COLUMNS}
            rate = feats["received_packets_per_second"] + feats["sent_packets_per_second"]
            b = {"packet_rate": sum(base) / len(base), "windows": len(base)} if base else None
            dist = distributed_analysis.compute_distributed_risk(feats, ctxs[i], b)
            base.append(rate)
            persistence = persistence + 1 if (pred[i] == 1 or dist["distributed_risk_score"] >= 0.7) else 0
            conf = float(proba[i] if pred[i] == 1 else 1 - proba[i])
            sev = severity.assess_severity("Attack" if pred[i] else "Benign", conf, feats, dist, persistence)
            sev_labels.append(sev["severity"])
            sev_scores.append(sev["severity_score"])
            risk_scores.append(dist["distributed_risk_score"])
        sev_labels = np.array(sev_labels)
        risk_scores = np.array(risk_scores)
        r = {"windows": n, "attack_windows": int(yw.sum()), "benign_windows": int((yw == 0).sum()),
             "ml_only": scores(yw, pred, proba),
             "actionable_high_or_critical": scores(yw, np.isin(sev_labels, ["High", "Critical"]).astype(int)),
             "medium_or_above": scores(yw, np.isin(sev_labels, ["Medium", "High", "Critical"]).astype(int)),
             "distributed_risk_ge_0.7_only": scores(yw, (risk_scores >= 0.7).astype(int)),
             "distributed_risk_ge_0.4_only": scores(yw, (risk_scores >= 0.4).astype(int))}
        by_style = {}
        for s in ("benign", "flood", "carpet", "slow"):
            mk = styles == s
            by_style[s] = {
                "n": int(mk.sum()),
                "ml_attack_rate": float(pred[mk].mean()),
                "actionable_rate": float(np.isin(sev_labels[mk], ["High", "Critical"]).mean()),
                "mean_confidence_attack_class": float(proba[mk].mean()),
                "mean_packet_rate": float((Xw.loc[mk, "received_packets_per_second"] + Xw.loc[mk, "sent_packets_per_second"]).mean()),
                "severity_counts": {k: int((sev_labels[mk] == k).sum()) for k in ("Low", "Medium", "High", "Critical")},
            }
        r["by_style"] = by_style
        r["severity_counts_all"] = {k: int((sev_labels == k).sum()) for k in ("Low", "Medium", "High", "Critical")}
        out["window_%ds" % ws] = r
        print(ws, r["ml_only"]["accuracy"], r["actionable_high_or_critical"]["fpr"])
    out["elapsed_seconds"] = round(time.time() - t0, 1)
    dump("window_pipeline.json", out)


# -------------------------------------------------------------- stage: latency
class _NullDB:
    def add_mitigation(self, *a, **k):
        pass

    def mark_mitigation_recovered(self, *a, **k):
        pass


def stage_latency():
    import tempfile
    from database.db import Database
    from ml import model_loader
    from security import detector
    from security.mitigation import MitigationManager

    tmp = tempfile.mkdtemp(prefix="sf_lat_", dir=os.environ.get("SF_TMP"))
    db = Database(os.path.join(tmp, "lat.db"))
    mit = MitigationManager(db, quarantine_seconds=40)
    model_loader.load_model()
    sim = TrafficSimulator(seed=11)
    local = set(local_ip_set()) | {"192.168.1.20"}
    rows = []
    base = collections.deque(maxlen=12)
    persistence = 0
    for i in range(600):
        is_attack = sim._rng.random() < 0.5
        pk = sim._make_window(is_attack)
        t0 = time.perf_counter()
        feats, ctx = aggregate_packets(pk, 10.0, local)
        t1 = time.perf_counter()
        ml = detector.detect(feats)
        t2 = time.perf_counter()
        rate = feats["received_packets_per_second"] + feats["sent_packets_per_second"]
        dist = distributed_analysis.compute_distributed_risk(feats, ctx, {"packet_rate": sum(base) / len(base), "windows": len(base)} if base else None)
        base.append(rate)
        persistence = persistence + 1 if (ml["label"] == 1 or dist["distributed_risk_score"] >= 0.7) else 0
        sev = severity.assess_severity(ml["prediction"], ml["confidence"], feats, dist, persistence)
        t3 = time.perf_counter()
        acts = mit.decide(sev["severity"], ctx, "latency test")
        t4 = time.perf_counter()
        rec = {"timestamp": time.time(), "interface": "sim", "source": "simulation", "prediction": ml["prediction"],
               "confidence": ml["confidence"], "severity": sev["severity"], "packet_rate": dist["packet_rate"],
               "byte_rate": dist["byte_rate"], "source_count": dist["unique_sources"],
               "destination_count": dist["unique_destinations"], "distributed_risk": dist["distributed_risk_score"],
               "mitigation_status": acts[0]["action"] if acts else "monitor",
               "detail": {"features": feats, "distributed": dist, "severity": sev, "actions": acts}}
        db.add_detection(rec)
        t5 = time.perf_counter()
        rows.append({"packets": len(pk), "aggregate_ms": (t1 - t0) * 1e3, "predict_ms": (t2 - t1) * 1e3,
                     "risk_severity_ms": (t3 - t2) * 1e3, "mitigate_ms": (t4 - t3) * 1e3, "db_ms": (t5 - t4) * 1e3,
                     "total_ms": (t5 - t0) * 1e3, "detect_to_mitigation_ms": (t4 - t1) * 1e3, "attack": int(is_attack)})
    df = pd.DataFrame(rows)

    def q(col):
        return {"mean": float(df[col].mean()), "p50": float(df[col].quantile(.5)), "p95": float(df[col].quantile(.95)),
                "max": float(df[col].max())}

    res = {"windows": len(df), "mean_packets_per_window": float(df["packets"].mean()),
           "max_packets_per_window": int(df["packets"].max())}
    for col in ("aggregate_ms", "predict_ms", "risk_severity_ms", "mitigate_ms", "db_ms", "total_ms", "detect_to_mitigation_ms"):
        res[col] = q(col)
    # single-row inference (what the dashboard path does); the shipped model was saved with n_jobs=-1
    import psutil
    res["host_cpu_percent_during_run"] = psutil.cpu_percent(interval=1.0)
    feats = {c: float(v) for c, v in zip(FEATURE_COLUMNS, [100, 60000, 10, 6000, 600, 90, 20000, 9, 2000, 220])}
    lat = []
    for _ in range(300):
        t = time.perf_counter()
        model_loader.predict_traffic(feats)
        lat.append((time.perf_counter() - t) * 1e3)
    res["single_inference_ms"] = {"mean": float(np.mean(lat)), "p50": float(np.percentile(lat, 50)),
                                  "p95": float(np.percentile(lat, 95)), "max": float(np.max(lat))}
    m_ = model_loader._MODEL
    saved_jobs = m_.n_jobs
    for nj in (1, -1):
        m_.n_jobs = nj
        lat2 = []
        for _ in range(200):
            t = time.perf_counter()
            model_loader.predict_traffic(feats)
            lat2.append((time.perf_counter() - t) * 1e3)
        res["single_inference_ms_n_jobs_%d" % nj] = {"mean": float(np.mean(lat2)), "p50": float(np.percentile(lat2, 50)),
                                                     "p95": float(np.percentile(lat2, 95)), "max": float(np.max(lat2))}
    m_.n_jobs = saved_jobs
    res["model_n_jobs_as_shipped"] = saved_jobs
    res["model_file_mb"] = round(os.path.getsize(SHIPPED) / 1e6, 2)
    # model load time and memory
    t = time.perf_counter()
    joblib.load(SHIPPED)
    res["model_load_seconds"] = round(time.perf_counter() - t, 3)
    dump("latency.json", res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["real", "hybrid", "windows", "latency", "all"])
    ap.add_argument("--csv", default=os.environ.get("CICIDS_CSV", ""))
    a = ap.parse_args()
    if a.stage in ("real", "all"):
        stage_real(a.csv)
    if a.stage in ("hybrid", "all"):
        stage_hybrid(a.csv)
    if a.stage in ("windows", "all"):
        stage_windows()
    if a.stage in ("latency", "all"):
        stage_latency()
