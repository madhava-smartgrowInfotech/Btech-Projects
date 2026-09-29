# CareWatch

Privacy-first camera monitoring that recognises daily activities, detects falls in real time and alerts
family instantly. It works with a webcam or an Android phone used as a network camera.

## Features
- **Live monitoring** - YOLO11n-pose finds 17 body keypoints per frame, on CPU.
- **Activity recognition** - walking, standing, sitting, lying, drinking water and picking up objects, with
  a live timeline.
- **Fall detection** - a rapid drop to the floor plus stillness, confirmed over a 3 s window.
- **Low-light robustness** - automatic gamma + CLAHE enhancement, and a model trained on darkened images.
- **Emergency alerts** - an on-screen 'I'm OK' countdown, then Telegram (with a snapshot) and email.
- **Privacy mode** - the live view shows only the skeleton. No video is stored, and a snapshot is saved only
  with an alert.
- **Daily report** - time per activity and long-inactivity warnings.
- **Evaluation** - per-activity accuracy and F1, fall sensitivity and specificity, and alert latency.

## Quick start (Windows)
```bat
setup.bat      :: once: venv, Python packages, npm install
run.bat        :: backend :8208 + frontend :5208, opens the browser
```
**Demo login:** `demo@carewatch.app` / `CareWatch123`

No camera? Start monitoring with the sample video `data\sample\demo_fall.mp4` as the camera source.

> **Alerts:** fill in `TELEGRAM_BOT_TOKEN`, `SMTP_USER` and `SMTP_PASSWORD` in `.env` so alerts can be
> delivered - see [docs/ALERTS_SETUP_WARNING.md](docs/ALERTS_SETUP_WARNING.md).

## Evaluation results
EVAL_RESULTS

## Tech
FastAPI, SQLAlchemy + SQLite, PyJWT + bcrypt, OpenCV, Ultralytics YOLO11n-pose, scikit-learn, React + Vite,
Tailwind CSS, Telegram Bot API, Gmail SMTP.

## Documentation
| Document | Contents |
|---|---|
| [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) | Problem, features, users, screens |
| [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) | Architecture, model, fall logic, data sources and licences, evaluation method, API |
| [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) | Setup, running, demo steps, retraining, smoke test, troubleshooting |
| [docs/ALERTS_SETUP_WARNING.md](docs/ALERTS_SETUP_WARNING.md) | How to turn on Telegram and Gmail delivery |
| [docs/PLAN.md](docs/PLAN.md) | Build plan |

## Project layout
```
backend/app/     FastAPI app - routes/, services/ (pose, features, activity, fall, monitor, alerts)
frontend/src/    React screens (pages/), components/, api.js
ml/              extract_keypoints.py, sequences.py, train.py, eval.py
scripts/         download_data.py, make_demo_video.py, smoke_test.py
data/            datasets (CCTV, fall detection, HAR sample), keypoints, own clips, sample video
models/          yolo11n-pose.pt, activity_rf.joblib
experiments/     metrics.json (training), eval/metrics.json (evaluation)
```
