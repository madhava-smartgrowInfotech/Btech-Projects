"""Consistent chart styling for training artefacts (PNG, light surface).

Colour roles: zone classes use the reserved status colours (always paired with text labels),
compared models use categorical slots in fixed order, baselines are neutral grey, and
magnitudes (confusion matrices, surfaces) use a single blue ramp.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e4e3df"
BASELINE_GREYS = ["#8d8c87", "#bdbcb6"]

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
STATUS = {"Strong": "#0ca30c", "Weak": "#fab219", "Dead": "#d03b3b"}
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
BLUES = LinearSegmentedColormap.from_list("ss_blues", ["#fcfcfb"] + BLUE_RAMP)


def style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": TEXT_2, "axes.titlecolor": TEXT,
        "axes.titlesize": 12, "axes.titleweight": "bold", "axes.labelsize": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
        "xtick.color": TEXT_2, "ytick.color": TEXT_2, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "legend.frameon": False, "legend.fontsize": 9, "font.size": 10,
        "lines.linewidth": 2, "figure.dpi": 110, "savefig.dpi": 150, "savefig.bbox": "tight",
    })


def save(fig, path) -> None:
    fig.savefig(path)
    plt.close(fig)


def confusion_panel(ax, cm: np.ndarray, classes: list[str], title: str) -> None:
    """Row-normalised confusion matrix with counts and row percentages in text ink."""
    cm = np.asarray(cm, float)
    rows = cm.sum(axis=1, keepdims=True)
    share = np.divide(cm, rows, out=np.zeros_like(cm), where=rows > 0)
    ax.imshow(share, cmap=BLUES, vmin=0, vmax=1)
    ax.grid(False)
    ax.set_xticks(range(len(classes)), classes)
    ax.set_yticks(range(len(classes)), classes)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title, fontsize=10)
    for i in range(len(classes)):
        for j in range(len(classes)):
            ink = "#ffffff" if share[i, j] > 0.55 else TEXT
            ax.text(j, i, f"{share[i, j]:.0%}\n{int(cm[i, j]):,}", ha="center", va="center", fontsize=8, color=ink)
    for spine in ax.spines.values():
        spine.set_visible(False)


def grouped_bars(ax, groups: list[str], series: dict[str, list[float]], colors: list[str], ylabel: str,
                 value_fmt: str = "{:.2f}", ylim: tuple[float, float] | None = None) -> None:
    n = len(series)
    width = 0.8 / n
    x = np.arange(len(groups))
    for k, (name, vals) in enumerate(series.items()):
        pos = x - 0.4 + width * (k + 0.5)
        bars = ax.bar(pos, vals, width * 0.9, color=colors[k], label=name, edgecolor=SURFACE, linewidth=1)
        for b, v in zip(bars, vals):
            if v is not None and not np.isnan(v):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height(), value_fmt.format(v),
                        ha="center", va="bottom", fontsize=7, color=TEXT_2)
    ax.set_xticks(x, groups)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)
    if ylim:
        ax.set_ylim(*ylim)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=min(n, 5))
