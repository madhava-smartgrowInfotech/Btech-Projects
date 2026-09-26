# MASTER PROMPT (FAST BUILD) - BioSight

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account (GPU training and downloads) and API token.
> - Gemini API key (report fallback) - https://aistudio.google.com/apikey
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **BioSight** - label-efficient medical image segmentation and DNA profile analysis powered by joint-embedding predictive learning, with structured AI reports.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8108**, frontend **5108** (`strictPort: true`). Any extra local service uses a port in **11080-11089**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Medical image segmentation and DNA analysis need expensive expert-labelled data.
- Reconstruction-based self-supervised methods focus on low-level detail rather than meaning.
- Imaging and genomic tasks are handled by separate pipelines.
- Model outputs are hard for clinicians and forensic analysts to interpret.

**What is needed:** A label-efficient, self-supervised framework that serves both tasks and explains its results in structured language.

---

## 3. Who uses it

- Radiology and research teams needing tumour segmentation with few annotations
- Forensic DNA laboratories matching STR profiles
- Bioinformatics researchers exploring learned representations

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**JEPA-DNA: Grounding Genomic Foundation Models through Joint-Embedding Predictive Architectures** - arXiv preprint (NVIDIA Digital Biology Research), 2026

- JEPA-DNA: combines a Joint-Embedding Predictive Architecture with generative objectives (masked-language modelling / next-token prediction) for genomic foundation models.
- Supervises global sequence embeddings in latent space so the model predicts the *meaning* of masked segments rather than recovering tokens.
- Consistent gains on 17 genomic benchmarks in linear-probing and zero-shot settings.

### 4.2 Advanced system (the specification - every point must be met)

- A JEPA core uses context and target encoders to predict representations of masked image patches and DNA sequence windows.
- A multi-scale cross-attention predictor captures both anatomical structures and repeat patterns such as STRs and VNTRs.
- Dual-domain tokenisation uses ViT patches for images and k-mer tokens for DNA sequences.
- A Q-Former or Perceiver bridge connects JEPA embeddings to an LLM fine-tuned with LoRA.
- The LLM generates structured outputs, such as segmented-region descriptions and STR match summaries, from few labels.

Objectives the product must meet:

1. Pre-train a JEPA encoder on medical images and DNA sequences without dense labels.
2. Segment medical images accurately using few annotated samples.
3. Analyse DNA fingerprints by capturing STR and VNTR repeat patterns.
4. Align JEPA embeddings with an LLM fine-tuned using LoRA.
5. Generate structured clinical and forensic text from model outputs.
6. Evaluate the framework against supervised and reconstruction-based baselines.

### 4.3 Latest approaches
- I-JEPA / V-JEPA self-supervised vision encoders that learn semantic features without pixel reconstruction.
- Promptable and label-efficient medical segmentation (foundation encoders + light decoders).
- LoRA-aligned small LLMs that turn model outputs into structured clinical text.
- k-mer tokenisation and latent-prediction objectives for DNA sequences.

### 4.4 What you will build - BioSight
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 JEPA pre-training** - a small ViT encoder pre-trained self-supervised on brain-MRI slices (no masks used).
- **F2 Few-label segmentation** - a light decoder fine-tuned on that encoder with only a fraction of the masks; the app shows the tumour mask overlay and its area.
- **F3 Label-efficiency comparison** - Dice / IoU at 10% and 100% of the masks against a supervised U-Net baseline, shown as a chart.
- **F4 DNA encoder and classification** - k-mer tokenisation with the same latent-prediction idea, then sequence classification.
- **F5 STR profile matching** - a query profile matched against a seeded synthetic profile database, ranked with a likelihood ratio.
- **F6 Structured reports** - Gemini turns the segmentation or match result into a structured report.

### 4.5 Data

- **Brain MRI segmentation (LGG)** (Kaggle) - https://www.kaggle.com/datasets/mateuszbuda/lgg-mri-segmentation - 1 GB, CC BY-NC-SA 4.0 -> commit a sample (about 200 slices with masks) plus the download script.
- **DNA classification dataset** (Kaggle) - https://www.kaggle.com/datasets/miadul/dna-classification-dataset - small -> commit.
- **STR profiles** - seeded synthetic generator using published allele-frequency tables (committed).

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. MRI analysis (upload -> mask, area, report)
4. Label-efficiency results
5. DNA analysis
6. STR matching
7. Model performance

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to BioSight:** PyTorch + timm (a small ViT encoder and a light segmentation decoder), Biopython for the DNA work, Gemini for the written reports.
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
1. Upload an MRI slice -> tumour mask overlay, area and a structured report.
2. Open the label-efficiency chart -> 10% of masks with the pre-trained encoder is close to the fully supervised baseline.
3. Classify a DNA sequence, then run an STR query -> ranked matches with likelihood ratios and a report.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- LoRA fine-tuning of a local LLM (Gemini writes the reports), the embedding explorer, and VNTR analysis beyond STR.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
