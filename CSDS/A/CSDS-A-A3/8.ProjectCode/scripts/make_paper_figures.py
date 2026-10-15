"""Compact figures for the IEEE paper (one-column width, 3.4 in), drawn from the same facts as the report.

    python scripts/make_paper_figures.py   ->  docs/paper/fig1_architecture.png ... fig5_models.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "paper"
SHOTS = ROOT / "docs" / "screenshots"
M = json.loads((ROOT / "models" / "metrics.json").read_text())
R = json.loads((ROOT / "docs" / "experiments" / "measured.json").read_text())
V2 = json.loads((ROOT / "docs" / "experiments" / "demo_retrain_metrics_v2.json").read_text())
DPI = 300
GREEN, RED, AMB = "#0f7a5a", "#c9372c", "#d99a1e"


def fig1():
    c = Canvas(3.4, 2.7)
    c.zone(0.3, 21.0, 33.4, 5.8, "", fc="#f4f5fb")
    for x, t in ((0.9, "Analyst /\nreporter"), (12.1, "Maintainer"), (23.3, "CLI")):
        c.box(x, 21.6, 9.8, 4.2, t, fc="white", fs=5.4, r=0.8, lw=0.8)
    c.box(0.3, 16.6, 33.4, 3.4, "React 18 + Vite (port 5103): 7 pages, recharts", fc=BLUE_L, fs=5.4, r=0.8, lw=0.8)
    c.box(0.3, 12.4, 33.4, 3.4, "Flask JSON API (port 8103): check, report, stats, retrain, sync", fc=INDIGO_L, ec=INDIGO, fs=5.4, r=0.8, lw=0.8, bold=True)
    mods = ["Features\n47 offline", "Detector\ncommunity, model", "Train\nRF, XGB, LR", "ThreatIntel\nvotes, feeds", "Retrain\nx3, reload"]
    for i, t in enumerate(mods):
        c.box(0.3 + i * 6.75, 7.4, 6.3, 4.1, t, fc=GREEN_L, fs=4.6, r=0.7, lw=0.7)
    c.box(0.3, 0.5, 10.5, 4.6, "SQLite\nreports, intel, checks", fc=AMBER_L, fs=5.0, r=0.8, lw=0.8)
    c.box(11.8, 0.5, 10.6, 4.6, "models/ +\nmetrics.json", fc=GREY_L, fs=5.0, r=0.8, lw=0.8)
    c.box(23.4, 0.5, 10.3, 4.6, "OpenPhish,\nURLhaus feeds", fc=ROSE_L, fs=5.0, r=0.8, lw=0.8)
    for x in (5.8, 17.0, 28.2):
        c.arrow((x, 21.6), (x, 20.0), both=True, lw=0.8)
    c.arrow((17, 16.6), (17, 15.8), both=True, lw=0.8)
    c.arrow((17, 12.4), (17, 11.5), both=True, lw=0.8)
    for x in (5.5, 17.0, 28.5):
        c.arrow((x, 7.4), (x, 5.1), both=True, lw=0.7)
    c.save(OUT / "fig1_architecture.png")


def fig2():
    c = Canvas(3.4, 3.5)
    cx = 17
    c.terminal(cx, 33, 15, 2.6, "URL", fs=5.6)
    c.box(cx - 10, 27.4, 20, 3.2, "normalise + 47 features", fc="white", fs=5.2, r=0.7, lw=0.8)
    c.diamond(cx, 21.8, 20, 5.4, "confirmed in\ncommunity store?", fs=4.8)
    c.box(24.5, 19.8, 9.2, 4.2, "community\nverdict\n(URL or host)", fc=ROSE_L, fs=4.6, r=0.7, lw=0.8)
    c.box(cx - 8, 13.2, 16, 3.2, "p = model score", fc=INDIGO_L, ec=INDIGO, fs=5.2, r=0.7, lw=0.8, bold=True)
    c.box(cx - 10, 8.6, 20, 3.2, "x0.4 popular domain; +-0.15 per net vote", fc=AMBER_L, fs=4.6, r=0.7, lw=0.8)
    c.diamond(cx, 3.9, 17, 4.6, "p vs 0.60 / 0.35", fs=4.8)
    c.arrow((cx, 31.7), (cx, 31.0), lw=0.8)
    c.arrow((cx, 27.4), (cx, 24.5), lw=0.8)
    c.arrow((cx + 10, 21.8), (24.5, 21.8), lw=0.8, label="yes", fs=4.4, loff=(0, 1.0))
    c.arrow((cx, 19.1), (cx, 16.4), lw=0.8, label="no", fs=4.4, loff=(1.4, 0))
    c.arrow((cx, 13.2), (cx, 11.8), lw=0.8)
    c.arrow((cx, 8.6), (cx, 6.2), lw=0.8)
    c.box(26.0, 3.7, 7.7, 2.4, "phishing", fc=ROSE_L, fs=4.4, r=0.6, lw=0.7)
    c.box(26.0, 0.6, 7.7, 2.4, "safe", fc=GREEN_L, fs=4.4, r=0.6, lw=0.7)
    c.box(0.3, 0.6, 9.5, 2.4, "suspicious", fc=AMBER_L, fs=4.4, r=0.6, lw=0.7)
    c.arrow((cx + 8.5, 4.2), (26.0, 4.9), lw=0.7)
    c.arrow((cx + 8.5, 3.6), (26.0, 1.8), lw=0.7)
    c.arrow((cx - 7, 3.4), (9.8, 2.2), lw=0.7)
    c.save(OUT / "fig2_flow.png")


def fig3():
    fig, axs = plt.subplots(1, 2, figsize=(3.4, 1.9), gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axs[0]
    keys = ["accuracy", "f1", "roc_auc"]
    labels = ["Acc.", "F1", "AUC"]
    for i, (n, col) in enumerate((("xgboost", GREEN), ("random_forest", INDIGO), ("logistic_regression", AMB))):
        vals = [M["models"][n][k] * 100 for k in keys]
        axs[0].bar(np.arange(3) + (i - 1) * 0.27, vals, 0.27, color=col, label={"xgboost": "XGB", "random_forest": "RF", "logistic_regression": "LR"}[n])
    ax.set_xticks(range(3))
    ax.set_xticklabels(labels, fontsize=6)
    ax.set_ylim(70, 102)
    ax.tick_params(labelsize=6)
    ax.set_ylabel("%", fontsize=6)
    ax.legend(fontsize=5, frameon=False, ncol=3, loc="upper center", handlelength=1, columnspacing=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax2 = axs[1]
    t = [d["threshold"] for d in R["thresholds"]]
    for k, col, lab in (("precision", INDIGO, "P"), ("recall", RED, "R"), ("f1", GREEN, "F1")):
        ax2.plot(t, [d[k] * 100 for d in R["thresholds"]], color=col, lw=1.2, label=lab, marker="o", ms=1.8)
    ax2.axvline(0.35, color=AMB, ls="--", lw=0.7)
    ax2.axvline(0.60, color=RED, ls="--", lw=0.7)
    ax2.set_xlabel("threshold", fontsize=6)
    ax2.tick_params(labelsize=6)
    ax2.set_ylim(72, 101)
    ax2.legend(fontsize=5, frameon=False, ncol=3, loc="lower center", handlelength=1, columnspacing=0.8)
    ax2.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / "fig3_results.png", dpi=DPI, facecolor="white")
    plt.close(fig)


def fig6():
    fig, axs = plt.subplots(1, 2, figsize=(3.4, 1.9), gridspec_kw={"width_ratios": [1.2, 1]})
    top = M["models"]["xgboost"]["top_features"][:7][::-1]
    axs[0].barh([d["feature"].replace("_", " ") for d in top], [d["importance"] for d in top], color=GREEN)
    axs[0].tick_params(labelsize=5)
    axs[0].set_xlabel("importance", fontsize=6)
    axs[0].spines[["top", "right"]].set_visible(False)
    lc = R["learning"]
    axs[1].plot([d["train_rows"] / 1000 for d in lc], [d["f1"] * 100 for d in lc], color=GREEN, marker="o", ms=2, lw=1.2)
    axs[1].set_xlabel("training URLs (thousands)", fontsize=6)
    axs[1].set_ylabel("F1 %", fontsize=6)
    axs[1].tick_params(labelsize=6)
    axs[1].spines[["top", "right"]].set_visible(False)
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / "fig6_features.png", dpi=DPI, facecolor="white")
    plt.close(fig)


def crop(src, box, name, width=1100):
    im = Image.open(SHOTS / src).convert("RGB").crop(box)
    h = int(im.height * width / im.width)
    im.resize((width, h), Image.LANCZOS).save(OUT / name, dpi=(DPI, DPI))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig1()
    fig2()
    fig3()
    fig6()
    crop("05_check_community_override.png", (276, 245, 1412, 800), "fig4_check.png")
    crop("21_models_after_retrain_full.png", (276, 235, 1412, 1090), "fig5_models.png")
    print("saved paper figures")
