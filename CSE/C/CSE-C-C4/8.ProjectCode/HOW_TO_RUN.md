# QuantPulse — HOW TO RUN (complete guide)

QuantPulse is a FastAPI backend (port **8404**) plus a React website (port **5404**).
Ports are set in the `.env` file next to `run.bat`.

## 1. Prerequisites

- **Windows 10/11**, about 3 GB free disk (first-run model libraries), internet for setup.
- **Python 3.11**: https://www.python.org/downloads/ (any 3.11.x). During setup tick **"Add python.exe to PATH"**.
  Verify in PowerShell: `python --version` should print `Python 3.11.x`.
- **Node.js 20 or newer** (recommended): https://nodejs.org/ — runs the website on port 5404.
  Without Node the API still serves the prebuilt website (`frontend/dist`) on port 8404.
- **Docker Desktop (optional, Method B only)**: https://www.docker.com/products/docker-desktop/
- **NewsAPI key (optional)**: https://newsapi.org (free tier). Without it QuantPulse uses its built-in headline
  fallback and nothing breaks.

## 2. Method A — Automatic (recommended)

1. Open the project folder (the one that contains `run.bat`).
2. Copy `.env.example` to `.env` if there is no `.env` yet (the defaults are fine).
3. **Double-click `run.bat`.** It prints each step:
   - `[1/6]` Python found.
   - `[2/6]` Virtual environment (`.venv`) created once, recreated if broken.
   - `[3/6]` Python dependencies installed once (several minutes, downloads TensorFlow and PyTorch).
   - `[4/6]` Models trained **only if** `artifacts\metrics.json` is missing (5–10 minutes on a CPU).
   - `[5/6]` Website packages installed once (`npm install`).
   - `[6/6]` Two windows open, **QuantPulse API** and **QuantPulse Website**, and your browser opens
     **http://localhost:5404**.
4. **How you know it worked:** the landing page shows a ticker chart, **Open app** shows 10 ticker cards, and the
   status pill in the top bar says **API online · models ready**.
5. **To stop:** close the two windows.

> The very first **News sentiment** screen can take a minute or two: the API loads the FinBERT language model on
> first use (and downloads it once). The screen shows a progress bar while it waits.

## 3. Method B — Docker

```powershell
docker compose up --build
```

Then open http://localhost:8000 (the container serves the prebuilt website itself). Stop with Ctrl+C or
`docker compose down`. Alternative one-click: `run-docker.bat`.

## 4. Method C — Manual (exact commands)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m backend.train        # first time only (or when retraining)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8404
```

In a second terminal, for the website with live reload:

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5404 (proxies /api to port 8404)
```

`npm run build` rebuilds `frontend/dist`, which the API serves at http://localhost:8404 when you do not run Node.

## 5. Checking it

With the stack running:

```powershell
python scripts\smoke_test.py          # API, error paths and website checks
pip install playwright; playwright install chromium
python scripts\capture_screens.py     # refreshes docs\screenshots\*.png
```

## 6. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Python was not found` | Install Python 3.11 from python.org, tick **Add to PATH**, reopen the terminal. |
| SmartScreen blocks `run.bat` | Click **More info → Run anyway**. It is a plain-text script, right-click → Edit to read it. |
| Top bar says **API offline** | The API window closed or crashed. Run `run.bat` again and read the **QuantPulse API** window. |
| `Port 8404/5404 already in use` | Close the other app, or change `BACKEND_PORT` / `FRONTEND_PORT` in `.env`. |
| `pip install` fails | Check internet/VPN and run `run.bat` again, it retries cleanly. |
| Screens say **models are not trained yet** (503) | Run `python -m backend.train` with the venv active. |
| Forecast screen says the models were trained on older prices | Expected: the live price history moved on. Retrain with `python -m backend.train` to forecast from the latest close. |
| Sentiment shows source **Built-in fallback** | No `NEWSAPI_KEY`. Put one in `.env` and restart to use live headlines. |
| Yahoo Finance blocked (429/offline) | The loader reuses `data/*.csv`; if absent it uses a clearly labelled synthetic series. The per-ticker mode (live / csv / synthetic) is shown in the app. |
| Website shows nothing on port 5404 | Node.js is missing or `npm install` failed. Open http://localhost:8404 for the prebuilt site. |

## Disclaimer

QuantPulse is a research and education tool. Forecasts are statistical estimates, not financial advice.
