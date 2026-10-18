"""Compact figures for the two-column IEEE paper (3.45 in wide, >= 6.2 pt text, 300 dpi).

    python scripts/make_paper_figures.py      -> docs/figures/paper_architecture.png, paper_flow.png

The full-size diagrams in docs/diagrams/ are drawn for the report; at a 3.4 in column their text would be unreadable,
so these two are simplified redraws of the same architecture and the same pipeline.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "figures")
NAVY, INK, SLATE = "#1B2A41", "#0F172A", "#475569"
BLUE, GREEN, ORANGE, PURPLE, GOLD = "#2A78D6", "#1BAF7A", "#EB6834", "#6B52D6", "#E8A317"
plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]


def box(ax, x, y, w, h, text, ec, fc="white", fs=6.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=ec, lw=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK, fontweight="bold" if bold else "normal", linespacing=1.2)


def arrow(ax, p, q, color=SLATE):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=color, lw=0.9, shrinkA=0, shrinkB=0, mutation_scale=7))


def architecture():
    fig, ax = plt.subplots(figsize=(3.45, 2.75))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 80)
    ax.axis("off")
    rows = [(60, "Presentation"), (41, "API (FastAPI, port 8314)"), (22, "Core package src/ (pure Python)"), (3, "Data and state")]
    for y, lab in rows:
        ax.add_patch(FancyBboxPatch((0.5, y), 99, 17, boxstyle="round,pad=0,rounding_size=1", fc="#F6F8FB", ec="#D5DCE6", lw=0.8))
        ax.text(2, y + 15.0, lab, fontsize=6.3, color=SLATE, fontweight="bold", va="center")
    box(ax, 4, 62, 44, 9.0, "React 19 SPA ChurnIQ\n(13 pages, port 5314)", BLUE, "#E8F0FC")
    box(ax, 52, 62, 44, 9.0, "Streamlit UI (13 pages)\nsame src/ core", ORANGE, "#FFF1EA")
    box(ax, 4, 43, 29, 9.0, "bearer token\nHMAC, 12 h expiry", GREEN, "#E6F6EF")
    box(ax, 36, 43, 29, 9.0, "31 routes\n401/404/409/422", GREEN, "#E6F6EF")
    box(ax, 68, 43, 28, 9.0, "AppState\n(in memory)", GREEN, "#E6F6EF")
    box(ax, 2, 24, 23, 9.0, "data_loader\npreprocessing", NAVY)
    box(ax, 26.3, 24, 23, 9.0, "train_models\nevaluation", NAVY)
    box(ax, 50.6, 24, 23, 9.0, "risk_segment.\nprediction", NAVY)
    box(ax, 74.9, 24, 23.1, 9.0, "explainability\nretention_engine", NAVY)
    box(ax, 4, 5, 28, 9.0, "customer CSV\n(1,000 rows)", GOLD, "#FFF8E5")
    box(ax, 36, 5, 28, 9.0, "models/*.pkl\n(joblib)", GOLD, "#FFF8E5")
    box(ax, 68, 5, 28, 9.0, "session state\n(no SQL DB)", GOLD, "#FFF8E5")
    arrow(ax, (62, 62), (62, 52))
    arrow(ax, (62, 43), (62, 33))
    arrow(ax, (62, 24), (62, 14))
    fig.savefig(os.path.join(OUT, "paper_architecture.png"), dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.02)
    plt.close(fig)


def flow():
    fig, ax = plt.subplots(figsize=(3.45, 2.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(-7, 84)
    ax.axis("off")
    left = [("1  Load, validate; detect\ntarget and ID columns", BLUE), ("2  Stratified split\n80 / 20, seed 42", BLUE),
            ("3  Fit preprocessor on\nthe training split only", PURPLE), ("4  Imbalance: class weights,\nSMOTE (train only), none", PURPLE)]
    right = [("5  Train LR, DT, RF\n(optional GB, HGB)", GREEN), ("6  Evaluate on test split;\nselect best model (F1)", GREEN),
             ("7  Score, risk band\n(30 / 60 / 80)", ORANGE), ("8  Drivers, what-if and\nrule-based actions", ORANGE)]
    w, h, gap = 43, 15, 6
    ys = [66 - i * 21 for i in range(4)]
    for i in range(4):
        box(ax, 1, ys[i], w, h, left[i][0], left[i][1], "white", 6.3)
        box(ax, 100 - 1 - w, ys[i], w, h, right[i][0], right[i][1], "white", 6.3)
        if i < 3:
            arrow(ax, (1 + w / 2, ys[i]), (1 + w / 2, ys[i + 1] + h))
            arrow(ax, (100 - 1 - w / 2, ys[i]), (100 - 1 - w / 2, ys[i + 1] + h))
    xm = 1 + w + gap / 2
    ax.plot([1 + w, xm, xm], [ys[3] + h / 2, ys[3] + h / 2, ys[0] + h / 2], color=SLATE, lw=0.9)
    arrow(ax, (xm, ys[0] + h / 2), (100 - 1 - w, ys[0] + h / 2))
    ax.text(50, -3.5, "Invalid data stop at step 1 (HTTP 422); retention rules fire only at P >= 60 %.", ha="center", fontsize=6.2, color=SLATE, style="italic")
    fig.savefig(os.path.join(OUT, "paper_flow.png"), dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.02)
    plt.close(fig)


def results_panels():
    import json

    ex = json.load(open(os.path.join(ROOT, "experiments", "churn_synthetic", "extra_analysis.json"), encoding="utf8"))
    m = json.load(open(os.path.join(ROOT, "experiments", "churn_synthetic", "metrics.json"), encoding="utf8"))
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})
    # stability: F1 by protocol
    fig, ax = plt.subplots(figsize=(3.45, 1.9))
    models = ["Logistic Regression", "Decision Tree", "Random Forest"]
    w = 0.26
    for i, (lab, col) in enumerate((("single split", "#94A3B8"), ("5-fold CV", BLUE), ("5 splits", ORANGE))):
        means, sds = [], []
        for n in models:
            if i == 0:
                means.append(m["app_default_split"]["class_weight"]["models"][n]["f1_score"])
                sds.append(0)
            else:
                d = (m["cross_validation_5fold_class_weight"] if i == 1 else m["repeated_random_splits_5_seeds_class_weight"])[n]["f1_score"]
                means.append(d["mean"])
                sds.append(d["std"])
        xs = [j + (i - 1) * w for j in range(3)]
        ax.bar(xs, means, w, yerr=sds, capsize=2, color=col, label=lab, ecolor=NAVY, error_kw={"lw": 0.8})
        for x, v in zip(xs, means):
            ax.text(x, 0.015, f"{v:.2f}", ha="center", fontsize=6.3, color="white", fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels(["LR", "DT", "RF"], fontsize=7)
    ax.tick_params(axis="y", labelsize=6.5)
    ax.set_ylim(0, 0.68)
    ax.set_ylabel("F1-score (bar: 1 sd)", fontsize=6.5)
    ax.legend(frameon=False, fontsize=6.3, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.14))
    fig.savefig(os.path.join(OUT, "paper_stability.png"), dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.02)
    plt.close(fig)
    # threshold sweep + reliability
    fig, axs = plt.subplots(1, 2, figsize=(3.45, 1.85))
    sw = ex["threshold_sweep"]
    ts = [s_["threshold"] for s_ in sw]
    for key, col, lab in (("precision", BLUE, "Precision"), ("recall", ORANGE, "Recall"), ("f1", GREEN, "F1")):
        axs[0].plot(ts, [s_[key] for s_ in sw], color=col, lw=1.2, label=lab)
    axs[0].axvline(0.5, ls="--", color="#94A3B8", lw=0.8)
    axs[0].set_xlabel("Decision threshold", fontsize=6.5)
    axs[0].legend(frameon=False, fontsize=6.2, loc="upper right")
    rel = ex["reliability"]
    axs[1].plot([0, 1], [0, 1], "--", color="#94A3B8", lw=0.8)
    axs[1].plot([r["mean_predicted"] for r in rel], [r["observed_churn"] for r in rel], "o-", color=BLUE, lw=1.2, ms=3)
    axs[1].set_xlabel("Mean predicted probability", fontsize=6.5)
    axs[1].set_ylabel("Observed churn rate", fontsize=6.5)
    for a in axs:
        a.tick_params(labelsize=6.3)
    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(OUT, "paper_threshold_calibration.png"), dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.02)
    plt.close(fig)


if __name__ == "__main__":
    architecture()
    flow()
    results_panels()
    print("wrote paper_architecture.png, paper_flow.png, paper_stability.png, paper_threshold_calibration.png")
