"""Result charts for the documents, drawn from docs/experiments/*.json and models/training_report.json.

    python scripts/make_figures.py        ->  docs/figures/*.png (150 dpi)
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "docs", "experiments")
OUT = os.path.join(ROOT, "docs", "figures")
os.makedirs(OUT, exist_ok=True)
X = json.load(open(os.path.join(EXP, "results.json")))
R = json.load(open(os.path.join(EXP, "real_data_results.json")))
REP = json.load(open(os.path.join(ROOT, "models", "training_report.json")))

DIS = ["diabetes", "heart", "liver", "kidney"]
NAME = {"diabetes": "Diabetes", "heart": "Heart disease", "liver": "Liver disease", "kidney": "Kidney disease"}
MODELS = ["Logistic Regression", "Decision Tree", "Random Forest", "SVM"]
COL = {"Logistic Regression": "#2A78D6", "Decision Tree": "#E8A317", "Random Forest": "#1BAF7A", "SVM": "#6B52D6"}
INK, SLATE = "#0F172A", "#475569"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#9AA8BD", "axes.titleweight": "bold", "axes.titlesize": 10})


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


def model_comparison():
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 6.6), sharey=True)
    metrics = ["accuracy", "precision", "recall", "f1"]
    for ax, d in zip(axes.flat, DIS):
        w = 0.2
        for i, m in enumerate(MODELS):
            vals = [REP[d]["all_results"][m][k] for k in metrics]
            bars = ax.bar(np.arange(4) + (i - 1.5) * w, vals, w, color=COL[m], label=m)
            if m == REP[d]["best_model"]:
                for b in bars:
                    b.set_edgecolor(INK)
                    b.set_linewidth(1.4)
        ax.axhline(0.92, color="#C0392B", ls="--", lw=1)
        ax.set_xticks(range(4))
        ax.set_xticklabels(["Accuracy", "Precision", "Recall", "F1"])
        ax.set_ylim(0.6, 1.0)
        ax.set_title(f"{NAME[d]} (selected: {REP[d]['best_model']})")
        ax.grid(axis="y", color="#E5E9F0", lw=0.6)
        ax.set_axisbelow(True)
    axes[0, 0].text(3.45, 0.925, "noise ceiling 0.92", color="#C0392B", fontsize=7.5, ha="right")
    from matplotlib.patches import Patch
    h, l = [Patch(color=COL[m]) for m in MODELS], MODELS
    fig.legend(h, l, ncol=4, loc="lower center", frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Hold-out metrics of the four algorithms (400-row test set, outlined bar = model served by the app)", fontweight="bold", fontsize=10.5)
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    save(fig, "model_comparison.png")


def roc_curves():
    fig, axes = plt.subplots(2, 2, figsize=(8, 7))
    for ax, d in zip(axes.flat, DIS):
        for m in MODELS:
            c = X[d]["roc_all"][m]
            ax.plot(c["fpr"], c["tpr"], color=COL[m], lw=1.6, label=f"{m} (AUC {X[d]['holdout'][m]['roc_auc']:.3f})")
        ax.plot([0, 1], [0, 1], color="#9AA8BD", ls="--", lw=1)
        ax.set_title(NAME[d])
        ax.set_xlabel("False positive rate")
        ax.set_ylabel("True positive rate")
        ax.legend(fontsize=7, loc="lower right", frameon=False)
        ax.grid(color="#E5E9F0", lw=0.6)
    fig.tight_layout()
    save(fig, "roc_curves.png")


def confusion():
    fig, axes = plt.subplots(1, 4, figsize=(11, 2.9))
    for ax, d in zip(axes, DIS):
        cm = np.array(X[d]["confusion"][REP[d]["best_model"]])
        ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max() * 1.1)
        for (i, j), v in np.ndenumerate(cm):
            ax.text(j, i, str(v), ha="center", va="center", fontsize=13, fontweight="bold", color="white" if v > cm.max() * 0.55 else INK)
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["Low risk", "High risk"])
        ax.set_yticklabels(["Low risk", "High risk"])
        ax.set_xlabel("Predicted")
        if d == "diabetes":
            ax.set_ylabel("Actual label")
        ax.set_title(f"{NAME[d]}\n{REP[d]['best_model']}", fontsize=9)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.tight_layout()
    save(fig, "confusion_matrices.png")


def threshold():
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.2), sharey=True)
    for ax, d in zip(axes, DIS):
        sw = X[d]["threshold_sweep"]
        t = [s["threshold"] for s in sw]
        for k, c, lab in (("precision", "#2A78D6", "Precision"), ("recall", "#E8A317", "Recall"), ("f1", "#1BAF7A", "F1")):
            ax.plot(t, [s[k] for s in sw], color=c, lw=1.8, label=lab)
        ax.axvline(0.5, color="#9AA8BD", ls="--", lw=1)
        ax.set_title(f"{NAME[d]}")
        ax.set_xlabel("Decision threshold")
        ax.grid(color="#E5E9F0", lw=0.6)
    axes[0].set_ylabel("Score")
    axes[0].legend(fontsize=7.5, frameon=False, loc="lower left")
    fig.tight_layout()
    save(fig, "threshold_sweep.png")


def importance():
    fig, axes = plt.subplots(2, 2, figsize=(9, 6.2))
    for ax, d in zip(axes.flat, DIS):
        pi = X[d]["perm_importance"][:6][::-1]
        ax.barh([p["feature"] for p in pi], [p["mean"] for p in pi], xerr=[p["std"] for p in pi], color="#2A78D6", ecolor="#475569", capsize=2)
        ax.set_title(f"{NAME[d]} ({REP[d]['best_model']})")
        ax.set_xlabel("Drop in test accuracy when the feature is shuffled")
        ax.grid(axis="x", color="#E5E9F0", lw=0.6)
        ax.tick_params(axis="y", labelsize=8)
    fig.tight_layout()
    save(fig, "importance.png")


def stability():
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.4), sharey=True)
    for ax, d in zip(axes, DIS):
        for i, m in enumerate(MODELS):
            x0 = i
            ax.errorbar(x0 - 0.12, X[d]["cv5"][m]["accuracy_mean"], yerr=X[d]["cv5"][m]["accuracy_std"], fmt="s", color=COL[m], capsize=3, ms=5)
            ax.errorbar(x0 + 0.12, X[d]["seed_study"][m]["accuracy_mean"], yerr=X[d]["seed_study"][m]["accuracy_std"], fmt="^", color=COL[m], capsize=3, ms=5, mfc="white")
            ax.plot(x0, X[d]["holdout"][m]["accuracy"], "o", color=INK, ms=4)
        ax.set_xticks(range(4))
        ax.set_xticklabels(["LR", "DT", "RF", "SVM"])
        ax.set_title(NAME[d])
        ax.grid(axis="y", color="#E5E9F0", lw=0.6)
        ax.axhline(0.92, color="#C0392B", ls="--", lw=1)
    axes[0].set_ylabel("Accuracy")
    from matplotlib.lines import Line2D
    fig.legend([Line2D([], [], marker="o", color=INK, ls="", ms=4), Line2D([], [], marker="s", color=SLATE, ls="", ms=5),
                Line2D([], [], marker="^", mfc="white", color=SLATE, ls="", ms=5)],
               ["seed-42 hold-out", "5-fold CV (mean, sd)", "10 random splits (mean, sd)"], ncol=3, loc="lower center", frameon=False, bbox_to_anchor=(0.5, -0.08))
    fig.tight_layout()
    save(fig, "stability.png")


def real_vs_synth():
    fig, ax = plt.subplots(figsize=(9, 3.8))
    x = np.arange(4)
    series = [
        ("Synthetic data, 5-fold CV (best algorithm)", [max(X[d]["cv5"][m]["accuracy_mean"] for m in MODELS) for d in DIS], "#2A78D6"),
        ("Real public data, 5x3 CV (best algorithm)", [max(R[d]["real_cv"][m]["accuracy_mean"] for m in MODELS) for d in DIS], "#1BAF7A"),
        ("Shipped model applied to real records", [R[d]["shipped_on_real"]["accuracy"] for d in DIS], "#E8A317"),
        ("Majority-class baseline on real data", [R[d]["majority_rate"] for d in DIS], "#9AA8BD"),
    ]
    w = 0.2
    for i, (lab, vals, c) in enumerate(series):
        bars = ax.bar(x + (i - 1.5) * w, vals, w, color=c, label=lab)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.008, f"{v*100:.0f}", ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([NAME[d] for d in DIS])
    ax.set_ylim(0.4, 1.05)
    ax.set_ylabel("Accuracy")
    ax.legend(fontsize=7.5, frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    ax.grid(axis="y", color="#E5E9F0", lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "real_vs_synthetic.png")


def sensitivity():
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.3), sharey=True)
    cols = {"diabetes": "#2A78D6", "heart": "#E8A317", "liver": "#1BAF7A", "kidney": "#6B52D6"}
    for ax, key, title, xl in ((axes[0], "dt_depth", "Decision tree", "max_depth"), (axes[1], "rf_trees", "Random forest (depth 8)", "n_estimators"),
                               (axes[2], "svm_C", "SVM (RBF)", "C")):
        for d in DIS:
            s = X[d]["sensitivity"][key]
            ks = list(s)
            ax.plot(range(len(ks)), [s[k] for k in ks], marker="o", ms=4, color=cols[d], label=NAME[d])
            ax.set_xticks(range(len(ks)))
            ax.set_xticklabels(ks)
        ax.set_title(title)
        ax.set_xlabel(xl)
        ax.grid(color="#E5E9F0", lw=0.6)
    axes[0].set_ylabel("Test accuracy")
    axes[2].legend(fontsize=7.5, frameon=False)
    fig.tight_layout()
    save(fig, "sensitivity.png")


def gap():
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.2), sharey=True)
    for ax, d in zip(axes, DIS):
        x = np.arange(4)
        ax.bar(x - 0.18, [X[d]["train_accuracy"][m] for m in MODELS], 0.36, color="#9AA8BD", label="train")
        ax.bar(x + 0.18, [X[d]["holdout"][m]["accuracy"] for m in MODELS], 0.36, color=[COL[m] for m in MODELS], label="test")
        ax.set_xticks(x)
        ax.set_xticklabels(["LR", "DT", "RF", "SVM"])
        ax.set_ylim(0.7, 1.0)
        ax.set_title(NAME[d])
        ax.grid(axis="y", color="#E5E9F0", lw=0.6)
    axes[0].set_ylabel("Accuracy")
    axes[0].legend(fontsize=7.5, frameon=False, loc="lower left")
    fig.tight_layout()
    save(fig, "train_test_gap.png")


def latency():
    A = json.load(open(os.path.join(EXP, "api_tests.json")))["latency"]
    labs = [k for k in A if "concurrent" not in k]
    fig, ax = plt.subplots(figsize=(7.5, 3))
    y = np.arange(len(labs))
    ax.barh(y - 0.18, [A[k]["p50_ms"] for k in labs], 0.36, color="#2A78D6", label="median")
    ax.barh(y + 0.18, [A[k]["p95_ms"] for k in labs], 0.36, color="#E8A317", label="95th percentile")
    ax.set_yticks(y)
    ax.set_yticklabels(labs, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Latency (ms), 200 calls on 127.0.0.1")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="x", color="#E5E9F0", lw=0.6)
    fig.tight_layout()
    save(fig, "api_latency.png")


if __name__ == "__main__":
    for f in (model_comparison, roc_curves, confusion, threshold, importance, stability, real_vs_synth, sensitivity, gap, latency):
        f()
