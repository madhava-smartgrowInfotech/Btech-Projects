"""QuantPulse diagrams 07-12: sequence, use case, ER, core-algorithm flowchart, sentiment flowchart, model architecture."""
from __future__ import annotations

from pathlib import Path

from matplotlib.patches import Ellipse, Rectangle

from .dgm_lib import *  # noqa: F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"


# --------------------------------------------------------------- 07 sequence
def sequence():
    fig, ax = canvas(10, 8.6, 100, 86)
    names = ["User", "React Forecast\npage (browser)", "FastAPI\n(main.py)", "artifacts/\nmetrics.json", "data_loader\n(yfinance)", "Yahoo\nFinance"]
    xs = [9, 26, 43, 60, 77, 92]
    cols = [ORANGE, BLUE, NAVY, GREY, TEAL, GREY]
    for x, n, c in zip(xs, names, cols):
        box(ax, x, 82.5, 14.5, 6.0, n, c, fs=7.0, bold=True)
        ax.plot([x, x], [79.3, 2], color="#9AA7B8", lw=1.0, ls=(0, (4, 3)), zorder=1)

    def msg(i, j, y, text, dashed=False, color=NAVY, above=True):
        arrow(ax, (xs[i], y), (xs[j], y), color=color, lw=1.4, ls="--" if dashed else "-")
        ax.text((xs[i] + xs[j]) / 2, y + (1.5 if above else -1.6), text, ha="center", fontsize=6.6, color=INK, va="center", linespacing=1.15,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9), zorder=6)

    def note(x, y, w, h, text, fc=PALE_ORANGE, ec=ORANGE):
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=1.0, zorder=3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=6.4, color=INK, zorder=4, linespacing=1.2)

    msg(0, 1, 76, "open /app/forecast?t=TSLA&h=short")
    msg(1, 2, 71.5, "GET /api/tickers")
    msg(2, 3, 67.5, "metrics(): read JSON once, cached", above=True)
    msg(3, 2, 63.8, "per-ticker objects", dashed=True)
    msg(2, 1, 60.2, "200 {tickers:[{ticker,last_close,trend,mode}]}", dashed=True)
    ax.add_patch(Rectangle((19, 14.5), 77, 43, fc="none", ec=PURPLE, lw=1.2, ls="--", zorder=2))
    ax.text(20, 55.4, "par  (Promise.all, both started together)", fontsize=7.0, color=PURPLE, fontweight="bold")
    msg(1, 2, 51, "GET /api/forecast/TSLA?horizon=short")
    msg(2, 3, 47.2, "lookup forecast_short (5 rows)")
    msg(2, 1, 43.6, "200 {last_close, trend, forecast[5]}", dashed=True)
    ax.plot([19, 96], [41.0, 41.0], color=PURPLE, lw=0.9, ls=":")
    msg(1, 2, 38.2, "GET /api/history/TSLA?days=250")
    msg(2, 4, 34.4, "load_ticker('TSLA')")
    msg(4, 5, 30.6, "yf.download(period 2y, 1d)")
    msg(5, 4, 26.8, "OHLCV rows (live)", dashed=True)
    note(61, 21.3, 33, 3.7, "writes data/TSLA.csv; mode = 'live'\n(falls back to CSV, then synthetic)", fc=PALE_TEAL, ec=TEAL)
    msg(4, 2, 18.8, "(df, mode)", dashed=True)
    msg(2, 1, 15.6, "200 history + forecast_overlay (BDay dates)", dashed=True)
    note(3, 5.0, 94, 7.0, "Page: buildSeries() draws actual closes, the dashed forecast and the confidence band; the table adds the actual close once it exists.\n"
         "No login step exists: no endpoint checks credentials.  /api/history costs one Yahoo download per call.", fc=PALE_BLUE, ec=BLUE)
    msg(1, 0, 13.4, "chart + 5-day table rendered", dashed=True, color=ORANGE)
    save(fig, OUT / "07_sequence_flow.png")


# ------------------------------------------------------------------ 08 use case
def use_case():
    fig, ax = canvas(10, 6.8, 100, 68)
    ax.add_patch(Rectangle((24, 2.2), 52, 65, fc="#FAFBFD", ec=NAVY, lw=1.6, zorder=1))
    ax.text(50, 64.6, "QuantPulse (website + pipeline)", ha="center", fontsize=9, fontweight="bold", color=NAVY)
    ys = [57, 48.5, 40, 31.5, 23, 14.5]
    labels = ["View dashboard of 10 tickers\n(last close, trend, outlook)", "Open 5-day / 30-day forecast\nwith confidence band", "Compare models (ablation,\nbaselines, loss curves)",
              "Inspect news sentiment\nand headlines", "Read method and data screen", "Switch light / dark theme"]
    for y, t in zip(ys, labels):
        ellipse(ax, 50, y, 36, 7.2, t, fs=7.0)
    ellipse(ax, 38, 5.2, 24, 5.4, "Retrain: python -m backend.train", fc=PALE_ORANGE, ec=ORANGE, fs=6.4)
    ellipse(ax, 64, 5.2, 24, 5.4, "Run pytest + smoke test", fc=PALE_ORANGE, ec=ORANGE, fs=6.4)
    box(ax, 11, 40, 17, 6, "Trader /\nanalyst", ORANGE, fs=8.5, bold=True)
    box(ax, 11, 11, 17, 6, "Evaluator /\ndeveloper", GREY, fs=8.5, bold=True)
    box(ax, 89, 50, 17, 6, "Yahoo Finance", GREY, fs=8.0, bold=True)
    box(ax, 89, 34, 17, 6, "NewsAPI\n(optional)", GREY, fs=8.0, bold=True)
    box(ax, 89, 20, 17, 6, "Hugging Face\n(FinBERT)", GREY, fs=8.0, bold=True)
    for y in ys:
        arrow(ax, (19.5, 40), (32, y), color=NAVY, lw=1.0, style="-")
    arrow(ax, (19.5, 10.5), (26.5, 5.9), color=NAVY, lw=1.0, style="-")
    arrow(ax, (19.5, 9.5), (52, 5.5), color=NAVY, lw=1.0, style="-")
    for y in (57, 48.5):
        arrow(ax, (80.5, 50), (68, y), color=GREY, lw=1.0, style="-", ls="--")
    arrow(ax, (80.5, 34), (68, 31.5), color=GREY, lw=1.0, style="-", ls="--")
    arrow(ax, (80.5, 20), (68, 31.5), color=GREY, lw=1.0, style="-", ls="--")
    ax.text(50, 0.4, "No login: every visitor of the website is the same actor. Dashed lines: external services supply data when a use case runs.", ha="center", fontsize=6.6, color=GREY, style="italic")
    save(fig, OUT / "08_use_case.png")


# ---------------------------------------------------------------------- 09 ER
def er():
    fig, ax = canvas(10, 7.8, 100, 78)

    def ent(cx, cy, w, name, attrs, c=NAVY):
        lh = 2.35
        h = 3.8 + lh * len(attrs) + 0.8
        ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, fc=WHITE, ec=c, lw=1.3, zorder=2))
        ax.add_patch(Rectangle((cx - w / 2, cy + h / 2 - 3.8), w, 3.8, fc=c, ec=c, zorder=3))
        ax.text(cx, cy + h / 2 - 1.9, name, ha="center", va="center", color=WHITE, fontsize=8.0, fontweight="bold", zorder=4)
        for i, a in enumerate(attrs):
            ax.text(cx - w / 2 + 0.9, cy + h / 2 - 3.8 - 1.5 - i * lh, a, ha="left", va="center", fontsize=6.5, color=INK, zorder=4, family="DejaVu Sans Mono")
        return h

    ent(14, 66, 24, "DailySentiment", ["PK ticker, date", "score = mean of the day", "ffill, 0 before 1st"], PURPLE)
    ent(50, 66, 26, "Headline", ["PK ticker, date, text", "source newsapi|synthetic", "sentiment_score [-1,1]"], PURPLE)
    ent(86, 66, 24, "ModelTier", ["PK name", "kind baseline|deep", "arima sarimax prophet", "random_forest svr lstm", "lstm_attention", "lstm_attention_sentiment", "hybrid_federated"], TEAL)
    ent(14, 40, 24, "PriceBar", ["PK ticker, date", "open high low close", "adj_close, volume"], BLUE)
    ent(50, 40, 26, "Ticker", ["PK symbol", "company (UI map)", "mode live|csv|synthetic", "n_rows, last_close, trend"])
    ent(86, 40, 24, "MetricRecord", ["PK ticker, model", "mae mse rmse r2", "directional_accuracy", "n_test"], TEAL)
    ent(14, 13, 24, "ArtifactFile", ["data/<T>.csv", "artifacts/metrics.json", "artifacts/forecasts.json", "serving/<T>_hybrid.keras", "serving/<T>_scalers.npz", "plots/*.png"], GREY)
    ent(50, 13, 26, "ForecastRow", ["PK ticker, horizon, day", "predicted_close", "lower, upper"], ORANGE)
    ent(86, 13, 24, "FederatedRound", ["PK round (1..2)", "mean_local_loss", "(copied into every", " ticker's record)"], GREY)
    L = dict(color=NAVY, lw=1.3, style="-")
    arrow(ax, (50, 47), (50, 60.2), "1 : n", lo=(3.5, 0), **L)
    arrow(ax, (37, 66), (26, 66), "n : 1  (per day)", lo=(0, 2.2), **L)
    arrow(ax, (37, 40), (26, 40), "1 : n", lo=(0, 2.2), **L)
    arrow(ax, (63, 40), (74, 40), "1 : n", lo=(0, 2.2), **L)
    arrow(ax, (86, 55.5), (86, 47), "1 : n", lo=(3.5, 0), **L)
    arrow(ax, (50, 33), (50, 18.8), "1 : n", lo=(3.5, 0), **L)
    arrow(ax, (86, 33), (86, 20), "1 : n  (per ticker)", lo=(8.5, 0), **L)
    arrow(ax, (14, 60.2), (14, 45.8), "aligned to trading dates", lo=(9.5, 0), color=GREY, lw=1.1, ls="--")
    arrow(ax, (14, 34.2), (14, 22.4), "stored in", lo=(5, 0), color=GREY, lw=1.1, ls="--")
    arrow(ax, (37, 13), (26, 13), "written to", lo=(0, 2.2), color=GREY, lw=1.1, ls="--")
    ax.text(50, 2.0, "Logical ER diagram: QuantPulse has no database. Entities are rows inside CSV and JSON files; relations are shared ticker / date keys.", ha="center", fontsize=6.9, color=GREY, style="italic")
    save(fig, OUT / "09_er_diagram.png")


# ----------------------------------------------------- 10 forecast flowchart
def flow_core():
    fig, ax = canvas(7.2, 9.6, 100, 133)
    C = 50
    box(ax, C, 129, 44, 5.2, "START  recursive_forecast(model, last_window,\nsteps, residual_std, close_scaler)", NAVY, fs=7.4)
    box(ax, C, 120, 52, 6.2, "win = last 20 scaled rows (20 x F);  scaled_preds = []\nsteps = 5 (short) or 30 (long)", BLUE, fs=7.4)
    diamond(ax, C, 110, 40, 9, "i < steps ?", fs=8.2)
    box(ax, C, 99, 54, 5.4, "p = model.predict(win)  (next scaled Close)", PURPLE, fs=7.4)
    box(ax, C, 91.5, 54, 5.0, "scaled_preds.append(p)", PURPLE, fs=7.4)
    box(ax, C, 82.5, 64, 7.6, "nxt = copy of win's last row;  nxt[Close] = p;\nnxt[Open] = nxt[High] = nxt[Low] = p\n(volume and sentiment carried forward)", PURPLE, fs=7.2)
    box(ax, C, 72.5, 54, 5.4, "win = win[1:] + [nxt]   (slide the window)", PURPLE, fs=7.4)
    arrow(ax, (C, 126.4), (C, 123.1), color=NAVY)
    arrow(ax, (C, 116.9), (C, 114.5), color=NAVY)
    arrow(ax, (C, 105.5), (C, 101.7), "yes", lo=(3, 0), color=NAVY)
    arrow(ax, (C, 96.3), (C, 94.0), color=NAVY)
    arrow(ax, (C, 89.0), (C, 86.3), color=NAVY)
    arrow(ax, (C, 78.7), (C, 75.2), color=NAVY)
    # loop back
    ax.plot([C + 27, 90, 90], [72.5, 72.5, 110], color=NAVY, lw=1.4, zorder=4)
    arrow(ax, (90, 110), (C + 20.3, 110), color=NAVY)
    ax.text(79, 74, "i += 1", fontsize=7, color=NAVY)
    arrow(ax, (C - 20, 110), (12, 110), "no", lo=(0, 1.8), color=NAVY, lw=1.4, style="-")
    ax.plot([12, 12], [110, 60], color=NAVY, lw=1.4, zorder=4)
    arrow(ax, (12, 60), (C - 25.6, 60), color=NAVY)
    box(ax, C, 60, 51, 6.4, "preds = close_scaler.inverse_transform(scaled_preds)\n(dollar prices)", TEAL, fs=7.2)
    box(ax, C, 49, 64, 6.8, "band(h) = 1.96 x residual_std x sqrt(h),  h = 1..steps\n(residual_std = std of test errors in scaled units)", TEAL, fs=7.2)
    box(ax, C, 38, 64, 7.2, "row h = {day: h, predicted_close: round(p_h, 2),\nlower: max(p_h - band_h, 0.01), upper: p_h + band_h}", TEAL, fs=7.2)
    diamond(ax, C, 25.5, 46, 11, "predicted_close of day 5\n>= last_close ?", fs=7.4)
    box(ax, 22, 12, 26, 5.2, "trend = 'up'", TEAL, fs=8.0)
    box(ax, 78, 12, 26, 5.2, "trend = 'down'", ORANGE, fs=8.0)
    box(ax, C, 3.6, 60, 5.0, "END  list of rows -> forecasts.json / metrics.json", NAVY, fs=7.4)
    arrow(ax, (C, 56.8), (C, 52.4), color=NAVY)
    arrow(ax, (C, 45.6), (C, 41.6), color=NAVY)
    arrow(ax, (C, 34.4), (C, 31.0), color=NAVY)
    arrow(ax, (C - 17, 25.5), (22, 14.6), "yes", lo=(-4, 1), color=NAVY)
    arrow(ax, (C + 17, 25.5), (78, 14.6), "no", lo=(4, 1), color=NAVY)
    arrow(ax, (22, 9.4), (C - 8, 6.1), color=NAVY)
    arrow(ax, (78, 9.4), (C + 8, 6.1), color=NAVY)
    save(fig, OUT / "10_flowchart_forecast.png")


# ------------------------------------------------------ 11 sentiment flowchart
def flow_sent():
    fig, ax = canvas(9.6, 8.2, 100, 85.5)
    box(ax, 50, 82, 52, 5.0, "get_daily_sentiment(ticker, trading_dates)", NAVY, fs=7.6)
    diamond(ax, 50, 72, 40, 9, "NEWSAPI_KEY set and\narticles returned (cache\nor request)?", fs=6.8)
    arrow(ax, (50, 79.5), (50, 76.5), color=NAVY)
    # live branch
    box(ax, 20, 58, 34, 8.4, "Live path: 50 articles of the last\n30 days (cached per ticker and day\nunder data/news_cache); titles + dates", BLUE, fs=6.6)
    box(ax, 20, 44.5, 32, 6.0, "score_headlines(titles)\nmeta.source = 'newsapi'", BLUE, fs=6.8)
    # synthetic branch
    box(ax, 80, 58, 34, 8.4, "Fallback: last 90 trading dates, 1-3\ntemplate headlines per day\n(positive 45 %, neutral 25 %, negative 30 %)", ORANGE, fs=6.6)
    box(ax, 80, 44.5, 34, 6.0, "score_headlines(same way)\nmeta.source = 'synthetic-fallback'", ORANGE, fs=6.8)
    arrow(ax, (33, 72), (20, 62.4), "yes", lo=(-3, 1.2), color=NAVY)
    arrow(ax, (67, 72), (80, 62.4), "no / failed", lo=(5, 1.2), color=NAVY)
    arrow(ax, (20, 53.7), (20, 47.6), color=NAVY)
    arrow(ax, (80, 53.7), (80, 47.6), color=NAVY)
    # scorer
    diamond(ax, 50, 33, 40, 9, "FinBERT-tone pipeline\nloads (transformers)?", fs=6.8)
    arrow(ax, (20, 41.4), (40, 35.5), color=NAVY)
    arrow(ax, (80, 41.4), (60, 35.5), color=NAVY)
    box(ax, 22, 22, 36, 8.4, "FinBERT: positive -> +prob, negative -> -prob,\nneutral -> 0 (batches of 32)\nscorer = 'finbert'", PURPLE, fs=6.6)
    box(ax, 78, 22, 36, 8.4, "Lexicon: (positive words - negative words)/3\nclipped to [-1, 1]\nscorer = 'lexicon'", PURPLE, fs=6.6)
    arrow(ax, (38, 31), (26, 26.4), "yes", lo=(-3, 1.5), color=NAVY)
    arrow(ax, (62, 31), (74, 26.4), "no", lo=(3, 1.5), color=NAVY)
    box(ax, 50, 8.5, 80, 8.6, "daily = mean score per calendar date  ->  aligned to the trading dates (no headline = NaN)\n-> forward fill -> fillna(0) -> clip to [-1, 1]  ->  one column appended to OHLCV for the sentiment tier\n(synthetic headlines cover only the last 90 dates, so earlier rows are 0)", TEAL, fs=6.7)
    arrow(ax, (22, 17.6), (36, 13.0), color=NAVY)
    arrow(ax, (78, 17.6), (64, 13.0), color=NAVY)
    save(fig, OUT / "11_flowchart_sentiment.png")


# ------------------------------------------------------------- 12 model
def model():
    fig, ax = canvas(10, 7.6, 100, 76)

    def stack(cx, title, rows, c):
        ax.text(cx, 72.5, title, ha="center", fontsize=8.2, fontweight="bold", color=c)
        y = 66
        for k, (t, col) in enumerate(rows):
            box(ax, cx, y, 25, 5.4, t, col, fs=6.5)
            if k < len(rows) - 1:
                arrow(ax, (cx, y - 2.7), (cx, y - 5.1), color=NAVY, lw=1.1)
            y -= 7.4
    inp = ("Input 20 x 5  (20 x 6 with sentiment)\nOpen High Low Close Volume [+ sentiment]", GREY)
    stack(15, "LSTM tier (baseline)", [inp, ("LSTM(64)", BLUE), ("BatchNormalization", BLUE), ("Dropout(0.2)", BLUE), ("Dense(1)  -> next Close (scaled)", NAVY)], BLUE)
    stack(46, "LSTM + attention tier (also +sentiment)", [inp, ("LSTM(64, return_sequences)", BLUE), ("MultiHeadAttention\n4 heads, key_dim 16, self (x, x)", PURPLE),
                                                      ("Add (residual)  +  LayerNormalization", PURPLE), ("GlobalAveragePooling1D", PURPLE), ("Dense(32, relu)  +  Dropout(0.2)", BLUE), ("Dense(1)", NAVY)], PURPLE)
    # federated
    panel(ax, 63, 8, 36, 60, "FedAvg stage (simulated, one process)", fc=PALE_ORANGE, ec=ORANGE, fs=8.0, tc=ORANGE)
    for i, t in enumerate(("TSLA", "AAPL", "AMZN", "...", "ORCL")):
        box(ax, 70 + i * 6.3, 58, 5.6, 4.6, t, ORANGE if t != "..." else GREY, fs=6.0)
    ax.text(81, 53, "10 clients = 10 tickers (attention + sentiment net)", ha="center", fontsize=6.3, color=INK)
    box(ax, 81, 45, 30, 6.4, "each round: copy the global weights,\ntrain 3 local epochs (batch 32) per client", PURPLE, fs=6.4)
    box(ax, 81, 34, 30, 6.4, "fedavg: sum(w_i x n_i / n),\nn_i = training windows of client i", NAVY, fs=6.5)
    box(ax, 81, 23, 30, 6.4, "2 rounds  ->  global model\n(mean local loss 0.040, 0.030 for TSLA's record)", NAVY, fs=6.3)
    box(ax, 81, 12.6, 30, 5.2, "scored on each ticker's own test split;\nsaved as <T>_hybrid.keras", TEAL, fs=6.3)
    for y1, y2 in ((55.5, 48.4), (41.8, 37.2), (30.8, 26.2), (19.8, 15.3)):
        arrow(ax, (81, y1), (81, y2), color=NAVY, lw=1.1)
    arrow(ax, (59.6, 46), (65.6, 46), "", color=PURPLE, lw=1.3)
    ax.text(62.2, 49.6, "same net\n(+sent.)", ha="center", fontsize=5.8, color=PURPLE)
    ax.text(50, 2.4, "Every tier: Adam lr 1e-3, MSE, batch 32, up to 50 epochs, EarlyStopping (patience 7, restore best), validation_split 0.15; Min-Max [0,1], scalers fitted on the first 80 % of rows.",
            ha="center", fontsize=6.3, color=GREY, style="italic")
    save(fig, OUT / "12_model_architecture.png")
