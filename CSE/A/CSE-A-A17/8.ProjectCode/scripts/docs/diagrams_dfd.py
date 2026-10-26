"""DFD level 1 (diagram 04) - kept apart so the layout can be tuned on its own."""

import os

from . import facts as F
from .dgm_lib import BLUE, GREY, INK, LIGHT, NAVY, PALE_BLUE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, arrow, box, canvas, ellipse, save as _save, store

MIN_FS = 8.0


def save(fig, path):
    """Bump every text to at least MIN_FS points (readable when the page is scaled to half width), then save."""
    for t in fig.findobj(__import__("matplotlib.text", fromlist=["Text"]).Text):
        if t.get_text() and t.get_fontsize() < MIN_FS:
            t.set_fontsize(MIN_FS)
    _save(fig, path)


W = 11.0


def txt(ax, x, y, s, fs=8.5, color=INK):
    ax.text(x, y, s, ha="center", va="center", fontsize=fs, color=color, zorder=6, linespacing=1.2)


def d_dfd1():
    fig, ax = canvas(W, 7.4, 100)          # height 67.3
    H_ = 100 * 7.4 / W
    E = dict(fc=PALE_BLUE, ec=BLUE, fs=8.2)
    ellipse(ax, 16, 56, 16, 10, "1.0\nIngest and\nclean", **E)
    ellipse(ax, 52, 56, 16, 10, "2.0\nAggregate daily\ndemand", **E)
    ellipse(ax, 86, 56, 16, 10, "3.0\nBuild\nfeatures", **E)
    store(ax, 34, 56, 13, 5, "D1  Merged\ntransactions", fs=7.6)
    store(ax, 69, 56, 13, 5, "D2  Daily\ndemand", fs=7.6)
    for a_, b_ in ((24, 27.5), (40.5, 44), (60, 62.5), (75.5, 78)):
        arrow(ax, (a_, 56), (b_, 56), color=GREY)
    box(ax, 12, 65, 22, 3.4, "Dataset provider (CSV files)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=7.8, r=0.5)
    box(ax, 38, 65, 14, 3.4, "Analyst", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8.2, r=0.5)
    arrow(ax, (13, 63.3), (14, 61), color=NAVY)
    arrow(ax, (34, 63.3), (21, 59.8), "files, row limit", lo=(-4.5, -2.0), fs=7.4, color=NAVY)
    # feature table: tall store on the right
    store(ax, 90, 28, 11, 34, "D3\nFeature\ntable", fs=8)
    arrow(ax, (88, 51), (88, 45.3), color=GREY)
    P = dict(fc=PALE_BLUE, ec=BLUE, fs=8)
    ellipse(ax, 62, 34, 19, 10, "4.0\nSplit and train", **P)
    ellipse(ax, 62, 23, 19, 10, "5.0\nDomain adaptation", fc=PALE_TEAL, ec=TEAL, fs=8)
    ellipse(ax, 62, 12, 19, 10, "6.0\nEvaluate and forecast", **P)
    for y in (34, 23, 12):
        arrow(ax, (84.4, y), (71.7, y), color=GREY)
    txt(ax, 78, 35.6, "features", 7.4, GREY)
    # results store (tall, left) and model store
    store(ax, 8, 29, 11, 34, "D4\nResults\n(metrics)", fs=8)
    for y, lab in ((34, "metrics"), (23, "before / after"), (12, "comparison, forecast")):
        arrow(ax, (52.4, y), (13.8, y), color=GREY)
        txt(ax, 24, y + 1.5, lab, 7.4, GREY)
    store(ax, 33, 28.5, 20, 4.4, "D5  Model files (joblib)", fs=7.6)
    arrow(ax, (53.5, 36.0), (41, 30.8), color=GREY)
    txt(ax, 46.5, 36.4, "model", 7.4, GREY)
    arrow(ax, (53.5, 25.0), (43.2, 27.4), color=TEAL)
    txt(ax, 49.5, 28.8, "adapted model", 7.4, TEAL)
    arrow(ax, (38, 26.2), (55, 15.4), color=GREY)
    txt(ax, 41.5, 18.2, "model", 7.4, GREY)
    # explain
    ellipse(ax, 33, 42, 17, 9, "7.0\nExplain\n(optional)", fc=PALE_PURPLE, ec=PURPLE, fs=8)
    arrow(ax, (13.8, 42), (24.5, 42), color=GREY)
    box(ax, 33, 50.6, 14, 3.0, "Gemini service", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=7.8, r=0.5, ls="--")
    arrow(ax, (30.5, 46.5), (30.5, 49.0), color=PURPLE)
    arrow(ax, (35.5, 49.0), (35.5, 46.5), color=PURPLE)
    txt(ax, 25.8, 48.3, "summary", 7.2, PURPLE)
    txt(ax, 40.3, 48.3, "text", 7.2, PURPLE)
    box(ax, 45, 3.4, 62, 4.6, "The analyst also supplies the training fraction and tuning flag (4.0), the domain choice (5.0),\nthe forecast request (6.0) and a question (7.0), and receives each result through the console.",
        fc=LIGHT, tc=INK, ec=GREY, fs=7.4, r=0.5)
    ax.set_ylim(0, H_)
    save(fig, os.path.join(F.DIAG, "04_dfd_level1.png"))


DRAWERS = {"dfd1": d_dfd1}
