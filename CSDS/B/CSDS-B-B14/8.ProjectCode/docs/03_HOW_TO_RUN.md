# AquaVision - How to run

## Requirements

- Windows 10/11
- Python 3.11 or newer (https://www.python.org/downloads/). Tick "Add python.exe to PATH" during install.
- Node.js LTS (https://nodejs.org/)
- An internet connection for the first setup (packages), the map tiles and the live weather forecast

No API keys are required. Open-Meteo is free and keyless, and the dataset is already included.

## 1. Setup (once)

Double-click `setup.bat` in the `8.ProjectCode` folder, or run it from a terminal:

```
setup.bat
```

This creates `venv\`, installs the Python packages from `requirements.txt`, creates `.env` from `.env.example` (with a fresh JWT secret) and runs `npm install` in `frontend\`.

## 2. Start

```
run.bat
```

Two windows open: the backend on http://127.0.0.1:8214 (API docs at `/docs`) and the frontend on http://localhost:5214. The browser opens automatically. Close both windows to stop.

## 3. Sign in

| Role | Email | Password |
|---|---|---|
| Engineer | engineer@aquavision.local | engineer123 |
| Manager | manager@aquavision.local | manager123 |

## 4. Demo walkthrough

1. **Water quality:** click "Lab sample A (reservoir outlet)", then "Check potability". You get "Not potable, ~87%" with SHAP reasons and guideline-limit flags.
2. **Demand forecast:** select Zone 3. The chart shows the next 7 days with max temperature, and the peak day is marked. Weather is live from Open-Meteo.
3. **Leaks & anomalies -> Leak detection:** keep pipe P53 (or click any pipe on the map), choose 12 L/s, then "Inject leak". A leak alert is raised and the ranked suspects appear on the map (#1 in red). "Repair all" resets the twin.
4. **Leaks & anomalies -> Abnormal consumption:** a night-flow meter (for example M1099) is flagged; select it to see its readings.
5. **Network map -> Distribution imbalance:** Zone 3 is under-supplied. Click "Test plan on the twin" to simulate the suggested rebalancing.
6. **Operations:** KPIs, map, charts and the alert list.

## 5. Checks

With the backend running:

```
venv\Scripts\python scripts\smoke_test.py
cd frontend && npm run build
```

## 6. Rebuild data and models (optional)

Everything is committed, so this is only needed to regenerate:

```
venv\Scripts\python scripts\fetch_weather.py
venv\Scripts\python scripts\download_data.py
venv\Scripts\python scripts\generate_network.py
venv\Scripts\python scripts\generate_consumption.py
venv\Scripts\python scripts\generate_leak_scenarios.py
venv\Scripts\python ml\train_quality.py
venv\Scripts\python ml\train_demand.py
venv\Scripts\python ml\train_leak.py
venv\Scripts\python ml\train_anomaly.py
venv\Scripts\python ml\eval.py
```

Run the steps in this order. `download_data.py` needs `KAGGLE_USERNAME` / `KAGGLE_KEY` in `.env` only if anonymous download is refused.

## Configuration (`.env`)

| Key | Default | Meaning |
|---|---|---|
| BACKEND_PORT | 8214 | API port |
| FRONTEND_PORT | 5214 | Web app port |
| JWT_SECRET | (generated) | Signs login tokens |
| JWT_EXPIRE_MINUTES | 720 | Session length |
| DATABASE_URL | sqlite:///data/app.db | Database file, created on first run |
| CITY_NAME / CITY_LAT / CITY_LON | Hyderabad | Location for the weather |
| KAGGLE_USERNAME / KAGGLE_KEY | empty | Optional, for re-downloading the dataset |

## Troubleshooting

- **"Port 5214 is already in use":** another copy is running. Close its window, or change FRONTEND_PORT in `.env`.
- **"Cannot reach the AquaVision server":** the backend window is closed or still starting. Wait a few seconds and retry.
- **The first quality check is slow (~5-10 s):** models load in the background at startup, and later checks take under a second.
- **Offline:** everything works except the map tiles. The forecast falls back to cached weather.
