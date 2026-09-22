"""Train the radio-condition estimate used as supporting evidence for phone-probe readings.

    python ml/train_throughput_model.py            # full run -> experiments/radio_estimate_<stamp>/ + models/radio_estimate.*
    python ml/train_throughput_model.py --quick    # smoke run (does not touch models/)

A phone browser measures speed, not radio metrics. This model learns, from drive-test traces that
record both, how well speed tests predict the radio class (from the 3GPP-style ranges). Probe speed
tests are reproduced from the traces: a test is the mean download/upload over 5 seconds, and each
virtual device runs one test per minute (three interleaved devices per trace, offsets 0/20/40 s).
"""
from __future__ import annotations

import argparse
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import h3
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

import _plots as P
from _common import EXPERIMENTS, MODELS, PROCESSED, SEED, new_run, seed_everything, write_json
from app.ml.calibration import CalibratedModel, expected_calibration_error, fit_temperature
from app.ml.service_quality import SPEED_FEATURES, speed_features
from app.ml.signal_ranges import CLASSES

TEST_SECONDS, TEST_SPACING, OFFSETS = 5, 60, (0, 20, 40)


def simulate_speed_tests(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df.state == "D"].copy()
    d["t_rel"] = d.groupby("device_key").ts.transform(lambda s: (s - s.min()).dt.total_seconds())
    tests = []
    for off in OFFSETS:
        x = d[d.t_rel >= off].copy()
        phase = (x.t_rel - off) % TEST_SPACING
        x = x[phase < TEST_SECONDS]
        x["bucket"] = ((x.t_rel - off) // TEST_SPACING).astype(int)
        g = x.groupby(["device_key", "bucket"])
        agg = g.agg(ts=("ts", "min"), lat=("lat", "mean"), lon=("lon", "mean"), n=("label", "size"),
                    dl_mbps=("dl_kbps", "mean"), ul_mbps=("ul_kbps", "mean"), mobility=("mobility", "first"),
                    operator=("operator", "first"),
                    label=("label", lambda s: int(s.value_counts().idxmax()))).reset_index()
        agg = agg[agg.n >= 3]
        agg["dl_mbps"] /= 1000.0
        agg["ul_mbps"] /= 1000.0
        agg["trace"] = agg.device_key
        agg["device_key"] = agg.device_key + f"#{off}"
        tests.append(agg)
    return pd.concat(tests, ignore_index=True).sort_values(["device_key", "ts"]).reset_index(drop=True)


def split_traces(tests: pd.DataFrame, seed: int, quick: bool) -> dict[str, list[str]]:
    rng = np.random.default_rng(seed)
    split = {"train": [], "val": [], "test": []}
    for _, keys in tests.groupby("mobility").trace.unique().items():
        keys = sorted(keys)
        rng.shuffle(keys)
        if quick:
            keys = keys[: max(3, len(keys) // 5)]
        n = len(keys)
        n_test, n_val = max(1, round(0.15 * n)), max(1, round(0.15 * n))
        split["test"] += keys[:n_test]
        split["val"] += keys[n_test:n_test + n_val]
        split["train"] += keys[n_test + n_val:]
    return split


def scores(y, pred) -> dict:
    p, r, f, s = precision_recall_fscore_support(y, pred, labels=[0, 1, 2], zero_division=0)
    return {"n": int(len(y)), "accuracy": float(accuracy_score(y, pred)),
            "macro_f1": float(f1_score(y, pred, labels=[0, 1, 2], average="macro", zero_division=0)),
            "per_class": {CLASSES[i]: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]), "support": int(s[i])} for i in range(3)},
            "confusion": confusion_matrix(y, pred, labels=[0, 1, 2]).tolist()}


def zone_scores(frame: pd.DataFrame, proba: np.ndarray, min_tests: int = 3) -> dict:
    """Aggregate to H3 resolution-9 zones (what complaints use): majority true class vs mean predicted probabilities."""
    z = frame[["lat", "lon", "label"]].copy()
    z[["p0", "p1", "p2"]] = proba
    z["cell"] = [h3.latlng_to_cell(a, b, 9) for a, b in zip(z.lat, z.lon)]
    g = z.groupby("cell").agg(n=("label", "size"), true=("label", lambda s: int(s.value_counts().idxmax())),
                              bad_share=("label", lambda s: float((s > 0).mean())), p0=("p0", "mean"), p1=("p1", "mean"), p2=("p2", "mean"))
    g = g[g.n >= min_tests]
    if g.empty:
        return {"zones": 0}
    pred = g[["p0", "p1", "p2"]].to_numpy().argmax(axis=1)
    bad_true, bad_pred = g.bad_share >= 0.7, (g.p1 + g.p2) >= 0.6
    return {"zones": int(len(g)), "min_tests_per_zone": min_tests, **{k: v for k, v in scores(g.true.to_numpy(), pred).items() if k != "per_class"},
            "bad_zone_detection": {"definition": ">= 70% of tests Weak/Dead", "prevalence": float(bad_true.mean()),
                                   "accuracy": float(accuracy_score(bad_true, bad_pred)), "f1": float(f1_score(bad_true, bad_pred, zero_division=0))}}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-copy", action="store_true", help="do not copy the result to models/")
    ap.add_argument("--out-root", default=None)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    seed_everything(args.seed)
    P.style()
    run_dir, log = new_run("radio_estimate_quick" if args.quick else "radio_estimate", Path(args.out_root) if args.out_root else EXPERIMENTS)
    t0 = time.time()

    df = pd.read_csv(PROCESSED / "lte_speed_clean.csv.gz", parse_dates=["ts"])
    tests = simulate_speed_tests(df)
    tests = tests.join(speed_features(tests).drop(columns=["dl_mbps", "ul_mbps"]))
    log.info("simulated speed tests: %d from %d traces", len(tests), tests.trace.nunique())
    split = split_traces(tests, args.seed, args.quick)
    parts = {k: tests[tests.trace.isin(v)] for k, v in split.items()}
    X = {k: v[SPEED_FEATURES].to_numpy() for k, v in parts.items()}
    y = {k: v.label.to_numpy() for k, v in parts.items()}
    log.info("tests  train %d | val %d | test %d", *(len(y[k]) for k in ("train", "val", "test")))

    xgb = XGBClassifier(n_estimators=150 if args.quick else 600, max_depth=5, learning_rate=0.05, subsample=0.8,
                        colsample_bytree=0.9, min_child_weight=5, tree_method="hist", objective="multi:softprob",
                        eval_metric="mlogloss", early_stopping_rounds=40, n_jobs=-1, random_state=args.seed)
    xgb.fit(X["train"], y["train"], sample_weight=compute_sample_weight("balanced", y["train"]),
            eval_set=[(X["val"], y["val"])], verbose=False)
    temperature = fit_temperature(xgb.predict_proba(X["val"]), y["val"])
    ece_v0, _ = expected_calibration_error(xgb.predict_proba(X["val"]), y["val"])
    ece_v1, _ = expected_calibration_error(CalibratedModel(xgb, temperature).predict_proba(X["val"]), y["val"])
    if ece_v1 >= ece_v0:
        temperature = 1.0
    model = CalibratedModel(xgb, temperature)
    log.info("best iteration %s, temperature %.3f", xgb.best_iteration, temperature)

    proba = model.predict_proba(X["test"])
    pred = proba.argmax(axis=1)
    test = scores(y["test"], pred)
    majority = int(np.bincount(y["train"]).argmax())
    baseline_majority = scores(y["test"], np.full(len(y["test"]), majority))
    # Baseline: two cut-offs on the single download speed, tuned on training tests.
    dl_tr = parts["train"].dl_mbps.to_numpy()
    grid = np.unique(np.percentile(dl_tr, np.arange(2, 99, 2)))
    best, best_f1 = (grid[-1], grid[0]), -1
    for hi in grid:
        for lo in grid[grid < hi]:
            f1 = f1_score(y["train"], np.where(dl_tr >= hi, 0, np.where(dl_tr >= lo, 1, 2)), average="macro")
            if f1 > best_f1:
                best, best_f1 = (float(hi), float(lo)), f1
    dl_te = parts["test"].dl_mbps.to_numpy()
    baseline_threshold = scores(y["test"], np.where(dl_te >= best[0], 0, np.where(dl_te >= best[1], 1, 2)))
    zones = zone_scores(parts["test"], proba)
    ece, reliability = expected_calibration_error(proba, y["test"])
    log.info("test per test: accuracy %.4f macro-F1 %.4f | majority %.4f | tuned speed threshold %.4f",
             test["accuracy"], test["macro_f1"], baseline_majority["macro_f1"], baseline_threshold["macro_f1"])
    log.info("test per zone (%s zones): accuracy %.4f macro-F1 %.4f | bad-zone F1 %.4f",
             zones.get("zones"), zones.get("accuracy", float("nan")), zones.get("macro_f1", float("nan")),
             zones.get("bad_zone_detection", {}).get("f1", float("nan")))

    fig, axes = P.plt.subplots(1, 2, figsize=(9.6, 4.4))
    P.confusion_panel(axes[0], test["confusion"], CLASSES, f"Per speed test (macro-F1 {test['macro_f1']:.3f})")
    if zones.get("zones"):
        P.confusion_panel(axes[1], zones["confusion"], CLASSES, f"Per zone (macro-F1 {zones['macro_f1']:.3f})")
    fig.suptitle("Radio-condition estimate from speed tests - test traces", fontsize=12, fontweight="bold", color=P.TEXT)
    fig.tight_layout()
    P.save(fig, run_dir / "confusion_matrix.png")

    fig, ax = P.plt.subplots(figsize=(7.2, 4.2))
    P.grouped_bars(ax, ["Accuracy", "Macro-F1"],
                   {"Speed-test model": [test["accuracy"], test["macro_f1"]],
                    "Tuned speed threshold": [baseline_threshold["accuracy"], baseline_threshold["macro_f1"]],
                    "Always majority class": [baseline_majority["accuracy"], baseline_majority["macro_f1"]]},
                   [P.SERIES[0]] + P.BASELINE_GREYS, "Score (test)", ylim=(0, 1.0))
    ax.set_title("Speed-test model vs baselines")
    P.save(fig, run_dir / "baselines.png")

    fig, ax = P.plt.subplots(figsize=(5.2, 5))
    ax.plot([0, 1], [0, 1], color=P.BASELINE_GREYS[1], linestyle="--", linewidth=1.2, label="Perfect calibration")
    ax.plot([b["confidence"] for b in reliability], [b["accuracy"] for b in reliability], marker="o", markersize=5,
            color=P.SERIES[0], label=f"Model (ECE {ece:.3f})")
    ax.set_xlabel("Predicted confidence")
    ax.set_ylabel("Observed accuracy")
    ax.set_title("Confidence calibration (test)")
    ax.legend(loc="upper left")
    P.save(fig, run_dir / "calibration.png")

    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    joblib.dump({"name": "XGBoost (speed tests)", "model": model, "features": SPEED_FEATURES, "classes": CLASSES,
                 "version": run_dir.name, "trained_at": created, "temperature": temperature}, run_dir / "model.joblib", compress=3)
    metrics = {
        "run": run_dir.name, "created_at": created, "quick": args.quick, "seed": args.seed,
        "task": "Estimate the radio class (3GPP-style ranges) from phone speed tests",
        "dataset": {"name": "4G LTE Speed Dataset (Cork)", "speed_test_simulation": {"test_seconds": TEST_SECONDS, "spacing_s": TEST_SPACING, "offsets_s": OFFSETS},
                    "split_method": "by trace file, 70/15/15 stratified by mobility",
                    "splits": {k: {"traces": len(v), "tests": int(len(y[k])), "class_counts": {CLASSES[c]: int((y[k] == c).sum()) for c in range(3)}} for k, v in split.items()},
                    "trace_files": split},
        "features": SPEED_FEATURES, "temperature": temperature,
        "test_per_speed_test": test, "test_per_zone": zones,
        "baselines": {"always_majority": baseline_majority, "tuned_speed_threshold": {"cutoffs_mbps": best, **baseline_threshold}},
        "calibration": {"ece": ece, "reliability": reliability},
        "interpretation": "Speed depends on cell load as well as radio conditions, so this is a partial proxy. The product shows it as an estimate next to the measured service-quality class and never lets it override that class.",
        "timings_s": {"total": round(time.time() - t0, 1)},
    }
    write_json(run_dir / "metrics.json", metrics)
    if not args.quick and not args.no_copy:
        MODELS.mkdir(exist_ok=True)
        shutil.copy2(run_dir / "model.joblib", MODELS / "radio_estimate.joblib")
        write_json(MODELS / "radio_estimate.json", {"version": run_dir.name, "created_at": created, "experiment": f"experiments/{run_dir.name}",
                                                    "test_per_speed_test": {"accuracy": test["accuracy"], "macro_f1": test["macro_f1"]},
                                                    "test_per_zone": {k: zones.get(k) for k in ("zones", "accuracy", "macro_f1")}, "ece": ece})
        log.info("copied to models/radio_estimate.joblib")
    log.info("done in %.1f s", time.time() - t0)


if __name__ == "__main__":
    main()
