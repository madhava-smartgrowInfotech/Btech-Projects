# HospiSense - How to run

## Requirements

- Windows 10/11
- Python 3.11 or newer - https://www.python.org/downloads/ (tick "Add python.exe to PATH")
- Node.js LTS (20 or newer) - https://nodejs.org/
- Free ports **8207** (API) and **5207** (web app)

No API keys are needed. The datasets and trained models are already in the repository.

## 1. Set up (once)

Double-click `setup.bat`, or run from this folder:

```bat
setup.bat
```

It creates `venv\`, installs `requirements.txt`, creates `.env` from `.env.example` with a random `JWT_SECRET`, and runs
`npm install` in `frontend\`. It takes about 3-5 minutes.

## 2. Start

```bat
run.bat
```

Two windows open ("HospiSense API" and "HospiSense Web"), then the browser opens at **http://localhost:5207**.
API docs: http://127.0.0.1:8207/docs. Close both windows to stop.

## 3. Sign in

| Role | Email | Password |
|---|---|---|
| Administrator | admin@hospisense.app | Admin@123 |
| Doctor | doctor@hospisense.app | Doctor@123 |

The login page has buttons that fill these in.

## 4. Demo walk-through

1. **Admissions** -> *Sample long stay* (a real held-out record, marked as sample data) -> *Admit patient*. The expected
   stay (for example about 6 days, "Long stay") appears with the SHAP reasons, such as readmissions adding days.
2. **Forecasts -> ICU demand**: the ICU early warnings list the first day each facility can pass its ICU capacity; the charts
   show the expected census, 90% band and capacity line.
3. **Allocation** (administrator) -> *Run optimiser*: review the bed conversions, diversions, nurse floats, extra shifts and
   equipment transfers with their reasons. Optionally change a quantity (0 drops an action), then *Accept plan*. The
   forecasts and dashboard then use the new capacity.
4. **Model performance**: prediction error, forecast error against the baselines, and the gain over the static allocation.

## 5. Checks

With the API running (`run.bat`):

```bat
venv\Scripts\python scripts\smoke_test.py
cd frontend && npm run build
```

The smoke test drives the whole flow through the API and prints `SMOKE TEST PASSED`. It admits a patient and accepts a
plan, so delete `data\app.db` afterwards if you want a clean start.

## 6. Rebuild the models and evaluation (optional)

```bat
venv\Scripts\python scripts\download_data.py   (only if data\raw is missing)
venv\Scripts\python ml\prepare_data.py
venv\Scripts\python ml\train.py
venv\Scripts\python ml\eval.py
```

This takes about 30 seconds on a CPU. Results go to `experiments\metrics.json` and `experiments\eval\metrics.json`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Port 5207 is in use` / API will not start | Close the program using port 5207 or 8207, or change `FRONTEND_PORT` / `BACKEND_PORT` in `.env` (the API port in `run.bat` too). |
| "Cannot reach the HospiSense server" in the browser | The API window has closed or failed - check its window for the error and run `run.bat` again. |
| `JWT_SECRET is missing` | Run `venv\Scripts\python scripts\init_env.py`. |
| Reset all admissions, plans, capacity and rosters | Stop HospiSense, delete `data\app.db`, start again. |
| `pip` fails to install `ortools` / `xgboost` | Use 64-bit Python 3.11-3.13. |
