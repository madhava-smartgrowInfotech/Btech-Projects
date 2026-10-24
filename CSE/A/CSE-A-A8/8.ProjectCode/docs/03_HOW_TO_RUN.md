# How to run LabLens

LabLens has two interfaces over the same Python pipeline and the same SQLite database (`data/medical_lab.db`):

| Interface | Start with | URL |
|---|---|---|
| **New web app** (React + FastAPI, kit V3 "Depth Studio") | `run.bat` | http://localhost:5308 (API on 8308) |
| Original Streamlit app (unchanged) | `streamlit run app.py` | http://localhost:8501 |

## 1. Prerequisites

- **Python 3.11+** and **Node.js 20+** (LTS) on your PATH.
- **Tesseract OCR** (optional but recommended): needed only for scanned PDFs and photos / screenshots (JPG, PNG).
  Text-based PDFs work without it.
  - Windows: install from https://github.com/UB-Mannheim/tesseract/wiki and make sure `tesseract.exe` is on PATH.
  - macOS: `brew install tesseract` - Ubuntu: `sudo apt-get install tesseract-ocr`

## 2. One-click start (Windows)

Double-click **`run.bat`**. The first run:

1. creates `backend\.venv` and installs `backend\requirements.txt` (a few minutes; it rebuilds the environment if it is missing or broken),
2. runs `npm install` in `frontend\`,
3. opens two console windows (API and web app) and your browser at http://localhost:5308.

Ports come from `.env` (`BACKEND_PORT=8308`, `FRONTEND_PORT=5308`). Close the two console windows to stop.

### Sign in

The original product had no login, so the new interface adds a demo account:

- **Email:** `demo@lablens.com`  **Password:** `Demo@1234`
- The login page also has a **Sign in as demo user** button. Change the credentials with `DEMO_EMAIL` / `DEMO_PASSWORD` and the token signing key with `JWT_SECRET` in `.env`.

### First look without a report

On an empty library, the Dashboard, My reports, Report analysis, Trends, Compare and Insights screens offer
**Load sample reports**. It renders five synthetic lab reports (invented patient and values, April to October 2026)
as real PDFs and runs them through the unchanged extraction pipeline, so you get trends and insights immediately.

## 3. Manual start (any OS)

```bash
# backend (from this folder)
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt     # macOS/Linux: backend/.venv/bin/python
backend/.venv/Scripts/python -m uvicorn backend.main:app --port 8308

# frontend (second terminal)
cd frontend
npm install
npm run dev            # http://localhost:5308, proxies /api to port 8308
```

Production-style: `cd frontend && npm run build`, then start only the backend - it serves `frontend/dist` itself at http://localhost:8308.

## 4. Optional settings (`.env`)

| Variable | Purpose |
|---|---|
| `BACKEND_PORT`, `FRONTEND_PORT` | fixed to 8308 / 5308 for this project |
| `JWT_SECRET` | signs login tokens - change on first run |
| `DEMO_EMAIL`, `DEMO_PASSWORD` | override the demo account |
| `ANTHROPIC_API_KEY` | enables the "Use LLM for richer explanations" switch (`ai_insights.py` reads exactly this name). Without it the built-in rule-based explanations are used. |

## 5. API (for reference)

Interactive docs: http://localhost:8308/docs. All routes except `/api/health`, `/api/config` and `/api/auth/login` need `Authorization: Bearer <token>`.

`POST /api/auth/login` - `GET /api/auth/me` - `GET /api/dashboard` - `GET|POST /api/reports` - `GET|DELETE /api/reports/{id}` -
`GET /api/tests` - `GET /api/trends?test=` - `GET /api/compare?a=&b=` - `GET /api/insights` - `POST /api/demo/seed`

## 6. Tests and screenshots

```bash
python scripts/smoke_test.py          # API + browser flow in a temporary copy (your database is untouched)
python scripts/ui_check.py            # 360/768/1440 px, light/dark, drawer, keyboard, reduced motion, error states
python scripts/capture_screens.py     # refreshes docs/screenshots/*.png (1440x900)
```

The last two need a running app (`run.bat`) and `pip install playwright && playwright install chromium`.
`smoke_test.py` needs a built frontend (`cd frontend && npm run build`) for its browser part.

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| "Cannot reach the LabLens backend on port 8308" in the UI | the API window is not running - start `run.bat` again and read its console for the error |
| Upload of a JPG/PNG fails with an OCR message | install Tesseract OCR (see Prerequisites) |
| "No recognizable lab test rows were found" | the layout is unusual or the scan is too faint; try a clearer file. Rows should look like `Hemoglobin 13.5 g/dL 12 - 16` |
| LLM switch is disabled | no `ANTHROPIC_API_KEY` in `.env` (optional feature) |
| Port already in use | another product is using 8308/5308; stop it or change the ports in `.env` |
