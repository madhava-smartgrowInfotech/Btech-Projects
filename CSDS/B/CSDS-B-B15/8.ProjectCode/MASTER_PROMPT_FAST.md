# MASTER PROMPT (FAST BUILD) - MediQueue

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (download script).
> - Gemini API key (free-text symptoms) - https://aistudio.google.com/apikey
> - An Android phone for the patient flow; install `cloudflared` (guided).
> - Optional: Telegram bot token for notifications.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **MediQueue** - district-wide outpatient booking that prioritises by severity, spreads patients across hospitals and shows a live queue position with waiting time.

**Goal: a fully working, end-to-end product in the shortest time.** Every feature in section 4.4 must really work with real data and the real model or API - nothing fake. Build only what is in this file. When two approaches both work, **always take the simpler one.**

---

## 1. Rules

1. **One stop only.** Do the Start step (section 8), show a short plan, and wait for **"proceed"**. After that, build straight through to the end without stopping. Don't ask more questions unless you are truly blocked; pick sensible defaults and list them in the final summary.
2. **Real product identity.** Never write anything suggesting coursework or an institution - in code, comments, UI, docs, sample data, file names or commit messages: no "B.Tech", "final year", "major/mini project", "semester", "college/university project", "student batch", "project guide", "supervisor", "viva", "project review", "project submission", "HOD" or academic department names, and no names of people or institutions. Ordinary product words (a hospital department, a moderator review) are fine. (This is a clinical decision-support product: every AI result is shown as an aid for a qualified professional, with a short disclaimer, never as a final diagnosis.)
3. **Works end-to-end, nothing fake.** No placeholders, dummy buttons or hard-coded results. Every output comes from the real pipeline. Seed/demo data is allowed only when clearly labelled as sample data.
4. **Speed rules.**
   - Build only the features in section 4.4. No extra features, no animation libraries, no refactoring for elegance.
   - Install only what section 6 lists. Do **not** add LangChain, LlamaIndex or any library not named there.
   - Timebox: if something still fails after 3 attempts, switch to a simpler approach that works and note it in the summary.
   - Testing = one smoke-test script that drives the real API, plus a frontend production build (`npm run build`). No large unit-test suites.
   - Run the backend and frontend in the background while you work; never block on them.
5. **Secrets** live only in `.env` (git-ignored); commit a complete `.env.example` listing every key and where to get it. Never hard-code keys.
6. **Leave `2.ABSTRACT.docx` and `MASTER_PROMPT.md` in this folder untouched**, and don't reference them in the product.
7. **Fixed ports** (other products may run on this PC at the same time): backend **8215**, frontend **5215** (`strictPort: true`). Any extra local service uses a port in **12150-12159**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- OP registration involves long queues and overcrowding.
- Limited daily slots leave many patients without a same-day consultation.
- Critical cases are not prioritised.
- Coordination and referrals between hospitals are slow.

**What is needed:** An intelligent booking system that prioritises by severity, spreads load across hospitals and keeps patients informed in real time.

---

## 3. Who uses it

- Patients booking outpatient visits from their phones
- Hospital OP desk staff and doctors
- District health administrators
- Referral coordinators

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Smart Medical Appointment Scheduling: Optimization, Machine Learning, and Overbooking to Enhance Resource Utilization** - IEEE Access, 2024 - https://doi.org/10.1109/access.2024.3349953

- Smart medical appointment scheduling with an integer linear programming model for slot optimisation.
- Machine learning predicts each patient's attendance (no-shows).
- A controlled overbooking strategy improves resource utilisation.

### 4.2 Advanced system (the specification - every point must be met)

- Patients book OP appointments online at hospitals within their district.
- Hospitals configure daily OP limits and emergency quotas, with automatic next-day scheduling.
- AI classifies symptom severity as mild, moderate, severe or critical.
- Hospitals are recommended by severity, location, specialty and availability.
- Secure inter-hospital referrals and dynamic queue positions with estimated waiting times.

Objectives the product must meet:

1. Enable online OP booking across hospitals in a district.
2. Manage daily OP limits and emergency quotas automatically.
3. Classify disease severity from symptoms using AI.
4. Recommend suitable hospitals by severity, location and specialty.
5. Provide dynamic queue positions and waiting-time estimates.
6. Support secure inter-hospital referrals and record sharing.

### 4.3 Latest approaches
- No-show prediction with calibrated overbooking.
- Symptom-based triage with red-flag rules and LLM symptom intake.
- Real-time queue updates and waiting-time prediction.
- Load balancing across a network of facilities and digital referrals.

### 4.4 What you will build - MediQueue
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 District hospital network** - Hyderabad hospitals from OpenStreetMap with specialties, daily OP limits and emergency quotas (seeded, editable).
- **F2 Patient booking** - pick symptoms (or type them, mapped by Gemini), location and date -> severity -> ranked hospital suggestions -> booking with a token.
- **F3 Severity classification** - mild / moderate / severe / critical from a symptom model plus severity weights and red-flag rules; critical cases get emergency advice and the emergency quota.
- **F4 Limits, quotas and overflow** - daily OP limits with automatic next-day scheduling when a day is full, and slot allocation that accounts for predicted no-shows.
- **F5 Live queue position** - position and estimated wait updating in real time as patients are called or emergencies inserted.
- **F6 Hospital console** - today's queue, call next, mark no-show, add emergency.
- **F7 Referrals** - a doctor refers a patient to another hospital with a consented summary, tracked to completion.
- **F8 District dashboard** - load across hospitals, waiting times and severity mix.

### 4.5 Data

- **Disease Symptom Prediction** (Kaggle) - https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset - CC BY-SA 4.0, includes Symptom-severity.csv -> commit.
- **Doctor's Specialty Recommendation** (Kaggle) - https://www.kaggle.com/datasets/ebrahimelgazar/doctor-specialist-recommendation-system - CC BY-SA 4.0 -> commit.
- **Medical Appointment No Shows** (Kaggle) - https://www.kaggle.com/datasets/joniarroba/noshowappointments - 10.2 MB, CC BY-NC-SA 4.0 -> commit.
- **Hyderabad hospitals** from OpenStreetMap (ODbL, attribute OpenStreetMap contributors) -> cached CSV committed.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (patient, hospital staff, district admin)
3. Book a visit (symptoms, hospitals on map)
4. My token (live position)
5. Hospital console
6. Referrals
7. District dashboard

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to MediQueue:** Leaflet + OpenStreetMap with a one-time Overpass fetch of Hyderabad hospitals (cached and committed), FastAPI WebSockets for the live queue, PuLP or OR-Tools for slot allocation, Gemini for free-text symptom mapping. Cloudflare quick tunnel for HTTPS on the phone.
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

**M2 - Frontend.** The screens in section 5 wired to the API. `run.bat` starts the backend and frontend and opens the browser. Then set up phone access: install Cloudflare's free quick tunnel (`winget install --id Cloudflare.cloudflared`), make the Vite dev server accept the tunnel host and proxy `/api` (and WebSockets) to the backend, and add a `run_phone.bat` that starts everything plus the tunnel and prints the `https://...trycloudflare.com` link. No account is needed. Commit and push.

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
1. On a phone, a patient enters 'fever, cough, breathlessness' -> 'Severe' -> 3 Hyderabad hospitals suggested on the map -> books token 14 (about 35 min).
2. The hospital console calls next and inserts an emergency -> the patient's position and wait update live.
3. A full day pushes new bookings to the next day automatically.
4. The doctor refers the patient to a pulmonology hospital; the district dashboard shows load across hospitals.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Telegram and email notifications (in-app only), and the specialty-recommendation model beyond the symptom-to-specialty mapping table.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
