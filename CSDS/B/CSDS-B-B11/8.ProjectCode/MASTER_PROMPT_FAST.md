# MASTER PROMPT (FAST BUILD) - NutriSense

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Gemini API key - https://aistudio.google.com/apikey
> - Optional: USDA FoodData Central key (guided).
> - Confirm the cuisines and conditions to support (defaults: North and South Indian; diabetes, hypertension, high cholesterol).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **NutriSense** - personalised Indian meal plans that hit your calorie and nutrient targets, respect allergies and health conditions, and adapt as you progress.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8211**, frontend **5211** (`strictPort: true`). Any extra local service uses a port in **12110-12119**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Generic diet charts ignore individual needs and goals.
- People find it hard to plan balanced meals with busy lifestyles.
- Diet apps often ignore allergies and medical conditions.
- Professional nutrition advice is costly and less accessible.

**What is needed:** An AI-powered planner that generates safe, balanced and personalised meal plans and tracks progress.

---

## 3. Who uses it

- People managing weight and everyday health
- People with diabetes, hypertension or high cholesterol
- Families planning meals together

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Artificial intelligence in personalized nutrition and food manufacturing: a comprehensive review of methods, applications, and future directions** - Frontiers in Nutrition, 2025 - https://doi.org/10.3389/fnut.2025.1636980

- A comprehensive review of AI in personalised nutrition and food manufacturing.
- Covers machine learning, deep learning, recommender systems and computer-vision food recognition applied to diet personalisation.
- Highlights future directions such as adaptive, data-driven meal recommendation.

### 4.2 Advanced system (the specification - every point must be met)

- Users create profiles with age, gender, height, weight, activity level, preferences and goals.
- The system calculates BMI, BMR and daily calorie requirements.
- AI generates balanced meal plans for weight loss, weight gain or maintenance.
- Recommendations respect dietary restrictions, allergies and medical conditions.
- Users track intake and progress through dashboards.

Objectives the product must meet:

1. Collect user profiles with health, activity and goal details.
2. Calculate daily calorie and nutrient requirements.
3. Generate personalised meal plans using AI.
4. Respect allergies, dietary restrictions and medical conditions.
5. Track nutritional intake and progress over time.
6. Provide an easy-to-use web interface.

### 4.3 Latest approaches
- Constraint optimisation (linear programming) that guarantees nutrient targets.
- LLM recipe generation with safety guardrails.
- Food photo recognition with multimodal models.
- Adaptive plans that recalibrate from progress data.

### 4.4 What you will build - NutriSense
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Profile and goals** - age, gender, height, weight, activity, diet type, cuisine, allergies, conditions and goal.
- **F2 Requirements** - BMI, BMR (Mifflin-St Jeor), daily calorie target and macro split, plus condition rules (low glycaemic load for diabetes, a sodium cap for hypertension).
- **F3 Meal plan generator** - a 7-day plan optimised with linear programming to hit calories, macros and fibre, with allergens hard-blocked and variety enforced; Gemini adds the recipe steps.
- **F4 Smart swaps** - replace any dish with nutritionally similar alternatives from a clustered food database.
- **F5 Food logging** - search dishes and portions, or log by photo with Gemini identifying the dish for the user to confirm.
- **F6 Progress tracking** - weight log, intake versus target charts and an adherence score, with a weekly recalculation of the target.
- **F7 Safety guardrails** - never below a safe calorie floor, condition limits enforced, and a clear disclaimer.

### 4.5 Data

- **Indian Food Nutritional Values Dataset (2025)** (Kaggle) - https://www.kaggle.com/datasets/batthulavinay/indian-food-nutrition - CC BY-SA 4.0 -> commit.
- **South Asian Recipes with Nutrition & Steps** (Kaggle) - https://www.kaggle.com/datasets/ahsanneural/10k-south-asian-recipes-with-nutrition-and-steps - 9.8 MB, CC BY-SA 4.0 -> commit.
- **Nutritional & Carbon Footprint Data of Indian Diet** (Kaggle) - https://www.kaggle.com/datasets/umangsinghal5/nutritional-and-carbon-footprint-data-of-indian-diet - CC BY 4.0 -> commit.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Profile wizard
4. Dashboard (targets, today's intake)
5. Weekly plan with swaps and recipes
6. Food log
7. Progress charts

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to NutriSense:** PuLP (CBC) for the meal optimisation, scikit-learn K-Means for the swap suggestions, Gemini for recipe steps and photo logging, the free USDA FoodData Central API for ingredient lookups.
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
1. Create a profile: 28, vegetarian, peanut allergy, weight-loss goal -> a 1,650 kcal target with macros.
2. Generate the week -> every day within target and no peanut dishes; swap a dish; open a recipe.
3. Log lunch by photo -> the dish is recognised, confirmed, and the intake chart updates.
4. Enter a week of weights -> the target recalculates.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- The grocery list generator and the carbon-footprint view.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
