# MASTER PROMPT (FAST BUILD) - ForgetSafe

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account (GPU training) and API token.
> - Hugging Face account (model downloads) - token only if a gated model is chosen.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **ForgetSafe** - certified, auditable 'right to be forgotten' for federated language models - remove a participant's data influence without retraining from scratch.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8109**, frontend **5109** (`strictPort: true`). Any extra local service uses a port in **11090-11099**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Client data influence remains embedded in federated LLM parameters after training.
- Retraining large models for every deletion request is impractical.
- Heuristic unlearning gives no formal proof that data was forgotten.
- Without verifiable unlearning, models cannot demonstrate compliance with the Right to Be Forgotten.

**What is needed:** A certified unlearning framework that removes a client's influence efficiently and proves it to regulators and users.

---

## 3. Who uses it

- Organisations training language models collaboratively (federated) on private data
- Data-protection and compliance officers
- Participants (clients) who request deletion of their data

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Certifying the Right to be Forgotten: Primal-Dual Optimization for Sample and Label Unlearning in Vertical Federated Learning** - Yu Jiang, Xindi Tong, Ziyao Liu, Xiaoxi Zhang, Kwok-Yan Lam, Chee Wei Tan

- FedORA: formulates the removal of samples or whole labels as a constrained optimisation problem solved with a primal-dual method.
- A new unlearning loss that promotes classification uncertainty rather than misclassification; adaptive step size; asymmetric batches for forgotten vs retained data.
- A theoretical bound on the difference from retraining from scratch, with comparable effectiveness at far lower computation and communication.

### 4.2 Advanced system (the specification - every point must be met)

- Clients submit unlearning requests that trigger removal of their data contribution from the federated global model.
- Parameter-level update techniques erase targeted contributions without retraining from scratch.
- Differential-privacy bounds give a provable, quantifiable guarantee that remaining influence is below a threshold.
- A verification and audit module records and demonstrates each unlearning request for compliance.
- The framework runs inside the federated training pipeline with low overhead while preserving model utility.

Objectives the product must meet:

1. Set up federated fine-tuning of an LLM across multiple clients.
2. Remove a client's data influence through parameter-level unlearning without full retraining.
3. Certify forgetting with differential-privacy based guarantees.
4. Verify unlearning using membership-inference tests and comparison with retraining.
5. Preserve model utility on the remaining data.
6. Provide auditable compliance records for each unlearning request.

### 4.3 Latest approaches
- Parameter-efficient (LoRA) federated fine-tuning of language models (Flower + PEFT).
- Certified removal through differential-privacy noise calibration.
- Unlearning verification with membership-inference attacks and distance to a retrained reference model.
- Tamper-evident audit logs for regulatory compliance.

### 4.4 What you will build - ForgetSafe
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Federated fine-tuning** - LoRA fine-tuning of a small language model across 5 simulated clients with Flower, on a subset of AG News (small config).
- **F2 Contribution tracking** - each client's per-round update is recorded so it can be removed later.
- **F3 Deletion request portal** - a client asks for its data to be forgotten.
- **F4 Unlearning engine** - parameter-level unlearning on the LoRA adapters, with retrain-from-scratch as the reference, and the time and communication cost of each shown side by side.
- **F5 Certification** - differential-privacy accounting (Opacus) produces an (epsilon, delta) certificate for the request.
- **F6 Verification** - membership-inference AUC before and after, accuracy on forgotten vs retained data, and distance to the retrained model.
- **F7 Audit record** - a hash-chained log plus a downloadable PDF certificate per request.

### 4.5 Data

- **AG News** (Kaggle) - https://www.kaggle.com/datasets/amananandrai/ag-news-classification-dataset - 29.5 MB -> commit; split across simulated clients by a seeded script. (Also on Hugging Face: https://huggingface.co/datasets/fancyzhx/ag_news.)

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Federation dashboard (clients, rounds, accuracy)
4. Deletion requests
5. Unlearning run (progress, method, cost)
6. Verification results
7. Certificates and audit log

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to ForgetSafe:** Flower (flwr) for the federated rounds, Hugging Face Transformers + PEFT (LoRA) on a small model (DistilGPT-2 or Qwen2.5-0.5B), Opacus for the privacy accounting, ReportLab for the certificate.
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
1. Dashboard shows 5 clients and the federated model's accuracy over rounds.
2. Client 3 submits a deletion request -> the unlearning run completes in a fraction of retraining time.
3. Verification: the membership-inference AUC for client 3 drops to about 0.5 and retained accuracy stays close to before.
4. Download the compliance certificate; the audit log shows the hash chain.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- The operations analytics dashboard and per-sample (rather than per-client) unlearning.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
