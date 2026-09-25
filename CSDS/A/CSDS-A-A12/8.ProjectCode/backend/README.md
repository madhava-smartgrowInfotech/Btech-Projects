# SeedIQ API

Backend service for SeedIQ: predicts millet seed germination outcomes from a
seed photo plus soil/crop conditions, and explains each prediction.

## Pipeline

1. **Morphological feature extraction** — OpenCV contour segmentation derives
   shape (area, perimeter, aspect ratio, circularity) and colour traits from
   the seed image.
2. **JEPA image encoder** — a small self-supervised Joint-Embedding
   Predictive Architecture (context encoder / EMA target encoder /
   predictor) learns visual representations from seed imagery without
   requiring germination labels.
3. **Feature fusion** — image embedding + morphological traits + soil
   moisture/temperature/humidity/rainfall/pH/seed variety are concatenated.
4. **XGBoost classifier** — predicts germination probability from the fused
   feature vector.
5. **Explanation engine** — turns XGBoost's per-feature contributions for
   the specific sample into a ranked, natural-language explanation and
   actionable recommendations.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

## Build the model artifacts (one-time)

```bash
python ml/build_pipeline.py
```

This generates the training dataset, pretrains the JEPA encoder, trains the
XGBoost fusion classifier, and writes everything under `artifacts/`
(`encoder.pt`, `classifier.json`, `tabular_scaler.joblib`,
`feature_names.json`, `metrics.json`, `feature_importance.json`).

## Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive docs at `http://localhost:8000/docs`.

## Endpoints

- `POST /api/predict` — multipart form (`image`, `soil_moisture`, `temperature`,
  `humidity`, `rainfall`, `soil_ph`, `seed_type`) -> prediction + explanation.
- `GET /api/history?limit=20` — recent predictions.
- `GET /api/history/{id}` — full stored prediction.
- `DELETE /api/history/{id}`
- `GET /api/stats` — dashboard aggregates + model evaluation metrics.
- `GET /api/model-info` — architecture summary + global feature importances.
- `GET /api/seed-types` — supported seed varieties.
- `GET /api/health`
