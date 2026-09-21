# MASTER PROMPT (FAST BUILD) - TalentTrack

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Gemini API key - https://aistudio.google.com/apikey
> - Install g++ and JDK 17 (guided).
> - Confirm the languages for the judge (default: Python, C++, Java) and the level structure.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **TalentTrack** - builds and proves job readiness - aptitude and coding practice with an automatic judge, contests, levels, AI mock interviews and resume analysis, connected to recruiters who shortlist by real skill.

**Goal: a fully working, end-to-end product in the shortest time.** Every feature in section 4.4 must really work with real data and the real model or API - nothing fake. Build only what is in this file. When two approaches both work, **always take the simpler one.**

---

## 1. Rules

1. **One stop only.** Do the Start step (section 8), show a short plan, and wait for **"proceed"**. After that, build straight through to the end without stopping. Don't ask more questions unless you are truly blocked; pick sensible defaults and list them in the final summary.
2. **Real product identity.** Never write anything suggesting coursework or an institution - in code, comments, UI, docs, sample data, file names or commit messages: no "B.Tech", "final year", "major/mini project", "semester", "college/university project", "student batch", "project guide", "supervisor", "viva", "project review", "project submission", "HOD" or academic department names, and no names of people or institutions. Ordinary product words (a hospital department, a moderator review) are fine. (This product is sold to training providers, bootcamps and hiring teams, so its *end users* are learners, mentors, candidates, recruiters and career-services teams - use those neutral words, never 'students' or 'college'. What must never appear is anything about who built this product or why.)
3. **Works end-to-end, nothing fake.** No placeholders, dummy buttons or hard-coded results. Every output comes from the real pipeline. Seed/demo data is allowed only when clearly labelled as sample data.
4. **Speed rules.**
   - Build only the features in section 4.4. No extra features, no animation libraries, no refactoring for elegance.
   - Install only what section 6 lists. Do **not** add LangChain, LlamaIndex or any library not named there.
   - Timebox: if something still fails after 3 attempts, switch to a simpler approach that works and note it in the summary.
   - Testing = one smoke-test script that drives the real API, plus a frontend production build (`npm run build`). No large unit-test suites.
   - Run the backend and frontend in the background while you work; never block on them.
5. **Secrets** live only in `.env` (git-ignored); commit a complete `.env.example` listing every key and where to get it. Never hard-code keys.
6. **Leave `2.ABSTRACT.docx` and `MASTER_PROMPT.md` in this folder untouched**, and don't reference them in the product.
7. **Fixed ports** (other products may run on this PC at the same time): backend **8209**, frontend **5209** (`strictPort: true`). Any extra local service uses a port in **12090-12099**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Hiring-readiness systems lack continuous skill assessment and tracking.
- Candidates practise on scattered platforms with little guidance.
- Recruiters shortlist without evidence of actual skills.
- Career-services teams cannot measure readiness with data.

**What is needed:** A unified platform that builds and measures job readiness and connects ready candidates to recruiters.

---

## 3. Who uses it

- Candidates preparing for jobs
- Recruiters running hiring drives
- Career-services teams tracking readiness
- Expert interviewers

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**AI-Powered Mock Interview Preparation** - International Journal for Modern Trends in Science and Technology (IJMTST), Vol. 11, Issue 04, 2025 - https://doi.org/10.5281/zenodo.15108980

- AI-powered mock interview preparation: the Gemini API generates role-specific interview questions.
- Candidate answers are evaluated with NLP for relevance and clarity.
- Personalised feedback helps candidates improve before real interviews.

### 4.2 Advanced system (the specification - every point must be met)

- Aptitude, coding and technical practice modules with automated evaluation.
- Leaderboards and regular coding contests to build skills.
- Level-based progression with expert-led mock interviews before a candidate becomes job-ready.
- AI resume analysis and an intelligent chatbot for career and hiring queries.
- Recruiter drive creation, eligibility criteria and skill-based shortlisting, with analytics dashboards.

Objectives the product must meet:

1. Provide aptitude, coding and technical practice with automated evaluation.
2. Run leaderboards and coding contests to build skills.
3. Track candidate progress through evaluation levels and mock interviews.
4. Analyse resumes and guide candidates with AI.
5. Enable recruiters to create drives and shortlist by performance.
6. Give career-services teams analytics dashboards on readiness.

### 4.3 Latest approaches
- LLM interviewers with rubric scoring and speech input.
- Automated code judges with hidden test cases and resource limits.
- ATS-style resume parsing and skills-based matching.
- Readiness scoring that combines many assessment signals.

### 4.4 What you will build - TalentTrack
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Aptitude practice** - a question bank by topic and difficulty, timed tests, automatic scoring and explanations.
- **F2 Coding practice and judge** - Monaco editor, problems with sample and hidden tests, a local runner with time limits, and verdicts (Accepted, Wrong Answer, Time Limit, Runtime Error, Compile Error).
- **F3 Technical MCQs** - programming, DBMS, OS and networks.
- **F4 Contests and leaderboard** - scheduled contests with a leaderboard and ratings.
- **F5 Level-based progression** - levels unlock by score; the final level is an expert mock interview that produces the 'job-ready' badge.
- **F6 AI mock interviews** - role-specific questions with rubric feedback.
- **F7 AI resume analysis** - PDF upload, parsing, an ATS-style score, role match and missing skills, backed by a role classifier trained on the resume dataset.
- **F8 Recruiter module** - drives with eligibility rules, a ranked shortlist with skill evidence, and a status pipeline.
- **F9 Readiness analytics** - cohort readiness and weak topics for career-services teams.

### 4.5 Data

- **Engineering Aptitude Test Questions** (Kaggle) - https://www.kaggle.com/datasets/keithzidandsouza/engineering-aptitude-test-questions - MIT -> commit.
- **Resume Dataset** (Kaggle) - https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset - 112.8 MB, CC0, 2,400+ resumes in 24 categories -> commit the CSV and a small sample of PDFs.
- **Coding problems** - write at least 30 original problems with sample and hidden tests (do not copy problems from commercial sites); committed.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (candidate, recruiter, career-services)
3. Candidate dashboard
4. Aptitude tests
5. Coding problems and editor
6. Contests and leaderboard
7. Mock interview and report
8. Resume analyser
9. Recruiter: drives and shortlist
10. Readiness analytics

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to TalentTrack:** Monaco editor for the code editor; a local sandboxed runner (subprocess per submission, temp folder, time limit) for Python, C++ and Java; pdfplumber for resume parsing; scikit-learn for the resume role classifier; Gemini for interviews, feedback and the chatbot.
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
1. A candidate takes an aptitude test and solves a coding problem -> Accepted on hidden tests; the leaderboard updates live.
2. Uploads a resume -> ATS score and missing skills; takes an AI mock interview -> feedback report.
3. A recruiter creates a drive (level 3+, Python) -> ranked shortlist with evidence -> invites sent.
4. The career-services dashboard shows readiness by topic.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Judge0 (the local runner replaces it), the career chatbot, and the code-similarity check.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
