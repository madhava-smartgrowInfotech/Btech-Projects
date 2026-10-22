"""Aggregate the LIAR2 experiment runs and draw the result charts into docs/figures/ (system python; matplotlib).

    python scripts/docs_build/make_figures.py

Reads experiments/liar2/seed_*.json and test_predictions_seed42.csv; writes experiments/liar2/metrics.json
(means, standard deviations, error analysis) and docs/figures/f01..f10.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiments" / "liar2"
FIG = ROOT / "docs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
LABELS = ["REAL", "PARTIALLY TRUE", "FAKE"]
NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY, RED = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#8B97A8", "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#5B6B7F", "axes.labelcolor": "#14213D", "xtick.color": "#14213D", "ytick.color": "#14213D"})


def ms(vals):
    a = np.array(vals, dtype=float)
    return float(a.mean()), float(a.std(ddof=1)) if len(a) > 1 else 0.0


def load_runs():
    runs = []
    for p in sorted(glob.glob(str(EXP / "seed_*.json"))):
        runs.append(json.load(open(p, encoding="utf-8")))
    return runs


def aggregate(runs):
    out = {"seeds": [r["seed"] for r in runs], "n_runs": len(runs)}
    r0 = runs[0]
    for k in ("n_train_subsample", "n_train_full", "n_valid", "n_test", "train_class_counts", "test_class_counts", "settings"):
        out[k] = r0[k]

    def stat(path_fn):
        vals = [path_fn(r) for r in runs]
        m, s = ms(vals)
        return {"mean": m, "std": s, "values": vals}

    def model_block(get):
        return {"accuracy": stat(lambda r: get(r)["accuracy"]), "f1_macro": stat(lambda r: get(r)["f1_macro"]),
                "f1_weighted": stat(lambda r: get(r)["f1_weighted"])}

    out["proposed_test"] = model_block(lambda r: r["proposed"]["test"])
    out["proposed_valid"] = model_block(lambda r: r["proposed"]["valid"])
    out["pca_svc_default_test"] = model_block(lambda r: r["pca_svc_default"]["test"])
    out["pca_svc_mask_only_test"] = model_block(lambda r: r["pca_svc_mask_only"]["test"])
    out["random_search_test"] = model_block(lambda r: r["random_search"]["test"])
    out["majority_test"] = model_block(lambda r: r["majority"])
    for tag in ("subsample", "full"):
        for name in ("LinearSVC", "LogisticRegression", "ComplementNB"):
            out[f"ref_{tag}_{name}_test"] = model_block(lambda r, tag=tag, name=name: r["ref_" + tag][name]["test"])
            out[f"ref_{tag}_{name}_time"] = stat(lambda r, tag=tag, name=name: r["ref_" + tag][name]["train_time_s"])
    out["train_time_s"] = stat(lambda r: r["train_time_s"])
    out["random_search_time_s"] = stat(lambda r: r["random_search"]["search_time_s"])
    out["n_firefly_evals"] = stat(lambda r: r["n_firefly_evals"])
    out["n_pca"] = stat(lambda r: r["pipeline"]["n_pca"])
    out["pca_variance"] = stat(lambda r: r["pipeline"]["pca_variance"])
    out["n_selected"] = stat(lambda r: r["pipeline"]["n_selected"])
    out["best_C"] = stat(lambda r: r["pipeline"]["best_C"])
    out["best_gamma"] = stat(lambda r: r["pipeline"]["best_gamma"])
    out["firefly_fitness_best"] = stat(lambda r: r["firefly_fitness_best"])
    out["random_fitness_best"] = stat(lambda r: r["random_search"]["fitness"])
    out["random_n_selected"] = stat(lambda r: r["random_search"]["n_selected"])
    out["internal_holdout_f1"] = stat(lambda r: r["internal_holdout"]["f1_macro"])
    out["internal_holdout_acc"] = stat(lambda r: r["internal_holdout"]["accuracy"])
    out["baseline_time_s"] = stat(lambda r: r["pipeline"]["baseline_time_s"])
    out["predict_time_test_s"] = stat(lambda r: r["predict_time_test_s"])
    out["firefly_history"] = [r["pipeline"]["firefly_history"] for r in runs]
    out["per_class_test"] = {c: {m: stat(lambda r, c=c, m=m: r["proposed"]["test"]["per_class"][c][m]) for m in ("precision", "recall", "f1-score")} for c in LABELS}
    cm = np.sum([np.array(r["proposed"]["test"]["confusion_matrix"]) for r in runs], axis=0)
    out["confusion_matrix_sum"] = cm.tolist()
    out["confusion_matrix_seed42"] = next((r["proposed"]["test"]["confusion_matrix"] for r in runs if r["seed"] == 42), runs[0]["proposed"]["test"]["confusion_matrix"])
    demo = next((r for r in runs if "demo_model_on_liar2_test" in r), None)
    if demo:
        out["demo_model_on_liar2_test"] = demo["demo_model_on_liar2_test"]
        out["demo_model_prediction_counts"] = demo["demo_model_prediction_counts"]
    return out


def error_analysis():
    p = EXP / "test_predictions_seed42.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    df["ok"] = df["true"] == df["pred"]
    df["conf"] = df[["p_real", "p_partial", "p_fake"]].max(axis=1)
    df["words"] = df["statement"].fillna("").str.split().str.len()
    res = {"n": int(len(df)), "accuracy": float(df["ok"].mean())}
    bins = [0, 0.4, 0.5, 0.6, 0.7, 0.8, 1.01]
    df["cbin"] = pd.cut(df["conf"], bins, right=False)
    res["by_confidence"] = [{"bin": str(k), "n": int(len(g)), "accuracy": float(g["ok"].mean())} for k, g in df.groupby("cbin", observed=True)]
    lb = [0, 10, 15, 20, 30, 1000]
    df["lbin"] = pd.cut(df["words"], lb, right=False)
    res["by_length"] = [{"bin": f"{int(k.left)}-{int(k.right) - 1}" if k.right < 1000 else f"{int(k.left)}+", "n": int(len(g)), "accuracy": float(g["ok"].mean())} for k, g in df.groupby("lbin", observed=True)]
    res["pairs"] = {f"{t} -> {pd_}": int(n) for (t, pd_), n in df[~df["ok"]].groupby(["true", "pred"]).size().items()}
    res["pred_counts"] = {k: int(v) for k, v in df["pred"].value_counts().items()}
    res["true_counts"] = {k: int(v) for k, v in df["true"].value_counts().items()}
    # the verdict comes from SVC.predict, the probabilities from Platt scaling (probability=True): they can disagree
    from sklearn.metrics import f1_score
    lab = {l: i for i, l in enumerate(LABELS)}
    pr = df["pred"].map(lab).values
    tr = df["true"].map(lab).values
    am = df[["p_real", "p_partial", "p_fake"]].values.argmax(1)
    res["label_vs_proba"] = {"disagree_n": int((am != pr).sum()), "disagree_rate": float((am != pr).mean()),
                             "argmax_counts": [int(x) for x in np.bincount(am, minlength=3)], "label_counts": [int(x) for x in np.bincount(pr, minlength=3)],
                             "acc_if_argmax": float((am == tr).mean()), "f1_if_argmax": float(f1_score(tr, am, average="macro")),
                             "partial_label_argmax_partial": int(((pr == 1) & (am == 1)).sum()),
                             "crosstab": {LABELS[i]: {LABELS[j]: int(((pr == i) & (am == j)).sum()) for j in range(3)} for i in range(3)}}
    # orig 6-way labels vs prediction
    six = {0: "pants-on-fire", 1: "false", 2: "barely-true", 3: "half-true", 4: "mostly-true", 5: "true"}
    res["by_original_label"] = {six[k]: {"n": int(len(g)), "pred_REAL": int((g["pred"] == "REAL").sum()), "pred_PARTIALLY TRUE": int((g["pred"] == "PARTIALLY TRUE").sum()),
                                         "pred_FAKE": int((g["pred"] == "FAKE").sum())} for k, g in df.groupby("orig_label")}
    return res, df


def save(fig, name):
    fig.savefig(FIG / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def f01_comparison(a):
    rows = [("Majority class\n(always FAKE)", a["majority_test"], GREY),
            ("Complement NB\n(TF-IDF, 3,000 docs)", a["ref_subsample_ComplementNB_test"], GREY),
            ("Logistic regression\n(TF-IDF, 3,000 docs)", a["ref_subsample_LogisticRegression_test"], GREY),
            ("Linear SVM\n(TF-IDF, 3,000 docs)", a["ref_subsample_LinearSVC_test"], GREY),
            ("Linear SVM\n(TF-IDF, all 18,369 docs)", a["ref_full_LinearSVC_test"], "#6C7A8C"),
            ("PCA + default RBF SVM", a["pca_svc_default_test"], BLUE),
            ("PCA + Firefly mask only", a["pca_svc_mask_only_test"], TEAL),
            ("PCA + random search\n(same budget)", a["random_search_test"], ORANGE),
            ("PCA + Firefly + MSVM\n(proposed)", a["proposed_test"], PURPLE)]
    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    y = np.arange(len(rows))[::-1]
    h = 0.36
    for i, (name, blk, col) in enumerate(rows):
        for off, key, lab, alpha in ((h / 2, "f1_macro", "Macro-F1", 1.0), (-h / 2, "accuracy", "Accuracy", 0.45)):
            m, s = blk[key]["mean"], blk[key]["std"]
            ax.barh(y[i] + off, m, height=h, color=col, alpha=alpha, label=lab if i == 0 else None, xerr=s if s > 0 else None, error_kw=dict(ecolor="#14213D", lw=1, capsize=2))
            ax.text(m + (s if s else 0) + 0.008, y[i] + off, f"{m:.3f}", va="center", fontsize=7.5)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=8)
    ax.set_xlim(0, 0.75)
    ax.set_xlabel("Score on the LIAR2 test split (2,296 statements, 3 classes); bars: dark = macro-F1, light = accuracy")
    ax.axvline(1 / 3, color="#999", lw=0.8, ls=":")
    ax.text(1 / 3 + 0.004, y[-1] - 0.62, "1/3", fontsize=7, color="#777")
    ax.set_title("Test scores of the proposed pipeline and its comparisons (mean of seeds; whiskers = std)", fontsize=9.5, color=NAVY, loc="left")
    save(fig, "f01_model_comparison.png")


def f02_firefly(a, runs):
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    cols = [PURPLE, BLUE, TEAL, ORANGE]
    for i, (r, c) in enumerate(zip(runs, cols)):
        h = r["pipeline"]["firefly_history"]
        ax.plot(range(1, len(h) + 1), h, marker="o", ms=3.5, color=c, label=f"Firefly, seed {r['seed']}")
        ax.axhline(r["random_search"]["fitness"], color=c, ls=":", lw=1)
    ax.plot([], [], color="#666", ls=":", label="random search best (same budget)")
    ax.set_xlabel("Firefly generation")
    ax.set_ylabel("Best fitness (CV macro-F1 less size penalty)")
    ax.legend(fontsize=7.5, frameon=False)
    ax.set_title("Firefly convergence on the training split", fontsize=9.5, color=NAVY, loc="left")
    save(fig, "f02_firefly_convergence.png")


def f03_confusion(a):
    cm = np.array(a["confusion_matrix_seed42"])
    norm = cm / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(5.0, 4.2))
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{cm[i, j]}\n({norm[i, j] * 100:.0f}%)", ha="center", va="center", color="white" if norm[i, j] > 0.5 else "#14213D", fontsize=9)
    ax.set_xticks(range(3))
    ax.set_yticks(range(3))
    ax.set_xticklabels(LABELS, fontsize=8)
    ax.set_yticklabels(LABELS, fontsize=8)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.spines[:].set_visible(False)
    ax.set_title("Confusion matrix, LIAR2 test split (seed 42)", fontsize=9.5, color=NAVY, loc="left")
    save(fig, "f03_confusion_matrix.png")


def f04_per_class(a):
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    w = 0.26
    x = np.arange(3)
    for k, (m, col) in enumerate((("precision", BLUE), ("recall", TEAL), ("f1-score", PURPLE))):
        vals = [a["per_class_test"][c][m]["mean"] for c in LABELS]
        errs = [a["per_class_test"][c][m]["std"] for c in LABELS]
        ax.bar(x + (k - 1) * w, vals, w, color=col, label=m.replace("f1-score", "F1"), yerr=errs, error_kw=dict(ecolor="#14213D", lw=1, capsize=2))
        for xi, v in zip(x + (k - 1) * w, vals):
            ax.text(xi, v + 0.025, f"{v:.2f}", ha="center", fontsize=7)
    sup = a["test_class_counts"]
    ax.set_xticks(x)
    ax.set_xticklabels([f"{c}\n(n={n})" for c, n in zip(LABELS, sup)], fontsize=8)
    ax.set_ylim(0, 1.0)
    ax.legend(fontsize=8, frameon=False, ncol=3, loc="upper left")
    ax.set_title("Per-class precision, recall and F1 on the test split (mean of seeds)", fontsize=9.5, color=NAVY, loc="left")
    save(fig, "f04_per_class_prf.png")


def f05_demo_vs_real(a, hold):
    fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.6), gridspec_kw=dict(width_ratios=[1, 1.15]))
    ax = axs[0]
    vals = [hold, a["demo_model_on_liar2_test"]["f1_macro"] if "demo_model_on_liar2_test" in a else 0, a["proposed_test"]["f1_macro"]["mean"]]
    names = ["Shipped demo model,\nits own held-out\nsynthetic split", "Shipped demo model,\nreal LIAR2 test", "Model trained on\nLIAR2, real test"]
    bars = ax.bar(range(3), vals, color=[GREY, RED, PURPLE], width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.3f}", ha="center", fontsize=8.5, fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels(names, fontsize=7.6)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Macro-F1")
    ax.set_title("A 1.000 score on templates does not transfer", fontsize=9, color=NAVY, loc="left")
    ax = axs[1]
    t = a["test_class_counts"]
    d = a.get("demo_model_prediction_counts", [0, 0, 0])
    x = np.arange(3)
    ax.bar(x - 0.2, t, 0.4, color=TEAL, label="true labels (LIAR2 test)")
    ax.bar(x + 0.2, d, 0.4, color=RED, label="demo model's predictions")
    for xi, v in zip(x - 0.2, t):
        ax.text(xi, v + 25, str(v), ha="center", fontsize=7.5)
    for xi, v in zip(x + 0.2, d):
        ax.text(xi, v + 25, str(v), ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(LABELS, fontsize=8)
    ax.legend(fontsize=7.5, frameon=False)
    ax.set_title("What the demo model does on real statements", fontsize=9, color=NAVY, loc="left")
    save(fig, "f05_demo_vs_real.png")


def f06_reliability(ea):
    res = ea[0]
    bins = res["by_confidence"]
    fig, ax = plt.subplots(figsize=(6.2, 3.5))
    x = np.arange(len(bins))
    ax.bar(x, [b["accuracy"] for b in bins], color=BLUE, width=0.6)
    for xi, b in zip(x, bins):
        ax.text(xi, b["accuracy"] + 0.015, f"{b['accuracy']:.2f}\n(n={b['n']})", ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels([b["bin"].replace("[", "").replace(")", "").replace(", ", " - ").replace("1.01", "1.0") for b in bins], fontsize=7.8)
    ax.axhline(res["accuracy"], color=ORANGE, ls="--", lw=1)
    ax.text(len(bins) - 0.5, res["accuracy"] + 0.01, f"overall {res['accuracy']:.3f}", color=ORANGE, ha="right", fontsize=7.5)
    ax.set_ylim(0, 1.15)
    ax.set_xlabel("Highest class probability (confidence) of the prediction")
    ax.set_ylabel("Accuracy in the bin")
    ax.set_title("Accuracy by confidence bin (seed 42, test split)", fontsize=9.5, color=NAVY, loc="left")
    save(fig, "f06_confidence_bins.png")


def f11_label_vs_proba(ea):
    lv = ea[0]["label_vs_proba"]
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    x = np.arange(3)
    ax.bar(x - 0.2, lv["label_counts"], 0.4, color=PURPLE, label="verdict shown (SVC.predict)")
    ax.bar(x + 0.2, lv["argmax_counts"], 0.4, color=ORANGE, label="class with the highest probability (Platt)")
    for xi, v in zip(x - 0.2, lv["label_counts"]):
        ax.text(xi, v + 25, str(v), ha="center", fontsize=7.5)
    for xi, v in zip(x + 0.2, lv["argmax_counts"]):
        ax.text(xi, v + 25, str(v), ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(LABELS, fontsize=8)
    ax.set_ylabel("Test statements (of 2,296)")
    ax.legend(fontsize=7.8, frameon=False)
    ax.set_title(f"Verdict and probabilities disagree on {lv['disagree_rate'] * 100:.1f}% of the test statements", fontsize=9.3, color=NAVY, loc="left")
    save(fig, "f11_label_vs_probability.png")


def f07_time(a):
    items = [("Complement NB (3,000 docs)", a["ref_subsample_ComplementNB_time"]["mean"], GREY), ("Linear SVM (3,000 docs)", a["ref_subsample_LinearSVC_time"]["mean"], GREY),
             ("Linear SVM (18,369 docs)", a["ref_full_LinearSVC_time"]["mean"], GREY), ("PCA + default SVM fit only", a["baseline_time_s"]["mean"], BLUE),
             ("Firefly search (full pipeline fit)", a["train_time_s"]["mean"], PURPLE), ("Random search (same budget)", a["random_search_time_s"]["mean"], ORANGE)]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    y = np.arange(len(items))[::-1]
    ax.barh(y, [i[1] for i in items], color=[i[2] for i in items], height=0.6)
    ax.set_xscale("log")
    for yi, it in zip(y, items):
        ax.text(it[1] * 1.12, yi, f"{it[1]:.2f} s" if it[1] < 100 else f"{it[1]:.0f} s", va="center", fontsize=8)
    ax.set_yticks(y)
    ax.set_yticklabels([i[0] for i in items], fontsize=8)
    ax.set_xlabel("Training time in seconds (log scale), mean of seeds, CPU only")
    ax.set_xlim(0.001, max(i[1] for i in items) * 8)
    ax.set_title("Training cost: the Firefly search is the expensive step", fontsize=9.5, color=NAVY, loc="left")
    save(fig, "f07_training_time.png")


def f08_funnel(a):
    stages = [("TF-IDF + stylometric\nfeatures", a["n_firefly_evals"] and 4025), ("After PCA\n(cap 300)", a["n_pca"]["mean"]), ("After Firefly\nselection", a["n_selected"]["mean"])]
    fig, ax = plt.subplots(figsize=(6.0, 3.3))
    vals = [s[1] for s in stages]
    bars = ax.bar(range(3), vals, color=[GREY, BLUE, PURPLE], width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 60, f"{v:.0f}", ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels([s[0] for s in stages], fontsize=8)
    ax.set_ylabel("Number of features")
    ax.set_ylim(0, 4600)
    ax.text(1, a["n_pca"]["mean"] + 420, f"keeps {a['pca_variance']['mean'] * 100:.1f}% of the variance", ha="center", fontsize=7.8, color=BLUE)
    ax.set_title("Dimensionality reduction (mean of seeds, 3,000 training documents)", fontsize=9.3, color=NAVY, loc="left")
    save(fig, "f08_feature_funnel.png")


def f09_seeds(a):
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    seeds = a["seeds"]
    x = np.arange(len(seeds))
    w = 0.26
    for k, (key, lab, col) in enumerate((("pca_svc_default_test", "PCA + default SVM", BLUE), ("random_search_test", "PCA + random search", ORANGE), ("proposed_test", "PCA + Firefly + MSVM", PURPLE))):
        v = a[key]["f1_macro"]["values"]
        ax.bar(x + (k - 1) * w, v, w, color=col, label=lab)
        for xi, vv in zip(x + (k - 1) * w, v):
            ax.text(xi, vv + 0.004, f"{vv:.3f}", ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([f"seed {s}" for s in seeds])
    lo = min(min(a[k]["f1_macro"]["values"]) for k in ("pca_svc_default_test", "random_search_test", "proposed_test"))
    ax.set_ylim(max(0, lo - 0.05), max(max(a[k]["f1_macro"]["values"]) for k in ("pca_svc_default_test", "random_search_test", "proposed_test")) + 0.04)
    ax.set_ylabel("Test macro-F1")
    ax.legend(fontsize=7.8, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    ax.set_title("Seed-to-seed variation of the test macro-F1", fontsize=9.5, color=NAVY, loc="left")
    save(fig, "f09_seed_variation.png")


def f10_length(ea):
    res = ea[0]
    bins = res["by_length"]
    fig, ax = plt.subplots(figsize=(6.0, 3.3))
    x = np.arange(len(bins))
    ax.bar(x, [b["accuracy"] for b in bins], color=TEAL, width=0.6)
    for xi, b in zip(x, bins):
        ax.text(xi, b["accuracy"] + 0.01, f"{b['accuracy']:.2f}\n(n={b['n']})", ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels([b["bin"] for b in bins])
    ax.set_xlabel("Statement length in words")
    ax.set_ylabel("Accuracy")
    ax.set_ylim(0, 0.9)
    ax.axhline(res["accuracy"], color=ORANGE, ls="--", lw=1)
    ax.set_title("Accuracy by statement length (seed 42, test split)", fontsize=9.5, color=NAVY, loc="left")
    save(fig, "f10_accuracy_by_length.png")


def main():
    runs = load_runs()
    if not runs:
        print("no seed_*.json yet")
        return 1
    a = aggregate(runs)
    ea = error_analysis()
    if ea:
        a["error_analysis"] = ea[0]
    demo_hold = 1.0
    try:
        demo_hold = json.load(open(ROOT / "models" / "metrics.json"))["f1_macro"]
    except Exception:
        pass
    a["demo_holdout_f1"] = demo_hold
    json.dump(a, open(EXP / "metrics.json", "w", encoding="utf-8"), indent=2)
    print("wrote experiments/liar2/metrics.json from", a["seeds"])
    f01_comparison(a)
    f02_firefly(a, runs)
    f03_confusion(a)
    f04_per_class(a)
    if "demo_model_on_liar2_test" in a:
        f05_demo_vs_real(a, demo_hold)
    if ea:
        f06_reliability(ea)
        f10_length(ea)
        f11_label_vs_proba(ea)
    f07_time(a)
    f08_funnel(a)
    f09_seeds(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
