"""QuantPulse design diagrams 01-06 (matplotlib, 150 dpi) -> docs/diagrams/.  Diagrams 07-12 live in diagrams_more.py.

    python -m scripts.docs.make_diagrams            # from 8.ProjectCode; writes all twelve
Every diagram mirrors the code: backend/app/{config,data_loader,sentiment,baselines,models_dl,federated,forecast,main}.py,
backend/train.py and frontend/src/{lib,pages}.
"""
from __future__ import annotations

from pathlib import Path

from .dgm_lib import *  # noqa: F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ 01 architecture
def architecture():
    fig, ax = canvas(9.6, 7.4, 100, 77)
    ax.text(36, 75.2, "QuantPulse: four tiers, no database, no authentication, no MIL component", ha="center", fontsize=8.2, color=ORANGE, fontweight="bold")
    # browser
    panel(ax, 1, 60, 70, 13.5, "TIER 1 - BROWSER (React 19 + Vite, port 5404)", fc=PALE_BLUE, fs=8.8)
    box(ax, 19, 65.3, 31, 6.4, "Six screens (lazy chunks)\nLanding · Dashboard · Forecast\nModels · Sentiment · About", BLUE, fs=7.4)
    box(ax, 53, 65.3, 31, 6.4, "src/lib/api.js client\nfetch /api/... (30 s; 240 s for\nsentiment), Vite proxy in dev", BLUE, fs=7.4)
    # fastapi
    panel(ax, 1, 40, 70, 18, "TIER 2 - FastAPI application (backend/app/main.py, port 8404)", fc=PALE_PURPLE, fs=8.8)
    box(ax, 19, 47, 31, 10.0, "7 JSON endpoints\n/api/health  /api/tickers\n/api/metrics[/{t}]  /api/forecast/{t}\n/api/sentiment/{t}  /api/history/{t}", PURPLE, fs=7.0)
    box(ax, 53, 47, 31, 10.0, "Serves the built SPA (frontend/dist)\nwith index.html fallback;\nCORS limited to localhost origins;\nerrors 400 / 404 / 422 / 503", PURPLE, fs=7.0)
    # modules
    panel(ax, 1, 17, 70, 21, "TIER 3 - pipeline modules (backend/app, imported by main.py and train.py)", fc=PALE_TEAL, fs=8.8)
    mods = [(10.5, 31.8, "config.py\ntickers, window 20,\nsplit 0.8, 64 units"), (28, 31.8, "data_loader.py\nyfinance -> CSV ->\nsynthetic (mode)"),
            (45.5, 31.8, "sentiment.py\nNewsAPI / synthetic,\nFinBERT-tone, daily"), (63, 31.8, "baselines.py\nARIMA SARIMAX Prophet\nRF SVR")]
    for x, y, t in mods:
        box(ax, x, y, 16, 7.4, t, TEAL, fs=6.6)
    mods2 = [(10.5, 22.2, "models_dl.py\nwindows, scalers, LSTM,\nattention LSTM, metrics"), (28, 22.2, "federated.py\nmanual FedAvg,\n10 clients"),
             (45.5, 22.2, "forecast.py\nrecursive 5 / 30-day\nforecast + band"), (63, 22.2, "backend/train.py\noffline pipeline,\nwrites artifacts")]
    for x, y, t in mods2:
        box(ax, x, y, 16, 7.4, t, TEAL if "train" not in t else NAVY, fs=6.6)
    # files
    panel(ax, 1, 1, 70, 14, "TIER 4 - files (JSON / CSV / Keras)", fc=LIGHT, fs=8.8)
    box(ax, 13.5, 6.6, 22, 7.0, "artifacts/\nmetrics.json, forecasts.json,\nserving/*.keras + *.npz, plots/", GREY, fs=6.5)
    box(ax, 36, 6.6, 20, 7.0, "data/<T>.csv\n(10 price files,\nrewritten on live pull)", GREY, fs=6.5)
    box(ax, 57.5, 6.6, 19, 7.0, "data/news_cache/\n<T>_<day>.json\n(NewsAPI only)", GREY, fs=6.5)
    # external
    box(ax, 86.5, 65, 24, 14, "", WHITE, ec=ORANGE, lw=1.4, ls="--", tc=INK)
    ax.text(86.5, 69.5, "Not part of QuantPulse", ha="center", fontsize=7.4, fontweight="bold", color=ORANGE)
    ax.text(86.5, 64.5, "database\nlogin / authentication\nMIL (multiple-instance)\nsocial-media source", ha="center", va="center", fontsize=6.8, color=INK, linespacing=1.3)
    panel(ax, 74, 17, 25, 36, "EXTERNAL SERVICES", fc=PALE_ORANGE, ec=ORANGE, fs=8.8, tc=ORANGE)
    box(ax, 86.5, 43, 21, 8, "Yahoo Finance (data_loader.py)\nyfinance, daily OHLCV,\n2-year pull", ORANGE, fs=6.8)
    box(ax, 86.5, 32.5, 21, 8, "NewsAPI.org (sentiment.py)\noptional key; ~30 days\nof headlines", ORANGE, fs=6.8)
    box(ax, 86.5, 22, 21, 8, "Hugging Face hub (sentiment.py)\nyiyanghkust/finbert-tone\nweights, PyTorch CPU", ORANGE, fs=6.8)
    # arrows
    arrow(ax, (36, 60), (36, 58.2), "HTTP + JSON", color=NAVY, lw=1.7, lo=(9, 0), fs=7)
    arrow(ax, (36, 40), (36, 38.2), "import", color=NAVY, lw=1.7, lo=(6, 0), fs=7)
    arrow(ax, (36, 17), (36, 15.2), "read / write", color=NAVY, lw=1.7, lo=(8, 0), fs=7)
    arrow(ax, (71, 35), (75.8, 43), "", color=ORANGE, lw=1.5)
    arrow(ax, (71, 31), (75.8, 32.5), "", color=ORANGE, lw=1.5)
    arrow(ax, (71, 26), (75.8, 22), "", color=ORANGE, lw=1.5)
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------- 02 high-level workflow
def workflow():
    fig, ax = canvas(9.8, 6.8, 100, 69.4)
    ax.text(50, 67.4, "Offline training pipeline (python -m backend.train) feeds the online website through JSON files", ha="center", fontsize=8.2, color=NAVY, fontweight="bold")
    panel(ax, 1, 38, 98, 27, "STAGE 1 - per ticker (10 tickers in turn, train_ticker)", fc=PALE_BLUE, fs=8.8)
    xs = [9.6, 25.8, 42.0, 58.2, 74.4, 90.6]
    cols = [BLUE, BLUE, PURPLE, NAVY, NAVY, NAVY]
    items = [("1 LOAD", "yfinance 2y daily\nor bundled CSV\nor synthetic (mode)"), ("2 BASELINES", "ARIMA SARIMAX\nProphet RF SVR\n80/20 split"),
             ("3 SENTIMENT", "headlines -> FinBERT\n-> daily score\n(aligned, ffill / 0)"), ("4 TIER LSTM", "LSTM(64)+BN+\nDropout+Dense\nwindow 20, [0,1]"),
             ("5 TIER ATTN", "LSTM + 4-head\nattention + resid +\nLayerNorm + GAP"), ("6 TIER SENT", "same network, one\nextra sentiment\ninput channel")]
    for x, (t, b), c in zip(xs, items, cols):
        box(ax, x, 51.5, 15.0, 17, f"{t}\n\n{b}", c, fs=6.5)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.5, 51.5), (b - 7.5, 51.5), color=NAVY, lw=1.6)
    ax.text(50, 41.2, "outputs per ticker: baseline metrics, three tier metrics + loss histories, 5- and 30-day recursive forecasts from the tier-3 model", ha="center", fontsize=6.7, color=GREY, style="italic")
    panel(ax, 1, 14.5, 98, 21, "STAGE 2 - after all tickers, then serving", fc=PALE_TEAL, fs=8.8)
    xs2 = [11, 30, 50, 70, 89]
    it2 = [("7 FEDAVG", "10 clients x 2 rounds\nx 3 local epochs;\nweighted average", PURPLE), ("8 EVALUATE", "global model scored\non each ticker; 5-day\nforecast re-made", NAVY),
           ("9 ARTIFACTS", "metrics.json,\nforecasts.json,\nserving/*.keras, plots", GREY), ("10 API :8404", "FastAPI reads the\nJSON; history and\nsentiment are live", TEAL),
           ("11 SCREENS :5404", "Dashboard, Forecast,\nModels, Sentiment,\nAbout", BLUE)]
    for x, (t, b, c) in zip(xs2, it2):
        box(ax, x, 24.5, 16.5, 14, f"{t}\n\n{b}", c, fs=6.5)
    for a, b in zip(xs2[:-1], xs2[1:]):
        arrow(ax, (a + 8.4, 24.5), (b - 8.4, 24.5), color=NAVY, lw=1.6)
    arrow(ax, (50, 38), (50, 35.7), color=NAVY, lw=1.6)
    ax.text(50, 16.4, "no database, no login, no MIL stage: news enters only as one daily sentiment number", ha="center", fontsize=6.7, color=ORANGE, fontweight="bold")
    panel(ax, 1, 0.5, 98, 11.5, "Runtime facts", fc=LIGHT, fs=8.0)
    ax.text(3, 5.0, "Serving models (*.keras) are written but the API reads only the JSON artifacts.  Dashboard / Models / Sentiment values come from metrics.json;\n"
            "Forecast and Landing also call /api/history, which re-downloads prices from Yahoo Finance on every request.", fontsize=6.7, color=INK, va="center")
    save(fig, OUT / "02_high_level_workflow.png")


# --------------------------------------------------------------------- 03 DFD 0
def dfd0():
    fig, ax = canvas(9.4, 6.4, 100, 68)
    circle(ax, 50, 34, 13, "0\nQuantPulse\nforecasting\nplatform", BLUE, fs=9.5)
    ext = [(14, 55, "Trader / analyst\n(browser user)", ORANGE), (14, 13, "Evaluator /\ndeveloper", GREY), (86, 58, "Yahoo Finance\n(yfinance)", GREY), (86, 34, "NewsAPI.org\n(optional)", GREY), (86, 10, "Hugging Face hub\n(FinBERT-tone)", GREY)]
    for x, y, t, c in ext:
        box(ax, x, y, 21, 9, t, c, fs=8.2, bold=True)
    A = dict(color=NAVY, fs=7.2)
    arrow(ax, (24.5, 57), (39.3, 40), "ticker, horizon,\nhistory length", lo=(-4, 4.5), **A)
    arrow(ax, (38.5, 30), (24.5, 52.5), "last close, trend, 5/30-day forecast\n+ band, model metrics, sentiment,\nprice history + overlay", lo=(-11, -3), **A)
    arrow(ax, (24.5, 15), (38.2, 28.5), "python -m backend.train,\ntests, .env settings", lo=(-5, -3.5), **A)
    arrow(ax, (39.5, 26), (24.5, 11), "metrics.json, plots,\ntest logs, screenshots", lo=(2, -4.5), **A)
    arrow(ax, (75.5, 58), (60, 42), "daily OHLCV\n(2 y, 10 tickers)", lo=(5, 4), **A)
    arrow(ax, (60, 38), (75.5, 55), "ticker symbol,\nperiod, interval", lo=(7, -4), **A)
    arrow(ax, (75.5, 35), (63, 34), "headlines\n(NEWSAPI_KEY)", lo=(0, 3.4), **A)
    arrow(ax, (63, 31.5), (75.5, 32.5), "query,\ndate range", lo=(0, -3.6), **A)
    arrow(ax, (75.5, 12), (60, 27), "model weights,\ntokenizer", lo=(7, 0), **A)
    ax.text(50, 3.0, "Level 0 context. The system boundary has no database, no login and no MIL component.", ha="center", fontsize=7.6, color=ORANGE, fontweight="bold")
    save(fig, OUT / "03_dfd_level0.png")


# ---------------------------------------------------------------------- 04 DFD 1
def dfd1():
    fig, ax = canvas(10, 7.4, 100, 74)
    pr = lambda cx, cy, n, t, c=TEAL: circle(ax, cx, cy, 6.6, f"{n}\n{t}", c, fs=6.4)
    ext = lambda cx, cy, t, w=15: box(ax, cx, cy, w, 6.4, t, GREY, fs=6.8, bold=True)
    st = lambda cx, cy, t, w: store(ax, cx, cy, w, 6.0, t, fs=6.4)
    ext(9, 62, "Yahoo Finance")
    ext(9, 36, "NewsAPI /\nHugging Face")
    pr(31, 62, "1.0", "Acquire\nprices", BLUE)
    pr(53, 62, "3.0", "Fit classical\nbaselines")
    pr(75, 62, "6.0", "Forecast &\nwrite artefacts", TEAL)
    pr(31, 36, "2.0", "Score news\nsentiment", PURPLE)
    pr(53, 36, "4.0", "Train deep\ntiers", NAVY)
    pr(75, 36, "5.0", "Federated\naveraging", PURPLE)
    st(31, 49, "D1 data/<T>.csv", 17)
    st(31, 20, "D2 news_cache/*.json", 20)
    st(90, 49, "D3 artifacts/", 16)
    pr(90, 26, "7.0", "Serve API\n& website", BLUE)
    ext(90, 6, "Trader / analyst", 17)
    ext(66, 10, "Yahoo Finance (live)", 19)
    A = dict(color=NAVY, fs=6.2)
    arrow(ax, (16.5, 62), (24.4, 62), "OHLCV", lo=(0, 2.2), **A)
    arrow(ax, (31, 55.4), (31, 52.2), "", **A)
    ax.text(32.2, 53.8, "write CSV", fontsize=6.2, color=INK)
    arrow(ax, (31, 45.8), (31, 42.7), "", **A)
    ax.text(32.2, 44.1, "trading dates", fontsize=6.2, color=INK)
    arrow(ax, (37.6, 62), (46.4, 62), "close series", lo=(0, 2.2), **A)
    arrow(ax, (36.5, 57.2), (48.5, 41.3), "OHLCV frame", lo=(7.2, 1.0), **A)
    arrow(ax, (16.5, 36), (24.4, 36), "headlines,\nweights", lo=(0, 3.4), **A)
    arrow(ax, (27, 30), (27, 23.2), "", **A)
    arrow(ax, (35, 23.2), (35, 30), "", **A)
    ax.text(36.2, 26.6, "cache", fontsize=6.2, color=INK)
    arrow(ax, (37.6, 36), (46.4, 36), "daily\nsentiment", lo=(0, 3.4), **A)
    arrow(ax, (59.6, 36), (68.4, 36), "tier models,\nclient data", lo=(0, 3.4), **A)
    arrow(ax, (59.6, 62), (68.4, 62), "baseline\nmetrics", lo=(0, 3.4), **A)
    arrow(ax, (57.5, 41.5), (70.6, 57.0), "tier metrics, histories,\nlast 20-day window", lo=(-9.5, 2.5), **A)
    arrow(ax, (75, 42.6), (75, 55.4), "global\nmodel", lo=(4.5, 0), **A)
    arrow(ax, (81.6, 62), (90, 52.2), "metrics.json,\nforecasts.json,\nmodels, plots", lo=(1.2, 5.0), **A)
    arrow(ax, (90, 45.8), (90, 32.6), "read JSON", lo=(5.2, 0), **A)
    arrow(ax, (87, 19.4), (87, 9.3), "ticker, horizon", lo=(-8.6, 0), **A)
    arrow(ax, (93.4, 9.3), (93.4, 19.4), "screens", lo=(4.2, 0), **A)
    arrow(ax, (66, 13.3), (84.4, 24), "price history\non every /api/history", lo=(-4, 4.5), color=GREY, fs=6.0, ls="--")
    ax.text(50, 1.8, "Level 1: seven processes, three data stores. Training (1.0-6.0) runs offline; only 7.0 talks to the browser. No database, no login.", ha="center", fontsize=6.9, color=GREY, style="italic")
    save(fig, OUT / "04_dfd_level1.png")


# ---------------------------------------------------------------- 05 DFD 2
def dfd2():
    fig, ax = canvas(10, 7.0, 100, 70)
    pr = lambda cx, cy, n, t, c=TEAL: circle(ax, cx, cy, 7.4, f"{n}\n{t}", c, fs=6.4)
    pr(14, 56, "4.1", "Build\nfeatures", BLUE)
    pr(40, 56, "4.2", "Scale\n[0,1]", BLUE)
    pr(66, 56, "4.3", "Window\n20 days", BLUE)
    pr(88, 40, "4.4", "Split 80/20,\nbuild model", NAVY)
    pr(66, 24, "4.5", "Train\n(early stop)", NAVY)
    pr(40, 24, "4.6", "Evaluate\n(inverse scale)", PURPLE)
    pr(14, 24, "4.7", "Keep model &\nhistory", TEAL)
    st = lambda cx, cy, t, w: store(ax, cx, cy, w, 6.0, t, fs=6.4)
    st(14, 40, "OHLCV frame + daily sentiment", 26)
    st(40, 9, "D3  artifacts (metrics.json, serving)", 36)
    A = dict(color=NAVY, fs=6.2)
    arrow(ax, (14, 43.2), (14, 48.6), "5 columns +\n1 optional", lo=(7, 0), **A)
    arrow(ax, (21.4, 56), (32.6, 56), "raw [n x 5|6]", lo=(0, 2.4), **A)
    arrow(ax, (47.4, 56), (58.6, 56), "scaled, clipped\n(fit rows 0..0.8n)", lo=(0, 3.6), **A)
    arrow(ax, (72, 51), (84, 44.5), "X [N,20,F],\ny = next Close", lo=(2.5, 4.4), **A)
    arrow(ax, (86, 33), (72, 28), "Xtr, ytr\n(first 80 %)", lo=(6.0, 0.5), **A)
    arrow(ax, (58.6, 24), (47.4, 24), "fitted model", lo=(0, 2.4), **A)
    arrow(ax, (84, 36), (47.5, 27.5), "Xte, yte (last 20 %)", lo=(-1, 4.4), **A)
    arrow(ax, (32.6, 24), (21.4, 24), "MAE MSE RMSE R2\ndirection", lo=(0, 3.6), **A)
    arrow(ax, (14, 16.6), (24, 10.7), "metrics, history,\nresidual std", lo=(-6.5, -1.5), **A)
    ax.text(3, 66, "4.0 Train deep tiers, expanded: runs three times per ticker\n(LSTM, LSTM + attention, + sentiment); only the third gets the sentiment column.", fontsize=6.8, color=GREY, style="italic", va="center")
    ax.text(70, 8, "Training: Adam 1e-3, MSE, batch 32, up to 50 epochs,\nEarlyStopping patience 7 (restore best), validation_split 0.15.\nSeeds: TensorFlow and NumPy 42.", fontsize=6.6, color=INK, va="center")
    save(fig, OUT / "05_dfd_level2.png")


# ---------------------------------------------------------------- 06 UML
def uml():
    fig, ax = canvas(11, 8.4, 100, 76.4)
    cls = lambda x, y, w, n, a, m, hdr=NAVY, st="module": uml_class(ax, x, y, w, n, a, m, hdr=hdr, fs=6.3, stereotype=st)
    cls(1, 75, 30, "train  (backend/train.py)", [], ["main()", "train_ticker(t, df, mode, fed_store)", "_save_loss_curve(history, path)", "_save_pred_plot(dates, y, yhat)"], hdr=ORANGE, st="entry point")
    cls(56, 75, 41, "main  (backend/app/main.py)", ["app: FastAPI   ART, FRONT_DIST", "_metrics_cache, _forecast_cache"],
        ["health()  tickers()  all_metrics()  ticker_metrics(t)", "forecast(t, horizon)  sentiment(t)  history(t, days)", "root()  spa(path)  _check_ticker(t)"], hdr=PURPLE, st="application")
    panel(ax, 0.5, 22.5, 97, 27.5, "backend/app modules (functions; no classes)", fc=PALE_TEAL, fs=7.6)
    cls(1.5, 46, 15.2, "data_loader", ["PERIOD, INTERVAL"], ["load_ticker(t)", "load_universe(list)", "_synthetic_series()"], hdr=BLUE)
    cls(18.2, 46, 17.2, "sentiment", ["_finbert (lazy)"], ["score_headlines(list)", "_fetch_newsapi(t)", "get_daily_sentiment()", "recent_headlines(t)"], hdr=PURPLE)
    cls(37, 46, 15.8, "baselines", [], ["run_arima  run_sarimax", "run_prophet  run_rf", "run_svr  run_all", "_metrics(y, yhat)"], hdr=TEAL)
    cls(54.3, 46, 20.5, "models_dl", [], ["make_windows  scale_split", "fit_scalers  apply_scalers", "prepare_features", "build_lstm", "build_attention_lstm", "train_model  evaluate_dl"], hdr=NAVY)
    cls(76.3, 46, 20.8, "federated  /  forecast", [], ["fedavg(weights, counts)", "run_federated(build_fn,", "  client_data, rounds,", "  local_epochs, shape)", "recursive_forecast(model,", "  window, steps, std, sc)"], hdr=NAVY)
    cls(1, 20, 33, "config", ["DEFAULT_TICKERS (10)  WINDOW = 20", "TRAIN_SPLIT = 0.8  BATCH_SIZE = 32", "EPOCHS = 50  LSTM_UNITS = 64  HEADS = 4"], ["get_tickers()   NEWS_API_KEY from env"], hdr=GREY)
    cls(38, 20, 28, "api  (frontend/src/lib/api.js)", ["request(path, {timeout, signal})"], ["health() tickers() metrics()", "tickerMetrics(t) forecast(t, h)", "history(t, days) sentiment(t)"], hdr=BLUE, st="object")
    cls(69, 20, 13, "ApiError", ["message", "status"], [], hdr=BLUE, st="class")
    cls(84, 20, 14, "useAsync", ["data, error,", "loading"], ["reload()"], hdr=BLUE, st="hook")
    A = dict(color=NAVY, lw=1.3, fs=6.2)
    arrow(ax, (16, 56.6), (16, 50.2), "imports every module", lo=(11, 0), **A)
    arrow(ax, (77, 60.0), (77, 50.2), "imports config, data_loader, sentiment;"+chr(10)+"reads artifacts/*.json", lo=(-14, -1), **A)
    ax.text(18.5, 21.0, "config is imported by every module", fontsize=6.2, color=GREY, va="center")
    ax.plot([66, 66, 99.0, 99.0], [20.6, 21.2, 21.2, 66], color=GREY, lw=1.4, ls="--", zorder=3)
    arrow(ax, (99.0, 66), (97.2, 66), "", color=GREY, lw=1.4)
    ax.text(74, 22.0, "HTTP GET /api/... (JSON)", fontsize=6.2, color=GREY, ha="center", bbox=dict(fc="white", ec="none", pad=0.6))
    ax.text(50, 1.2, "UML class diagram: QuantPulse is mostly modules of functions, drawn as <<module>> boxes. Solid arrows: imports. Dashed: HTTP from the React client.", ha="center", fontsize=6.7, color=GREY, style="italic")
    save(fig, OUT / "06_uml_class.png")


def main():
    for fn in (architecture, workflow, dfd0, dfd1, dfd2, uml):
        fn()
    from . import diagrams_more as dm

    for fn in (dm.sequence, dm.use_case, dm.er, dm.flow_core, dm.flow_sent, dm.model):
        fn()


if __name__ == "__main__":
    main()
