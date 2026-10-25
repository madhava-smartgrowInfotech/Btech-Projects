"""
Measured results for the documentation set. Writes experiments/metrics.json.

Run from 8.ProjectCode:  python scripts/run_experiments.py
Reads the product code (backend/) but never modifies models/ or data/.
Sections:
  saved_models   - the three shipped GRBMC models + ensemble on the held-out 20% split (1,600 rows)
  serving        - what the Flask serving path does to a fresh batch (scaler is skipped) vs correct scaling
  baselines      - LR / RF / XGBoost on the same balanced split
  imbalance      - 1% fraud variant: no resampling / class weights / SMOTE / undersampling, 5 seeds
  seeds          - GRBMC retrained with 5 seeds (20 epochs, 8,000-row subset, same as seed_models.py)
  full39k        - GRBMC trained on the whole 39,000-row file
"""
import gc
import json
import os
import pathlib
import sys
import time
import warnings

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
                             average_precision_score, confusion_matrix, roc_curve)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
import synthetic_data
import train as train_mod
from preprocessing import full_pipeline, NUMERICAL_COLS, CATEGORICAL_COLS
from rbm_classifier import GRBMC

OUT = ROOT / "experiments"
OUT.mkdir(exist_ok=True)
MODEL_DIR = ROOT / "models"
MODES = ["classical", "sa", "qa"]


def retry(fn, *a, **kw):
    """The shared box is short on commit memory at times (sibling jobs); retry allocation failures."""
    for attempt in range(8):
        try:
            return fn(*a, **kw)
        except (MemoryError, Exception) as e:  # noqa: BLE001
            if "alloc" not in str(e).lower() and not isinstance(e, MemoryError):
                raise
            print("memory pressure, retry", attempt + 1, flush=True)
            gc.collect()
            time.sleep(20)
    return fn(*a, **kw)


def metrics(y, pred, proba=None):
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    m = {"accuracy": accuracy_score(y, pred), "precision": precision_score(y, pred, zero_division=0),
         "recall": recall_score(y, pred, zero_division=0), "f1": f1_score(y, pred, zero_division=0),
         "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
    if proba is not None and len(set(y)) > 1:
        m["roc_auc"] = roc_auc_score(y, proba)
        m["pr_auc"] = average_precision_score(y, proba)
    return {k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in m.items()}


def mean_std(rows, keys):
    return {k: {"mean": float(np.mean([r[k] for r in rows])), "std": float(np.std([r[k] for r in rows]))} for k in keys}


def fresh_dataset(n_fraud, n_legit, seed):
    synthetic_data.RNG = np.random.default_rng(seed)
    return synthetic_data.generate_synthetic_transactions(n_fraud=n_fraud, n_legit=n_legit)


def serve_transform(df_raw, res, scale):
    """Feature vector for a raw frame. scale=False reproduces app.predict_batch (scaler step raises and is swallowed)."""
    df_enc = pd.get_dummies(df_raw.drop(columns=["Class"], errors="ignore"), columns=CATEGORICAL_COLS, dtype=float)
    for c in res["scaler"].feature_names_in_:
        if c not in df_enc.columns:
            df_enc[c] = 0.0
    if scale:
        cols = list(res["scaler"].feature_names_in_)
        df_enc[cols] = res["scaler"].transform(df_enc[cols])
    for c in res["columns"]:
        if c not in df_enc.columns:
            df_enc[c] = 0.0
    return df_enc[res["columns"]].values.astype(float)


def ensemble_proba(models, X):
    return np.mean([m.predict_proba(X) for m in models.values()], axis=0)[:, 1]


def curve(y, p, n=60):
    fpr, tpr, _ = roc_curve(y, p)
    idx = np.unique(np.linspace(0, len(fpr) - 1, n).astype(int))
    return {"fpr": fpr[idx].tolist(), "tpr": tpr[idx].tolist()}


def main():
    part_file = OUT / "_partial.json"
    results = json.loads(part_file.read_text()) if part_file.exists() else {}
    results["python"] = sys.version.split()[0]

    def save():
        part_file.write_text(json.dumps(results))
    df = pd.read_csv(ROOT / "data" / "creditcard_synthetic.csv")
    results["dataset"] = {"rows": int(len(df)), "columns": int(df.shape[1]), "fraud": int(df.Class.sum()),
                          "legit": int((df.Class == 0).sum()),
                          "amount_mean_fraud": float(df[df.Class == 1].Amount.mean()),
                          "amount_mean_legit": float(df[df.Class == 0].Amount.mean())}

    # ---- the pipeline the backend rebuilds at start-up (8,000-row sample, 18 features, undersampled, 80/20) ----
    res = full_pipeline(df.sample(n=8000, random_state=42), method="manual", top_k=18)
    X_tr, X_te, y_tr, y_te = res["X_train"], res["X_test"], res["y_train"].values, res["y_test"].values
    results["split"] = {"train": list(X_tr.shape), "test": list(X_te.shape), "features": res["columns"],
                        "train_fraud": int(y_tr.sum()), "test_fraud": int(y_te.sum()),
                        "dropped_by_correlation": res["dropped_corr"]}

    # ---- saved models ----
    models = {m: joblib.load(MODEL_DIR / f"grbmc_{m}.pkl") for m in MODES}
    if "saved_models" not in results:
        sm = {}
        probas = {}
        for m, mdl in models.items():
            probas[m] = mdl.predict_proba(X_te.values)[:, 1]
            sm[m] = metrics(y_te, (probas[m] > 0.5).astype(int), probas[m])
            sm[m].update({"n_hidden": int(mdl.n_hidden), "batch_size": int(mdl.batch_size), "roc": curve(y_te, probas[m])})
        pe = np.mean([probas[m] for m in MODES], axis=0)
        sm["ensemble"] = metrics(y_te, (pe > 0.5).astype(int), pe)
        sm["ensemble"]["roc"] = curve(y_te, pe)
        sweep = []
        for t in np.arange(0.1, 0.91, 0.05):
            r = metrics(y_te, (pe > t).astype(int))
            sweep.append({"threshold": round(float(t), 2), **{k: r[k] for k in ["precision", "recall", "f1", "fp", "fn"]}})
        sm["ensemble_threshold_sweep"] = sweep
        sm["classical_threshold_sweep"] = [
            {"threshold": round(float(t), 2), **{k: v for k, v in metrics(y_te, (probas["classical"] > t).astype(int)).items()
                                                 if k in ["accuracy", "precision", "recall", "f1", "fp", "fn"]}}
            for t in np.arange(0.1, 0.91, 0.05)]
        sm["histories"] = {m: json.load(open(MODEL_DIR / f"history_{m}.json")) for m in MODES}
        results["saved_models"] = sm
        print("saved models done")
        save()

    # ---- serving path: fresh balanced batch, as served vs correctly scaled ----
    if "serving" not in results:
        fresh = fresh_dataset(1000, 1000, seed=2026)
        yf = fresh["Class"].values
        serv = {}
        for label, scale in [("as_served_no_scaling", False), ("with_scaling", True)]:
            Xf = serve_transform(fresh, res, scale)
            pf = {m: models[m].predict_proba(Xf)[:, 1] for m in MODES}
            pfe = np.mean([pf[m] for m in MODES], axis=0)
            serv[label] = {m: metrics(yf, (pf[m] > 0.5).astype(int), pf[m]) for m in MODES}
            serv[label]["ensemble"] = metrics(yf, (pfe > 0.5).astype(int), pfe)
        sample = pd.read_csv(ROOT / "data" / "sample_batch.csv")
        Xs = serve_transform(sample, res, False)
        serv["sample_batch_rows"] = int(len(sample))
        serv["sample_batch_as_served_flagged"] = int((ensemble_proba(models, Xs) > 0.5).sum())
        Xs2 = serve_transform(sample, res, True)
        serv["sample_batch_scaled_flagged"] = int((ensemble_proba(models, Xs2) > 0.5).sum())
        serv["sample_batch_true_fraud"] = int(sample["Class"].sum())
        serv["scaler_features"] = int(len(res["scaler"].feature_names_in_))
        serv["selected_numeric_features"] = int(sum(c in NUMERICAL_COLS for c in res["columns"]))
        serv["fresh_rows"] = int(len(fresh))
        results["serving"] = serv
        print("serving done")
        save()

    # ---- baselines on the same balanced split ----
    zoo = {"Logistic Regression": lambda: LogisticRegression(max_iter=2000, random_state=42),
           "Random Forest": lambda: RandomForestClassifier(n_estimators=100, min_samples_leaf=2, random_state=42, n_jobs=2),
           "XGBoost": lambda: XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1, eval_metric="logloss",
                                            random_state=42, n_jobs=2)}
    if "baselines_balanced" not in results:
        base = {}
        for name, mk in zoo.items():
            t0 = time.time()
            clf = retry(lambda: mk().fit(X_tr.values, y_tr))
            fit_s = time.time() - t0
            p = clf.predict_proba(X_te.values)[:, 1]
            base[name] = metrics(y_te, (p > 0.5).astype(int), p)
            base[name]["fit_seconds"] = fit_s
            base[name]["roc"] = curve(y_te, p)
            if name == "Random Forest":
                base[name]["top_importances"] = sorted(zip(res["columns"], clf.feature_importances_.tolist()),
                                                       key=lambda kv: -kv[1])[:10]
        results["baselines_balanced"] = base
        print("baselines done")
        save()

    # ---- 1% fraud variant ----
    if "imbalance" not in results:
        imb = {"fraud_rate": 0.01, "rows": 39000}
        raw = fresh_dataset(390, 38610, seed=7)
        raw_enc = pd.get_dummies(raw, columns=CATEGORICAL_COLS, dtype=float)
        feats = [c for c in raw_enc.columns if c != "Class"]
        num = [c for c in NUMERICAL_COLS if c in feats]
        rows = {}
        rule_rows = []
        for seed in range(5):
            Xtr, Xte, ytr, yte = train_test_split(raw_enc[feats], raw_enc["Class"].values, test_size=0.2,
                                                  stratify=raw_enc["Class"].values, random_state=seed)
            sc = StandardScaler().fit(Xtr[num])
            Xtr, Xte = Xtr.copy(), Xte.copy()
            Xtr[num] = sc.transform(Xtr[num])
            Xte[num] = sc.transform(Xte[num])
            raw_te = raw.loc[Xte.index]
            flag = ((raw_te.Amount > 200).astype(int) + (raw_te.Card_Present == 0).astype(int) +
                    (raw_te.Transaction_Type == "Online").astype(int) + (raw_te.Country_Match == 0).astype(int)) >= 3
            rule_rows.append(metrics(yte, flag.astype(int).values))
            strategies = {
                "none": (Xtr.values, ytr, None),
                "class_weight": (Xtr.values, ytr, "balanced"),
                "SMOTE": (*SMOTE(random_state=seed).fit_resample(Xtr.values, ytr), None),
                "undersample": (*RandomUnderSampler(random_state=seed).fit_resample(Xtr.values, ytr), None)}
            for sname, (Xs_, ys_, cw) in strategies.items():
                for name in zoo:
                    if name == "Logistic Regression":
                        clf = LogisticRegression(max_iter=2000, random_state=seed, class_weight=cw)
                    elif name == "Random Forest":
                        clf = RandomForestClassifier(n_estimators=100, min_samples_leaf=2, random_state=seed, n_jobs=2, class_weight=cw)
                    else:
                        spw = float((ys_ == 0).sum() / max((ys_ == 1).sum(), 1)) if cw else 1.0
                        clf = XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1, eval_metric="logloss",
                                            random_state=seed, n_jobs=2, scale_pos_weight=spw)
                    retry(clf.fit, Xs_, ys_)
                    p = clf.predict_proba(Xte.values)[:, 1]
                    rows.setdefault((name, sname), []).append(metrics(yte, (p > 0.5).astype(int), p))
                    del clf
                    gc.collect()
            # GRBMC (simulated annealing) trained on the undersampled set, as the product would
            Xu, yu = strategies["undersample"][:2]
            train_mod.GRBMC = lambda **kw: GRBMC(**kw, rng_seed=seed)
            mdl, _ = retry(train_mod.train_model, pd.DataFrame(Xu), pd.Series(yu), pd.DataFrame(Xte.values), pd.Series(yte),
                           n_visible=Xu.shape[1], mode="sa", epochs=20, verbose=False)
            p = mdl.predict_proba(Xte.values)[:, 1]
            rows.setdefault(("GRBMC (SA)", "undersample"), []).append(metrics(yte, (p > 0.5).astype(int), p))
            print("imbalance seed", seed)
        keys = ["precision", "recall", "f1", "roc_auc", "pr_auc"]
        imb["test_rows_per_seed"] = int(len(yte))
        imb["test_fraud_per_seed"] = int(yte.sum())
        imb["results"] = [{"model": k[0], "strategy": k[1], **mean_std(v, keys),
                           "mean_fp": float(np.mean([r["fp"] for r in v])), "mean_fn": float(np.mean([r["fn"] for r in v]))}
                          for k, v in rows.items()]
        imb["rule_based"] = {**mean_std(rule_rows, ["precision", "recall", "f1"]),
                             "mean_fp": float(np.mean([r["fp"] for r in rule_rows])),
                             "mean_fn": float(np.mean([r["fn"] for r in rule_rows]))}
        results["imbalance"] = imb
        train_mod.GRBMC = GRBMC
        save()

    # ---- seeds: GRBMC retrained, 20 epochs, same 8,000-row split ----
    if "seeds" not in results:
        seeds = {m: [] for m in MODES}
        for seed in range(5):
            train_mod.GRBMC = lambda **kw: GRBMC(**kw, rng_seed=seed)
            for m in MODES:
                mdl, h = retry(train_mod.train_model, X_tr, res["y_train"], X_te, res["y_test"], n_visible=X_tr.shape[1],
                               mode=m, epochs=20, verbose=False)
                p = mdl.predict_proba(X_te.values)[:, 1]
                r = metrics(y_te, (p > 0.5).astype(int), p)
                r["best_epoch_f1"] = float(max(h["f1"]))
                r["elapsed_sec"] = float(h["elapsed_sec"])
                seeds[m].append(r)
            print("seed", seed)
        results["seeds"] = {m: {"runs": v, **mean_std(v, ["accuracy", "precision", "recall", "f1", "roc_auc", "best_epoch_f1", "elapsed_sec"])}
                            for m, v in seeds.items()}
        train_mod.GRBMC = GRBMC
        save()

    # ---- full 39,000-row file ----
    if "full39k" not in results:
        t0 = time.time()
        resf = full_pipeline(df, method="manual", top_k=18)
        full = {"train": list(resf["X_train"].shape), "test": list(resf["X_test"].shape), "pipeline_seconds": time.time() - t0}
        for m in MODES:
            mdl, h = retry(train_mod.train_model, resf["X_train"], resf["y_train"], resf["X_test"], resf["y_test"],
                           n_visible=resf["X_train"].shape[1], mode=m, epochs=20, verbose=False)
            p = mdl.predict_proba(resf["X_test"].values)[:, 1]
            r = metrics(resf["y_test"].values, (p > 0.5).astype(int), p)
            r["elapsed_sec"] = float(h["elapsed_sec"])
            full[m] = r
        for name, mk in zoo.items():
            clf = retry(lambda: mk().fit(resf["X_train"].values, resf["y_train"].values))
            p = clf.predict_proba(resf["X_test"].values)[:, 1]
            full[name] = metrics(resf["y_test"].values, (p > 0.5).astype(int), p)
        results["full39k"] = full

        save()

    (OUT / "metrics.json").write_text(json.dumps(results, indent=1))
    print("wrote", OUT / "metrics.json")


if __name__ == "__main__":
    main()
