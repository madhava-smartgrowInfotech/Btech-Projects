# NutriSense - How to Run

## Requirements
- Windows 10/11
- Python 3.11 or newer (tick "Add python.exe to PATH" during install)
- Node.js LTS (20 or newer)
- Internet access (Gemini and USDA lookups)

## 1. One-time setup
1. Open the `8.ProjectCode` folder.
2. Double-click **`setup.bat`**. It will:
   - create a Python virtual environment and install the backend packages
   - create `.env` from `.env.example`, with a random login secret
   - build the food database and train the swap model if they are missing (both are already included)
   - install the frontend packages
3. Open `.env` in a text editor and paste your Gemini key after `GEMINI_API_KEY=`.
   Get a free key at https://aistudio.google.com/apikey.
   The key enables recipe steps and photo logging. Everything else works without it.
4. Optional: add your own USDA key (`USDA_API_KEY`) from https://fdc.nal.usda.gov/api-key-signup.html. Without one, USDA's shared `DEMO_KEY` is used.

## 2. Start
Double-click **`run.bat`**. It opens two windows (API and web app), then your browser at http://localhost:5211.

| Service | Address |
|---|---|
| Web app | http://localhost:5211 |
| API | http://localhost:8211/api (interactive docs at http://localhost:8211/docs) |

To stop NutriSense, close the two server windows.

## 3. Log in
- **Sample account:** `demo@nutrisense.app` / `Demo@1234`
  (a 28-year-old woman, vegetarian, peanut allergy, weight-loss goal, 1650 kcal target)
- Or click **Create an account** and complete the profile wizard.

## 4. Demo walkthrough
1. Log in with the sample account. The dashboard shows a 1650 kcal target and the macro split.
2. Open **Weekly plan** and click **Generate my plan**. Every day is within 5 % of the target, with no peanut dishes.
3. Click **Swap** on any dish and pick an alternative. Click **Recipe** to see AI-written steps.
4. Open **Food log**, then **Log by photo**. Upload `data/sample/photos/masala_dosa.jpg`, click **Recognise dish**, and click **Log** on the match. The intake bars update.
5. Open **Progress** and log a week of weights (e.g. 66.0, 65.9, 65.9, 65.8, 65.8, 65.7, 65.7 on seven consecutive dates ending today). After the seventh entry the target is recalculated and shown in the target history.

## 5. Checks (optional)
From the `8.ProjectCode` folder, with the backend running:

```bat
venv\Scripts\python scripts\smoke_test.py      :: end-to-end API test
venv\Scripts\python ml\eval.py                 :: evaluation -> experiments\eval\metrics.json
cd frontend && npm run build                   :: production build of the web app
```

## Rebuilding the data (optional)
```bat
venv\Scripts\python scripts\download_data.py   :: re-download the Kaggle datasets into data\raw
venv\Scripts\python ml\build_foods.py          :: data\raw -> data\processed\foods.csv
venv\Scripts\python ml\train_swaps.py          :: K-Means swap model -> models\, experiments\metrics.json
```

## Troubleshooting
| Problem | Fix |
|---|---|
| "Port 5211 is already in use" | Another copy is running. Close its windows, or change `FRONTEND_PORT` in `.env`. |
| "Cannot reach the NutriSense server" | The API window closed or failed. Re-run `run.bat` and read the API window for errors. |
| Recipe or photo says "Gemini is not configured" | Add `GEMINI_API_KEY` to `.env`, then restart with `run.bat`. |
| USDA search unavailable | The shared `DEMO_KEY` is rate-limited. Add your own free key to `.env`. |
| Start from a clean database | Stop the app and delete `data\app.db`. It is recreated, with the sample account, on the next start. |
