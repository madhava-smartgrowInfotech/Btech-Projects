# MASTER PROMPT (FAST BUILD) - UniHealth

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Gemini API key - https://aistudio.google.com/apikey
> - Optional: Telegram bot token or Gmail app password for reminders (guided).
> - Confirm three fictional hospital names (defaults are generated).
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **UniHealth** - one patient-controlled health record across hospitals - HL7 FHIR exchange, a master patient index, consent you can see and revoke, and an AI assistant that explains your records.

**Goal: a fully working, end-to-end product in the shortest time.** Every feature in section 4.4 must really work with real data and the real model or API - nothing fake. Build only what is in this file. When two approaches both work, **always take the simpler one.**

---

## 1. Rules

1. **One stop only.** Do the Start step (section 8), show a short plan, and wait for **"proceed"**. After that, build straight through to the end without stopping. Don't ask more questions unless you are truly blocked; pick sensible defaults and list them in the final summary.
2. **Real product identity.** Never write anything suggesting coursework or an institution - in code, comments, UI, docs, sample data, file names or commit messages: no "B.Tech", "final year", "major/mini project", "semester", "college/university project", "student batch", "project guide", "supervisor", "viva", "project review", "project submission", "HOD" or academic department names, and no names of people or institutions. Ordinary product words (a hospital department, a moderator review) are fine. (This is a clinical decision-support product: every AI result is shown as an aid for a qualified professional, with a short disclaimer, never as a final diagnosis.)
3. **Works end-to-end, nothing fake.** No placeholders, dummy buttons or hard-coded results. Every output comes from the real pipeline. Seed/demo data is allowed only when clearly labelled as sample data.
4. **Speed rules.**
   - Build only the features in section 4.4. No extra features, no animation libraries, no refactoring for elegance.
   - Install only what section 6 lists. Do **not** add LangChain, LlamaIndex or any library not named there.
   - Timebox: if something still fails after 3 attempts, switch to a simpler approach that works and note it in the summary.
   - Testing = one smoke-test script that drives the real API, plus a frontend production build (`npm run build`). No large unit-test suites.
   - Run the backend and frontend in the background while you work; never block on them.
5. **Secrets** live only in `.env` (git-ignored); commit a complete `.env.example` listing every key and where to get it. Never hard-code keys.
6. **Leave `2.ABSTRACT.docx` and `MASTER_PROMPT.md` in this folder untouched**, and don't reference them in the product.
7. **Fixed ports** (other products may run on this PC at the same time): backend **8206**, frontend **5206** (`strictPort: true`). Any extra local service uses a port in **12060-12069**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

---

## 2. The problem

- Patient records are scattered across hospitals.
- Doctors lack the complete medical history when patients change hospitals.
- Repeated tests and delayed decisions reduce continuity of care.
- Patients cannot access or understand their complete health information.

**What is needed:** A secure, standards-based system that unifies patient records across hospitals and turns them into useful health insights.

---

## 3. Who uses it

- Patients who own and view their unified record
- Doctors who need a patient's history from other hospitals
- Hospital records staff
- Platform administrators

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**Enabling Cross-Institution Health Data Sharing in Norway: EUDI Wallets, On-Chain Consent, and openEHR↔FHIR Translation** - IEEE Access, 2026 - https://doi.org/10.1109/access.2026.3661642

- Cross-institution health data sharing: EU Digital Identity (EUDI) wallets for identity, on-chain patient consent, and openEHR <-> FHIR translation.
- Records stay in each institution's repository and are translated into FHIR bundles for exchange.
- Access is granted only after verified identity and recorded consent.

### 4.2 Advanced system (the specification - every point must be met)

- Hospitals exchange standardised patient records using HL7 FHIR.
- A Master Patient Index identifies the hospitals that hold a patient's records.
- Secure FHIR REST APIs retrieve records with authentication and patient consent.
- After treatment, hospitals sync a FHIR summary to a unified platform while keeping ownership of the originals.
- A Random Forest AI assistant predicts health risks, explains reports, summarises treatment and sends reminders.

Objectives the product must meet:

1. Exchange standardised patient records between hospitals using HL7 FHIR.
2. Locate patient records across hospitals with a Master Patient Index.
3. Enforce authentication and patient consent for record access.
4. Maintain a unified, patient-accessible health record.
5. Predict health risks and explain reports with an AI assistant.
6. Provide medication guidance, follow-up reminders and answers to health queries.

### 4.3 Latest approaches
- HL7 FHIR R4 REST APIs with SMART-on-FHIR style scopes.
- Probabilistic record linkage for master patient indexes (IHE PIX/PDQ style).
- Consent stored as FHIR Consent resources with tamper-evident audit trails.
- LLM summaries and plain-language explanations of clinical records for patients.

### 4.4 What you will build - UniHealth
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Three simulated hospitals** - three independent FHIR R4 servers with their own databases and patient IDs, loaded with different Synthea patients that overlap.
- **F2 Master Patient Index** - fuzzy matching on name, date of birth, gender and phone links one person's records across hospitals, with a confidence score.
- **F3 Consent management** - the patient grants or revokes access per hospital and data category, stored as a FHIR Consent and written to a hash-chained, tamper-evident log.
- **F4 Secure retrieval** - a doctor's request passes a consent check, then FHIR REST calls fetch and merge the records into one timeline; every access is audited.
- **F5 Post-treatment sync** - a hospital pushes a FHIR summary to the platform while the original stays with the hospital.
- **F6 Unified patient record** - encounters, conditions, medications, labs and allergies in one timeline, downloadable as a FHIR bundle.
- **F7 Health-risk prediction** - Random Forest models (heart disease, diabetes) reading values from the record, with the top factors shown.
- **F8 AI assistant and reminders** - Gemini explains reports in plain language and summarises treatment; medication and follow-up reminders appear in-app.

### 4.5 Data

- **Synthea sample data (FHIR R4)** - https://synthea.mitre.org/downloads - about 30 MB zip of synthetic patients -> commit; split across the three hospitals by a seeded script.
- **Heart Disease Dataset** (Kaggle) - https://www.kaggle.com/datasets/johnsmith88/heart-disease-dataset (UCI source: https://archive.ics.uci.edu/dataset/45/heart+disease) -> commit.
- **Pima Indians Diabetes** (Kaggle) - https://www.kaggle.com/datasets/kumargh/pimaindiansdiabetescsv - CC0 -> commit.

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (patient, doctor, admin)
3. Patient: timeline, consents, assistant, reminders
4. Doctor: search, access request, merged record, risk panel
5. Hospital console
6. Audit and consent log

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to UniHealth:** fhir.resources for FHIR R4 models and validation; each simulated hospital is a small FastAPI app with its own SQLite file on its own port; rapidfuzz for record linkage; scikit-learn Random Forest for the risk models; Gemini for the assistant.
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
1. A patient logs in -> one timeline built from three hospitals.
2. A doctor at Hospital B requests the history -> blocked until the patient grants consent -> then the merged record loads; the audit log shows every access.
3. The patient revokes consent -> the next request fails; the consent ledger verifies intact.
4. The AI assistant explains a lipid panel in Telugu; the risk panel shows heart-disease risk with reasons.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- The uncertain-match review queue, compatibility testing against the public HAPI server, and Telegram/email reminders.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
