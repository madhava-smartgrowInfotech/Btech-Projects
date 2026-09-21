# MASTER PROMPT (FAST BUILD) - APISentry

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Gemini API key - https://aistudio.google.com/apikey
> - Confirm scans stay local (default: localhost only).
> - Optional: Docker Desktop if you also want crAPI.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **APISentry** - automated security testing for payment APIs - OWASP API Top 10 checks, AI-generated business-logic tests, a security score and clear fixes before deployment.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8213**, frontend **5213** (`strictPort: true`). Any extra local service uses a port in **12130-12139**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Payment APIs are frequent targets of cyberattacks.
- Security testing requires skilled professionals and expensive tools.
- Critical vulnerabilities often remain undetected before deployment.
- Developers lack simple, actionable security feedback.

**What is needed:** A simple, automated, low-cost tool that tests payment APIs and gives developers clear fixes before deployment.

---

## 3. Who uses it

- Backend and API developers at fintech and payment companies
- QA and security engineers
- Engineering managers who need a security score

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**LLM-Driven, Self-Improving Framework for Security Test Automation: Leveraging Karate DSL for Augmented API Resilience** - IEEE Access, 2025 - https://doi.org/10.1109/access.2025.3554960

- An LLM-driven, self-improving framework for API security test automation built on Karate DSL.
- LLMs with retrieval (RAG) generate security tests from API descriptions, focusing on Broken Object Level Authorization (BOLA).
- Test results feed back to improve the generated tests over iterations.

### 4.2 Advanced system (the specification - every point must be met)

- The tool imports REST API endpoints from specifications or collections.
- Automated tests check for broken authentication, BOLA / IDOR, excessive data exposure, rate limiting and injection.
- Tests follow the OWASP API Security Top 10.
- Each API receives a security score based on findings and their severity.
- A detailed report gives developers clear recommendations before deployment.

Objectives the product must meet:

1. Scan REST APIs automatically for OWASP API Top 10 vulnerabilities.
2. Detect broken authentication and BOLA / IDOR issues.
3. Identify excessive data exposure, rate-limiting and injection weaknesses.
4. Calculate an overall API security score.
5. Generate detailed reports with recommendations.
6. Validate the tool on deliberately vulnerable APIs.

### 4.3 Latest approaches
- Full OWASP API Security Top 10 (2023) coverage.
- LLM-generated, stateful, multi-user test cases from OpenAPI specifications.
- Payment-specific abuse testing (amount tampering, replay, race conditions).
- CI/CD integration with JUnit / SARIF outputs and fail thresholds.

### 4.4 What you will build - APISentry
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Target import** - OpenAPI / Swagger or Postman collection, or endpoints entered by hand, with auth profiles (bearer JWT, API key) and two test users for access-control checks.
- **F2 Scope guard** - scans run only against allow-listed hosts (localhost by default) after the user confirms they are authorised to test the target.
- **F3 OWASP API Top 10 tests** - broken object level authorization (BOLA / IDOR), broken authentication (missing, invalid, expired tokens, weak JWT settings), excessive data exposure and mass assignment, missing rate limiting, function-level authorization, injection payloads, and security misconfiguration (CORS, headers, verbose errors).
- **F4 AI-generated tests** (NEW) - Gemini reads the spec and proposes extra business-logic tests (negative amounts, changed account IDs, replayed payment IDs) that the scanner then runs.
- **F5 Security score** - 0-100 with a grade, weighted by severity, plus a per-endpoint breakdown.
- **F6 Findings** - request/response evidence, a curl command to reproduce, the OWASP mapping, and a fix recommendation with a code snippet.
- **F7 Reports and CLI** - a PDF/HTML report, and `apisentry scan --spec ... --fail-on high` for use in a build pipeline.
- **F8 Validation** - findings compared with each target's known vulnerability list, giving a detection rate and false-positive count.

### 4.5 Data

- No dataset. Payload lists and the targets' known-vulnerability lists are written by you and committed.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Targets (import, auth, scope)
4. Scan progress
5. Results (score, findings)
6. Finding detail
7. Reports
8. Validation

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to APISentry:** httpx (async) for the requests, an OpenAPI spec parser, PyJWT for the token tests, Typer for the CLI, Jinja2 + ReportLab for the reports, Gemini for generated tests; VAmPI (runs with plain Python) plus a small deliberately vulnerable 'DemoPay' API you write, both in `targets/`.
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
2. Write `docs/PLAN.md` (30 lines or fewer: architecture, endpoints, tables, screens).
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
1. Import DemoPay's OpenAPI spec with two user tokens -> the scan runs -> score 38/100 (grade D).
2. Findings include BOLA on /accounts/{id} and a missing rate limit on /login, each with evidence and a fix.
3. Gemini proposes extra business-logic tests and the scanner runs them.
4. Run the CLI with --fail-on high -> a non-zero exit code; the validation page shows the detection rate against the known vulnerability list.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Payment-specific abuse tests (amount tampering, idempotency replay, race conditions), scan history and diffs, SARIF/JUnit export, and OWASP crAPI as a second target.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
