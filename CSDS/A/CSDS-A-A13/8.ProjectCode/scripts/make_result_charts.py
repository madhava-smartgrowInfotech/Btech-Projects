"""Charts for the results documents, drawn from the measured values in doc_common.py (docs/REPORT_FACTS.md)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402

from doc_common import BENCH, CHARTS, LATENCY, METHODS, TESTS  # noqa: E402

INK, BLUE, ORANGE, GREEN, GREY = "#1b2238", "#3f3fbf", "#e4572e", "#2f9e6d", "#7a8ba8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": "#8a93a8", "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": INK, "ytick.color": INK})


def violation_matrix():
    rows = ["Same-paper neighbour pairs", "Roll-gap violations", "Accessible seats missed", "Same-department pairs (preference)"]
    idx = [1, 2, 3, 4]
    data = np.array([[BENCH["m-600"][m][i] for m in METHODS] for i in idx], dtype=float)
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    shown = np.where(data == 0, 0.5, data)
    im = ax.imshow(shown, cmap="YlOrRd", norm=LogNorm(vmin=0.5, vmax=2000), aspect="auto")
    ax.set_xticks(range(len(METHODS)), METHODS)
    ax.set_yticks(range(len(rows)), rows)
    ax.xaxis.tick_top()
    for r in range(data.shape[0]):
        for c in range(data.shape[1]):
            v = int(data[r, c])
            ax.text(c, r, f"{v:,}", ha="center", va="center", fontsize=11, fontweight="bold", color="white" if v > 400 else INK)
    ax.set_title("Violations left by each method (600 candidates)", y=-0.12, fontsize=10, fontweight="bold")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    fig.tight_layout()
    fig.savefig(CHARTS / "violation_matrix.png", dpi=150, facecolor="white")
    plt.close(fig)


def api_latency():
    names = [n for n, _, _ in LATENCY]
    med = [m for _, m, _ in LATENCY]
    p95 = [p for _, _, p in LATENCY]
    y = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.barh(y - 0.2, med, 0.38, color=BLUE, label="median")
    ax.barh(y + 0.2, p95, 0.38, color=GREY, label="95th percentile")
    ax.set_xscale("log")
    ax.set_yticks(y, names)
    ax.invert_yaxis()
    ax.set_xlabel("response time in milliseconds (log scale)")
    ax.legend(frameon=False, loc="upper right")
    for yy, m in zip(y, med):
        ax.text(m * 1.12, yy - 0.2, f"{m:,.1f}" if m < 100 else f"{m:,.0f}", va="center", fontsize=8)
    ax.set_title("API response times, local server, sample data loaded", fontsize=10, fontweight="bold")
    ax.grid(axis="x", color="#e3e6ee", lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(CHARTS / "api_latency.png", dpi=150, facecolor="white")
    plt.close(fig)


def tests_chart():
    names = [n.replace("test_", "").replace(".py", "") for n, _ in TESTS]
    vals = [v for _, v in TESTS]
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    bars = ax.bar(names, vals, color=GREEN)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.2, str(v), ha="center", fontsize=9, fontweight="bold")
    ax.set_ylabel("tests (all passed)")
    ax.set_ylim(0, max(vals) + 3)
    ax.set_title("Backend tests by module: 58 passed, 0 failed", fontsize=10, fontweight="bold")
    ax.grid(axis="y", color="#e3e6ee", lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(CHARTS / "tests_by_module.png", dpi=150, facecolor="white")
    plt.close(fig)


def same_dept_chart():
    keys = ["xs-150", "s-300", "m-600", "l-1000", "xl-2000"]
    x = np.arange(len(keys))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    w = 0.2
    cols = [GREEN, ORANGE, "#f2a541", GREY]
    for i, m in enumerate(METHODS):
        ax.bar(x + (i - 1.5) * w, [BENCH[k][m][4] for k in keys], w, label=m, color=cols[i])
    ax.set_xticks(x, ["150", "300", "600", "1,000", "2,000"])
    ax.set_xlabel("candidates in the sitting")
    ax.set_ylabel("same-department neighbour pairs")
    ax.set_title("Department mix (a preference, lower is better)", fontsize=10, fontweight="bold")
    ax.legend(frameon=False, ncol=4, fontsize=8, loc="upper left")
    ax.grid(axis="y", color="#e3e6ee", lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(CHARTS / "same_department_by_method.png", dpi=150, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    CHARTS.mkdir(parents=True, exist_ok=True)
    violation_matrix()
    api_latency()
    tests_chart()
    same_dept_chart()
    print("charts written to", CHARTS)
