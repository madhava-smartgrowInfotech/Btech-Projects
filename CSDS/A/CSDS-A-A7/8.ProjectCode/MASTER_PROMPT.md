# MASTER PROMPT - SHEGUARD

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT.md completely and follow it exactly, starting with Phase 1."*
> Everything the session needs is inside this file.

---

## 0. Your role

You are the lead engineer and product designer for **SHEGUARD** - a women's safety companion that helps choose safer routes, triggers help hands-free and keeps trusted people informed with live location and evidence.

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

- Women face safety threats in both isolated and crowded public places.
- Existing apps require manual SOS activation, which is difficult in an emergency.
- Most solutions stop at sending an alert and do not support prevention or follow-up.
- Emergency evidence is rarely captured or stored securely.

**What is needed:** A safety platform that helps prevent risk, activates help with minimal effort, keeps guardians informed and preserves evidence.

---

## 3. Who uses it

- Women travelling alone or at night
- Guardians (family, friends) who receive alerts and live location
- Community members reporting unsafe spots (moderated)

---

## 4. System evolution - understand this before designing

### 4.1 Reference system (published research this product builds on)

**SafeRoutes: Charting a Secure Path-A Holistic Approach to Women's Safety Through Advanced Clustering and GPS Integration** - IEEE Access, 2024 - https://doi.org/10.1109/access.2024.3488784

- SafeRoutes: a holistic approach to women's safety through advanced clustering and GPS.
- A data pipeline from public/government sources; unsupervised clustering of regions using crime rates, police presence and infrastructure.
- Integration with map APIs and cab vendors to raise real-time alerts when a trip deviates into unsafe areas.

### 4.2 Advanced system - the product specification (must be fully satisfied)

- Safe Route guidance helps users choose safer travel routes using available safety information.
- SafePhrase voice activation and Smart SOS trigger an emergency with minimal actions.
- An emergency session shares live location with trusted guardians in real time.
- Timestamps, location details and audio or image evidence are stored securely.
- Gemini-based AI assistance and community safety reports support users, with data protected by Row Level Security.

Objectives the product must meet:

1. Provide Safe Route guidance using available safety information.
2. Enable quick emergency activation through SafePhrase and Smart SOS.
3. Share live location with trusted guardians during an emergency session.
4. Preserve emergency evidence such as timestamps, location, audio and images securely.
5. Offer AI-powered safety assistance using the Gemini API.
6. Protect user data with role-based access and Row Level Security.

### 4.3 Latest approaches (2025-2026 state of the art)

- Route safety scoring that combines crime density, time of day and community reports.
- Hands-free emergency triggers: voice keywords, shake detection and one-tap SOS.
- Live location streaming over WebSockets with a shareable tracking page.
- Tamper-evident evidence capture (hashing) and installable PWAs on phones.

### 4.4 What you will build - SHEGUARD (the latest, advanced, innovative system)

This combines the specification in 4.2 with the improvements below. Items marked **NEW** go beyond the specification.

- **F1 Safe Route** - routes from the free OSRM service, scored by area risk and time of day; the safest option is recommended on a Leaflet map.
- **F2 Area risk model** - clustering (K-Means / DBSCAN) of districts from the Kaggle crime datasets; heat layer on the map.
- **F3 Emergency triggers** - SafePhrase voice trigger (Web Speech API), one-tap Smart SOS, and shake-to-SOS via DeviceMotion (NEW).
- **F4 Emergency session with live location** - streams the position to guardians over WebSockets; guardians open a live tracking page.
- **F5 Free alerts** - Telegram bot message and email (Gmail SMTP) to guardians with the live-tracking link, plus in-app alerts.
- **F6 Evidence capture** (NEW) - short audio/photo evidence uploaded with timestamp, location and SHA-256 hash (tamper-evident).
- **F7 AI safety assistant** - Gemini-powered chat for safety guidance and nearby help.
- **F8 Community safety reports** - users mark unsafe spots; admin moderation; reports feed the risk score.
- **F9 Route deviation check-in** (NEW) - if the user leaves the chosen route, the app asks 'Are you safe?' and escalates if there is no answer.
- **F10 Installable PWA** - home-screen icon, full-screen app, offline shell.

---

## 5. Screens and user flows

1. Landing page
2. Login / register
3. Home (SOS button, status)
4. Safe Route planner
5. Emergency session (live map, evidence, cancel)
6. Guardian live-tracking page
7. Guardians management (Telegram / email)
8. Community reports map
9. AI assistant
10. Admin moderation

Every screen needs loading, empty and error states, and must work on a phone-sized screen.

---

## 6. AI / ML components

- Clustering of district crime statistics (scikit-learn) into risk tiers, trained locally; time-of-day weighting; report the cluster profiles in the product.
- Gemini for the assistant. No deep-learning training required.

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

**Specific to SHEGUARD**
- Installable PWA (vite-plugin-pwa), FastAPI WebSockets, Leaflet + OSRM public routing (https://router.project-osrm.org), Web Speech API, DeviceMotion API
- Free alerts: Telegram Bot API (bot from @BotFather) + email via Gmail SMTP (app password)
- Cloudflare quick tunnel for HTTPS on phones (section 10, Phase 2)
- Replaces the original plan's Flutter + Supabase with a PWA + FastAPI + SQLite, with the same features.

---

## 8. Data and datasets

- **Crime in India** (Kaggle) - https://www.kaggle.com/datasets/rajanand/crime-in-india - 4.4 MB -> commit.
- **Crimes against women in India 2001-2021** (Kaggle) - https://www.kaggle.com/datasets/balajivaraprasad/crimes-against-women-in-india-2001-2021 -> commit.
- District coordinates: geocode district names once through OpenStreetMap Nominatim (respect 1 request/second) and commit the cached CSV.

**Dataset rules**
- If a dataset's total size is about 200 MB or less and no single file is over 100 MB, **commit the complete dataset** under `data/raw/`.
- Otherwise commit a **representative sample** under `data/sample/` (enough for the app and tests to run) **plus** `scripts/download_data.py`, which downloads the full dataset (Kaggle datasets via `kagglehub`, which uses the user's Kaggle API token), verifies it and places it in `data/raw/` (git-ignored for the full copy).
- Document every dataset in `docs/04_DATASET.md`: source link, licence, size, columns/classes, how it was cleaned, what is committed, and a step-by-step download guide (including how to create a Kaggle API token).
- Any data you generate (synthetic or simulated) must come from a committed, seeded generator script so it can be re-created exactly.

---

## 9. What you must get from the user (ask in Phase 2)

1. Gemini API key - https://aistudio.google.com/apikey
2. Telegram bot token from @BotFather and each guardian's chat ID (guided: https://core.telegram.org/bots/tutorial).
3. Gmail address + app password for email alerts (guided).
4. An Android phone with Chrome for testing; install `cloudflared` (guided).

For each item, give numbered, beginner-friendly steps (which website, which button, what to copy, where to paste it), then **wait** until the user confirms. Check that each key or file works before moving on.

---

## 10. Workflow - follow in this order

**Phase 1 - Understand and plan (no code yet)**
1. Read this whole file. Check the machine: Windows version, Python (3.11 preferred), Node.js (LTS), Git, free disk space. Tell the user what is missing and how to install it.
2. Write `docs/PLAN.md`: architecture (with a Mermaid diagram), module list mapped to features F1..Fn, database tables, API endpoints, ML pipeline, screens, milestones, risks.
3. Show the user a short summary of the plan and **stop**. Continue only after the user approves (they may ask for changes).

**Phase 2 - Requirements and guided setup**
1. Ask for every item in section 9, one group at a time, with step-by-step guidance.
   - **Model training runs locally** on this PC (CPU is enough): prepare `ml/train_*.py` scripts; they run in Phase 4.
   - **Phone access (camera, GPS, microphone need HTTPS):** guide the user to install Cloudflare's free quick tunnel (`winget install --id Cloudflare.cloudflared`). Configure the Vite dev server to proxy `/api` (and WebSockets) to the backend and to accept the tunnel host, then `cloudflared tunnel --url http://localhost:5173` gives an `https://...trycloudflare.com` link to open on the phone. Add a `run_phone.bat` that starts everything plus the tunnel and prints the link. No account is needed.
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
1. Install the PWA on a phone via the HTTPS link; add a guardian (Telegram + email).
2. Plan a route -> safest route highlighted with a risk explanation.
3. Say the SafePhrase -> emergency session starts -> guardian gets Telegram and email with the live link and watches the location move.
4. Capture evidence -> it appears with a hash; leave the route -> 'Are you safe?' check-in; cancel the emergency.

**Checklist**
- [ ] Every feature F1..Fn works end-to-end through the UI.
- [ ] Every model, AI component or optimisation engine is evaluated; metrics are visible in the product and in `docs/05_MODELS_AND_TRAINING.md`.
- [ ] `setup.bat` and `run.bat` work on a fresh Windows machine following `docs/03_HOW_TO_RUN.md`.
- [ ] Backend tests pass; the frontend production build succeeds.
- [ ] No placeholder text, no academic wording, no hard-coded secrets.
- [ ] All docs and the README are written, and `../18.FinalCodeExecutionSteps/HOW_TO_RUN.md` is copied.
- [ ] Everything is committed and pushed.
