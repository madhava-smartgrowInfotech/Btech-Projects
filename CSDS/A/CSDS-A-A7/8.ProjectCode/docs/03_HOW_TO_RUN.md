# SHEGUARD - How to run

## Prerequisites
- Python 3.10+ and Node.js 18+ on PATH.
- A Gemini API key, a Telegram bot token, and a Gmail address + App Password (all free - see
  `.env.example` for exactly where to get each one). The app runs without them; the AI
  assistant, Telegram alerts and email alerts just won't fire until they're filled in.

## First-time setup
```
setup.bat
```
This copies `.env.example` to `.env` (fill in your keys afterwards), creates the Python venv,
installs backend requirements, and runs `npm install` in `frontend/`.

## Train the area-risk model (one time, or whenever the data changes)
```
venv\Scripts\python.exe ml\train_risk_model.py
```
Districts are already geocoded and committed (`data/districts_geocoded.csv`), so this takes a
few seconds. It writes `models/risk_model.joblib`, `data/district_risk.csv` and
`experiments/metrics.json`. The backend loads `data/district_risk.csv` into its database
automatically the first time it starts.

## Run it
```
run.bat
```
Opens two terminal windows (backend on http://localhost:8107, frontend on
http://localhost:5107) and your browser to the app.

**Demo login:** `demo@sheguard.app` / `Demo@1234` (created by `scripts\seed_demo.py` - run it
once after the backend is up, or just register your own account from the app).

## Try it on your phone
1. Install the tunnel once: `winget install --id Cloudflare.cloudflared`
2. Run:
   ```
   run_phone.bat
   ```
3. A third window opens with a `https://xxxx.trycloudflare.com` link - open that on your
   phone's Chrome, then use the browser menu → "Add to Home screen" to install the PWA.

## Verify everything works
```
venv\Scripts\python.exe scripts\smoke_test.py
```
Drives the real running backend through register → login → add guardian → plan a route (real
OSRM call) → start SOS (real Telegram/email attempt) → push location → upload evidence → cancel
→ read the public tracking page. The AI-assistant step only warns (doesn't fail) if
`GEMINI_API_KEY` isn't set yet.

```
cd frontend && npm run build
```
Production build of the frontend.

## Evaluation numbers
```
venv\Scripts\python.exe ml\eval.py
```
Writes cluster-quality and route-scoring sanity-check numbers to
`experiments/eval/metrics.json` (see the README for the latest run's results).
