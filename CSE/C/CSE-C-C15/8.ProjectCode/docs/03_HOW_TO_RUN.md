# 03 - How to run SentinelFlow (React console + Flask API)

SentinelFlow now has two parts that run side by side:

| Part | What | Address |
|---|---|---|
| API | Flask app (`app.py`): detection pipeline, SQLite, REST endpoints | `http://127.0.0.1:8415` |
| Console | React + Vite UI in `frontend/` (design kit V5 "Kinetic Mono") | `http://127.0.0.1:5415` |

The ports live in `.env` (`BACKEND_PORT=8415`, `FRONTEND_PORT=5415`). The Vite dev server proxies `/api` and
`/static/results` to the API, so the browser only ever talks to port 5415. The original server-rendered dashboard is
still served by the API itself at `http://127.0.0.1:8415/`.

## 1. Prerequisites

- Windows 10/11, **Python 3.11 or 3.12** on PATH (tick "Add python.exe to PATH" when installing)
- **Node.js 20 or newer** (includes npm) from https://nodejs.org/
- Optional, live capture only: Npcap (https://npcap.com/) and an Administrator terminal. Simulation mode needs neither.

## 2. One-click start

Double-click **`run.bat`**. It:

1. creates `.env` with the default ports if it is missing;
2. creates `.venv` (or rebuilds it if it points at a Python that no longer exists) and installs `requirements.txt`;
3. trains the Random Forest if `models/sentinelflow_rf.joblib` is missing;
4. runs `npm install` in `frontend/` on the first run;
5. starts the API in a minimised window ("SentinelFlow API") and the React UI in the main window, then opens
   `http://127.0.0.1:5415/`.

`run.bat check` performs steps 1-4 and exits without starting anything (handy for a first-time install).

To stop: press Ctrl+C in the main window and close the "SentinelFlow API" window.

## 3. Signing in

The product runs on localhost only and has no user database, so the console uses a demo sign-in gate:

```
email:    demo@sentinelflow.com
password: Demo@1234
```

The login page has a "Fill demo credentials" button.

## 4. Using the console

1. **Overview** - choose an interface and a window, then **Start simulation** (works everywhere; synthetic traffic scored by
   the real model, always labelled as simulation) or **Start live** (needs Npcap + Administrator). **Stop** ends either.
2. **Detections** - every scored window; click **Inspect** for the full threat detail.
3. **Analytics**, **Network health**, **Mitigation**, **Model**, **Settings** - see `docs/FRONTEND_PLAN.md` for the screen map.
4. Keyboard: `/` opens search, `g` then `o`/`d`/`a`/`n`/`m`/`p`/`s` jumps between screens, `g l` opens the activity log,
   `?` lists shortcuts, `Esc` closes any overlay. The sun/moon button toggles dark mode (remembered in the browser).

## 5. Manual start (two terminals)

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python ml\train_model.py        (only if models\ is empty)
python app.py                   (terminal 1: API on 8415)

cd frontend
npm install
npm run dev                     (terminal 2: UI on 5415)
```

Production-style build: `cd frontend && npm run build && npm run preview` (also served on 5415).

## 6. Checks

With both servers running:

```text
python scripts\smoke_test.py        API + proxy checks (27 assertions)
python scripts\capture_screens.py   signs in, starts a simulation, saves docs\screenshots\*.png, reports console errors
```

## 7. Docker

`docker build -t sentinelflow .` / `run-docker.bat` still serve the original dashboard on port 5000 inside the container
(`BACKEND_HOST` / `BACKEND_PORT` are set in the Dockerfile). The React console is a local-development front end and is not part of the image.

## 8. Troubleshooting

- **UI shows "Backend unreachable":** the API window is not running. Start it (`python app.py`) or re-run `run.bat`.
- **Port already in use:** change `BACKEND_PORT` / `FRONTEND_PORT` in `.env` and restart both servers. The UI reads the same file.
- **Live capture will not start:** the UI shows the exact backend reason. Run as Administrator with Npcap installed, or use simulation.
- **`npm install` fails:** check the internet connection and that `node --version` is 20 or newer, then re-run `run.bat`.
- **Model metrics say "synthetic":** CICIDS2017 could not be downloaded at training time, so a labelled synthetic dataset was used.
  The Model screen says so; retrain on real captures before relying on the numbers.
