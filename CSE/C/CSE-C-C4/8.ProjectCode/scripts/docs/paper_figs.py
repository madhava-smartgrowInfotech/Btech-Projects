"""Compact figures for the two-column IEEE paper -> docs/figures/paper_*.png (drawn at column width so the text stays legible)."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

from . import facts as F

NAVY, BLUE, TEAL, ORANGE, GREEN, RED, GREY, PURPLE = "#1B2A41", "#2F6DB5", "#1E9E8F", "#E08A1E", "#3C9D5D", "#C0392B", "#8A94A6", "#6B52D6"
PALE = {"blue": "#E4EEF9", "teal": "#DFF3EF", "orange": "#FCEBD3", "green": "#E3F3E8", "grey": "#EEF0F4", "red": "#F9E0DC", "purple": "#ECE8FA"}
plt.rcParams["font.family"] = "DejaVu Serif"


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


def _box(ax, x, y, w, h, text, fc="grey", ec=NAVY, fs=5.6, bold=False, lw=0.7, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=PALE.get(fc, fc), ec=ec, lw=lw, linestyle=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=NAVY, fontweight="bold" if bold else "normal", linespacing=1.15)


def _arrow(ax, x1, y1, x2, y2, color=NAVY, style="-|>", lw=0.8, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=6, lw=lw, color=color, linestyle=ls, shrinkA=0, shrinkB=0))


def arch():
    fig, ax = _canvas(3.5, 3.0, 100, 86)
    _box(ax, 1, 73, 98, 11, "Browser: React 19 + Vite (port 5404)\nLanding · Dashboard · Forecast · Models · Sentiment · About", "blue", fs=5.3, bold=True)
    _arrow(ax, 50, 73, 50, 69.5, style="<|-|>")
    _box(ax, 1, 56, 98, 12, "FastAPI service (port 8404): 7 JSON endpoints + built site\nreads stored JSON; history and sentiment are computed live", "purple", fs=5.3, bold=True)
    _arrow(ax, 50, 56, 50, 52.5)
    mods = [("data_loader\nYahoo -> CSV\n-> synthetic", "orange"), ("sentiment\nNewsAPI or\nsynthetic;\nFinBERT-tone", "orange"), ("baselines\nARIMA SARIMAX\nProphet RF SVR", "teal"),
            ("models_dl\nLSTM, LSTM +\n4-head attn.", "teal"), ("federated\nFedAvg\n10 clients", "teal"), ("forecast\n5 / 30 days\n+ band", "teal")]
    w = 15.2
    for i, (t, c) in enumerate(mods):
        _box(ax, 1 + i * 16.55, 29, w, 23, t, c, fs=4.5)
    ax.text(53, 53.6, "pipeline modules (offline: backend.train)", ha="left", fontsize=4.6, color=GREY, style="italic")
    _arrow(ax, 50, 29, 50, 25.5)
    _box(ax, 1, 10, 98, 15, "Files (no database): artifacts/metrics.json, forecasts.json, serving/*.keras, plots ·\ndata/<TICKER>.csv · data/news_cache/*.json", "grey", fs=5.0)
    ax.text(50, 4, "No login, no database, no multiple-instance component", ha="center", fontsize=5.2, color=RED, fontweight="bold")
    return _save(fig, "paper_arch.png")


def flow():
    fig, ax = _canvas(3.5, 3.2, 100, 92)
    ax.text(1, 89.5, "A  Product pipeline (python -m backend.train)", fontsize=5.6, color=NAVY, fontweight="bold")
    xs = [1, 17.5, 34, 50.5, 67, 83.5]
    lab = [("1 Load\n10 tickers,\n501 rows", "orange"), ("2 Baselines\nARIMA, RF,\nSVR ...", "teal"), ("3 Daily\nsentiment\nFinBERT-tone", "orange"), ("4 LSTM\ntier", "blue"), ("5 + 4-head\nattention", "blue"), ("6 + sentiment\nchannel", "blue")]
    for x, (t, c) in zip(xs, lab):
        _box(ax, x, 68, 14.5, 17, t, c, fs=4.5)
    for x in xs[:-1]:
        _arrow(ax, x + 14.9, 76.5, x + 16.2, 76.5)
    _box(ax, 1, 46, 31, 16, "7 FedAvg\n10 clients x 2 rounds\nx 3 local epochs", "purple", fs=4.8)
    _box(ax, 36, 46, 28, 16, "8 Score each tier\n80/20 chronological\nsplit, 97 windows", "green", fs=4.8)
    _box(ax, 68, 46, 31, 16, "9 Write JSON, Keras\nthen serve: API and\nsix screens", "grey", fs=4.8)
    _arrow(ax, 32.5, 54, 35.3, 54)
    _arrow(ax, 64.5, 54, 67.3, 54)
    _arrow(ax, 91, 68, 91, 63.5, ls=":")
    ax.plot([1, 99], [41, 41], color=GREY, lw=0.5, ls="--")
    ax.text(1, 37.5, "B  Offline multiple-instance study (not in the application)", fontsize=5.6, color=RED, fontweight="bold")
    b = [("Headlines of\nticker T,\nbefore close\nof day t", "orange"), ("FinBERT-tone\ninstance\nvectors h_i", "orange"), ("Gated attention\npooling\nz = Σ a_i h_i", "purple"), ("+ LSTM over\n20 price days", "blue"), ("P(close t+1\n> close t)", "green")]
    w = 17.5
    for i, (t, c) in enumerate(b):
        _box(ax, 1 + i * 19.7, 8, w, 24, t, c, fs=4.4)
        if i:
            _arrow(ax, 1 + i * 19.7 - 1.5, 20, 1 + i * 19.7 + 0.3, 20)
    ax.text(50, 2.5, "bag label = next-day direction only; no headline is labelled", ha="center", fontsize=4.8, color=GREY, style="italic")
    return _save(fig, "paper_flow.png")


def results():
    """Panel (a): true-target MAE per model against persistence; panel (b): MIL study accuracy against the always-up rate."""
    RR, MIL = F.RR, F.MIL
    T = list(RR["tickers"])
    S = len(RR["seeds"])

    def tier(t):
        return np.mean([np.mean([RR["tickers"][k]["models"][t][s]["mae_true"] for k in T]) for s in range(S)])

    def sd(t):
        return np.std([np.mean([RR["tickers"][k]["models"][t][s]["mae_true"] for k in T]) for s in range(S)])

    rows = [("Persistence", np.mean([RR["tickers"][k]["persistence"]["mae"] for k in T]), 0, GREEN),
            ("Random Forest", np.mean([RR["tickers"][k]["baselines"]["random_forest"]["mae"] for k in T]), 0, TEAL),
            ("ARIMA", np.mean([RR["tickers"][k]["baselines"]["arima"]["mae"] for k in T]), 0, TEAL),
            ("LSTM + attention", tier("lstm_attention"), sd("lstm_attention"), BLUE),
            ("+ sentiment", tier("lstm_attention_sentiment"), sd("lstm_attention_sentiment"), BLUE),
            ("LSTM", tier("lstm"), sd("lstm"), BLUE),
            ("Hybrid (FedAvg)", tier("hybrid_federated"), sd("hybrid_federated"), BLUE)]
    fig, (a, b) = plt.subplots(2, 1, figsize=(3.4, 3.9), gridspec_kw={"height_ratios": [1.0, 1.0], "hspace": 0.78})
    y = np.arange(len(rows))[::-1]
    a.barh(y, [r[1] for r in rows], xerr=[r[2] for r in rows], color=[r[3] for r in rows], height=0.62, error_kw={"lw": 0.7, "capsize": 2})
    a.set_yticks(y)
    a.set_yticklabels([r[0] for r in rows], fontsize=6)
    for yy, r in zip(y, rows):
        a.text(r[1] + r[2] + 1.0, yy, f"{r[1]:.1f}", va="center", fontsize=5.6)
    a.set_xlabel("MAE on real closes ($), ten-ticker mean; bars = sd over seeds", fontsize=5.2)
    a.set_title("(a) Deep tiers against 'tomorrow = today'", fontsize=6.4, loc="left")
    a.tick_params(axis="x", labelsize=5.6)
    a.set_xlim(0, max(r[1] + r[2] for r in rows) * 1.18)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    names = [("majority_class", "Majority class"), ("lstm_price", "LSTM price\n(same window)"), ("lstm_price_full_history", "LSTM price\n(since 2016)"), ("lstm_flat_sentiment", "+ mean\nsentiment"),
             ("lstm_mil_mean", "MIL\nmean"), ("lstm_mil_max", "MIL\nmax"), ("lstm_mil_attention", "MIL\nattention"), ("placebo_mil_attention_shuffled_bags", "Placebo\nbags")]
    acc = [MIL["models"][k]["summary"]["accuracy"] for k, _ in names]
    x = np.arange(len(names))
    b.bar(x, [m["mean"] * 100 for m in acc], yerr=[m["std"] * 100 for m in acc], color=[GREY, BLUE, BLUE, ORANGE, PURPLE, PURPLE, PURPLE, RED], width=0.66, error_kw={"lw": 0.7, "capsize": 2})
    b.axhline(MIL["always_up_accuracy_test"] * 100, color=NAVY, lw=0.9, ls="--")
    b.text(len(names) - 0.5, MIL["always_up_accuracy_test"] * 100 + 0.35, f"always up {MIL['always_up_accuracy_test'] * 100:.1f} %", ha="right", fontsize=5.4, color=NAVY)
    b.set_xticks(x)
    b.set_xticklabels([n for _, n in names], fontsize=5.0, rotation=40, ha="right")
    b.set_ylim(44, 58)
    b.set_ylabel("next-day accuracy (%)", fontsize=5.4)
    b.set_title(f"(b) Real headlines: {MIL['n_test_pooled']:,} test days, 7 tickers, 5 seeds", fontsize=6.4, loc="left")
    b.tick_params(axis="y", labelsize=5.6)
    for s in ("top", "right"):
        b.spines[s].set_visible(False)
    fig.subplots_adjust(left=0.27, right=0.97, top=0.95, bottom=0.17)
    return _save(fig, "paper_results.png")


def shot(name, out, crop=None):
    im = Image.open(F.shot(name)).convert("RGB")
    if crop:
        im = im.crop(crop)
    p = os.path.join(F.FIGS, out)
    os.makedirs(F.FIGS, exist_ok=True)
    im.save(p)
    return p


def make():
    return {"arch": arch(), "flow": flow(), "results": results(),
            "forecast": shot("04_forecast_5day.png", "paper_shot_forecast.png", (264, 72, 1440, 900)),
            "models": shot("06_models_comparison.png", "paper_shot_models.png", (264, 72, 1440, 900))}
