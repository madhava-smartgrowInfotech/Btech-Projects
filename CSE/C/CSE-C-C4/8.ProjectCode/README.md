# QuantPulse — AI-Powered Short-Term Stock Trend Forecasting

QuantPulse is a production-style forecasting platform for retail and professional traders.
It ingests historical OHLCV price data plus financial-news sentiment for a configurable
10-ticker technology universe and produces **5-day** short-term closing-price forecasts
with confidence bands, **30-day** longer-horizon forecasts, per-ticker directional
trend indicators (up/down), a sentiment overlay, and a model-comparison dashboard
pitting the hybrid deep model against classical baselines.

Live product: FastAPI backend (`backend/`, port 8404) + a React website (`frontend/`, port 5404) built on the
"Soft Pastel Calm" kit: landing page, dashboard, forecast, model comparison, news sentiment and method screens.

## Ticker universe (default)

| # | Ticker | Company |
|---|--------|---------|
| 1 | TSLA | Tesla |
| 2 | AAPL | Apple |
| 3 | AMZN | Amazon |
| 4 | MSFT | Microsoft |
| 5 | GOOGL | Google (Alphabet) |
| 6 | NVDA | Nvidia |
| 7 | META | Meta Platforms |
| 8 | FDX | FedEx |
| 9 | IBM | IBM |
| 10 | ORCL | Oracle |

Override with the `QP_TICKERS` env var (comma-separated), e.g.
`QP_TICKERS=TSLA,AAPL,MSFT`.

**Engineering assumptions (explicit):** "Google" → GOOGL; "Meta/or Airbnb" → META;
"Oracle" → ORCL. Prophet is a real dependency (Windows wheel); FinBERT-tone runs on
the PyTorch CPU backend (`framework="pt"`); NewsAPI is optional — without a key the
pipeline uses clearly-labeled synthetic headlines with the same schema and the FinBERT
scorer still runs on them.

## Architecture

1. **Baselines** (`backend/app/baselines.py`): ARIMA(5,1,0), SARIMAX, Prophet,
   Random Forest (lag-20), SVR — 80/20 chronological split.
2. **Core LSTM** (`models_dl.py`): 1× LSTM(64) + BatchNorm + Dropout(0.2) + Dense(1),
   20-day window, Min-Max [0,1], batch 32, ≤50 epochs + early stopping.
3. **Attention tier**: LSTM(64, return-sequences) + MultiHeadAttention(4 heads) +
   residual + LayerNorm + GlobalAveragePooling + Dense(32) + Dense(1).
4. **Sentiment tier**: NewsAPI headlines (cached, `NEWSAPI_KEY`) scored by FinBERT-tone
   (`yiyanghkust/finbert-tone`, inference only), aligned to trading dates and
   concatenated as an extra input channel. Synthetic-headline fallback with identical
   schema when no key is present.
5. **Federated simulation** (`federated.py`): per-ticker clients train locally, weights
   aggregated in-process with manual FedAvg (2 rounds × 3 local epochs).
6. **Ablation** (`backend/train.py`): MAE / MSE / RMSE / R² / directional accuracy for
   LSTM → LSTM+Attention → +Sentiment → Full Hybrid (FedAvg), plus Tesla loss curves
   and predicted-vs-actual plots in `artifacts/plots/`.

## Quick start

- Zero-knowledge path: double-click **`run.bat`** → opens http://localhost:5404.
- Docker path: `docker compose up --build` (see `run-docker.bat`).
- Full guide with prerequisites, manual commands and troubleshooting: **`HOW_TO_RUN.md`**.

## API (all on http://localhost:8404)

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | readiness, ticker list, news source |
| `GET /api/tickers` | universe + last close + trend |
| `GET /api/metrics` / `/api/metrics/{ticker}` | baselines + deep tiers + sentiment meta |
| `GET /api/forecast/{ticker}?horizon=short\|long` | 5-/30-day forecast + bands |
| `GET /api/sentiment/{ticker}` | daily sentiment + headlines |
| `GET /api/history/{ticker}?days=120` | OHLCV + forecast overlay |

Invalid tickers → `400` with a clear message; unknown tickers → `404`;
missing artifacts → `503` telling you to run `python -m backend.train`.

## Results

See `artifacts/metrics.json` (full per-ticker tables), `QuantPulse_Product_Overview.pdf`,
and `screenshots/`. Headline numbers are summarized in the product overview document.

## Repo layout

```
QuantPulse/
  backend/app/        FastAPI + pipeline modules (config, data_loader, sentiment,
                      baselines, models_dl, federated, forecast, main)
  backend/train.py    end-to-end training + ablation + artifact generation
  backend/requirements.txt
  backend/Dockerfile
  frontend/           React + Vite SPA (kit V4, Recharts, Framer Motion); docs/FRONTEND_PLAN.md
  data/               bundled OHLCV CSVs (from live Yahoo Finance pull)
  artifacts/          metrics.json, forecasts.json, serving/*.keras, plots/
  screenshots/        real dashboard captures
  run.bat / run-docker.bat / docker-compose.yml
  HOW_TO_RUN.md / QuantPulse_Product_Overview.pdf / .env.example
```

## Disclaimer

QuantPulse is a research/education tool. Forecasts are statistical estimates, not
financial advice.
