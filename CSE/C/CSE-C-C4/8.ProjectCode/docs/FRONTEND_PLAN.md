# Frontend plan - QuantPulse (CSE-C-C4)

Kit **V4 - Soft Pastel Calm** (JavaScript `.jsx`), backend port **8404**, frontend port **5404**.

The project root is `8.ProjectCode/` itself (the code is not inside a `QuantPulse/` sub-folder):
`backend/` (FastAPI + training pipeline), `frontend/` (React, Vite), `data/`, `artifacts/`, `run.bat`.
The existing UI is already a React + Tailwind single page (`frontend/src/App.jsx`, one screen with three
tabs). It is replaced by the kit-based, multi-screen app. The backend logic is not touched.

## 1. Backend endpoints (all JSON, `backend/app/main.py`)

| # | Method + path | Request | Response | Errors |
|---|---------------|---------|----------|--------|
| 1 | `GET /api/health` | - | `{status, product, tickers[], trained, news_source}` | - |
| 2 | `GET /api/tickers` | - | `{tickers:[{ticker, last_close, trend, mode}]}` | - |
| 3 | `GET /api/metrics` | - | `{<TICKER>: {mode, n_rows, baselines, sentiment, deep, histories, forecast_short, forecast_long, last_close, trend, headlines, federated_rounds}}` | 503 not trained |
| 4 | `GET /api/metrics/{ticker}` | path ticker (1-6 letters) | `{ticker, ...same per-ticker object}` | 400 bad ticker, 404 unknown |
| 5 | `GET /api/forecast/{ticker}?horizon=short\|long` | `horizon` default `short` | `{ticker, horizon, last_close, trend, forecast:[{day, predicted_close, lower, upper}]}` (5 or 30 rows) | 400, 404, 422 bad horizon |
| 6 | `GET /api/sentiment/{ticker}` | path ticker | `{ticker, meta:{source, scorer, n_headlines, note}, daily:[{date, score}] (last 30), headlines:[{headline, sentiment_score}]}` | 400 |
| 7 | `GET /api/history/{ticker}?days=120` | `days` 20-500 | `{ticker, mode, history:[{date, open, high, low, close, volume}], forecast_overlay:[{date, predicted_close, lower, upper}]}` | 400, 422 |
| - | `GET /` and `/assets/*` | - | serves `frontend/dist` when built | - |

Nested metric shapes: `baselines.<arima|sarimax|prophet|random_forest|svr>.metrics = {mae, mse, rmse, r2, directional_accuracy, n_test}`;
`deep.<lstm|lstm_attention|lstm_attention_sentiment|hybrid_federated> = {mae, mse, rmse, r2, directional_accuracy, n_test}`;
`histories.<tier> = {loss[], val_loss[]}`; `federated_rounds = [{round, mean_local_loss}]`.

Observations: `/api/sentiment` is slow on the first call (FinBERT-tone loads, and downloads on a cold cache), so the UI
needs a patient loading state. No auth exists in the backend. No endpoint is missing for the existing screens.
`artifacts/plots/TSLA_*.png` (loss curves, predicted vs actual) exist on disk but have no HTTP route.

## 2. Existing features / screens (README, HOW_TO_RUN, current `App.jsx`)

| ID | Feature | Where today |
|----|---------|-------------|
| F1 | Ticker selector for the 10-ticker universe (TSLA, AAPL, AMZN, MSFT, GOOGL, NVDA, META, FDX, IBM, ORCL) | header tab buttons |
| F2 | Last close + trend (up/down) + data mode (`live`/`csv`/`synthetic`) per ticker | top-left card |
| F3 | 5-day forecast table with lower/upper confidence band | top-middle card |
| F4 | Price history (120 days) + forecast overlay with 95% confidence band, actual vs forecast | "Forecast charts" tab |
| F5 | 5-day / 30-day horizon switch (30-day forecast chart) | horizon buttons |
| F6 | Ablation of the deep tiers (LSTM, +Attention, +Sentiment, Hybrid FedAvg): MAE/MSE/R2/directional accuracy table + MAE/RMSE chart | "Model comparison" tab |
| F7 | Classical baselines (ARIMA, SARIMAX, Prophet, RF, SVR) metrics table | "Model comparison" tab |
| F8 | Hybrid vs baselines MAE comparison chart | "Model comparison" tab |
| F9 | Daily sentiment overlay (last 30 trading days) | "Sentiment panel" tab |
| F10 | Recent headlines with tone label + score; sentiment source/scorer/count (synthetic-fallback vs NewsAPI) | sentiment card + panel |
| F11 | All-model metrics grid for the selected ticker | bottom card |
| F12 | Backend/readiness awareness (unreachable error, `trained` flag, news source) | error banner |
| F13 | Research/education disclaimer ("not financial advice") | footer |
| F14 | Federated learning rounds and loss curves (in the API, not yet shown) | - |

## 3. Screen map (built)

Landing page `/` (Soft Pastel Calm hero, live forecast preview, stats strip, ticker marquee, features, CTA) and the app at `/app`:

| Route | Screen | Features | Endpoints |
|-------|--------|----------|-----------|
| `/` | Landing | pitch, live preview, live numbers | 2, 3, 7 |
| `/app` | Dashboard | F1 F2 F12 F13 - ticker cards, KPIs, sortable/searchable table | 2, 3 (+1 via the shell status pill) |
| `/app/forecast?t=&h=` | Forecast | F1 F2 F3 F4 F5 - ticker, horizon, history range, chart with band, forecast table with actuals | 2, 5, 7 |
| `/app/models?t=&tab=` | Model comparison | F6 F7 F8 F11 F14 - ablation chart/table, baselines, all-model MAE, loss curves, FedAvg rounds | 2, 4 |
| `/app/sentiment?t=` | News sentiment | F9 F10 - daily score chart, headline list with search and tone filter | 2, 6 |
| `/app/about` | Method and data | pipeline, installation facts, per-ticker data table, disclaimer (F13) | 1, 3 |

Shared: AppShell (sidebar, topbar with persisted theme toggle and API status pill, mobile drawer and bottom bar),
toasts on refresh, skeleton / empty / error states on every screen.

## 4. Kit adaptation notes

The V4 kit is product-coupled to another project (HubOptima). Adapted in the project copy only:
`lib/api` (new), `lib/palette` (new), `lib/hooks` (new), `lib/market` (new), `components/reactbits/Blobs` (new),
`Layout.jsx` nav, brand, status pill and sidebar note (rewritten), `Feedback.jsx` error hints, `theme.jsx` (storage key,
saved theme read on load), `format.js` (USD), `charts/index.jsx` (added `ForecastChart` with a confidence band).
The original kit folder was not edited. Nothing is imported from outside this folder.

## 5. Backend changes (additive only)

`backend/app/main.py`: CORS origins for ports 5404/8404, and a single-page-app fallback route so `/app/forecast` can be
reloaded when the API serves `frontend/dist`. No endpoint, contract or model logic changed.

## 6. Data caveat found while wiring

`/api/history` serves live Yahoo prices (to the latest close) while the trained models forecast from the close they were
trained on (e.g. 8 Sep 2026). The Forecast screen anchors the forecast on that cut-off date, draws the actual closes since
then, and shows them next to each forecast day, with a note to retrain.

## 7. Feature checklist (verified in the browser against the real API)

- [x] F1 ticker selector  - [x] F2 last close, trend, mode  - [x] F3 5-day table with band  - [x] F4 history chart with band
- [x] F5 5-day / 30-day switch  - [x] F6 deep-tier ablation  - [x] F7 baselines  - [x] F8 hybrid vs baselines MAE chart
- [x] F9 daily sentiment  - [x] F10 headlines and tone, source/scorer  - [x] F11 all-model metrics  - [x] F12 offline / not-trained handling
- [x] F13 disclaimer  - [x] F14 federated rounds and loss curves