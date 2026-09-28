# SignBridge - How to run

## Requirements

- Windows 10/11 (macOS / Linux work too, using the manual commands below)
- **Python 3.11+** and **Node.js LTS** (20 or newer) on the PATH
- A webcam and a microphone; Chrome or Edge
- About 3 GB of free disk space (Python packages + the offline speech model)
- Internet **only for setup**; after that SignBridge runs fully offline

## 1. One-time setup

Open the `8.ProjectCode` folder and double-click **`setup.bat`** (or run it in a terminal). It:

1. creates `.env` from `.env.example` if it is missing,
2. creates `venv/` and installs the Python packages from `requirements.txt` (CPU PyTorch included),
3. downloads the offline speech model (faster-whisper `small`, about 480 MB, one time),
4. installs the frontend packages (`frontend/node_modules`).

`.env` settings (defaults are fine):

| Key | Meaning |
|-----|---------|
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Optional. Polishes sentences when online. Without it, offline rules are used. |
| `BACKEND_PORT` / `FRONTEND_PORT` | 8205 / 5205 (fixed) |
| `JWT_SECRET`, `JWT_EXPIRE_HOURS` | Login tokens |
| `WHISPER_MODEL` | `small` (default), `base` or `tiny` for slower computers |

## 2. Start

Double-click **`run.bat`**. It opens two windows (backend on port **8205**, frontend on port **5205**)
and then the browser at **http://localhost:5205**.

**Demo login:** `demo@signbridge.app` / `demo1234` (pre-filled on the sign-in page).

Allow camera and microphone access when the browser asks.

## 3. Try the demo

1. **Conversation** -> *Start camera*. Sit about an arm's length away with your upper body in view.
2. Sign **HELLO**, lower your hands briefly, then sign **HOW ARE YOU**. The signs appear as chips;
   after a ~3 s pause the sentence *"Hello, how are you?"* appears and is spoken aloud.
3. The hearing person presses **Start listening** and speaks. Live subtitles appear in large text
   (works with the network cable unplugged / Wi-Fi off; the header then shows *Offline mode*).
4. The transcript on the right holds both sides. Type a title and press **Save**; open **History** to read or download it.
5. **Performance** shows accuracy, the confusion matrix and latency.

Fingerspelling: switch the camera mode to *Fingerspelling A-Z, 1-9*, hold each letter steady for about a
second; lower your hands for ~1 s to finish the word (useful for names).

## Manual start (any OS)

```bash
# backend (from 8.ProjectCode)
venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8205     # Windows
venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8205         # macOS / Linux
# frontend
cd frontend && npm run dev
```

## Checks

```bash
venv\Scripts\python scripts\smoke_test.py      # with the backend running: drives the whole pipeline
cd frontend && npm run build                    # production build
venv\Scripts\python -m ml.eval                  # re-runs the evaluation -> experiments/eval/metrics.json
```

## Rebuilding data and models (optional)

The landmark datasets and trained models are committed, so this is only needed to reproduce them.

```bash
venv\Scripts\python scripts\download_data.py    # Kaggle downloads via kagglehub -> data/raw/
venv\Scripts\python -m ml.prepare_data          # -> data/*.npz, data/letters_landmarks.csv, data/splits.json
venv\Scripts\python -m ml.train                 # -> models/*.onnx, experiments/train_metrics.json (CPU, minutes)
venv\Scripts\python -m ml.eval
```

On a Kaggle GPU instead: import `notebooks/signbridge_kaggle_train.ipynb`, *Add Data* ->
"Indian Sign Language Mediapipe Holistic Landmarks", *Accelerator: GPU*, *Run All*, then copy
`word_model.onnx`, `word_model.pt`, `labels.json` into `models/`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Cannot reach the SignBridge server" | The backend window must be running; check port 8205 is free. |
| Port 5205 already in use | Close the other program; the port is fixed on purpose (`strictPort`). |
| Camera / microphone blocked | Click the camera icon in the address bar and allow access, then reload. |
| No speech output | Windows needs at least one installed voice (Settings -> Time & language -> Speech). |
| Subtitles slow | Set `WHISPER_MODEL=base` in `.env` and restart the backend. |
| Signs not recognised | Good light, plain background, upper body and both hands in view; lower hands between signs. |
