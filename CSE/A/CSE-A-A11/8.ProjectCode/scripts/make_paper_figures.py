"""Figures for the IEEE paper, sized for one 3.4 in column: a compact architecture, a compact review flow, a results chart\nand two narrow real screens (captured by scripts/paper_shots.py).\n\n    python scripts/make_paper_figures.py      -> docs/paper/*.png\n"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor  # noqa: E402
from doc_common import BEST, EV, MODELS, SEEDS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "paper"
FS = 5.6


def architecture(path):
    c = Canvas(3.45, 2.75)
    c.box(1, 22.2, 32.5, 4.2, "Developer - browser (React 19 + Vite, port 5311)", fc=BLUE_L, fs=FS, bold=True, r=1)
    c.box(1, 16.6, 32.5, 4.4, "FastAPI REST API (port 8311): JWT, 25 routes, job threads", fc=INDIGO_L, ec=INDIGO, fs=FS, bold=True, r=1)
    c.arrow((17, 22.2), (17, 21.0), both=True, lw=0.8)
    svc = ["diffutil\ndiff / zip /\nGitHub", "rules\nAST + taint\n30 rules", "metrics +\nmlmodel\nXGBoost", "agents\n7 agents,\njudge", "codeintel\nretrieval\n+ graph"]
    bw = 6.0
    for i, t in enumerate(svc):
        x = 1 + i * (bw + 0.625)
        c.box(x, 9.4, bw, 5.8, t, fc="white", fs=4.7, r=0.8)
        c.arrow((x + bw / 2, 16.6), (x + bw / 2, 15.2), lw=0.7)
    c.box(1, 2.2, 8.4, 5.2, "app.db\nusers", fc=AMBER_L, fs=FS, r=0.8)
    c.box(10.4, 2.2, 8.4, 5.2, "history.db\nreviews", fc=AMBER_L, fs=FS, r=0.8)
    c.box(19.8, 2.2, 6.4, 5.2, "model\nartefacts", fc=GREEN_L, fs=5.0, r=0.8)
    c.box(27.2, 2.2, 6.3, 5.2, "GitHub /\nLLM (opt.)", fc=ROSE_L, fs=4.8, r=0.8)
    for x in (5.2, 14.6, 23.0):
        c.arrow((x, 9.4), (x, 7.4), both=True, lw=0.7)
    c.arrow((30.3, 9.4), (30.3, 7.4), both=True, lw=0.7, ls="--")
    c.text(17.2, 0.7, "solid: local calls    dashed: optional external services", fs=4.6, italic=True)
    c.save(path)


def flow(path):
    c = Canvas(3.45, 3.3)
    L, R, bw, h = 1.0, 19.0, 14.6, 3.0
    a = c.box(L, 29.0, bw, h, "Input: diff, PR URL,\nfiles / zip / folder", fc=BLUE_L, fs=4.6, r=0.8)
    b = c.box(L, 24.4, bw, h, "1 Ingestion: files,\nhunks, changed lines", fc=BLUE_L, fs=4.6, r=0.8)
    s = c.box(L, 19.8, bw, h, "2 Static: AST + taint\nrules, quality checks", fc=INDIGO_L, fs=4.6, r=0.8)
    m = c.box(L, 15.2, bw, h, "3 ML risk: 14 metrics\n-> p(vuln), type", fc=INDIGO_L, fs=4.6, r=0.8)
    for p_, q in ((a, b), (b, s), (s, m)):
        c.arrow(anchor(p_, "b"), anchor(q, "t"), lw=0.7)
    r_ = c.box(R, 29.0, bw, h, "4 Reasoner: CWE,\nOWASP, source->sink", fc=GREEN_L, fs=4.6, r=0.8)
    rem = c.box(R, 24.4, bw, h, "5 Remediation: patch,\nthen re-scan to verify", fc=GREEN_L, fs=4.6, r=0.8)
    q_ = c.box(R, 19.8, bw, h, "6 Quality reviewer:\nmaintainability", fc=GREEN_L, fs=4.6, r=0.8)
    j = c.box(R, 15.2, bw, h, "7 Judge: de-duplicate,\nscore, verdict", fc=AMBER_L, fs=4.6, r=0.8, bold=True)
    c.path([(L + bw, 16.7), (17.3, 16.7), (17.3, 30.5), (R, 30.5)], lw=0.7)
    for p_, q in ((r_, rem), (rem, q_), (q_, j)):
        c.arrow(anchor(p_, "b"), anchor(q, "t"), lw=0.7)
    c.box(R - 3, 10.2, bw + 3, 3.0, "score = 100(1 - e^(-W/18))", fc=GREY_L, fs=4.6, r=0.6)
    c.arrow((R + bw / 2, 15.2), (R + bw / 2, 13.2), lw=0.7)
    c.box(1, 2.2, 10.0, 4.2, "BLOCK", fc=ROSE_L, fs=5.0, r=0.8, bold=True)
    c.box(12.0, 2.2, 11.4, 4.2, "REQUEST_\nCHANGES", fc=AMBER_L, fs=4.4, r=0.8, bold=True)
    c.box(24.4, 2.2, 9.1, 4.2, "APPROVE", fc=GREEN_L, fs=4.8, r=0.8, bold=True)
    c.line((R + bw / 2, 10.2), (R + bw / 2, 8.4), lw=0.7)
    c.line((6.0, 8.4), (29.0, 8.4), lw=0.7)
    for x in (6.0, 17.7, 29.0):
        c.arrow((x, 8.4), (x, 6.4), lw=0.7)
    c.save(path)


def results_chart(path):
    fig, (a, b) = plt.subplots(2, 1, figsize=(3.45, 3.5), gridspec_kw={"height_ratios": [1.15, 1]})
    names = sorted(MODELS, key=lambda n: MODELS[n]["f1"])
    cols = ["#d1495b" if n == BEST else "#8c8caa" for n in names]
    a.barh([n.replace(" (RBF)", "") for n in names], [MODELS[n]["f1"] for n in names], color=cols, height=0.7)
    for i, n in enumerate(names):
        a.text(MODELS[n]["f1"] + 0.01, i, f"{MODELS[n]['f1']:.3f}", va="center", fontsize=5.5)
    a.set_xlim(0, 1.05)
    a.tick_params(labelsize=5.5)
    a.set_title("(a) F1 of nine classifiers, 1,500 held-out functions", fontsize=6.5, loc="left")
    rows = [("Rules", "rule_engine"), (BEST, "ml_model"), ("Either", "combined_or"), ("Both", "combined_and")]
    x = np.arange(len(rows))
    for i, (m, col) in enumerate((("precision", "#6d5bd0"), ("recall", "#2f9e6d"), ("f1", "#e08a2c"))):
        v = [EV[k][m] for _, k in rows]
        bars = b.bar(x + (i - 1) * 0.27, v, 0.27, color=col, label={"precision": "P", "recall": "R", "f1": "F1"}[m])
        for bb, val in zip(bars, v):
            b.text(bb.get_x() + bb.get_width() / 2, val + 0.015, f"{val:.2f}", ha="center", fontsize=4.6)
    b.set_xticks(x, [r[0] for r in rows], fontsize=5.5)
    b.set_ylim(0, 1.18)
    b.tick_params(labelsize=5.5)
    b.legend(ncol=3, fontsize=5, frameon=False, loc="upper right")
    b.set_title("(b) rule engine, ML model and their combinations", fontsize=6.5, loc="left")
    for ax in (a, b):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(pad=0.4, h_pad=0.8)
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)


def fit(im, width=1000):
    r = width / im.size[0]
    return im.resize((width, int(im.size[1] * r)), Image.LANCZOS)


def screens():
    im = Image.open(OUT / "shot_review.png").convert("RGB")
    fit(im.crop((0, 30, im.size[0], 1010))).save(OUT / "fig4_review.png", optimize=True)
    f = Image.open(OUT / "shot_finding.png").convert("RGB")
    w = f.size[0]
    top, bot = f.crop((0, 0, w, 403)), f.crop((0, 1420, w, 1958))
    stack = Image.new("RGB", (w, top.size[1] + bot.size[1] + 8), "white")
    stack.paste(top, (0, 0))
    stack.paste(bot, (0, top.size[1] + 8))
    fit(stack).save(OUT / "fig5_finding.png", optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture(OUT / "fig1_architecture.png")
    flow(OUT / "fig2_flow.png")
    results_chart(OUT / "fig3_results.png")
    screens()
    print("saved", OUT)
