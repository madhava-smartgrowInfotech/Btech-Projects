# MASTER PROMPT (FAST BUILD) - PhishShield

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (for the download script).
> - Optional: PhishTank API key (the product works without it).
> - Chrome browser to load the unpacked extension (guided).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **PhishShield** - real-time phishing URL detection that combines machine learning with continuously updated threat intelligence.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8103**, frontend **5103** (`strictPort: true`). Any extra local service uses a port in **11030-11039**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Phishing websites continue to steal user credentials and financial data at scale.
- Blacklist-based methods cannot detect newly created, zero-day phishing URLs.
- Static rules and one-time-trained models fail as attack patterns evolve.
- High false positives in existing filters block legitimate websites.

**What is needed:** An adaptive phishing detection system that classifies unseen URLs with ML and stays current through crowdsourced threat intelligence.

---

## 3. Who uses it

- Everyday users checking suspicious links
- IT and security teams screening links in bulk
- Organisations that want a browser-level warning

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**A Dynamic Phishing URL Detection System Integrating Advanced Machine Learning and Crowdsourced Threat Intelligence** - IEEE Access, 2026 - https://doi.org/10.1109/access.2026.3700833

- A dynamic phishing detection framework in three stages: feature engineering from URLs and user reports, ML classification, and model refinement through crowdsourced feedback.
- Addresses the weakness of static blacklists by learning newly observed attack patterns.
- Reported very high accuracy (99.8%) on a recent phishing URL dataset.

### 4.2 Advanced system (the specification - every point must be met)

- URLs are analysed using lexical, structural and domain-based features such as length, special characters, subdomains and domain age.
- ML models including Random Forest, XGBoost and Logistic Regression classify URLs as phishing or legitimate.
- Crowdsourced threat intelligence from trusted cybersecurity communities adds newly reported phishing URLs.
- The model is refined continuously with new threat data to adapt to evolving attack patterns.
- Real-time classification gives users an immediate verdict with a confidence score.

Objectives the product must meet:

1. Collect and preprocess a dataset of phishing and legitimate URLs.
2. Extract lexical, structural and domain-based URL features.
3. Train and compare Random Forest, XGBoost and Logistic Regression classifiers.
4. Integrate crowdsourced threat intelligence for newly reported phishing URLs.
5. Refine the model continuously as new threat data arrives.
6. Provide real-time URL classification through a simple web interface.

### 4.3 Latest approaches
- Character-level deep models on raw URLs alongside engineered lexical, host and domain features.
- Continual learning from live threat feeds with drift monitoring and versioned models.
- Explainable predictions (SHAP) so analysts see why a URL was flagged.
- Browser-extension protection that checks links before the page loads.

### 4.4 What you will build - PhishShield
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 URL check** - single URL and bulk CSV upload; verdict, probability and risk level.
- **F2 Feature engine** - lexical, structural and domain features (length, entropy, special characters, subdomains, TLD, IP use).
- **F3 Model comparison** - Random Forest, XGBoost and Logistic Regression trained and compared; the best one is served; a metrics page shows accuracy, precision, recall, F1 and ROC-AUC.
- **F4 Threat-feed match** - the cached OpenPhish community feed gives an instant hit before the model runs.
- **F5 Report and retrain loop** - users report URLs, a moderator approves, and one click retrains and versions the model with its new metrics.
- **F6 Why flagged** (NEW) - SHAP explanation of the top features behind each verdict.

### 4.5 Data

- **Phishing Site URLs** (Kaggle) - https://www.kaggle.com/datasets/taruntiwarihp/phishing-site-urls - 30 MB, Open Database licence -> commit in full.
- **PhiUSIIL Phishing URL Dataset** (UCI, optional extra validation) - https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset
- **OpenPhish community feed** - https://openphish.com/feed.txt (live, cached locally).

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. URL check (single + bulk)
4. Result with SHAP explanation
5. Reports and moderation queue
6. Models: metrics, versions, retrain

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to PhishShield:** XGBoost, SHAP, tldextract; the free OpenPhish feed (https://openphish.com/feed.txt, no key).
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
1. Check a known phishing URL -> High risk with the SHAP reasons; check a well-known safe site -> Safe.
2. Upload a CSV of 50 URLs -> bulk results.
3. Report a suspicious URL -> the moderator approves it -> retrain -> a new model version appears with its metrics.
4. The feed page shows the cached OpenPhish entries and an instant match.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- The Chrome extension and the analytics dashboard.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
