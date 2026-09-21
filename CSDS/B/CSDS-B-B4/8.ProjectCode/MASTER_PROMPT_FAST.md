# MASTER PROMPT (FAST BUILD) - UPI Guardian

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (download script).
> - An Android phone with Chrome to install the PWA; install `cloudflared` (guided).
> - Confirm defaults: hold time 30 minutes for high risk, risk thresholds, languages English / Hindi / Telugu.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **UPI Guardian** - stops UPI fraud before the money leaves - real-time payment risk scoring, scam-SMS checks, intent verification, a protective hold on risky payments and spoken warnings in English, Hindi and Telugu.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8204**, frontend **5204** (`strictPort: true`). Any extra local service uses a port in **12040-12049**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

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

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Hybrid Contrastive Learning With Attention-Based Neural Networks for Robust Fraud Detection in Digital Payment Systems** - IEEE Open Journal of the Computer Society, 2025 - https://doi.org/10.1109/ojcs.2025.3581950

- A hybrid contrastive-learning (Siamese) and attention-based neural network for fraud detection in digital payment systems.
- Contrastive pairs make the model robust to heavy class imbalance and evolving fraud patterns.
- SHAP explains which transaction features drive each fraud decision.

### 4.2 Advanced system (the specification - every point must be met)

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

### 4.3 Latest approaches
- Pre-transaction (real-time) risk scoring instead of after-the-fact detection.
- Behavioural signals: amount vs usual, new payee, velocity, time of day, payee reputation.
- NLP scam-message detection covering Indian scam patterns (fake KYC, refunds, lottery, collect-request tricks).
- Risk-based friction: step-up confirmation, cooling-off holds, trusted-contact approval, explainable warnings.

### 4.4 What you will build - UPI Guardian
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 UPI sandbox** - demo wallets with UPI IDs: send money, scan-and-pay QR, and collect requests. Clearly labelled as a sandbox; no real money moves.
- **F2 Real-time risk engine** - every payment is scored before confirmation from behaviour (amount vs usual, new payee, velocity, time), history and payee trust.
- **F3 Payee trust score** - account age, received-payment patterns and past reports.
- **F4 Suspicious SMS check** - the user pastes an SMS; a classifier plus scam-pattern rules give a verdict with the phrases highlighted, and that raises the risk of a related payment.
- **F5 Payment-intent verification** - risky payments ask what the payment is for, then warn about the matching scam pattern.
- **F6 Delayed Protection Mode** - high-risk payments are held for a cooling-off period and can be cancelled.
- **F7 Explained warnings** - SHAP's top reasons written in plain language.
- **F8 Voice assistance** - spoken warnings in English, Hindi and Telugu.

### 4.5 Data

- **Digital Payment Fraud Detection Benchmark** (Kaggle) - https://www.kaggle.com/datasets/rohit8527kmr7518/digital-payment-fraud-detection-benchmark - 57.8 MB, CC0; 400k transactions with temporal drift -> commit.
- **UPI Transactions 2024** (Kaggle) - https://www.kaggle.com/datasets/skullagos5246/upi-transactions-2024-dataset - 28.4 MB, CC0 -> commit; use its fraud label if present, otherwise for behaviour profiles.
- **SMS Spam Collection** (Kaggle mirror of UCI) - https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset (UCI: https://archive.ics.uci.edu/dataset/228/sms+spam+collection) -> commit.
- **Indian UPI-scam SMS set** - written by you, labelled, committed.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Wallet home (balance, UPI ID, QR)
4. Send / scan / collect with the risk panel
5. Intent check and hold screens
6. SMS check
7. History with risk reasons
8. Settings (language, hold time)

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to UPI Guardian:** XGBoost + SHAP for the risk model, scikit-learn for the SMS classifier, gTTS for Hindi/Telugu/English voice warnings, qrcode + html5-qrcode for the QR flows, installable PWA (vite-plugin-pwa). Cloudflare quick tunnel for HTTPS on the phone.
- **Training:** The model(s) train **locally on CPU in M1** with small, fast configs (few epochs / a data subset) - accuracy just needs to be good enough to demo, not to top a benchmark. Save the model file plus a `metrics.json` under `experiments/`.

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

**M1 - Backend and core logic.** Project skeleton, `setup.bat` (venv + pip + `npm install`), backend with login and the database, then the data/model pipeline and every feature endpoint from section 4.4. Train the model(s) here with a small, fast config and save the metrics. `scripts/smoke_test.py` drives the running API through the main flow end-to-end and must pass. Commit and push.

**M2 - Frontend.** The screens in section 5 wired to the API. `run.bat` starts the backend and frontend and opens the browser. Then set up phone access: install Cloudflare's free quick tunnel (`winget install --id Cloudflare.cloudflared`), make the Vite dev server accept the tunnel host and proxy `/api` (and WebSockets) to the backend, and add a `run_phone.bat` that starts everything plus the tunnel and prints the `https://...trycloudflare.com` link. No account is needed. Commit and push.

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
1. Install the PWA on a phone; pay a known contact a normal amount -> Low risk, paid instantly.
2. Paste a 'your KYC expires today' SMS -> Scam, with the phrases highlighted and a spoken Hindi warning.
3. Pay 25,000 to a new payee at night -> High risk: the intent check, the plain-language reasons, and the payment held.
4. Cancel it during the hold.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Community scam reports, the collect-request disguise guard, and the admin fraud analytics dashboard.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
