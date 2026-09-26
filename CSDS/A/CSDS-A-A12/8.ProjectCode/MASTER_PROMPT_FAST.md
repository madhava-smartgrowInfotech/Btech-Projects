# MASTER PROMPT (FAST BUILD) - SeedSense

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account (GPU training) and API token; accept the Plant Seedlings competition rules (guided).
> - Gemini API key (advisor fallback) - https://aistudio.google.com/apikey
> - Optional: millet seed photos with germination outcomes.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **SeedSense** - millet seed germination prediction from seed images and growing conditions, with an AI agronomy advisor.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8112**, frontend **5112** (`strictPort: true`). Any extra local service uses a port in **11120-11129**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Germination is checked manually, which is slow and error-prone.
- Large numbers of seeds cannot be assessed quickly.
- Labelled germination data is scarce for training deep models.
- Farmers receive no clear explanation or advice with the results.

**What is needed:** A fast, explainable system that predicts millet seed germination from images and crop conditions with little labelled data.

---

## 3. Who uses it

- Farmers and farmer-producer organisations
- Seed companies and seed banks testing lots
- Agronomists and extension officers

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Deep learning-based seed germination prediction using morphological traits and RGB images** - BMC Plant Biology, Vol. 26, Article 757, 2026 - https://doi.org/10.1186/s12870-026-08599-3

- Deep-learning prediction of seed germination capacity from RGB images plus automatically extracted morphological traits.
- Dataset of 3,645 images of okra, eggplant and tomato seeds from a microscope, camera and scanner, each seed sown and its germination recorded.
- Weighted F1 of about 0.93 on test data; compared with VGG19, ResNet50 and EfficientNetB5.

### 4.2 Advanced system (the specification - every point must be met)

- JEPA learns features from millet seed images using little labelled data.
- Image features are combined with soil moisture, temperature, humidity, rainfall, soil pH and seed type.
- A machine learning model predicts whether each seed will germinate.
- A fine-tuned LLM explains the prediction and suggests better seed selection and crop management.
- A web application lets users upload seed images, enter crop details and view predictions.

Objectives the product must meet:

1. Learn millet seed image features with a self-supervised JEPA encoder.
2. Combine image features with soil, weather and seed-type data.
3. Predict whether each seed will germinate.
4. Explain predictions and suggest improvements using a fine-tuned LLM.
5. Evaluate with accuracy, precision, recall, F1-score and the confusion matrix.
6. Provide a web application for image upload and results.

### 4.3 Latest approaches
- Self-supervised pre-training (I-JEPA / DINO-style) for label-scarce agricultural imagery.
- Multimodal fusion of image embeddings with tabular environmental data.
- LLM-based agronomy advisors that explain predictions and give actionable recommendations.

### 4.4 What you will build - SeedSense
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Seed image analysis** - single and multi-seed upload; per-seed segmentation and morphological traits (area, perimeter, circularity, colour) with OpenCV.
- **F2 JEPA image encoder** - a small ViT pre-trained self-supervised on the seed images.
- **F3 Fusion prediction** - image embedding + traits + conditions (soil moisture, temperature, humidity, rainfall, pH, seed type) -> germination probability.
- **F4 AI advisor** - Gemini explains the result and advises on seed selection and crop management.
- **F5 Evaluation** - accuracy, precision, recall, F1 and confusion matrix against a ResNet-50 baseline.
- **F6 Seed-lot report** - expected germination for a batch of seeds, downloadable as PDF.
- **F7 Web app** - upload, conditions form and results, as the specification requires.

### 4.5 Data

- **Germinated and non-germinated seed images** (Kaggle) - https://www.kaggle.com/datasets/shajinrp/germinated-and-non-germinated-seed - 9 MB, labelled -> commit.
- **Plant Seedlings Classification** (Kaggle competition, for self-supervised pre-training) - https://www.kaggle.com/competitions/plant-seedlings-classification - the user must accept the competition rules once; use it inside the Kaggle notebook (not committed).
- **Millet seed photos** - optional user-collected images added through F7.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. New analysis (upload + conditions)
4. Result (probability, traits, advice)
5. Lot report
6. Model performance

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to SeedSense:** PyTorch + timm (small ViT), OpenCV for the seed traits, Gemini for the advice, ReportLab for the lot report.
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
1. Upload a seed image with conditions -> germination probability, traits and advisor explanation.
2. Upload a batch -> lot report with expected germination % and a PDF.
3. Model performance shows the JEPA fusion model vs the ResNet50 baseline with the confusion matrix.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- LoRA fine-tuning of a local LLM (Gemini advises instead), the millet data-collection mode, and pre-training on the extra competition dataset.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
