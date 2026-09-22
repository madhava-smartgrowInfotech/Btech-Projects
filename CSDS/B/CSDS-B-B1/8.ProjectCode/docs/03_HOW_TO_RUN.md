# How to run CivicPulse

## 1. Prerequisites (Windows)

- **Python 3.11** (3.11 or 3.12; `py -3.11 --version` should work)
- **Node.js 20 LTS or newer** (`node --version`)
- **Git**
- A **Gemini API key** from https://aistudio.google.com/apikey (free). Without it, everything works except
  detail extraction and draft replies, which show "unavailable".
- Internet access for map tiles, Gemini and the first-time package install.

## 2. First-time setup

Open a terminal in the `8.ProjectCode` folder and run:

```bat
setup.bat
```

It creates `venv\`, installs the Python packages, creates `.env` from `.env.example` with a random
`JWT_SECRET`, and runs `npm install` in `frontend\`. The datasets and trained models are already in the
repository; setup only downloads or trains them if they are missing.

Then open `.env` and paste your key:

```
GEMINI_API_KEY=your-key-here
```

| Key | Meaning |
|---|---|
| `GEMINI_API_KEY` | Gemini key (extraction + draft replies) |
| `GEMINI_MODEL` / `GEMINI_FALLBACK_MODEL` | models to use; the fallback is tried when the first is busy |
| `JWT_SECRET` | secret for login tokens (set by setup) |
| `BACKEND_PORT` / `FRONTEND_PORT` | 8201 / 5201 |
| `DATABASE_PATH` | SQLite file, default `data/app.db` |

## 3. Start

```bat
run.bat
```

Two console windows open (API on http://localhost:8201, web app on http://localhost:5201) and the browser
opens the app. The first start builds the sample database (about 30 seconds). Close both console windows to
stop.

Manual start, if you prefer:

```bat
cd backend  && ..\venv\Scripts\python -m uvicorn app.main:app --port 8201
cd frontend && npm run dev
```

## 4. Demo logins

| Role | Email | Password |
|---|---|---|
| Citizen | citizen@civicpulse.local | Citizen@123 |
| Officer | officer@civicpulse.local | Officer@123 |
| Admin | admin@civicpulse.local | Admin@123 |

The login page has one-click buttons that fill these in.

## 5. Demo walkthrough

1. Log in as **Citizen** -> *File a complaint*. Type in Hindi (for example: "कोरमंगला 5th ब्लॉक की मुख्य सड़क पर
   बहुत बड़ा गड्ढा है, पिछले दो हफ्ते से कोई मरम्मत नहीं हुई। कल रात एक बाइक सवार गिरकर घायल हो गया। कृपया जल्द ठीक
   करें।"), add a
   photo, tap the map, submit. Note the tracking ID.
2. Log out, log in as **Officer**. The complaint is near the top of the *Triage queue* as Roads & Footpaths ->
   Roads, High, about 6 days, with key words गड्ढा / सड़क / घायल. Open it to see the LIME words, the SHAP
   factors and the Gemini details, then click **Accept & assign**.
3. Open another complaint whose department looks wrong, choose the right department, type a reason and
   save. Click **Retrain model now**; the before / after metrics appear in about a minute.
4. Open *Hotspots & analytics*: the map, recurring issues, SLA table and trends include the new complaints.
   Back on the complaint, click **Draft with Gemini**, edit the reply and send it. The citizen sees it on
   *My complaints*.

Admins can change a department's SLA days with the pencil icon in the SLA table.

## 6. Checks

With the backend running:

```bat
venv\Scripts\python scripts\smoke_test.py
cd frontend && npm run build
```

The smoke test drives the whole flow through the real API (including Gemini and a retrain) and prints
`ALL 25 CHECKS PASSED`. Note that it retrains the live model; run `venv\Scripts\python ml\train.py` afterwards
to return to the original v1 models.

## 7. Models and evaluation

```bat
venv\Scripts\python ml\train.py        :: retrain all models from data\raw (~3 min on CPU)
venv\Scripts\python ml\eval.py         :: evaluation -> experiments\eval\metrics.json (~3 min)
venv\Scripts\python scripts\download_data.py   :: re-download the datasets
```

## 8. Reset the demo data

Stop the backend, delete `data\app.db` (and `app.db-wal` / `app.db-shm` if present) and `data\uploads\*`,
then start again. The sample data is regenerated identically (seeded).

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| `Port 5201 is already in use` / backend fails to bind 8201 | Another program uses the port. Close it, or change `FRONTEND_PORT` / `BACKEND_PORT` in `.env`. |
| "Cannot reach the CivicPulse server" in the browser | The API window is not running or still starting; check the "CivicPulse API" console. |
| "Gemini is busy right now" | The Gemini model is overloaded (HTTP 503). Try again in a minute, or set `GEMINI_MODEL` to another model. |
| Extraction shows "failed" | Check `GEMINI_API_KEY` in `.env`, restart the backend, then click *Extract details*. |
| `Set JWT_SECRET in .env` on start | Run `setup.bat` or set `JWT_SECRET` to any long random string. |
| Map is grey | Map tiles come from OpenStreetMap and need internet access. |
| First retrain is slow | The feature cache in `data\cache\` is built on the first retrain after a fresh clone (~1 min); later retrains are faster. |
