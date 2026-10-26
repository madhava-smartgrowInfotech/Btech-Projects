"""Compact figures for the two-column IEEE paper -> docs/figures/paper_*.png (drawn at column width so text stays legible).

Self-contained: only matplotlib and the experiments JSON read through facts.py. Output screens reuse the real screenshots.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

from . import facts as F

NAVY, BLUE, TEAL, ORANGE, GREY, RED, INK = "#1F3A5F", "#2E6FB7", "#1F8A8A", "#E07B26", "#8A97A8", "#C0392B", "#1B2733"
PALE = {BLUE: "#E4EEF9", TEAL: "#DFF1F1", ORANGE: "#FBEBDD", NAVY: "#E3E8F0"}


def _save(fig, name):
    os.makedirs(F.FIGS, exist_ok=True)
    p = os.path.join(F.FIGS, name)
    fig.savefig(p, dpi=220, facecolor="white")
    plt.close(fig)
    return p


def _canvas(w_in, h_in, w, h):
    fig = plt.figure(figsize=(w_in, h_in))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def _box(ax, cx, cy, w, h, text, color=BLUE, fs=5.4, fill=None, tc=INK, bold=False):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0.0,rounding_size=1.2", fc=fill or PALE[color], ec=color, lw=0.8))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal", linespacing=1.15)


def _arrow(ax, p, q, color=NAVY):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=6, lw=0.9, color=color, shrinkA=0, shrinkB=0))


def arch():
    fig, ax = _canvas(3.5, 2.7, 100, 77)
    ax.text(1, 74, "Browser", fontsize=5.6, color=BLUE, fontweight="bold")
    _box(ax, 50, 67, 96, 10, "React 19 + Vite app (port 5307): 6 screens\n(landing, sign-in, new patient, result, queue, performance)", BLUE, fs=5.0)
    _arrow(ax, (50, 62.5), (50, 58.5))
    ax.text(1, 59.5, "API", fontsize=5.6, color=TEAL, fontweight="bold")
    _box(ax, 50, 52, 96, 10, "FastAPI (port 8307): 13 JSON endpoints under /api, JWT bearer auth,\npydantic range checks, 15 MB upload cap", TEAL, fs=5.0)
    _arrow(ax, (50, 46.5), (50, 42.5))
    ax.text(1, 43.5, "Services", fontsize=5.6, color=ORANGE, fontweight="bold")
    xs = [13.5, 38, 62.5, 87]
    labels = ["extract.py\nPDF text or OCR,\nlexicon, negation,\n6 lab ranges", "features.py\n8 vitals + 28 flags\n= 36 inputs", "triage.py\nXGBoost, isotonic\ncalibration, SHAP", "pdf.py\ntriage summary\n(ReportLab)"]
    for x, t in zip(xs, labels):
        _box(ax, x, 32, 23, 17, t, ORANGE, fs=4.7)
    _arrow(ax, (50, 22.5), (50, 18.5))
    ax.text(1, 19.5, "Storage", fontsize=5.6, color=NAVY, fontweight="bold")
    _box(ax, 27, 10, 46, 13, "SQLite (SQLAlchemy)\nusers, patients, overrides", NAVY, fs=5.0)
    _box(ax, 75, 10, 46, 13, "Files: models/triage_model.joblib,\nexperiments/*.json, sample reports", NAVY, fs=5.0)
    return _save(fig, "paper_arch.png")


def flow():
    fig, ax = _canvas(3.5, 2.55, 100, 73)
    row1 = [("Upload\nPDF / scan", BLUE), ("Read pages\nPDF text,\nelse OCR", BLUE), ("Parse\nlexicon,\nnegation, labs", BLUE), ("Vitals\n(8 fields)", TEAL)]
    xs = [12.5, 37.5, 62.5, 87.5]
    for x, (t, c) in zip(xs, row1):
        _box(ax, x, 60, 21, 17, t, c, fs=5.0)
    for a, b in zip(xs[:-1], xs[1:]):
        _arrow(ax, (a + 10.7, 60), (b - 10.7, 60))
    _box(ax, 87.5, 34, 21, 15, "Fuse\n36 inputs", ORANGE, fs=5.2)
    _arrow(ax, (87.5, 51.3), (87.5, 41.7))
    _box(ax, 62.5, 34, 21, 15, "Calibrated\nXGBoost,\npriority 1-5", ORANGE, fs=5.0)
    _arrow(ax, (76.8, 34), (73.2, 34))
    _box(ax, 37.5, 34, 21, 15, "SHAP drivers,\nrisk level,\nconfidence", ORANGE, fs=5.0)
    _arrow(ax, (51.8, 34), (48.2, 34))
    _box(ax, 12.5, 34, 21, 15, "Clinician:\naccept or\nchange + reason", NAVY, fs=5.0)
    _arrow(ax, (26.8, 34), (23.2, 34))
    _box(ax, 25, 9, 46, 11, "Queue reorders; override stored;\nsummary PDF on request", NAVY, fs=5.0)
    _arrow(ax, (12.5, 26.3), (12.5, 14.7))
    return _save(fig, "paper_flow.png")


def results():
    comp = F.COMP
    fig, axs = plt.subplots(2, 2, figsize=(3.5, 3.1))
    # (a) accuracy by model
    ax = axs[0, 0]
    names = ["Log. reg.", "MLP", "HistGB", "Extra tr.", "XGB (ship.)", "Rand. f.", "k-NN", "Dec. tree"]
    keys = ["Logistic regression", "MLP", "HistGradientBoosting", "Extra trees", "XGBoost (shipped config)", "Random forest", "k-nearest neighbours", "Decision tree"]
    vals = [comp[k]["accuracy"] * 100 for k in keys]
    cols = [ORANGE if k.startswith("XGBoost") else BLUE for k in keys]
    ax.barh(range(len(vals))[::-1], vals, color=cols, height=0.65)
    ax.set_yticks(range(len(vals))[::-1])
    ax.set_yticklabels(names, fontsize=4.8)
    ax.set_xlim(40, 80)
    ax.set_title("(a) Accuracy, %", fontsize=5.6, pad=2)
    # (b) ablation
    ax = axs[0, 1]
    ab = [("Vitals\nonly", F.ABL["Vitals only (8)"]["accuracy"]), ("Report\nonly", F.ABL["Report only (28)"]["accuracy"]), ("Fused", F.ABL["Fused (36)"]["accuracy"])]
    ax.bar(range(3), [v * 100 for _, v in ab], color=[GREY, BLUE, ORANGE], width=0.6)
    for i, (_, v) in enumerate(ab):
        ax.text(i, v * 100 + 1, f"{v * 100:.1f}", ha="center", fontsize=5)
    ax.set_xticks(range(3))
    ax.set_xticklabels([n for n, _ in ab], fontsize=4.8)
    ax.set_ylim(0, 85)
    ax.set_title("(b) Inputs used, accuracy %", fontsize=5.6, pad=2)
    # (c) recall per priority
    ax = axs[1, 0]
    ax.bar(range(1, 6), [r * 100 for r in F.REC], color=[RED, ORANGE, BLUE, TEAL, NAVY], width=0.6)
    for i, r in enumerate(F.REC, 1):
        ax.text(i, r * 100 + 1.5, f"{r * 100:.0f}", ha="center", fontsize=5)
    ax.set_xticks(range(1, 6))
    ax.set_xticklabels([f"P{i}" for i in range(1, 6)], fontsize=5)
    ax.set_ylim(0, 100)
    ax.set_title("(c) Recall per priority, %", fontsize=5.6, pad=2)
    # (d) threshold
    ax = axs[1, 1]
    th = [r for r in F.THR if r["threshold"] >= 0.5]
    x = [r["threshold"] for r in th]
    ax.plot(x, [r["accuracy"] * 100 for r in th], color=ORANGE, marker="o", ms=2.2, lw=1.0, label="accuracy")
    ax.plot(x, [r["coverage"] * 100 for r in th], color=BLUE, marker="s", ms=2.2, lw=1.0, label="coverage")
    ax.axvline(0.85, color=GREY, ls=":", lw=0.8)
    ax.set_ylim(0, 105)
    ax.set_xlabel("confidence threshold", fontsize=4.8, labelpad=1)
    ax.legend(fontsize=4.4, loc="lower left", frameon=False)
    ax.set_title("(d) Confidence threshold, %", fontsize=5.6, pad=2)
    for a in axs.ravel():
        a.tick_params(labelsize=4.8, length=2, pad=1)
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
    fig.subplots_adjust(left=0.17, right=0.98, top=0.93, bottom=0.09, hspace=0.5, wspace=0.42)
    return _save(fig, "paper_results.png")


def screen(name, out):
    """Real screenshot, re-saved as an optimised PNG for the paper (no mock-ups)."""
    im = Image.open(F.shot(name)).convert("RGB")
    im = im.crop((250, 0, im.width, im.height))  # drop the sidebar so the content is legible at column width
    p = os.path.join(F.FIGS, out)
    os.makedirs(F.FIGS, exist_ok=True)
    im.save(p, optimize=True)
    return p


def make():
    return {"arch": arch(), "flow": flow(), "results": results(),
            "why": screen("08_result_why.png", "paper_screen_why.png"), "perf": screen("12_performance.png", "paper_screen_perf.png")}


if __name__ == "__main__":
    print(make())
