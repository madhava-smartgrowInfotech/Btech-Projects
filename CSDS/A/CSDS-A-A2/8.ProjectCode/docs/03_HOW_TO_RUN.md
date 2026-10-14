# How to run — Attendance Magic

Two front-ends share the same `core/` logic and the same SQLite database:

| | URL | Start |
|---|---|---|
| **React app (new)** — Neo Brutal Grid UI | http://localhost:5102 | `run.bat` |
| FastAPI layer used by the React app | http://127.0.0.1:8102/docs | `run.bat` |
| Streamlit app (original, unchanged) | http://localhost:8501 | `venv\Scripts\streamlit run app.py` |

Ports come from `.env` (`BACKEND_PORT=8102`, `FRONTEND_PORT=5102`).

## First time (Windows)

```
setup.bat
```
Creates `venv\` with **Python 3.11** (mediapipe 0.10.21 has no wheel for 3.13/3.14), installs `requirements.txt`
+ `backend\requirements.txt`, seeds the demo accounts and runs `npm install` in `frontend\`.
The first run downloads the InsightFace `buffalo_l` model (~280 MB) to `%USERPROFILE%\.insightface`.

## Every time

```
run.bat      # opens two server windows + the browser
stop.bat     # stops whatever is listening on the two ports
```

Manual equivalent:
```
venv\Scripts\python -m uvicorn backend.api:app --host 127.0.0.1 --port 8102
cd frontend && npm run dev
```

## Demo accounts (`scripts\seed_demo.py`)

| Role | Login | Password |
|---|---|---|
| Faculty | `faculty@college.edu` | `faculty123` |
| Students | `23K91A6706`, `23K91A6740`, `23K91A6757`, `24K95A6704` | `student123` |

Seeded students have no face yet: register a new student (with a photo) or enrol a face for them under
**Faculty → Students → Manage**.

## Try the flow

1. Sign in as faculty → **New session** → set the location (Browser GPS, or *Manual (testing)*) → **Create session**.
2. Open the share link (`http://localhost:5102/?session=…`) or scan the QR on a phone.
3. Sign in as a student → eligibility → location → random live challenge (two photos) → face match → done.
4. Back on the session page: records, map, verification log, analytics, **Export to Excel**, **Close session now**.

Camera and GPS need **HTTPS on phones** (localhost is fine on the laptop itself). Each photo slot also has an
**Upload photo** tab for testing without a camera.

## Tests

```
venv\Scripts\python scripts\smoke_test.py   # end-to-end API flow with real models (41 checks)
venv\Scripts\python -m pytest -q             # original 23 core + Streamlit tests
cd frontend && npm run build                 # production build
```
