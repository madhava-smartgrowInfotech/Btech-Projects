# How to run PneumoDetect

The project has two front ends over the same Python code:

| | Stack | Port | Start with |
|---|---|---|---|
| **New UI** (recommended) | React + Vite, talking to a FastAPI layer | UI **5312**, API **8312** | `run.bat` |
| Original UI | Flask + Jinja templates | 5000 | `run.bat flask` or `python app.py` |

Both use the same model code, the same SQLite file (`pneumonia_app.db`) and the same `static/uploads` and `static/heatmaps` folders.

## Requirements

- Windows, Python 3.10 or 3.11 on PATH
- Node.js 18 or newer on PATH
- About 2 GB of disk for the Python environment (TensorFlow)

## One-click start

Double-click `run.bat` (or run it from a terminal in this folder). It will:

1. create `.venv` and install `requirements.txt` + `requirements-api.txt` (first run only, several minutes)
2. run `npm install` in `frontend/` (first run only)
3. open two windows, **PneumoDetect API** and **PneumoDetect UI**, and launch the browser at http://localhost:5312

Stop everything with `stop.bat` or by closing the two windows.

**Demo login:** `demo@pneumodetect.ai` / `Pneumo@123` (also shown, with a fill button, on the sign-in page).

## Ports and settings

`.env` in this folder (copy `.env.example` if it is missing):

```
BACKEND_PORT=8312
FRONTEND_PORT=5312
DEMO_EMAIL=demo@pneumodetect.ai
DEMO_PASSWORD=Pneumo@123
SESSION_SECRET=change-me-for-any-real-deployment
```

`run.bat` and `frontend/vite.config.js` both read the ports from it. `.env` is git-ignored, `.env.example` is committed.

## Manual start (two terminals)

```
# terminal 1, project root
.venv\Scripts\python -m uvicorn backend.main:api --port 8312

# terminal 2
cd frontend
npm install
npm run dev
```

API docs: http://localhost:8312/docs

## Demo mode and a trained model

Trained weights ship in `saved_models/` (`pneumonia_model.h5` and `class_indices.json`, the custom CNN from experiment `exp02_custom_cnn_tuned`), so every screen shows the **Trained model** badge. Delete those two files and the app falls back to an untrained network and the **Demo model** badge.

To reproduce the weights, download the Kermany chest X-ray set (CC BY 4.0) and run

```
python scripts\train_experiment.py --data_root <path to chest_xray> --name exp02_custom_cnn_tuned ^
    --lr 3e-4 --epochs 40 --patience 10 --reduce_patience 3 --export_model saved_models
```

then restart the API. Results of every run are in `experiments\<name>\metrics.json`.

## Tests and tooling

With the stack running:

```
python scripts\smoke_test.py        # API: login, upload validation, predict, history, delete
python scripts\capture_screens.py   # walks every screen, writes docs\screenshots\*.png, fails on console errors
python scripts\verify_ui.py         # 360/768/1440 px, light/dark, keyboard, reduced motion
python scripts\reset_demo_data.py   # clears history and uploaded images
```

The screenshot and verify scripts need `pip install playwright` and `playwright install chromium`.
`dataset_sample/` holds four public-domain chest X-rays (see its README) that the scripts upload.

## Production build

```
cd frontend
npm run build      # output in frontend/dist
```

## Troubleshooting

- **"The API is not reachable"** in the UI: the API window is not running or is still loading TensorFlow (about 20 seconds on first start). Check the **PneumoDetect API** window.
- **Port already in use:** change the ports in `.env` and start again.
- **`ModuleNotFoundError: cv2`** when running without `run.bat`: `pip install -r requirements.txt -r requirements-api.txt` into the Python you are using.
- The `venv/` folder that came with the repo was created on another machine; ignore it. `run.bat` uses `.venv`.
