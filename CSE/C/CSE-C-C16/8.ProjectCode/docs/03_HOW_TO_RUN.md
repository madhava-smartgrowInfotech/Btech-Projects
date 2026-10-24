# How to run AgriVision

AgriVision has two front ends over the same data:

| | What | Port | Start |
|---|---|---|---|
| **New** (React, Aurora Glass) | `frontend/` + FastAPI layer in `backend/` | API **8416**, web **5416** | `run.bat` |
| Original (Flask templates) | `agrivision/` | 5000 | `cd agrivision && python app.py` |

Both read and write the same SQLite file (`agrivision/agrivision.db`) and the same `agrivision/static/uploads/`, so an
account or a scan made in one shows up in the other. The Flask app is unchanged.

## One-click start (Windows)

1. Install **Python 3.10+** (tick "Add python.exe to PATH") and **Node.js 20+**.
2. Double-click **`run.bat`** in this folder. The first run:
   - creates `.venv` and installs `backend/requirements.txt` (a few minutes),
   - runs `npm install` in `frontend/` (a minute or two),
   - starts the API on 8416 and the web app on 5416, then opens **http://localhost:5416**.
3. Sign in with the demo account **`demo@agrivision.ai` / `demo1234`**, or create your own on the Register page.

Close the two minimised windows ("AgriVision backend" / "AgriVision frontend") to stop.

A `.venv` copied from another computer is detected and rebuilt automatically.

## Manual start

```bash
# project root
python -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements.txt
set PYTHONHASHSEED=0
.venv\Scripts\python -m uvicorn backend.main:app --port 8416

# second terminal
cd frontend
npm install
npm run dev          # http://localhost:5416, proxies /api to 8416
npm run build        # type-check + production bundle in frontend/dist
```

Ports live in `.env` (`BACKEND_PORT`, `FRONTEND_PORT`; copy `.env.example` if it is missing). `.env` is git-ignored.

## The diagnosis engine

`agrivision/models/` ships **empty**, so `inference.py` uses its colour/texture **heuristic**. The app says so on the
sidebar, the landing page and every result. To use a real CNN:

```bash
pip install tensorflow           # not in backend/requirements.txt on purpose (large)
cd agrivision && python train.py # trains on ../datasets/plantdoc-images, writes models/plantdoc_cnn.h5
```

Restart the API; `/api/health` then reports `trained_model: true` and the UI switches its wording. The 1.4 GB
`datasets/` folder is git-ignored.

## API in one table

All JSON under `/api`. Sign in with `POST /api/v1/auth/login`, then send `Authorization: Bearer <token>`.

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | status, class count, engine |
| POST | `/api/v1/auth/login`, `/auth/register` | returns `token` + `user` |
| GET | `/api/v1/auth/me` | current user |
| PUT | `/api/v1/profile` | name, region, language (en/hi/mr), crops |
| GET | `/api/v1/dashboard` | totals and 6 recent scans |
| POST | `/api/v1/detect/upload` | multipart `image` (JPG/PNG/JPEG/WEBP, 10 MB) + `crop_type` |
| GET | `/api/v1/history` | `limit, offset, q, crop, disease` |
| GET / DELETE | `/api/v1/history/{id}` | one result / delete it |
| GET | `/api/v1/history/{id}/export?format=csv|pdf`, `/api/v1/history/export` | downloads |
| GET | `/api/v1/analytics/dashboard` | distribution, severity, timeline |
| GET | `/api/v1/diseases`, `/api/v1/diseases/{class}` | 38-class knowledge base |

Interactive docs: http://127.0.0.1:8416/docs

## Checks

```bash
python scripts/smoke_test.py       # starts its own API with a throw-away DB, 39 checks
python scripts/capture_screens.py  # needs both servers + `pip install playwright` + `playwright install chromium`
python scripts/ui_checks.py        # 55 browser checks: 360/768/1440 px, drawer, theme, language, delete, keyboard
```

`capture_screens.py` signs in as the demo farmer, uploads real PlantDoc leaves (from `datasets/`), and writes 1440x900
PNGs to `docs/screenshots/`; it removes the scans it created afterwards (set `KEEP_SEEDED=1` to keep them) and freezes
animations (set `AGRIVISION_MOTION=1` to capture with them on). On a PC without a usable GPU, headless Chrome needs the
SwiftShader flags the scripts already pass; each screenshot can still take a while.

## Troubleshooting

- **"API offline" chip in the top bar**: the backend is not running. Start it (run.bat) and refresh.
- **Port already in use**: change the ports in `.env`, then restart.
- **Fonts look plain offline**: the Google Fonts stylesheet loads without blocking; the app falls back to system fonts.
- **First `npm run dev` is slow**: Vite pre-bundles dependencies once; later starts are quick.
