# MASTER PROMPT (FAST BUILD) - AffectLens

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account (GPU training) and API token.
> - A webcam for the live mode.
> - Optional: request the RAF-DB compound subset (guided).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **AffectLens** - recognises complex, mixed emotions in faces, trained with GAN-generated expressions.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8116**, frontend **5116** (`strictPort: true`). Any extra local service uses a port in **11160-11169**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Existing systems recognise only single basic emotions.
- Real expressions often contain several emotions at once.
- Complex-emotion training data is scarce.
- Expression-editing methods distort facial identity.

**What is needed:** A system that generates realistic complex-emotion data and recognises multiple emotions in a single face.

---

## 3. Who uses it

- Mental-health and well-being applications
- Driver-monitoring and safety systems
- Customer-experience and human-computer-interaction teams

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Complex Emotion Estimation Using Analysis-by-Synthesis of Facial Expression Images** - IEEE Access, 2025 - https://doi.org/10.1109/access.2025.3570167

- Complex emotion estimation by analysis-by-synthesis of facial expression images.
- Conditioned Emotion GANs (cEmoGANs) generate complex expressions while preserving identity, with better quality, less distortion and more diversity.
- A multi-label CNN trained on the generated images outperforms earlier models.

### 4.2 Advanced system (the specification - every point must be met)

- cEmoGANs generate facial images with specified complex emotions.
- The generator preserves identity while changing only the expression.
- Generated images enlarge and diversify the training dataset.
- A CNN multi-label classifier predicts every emotion present in a face.
- The system recognises both basic and complex emotions more accurately.

Objectives the product must meet:

1. Generate identity-preserving facial images with complex emotions using cEmoGANs.
2. Enlarge the complex-emotion dataset with generated images.
3. Train a CNN multi-label classifier for basic and complex emotions.
4. Evaluate recognition performance against single-label baselines.
5. Provide an interface for emotion recognition from uploaded images.

### 4.3 Latest approaches
- Diffusion- and GAN-based identity-preserving expression editing.
- Compound-expression datasets (RAF-DB compound) and multi-label recognition.
- Transformer backbones and valence-arousal estimation for richer affect.

### 4.4 What you will build - AffectLens
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 cEmoGAN** - a small conditional GAN with an identity-preservation loss that generates faces with a chosen emotion mix (trained with a short, fixed schedule).
- **F2 Synthetic dataset builder** - generates a balanced set of complex-emotion images, reported with FID and an identity-similarity score.
- **F3 Multi-label recogniser** - a CNN predicting basic and complex emotions, trained on real data and on real + synthetic data.
- **F4 Comparison** - per-class F1, macro F1 and Hamming loss for real-only vs real + synthetic, against a single-label baseline.
- **F5 Analyse a photo** - upload an image, get face detection and emotion confidence bars.
- **F6 Expression studio** (NEW) - pick an emotion mix and generate a face with the GAN.

### 4.5 Data

- **FER-2013** (Kaggle) - https://www.kaggle.com/datasets/msambare/fer2013 - 54 MB -> commit.
- **RAF-DB** (Kaggle mirror) - https://www.kaggle.com/datasets/shuvoalok/raf-db-dataset - 37 MB -> commit (check the licence notes; if redistribution is not allowed, commit only the download script).
- **RAF-DB compound subset** - optional, by request from the dataset owners.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Analyse photo
4. Expression studio
5. Model performance (real vs real + synthetic)

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to AffectLens:** PyTorch + torchvision (a small conditional GAN and a CNN), MediaPipe for face detection, torchmetrics for FID.
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
1. Upload a photo -> 'happily surprised' with confidence bars.
2. Open the expression studio, pick a mix such as 'sadly fearful' -> the GAN generates the face.
3. The dataset builder reports FID and identity similarity for the generated set.
4. The performance page shows real-only versus real + synthetic training results.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Live webcam mode with an emotion timeline, and the RAF-DB compound subset (FER-2013 plus generated data is enough).
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
