# MASTER PROMPT (FAST BUILD) - CallSense

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (do this first - it saves the most time):**
> - Kaggle account and API token (dataset download).
> - Gemini API key - https://aistudio.google.com/apikey
> - A microphone for the live mode.
> - Optional: a few real call recordings shared with consent.
> - In the session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **CallSense** - analyses every customer call automatically - transcripts, intent, sentiment and voice emotion, summaries and agent scorecards, plus live assist during calls.

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
7. **Fixed ports** (other products may run on this PC at the same time): backend **8217**, frontend **5217** (`strictPort: true`). Any extra local service uses a port in **12170-12179**. Put them in `.env` / `.env.example`; never use the defaults 8000 / 5173.
8. **Everything is committed** (code, sample data, model/eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`, and the full dataset when only a sample is committed.

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

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**AI-Based Conversational Agents: A Scoping Review From Technologies to Future Directions** - IEEE Access, 2022 - https://doi.org/10.1109/access.2022.3201144

- A scoping review of AI-based conversational agents, from technologies to future directions.
- Covers NLP and natural-language understanding, dialogue management and deep-learning models behind conversational systems.
- Discusses sentiment and emotion modelling and how conversational AI is evaluated.

### 4.2 Advanced system (the specification - every point must be met)

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

### 4.3 Latest approaches
- Whisper-class speech recognition running on CPU (faster-whisper).
- Speaker separation and diarization for agent / customer turns.
- Transformer intent and sentiment models, and speech emotion recognition (wav2vec2-style).
- LLM call summaries, QA scorecards and real-time agent assist.

### 4.4 What you will build - CallSense
Items marked **NEW** go beyond the specification. Build these and only these.

- **F1 Call ingestion** - upload recordings singly or in bulk, or record from the microphone.
- **F2 Transcription** - faster-whisper with timestamps, and agent/customer separation by stereo channel or a simple turn split.
- **F3 Intent and topics** - customer-support intent classification plus keyword extraction, trained on the Bitext dataset.
- **F4 Sentiment and emotion** - text sentiment per segment plus voice emotion from a pretrained model, drawn as an emotion timeline with escalation flags.
- **F5 Call summary** - Gemini writes the reason for the call, the resolution and the action items.
- **F6 Agent scorecard** - greeting, empathy, talk/listen ratio, silence, interruptions, resolution and sentiment change, combined into a score with the evidence.
- **F7 Sample call studio** - generates realistic sample calls from scripts with two offline voices, clearly labelled as samples.
- **F8 Analytics** - call volumes, top intents, sentiment trends and an agent leaderboard, with search across transcripts.
- **F9 Evaluation** - intent accuracy and macro-F1, sentiment F1, and transcription word error rate on the sample calls.

### 4.5 Data

- **Bitext Customer Support Dataset** (Kaggle) - https://www.kaggle.com/datasets/bitext/bitext-gen-ai-chatbot-customer-support-dataset - 18.3 MB, CDLA-Sharing-1.0 -> commit.
- **Call Center Transcripts Dataset** (Kaggle) - https://www.kaggle.com/datasets/oleksiymaliovanyy/call-center-transcripts-dataset - 20.9 MB, MIT -> commit.
- **RAVDESS Emotional Speech Audio** (Kaggle) - https://www.kaggle.com/datasets/uwrfkaggler/ravdess-emotional-speech-audio - 563 MB, CC BY-NC-SA 4.0 -> sample plus script.
- **CREMA-D** (Kaggle) - https://www.kaggle.com/datasets/ejlok1/cremad - 578 MB, ODC-By -> sample plus script.
- **Sample calls** generated by F10 (committed).

**Dataset rules:** commit the dataset when it is about 200 MB or less with no single file over 100 MB; otherwise commit a representative sample under `data/sample/` plus `scripts/download_data.py` (Kaggle downloads through `kagglehub`). Anything you generate must come from a committed, seeded script. Record each source, its licence and what is committed in `docs/02_HOW_IT_WORKS.md`.

---

## 5. Screens

1. Landing
2. Login (supervisor, agent)
3. Calls list and upload
4. Call detail (player, transcript, emotion timeline, summary, scorecard)
5. Sample call studio
6. Analytics
7. Model performance

Keep the UI clean and responsive (Tailwind), with a loading and an error state on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version - ask before adding anything)

- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to the backend port.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite (created on first run), PyJWT + bcrypt for login, python-dotenv. Keep the schema small.
- **Specific to CallSense:** faster-whisper (small model, CPU) for transcription, scikit-learn for intent and sentiment (trains in seconds), a pretrained speech-emotion model from Hugging Face for voice emotion, librosa, Gemini for summaries, and pyttsx3 to generate the sample calls.
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
1. Generate a sample 'refund request' call in the studio, then run it through the pipeline.
2. The transcript is split by speaker, the intent is 'get_refund', and the emotion timeline shows frustration then relief.
3. The summary and the agent scorecard (82/100) appear with their evidence.
4. Analytics show the top intents, the sentiment trend and the agent leaderboard.

**Checklist:** every feature in 4.4 works through the UI - the smoke test passes - `npm run build` succeeds - the evaluation numbers are in the README - the 3 docs and the HOW_TO_RUN copy are done - no academic wording, no hard-coded secrets - everything committed and pushed.

---

## Deferred for speed (not in this build)
- Kaggle GPU training of a speech-emotion model (a pretrained one is used) and of a transformer intent model, live real-time agent assist, and PII redaction.
These are intentionally left out to keep the build fast. Do not add them unless the user asks.
