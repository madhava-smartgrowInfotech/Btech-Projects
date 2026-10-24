# AgriVision 🌱 — AI Plant Disease Detection (PRD v1.0 MVP)

Flask + Tailwind + vanilla JS. PD36-C 38-class platform with auth, detection,
history, analytics, encyclopedia, CSV/PDF export, REST API, EN/HI/MR toggle.

## Run
```powershell
cd agrivision
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:5000  |  demo: demo@agrivision.ai / demo1234
```

## Structure
```
app.py            Flask app: pages + REST API + SQLite + uploads
disease_db.py     38-class knowledge base (symptoms/treatments/prevention)
inference.py      Hybrid engine: loads models/pd36c.h5|.onnx if present,
                  else calibrated colour/texture heuristic (stable per image)
config.py         Secrets, DB + upload paths
templates/        base, index, login, register, dashboard, detect, result,
                  history, analytics, encyclopedia, disease_detail, profile
static/css|js     Theme, i18n (en/hi/mr), upload UX
```

## Real model
Train/export your PD36-C (224×224, 38 softmax) → save as `models/pd36c.h5`.
It auto-loads on next start (`engine` field in results shows the backend).

## API (PRD §11)
`POST /api/v1/auth/register` · `POST /api/v1/detect/upload` (login) ·
`GET /api/v1/history` · `GET /api/v1/history/<id>` ·
`GET /api/v1/analytics/dashboard` · `GET /api/v1/diseases` · `GET /health`
