"""DFD level 2 (diagram 05): the domain-adaptation process 5.0 expanded."""

import os

from . import facts as F
from .dgm_lib import BLUE, GREY, INK, NAVY, PALE_BLUE, TEAL, arrow, box, canvas, ellipse, store
from .diagrams_dfd import save, txt

W = 11.0


def d_dfd2():
    fig, ax = canvas(W, 6.6, 100)          # height 60
    H_ = 100 * 6.6 / W
    box(ax, 9, 52, 15, 6.4, "Analyst\n(column, source,\ntarget)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8, r=0.5)
    store(ax, 9, 36, 15, 6.5, "D3\nFeature table", fs=8)
    ellipse(ax, 32, 44, 19, 11, "5.1\nSplit domains,\nhold out target test", fc="#DDF3EE", ec=TEAL, fs=8)
    ellipse(ax, 58, 54, 19, 10, "5.2\nTrain source model,\nscore target test", fc=PALE_BLUE, ec=BLUE, fs=8)
    ellipse(ax, 84, 44, 17, 11, "5.3\nTrain domain\nclassifier", fc=PALE_BLUE, ec=BLUE, fs=8)
    ellipse(ax, 84, 28, 17, 11, "5.4\nWeights p/(1-p),\nclip at 20", fc=PALE_BLUE, ec=BLUE, fs=8)
    ellipse(ax, 84, 12, 17, 10, "5.5\nTrain weighted\nXGBoost", fc=PALE_BLUE, ec=BLUE, fs=8)
    ellipse(ax, 58, 14, 19, 11, "5.6\nScore target test,\nbefore/after report", fc="#DDF3EE", ec=TEAL, fs=8)
    arrow(ax, (9, 48.8), (24.5, 46.5), color=NAVY)
    arrow(ax, (16.5, 36), (25.5, 40.5), color=GREY)
    arrow(ax, (38.5, 48.5), (50.2, 53), color=GREY)
    txt(ax, 38, 54.5, "source rows", 8, GREY)
    arrow(ax, (41.5, 43.6), (75.5, 44), color=GREY)
    txt(ax, 69, 46.4, "source + target features", 8, GREY)
    arrow(ax, (84, 38.5), (84, 33.5), color=GREY)
    txt(ax, 87.5, 36, "p", 8, GREY)
    arrow(ax, (84, 22.5), (84, 17), color=GREY)
    txt(ax, 90.5, 20, "weights", 8, GREY)
    arrow(ax, (75.5, 12.5), (67.5, 13.2), color=GREY)
    txt(ax, 71.5, 8.6, "adapted model", 8, GREY)
    arrow(ax, (58, 49), (58, 19.6), color=GREY)
    txt(ax, 66.5, 33, "before-adaptation\nmetrics", 8, GREY)
    arrow(ax, (35, 38.5), (51, 19.5), color=GREY)
    txt(ax, 32.5, 27.5, "target test rows", 8, GREY)
    box(ax, 9, 14, 15, 6.4, "Analyst\n(report, shift\ntable, accuracy)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8, r=0.5)
    arrow(ax, (48.5, 14), (16.7, 14), color=NAVY)
    store(ax, 32, 4.5, 18, 5, "D5  Model files", fs=8)
    arrow(ax, (51, 9.0), (41.2, 5.2), color=TEAL)
    txt(ax, 49, 2.6, "adapted model saved", 8, TEAL)
    ax.set_ylim(0, H_)
    save(fig, os.path.join(F.DIAG, "05_dfd_level2.png"))


DRAWERS = {"dfd2": d_dfd2}
