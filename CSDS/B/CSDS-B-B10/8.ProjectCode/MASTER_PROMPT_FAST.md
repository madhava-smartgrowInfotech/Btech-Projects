# MASTER PROMPT (FAST BUILD) - SkyCipher

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (download script).
> - Optional: a webcam for the live link.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **SkyCipher** - lightweight, chaos-based image encryption for drone links - wavelet decomposition, chaotic keys and XOR diffusion fast enough for live transmission, with a full security lab.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8210**, frontend **5210** (`strictPort: true`). Any extra local service uses a port in **12100-12109**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- UAV images sent over wireless links can be intercepted or modified.
- Strong conventional ciphers are too heavy for real-time transmission.
- Weak image ciphers leave pixel correlation that attackers can exploit.
- Lightweight schemes often lack thorough security evaluation.

**What is needed:** A lightweight yet strong image encryption scheme suitable for real-time UAV transmission.

---

## 3. Who uses it

- Drone operators in survey, agriculture, inspection and disaster response
- Ground-station operators receiving imagery
- Security auditors validating the link

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**A Lightweight Multi-Chaos-Based Image Encryption Scheme for IoT Networks** - IEEE Access, 2024 - https://doi.org/10.1109/access.2024.3377665

- A lightweight multi-chaos image encryption scheme for resource-constrained IoT devices.
- Henon and 2D-logistic chaotic maps generate the key streams for permutation and diffusion.
- Security validated with NPCR, UACI, entropy and correlation analysis at low computational cost.

### 4.2 Advanced system (the specification - every point must be met)

- The input image is decomposed into frequency sub-bands using the Discrete Wavelet Transform.
- A chaotic map generates unpredictable keys that are highly sensitive to initial conditions.
- XOR-based diffusion encrypts pixels to reduce correlation.
- The scheme is purely software-based and lightweight enough for real-time transmission.
- Security is verified using entropy, histogram, correlation, NPCR, UACI, PSNR, MSE and key sensitivity.

Objectives the product must meet:

1. Decompose images using the Discrete Wavelet Transform.
2. Generate unpredictable encryption keys using a chaotic map.
3. Encrypt images with XOR-based diffusion.
4. Recover images accurately through decryption.
5. Evaluate security using entropy, histogram, correlation, NPCR, UACI and key sensitivity.
6. Measure PSNR, MSE and encryption and decryption time.

### 4.3 Latest approaches
- 2-D and hyperchaotic maps with large key spaces.
- Integer (lifting) wavelet transforms that make transform-domain encryption exactly reversible.
- Session keys from elliptic-curve key exchange (X25519 + HKDF) and per-frame integrity tags.
- Real-time frame encryption for video links with benchmarks against AES / ChaCha20.

### 4.4 What you will build - SkyCipher
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Encryption engine** - integer Haar lifting DWT into sub-bands, chaotic key streams (2-D logistic / Henon) seeded from a 256-bit key, then permutation and XOR diffusion; decryption is bit-exact.
- **F2 Image studio** - upload, encrypt and decrypt; view the sub-bands, the cipher image and the histograms.
- **F3 Security lab** - entropy, histogram uniformity, correlation (horizontal, vertical, diagonal), NPCR, UACI, PSNR, MSE, key sensitivity and key space, with an exportable report.
- **F4 Attack tests** - noise and cropping applied to the cipher image, showing how much of the image still recovers.
- **F5 Live UAV link** (NEW) - a sender streams drone frames encrypted over a WebSocket to a ground station that decrypts and displays them, with FPS, latency and throughput shown.
- **F6 Benchmark** - encryption and decryption time compared with AES-CTR and ChaCha20 on the same images.

### 4.5 Data

- **VisDrone** (Kaggle) - https://www.kaggle.com/datasets/banuprasadb/visdrone-dataset - 2.16 GB, CC BY-NC-SA 3.0 IGO -> commit a sample (about 60 images and 2 short sequences) plus the download script.
- **USC-SIPI image database** (standard test images) - https://sipi.usc.edu/database/ - include a few permitted images for the security lab.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login / register
3. Image studio
4. Security lab and report
5. Live link (sender and ground station)
6. Benchmark

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to SkyCipher:** NumPy for the cipher, PyWavelets for the sub-band views with an integer lifting transform on the cipher path (so decryption is exact), OpenCV, scikit-image (SSIM), and the `cryptography` package for the AES / ChaCha20 baseline.
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
2. Write `docs/PLAN.md` (30 lines or fewer: architecture, endpoints, tables, screens, the dataset you will use).
3. Show a 10-line summary and wait for **"proceed"**.

**M1 - Backend and core logic.** Project skeleton, `setup.bat` (venv + pip + `npm install`), backend with login and the database, then the data/model pipeline and every feature endpoint from section 4.4. `scripts/smoke_test.py` drives the running API through the main flow end-to-end and must pass. Commit and push.

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
1. Encrypt a drone image -> a noise-like cipher and a flat histogram; decrypt -> the identical image (checksum matches).
2. The security lab shows NPCR, UACI, entropy and correlation; a 1-bit key change fails to decrypt.
3. Apply noise and cropping -> the report shows how much still recovers.
4. Start the live link -> encrypted frames stream to the ground station in real time; the benchmark compares it with AES and ChaCha20.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- X25519 session-key exchange and per-frame HMAC tamper detection, batch folder mode and the mission log.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
