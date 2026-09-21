# MASTER PROMPT (FAST BUILD) - RetinaGuard

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (dataset download).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **RetinaGuard** - screens fundus images for hypertensive retinopathy with wavelet features and a CNN, adds clinical heart-risk prediction and combines both into one risk stage.

**Goal: a fully working, end-to-end product in the shortest time.** Every feature in section 4.4 must really work with real data and the real model or API - nothing fake. Build only what is in this file. When two approaches both work, **always take the simpler one.**

---

## 1. Rules

1. **One stop only.** Do the Start step (section 8), show a short plan, and wait for **"proceed"**. After that, build straight through to the end without stopping. Don't ask more questions unless you are truly blocked; pick sensible defaults and list them in the final summary.
2. **Real product identity.** Never write anything suggesting coursework or an institution - in code, comments, UI, docs, sample data, file names or commit messages: no "B.Tech", "final year", "major/mini project", "semester", "college/university project", "student batch", "project guide", "supervisor", "viva", "project review", "project submission", "HOD" or academic department names, and no names of people or institutions. Ordinary product words (a hospital department, a moderator review) are fine. (This is a clinical decision-support product: every AI result is shown as an aid for a qualified professional, with a short disclaimer, never as a final diagnosis.)
3. **Works end-to-end, nothing fake.** No placeholders, dummy buttons or hard-coded results. Every output comes from the real pipeline. Seed/demo data is allowed only when clearly labelled as sample data.
4. **Speed rules.**
   - Build only the features in section 4.4. No extra features, no animation libraries, no refactoring for elegance.
   - Install only what section 6 lists. Do **not** add LangChain, LlamaIndex or any library not named there.
   - Timebox: if something still fails after 3 attempts, switch to a simpler approach that works and note it in the summary.
   - Testing = one smoke-test script that drives the real API, plus a frontend production build (`npm run build`). No large unit-test suites.
   - Run the backend and frontend in the background while you work; never block on them.
5. **Secrets** live only in `.env` (git-ignored); commit a complete `.env.example` listing every key and where to get it. Never hard-code keys.
6. **Leave `2.ABSTRACT.docx` and `MASTER_PROMPT.md` in this folder untouched**, and don't reference them in the product.
7. **Fixed ports** (other products may run on this PC at the same time): backend **8216**, frontend **5216** (`strictPort: true`). Any extra local service uses a port in **12160-12169**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Hypertensive retinopathy progresses silently until vision is affected.
- Manual screening is slow and needs specialists.
- Eye and heart risks are evaluated separately.
- Screening tools rarely give an overall health risk stage.

**What is needed:** An automated screening system that analyses fundus images and clinical data together to detect hypertensive retinopathy and cardiovascular risk early.

---

## 3. Who uses it

- Ophthalmologists and optometrists
- Physicians and cardiologists screening hypertensive patients
- Eye clinics and screening camps with fundus cameras

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Optimizing Deep Learning Architectures for Diabetic Retinopathy Detection: A Comparative Study of CNN and ResNet-50 With ADAM and SGDM** - IEEE Access, 2026 - https://doi.org/10.1109/access.2026.3663765

- Optimising deep-learning architectures for diabetic retinopathy detection: a CNN compared with ResNet-50.
- Each model is trained with ADAM and SGDM optimisers to find the best configuration.
- Fundus images are preprocessed with CLAHE and augmented before training.

### 4.2 Advanced system (the specification - every point must be met)

- Fundus images are preprocessed and resized to a uniform size.
- The Haar Wavelet Transform extracts enhanced vessel and lesion features.
- A LeNet CNN classifies hypertensive retinopathy from the wavelet features.
- An ML model predicts heart disease risk from clinical parameters.
- A web app combines both outputs into an overall risk stage.

Objectives the product must meet:

1. Preprocess and enhance retinal fundus images.
2. Extract features using the Haar Wavelet Transform.
3. Detect hypertensive retinopathy using a LeNet CNN.
4. Predict heart disease risk from clinical parameters.
5. Combine both results into an overall risk stage.
6. Provide a web interface for screening and results.

### 4.3 Latest approaches
- Wavelet-domain features that highlight vessels and lesions.
- Vessel analysis (width and arteriovenous changes) for hypertensive signs.
- Transfer learning with explainable heatmaps.
- Multimodal risk that combines retinal findings with clinical data for cardiovascular risk.

### 4.4 What you will build - RetinaGuard
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Fundus upload and preprocessing** - green channel, CLAHE, resize and normalisation, shown step by step, with a blur/illumination quality check.
- **F2 Haar wavelet features** - 2-level Haar sub-bands (LL, LH, HL, HH) highlighting vessels and lesions.
- **F3 Hypertensive retinopathy detection** - a LeNet CNN on the wavelet sub-bands returning a probability (small model, trains on CPU).
- **F4 Explanation** - a Grad-CAM heatmap plus a vessel map from the Frangi filter.
- **F5 Heart-disease risk** - a clinical form (age, sex, blood pressure, cholesterol and the rest) scored by a Random Forest / XGBoost model with SHAP reasons.
- **F6 Combined risk stage** - the retinal result and the clinical risk combined into Low / Moderate / High / Very high with recommendations.
- **F7 Screening report** - a PDF with the images, findings and risk stage.
- **F8 Evaluation** - accuracy, sensitivity, specificity, F1 and ROC-AUC for both models, with the confusion matrices.

### 4.5 Data

- **Hypertension & Hypertensive Retinopathy Dataset** (Kaggle) - https://www.kaggle.com/datasets/harshwardhanfartale/hypertension-and-hypertensive-retinopathy-dataset - 1 GB, CC BY-NC 4.0 -> commit a sample plus the download script.
- **Ocular Disease Recognition (ODIR-5K)** (Kaggle) - https://www.kaggle.com/datasets/andrewmvd/ocular-disease-recognition-odir5k - 1.9 GB; includes a Hypertension (H) label -> sample plus script.
- **Heart Disease Dataset** (Kaggle) - https://www.kaggle.com/datasets/johnsmith88/heart-disease-dataset (UCI source: https://archive.ics.uci.edu/dataset/45/heart+disease) -> commit.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (clinician, technician)
3. New screening (fundus + clinical form)
4. Result (wavelet view, heatmap, risk stage)
5. Report
6. Patients and history
7. Model performance

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to RetinaGuard:** PyTorch (CPU wheel) for the small LeNet - it trains on CPU in minutes; PyWavelets for the Haar transform; OpenCV and scikit-image (Frangi vessel filter); scikit-learn / XGBoost + SHAP for the heart-risk model; ReportLab for the report.
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
1. Upload a fundus image -> the quality check passes and the wavelet sub-bands are shown.
2. 'Hypertensive retinopathy 91%' with the heatmap and vessel map.
3. Fill the clinical form -> heart-disease risk 68% with its top factors.
4. Combined stage High -> recommendations and the PDF screening report.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- The ResNet-50 comparison with Adam versus SGDM (that is what needed a GPU), and the ODIR-5K dataset as a second source.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
