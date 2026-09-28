"""Evaluate every saved model against the objectives -> experiments/eval/metrics.json.

Uses the trained files in models/ (no retraining). Leak evaluation runs on a fresh set of twin scenarios
generated with a different seed than the training scenarios.
"""
import json
import sys
from datetime import timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import anomaly, demand, imbalance, leaks, quality, twin  # noqa: E402

OUT = ROOT / "experiments" / "eval" / "metrics.json"


def eval_quality():
    df = pd.read_csv(ROOT / "data" / "water_potability.csv")
    X, y = df[quality.FEATURES], df["Potability"].astype(int)
    _, Xte, _, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    b = quality.bundle()
    model = b["model"]
    p = model.predict_proba(Xte)[:, 1]
    out = {"test_rows": len(Xte),
           "stacking_ensemble": {"accuracy": round(accuracy_score(yte, p >= 0.5), 4), "f1": round(f1_score(yte, p >= 0.5), 4),
                                 "roc_auc": round(roc_auc_score(yte, p), 4),
                                 "confusion_matrix": confusion_matrix(yte, p >= 0.5).tolist()},
           "members": {}}
    Xi = model.named_steps["impute"].transform(Xte)
    for name, est in zip(b["member_names"], model.named_steps["stack"].estimators_):
        q = est.predict_proba(Xi)[:, 1]
        out["members"][name] = {"accuracy": round(accuracy_score(yte, q >= 0.5), 4), "f1": round(f1_score(yte, q >= 0.5), 4),
                                "roc_auc": round(roc_auc_score(yte, q), 4)}
    return out


def eval_demand(test_days=90):
    hist = demand.load_history()
    cutoff = hist["date"].max() - timedelta(days=test_days)
    errs, naive = [], []
    origins = pd.date_range(cutoff, hist["date"].max() - timedelta(days=7), freq="7D")
    for o in origins:
        past = hist[hist["date"] <= o]
        fut = hist[(hist["date"] > o) & (hist["date"] <= o + timedelta(days=7))]
        weather = fut.drop_duplicates("date").sort_values("date")[["tmax", "tmin", "precip"]].reset_index(drop=True)
        fc = demand.recursive_forecast(past, weather, 7)
        fc["date"] = pd.to_datetime(fc["date"])
        j = fc.merge(fut, on=["date", "zone"])
        errs.extend(np.abs(j.forecast_m3 - j.consumption_m3) / j.consumption_m3)
        # seasonal naive: same weekday last week
        lw = past[past["date"] > o - timedelta(days=7)].copy()
        lw["date"] = lw["date"] + timedelta(days=7)
        k = lw.merge(fut, on=["date", "zone"], suffixes=("_lw", ""))
        naive.extend(np.abs(k.consumption_m3_lw - k.consumption_m3) / k.consumption_m3)
    return {"horizon_days": 7, "origins": len(origins), "test_days": test_days,
            "xgboost_mape": round(float(np.mean(errs)) * 100, 2),
            "seasonal_naive_mape": round(float(np.mean(naive)) * 100, 2)}


def eval_leaks(n_leak=150, n_none=150):
    rng = np.random.default_rng(777)  # different seed from the training scenarios
    pipes = twin.candidate_pipes()
    y, p, top1, top3, zone = [], [], 0, 0, 0
    for i in range(n_leak + n_none):
        pipe = str(rng.choice(pipes)) if i < n_leak else None
        lps = float(rng.uniform(2.0, 20.0)) if pipe else 0.0
        res = twin.residuals(twin.observe(pipe, lps, rng))
        a = leaks.analyze(res)
        y.append(int(pipe is not None))
        p.append(a["leak_probability"])
        if pipe:
            ranked = [r["pipe"] for r in a["ranking"]]
            top1 += ranked[0] == pipe
            top3 += pipe in ranked[:3]
            zone += a["ranking"][0]["zone"] == twin.pipe_zone()[pipe]
    y, p = np.array(y), np.array(p)
    return {"scenarios": len(y), "leak_size_lps": [2, 20], "candidate_pipes": len(pipes),
            "detection": {"precision": round(precision_score(y, p >= 0.5), 4), "recall": round(recall_score(y, p >= 0.5), 4),
                          "f1": round(f1_score(y, p >= 0.5), 4), "roc_auc": round(roc_auc_score(y, p), 4)},
            "localisation": {"top1_accuracy": round(top1 / n_leak, 4), "top3_accuracy": round(top3 / n_leak, 4),
                             "zone_accuracy": round(zone / n_leak, 4)}}


def eval_anomaly():
    s = anomaly.scored()
    truth = pd.read_csv(ROOT / "data" / "sample" / "meter_anomaly_truth.csv", parse_dates=["date"])
    s = s.merge(truth.rename(columns={"type": "true_type"}), on=["meter_id", "date"], how="left")
    yt = s.true_type.notna()
    flagged = {m["meter_id"] for m in anomaly.flagged_meters()}
    last = s.date.max()
    true_recent = set(truth[truth.date > last - pd.Timedelta(days=anomaly.RECENT_DAYS)].meter_id)
    tp = len(flagged & true_recent)
    return {"meter_days": len(s),
            "day_level": {"precision": round(precision_score(yt, s.anomaly), 4), "recall": round(recall_score(yt, s.anomaly), 4)},
            "meter_level_last_7_days": {"precision": round(tp / max(1, len(flagged)), 4),
                                        "recall": round(tp / max(1, len(true_recent)), 4)}}


def eval_imbalance():
    a = imbalance.analyse()
    rec = a["suggestion"]["recommended"]
    return {"equity_before": a["current"]["equity_score"], "nrw_before_pct": a["current"]["nrw_pct"],
            "equity_after": rec["equity_score"] if rec else a["current"]["equity_score"],
            "nrw_after_pct": rec["nrw_pct"] if rec else a["current"]["nrw_pct"],
            "action": imbalance.describe_action(rec["pump_speed"], rec["throttle"]) if rec else "none",
            "worst_zone": a["worst_zone"]}


def main():
    metrics = {"quality": eval_quality(), "demand": eval_demand(), "leaks": eval_leaks(),
               "anomaly": eval_anomaly(), "imbalance": eval_imbalance()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(metrics, indent=1))
    print(json.dumps(metrics, indent=1))


if __name__ == "__main__":
    main()
