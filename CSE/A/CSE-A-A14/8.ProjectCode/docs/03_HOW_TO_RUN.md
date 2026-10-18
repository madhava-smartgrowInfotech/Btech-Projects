# How to run - ChurnIQ (React + FastAPI) and the original Streamlit app

The project now has two front ends over the same Python core in `src/`:

| Front end | Start | URL |
|---|---|---|
| **React app (new)** on a FastAPI layer | `run.bat` | http://localhost:5314 (API on `8314`, docs at `/docs`) |
| Streamlit app (original, untouched) | `run.bat streamlit` | http://localhost:8501 |

## Prerequisites

- Windows with **Python 3.10+** and **Node.js 18+** on `PATH`
- Internet access on the first run only (pip and npm downloads)

## One-command start

```
run.bat
```

The first run creates `.venv`, installs `backend\requirements.txt`, runs `npm install` in `frontend\`, then opens
two console windows (API and web app) and your browser. Later runs start in a few seconds.

| Command | What it does |
|---|---|
| `run.bat` | Start the API (8314) and the React app (5314) |
| `run.bat smoke` | Run `scripts/smoke_test.py` against the running API (60+ checks) |
| `run.bat build` | Production build of the frontend into `frontend/dist` |
| `run.bat streamlit` | Launch the original Streamlit app instead |

Ports come from `.env` (`BACKEND_PORT=8314`, `FRONTEND_PORT=5314`). Change them there; Vite and the API both read it.

## Demo login

The React app asks you to sign in. The demo account is shown on the sign-in page and works with one click:

| | |
|---|---|
| Email | `demo@churniq.com` |
| Password | `Demo@1234` |

Change it in `.env` (`DEMO_EMAIL`, `DEMO_PASSWORD`, `AUTH_SECRET`) and restart the API. Tokens last 12 hours.

## First five minutes

1. Sign in, then press **Quick start with sample data** on the dashboard. It loads 1,000 synthetic customers,
   prepares them, trains Logistic Regression, Decision Tree and Random Forest, and saves the best one (a few seconds).
2. Explore **Customer risk**, **Customer 360**, **Explainable AI**, **What-if** and **Retention actions**.
3. To use your own data: **Data upload** -> drop a CSV -> check the detected churn and ID columns -> **Prepare data**
   -> **Model training** -> **Save as active model**.

## Run the two halves by hand

```
python -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements.txt
.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8314
```

and in a second terminal:

```
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to the backend, so no CORS setup is needed during development.

## Checks and tooling

| Script | Purpose |
|---|---|
| `scripts/smoke_test.py [base_url]` | End-to-end API test: login, data, EDA, training, evaluation, risk, customer, XAI, what-if, retention, batch, drift. Exit code 0 means pass |
| `scripts/capture_screens.py [base_url]` | Drives the running app with Playwright and writes 1440x900 PNGs to `docs/screenshots/` (needs `pip install playwright`) |

## Things to know

- **State lives in the API process.** The loaded dataset and the trained-model comparison are in memory (like a Streamlit
  session). The *saved* model is written to `models/` and restored when the API restarts; load the sample or your CSV
  again to score customers.
- **SHAP is optional.** Without `pip install shap`, explanations use permutation importance and model coefficients and
  the interface says so. After installing it, restart the API.
- **Everything is local.** No customer data leaves the machine; no external AI service is called.
- The `models/*.pkl` files are produced at runtime and are git-ignored.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "API offline" pill in the top bar | The API window closed. Run `run.bat` again, or start uvicorn as shown above |
| Port already in use | Change `BACKEND_PORT` / `FRONTEND_PORT` in `.env` and restart |
| `pip install` fails for `shap` | It is optional and not in `backend\requirements.txt`; skip it |
| Sign-in says the session expired | Tokens last 12 hours, or the API was restarted with a different `AUTH_SECRET`; sign in again |
| A screen says it needs a dataset or model | Use **Quick start** on the dashboard, or follow the first-five-minutes steps |
