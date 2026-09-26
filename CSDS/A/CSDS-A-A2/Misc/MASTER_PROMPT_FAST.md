# MASTER PROMPT (FAST BUILD) - Attendance Magic

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - 2-3 volunteers with Android/iPhone phones (Chrome/Safari) for testing.
> - Install `cloudflared` (guided) for the HTTPS phone link.
> - Default geo-fence radius and session length (defaults: 100 m, 10 minutes).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **Attendance Magic** - proxy-proof attendance: geo-fenced sessions, a live face challenge and duplicate-face blocking, all from a phone browser.

**Goal: a fully working, end-to-end product in the shortest time.** Every feature in section 4.4 must really work with real data and the real model or API - nothing fake. Build only what is in this file. When two approaches both work, **always take the simpler one.**

---

## 1. Rules

1. **One stop only.** Do the Start step (section 8), show a short plan, and wait for **"proceed"**. After that, build straight through to the end without stopping. Don't ask more questions unless you are truly blocked; pick sensible defaults and list them in the final summary.
2. **Real product identity.** Never write anything suggesting coursework or an institution - in code, comments, UI, docs, sample data, file names or commit messages: no "B.Tech", "final year", "major/mini project", "semester", "college/university project", "student batch", "project guide", "supervisor", "viva", "project review", "project submission", "HOD" or academic department names, and no names of people or institutions. Ordinary product words (a hospital department, a moderator review) are fine. (This product is sold to organisations that run classes or examinations, so its *end users* may be instructors, examiners and attendees - that is fine. What must never appear is anything about who built this product or why.)
3. **Works end-to-end, nothing fake.** No placeholders, dummy buttons or hard-coded results. Every output comes from the real pipeline. Seed/demo data is allowed only when clearly labelled as sample data.
4. **Speed rules.**
   - Build only the features in section 4.4. No extra features, no animation libraries, no refactoring for elegance.
   - Install only what section 6 lists. Do **not** add LangChain, LlamaIndex or any library not named there.
   - Timebox: if something still fails after 3 attempts, switch to a simpler approach that works and note it in the summary.
   - Testing = one smoke-test script that drives the real API, plus a frontend production build (`npm run build`). No large unit-test suites.
   - Run the backend and frontend in the background while you work; never block on them.
5. **Secrets** live only in `.env` (git-ignored); commit a complete `.env.example` listing every key and where to get it. Never hard-code keys.
6. **Leave `2.ABSTRACT.docx` and `MASTER_PROMPT.md` in this folder untouched**, and don't reference them in the product.
7. **Fixed ports** (other products may run on this PC at the same time): backend **8102**, frontend **5102** (`strictPort: true`). Any extra local service uses a port in **11020-11029**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Manual attendance consumes class time and is prone to errors and proxy marking.
- Link-based and QR-based digital attendance can be shared with absent attendees.
- Face recognition alone can be spoofed with photos or videos.
- Existing systems do not confirm that the attendee is physically present at the venue.

**What is needed:** An attendance system that verifies location, liveness and identity together within each time-bound session.

---

## 3. Who uses it

- Session hosts (instructors, trainers, event organisers) who run attendance
- Attendees who mark attendance from their phones
- Administrators who manage people, sessions and reports

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Real-Time Student Face Recognition Attendance System Using AI** - International Advanced Research Journal in Science, Engineering and Technology (IARJSET), Vol. 12, Issue 5, 2025 - https://doi.org/10.17148/IARJSET.2025.125183

- Automates attendance with CNN-based face detection and recognition on a live video stream.
- Matches detected faces against stored profiles and marks attendance instantly, claiming robustness to lighting and partial occlusion.
- Mentions resistance to impersonation, but relies on recognition alone - no liveness or location checks.

### 4.2 Advanced system (the specification - every point must be met)

- Hosts create time-bound attendance sessions with a configurable geo-fence and share a unique session link.
- Attendees are authenticated with JWT and verified by GPS location, device identity and roll-number restrictions.
- A random live facial challenge, such as turning the head, is verified in real time using MediaPipe landmarks.
- InsightFace embeddings compare the captured face with faces already recorded in the session to block duplicate identities.
- Hosts view attendance summaries and lists and export records to Excel.

Objectives the product must meet:

1. Enable hosts to create time-bound attendance sessions with configurable geo-fences.
2. Authenticate attendees securely using JWT, device identification and roll-number restrictions.
3. Verify physical presence by checking the attendee's GPS location against the session boundary.
4. Detect liveness through a random live facial challenge using MediaPipe.
5. Prevent duplicate identities by matching InsightFace embeddings within each session.
6. Provide attendance summaries and Excel export for hosts.

### 4.3 Latest approaches
- Challenge-response liveness (random head turn / blink) plus passive anti-spoofing to defeat photos and replayed videos.
- ArcFace-family embeddings (InsightFace) for accurate one-to-one face verification on CPU.
- Browser-side face landmark tracking (MediaPipe Face Landmarker) for real-time challenge detection.
- Geo-fencing with GPS accuracy thresholds and mock-location heuristics; privacy-friendly storage of embeddings instead of raw photos.

### 4.4 What you will build - Attendance Magic
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Session with geo-fence** - the host creates a time-bound session, picks a centre and radius on a map, and gets a link plus QR code.
- **F2 Secure join** - login (JWT), roll/ID restriction per session, and a device fingerprint stored with each attempt.
- **F3 Location check** - the phone's GPS must be inside the geo-fence, with an accuracy threshold.
- **F4 Live face challenge** - a random challenge (turn left / right / blink) verified in the browser with MediaPipe landmarks.
- **F5 Face match and duplicate block** - InsightFace embedding compared with the enrolled face; the same face cannot mark a second identity in one session.
- **F6 Reports** - per-session list, summary, Excel export, and a log of every rejected attempt with its reason (NEW).

### 4.5 Data

- No external dataset. Faces are enrolled inside the product. Test with 2-3 consenting volunteers.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Host: sessions + create session (map, QR)
4. Host: live session list (auto-refresh)
5. Attendee join flow: location -> challenge -> match -> success
6. Face enrolment
7. Reports + Excel export

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to Attendance Magic:** MediaPipe Face Landmarker (in the browser) for the liveness challenge; InsightFace + onnxruntime (CPU) for face matching; Leaflet for the geo-fence map; openpyxl; qrcode. Cloudflare quick tunnel for HTTPS on phones.
- **Training:** No model training - this product uses pretrained models, APIs and/or an optimisation engine. Skip straight to the app.

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
2. Write `docs/PLAN.md` (30 lines or fewer: architecture, endpoints, tables, screens).
3. Show a 10-line summary and wait for **"proceed"**.

**M1 - Backend and core logic.** Project skeleton, `setup.bat` (venv + pip + `npm install`), backend with login and the database, then the data/model pipeline and every feature endpoint from section 4.4. `scripts/smoke_test.py` drives the running API through the main flow end-to-end and must pass. Commit and push.

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
1. The host creates a session with a 100 m geo-fence and shows the QR code.
2. An attendee opens the link on a phone: location accepted -> 'turn your head left' -> face matched -> marked present; the host list shows them.
3. A second account tries with the same face -> blocked as a duplicate, with the reason logged.
4. The host ends the session and downloads the Excel report.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- WebSocket live dashboard (the list auto-refreshes instead), enrolment quality scoring, mock-location heuristics.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
