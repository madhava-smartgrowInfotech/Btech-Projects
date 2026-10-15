"""Tiny matplotlib diagram toolkit used by make_diagrams.py (no system dependency)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse, Rectangle, Polygon

GREEN, DARK, LIGHT = "#15803d", "#14532d", "#dcfce7"
BLUE, BLUE_L = "#0369a1", "#e0f2fe"
AMB, AMB_L = "#b45309", "#fef3c7"
RED, RED_L = "#b91c1c", "#fee2e2"
PUR, PUR_L = "#6d28d9", "#ede9fe"
GREY, GREY_L = "#475569", "#f1f5f9"
INK = "#0f172a"


def canvas(w, h, title=None, dpi=150):
    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi)
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    if title:
        ax.text(w / 2, h - 0.25, title, ha="center", va="center", fontsize=15, fontweight="bold", color=INK)
    return fig, ax


def box(ax, x, y, w, h, text="", fc=LIGHT, ec=GREEN, fs=10, bold=False, r=0.08, lw=1.6, color=INK, ls="-", ha="center", va="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, ls=ls))
    if text:
        tx = x + w / 2 if ha == "center" else x + 0.12
        ax.text(tx, y + h / 2, text, ha=ha, va=va, fontsize=fs, color=color, fontweight="bold" if bold else "normal", linespacing=1.25)
    return (x, y, w, h)


def label(ax, x, y, text, fs=10, color=INK, bold=False, ha="center", va="center", italic=False, rot=0):
    ax.text(x, y, text, ha=ha, va=va, fontsize=fs, color=color, fontweight="bold" if bold else "normal",
            style="italic" if italic else "normal", linespacing=1.25, rotation=rot)


def arrow(ax, p, q, text="", color=GREY, fs=8.5, lw=1.5, ls="-", style="-|>", off=(0, 0.13), rad=0.0, tcolor=None, ha="center"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=13, color=color, lw=lw, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))
    if text:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, ha=ha, va="center", fontsize=fs,
                color=tcolor or color, bbox=dict(fc="white", ec="none", pad=1.2, alpha=0.9))


def ell(ax, x, y, w, h, text, fc=LIGHT, ec=GREEN, fs=9.5, lw=1.6):
    ax.add_patch(Ellipse((x, y), w, h, fc=fc, ec=ec, lw=lw))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)


def diamond(ax, cx, cy, w, h, text, fc=AMB_L, ec=AMB, fs=9):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], fc=fc, ec=ec, lw=1.6))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)


def store(ax, x, y, w, h, text, fc=AMB_L, ec=AMB, fs=9):
    """Open-ended rectangle = data store."""
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec="none"))
    ax.plot([x, x + w], [y + h, y + h], color=ec, lw=1.8); ax.plot([x, x + w], [y, y], color=ec, lw=1.8)
    ax.plot([x, x], [y, y + h], color=ec, lw=1.8)
    ax.text(x + w / 2 + 0.05, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)


def save(fig, path):
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white", pad_inches=0.15)
    plt.close(fig)
    print("saved", path)
