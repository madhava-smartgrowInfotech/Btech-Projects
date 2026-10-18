# How to run - SignSpeak (CSE-A-A16)

## Quick start (Windows)

1. Install **Python 3.10 or 3.11** (tick "Add Python to PATH") and **Node.js 18+**.
2. Double-click **`run.bat`**. First run creates `.venv`, installs the Python packages (TensorFlow is large - allow several
   minutes) and the frontend packages, then opens the app.
3. The browser opens **http://localhost:5316**. The API runs in its own window on port **8316**
   (API docs: http://127.0.0.1:8316/docs). Ports come from `.env`.

Use **Chrome or Edge** and open the app on `localhost` - the browser only allows webcam access there (or on https).

## Manual start

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8316    # terminal 1
cd frontend && npm install && npm run dev                           # terminal 2
```

The original desktop app still works: `python run.py`.

## First use

The repo ships **no dataset and no trained model**. Either:

* **Collect** - open *Collect data*, start the camera, pick a letter, capture one image or a burst (150-250 per class is a
  good target), or
* **Import a dataset** - drop images into `data/<CLASS>/` (classes `A`-`Z`, `space`, `del`, `nothing`). The public Kaggle
  "ASL Alphabet" dataset uses exactly these folder names.

Then open *Train model* (at least 2 classes needed), and *Recognize* when it finishes.
The model is saved to `models/` (`asl_cnn_model.keras`, `labels.json`, `classification_report.txt`, `training_history.json`,
`confusion_matrix.json`).

## Tests

```bash
python scripts/smoke_test.py          # API flow on synthetic frames, in a temp copy (never touches data/ or models/)
python scripts/capture_screens.py     # needs the app running; writes docs/screenshots/*.png
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Can't reach the SignSpeak server" | The API window is not running or still loading TensorFlow - wait ~20 s or rerun `run.bat`. |
| Camera permission message | Allow the camera in the address bar. Close other apps using the webcam. |
| Port already in use | `netstat -ano \| findstr :5316` then `taskkill /PID <pid> /F`. |
| "No trained model" on Recognize | Train one first (Train model screen). |
| Speak does nothing | The server voice (pyttsx3) plays on this PC's speakers; if it fails the browser voice is used. |
