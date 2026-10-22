# HOW_TO_RUN.md — CareLens AI

The app is a FastAPI backend (**port 8412**) plus a React + Vite frontend (**port 5412**). Ports live in `.env` (`BACKEND_PORT`, `FRONTEND_PORT`).
**Demo login:** `demo@carelens.ai` / `Demo@1234` (created automatically, with sample consultations).

## 1. Prerequisites

- **Python 3.11** (any recent Python 3.10+ works): https://www.python.org/downloads/
  - On Windows, tick "Add python.exe to PATH" during installation.
- **Docker Desktop** (only for Method B): https://www.docker.com/products/docker-desktop/
- **Node.js 18+** (for the React frontend): https://nodejs.org/
- A Windows 10/11 laptop or desktop with ~4 GB free disk (models download on first run) and a browser (Edge/Chrome).

## 2. Method A — Automatic (Recommended)

For zero-coding users:

1. Open File Explorer and locate the project folder (the one containing `run.bat`).
2. Double-click **`run.bat`**.
3. A black command window shows progress: checking Python and Node, creating `.venv` (first time only), installing backend and frontend dependencies, preparing the knowledge base, seeding the demo account, then it opens two server windows (**CareLens API** and **CareLens Web**).
4. Your browser opens automatically at **http://localhost:5412**. If it doesn't, type that address manually.
5. Click **Try the demo login** (or create your own account), then type symptoms (e.g. "I have high fever, headache and body pain") and press Send.
6. Review the response, evidence cards, and history page.
7. To stop: close the two server windows (or press **Ctrl+C** in each).

First startup takes longer (model downloads). Later startups are fast.

## 3. Method B — Docker (legacy single-server UI)

Docker serves only the original server-rendered pages from the backend on port 8000; it does not build the React frontend.

```bat
docker build -t carelens-ai .
docker run -p 127.0.0.1:8000:8000 carelens-ai
```

Open **http://localhost:8000**. Use Method A or C for the full React app.

## 4. Method C — Manual

Windows (Command Prompt), two terminals:

```bat
:: terminal 1 - backend
cd /d D:\path	o\project
python -m venv .venv
.venv\Scriptsctivate.bat
pip install -r requirements.txt
python scripts\prepare_data.py
python scriptsuild_index.py
python scripts\seed_demo.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8412

:: terminal 2 - frontend
cd /d D:\path	o\projectrontend
npm install
npm run dev
```

Linux/macOS: same commands with `source .venv/bin/activate` and forward slashes.

Then open **http://localhost:5412**. The Vite dev server proxies `/api` to the backend on 8412.

Optional checks (app running): `python scripts/smoke_test.py` (API end-to-end) and `python scripts/capture_screens.py` (needs `pip install playwright`; saves screenshots to `docs/screenshots/`).

## 5. Troubleshooting

- **Python not found**: reinstall Python with "Add to PATH" ticked, then reopen the terminal and try again.
- **Windows Defender/SmartScreen warning on run.bat**: click "More info" → "Run anyway" (the file is a local plain-text script you can open in Notepad).
- **Port already in use** (`address already in use`): change `BACKEND_PORT` / `FRONTEND_PORT` in `.env` (and `CARELENS_PORT`), or close the program using ports 8412 / 5412.
- **Browser does not open**: manually visit http://localhost:5412 after both server windows show they are running.
- **Dependency installation failures**: check internet access, then re-run `pip install -r requirements.txt` and read the red error text before closing the window.
- **Model download failures / slow first start**: models (`all-MiniLM-L6-v2`, reranker, Flan-T5) download once from Hugging Face. The app still works offline via built-in fallbacks (TF-IDF retrieval + evidence-based responses) if downloads fail.
- **Docker not running**: start Docker Desktop and wait until it says "Running" before `docker build`/`docker compose up`.
- **Permission/path issues**: keep the project in a path without special characters, avoid OneDrive-locked folders if writes fail, and run the terminal as a normal user (not admin required).
