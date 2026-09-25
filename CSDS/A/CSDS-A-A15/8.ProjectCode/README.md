# VisionForge AI

Explainable computer-vision platform for industrial surface-defect inspection. A trained
CNN classifies six defect categories, Grad-CAM explains *why*, a rule-based engine maps the
detection to likely root causes and corrective actions, and everything rolls up into a
downloadable PDF report and an analytics dashboard.

## Stack

- **Backend:** FastAPI, SQLAlchemy (SQLite), PyTorch/torchvision (ResNet18 + Grad-CAM), ReportLab
- **Frontend:** React + TypeScript (Vite), Tailwind CSS v4, Framer Motion, GSAP, Lenis, Three.js
  (react-three-fiber), Recharts

## One-time setup

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Prepare the dataset split (already downloaded into backend/data/NEU-CLS)
python -m app.ml.prepare_data

# Train the defect classifier (writes backend/models/*)
python -m app.ml.train

# Create a demo login
python -m app.seed
```

### 2. Frontend

```bash
cd frontend
npm install
```

## Running it

```bash
# terminal 1
cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000

# terminal 2
cd frontend && npm run dev
```

Open http://localhost:5173 — sign in with the seeded demo account
(`demo@visionforge.ai` / `demo1234`) or create a new one.

## Project layout

```
backend/
  app/
    ml/            model, training script, Grad-CAM, inference
    routers/       auth, inspections, reports, analytics
    services/      root-cause engine, PDF report generator
  models/          trained checkpoint + evaluation metrics (generated)
  storage/         uploaded images, heatmaps, generated reports (generated)
frontend/
  src/
    components/    layout, dashboard widgets, ReactBits-style micro-interactions, ui primitives
    pages/         landing, auth, dashboard, inspection detail, history, analytics, catalog
    three/         WebGL hero background
```
