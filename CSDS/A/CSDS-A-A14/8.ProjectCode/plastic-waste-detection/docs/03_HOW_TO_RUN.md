# How to run - PlastiScan

PlastiScan has **two interfaces over the same Python code**:

| Interface | Start | URL |
|---|---|---|
| **New web app** (React + FastAPI) - recommended | `run.bat` | http://localhost:5114 (API on http://127.0.0.1:8114/docs) |
| Original Streamlit app (unchanged) | `streamlit run app.py` | http://localhost:8501 |

Both use the same `src/` modules, the same `models/best.pt` and the same `detection_history.db`.

## Requirements
- Python 3.10+ and Node.js 18+ on PATH.

## One-click start (Windows)
Double-click `run.bat` in this folder. On the first run it
1. creates `.venv` and installs `requirements.txt` + `backend/requirements.txt`,
2. runs `npm install` in `frontend/`,
3. opens two windows (API on **8114**, web app on **5114**) and your browser.

Ports are 8114 (backend) and 5114 (frontend). See `.env.example`. To change them, set `BACKEND_PORT` /
`FRONTEND_PORT` before `run.bat` and edit `frontend/vite.config.js` (`server.port`, proxy target).

## Start the parts by hand
```bash
# 1) API (from this folder)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r backend/requirements.txt
python -m uvicorn backend.main:app --port 8114

# 2) web app (second terminal)
cd frontend
npm install
npm run dev          # http://localhost:5114
npm run build        # production build into frontend/dist
```

## Model weights
No trained weights are bundled. Without `models/best.pt` the API loads the general COCO `yolov8n.pt` (downloaded on
first start, needs internet) and the UI says clearly that it is a placeholder - it will not reliably detect plastic.
To get real detection, put a dataset in `data/` and run:
```bash
python train.py --epochs 50 --img-size 640 --batch-size 16     # writes models/best.pt
python evaluate.py                                              # writes results/eval_summary.json + plots
```
The **Evaluation** screen shows those numbers; until `evaluate.py` has run it shows an empty state.

## API (new, thin layer in `backend/main.py`)
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | API status, device (cpu/cuda), model state |
| POST | `/api/model/reload` | retry loading the model after a failure |
| POST | `/api/detect` | multipart `file`, `conf` (0.1-0.9), `preprocess` -> boxes, scores, annotated image |
| GET / DELETE | `/api/history` | detection history rows / clear history |
| GET | `/api/evaluation` | metrics + plot list from `results/` |
| GET | `/api/evaluation/plots/{name}` | one evaluation plot (whitelisted names) |

## Tests
```bash
python scripts/smoke_test.py      # API smoke test (starts the API itself if it is not running)
cd frontend && npm run build      # frontend compiles
```

## Folder map
```
backend/          FastAPI layer (imports src/, no logic of its own)
frontend/         React app (Vite). src/components = copied design kit V4, src/pages = the screens
src/ pages/ app.py train.py evaluate.py predict.py     original project, untouched
scripts/smoke_test.py   run.bat   .env.example
docs/FRONTEND_PLAN.md   inventory and feature checklist
```
