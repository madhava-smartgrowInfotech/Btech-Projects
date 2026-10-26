"""Diagrams 07-12: sequence, use case, ER, two flowcharts and the model architecture (see make_diagrams.py)."""

import os

from . import facts as F
from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, WHITE,
                      arrow, box, canvas, diamond, ellipse, panel, save as _save, uml_class)

MIN_FS = 8.0


def save(fig, path):
    """Bump every text to at least MIN_FS points (readable when the page is scaled to half width), then save."""
    for t in fig.findobj(__import__("matplotlib.text", fromlist=["Text"]).Text):
        if t.get_text() and t.get_fontsize() < MIN_FS:
            t.set_fontsize(MIN_FS)
    _save(fig, path)


W = 11.0


def out(name):
    os.makedirs(F.DIAG, exist_ok=True)
    return os.path.join(F.DIAG, name)


def txt(ax, x, y, s, fs=8.5, color=INK, ha="center", bold=False, style="normal"):
    ax.text(x, y, s, ha=ha, va="center", fontsize=fs, color=color, fontweight="bold" if bold else "normal", style=style, zorder=6, linespacing=1.2)


# ------------------------------------------------------------------------------------------------ 07 sequence
def d_seq():
    fig, ax = canvas(W, 7.9, 100)          # height 71.8
    H_ = 100 * 7.9 / W
    heads = [(8, "Browser\n(React page)", NAVY), (24, "Vite proxy\n:5317", TEAL), (41, "FastAPI route\n/api/domain/run", NAVY),
             (58, "State S\n+ RLock", ORANGE), (75, "src/ modules", BLUE), (91, "models/\n(joblib)", TEAL)]
    top = 68.0
    for x, t, c in heads:
        box(ax, x, top, 14.5, 5.4, t, fc=c, fs=8.2, bold=True, r=0.8)
        ax.plot([x, x], [top - 2.7, 1.5], color=GREY, ls="--", lw=1.0, zorder=1)
    X = {n: h[0] for n, h in zip(("b", "v", "f", "s", "m", "j"), heads)}

    def msg(a, b, y, label, dashed=False, color=NAVY, above=True):
        x1, x2 = X[a], X[b]
        arrow(ax, (x1, y), (x2, y), color=color, lw=1.3, ls="--" if dashed else "-")
        mx = (x1 + x2) / 2
        ax.text(mx, y + 0.9, label, ha="center", va="bottom", fontsize=7.6, color=INK, zorder=6, linespacing=1.15,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))

    def note(x, y, s, w=24, fc=PALE_ORANGE, ec=ORANGE):
        box(ax, x, y, w, 3.6, s, fc=fc, tc=INK, ec=ec, fs=7.4, r=0.5)

    y = 60.4
    msg("b", "v", y, "1  POST /api/domain/run\n{domain_col, source, target}"); y -= 4.6
    msg("v", "f", y, "2  forward to 127.0.0.1:8317"); y -= 4.0
    msg("f", "s", y, "3  with LOCK; need('feature_table')"); y -= 4.3
    note(41, y, "4  validate: column allowed,\nsource != target, both non-empty", 27); y -= 4.6
    msg("f", "m", y, "5  split_domains();  chronological_split(target, 0.5)"); y -= 4.4
    msg("f", "m", y, "6  train_xgboost(source);  evaluate_model()  = before"); y -= 4.4
    msg("f", "m", y, "7  train_domain_classifier();  domain_shift_summary()"); y -= 4.4
    msg("f", "m", y, "8  compute_instance_weights();  train_adapted_model()"); y -= 4.4
    msg("f", "m", y, "9  evaluate_model() = after;  before_after_report()"); y -= 4.4
    msg("f", "j", y, "10  joblib.dump(adapted_xgboost.joblib)", color=TEAL); y -= 4.2
    msg("f", "s", y, "11  S['domain_eval'], S['domain_run'] = result"); y -= 4.4
    msg("f", "v", y, "12  200 JSON: shift table, histogram, box, report", dashed=True, color=TEAL)
    msg("v", "b", y - 3.7, "13  response", dashed=True, color=TEAL); y -= 8.0
    note(12, y - 0.2, "14  draw histogram, box plot,\nbefore/after cards", 20, PALE_BLUE, BLUE)
    save(fig, out("07_sequence_flow.png"))
    return H_


# ------------------------------------------------------------------------------------------------ 08 use case
def d_uc():
    fig, ax = canvas(W, 7.4, 100)          # height 67.3
    H_ = 100 * 7.4 / W
    ax.add_patch(__import__("matplotlib.patches", fromlist=["Rectangle"]).Rectangle((22, 1.5), 56, 64, fc="#FAFBFD", ec=NAVY, lw=1.5, zorder=0))
    txt(ax, 50, 63.3, "TrendCast (system boundary)", 9.5, NAVY, bold=True)
    cases = ["Upload data", "Explore data", "View aggregated demand table", "Build features", "Train baseline and XGBoost", "Run domain adaptation",
             "Review evaluation and importance", "Generate 7 / 14 / 30-day forecast", "Ask for AI explanation", "Run experiments, tests, screenshots"]
    ys = [57.2 - i * 5.55 for i in range(len(cases))]
    cx = 42
    pos = {}
    for c, y in zip(cases, ys):
        ellipse(ax, cx, y, 30, 4.6, c, fc=PALE_BLUE if "experiments" not in c else PALE_ORANGE, ec=BLUE if "experiments" not in c else ORANGE, fs=8.3)
        pos[c] = y
    ellipse(ax, 68, pos["Train baseline and XGBoost"], 17, 4.6, "Tune hyperparameters", fc=PALE_TEAL, ec=TEAL, fs=8)
    # actors
    def actor(x, y, label, c):
        ax.add_patch(__import__("matplotlib.patches", fromlist=["Circle"]).Circle((x, y + 4.3), 1.4, fc="white", ec=c, lw=1.6, zorder=3))
        ax.plot([x, x], [y + 2.9, y - 1.8], color=c, lw=1.6, zorder=3)
        ax.plot([x - 2.4, x + 2.4], [y + 1.3, y + 1.3], color=c, lw=1.6, zorder=3)
        ax.plot([x, x - 2], [y - 1.8, y - 5], color=c, lw=1.6, zorder=3)
        ax.plot([x, x + 2], [y - 1.8, y - 5], color=c, lw=1.6, zorder=3)
        txt(ax, x, y - 7.4, label, 8.8, c, bold=True)
    actor(8, 32, "Analyst", NAVY)
    actor(91, 54.2, "Gemini service\n(optional)", PURPLE)
    actor(91, 13, "Developer /\nevaluator", ORANGE)
    for c in cases[:-1]:
        ax.plot([11, 27], [32 + 1.3, pos[c]], color=NAVY, lw=0.9, zorder=1)
    ax.plot([87.5, 57], [54.2 + 1.3, pos["Ask for AI explanation"]], color=PURPLE, lw=1.1, zorder=1)
    ax.plot([87.5, 57], [13 + 1.3, pos["Run experiments, tests, screenshots"]], color=ORANGE, lw=1.1, zorder=1)
    # include / extend
    arrow(ax, (cx - 8, pos["Train baseline and XGBoost"] + 2.3), (cx - 8, pos["Build features"] - 2.3), "<<include>>", color=GREY, ls="--", lw=1.1, lo=(-6.5, 0), fs=7.4)
    arrow(ax, (cx + 8, pos["Run domain adaptation"] + 2.3), (cx + 8, pos["Train baseline and XGBoost"] - 2.3), "<<include>>", color=GREY, ls="--", lw=1.1, lo=(7.5, 0), fs=7.4)
    arrow(ax, (59.5, pos["Train baseline and XGBoost"]), (57, pos["Train baseline and XGBoost"]), "<<extend>>", color=GREY, ls="--", lw=1.1, lo=(-0.5, 2.4), fs=7.4)
    arrow(ax, (cx + 12, pos["Ask for AI explanation"] + 2.3), (cx + 12, pos["Review evaluation and importance"] - 2.3), "<<extend>>", color=GREY, ls="--", lw=1.1, lo=(7.5, 0), fs=7.4)
    ax.set_ylim(0, H_)
    save(fig, out("08_use_case.png"))


# ------------------------------------------------------------------------------------------------ 09 ER
def d_er():
    fig, ax = canvas(W, 7.0, 100)          # height 63.6
    H_ = 100 * 7.0 / W
    fs = 7.3
    cust = uml_class(ax, 1, 62.5, 21, "Customer", ["customer_id  PK", "age", "club_member_status", "fashion_news_frequency", "postal_code"], [], fs=fs, hdr=BLUE)
    tx = uml_class(ax, 27, 62.5, 22, "Transaction", ["t_dat", "customer_id  FK", "article_id  FK", "price", "sales_channel_id"], [], fs=fs, hdr=NAVY)
    art = uml_class(ax, 54, 62.5, 22, "Article", ["article_id  PK", "prod_name", "product_type_name", "product_group_name", "colour_group_name", "department_name", "section_name", "garment_group_name"], [], fs=fs, hdr=BLUE)
    fc = uml_class(ax, 80, 62.5, 19, "Forecast", ["article_id", "horizon  (7, 14, 30)", "t_dat", "predicted_demand"], [], fs=fs, hdr=PURPLE)
    dd = uml_class(ax, 1, 31, 21, "DailyDemand", ["t_dat", "article_id", "demand  (units)", "price  (mean)", "sales_channel_id  (mode)", "product attributes"], [], fs=fs, hdr=NAVY)
    fr = uml_class(ax, 27, 31, 22, "FeatureRow", ["t_dat", "article_id", "demand  (target)", "calendar  (14)", "lag / rolling  (9)", "price, channel, 6 codes"], [], fs=fs, hdr=NAVY)
    dr = uml_class(ax, 54, 31, 22, "DomainRun", ["domain_col", "source, target", "classifier_accuracy", "weights  mean/min/max", "before  RMSE MAE MAPE R2", "after   RMSE MAE MAPE R2"], [], fs=fs, hdr=TEAL)
    mf = uml_class(ax, 80, 31, 19, "ModelFile", ["kind  baseline | adapted", "path  models/*.joblib", "feature_cols  list"], [], fs=fs, hdr=TEAL)
    # relationships (crow's-foot style labels)
    def rel(p1, p2, a, b, label="", lo=(0, 1.3)):
        arrow(ax, p1, p2, color=GREY, lw=1.4, style="-")
        ax.text(p1[0] + (1.0 if p2[0] > p1[0] else -1.0 if p2[0] < p1[0] else 0.8), p1[1] + (0.8 if p2[1] <= p1[1] else -0.8), a, fontsize=8, color=NAVY, ha="center", va="center", fontweight="bold", zorder=6)
        ax.text(p2[0] + (-1.0 if p2[0] > p1[0] else 1.0 if p2[0] < p1[0] else 0.8), p2[1] + (-0.8 if p2[1] <= p1[1] else 0.8), b, fontsize=8, color=NAVY, ha="center", va="center", fontweight="bold", zorder=6)
        if label:
            ax.text((p1[0] + p2[0]) / 2 + lo[0], (p1[1] + p2[1]) / 2 + lo[1], label, fontsize=7.4, ha="center", va="center", color=INK, zorder=6,
                    bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.9))
    rel((27, 55), (22, 55), "N", "1", "places", lo=(0, 1.3))
    rel((49, 52), (54, 52), "N", "1", "is of", lo=(0, 1.3))
    ax.plot([38, 38], [fc[1] + 0, 0], alpha=0)
    # transaction -> daily demand (aggregates)
    rel((33, 62.5 - tx[3]), (12, 31 + 0.0), "N", "1", "aggregated by\n(date, article)", lo=(-4, 0))
    arrow(ax, (12, 31 - dd[3] + 0.0), (12, 31 - dd[3] + 0.0), color=GREY)
    rel((22, 21), (27, 21), "1", "1", "becomes", lo=(0, 1.4))
    rel((49, 21), (54, 21), "N", "1", "adapted\nin", lo=(0, 2.3))
    rel((76, 21), (80, 21), "1", "N", "produces", lo=(-0.5, 2.2))
    rel((38, 31 - fr[3] - 0.2), (86, 31 - mf[3] - 0.2), "N", "1", "", lo=(0, 0))
    ax.plot([38, 38, 89.5, 89.5], [31 - fr[3], 6.5, 6.5, 31 - mf[3]], color=GREY, lw=1.4, zorder=3)
    txt(ax, 64, 4.7, "baseline model trained from the feature table  (N rows : 1 model file)", 7.6)
    ax.plot([38, 38, 38.1], [31 - fr[3], 6.5, 6.5], color=GREY, lw=1.4)
    rel((89.5, 62.5 - fc[3]), (89.5, 31), "N", "1", "uses", lo=(3.6, 0))
    rel((76, 55), (80, 55), "1", "N", "", lo=(0, 0))
    ax.text(78, 56.4, "for", fontsize=7.4, ha="center", color=INK, zorder=6)
    ax.set_ylim(0, H_)
    save(fig, out("09_er_diagram.png"))


# ------------------------------------------------------------------------------------------------ flow helpers
def flow_box(ax, x, y, text, w=17.5, h=8.6, fc=NAVY, tc=WHITE, fs=7.8, ec=None):
    return box(ax, x, y, w, h, text, fc=fc, tc=tc, fs=fs, ec=ec)


def guard(ax, x, y, text, w=20, h=4.6, fs=7.2):
    box(ax, x, y, w, h, text, fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=fs, r=0.6, ls="--")


# ------------------------------------------------------------------------------------------------ 10 algorithm flowchart
def d_flow_algo():
    fig, ax = canvas(W, 7.0, 100)          # height 63.6
    H_ = 100 * 7.0 / W
    xs = [11, 31, 51, 71, 91]
    r1, r2, r3 = 55, 33, 9.5
    s1 = ["Raw rows\ntransactions, articles\n(customers)", "Clean\nparse t_dat; drop null ids,\nprice <= 0, exact\nduplicates", "Merge\nleft join articles\n(+ customers);\nmissing -> Unknown",
          "Aggregate\ncount rows per\n(t_dat, article_id)\n= units sold", "Fill missing days\ndemand = 0 between first\nand last sale\n(articles >= 5 sales)"]
    for i, (x, t) in enumerate(zip(xs, s1)):
        flow_box(ax, x, r1, t, fc=NAVY if i else GREY)
        if i:
            arrow(ax, (xs[i - 1] + 8.9, r1), (x - 8.9, r1), color=GREY)
    arrow(ax, (91, r1 - 4.4), (91, r2 + 4.4), color=GREY)
    s2 = ["Features\nshift(1) first, then lag 1/7/14/28,\nrolling mean 7/14/28,\nstd 7/28", "Encode and add calendar\n6 attributes -> codes;\n14 calendar features", "Split by date\nfirst 80 % of dates train,\nlast 20 % test",
          "Train\nmoving average, XGBoost\n(optional tuning:\nTimeSeriesSplit)", "Evaluate on test\nRMSE, MAE, safe MAPE, R2\nfeature importance"]
    xs2 = xs[::-1]
    for i, (x, t) in enumerate(zip(xs2, s2)):
        flow_box(ax, x, r2, t, fc=BLUE, fs=7.6)
        if i:
            arrow(ax, (xs2[i - 1] - 8.9, r2), (x + 8.9, r2), color=GREY)
    # row 2 flows right-to-left, so the guards sit beneath
    guard(ax, 91 - 0, 21.5, "G1  shift(1) before rolling:\nthe current day is never in its features", w=21)
    guard(ax, 51, 21.5, "G2  split by date,\nnever at random", w=19)
    guard(ax, 31, 21.5, "G3  tuning uses\nTimeSeriesSplit folds", w=19)
    ax.plot([71, 71], [r2 - 4.4, 24.0], color=ORANGE, lw=0.8, ls=":")
    # row 3: right-to-left
    arrow(ax, (11, r2 - 4.4), (11, r3 + 4.4), color=GREY)
    flow_box(ax, 11, r3, "Save model\nmodels/baseline_\nxgboost.joblib", fc=TEAL, fs=7.6)
    flow_box(ax, 31, r3, "Forecast loop\nrow = last known row; update\ncalendar, lags, rolling\nfrom history", fc=TEAL, fs=7.4)
    diamond(ax, 53, r3, 20, 10.5, "step < horizon?\n(7, 14 or 30)", fs=7.8)
    flow_box(ax, 78, r3, "Forecast table + chart\npredicted units per day\n(clipped at 0)", fc=TEAL, fs=7.6)
    arrow(ax, (19.9, r3), (22.2, r3), color=GREY)
    arrow(ax, (39.9, r3), (43, r3), color=GREY)
    arrow(ax, (63, r3), (69.2, r3), "no", color=GREY, lo=(0, 1.6), fs=8)
    arrow(ax, (53, r3 + 5.3), (53, r3 + 10.5), color=GREY, lw=0.01)
    ax.plot([53, 53, 36, 36], [r3 + 5.3, r3 + 10.5, r3 + 10.5, r3 + 4.4], color=GREY, lw=1.5, zorder=3)
    arrow(ax, (36, r3 + 5.0), (36, r3 + 4.4), color=GREY)
    txt(ax, 49.5, r3 + 12.0, "yes: append prediction to history", 7.6)
    guard(ax, 43, 21.6, "G4  recursive: each prediction\nfeeds the next day's lags", w=0.1, h=0.1)
    ax.texts[-1].set_visible(False)
    ax.set_ylim(0, H_)
    save(fig, out("10_flowchart_algorithm.png"))


# ------------------------------------------------------------------------------------------------ 11 domain adaptation flowchart
def d_flow_da():
    fig, ax = canvas(W, 7.0, 100)          # height 63.6
    H_ = 100 * 7.0 / W
    xs = [11, 31, 53, 75, 92]
    r1, r2, r3 = 53, 31, 9.5
    flow_box(ax, xs[0], r1, "Feature table\n(31,094 rows in\nthe real subset)", fc=GREY, w=16)
    flow_box(ax, xs[1], r1, "Choose domain column,\nsource and target value\n(channel, product group,\ndepartment)", w=19)
    diamond(ax, xs[2], r1, 21, 12, "source != target\nand both have rows?", fs=7.6)
    flow_box(ax, xs[3], r1, "Features without the\ndomain column; split source\nrows and target rows", w=19)
    flow_box(ax, xs[4], r1, "Target: first 50 % of dates\nunused for the source\nmodel; last 50 % = test", w=16.5, fs=7.4)
    arrow(ax, (19, r1), (21.4, r1), color=GREY)
    arrow(ax, (40.6, r1), (42.5, r1), color=GREY)
    arrow(ax, (63.5, r1), (65.4, r1), "yes", color=GREY, lo=(0, 1.8), fs=8)
    arrow(ax, (84.6, r1), (83.8, r1), color=GREY)
    box(ax, xs[2], 41.5, 20, 3.6, "no: HTTP 400, nothing trained", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.4, r=0.5)
    arrow(ax, (xs[2], r1 - 6.0), (xs[2], 43.3), color=ORANGE)
    arrow(ax, (92, r1 - 4.4), (92, r2 + 4.4), color=GREY)
    s2 = ["Train XGBoost on\nsource rows only\n(default parameters)", "Score target test\n= BEFORE metrics", "Domain classifier\nlogistic regression,\nsource 0 vs target 1\n(25 % held-out accuracy)",
          "Importance weight\nw = p / (1 - p)\nclipped to [0, 20]", "Train XGBoost on\nsource rows with\nsample_weight = w"]
    xs2 = xs[::-1]
    for i, (x, t) in enumerate(zip(xs2, s2)):
        flow_box(ax, x, r2, t, fc=BLUE if i != 4 else TEAL, w=17.5, fs=7.5)
        if i:
            arrow(ax, (xs2[i - 1] - 8.9, r2), (x + 8.9, r2), color=GREY)
    arrow(ax, (11, r2 - 4.4), (11, r3 + 4.4), color=GREY)
    flow_box(ax, 11, r3, "Score the same\ntarget test rows\n= AFTER metrics", fc=TEAL, w=17.5, fs=7.6)
    flow_box(ax, 33, r3, "Report\nRMSE MAE MAPE R2\nand improvement %", fc=TEAL, w=17.5, fs=7.6)
    flow_box(ax, 55, r3, "Save adapted model\nmodels/adapted_\nxgboost.joblib; keep\nresult in S", fc=TEAL, w=18, fs=7.4)
    flow_box(ax, 77, r3, "Return JSON:\nshift table, histogram,\nbox plot, weights, report", fc=TEAL, w=19, fs=7.4)
    for a, b in ((19.9, 24.2), (41.9, 45.8), (64, 67.4)):
        arrow(ax, (a, r3), (b, r3), color=GREY)
    # findings
    box(ax, 33, 20.2, 30, 5.6, "Measured: weights are not normalised; for\nperfectly separable domains p/(1-p) is about 1e-5\nand XGBoost collapses to a constant", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.2, r=0.6, ls="--")
    box(ax, 74, 20.2, 30, 5.6, "Measured: source rows include dates inside the\ntarget test window; restricting them removes\nthe only clear gain (time-clean protocol)", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.2, r=0.6, ls="--")
    ax.set_ylim(0, H_)
    save(fig, out("11_flowchart_domain_adaptation.png"))


# ------------------------------------------------------------------------------------------------ 12 model architecture
def d_model():
    fig, ax = canvas(W, 6.4, 100)          # height 58.2
    H_ = 100 * 6.4 / W
    groups = [("Price and channel  (2)", "price, sales_channel_id", BLUE), ("Product attributes  (6)", "type, group, colour, department,\nsection, garment group  (label codes)", TEAL),
              ("Calendar  (14)", "year, month, day, weekday, week, day of year,\nquarter, weekend, month start/end,\nmonth and weekday sin/cos", NAVY),
              ("Lag and rolling  (9)", "lag 1, 7, 14, 28; rolling mean 7, 14, 28;\nrolling std 7, 28  (computed on shift(1))", ORANGE)]
    ys = [50, 38, 26, 14]
    for (t, d, c), y in zip(groups, ys):
        box(ax, 20, y, 36, 9.4, f"{t}\n{d}", fc=c, fs=7.8)
        arrow(ax, (38.2, y), (46, 32), color=GREY, lw=1.1)
    box(ax, 52, 32, 11, 12, "31 input\ncolumns", fc=LIGHT, tc=INK, ec=GREY, fs=8.5, bold=True)
    arrow(ax, (57.7, 32), (63, 32), color=NAVY, lw=1.6)
    box(ax, 73, 32, 20, 14, "XGBoost regressor\n300 trees, depth 8\nlearning rate 0.05\nsubsample 0.8\ncolsample 0.8", fc=NAVY, fs=8, bold=False)
    arrow(ax, (83.2, 32), (88.5, 32), color=NAVY, lw=1.6)
    box(ax, 94, 32, 9.4, 9, "units\nper\nday", fc=TEAL, fs=8.5, bold=True)
    box(ax, 73, 11, 22, 9, "Moving average (7 days)\nbaseline in the product;\nlast 7 training days per article", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=7.4)
    box(ax, 73, 51, 24, 9, "Weighted variant (domain adaptation)\nsame model, plus sample_weight\nw = p / (1 - p) from the classifier", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=7.4)
    arrow(ax, (73, 46.5), (73, 39.2), color=TEAL, ls="--", lw=1.3)
    arrow(ax, (73, 15.6), (73, 24.8), color=BLUE, ls="--", lw=1.3)
    txt(ax, 86.5, 21, "compared on the same\ntest rows", 7.4, GREY)
    ax.set_ylim(0, H_)
    save(fig, out("12_model_architecture.png"))


DRAWERS = {"seq": d_seq, "uc": d_uc, "er": d_er, "flow_algo": d_flow_algo, "flow_da": d_flow_da, "model": d_model}
