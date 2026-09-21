# MASTER PROMPT (FAST BUILD) - AquaVision

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (download script).
> - Confirm the city for weather data (default: Hyderabad).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **AquaVision** - water-utility intelligence without heavy IoT - predicts water quality and demand, detects leaks, imbalances and abnormal consumption on a digital twin of the city network.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8214**, frontend **5214** (`strictPort: true`). Any extra local service uses a port in **12140-12149**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Water quality testing is manual, slow and infrequent.
- Leakages and unequal distribution waste water.
- Existing ML focuses only on water quality prediction.
- Water managers lack integrated, data-driven decision support.

**What is needed:** An affordable AI platform that predicts quality and demand and detects leaks and anomalies for better water management.

---

## 3. Who uses it

- Municipal water-utility engineers
- Distribution and operations managers
- Water-quality laboratory staff

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Advancing Water Quality Management: An Integrated Approach Using Ensemble Machine Learning and Real-Time Interactive Visualization** - IEEE Access, 2025 - https://doi.org/10.1109/access.2025.3573589

- Water-quality management with an ensemble of Decision Trees, Random Forest, GBM, XGBoost and neural networks predicting potability.
- Quality parameters (pH, hardness, solids, chloramines, sulfate and others) feed the ensemble.
- Results are shown on a real-time interactive visualisation dashboard.

### 4.2 Advanced system (the specification - every point must be met)

- Public water-quality datasets, distribution records, weather and consumption data are combined.
- An ensemble of Random Forest, XGBoost, Gradient Boosting and Decision Tree predicts water quality.
- Demand forecasting models predict future water needs.
- Additional models detect distribution imbalances, leakages and abnormal consumption.
- An interactive dashboard supports decisions without heavy IoT infrastructure.

Objectives the product must meet:

1. Predict water quality using an ensemble of ML models.
2. Forecast future water demand.
3. Detect distribution imbalances and pipeline leakages.
4. Identify abnormal water consumption patterns.
5. Provide an interactive decision-support dashboard.
6. Keep the solution low-cost without heavy IoT infrastructure.

### 4.3 Latest approaches
- Stacking ensembles with SHAP explanations for water quality.
- Demand forecasting with weather features.
- Hydraulic-model-based leak detection (pressure residuals) and anomaly detection on flows.
- Digital twins of distribution networks for what-if analysis.

### 4.4 What you will build - AquaVision
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Water-quality prediction** - potable or not from the 9 quality parameters using an ensemble (Random Forest, XGBoost, Gradient Boosting, Decision Tree with stacking), with SHAP reasons and per-parameter checks against WHO limits.
- **F2 Network model** - a city distribution network simulated with WNTR (zones, pipes, tanks, pumps), shown on a map.
- **F3 Demand forecasting** - next 7 days per zone from consumption history plus Open-Meteo weather.
- **F4 Leak detection** - leak scenarios simulated in the network; the model detects a leak and ranks the likely zone or pipe.
- **F5 Distribution imbalance** - supply versus demand per zone with an equity score and a rebalancing suggestion.
- **F6 Abnormal consumption** - per-meter anomalies (bursts, night flow, suspected theft) via IsolationForest.
- **F7 Dashboard** - KPIs (non-revenue water, pressure, quality), the map, charts and an alert list.
- **F8 Evaluation** - accuracy / F1 / ROC-AUC for quality, MAPE for demand, and precision / recall plus top-3 localisation accuracy for leaks.

### 4.5 Data

- **Water Quality (Water Potability)** (Kaggle) - https://www.kaggle.com/datasets/adityakadiwal/water-potability - 0.5 MB, CC0 -> commit.
- **Simulated network data** - consumption, pressures, flows and leak scenarios generated by committed, seeded WNTR scripts (committed).
- **Weather** - Open-Meteo history for the chosen city, cached and committed.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (engineer, manager)
3. Operations dashboard
4. Water-quality check
5. Network map
6. Demand forecast
7. Leaks and anomalies

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to AquaVision:** WNTR (the EPA water-network simulator) to generate the network, demands, pressures and leak scenarios; XGBoost + scikit-learn (Random Forest, Gradient Boosting, Decision Tree) with a stacking ensemble; SHAP; IsolationForest; the free Open-Meteo weather API; Leaflet for the network map.
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
1. Enter a lab sample -> 'Not potable, 81%' with SHAP reasons and WHO-limit flags.
2. The demand forecast for Zone 3 shows a peak on a hot day.
3. Inject a leak in the twin -> alert within minutes, likely pipe ranked first on the map.
4. An abnormal night-flow meter is flagged; the imbalance view suggests rebalancing.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- The incident workflow with assignment and closure, and the separate laboratory role.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
