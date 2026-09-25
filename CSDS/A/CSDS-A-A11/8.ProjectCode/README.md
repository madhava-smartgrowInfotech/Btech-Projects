# Nuvara

Nuvara is a modern object-design storefront with a real intelligence layer underneath it: a
multi-agent recommender, a digital twin simulation lab that tests strategies before they go
live, explainable-AI breakdowns for every recommendation, a self-learning feedback loop, and a
live traffic/load control center.

The repo has two independent services:

```
backend/    FastAPI service — catalog, multi-agent recommender, digital twin, feedback engine,
            traffic simulation. Python 3.10+, SQLite.
frontend/   React + TypeScript + Vite storefront and the "Nuvara Intelligence" console.
```

Everything under `backend/` and `frontend/` is real, runnable code — no hardcoded numbers. The
recommender is genuine cosine similarity / TF-IDF / weighted scoring; the digital twin runs an
actual simulated population; the feedback loop actually updates the live weights; the traffic
console drives a real queueing model and streams it over a WebSocket.

## Run it

Two terminals, both services independent.

**Backend**
```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
First boot seeds the SQLite database (a few seconds). API docs at `http://localhost:8000/docs`,
WebSocket at `ws://localhost:8000/ws/traffic`.

**Frontend**
```bash
cd frontend
npm install
npm run dev
```
Serves at `http://localhost:5173`. It reads `VITE_API_BASE_URL` (defaults to
`http://localhost:8000/api`) and `VITE_WS_URL` (defaults to `ws://localhost:8000/ws/traffic`) —
see `frontend/.env.example`. You only need a `frontend/.env` file if you're running the backend
on a non-default port.

If port 8000 or 5173 is already taken on your machine, pass a different port to either command
(`--port 8001`, `npm run dev -- --port 5174`) and update `frontend/.env` to match — the backend's
CORS allow-list in `backend/app/config.py` already includes both `5173` and `5174`; add another
entry there if you pick a different frontend port.

## What to look at

- `/` — storefront home, personalized "Recommended for you" rail, persona switcher in the header
  (switching persona visibly changes the recommendations — that's the personalization engine
  running live).
- `/product/:slug` — "Why this?" opens the explainability drawer with the real per-agent score
  breakdown behind that specific recommendation.
- `/intelligence` — the ops console:
  - **Digital Twin Lab** — set candidate agent weights, run a simulation against the full
    synthetic shopper population, see baseline-vs-candidate lift and a deploy/hold/reject verdict.
  - **Feedback / Learning** — the live agent weights and how they've drifted from real feedback.
  - **Traffic Control Center** — live RPS/latency/queue/cache metrics over a WebSocket; trigger a
    `flash_sale` or `spike` load profile and watch the autoscaler react in real time.

See `backend/README.md` and `frontend/README.md` for the full architecture writeups, and
`API_CONTRACT.md` for the complete route reference both sides were built against.
