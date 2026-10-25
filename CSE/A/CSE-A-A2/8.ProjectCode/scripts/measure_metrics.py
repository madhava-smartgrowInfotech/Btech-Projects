"""ResQAI model evaluation: every number the documentation quotes about the two classifiers comes from here.

Run from the project folder:   python scripts/measure_metrics.py
Writes experiments/resqai_eval/metrics.json.

What it measures (all on the synthetic sensor-event dataset that train_models.py generates, because the project
ships no real crash recordings):
  1. the shipped models/*.pkl on the exact held-out 20 % split train_models.py uses (n = 2,400 of 12,000);
  2. a fresh retrain with the same hyper-parameters, and how often it agrees with the shipped pickles;
  3. a 5-seed repeat (new dataset + new split + new forest per seed) for mean and spread;
  4. baselines on the same split (rule-based fallback, logistic regression, decision tree, gradient boosting);
  5. feature importance, permutation importance and feature-group ablations;
  6. robustness to additive sensor noise;
  7. out-of-distribution probes: pothole and speed-breaker events that the generator never produces (constructed here,
     NOT real recordings - the parameters are in make_probe_events);
  8. a decision-threshold sweep for the accident detector;
  9. in-process inference latency.
"""
import json
import math
import sys
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import sklearn  # noqa: E402

import train_models as tm  # noqa: E402  (seeds numpy with 42 on import, like a real training run)

OUT = ROOT / "experiments" / "resqai_eval"
OUT.mkdir(parents=True, exist_ok=True)
FEATURES = tm.FEATURE_NAMES
SEV_NAMES = ["None", "Minor", "Moderate", "Severe"]
KINDS = ["normal", "harsh_brake", "minor_crash", "moderate_crash", "severe_crash"]
KIND_P = [0.60, 0.20, 0.10, 0.06, 0.04]
SEED = tm.RANDOM_STATE


def make_dataset(seed, n=tm.N_SAMPLES):
    """Same procedure as tm.generate_dataset, but also returns the event kind of every row."""
    np.random.seed(seed)
    kinds = np.random.choice(KINDS, size=n, p=KIND_P)
    df = pd.DataFrame([tm.make_event(k) for k in kinds])
    df["kind"] = kinds
    return df


def split(df, seed):
    idx = np.arange(len(df))
    tr, te = train_test_split(idx, test_size=0.2, random_state=seed, stratify=df["accident"].values)
    return tr, te


def fit_models(Xtr, y_acc, y_sev, seed):
    sc = StandardScaler().fit(Xtr)
    det = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=seed, class_weight="balanced")
    det.fit(sc.transform(Xtr), y_acc)
    sev = RandomForestClassifier(n_estimators=250, max_depth=12, random_state=seed, class_weight="balanced")
    sev.fit(sc.transform(Xtr), y_sev)
    return sc, det, sev


def app_predict(sc, det, sev, X):
    """The decision logic of app.predict_from_features: severity forced to None when the detector says no accident."""
    Xs = sc.transform(X)
    acc = det.predict(Xs)
    proba = det.predict_proba(Xs)[:, 1]
    sv = sev.predict(Xs)
    sv = np.where(acc == 0, 0, sv)
    return acc.astype(int), sv.astype(int), proba


def bin_metrics(y, p, proba=None):
    tn, fp, fn, tp = confusion_matrix(y, p, labels=[0, 1]).ravel()
    out = {
        "n": int(len(y)), "accuracy": accuracy_score(y, p), "precision": precision_score(y, p, zero_division=0),
        "recall": recall_score(y, p, zero_division=0), "f1": f1_score(y, p, zero_division=0),
        "false_alarm_rate": fp / (fp + tn) if fp + tn else 0.0, "miss_rate": fn / (fn + tp) if fn + tp else 0.0,
        "confusion": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }
    if proba is not None and len(set(y)) == 2:
        out["roc_auc"] = roc_auc_score(y, proba)
    return {k: (round(v, 5) if isinstance(v, float) else v) for k, v in out.items()}


def sev_metrics(y, p):
    pr, rc, f1, sup = precision_recall_fscore_support(y, p, labels=[0, 1, 2, 3], zero_division=0)
    cm = confusion_matrix(y, p, labels=[0, 1, 2, 3])
    adjacent = int(np.sum(np.abs(np.array(y) - np.array(p)) == 1))
    wrong = int(np.sum(np.array(y) != np.array(p)))
    return {
        "n": int(len(y)), "accuracy": round(accuracy_score(y, p), 5), "macro_f1": round(f1_score(y, p, average="macro", zero_division=0), 5),
        "weighted_f1": round(f1_score(y, p, average="weighted", zero_division=0), 5),
        "per_class": {SEV_NAMES[i]: {"precision": round(pr[i], 4), "recall": round(rc[i], 4), "f1": round(f1[i], 4), "support": int(sup[i])} for i in range(4)},
        "confusion": cm.tolist(), "errors": wrong, "adjacent_class_errors": adjacent,
        "adjacent_share_of_errors": round(adjacent / wrong, 4) if wrong else None,
    }


def alert_metrics(true_sev, pred_sev):
    """The app only starts the 15 s confirmation for Moderate/Severe results; measure that decision on its own."""
    y = (np.array(true_sev) >= 2).astype(int)
    p = (np.array(pred_sev) >= 2).astype(int)
    return bin_metrics(y, p)


def rule_predict(X):
    """app.rule_based_fallback thresholds applied to acc_magnitude (column 3)."""
    mag = X[:, FEATURES.index("acc_magnitude")]
    sev = np.where(mag < 15, 0, np.where(mag < 28, 1, np.where(mag < 45, 2, 3)))
    return (sev > 0).astype(int), sev


def with_noise(df_raw, k, rng, scale):
    """Add N(0, (k*scale)^2) noise to the nine raw sensor channels and recompute magnitudes."""
    d = df_raw.copy()
    for c in ["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z", "speed_before", "speed_change", "jerk"]:
        d[c] = d[c] + rng.normal(0, k * scale[c], len(d))
    d["jerk"] = d["jerk"].abs()
    d["acc_magnitude"] = np.sqrt(d.acc_x ** 2 + d.acc_y ** 2 + d.acc_z ** 2)
    d["gyro_magnitude"] = np.sqrt(d.gyro_x ** 2 + d.gyro_y ** 2 + d.gyro_z ** 2)
    return d


def make_probe_events(kind, n, rng):
    """Events the training generator never produces. Parameters are our own construction (documented in the report)."""
    g = 9.81
    rows = []
    for _ in range(n):
        if kind == "pothole":
            sign = rng.choice([-1, 1])
            r = dict(acc_x=rng.normal(0, 1.0), acc_y=rng.normal(0, 1.0), acc_z=g + sign * rng.uniform(6, 18),
                     gyro_x=rng.normal(0, 0.6), gyro_y=rng.normal(0, 0.6), gyro_z=rng.normal(0, 0.4),
                     speed_before=rng.uniform(10, 60), speed_change=rng.normal(0, 3), jerk=abs(rng.normal(12, 4)))
        else:  # speed_breaker
            r = dict(acc_x=rng.normal(-1.0, 0.8), acc_y=rng.normal(0, 0.6), acc_z=g + rng.uniform(3, 9),
                     gyro_x=rng.normal(0, 0.4), gyro_y=rng.normal(0, 0.4), gyro_z=rng.normal(0, 0.3),
                     speed_before=rng.uniform(5, 30), speed_change=-rng.uniform(0, 8), jerk=abs(rng.normal(5, 2)))
        r["acc_magnitude"] = math.sqrt(r["acc_x"] ** 2 + r["acc_y"] ** 2 + r["acc_z"] ** 2)
        r["gyro_magnitude"] = math.sqrt(r["gyro_x"] ** 2 + r["gyro_y"] ** 2 + r["gyro_z"] ** 2)
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    t0 = time.time()
    res = {"environment": {"python": sys.version.split()[0], "sklearn": sklearn.__version__, "numpy": np.__version__,
                           "pandas": pd.__version__}}

    # ------------------------------------------------------------------ dataset (seed 42, as in train_models.py)
    df = make_dataset(SEED)
    check = None
    np.random.seed(SEED)
    ref = tm.generate_dataset()
    check = bool(np.allclose(ref[FEATURES + ["accident", "severity"]].values, df[FEATURES + ["accident", "severity"]].values))
    tr, te = split(df, SEED)
    Xtr, Xte = df.loc[tr, FEATURES].values, df.loc[te, FEATURES].values
    yacc_tr, yacc_te = df.loc[tr, "accident"].values, df.loc[te, "accident"].values
    ysev_tr, ysev_te = df.loc[tr, "severity"].values, df.loc[te, "severity"].values
    kinds_te = df.loc[te, "kind"].values
    res["dataset"] = {
        "generator_reproduces_train_models": check, "n_total": int(len(df)), "n_train": int(len(tr)), "n_test": int(len(te)),
        "features": FEATURES, "kind_counts_total": df["kind"].value_counts().to_dict(),
        "severity_counts_total": {SEV_NAMES[k]: int(v) for k, v in df["severity"].value_counts().sort_index().items()},
        "accident_rate_total": round(float(df["accident"].mean()), 4),
        "kind_counts_test": {k: int(v) for k, v in pd.Series(kinds_te).value_counts().items()},
        "severity_counts_test": {SEV_NAMES[k]: int(v) for k, v in pd.Series(ysev_te).value_counts().sort_index().items()},
        "class_overlap": {c: {k: [round(float(df.loc[df.kind == k, c].min()), 2), round(float(df.loc[df.kind == k, c].max()), 2)] for k in KINDS}
                          for c in ["acc_magnitude", "jerk", "speed_change"]},
    }

    # ------------------------------------------------------------------ 1. shipped models
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        sdet = joblib.load(ROOT / "models" / "accident_detector.pkl")
        ssev = joblib.load(ROOT / "models" / "severity_predictor.pkl")
        ssc = joblib.load(ROOT / "models" / "feature_scaler.pkl")
        names = joblib.load(ROOT / "models" / "feature_names.pkl")
    res["shipped_model"] = {"feature_names_match": list(names) == FEATURES, "pickle_version_warnings": sorted({str(x.message)[:120] for x in w}),
                            "detector": {"n_estimators": sdet.n_estimators, "max_depth": sdet.max_depth},
                            "severity": {"n_estimators": ssev.n_estimators, "max_depth": ssev.max_depth}}
    acc_p, sev_p, proba = app_predict(ssc, sdet, ssev, Xte)
    res["shipped_model"]["detector_test"] = bin_metrics(yacc_te, acc_p, proba)
    res["shipped_model"]["severity_test_after_gating"] = sev_metrics(ysev_te, sev_p)
    res["shipped_model"]["alert_trigger_test"] = alert_metrics(ysev_te, sev_p)
    # raw severity model without the detector gate
    res["shipped_model"]["severity_test_raw"] = sev_metrics(ysev_te, ssev.predict(ssc.transform(Xte)))
    # training-set score (generalisation gap)
    a_tr, s_tr, _ = app_predict(ssc, sdet, ssev, Xtr)
    res["shipped_model"]["detector_train_accuracy"] = round(accuracy_score(yacc_tr, a_tr), 5)
    res["shipped_model"]["severity_train_accuracy"] = round(accuracy_score(ysev_tr, s_tr), 5)
    # per event kind
    per_kind = {}
    for k in KINDS:
        m = kinds_te == k
        per_kind[k] = {"n": int(m.sum()), "predicted_accident_rate": round(float(acc_p[m].mean()), 4),
                       "alert_trigger_rate": round(float((sev_p[m] >= 2).mean()), 4),
                       "predicted_severity_counts": {SEV_NAMES[s]: int((sev_p[m] == s).sum()) for s in range(4)},
                       "mean_accident_probability": round(float(proba[m].mean()), 4)}
    res["shipped_model"]["per_event_kind"] = per_kind
    wrong_idx = np.where((acc_p != yacc_te) | (sev_p != ysev_te))[0]
    res["shipped_model"]["misclassified_examples"] = [
        {"kind": str(kinds_te[i]), "true_severity": SEV_NAMES[ysev_te[i]], "pred_severity": SEV_NAMES[sev_p[i]],
         "accident_probability": round(float(proba[i]), 3), **{f: round(float(Xte[i][j]), 2) for j, f in enumerate(FEATURES) if f in ("acc_magnitude", "gyro_magnitude", "speed_before", "speed_change", "jerk")}}
        for i in wrong_idx[:12]]

    # ------------------------------------------------------------------ 2. fresh retrain
    sc, det, sev = fit_models(Xtr, yacc_tr, ysev_tr, SEED)
    a2, s2, p2 = app_predict(sc, det, sev, Xte)
    res["retrained_same_seed"] = {"detector_test": bin_metrics(yacc_te, a2, p2), "severity_test": sev_metrics(ysev_te, s2),
                                  "alert_trigger_test": alert_metrics(ysev_te, s2),
                                  "agreement_with_shipped_detector": round(float((a2 == acc_p).mean()), 5),
                                  "agreement_with_shipped_severity": round(float((s2 == sev_p).mean()), 5)}

    # ------------------------------------------------------------------ 3. five-seed study
    seeds = [11, 22, 33, 44, 55]
    rows = []
    for s in seeds:
        d = make_dataset(s)
        a, b = split(d, s)
        sc_s, det_s, sev_s = fit_models(d.loc[a, FEATURES].values, d.loc[a, "accident"].values, d.loc[a, "severity"].values, s)
        ap, sp, pp = app_predict(sc_s, det_s, sev_s, d.loc[b, FEATURES].values)
        dm = bin_metrics(d.loc[b, "accident"].values, ap, pp)
        sm = sev_metrics(d.loc[b, "severity"].values, sp)
        am = alert_metrics(d.loc[b, "severity"].values, sp)
        rows.append({"seed": s, "det_accuracy": dm["accuracy"], "det_f1": dm["f1"], "det_recall": dm["recall"], "det_false_alarm": dm["false_alarm_rate"],
                     "sev_accuracy": sm["accuracy"], "sev_macro_f1": sm["macro_f1"], "alert_precision": am["precision"], "alert_recall": am["recall"],
                     "alert_false_alarm": am["false_alarm_rate"]})
    sd = pd.DataFrame(rows)
    res["five_seed"] = {"seeds": seeds, "rows": rows,
                        "mean": {c: round(float(sd[c].mean()), 5) for c in sd.columns if c != "seed"},
                        "std": {c: round(float(sd[c].std(ddof=1)), 5) for c in sd.columns if c != "seed"},
                        "min": {c: round(float(sd[c].min()), 5) for c in sd.columns if c != "seed"}}

    # ------------------------------------------------------------------ 4. baselines on the seed-42 split
    base = {}
    Xtr_s, Xte_s = sc.transform(Xtr), sc.transform(Xte)
    ra, rs = rule_predict(Xte)
    base["rule_based_fallback (acc_magnitude < 15 / 28 / 45)"] = {"det_accuracy": round(accuracy_score(yacc_te, ra), 4), "det_f1": round(f1_score(yacc_te, ra), 4),
                                                                   "det_false_alarm": bin_metrics(yacc_te, ra)["false_alarm_rate"],
                                                                   "sev_accuracy": round(accuracy_score(ysev_te, rs), 4), "sev_macro_f1": round(f1_score(ysev_te, rs, average="macro"), 4)}
    models = {
        "logistic_regression": lambda: LogisticRegression(max_iter=2000, class_weight="balanced"),
        "decision_tree (depth 10)": lambda: DecisionTreeClassifier(max_depth=10, random_state=SEED, class_weight="balanced"),
        "hist_gradient_boosting": lambda: HistGradientBoostingClassifier(random_state=SEED),
    }
    for name, mk in models.items():
        ma, ms = mk().fit(Xtr_s, yacc_tr), mk().fit(Xtr_s, ysev_tr)
        pa, ps = ma.predict(Xte_s), ms.predict(Xte_s)
        ps = np.where(pa == 0, 0, ps)
        base[name] = {"det_accuracy": round(accuracy_score(yacc_te, pa), 4), "det_f1": round(f1_score(yacc_te, pa), 4),
                      "det_false_alarm": bin_metrics(yacc_te, pa)["false_alarm_rate"],
                      "sev_accuracy": round(accuracy_score(ysev_te, ps), 4), "sev_macro_f1": round(f1_score(ysev_te, ps, average="macro"), 4)}
    base["random_forest (ResQAI, retrained)"] = {"det_accuracy": res["retrained_same_seed"]["detector_test"]["accuracy"], "det_f1": res["retrained_same_seed"]["detector_test"]["f1"],
                                                  "det_false_alarm": res["retrained_same_seed"]["detector_test"]["false_alarm_rate"],
                                                  "sev_accuracy": res["retrained_same_seed"]["severity_test"]["accuracy"], "sev_macro_f1": res["retrained_same_seed"]["severity_test"]["macro_f1"]}
    res["baselines"] = base

    # ------------------------------------------------------------------ 5. importance and ablations
    imp_d = dict(zip(FEATURES, [round(float(v), 4) for v in sdet.feature_importances_]))
    imp_s = dict(zip(FEATURES, [round(float(v), 4) for v in ssev.feature_importances_]))
    Xte_scaled = ssc.transform(Xte)
    pi_d = permutation_importance(sdet, Xte_scaled, yacc_te, scoring="f1", n_repeats=5, random_state=SEED)
    pi_s = permutation_importance(ssev, Xte_scaled, ysev_te, scoring="f1_macro", n_repeats=5, random_state=SEED)
    res["importance"] = {"detector_gini": imp_d, "severity_gini": imp_s,
                         "detector_permutation_f1_drop": {f: round(float(v), 4) for f, v in zip(FEATURES, pi_d.importances_mean)},
                         "severity_permutation_macro_f1_drop": {f: round(float(v), 4) for f, v in zip(FEATURES, pi_s.importances_mean)}}
    groups = {
        "all 11 features": FEATURES,
        "accelerometer only (x, y, z, magnitude)": ["acc_x", "acc_y", "acc_z", "acc_magnitude"],
        "acc_magnitude only": ["acc_magnitude"],
        "without gyroscope": [f for f in FEATURES if not f.startswith("gyro")],
        "without speed (speed_before, speed_change)": [f for f in FEATURES if f not in ("speed_before", "speed_change")],
        "without jerk": [f for f in FEATURES if f != "jerk"],
        "without acc_magnitude and jerk": [f for f in FEATURES if f not in ("acc_magnitude", "jerk")],
    }
    abl = {}
    for gname, cols in groups.items():
        ci = [FEATURES.index(c) for c in cols]
        s2_ = StandardScaler().fit(Xtr[:, ci])
        d_ = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=SEED, class_weight="balanced").fit(s2_.transform(Xtr[:, ci]), yacc_tr)
        v_ = RandomForestClassifier(n_estimators=250, max_depth=12, random_state=SEED, class_weight="balanced").fit(s2_.transform(Xtr[:, ci]), ysev_tr)
        pa = d_.predict(s2_.transform(Xte[:, ci]))
        ps = np.where(pa == 0, 0, v_.predict(s2_.transform(Xte[:, ci])))
        abl[gname] = {"n_features": len(cols), "det_accuracy": round(accuracy_score(yacc_te, pa), 4), "det_f1": round(f1_score(yacc_te, pa), 4),
                      "det_false_alarm": bin_metrics(yacc_te, pa)["false_alarm_rate"],
                      "sev_accuracy": round(accuracy_score(ysev_te, ps), 4), "sev_macro_f1": round(f1_score(ysev_te, ps, average="macro"), 4)}
    res["ablation"] = abl

    # ------------------------------------------------------------------ 6. noise robustness (shipped models)
    raw_te = df.loc[te, FEATURES].reset_index(drop=True)
    scale = {c: float(raw_te[c].std()) for c in ["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z", "speed_before", "speed_change", "jerk"]}
    noise = []
    for k in [0.0, 0.05, 0.1, 0.25, 0.5, 1.0]:
        rng = np.random.default_rng(SEED)
        dn = with_noise(raw_te, k, rng, scale)
        a_, s_, p_ = app_predict(ssc, sdet, ssev, dn[FEATURES].values)
        dm, sm = bin_metrics(yacc_te, a_, p_), sev_metrics(ysev_te, s_)
        noise.append({"noise_sd_fraction_of_feature_sd": k, "det_accuracy": dm["accuracy"], "det_f1": dm["f1"], "det_false_alarm": dm["false_alarm_rate"],
                      "det_recall": dm["recall"], "sev_accuracy": sm["accuracy"], "sev_macro_f1": sm["macro_f1"]})
    res["noise_robustness"] = noise

    # ------------------------------------------------------------------ 7. out-of-distribution probes
    rng = np.random.default_rng(2026)
    probes = {}
    for kind in ["pothole", "speed_breaker"]:
        dp = make_probe_events(kind, 1000, rng)
        a_, s_, p_ = app_predict(ssc, sdet, ssev, dp[FEATURES].values)
        probes[kind] = {"n": 1000, "predicted_accident_rate": round(float(a_.mean()), 4), "alert_trigger_rate": round(float((s_ >= 2).mean()), 4),
                        "mean_accident_probability": round(float(p_.mean()), 4),
                        "predicted_severity_counts": {SEV_NAMES[s]: int((s_ == s).sum()) for s in range(4)},
                        "acc_magnitude_range": [round(float(dp.acc_magnitude.min()), 1), round(float(dp.acc_magnitude.max()), 1)]}
    res["ood_probes"] = probes
    # low-severity edge: a crash-magnitude spike at very low speed (the generator's minor crash starts at 10 km/h)
    # (kept out: no ground truth beyond our own construction)

    # ------------------------------------------------------------------ 8. detector threshold sweep (shipped model)
    sweep = []
    for t in [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]:
        p = (proba >= t).astype(int)
        m = bin_metrics(yacc_te, p)
        sweep.append({"threshold": t, "precision": m["precision"], "recall": m["recall"], "f1": m["f1"], "false_alarm_rate": m["false_alarm_rate"],
                      "false_positives": m["confusion"][0][1], "false_negatives": m["confusion"][1][0]})
    res["threshold_sweep"] = sweep
    res["probability_separation"] = {"min_proba_true_accident": round(float(proba[yacc_te == 1].min()), 4), "max_proba_true_non_accident": round(float(proba[yacc_te == 0].max()), 4)}

    # ------------------------------------------------------------------ 9. in-process inference latency
    x1 = Xte[:1]
    times = []
    for i in range(1200):
        x = Xte[i:i + 1]
        t1 = time.perf_counter()
        app_predict(ssc, sdet, ssev, x)
        times.append((time.perf_counter() - t1) * 1000)
    times = np.array(times[200:])
    res["inference_latency_ms"] = {"n": int(len(times)), "mean": round(float(times.mean()), 2), "p50": round(float(np.percentile(times, 50)), 2),
                                   "p95": round(float(np.percentile(times, 95)), 2), "p99": round(float(np.percentile(times, 99)), 2), "max": round(float(times.max()), 2),
                                   "note": "scaler + both forests, one reading, single process, no HTTP"}
    res["model_size_kb"] = {f: round((ROOT / "models" / f).stat().st_size / 1024, 1) for f in ["accident_detector.pkl", "severity_predictor.pkl", "feature_scaler.pkl", "feature_names.pkl"]}
    res["elapsed_s"] = round(time.time() - t0, 1)
    (OUT / "metrics.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ["shipped_model", "five_seed"]}, indent=1)[:6000])
    print("saved", OUT / "metrics.json", "in", res["elapsed_s"], "s")


if __name__ == "__main__":
    main()
