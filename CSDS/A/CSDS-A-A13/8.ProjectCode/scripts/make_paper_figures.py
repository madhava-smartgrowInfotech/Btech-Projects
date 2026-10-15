"""Compact figures for the IEEE paper (one-column width, 3.4 in), drawn from the same facts as the report.

    python scripts/make_paper_figures.py       ->  docs/paper/fig1_architecture.png, fig2_algorithm.png, fig3_violations.png
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, INK, ROSE_L, Canvas, anchor  # noqa: E402
from doc_common import BENCH, METHODS, ROOT  # noqa: E402

OUT = ROOT / "docs" / "paper"
DPI = 300


def fig1():
    c = Canvas(3.4, 2.75)
    c.zone(0.3, 21.2, 33.4, 5.9, "", fc="#f4f5fb")
    for x, t in ((0.9, "Administrator\nconsole"), (12.1, "Invigilator\ntablet"), (23.3, "Public seat\nlookup")):
        c.box(x, 21.8, 9.8, 4.2, t, fc="white", fs=5.4, r=0.8, lw=0.8)
    c.box(0.3, 16.8, 33.4, 3.3, "React 18 + TypeScript + Vite (port 5113)\nseat map (dnd-kit), charts, TanStack Query", fc=BLUE_L, fs=5.4, r=0.8, lw=0.8)
    c.box(0.3, 12.7, 33.4, 3.3, "FastAPI REST API (port 8113): JWT, roles, rate limit", fc=INDIGO_L, ec=INDIGO, fs=5.6, r=0.8, lw=0.8, bold=True)
    svc = ["Importer\nparse, validate", "Seating engine\nCP-SAT A + B", "Validator\nsolver-free", "Swap checker\nsame rules", "Exports\nPDF, Excel, QR", "Attendance\nAnalytics, audit"]
    for i, t in enumerate(svc):
        x = 0.3 + (i % 3) * 11.3
        y = 8.9 - (i // 3) * 3.8
        c.box(x, y, 10.8, 3.3, t, fc=GREEN_L, fs=5.0, r=0.7, lw=0.7)
    c.box(0.3, 0.4, 21.4, 3.6, "SQLite: 16 tables, append-only audit trail", fc=AMBER_L, fs=5.4, r=0.8, lw=0.8)
    c.box(22.5, 0.4, 11.2, 3.6, "engine profile,\nbenchmark runs", fc=GREY_L, fs=5.0, r=0.8, lw=0.8)
    for x in (5.8, 17.0, 28.2):
        c.arrow((x, 21.8), (x, 20.1), both=True, lw=0.8)
    c.arrow((17, 16.8), (17, 16.0), both=True, lw=0.8)
    c.arrow((17, 12.7), (17, 12.3), both=True, lw=0.8)
    c.arrow((11, 5.6), (11, 4.0), both=True, lw=0.8)
    c.arrow((28, 5.6), (28, 4.0), lw=0.8)
    c.save(OUT / "fig1_architecture.png")


def fig2():
    c = Canvas(3.4, 4.05)
    c.ax.set_ylim(0, 40.5)
    cx, w = 15.5, 24
    def box(y, t, fc=INDIGO_L, h=2.5):
        c.box(cx - w / 2, y - h / 2, w, h, t, fc=fc, fs=5.3, r=0.7, lw=0.8)
    c.terminal(cx, 39.0, 8, 2.0, "Start", fs=5.5)
    box(35.6, "Load sitting, rules, seed;\npre-checks (seats, access, ceiling)")
    c.diamond(cx, 31.3, 14, 4.2, "problem?", fs=5.2)
    c.box(26.6, 29.8, 7.0, 3.0, "stop:\nexplain\nreason", fc=ROSE_L, fs=4.8, r=0.7, lw=0.7)
    box(26.4, "Stage A pass 1 (CP-SAT):\nhalls + colour class per paper")
    box(22.6, "Stage A pass 2: seeded random\nweights among equal optima")
    box(18.8, "Seeded split of candidates\nbetween halls")
    box(15.0, "Stage B per hall (parallel CP-SAT):\nroll gap, access, dept. mix, random")
    c.diamond(cx, 10.8, 14, 4.2, "all halls\nsolved?", fs=5.0)
    c.box(26.6, 8.9, 7.0, 4.0, "retry 4x budget,\nease hall, redo\nStage A (max 5)", fc=AMBER_L, fs=4.6, r=0.7, lw=0.7)
    box(6.0, "Independent validator; store plan with\nseed, rules, three SHA-256 hashes", fc=GREEN_L)
    c.terminal(cx, 2.4, 8, 2.0, "End", fs=5.5)
    for a, b in ((37.9, 36.9), (34.35, 33.4), (29.2, 27.65), (25.15, 23.85), (21.35, 20.05), (17.55, 16.25), (13.75, 12.9), (8.7, 7.25), (4.75, 3.4)):
        c.arrow((cx, a), (cx, b), lw=0.8)
    c.arrow((cx + 7, 31.3), (26.6, 31.3), lw=0.8)
    c.text(cx + 8.2, 32.1, "yes", fs=4.8)
    c.text(cx + 1.4, 29.0, "no", fs=4.8)
    c.arrow((cx + 7, 10.8), (26.6, 10.8), lw=0.8)
    c.text(cx + 8.2, 11.6, "no", fs=4.8)
    c.text(cx + 1.4, 8.4, "yes", fs=4.8)
    c.path([(30.1, 12.9), (30.1, 26.4), (cx + w / 2, 26.4)], lw=0.8)
    c.save(OUT / "fig2_algorithm.png")


def fig3():
    keys = ["xs-150", "s-300", "m-600", "l-1000", "xl-2000"]
    labels = ["150", "300", "600", "1,000", "2,000"]
    x = np.arange(len(keys))
    w = 0.2
    cols = {"SeatWise": "#2f9e6d", "Sequential": "#e4572e", "Round-robin": "#f2a541", "Random shuffle": "#7a8ba8"}
    fig, ax = plt.subplots(figsize=(3.4, 2.15))
    plt.rcParams.update({"font.family": "Times New Roman"})
    for i, m in enumerate(METHODS):
        vals = [BENCH[k][m][1] for k in keys]
        bars = ax.bar(x + (i - 1.5) * w, vals, w, label=m, color=cols[m], linewidth=0)
        if m == "SeatWise":
            for b in bars:
                ax.text(b.get_x() + b.get_width() / 2, 40, "0", ha="center", va="bottom", fontsize=5.5, color="#2f9e6d", fontweight="bold")
    ax.set_xticks(x, labels, fontsize=6.5)
    ax.set_xlabel("candidates in the sitting", fontsize=7)
    ax.set_ylabel("same-paper neighbour pairs", fontsize=7)
    ax.tick_params(axis="y", labelsize=6.5)
    ax.legend(frameon=False, fontsize=6, loc="upper left")
    ax.grid(axis="y", color="#e3e6ee", lw=0.5)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / "fig3_violations.png", dpi=DPI, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    import diagram_kit
    diagram_kit.DPI = DPI
    fig1()
    fig2()
    fig3()
    print("written to", OUT)
