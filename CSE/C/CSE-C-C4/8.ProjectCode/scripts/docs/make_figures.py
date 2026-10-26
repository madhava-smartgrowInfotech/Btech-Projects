"""QuantPulse result figures f01-f14 (matplotlib, 150 dpi) -> docs/figures/.   Run from 8.ProjectCode:

    python -m scripts.docs.make_figures [f01 f05 ...]

Every plotted number is read from experiments/**/metrics.json or artifacts/metrics.json through scripts/docs/facts.py; only the base-paper
figures in F.BASE_PAPER_RESULTS are typed values (quoted from the paper's text).
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import facts as F

OUT = Path(F.FIGS)
OUT.mkdir(parents=True, exist_ok=True)
NAVY, INK, GREY, TEAL, ORANGE, RED, PURPLE, LIGHT = "#1B2A41", "#14213D", "#7A8794", "#14907F", "#D9772F", "#C0392B", "#6B5BD2", "#C9D3DF"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#8895A7",
                     "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "axes.titleweight": "bold", "axes.titlesize": 10, "figure.facecolor": "white",
                     "axes.grid": True, "grid.color": "#E6EBF1", "grid.linewidth": 0.7, "axes.axisbelow": True})
T = F.TICKERS
RR, SUM, FWD, MIL, API = F.RR, F.SUM, F.FWD, F.MIL, F.API
S = len(RR["seeds"])
TIERS = ["lstm", "lstm_attention", "lstm_attention_sentiment", "attention_shuffled_sentiment", "hybrid_federated"]
TSHORT = {"lstm": "LSTM", "lstm_attention": "LSTM +\nattention", "lstm_attention_sentiment": "+ attention\n+ sentiment", "attention_shuffled_sentiment": "placebo\n(shuffled sent.)", "hybrid_federated": "hybrid\n(FedAvg)"}
TCOL = {"lstm": GREY, "lstm_attention": NAVY, "lstm_attention_sentiment": ORANGE, "attention_shuffled_sentiment": PURPLE, "hybrid_federated": TEAL}


def save(fig, name, foot=None):
    if foot:
        fig.text(0.01, -0.02, foot, fontsize=7, color=GREY, ha="left", va="top")
    fig.savefig(OUT / name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


def seed_mean(tier, key):
    """ten-ticker mean per seed"""
    return np.array([np.mean([RR["tickers"][t]["models"][tier][s][key] for t in T]) for s in range(S)])


def tick_mean(tier, key, t):
    return float(np.mean([x[key] for x in RR["tickers"][t]["models"][tier]]))


def f01():
    keys = ["arima", "sarimax", "prophet", "random_forest", "svr", "lstm", "lstm_attention", "lstm_attention_sentiment", "hybrid_federated"]
    names = ["ARIMA", "SARIMAX", "Prophet", "Random\nForest", "SVR", "LSTM", "LSTM +\nattention", "+ attention\n+ sentiment", "hybrid\n(FedAvg)"]
    m = [SUM["models"][k]["mae"]["mean"] for k in keys]
    lo = [SUM["models"][k]["mae"]["min"] for k in keys]
    hi = [SUM["models"][k]["mae"]["max"] for k in keys]
    fig, ax = plt.subplots(figsize=(8.4, 3.8))
    cols = [GREY] * 5 + [NAVY] * 4
    ax.bar(range(9), m, color=cols, width=0.7)
    ax.errorbar(range(9), m, yerr=[np.array(m) - lo, np.array(hi) - np.array(m)], fmt="none", ecolor=INK, capsize=3, lw=1)
    for i, v in enumerate(m):
        ax.text(i, hi[i] + 2, f"{v:.1f}", ha="center", fontsize=8, color=INK)
    ax.set_xticks(range(9))
    ax.set_xticklabels(names, fontsize=7.5)
    ax.set_ylabel("MAE on test windows (US$)")
    ax.set_title("Shipped artefact: mean MAE per model (range over tickers)")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=GREY), plt.Rectangle((0, 0), 1, 1, color=NAVY)], labels=["classical baselines", "deep tiers"], frameon=False, loc="upper right")
    save(fig, "f01_shipped_mae_by_model.png", "artifacts/metrics.json, 10 tickers, seed 42, 97 (deep) / 101 (baselines) test windows each; bars = mean, whiskers = min-max.")


def f02():
    x = np.arange(len(T))
    pers = [RR["tickers"][t]["persistence"]["mae"] for t in T]
    att = [tick_mean("lstm_attention", "mae_true", t) for t in T]
    lstm = [tick_mean("lstm", "mae_true", t) for t in T]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    w = 0.27
    ax.bar(x - w, pers, w, color=TEAL, label="persistence (yesterday's close)")
    ax.bar(x, att, w, color=NAVY, label="LSTM + attention")
    ax.bar(x + w, lstm, w, color=GREY, label="LSTM")
    ax.set_xticks(x)
    ax.set_xticklabels(T, fontsize=8)
    ax.set_ylabel("MAE vs real closes (US$)")
    ax.set_title("Deep tiers against 'tomorrow = today' on real closes")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "f02_true_mae_vs_persistence.png", f"Re-run on the 501 training rows, {S} seeds averaged per ticker; persistence has no randomness. Test part = last 20 % of rows.")


def f03():
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.4, 3.5), gridspec_kw={"width_ratios": [1, 1]})
    above = [RR["tickers"][t]["test_close_above_train_max_pct"] for t in T]
    a.barh(T[::-1], above[::-1], color=ORANGE)
    a.set_xlabel("test closes above the training maximum (%)")
    a.set_title("Targets clipped by the scaler")
    a.set_xlim(0, 100)
    ship = [tick_mean("lstm_attention", "directional_accuracy", t) * 100 for t in T]
    true = [tick_mean("lstm_attention", "da_true", t) * 100 for t in T]
    y = np.arange(len(T))
    b.barh(y + 0.2, ship[::-1], 0.38, color=ORANGE, label="shipped scoring")
    b.barh(y - 0.2, true[::-1], 0.38, color=NAVY, label="real closes")
    b.axvline(50, color=INK, lw=0.8, ls="--")
    b.set_yticks(y)
    b.set_yticklabels(T[::-1])
    b.set_xlabel("directional accuracy, LSTM + attention (%)")
    b.set_title("Direction: shipped vs true")
    b.set_xlim(0, 100)
    b.legend(frameon=False, fontsize=7, loc="lower right")
    fig.tight_layout()
    save(fig, "f03_clipping_and_direction.png", f"Re-run, {S} seeds averaged per ticker; dashed line = 50 %. A flat clipped target makes 'not up' and 'not up' agree.")


def f04():
    fig, axes = plt.subplots(2, 5, figsize=(10.5, 4.6), sharex=True)
    for ax, t in zip(axes.ravel(), T):
        r = FWD["tickers"][t]
        act = np.array(r["actual"])
        pred = np.array(r["long_pred"])
        d = np.arange(1, len(act) + 1)
        ax.plot(np.arange(0, len(act) + 1), np.r_[r["last_close"], act], color=INK, lw=1.4, label="actual close")
        ax.plot(np.arange(0, len(pred) + 1), np.r_[r["last_close"], pred], color=ORANGE, lw=1.4, ls="--", label="shipped forecast")
        ax.set_title(t, fontsize=9)
        ax.tick_params(labelsize=7)
    for ax in axes[1]:
        ax.set_xlabel("trading days after 2026-09-08", fontsize=7)
    for ax in axes[:, 0]:
        ax.set_ylabel("close (US$)", fontsize=7)
    axes[0, 0].legend(frameon=False, fontsize=7)
    fig.suptitle("Shipped 30-day forecasts against the closes that followed", fontweight="bold", fontsize=11, y=1.0)
    fig.tight_layout()
    save(fig, "f04_forward_test_30day.png", "artifacts/metrics.json forecasts made from the 2026-09-08 close; actual closes from the pinned snapshot (30 trading days), one panel per ticker, y-axes differ.")


def f05():
    x = np.arange(len(T))
    p = [FWD["tickers"][t]["short"]["pred_end_pct_change"] for t in T]
    a = [FWD["tickers"][t]["short"]["actual_end_pct_change"] for t in T]
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    ax.bar(x - 0.2, p, 0.38, color=ORANGE, label="shipped forecast")
    ax.bar(x + 0.2, a, 0.38, color=NAVY, label="actual")
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(T, fontsize=8)
    ax.set_ylabel("change after 5 trading days (%)")
    ax.set_title(f"5-day change: forecast {FWD['short']['mean_pred_change_pct']:+.1f} % on average, actual {FWD['short']['mean_actual_change_pct']:+.1f} %")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "f05_forecast_vs_actual_change.png", f"10 tickers, one forecast each; trend flag right for {FWD['short']['trend_hits']} of 10.")


def f06():
    n = RR["tickers"][T[0]]["n_rows"]
    k_raw = int(n * 0.8)
    img = np.zeros((len(T), n))
    for i, t in enumerate(T):
        nz = RR["tickers"][t]["sentiment_nonzero_rows"]
        img[i, n - nz:] = 1
    fig, (a, b) = plt.subplots(1, 2, figsize=(8.4, 3.4), gridspec_kw={"width_ratios": [1.6, 1]})
    a.imshow(img, aspect="auto", cmap=matplotlib.colors.ListedColormap(["#EEF2F7", ORANGE]), interpolation="nearest", extent=[0, n, len(T), 0])
    a.axvline(k_raw, color=INK, lw=1.2, ls="--")
    a.set_yticks(np.arange(len(T)) + 0.5)
    a.set_yticklabels(T, fontsize=8)
    a.set_xlabel("row (trading day) of the 501-row window; dashed line = train/test boundary")
    a.set_title("Where the sentiment channel is non-zero")
    a.grid(False)
    tr = [RR["tickers"][t]["sentiment_nonzero_in_train_part"] for t in T]
    te = [RR["tickers"][t]["sentiment_nonzero_in_test_part"] for t in T]
    x = np.arange(len(T))
    b.bar(x - 0.2, tr, 0.38, color=NAVY, label="training part (400 rows)")
    b.bar(x + 0.2, te, 0.38, color=ORANGE, label="test part (101 rows)")
    b.set_xticks(x)
    b.set_xticklabels(T, rotation=60, fontsize=7)
    b.set_ylabel("non-zero rows")
    b.set_title("Rows with sentiment")
    b.set_ylim(0, 125)
    for xi in x:
        b.text(xi - 0.2, 2, "0", ha="center", fontsize=7, color=NAVY)
    b.legend(frameon=False, fontsize=7, loc="upper center", ncol=1)
    fig.tight_layout()
    save(fig, "f06_sentiment_channel.png", "Synthetic template headlines exist only for the last 90 trading days, then are forward-filled; earlier rows are exactly 0 (re-run data, 10 tickers).")


def f07():
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    pers = np.mean([RR["tickers"][t]["persistence"]["mae"] for t in T])
    for i, tier in enumerate(TIERS):
        v = seed_mean(tier, "mae_true")
        ax.scatter(np.full(S, i) + np.linspace(-0.12, 0.12, S), v, color=TCOL[tier], s=34, zorder=3)
        ax.hlines(v.mean(), i - 0.25, i + 0.25, color=INK, lw=1.5, zorder=4)
        ax.text(i, v.max() + 1.5, f"{v.mean():.1f}", ha="center", fontsize=8)
    ax.axhline(pers, color=TEAL, lw=1.4, ls="--")
    ax.text(len(TIERS) - 0.5, pers + 1.2, f"persistence {pers:.1f}", color=TEAL, ha="right", fontsize=8)
    ax.set_xticks(range(len(TIERS)))
    ax.set_xticklabels([TSHORT[t] for t in TIERS], fontsize=8)
    ax.set_ylabel("MAE vs real closes (US$), ten-ticker mean")
    ax.set_ylim(0, max(seed_mean(t, "mae_true").max() for t in TIERS) * 1.15)
    ax.set_title("Seed-to-seed variation of each tier")
    save(fig, "f07_seed_variation.png", f"Each dot = one seed ({S} seeds), mean of the ten tickers; bar = mean over seeds.")


MNAMES = {"majority_class": "majority class", "logreg_price_C1.0": "logistic reg. (price)", "lstm_price": "LSTM price (same window)", "lstm_price_full_history": "LSTM price (since 2016)",
          "lstm_flat_sentiment": "LSTM + flat sentiment", "lstm_mil_mean": "LSTM + MIL mean", "lstm_mil_max": "LSTM + MIL max", "lstm_mil_attention": "LSTM + MIL attention",
          "mil_attention_news_only": "MIL attention, news only", "placebo_mil_attention_shuffled_bags": "placebo (other days' bags)"}


def f08():
    keys = list(MNAMES)
    m = [MIL["models"][k]["summary"]["accuracy"]["mean"] * 100 for k in keys]
    sd = [MIL["models"][k]["summary"]["accuracy"]["std"] * 100 for k in keys]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    y = np.arange(len(keys))[::-1]
    cols = [GREY if "MIL" not in MNAMES[k] and "sentiment" not in MNAMES[k] else (TEAL if "MIL" in MNAMES[k] and "placebo" not in MNAMES[k] else (PURPLE if "placebo" in MNAMES[k] else NAVY)) for k in keys]
    ax.barh(y, m, xerr=sd, color=cols, capsize=3, ecolor=INK)
    ax.axvline(MIL["always_up_accuracy_test"] * 100, color=RED, lw=1.4, ls="--")
    ax.text(MIL["always_up_accuracy_test"] * 100 + 0.2, y[0] + 0.45, f"always up {MIL['always_up_accuracy_test'] * 100:.1f} %", color=RED, fontsize=8)
    ax.axvline(50, color=INK, lw=0.8, ls=":")
    ax.set_yticks(y)
    ax.set_yticklabels([MNAMES[k] for k in keys], fontsize=8)
    ax.set_xlim(40, 60)
    ax.set_xlabel("accuracy on pooled test samples (%)")
    ax.set_title("Next-day direction: price-only vs news (MIL) models")
    for yi, v in zip(y, m):
        ax.text(59.8, yi, f"{v:.1f}", fontsize=8, color=INK, ha="right", va="center")
    save(fig, "f08_mil_accuracy.png", f"{MIL['n_test_pooled']} test samples (Q2-Q4 2023, {len(MIL['tickers'])} tickers); mean ± std over {len(MIL['seeds'])} seeds (one run for majority class and logistic regression).")


SHORT9 = ["LSTM price\n(same window)", "LSTM price\n(since 2016)", "LSTM +\nflat sentiment", "LSTM +\nMIL mean", "LSTM +\nMIL max", "LSTM +\nMIL attention", "MIL attention\nnews only", "placebo\n(other bags)"]


def f09():
    keys = ["lstm_price", "lstm_price_full_history", "lstm_flat_sentiment", "lstm_mil_mean", "lstm_mil_max", "lstm_mil_attention", "mil_attention_news_only", "placebo_mil_attention_shuffled_bags"]
    fig, ax = plt.subplots(figsize=(8.4, 3.8))
    x = np.arange(len(keys))
    for j, (met, c) in enumerate((("precision", NAVY), ("recall", ORANGE), ("f1", TEAL))):
        v = [MIL["models"][k]["summary"][met]["mean"] for k in keys]
        e = [MIL["models"][k]["summary"][met]["std"] for k in keys]
        ax.bar(x + (j - 1) * 0.27, v, 0.27, yerr=e, color=c, capsize=2, ecolor=INK, label=met if met != "f1" else "F1")
    ax.set_xticks(x)
    ax.set_xticklabels(SHORT9, fontsize=7)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("score (positive class = next day up)")
    ax.set_title("Precision, recall and F1 of the direction models")
    ax.legend(frameon=False, ncol=3, fontsize=8, loc="upper left")
    save(fig, "f09_mil_prf.png", f"{MIL['n_test_pooled']} pooled test samples, threshold 0.5; mean ± std over {len(MIL['seeds'])} seeds. High recall of the full-history LSTM = it predicts 'up' on 95 % of days.")


def f10():
    items = [(k, v) for k, v in MIL["paired_vs_lstm_price"].items()]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    y = np.arange(len(items))[::-1]
    for yi, (k, v) in zip(y, items):
        ax.plot([v["ci95"][0] * 100, v["ci95"][1] * 100], [yi, yi], color=NAVY, lw=2)
        ax.scatter([v["acc_diff"] * 100], [yi], color=ORANGE, zorder=3, s=36)
        ax.text(v["ci95"][1] * 100 + 0.3, yi, f"{v['acc_diff'] * 100:+.1f}", va="center", fontsize=8)
    ax.axvline(0, color=INK, lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels([MNAMES.get(k, k) for k, _ in items], fontsize=8)
    ax.set_xlabel("accuracy difference to the price-only LSTM (points)")
    ax.set_title("Paired bootstrap: does news help?")
    save(fig, "f10_mil_paired_ci.png", f"{MIL['n_test_pooled']} test samples, seed-averaged probabilities, 2,000 bootstrap resamples; dot = difference, line = 95 % interval.")


def f11():
    keys = ["health", "tickers", "metrics_all", "metrics_one", "forecast_short", "forecast_long", "history_120d", "sentiment", "frontend_index"]
    lab = ["health", "tickers", "metrics (all)", "metrics (1)", "forecast 5d", "forecast 30d", "history 120d", "sentiment", "web index"]
    med = [API["endpoints"][k]["median_ms"] for k in keys]
    p95 = [API["endpoints"][k]["p95_ms"] for k in keys]
    x = np.arange(len(keys))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.bar(x - 0.2, med, 0.38, color=NAVY, label="median")
    ax.bar(x + 0.2, p95, 0.38, color=ORANGE, label="p95")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([l.replace(" ", chr(10), 1) for l in lab], fontsize=7.5)
    ax.set_ylabel("latency (ms, log scale)")
    ax.set_title("API latency on 127.0.0.1")
    ax.legend(frameon=False, fontsize=8)
    for xi, v in zip(x, med):
        ax.text(xi - 0.2, v * 1.15, f"{v:.0f}" if v >= 10 else f"{v:.1f}", ha="center", fontsize=7)
    save(fig, "f11_api_latency.png", "Single uvicorn worker, Windows 11, shared machine; 8-50 warm calls per endpoint. History re-downloads from Yahoo; sentiment runs FinBERT-tone.")


def f12():
    B = F.BASE_PAPER_RESULTS
    fig, (a, b) = plt.subplots(1, 2, figsize=(8.2, 3.8))
    labs = ["base paper\nhybrid (reported)", "QuantPulse hybrid\n(shipped, mean)", "QuantPulse hybrid\n(re-run, real closes)"]
    vals = [B["r2_avg"], SUM["models"]["hybrid_federated"]["r2"]["mean"], seed_mean("hybrid_federated", "r2_true").mean()]
    a.bar(range(3), vals, color=[GREY, ORANGE, NAVY])
    a.set_yscale("symlog", linthresh=1)
    a.set_yticks([-100, -10, -1, 0, 1])
    a.set_yticklabels(["-100", "-10", "-1", "0", "1"])
    a.axhline(0, color=INK, lw=0.8)
    for i, v in enumerate(vals):
        a.text(i, v + (0.15 if v > 0 else -0.5) if v > 0 else v * 1.35 - 0.2, f"{v:.2f}", ha="center", fontsize=8)
    a.set_xticks(range(3))
    a.set_xticklabels(labs, fontsize=7)
    a.set_ylabel("R2 (symlog axis)")
    a.set_title("Variance explained")
    ship = SUM["models"]["lstm"]["directional_accuracy"]["mean"] * 100
    true = seed_mean("lstm", "da_true").mean() * 100
    labs2 = ["base paper\nLSTM (reported)", "QuantPulse LSTM\n(shipped scoring)", "QuantPulse LSTM\n(real closes)"]
    v2 = [B["lstm_trend_acc"], ship, true]
    b.bar(range(3), v2, color=[GREY, ORANGE, NAVY])
    b.axhline(50, color=INK, lw=0.8, ls="--")
    for i, v in enumerate(v2):
        b.text(i, v + 1, f"{v:.1f}", ha="center", fontsize=8)
    b.set_ylim(0, 85)
    b.set_xticks(range(3))
    b.set_xticklabels(labs2, fontsize=7)
    b.set_ylabel("trend / directional accuracy (%)")
    b.set_title("Direction")
    fig.suptitle("Base paper vs this project: datasets and protocols differ - indicative only", fontsize=9.5, fontweight="bold", y=1.02)
    fig.tight_layout()
    save(fig, "f12_base_paper_comparison.png", "Base paper: 30-day NewsAPI window, scaled units (text of Sections III-IV). QuantPulse: two years of data, 97 test windows per ticker; re-run = 5 seeds.")


def f13():
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.6), sharey=False)
    for ax, h, nm in ((axes[0], "short", "5-day"), (axes[1], "long", "30-day")):
        vals, errs = [], []
        for tier in TIERS:
            v = [np.mean([RR["tickers"][t]["forward"][tier][s][h]["mae"] for t in T]) for s in range(S)]
            vals.append(np.mean(v))
            errs.append(np.std(v))
        pers = np.mean([FWD["tickers"][t][h]["persistence_mae"] for t in T])
        ax.bar(range(len(TIERS)), vals, yerr=errs, color=[TCOL[t] for t in TIERS], capsize=3, ecolor=INK)
        ax.axhline(pers, color=TEAL, ls="--", lw=1.4, label=f"'no change' forecast: {pers:.1f}")
        ax.legend(frameon=False, fontsize=8, loc="upper right")
        ax.set_ylim(0, (max(vals) + max(errs)) * 1.28)
        ax.set_xticks(range(len(TIERS)))
        ax.set_xticklabels([TSHORT[t] for t in TIERS], fontsize=6.5)
        ax.set_ylabel("forward MAE (US$)")
        ax.set_title(f"{nm} forecasts, re-trained tiers")
    fig.tight_layout()
    save(fig, "f13_forward_tiers.png", f"Forecasts from the 2026-09-08 close against the following closes; ten-ticker mean, bars = mean ± std over {S} seeds.")


def f14():
    ex = max(MIL["attention_examples"], key=lambda e: e["n_headlines"])
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    labels = ["\n".join(textwrap.wrap(t["headline"], 62)) for t in ex["top"]]
    w = [t["weight"] for t in ex["top"]]
    y = np.arange(len(w))[::-1]
    ax.barh(y, w, color=NAVY)
    ax.axvline(ex["uniform_weight"], color=RED, ls="--", lw=1.4)
    ax.plot([], [], color=RED, ls="--", lw=1.4, label=f"uniform weight 1/{ex['n_headlines']} = {ex['uniform_weight']:.3f}")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("attention weight")
    ax.set_xlim(0, max(max(w), ex["uniform_weight"]) * 1.9)
    for yi, t in zip(y, ex["top"]):
        ax.text(t["weight"] + 0.0008, yi, f"{t['weight']:.3f}\npos {t['p_pos']:.2f} neg {t['p_neg']:.2f}", va="center", fontsize=7)
    ax.set_title(f"Gated attention, {ex['ticker']} {ex['date']}: {ex['n_headlines']} headlines, next day {'up' if ex['label_next_day_up'] else 'down'}, p(up) = {ex['p_up']:.2f}", fontsize=9, loc="left")
    save(fig, "f14_mil_attention_examples.png", "Top three headlines by attention weight, last test fold, first seed. Weights sit close to uniform: attention did not single out headlines.")


ALL = {f"f{i:02d}": g for i, g in enumerate([f01, f02, f03, f04, f05, f06, f07, f08, f09, f10, f11, f12, f13, f14], 1)}

if __name__ == "__main__":
    for k in (sys.argv[1:] or ALL):
        ALL[k]()
