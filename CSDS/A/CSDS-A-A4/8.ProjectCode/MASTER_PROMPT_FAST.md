# MASTER PROMPT (FAST BUILD) - HubOptima

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (for the download script).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **HubOptima** - predict-then-optimise planning of e-commerce logistics hubs, balancing cost and delivery speed.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8104**, frontend **5104** (`strictPort: true`). Any extra local service uses a port in **11040-11049**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Poor hub placement increases transportation cost and delays deliveries.
- Traditional hub location models assume fixed demand and ignore fluctuations.
- Exact optimisation is too slow for large, changing logistics networks.
- Forecasting and optimisation are done separately, which weakens hub decisions.

**What is needed:** A framework that feeds ML demand forecasts directly into an efficient optimisation model, so hub choices adapt to changing demand.

---

## 3. Who uses it

- Logistics and network-planning teams
- Operations managers deciding where to open or close hubs
- Analysts running what-if scenarios

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Advanced Optimization in E-Commerce Logistics: Combining Matheuristics With Random Forests for Hub Location Efficiency** - IEEE Access, 2025 - https://doi.org/10.1109/access.2025.3550560

- Integrates matheuristics with a Random Forest to solve the Hub Location Problem for e-commerce logistics.
- Uses real data from a global logistics company; RF predicts demand, the optimiser adjusts hub configurations to demand and constraints.
- Reported +7.8% delivery-time compliance, +9.4% fulfilment rate and +16% network robustness over traditional methods.

### 4.2 Advanced system (the specification - every point must be met)

- A Random Forest model predicts future demand for each region from historical logistics data.
- Predicted demand is fed into a matheuristic optimisation model for hub selection.
- The optimiser considers transportation cost, delivery time, hub capacity and network constraints.
- Hub configurations are re-optimised as demand patterns and business requirements change.
- Results are compared with traditional hub location methods on cost, delivery time and fulfilment rate.

Objectives the product must meet:

1. Collect and preprocess historical e-commerce logistics data.
2. Predict regional demand using a Random Forest model.
3. Formulate hub location as an optimisation problem with cost, time and capacity constraints.
4. Solve the problem efficiently with a matheuristic approach.
5. Re-optimise hub configurations as demand changes.
6. Compare performance with traditional hub location methods.

### 4.3 Latest approaches
- Probabilistic (quantile) demand forecasts instead of point estimates.
- Robust and scenario-based optimisation under demand uncertainty.
- Modern MIP/CP-SAT solvers combined with large-neighbourhood-search heuristics for large networks.
- Interactive scenario planning on maps (a lightweight network digital twin).

### 4.4 What you will build - HubOptima
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Data import** - load the Olist orders, customers, sellers and geolocation files and aggregate demand by region.
- **F2 Demand forecast** - Random Forest per region, reported with MAE / RMSE / MAPE.
- **F3 Hub optimisation** - capacitated hub-location model solved with OR-Tools, plus a fast matheuristic (fix-and-optimise) for larger runs.
- **F4 Constraints editor** - number of hubs, capacity, fixed opening cost, maximum service distance.
- **F5 Map and KPIs** - hubs, regions and allocations on a map; total cost, average distance, SLA compliance and utilisation compared with a greedy baseline.
- **F6 Re-optimise on demand change** (NEW) - a demand scenario (for example +20%) re-runs the optimiser and shows both plans side by side.

### 4.5 Data

- **Brazilian E-Commerce Public Dataset by Olist** (Kaggle) - https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce - 120 MB, CC BY-NC-SA 4.0, every file under 100 MB -> commit in full.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Data overview
4. Demand forecast
5. Optimisation setup + results map + KPIs
6. Scenario comparison

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to HubOptima:** Google OR-Tools (or PuLP + CBC) for the optimiser, Leaflet + react-leaflet, geopy.
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
1. Open the forecast page -> demand per region with error metrics.
2. Set 5 hubs, capacity and a 500 km limit -> optimise -> hubs and allocations on the map with KPIs against the greedy baseline.
3. Run the +20% demand scenario -> the optimiser re-runs and both plans appear side by side.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- PDF / Excel report export and saved multi-scenario history.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
