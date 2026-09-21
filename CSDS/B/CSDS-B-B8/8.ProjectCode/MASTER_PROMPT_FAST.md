# MASTER PROMPT (FAST BUILD) - CareWatch

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (dataset download).
> - A webcam, or an Android phone with the free 'IP Webcam' app (guided).
> - Telegram bot token and the contacts' chat IDs; a Gmail app password (guided).
> - Optional: a volunteer to record a few short activity clips.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **CareWatch** - privacy-first camera monitoring that recognises daily activities, detects falls in real time and alerts family instantly.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8208**, frontend **5208** (`strictPort: true`). Any extra local service uses a port in **12080-12089**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- HAR systems trained on small, controlled datasets fail in real homes.
- Accuracy drops in low light and occlusion.
- Falls go unnoticed when elderly people live alone.
- Existing systems do not send emergency alerts automatically.

**What is needed:** A robust monitoring system that recognises activities, detects falls and alerts caregivers immediately.

---

## 3. Who uses it

- Elderly people living alone
- Family members and caregivers who receive alerts
- Care homes monitoring several rooms

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**WiViHAR: A Deep Learning-Based Human Activity Recognition Method Using WiFi and Vision Multimodal Fusion** - IEEE Transactions on Human-Machine Systems, 2026 - https://doi.org/10.1109/thms.2026.3675889

- WiViHAR: human activity recognition fusing WiFi signals and vision with deep learning.
- Attention-based networks and multimodal fusion keep recognition robust under lighting changes and occlusion.
- Targets smart-home and healthcare monitoring.

### 4.2 Advanced system (the specification - every point must be met)

- A deep-learning model recognises walking, standing, sitting, drinking water and picking up objects from video.
- Training on a larger, diverse dataset improves robustness in low light and occlusion.
- A fall detection module identifies accidental falls in real time.
- Emergency alerts are sent through SMS, email, mobile notifications or alarms.
- The system provides continuous, camera-based monitoring for elderly care and smart homes.

Objectives the product must meet:

1. Recognise daily activities from video using deep learning.
2. Improve robustness in low light and partial occlusion.
3. Detect accidental falls in real time.
4. Send automatic emergency alerts to caregivers and family.
5. Provide continuous monitoring for elderly care and smart homes.
6. Evaluate recognition accuracy and alert latency.

### 4.3 Latest approaches
- Pose-based activity recognition (keypoint sequences with temporal CNN / transformer / graph models): light-robust and privacy-friendly.
- Fast pose estimators (YOLO-pose, MediaPipe Pose) running on CPU.
- Fall detection from pose dynamics plus post-fall inactivity, with confirmation windows to cut false alarms.
- Low-light enhancement and occlusion-aware training.

### 4.4 What you will build - CareWatch
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Live monitoring** - webcam or a phone used as a network camera; body keypoints extracted per frame with a pretrained pose model.
- **F2 Activity recognition** - walking, standing, sitting, lying, drinking water and picking up objects, from a small classifier over keypoint sequences, with a live timeline.
- **F3 Fall detection** - a rapid transition to the floor plus inactivity, with a confirmation window to cut false alarms.
- **F4 Low-light robustness** - CLAHE / gamma enhancement plus darkening augmentation in training, so recognition holds up in dim rooms.
- **F5 Emergency alerts** - Telegram message with a snapshot, an email, and an on-screen 'I'm OK' countdown before the alert is sent.
- **F6 Privacy mode** (NEW) - the live view shows only the skeleton and no video is stored; snapshots are saved only with an alert.
- **F7 Daily report** - time spent per activity and long-inactivity warnings.
- **F8 Evaluation** - per-activity accuracy and F1, fall sensitivity and specificity, and alert latency.

### 4.5 Data

- **CCTV Incident Dataset - Fall & Lying Down** (Kaggle) - https://www.kaggle.com/datasets/simuletic/cctv-incident-dataset-fall-and-lying-down-detection - 163.8 MB, CC BY-NC-SA 4.0 -> commit.
- **Fall Detection Dataset** (Kaggle) - https://www.kaggle.com/datasets/uttejkumarkandagatla/fall-detection-dataset - 50 MB, labelled images -> commit.
- **Human Action Recognition (HAR)** (Kaggle) - https://www.kaggle.com/datasets/meetnagadia/human-action-recognition-har-dataset - 313 MB, 15 actions including drinking and sitting -> commit a sample plus the download script.
- **Own clips** recorded with consent through F9, committed as keypoint files (not raw video).

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Live monitor (skeleton, activity, status)
4. Alerts and acknowledgement
5. Contacts and settings
6. Daily report
7. Model performance

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to CareWatch:** A pretrained pose model (MediaPipe Pose or YOLO11n-pose) for keypoints - no training needed there - plus a small scikit-learn / PyTorch classifier on keypoint sequences that trains on CPU; OpenCV; Telegram Bot API + Gmail SMTP for free alerts.
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
1. The live monitor labels walking, sitting and drinking water in real time, showing only a skeleton.
2. A volunteer lies down on a mat (a simulated fall) -> the countdown appears -> nobody presses 'I'm OK' -> Telegram and email alerts go out with a snapshot.
3. Dim the lights -> recognition continues.
4. The daily report shows time spent per activity and the inactivity warning.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Kaggle GPU training (a pretrained pose model plus a small CPU classifier is enough), multi-camera rooms, escalation to a second contact, and browser push alerts.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
