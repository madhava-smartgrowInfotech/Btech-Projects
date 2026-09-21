# MASTER PROMPT - CivicPulse

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT.md completely and follow it exactly, starting with Phase 1."*
> Everything the session needs is inside this file.

---

## 0. Your role

You are the lead engineer and product designer for **CivicPulse** - AI decision support for public grievance offices - understands complaints in English, Hindi and Hinglish, predicts priority and resolution time, routes them to the right department and explains every suggestion.

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

- Officers manually analyse, prioritise and route large volumes of complaints.
- Urgent civic issues are delayed because prioritisation is inconsistent.
- Resolution times and resources are not planned using data.
- Existing systems give no explainable decision support.

**What is needed:** An explainable decision support system that classifies, prioritises and routes complaints while officers keep the final decision.

---

## 3. Who uses it

- Citizens filing and tracking complaints
- Grievance officers who review AI suggestions and decide
- Field staff who resolve assigned complaints
- Administrators who manage departments, SLAs and analytics

---

## 4. System evolution - understand this before designing

### 4.1 Reference system (published research this product builds on)

**A Generalized Spatio-Temporal Causal Knowledge Graph Framework With Large Language Model-Enhanced Reasoning for Urban Event Management** - IEEE Access, 2026 - https://doi.org/10.1109/access.2026.3699522

- A generalised spatio-temporal causal knowledge-graph framework for urban event management.
- Unstructured citizen complaints are processed with LLM-verified information extraction to pull out events, places and times.
- Reasoning over the causal knowledge graph assesses urgency and supports decisions about urban events.

### 4.2 Advanced system - the product specification (must be fully satisfied)

- NLP models classify complaints by category and extract key details.
- ML predicts priority and estimates resolution time.
- The system recommends the responsible department for each complaint.
- Explainable AI shows the reasons behind every recommendation, and officers make the final decision.
- Role-based modules support citizens, officers, field staff and administrators with real-time analytics.

Objectives the product must meet:

1. Classify citizen complaints automatically using NLP.
2. Predict complaint priority and estimate resolution time.
3. Recommend the responsible department for each complaint.
4. Explain every recommendation using XAI.
5. Keep officers in control through a human-in-the-loop workflow.
6. Provide real-time analytics for monitoring governance performance.

### 4.3 Latest approaches (2025-2026 state of the art)

- Indic multilingual transformers (MuRIL, IndicBERT, XLM-R) that handle Hindi, English and romanised Hinglish.
- LLM-based structured extraction (location, issue, affected people) with schema validation.
- Spatio-temporal hotspot detection and duplicate clustering of related complaints.
- Human-in-the-loop active learning: officer overrides become new training labels.

### 4.4 What you will build - CivicPulse (the latest, advanced, innovative system)

This combines the specification in 4.2 with the improvements below. Items marked **NEW** go beyond the specification.

- **F1 Complaint intake** - web form with text (English, Hindi, Hinglish), photo, and map location; tracking ID and status page for the citizen.
- **F2 Complaint understanding** - fine-tuned multilingual transformer classifies category and department; Gemini extracts key details (place, issue, affected people, duration) as structured fields.
- **F3 Priority prediction** - Low / Medium / High / Critical from text, urgency cues, category and history.
- **F4 Resolution-time estimate** - expected days to resolve, learned from real service-request patterns, with an SLA-breach risk flag (NEW).
- **F5 Department recommendation** - top-3 departments with confidence.
- **F6 Explanations** - LIME highlights the words behind the category; SHAP shows the factors behind priority and resolution time.
- **F7 Officer workbench (human in the loop)** - accept or override every suggestion with a reason; overrides are stored as new labels for retraining.
- **F8 Field-staff workflow** - assignment, status updates with photo proof, closure verification by the citizen.
- **F9 Duplicate and hotspot detection** (NEW) - similar complaints grouped; hotspot map of recurring issues by ward.
- **F10 Analytics** - volumes, SLA compliance, department performance, category trends, officer workload.
- **F11 Draft replies** (NEW) - Gemini drafts a polite status reply to the citizen in their language for the officer to edit.

---

## 5. Screens and user flows

1. Landing page
2. Login (citizen, officer, field staff, admin)
3. File a complaint
4. Track my complaints
5. Officer triage queue with AI suggestions and explanations
6. Complaint detail (history, override, draft reply)
7. Field-staff tasks
8. Hotspot map
9. Analytics dashboard
10. Admin: departments, SLAs, users
11. Model performance

Every screen needs loading, empty and error states, and must work on a phone-sized screen.

---

## 6. AI / ML components

- Kaggle GPU: fine-tune a multilingual transformer (for example `google/muril-base-cased`; fallback `distilbert-base-multilingual-cased`) for category and department; TF-IDF + Logistic Regression as the baseline.
- Local CPU: priority classifier and resolution-time regressor (XGBoost) on text embeddings plus metadata; LIME / SHAP explanations.
- Report accuracy, macro-F1 and a confusion matrix per task, MAE for resolution time, and the gain over the baseline.

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

**Specific to CivicPulse**
- Hugging Face Transformers, XGBoost, SHAP, LIME, sentence-transformers (duplicates), Leaflet (maps)
- Replaces the original plan's Django / PostgreSQL / MySQL option with FastAPI + SQLite.

---

## 8. Data and datasets

- **Citizen Grievance Dataset** (Kaggle) - https://www.kaggle.com/datasets/abhisheksingh016/citizen-grievance-dataset - 0.7 MB, CC0; Hindi, Hinglish and English grievances labelled by department -> commit.
- **Indian Citizen Complaint** (Kaggle) - https://www.kaggle.com/datasets/shebinsam2004/indian-citizen-complaint - 4.2 MB, MIT -> commit.
- **CivicComp-HiEn: Hindi-English Civic Complaints** (Kaggle) - https://www.kaggle.com/datasets/shyamtripathi373/civiccomp-hien-hindienglish-civic-complaints - 1.2 GB, CC BY-SA 4.0; real bilingual civic complaints -> commit a sample plus the download script; use the full set inside the Kaggle notebook.
- **NYC 311 Service Requests** (open data API, no key) - https://data.cityofnewyork.us/resource/erm2-nwe9.json - created/closed dates by complaint type; the download script pulls about 200k recent rows to learn realistic resolution-time patterns per category -> commit the extract if under the size rule.
- **Workflow data** - a committed, seeded generator for wards, departments, officers and complaint histories.

**Dataset rules**
- If a dataset's total size is about 200 MB or less and no single file is over 100 MB, **commit the complete dataset** under `data/raw/`.
- Otherwise commit a **representative sample** under `data/sample/` (enough for the app and tests to run) **plus** `scripts/download_data.py`, which downloads the full dataset (Kaggle datasets via `kagglehub`, which uses the user's Kaggle API token), verifies it and places it in `data/raw/` (git-ignored for the full copy).
- Document every dataset in `docs/04_DATASET.md`: source link, licence, size, columns/classes, how it was cleaned, what is committed, and a step-by-step download guide (including how to create a Kaggle API token).
- Any data you generate (synthetic or simulated) must come from a committed, seeded generator script so it can be re-created exactly.

---

## 9. What you must get from the user (ask in Phase 2)

1. Kaggle account (GPU training and downloads) and API token.
2. Gemini API key - https://aistudio.google.com/apikey
3. Confirm the department list and SLA days (defaults: Roads, Water Supply, Sanitation, Electricity, Health, Revenue, Public Safety, Town Planning).
4. Confirm languages (default: English, Hindi, Hinglish input; English, Hindi, Telugu replies).

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
1. A citizen files 'सड़क पर बड़ा गड्ढा है, दो दिन से पानी भरा है' with a photo and location -> gets a tracking ID.
2. The officer queue shows: Roads, High priority, about 4 days, with highlighted words and SHAP factors -> the officer accepts.
3. Field staff close it with a photo; the citizen confirms; the analytics and hotspot map update.
4. The officer overrides a wrong department -> the override appears in the retraining set.

**Checklist**
- [ ] Every feature F1..Fn works end-to-end through the UI.
- [ ] Every model, AI component or optimisation engine is evaluated; metrics are visible in the product and in `docs/05_MODELS_AND_TRAINING.md`.
- [ ] `setup.bat` and `run.bat` work on a fresh Windows machine following `docs/03_HOW_TO_RUN.md`.
- [ ] Backend tests pass; the frontend production build succeeds.
- [ ] No placeholder text, no academic wording, no hard-coded secrets.
- [ ] All docs and the README are written, and `../18.FinalCodeExecutionSteps/HOW_TO_RUN.md` is copied.
- [ ] Everything is committed and pushed.
