# How to run - Smart Rider (CSE-A-A6)

Smart Rider Impairment Warning System for Two-Wheelers: the original Tkinter desktop prototype plus a new web
interface (FastAPI backend in `backend/`, React frontend in `frontend/`).

## Quick start (Windows)

1. Install **Python 3.12 or newer** (3.14 is what the pinned packages were tested on; tick "Add Python to PATH") and **Node.js 18+**.
2. Double-click **`run.bat`**. The first run:
   * rebuilds `.venv` if it was copied from another PC (the one shipped in the repo pointed at a missing Python),
   * installs `requirements.txt` and `backend/requirements.txt` (OpenCV, MediaPipe, NumPy, Matplotlib, FastAPI),
   * downloads Google's `face_landmarker.task` (about 3.7 MB) into `models/` if it is missing,
   * installs the frontend packages, then opens the app.
3. The browser opens **http://localhost:5306**. The API runs in its own window on port **8306**
   (interactive API docs: http://127.0.0.1:8306/docs). Ports come from `.env`.
4. Sign in with the **demo account** shown on the login page:
   **`demo@smartrider.app`** / **`Demo@1234`** (override with `DEMO_EMAIL`, `DEMO_PASSWORD`, `AUTH_SECRET` in `.env`; see `.env.example`).

Use **Chrome or Edge** and open the app on `localhost`: browsers only allow webcam access there (or on https).

## Manual start

```bash
py -3.14 -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt -r backend/requirements.txt
python setup_model.py                                              # once
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8306   # terminal 1
cd frontend && npm install && npm run dev                          # terminal 2
```

## The original desktop app still works

```bash
.venv\Scripts\python.exe app.py                # Tkinter window
.venv\Scripts\python.exe app.py --simulation   # starts straight in simulation
```

Both front ends write to the same `data/events.sqlite3` and `data/settings.json`, so history and calibration are shared.

## Using the web app

| Screen | What to do |
|--------|-----------|
| **Monitor** | *Simulation mode* needs no camera: pick a scenario, press *Start monitoring*. *Prolonged eye closure* reaches a warning about 6 s in. For the live path press *Start camera*, allow the browser prompt, *Calibrate* (look forward, eyes open, 8-15 s), then *Start monitoring*. Turn on *Alert sound* for three beeps when a warning fires. |
| **Event history** | Up to 500 logged events, EAR chart (live vs simulation), filters, search and **Export CSV**. |
| **Thresholds** | Six validated rule values. Saving stops monitoring and clears the calibrated flag, exactly like the desktop app. |
| **Research** | Upload a consented, labelled measurement CSV and held-out subject IDs. *Use synthetic sample* loads a generated demo file; any report built from it is flagged **Synthetic data**. |
| **How it works** | Pipeline, formulas, quality gates, limitations, reference, command-line tools. |

Frames from your camera are analysed in memory by the server and are never written to disk.

## Tests

```bash
.venv\Scripts\python.exe -m unittest discover -s tests -v   # 20 original unit tests (core, storage, research)
.venv\Scripts\python.exe smoke_test.py                       # original Tk integration check
.venv\Scripts\python.exe scripts\smoke_test.py               # web API flow in temp storage (34 checks); never touches data/
python scripts\capture_screens.py --video face.y4m           # needs the app running; walks every screen, saves docs/screenshots/*.png
python scripts\check_layout.py                               # needs the app running; 360/768/1440 px, light+dark, overflow, console, labels
```

`capture_screens.py` and `check_layout.py` need Playwright (`pip install playwright` then `playwright install chromium`).
The camera step feeds Chromium's fake webcam with a looping video of one public-domain face photograph; without
`--video` that step is skipped.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Can't reach the Smart Rider server" | The API window is not running or still starting. Wait a few seconds or rerun `run.bat`. |
| Camera permission message | Allow the camera in the address bar and close other apps using the webcam. |
| "Landmark model missing" badge | Run `python setup_model.py` (needs internet once). Simulation works without it. |
| Signal quality stuck on "Poor lighting" / "No face" | Face the camera, light your face from the front, keep both eyes in view. These gates are deliberate: the app will not guess. |
| Port already in use | `netstat -ano \| findstr :5306` then `taskkill /PID <pid> /F`. |
| Signed out unexpectedly | The demo token lasts 12 hours, and changing `AUTH_SECRET` invalidates it. Sign in again. |

## Safety

A camera cannot confirm alcohol consumption. *Normal* does not certify fitness to ride. This is a stationary
demonstration prototype, not a medical device or a road-ready safety system, and it never controls ignition, brakes
or vehicle power.
