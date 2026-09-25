# Mosaic

*See every emotion, not just one.*

Mosaic detects both basic (happy, sad, angry, fear, disgust, surprise,
neutral) and compound emotions (e.g. "happily surprised", "sadly angry") from
a single facial image. The classifier is trained on real face data and
augmented with a conditional GAN that synthesizes rare compound-expression
examples — see `backend/README.md` for the full training pipeline.

## Stack

- **Backend** (`backend/`) — FastAPI, SQLite, JWT auth, PyTorch (CNN
  multi-label classifier + conditional GAN), OpenCV face detection.
- **Frontend** (`frontend/`) — Next.js, TypeScript, Tailwind CSS, GSAP, Lenis,
  Framer Motion, Three.js, Recharts.

See `API_CONTRACT.md` for the endpoint reference shared by both.

## Running locally

```bash
# 1. Backend — train once, then serve
cd backend
python -m venv .venv && ./.venv/Scripts/activate
pip install -r requirements.txt
python -m app.ml.run_pipeline      # one-time, real training run
uvicorn app.main:app --reload --port 8000

# 2. Frontend
cd frontend
npm install
npm run dev                         # http://localhost:3000
```
