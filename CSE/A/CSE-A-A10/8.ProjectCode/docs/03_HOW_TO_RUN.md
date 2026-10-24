# How to run FlowSense

FlowSense has two front doors over the same simulation engine (`smart_traffic/`):

| | What | Port | Start |
|---|---|---|---|
| **Web app (new)** | React UI (`frontend/`) + FastAPI (`backend/`) | UI **5310**, API **8310** | `run.bat` |
| Streamlit app (original, unchanged) | `app.py` | 8501 | `streamlit run app.py` |

## One-click start (Windows)

1. Install **Python 3.10+** (tick *Add to PATH*) and **Node.js 20+**.
2. Double-click **`run.bat`**.
   - First run only: it creates `.venv`, installs `backend/requirements.txt`, installs YOLOv8
     (`backend/requirements-yolo.txt`: ultralytics + PyTorch, a few minutes) and runs `npm install` in `frontend/`.
   - It opens two minimised windows (*FlowSense API*, *FlowSense Web*) and your browser at <http://localhost:5310>.
3. Sign in with the **demo account** shown on the sign-in page (`operator@flowsense.app` / `Flow@1234`, set in `.env`).

`run.bat nobrowser` starts everything without opening the browser. Close the two *FlowSense* windows to stop.
If the YOLOv8 install fails (offline, disk full) everything except the YOLOv8 modes of the Vision page still works.

## By hand

```
python -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements.txt -r backend\requirements-yolo.txt
.venv\Scripts\python -m uvicorn backend.main:app --port 8310        # API (run from this folder)

cd frontend
npm install
npm run dev                                                        # UI on http://localhost:5310
npm run build                                                      # production build in frontend/dist
```

## Settings (`.env`)

| Key | Default | Meaning |
|---|---|---|
| `BACKEND_PORT` / `FRONTEND_PORT` | 8310 / 5310 | fixed so several products can run side by side |
| `DEMO_EMAIL` / `DEMO_PASSWORD` | `operator@flowsense.app` / `Flow@1234` | the demo operator account |
| `JWT_SECRET` | built-in dev key if missing or a placeholder | signs the sign-in token (use 32+ random characters) |

## Checks

With the app running:

```
python scripts/smoke_test.py       # drives every API endpoint end to end (live sim, benchmark, vision, prediction, violations)
python scripts/check_ui.py         # real-browser checks: 360/768/1440 px, light/dark, keyboard, drawer, reduced motion
python scripts/capture_screens.py  # walks every screen with real data and saves docs/screenshots/*.png
```

The two browser scripts need `pip install playwright` and the Chrome that is already installed
(set `CHANNEL=` to empty and run `playwright install chromium` to use the bundled Chromium instead).

## Notes

- The **prediction model trains once at every API start** (about 10 s, in the background). The UI shows a
  "training" state and the *Prediction* page waits for it; benchmark runs with *ML forecast* on wait too.
- The live simulation is **one shared simulation** held by the API process. Restarting the API starts a fresh one.
- `yolov8n.pt` (the YOLOv8 nano weights) sits in the project root and is loaded from there; if it is missing
  ultralytics downloads it on first use (needs internet).
- On Windows PyTorch must be imported before scikit-learn / OpenCV, otherwise its DLLs fail to load;
  `backend/main.py` does that for you.
