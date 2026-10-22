"""Shared drawing helpers for make_diagrams.py (matplotlib only)."""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "diagrams")
os.makedirs(OUT, exist_ok=True)

NAVY, INK, SLATE = "#1B2A41", "#0F172A", "#475569"
ORANGE, BLUE, GREEN, PURPLE, GOLD = "#EB6834", "#2A78D6", "#1BAF7A", "#6B52D6", "#E8A317"
PAPER, LINE = "#F6F8FB", "#9AA8BD"
plt.rcParams["font.family"] = "DejaVu Sans"


def canvas(w, h, title=None, ty=99):
    """Work in a 100 x 100 coordinate space; the figure is cropped to its content when saved."""
    top = ty + 2
    fig, ax = plt.subplots(figsize=(w, w * top / 100))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, top)
    ax.axis("off")
    ax.set_aspect("equal")
    if title:
        ax.text(1, ty, title, fontsize=13, fontweight="bold", color=NAVY, va="top")
    return fig, ax


def box(ax, x, y, w, h, text, fc=PAPER, ec=LINE, tc=INK, fs=9.5, bold=False, lw=1.3, rounding=1.2, ls="-"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rounding}", fc=fc, ec=ec, lw=lw, ls=ls)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc,
            fontweight="bold" if bold else "normal", linespacing=1.25)
    return (x, y, w, h)


def arrow(ax, p, q, label=None, color=SLATE, lw=1.4, ls="-", fs=8, off=(0, 1.2), rad=0.0, head="-|>", lab_ha="center", lp=None):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle=head, color=color, lw=lw, ls=ls,
                                                    connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))
    if label:
        lx, ly = lp if lp else ((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1])
        ax.text(lx, ly, label, fontsize=fs, color=color,
                ha=lab_ha, va="center", bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path)


def mid(b, side):
    x, y, w, h = b
    return {"l": (x, y + h / 2), "r": (x + w, y + h / 2), "t": (x + w / 2, y + h), "b": (x + w / 2, y)}[side]


# ---------------------------------------------------------------- DFD helpers
def process(ax, cx, cy, r, text, num, fs=8):
    ax.add_patch(Circle((cx, cy), r, fc="#E8F0FC", ec=BLUE, lw=1.6))
    ax.text(cx, cy + r * 0.42, num, ha="center", va="center", fontsize=8.5, fontweight="bold", color=BLUE)
    ax.text(cx, cy - r * 0.12, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)
    return (cx, cy, r)


def entity(ax, x, y, w, h, text):
    ax.add_patch(Rectangle((x, y), w, h, fc="#FFF1EA", ec=ORANGE, lw=1.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, color=INK, fontweight="bold", linespacing=1.2)
    return (x, y, w, h)


def store(ax, x, y, w, h, text, tag):
    ax.add_patch(Rectangle((x, y), w, h, fc="#FFF8E5", ec="none"))
    ax.plot([x, x + w], [y + h, y + h], color=GOLD, lw=1.8)
    ax.plot([x, x + w], [y, y], color=GOLD, lw=1.8)
    ax.plot([x, x], [y, y + h], color=GOLD, lw=1.8)
    ax.text(x + 1.3, y + h / 2, tag, ha="left", va="center", fontsize=8.5, fontweight="bold", color=GOLD)
    ax.text(x + w / 2 + 2.5, y + h / 2, text, ha="center", va="center", fontsize=8.5, color=INK, linespacing=1.2)
    return (x, y, w, h)


# ---------------------------------------------------------------- 06 UML class
def uml_class(ax, x, y, w, name, attrs, methods, stereo=None, color=BLUE, fs=7.6):
    lh = 2.15
    h = 4.6 + lh * (len(attrs) + len(methods)) + (1.2 if attrs and methods else 0)
    ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=color, lw=1.6))
    ax.add_patch(Rectangle((x, y - 4.6), w, 4.6, fc=color, ec=color))
    if stereo:
        ax.text(x + w / 2, y - 1.1, f"<<{stereo}>>", ha="center", va="center", color="white", fontsize=6.8)
        ax.text(x + w / 2, y - 3.1, name, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold")
    else:
        ax.text(x + w / 2, y - 2.3, name, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold")
    cy = y - 4.6 - 1.2
    for a in attrs:
        ax.text(x + 1, cy, a, fontsize=fs, va="center", color=INK, family="monospace")
        cy -= lh
    if attrs and methods:
        ax.plot([x, x + w], [cy + 0.2, cy + 0.2], color=color, lw=0.8)
        cy -= 1.0
    for m in methods:
        ax.text(x + 1, cy, m, fontsize=fs, va="center", color=INK, family="monospace")
        cy -= lh
    return (x, y - h, w, h)


def diamond(ax, cx, cy, w, h, text, fc="#FFF8E5", ec=GOLD, fs=8):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], closed=True, fc=fc, ec=ec, lw=1.5))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.1)


