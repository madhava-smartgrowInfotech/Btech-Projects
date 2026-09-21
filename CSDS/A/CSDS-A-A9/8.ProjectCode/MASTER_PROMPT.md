# MASTER PROMPT - ForgetSafe

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT.md completely and follow it exactly, starting with Phase 1."*
> Everything the session needs is inside this file.

---

## 0. Your role

You are the lead engineer and product designer for **ForgetSafe** - certified, auditable 'right to be forgotten' for federated language models - remove a participant's data influence without retraining from scratch.

You will take it from this almost-empty folder to a complete, polished, fully working product.

**Scale:** build a complete product that runs end-to-end on a single Windows 10/11 machine and can be demonstrated live. Do **not** engineer for internet scale - no microservices, Kubernetes, message brokers, cloud deployment or load balancing. But **nothing may be fake**: every feature in section 4.4 must really work with real data, real models and real outputs.

---

## 1. Non-negotiable rules

1. **Plan -> Ask -> Build.** Do not write application code at the start. Complete Phase 1 (plan) and Phase 2 (requirements and guided setup) from section 10, then wait for the user's explicit **"proceed"** before building.
2. **Real product identity.** It must read, look and behave like a genuine product from a product company. Never write anywhere - code, comments, UI text, docs, README, sample data, file names, commit messages - anything suggesting it is coursework or was built for an institution: no "B.Tech", "final year", "major project", "mini project", "semester", "college project", "university project", "student batch", "project guide", "supervisor", "viva", "project review", "project submission", "HOD" or academic department names, and no names of people or institutions outside the product itself. Ordinary product words (for example a hospital department or a moderator review) are fine.
3. **Works end-to-end.** No placeholders, TODOs, dummy buttons, hard-coded fake results or "coming soon" screens. Seed/demo data is allowed only as clearly labelled sample data; every prediction must come from the real trained model or the real API.
4. **Stay on purpose.** Build exactly the product in section 4.4. Small polish is welcome; changing the product's stated purpose or core technique is not.
5. **Local Windows first.** One-command setup and start (`setup.bat`, `run.bat`). Docker is optional - use it only if a component genuinely needs it, and say why.
6. **Everything is committed** (section 14): code, notebooks, training logs, metrics, result plots, trained models, datasets (full or sample - section 8) and all docs. Only `venv/`, `node_modules/` and `.env` stay out.
7. **Secrets** live only in `.env` (git-ignored). Commit a complete `.env.example` listing every key with a comment on where to get it. Never hard-code keys.
8. **Ask, don't guess.** When anything outside the code is needed (keys, files, hardware, a decision), ask - and explain exactly how to get it, step by step, for a non-expert.
9. **Documentation is part of the product** (section 13).
10. **Leave `2.ABSTRACT.docx` in this folder untouched** and do not reference it anywhere in the product. Do not modify anything outside this folder except the final copy step in Phase 8.

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

## 4. System evolution - understand this before designing

### 4.1 Reference system (published research this product builds on)

**Certifying the Right to be Forgotten: Primal-Dual Optimization for Sample and Label Unlearning in Vertical Federated Learning** - Yu Jiang, Xindi Tong, Ziyao Liu, Xiaoxi Zhang, Kwok-Yan Lam, Chee Wei Tan

- FedORA: formulates the removal of samples or whole labels as a constrained optimisation problem solved with a primal-dual method.
- A new unlearning loss that promotes classification uncertainty rather than misclassification; adaptive step size; asymmetric batches for forgotten vs retained data.
- A theoretical bound on the difference from retraining from scratch, with comparable effectiveness at far lower computation and communication.

### 4.2 Advanced system - the product specification (must be fully satisfied)

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

### 4.3 Latest approaches (2025-2026 state of the art)

- Parameter-efficient (LoRA) federated fine-tuning of language models (Flower + PEFT).
- Certified removal through differential-privacy noise calibration.
- Unlearning verification with membership-inference attacks and distance to a retrained reference model.
- Tamper-evident audit logs for regulatory compliance.

### 4.4 What you will build - ForgetSafe (the latest, advanced, innovative system)

This combines the specification in 4.2 with the improvements below. Items marked **NEW** go beyond the specification.

- **F1 Federated LoRA fine-tuning** - a small language model fine-tuned across 5 simulated clients with Flower (for example DistilGPT-2 or Qwen2.5-0.5B on AG News as an instruction task).
- **F2 Contribution tracking** - per-client, per-round updates recorded so they can be removed later.
- **F3 Deletion request portal** - a client submits a request to forget its data (whole client or selected samples).
- **F4 Unlearning engine** - primal-dual constrained unlearning (inspired by 4.1) on the LoRA adapters, plus retrain-from-scratch as a reference.
- **F5 Certification** - differential-privacy accounting (Opacus) and an influence threshold produce an unlearning certificate (epsilon, delta, threshold met).
- **F6 Verification** - membership-inference AUC before and after, accuracy on forgotten vs retained data, distance to the retrained model.
- **F7 Compliance certificate and audit log** (NEW) - a hash-chained log and a downloadable PDF certificate per request.
- **F8 Operations dashboard** (NEW) - rounds, clients, requests, metrics over time.

---

## 5. Screens and user flows

1. Landing page
2. Login / register
3. Federation dashboard (clients, rounds, accuracy)
4. Deletion requests
5. Unlearning run (progress, method, cost)
6. Verification results
7. Certificates and audit log

Every screen needs loading, empty and error states, and must work on a phone-sized screen.

---

## 6. AI / ML components

- Federated training and unlearning experiments run on Kaggle GPU; the product loads the resulting adapters, metrics and logs, and can run a light unlearning request on CPU for the demo.
- Report: accuracy on retained / forgotten data, membership-inference AUC, time and communication cost vs retraining.

Save for every trained model: the model file, a metrics JSON (with the dataset split and date), confusion matrix / curves as PNG, and the training log - all under `experiments/<run-name>/` - and show the key metrics inside the product (an "About the model" or "Model performance" view).

---

## 7. Tech stack (fixed - ask before changing anything)

**Frontend**
- React 18 + Vite + TypeScript
- Tailwind CSS + shadcn/ui (Radix-based components) + Lucide icons
- React Router, TanStack Query (server state), Axios
- Motion (Framer Motion) for component/page transitions and micro-interactions
- GSAP + ScrollTrigger for scroll-driven landing-page sequences
- Lenis for smooth scrolling (landing page)
- React Bits (reactbits.dev) components for premium text/background effects - copy the component source into src/components/reactbits/ (they are copy-paste components, not an npm package)
- Recharts for charts and analytics

**Backend**
- Python 3.11, FastAPI + Uvicorn, Pydantic v2
- SQLAlchemy 2.x with SQLite (single file under data/), created automatically on first run
- JWT authentication (PyJWT) with bcrypt password hashing (passlib)
- python-dotenv for configuration; structured logging; automatic OpenAPI docs at /docs
- pytest for backend tests

**Data / ML / AI**
- scikit-learn / XGBoost for classical ML; PyTorch (+ torchvision) for deep learning; joblib for model files
- Google Gemini API through the official google-genai Python SDK for LLM features. Model name comes from .env (GEMINI_MODEL); default to the newest free-tier 'Flash' model available when you build (check Google AI Studio).
- pandas, NumPy, matplotlib (training plots saved as PNG)

**Specific to ForgetSafe**
- Flower (flwr), Opacus, Hugging Face Transformers + PEFT (LoRA), PyTorch, ReportLab (certificates)

---

## 8. Data and datasets

- **AG News** (Kaggle) - https://www.kaggle.com/datasets/amananandrai/ag-news-classification-dataset - 29.5 MB -> commit; split across simulated clients by a seeded script. (Also on Hugging Face: https://huggingface.co/datasets/fancyzhx/ag_news.)

**Dataset rules**
- If a dataset's total size is about 200 MB or less and no single file is over 100 MB, **commit the complete dataset** under `data/raw/`.
- Otherwise commit a **representative sample** under `data/sample/` (enough for the app and tests to run) **plus** `scripts/download_data.py`, which downloads the full dataset (Kaggle datasets via `kagglehub`, which uses the user's Kaggle API token), verifies it and places it in `data/raw/` (git-ignored for the full copy).
- Document every dataset in `docs/04_DATASET.md`: source link, licence, size, columns/classes, how it was cleaned, what is committed, and a step-by-step download guide (including how to create a Kaggle API token).
- Any data you generate (synthetic or simulated) must come from a committed, seeded generator script so it can be re-created exactly.

---

## 9. What you must get from the user (ask in Phase 2)

1. Kaggle account (GPU training) and API token.
2. Hugging Face account (model downloads) - token only if a gated model is chosen.

For each item, give numbered, beginner-friendly steps (which website, which button, what to copy, where to paste it), then **wait** until the user confirms. Check that each key or file works before moving on.

---

## 10. Workflow - follow in this order

**Phase 1 - Understand and plan (no code yet)**
1. Read this whole file. Check the machine: Windows version, Python (3.11 preferred), Node.js (LTS), Git, free disk space, and whether an NVIDIA GPU is present (not required - heavy training runs on Kaggle's free GPU). Tell the user what is missing and how to install it.
2. Write `docs/PLAN.md`: architecture (with a Mermaid diagram), module list mapped to features F1..Fn, database tables, API endpoints, ML pipeline, screens, milestones, risks.
3. Show the user a short summary of the plan and **stop**. Continue only after the user approves (they may ask for changes).

**Phase 2 - Requirements and guided setup**
1. Ask for every item in section 9, one group at a time, with step-by-step guidance.
   - **Kaggle GPU training.** Create Kaggle-ready notebooks in `notebooks/` (for example `notebooks/kaggle_train_<model>.ipynb`). Each reads data from `/kaggle/input/...`, trains on the GPU, and writes the model file, `metrics.json`, plots and the log to `/kaggle/working/`. Then guide the user:
     1. Sign in at kaggle.com and create a notebook. File -> Import Notebook -> choose the file from `notebooks/`.
     2. Add data -> search the dataset name from section 8 -> Add.
     3. Settings -> Accelerator -> GPU. Turn Internet on if the notebook installs packages.
     4. Run All. Wait for it to finish, then download everything from the Output panel.
     5. Put the model file into `models/` and the other files into `experiments/<run-name>/`.

     Then check the files load correctly and continue.
2. Create `.env.example` and help the user fill `.env`. Test every key or connection with a tiny script and report the result.
3. Confirm everything is ready and wait for **"proceed"**.

**Phase 3 - Foundations**
Project skeleton (section 11), `setup.bat` and `run.bat`, backend app with database, auth and seed data, frontend app shell with routing, theme and layout. Commit and push.

**Phase 4 - Data and AI/ML**
Data scripts, preprocessing, training (locally, or loading the files trained on Kaggle), evaluation, experiment artefacts, inference service with tests. Commit and push.

**Phase 5 - Features**
Build features F1..Fn end-to-end (API + UI) in the order from the plan. Commit and push after each major feature.

**Phase 6 - Landing page and polish**
The animated landing page, micro-interactions, responsive fixes, accessibility pass, empty/error states. Commit and push.

**Phase 7 - Test end-to-end**
Run backend tests, a production build of the frontend, and walk through the demo scenario in section 15 yourself. Fix everything you find. Commit and push.

**Phase 8 - Documentation and hand-over**
Write all docs (section 13) and the README. Copy `docs/03_HOW_TO_RUN.md` to `../18.FinalCodeExecutionSteps/HOW_TO_RUN.md`. Final commit and push. Give the user a short summary: how to run it, the demo login, and what each part does.

---

## 11. Folder structure

```
8.ProjectCode/
  backend/            FastAPI app (app/api, app/core, app/models, app/schemas, app/services, app/ml), tests/
  frontend/           React + Vite app (src/pages, src/components, src/components/reactbits, src/lib)
  ml/                 training and evaluation code
  notebooks/          notebooks (including Kaggle-ready ones)
  experiments/        one folder per training run: model file, metrics.json, plots, log
  models/             the model files the app loads
  data/               raw/ (full data if committed), sample/, processed/, app.db
  scripts/            download_data.py, generators, utilities
  docs/               all documentation (section 13)
  setup.bat  run.bat  .env.example  .gitignore  README.md
```

---

## 12. Frontend design brief

- **Brand:** a clean logo (SVG), a colour palette that fits the product's field, light and dark themes, a consistent type scale.
- **Landing page:**
  - an animated hero (a React Bits text or background effect) with a clear one-line value proposition and a "Get started" call to action;
  - GSAP ScrollTrigger reveals for the "How it works" steps and the feature grid, with Lenis smooth scrolling;
  - Motion micro-interactions on cards and buttons, and a footer.
- **App:** login and register, a sidebar layout, a dashboard with KPI cards and Recharts charts, then the feature screens from section 5. Use toasts, skeleton loaders and confirmation dialogs.
- **Motion quality:** animations must be smooth and purposeful, never block the user, and respect `prefers-reduced-motion`.
- **Responsive:** everything must work from 360 px phone width up to desktop.

---

## 13. Documentation (`docs/`) and README

Write each document separately, clearly, for someone new to the product:

| File | Contents |
|---|---|
| `docs/01_OVERVIEW.md` | What the product is, the problem, users, feature list |
| `docs/02_ARCHITECTURE.md` | How it works: architecture and data-flow diagrams (Mermaid), components, sequence of the main flows |
| `docs/03_HOW_TO_RUN.md` | Prerequisites, installation, `setup.bat` / `run.bat`, first login, stopping, resetting, running on a phone if relevant |
| `docs/04_DATASET.md` | Dataset sources, licences, schema, cleaning, what is committed, download guide |
| `docs/05_MODELS_AND_TRAINING.md` | Models, how they are trained (local steps / Kaggle notebook steps), settings, results tables, plots |
| `docs/06_API_REFERENCE.md` | Every endpoint with request and response examples |
| `docs/07_USER_GUIDE.md` | Screen-by-screen walkthrough of every feature |
| `docs/08_CONFIGURATION.md` | Every `.env` key, what it does and how to obtain it |
| `docs/09_TESTING.md` | Tests, how to run them, results, the demo scenario |
| `docs/10_TROUBLESHOOTING.md` | Common problems and fixes |
| `docs/11_PROJECT_STRUCTURE.md` | Folder-by-folder explanation of the code |

`README.md` in the root: product introduction, key features, quick start, demo login, and a **Documentation index for maintainers** linking every file above.

---

## 14. Git rules

- This folder sits inside a larger Git repository; `git rev-parse --show-toplevel` shows its root. **Stage only files inside this folder** - run `git add -A .` from this folder.
- Commit messages: **3-5 plain words** (for example "Add login and dashboard"). No message body, no co-author or AI-attribution lines.
- The author identity is already configured in the repository - never change any git config.
- Before every push: `git pull --rebase`, then `git push`. Never force-push. Commit and push at least after every phase in section 10.
- `.gitignore` in this folder must exclude `venv/`, `node_modules/`, `__pycache__/`, `.env`, `data/raw/` **only when** the full dataset is not being committed, and build output (`dist/`).
- Any single file over 100 MB (for example a large model) goes through Git LFS: `git lfs install`, then `git lfs track "<pattern>"`, and commit `.gitattributes`.

---

## 15. Definition of done

**Demo scenario - must run smoothly from a fresh `run.bat`:**
1. Dashboard shows 5 clients and the federated model's accuracy over rounds.
2. Client 3 submits a deletion request -> the unlearning run completes in a fraction of retraining time.
3. Verification: the membership-inference AUC for client 3 drops to about 0.5 and retained accuracy stays close to before.
4. Download the compliance certificate; the audit log shows the hash chain.

**Checklist**
- [ ] Every feature F1..Fn works end-to-end through the UI.
- [ ] Every model, AI component or optimisation engine is evaluated; metrics are visible in the product and in `docs/05_MODELS_AND_TRAINING.md`.
- [ ] `setup.bat` and `run.bat` work on a fresh Windows machine following `docs/03_HOW_TO_RUN.md`.
- [ ] Backend tests pass; the frontend production build succeeds.
- [ ] No placeholder text, no academic wording, no hard-coded secrets.
- [ ] All docs and the README are written, and `../18.FinalCodeExecutionSteps/HOW_TO_RUN.md` is copied.
- [ ] Everything is committed and pushed.
