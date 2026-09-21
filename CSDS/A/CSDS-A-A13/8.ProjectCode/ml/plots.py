"""Benchmark charts (PNG). Quiet chrome, thin marks, selective labels."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# Fixed categorical order (validated adjacent-pair palette); colour follows the method.
METHOD_COLORS = {
    "SeatWise": "#2a78d6",
    "Sequential": "#eb6834",
    "Round-robin": "#1baf7a",
    "Random shuffle": "#eda100",
}
METHOD_ORDER = list(METHOD_COLORS)


def _style() -> None:
    plt.rcParams.update({
        "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
        "font.size": 10,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 1,
        "axes.labelcolor": INK_SECONDARY,
        "axes.titlecolor": INK,
        "axes.titlesize": 12,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.titlepad": 14,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 1,
        "grid.linestyle": "-",
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_SECONDARY,
        "ytick.labelcolor": INK_SECONDARY,
        "legend.frameon": False,
        "legend.labelcolor": INK_SECONDARY,
        "savefig.facecolor": SURFACE,
        "savefig.dpi": 160,
    })


def _save(fig, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def _subtitle(ax, text: str) -> None:
    ax.text(0, 1.01, text, transform=ax.transAxes, color=MUTED, fontsize=9, va="bottom")


def solve_time_by_size(sizes: list[int], mean_s: list[float], min_s: list[float], max_s: list[float], path: Path) -> Path:
    _style()
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.grid(axis="x", visible=False)
    lower = np.array(mean_s) - np.array(min_s)
    upper = np.array(max_s) - np.array(mean_s)
    ax.errorbar(sizes, mean_s, yerr=[lower, upper], color=METHOD_COLORS["SeatWise"], ecolor=AXIS,
                elinewidth=1, capsize=3, linewidth=2, marker="o", markersize=7,
                markeredgecolor=SURFACE, markeredgewidth=2, solid_capstyle="round")
    ax.annotate(f"{mean_s[-1]:.1f} s", (sizes[-1], mean_s[-1]), xytext=(8, 0), textcoords="offset points",
                color=INK, va="center", fontsize=9)
    ax.set_xticks(sizes, [f"{s:,}" for s in sizes])
    ax.set_xlabel("Candidates in the session")
    ax.set_ylabel("Solve time (seconds)")
    ax.set_ylim(bottom=0)
    ax.set_title("SeatWise solve time by session size")
    _subtitle(ax, "Mean over seeds; whiskers show the fastest and slowest run")
    return _save(fig, path)


def grouped_columns(groups: list[str], values: dict[str, list[float]], title: str, subtitle: str,
                    ylabel: str, path: Path, label_method: str | None = "SeatWise") -> Path:
    _style()
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    ax.grid(axis="x", visible=False)
    methods = [m for m in METHOD_ORDER if m in values]
    width = 0.8 / len(methods)
    x = np.arange(len(groups))
    for i, method in enumerate(methods):
        pos = x - 0.4 + width * (i + 0.5)
        bars = ax.bar(pos, values[method], width=width, color=METHOD_COLORS[method], label=method,
                      edgecolor=SURFACE, linewidth=1.5)
        if method == label_method:
            for bar, value in zip(bars, values[method]):
                ax.annotate(f"{value:,.0f}", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                            xytext=(0, 3), textcoords="offset points", ha="center", color=INK, fontsize=8)
    ax.set_xticks(x, groups)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    _subtitle(ax, subtitle)
    ax.legend(ncols=len(methods), loc="upper left", bbox_to_anchor=(0, -0.12), handlelength=1, handleheight=1)
    return _save(fig, path)


def method_bars(values: dict[str, float], title: str, subtitle: str, xlabel: str, path: Path,
                fmt: str = "{:.2f}") -> Path:
    _style()
    methods = [m for m in METHOD_ORDER if m in values][::-1]
    fig, ax = plt.subplots(figsize=(7.5, 0.55 * len(methods) + 1.6))
    ax.grid(axis="y", visible=False)
    bars = ax.barh(methods, [values[m] for m in methods], height=0.5,
                   color=[METHOD_COLORS[m] for m in methods], edgecolor=SURFACE, linewidth=1.5)
    for bar, method in zip(bars, methods):
        ax.annotate(fmt.format(values[method]), (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                    xytext=(4, 0), textcoords="offset points", va="center", color=INK, fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_xlim(0, max(max(values.values()) * 1.15, 1e-9))
    ax.set_title(title)
    _subtitle(ax, subtitle)
    return _save(fig, path)


def hall_utilisation(halls: list[str], percent: list[float], path: Path) -> Path:
    _style()
    fig, ax = plt.subplots(figsize=(max(6.0, 0.45 * len(halls) + 2), 4.0))
    ax.grid(axis="x", visible=False)
    ax.bar(halls, percent, width=0.6, color=METHOD_COLORS["SeatWise"], edgecolor=SURFACE, linewidth=1.5)
    mean = float(np.mean(percent)) if percent else 0.0
    ax.axhline(mean, color=INK_SECONDARY, linewidth=1)
    ax.annotate(f"mean {mean:.0f}%", (len(halls) - 0.5, mean), xytext=(0, 4), textcoords="offset points",
                ha="right", color=INK_SECONDARY, fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Seats used (%)")
    ax.tick_params(axis="x", labelrotation=90 if len(halls) > 14 else 0)
    ax.set_title("Hall utilisation in a typical session")
    _subtitle(ax, "Share of usable seats filled in each hall the engine opened")
    return _save(fig, path)


def budget_tuning(budgets: list[float], dept_pairs: list[float], solve_s: list[float], chosen: float, path: Path) -> Path:
    _style()
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    ax.grid(axis="x", visible=False)
    ax.plot(budgets, dept_pairs, color=METHOD_COLORS["SeatWise"], linewidth=2, marker="o", markersize=7,
            markeredgecolor=SURFACE, markeredgewidth=2)
    i = budgets.index(chosen)
    ax.annotate(f"chosen: {chosen:g} per hall\n{solve_s[i]:.1f} s per session",
                (chosen, dept_pairs[i]), xytext=(10, 12), textcoords="offset points",
                color=INK, fontsize=9, arrowprops={"arrowstyle": "-", "color": AXIS, "linewidth": 1})
    ax.set_xscale("log", base=2)
    ax.set_xticks(budgets, [f"{b:g}" for b in budgets])
    ax.set_xlabel("Deterministic time budget per hall")
    ax.set_ylabel("Same-department neighbour pairs")
    ax.set_title("Choosing the per-hall time budget")
    _subtitle(ax, "Lower is better; the smallest budget within 3% of the best is used")
    return _save(fig, path)
