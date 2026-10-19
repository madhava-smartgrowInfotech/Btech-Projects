# StoryVox — HOW TO RUN

Follow these steps exactly. You only need **one** method (A, B, or C).

## 1. Prerequisites

- **Python 3.11 or newer** (Method A and C). Download: https://www.python.org/downloads/
- **Node.js 20 or newer** (Method A and C) for the web app. Download: https://nodejs.org/
- **Git** is not required (you already have the StoryVox folder).
- **Docker Desktop** is required only for Method B. Download: https://www.docker.com/products/docker-desktop/
- **Disk/RAM:** at least 8 GB free disk (model weights download on first run) and 8 GB RAM recommended. CPU-only machines work but are slower.
- **Internet:** required on the first run to download story/voice models and Python packages. Later runs work offline with cached models.

Check Python and Node (open Command Prompt or PowerShell and run):

```text
python --version
node --version
```

You should see something like `Python 3.11.x`. If not, install Python and tick “Add python.exe to PATH” during setup.

## 2. Method A — Automatic (recommended)

For someone with zero coding knowledge.

1. Open the **StoryVox** folder (the one containing `run.bat`).
2. **Double-click `run.bat`**. It creates a `.venv` folder (first time only, and rebuilds it if it was copied from another computer), installs the Python packages and the web app packages, then opens **two windows**:
   - **StoryVox API** (the FastAPI server on port **8402**)
   - the **web app** (Vite on port **5402**), which also opens in your browser
   Keep both open. The **first run downloads ML models**, so it can take 10–30+ minutes depending on internet speed. Later runs are fast.
3. Your browser opens **http://localhost:5402**. If not, type that address manually.
4. To use StoryVox: open the **Studio**, enter a story idea, pick a language, press **Generate story**, then play/download the narration. **History** lists past stories and **Evaluation** shows measured metrics.
5. To stop: press **Ctrl+C** in each window, or just close them.

## 3. Method B — Docker

Recommended if Docker Desktop is installed. Open a terminal in the StoryVox folder and copy-paste:

```bash
docker build -t storyvox:latest .
docker run --rm -p 127.0.0.1:8402:8402 -v "%cd%/data:/app/data" storyvox:latest
```

(On macOS/Linux use `$(pwd)/data:/app/data` instead of `%cd%/data:/app/data`.)

Then open **http://localhost:8402** (the image contains the built web app, so one port serves everything).

Stop the container with **Ctrl+C**. Alternatively double-click `run-docker.bat`, which does the same build + run steps and pauses so you can read errors.

## 4. Method C — Manual

Exact copy-paste commands. Open **two** terminals in the StoryVox folder.

Terminal 1, the API (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8402
```

Terminal 1 on Command Prompt: use `.venv\Scriptsctivate.bat` instead of the Activate.ps1 line. On macOS / Linux: `python3 -m venv .venv`, `source .venv/bin/activate`, then the same pip and uvicorn lines.

Terminal 2, the web app (all systems):

```bash
cd frontend
npm install
npm run dev
```

Then open **http://localhost:5402**. The dev server forwards `/api` to the API on 8402. Stop each terminal with **Ctrl+C**.

**Single-port alternative:** run `npm run build` inside `frontend`, then start only the API. It serves the built app at **http://localhost:8402**.

Optional checks (with the app running): `python scripts/smoke_test.py` and, to regenerate documentation screenshots, `pip install playwright` then `python scripts/capture_screens.py`.

## 5. Troubleshooting

- **“Python not found” / `python` not recognized:** install Python from https://www.python.org/downloads/ and tick “Add python.exe to PATH”. Close and reopen the terminal, then run `python --version`.
- **Windows Defender / SmartScreen blocks `run.bat`:** click **More info → Run anyway**. The file is a plain text launcher; right-click → Edit to inspect it.
- **Port already in use (8402 or 5402):** another program uses the port. Stop it, or set `PORT_OVERRIDE` for the API, or change `FRONTEND_PORT` in `.env` and `PORT` to match the API.
- **Browser did not open automatically:** manually visit **http://localhost:5402**.
- **Dependency install fails:** update pip (`python -m pip install --upgrade pip`), check internet/VPN, then retry `pip install -r requirements.txt`. Delete `.venv` and retry if the environment is corrupted.
- **Model download fails / slow:** check internet and disk space; rerun — Hugging Face downloads resume from cache. CPU-only users can keep the default small `Qwen/Qwen3-0.6B` model.
- **Insufficient RAM / process killed:** close other apps, use Short length, avoid running evaluation and generation at the same time.
- **CUDA/GPU unavailable:** normal on most laptops — StoryVox runs on CPU automatically (slower). No action needed.
- **“Narration could not be generated”:** the speech checkpoint may still be downloading; wait a minute and retry. Check the server window for the exact error.
- **Missing audio files:** if a WAV was manually deleted, History shows “no audio” — regenerate narration from the story page.
- **The web app says "API offline":** the StoryVox API window is not running or crashed. Start it again (run.bat) and press Retry.
- **“Node.js was not found”:** install Node.js 20+ from https://nodejs.org/ and run run.bat again.
