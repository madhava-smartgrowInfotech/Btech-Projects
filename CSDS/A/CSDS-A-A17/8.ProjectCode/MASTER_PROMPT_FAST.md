# MASTER PROMPT (FAST BUILD) - CropSight

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account (GPU training) and API token.
> - OpenWeatherMap API key (free) - https://openweathermap.org/api
> - Do you have an ESP32 + DHT22? If yes, guide the flashing with the Arduino IDE; if not, use the simulator.
> - Optional: data.gov.in API key for live mandi prices.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **CropSight** - smart crop delivery - AI quality grading, price intelligence, storage monitoring and a farmer-to-buyer marketplace.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8117**, frontend **5117** (`strictPort: true`). Any extra local service uses a port in **11170-11179**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Crop quality is graded manually and inconsistently.
- Farmers cannot predict prices or choose the best time to sell.
- Storage and transport conditions cause unmonitored post-harvest losses.
- Middlemen and limited market access reduce farmer income.

**What is needed:** An integrated platform that grades quality, forecasts prices, monitors the supply chain and connects farmers to buyers.

---

## 3. Who uses it

- Farmers selling produce
- Buyers, traders and distributors
- Storage and transport operators

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**AI-Driven Smart Agriculture: An Integrated Approach for Soil Analysis, Irrigation, and Crop-Fertilizer Recommendations** - IEEE Access, 2025 - https://doi.org/10.1109/access.2025.3594162

- An AI-driven smart agriculture system combining IoT soil sensors, deep learning and explainable AI.
- A Transformer-based tabular model for irrigation advice (99.13% accuracy), TabNet for soil analysis and a fusion transformer for crop and fertiliser recommendation.
- XAI used to explain soil and irrigation predictions.

### 4.2 Advanced system (the specification - every point must be met)

- Deep learning grades crop quality from images using size, colour, texture and defects.
- ML models forecast prices from market trends, weather, demand and regional variations.
- IoT sensors monitor temperature and humidity during storage and transport.
- Explainable AI shows why a grade or price was predicted.
- A digital marketplace recommends buyers, delivery routes and the best time to sell.

Objectives the product must meet:

1. Grade crop quality automatically from images using deep learning.
2. Forecast crop prices from market, weather and demand data.
3. Monitor storage and transport conditions using IoT sensors.
4. Explain grading and pricing decisions with XAI.
5. Recommend buyers, delivery routes and the best time to sell.
6. Connect farmers, distributors and buyers through a digital marketplace.

### 4.3 Latest approaches
- CNN / vision-transformer produce grading from photos.
- Gradient-boosted price forecasting with lag and weather features.
- Cold-chain IoT monitoring with spoilage-risk alerts.
- Digital marketplaces with price discovery and delivery routing.

### 4.4 What you will build - CropSight
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Quality grading** - a photo is graded fresh/rotten with an A/B/C grade and a defect percentage, explained with a Grad-CAM view.
- **F2 Price forecasting** - XGBoost on the mandi price history with lag and weather features, giving a forecast and a 'best time to sell' suggestion, explained with SHAP.
- **F3 Storage monitoring** - temperature and humidity from a simulated sensor feed (or a real ESP32 + DHT22 if available) with spoilage-risk alerts.
- **F4 Weather** - OpenWeatherMap forecast used in the pricing and storage advice.
- **F5 Marketplace** - farmers list graded lots with a suggested price; buyers browse and make offers.
- **F6 Delivery recommendation** - nearest suitable buyers or markets with a route on the map.
- **F7 Evaluation** - grading accuracy, F1 and confusion matrix; price MAE / MAPE.

### 4.5 Data

- **Fruits fresh and rotten for classification** (Kaggle) - https://www.kaggle.com/datasets/sriramr/fruits-fresh-and-rotten-for-classification - 1.9 GB -> commit a sample plus the download script.
- **Indian agricultural mandi prices 2023-2025** (Kaggle) - https://www.kaggle.com/datasets/arjunyadav99/indian-agricultural-mandi-prices-20232025 - 10 MB -> commit.
- Optional live prices: data.gov.in 'Current daily price of various commodities' - https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi (free API key).

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (farmer, buyer, admin)
3. Grade my produce
4. Price outlook
5. Storage monitor
6. Marketplace (list, browse, offers)
7. Delivery planner
8. Model performance

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to CropSight:** PyTorch (a small CNN) for grading, XGBoost + SHAP for prices, pytorch-grad-cam, Leaflet + the free OSRM routing service, the free OpenWeatherMap API, and a simulated sensor feed (ESP32 firmware only if the user has the board).
- **Training:** Heavy training runs **once on Kaggle's free GPU** (milestone M1b) with a small, fast config. Everything else runs on CPU.

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

**M1 - Backend and core logic.** Project skeleton, `setup.bat` (venv + pip + `npm install`), backend with login and the database, then the data/model pipeline and every feature endpoint from section 4.4. Build the data pipeline here; the heavy model trains in M1b. `scripts/smoke_test.py` drives the running API through the main flow end-to-end and must pass. Commit and push.

**M1b - Train on Kaggle GPU (only heavy model here).** Create one notebook in `notebooks/` that reads the dataset from `/kaggle/input/...`, trains a **small, fast config** (few epochs, a subset if needed), and writes the model file, `metrics.json` and a couple of plots to `/kaggle/working/`. Then guide the user in 5 short steps: sign in to kaggle.com -> New Notebook -> File -> Import Notebook (pick it from `notebooks/`) -> Add Data (the dataset from section 4.5) -> Settings -> Accelerator: GPU -> Run All -> download the Output. Put the model file in `models/` and the rest in `experiments/`. Confirm the files load on CPU, then continue. Commit and push.

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
1. A farmer uploads a tomato photo -> grade A, 92% fresh, Grad-CAM view.
2. Price outlook for tomato in a chosen market -> forecast and 'sell in 4 days'.
3. The storage monitor shows live readings (ESP32 or simulator) and a spoilage alert when humidity rises.
4. List the lot -> a buyer makes an offer -> the delivery planner shows the route.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- ESP32 firmware as a required part (the simulator is the default), and the admin analytics page.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
