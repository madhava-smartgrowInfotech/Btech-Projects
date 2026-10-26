"""Result figures for the TrendCast documents (matplotlib, 150 dpi, ~7x4 in) -> docs/figures/.

    python -m scripts.docs.make_figures            # all
    python -m scripts.docs.make_figures f01 f05    # selected

Reads only experiments/**/metrics.json and the CSVs next to them; f07 recomputes the importance weights with the
project's own src/ functions on the real subset (same loading code as scripts/run_experiments.py).
"""

import os
import sys

try:  # LightGBM crashes on this machine if pandas/xgboost are imported before it; run_experiments imports it too
    import lightgbm  # noqa: F401
except ImportError:  # pragma: no cover
    pass

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import facts as F
from .dgm_lib import BLUE, GREY, INK, NAVY, ORANGE, PURPLE, TEAL

RED = "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "axes.labelsize": 9,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#8895A7", "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.grid": True, "grid.color": "#E3E8EF", "grid.linewidth": 0.8, "axes.axisbelow": True,
                     "legend.frameon": False, "legend.fontsize": 8.5})


def out(name):
    os.makedirs(F.FIGS, exist_ok=True)
    return os.path.join(F.FIGS, name)


def finish(fig, name):
    fig.tight_layout()
    fig.savefig(out(name), dpi=150, facecolor="white")
    plt.close(fig)
    print("saved", name)


def short(label):
    s_ = label.replace(" (channel 2 -> 1)", "").replace(" (channel 1 -> 2)", "")
    a_, b_ = s_.split(" -> ")
    return a_.replace(" body", "") + chr(10) + chr(8594) + " " + b_


def label_bars(ax, bars, fmt="{:.2f}", pad=0.01, horizontal=False, fs=8.5):
    for b in bars:
        if horizontal:
            w = b.get_width()
            ax.text(w + pad, b.get_y() + b.get_height() / 2, fmt.format(w), va="center", ha="left" if w >= 0 else "right", fontsize=fs, color=INK)
        else:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + pad if h >= 0 else h - pad, fmt.format(h), ha="center", va="bottom" if h >= 0 else "top", fontsize=fs, color=INK)


def f01():
    M = F.FC["models"]
    order = [("Naive (lag 1)", "Naive\nlag 1", GREY), ("Rolling mean 7 (shifted)", "Rolling\nmean 7", GREY), (F.MA, "Moving\naverage 7", GREY), ("Seasonal naive (lag 7)", "Seasonal\nnaive", GREY),
             ("Random forest", "Random\nforest", BLUE), ("LightGBM", "LightGBM", BLUE), (F.XGB, "XGBoost\n(default)", NAVY), (F.XGB_T, "XGBoost\n(tuned)", TEAL)]
    vals = [M[k]["RMSE"] for k, _, _ in order]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    x = np.arange(len(order))
    bars = ax.bar(x, vals, color=[c for _, _, c in order], width=0.68)
    sd = F.FC["xgboost_seed_stats"]["RMSE"]["std"]
    ax.errorbar([6], [vals[6]], yerr=[sd], color=INK, capsize=4, lw=1.4, zorder=5)
    label_bars(ax, bars, "{:.2f}", 0.15)
    ax.set_xticks(x)
    ax.set_xticklabels([l for _, l, _ in order], fontsize=8.5)
    ax.set_ylabel("Test RMSE (units per article-day), lower is better")
    ax.set_title("Forecast error on the held-out window (2018-12-14 to 2019-01-04)")
    ax.set_ylim(0, max(vals) * 1.15)
    ax.text(0.99, 0.97, f"XGBoost default: mean of 5 seeds, error bar = 1 s.d. ({sd:.3f})", transform=ax.transAxes, ha="right", va="top", fontsize=8.5, color=GREY)
    finish(fig, "f01_model_comparison.png")


def f02():
    A = F.FC["ablation"]
    names = list(A)
    rm = [A[n]["RMSE"] for n in names]
    r2 = [A[n]["R2"] for n in names]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.4, 4.2), sharey=True, gridspec_kw={"width_ratios": [1, 1]})
    y = np.arange(len(names))[::-1]
    cols = [NAVY if n.startswith("all") else (ORANGE if ("no lag" in n or "calendar" in n) else TEAL) for n in names]
    b1 = a1.barh(y, rm, color=cols, height=0.62)
    label_bars(a1, b1, "{:.2f}", 0.15, True)
    a1.set_yticks(y)
    a1.set_yticklabels([f"{n} ({A[n]['n_features']})" for n in names], fontsize=8.5)
    a1.set_xlabel("RMSE (lower is better)")
    a1.set_xlim(0, max(rm) * 1.18)
    a1.set_title("RMSE")
    b2 = a2.barh(y, r2, color=cols, height=0.62)
    label_bars(a2, b2, "{:.2f}", 0.015, True)
    a2.axvline(0, color=INK, lw=0.9)
    a2.set_xlabel("R2 (higher is better)")
    a2.set_xlim(min(r2) - 0.2, max(r2) + 0.2)
    a2.set_title("R2")
    fig.suptitle("Feature-group ablation: lag / rolling features carry the model", fontweight="bold", fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out("f02_ablation.png"), dpi=150, facecolor="white")
    plt.close(fig)
    print("saved f02_ablation.png")


def f03():
    d = pd.read_csv(os.path.join(F.EXP, "forecasting", "test_daily_series.csv"), parse_dates=["t_dat"])
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    ax.plot(d.t_dat, d.demand, color=INK, lw=2.0, label="Actual")
    ax.plot(d.t_dat, d.xgb, color=TEAL, lw=1.8, label="XGBoost (5-seed mean)")
    ax.plot(d.t_dat, d.ma, color=ORANGE, lw=1.8, ls="--", label="Moving average (7 d)")
    ax.set_ylabel("Units sold per day, 300 articles")
    ax.set_xlabel("Date")
    ax.set_title("Daily total demand over the test window", pad=26)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=3, fontsize=8.5)
    ev = F.FC["test_daily_totals_error"]
    ax.set_xlabel(f"Date    (daily-total WAPE: XGBoost {ev['xgb_daily_wape_pct']:.1f} %, moving average {ev['ma_daily_wape_pct']:.1f} %)")
    fig.autofmt_xdate(rotation=30)
    finish(fig, "f03_test_daily_series.png")


def f04():
    R = F.REC["results"]
    names = [("xgb_app", "XGBoost recursive (as shipped)", NAVY), ("xgb_fixed", "XGBoost, calendar refreshed", BLUE), ("flat_ma7", "Flat mean of last 7 days", ORANGE), ("repeat_last_week", "Repeat last week", GREY)]
    bands = [b["band"] for b in R["xgb_app"]["by_band"]]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    w = 0.2
    x = np.arange(len(bands))
    for i, (k, lab, c) in enumerate(names):
        v = [b["WAPE (%)"] for b in R[k]["by_band"]]
        bars = ax.bar(x + (i - 1.5) * w, v, w, color=c, label=lab)
        label_bars(ax, bars, "{:.0f}", 1.0, fs=8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"days {b}" for b in bands])
    ax.set_ylabel("WAPE (%), lower is better")
    ax.set_title(f"Recursive multi-day forecast error by horizon (origin {F.REC['origin']}, {F.REC['articles_scored']} articles)")
    ax.legend(loc="upper left")
    ax.set_ylim(0, 150)
    finish(fig, "f04_recursive_horizon.png")


def f05():
    P = F.DOM["pairs"]
    labs = [short(p["label"]) for p in P]
    series = [("As shipped", [p["app"]["rmse_improvement_pct_mean"] for p in P], NAVY), ("Weights rescaled to mean 1", [p["app"]["normalised_improvement_pct_mean"] for p in P], TEAL),
              ("Time-clean source", [p["time_clean"]["rmse_improvement_pct_mean"] for p in P], ORANGE), ("Shuffled weights (control)", [p["app"]["shuffled_improvement_pct_mean"] for p in P], GREY)]
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    w = 0.2
    x = np.arange(len(P))
    for i, (lab, v, c) in enumerate(series):
        ax.bar(x + (i - 1.5) * w, v, w, color=c, label=lab)
    ax.axhline(0, color=INK, lw=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(labs, fontsize=8, rotation=0)
    for t in ax.get_xticklabels():
        t.set_wrap(True)
    ax.set_ylabel("RMSE change vs source-only model (%), + is better")
    ax.set_title("Adaptation effect on RMSE: six source-target pairs, 5 seeds", fontsize=9.5)
    ax.legend(loc="lower left", fontsize=8)
    ax.set_ylim(-52, 20)
    s = F.DOM["summary"]
    ax.text(0.99, 0.97, f"helped in {s['pairs_where_adaptation_helped']} of {s['pairs_total']} pairs as shipped", transform=ax.transAxes, ha="right", va="top", fontsize=8.5, color=GREY)
    finish(fig, "f05_domain_pairs.png")


def f06():
    P = F.DOM["pairs"]
    labs = [short(p["label"]) for p in P]
    series = [("Source-only (before)", "before", GREY), ("Importance-weighted (adapted)", "adapted", NAVY), ("Pooled source + target, unweighted", "pooled_unweighted", TEAL), ("Target-only (first half)", "target_only_oracle", ORANGE)]
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    w = 0.2
    x = np.arange(len(P))
    for i, (lab, k, c) in enumerate(series):
        v = [p["app"][k]["RMSE"]["mean"] for p in P]
        e = [p["app"][k]["RMSE"]["std"] for p in P]
        ax.bar(x + (i - 1.5) * w, v, w, yerr=e, color=c, label=lab, capsize=2, error_kw={"lw": 0.9})
    ax.set_xticks(x)
    ax.set_xticklabels(labs, fontsize=8)
    ax.set_ylabel("RMSE on the held-out target test rows")
    ax.set_title("Adaptation against simple controls (mean of 5 seeds, bar = 1 s.d.)")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.set_ylim(0, 33)
    finish(fig, "f06_domain_controls.png")


def f07():
    from . import facts  # noqa: F401
    sys.path.insert(0, F.CODE)
    from scripts import run_experiments as RE
    from src import domain_adaptation as DA
    from src import feature_engineering as FE
    from pathlib import Path
    ft, mappings, _, _ = RE.load(Path(F.CODE) / "data" / "real_hm")
    cols = FE.get_feature_columns(ft)
    code = lambda c, n: next(k for k, v in mappings[c].items() if v == n)  # noqa: E731
    cases = [("sales_channel_id", 2.0, 1.0, "Channel 2 > channel 1\n(classifier accuracy about 66 %)", TEAL),
             ("department_name", code("department_name", "Knitwear"), code("department_name", "Trouser"), "Knitwear > Trouser\n(classifier accuracy 100 %)", ORANGE)]
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    bins = np.linspace(-6.5, 1.5, 49)
    for col, s, t, lab, c in cases:
        fcols = [x for x in cols if x != col]
        sd, td = DA.split_domains(ft, col, s, t)
        clf, acc = DA.train_domain_classifier(sd[fcols], td[fcols])
        w = DA.compute_instance_weights(clf, sd[fcols])
        ax.hist(np.log10(np.maximum(w, 1e-7)), bins=bins, alpha=0.65, color=c, label=f"{lab}\nsum of weights = {w.sum():,.1f}, n = {len(w):,}")
    ax.axvline(0, color=INK, lw=1.0, ls=":")
    ax.set_ylim(0, 7000)
    ax.text(0.9, 1200, "weight 1\n(unweighted)", fontsize=8, color=INK)
    ax.set_xlabel("log10 of the importance weight  p / (1 - p)")
    ax.set_ylabel("Source rows")
    ax.set_title("Weights collapse when the domains are perfectly separable")
    ax.legend(loc="upper left", fontsize=8)
    ax.text(0.99, 0.98, "XGBoost min_child_weight = 1:\na child needs total weight >= 1, so a\ntotal below 1 cannot split\n(the model predicts a constant)", transform=ax.transAxes, ha="right", va="top", fontsize=8.5, color=RED,
            bbox=dict(fc="white", ec=RED, lw=0.8, pad=3))
    finish(fig, "f07_weights_collapse.png")


def f08():
    T = F.EX["top10_by_shap"]
    feats = [t["feature"] for t in T][::-1]
    shap = np.array([t["mean_abs_shap"] for t in T][::-1])
    gain = np.array([t["gain_importance"] for t in T][::-1])
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    y = np.arange(len(feats))
    ax.barh(y + 0.19, shap / shap.max(), 0.36, color=NAVY, label="mean |SHAP| (units), scaled to top = 1")
    ax.barh(y - 0.19, gain / gain.max(), 0.36, color=ORANGE, label="gain importance, scaled to top = 1")
    ax.set_yticks(y)
    ax.set_yticklabels(feats)
    ax.set_xlabel("Importance relative to the largest value of each method")
    ax.set_title("Top-10 features by exact TreeSHAP vs the gain importance shown in the app")
    ax.legend(loc="lower right", fontsize=8)
    ax.text(0.99, 0.5, f"Spearman rank correlation\nover all 31 features: {F.EX['spearman_rank_corr_shap_vs_gain']:.2f}", transform=ax.transAxes, ha="right", va="center", fontsize=8.5, color=GREY)
    finish(fig, "f08_shap_vs_gain.png")


def f09():
    names = [("XGBoost", "XGBoost"), ("Moving average (7d)", "Moving average"), ("Seasonal naive (lag 7)", "Seasonal naive")]
    under = [F.INV[k]["understock_pct_of_demand"] for k, _ in names]
    over = [F.INV[k]["overstock_pct_of_demand"] for k, _ in names]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    x = np.arange(len(names))
    b1 = ax.bar(x - 0.19, under, 0.36, color=ORANGE, label="Under-forecast (units that would be lost sales)")
    b2 = ax.bar(x + 0.19, over, 0.36, color=BLUE, label="Over-forecast (excess units)")
    label_bars(ax, b1, "{:.1f} %", 0.6)
    label_bars(ax, b2, "{:.1f} %", 0.6)
    ax.set_xticks(x)
    ax.set_xticklabels([n for _, n in names])
    ax.set_ylabel(f"% of units actually sold ({F.INV['actual_units']:,.0f})")
    ax.set_title("Forecast error expressed as stock units (test window)")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_ylim(0, max(over) * 1.3)
    finish(fig, "f09_inventory_units.png")


def f10():
    rows = [("attributes_calendar_only_unseen_article", "XGBoost,\nattributes + calendar\n(unseen article)", NAVY), ("product_type_mean_baseline_unseen_article", "Mean of the\nproduct type\n(unseen article)", GREY),
            ("full_features_unseen_article_lags_assumed_known", "Reference: own\nlag features\nknown", TEAL)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 4.0))
    x = np.arange(len(rows))
    w = [F.COLD[k]["WAPE (%)"] for k, _, _ in rows]
    r = [F.COLD[k]["R2"] for k, _, _ in rows]
    b1 = a1.bar(x, w, 0.6, color=[c for _, _, c in rows])
    label_bars(a1, b1, "{:.1f}", 1.0)
    a1.set_xticks(x)
    a1.set_xticklabels([l for _, l, _ in rows], fontsize=8)
    a1.set_ylabel("WAPE (%), lower is better")
    a1.set_title("WAPE")
    a1.set_ylim(0, max(w) * 1.2)
    b2 = a2.bar(x, r, 0.6, color=[c for _, _, c in rows])
    label_bars(a2, b2, "{:.2f}", 0.015)
    a2.axhline(0, color=INK, lw=0.9)
    a2.set_xticks(x)
    a2.set_xticklabels([l for _, l, _ in rows], fontsize=8)
    a2.set_ylabel("R2, higher is better")
    a2.set_title("R2")
    a2.set_ylim(min(r) - 0.1, max(r) * 1.2)
    fig.suptitle(f"Cold start (offline): 5-fold split by article, {F.COLD['articles']} articles", fontweight="bold", fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out("f10_cold_start.png"), dpi=150, facecolor="white")
    plt.close(fig)
    print("saved f10_cold_start.png")


def f11():
    bp = {"lgbm": 33.71, "ma": 33.71 + 2.86, "naive": 33.71 + 14.06}     # as stated in the base paper text (Section V.A)
    ours = {"xgb": F.fm(F.XGB), "ma": F.fm(F.MA), "naive": F.fm("Naive (lag 1)")}
    gain_bp = [(bp["ma"] - bp["lgbm"]) / bp["ma"] * 100, (bp["naive"] - bp["lgbm"]) / bp["naive"] * 100]
    gain_us = [(ours["ma"] - ours["xgb"]) / ours["ma"] * 100, (ours["naive"] - ours["xgb"]) / ours["naive"] * 100]
    fig, ax = plt.subplots(figsize=(7.2, 4.1))
    x = np.arange(2)
    b1 = ax.bar(x - 0.19, gain_bp, 0.36, color=GREY, label="Base paper: LightGBM, UCI Online Retail II, one-day-ahead")
    b2 = ax.bar(x + 0.19, gain_us, 0.36, color=NAVY, label="TrendCast: XGBoost, H&M subset, one-day-ahead")
    label_bars(ax, b1, "{:+.1f} %", 0.8)
    label_bars(ax, b2, "{:+.1f} %", 0.8)
    ax.axhline(0, color=INK, lw=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(["vs 7-day moving average", "vs naive lag-1 (repeat yesterday)"])
    ax.set_ylabel("RMSE reduction vs the baseline (%)")
    ax.set_title("Relative gain over simple baselines (different datasets: indicative only)")
    ax.legend(loc="upper left", fontsize=8)
    ax.set_ylim(-28, 52)
    finish(fig, "f11_base_paper_comparison.png")


def f12():
    A = F.API
    st = A["stages_seconds"]
    lat = A["latency_ms"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.0, 4.2), gridspec_kw={"width_ratios": [1.1, 1]})
    names = list(st)[::-1]
    v = [st[n] for n in names]
    b = a1.barh(range(len(names)), v, color=TEAL, height=0.62)
    a1.set_yticks(range(len(names)))
    a1.set_yticklabels(names, fontsize=8)
    a1.set_xscale("log")
    for bar, val in zip(b, v):
        a1.text(val * 1.12, bar.get_y() + bar.get_height() / 2, f"{val:.2f} s", va="center", fontsize=8.5)
    a1.set_xlim(0.05, 120)
    a1.set_xlabel("Seconds (log scale)")
    a1.set_title("Pipeline stages, 684,392 rows")
    ln = list(lat)[::-1]
    med = [lat[n]["median"] for n in ln]
    p95 = [lat[n]["p95"] for n in ln]
    y = np.arange(len(ln))
    a2.barh(y, med, color=NAVY, height=0.62, label="median")
    a2.scatter(p95, y, color=ORANGE, zorder=5, s=26, label="95th percentile")
    for yy, m in zip(y, med):
        a2.text(max(p95) * 1.03, yy, f"{m:.0f} ms", va="center", fontsize=8)
    a2.set_yticks(y)
    a2.set_yticklabels(ln, fontsize=8)
    a2.set_xlabel("Milliseconds per request")
    a2.set_title(f"API latency ({lat[ln[0]]['n']} calls each)")
    a2.set_xlim(0, max(p95) * 1.35)
    a2.legend(loc="upper center", bbox_to_anchor=(0.62, 1.0), fontsize=8)
    fig.tight_layout()
    fig.savefig(out("f12_api_latency.png"), dpi=150, facecolor="white")
    plt.close(fig)
    print("saved f12_api_latency.png")


def f13():
    s = F.FC["xgboost_seed_stats"]
    vals = s["RMSE"]["values"]
    seeds = [42, 43, 44, 45, 46]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.vlines([str(x) for x in seeds], [min(vals) - 0.1] * 5, vals, color=NAVY, lw=2.2)
    ax.scatter([str(x) for x in seeds], vals, color=NAVY, s=60, zorder=5)
    for xx, vv in zip(seeds, vals):
        ax.text(str(xx), vv + 0.012, f"{vv:.3f}", ha="center", va="bottom", fontsize=8.5)
    m, sd = s["RMSE"]["mean"], s["RMSE"]["std"]
    ax.axhline(m, color=ORANGE, lw=1.5)
    ax.axhspan(m - sd, m + sd, color=ORANGE, alpha=0.18)
    ax.text(0.02, 0.97, f"mean {m:.3f}, s.d. {sd:.3f}", transform=ax.transAxes, va="top", fontsize=8.5, color=INK)
    ax.set_ylim(min(vals) - 0.12, max(vals) + 0.12)
    ax.set_xlabel("XGBoost random_state")
    ax.set_ylabel("Test RMSE")
    ax.set_title("Seed-to-seed spread of the default model is small")
    finish(fig, "f13_xgb_seed_stability.png")


FIGS = {"f01": f01, "f02": f02, "f03": f03, "f04": f04, "f05": f05, "f06": f06, "f07": f07, "f08": f08, "f09": f09, "f10": f10, "f11": f11, "f12": f12, "f13": f13}


def main():
    keys = sys.argv[1:] or list(FIGS)
    for k in keys:
        FIGS[k]()


if __name__ == "__main__":
    main()
