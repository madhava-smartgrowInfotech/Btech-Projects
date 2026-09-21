# MASTER PROMPT (FAST BUILD) - ShopTwin

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (download script).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **ShopTwin** - an adaptive e-commerce recommendation engine that tests strategies in a digital twin before customers ever see them.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8111**, frontend **5111** (`strictPort: true`). Any extra local service uses a port in **11110-11119**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Recommenders depend on historical data and adapt poorly to changing behaviour.
- Recommendations lack transparency, which reduces customer trust.
- Strategies are deployed without testing their likely impact.
- Performance drops during high-traffic shopping periods.

**What is needed:** An adaptive recommendation system that tests, explains and reliably serves personalised recommendations at scale.

---

## 3. Who uses it

- E-commerce product and growth teams
- Merchandisers
- Shoppers who receive recommendations (demo storefront)

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**An E-Commerce Recommendation System Based on Dynamic Analysis of Customer Behavior** - International Journal for Research in Applied Science and Engineering Technology, 2024 - https://doi.org/10.22214/ijraset.2024.64867

- Recommendations from dynamic analysis of customer behaviour - purchase history, browsing and likes.
- Contrasts static and dynamic recommenders and combines collaborative filtering, content-based filtering and hybrid ML.
- Claims to ease the cold-start problem and improve scalability and accuracy (accuracy, recall, F1).

### 4.2 Advanced system (the specification - every point must be met)

- Engagement signals such as views, clicks, searches, cart actions, purchases and reviews are processed with big-data analytics.
- A multi-agent AI framework generates personalised recommendations from user behaviour.
- A digital twin simulates recommendation strategies virtually before they are shown to users.
- Explainable AI gives clear reasons for each recommendation.
- A self-learning feedback engine updates the model, and AI-based traffic optimisation manages load at peak times.

Objectives the product must meet:

1. Analyse customer engagement signals using big-data analytics.
2. Generate personalised recommendations with a multi-agent AI framework.
3. Simulate recommendation strategies in a digital twin before deployment.
4. Explain each recommendation using explainable AI.
5. Update the model continuously through a self-learning feedback engine.
6. Maintain response time during peak traffic through AI-based load management.

### 4.3 Latest approaches
- Session-based sequential recommenders and implicit-feedback matrix factorisation (ALS).
- Offline evaluation in simulators / digital twins before A/B tests; bandits for exploration.
- LLM or feature-based explanations of recommendations.
- Caching and request prioritisation to keep latency low at peak times.

### 4.4 What you will build - ShopTwin
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Demo storefront** - catalogue from the REES46 sample, tracking views, cart adds and purchases.
- **F2 Behaviour analytics** - engagement signals aggregated per user and product with pandas.
- **F3 Multi-agent recommender** - collaborative (ALS), content-based, trending and session agents blended by an orchestrator.
- **F4 Digital twin** - simulated customers replay behaviour to score a strategy offline (CTR, conversion, revenue) before it goes live.
- **F5 Explained recommendations** - 'because you viewed...', 'popular with similar shoppers', matching attributes.
- **F6 Feedback learning** - new events update the models incrementally on a schedule.
- **F7 Peak-traffic handling** (NEW) - response caching and a request queue, demonstrated with a small load test.
- **F8 Admin analytics** - strategy comparison and live metrics.

### 4.5 Data

- **eCommerce behaviour data from multi category store (REES46)** (Kaggle) - https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store - 14 GB -> commit a sample (about 300k events) plus the download script.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Storefront (home, product, cart)
4. 'Why this?' panel
5. Admin: strategies and twin runs
6. Admin: analytics and load-test results

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to ShopTwin:** implicit (ALS) or scikit-learn for the recommenders, cachetools for the response cache; the digital twin is a seeded Python simulation.
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
1. Browse the storefront as a new shopper -> recommendations adapt after a few views; open 'Why this?'.
2. Admin runs the digital twin for two strategies -> twin predicts which converts better -> deploy the winner.
3. Run the load test -> latency stays stable thanks to caching and priority handling.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Locust as a separate tool (a simple async load script replaces it) and SHAP explanations (feature-based reasons instead).
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
