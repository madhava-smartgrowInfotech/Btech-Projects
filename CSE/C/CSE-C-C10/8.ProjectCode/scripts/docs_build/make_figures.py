"""Draw the result charts for the VenturePulse documents into docs/figures/ (system python; matplotlib).

    python scripts/docs_build/make_figures.py

Reads evaluation/real_results.json, extra_results.json, evaluation_results.json and latency.json; writes docs/figures/f01..f13.
Only the literature figures in f11 are typed (docs/REPORT_FACTS.md section 14).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "evaluation"
FIG = ROOT / "docs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY, RED = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#8B97A8", "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#5B6B7F", "axes.labelcolor": "#14213D", "xtick.color": "#14213D", "ytick.color": "#14213D",
                     "axes.titlesize": 10.5, "axes.titleweight": "bold", "axes.titlecolor": "#1F3A5F"})

R = json.load(open(EV / "real_results.json", encoding="utf-8"))
X = json.load(open(EV / "extra_results.json", encoding="utf-8"))
S = json.load(open(EV / "evaluation_results.json", encoding="utf-8"))
LAT = json.load(open(EV / "latency.json", encoding="utf-8"))

SHORT = {"Logistic Regression": "Logistic\nRegression", "Decision Tree": "Decision\nTree", "Random Forest": "Random\nForest",
         "XGBoost": "XGBoost", "HistGradientBoosting": "Hist. Gradient\nBoosting"}


def save(fig, name):
    fig.savefig(FIG / name, dpi=170, facecolor="white", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print("saved", name)


def mk(blk, key):
    return blk[key]["mean"], blk[key]["std"]


def grouped(ax, groups, series, colors, width=0.8, ylim=None, fmt="{:.2f}", fs=7):
    """groups: x labels; series: list of (label, means, stds)."""
    n = len(series)
    w = width / n
    x = np.arange(len(groups))
    for i, (lab, m, s) in enumerate(series):
        pos = x - width / 2 + w * (i + 0.5)
        ax.bar(pos, m, w * 0.92, yerr=s, capsize=2, label=lab, color=colors[i], error_kw={"lw": 0.9, "ecolor": "#14213D"})
        for p, v in zip(pos, m):
            pass
        for p, v, e in zip(pos, m, s):
            ax.text(p, v + e + 0.006, fmt.format(v), ha="center", va="bottom", fontsize=fs)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    if ylim:
        ax.set_ylim(*ylim)


# ---------------------------------------------------------------- f01
def f01():
    names = list(R["models"].keys())
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    ser = []
    for key, lab in (("balanced_accuracy", "Balanced accuracy"), ("roc_auc", "ROC-AUC"), ("f1", "F1 (success class)")):
        ser.append((lab, [mk(R["models"][n], key)[0] for n in names], [mk(R["models"][n], key)[1] for n in names]))
    grouped(ax, [SHORT[n] for n in names], ser, [BLUE, TEAL, ORANGE], ylim=(0.4, 1.0))
    ax.set_ylabel("score (mean ± std, 5 splits)")
    ax.set_title(f"Model comparison on the real table ({R['dataset']['rows']} start-ups)")
    ax.legend(ncol=3, frameon=False, loc="upper left", fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    save(fig, "f01_model_comparison_real.png")


# ---------------------------------------------------------------- f02
def f02():
    cm = np.array(R["models"]["Random Forest"]["confusion_matrix_mean"])
    fig, ax = plt.subplots(figsize=(4.4, 3.8))
    ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max() * 1.15)
    lab = ["FAILURE", "SUCCESS"]
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i, j]:.1f}", ha="center", va="center", fontsize=14, fontweight="bold",
                    color="white" if cm[i, j] > cm.max() * 0.55 else NAVY)
    ax.set_xticks([0, 1]); ax.set_xticklabels(lab); ax.set_yticks([0, 1]); ax.set_yticklabels(lab)
    ax.set_xlabel("predicted"); ax.set_ylabel("actual")
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title("Random Forest: mean confusion matrix\n(per test fold of 185 start-ups)", fontsize=9.5)
    save(fig, "f02_confusion_matrix_rf.png")


# ---------------------------------------------------------------- f03
def f03():
    sw = R["threshold_sweep_logreg"]
    t = [r["threshold"] for r in sw]
    fig, ax = plt.subplots(figsize=(6.4, 3.7))
    for key, lab, c in (("precision", "Precision", BLUE), ("recall", "Recall (success)", ORANGE), ("f1", "F1", TEAL), ("balanced_accuracy", "Balanced accuracy", PURPLE)):
        ax.plot(t, [r[key] for r in sw], marker="o", ms=3.5, lw=1.8, label=lab, color=c)
    ax.axvline(0.5, color=GREY, ls="--", lw=1)
    ax.text(0.505, 0.27, "default 0.5", color=GREY, fontsize=8)
    ax.set_xlabel("decision threshold on P(success)"); ax.set_ylabel("score (pooled test predictions)")
    ax.set_ylim(0.2, 1.0)
    ax.set_title("Logistic Regression: threshold sweep (real table)")
    ax.legend(ncol=2, frameon=False, fontsize=8, loc="lower left")
    ax.grid(alpha=0.25)
    save(fig, "f03_threshold_sweep.png")


# ---------------------------------------------------------------- f04
def f04():
    fi = R["feature_importance"]
    fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.9))
    for ax, key, title, c in ((axes[0], "random_forest_permutation_auc", "RF permutation\n(drop in ROC-AUC)", TEAL),
                              (axes[1], "random_forest_gini", "RF Gini importance", BLUE),
                              (axes[2], "logistic_abs_coef", "Logistic Regression\n|coefficient|", ORANGE)):
        top = fi[key][:8][::-1]
        ax.barh([d["feature"] for d in top], [d["value"] for d in top], color=c, height=0.7)
        for i, d in enumerate(top):
            ax.text(d["value"], i, f" {d['value']:.3f}", va="center", fontsize=8)
        ax.set_title(title, fontsize=9.5)
        ax.set_xlim(0, max(d["value"] for d in top) * 1.22)
        ax.tick_params(axis="y", labelsize=8.5)
        ax.tick_params(axis="x", labelsize=8)
    fig.suptitle("Top-8 features on the real table", fontsize=11, fontweight="bold", color=NAVY, y=1.02)
    fig.tight_layout()
    save(fig, "f04_feature_importance.png")


# ---------------------------------------------------------------- f05
def f05():
    names = ["Logistic Regression", "Decision Tree", "Random Forest", "XGBoost"]
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.6))
    for ax, key, lab in ((axes[0], "balanced_accuracy", "Balanced accuracy"), (axes[1], "roc_auc", "ROC-AUC")):
        ser = [("Synthetic table (1,400 rows)", [mk(R["synthetic_structured_only"][n], key)[0] for n in names], [mk(R["synthetic_structured_only"][n], key)[1] for n in names]),
               ("Real table (922 rows)", [mk(R["models"][n], key)[0] for n in names], [mk(R["models"][n], key)[1] for n in names])]
        grouped(ax, [SHORT[n] for n in names], ser, [GREY, BLUE], ylim=(0.4, 0.95), fs=7.5)
        ax.set_title(lab); ax.set_ylabel(lab); ax.grid(axis="y", alpha=0.25)
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Same models, structured features only: synthetic vs real data", fontsize=11, fontweight="bold", color=NAVY, y=1.02)
    fig.tight_layout()
    save(fig, "f05_synthetic_vs_real.png")


# ---------------------------------------------------------------- f06
def f06():
    strategies = [("none", "No correction", GREY), ("class_weight", "Class weights", BLUE), ("oversample", "Random oversampling", TEAL)]
    models = ["Logistic Regression", "Random Forest"]
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.6))
    for ax, key, lab in ((axes[0], "balanced_accuracy", "Balanced accuracy"), (axes[1], "recall", "Recall of the success class")):
        ser = [(l, [mk(R["imbalance"][m][s], key)[0] for m in models], [mk(R["imbalance"][m][s], key)[1] for m in models]) for s, l, _ in strategies]
        grouped(ax, [SHORT[m] for m in models], ser, [c for _, _, c in strategies], width=0.75, ylim=(0.5, 1.0))
        ax.set_title(lab); ax.set_ylabel(lab); ax.grid(axis="y", alpha=0.25)
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Class-imbalance handling on the real table (failure is the minority, 35.4 %)", fontsize=10.5, fontweight="bold", color=NAVY, y=1.02)
    fig.tight_layout()
    save(fig, "f06_imbalance_strategies.png")


# ---------------------------------------------------------------- f07
def f07():
    models = ["Logistic Regression", "Random Forest", "XGBoost"]
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.6))
    for ax, key, lab in ((axes[0], "balanced_accuracy", "Balanced accuracy"), (axes[1], "roc_auc", "ROC-AUC")):
        ser = [("All features", [mk(X["with_all_features"][m], key)[0] for m in models], [mk(X["with_all_features"][m], key)[1] for m in models]),
               ("Without post-hoc fields", [mk(X["without_posthoc_features"][m], key)[0] for m in models], [mk(X["without_posthoc_features"][m], key)[1] for m in models])]
        grouped(ax, [SHORT[m] for m in models], ser, [BLUE, ORANGE], ylim=(0.5, 0.9))
        ax.set_title(lab); ax.set_ylabel(lab); ax.grid(axis="y", alpha=0.25)
    axes[0].legend(frameon=False, fontsize=8, loc="upper right")
    fig.suptitle("Dropping relationships, milestones and the two milestone-age fields", fontsize=10.5, fontweight="bold", color=NAVY, y=1.02)
    fig.tight_layout()
    save(fig, "f07_leakage_ablation.png")


# ---------------------------------------------------------------- f08
def f08():
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.6))
    ks = list(S["retrieval_k"].keys())
    kl = [k.split("=")[1] for k in ks]
    ax = axes[0]
    m = [S["retrieval_k"][k]["mean"] for k in ks]; s = [S["retrieval_k"][k]["std"] for k in ks]
    ax.errorbar(kl, m, yerr=s, marker="o", color=ORANGE, lw=2, capsize=3)
    ax.set_ylim(0.55, 0.8); ax.set_xlabel("retrieval size k"); ax.set_ylabel("balanced accuracy")
    ax.set_title("Synthetic table, fused vector", fontsize=9.5); ax.grid(alpha=0.25)
    ax = axes[1]
    rk = X["retrieval_only_structured"]
    m = [rk[k]["balanced_accuracy"]["mean"] for k in rk]; s = [rk[k]["balanced_accuracy"]["std"] for k in rk]
    ax.errorbar(list(rk.keys()), m, yerr=s, marker="o", color=BLUE, lw=2, capsize=3, label="Retrieval vote only")
    ax.axhline(R["models"]["Logistic Regression"]["balanced_accuracy"]["mean"], color=GREY, ls="--", lw=1.2, label="Logistic Regression")
    ax.axhline(R["models"]["Random Forest"]["balanced_accuracy"]["mean"], color=TEAL, ls="--", lw=1.2, label="Random Forest")
    ax.set_ylim(0.55, 0.8); ax.set_xlabel("retrieval size k"); ax.set_ylabel("balanced accuracy")
    ax.set_title("Real table, structured features only", fontsize=9.5); ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.suptitle("Similar-case retrieval vote by number of neighbours", fontsize=11, fontweight="bold", color=NAVY, y=1.02)
    fig.tight_layout()
    save(fig, "f08_retrieval_k.png")


# ---------------------------------------------------------------- f09
def f09():
    rep = S["representations"]
    labels = ["Structured\nonly", "Text only", "Combined\n(fused)"]
    vals = [rep["structured_only"], rep["text_only"], rep["combined"]]
    fig, ax = plt.subplots(figsize=(5.6, 3.7))
    bars = ax.bar(labels, [v["mean"] for v in vals], yerr=[v["std"] for v in vals], capsize=3, color=[BLUE, ORANGE, TEAL], width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v["mean"] + v["std"] + 0.012, f"{v['mean']:.3f}", ha="center", fontsize=9, fontweight="bold")
    ax.set_ylim(0.4, 0.85); ax.set_ylabel("balanced accuracy (Logistic Regression)")
    ax.set_title("Representation study on the shipped synthetic data")
    ax.text(0.5, -0.27, "Caution: the synthetic descriptions are template text that differs between classes,\nso the text channel leaks the label. Not evidence for real data.",
            transform=ax.transAxes, ha="center", va="top", fontsize=8, color=RED)
    ax.grid(axis="y", alpha=0.25)
    save(fig, "f09_representation_study.png")


# ---------------------------------------------------------------- f10
def f10():
    cal = R["calibration_logreg"]
    mp = [c["mean_pred"] for c in cal]; ob = [c["observed"] for c in cal]
    fig, ax = plt.subplots(figsize=(4.9, 4.3))
    ax.plot([0, 1], [0, 1], color=GREY, ls="--", lw=1.2, label="perfect calibration")
    ax.plot(mp, ob, marker="o", color=BLUE, lw=2, label="Logistic Regression (class-weighted)")
    for x, y, c in zip(mp, ob, cal):
        ax.text(x, y + 0.035, f"n={c['n']}", fontsize=6.8, ha="center", color=NAVY)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.08)
    ax.set_xlabel("mean predicted P(success)"); ax.set_ylabel("observed success rate")
    ax.set_title("Reliability of the predicted probability\n(real table, pooled test predictions)", fontsize=9.5)
    ax.legend(frameon=False, fontsize=8, loc="lower right"); ax.grid(alpha=0.25)
    save(fig, "f10_calibration.png")


# ---------------------------------------------------------------- f11
def f11():
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    rows = [("Panjwani et al. [1]: best ensembles, accuracy\n(dataset not stated)", 0.85, 0.92, "range", GREY),
            ("Maarouf [2]: kNN-ICL, k=50", 0.713, None, "bal", ORANGE),
            ("Maarouf [2]: fused LLM", 0.743, None, "bal", ORANGE),
            ("Maarouf [2]: Random Forest", 0.634, None, "bal", ORANGE),
            ("Maarouf [2]: Logistic Regression", 0.631, None, "bal", ORANGE),
            ("Maarouf [2]: XGBoost", 0.618, None, "bal", ORANGE),
            ("This project: XGBoost, accuracy", R["models"]["XGBoost"]["accuracy"]["mean"], None, "acc", BLUE),
            ("This project: Random Forest, balanced accuracy", R["models"]["Random Forest"]["balanced_accuracy"]["mean"], None, "bal", BLUE),
            ("This project: XGBoost, balanced accuracy", R["models"]["XGBoost"]["balanced_accuracy"]["mean"], None, "bal", BLUE)]
    rows = rows[::-1]
    for i, (lab, a, b, kind, c) in enumerate(rows):
        if kind == "range":
            ax.barh(i, b - a, left=a, color=c, height=0.6, hatch="//", edgecolor="white")
            ax.text(b + 0.005, i, "0.85-0.92", va="center", fontsize=9)
        else:
            ax.barh(i, a, color=c, height=0.6)
            ax.text(a + 0.005, i, f"{a:.3f}", va="center", fontsize=9)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=9)
    ax.set_xlim(0.5, 0.99); ax.set_xlabel("reported score (accuracy or balanced accuracy, as labelled)")
    ax.text(0, 1.01, "Different datasets and protocols - not comparable one-to-one. Orange: [2] balanced accuracy (4,034 start-ups; fused LLM trained on 20,172).", transform=ax.transAxes, fontsize=7.6, style="italic", color=RED, va="bottom", ha="left")
    ax.grid(axis="x", alpha=0.25)
    fig.subplots_adjust(top=0.86)
    ax.set_title("Reported figures of the papers and of this project", loc="left", pad=16)
    save(fig, "f11_vs_base_papers.png")


# ---------------------------------------------------------------- f12
def f12():
    eps = [("health", "GET /api/health"), ("model_metrics", "GET /api/model-metrics"), ("insights", "GET /api/insights"),
           ("predict_k10", "POST /predict (k=10)"), ("predict_k50", "POST /predict (k=50)")]
    fig, ax = plt.subplots(figsize=(7.0, 3.5))
    y = np.arange(len(eps))[::-1]
    med = [LAT[k]["median_ms"] for k, _ in eps]; p95 = [LAT[k]["p95_ms"] for k, _ in eps]
    ax.barh(y + 0.19, med, 0.36, color=BLUE, label="median")
    ax.barh(y - 0.19, p95, 0.36, color=ORANGE, label="95th percentile")
    for yy, a, b in zip(y, med, p95):
        ax.text(a + 6, yy + 0.19, f"{a:.1f} ms", va="center", fontsize=7.5)
        ax.text(b + 6, yy - 0.19, f"{b:.1f} ms", va="center", fontsize=7.5)
    ax.set_yticks(y); ax.set_yticklabels([l for _, l in eps], fontsize=8.5)
    ax.set_xlabel("latency (ms), 127.0.0.1, warm model, CPU"); ax.set_xlim(0, max(p95) * 1.18)
    ax.set_title("API latency"); ax.legend(frameon=False, fontsize=8, loc="upper right"); ax.grid(axis="x", alpha=0.25)
    save(fig, "f12_latency.png")


# ---------------------------------------------------------------- f13
def f13():
    d = R["dataset"]
    syn = S["metadata"]["class_counts"] if "class_counts" in S["metadata"] else None
    meta = json.load(open(ROOT / "models" / "metadata.json", encoding="utf-8"))
    syn = meta["class_counts"]
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    labs = [f"Shipped synthetic table\n({syn['SUCCESS'] + syn['FAILURE']:,} rows)", f"Real public table\n({d['rows']} rows)"]
    succ = [syn["SUCCESS"], d["success"]]; fail = [syn["FAILURE"], d["failure"]]
    y = [1, 0]
    ax.barh(y, succ, color=TEAL, height=0.5, label="SUCCESS")
    ax.barh(y, fail, left=succ, color=RED, height=0.5, label="FAILURE")
    for yy, s, f in zip(y, succ, fail):
        ax.text(s / 2, yy, f"{s}  ({s / (s + f) * 100:.1f} %)", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        ax.text(s + f / 2, yy, f"{f}  ({f / (s + f) * 100:.1f} %)", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=8.5)
    ax.set_xlabel("start-ups"); ax.set_title("Class balance of the two tables")
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.22))
    save(fig, "f13_class_balance.png")


if __name__ == "__main__":
    for fn in (f01, f02, f03, f04, f05, f06, f07, f08, f09, f10, f11, f12, f13):
        fn()
