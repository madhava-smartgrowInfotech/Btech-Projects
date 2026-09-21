# MASTER PROMPT (FAST BUILD) - ClauseGuard

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Gemini API key - https://aistudio.google.com/apikey
> - Optional: 2-3 real contracts (rental, freelance, employment) to test with.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **ClauseGuard** - contract complexity scoring and predatory-clause detection for Indian agreements, with plain-language explanations.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8106**, frontend **5106** (`strictPort: true`). Any extra local service uses a port in **11060-11069**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Non-experts cannot easily identify predatory or ambiguous clauses in contracts.
- Legal review is expensive and inaccessible for freelancers and small businesses.
- Existing tools ignore Indian contract law and analyse clauses in isolation.
- Users sign contracts without understanding hidden liabilities or unfair terms.

**What is needed:** An affordable, jurisdiction-aware tool that flags predatory clauses and explains contract risks in plain language before signing.

---

## 3. Who uses it

- Freelancers, gig workers and individuals signing contracts
- Startups and small businesses without in-house counsel
- Legal-ops teams doing first-pass review

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**SmartLaw Advisor: AI-Powered Legal Consultation and Contract Analysis for Saudi Arabia** - IEEE Access, 2026 - https://doi.org/10.1109/access.2026.3665420

- A virtual legal-advisory platform: an LLM chatbot (Gemini 1.5) with a standard RAG pipeline over a jurisdiction-specific legal corpus.
- A contract-analysis system that extracts and classifies clauses and checks compliance with national law.
- Evaluated on 150 legal questions (98.67% accuracy) and 50 real contract drafts.

### 4.2 Advanced system (the specification - every point must be met)

- Users upload contracts and receive clause-level annotations, a complexity score and a plain-language risk summary.
- Clauses are embedded and stored in PostgreSQL with pgvector for semantic similarity search.
- A RAG pipeline with the Claude API reasons over retrieved clauses and legal context.
- A Neo4j graph models clause types, legal concepts and precedent patterns to detect risky clause combinations.
- A FastAPI backend and Next.js frontend deliver fast, API-based inference without a local GPU.

Objectives the product must meet:

1. Segment uploaded contracts into clauses and classify clause types.
2. Build a RAG pipeline using the Claude API and pgvector semantic search.
3. Model clause relationships and legal concepts in a Neo4j knowledge graph.
4. Flag predatory clauses and clause combinations using Indian contract law criteria.
5. Compute an overall contract complexity score and a plain-language risk summary.
6. Evaluate clause classification and predatory detection separately using CUAD and curated criteria.

### 4.3 Latest approaches
- Clause-level classification with legal embeddings and LLMs, benchmarked on CUAD and clause-risk benchmarks.
- Knowledge-graph-augmented RAG (GraphRAG) to reason about interactions between clauses.
- Risk scoring with explanations and safer-alternative clause suggestions.

### 4.4 What you will build - ClauseGuard
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Contract upload** - PDF or DOCX, split into clauses with page numbers.
- **F2 Clause classification** - each clause labelled with its CUAD-style type using embeddings plus Gemini as the tie-breaker.
- **F3 Predatory-clause detection** - a curated Indian contract-law rule set (restraint of trade, penalty vs liquidated damages, unilateral termination, unlimited liability, one-sided arbitration, auto-renewal, IP overreach) with the reason and the provision.
- **F4 Risky combinations** (NEW) - a clause graph (NetworkX) flags combinations that are harmless alone but dangerous together.
- **F5 Complexity score** - readability, legalese density, cross-references and length, shown as a grade.
- **F6 Plain-language summary and safer wording** - key obligations, and a fairer alternative for each flagged clause.
- **F7 Evaluation** - clause classification scored on CUAD, and predatory detection scored on a small labelled set you write - reported separately.

### 4.5 Data

- **CUAD - Contract Understanding Atticus Dataset** - https://www.atticusprojectai.org/cuad (also on Hugging Face: https://huggingface.co/datasets/theatticusproject/cuad-qa). Commit it in full if it fits the size rule; otherwise commit a sample plus the download script.
- **Indian contract risk rules and test contracts** - you author the rule set and a small labelled test set (committed).

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Upload contract
4. Contract report: grade, risk summary, annotated clauses
5. Clause detail (explanation, rule, safer wording)
6. Clause graph
7. Evaluation

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to ClauseGuard:** PyMuPDF and python-docx for parsing; Gemini for clause classification, explanations and the summary; embeddings from Gemini stored in SQLite and searched with NumPy (a local vector store - no ChromaDB, no pgvector); NetworkX for the clause graph (no Neo4j).
- **Training:** No model training - this product uses pretrained models, APIs and/or an optimisation engine. Skip straight to the app.

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

**M1 - Backend and core logic.** Project skeleton, `setup.bat` (venv + pip + `npm install`), backend with login and the database, then the data/model pipeline and every feature endpoint from section 4.4. `scripts/smoke_test.py` drives the running API through the main flow end-to-end and must pass. Commit and push.

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
1. Upload a freelance contract -> complexity grade and a list of flagged clauses with severity.
2. Open a flagged non-compete -> explanation, rule reference and safer wording.
3. The graph view shows a risky combination (unilateral termination + no refund + penalty).
4. The evaluation page shows CUAD classification scores and predatory-detection scores separately.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Neo4j (a NetworkX graph replaces it), ChromaDB, and the contract history dashboard.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
