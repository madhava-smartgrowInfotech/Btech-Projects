# MASTER PROMPT - UPI Guardian

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT.md completely and follow it exactly, starting with Phase 1."*
> Everything the session needs is inside this file.

---

## 0. Your role

You are the lead engineer and product designer for **UPI Guardian** - stops UPI fraud before the money leaves - real-time payment risk scoring, scam-SMS checks, intent verification, a protective hold on risky payments and spoken warnings in English, Hindi and Telugu.

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

- UPI fraud through phishing, fake requests, QR scams and social engineering is rising.
- Existing systems detect fraud only after money is transferred.
- Users approve fraudulent payments themselves when they are tricked.
- Warnings are generic, unexplained and mostly in English.

**What is needed:** A preventive framework that assesses payment risk in real time and helps users stop fraud before it happens.

---

## 3. Who uses it

- UPI users, especially first-time digital payment users and elderly people
- Family members who act as trusted contacts
- Fraud-risk teams monitoring scam trends

---

## 4. System evolution - understand this before designing

### 4.1 Reference system (published research this product builds on)

**Hybrid Contrastive Learning With Attention-Based Neural Networks for Robust Fraud Detection in Digital Payment Systems** - IEEE Open Journal of the Computer Society, 2025 - https://doi.org/10.1109/ojcs.2025.3581950

- A hybrid contrastive-learning (Siamese) and attention-based neural network for fraud detection in digital payment systems.
- Contrastive pairs make the model robust to heavy class imbalance and evolving fraud patterns.
- SHAP explains which transaction features drive each fraud decision.

### 4.2 Advanced system - the product specification (must be fully satisfied)

- AI risk analysis scores each payment using transaction behaviour, payment history, receiver trust score and suspicious SMS indicators.
- Smart Payment Intent Verification asks users to confirm the purpose of high-risk payments.
- Delayed Protection Mode briefly holds high-risk transfers so users can reconsider.
- Explainable AI tells users why a payment was flagged.
- Personalised multilingual voice assistance in English, Hindi and Telugu guides users.

Objectives the product must meet:

1. Score UPI payment risk using transaction behaviour, history, receiver trust and SMS signals.
2. Detect suspicious SMS and payment requests with NLP.
3. Verify payment intent for high-risk transactions.
4. Hold high-risk payments temporarily through Delayed Protection Mode.
5. Explain risk decisions to users with explainable AI.
6. Provide voice assistance in English, Hindi and Telugu.

### 4.3 Latest approaches (2025-2026 state of the art)

- Pre-transaction (real-time) risk scoring instead of after-the-fact detection.
- Behavioural signals: amount vs usual, new payee, velocity, time of day, payee reputation.
- NLP scam-message detection covering Indian scam patterns (fake KYC, refunds, lottery, collect-request tricks).
- Risk-based friction: step-up confirmation, cooling-off holds, trusted-contact approval, explainable warnings.

### 4.4 What you will build - UPI Guardian (the latest, advanced, innovative system)

This combines the specification in 4.2 with the improvements below. Items marked **NEW** go beyond the specification.

- **F1 UPI sandbox** - demo wallets with UPI IDs: send money, scan-and-pay QR, collect requests (approve/decline), history. Clearly labelled as a sandbox; no real money moves.
- **F2 Real-time risk engine** - every payment is scored before confirmation from behaviour, history, payee trust and SMS signals.
- **F3 Payee trust score** - payee account age, received-payment patterns and community scam reports (NEW).
- **F4 Suspicious SMS check** - the user pastes an SMS; NLP classifier + scam-pattern rules give a verdict with highlighted phrases; a scam SMS raises the risk of related payments.
- **F5 Payment-intent verification** - for risky payments, asks the purpose ('Are you expecting a refund?') and branches into scam-specific warnings.
- **F6 Delayed Protection Mode** - holds high-risk payments for a configurable cooling-off time; cancel anytime; optional trusted-contact approval (NEW).
- **F7 Explainable warnings** - SHAP top reasons turned into plain language.
- **F8 Voice assistant** - spoken warnings and guidance in English, Hindi and Telugu (gTTS), plus translated UI text.
- **F9 Collect-request and QR guard** (NEW) - detects 'you will receive money' tricks that are really debit requests.
- **F10 Fraud analytics** (NEW) - admin view of blocked/held payments, scam types and trends.

---

## 5. Screens and user flows

1. Landing page
2. Login / register
3. Wallet home (balance, UPI ID, QR)
4. Send / scan / collect flows with the risk panel
5. Intent check and hold screens
6. SMS check
7. Payment history with risk reasons
8. Trusted contacts and settings (language, hold time)
9. Admin fraud analytics
10. Model performance

Every screen needs loading, empty and error states, and must work on a phone-sized screen.

---

## 6. AI / ML components

- Local CPU: risk model (XGBoost, compared with Logistic Regression and Random Forest) with time-based validation; report precision, recall, F1 and PR-AUC; SHAP explanations.
- SMS classifier: TF-IDF (word + character n-grams) + linear model as the baseline and a small transformer if it helps; trained on the SMS Spam Collection plus a labelled set of Indian UPI-scam messages (English, Hindi, Telugu) that you write and commit.

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

**Specific to UPI Guardian**
- Installable PWA (vite-plugin-pwa), XGBoost, SHAP, gTTS (Hindi and Telugu voices), qrcode + html5-qrcode (QR scanning)
- Cloudflare quick tunnel for HTTPS on phones (section 10, Phase 2)
- Replaces the original plan's Flutter / React Native app with an installable PWA.

---

## 8. Data and datasets

- **Digital Payment Fraud Detection Benchmark** (Kaggle) - https://www.kaggle.com/datasets/rohit8527kmr7518/digital-payment-fraud-detection-benchmark - 57.8 MB, CC0; 400k transactions with temporal drift -> commit.
- **UPI Transactions 2024** (Kaggle) - https://www.kaggle.com/datasets/skullagos5246/upi-transactions-2024-dataset - 28.4 MB, CC0 -> commit; use its fraud label if present, otherwise for behaviour profiles.
- **SMS Spam Collection** (Kaggle mirror of UCI) - https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset (UCI: https://archive.ics.uci.edu/dataset/228/sms+spam+collection) -> commit.
- **Indian UPI-scam SMS set** - written by you, labelled, committed.

**Dataset rules**
- If a dataset's total size is about 200 MB or less and no single file is over 100 MB, **commit the complete dataset** under `data/raw/`.
- Otherwise commit a **representative sample** under `data/sample/` (enough for the app and tests to run) **plus** `scripts/download_data.py`, which downloads the full dataset (Kaggle datasets via `kagglehub`, which uses the user's Kaggle API token), verifies it and places it in `data/raw/` (git-ignored for the full copy).
- Document every dataset in `docs/04_DATASET.md`: source link, licence, size, columns/classes, how it was cleaned, what is committed, and a step-by-step download guide (including how to create a Kaggle API token).
- Any data you generate (synthetic or simulated) must come from a committed, seeded generator script so it can be re-created exactly.

---

## 9. What you must get from the user (ask in Phase 2)

1. Kaggle account and API token (download script).
2. An Android phone with Chrome to install the PWA; install `cloudflared` (guided).
3. Confirm defaults: hold time 30 minutes for high risk, risk thresholds, languages English / Hindi / Telugu.

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
1. Install the PWA on a phone; pay a known contact a normal amount -> Low risk, paid instantly.
2. Paste 'Your KYC expires today, click link...' -> Scam, with highlighted phrases and a spoken Hindi warning.
3. Try paying 25,000 to a new payee at night -> High risk: intent check, SHAP reasons, payment held; cancel it.
4. Approve a 'collect request' disguised as a refund -> the guard warns that this will debit money.

**Checklist**
- [ ] Every feature F1..Fn works end-to-end through the UI.
- [ ] Every model, AI component or optimisation engine is evaluated; metrics are visible in the product and in `docs/05_MODELS_AND_TRAINING.md`.
- [ ] `setup.bat` and `run.bat` work on a fresh Windows machine following `docs/03_HOW_TO_RUN.md`.
- [ ] Backend tests pass; the frontend production build succeeds.
- [ ] No placeholder text, no academic wording, no hard-coded secrets.
- [ ] All docs and the README are written, and `../18.FinalCodeExecutionSteps/HOW_TO_RUN.md` is copied.
- [ ] Everything is committed and pushed.
