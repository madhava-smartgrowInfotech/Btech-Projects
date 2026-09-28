# TaxSentinel - How to run

## Requirements
- Windows 10/11
- Python 3.11+ (https://www.python.org/downloads/, tick "Add python.exe to PATH")
- Node.js LTS (https://nodejs.org/)
- A Gemini API key for written explanations (free): https://aistudio.google.com/apikey
- Ports 8105 (API) and 5105 (web) free

## 1. Set up (once)
Open the `8.ProjectCode` folder and double-click **`setup.bat`** (or run it from a terminal). It:
1. creates `venv\` and installs PyTorch (CPU build) and `requirements.txt`;
2. creates `.env` from `.env.example` with a random `JWT_SECRET`;
3. trains the JEPA encoder if `models\jepa.pt` is missing;
4. runs `npm install` in `frontend\`.

Then open `.env` and paste your key:
```
GEMINI_API_KEY=AIza...
```
Without the key everything works except the *Write explanation* button, which shows a clear message.

## 2. Start
Double-click **`run.bat`**. It opens two windows (API and web), waits for the API, then opens
http://localhost:5105.

Sign in with the demo account **demo@taxsentinel.app / Demo@1234**, or create your own.

To stop, close the two server windows.

## 3. Demo walkthrough
1. **Overview** → *Generate & analyse* (seed 42, 600 taxpayers; about 20-40 s). The counts, flagged taxpayers, patterns and chains refresh.
2. Open the **top-ranked taxpayer**: layer scores, the monthly GSTR-2B vs GSTR-3B chart, evidence (ITC spikes, mismatches, anomalous invoices) and the network graph with its circular-trading loop in red.
3. **Open case & explanation** → *Write explanation*. Gemini's case note cites the evidence; click an `E#` to jump to it.
4. **Fraud rings**: every loop, shell cluster and ranked invoice chain; click a chain for its invoices.
5. **Model performance**: precision@k and recall vs the rule baseline, ablations, per-pattern recall.

## 4. Command line (optional)
From `8.ProjectCode` with the venv:
```bat
venv\Scripts\python scripts\generate_gst_data.py --seed 42 --taxpayers 600   :: regenerate data/generated
venv\Scripts\python -m ml.train                                              :: retrain models/jepa.pt
venv\Scripts\python -m ml.eval                                               :: experiments/eval/metrics.json
venv\Scripts\python scripts\download_data.py                                 :: PaySim sample (Kaggle)
venv\Scripts\python scripts\smoke_test.py                                    :: end-to-end API test (API must be running)
cd frontend && npm run build                                                 :: production build
```
Manual start without `run.bat`:
```bat
venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8105
cd frontend && npm run dev
```

## 5. Troubleshooting
| Symptom | Fix |
|---|---|
| "Port 5105 is already in use" | Another copy is running. Close it, or change `FRONTEND_PORT` in `.env` |
| Web page says it cannot reach the API | Start the API window (`run.bat`) and check http://127.0.0.1:8105/api/health |
| "GEMINI_API_KEY is not set" | Add the key to `.env` and restart the API window |
| Gemini 429 / quota errors | The free tier is rate-limited. Wait a minute; fallback models in `GEMINI_FALLBACK_MODELS` are tried automatically |
| Kaggle asks for credentials | Set `KAGGLE_USERNAME` / `KAGGLE_KEY` in `.env` (kaggle.com → Settings → API → Create New Token) |
| Start over with a clean state | Stop the servers, delete `data\workspace\` and `data\app.db`, then start again |
