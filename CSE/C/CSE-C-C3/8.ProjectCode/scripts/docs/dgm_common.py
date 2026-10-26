"""Shared helpers for the ParkSure diagram modules (output path, minimum font size, text, UML boxes, polylines)."""

import os

import matplotlib.text
from matplotlib.patches import Circle, Rectangle

from . import facts as F
from .dgm_lib import GREY, INK, NAVY, WHITE, arrow, save as _save

MIN_FS = 8.0
W = 11.0


def out(name):
    os.makedirs(F.DIAG, exist_ok=True)
    return os.path.join(F.DIAG, name)


def save(fig, name):
    """Bump every text to at least MIN_FS points (readable when the page is scaled to half width), then save."""
    for t in fig.findobj(matplotlib.text.Text):
        if t.get_text() and t.get_fontsize() < MIN_FS:
            t.set_fontsize(MIN_FS)
    _save(fig, out(name))


def txt(ax, x, y, s, fs=8.5, color=INK, ha="center", bold=False, style="normal", bg=False, va="center"):
    ax.text(x, y, s, ha=ha, va=va, fontsize=fs, color=color, fontweight="bold" if bold else "normal", style=style, zorder=6,
            linespacing=1.2, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9) if bg else None)


def poly(ax, pts, color=GREY, lw=1.4, ls="-", head=True):
    """Polyline through pts with an arrow head on the last segment."""
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, ls=ls, zorder=3, solid_capstyle="butt")
    if head:
        arrow(ax, pts[-2], pts[-1], color=color, lw=lw, ls=ls)
    else:
        ax.plot([pts[-2][0], pts[-1][0]], [pts[-2][1], pts[-1][1]], color=color, lw=lw, ls=ls, zorder=3)


def uml(ax, x, y, w, name, attrs, methods, hdr=NAVY, stereotype=None, fs=10.0, lh=2.35):
    """UML class box, top-left corner at (x, y). Returns (x, y_bottom, w, h)."""
    h_head = 6.0 if stereotype else 4.4
    h_attr = lh * len(attrs) + 1.0 if attrs else 1.6
    h_meth = lh * len(methods) + 1.0 if methods else 1.6
    h = h_head + h_attr + h_meth
    ax.add_patch(Rectangle((x, y - h), w, h, fc=WHITE, ec=NAVY, lw=1.3, zorder=2))
    ax.add_patch(Rectangle((x, y - h_head), w, h_head, fc=hdr, ec=NAVY, lw=1.3, zorder=3))
    if stereotype:
        ax.text(x + w / 2, y - 1.5, f"<<{stereotype}>>", ha="center", va="center", color=WHITE, fontsize=9, zorder=4, style="italic")
        ax.text(x + w / 2, y - 4.2, name, ha="center", va="center", color=WHITE, fontsize=11, fontweight="bold", zorder=4)
    else:
        ax.text(x + w / 2, y - h_head / 2, name, ha="center", va="center", color=WHITE, fontsize=11, fontweight="bold", zorder=4)
    ax.plot([x, x + w], [y - h_head - h_attr, y - h_head - h_attr], color=NAVY, lw=1.0, zorder=3)
    for i, a in enumerate(attrs):
        ax.text(x + 0.9, y - h_head - 0.5 - lh * (i + 0.5), a, ha="left", va="center", fontsize=fs, color=INK, zorder=4, family="DejaVu Sans Mono")
    for i, m in enumerate(methods):
        ax.text(x + 0.9, y - h_head - h_attr - 0.5 - lh * (i + 0.5), m, ha="left", va="center", fontsize=fs, color=INK, zorder=4, family="DejaVu Sans Mono")
    return (x, y - h, w, h)


def actor(ax, cx, cy, label, color=NAVY, scale=1.0):
    """Stick figure with its head at (cx, cy)."""
    r = 1.6 * scale
    ax.add_patch(Circle((cx, cy), r, fc="white", ec=color, lw=1.6, zorder=3))
    ax.plot([cx, cx], [cy - r, cy - 6.5 * scale], color=color, lw=1.6, zorder=3)
    ax.plot([cx - 3 * scale, cx + 3 * scale], [cy - 3.2 * scale, cy - 3.2 * scale], color=color, lw=1.6, zorder=3)
    ax.plot([cx, cx - 2.6 * scale], [cy - 6.5 * scale, cy - 10.5 * scale], color=color, lw=1.6, zorder=3)
    ax.plot([cx, cx + 2.6 * scale], [cy - 6.5 * scale, cy - 10.5 * scale], color=color, lw=1.6, zorder=3)
    ax.text(cx, cy - 12.6 * scale, label, ha="center", va="center", fontsize=9, fontweight="bold", color=INK, zorder=4)
