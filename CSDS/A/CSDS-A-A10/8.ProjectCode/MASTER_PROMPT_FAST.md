# MASTER PROMPT (FAST BUILD) - CareFlow

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (download script).
> - Optional: Telegram bot token for patient alerts (guided).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **CareFlow** - real-time patient-flow management for hospitals - digital tokens, live queues, bed and ICU visibility and AI wait-time prediction.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8110**, frontend **5110** (`strictPort: true`). Any extra local service uses a port in **11100-11109**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- In-hospital activities such as queues, lab tests and bed checks are handled manually.
- Patients face long, unpredictable waits and confusion between departments.
- Bed and ICU availability is not visible in real time.
- Emergency cases are not prioritised automatically.

**What is needed:** A system that tracks patients and resources in real time and uses AI to reduce waiting and prioritise care.

---

## 3. Who uses it

- Front-desk and registration staff
- Doctors and nurses
- Laboratory and pharmacy staff
- Hospital administrators
- Patients watching their queue position

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Alleviate: An AI-Powered Mobile Application for Personalized Healthcare Management and Doctor Recommendation** - IEEE Access, 2025 - https://doi.org/10.1109/access.2025.3647089

- Alleviate: an AI-powered mobile application for personalised healthcare management (Flutter, Flask, Firebase).
- ML models (Logistic Regression, Random Forest) with NLP for specialist, diet and exercise recommendations; appointment scheduling, prescriptions and a clinic dashboard.
- Doctor verification against the national medical registry and map-based navigation to facilities.

### 4.2 Advanced system (the specification - every point must be met)

- Digital tokens are generated at registration, and patients are tracked across departments.
- Laboratory tests are scheduled automatically to reduce queues.
- Bed and ICU availability is monitored and updated in real time.
- Role-based dashboards serve doctors, nurses, laboratory staff and administrators.
- AI models predict waiting time, prioritise emergencies and recommend bed and ICU allocation.

Objectives the product must meet:

1. Generate digital tokens and manage patient queues automatically.
2. Track patient movement across OPD, laboratory, pharmacy, wards and ICU.
3. Schedule laboratory tests to reduce waiting time.
4. Monitor bed and ICU availability in real time.
5. Predict waiting time and prioritise emergency cases using AI.
6. Provide role-based dashboards for hospital staff and administrators.

### 4.3 Latest approaches
- ML wait-time prediction from queue state and time features.
- Emergency-severity-index style triage scoring for queue priority.
- Real-time dashboards and TV queue displays over WebSockets.
- Bed-management optimisation and predictive occupancy.

### 4.4 What you will build - CareFlow
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Registration and digital tokens** - a QR token per visit, routed to the right department.
- **F2 Live queues** - OPD, laboratory and pharmacy queues updating in real time over WebSockets, with a TV display mode.
- **F3 Patient journey** - a state machine across OPD, lab, pharmacy, ward and ICU with a timeline per patient.
- **F4 Lab scheduling** - test slots allocated by current load.
- **F5 Bed and ICU board** - real-time availability and allocation.
- **F6 AI wait-time and triage** - a wait-time model (trained on CPU) shown on tokens and screens, and a triage score that moves critical patients up the queue.
- **F7 Role dashboards** - registration, doctor, lab, admin views with basic throughput analytics.

### 4.5 Data

- **Healthcare analytics - patient flow data** (Kaggle) - https://www.kaggle.com/datasets/hassanjameelahmed/healthcare-analytics-patient-flow-data -> commit.
- **ER wait time** (Kaggle) - https://www.kaggle.com/datasets/rivalytics/er-wait-time -> commit.
- **Hospital beds management** (Kaggle) - https://www.kaggle.com/datasets/jaderz/hospital-beds-management -> commit.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (role-based)
3. Registration desk
4. Department queue console
5. TV queue display
6. Patient token status
7. Bed and ICU board
8. Admin analytics

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to CareFlow:** FastAPI WebSockets for the live queues, qrcode for the tokens, a seeded arrival simulator so queues move during the demo.
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
1. Registration issues a token -> the patient status page shows the predicted wait.
2. The simulator runs; the OPD queue and TV display update live; an emergency case jumps the queue.
3. The doctor sends the patient to the lab -> slot allocated -> journey timeline updates.
4. Admit to ICU -> bed board updates; admin analytics show throughput and wait-time trends.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Telegram patient alerts and the detailed per-department analytics pages.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
