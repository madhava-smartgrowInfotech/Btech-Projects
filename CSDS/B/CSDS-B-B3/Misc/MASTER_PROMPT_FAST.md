# MASTER PROMPT (FAST BUILD) - SkillVerse

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Gemini API key - https://aistudio.google.com/apikey
> - Confirm wallet rules (defaults: 100 starter credits, 10% platform fee, minimum withdrawal 200 credits).
> - Confirm the career paths to include (default: 12 common tech and business roles).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **SkillVerse** - a learn-and-earn ecosystem - buy and sell learning resources with an in-app wallet, get matched with mentors, follow AI career roadmaps and practise AI mock interviews.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8203**, frontend **5203** (`strictPort: true`). Any extra local service uses a port in **12030-12039**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Learning resources, mentorship and job-preparation material are scattered across platforms.
- Learners lack personalised career guidance and learning roadmaps.
- Job-interview preparation gives little individualised feedback.
- Learners have few opportunities to share knowledge and earn from it.

**What is needed:** An integrated, AI-powered ecosystem where learners learn, earn, get mentored and prepare for jobs in one place.

---

## 3. Who uses it

- Learners building job-ready skills
- Knowledge creators who sell notes, templates and courses
- Mentors who guide learners
- Moderators and administrators

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Enhancing Efficient Personalized Learning and Educational Management in Universities Using Graph Neural Networks in Intelligent Tutoring Systems** - IEEE Access, 2026 - https://doi.org/10.1109/access.2026.3662800

- Personalised learning with graph neural networks inside an intelligent tutoring system.
- The curriculum is modelled as a directed acyclic graph of concepts; the learner's knowledge state is tracked over it.
- Adaptive reinforcement chooses the next learning step, improving the efficiency of personalised learning and its management.

### 4.2 Advanced system (the specification - every point must be met)

- Learn & Earn Marketplace: learners share, access and monetise notes, study materials, case studies, coding templates and courses.
- Peer Mentorship System: connects learners with experienced peers for learning, coding, portfolio, internship and job guidance.
- AI Career Guidance: recommends career domains and personalised learning roadmaps from interests, skills and goals.
- AI Interview Assistance: mock interviews with feedback on technical knowledge, communication and overall performance.
- Personalised Ecosystem: portfolios, progress dashboards, community discussions and gamification.

Objectives the product must meet:

1. Build a Learn & Earn marketplace for sharing and monetising learning resources.
2. Connect learners with peer mentors for learning and career guidance.
3. Recommend career paths and personalised learning roadmaps using AI.
4. Provide AI mock interviews with detailed performance feedback.
5. Track learner progress through profiles, dashboards and gamification.
6. Encourage collaborative, community-driven learning.

### 4.3 Latest approaches
- Skill graphs combined with LLM-generated, personalised roadmaps.
- Embedding-based matching of learners to mentors and resources.
- LLM mock interviewers with rubric scoring and speech input.
- Creator economies with wallets, revenue share and automated content-quality checks.

### 4.4 What you will build - SkillVerse
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Learn & Earn marketplace** - upload notes, templates and courses; previews, search, ratings and reviews.
- **F2 In-app wallet** - a credit ledger: starter credits, buying with credits, creator earnings minus a platform fee, and admin-approved withdrawal records. Clearly labelled as in-app credits.
- **F3 Originality and quality check** (NEW) - near-duplicate detection with embeddings plus a Gemini quality review before a listing goes live.
- **F4 Peer mentorship** - mentor profiles, skill-based matching, booking slots and session feedback.
- **F5 AI career guidance** - a short quiz on interests, skills and goals returns career paths with reasons.
- **F6 Personalised roadmap** - a step-by-step skill roadmap for the chosen path, tracked as progress, with marketplace resources linked to each step.
- **F7 AI mock interviews** - role-specific questions, spoken or typed answers, scores for technical depth, communication and confidence, and a feedback report.
- **F8 Gamification and community** - XP, levels, badges, a leaderboard and a discussion board.

### 4.5 Data

- No external dataset is required.
- **Job Description Dataset** (Kaggle, optional) - https://www.kaggle.com/datasets/ravindrasinghrana/job-description-dataset - 1.66 GB, CC0 -> commit a sample (about 20k rows) plus the download script; grounds career paths and skills in real job postings.
- Demo catalogue: seeded sample resources, mentors and users, clearly labelled as sample content.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Dashboard (progress, XP)
4. Marketplace (browse, resource page, upload)
5. Wallet
6. Mentors (find, book, chat)
7. Career guidance + roadmap
8. Mock interview room and report
9. Community

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to SkillVerse:** Gemini for career guidance, roadmaps, mock interviews and the quality check; Gemini embeddings stored in SQLite with NumPy search for matching and duplicate detection; the browser Web Speech API for spoken answers; an in-app credit wallet (no payment gateway, no real money).
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
1. A learner signs up (100 credits), takes the career quiz -> 'Data Analyst' path with a roadmap graph.
2. Buys a SQL notes pack with credits; the creator's wallet shows the earning minus the fee.
3. Books a mentor slot; takes an AI mock interview by voice -> scored feedback report.
4. A duplicate upload is blocked by the originality check; XP and badges update.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- The roadmap as an interactive graph (a step list replaces it), real payments, and recommendation feeds.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
