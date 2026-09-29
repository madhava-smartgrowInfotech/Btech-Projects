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
From `python ml/eval.py` (`experiments/eval/metrics.json`), on windows built only from held-out images. Motion
is added to real extracted poses by the seeded sequence builder.

**Activity recognition** - accuracy (recall) / F1 per activity

| Activity | Normal light | Dim, no enhancement | Dim + CareWatch enhancement | Legs occluded |
|---|---|---|---|---|
| Walking | 98.0 / 97.2 | 99.6 / 98.4 | 99.6 / 98.8 | 98.0 / 95.0 |
| Standing | 90.4 / 87.1 | 85.6 / 85.1 | 84.8 / 83.3 | 62.0 / 66.0 |
| Sitting | 71.2 / 71.9 | 70.0 / 69.6 | 74.0 / 72.0 | 57.6 / 55.1 |
| Lying | 81.2 / 82.5 | 77.6 / 79.8 | 82.8 / 84.0 | 79.2 / 80.3 |
| Drinking water | 76.8 / 78.8 | 79.6 / 79.8 | 76.0 / 79.8 | 78.0 / 79.0 |
| Picking up objects | 100 / 99.4 | 100 / 99.4 | 100 / 99.2 | 100 / 99.2 |
| **Overall accuracy** | **86.3%** | **85.4%** | **86.2%** | **79.1%** |
| Macro F1 | 86.2% | 85.4% | 86.2% | 79.1% |

**Fall detection** - 640 simulated 10 fps sequences built from real poses (80 per scenario)

| Metric | Result |
|---|---|
| Sensitivity (falls caught) | **65.4%** (157 / 240: fast 54/80, slow collapse 57/80, legs hidden 46/80) |
| Specificity (non-falls ignored) | **92.3%** (369 / 400: standing 80/80, walking 80/80, picking up 79/80, sitting down 70/80, sitting then lying back 60/80) |
| Impact -> confirmed fall | mean 4.18 s, median 3.0 s, 95th percentile 9.0 s (3 s confirmation window) |

**Alert latency and speed** (CPU)

| Step | Time |
|---|---|
| Pose model (YOLO11n-pose, 480 px) | 29.6 ms / frame |
| Activity classifier | 12.4 ms / window (pipeline about 24 fps, 7-15 fps live alongside other apps) |
| Impact -> confirmed fall | 4.18 s mean |
| 'I'm OK' countdown | 20 s (configurable 5-300 s) |
| Alert delivery (Telegram + email) | measured on real deliveries once `.env` keys are set; logged per alert on the Alerts screen |
| **Impact -> alert sent** | **about 24.2 s** (confirmation + countdown + delivery) |

The pose model finds the person in 99.2% of normal images, 92.0% of darkened images and 88.4% of darkened +
enhanced images. Enhancement costs a few detections on heavily darkened stills, but recognition on the
people it finds improves (85.4% -> 86.2%). Limitations are listed in
[docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md#limitations).

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
