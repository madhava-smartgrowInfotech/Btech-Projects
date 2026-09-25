# CropSight

AI-based crop quality grading, price intelligence and smart delivery — a full-stack agtech platform connecting farmers, buyers and distributors.

- **Quality grading**: real computer-vision features (color, texture, edges, blemishes, size) extracted from an uploaded crop photo, classified A/B/C/Reject by a trained Random Forest, explained with SHAP.
- **Price intelligence**: a Gradient Boosted Regression model trained on a synthetic-but-realistic multi-year market dataset (seasonality, weather, demand/supply, quality premium), serving a current price + 30-day forecast with a confidence band and a "best day to sell" recommendation.
- **Delivery planning**: a transparent scoring engine ranks buyers/routes by price, distance, reliability and spoilage risk.
- **Live monitoring**: a simulated IoT sensor stream (temperature/humidity/shock) over WebSocket for shipments in transit, with anomaly alerts.
- **Marketplace**: farmer → buyer → distributor order lifecycle (placed → confirmed → in transit → delivered), role-gated at every transition.
- **Model transparency**: an admin "model insights" panel shows each model's algorithm, accuracy, global feature importance and a plain-language note on what it was trained on.

No real crop-image or market-price dataset was available for this project, so both ML models are trained on **synthetically generated but realistic datasets** (see `backend/app/ml/*/generate_dataset.py`), then genuinely trained with scikit-learn and served with real inference — this is disclosed honestly in the app's own admin panel rather than hidden.

## Stack

- **Backend**: Python, FastAPI, SQLAlchemy (SQLite), scikit-learn, SHAP, OpenCV + scikit-image, JWT auth.
- **Frontend**: React 19 + TypeScript + Vite, Tailwind CSS v4, Framer Motion, GSAP + ScrollTrigger, Lenis (smooth scroll), Three.js via React Three Fiber, Recharts, Zustand, React Router.

## Project structure

```
backend/    FastAPI app, ML pipelines (backend/app/ml), SQLite DB, seed script
frontend/   Vite + React app
file/       original project brief documents (not part of the running app)
```

## Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# train both models (writes .joblib artifacts to app/data/)
python -m app.ml.quality.train_model
python -m app.ml.price.train_model

# seed demo accounts, towns and a sample listing
python scripts/seed_db.py

# run the API
python -m uvicorn app.main:app --port 8000
```

The API is served at `http://127.0.0.1:8000` (docs at `/docs`).

> Note: don't run uvicorn with `--reload` on Windows in this setup — it was observed to leave orphaned worker processes holding the port with stale code after a reload. Just restart the process manually after backend edits.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server runs at `http://127.0.0.1:5190` (fixed port, see `vite.config.ts`) and proxies `/api`, `/uploads` and `/ws` to the backend on port 8000.

If `127.0.0.1:5190` is already in use by something else on your machine, change the port in `frontend/vite.config.ts` (`server.port`).

### Demo accounts

All seeded accounts use the password `cropsight123`:

| Role | Email |
|---|---|
| Farmer | farmer@cropsight.dev |
| Buyer | buyer1@cropsight.dev (also buyer2/3/4) |
| Distributor | distributor@cropsight.dev |
| Admin | admin@cropsight.dev |

### Try the golden path

1. Log in as the farmer, drag in any crop photo, grade it.
2. Forecast its price and plan delivery from the listing workspace, then publish it to the marketplace.
3. Log in as a buyer, find the listing in the marketplace, place an order.
4. Log in as the farmer again and confirm the order.
5. Log in as the distributor, start transit (opens live IoT monitoring), then mark it delivered.
6. Log in as the admin to see platform KPIs and both models' transparency cards.

## Re-training the models

Both `train_model.py` scripts regenerate their dataset if `app/data/*.csv` doesn't exist yet, then always retrain and overwrite the `.joblib` artifact. Delete the CSVs in `backend/app/data/` if you want a fresh synthetic dataset.
