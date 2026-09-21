# MASTER PROMPT (FAST BUILD) - SignalScout

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - An Android phone (Android 10+) with a SIM card and a USB cable; install Android Studio (guided).
> - Which hardware is available: ESP32, NEO-6M GPS module? (Without it, use the simulator.)
> - Telegram bot token and/or Gmail app password for complaint notifications (guided).
> - Optional: OpenCelliD API key.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **SignalScout** - finds weak and dead mobile-network zones automatically from real phone and sensor readings, points users to better signal and files complaints with technical evidence.

**Goal: a fully working, end-to-end product in the shortest time.** Every feature in section 4.4 must really work with real data and the real model or API - nothing fake. Build only what is in this file. When two approaches both work, **always take the simpler one.**

---

## 1. Rules

1. **One stop only.** Do the Start step (section 8), show a short plan, and wait for **"proceed"**. After that, build straight through to the end without stopping. Don't ask more questions unless you are truly blocked; pick sensible defaults and list them in the final summary.
2. **Real product identity.** Never write anything suggesting coursework or an institution - in code, comments, UI, docs, sample data, file names or commit messages: no "B.Tech", "final year", "major/mini project", "semester", "college/university project", "student batch", "project guide", "supervisor", "viva", "project review", "project submission", "HOD" or academic department names, and no names of people or institutions. Ordinary product words (a hospital department, a moderator review) are fine.
3. **Works end-to-end, nothing fake.** No placeholders, dummy buttons or hard-coded results. Every output comes from the real pipeline. Seed/demo data is allowed only when clearly labelled as sample data.
4. **Speed rules.**
   - Build only the features in section 4.4. No extra features, no animation libraries, no refactoring for elegance.
   - Install only what section 6 lists. Do **not** add LangChain, LlamaIndex or any library not named there.
   - Timebox: if something still fails after 3 attempts, switch to a simpler approach that works and note it in the summary.
   - Testing = one smoke-test script that drives the real API, plus a frontend production build (`npm run build`). No large unit-test suites.
   - Run the backend and frontend in the background while you work; never block on them.
5. **Secrets** live only in `.env` (git-ignored); commit a complete `.env.example` listing every key and where to get it. Never hard-code keys.
6. **Leave `2.ABSTRACT.docx` and `MASTER_PROMPT.md` in this folder untouched**, and don't reference them in the product.
7. **Fixed ports** (other products may run on this PC at the same time): backend **8202**, frontend **5202** (`strictPort: true`). Any extra local service uses a port in **12020-12029**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Weak signals and call drops persist, especially in rural and semi-urban areas.
- Users must notice problems and register complaints manually.
- Complaints lack accurate technical and location details.
- Existing ML studies only predict coverage, without real-time detection or complaint automation.

**What is needed:** An IoT and AI system that monitors signal quality continuously, classifies zones, and registers and tracks complaints automatically.

---

## 3. Who uses it

- Mobile users in rural and semi-urban areas
- Network operators' field engineers and complaint desks
- Local bodies and communities monitoring coverage

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Automated Network Intrusion Detection for Internet of Things: Security Enhancements** - IEEE Access, 2024 - https://doi.org/10.1109/access.2024.3369237

- An automatic machine-learning intrusion detection system for Internet of Things networks.
- Network traffic data is collected and pre-processed, features are selected, and a Random Forest classifier detects malicious activity.
- Shows that lightweight ML on continuously collected IoT network data can monitor a network automatically - the pipeline this product applies to signal quality.

### 4.2 Advanced system (the specification - every point must be met)

- ESP32 acts as the IoT sensing node, collecting RSSI and related measurements through built-in Wi-Fi / Bluetooth.
- An optional GPS module such as NEO-6M adds geographic coordinates to each observation.
- A Python FastAPI AI microservice classifies signal zones and suggests relocation.
- A Spring Boot backend automatically raises complaints for weak or dead zones and manages their lifecycle in PostgreSQL.
- A React dashboard shows coverage heatmaps, complaint status and recommended locations, with offline-first operation.

Objectives the product must meet:

1. Collect RSSI, SINR, latency and GPS data continuously using ESP32 and smartphone APIs.
2. Classify signal zones as Strong, Weak or Dead using machine learning.
3. Recommend nearby locations with better signal.
4. Register complaints automatically for weak or dead zones via SMS gateway or REST API.
5. Track complaints from detection to resolution on a dashboard.
6. Support offline-first operation during power or internet outages.

### 4.3 Latest approaches
- Signal-quality classification from RSRP / RSRQ / SINR using 3GPP-style ranges and ML.
- Spatial interpolation (Gaussian Process regression / kriging) to predict coverage between measured points.
- Crowdsourced drive-test style measurement from phones, with offline-first sync.
- Automatic ticket creation with evidence and closed-loop verification from new readings.

### 4.4 What you will build - SignalScout
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Android field probe** - one screen: start/stop logging; reads RSSI / RSRP / RSRQ / SINR, network type, operator and GPS every few seconds; queues readings offline in Room and syncs when online.
- **F2 Zone classification** - Strong / Weak / Dead per reading and map cell from a Random Forest trained on the public signal datasets, using documented 3GPP-style thresholds.
- **F3 Coverage heatmap** - readings on a Leaflet heat layer, filterable by operator and network type.
- **F4 Better-signal suggestion** - a Gaussian Process predicts signal nearby and points to the closest strong-signal spot.
- **F5 Automatic complaints** - a zone that stays Weak/Dead past a threshold raises a complaint carrying its technical evidence, with a lifecycle from Detected to Resolved.
- **F6 Operator desk** - complaint queue with evidence and status updates, plus a free Telegram/email notice.
- **F7 Offline-first** - readings collected without network sync later, and the dashboard shows what is pending.
- **F8 Analytics** - worst areas, time-of-day patterns and operator comparison.

### 4.5 Data

- **Cellular Network Analysis Dataset** (Kaggle) - https://www.kaggle.com/datasets/suraj520/cellular-network-analysis-dataset - 3 MB, CC0; 3G/4G/5G/LTE signal metrics from Bihar, India -> commit.
- **4G LTE Speed Dataset** (Kaggle) - https://www.kaggle.com/datasets/aeryss/lte-dataset - 18.6 MB, CC BY-SA 4.0; RSRP / RSRQ / SNR / CQI traces with GPS -> commit.
- **Own field readings** collected with the app, committed as an anonymised sample under `data/field/`.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (user, engineer)
3. Android app: live meter + sync status
4. Coverage map
5. My complaints
6. Operator desk
7. Analytics

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to SignalScout:** A minimal Android app in `android/` (Kotlin + Jetpack Compose, one screen, Room for the offline queue) that reads cellular metrics through TelephonyManager plus GPS; scikit-learn (Random Forest + Gaussian Process); Leaflet with a heat layer; Telegram / Gmail for complaint notices. ESP32 firmware only if the user has the board.
- **Training:** The model(s) train **locally on CPU in M1** with small, fast configs (few epochs / a data subset) - accuracy just needs to be good enough to demo, not to top a benchmark. Save the model file plus a `metrics.json` under `experiments/`.

---

## 7. Folder structure

```
8.ProjectCode/
  backend/app/        main.py, db.py, auth.py, routes/, services/
  frontend/src/       pages/, components/, api.js
  ml/                 training / evaluation scripts
  scripts/            smoke_test.py, download_data.py (if a big dataset), generators
  notebooks/          Kaggle notebook (only if training on Kaggle)
  data/               raw or sample data, app.db (git-ignored)
  models/  experiments/   trained model(s) and metrics
  docs/               01_OVERVIEW.md, 02_HOW_IT_WORKS.md, 03_HOW_TO_RUN.md
  setup.bat  run.bat  .env.example  .gitignore  README.md
```

---

## 8. Workflow

**Start (then the only stop)**
1. Check Python, Node.js LTS and Git. Check that `.env` has every key from section 6 (create `.env` from `.env.example` with the user if missing) and that any files/datasets you need are present. If something is missing, give the user 2-3 exact steps to fix it.
2. Write `docs/PLAN.md` (30 lines or fewer: architecture, endpoints, tables, screens, the dataset you will use).
3. Show a 10-line summary and wait for **"proceed"**.

**M1 - Backend and core logic.** Project skeleton, `setup.bat` (venv + pip + `npm install`), backend with login and the database, then the data/model pipeline and every feature endpoint from section 4.4. Train the model(s) here with a small, fast config and save the metrics. `scripts/smoke_test.py` drives the running API through the main flow end-to-end and must pass. Commit and push.

**M2 - Frontend.** The screens in section 5 wired to the API. `run.bat` starts the backend and frontend and opens the browser. Commit and push.

**M3 - Finish.** `ml/eval.py` (or `scripts/eval.py`) produces the evaluation numbers the objectives ask for and saves them to `experiments/eval/metrics.json`. Write the 3 docs and a README (features, quick start, demo login, evaluation results, and a documentation index). Copy `docs/03_HOW_TO_RUN.md` to `../18.FinalCodeExecutionSteps/HOW_TO_RUN.md`. Final check: smoke test passes and `npm run build` succeeds. Commit and push. Give the user a short summary: how to run it, the demo login, and the defaults you chose.

---

## 9. Git rules (other sessions may be committing in sibling folders at the same time)

- From this folder: `git add -A .` then `git commit -m "<3-5 plain words>" -- .` - never a bare `git commit`. No message body, no co-author or AI-attribution lines. Never change git config.
- Push with `git push` (no pull needed). If it is rejected because the remote has newer commits, run `git pull --rebase --autostash` only when `git status` shows nothing outside this folder; otherwise wait a minute and retry.
- On `index.lock` / "another git process": wait 10 seconds and retry. Never delete the lock file.
- Never run `git stash`, `reset`, `checkout`, `restore`, `clean`, `rebase` or `push --force`.
- In M3, name the copied file explicitly: `git add -A . ../18.FinalCodeExecutionSteps/HOW_TO_RUN.md` and `git commit -m "<message>" -- . ../18.FinalCodeExecutionSteps/HOW_TO_RUN.md`.
- `.gitignore`: `venv/`, `node_modules/`, `__pycache__/`, `.env`, `dist/`, `data/app.db`, and `data/raw/` when only a sample is committed.
- A single file over 100 MB (a large model) needs Git LFS: ask the user first, then `git lfs track "<pattern>"` from this folder and commit the `.gitattributes` it creates.

---

## 10. Done when

**Demo (from a fresh `run.bat`):**
1. Install the Android app and walk around: readings appear on the coverage map coloured Strong / Weak / Dead.
2. Stand in a weak spot -> the app points to the nearest strong-signal spot.
3. Stay in a dead zone past the threshold -> a complaint is raised with its technical evidence and a Telegram notice.
4. Turn on airplane mode, collect readings, turn it off -> the queued readings sync.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- ESP32 sensor node as a required part (only if the hardware is on hand), background logging while the app is closed, auto-verification of resolved complaints, and OpenCelliD tower data.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
