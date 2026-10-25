"""Compact figures for the two-column IEEE paper (3.45 in wide, >= 6 pt text, 300 dpi).

    python scripts/make_paper_figures.py
      -> docs/figures/paper_architecture.png, paper_flow.png, paper_results.png, paper_screen_predict.png, paper_screen_models.png

The full-size diagrams in docs/diagrams/ are drawn for the report; at a 3.4 in column their text would be too small,
so the architecture and the main flow are simplified redraws of the same design. Fig. 3 is drawn from docs/experiments/*.json.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "figures")
SHOTS = os.path.join(ROOT, "docs", "screenshots")
NAVY, INK, SLATE = "#1B2A41", "#0F172A", "#475569"
BLUE, GREEN, ORANGE, PURPLE, GOLD = "#2A78D6", "#1BAF7A", "#EB6834", "#6B52D6", "#E8A317"
plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]


def box(ax, x, y, w, h, text, ec, fc="white", fs=6.3, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=ec, lw=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK, fontweight="bold" if bold else "normal", linespacing=1.2)


def arrow(ax, p, q, color=SLATE):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=color, lw=0.9, shrinkA=0, shrinkB=0, mutation_scale=7))


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.02)
    plt.close(fig)
    print("wrote", name)


def architecture():
    fig, ax = plt.subplots(figsize=(3.45, 2.85))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 84)
    ax.axis("off")
    rows = [(63, "Presentation"), (43, "Service (FastAPI, port 8303)"), (23, "Training and model files"), (3, "Data")]
    for y, lab in rows:
        ax.add_patch(FancyBboxPatch((0.5, y), 99, 18, boxstyle="round,pad=0,rounding_size=1", fc="#F6F8FB", ec="#D5DCE6", lw=0.8))
        ax.text(2, y + 15.6, lab, fontsize=6.0, color=SLATE, fontweight="bold", va="center")
    box(ax, 4, 65, 44, 9.5, "React 19 + Vite (port 5303)\nLanding, Predict x4,\nModels, Datasets", BLUE, "#E8F0FC", fs=5.9)
    box(ax, 52, 65, 44, 9.5, "Original Flask pages\n(port 5000), same models", ORANGE, "#FFF1EA", fs=5.9)
    box(ax, 4, 45, 44, 9.5, "backend/main.py: 7 routes\n422 / 404 errors, CORS", GREEN, "#E6F6EF", fs=5.9)
    box(ax, 52, 45, 44, 9.5, "app.py: BUNDLES\n(model, scaler, features)", GREEN, "#E6F6EF", fs=5.9)
    box(ax, 4, 25, 44, 9.5, "train_models.py: scale, fit 4\nalgorithms, best by F1", NAVY, fs=5.9)
    box(ax, 52, 25, 44, 9.5, "models/*.pkl (joblib)\ntraining_report.json", GOLD, "#FFF8E5", fs=5.9)
    box(ax, 4, 5, 44, 9.5, "generate_data.py\nseed 42, 8% label flips", NAVY, fs=5.9)
    box(ax, 52, 5, 44, 9.5, "data/*.csv: 4 x 2,000\nsynthetic rows", GOLD, "#FFF8E5", fs=5.9)
    arrow(ax, (42, 64.5), (42, 54.5))
    arrow(ax, (50, 50), (52, 50))
    arrow(ax, (74, 34.5), (74, 45))
    arrow(ax, (50, 30), (52, 30))
    arrow(ax, (26, 14.5), (26, 25))
    arrow(ax, (50, 10), (52, 10))
    save(fig, "paper_architecture.png")


def flow():
    fig, ax = plt.subplots(figsize=(3.45, 2.65))
    ax.set_xlim(0, 100)
    ax.set_ylim(-7, 84)
    ax.axis("off")
    left = [("1  Choose disease; type values\nor load a real CSV row", BLUE), ("2  Browser check: required,\nnumeric, training-range hint", BLUE),
            ("3  POST /api/predict/{d}\nJSON of feature values", PURPLE), ("4  Unknown disease: 404;\nmissing / non-finite: 422", PURPLE)]
    right = [("5  StandardScaler\n(fitted on training part)", GREEN), ("6  model.predict and\nmax predict_proba", GREEN),
             ("7  JSON: class, confidence,\nmodel, hold-out accuracy", ORANGE), ("8  Result card: High / Low\nrisk + notice", ORANGE)]
    w, h, gap = 43, 15, 6
    ys = [66 - i * 21 for i in range(4)]
    for i in range(4):
        box(ax, 1, ys[i], w, h, left[i][0], left[i][1], "white", 6.0)
        box(ax, 100 - 1 - w, ys[i], w, h, right[i][0], right[i][1], "white", 6.0)
        if i < 3:
            arrow(ax, (1 + w / 2, ys[i]), (1 + w / 2, ys[i + 1] + h))
            arrow(ax, (100 - 1 - w / 2, ys[i]), (100 - 1 - w / 2, ys[i + 1] + h))
    xm = 1 + w + gap / 2
    ax.plot([1 + w, xm, xm], [ys[3] + h / 2, ys[3] + h / 2, ys[0] + h / 2], color=SLATE, lw=0.9)
    arrow(ax, (xm, ys[0] + h / 2), (100 - 1 - w, ys[0] + h / 2))
    ax.text(50, -3.5, "Nothing is stored: each request is answered from the loaded model files.", ha="center", fontsize=5.8, color=SLATE, style="italic")
    save(fig, "paper_flow.png")


def results():
    X = json.load(open(os.path.join(ROOT, "docs", "experiments", "results.json")))
    R = json.load(open(os.path.join(ROOT, "docs", "experiments", "real_data_results.json")))
    REP = json.load(open(os.path.join(ROOT, "models", "training_report.json")))
    dis = ["diabetes", "heart", "liver", "kidney"]
    models = ["Logistic Regression", "Decision Tree", "Random Forest", "SVM"]
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(3.45, 2.2))
    series = [
        ("Synthetic hold-out (served model)", [REP[d]["all_results"][REP[d]["best_model"]]["accuracy"] for d in dis], BLUE),
        ("Real data, cross-validated (best algorithm)", [max(R[d]["real_cv"][m]["accuracy_mean"] for m in models) for d in dis], GREEN),
        ("Served model on real records", [R[d]["shipped_on_real"]["accuracy"] for d in dis], GOLD),
        ("Majority-class baseline, real data", [R[d]["majority_rate"] for d in dis], "#94A3B8"),
    ]
    w = 0.2
    x = np.arange(4)
    for i, (lab, vals, c) in enumerate(series):
        bars = ax.bar(x + (i - 1.5) * w, vals, w, color=c, label=lab)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v*100:.0f}", ha="center", fontsize=5.3)
    ax.set_xticks(x)
    ax.set_xticklabels(["Diabetes", "Heart", "Liver", "Kidney"], fontsize=6.5)
    ax.set_ylim(0.4, 1.2)
    ax.set_yticks([0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_ylabel("Accuracy", fontsize=6.5)
    ax.tick_params(axis="y", labelsize=6)
    ax.legend(frameon=False, fontsize=5.4, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.02), columnspacing=0.8, handlelength=1.2)
    save(fig, "paper_results.png")


def stability():
    X = json.load(open(os.path.join(ROOT, "docs", "experiments", "results.json")))
    dis = ["diabetes", "heart", "liver", "kidney"]
    models = ["Logistic Regression", "Decision Tree", "Random Forest", "SVM"]
    col = {"Logistic Regression": BLUE, "Decision Tree": GOLD, "Random Forest": GREEN, "SVM": PURPLE}
    short = {"Logistic Regression": "LR", "Decision Tree": "DT", "Random Forest": "RF", "SVM": "SVM"}
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(3.45, 2.0))
    for j, m in enumerate(models):
        xs = np.arange(4) + (j - 1.5) * 0.17
        ax.errorbar(xs, [X[d]["seed_study"][m]["accuracy_mean"] for d in dis], yerr=[X[d]["seed_study"][m]["accuracy_std"] for d in dis],
                    fmt="o", color=col[m], capsize=2, ms=3.5, lw=0.9, label=short[m])
        ax.plot(xs, [X[d]["holdout"][m]["accuracy"] for d in dis], "x", color=col[m], ms=4, mew=0.9)
    ax.axhline(0.92, color="#C0392B", ls="--", lw=0.8)
    ax.text(3.45, 0.925, "noise ceiling 0.92", fontsize=5.5, color="#C0392B", ha="right")
    ax.set_xticks(range(4))
    ax.set_xticklabels(["Diabetes", "Heart", "Liver", "Kidney"], fontsize=6.5)
    ax.set_ylabel("Test accuracy", fontsize=6.5)
    ax.set_ylim(0.70, 0.95)
    ax.tick_params(axis="y", labelsize=6)
    ax.legend(frameon=False, fontsize=5.8, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.38), handlelength=1)
    save(fig, "paper_stability.png")


def screens():
    a = Image.open(os.path.join(SHOTS, "05_predict-diabetes.png")).convert("RGB").crop((276, 290, 1412, 700))
    a.save(os.path.join(OUT, "paper_screen_predict.png"))
    b = Image.open(os.path.join(SHOTS, "09_models.png")).convert("RGB").crop((276, 315, 1412, 735))
    b.save(os.path.join(OUT, "paper_screen_models.png"))
    print("wrote screens")


if __name__ == "__main__":
    architecture()
    flow()
    results()
    stability()
    screens()
