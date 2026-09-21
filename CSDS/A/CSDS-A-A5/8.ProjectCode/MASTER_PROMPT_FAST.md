# MASTER PROMPT (FAST BUILD) - TaxSentinel

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (dataset download).
> - Gemini API key - https://aistudio.google.com/apikey
> - Confirm the fraud patterns for the generator (shown at the Start step).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **TaxSentinel** - self-supervised detection and plain-language explanation of GST input-tax-credit fraud patterns.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8105**, frontend **5105** (`strictPort: true`). Any extra local service uses a port in **11050-11059**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- ITC fraud through fake invoices, circular trading and shell companies causes large revenue losses.
- Manual audits and rule-based checks are slow and reactive.
- Confirmed fraud labels are scarce, which limits supervised learning.
- Existing systems rarely explain why a claim is flagged.

**What is needed:** A self-supervised, explainable framework that learns normal GST behaviour and flags and explains suspicious ITC claims.

---

## 3. Who uses it

- Tax-administration analysts and investigators
- Forensic accountants
- Compliance teams at large businesses auditing their supplier networks

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Combating GST Input Tax Credit Fraud in India: Forensic Accounting, Data Analytics, and Legal Enforcement Strategies** - International Journal of Management, Public Policy and Research, 2026 - https://doi.org/10.55829/ykz3ea41

- Explains how GST Input Tax Credit fraud is executed: fake invoices, circular trading, networks of shell companies.
- Uses official data and case studies to size the problem and argues for forensic methods: data analytics, digital forensics and network analysis.
- Descriptive and rule-oriented - no learning system that detects hidden patterns automatically.

### 4.2 Advanced system (the specification - every point must be met)

- A JEPA module learns compact predictive embeddings of normal GST behaviour from unlabelled invoices, returns and transaction flows.
- Invoice-level, taxpayer-behaviour and buyer-seller network features are combined in a multi-layer fraud assessment.
- Deviations from learned behaviour are converted into fraud risk scores for taxpayers and invoice chains.
- Target patterns include fake invoices, circular trading, shell entities and abnormal spikes in ITC claims.
- A tuned LLM generates natural-language explanations of why each claim was flagged.

Objectives the product must meet:

1. Build a multi-layer GST dataset covering invoices, taxpayer behaviour and transaction networks.
2. Learn normal GST behaviour with a self-supervised JEPA encoder.
3. Detect fraud patterns such as fake invoices, circular trading and shell-entity activity.
4. Score and rank suspicious taxpayers and invoice chains by deviation from learned behaviour.
5. Generate natural-language explanations for flagged claims using a tuned LLM.
6. Evaluate detection accuracy and explanation quality.

### 4.3 Latest approaches
- Graph analytics and graph ML for fraud rings (cycle detection, community detection, GNN embeddings).
- Self-supervised representation learning (JEPA / contrastive) for label-scarce anomaly detection.
- LLM-generated, evidence-grounded case narratives for investigators.
- Human-in-the-loop case management that turns outcomes into new labels.

### 4.4 What you will build - TaxSentinel
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 GST ecosystem generator** - a seeded script that creates taxpayers, invoices and monthly returns with injected fraud (fake invoices, circular trading, shell entities, ITC spikes) and ground-truth labels.
- **F2 Feature layers** - invoice-level, taxpayer-behaviour and network-level features.
- **F3 JEPA behaviour encoder** - a small self-supervised encoder (trains on CPU in minutes) whose prediction error is the anomaly score.
- **F4 Fraud-ring detection** - circular-trading cycles and shell clusters found with NetworkX, shown as an interactive graph.
- **F5 Risk ranking** - combined score per taxpayer and invoice chain, with drill-down to the evidence.
- **F6 Written explanations** - Gemini turns the evidence into an investigator-style narrative that cites it.
- **F7 Evaluation** - precision@k, recall and F1 against the injected labels, compared with a rule-based baseline.

### 4.5 Data

- **Synthetic GST dataset** - produced by your committed, seeded generator (`scripts/generate_gst_data.py`). Commit the generated data.
- **PaySim - Synthetic Financial Datasets for Fraud Detection** (Kaggle) - https://www.kaggle.com/datasets/ealaxi/paysim1 - 470 MB, CC BY-SA 4.0 -> commit a sample (about 100k rows) plus the download script.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Overview dashboard
4. Taxpayers: risk ranking and profile
5. Fraud-ring graph
6. Case detail with the written explanation
7. Model performance

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to TaxSentinel:** PyTorch (CPU wheel) for the small JEPA encoder, NetworkX for the fraud-ring graph, react-force-graph for the graph view, Gemini for the written explanations.
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
1. Generate the ecosystem -> the dashboard shows taxpayers, invoices and flagged counts.
2. Open the top-ranked taxpayer -> the evidence (ITC spike, mismatched returns) and the graph showing a circular-trading loop.
3. Read the written explanation that cites that evidence.
4. The performance page shows precision@k and recall against the rule baseline.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- LoRA fine-tuning of a small local LLM (Gemini writes the explanations instead), PaySim pre-training, and the case-management workflow.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
