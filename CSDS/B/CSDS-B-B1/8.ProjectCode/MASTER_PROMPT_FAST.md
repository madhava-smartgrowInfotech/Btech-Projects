# MASTER PROMPT (FAST BUILD) - CivicPulse

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (dataset download).
> - Gemini API key - https://aistudio.google.com/apikey
> - Confirm the department list and SLA days (defaults: Roads, Water Supply, Sanitation, Electricity, Health, Revenue, Public Safety, Town Planning).
> - Confirm languages (default: English, Hindi and Hinglish input).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **CivicPulse** - AI decision support for public grievance offices - understands complaints in English, Hindi and Hinglish, predicts priority and resolution time, routes them to the right department and explains every suggestion.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8201**, frontend **5201** (`strictPort: true`). Any extra local service uses a port in **12010-12019**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Officers manually analyse, prioritise and route large volumes of complaints.
- Urgent civic issues are delayed because prioritisation is inconsistent.
- Resolution times and resources are not planned using data.
- Existing systems give no explainable decision support.

**What is needed:** An explainable decision support system that classifies, prioritises and routes complaints while officers keep the final decision.

---

## 3. Who uses it

- Citizens filing and tracking complaints
- Grievance officers who review AI suggestions and decide
- Field staff who resolve assigned complaints
- Administrators who manage departments, SLAs and analytics

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**A Generalized Spatio-Temporal Causal Knowledge Graph Framework With Large Language Model-Enhanced Reasoning for Urban Event Management** - IEEE Access, 2026 - https://doi.org/10.1109/access.2026.3699522

- A generalised spatio-temporal causal knowledge-graph framework for urban event management.
- Unstructured citizen complaints are processed with LLM-verified information extraction to pull out events, places and times.
- Reasoning over the causal knowledge graph assesses urgency and supports decisions about urban events.

### 4.2 Advanced system (the specification - every point must be met)

- NLP models classify complaints by category and extract key details.
- ML predicts priority and estimates resolution time.
- The system recommends the responsible department for each complaint.
- Explainable AI shows the reasons behind every recommendation, and officers make the final decision.
- Role-based modules support citizens, officers, field staff and administrators with real-time analytics.

Objectives the product must meet:

1. Classify citizen complaints automatically using NLP.
2. Predict complaint priority and estimate resolution time.
3. Recommend the responsible department for each complaint.
4. Explain every recommendation using XAI.
5. Keep officers in control through a human-in-the-loop workflow.
6. Provide real-time analytics for monitoring governance performance.

### 4.3 Latest approaches
- Indic multilingual transformers (MuRIL, IndicBERT, XLM-R) that handle Hindi, English and romanised Hinglish.
- LLM-based structured extraction (location, issue, affected people) with schema validation.
- Spatio-temporal hotspot detection and duplicate clustering of related complaints.
- Human-in-the-loop active learning: officer overrides become new training labels.

### 4.4 What you will build - CivicPulse
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Complaint intake** - web form with text (English, Hindi, Hinglish), photo and map location; a tracking ID and status page for the citizen.
- **F2 Classification** - category and department predicted by a TF-IDF + Logistic Regression model (trains on CPU in under a minute), with Gemini extracting the key details (place, issue, affected people) as structured fields.
- **F3 Priority prediction** - Low / Medium / High / Critical from the text, urgency cues and category.
- **F4 Resolution-time estimate** - expected days to resolve, learned from real service-request patterns, with an SLA-breach flag.
- **F5 Explanations** - the words that drove the category (LIME) and the factors behind priority and time (SHAP).
- **F6 Officer workbench** - accept or override every suggestion with a reason; overrides are stored as new labels and one click retrains the model.
- **F7 Hotspot map and analytics** (NEW) - recurring issues by ward, SLA compliance and category trends.
- **F8 Draft reply** - Gemini drafts a status reply to the citizen in their language for the officer to edit.

### 4.5 Data

- **Citizen Grievance Dataset** (Kaggle) - https://www.kaggle.com/datasets/abhisheksingh016/citizen-grievance-dataset - 0.7 MB, CC0; Hindi, Hinglish and English grievances labelled by department -> commit.
- **Indian Citizen Complaint** (Kaggle) - https://www.kaggle.com/datasets/shebinsam2004/indian-citizen-complaint - 4.2 MB, MIT -> commit.
- **CivicComp-HiEn: Hindi-English Civic Complaints** (Kaggle) - https://www.kaggle.com/datasets/shyamtripathi373/civiccomp-hien-hindienglish-civic-complaints - 1.2 GB, CC BY-SA 4.0; real bilingual civic complaints -> commit a sample plus the download script; use the full set inside the Kaggle notebook.
- **NYC 311 Service Requests** (open data API, no key) - https://data.cityofnewyork.us/resource/erm2-nwe9.json - created/closed dates by complaint type; the download script pulls about 200k recent rows to learn realistic resolution-time patterns per category -> commit the extract if under the size rule.
- **Workflow data** - a committed, seeded generator for wards, departments, officers and complaint histories.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (citizen, officer, admin)
3. File a complaint
4. Track my complaints
5. Officer triage queue with suggestions and explanations
6. Complaint detail (override, draft reply)
7. Hotspot map and analytics

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to CivicPulse:** scikit-learn (TF-IDF + Logistic Regression) for category and department, XGBoost for priority and resolution time, LIME / SHAP for the explanations, Gemini for structured extraction and draft replies, Leaflet for the hotspot map.
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
1. A citizen files a complaint in Hindi with a photo and location -> gets a tracking ID.
2. The officer queue shows Roads, High priority, about 4 days, with the words that drove it -> the officer accepts.
3. The officer overrides a wrong department -> one click retrains and the new metrics appear.
4. The hotspot map and SLA analytics update; Gemini drafts the reply to the citizen.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Fine-tuning a multilingual transformer on Kaggle (the TF-IDF model plus Gemini extraction is accurate enough and trains instantly), the field-staff app, and duplicate clustering.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
