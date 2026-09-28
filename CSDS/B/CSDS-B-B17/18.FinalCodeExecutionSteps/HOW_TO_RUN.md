# CallSense - how to run

## Requirements
- Windows 10/11 with the built-in speech voices (used only by the sample call studio)
- Python 3.11+, Node.js LTS (20+), Git
- About 3 GB of disk space (Python packages + speech models) and an internet connection for the first setup
- A Gemini API key for call summaries (https://aistudio.google.com/apikey)
- Optional: a microphone for recording calls in the browser

## First-time setup
```bat
cd 8.ProjectCode
setup.bat
```
`setup.bat` creates `venv`, installs the Python packages (CPU PyTorch, faster-whisper, transformers, ...),
creates `.env` from `.env.example` if it is missing, runs `npm install`, trains the text models if `models/` is
empty, generates the sample recordings if missing, and downloads the speech models (about 850 MB, once).

Open `.env` and check `GEMINI_API_KEY` (and optionally `GEMINI_MODEL`, `GEMINI_FALLBACK_MODELS`).

## Start
```bat
run.bat
```
Opens two console windows (API on http://localhost:8217, web app on http://localhost:5217) and the browser.
Close the two windows to stop.

Manual start (two terminals):
```bat
venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8217
cd frontend && npm run dev
```

## Demo logins
| Role | Email | Password |
|------|-------|----------|
| Supervisor | supervisor@callsense.local | CallSense@123 |
| Agent (Alex) | agent@callsense.local | CallSense@123 |
| Agents | sam@callsense.local, jordan@callsense.local | CallSense@123 |

The password is `DEMO_PASSWORD` in `.env`.

## Demo walk-through
1. Sign in as the supervisor. On **Calls** press **Load sample calls** to queue the 10 bundled sample calls
   (each takes about a minute to analyse on CPU).
2. Open **Sample studio**, pick *Refund request - returned headphones*, choose agent Alex and press
   **Generate sample call and analyse**. The call page opens and shows progress.
3. When it finishes: the transcript is split into agent / customer, the intent is `get_refund`, the emotion timeline
   goes from frustrated/angry to relieved, and the summary and scorecard appear with their evidence.
4. **Analytics** shows volumes, top intents, the sentiment trend and the agent leaderboard; search transcripts from
   the Calls page (e.g. "refund").
5. **Model performance** shows the training and evaluation results.

## Useful commands
```bat
venv\Scripts\python scripts\smoke_test.py            :: end-to-end API test (backend must be running)
venv\Scripts\python ml\train.py                      :: retrain intent / sentiment / keyword models
venv\Scripts\python ml\eval.py                       :: full evaluation -> experiments\eval\metrics.json (~20 min)
venv\Scripts\python scripts\generate_sample_calls.py :: re-render the sample recordings
venv\Scripts\python scripts\download_data.py         :: re-download datasets (add --full for complete audio sets)
cd frontend && npm run build                         :: production build of the web app
```

## Troubleshooting
- **Port in use** - change `BACKEND_PORT` / `FRONTEND_PORT` in `.env` (defaults 8217 / 5217).
- **Summary missing** - the call page shows the Gemini error; check the key, then press *Regenerate*. The rest of
  the analysis does not depend on Gemini.
- **First call is slow** - the speech models load when the API starts; later calls take roughly the call length.
- **Studio: "No offline text-to-speech voices"** - install an English voice in Windows Settings > Time & language > Speech.
- **Microphone blocked** - allow microphone access for localhost in the browser.
