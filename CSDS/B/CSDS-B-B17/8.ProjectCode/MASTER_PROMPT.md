# MASTER PROMPT - CallSense

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT.md completely and follow it exactly, starting with Phase 1."*
> Everything the session needs is inside this file.

---

## 0. Your role

You are the lead engineer and product designer for **CallSense** - analyses every customer call automatically - transcripts, intent, sentiment and voice emotion, summaries and agent scorecards, plus live assist during calls.

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
11. **Fixed ports - other products may be running on this PC at the same time.** Backend API: **8217**. Frontend dev server: **5217**. Any extra local service (simulators, extra servers, test targets, worker UIs) uses a port in **12170-12179**. Put them in `.env` / `.env.example` and `vite.config.ts` (with `strictPort: true`); never use the defaults 8000 / 5173.

---

## 2. The problem

- Organisations review only a small sample of calls manually.
- Manual monitoring is slow, subjective and costly.
- Customer emotion, intent and issues are not captured systematically.
- Insights arrive too late for timely decisions.

**What is needed:** An AI system that analyses every call automatically and delivers real-time insights on customers and agents.

---

## 3. Who uses it

- Contact-centre supervisors and QA teams
- Customer-support agents
- Customer-experience and operations managers

---

## 4. System evolution - understand this before designing

### 4.1 Reference system (published research this product builds on)

**AI-Based Conversational Agents: A Scoping Review From Technologies to Future Directions** - IEEE Access, 2022 - https://doi.org/10.1109/access.2022.3201144

- A scoping review of AI-based conversational agents, from technologies to future directions.
- Covers NLP and natural-language understanding, dialogue management and deep-learning models behind conversational systems.
- Discusses sentiment and emotion modelling and how conversational AI is evaluated.

### 4.2 Advanced system - the product specification (must be fully satisfied)

- Speech-to-text converts voice calls into transcripts.
- NLP identifies intent, extracts keywords and classifies call topics.
- Sentiment analysis detects customer emotions during the call.
- The system generates concise call summaries and evaluates agent performance.
- Interactive dashboards present real-time call analytics.

Objectives the product must meet:

1. Convert customer calls into text using speech recognition.
2. Identify customer intent and classify call topics.
3. Detect customer sentiment and emotion.
4. Generate concise call summaries automatically.
5. Evaluate agent performance.
6. Provide real-time analytics dashboards.

### 4.3 Latest approaches (2025-2026 state of the art)

- Whisper-class speech recognition running on CPU (faster-whisper).
- Speaker separation and diarization for agent / customer turns.
- Transformer intent and sentiment models, and speech emotion recognition (wav2vec2-style).
- LLM call summaries, QA scorecards and real-time agent assist.

### 4.4 What you will build - CallSense (the latest, advanced, innovative system)

This combines the specification in 4.2 with the improvements below. Items marked **NEW** go beyond the specification.

- **F1 Call ingestion** - upload recordings (wav / mp3, mono or stereo) singly or in bulk; live microphone call mode.
- **F2 Transcription** - faster-whisper with timestamps; agent / customer separation by stereo channel or speaker-embedding clustering.
- **F3 Intent and topics** - customer-support intent classification (27 intents) and keywords.
- **F4 Sentiment and emotion** - text sentiment plus voice emotion per segment -> emotion timeline; escalation detection.
- **F5 Summaries** - Gemini summary: reason for call, resolution, action items.
- **F6 Agent scorecard** - greeting, empathy, script compliance, talk/listen ratio, silence, interruptions, resolution, sentiment change -> score with evidence.
- **F7 Live assist** (NEW) - live transcript, live sentiment and suggested replies during a call.
- **F8 PII redaction** (NEW) - card numbers, phone numbers and emails masked in transcripts.
- **F9 Analytics** - volumes, top intents, sentiment trends, agent leaderboard, search across calls.
- **F10 Sample call studio** (NEW) - generates realistic sample calls from scripts with two offline text-to-speech voices, clearly labelled as samples.

---

## 5. Screens and user flows

1. Landing page
2. Login (supervisor, agent, admin)
3. Calls list and upload
4. Call detail (player, transcript, emotion timeline, summary, scorecard)
5. Live assist
6. Agents and scorecards
7. Analytics
8. Sample call studio
9. Model performance

Every screen needs loading, empty and error states, and must work on a phone-sized screen.

---

## 6. AI / ML components

- Kaggle GPU: DistilBERT intent classifier (Bitext), speech-emotion model (wav2vec2-base fine-tune or CNN on log-mel features) on RAVDESS + CREMA-D, text-sentiment model on the call-centre transcripts.
- Report intent accuracy / macro-F1, emotion accuracy / unweighted average recall, sentiment F1, and transcription word error rate on the sample calls.

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

**Specific to CallSense**
- faster-whisper (CPU int8), librosa, Hugging Face Transformers, speaker embeddings (resemblyzer or speechbrain), Piper (offline text-to-speech) - https://github.com/OHF-Voice/piper1-gpl
- Browser MediaRecorder + FastAPI WebSockets for live audio
- Replaces the original plan's Streamlit / Dash + MongoDB / PostgreSQL with React + SQLite.

---

## 8. Data and datasets

- **Bitext Customer Support Dataset** (Kaggle) - https://www.kaggle.com/datasets/bitext/bitext-gen-ai-chatbot-customer-support-dataset - 18.3 MB, CDLA-Sharing-1.0 -> commit.
- **Call Center Transcripts Dataset** (Kaggle) - https://www.kaggle.com/datasets/oleksiymaliovanyy/call-center-transcripts-dataset - 20.9 MB, MIT -> commit.
- **RAVDESS Emotional Speech Audio** (Kaggle) - https://www.kaggle.com/datasets/uwrfkaggler/ravdess-emotional-speech-audio - 563 MB, CC BY-NC-SA 4.0 -> sample plus script.
- **CREMA-D** (Kaggle) - https://www.kaggle.com/datasets/ejlok1/cremad - 578 MB, ODC-By -> sample plus script.
- **Sample calls** generated by F10 (committed).

**Dataset rules**
- If a dataset's total size is about 200 MB or less and no single file is over 100 MB, **commit the complete dataset** under `data/raw/`.
- Otherwise commit a **representative sample** under `data/sample/` (enough for the app and tests to run) **plus** `scripts/download_data.py`, which downloads the full dataset (Kaggle datasets via `kagglehub`, which uses the user's Kaggle API token), verifies it and places it in `data/raw/` (git-ignored for the full copy).
- Document every dataset in `docs/04_DATASET.md`: source link, licence, size, columns/classes, how it was cleaned, what is committed, and a step-by-step download guide (including how to create a Kaggle API token).
- Any data you generate (synthetic or simulated) must come from a committed, seeded generator script so it can be re-created exactly.

---

## 9. What you must get from the user (ask in Phase 2)

1. Kaggle account (GPU training) and API token.
2. Gemini API key - https://aistudio.google.com/apikey
3. A microphone for live mode.
4. Optional: a few real call recordings shared with consent.

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

Other Claude Code sessions may be building other products in sibling folders of the same repository **at the same time**. Touch only this folder.

- **Commit only this folder.** From this folder run `git add -A .` and then `git commit -m "<message>" -- .` - the `-- .` keeps anything other sessions have staged out of your commit. Never run a bare `git commit`.
- Commit messages: **3-5 plain words** (for example "Add login and dashboard"). No message body, no co-author or AI-attribution lines.
- The author identity is already configured in the repository - never change any git config.
- **Push** with `git push` after every commit. All sessions share one local branch, so it already contains everyone's commits and no pull is normally needed. If the push is rejected because the remote has newer commits, run `git pull --rebase --autostash` only when `git status` shows no changes outside this folder; otherwise wait a minute and try again, and ask the user if it keeps failing.
- If git reports `index.lock` or "another git process", another session is committing: wait 10 seconds and retry (up to 5 times). Never delete `.git/index.lock` yourself.
- **Never** run commands that change files outside this folder or rewrite history: no `git stash`, `git reset`, `git checkout`, `git restore`, `git clean`, `git rebase` (other than the pull above) and never `git push --force`.
- The one exception to "only this folder" is Phase 8: name `../18.FinalCodeExecutionSteps/HOW_TO_RUN.md` explicitly in both commands - `git add -A . ../18.FinalCodeExecutionSteps/HOW_TO_RUN.md` and `git commit -m "<message>" -- . ../18.FinalCodeExecutionSteps/HOW_TO_RUN.md`.
- `.gitignore` in this folder must exclude `venv/`, `node_modules/`, `__pycache__/`, `.env`, `data/raw/` **only when** the full dataset is not being committed, and build output (`dist/`).
- A single file over 100 MB (for example a large model) needs Git LFS: ask the user first, then `git lfs track "<pattern>"` from this folder and commit the `.gitattributes` it creates here.

---

## 15. Definition of done

**Demo scenario - must run smoothly from a fresh `run.bat`:**
1. Upload a sample 'refund request' call -> transcript split by speaker, intent 'get_refund', emotion timeline showing frustration then relief.
2. The summary and agent scorecard (82/100) appear with evidence.
3. Start live assist and talk into the microphone -> live transcript, sentiment and suggested replies.
4. Analytics show top intents and the agent leaderboard; card numbers are masked.

**Checklist**
- [ ] Every feature F1..Fn works end-to-end through the UI.
- [ ] Every model, AI component or optimisation engine is evaluated; metrics are visible in the product and in `docs/05_MODELS_AND_TRAINING.md`.
- [ ] `setup.bat` and `run.bat` work on a fresh Windows machine following `docs/03_HOW_TO_RUN.md`.
- [ ] Backend tests pass; the frontend production build succeeds.
- [ ] No placeholder text, no academic wording, no hard-coded secrets.
- [ ] It runs on its own ports (8217 / 5217) while other products run on the same PC.
- [ ] All docs and the README are written, and `../18.FinalCodeExecutionSteps/HOW_TO_RUN.md` is copied.
- [ ] Everything is committed and pushed.
