# MASTER PROMPT (FAST BUILD) - SeatWise

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Default rules to confirm: adjacency definition (8 neighbours), roll-number gap, accessible seats per hall.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **SeatWise** - constraint-optimised, cheat-resistant exam seating plans generated in seconds.

**Goal: a fully working, end-to-end product in the shortest time.** Every feature in section 4.4 must really work with real data and the real model or API - nothing fake. Build only what is in this file. When two approaches both work, **always take the simpler one.**

---

## 1. Rules

1. **One stop only.** Do the Start step (section 8), show a short plan, and wait for **"proceed"**. After that, build straight through to the end without stopping. Don't ask more questions unless you are truly blocked; pick sensible defaults and list them in the final summary.
2. **Real product identity.** Never write anything suggesting coursework or an institution - in code, comments, UI, docs, sample data, file names or commit messages: no "B.Tech", "final year", "major/mini project", "semester", "college/university project", "student batch", "project guide", "supervisor", "viva", "project review", "project submission", "HOD" or academic department names, and no names of people or institutions. Ordinary product words (a hospital department, a moderator review) are fine. (This product is sold to organisations that run classes or examinations, so its *end users* may be instructors, examiners and attendees - that is fine. What must never appear is anything about who built this product or why.)
3. **Works end-to-end, nothing fake.** No placeholders, dummy buttons or hard-coded results. Every output comes from the real pipeline. Seed/demo data is allowed only when clearly labelled as sample data.
4. **Speed rules.**
   - Build only the features in section 4.4. No extra features, no animation libraries, no refactoring for elegance.
   - Install only what section 6 lists. Do **not** add LangChain, LlamaIndex or any library not named there.
   - Timebox: if something still fails after 3 attempts, switch to a simpler approach that works and note it in the summary.
   - Testing = one smoke-test script that drives the real API, plus a frontend production build (`npm run build`). No large unit-test suites.
   - Run the backend and frontend in the background while you work; never block on them.
5. **Secrets** live only in `.env` (git-ignored); commit a complete `.env.example` listing every key and where to get it. Never hard-code keys.
6. **Leave `2.ABSTRACT.docx` and `MASTER_PROMPT.md` in this folder untouched**, and don't reference them in the product.
7. **Fixed ports** (other products may run on this PC at the same time): backend **8113**, frontend **5113** (`strictPort: true`). Any extra local service uses a port in **11130-11139**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Manual and spreadsheet-based seating is slow and prone to errors.
- Predictable seating patterns allow malpractice.
- Multiple constraints are difficult to satisfy by hand.
- Candidates and staff lack a digital way to find seat allocations.

**What is needed:** An intelligent system that produces fair, unpredictable and constraint-satisfying seating plans automatically.

---

## 3. Who uses it

- Examination controllers and administrators
- Invigilators (hall lists, attendance)
- Candidates looking up their seat

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Exam Seating Arrangement System** - International Journal of Research Publication and Reviews (IJRPR), Vol. 6, Issue 12, 2025

- A digital exam seating arrangement platform that integrates candidate details, roll numbers, courses, hall capacities and schedules.
- Structured sorting and distribution algorithms allocate seats evenly and reduce malpractice.
- Supports several exam types, real-time updates, downloadable seating charts, hall-wise reports and invigilator instructions.

### 4.2 Advanced system (the specification - every point must be met)

- Administrators upload candidate data and configure examination halls on a central dashboard.
- An optimisation algorithm allocates seats while respecting capacity, subject combinations and roll-number rules.
- Anti-cheating spacing keeps candidates of the same course or adjacent roll numbers apart.
- Randomisation makes seating unpredictable while keeping it fair.
- Seating charts are exported, printed or displayed, with attendance tracking, seat lookup and automated reports.

Objectives the product must meet:

1. Automate seat allocation from uploaded candidate and hall data.
2. Satisfy capacity, subject-combination and roll-number constraints using optimisation.
3. Enforce anti-cheating spacing and randomise seating.
4. Generate exportable seating charts and hall-wise reports.
5. Provide real-time seat lookup and attendance tracking.
6. Reduce the time and errors of manual seating preparation.

### 4.3 Latest approaches
- Constraint programming (CP-SAT) for seating and timetabling with hard and soft constraints.
- Graph-colouring style separation of conflicting candidates.
- Seeded randomised allocation with an audit trail for fairness.
- QR-based seat lookup and digital attendance.

### 4.4 What you will build - SeatWise
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Data import** - candidates, courses, halls (rows x columns) and the timetable from Excel/CSV templates, with validation.
- **F2 Constraint-optimised allocation** - CP-SAT with capacity, no same-course neighbours (including diagonals), roll-number spacing and accessible seats.
- **F3 Seeded randomisation** - a different valid plan each run, with the seed logged for audit.
- **F4 Visual hall grid** - the seat map per hall, with a manual swap that is checked against the constraints (NEW).
- **F5 Exports** - seating charts (PDF), hall-wise lists (Excel) and invigilator sheets.
- **F6 Seat lookup and attendance** - candidates find their hall and seat by ID and get a QR slip; invigilators mark attendance per hall.
- **F7 Summary** - utilisation, constraints satisfied, adjacency conflicts (must be zero) and the time taken versus manual preparation.

### 4.5 Data

- No external dataset. Write a seeded generator for realistic candidates, courses, halls and timetables, and commit its output plus ready-to-import Excel templates.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (admin, invigilator)
3. Data import
4. Generate plan (constraints)
5. Hall seat maps
6. Exports
7. Hall attendance
8. Public seat lookup

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to SeatWise:** Google OR-Tools CP-SAT for the allocation, ReportLab for PDFs, openpyxl for Excel, qrcode for the slips.
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
1. Import candidates, halls and timetable -> validation passes.
2. Generate plans for three exams -> solved in seconds, zero same-course neighbours.
3. Open a hall map, try an illegal swap -> blocked with a reason; download PDFs and Excel.
4. A candidate looks up their seat by ID and downloads a QR slip; an invigilator marks attendance.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Drag-and-drop seat swapping (a click-to-swap dialog replaces it) and the analytics dashboard.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
