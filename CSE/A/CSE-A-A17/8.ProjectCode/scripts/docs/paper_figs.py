"""Compact figures for the two-column IEEE paper -> docs/figures/paper_*.png (drawn at column width so text stays legible)."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from . import facts as F

NAVY, BLUE, TEAL, ORANGE, GREEN, RED, GREY = "#1B2A41", "#2F6DB5", "#1E9E8F", "#E08A1E", "#3C9D5D", "#C0392B", "#8A94A6"
PALE = {"blue": "#E4EEF9", "teal": "#DFF3EF", "orange": "#FCEBD3", "green": "#E3F3E8", "grey": "#EEF0F4", "red": "#F9E0DC"}


def _save(fig, name):
    os.makedirs(F.FIGS, exist_ok=True)
    p = os.path.join(F.FIGS, name)
    fig.savefig(p, dpi=220, facecolor="white")
    plt.close(fig)
    return p


def _canvas(w, h, xmax, ymax):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.axis("off")
    return fig, ax


def _box(ax, x, y, w, h, text, fc="grey", ec=NAVY, fs=5.6, bold=False, lw=0.7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=PALE.get(fc, fc), ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=NAVY, fontweight="bold" if bold else "normal", linespacing=1.15)


def _arrow(ax, x1, y1, x2, y2, color=NAVY, style="-|>", lw=0.8, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=6, lw=lw, color=color, linestyle=ls, shrinkA=0, shrinkB=0))


def arch():
    fig, ax = _canvas(3.5, 2.9, 100, 83)
    _box(ax, 1, 70, 98, 12, "Analyst console - React 19 + Vite (port 5317, 13 pages)\nUpload · Explore · Features · Train · Domain · Evaluate · Forecast · AI", "blue", fs=5.2, bold=True)
    _box(ax, 1, 51, 98, 15, "FastAPI service (port 8317) - 22 routes\nshared pipeline state S + lock · gating (409) · validation (400/422)\nStreamlit app.py is a second front end over the same src/", "teal", fs=5.1, bold=True)
    _arrow(ax, 50, 70, 50, 66.6, style="<|-|>")
    _box(ax, 1, 20, 31, 26, "Data prep\npreprocessing\ndemand_forecasting\nfeature_engineering\n(31 inputs,\nshifted lags)", "orange", fs=4.8)
    _box(ax, 34.5, 20, 31, 26, "Models\nbaseline_models\nxgboost_model\n(300 trees, depth 8,\noptional tuning)\nevaluation", "green", fs=4.8)
    _box(ax, 68, 20, 31, 26, "Domain adaptation\nlogistic domain\nclassifier ->\nweights p/(1-p),\nclip 20 ->\nweighted XGBoost", "blue", fs=4.8)
    for x in (16.5, 50, 83.5):
        _arrow(ax, x, 52, x, 46.5)
    _box(ax, 1, 2, 70, 12, "In-memory tables · models/*.joblib (3 files)\nNo database", "grey", fs=5.0)
    _box(ax, 73, 2, 26, 12, "Gemini (optional)\naggregates only", "orange", fs=4.8)
    _arrow(ax, 36, 20, 36, 14.5, style="-")
    _arrow(ax, 86, 51, 86, 14.5, style="<|-", color=ORANGE, ls="--")
    return _save(fig, "paper_arch.png")


def flow():
    fig, ax = _canvas(3.5, 3.2, 100, 92)
    steps = [("Raw CSVs: transactions, articles", "grey"),
             ("Clean (dates, ids, price > 0, duplicates) and merge", "orange"),
             ("Units sold per article per day; fill gap days with 0", "orange"),
             ("Calendar + price + attributes + lags / rolling means\n(all shifted by 1 day: no same-day leakage)", "green"),
             ("Split by DATE: first 80 % train, last 20 % test", "teal"),
             ("Moving average · XGBoost (default or tuned) -> RMSE, MAE,\nsafe MAPE, R2", "blue")]
    y = 84
    for t, c in steps:
        _box(ax, 2, y, 56, 7.4, t, c, fs=4.5)
        y -= 11.6
    for i in range(5):
        _arrow(ax, 30, 84 - i * 11.6, 30, 84 - i * 11.6 - 4)
    ax.add_patch(FancyBboxPatch((62, 8), 37, 82, boxstyle="round,pad=0.25,rounding_size=1.2", fc="white", ec=TEAL, lw=0.9, ls="--"))
    ax.text(80.5, 86, "Domain adaptation", ha="center", fontsize=5.2, fontweight="bold", color=NAVY)
    d = [("Source rows / target rows\n(domain column removed\nfrom the inputs)", "grey"), ("Source-only XGBoost ->\nbefore: RMSE on later half\nof target dates", "blue"),
         ("Logistic classifier\nsource vs target -> p", "orange"), ("w = p/(1-p),\nclipped at 20", "orange"), ("Weighted XGBoost ->\nafter: same target rows", "green")]
    y = 74
    for t, c in d:
        _box(ax, 65, y, 31, 10, t, c, fs=4.3)
        y -= 14
    for i in range(4):
        _arrow(ax, 80.5, 74 - i * 14, 80.5, 74 - i * 14 - 4)
    _arrow(ax, 58, 25, 62, 25, color=TEAL)
    _box(ax, 2, 6, 56, 9, "Recursive forecast: each predicted day feeds the next day's lags", "grey", fs=4.5)
    _arrow(ax, 30, 12.4, 30, 15.2, style="<|-", color=NAVY)
    return _save(fig, "paper_flow.png")


def results():
    pairs = F.DOM["pairs"]
    labels = ["Ch2→Ch1", "Ch1→Ch2", "Upper→Lower", "Lower→Upper", "Knit→Trouser", "Jersey→Blouse"]
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    y = np.arange(len(pairs))
    h = 0.26
    app = [p["app"]["rmse_improvement_pct_mean"] for p in pairs]
    nrm = [p["app"]["normalised_improvement_pct_mean"] for p in pairs]
    tc = [p["time_clean"]["rmse_improvement_pct_mean"] for p in pairs]
    ax.barh(y - h, app, h, color=BLUE, label="as shipped")
    ax.barh(y, nrm, h, color=ORANGE, label="weights rescaled to mean 1")
    ax.barh(y + h, tc, h, color=GREEN, label="time-clean source")
    ax.axvline(0, color=NAVY, lw=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=6)
    ax.invert_yaxis()
    ax.tick_params(axis="x", labelsize=6)
    ax.set_xlabel("Target RMSE improvement over source-only model (%)", fontsize=6)
    for yy, v in zip(y - h, app):
        ax.text(v + (1 if v >= 0 else -1), yy, f"{v:+.1f}", va="center", ha="left" if v >= 0 else "right", fontsize=5)
    ax.legend(fontsize=5.5, loc="upper left", frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xlim(-58, 22)
    fig.tight_layout(pad=0.4)
    return _save(fig, "paper_domain.png")


def daily():
    import pandas as pd
    d = pd.read_csv(os.path.join(F.EXP, "forecasting", "test_daily_series.csv"), parse_dates=["t_dat"])
    fig, ax = plt.subplots(figsize=(3.5, 2.1))
    ax.plot(d["t_dat"], d["demand"], color=NAVY, lw=1.2, label="actual units")
    ax.plot(d["t_dat"], d["xgb"], color=BLUE, lw=1.0, ls="--", label="XGBoost")
    ax.plot(d["t_dat"], d["ma"], color=ORANGE, lw=1.0, ls=":", label="7-day moving average")
    ax.tick_params(labelsize=5.5)
    ax.set_ylabel("Units sold per day (300 articles)", fontsize=6)
    ax.legend(fontsize=5.5, frameon=False, loc="upper left")
    fig.autofmt_xdate(rotation=30)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout(pad=0.4)
    return _save(fig, "paper_daily.png")


def make():
    return {"arch": arch(), "flow": flow(), "results": results(), "daily": daily()}
