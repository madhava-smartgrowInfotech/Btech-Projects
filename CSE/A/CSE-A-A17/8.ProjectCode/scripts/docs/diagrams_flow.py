"""Flowcharts 10 (core algorithm) and 11 (domain adaptation), drawn on one 5-column grid."""

import os

from . import facts as F
from .dgm_lib import GREY, INK, NAVY, BLUE, TEAL, ORANGE, PALE_ORANGE, arrow, box, canvas, diamond
from .diagrams_uml import save

W = 11.0
XS = [10.5, 30.5, 50.5, 70.5, 90.5]
BW, BH = 16.5, 8.6


def fb(ax, x, y, text, fc=NAVY, fs=8.0, w=BW, h=BH):
    box(ax, x, y, w, h, text, fc=fc, tc="white", fs=fs)


def tag(ax, x, y, text, w=20, h=4.6):
    box(ax, x, y, w, h, text, fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8.0, r=0.6, ls="--")


def txt(ax, x, y, s, fs=8.0, color=INK, bg=False):
    ax.text(x, y, s, ha="center", va="center", fontsize=fs, color=color, zorder=7, linespacing=1.15,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.95) if bg else None)


def d_flow_algo():
    HIN = 7.6
    fig, ax = canvas(W, HIN, 100)
    H_ = 100 * HIN / W
    r1, r2, r3 = 60, 39, 14
    s1 = ["Raw rows\ntransactions,\narticles, customers", "Clean\nparse t_dat; drop null ids,\nprice <= 0, exact\nduplicates", "Merge\nleft join articles\n(+ customers);\nmissing -> Unknown",
          "Aggregate\ncount rows per\n(t_dat, article_id)\n= units sold", "Fill missing days\ndemand = 0 between\nfirst and last sale"]
    for i, (x, t) in enumerate(zip(XS, s1)):
        fb(ax, x, r1, t, fc=GREY if i == 0 else NAVY)
        if i:
            arrow(ax, (XS[i - 1] + BW / 2, r1), (x - BW / 2, r1), color=GREY)
    arrow(ax, (XS[4], r1 - BH / 2), (XS[4], r2 + BH / 2), color=GREY)
    s2 = ["Features\nshift(1) first; lag 1,\n7, 14, 28; rolling mean\n7, 14, 28; std 7, 28", "Encode + calendar\n6 attributes -> codes;\n14 calendar features", "Split by date\nfirst 80 % of dates\ntrain, last 20 % test",
          "Train\nmoving average, XGBoost\n(optional tuning)", "Evaluate on test\nRMSE, MAE, MAPE, R2\nfeature importance"]
    xs2 = XS[::-1]
    for i, (x, t) in enumerate(zip(xs2, s2)):
        fb(ax, x, r2, t, fc=BLUE)
        if i:
            arrow(ax, (xs2[i - 1] - BW / 2, r2), (x + BW / 2, r2), color=GREY)
    ty = 28.5
    for x, t, w in ((88.5, "G1  shift(1) before rolling:\nthe current day is never\nin its own features", 20), (XS[2], "G2  split by date,\nnever at random", 17), (XS[1], "G3  tuning uses\nTimeSeriesSplit:\nvalidation is later", 17.5)):
        tag(ax, x, ty, t, w, 6.0 if "G1" in t or "G3" in t else 4.6)
        ax.plot([XS[1] if "G3" in t else (XS[2] if "G2" in t else XS[4])] * 2, [r2 - BH / 2, ty + 3.1], color=ORANGE, lw=0.9, ls=":", zorder=1)
    arrow(ax, (XS[0], r2 - BH / 2), (XS[0], r3 + BH / 2), color=GREY)
    fb(ax, XS[0], r3, "Save model\nmodels/baseline_\nxgboost.joblib", fc=TEAL)
    fb(ax, XS[1], r3, "Forecast loop\nrow = last known row;\nrefresh calendar, lags,\nrolling from history", fc=TEAL)
    diamond(ax, 54, r3, 21, 11, "step < horizon?\n(7, 14 or 30)", fs=8.0)
    fb(ax, 82, r3, "Forecast table\n+ chart; units per\nday, clipped at 0", fc=TEAL)
    arrow(ax, (XS[0] + BW / 2, r3), (XS[1] - BW / 2, r3), color=GREY)
    arrow(ax, (XS[1] + BW / 2, r3), (54 - 10.5, r3), color=GREY)
    arrow(ax, (54 + 10.5, r3), (82 - BW / 2, r3), color=GREY)
    txt(ax, 69, r3 + 2.3, "no", 8.0)
    # loop back (yes): above row 3, below the guard tags
    ly = 22.2
    ax.plot([54, 54, XS[1]], [r3 + 5.5, ly, ly], color=GREY, lw=1.5, zorder=3)
    arrow(ax, (XS[1], ly), (XS[1], r3 + BH / 2), color=GREY)
    txt(ax, 42, ly + 1.4, "yes: append the prediction to the history", 8.0)
    tag(ax, XS[1], 4.6, "G4  recursive forecast: each prediction\nfeeds the next day's lags", 30, 4.6)
    ax.set_ylim(0, H_)
    save(fig, os.path.join(F.DIAG, "10_flowchart_algorithm.png"))


def d_flow_da():
    HIN = 7.6
    fig, ax = canvas(W, HIN, 100)
    H_ = 100 * HIN / W
    r1, r2, r3 = 60, 37, 14
    fb(ax, XS[0], r1, "Feature table\n(31,094 rows in the\nreal subset)", fc=GREY)
    fb(ax, XS[1], r1, "Choose domain column,\nsource and target value\n(channel, group, dept.)")
    diamond(ax, 51, r1, 19, 11, "source != target\nand both have\nrows?", fs=8.0)
    fb(ax, 72, r1, "Drop the domain column\nfrom the features; split\nsource / target rows")
    fb(ax, 91.5, r1, "Target: first 50 % of\ndates unused here;\nlast 50 % = test")
    arrow(ax, (XS[0] + BW / 2, r1), (XS[1] - BW / 2, r1), color=GREY)
    arrow(ax, (XS[1] + BW / 2, r1), (51 - 9.5, r1), color=GREY)
    arrow(ax, (51 + 9.5, r1), (72 - BW / 2, r1), color=GREY)
    txt(ax, 62, r1 + 2.2, "yes", 8.0)
    arrow(ax, (72 + BW / 2, r1), (91.5 - BW / 2, r1), color=GREY)
    box(ax, 51, 48.2, 22, 3.8, "no: HTTP 400, nothing trained", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8.0, r=0.5)
    arrow(ax, (51, r1 - 5.5), (51, 50.2), color=ORANGE)
    arrow(ax, (91.5, r1 - BH / 2), (91.5, r2 + BH / 2), color=GREY)
    xs2 = [91.5, 72, 51, 30.5, 10.5]
    s2 = ["Train XGBoost on\nsource rows only\n(default parameters)", "Score the target\ntest rows =\nBEFORE metrics", "Domain classifier:\nlogistic regression,\nsource 0 vs target 1",
          "Importance weight\nw = p / (1 - p),\nclipped to [0, 20]", "Train XGBoost on\nsource rows with\nsample_weight = w"]
    for i, (x, t) in enumerate(zip(xs2, s2)):
        fb(ax, x, r2, t, fc=TEAL if i == 4 else BLUE)
        if i:
            arrow(ax, (xs2[i - 1] - BW / 2, r2), (x + BW / 2, r2), color=GREY)
    arrow(ax, (XS[0], r2 - BH / 2), (XS[0], r3 + BH / 2), color=GREY)
    xs3 = [10.5, 30.5, 51, 72]
    s3 = ["Score the same\ntarget test rows =\nAFTER metrics", "Report: RMSE, MAE,\nMAPE, R2 and\nimprovement %", "Save adapted model\nmodels/adapted_\nxgboost.joblib", "Return JSON: shift\ntable, histogram, box\nplot, weights, report"]
    for i, (x, t) in enumerate(zip(xs3, s3)):
        fb(ax, x, r3, t, fc=TEAL)
        if i:
            arrow(ax, (xs3[i - 1] + BW / 2, r3), (x - BW / 2, r3), color=GREY)
    ty = 25.5
    tag(ax, 34, ty, "Measured: weights are not normalised; for\nperfectly separable domains p/(1-p) is about\n1e-5 and XGBoost collapses to a constant", 38, 6.4)
    tag(ax, 73.5, ty, "Measured: source rows include dates inside the\ntarget test window; removing them erases the\nonly clear gain (time-clean protocol)", 38, 6.4)
    ax.set_ylim(0, H_)
    save(fig, os.path.join(F.DIAG, "11_flowchart_domain_adaptation.png"))


DRAWERS = {"flow_algo": d_flow_algo, "flow_da": d_flow_da}
