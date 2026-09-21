# MASTER PROMPT (FAST BUILD) - HospiSense

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (download script).
> - Confirm the hospital structure (default: 5 facilities; wards General, Surgical, Maternity, Paediatric, ICU; nurse-to-patient ratios).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **HospiSense** - predicts length of stay, bed and ICU demand, and recommends how to allocate beds, staff and equipment - with the reasons behind every number.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8207**, frontend **5207** (`strictPort: true`). Any extra local service uses a port in **12070-12079**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Hospitals cannot forecast admissions, length of stay and resource demand reliably.
- Overcrowding and resource shortages delay patient care.
- Decisions are made under time pressure with incomplete information.
- Existing predictions lack explanations and actionable recommendations.

**What is needed:** An explainable decision support system that predicts resource demand and recommends allocations in advance.

---

## 3. Who uses it

- Hospital administrators and bed managers
- Doctors and nurse managers
- Operations planners

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Predicting Hospital Stay Length Using Explainable Machine Learning** - IEEE Access, 2024 - https://doi.org/10.1109/access.2024.3421295

- Predicts short versus long ICU length of stay at admission from electronic health record data.
- Uses XGBoost and compares it with other classifiers.
- Explainable AI (SHAP) shows which clinical factors drive each prediction.

### 4.2 Advanced system (the specification - every point must be met)

- ML models predict length of stay, bed occupancy and ICU requirements from EHR data.
- Resource utilisation forecasts cover beds, staff and critical equipment.
- An optimisation layer recommends the allocation of beds, staff and equipment.
- Explainable AI such as SHAP shows the factors behind each prediction.
- A dashboard supports administrators and doctors in making timely decisions.

Objectives the product must meet:

1. Predict patient length of stay from EHR data.
2. Forecast bed occupancy and ICU requirements.
3. Recommend the optimal allocation of beds, staff and equipment.
4. Explain predictions using explainable AI.
5. Provide a decision dashboard for doctors and administrators.
6. Evaluate prediction accuracy and improvement in resource use.

### 4.3 Latest approaches
- Gradient-boosting length-of-stay models with SHAP explanations.
- Census and occupancy forecasting with lag features and uncertainty bands.
- Mathematical optimisation (MIP) for bed assignment and staff rostering.
- What-if simulation of hospital capacity (a lightweight digital twin).

### 4.4 What you will build - HospiSense
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Length-of-stay prediction** - expected days and a short/long class at admission, with SHAP reasons.
- **F2 Occupancy forecast** - bed occupancy per ward for the next 7-14 days from admissions plus predicted stays.
- **F3 ICU demand forecast** - expected ICU beds needed, with an early warning when it exceeds capacity.
- **F4 Staff and equipment demand** - nurses per shift and key equipment derived from the forecast load.
- **F5 Allocation recommendations** - OR-Tools suggests bed assignments, shift staffing and equipment distribution within capacity, and explains the trade-off.
- **F6 Decision dashboard** - KPIs, forecasts and recommendations that an administrator can accept or modify.
- **F7 Evaluation** - MAE / R2 for length of stay, forecast error against a naive baseline, and the improvement in resource use versus the current allocation.

### 4.5 Data

- **Hospital Length of Stay Dataset (Microsoft)** (Kaggle) - https://www.kaggle.com/datasets/aayushchou/hospital-length-of-stay-dataset-microsoft - 11.8 MB, 100k patients with admission and discharge dates -> commit.
- **AV: Healthcare Analytics II** (Kaggle) - https://www.kaggle.com/datasets/nehaprabhavalkar/av-healthcare-analytics-ii - 37.5 MB, stay bands by ward and severity -> commit.
- **Hospital Beds Management** (Kaggle) - https://www.kaggle.com/datasets/jaderz/hospital-beds-management - 0.4 MB, CC0; weekly service-level beds, patients, staff and schedules -> commit.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (admin, doctor)
3. Dashboard (KPIs, alerts)
4. Admissions and predictions (with SHAP)
5. Occupancy and ICU forecasts
6. Allocation recommendations
7. Model performance

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to HospiSense:** XGBoost (or LightGBM) + SHAP for the predictions, Google OR-Tools for the allocation.
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
1. Admit a patient -> predicted 6.2 days, 'long stay', with the reasons.
2. The forecast shows ICU demand passing capacity on day 5 -> an early warning appears.
3. Run the optimiser -> bed moves, extra nurse shifts and equipment transfer recommended; accept the plan.
4. The performance page shows the prediction error and the gain over the current allocation.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- The what-if surge simulator and the separate planner role.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
