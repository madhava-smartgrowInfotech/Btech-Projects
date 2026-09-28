# AquaVision - Build Plan

**Architecture:** React + Vite (5214) -> `/api` proxy -> FastAPI (8214) -> services (WNTR digital twin, ML models) -> SQLite (`data/app.db`).
Offline pipeline: `scripts/` generates the network, sample consumption/meter data and leak scenarios (seeded); `ml/` trains the models into `models/` and writes metrics to `experiments/`.

**Data:** Kaggle Water Potability (CC0, committed) - Open-Meteo daily history for Hyderabad (cached CSV) - WNTR-simulated city network (5 zones), zone consumption history, 150 customer meters (hourly), leak scenarios.

**Models:**
- Quality: stacking (RF, XGBoost, GBM, Decision Tree -> logistic meta), exact SHAP over the full ensemble, WHO-limit checks.
- Demand: XGBoost regressor (lags, calendar, temperature, rain), 7-day recursive forecast with the Open-Meteo forecast.
- Leaks: RandomForest detector on pressure/flow residuals (twin baseline vs observed) + sensitivity-signature correlation to rank pipes.
- Imbalance: pressure-driven twin simulation -> delivered/required per zone, equity score, what-if rebalancing.
- Anomalies: IsolationForest on per-meter daily features, labelled burst / night flow / suspected theft.

**Tables:** users, quality_checks, leak_events, alerts.

**Endpoints:** `POST /api/auth/login`, `GET /api/auth/me`, `GET /api/dashboard`, `POST /api/quality/predict`,
`GET /api/quality/samples|history|limits`, `GET /api/network`, `GET /api/forecast/zones`, `GET /api/forecast?zone=`,
`POST /api/leaks/inject`, `GET /api/leaks/events`, `POST /api/leaks/clear`, `GET /api/imbalance`, `POST /api/imbalance/whatif`,
`GET /api/anomalies`, `GET /api/anomalies/meter/{id}`, `GET /api/alerts`, `GET /api/metrics`, `GET /api/health`.

**Screens:** Landing, Login, Operations dashboard, Water-quality check, Network map, Demand forecast, Leaks & anomalies.

**Roles:** engineer (all, including leak injection and what-if), manager (all views, what-if).
