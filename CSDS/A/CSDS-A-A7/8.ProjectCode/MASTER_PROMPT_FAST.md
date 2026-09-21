# MASTER PROMPT (FAST BUILD) - SHEGUARD

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Gemini API key - https://aistudio.google.com/apikey
> - Telegram bot token from @BotFather and each guardian's chat ID (guided: https://core.telegram.org/bots/tutorial).
> - Gmail address + app password for email alerts (guided).
> - An Android phone with Chrome for testing; install `cloudflared` (guided).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **SHEGUARD** - a women's safety companion that helps choose safer routes, triggers help hands-free and keeps trusted people informed with live location and evidence.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8107**, frontend **5107** (`strictPort: true`). Any extra local service uses a port in **11070-11079**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

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

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**SafeRoutes: Charting a Secure Path-A Holistic Approach to Women's Safety Through Advanced Clustering and GPS Integration** - IEEE Access, 2024 - https://doi.org/10.1109/access.2024.3488784

- SafeRoutes: a holistic approach to women's safety through advanced clustering and GPS.
- A data pipeline from public/government sources; unsupervised clustering of regions using crime rates, police presence and infrastructure.
- Integration with map APIs and cab vendors to raise real-time alerts when a trip deviates into unsafe areas.

### 4.2 Advanced system (the specification - every point must be met)

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

### 4.3 Latest approaches
- Route safety scoring that combines crime density, time of day and community reports.
- Hands-free emergency triggers: voice keywords, shake detection and one-tap SOS.
- Live location streaming over WebSockets with a shareable tracking page.
- Tamper-evident evidence capture (hashing) and installable PWAs on phones.

### 4.4 What you will build - SHEGUARD
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Safe Route** - routes from OSRM scored by area risk and time of day; the safest one is recommended on a map with a risk heat layer.
- **F2 Area risk model** - K-Means / DBSCAN clustering of the district crime data into risk tiers (trains on CPU in seconds), with district coordinates geocoded once and committed.
- **F3 Emergency triggers** - SafePhrase voice trigger (Web Speech API) and a one-tap SOS button.
- **F4 Live location session** - the position streams to guardians over WebSockets; guardians open a live tracking page.
- **F5 Free alerts** - Telegram message and email to guardians with the tracking link, plus in-app alerts.
- **F6 Evidence capture** (NEW) - a photo or short audio clip saved with time, location and a SHA-256 hash.
- **F7 AI safety assistant** - Gemini answers safety questions and suggests next steps.
- **F8 Roles and access** - each user sees only their own sessions and evidence; guardians see only what is shared with them.
- **F9 Installable PWA** - home-screen icon and full-screen app on the phone.

### 4.5 Data

- **Crime in India** (Kaggle) - https://www.kaggle.com/datasets/rajanand/crime-in-india - 4.4 MB -> commit.
- **Crimes against women in India 2001-2021** (Kaggle) - https://www.kaggle.com/datasets/balajivaraprasad/crimes-against-women-in-india-2001-2021 -> commit.
- District coordinates: geocode district names once through OpenStreetMap Nominatim (respect 1 request/second) and commit the cached CSV.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Home (SOS button, status)
4. Safe Route planner
5. Emergency session (live map, evidence, cancel)
6. Guardian live-tracking page
7. Guardians and settings
8. AI assistant

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to SHEGUARD:** Installable PWA (vite-plugin-pwa), FastAPI WebSockets for live location, Leaflet + the free OSRM routing service, the browser Web Speech API for the voice trigger, Telegram Bot API + Gmail SMTP for free alerts, Gemini for the assistant. Cloudflare quick tunnel for HTTPS on the phone.
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
1. Install the PWA on a phone and add a guardian.
2. Plan a route -> the safest option is highlighted with its risk explanation.
3. Say the SafePhrase -> the emergency session starts -> the guardian gets a Telegram message and email with a live link and watches the location move.
4. Capture evidence -> it is stored with its hash; cancel the emergency.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Shake-to-SOS, community reports with moderation, and the route-deviation check-in.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
