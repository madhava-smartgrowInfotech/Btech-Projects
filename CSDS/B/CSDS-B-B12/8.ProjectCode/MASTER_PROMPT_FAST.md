# MASTER PROMPT (FAST BUILD) - PulmoVision

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account (GPU training) and API token.
> - Gemini API key - https://aistudio.google.com/apikey
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **PulmoVision** - explainable screening of eight lung diseases from chest X-rays and CT scans - lung segmentation, heatmaps, severity and multilingual reports.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8212**, frontend **5212** (`strictPort: true`). Any extra local service uses a port in **12120-12129**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Pulmonary diseases need early detection, but radiologists are scarce.
- Existing models often detect only one disease.
- Predictions lack explanations and severity information.
- Reports are technical and not available in regional languages.

**What is needed:** An explainable, multilingual screening tool that detects multiple lung diseases from X-ray and CT images.

---

## 3. Who uses it

- Radiologists and physicians (screening aid)
- Diagnostic centres and rural clinics
- Patients receiving their reports

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**High-Performance Lung Disease Identification and Explanation Using a ReciproCAM-Enhanced Lightweight Convolutional Neural Network** - IEEE Access, 2025 - https://doi.org/10.1109/access.2025.3568463

- A lightweight CNN for identifying multiple lung diseases from chest CT.
- ReciproCAM heatmaps explain which regions drive each decision.
- High accuracy with low computational cost.

### 4.2 Advanced system (the specification - every point must be met)

- Images are preprocessed with resizing, normalisation, contrast enhancement and noise reduction.
- U-Net segmentation isolates the lung region.
- EfficientNetB0 transfer learning classifies eight pulmonary conditions and normal cases.
- Grad-CAM heatmaps, confidence scores and severity information explain each prediction.
- An AI assistant and multilingual PDF reports support users, with secure, encrypted storage.

Objectives the product must meet:

1. Preprocess and segment lung regions from chest X-ray and CT images.
2. Classify multiple pulmonary diseases using transfer learning.
3. Explain predictions with Grad-CAM heatmaps.
4. Report confidence and severity for each prediction.
5. Generate multilingual PDF reports with an AI clinical assistant.
6. Secure patient records with authentication and encryption.

### 4.3 Latest approaches
- Lung-field segmentation (U-Net) before classification.
- EfficientNet / ConvNeXt transfer learning for multi-class chest imaging.
- Grad-CAM / ReciproCAM explanations with calibrated confidence.
- LLM-generated, patient-friendly multilingual reports.

### 4.4 What you will build - PulmoVision
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Upload and modality check** - chest X-ray or CT (PNG / JPG / DICOM); the app detects which and rejects anything else.
- **F2 Preprocessing** - resize, normalisation, CLAHE and denoising, shown step by step.
- **F3 Lung segmentation** - a U-Net lung mask overlaid on X-rays.
- **F4 Classification** - an X-ray model (COVID-19, viral pneumonia, lung opacity, tuberculosis, normal) and a CT model (adenocarcinoma, large-cell carcinoma, squamous-cell carcinoma, normal), both EfficientNet-B0 transfer learning.
- **F5 Explanation and severity** - a Grad-CAM heatmap, the confidence, and a severity estimate from the affected lung area.
- **F6 AI assistant and multilingual report** - Gemini explains the finding and next steps, and a PDF report is produced in English, Hindi or Telugu.
- **F7 Secure records** - patient records with encryption at rest, role-based access and an audit log.
- **F8 Evaluation** - Dice / IoU for segmentation, and accuracy, macro-F1, per-class sensitivity and confusion matrices for both classifiers.

### 4.5 Data

- **COVID-19 Radiography Database** (Kaggle) - https://www.kaggle.com/datasets/tawsifurrahman/covid19-radiography-database - 769 MB, includes lung masks -> commit a sample plus the download script.
- **Tuberculosis (TB) Chest X-ray Database** (Kaggle) - https://www.kaggle.com/datasets/tawsifurrahman/tuberculosis-tb-chest-xray-dataset - 662 MB -> sample plus script.
- **Chest X-Ray Images (Pneumonia)** (Kaggle) - https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia - 1.18 GB; bacterial vs viral in file names -> sample plus script.
- **Chest CT-Scan Images** (Kaggle) - https://www.kaggle.com/datasets/mohamedhanyyy/chest-ctscan-images - 119 MB -> commit.
- Credit every dataset's authors in `docs/04_DATASET.md` and follow each licence.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (doctor, technician)
3. New scan (upload, modality check)
4. Result (mask, heatmap, severity, assistant)
5. Report preview / download
6. Patients and history
7. Model performance

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to PulmoVision:** PyTorch + timm (EfficientNet-B0) and segmentation-models-pytorch (U-Net), pytorch-grad-cam, pydicom, ReportLab with Noto Sans Devanagari / Telugu fonts for the multilingual report, and Fernet encryption for stored files.
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
1. Upload a chest X-ray -> lung mask, 'Tuberculosis 94%', heatmap, moderate severity.
2. Upload a CT slice -> 'Adenocarcinoma' with heatmap.
3. Ask the assistant 'What should happen next?'; download the Telugu PDF report.
4. Upload a non-chest image -> rejected by the modality check.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Bacterial pneumonia as a separate class (the pneumonia dataset is dropped; 7 classes across the two models), and the scan-comparison-over-time view.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
