# MedFlow — Hospital Patient Flow Intelligence Platform

A full-stack, real-time hospital operations platform: digital token queues, cross-department
patient tracking, lab scheduling, live bed/ICU availability, and AI-assisted triage & wait-time
prediction — with role-based consoles for reception, doctors, nurses, lab staff and admins, plus
a public waiting-room display board.

```
8.ProjectCode/
├── backend/        FastAPI + SQLAlchemy + scikit-learn (Python)
├── frontend/       React + TypeScript + Vite (Tailwind, Framer Motion, GSAP, Three.js)
└── files/          Original project brief documents (not used by the app)
```

## Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite (swap `MEDFLOW_DATABASE_URL` for Postgres in production),
  JWT auth, WebSockets for live updates, scikit-learn for the ML layer.
- **Frontend**: React 19 + TypeScript + Vite, Tailwind CSS v4, Framer Motion, GSAP/ScrollTrigger,
  Lenis smooth scroll, React Three Fiber (3D hero visual), Recharts, Radix UI primitives.
- **ML models** (`backend/app/ml/`): a wait-time regressor (RandomForest) and a triage classifier
  (GradientBoosting) trained on synthetically generated but clinically-plausible data — the triage
  labels come from a NEWS2-style early-warning scoring formula, and the queueing data follows
  standard multi-server waiting-time behaviour. Both retrain automatically on first run.

## Running it locally

### 1. Backend

```bash
cd backend
python -m venv venv
./venv/Scripts/pip install -r requirements.txt      # venv/bin/pip on macOS/Linux
./venv/Scripts/python seed.py                        # creates DB + demo hospital data
./venv/Scripts/python -m uvicorn app.main:app --reload --port 8010
```

The API serves at `http://127.0.0.1:8010`, docs at `/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (Vite defaults to `5173`, falling back to the next free port). The dev
server proxies `/api` and `/ws` to the backend on port `8010` — update `vite.config.ts` if you run
the backend elsewhere.

### 3. Sign in

Use any of the seeded demo accounts (also shown on the login screen):

| Role | Email | Password |
|---|---|---|
| Administrator | admin@medflow.app | Admin@123 |
| Doctor · General Medicine | dr.mehta@medflow.app | Doctor@123 |
| Doctor · Emergency | dr.rao@medflow.app | Doctor@123 |
| Doctor · Pediatrics | dr.verma@medflow.app | Doctor@123 |
| Nurse · Ward | nurse.iyer@medflow.app | Nurse@123 |
| Lab Technician | lab.singh@medflow.app | Lab@123 |
| Reception | reception.kaur@medflow.app | Reception@123 |

The public waiting-room board (no login) is at `/board`.

## Core flow

1. **Reception** registers a patient → a digital token is issued and, if vitals are supplied, an
   AI triage model scores them (critical / urgent / normal) and a wait-time model predicts queue
   time from live department load.
2. **Doctors** pull patients from their department queue (priority-ordered), consult, order lab
   tests, admit to a ward/ICU bed, or discharge.
3. **Lab staff** move ordered tests through scheduled → in progress → completed; results flow back
   onto the patient's visit.
4. **Nurses** see a live bed/ICU board, admit/discharge patients, and clear beds after cleaning.
5. **Admins** get hospital-wide KPIs, department load charts and bed/ICU occupancy — all updating
   in real time over WebSockets.
6. The **waiting-room board** is a public, auto-refreshing display of now-serving tokens per
   department, meant for a waiting-area screen.

## Retraining the ML models

```bash
cd backend
./venv/Scripts/python -m app.ml.train
```

Regenerates `app/ml/artifacts/*.joblib`. Re-run whenever the feature schema in `app/ml/train.py`
changes.
