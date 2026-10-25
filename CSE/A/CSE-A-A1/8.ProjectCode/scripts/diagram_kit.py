"""Small matplotlib drawing kit for the design diagrams (boxes, arrows, data stores, actors, lifelines)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

INK = "#1f2937"
MUTED = "#5b6475"
VIOLET, VIOLET_BG = "#6d5ae6", "#ece9fd"
CYAN, CYAN_BG = "#0e9fb3", "#dff6fa"
GREEN, GREEN_BG = "#23956a", "#dcf4ea"
AMBER, AMBER_BG = "#c98412", "#fcefd3"
ROSE, ROSE_BG = "#c9425c", "#fbe3e8"
GREY, GREY_BG = "#7b8597", "#eef0f4"
WHITE = "#ffffff"

THEMES = {"violet": (VIOLET, VIOLET_BG), "cyan": (CYAN, CYAN_BG), "green": (GREEN, GREEN_BG), "amber": (AMBER, AMBER_BG),
          "rose": (ROSE, ROSE_BG), "grey": (GREY, GREY_BG), "white": (INK, WHITE)}


def canvas(w, h, xlim=(0, 100), ylim=None):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim)
    ax.set_ylim(*(ylim or (0, 100 * h / w)))
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text="", theme="white", fs=9, bold=False, round_=1.2, lw=1.4, align="center", ls="-", color=None, z=2):
    ec, fc = THEMES[theme]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={round_}", fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))
    if text:
        if align == "center":
            ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=color or INK,
                    fontweight="bold" if bold else "normal", zorder=z + 1, linespacing=1.25)
        else:
            ax.text(x + 1.2, y + h - 1.0, text, ha="left", va="top", fontsize=fs, color=color or INK, zorder=z + 1, linespacing=1.3)
    return (x, y, w, h)


def label(ax, x, y, text, fs=8.5, color=MUTED, ha="center", va="center", bold=False, italic=False, rot=0, bg=None):
    ax.text(x, y, text, ha=ha, va=va, fontsize=fs, color=color, fontweight="bold" if bold else "normal",
            fontstyle="italic" if italic else "normal", rotation=rot, zorder=6, linespacing=1.2,
            bbox=dict(fc=bg, ec="none", pad=1.2) if bg else None)


def arrow(ax, p, q, text=None, theme="grey", lw=1.4, style="-|>", rad=0.0, fs=8, ls="-", tpos=0.5, toff=(0, 0), bg=WHITE, z=4):
    ec = THEMES[theme][0] if theme in THEMES else theme
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=11, lw=lw, color=ec, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0, zorder=z))
    if text:
        mx, my = p[0] + (q[0] - p[0]) * tpos + toff[0], p[1] + (q[1] - p[1]) * tpos + toff[1]
        ax.text(mx, my, text, ha="center", va="center", fontsize=fs, color=INK, zorder=z + 2,
                bbox=dict(fc=bg, ec="none", pad=1.0), linespacing=1.15)


def poly_arrow(ax, pts, text=None, theme="grey", lw=1.4, fs=8, ls="-", tidx=0, toff=(0, 0), bg=WHITE):
    ec = THEMES[theme][0]
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=ec, lw=lw, ls=ls, zorder=4, solid_capstyle="round")
    arrow(ax, pts[-2], pts[-1], theme=theme, lw=lw, ls=ls)
    if text:
        a, b = pts[tidx], pts[tidx + 1]
        ax.text((a[0] + b[0]) / 2 + toff[0], (a[1] + b[1]) / 2 + toff[1], text, ha="center", va="center", fontsize=fs, color=INK,
                zorder=7, bbox=dict(fc=bg, ec="none", pad=1.0), linespacing=1.15)


def store(ax, x, y, w, h, text, theme="amber", fs=8.5):
    """DFD data store: open rectangle with left bar."""
    ec, fc = THEMES[theme]
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=1.4, zorder=2))
    ax.plot([x + 3.2, x + 3.2], [y, y + h], color=ec, lw=1.4, zorder=3)
    ax.text(x + 3.2 + (w - 3.2) / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK, zorder=4, linespacing=1.2)


def cylinder(ax, x, y, w, h, text, theme="amber", fs=9):
    ec, fc = THEMES[theme]
    e = h * 0.16
    ax.add_patch(Rectangle((x, y + e / 2), w, h - e, fc=fc, ec="none", zorder=2))
    ax.plot([x, x], [y + e / 2, y + h - e / 2], color=ec, lw=1.4, zorder=3)
    ax.plot([x + w, x + w], [y + e / 2, y + h - e / 2], color=ec, lw=1.4, zorder=3)
    ax.add_patch(Ellipse((x + w / 2, y + e / 2), w, e, fc=fc, ec=ec, lw=1.4, zorder=3))
    ax.add_patch(Ellipse((x + w / 2, y + h - e / 2), w, e, fc=fc, ec=ec, lw=1.4, zorder=4))
    ax.text(x + w / 2, y + h / 2 - e / 4, text, ha="center", va="center", fontsize=fs, color=INK, zorder=5, linespacing=1.2)


def circle_process(ax, cx, cy, r, text, theme="violet", fs=8.5, num=None):
    ec, fc = THEMES[theme]
    ax.add_patch(Ellipse((cx, cy), 2 * r, 2 * r, fc=fc, ec=ec, lw=1.5, zorder=2))
    if num:
        ax.text(cx, cy + r * 0.52, num, ha="center", va="center", fontsize=fs, color=ec, fontweight="bold", zorder=4)
        ax.text(cx, cy - r * 0.12, text, ha="center", va="center", fontsize=fs, color=INK, zorder=4, linespacing=1.15)
    else:
        ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, zorder=4, linespacing=1.15)


def diamond(ax, cx, cy, w, h, text, theme="amber", fs=8.5):
    ec, fc = THEMES[theme]
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], closed=True, fc=fc, ec=ec, lw=1.4, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, zorder=4, linespacing=1.15)


def terminator(ax, cx, cy, w, h, text, theme="green", fs=9):
    box(ax, cx - w / 2, cy - h / 2, w, h, text, theme=theme, fs=fs, round_=h / 2, bold=True)


def actor(ax, x, y, text, theme="violet", s=1.0, fs=9):
    ec = THEMES[theme][0]
    ax.add_patch(Ellipse((x, y + 7.6 * s), 3.4 * s, 3.4 * s, fc=WHITE, ec=ec, lw=1.6, zorder=3))
    ax.plot([x, x], [y + 5.9 * s, y + 2.2 * s], color=ec, lw=1.6, zorder=3)
    ax.plot([x - 2.4 * s, x + 2.4 * s], [y + 4.8 * s, y + 4.8 * s], color=ec, lw=1.6, zorder=3)
    ax.plot([x, x - 2.2 * s], [y + 2.2 * s, y - 0.8 * s], color=ec, lw=1.6, zorder=3)
    ax.plot([x, x + 2.2 * s], [y + 2.2 * s, y - 0.8 * s], color=ec, lw=1.6, zorder=3)
    ax.text(x, y - 2.2 * s, text, ha="center", va="top", fontsize=fs, color=INK, fontweight="bold", zorder=4, linespacing=1.15)


def lifeline(ax, x, y_top, y_bot, text, theme="violet", w=14, h=4.6, fs=8.5):
    ec, fc = THEMES[theme]
    box(ax, x - w / 2, y_top, w, h, text, theme=theme, fs=fs, bold=True, round_=0.8)
    ax.plot([x, x], [y_top, y_bot], color=ec, lw=1.0, ls=(0, (4, 3)), zorder=1)


def activation(ax, x, y0, y1, theme="violet", w=1.6):
    ec, fc = THEMES[theme]
    ax.add_patch(Rectangle((x - w / 2, y1), w, y0 - y1, fc=fc, ec=ec, lw=1.0, zorder=3))


def title(ax, text, y=None, fs=11):
    x0, x1 = ax.get_xlim()
    y1 = ax.get_ylim()[1]
    ax.text((x0 + x1) / 2, (y if y is not None else y1 - 1.2), text, ha="center", va="top", fontsize=fs, color=INK, fontweight="bold")


def save(fig, path):
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=WHITE, pad_inches=0.08)
    plt.close(fig)
    print("wrote", path)
