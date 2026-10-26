"""Tiny matplotlib drawing helpers shared by make_diagrams.py (boxes, arrows, UML class boxes, circles)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

NAVY = "#1F3A5F"
BLUE = "#2B6CB0"
TEAL = "#14907F"
ORANGE = "#D9772F"
PURPLE = "#6B5BD2"
GREY = "#5B6B7F"
LIGHT = "#EEF2F7"
PALE_BLUE = "#E3EEFB"
PALE_TEAL = "#DDF3EE"
PALE_ORANGE = "#FBE9DA"
PALE_PURPLE = "#ECE9FB"
WHITE = "#FFFFFF"
INK = "#14213D"

plt.rcParams["font.family"] = "DejaVu Sans"


def canvas(w_in: float, h_in: float, w: float = 100, h: float | None = None):
    h = h if h is not None else w * h_in / w_in
    fig, ax = plt.subplots(figsize=(w_in, h_in))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    fig.subplots_adjust(0.01, 0.01, 0.99, 0.99)
    return fig, ax


def box(ax, cx, cy, w, h, text, fc=NAVY, tc=WHITE, fs=9.5, ec=None, bold=False, r=1.2, lw=1.2, ls="-", va="center", alpha=1):
    p = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                       fc=fc, ec=ec or fc, lw=lw, ls=ls, alpha=alpha, zorder=2)
    ax.add_patch(p)
    ax.text(cx, cy, text, ha="center", va=va, color=tc, fontsize=fs, fontweight="bold" if bold else "normal",
            zorder=3, linespacing=1.25)
    return (cx, cy, w, h)


def panel(ax, x, y, w, h, title, fc=LIGHT, ec="#B7C3D3", fs=10, tc=NAVY):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=ec, lw=1.2, zorder=1))
    ax.text(x + 1.2, y + h - 1.0, title, ha="left", va="top", color=tc, fontsize=fs, fontweight="bold", zorder=3)


def arrow(ax, p1, p2, label=None, color=GREY, lw=1.5, rad=0.0, fs=8, ls="-", lo=(0, 1.2), ha="center", style="-|>", z=4, bg=True):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=13, color=color, lw=lw, ls=ls,
                        connectionstyle=f"arc3,rad={rad}", zorder=z, shrinkA=0, shrinkB=0)
    ax.add_patch(a)
    if label:
        mx, my = (p1[0] + p2[0]) / 2 + lo[0], (p1[1] + p2[1]) / 2 + lo[1]
        ax.text(mx, my, label, ha=ha, va="center", fontsize=fs, color=INK, zorder=5,
                bbox=dict(fc="white", ec="none", pad=0.8, alpha=0.9) if bg else None)


def circle(ax, cx, cy, r, text, fc=BLUE, tc=WHITE, fs=9.5, bold=True):
    ax.add_patch(Circle((cx, cy), r, fc=fc, ec=fc, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", color=tc, fontsize=fs, fontweight="bold" if bold else "normal", zorder=3, linespacing=1.2)


def ellipse(ax, cx, cy, w, h, text, fc=PALE_BLUE, ec=BLUE, tc=INK, fs=9):
    ax.add_patch(Ellipse((cx, cy), w, h, fc=fc, ec=ec, lw=1.3, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", color=tc, fontsize=fs, zorder=3, linespacing=1.2)


def diamond(ax, cx, cy, w, h, text, fc=PALE_ORANGE, ec=ORANGE, tc=INK, fs=9):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], fc=fc, ec=ec, lw=1.4, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", color=tc, fontsize=fs, zorder=3, linespacing=1.2)


def store(ax, cx, cy, w, h, text, fc=PALE_TEAL, ec=TEAL, tc=INK, fs=9):
    """Open-ended rectangle used for DFD data stores."""
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, fc=fc, ec="none", zorder=2))
    ax.plot([cx - w / 2, cx + w / 2], [cy + h / 2, cy + h / 2], color=ec, lw=1.6, zorder=3)
    ax.plot([cx - w / 2, cx + w / 2], [cy - h / 2, cy - h / 2], color=ec, lw=1.6, zorder=3)
    ax.plot([cx - w / 2, cx - w / 2], [cy - h / 2, cy + h / 2], color=ec, lw=1.6, zorder=3)
    ax.text(cx, cy, text, ha="center", va="center", color=tc, fontsize=fs, zorder=4, linespacing=1.2)


def uml_class(ax, x, y, w, name, attrs, methods, hdr=NAVY, fs=7.6, stereotype=None, lh=2.15):
    """Class box with its top-left corner at (x, y). Returns (x, y_bottom, w, h)."""
    h_head = 4.6 if stereotype else 3.4
    h_attr = max(lh * len(attrs) + 1.2, 2.6)
    h_meth = max(lh * len(methods) + 1.2, 2.6)
    h = h_head + h_attr + h_meth
    ax.add_patch(Rectangle((x, y - h), w, h, fc=WHITE, ec=NAVY, lw=1.3, zorder=2))
    ax.add_patch(Rectangle((x, y - h_head), w, h_head, fc=hdr, ec=NAVY, lw=1.3, zorder=3))
    if stereotype:
        ax.text(x + w / 2, y - 1.15, f"<<{stereotype}>>", ha="center", va="center", color=WHITE, fontsize=fs - 0.4, zorder=4, style="italic")
        ax.text(x + w / 2, y - 3.2, name, ha="center", va="center", color=WHITE, fontsize=fs + 1.2, fontweight="bold", zorder=4)
    else:
        ax.text(x + w / 2, y - h_head / 2, name, ha="center", va="center", color=WHITE, fontsize=fs + 1.2, fontweight="bold", zorder=4)
    ax.plot([x, x + w], [y - h_head - h_attr, y - h_head - h_attr], color=NAVY, lw=1.0, zorder=3)
    for i, a in enumerate(attrs):
        ax.text(x + 0.9, y - h_head - 1.3 - i * lh, a, ha="left", va="center", fontsize=fs, color=INK, zorder=4, family="DejaVu Sans Mono")
    for i, m in enumerate(methods):
        ax.text(x + 0.9, y - h_head - h_attr - 1.3 - i * lh, m, ha="left", va="center", fontsize=fs, color=INK, zorder=4, family="DejaVu Sans Mono")
    return (x, y - h, w, h)


def save(fig, path):
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)
    print("saved", path)


MIN_FS = 8.0
W = 11.0


def save_min(fig, path):
    """Bump every text to at least MIN_FS points (readable when the page is scaled to half width), then save."""
    from matplotlib.text import Text

    for t in fig.findobj(Text):
        if t.get_text() and t.get_fontsize() < MIN_FS:
            t.set_fontsize(MIN_FS)
    save(fig, path)


def out(name):
    """Output path inside docs/diagrams/ (created on demand)."""
    import os

    from . import facts as F

    os.makedirs(F.DIAG, exist_ok=True)
    return os.path.join(F.DIAG, name)


def txt(ax, x, y, s, fs=8.5, color=INK, ha="center", bold=False, style="normal"):
    ax.text(x, y, s, ha=ha, va="center", fontsize=fs, color=color, fontweight="bold" if bold else "normal", style=style, zorder=6, linespacing=1.2)


def pline(ax, pts, color=GREY, lw=1.5, ls="-", head=True, label=None, lpos=None, fs=8):
    """Orthogonal polyline with an arrow head on the last segment; optional label at lpos."""
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, ls=ls, zorder=3, solid_capstyle="butt")
    a, b = pts[-2], pts[-1]
    if head:
        arrow(ax, a, b, color=color, lw=lw, ls=ls)
    else:
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, ls=ls, zorder=3)
    if label:
        lx, ly = lpos
        ax.text(lx, ly, label, ha="center", va="center", fontsize=fs, color=INK, zorder=5,
                bbox=dict(fc="white", ec="none", pad=0.8, alpha=0.9), linespacing=1.2)


def actor(ax, x, y, label, fs=8.5, color=NAVY):
    """UML stick figure with its feet at y; label below."""
    ax.add_patch(Circle((x, y + 6.6), 1.5, fc="white", ec=color, lw=1.5, zorder=4))
    ax.plot([x, x], [y + 5.1, y + 2.4], color=color, lw=1.5, zorder=4)
    ax.plot([x - 2.2, x + 2.2], [y + 4.2, y + 4.2], color=color, lw=1.5, zorder=4)
    ax.plot([x, x - 1.8], [y + 2.4, y], color=color, lw=1.5, zorder=4)
    ax.plot([x, x + 1.8], [y + 2.4, y], color=color, lw=1.5, zorder=4)
    ax.text(x, y - 1.5, label, ha="center", va="top", fontsize=fs, color=INK, zorder=5, linespacing=1.2)
