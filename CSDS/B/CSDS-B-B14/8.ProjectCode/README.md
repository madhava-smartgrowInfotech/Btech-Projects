# AquaVision

**Water-utility intelligence without heavy IoT.** AquaVision predicts water quality and demand, and detects leaks, distribution imbalances and abnormal consumption on a digital twin of the city distribution network.

## Features

- **Water-quality prediction:** a stacking ensemble (Random Forest, XGBoost, Gradient Boosting, Decision Tree) with exact SHAP reasons and guideline-limit checks.
- **Network digital twin:** WNTR / EPANET model of 5 zones, 85 pipes, a pump and a tank, shown on a Leaflet map.
- **7-day demand forecast** per zone from consumption history and live Open-Meteo weather.
- **Leak detection:** inject a leak into the twin. A detector flags it from 16 pressure loggers and 5 zone meters and ranks the likely pipes.
- **Distribution imbalance:** supply vs demand per zone, an equity score, and a rebalancing plan verified by simulation, plus free what-if runs.
- **Abnormal consumption:** IsolationForest over 150 customer meters finds bursts, night flow and suspected theft.
- **Operations dashboard:** NRW, pressure, quality, equity, the map, charts and alerts.
- **Evaluation** of every model (below).

## Quick start (Windows)

```
setup.bat      # once: venv + packages + .env + npm install
run.bat        # starts API :8214 and web app :5214, opens the browser
```

Requires Python 3.11+ and Node.js LTS. No API keys are needed. Full steps are in [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md).

## Demo login

| Role | Email | Password |
|---|---|---|
| Engineer (can inject leaks) | engineer@aquavision.local | engineer123 |
| Manager | manager@aquavision.local | manager123 |

## Evaluation results

From `ml/eval.py`, saved in `experiments/eval/metrics.json`:

| Objective | Metric | Result |
|---|---|---|
| Water quality (656 held-out samples) | Accuracy / F1 / ROC-AUC, stacking ensemble | **0.671 / 0.443 / 0.661** |
| | Members, accuracy: RF / XGBoost / GBM / DT | 0.674 / 0.643 / 0.654 / 0.634 |
| Demand forecast (last 90 days, 12 weekly origins) | 7-day recursive MAPE, XGBoost | **2.33%** (seasonal naive: 6.37%) |
| Leak detection (300 new twin scenarios, 2-20 L/s) | Precision / recall / F1 / ROC-AUC | **1.00 / 0.98 / 0.99 / 0.9998** |
| Leak localisation (82 candidate pipes) | Top-1 / top-3 pipe accuracy / correct zone | **0.47 / 0.76 / 1.00** |
| Abnormal consumption (6,750 meter-days) | Day-level precision / recall | 0.72 / 0.94 |
| | Meter-level precision / recall (last 7 days) | **0.92 / 1.00** |
| Distribution imbalance | Equity score before -> after the recommended plan | 87.2 -> 98.9 (NRW 9.26% -> 10.93%) |

About these numbers:
- The water-potability dataset is known to be hard to separate. Around 0.65-0.70 accuracy is typical for it.
- Leak, demand and meter results come from simulated or sample data (see docs/02).
- Top-3 localisation with 16 loggers is the realistic target: adjacent pipes between unmonitored junctions produce nearly identical signatures.

## Project layout

```
backend/app/     FastAPI app: main.py, db.py, auth.py, routes/, services/ (twin, quality, demand, leaks, imbalance, anomaly)
frontend/src/    React + Vite + Tailwind: pages/, components/, api.js
ml/              training scripts and eval.py
scripts/         data generators, weather/dataset download, smoke_test.py
data/            water_potability.csv, weather cache, network, sample data
models/          trained models          experiments/   metrics
docs/            documentation
```

## Documentation

- [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md): problem, users, features, screens
- [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md): architecture, data sources and licences, models
- [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md): setup, run, demo walkthrough, rebuild, troubleshooting
- [docs/PLAN.md](docs/PLAN.md): build plan (endpoints, tables, screens)
