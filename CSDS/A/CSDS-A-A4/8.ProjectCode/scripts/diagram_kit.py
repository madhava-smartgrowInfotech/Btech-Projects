"""Tiny matplotlib drawing kit used by make_diagrams.py (boxes, arrows, lifelines; no system dependency)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Ellipse, FancyBboxPatch, Polygon, Rectangle  # noqa: E402

INK = "#1b2238"
INDIGO = "#3f3fbf"
INDIGO_L = "#e6e6fb"
BLUE_L = "#dbe8fb"
GREEN_L = "#d9f2e4"
AMBER_L = "#fbebc8"
ROSE_L = "#fbdcdc"
GREY_L = "#eef0f4"
LINE = "#44506b"
DPI = 150


class Canvas:
    """A drawing surface measured in tenths of an inch (so 1 unit = 0.1 in)."""

    def __init__(self, w_in: float, h_in: float, title: str | None = None):
        self.fig, self.ax = plt.subplots(figsize=(w_in, h_in))
        self.W, self.H = w_in * 10, h_in * 10
        self.ax.set_xlim(0, self.W)
        self.ax.set_ylim(0, self.H)
        self.ax.axis("off")
        self.fig.subplots_adjust(0.005, 0.005, 0.995, 0.995)
        if title:
            self.ax.text(self.W / 2, self.H - 4, title, ha="center", va="top", fontsize=12, fontweight="bold", color=INK)

    # ---- shapes -------------------------------------------------------
    def box(self, x, y, w, h, text="", fc="white", ec=INK, fs=8.5, bold=False, lw=1.2, r=2.0, align="center",
            color=INK, ls="-", va="center", pad=1.2):
        """Rounded box with (x, y) = bottom-left."""
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, ls=ls))
        if text:
            tx = x + w / 2 if align == "center" else x + pad
            ty = y + h / 2 if va == "center" else y + h - pad
            self.ax.text(tx, ty, text, ha=align, va=va, fontsize=fs, fontweight="bold" if bold else "normal",
                         color=color, linespacing=1.25)
        return {"x": x, "y": y, "w": w, "h": h}

    def rect(self, x, y, w, h, fc="white", ec=INK, lw=1.0, ls="-", alpha=1.0, z=0):
        self.ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, ls=ls, alpha=alpha, zorder=z))

    def zone(self, x, y, w, h, label, fc=GREY_L, ec="#9aa5ba", fs=9):
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=3", fc=fc, ec=ec, lw=1.0, ls="--", zorder=0))
        self.ax.text(x + 2.5, y + h - 1.8, label, ha="left", va="top", fontsize=fs, fontweight="bold", color="#3a4560", zorder=1)

    def ellipse(self, cx, cy, w, h, text, fc=INDIGO_L, ec=INDIGO, fs=8):
        self.ax.add_patch(Ellipse((cx, cy), w, h, fc=fc, ec=ec, lw=1.2))
        self.ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)

    def diamond(self, cx, cy, w, h, text, fc=AMBER_L, ec=INK, fs=8):
        self.ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], fc=fc, ec=ec, lw=1.2))
        self.ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)
        return {"x": cx - w / 2, "y": cy - h / 2, "w": w, "h": h}

    def terminal(self, cx, cy, w, h, text, fc=GREEN_L, fs=8.5):
        return self.box(cx - w / 2, cy - h / 2, w, h, text, fc=fc, r=h / 2, fs=fs, bold=True)

    def text(self, x, y, s, fs=8.5, ha="center", va="center", bold=False, color=INK, italic=False, rot=0):
        self.ax.text(x, y, s, fontsize=fs, ha=ha, va=va, fontweight="bold" if bold else "normal", color=color,
                     style="italic" if italic else "normal", rotation=rot, linespacing=1.25)

    # ---- lines --------------------------------------------------------
    def arrow(self, p, q, label=None, color=LINE, lw=1.2, ls="-", head=True, fs=7.5, lpos=0.5, loff=(0, 1.6), lha="center",
              both=False, bg="white"):
        style = "<|-|>" if both else ("-|>" if head else "-")
        self.ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle=style, lw=lw, color=color, ls=ls, shrinkA=0, shrinkB=0,
                                                              mutation_scale=9))
        if label:
            mx, my = p[0] + (q[0] - p[0]) * lpos, p[1] + (q[1] - p[1]) * lpos
            self.ax.text(mx + loff[0], my + loff[1], label, fontsize=fs, ha=lha, va="center", color=INK,
                         bbox=dict(fc=bg, ec="none", pad=0.6, alpha=0.92), zorder=5)

    def path(self, pts, label=None, color=LINE, lw=1.2, ls="-", head=True, fs=7.5, seg=0, loff=(0, 1.6), lha="center"):
        """Poly-line with an arrow head on the last leg; label sits at the middle of leg `seg`."""
        for a, b in zip(pts[:-2], pts[1:-1]):
            self.ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, ls=ls, solid_capstyle="butt")
        self.arrow(pts[-2], pts[-1], color=color, lw=lw, ls=ls, head=head)
        if label:
            a, b = pts[seg], pts[seg + 1]
            self.ax.text((a[0] + b[0]) / 2 + loff[0], (a[1] + b[1]) / 2 + loff[1], label, fontsize=fs, ha=lha, va="center",
                         color=INK, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.92), zorder=5)

    def line(self, p, q, color=LINE, lw=1.0, ls="-"):
        self.ax.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=lw, ls=ls, solid_capstyle="butt")

    def save(self, path):
        self.fig.savefig(path, dpi=DPI, facecolor="white")
        plt.close(self.fig)


def anchor(b, side):
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    return {"l": (x, y + h / 2), "r": (x + w, y + h / 2), "t": (x + w / 2, y + h), "b": (x + w / 2, y), "c": (x + w / 2, y + h / 2)}[side]
