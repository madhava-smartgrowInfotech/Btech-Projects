"""Extra measurements for the documentation run (does NOT overwrite models/ or static/).

Reproduces the training pipeline in memory (same seed, same split, same hyper-parameters as src/hybrid_model.py)
and adds what the original run never measured: confusion matrices, a label-free (deployable) variant of the
residual hybrid, a borderline-band sweep, a decision-threshold sweep, a multi-seed study, numeric SHAP ranking,
a calibration curve, recommender gain statistics and latency.

Run with the project venv:  .venv\\Scripts\\python.exe scripts\\run_experiments.py
Outputs: docs/experiments/*.json and docs/figures/*.png
"""
import json
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (accuracy_score, roc_auc_score, f1_score, precision_score, recall_score,
                             brier_score_loss, confusion_matrix)
from xgboost import XGBClassifier
from preprocess import load_raw, build_features

OUT = os.path.join(ROOT, "docs", "experiments")
FIG = os.path.join(ROOT, "docs", "figures")
os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.size": 10, "axes.grid": True, "grid.alpha": 0.25})
C1, C2, C3, C4 = "#1f4e79", "#c0504d", "#4f8a3c", "#8064a2"


def m5(y, p, prob):
    return {"accuracy": float(accuracy_score(y, p)), "roc_auc": float(roc_auc_score(y, prob)),
            "f1": float(f1_score(y, p)), "precision": float(precision_score(y, p)),
            "recall": float(recall_score(y, p))}


def cm(y, p):
    t = confusion_matrix(y, p, labels=[0, 1])
    return {"tn": int(t[0, 0]), "fp": int(t[0, 1]), "fn": int(t[1, 0]), "tp": int(t[1, 1])}


def make_models(seed):
    return {
        "logreg": LogisticRegression(max_iter=1000, random_state=seed),
        "tree": DecisionTreeClassifier(random_state=seed),
        "rf": RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=-1),
        "svm": SVC(kernel="rbf", probability=True, random_state=seed),
        "knn": KNeighborsClassifier(n_neighbors=9),
        "xgb": XGBClassifier(n_estimators=100, max_depth=8, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
                             reg_alpha=0.1, reg_lambda=1.0, eval_metric="logloss", random_state=seed, n_jobs=-1),
    }


def run_seed(df, comp, seed, keep=False):
    """One full train/evaluate cycle. Returns metrics dict (and the artefacts if keep)."""
    train_df, temp = train_test_split(df, test_size=0.30, stratify=df["Placed"], random_state=seed)
    val_df, test_df = train_test_split(temp, test_size=0.50, stratify=temp["Placed"], random_state=seed)
    Xtr, feats, fm, sc = build_features(train_df, comp, fit=True)
    Xte, _, _, _ = build_features(test_df, comp, freq_maps=fm, scaler_stats=sc)
    ytr, yte = train_df["Placed"].values, test_df["Placed"].values
    res, fitted = {}, {}
    for name, mdl in make_models(seed).items():
        mdl.fit(Xtr, ytr)
        prob = mdl.predict_proba(Xte)[:, 1]
        res[name] = m5(yte, (prob >= 0.5).astype(int), prob)
        fitted[name] = mdl
    calib = CalibratedClassifierCV(make_models(seed)["xgb"], method="sigmoid", cv=3)
    calib.fit(Xtr, ytr)
    px = calib.predict_proba(Xte)[:, 1]
    pred_x = (px >= 0.5).astype(int)
    res["xgb_calibrated"] = m5(yte, pred_x, px)
    knn, svm = fitted["knn"], fitted["svm"]
    pk, ps = knn.predict(Xte), svm.predict(Xte)
    prk, prs = knn.predict_proba(Xte)[:, 1], svm.predict_proba(Xte)[:, 1]
    border = (px >= 0.4) & (px <= 0.6)
    oracle = (pred_x != yte) | border          # paper Eq.1 - uses the true labels
    # paper-style hybrids (as in metrics.json)
    for nm, loc, lp in (("hybrid_xgb_knn", pk, prk), ("hybrid_xgb_svm", ps, prs)):
        pr = pred_x.copy(); pr[oracle] = loc[oracle]
        pb = px.copy(); pb[oracle] = lp[oracle]
        res[nm] = m5(yte, pr, pb)
    # label-free variants (what can run at serving time)
    pr = pred_x.copy(); pr[border] = pk[border]
    pb = px.copy(); pb[border] = prk[border]
    res["hybrid_knn_labelfree"] = m5(yte, pr, pb)
    serv = px.copy(); serv[border] = 0.5 * px[border] + 0.5 * prk[border]     # exactly src/recommend.predict_for
    res["hybrid_knn_serving"] = m5(yte, (serv >= 0.5).astype(int), serv)
    extra = {"brier": float(brier_score_loss(yte, px)), "residual_rate_oracle": float(oracle.mean()),
             "borderline_rate": float(border.mean())}
    if keep:
        art = dict(train_df=train_df, test_df=test_df, Xtr=Xtr, Xte=Xte, ytr=ytr, yte=yte, feats=feats, fm=fm, sc=sc,
                   px=px, pk=pk, prk=prk, serv=serv, border=border, oracle=oracle, pred_x=pred_x, calib=calib,
                   fitted=fitted)
        return res, extra, art
    return res, extra, None


def main():
    df, comp = load_raw()
    facts = {}

    # ---------------- dataset facts ----------------
    facts["dataset"] = {
        "rows": int(len(df)), "columns": int(df.shape[1]), "placed_rate": round(float(df["Placed"].mean()), 4),
        "placed": int(df["Placed"].sum()), "not_placed": int((1 - df["Placed"]).sum()),
        "cgpa_mean": round(float(df["CGPA"].mean()), 3), "cgpa_sd": round(float(df["CGPA"].std()), 3),
        "cgpa_min": float(df["CGPA"].min()), "cgpa_max": float(df["CGPA"].max()),
        "by_branch": df.groupby("Branch")["Placed"].agg(["mean", "count"]).round(3).to_dict("index"),
        "by_tier": df.groupby("Target_Tier")["Placed"].agg(["mean", "count"]).round(3).to_dict("index"),
        "by_year": df.groupby("Placement_Year")["Placed"].agg(["mean", "count"]).round(3).to_dict("index"),
        "backlog_effect": df.groupby("Backlogs")["Placed"].mean().round(3).to_dict(),
        "internship_effect": df.groupby("Internships")["Placed"].mean().round(3).to_dict(),
        "missing_values": int(df.isna().sum().sum()), "companies": int(len(comp)),
        "companies_by_tier": comp["Tier"].value_counts().sort_index().to_dict(),
        "split": {"train": 2100, "validation": 450, "test": 450},
    }

    # ---------------- seed 42 (headline) ----------------
    t0 = time.time()
    res, extra, A = run_seed(df, comp, 42, keep=True)
    print("seed 42 done in %.1fs" % (time.time() - t0))
    with open(os.path.join(ROOT, "models", "metrics.json")) as f:
        shipped = json.load(f)["results"]
    drift = {k: {m: round(res[k][m] - shipped[k][m], 4) for m in shipped[k]} for k in shipped if k in res}
    retrain_seed42 = res
    # --- the shipped artefacts (models/*.pkl) reproduce models/metrics.json exactly; use them for every seed-42 analysis ---
    import pickle
    pre = pickle.load(open(os.path.join(ROOT, "models", "preprocess.pkl"), "rb"))
    cal = pickle.load(open(os.path.join(ROOT, "models", "xgb_calibrated.pkl"), "rb"))
    knn_s = pickle.load(open(os.path.join(ROOT, "models", "knn_residual.pkl"), "rb"))
    svm_s = pickle.load(open(os.path.join(ROOT, "models", "svm_residual.pkl"), "rb"))
    tr_s, temp_s = train_test_split(df, test_size=0.30, stratify=df["Placed"], random_state=42)
    _, te_s = train_test_split(temp_s, test_size=0.50, stratify=temp_s["Placed"], random_state=42)
    Xs, _, _, _ = build_features(te_s, comp, freq_maps=pre["freq_maps"], scaler_stats=pre["scaler"])
    ys = te_s["Placed"].values
    ps = cal.predict_proba(Xs)[:, 1]
    pdx = (ps >= 0.5).astype(int)
    bs = (ps >= 0.4) & (ps <= 0.6)
    os_ = (pdx != ys) | bs
    pks, prks = knn_s.predict(Xs), knn_s.predict_proba(Xs)[:, 1]
    sh = dict(shipped)
    pr = pdx.copy(); pr[bs] = pks[bs]; pb = ps.copy(); pb[bs] = prks[bs]
    sh["hybrid_knn_labelfree"] = {k: round(v, 4) for k, v in m5(ys, pr, pb).items()}
    sv_ = ps.copy(); sv_[bs] = 0.5 * ps[bs] + 0.5 * prks[bs]
    sh["hybrid_knn_serving"] = {k: round(v, 4) for k, v in m5(ys, (sv_ >= 0.5).astype(int), sv_).items()}
    facts["seed42"] = {"results": sh, "brier": round(float(brier_score_loss(ys, ps)), 4), "residual_rate_oracle": round(float(os_.mean()), 4),
                       "borderline_rate": round(float(bs.mean()), 4),
                       "retrain_max_abs_drift_vs_shipped": round(max(abs(x) for d in drift.values() for x in d.values()), 4),
                       "shipped_pickles_reproduce_metrics_json": bool(abs(accuracy_score(ys, pdx) - shipped["xgb_calibrated"]["accuracy"]) < 1e-4)}
    A = dict(A, yte=ys, px=ps, pk=pks, prk=prks, border=bs, oracle=os_, pred_x=pdx, serv=sv_, Xte=Xs, test_df=te_s)
    yte, px, pk, prk, border, oracle, pred_x = ys, ps, pks, prks, bs, os_, pdx
    res = sh

    # confusion matrices
    pr_or = pred_x.copy(); pr_or[oracle] = pk[oracle]
    pr_lf = pred_x.copy(); pr_lf[border] = pk[border]
    pr_sv = (A["serv"] >= 0.5).astype(int)
    facts["confusion"] = {"xgb_calibrated": cm(yte, pred_x), "hybrid_oracle": cm(yte, pr_or),
                          "hybrid_labelfree": cm(yte, pr_lf), "hybrid_serving": cm(yte, pr_sv),
                          "logreg": cm(yte, (A["fitted"]["logreg"].predict_proba(A["Xte"])[:, 1] >= 0.5).astype(int))}
    facts["residual"] = {
        "n_test": int(len(yte)), "oracle_residual": int(oracle.sum()), "borderline_only": int(border.sum()),
        "xgb_errors": int((pred_x != yte).sum()),
        "xgb_errors_inside_band": int(((pred_x != yte) & border).sum()),
        "knn_acc_on_borderline": round(float((pk[border] == yte[border]).mean()), 4),
        "xgb_acc_on_borderline": round(float((pred_x[border] == yte[border]).mean()), 4),
        "knn_acc_on_oracle": round(float((pk[oracle] == yte[oracle]).mean()), 4),
        "xgb_acc_on_oracle": round(float((pred_x[oracle] == yte[oracle]).mean()), 4),
    }

    # band sweep (label-free, hard replacement by kNN)
    band = []
    for lo, hi in ((0.5, 0.5), (0.45, 0.55), (0.4, 0.6), (0.35, 0.65), (0.3, 0.7), (0.2, 0.8)):
        b = (px >= lo) & (px <= hi)
        pr = pred_x.copy(); pr[b] = pk[b]
        pb = px.copy(); pb[b] = prk[b]
        r = m5(yte, pr, pb)
        band.append({"lo": lo, "hi": hi, "replaced": int(b.sum()), **{k: round(v, 4) for k, v in r.items()}})
    facts["band_sweep"] = band

    # decision-threshold sweep (calibrated XGBoost)
    thr = []
    for t in (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70):
        p = (px >= t).astype(int)
        thr.append({"threshold": t, "accuracy": round(float(accuracy_score(yte, p)), 4), "precision": round(float(precision_score(yte, p)), 4),
                    "recall": round(float(recall_score(yte, p)), 4), "f1": round(float(f1_score(yte, p)), 4)})
    facts["threshold_sweep"] = thr

    # calibration curve
    fr, mp = calibration_curve(yte, px, n_bins=8, strategy="uniform")
    raw = A["fitted"]["xgb"].predict_proba(A["Xte"])[:, 1]
    fr2, mp2 = calibration_curve(yte, raw, n_bins=8, strategy="uniform")
    facts["calibration"] = {"brier_platt": round(float(brier_score_loss(yte, px)), 4), "brier_raw_xgb": round(float(brier_score_loss(yte, raw)), 4),
                            "brier_logreg": round(float(brier_score_loss(yte, A["fitted"]["logreg"].predict_proba(A["Xte"])[:, 1])), 4),
                            "mean_prob_test": round(float(px.mean()), 4), "base_rate_test": round(float(yte.mean()), 4)}

    # ---------------- SHAP ----------------
    try:
        import shap
        ex = shap.TreeExplainer(A["fitted"]["xgb"])
        sv = ex.shap_values(A["Xte"])
        mean_abs = np.abs(sv).mean(0)
        names = [f.replace("_std", "").replace("_freq", " (freq)") for f in A["feats"]]
        order = np.argsort(mean_abs)[::-1]
        facts["shap_top"] = [{"feature": names[i], "mean_abs_shap": round(float(mean_abs[i]), 4)} for i in order[:12]]
        facts["shap_n"] = int(len(A["Xte"]))
        top = order[:10][::-1]
        plt.figure(figsize=(6.4, 3.8))
        plt.barh([names[i] for i in top], [mean_abs[i] for i in top], color=C3)
        plt.xlabel("Mean |SHAP value| (test set, n=450)"); plt.title("Top-10 feature contributions (XGBoost)")
        plt.tight_layout(); plt.savefig(os.path.join(FIG, "shap_top10.png"), dpi=150); plt.close()
    except Exception as e:  # pragma: no cover
        facts["shap_error"] = str(e)

    # ---------------- multi-seed study ----------------
    seeds = [42, 1, 2, 3, 4]
    allres = {}
    for s in seeds:
        r, e, _ = (retrain_seed42, extra, None) if s == 42 else run_seed(df, comp, s)
        allres[s] = r
        print("seed", s, "done")
    models = list(allres[42].keys())
    ms = {}
    for mname in models:
        ms[mname] = {}
        for met in ("accuracy", "roc_auc", "f1", "precision", "recall"):
            vals = np.array([allres[s][mname][met] for s in seeds])
            ms[mname][met] = {"mean": round(float(vals.mean()), 4), "sd": round(float(vals.std(ddof=1)), 4),
                              "min": round(float(vals.min()), 4), "max": round(float(vals.max()), 4)}
    facts["multi_seed"] = {"seeds": seeds, "summary": ms,
                           "per_seed_accuracy": {m: [round(allres[s][m]["accuracy"], 4) for s in seeds] for m in models}}

    # ---------------- recommender statistics ----------------
    from src.recommend import recommend, predict_for, pre_comp_cache
    tdf = A["test_df"].reset_index(drop=True)
    rej = tdf[(A["px"] < 0.5)].head(60)          # students the model rates as not ready for their own target
    gains, base, topp, matched, ready_after, tier_shift, lat = [], [], [], 0, 0, [], []
    for _, r in rej.iterrows():
        prof = {"cgpa": r["CGPA"], "tenth": r["Tenth_Percent"], "twelfth": r["Twelfth_Percent"], "aptitude": r["Aptitude_Score"],
                "technical": r["Technical_Score"], "communication": r["Communication_Score"], "dsa": r["DSA_Score"],
                "projects": int(r["Projects"]), "internships": int(r["Internships"]), "certifications": int(r["Certifications"]),
                "backlogs": int(r["Backlogs"]), "branch": r["Branch"], "target_company": r["Target_Company"],
                "target_role": r["Target_Role"] if r["Target_Role"] in ("SDE", "Data Analyst", "ML Engineer", "QA Engineer") else "SDE"}
        t = time.perf_counter()
        out = recommend(prof, top_k=5)
        lat.append(time.perf_counter() - t)
        base.append(out["base_prob"])
        if out["hybrid"]:
            matched += int(out["match_rate"] > 0)
            topp.append(out["hybrid"][0]["prob"])
            gains.append(out["avg_gain"])
            ready_after += int(out["hybrid"][0]["prob"] >= 0.5)
    facts["recommender"] = {
        "students": int(len(rej)), "with_at_least_one_better_alt": int(matched),
        "mean_base_prob": round(float(np.mean(base)), 4), "mean_top1_prob": round(float(np.mean(topp)), 4),
        "mean_avg_gain_over_improved": round(float(np.mean([g for g in gains if g > 0])), 4) if any(g > 0 for g in gains) else 0.0,
        "top1_reaches_ready": int(ready_after),
        "recommend_latency_s": {"mean": round(float(np.mean(lat)), 3), "p50": round(float(np.percentile(lat, 50)), 3),
                                "p95": round(float(np.percentile(lat, 95)), 3), "max": round(float(np.max(lat)), 3)},
        "note": "Gains are model-estimated probabilities, not realised placements."}
    plt.figure(figsize=(5.6, 3.4))
    plt.hist([t - b for t, b in zip(topp, base[:len(topp)])], bins=15, color=C1, alpha=0.85)
    plt.xlabel("Top-1 recommendation probability minus original-target probability"); plt.ylabel("Students")
    plt.title("Estimated gain from the hybrid recommendation (n=%d)" % len(topp)); plt.tight_layout()
    plt.savefig(os.path.join(FIG, "reco_gain.png"), dpi=150); plt.close()

    # ---------------- inference latency (in-process) ----------------
    row = pre_comp_cache().iloc[6]
    prof = {"cgpa": 8.4, "aptitude": 82, "technical": 84, "communication": 75, "dsa": 80, "projects": 3,
            "internships": 1, "certifications": 2, "backlogs": 0, "branch": "CSE"}
    predict_for(prof, row, "SDE")
    ts = []
    for _ in range(100):
        t = time.perf_counter(); predict_for(prof, row, "SDE"); ts.append((time.perf_counter() - t) * 1000)
    facts["latency_predict_for_ms"] = {"mean": round(float(np.mean(ts)), 2), "p50": round(float(np.percentile(ts, 50)), 2),
                                        "p95": round(float(np.percentile(ts, 95)), 2), "n": 100}
    # -------- figures --------
    labels = {"logreg": "LogReg", "tree": "Tree", "rf": "RF", "svm": "SVM", "knn": "kNN", "xgb": "XGB",
              "xgb_calibrated": "XGB+Platt", "hybrid_xgb_knn": "Hybrid (paper)", "hybrid_knn_serving": "Hybrid (serving)"}
    keys = list(labels)
    x = np.arange(len(keys)); w = 0.26
    fig, ax = plt.subplots(figsize=(8.4, 3.8))
    for i, (met, col) in enumerate((("accuracy", C1), ("f1", C3), ("roc_auc", C2))):
        ax.bar(x + (i - 1) * w, [res[k][met] for k in keys], w, label=met.replace("roc_auc", "ROC-AUC").replace("f1", "F1").capitalize() if met == "accuracy" else met.replace("roc_auc", "ROC-AUC").replace("f1", "F1"), color=col)
    ax.set_xticks(x); ax.set_xticklabels([labels[k] for k in keys], rotation=20, ha="right")
    ax.set_ylim(0.65, 0.95); ax.set_ylabel("Score (test set, n=450)"); ax.legend(ncol=3, loc="upper left")
    ax.set_title("Model comparison on the held-out test set (seed 42)"); plt.tight_layout()
    plt.savefig(os.path.join(FIG, "model_comparison.png"), dpi=150); plt.close()

    fig, axs = plt.subplots(1, 3, figsize=(8.6, 2.9))
    for ax, key, ttl in zip(axs, ("xgb_calibrated", "hybrid_oracle", "hybrid_serving"),
                            ("XGBoost + Platt", "Hybrid (labels used)", "Hybrid (label-free)")):
        c = facts["confusion"][key]
        mat = np.array([[c["tn"], c["fp"]], [c["fn"], c["tp"]]])
        ax.imshow(mat, cmap="Blues")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(mat[i, j]), ha="center", va="center", color="white" if mat[i, j] > mat.max() / 2 else "black", fontsize=12)
        ax.set_xticks([0, 1]); ax.set_xticklabels(["Pred 0", "Pred 1"]); ax.set_yticks([0, 1]); ax.set_yticklabels(["True 0", "True 1"])
        ax.set_title(ttl, fontsize=9); ax.grid(False)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "confusion_matrices.png"), dpi=150); plt.close()

    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ax.plot([t["threshold"] for t in thr], [t["precision"] for t in thr], "o-", color=C1, label="Precision")
    ax.plot([t["threshold"] for t in thr], [t["recall"] for t in thr], "s-", color=C2, label="Recall")
    ax.plot([t["threshold"] for t in thr], [t["f1"] for t in thr], "^-", color=C3, label="F1")
    ax.plot([t["threshold"] for t in thr], [t["accuracy"] for t in thr], "d--", color=C4, label="Accuracy")
    ax.set_xlabel("Decision threshold on calibrated probability"); ax.set_ylabel("Score"); ax.legend(); ax.set_title("Threshold analysis (XGBoost + Platt)")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "threshold_sweep.png"), dpi=150); plt.close()

    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1], [0, 1], "k:", label="Perfect")
    ax.plot(mp2, fr2, "o-", color=C2, label="XGBoost (raw)")
    ax.plot(mp, fr, "s-", color=C1, label="XGBoost + Platt")
    ax.set_xlabel("Mean predicted probability"); ax.set_ylabel("Observed placed fraction"); ax.legend(); ax.set_title("Reliability diagram (test set)")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "calibration.png"), dpi=150); plt.close()

    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    for k, col in (("xgb_calibrated", C1), ("logreg", C2), ("hybrid_knn_serving", C3), ("hybrid_xgb_knn", C4)):
        v = [allres[s][k]["accuracy"] for s in seeds]
        ax.plot(range(len(seeds)), v, "o-", color=col, label=labels[k])
    ax.set_xticks(range(len(seeds))); ax.set_xticklabels(["seed %d" % s for s in seeds])
    ax.set_ylabel("Test accuracy"); ax.legend(ncol=2, fontsize=8); ax.set_title("Accuracy across five random splits")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "multi_seed.png"), dpi=150); plt.close()

    with open(os.path.join(OUT, "experiments.json"), "w") as f:
        json.dump(facts, f, indent=2, default=str)
    print("wrote", os.path.join(OUT, "experiments.json"))


if __name__ == "__main__":
    main()
