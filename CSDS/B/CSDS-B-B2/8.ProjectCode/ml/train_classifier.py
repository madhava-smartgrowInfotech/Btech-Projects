"""Train the radio zone classifier (Strong / Weak / Dead) and save every artefact.

    python ml/train_classifier.py            # full run -> experiments/classifier_<stamp>/ + models/zone_classifier.*
    python ml/train_classifier.py --quick    # fast smoke run on a few traces (does not touch models/)

Candidates: Random Forest, XGBoost and a PyTorch MLP, compared against two baselines (the documented
ranges applied to whatever the device reports, and two cut-offs on one metric tuned on training data).
Training data is expanded to four device profiles so the model copes with devices that do not report
every metric.

Evaluation (all splits by trace file - a trace never appears on both sides):
  1. 15% of traces are held out as the final test set.
  2. 5-fold cross-validation on the rest compares every candidate and baseline (mean +/- std), and the
     candidate with the best mean macro-F1 across profiles is chosen. Cross-validation is used because a
     single 20-trace validation split proved too noisy to rank methods on the sparse profiles.
  3. The chosen model is refit, calibrated on a validation split and scored once on the test traces.
"""
from __future__ import annotations

import argparse
import platform
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

import _plots as P
from _common import EXPERIMENTS, MODELS, PROCESSED, SEED, new_run, seed_everything, write_json
from app.ml.calibration import CalibratedModel, expected_calibration_error, fit_temperature
from app.ml.features import FEATURES, PROFILES, apply_profile, build_features
from app.ml.mlp import TorchMLPClassifier
from app.ml.signal_ranges import CLASSES, RANGES, STRONG, label_arrays

PROFILE_LABELS = {"full": "All metrics", "no_sinr_cqi": "No SINR/CQI", "level_only": "Level only", "rssi_only": "RSSI only"}
CANDIDATES = ["Random Forest", "XGBoost", "PyTorch MLP"]
BASELINES = ["Ranges on reported metrics", "Tuned single threshold"]


# ---------------------------------------------------------------- data
def split_traces(df: pd.DataFrame, seed: int, quick: bool) -> dict[str, list[str]]:
    """70/15/15 split of trace files, stratified by mobility (static, pedestrian, car, bus, train)."""
    rng = np.random.default_rng(seed)
    split = {"train": [], "val": [], "test": []}
    for _, keys in df.groupby("mobility").device_key.unique().items():
        keys = sorted(keys)
        rng.shuffle(keys)
        if quick:
            keys = keys[: max(3, len(keys) // 5)]
        n = len(keys)
        n_test = max(1, round(0.15 * n))
        n_val = max(1, round(0.15 * n))
        split["test"] += keys[:n_test]
        split["val"] += keys[n_test:n_test + n_val]
        split["train"] += keys[n_test + n_val:]
    return split


def augmented(df: pd.DataFrame, keys: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    base = df[df.device_key.isin(keys)]
    parts = []
    for profile in PROFILES:
        sub = apply_profile(base, profile)
        parts.append(sub.assign(trace=sub.device_key, device_key=sub.device_key + "|" + profile, profile=profile))
    frame = pd.concat(parts, ignore_index=True)
    return frame, build_features(frame), frame.label.to_numpy()


# ---------------------------------------------------------------- metrics
def fast_macro_f1(y: np.ndarray, p: np.ndarray) -> float:
    cm = np.bincount(y * 3 + p, minlength=9).reshape(3, 3).astype(float)
    tp = np.diag(cm)
    prec = np.divide(tp, cm.sum(0), out=np.zeros(3), where=cm.sum(0) > 0)
    rec = np.divide(tp, cm.sum(1), out=np.zeros(3), where=cm.sum(1) > 0)
    f1 = np.divide(2 * prec * rec, prec + rec, out=np.zeros(3), where=(prec + rec) > 0)
    return float(f1.mean())


def scores(y: np.ndarray, pred: np.ndarray) -> dict:
    p, r, f, s = precision_recall_fscore_support(y, pred, labels=[0, 1, 2], zero_division=0)
    return {
        "n": int(len(y)),
        "accuracy": float(accuracy_score(y, pred)),
        "macro_f1": float(f1_score(y, pred, labels=[0, 1, 2], average="macro", zero_division=0)),
        "per_class": {CLASSES[i]: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]), "support": int(s[i])} for i in range(3)},
        "confusion": confusion_matrix(y, pred, labels=[0, 1, 2]).tolist(),
    }


def by_profile(frame: pd.DataFrame, y: np.ndarray, pred: np.ndarray) -> dict:
    out = {prof: scores(y[(frame.profile == prof).to_numpy()], pred[(frame.profile == prof).to_numpy()]) for prof in PROFILES}
    out["mean_macro_f1"] = float(np.mean([out[p]["macro_f1"] for p in PROFILES]))
    return out


# ---------------------------------------------------------------- baselines
def rule_on_reported(frame: pd.DataFrame) -> np.ndarray:
    """The documented ranges applied to the metrics this device reports (Strong when nothing to judge)."""
    pred = label_arrays(frame.family.to_numpy(), frame.level.to_numpy(), frame.quality.to_numpy(), frame.sinr.to_numpy())
    return np.where(pred < 0, STRONG, pred)


class TunedThreshold:
    """Two cut-offs on one metric (level, or RSSI for rssi-only devices), tuned per family for macro-F1."""

    def fit(self, frame: pd.DataFrame, y: np.ndarray):
        self.cuts: dict[tuple[str, str], tuple[float, float]] = {}
        for metric in ("level", "rssi"):
            for fam in frame.family.unique():
                mask = (frame.family == fam).to_numpy() & frame[metric].notna().to_numpy()
                if mask.sum() < 200:
                    continue
                v, t = frame[metric].to_numpy()[mask], y[mask]
                grid = np.unique(np.percentile(v, np.arange(4, 97, 4)))
                best, best_f1 = (float(grid[-1]), float(grid[0])), -1.0
                for hi in grid:
                    for lo in grid[grid < hi]:
                        f1 = fast_macro_f1(t, np.where(v >= hi, 0, np.where(v >= lo, 1, 2)))
                        if f1 > best_f1:
                            best, best_f1 = (float(hi), float(lo)), f1
                self.cuts[(metric, fam)] = best
        return self

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        out = np.full(len(frame), STRONG)
        fam = frame.family.to_numpy()
        for metric in ("rssi", "level"):   # level wins when both are reported
            v = frame[metric].to_numpy()
            for f in np.unique(fam):
                cut = self.cuts.get((metric, f))
                if cut is None:
                    wb, db = RANGES.get(f, {}).get(metric, (None, None)) if metric == "level" else (None, None)
                    if wb is None:
                        continue
                    cut = (wb, db)
                mask = (fam == f) & ~np.isnan(v)
                out[mask] = np.where(v[mask] >= cut[0], 0, np.where(v[mask] >= cut[1], 1, 2))
        return out


# ---------------------------------------------------------------- candidates
def make_model(name: str, seed: int, quick: bool, early_stopping: bool):
    if name == "Random Forest":
        return RandomForestClassifier(n_estimators=60 if quick else 200, min_samples_leaf=5, max_features="sqrt",
                                      max_samples=0.5, class_weight="balanced_subsample", n_jobs=-1, random_state=seed)
    if name == "XGBoost":
        return XGBClassifier(n_estimators=(200 if quick else 800) if early_stopping else (120 if quick else 300),
                             max_depth=7, learning_rate=0.08, subsample=0.8, colsample_bytree=0.8, min_child_weight=2,
                             tree_method="hist", objective="multi:softprob", eval_metric="mlogloss",
                             early_stopping_rounds=40 if early_stopping else None, n_jobs=-1, random_state=seed)
    return TorchMLPClassifier(epochs=(5 if quick else 30) if early_stopping else (4 if quick else 12), seed=seed)


def fit_model(name: str, model, X, y, X_val=None, y_val=None, log=None):
    if name == "Random Forest":
        model.fit(X, y)
    elif name == "XGBoost":
        kwargs = {"eval_set": [(X_val, y_val)], "verbose": False} if X_val is not None else {"verbose": False}
        model.fit(X, y, sample_weight=compute_sample_weight("balanced", y), **kwargs)
    else:
        model.fit(X, y, X_val, y_val, log=log or (lambda *_: None))
    return model


def cross_validate(dev_f: pd.DataFrame, Xdev: np.ndarray, ydev: np.ndarray, traces: pd.DataFrame, seed: int, quick: bool, log) -> dict:
    n_folds = 3 if quick else 5
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    row_trace = dev_f.trace.to_numpy()
    results = {name: {p: [] for p in PROFILES} for name in CANDIDATES + BASELINES}
    for fold, (tr_idx, va_idx) in enumerate(skf.split(traces.trace, traces.mobility), start=1):
        tr_mask = np.isin(row_trace, traces.trace.to_numpy()[tr_idx])
        va_mask = ~tr_mask
        f_va, y_va = dev_f[va_mask], ydev[va_mask]
        prof_va = f_va.profile.to_numpy()
        preds = {}
        for name in CANDIDATES:
            m = fit_model(name, make_model(name, seed, quick, early_stopping=False), Xdev[tr_mask], ydev[tr_mask])
            preds[name] = m.predict_proba(Xdev[va_mask]).argmax(axis=1)
        preds["Ranges on reported metrics"] = rule_on_reported(f_va)
        preds["Tuned single threshold"] = TunedThreshold().fit(dev_f[tr_mask], ydev[tr_mask]).predict(f_va)
        for name, pred in preds.items():
            for p in PROFILES:
                results[name][p].append(fast_macro_f1(y_va[prof_va == p], pred[prof_va == p]))
        log("  fold %d/%d  %s" % (fold, n_folds, " | ".join(
            f"{n.split()[0]} {np.mean([results[n][p][-1] for p in PROFILES]):.3f}" for n in CANDIDATES + BASELINES)))
    summary = {}
    for name, per in results.items():
        summary[name] = {p: {"mean": float(np.mean(v)), "std": float(np.std(v)), "folds": v} for p, v in per.items()}
        fold_means = np.mean([per[p] for p in PROFILES], axis=0)
        summary[name]["mean_macro_f1"] = {"mean": float(fold_means.mean()), "std": float(fold_means.std())}
    return {"folds": n_folds, "results": summary}


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="small smoke run; does not update models/")
    ap.add_argument("--out-root", default=None, help="folder for the run (default experiments/)")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--no-copy", action="store_true", help="do not copy the result to models/")
    args = ap.parse_args()

    seed_everything(args.seed)
    P.style()
    run_dir, log = new_run("classifier_quick" if args.quick else "classifier", Path(args.out_root) if args.out_root else EXPERIMENTS)
    t0 = time.time()
    log.info(f"run folder: {run_dir}")

    df = pd.read_csv(PROCESSED / "lte_speed_clean.csv.gz", parse_dates=["ts"])
    split = split_traces(df, args.seed, args.quick)
    log.info("traces  train %d | val %d | test %d", *(len(split[k]) for k in ("train", "val", "test")))

    # ------------------------------------------------ cross-validation on the development traces
    dev_keys = split["train"] + split["val"]
    dev_f, Xdev_df, ydev = augmented(df, dev_keys)
    Xdev = Xdev_df.to_numpy()
    traces = df[df.device_key.isin(dev_keys)].groupby("device_key").mobility.first().reset_index().rename(columns={"device_key": "trace"})
    log.info("cross-validation on %d development traces (%d rows over 4 device profiles) ...", len(traces), len(ydev))
    t = time.time()
    cv = cross_validate(dev_f, Xdev, ydev, traces, args.seed, args.quick, log.info)
    cv_time = time.time() - t
    for name in CANDIDATES + BASELINES:
        r = cv["results"][name]
        log.info("cv   %-28s mean macro-F1 %.4f +/- %.4f | %s", name, r["mean_macro_f1"]["mean"], r["mean_macro_f1"]["std"],
                 ", ".join(f"{p} {r[p]['mean']:.3f}+/-{r[p]['std']:.3f}" for p in PROFILES))
    chosen = max(CANDIDATES, key=lambda k: cv["results"][k]["mean_macro_f1"]["mean"])
    log.info("chosen model (best cross-validated mean macro-F1): %s", chosen)

    # ------------------------------------------------ final models on train, early stopping + calibration on val
    tr_mask = dev_f.trace.isin(split["train"]).to_numpy()
    Xtr, ytr, tr_f = Xdev[tr_mask], ydev[tr_mask], dev_f[tr_mask]
    Xva, yva = Xdev[~tr_mask], ydev[~tr_mask]
    te_f, Xte_df, yte = augmented(df, split["test"])
    Xte = Xte_df.to_numpy()
    log.info("final fit  train %d rows | val %d | test %d", len(ytr), len(yva), len(yte))

    candidates, timings = {}, {}
    for name in CANDIDATES:
        t = time.time()
        log.info("training %s ...", name)
        candidates[name] = fit_model(name, make_model(name, args.seed, args.quick, early_stopping=True), Xtr, ytr, Xva, yva, log.info)
        timings[name] = time.time() - t
    mlp = candidates["PyTorch MLP"]

    raw_val = candidates[chosen].predict_proba(Xva)
    temperature = fit_temperature(raw_val, yva)
    ece_val_before, _ = expected_calibration_error(raw_val, yva)
    ece_val_after, _ = expected_calibration_error(CalibratedModel(candidates[chosen], temperature).predict_proba(Xva), yva)
    if ece_val_after >= ece_val_before:   # keep the scaling only if it really improves calibration
        temperature = 1.0
    model = CalibratedModel(candidates[chosen], temperature)
    log.info("temperature %.3f (validation ECE %.4f -> %.4f)", temperature, ece_val_before, min(ece_val_after, ece_val_before))

    # ------------------------------------------------ test evaluation (once)
    test = {name: by_profile(te_f, yte, m.predict_proba(Xte).argmax(axis=1)) for name, m in candidates.items()}
    test["Ranges on reported metrics"] = by_profile(te_f, yte, rule_on_reported(te_f))
    test["Tuned single threshold"] = by_profile(te_f, yte, TunedThreshold().fit(tr_f, ytr).predict(te_f))
    proba_te_raw = candidates[chosen].predict_proba(Xte)
    proba_te = model.predict_proba(Xte)
    ece_before, rel_before = expected_calibration_error(proba_te_raw, yte)
    ece_after, reliability = expected_calibration_error(proba_te, yte)
    overall = scores(yte, proba_te.argmax(axis=1))
    for name, res in test.items():
        log.info("test %-28s mean macro-F1 %.4f | %s", name, res["mean_macro_f1"], ", ".join(f"{p} {res[p]['macro_f1']:.3f}" for p in PROFILES))
    log.info("test chosen overall accuracy %.4f macro-F1 %.4f | ECE %.4f -> %.4f", overall["accuracy"], overall["macro_f1"], ece_before, ece_after)

    # ------------------------------------------------ consistency check: Patna, signal level only
    patna = pd.read_csv(PROCESSED / "cellular_analysis_clean.csv.gz", parse_dates=["ts"])
    ext = patna.assign(device_key=np.arange(len(patna)).astype(str), quality=np.nan, sinr=np.nan, rssi=np.nan, cqi=np.nan)
    ext_pred = model.predict_proba(build_features(ext).to_numpy()).argmax(axis=1)
    external = scores(patna.label.to_numpy(), ext_pred)
    external["by_network_type"] = {nt: float(accuracy_score(g.label, ext_pred[g.index])) for nt, g in patna.groupby("network_type")}
    external["note"] = ("Consistency check on independent measurements from another region (Patna; 3G/4G/5G/LTE strings) "
                        "with only a signal level per reading. Its labels are the documented ranges on that single level, "
                        "so this confirms the model behaves consistently on level-only input and unseen network-type "
                        "strings; it is not a measure of accuracy against full radio conditions.")
    log.info("consistency (Patna, level only) accuracy %.4f macro-F1 %.4f", external["accuracy"], external["macro_f1"])

    # ------------------------------------------------ feature importance (permutation, model-agnostic)
    rng = np.random.default_rng(args.seed)
    sample = rng.choice(len(yte), size=min(20000, len(yte)), replace=False)
    Xs, ys = Xte[sample], yte[sample]
    base_f1 = fast_macro_f1(ys, model.predict(Xs))
    drops = []
    for j in range(Xs.shape[1]):
        vals = []
        for _ in range(3):
            Xp = Xs.copy()
            Xp[:, j] = rng.permutation(Xp[:, j])
            vals.append(base_f1 - fast_macro_f1(ys, model.predict(Xp)))
        drops.append(float(np.mean(vals)))
    importance = sorted(zip(FEATURES, drops), key=lambda kv: -kv[1])

    # ------------------------------------------------ plots
    names = CANDIDATES + BASELINES
    colors = P.SERIES[:len(CANDIDATES)] + P.BASELINE_GREYS

    fig, ax = P.plt.subplots(figsize=(10, 4.8))
    P.grouped_bars(ax, [PROFILE_LABELS[p] for p in PROFILES],
                   {n: [cv["results"][n][p]["mean"] for p in PROFILES] for n in names}, colors,
                   f"Macro-F1 ({cv['folds']}-fold cross-validation)", ylim=(0, 1.1),
                   errors={n: [cv["results"][n][p]["std"] for p in PROFILES] for n in names})
    ax.set_title("Cross-validated macro-F1 by device profile (mean +/- std over folds)")
    P.save(fig, run_dir / "cv_profile_scores.png")

    fig, ax = P.plt.subplots(figsize=(10, 4.8))
    P.grouped_bars(ax, [PROFILE_LABELS[p] for p in PROFILES], {n: [test[n][p]["macro_f1"] for p in PROFILES] for n in names},
                   colors, "Macro-F1 (held-out test traces)", ylim=(0, 1.1))
    ax.set_title("Held-out test macro-F1 by device profile")
    P.save(fig, run_dir / "profile_scores.png")

    fig, axes = P.plt.subplots(2, 2, figsize=(9, 8.4))
    for ax, prof in zip(axes.ravel(), PROFILES):
        P.confusion_panel(ax, test[chosen][prof]["confusion"], CLASSES, f"{PROFILE_LABELS[prof]}  (macro-F1 {test[chosen][prof]['macro_f1']:.3f})")
    fig.suptitle(f"{chosen} - test traces, by device profile", fontsize=12, fontweight="bold", color=P.TEXT)
    fig.tight_layout()
    P.save(fig, run_dir / "confusion_matrix.png")

    fig, ax = P.plt.subplots(figsize=(5.2, 5))
    ax.plot([0, 1], [0, 1], color=P.BASELINE_GREYS[1], linestyle="--", linewidth=1.2, label="Perfect calibration")
    ax.plot([b["confidence"] for b in rel_before], [b["accuracy"] for b in rel_before], marker="o", markersize=5,
            color=P.SERIES[1], label=f"Before (ECE {ece_before:.3f})")
    ax.plot([b["confidence"] for b in reliability], [b["accuracy"] for b in reliability], marker="o", markersize=5,
            color=P.SERIES[0], label=f"After temperature {temperature:.2f} (ECE {ece_after:.3f})")
    ax.set_xlabel("Predicted confidence")
    ax.set_ylabel("Observed accuracy")
    ax.set_xlim(0.3, 1.0)
    ax.set_ylim(0.3, 1.0)
    ax.set_title("Confidence calibration (test)")
    ax.legend(loc="upper left")
    P.save(fig, run_dir / "calibration.png")

    top = importance[:15][::-1]
    fig, ax = P.plt.subplots(figsize=(7, 5.2))
    ax.barh([k for k, _ in top], [v for _, v in top], color=P.SERIES[0], height=0.6)
    ax.set_xlabel("Drop in macro-F1 when the feature is shuffled")
    ax.set_title(f"Feature importance - {chosen}")
    ax.grid(axis="y", visible=False)
    P.save(fig, run_dir / "feature_importance.png")

    # Loss and validation F1 have different scales, so they get two panels rather than a second y-axis.
    hist = mlp.history_
    if hist:
        fig, (ax1, ax2) = P.plt.subplots(1, 2, figsize=(10, 3.8))
        ax1.plot([h["epoch"] for h in hist], [h["train_loss"] for h in hist], color=P.SERIES[0])
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("Weighted cross-entropy")
        ax1.set_title("PyTorch MLP - training loss")
        if any("val_macro_f1" in h for h in hist):
            ax2.plot([h["epoch"] for h in hist], [h["val_macro_f1"] for h in hist], color=P.SERIES[0])
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel("Macro-F1")
        ax2.set_title("PyTorch MLP - validation macro-F1")
        P.save(fig, run_dir / "mlp_training.png")

    # ------------------------------------------------ save
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    bundle = {"name": chosen, "model": model, "features": FEATURES, "classes": CLASSES, "version": run_dir.name,
              "trained_at": created, "temperature": temperature, "profiles": list(PROFILES)}
    joblib.dump(bundle, run_dir / "model.joblib", compress=3)

    def split_stats(frame, y):
        return {"traces": int(frame.trace.nunique()), "rows": int(len(y)), "class_counts": {CLASSES[k]: int((y == k).sum()) for k in range(3)}}

    metrics = {
        "run": run_dir.name, "created_at": created, "quick": args.quick, "seed": args.seed,
        "task": "Classify each radio reading as Strong / Weak / Dead",
        "dataset": {"name": "4G LTE Speed Dataset (Cork)", "file": "data/processed/lte_speed_clean.csv.gz",
                    "date_range": [str(df.ts.min()), str(df.ts.max())],
                    "split_method": "by trace file, stratified by mobility: 15% test held out; 5-fold cross-validation on the rest; "
                                    "final fit on 70% train with 15% validation for early stopping and calibration",
                    "splits": {"train": split_stats(tr_f, ytr), "val": split_stats(dev_f[~tr_mask], yva), "test": split_stats(te_f, yte)},
                    "trace_files": split},
        "labels": {"method": "documented 3GPP-style ranges, worst metric wins", "ranges": RANGES},
        "features": FEATURES, "profiles": PROFILES,
        "cross_validation": cv, "chosen": chosen, "chosen_by": "best cross-validated mean macro-F1 across device profiles",
        "temperature": temperature, "test": test, "test_overall_chosen": overall,
        "calibration": {"ece_before": ece_before, "ece_after": ece_after, "reliability": reliability},
        "consistency_check_patna": external,
        "feature_importance": [{"feature": k, "macro_f1_drop": float(v)} for k, v in importance],
        "mlp_history": mlp.history_,
        "timings_s": {"cross_validation": round(cv_time, 1), **{k: round(v, 1) for k, v in timings.items()}, "total": round(time.time() - t0, 1)},
        "environment": {"python": platform.python_version(), "sklearn": sklearn.__version__, "xgboost": xgboost.__version__},
    }
    write_json(run_dir / "metrics.json", metrics)

    if not args.quick and not args.no_copy:
        MODELS.mkdir(exist_ok=True)
        shutil.copy2(run_dir / "model.joblib", MODELS / "zone_classifier.joblib")
        write_json(MODELS / "zone_classifier.json", {
            "version": run_dir.name, "created_at": created, "model": chosen, "experiment": f"experiments/{run_dir.name}",
            "cv_macro_f1_by_profile": {p: cv["results"][chosen][p] for p in PROFILES},
            "test_macro_f1_by_profile": {p: test[chosen][p]["macro_f1"] for p in PROFILES},
            "test_accuracy_by_profile": {p: test[chosen][p]["accuracy"] for p in PROFILES},
            "test_overall": {"accuracy": overall["accuracy"], "macro_f1": overall["macro_f1"]},
            "ece_after_calibration": ece_after,
        })
        log.info("copied to models/zone_classifier.joblib")
    log.info("done in %.1f s", time.time() - t0)


if __name__ == "__main__":
    main()
