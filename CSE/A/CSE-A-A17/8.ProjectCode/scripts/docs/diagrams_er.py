"""Logical ER diagram (09) and the use-case diagram (08)."""

import os

from matplotlib.patches import Circle, Rectangle

from . import facts as F
from .dgm_lib import BLUE, GREY, INK, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_TEAL, PURPLE, TEAL, arrow, canvas, ellipse
from .diagrams_uml import cls, save

W = 11.0


def txt(ax, x, y, s, fs=8.0, color=INK, bold=False, bg=False):
    ax.text(x, y, s, ha="center", va="center", fontsize=fs, color=color, fontweight="bold" if bold else "normal", zorder=7, linespacing=1.15,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.95) if bg else None)


def d_er():
    fig, ax = canvas(W, 8.4, 100)          # height 76.4
    H_ = 100 * 8.4 / W
    top, mid, low = 73.5, 47.0, 21.5
    cust = cls(ax, 1, top, 21, "Customer", "entity", ["customer_id  PK", "age", "club_member_status", "fashion_news_freq.", "postal_code"], [], hdr=BLUE)
    tx = cls(ax, 27, top, 22, "Transaction", "entity", ["t_dat", "customer_id  FK", "article_id  FK", "price", "sales_channel_id"], [], hdr=NAVY)
    art = cls(ax, 54, top, 22, "Article", "entity", ["article_id  PK", "prod_name", "product_type_name", "product_group_name", "colour_group_name", "department_name", "section_name", "garment_group_name"], [], hdr=BLUE)
    fc = cls(ax, 80, top, 19, "Forecast", "derived", ["article_id", "horizon  7|14|30", "t_dat", "predicted_demand"], [], hdr=PURPLE)
    dd = cls(ax, 27, mid, 22, "DailyDemand", "derived", ["t_dat", "article_id", "demand  (units)", "price  (mean)", "sales_channel_id (mode)", "product attributes"], [], hdr=NAVY)
    fr = cls(ax, 54, mid, 22, "FeatureRow", "derived", ["t_dat", "article_id", "demand  (target)", "calendar  (14)", "lag / rolling  (9)", "price, channel, 6 codes"], [], hdr=NAVY)
    mf = cls(ax, 80, mid, 19, "ModelFile", "file", ["kind  baseline|adapted", "path  models/*.joblib", "feature_cols  list"], [], hdr=TEAL)
    dr = cls(ax, 54, low, 22, "DomainRun", "derived", ["domain_col", "source, target", "classifier_accuracy", "weights  mean/min/max", "before  RMSE MAE MAPE R2", "after   RMSE MAE MAPE R2"], [], hdr=TEAL)

    def line(pts, a=None, b=None, label=None, lp=None):
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=GREY, lw=1.5, zorder=3)
        if a:
            txt(ax, a[0], a[1], a[2], 8.5, NAVY, True)
        if b:
            txt(ax, b[0], b[1], b[2], 8.5, NAVY, True)
        if label:
            txt(ax, lp[0], lp[1], label, 8.0, INK, False, True)

    line([(22, 66), (27, 66)], (23.3, 67.6, "1"), (25.7, 67.6, "N"), "places", (24.5, 63.2))
    line([(49, 66), (54, 66)], (50.3, 67.6, "N"), (52.7, 67.6, "1"), "is of", (51.5, 63.2))
    line([(76, 66), (80, 66)], (77.0, 67.6, "1"), (79.0, 67.6, "N"), "for", (78, 63.2))
    line([(38, tx[1]), (38, mid)], (36.4, tx[1] - 1.6, "N"), (36.4, mid + 1.6, "1"), "aggregated by" + chr(10) + "(date, article)", (45.5, (tx[1] + mid) / 2))
    line([(49, 37), (54, 37)], (50.3, 38.6, "1"), (52.7, 38.6, "1"), "becomes", (51.5, 34.2))
    line([(76, 37), (80, 37)], (77.0, 38.6, "N"), (79.0, 38.6, "1"), "trains", (78, 34.2))
    line([(65, fr[1]), (65, low)], (63.6, fr[1] - 1.6, "N"), (63.6, low + 1.6, "1"), "adapted in", (71.5, (fr[1] + low) / 2))
    line([(76, 8.5), (89.5, 8.5), (89.5, mf[1])], (77.4, 10.2, "N"), (91.1, mf[1] - 1.6, "1"), "produces", (83, 6.0))
    line([(89.5, fc[1]), (89.5, mid)], (91.1, fc[1] - 1.6, "N"), (91.1, mid + 1.6, "1"), "uses", (94.5, (fc[1] + mid) / 2))
    ax.set_ylim(0, H_)
    save(fig, os.path.join(F.DIAG, "09_er_diagram.png"))


def actor(ax, x, y, label, c):
    ax.add_patch(Circle((x, y + 4.3), 1.4, fc="white", ec=c, lw=1.6, zorder=3))
    ax.plot([x, x], [y + 2.9, y - 1.8], color=c, lw=1.6, zorder=3)
    ax.plot([x - 2.4, x + 2.4], [y + 1.3, y + 1.3], color=c, lw=1.6, zorder=3)
    ax.plot([x, x - 2], [y - 1.8, y - 5], color=c, lw=1.6, zorder=3)
    ax.plot([x, x + 2], [y - 1.8, y - 5], color=c, lw=1.6, zorder=3)
    txt(ax, x, y - 7.6, label, 8.8, c, True)


def d_uc():
    fig, ax = canvas(W, 7.4, 100)          # height 67.3
    H_ = 100 * 7.4 / W
    ax.add_patch(Rectangle((22, 1.2), 56, 65, fc="#FAFBFD", ec=NAVY, lw=1.5, zorder=0))
    txt(ax, 50, 64.2, "TrendCast (system boundary)", 9.5, NAVY, True)
    cases = ["Upload data", "Explore data", "View aggregated demand table", "Build features", "Train baseline and XGBoost", "Run domain adaptation",
             "Review evaluation and importance", "Generate 7 / 14 / 30-day forecast", "Ask for AI explanation", "Run experiments, tests, screenshots"]
    ys = [59.0 - i * 5.95 for i in range(len(cases))]
    cx = 42
    pos = dict(zip(cases, ys))
    for c, y in pos.items():
        dev = "experiments" in c
        ellipse(ax, cx, y, 31, 3.9, c, fc=PALE_ORANGE if dev else PALE_BLUE, ec=ORANGE if dev else BLUE, fs=8.2)
    ellipse(ax, 68, pos["Train baseline and XGBoost"], 17, 3.9, "Tune hyperparameters", fc=PALE_TEAL, ec=TEAL, fs=8.2)
    actor(ax, 8, 32, "Analyst", NAVY)
    actor(ax, 91, 33, "Gemini service\n(optional)", PURPLE)
    actor(ax, 91, 13, "Developer /\nevaluator", ORANGE)
    for c in cases[:-1]:
        ax.plot([11, 26.5], [33.3, pos[c]], color=NAVY, lw=0.9, zorder=1)
    ax.plot([88, 57.5], [34.3, pos["Ask for AI explanation"]], color=PURPLE, lw=1.1, zorder=1)
    ax.plot([88, 57.5], [14.3, pos["Run experiments, tests, screenshots"]], color=ORANGE, lw=1.1, zorder=1)
    g = 1.95
    arrow(ax, (cx - 9, pos["Train baseline and XGBoost"] + g), (cx - 9, pos["Build features"] - g), color=GREY, ls="--", lw=1.1)
    txt(ax, cx - 16.5, (pos["Train baseline and XGBoost"] + pos["Build features"]) / 2, "<<include>>", 7.8, GREY, bg=True)
    arrow(ax, (cx + 9, pos["Run domain adaptation"] + g), (cx + 9, pos["Train baseline and XGBoost"] - g), color=GREY, ls="--", lw=1.1)
    txt(ax, cx + 16.5, (pos["Run domain adaptation"] + pos["Train baseline and XGBoost"]) / 2, "<<include>>", 7.8, GREY, bg=True)
    arrow(ax, (59.5, pos["Train baseline and XGBoost"]), (57.7, pos["Train baseline and XGBoost"]), color=GREY, ls="--", lw=1.1)
    txt(ax, 64, pos["Train baseline and XGBoost"] + 3.6, "<<extend>>", 7.8, GREY, bg=True)
    ya, yr = pos["Ask for AI explanation"], pos["Review evaluation and importance"]
    ax.plot([57.7, 61, 61], [ya, ya, yr], color=GREY, lw=1.1, ls="--", zorder=3)
    arrow(ax, (61, yr), (57.7, yr), color=GREY, ls="--", lw=1.1)
    txt(ax, 66.5, (ya + yr) / 2, "<<extend>>", 7.8, GREY, bg=True)
    ax.set_ylim(0, H_)
    save(fig, os.path.join(F.DIAG, "08_use_case.png"))


DRAWERS = {"er": d_er, "uc": d_uc}
