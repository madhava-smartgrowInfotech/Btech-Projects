# MASTER PROMPT (FAST BUILD) - VisionForge AI

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account (GPU training) and API token.
> - Gemini API key - https://aistudio.google.com/apikey
> - Optional: register for MVTec AD (guided).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **VisionForge AI** - explainable visual inspection for manufacturing - detects defects, shows why, suggests root causes and writes the inspection report.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8115**, frontend **5115** (`strictPort: true`). Any extra local service uses a port in **11150-11159**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Manual inspection is slow, inconsistent and error-prone.
- AI defect detectors do not explain their decisions.
- Detections are not linked to root causes or corrective actions.
- Inspection reports are still prepared by hand.

**What is needed:** An explainable inspection system that detects defects, shows why, and reports causes and actions automatically.

---

## 3. Who uses it

- Quality-control engineers
- Production-line supervisors
- Plant managers reviewing defect trends

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**VLCIM: A Vision-Language Cyclic Interaction Model for Industrial Defect Detection** - IEEE Transactions on Instrumentation and Measurement, 2025 - https://doi.org/10.1109/tim.2025.3583364

- VLCIM: a vision-language cyclic interaction model that progressively refines visual features using domain knowledge and a large generic model.
- A recursive guidance module and cross-modal interaction fuse vision and language features; a dual-view synergistic mechanism sharpens decisions.
- Improved detection on three industrial datasets (+5.9%, +5.6%, +4.1%).

### 4.2 Advanced system (the specification - every point must be met)

- Deep-learning models detect and classify defects in images of PCBs, steel surfaces and other components.
- Explainable AI such as Grad-CAM highlights the regions behind each detection.
- A language layer generates human-readable explanations and suggests possible root causes.
- Inspection reports include defect type, confidence score, explanation, causes and corrective actions.
- The fully software-based system uses public industrial datasets, keeping it low-cost.

Objectives the product must meet:

1. Detect and classify defects in industrial product images using deep learning.
2. Highlight defect regions with explainable AI heatmaps.
3. Generate human-readable explanations and possible root causes.
4. Produce automated inspection reports with corrective actions.
5. Provide a web dashboard for upload, analysis and reporting.
6. Evaluate detection accuracy on public industrial datasets.

### 4.3 Latest approaches
- Supervised detectors (YOLO) for known defect types.
- Anomaly detection (PatchCore-style) for defect types never seen in training.
- Class-activation heatmaps for visual explanation.
- Multimodal LLMs that turn detections into root-cause analysis and corrective actions.

### 4.4 What you will build - VisionForge AI
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Defect detection** - YOLO trained on the steel-surface defect classes, with boxes and confidence.
- **F2 Visual explanation** - Grad-CAM / EigenCAM heatmap over the detected region.
- **F3 Vision-language explanation** - Gemini describes the defect in plain language and gives likely root causes and corrective actions, grounded in a short defect knowledge base you write.
- **F4 Inspection report** - PDF with the image, heatmap, defect type, confidence, causes and actions.
- **F5 Batch inspection** - inspect a folder of images and get a pass/fail summary.
- **F6 Dashboard and history** - past inspections with a defect-type breakdown.
- **F7 Evaluation** - mAP50, precision and recall per class on the public dataset.

### 4.5 Data

- **NEU Surface Defect Database** (Kaggle) - https://www.kaggle.com/datasets/kaustubhdikshit/neu-surface-defect-database - 27 MB -> commit.
- **PCB Defects** (Kaggle) - https://www.kaggle.com/datasets/akhatova/pcb-defects - 1.9 GB -> commit a sample plus the download script.
- **MVTec AD** (optional, for anomaly mode; free registration) - https://www.mvtec.com/company/research/datasets/mvtec-ad

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Inspect (single image)
4. Result (boxes, heatmap, explanation)
5. Batch inspection
6. Reports and history
7. Model performance

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to VisionForge AI:** Ultralytics YOLO (small model), pytorch-grad-cam for the heatmaps, Gemini (multimodal) for the explanations, ReportLab for the reports.
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
1. Upload a steel image -> 'scratches' detected with a heatmap.
2. The explanation gives the likely root cause and corrective actions; download the PDF inspection report.
3. Run a batch on a folder -> pass/fail summary and history.
4. The performance page shows mAP50 and per-class precision and recall.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- The PCB dataset and the second model, the unseen-defect anomaly mode, and the Pareto analytics page.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
