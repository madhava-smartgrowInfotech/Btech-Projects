# MASTER PROMPT (FAST BUILD) - PolicyLens

> **How to use this file:** open this folder (`8.ProjectCode`) as its own workspace, start a new Claude Code session and say:
> *"Read MASTER_PROMPT_FAST.md completely and follow it exactly."*
> This file replaces `MASTER_PROMPT.md` for this build - ignore that file.
>
> **Before you start (5 minutes, saves the most time):**
> 1. Get a free Gemini API key: https://aistudio.google.com/apikey -> "Create API key" -> copy it.
> 2. Download 2-3 health-insurance **policy wording** PDFs from Indian insurers' official websites (each insurer has a "Policy Wordings" or "Downloads" page) and put them in `data/policies/` inside this folder.
> 3. In the Claude Code session, switch to **accept-edits** mode, and when it first asks to run `pip`, `npm`, `python` or `git`, choose **"Yes, and don't ask again"**. Waiting for approvals is the biggest hidden time cost.

---

## 0. Your role and the goal

You are the lead engineer for **PolicyLens** - an AI assistant that reads a person's own health-insurance policy, answers questions with exact clause citations, and guides them through claims.

**Goal: a fully working, end-to-end product in the shortest time (target about 2-3 hours).** Every feature below must really work with real PDFs and the real Gemini API. Nothing beyond this file gets built. When two approaches both work, **always take the simpler one.**

---

## 1. Rules

1. **One stop only.** Do the Start step (section 8), show a short plan, and wait for **"proceed"**. After that, build straight through to the end without stopping. Do not ask further questions unless you are truly blocked; choose sensible defaults and list them in the final summary.
2. **Real product identity.** Never write anything suggesting coursework or an institution - in code, comments, UI, docs, sample data, file names or commit messages: no "B.Tech", "final year", "major/mini project", "semester", "college/university project", "student batch", "project guide", "supervisor", "viva", "project review", "project submission", "HOD", and no names of people or institutions.
3. **Works end-to-end, nothing fake.** No placeholders, dummy buttons or hard-coded answers. Every result comes from the real pipeline.
4. **Speed rules.**
   - Build only the features in section 4.4. No extra features, no animation libraries, no refactoring for elegance.
   - Install only the packages in section 6. **Do not use** LangChain, LlamaIndex, ChromaDB, PyTorch or sentence-transformers (large installs, no benefit here).
   - Timebox: if something still fails after 3 attempts, switch to a simpler approach that works and note it.
   - Testing = one smoke-test script plus a frontend production build (section 8). No large unit-test suites.
   - Run the backend and frontend in the background while you work; never block on them.
5. **Secrets** only in `.env` (git-ignored); commit a complete `.env.example`.
6. **Leave `2.ABSTRACT.docx` and `MASTER_PROMPT.md` in this folder untouched**, and do not reference them in the product.
7. **Fixed ports** (other products may run on this PC at the same time): backend **8101**, frontend **5101** (`strictPort: true`). Any extra service uses 11010-11019.
8. **Everything is committed** (code, sample PDFs, eval results, docs) except `venv/`, `node_modules/`, `.env`, `dist/`.

---

## 2. The problem

- Health-insurance policies are long and technical, so people cannot easily find coverage, exclusions and conditions.
- Agents and helplines give slow, generic and inconsistent answers.
- General chatbots produce answers that are not supported by the person's actual policy.
- Claims get delayed or rejected because people lack guidance on eligibility and documents.

**What is needed:** an assistant that answers strictly from the user's own policy, cites the supporting clauses and guides claims step by step.

---

## 3. Who uses it

- Policyholders and their families who need clear answers about their cover
- Insurance advisors who explain policies to many customers
- HR / benefits teams handling group health policies

---

## 4. System evolution (read, then build 4.4)

### 4.1 Reference system
**A Hybrid Transformer-Based Framework for Multi-Document Summarization of Turkish Legal Documents** - IEEE Access, 2025 - https://doi.org/10.1109/access.2025.3545750
- Hybrid pipeline: extractive methods (TF-IDF, TextRank) followed by transformer models (LED, Long-T5, BART, GPT-3.5) to summarise long legal documents.
- Evaluated with ROUGE; LLMs gave the most faithful summaries of long legal text.

### 4.2 Advanced system (the specification - must be met)
- Extract key policy attributes (policy number, sum insured, deductibles, co-pay, waiting periods, exclusions, benefit rules) from uploaded policies.
- Retrieval-augmented generation: policy text chunked, embedded and stored in a vector store; relevant clauses retrieved for each question.
- Plain-language answers grounded in and citing the retrieved clauses.
- Claim guidance: eligibility pre-check, evidence checklist, step-by-step procedure.
- Summary of risks, exclusions and cost-coverage trade-offs to support plan comparison.
- Evaluation of answer accuracy, faithfulness and response time.

### 4.3 Latest approaches
- Hybrid retrieval (keyword BM25 + dense embeddings) beats either alone on policy and legal text.
- Long-context LLMs with schema-constrained JSON output for structured extraction.
- Citation-grounded answers with an explicit "not stated in this policy" refusal.

### 4.4 What you will build - PolicyLens
- **F1 Upload and parse** - upload a policy PDF; PyMuPDF extracts text per page; chunks of about 1,000 characters with overlap, each keeping its page number.
- **F2 Policy Card** - one Gemini call over the full policy text (JSON output with a response schema): policy name, insurer, sum insured, deductible, co-pay, room-rent limit, waiting periods, key exclusions, sub-limits, plus a **"Watch-outs"** list (risks and traps) - every value with its page number.
- **F3 Ask your policy** - chat answers with citations like [p. 12]; clicking a citation opens the PDF at that page; if the policy does not cover the question, it says so instead of guessing.
- **F4 Hybrid retrieval** (NEW) - BM25 (`rank-bm25`) + Gemini embeddings (cosine search in NumPy over vectors stored in SQLite - a local vector store, no server), merged with reciprocal-rank fusion.
- **F5 Claim check** - describe a treatment or hospitalisation (plus optional amount and days) -> covered / partly covered / not covered, reasons with page citations, a document checklist and claim steps (JSON output).
- **F6 Compare two policies** - two Policy Cards side by side plus a short AI summary of the trade-offs.
- **F7 Answer language** (NEW) - English, Hindi or Telugu, chosen from a dropdown.
- **F8 Evaluation** - `scripts/eval.py` runs 10 question/answer pairs you write from the sample policies and reports retrieval hit rate, answer accuracy, faithfulness (answer supported by the cited text, judged by Gemini) and average response time; results saved to `experiments/eval/metrics.json` and shown in the README.

---

## 5. Screens (4 pages, simple and clean)

1. **Landing** - hero line, three feature cards, "Get started" button.
2. **Login / Register** - email + password; a seeded demo account.
3. **My policies** - upload, list, "Compare" (pick two).
4. **Policy page** - tabs: **Policy Card** | **Ask** | **Claim check**, with the PDF viewable at a cited page (browser's built-in PDF viewer via `#page=N`).

Clean, responsive layout with Tailwind; loading and error messages on every action. No landing-page animation libraries.

---

## 6. Tech stack (fast version)

- **Backend:** Python 3.11+, FastAPI, Uvicorn, python-multipart, SQLite through SQLAlchemy 2 (keep the schema to about 5 tables), PyJWT + bcrypt for login, python-dotenv.
- **AI / retrieval:** google-genai (Gemini chat model from `GEMINI_MODEL` in `.env` - use the newest free-tier Flash model listed in Google AI Studio; embeddings with the current Gemini embedding model, e.g. `gemini-embedding-001`, **batched** and cached per policy), PyMuPDF, rank-bm25, NumPy. Retry with backoff on rate-limit (429) errors.
- **Frontend:** React + Vite (**JavaScript**, not TypeScript), Tailwind CSS, react-router-dom, axios, lucide-react icons. Vite proxies `/api` to port 8101.

---

## 7. Folder structure

```
8.ProjectCode/
  backend/app/        main.py, db.py, auth.py, ingest.py, retrieval.py, llm.py, routes/
  frontend/src/       pages/ (Landing, Login, Policies, Policy), components/, api.js
  scripts/            smoke_test.py, eval.py
  data/policies/      the sample policy PDFs (committed)
  data/app.db         created on first run (git-ignored)
  experiments/eval/   metrics.json
  docs/               01_OVERVIEW.md, 02_HOW_IT_WORKS.md, 03_HOW_TO_RUN.md
  setup.bat  run.bat  .env.example  .gitignore  README.md
```

---

## 8. Workflow

**Start (then the only stop)**
1. Check Python, Node.js LTS and Git; check that `.env` has `GEMINI_API_KEY` (create `.env` from `.env.example` with the user if missing) and that `data/policies/` has at least one PDF. If anything is missing, give the user 2-3 exact steps to fix it.
2. Write `docs/PLAN.md` (30 lines or fewer: architecture, endpoints, tables, screens).
3. Show a 10-line summary and wait for **"proceed"**.

**M1 - Backend (about 60 min):** `setup.bat` (venv + pip + npm install), backend with auth, ingest, Policy Card, retrieval, chat, claim check, compare. `scripts/smoke_test.py` calls the running API: register -> upload a sample PDF -> Policy Card -> 3 questions -> claim check -> compare - and must pass. Commit and push.

**M2 - Frontend (about 45-60 min):** the 4 pages wired to the API; `run.bat` starts backend and frontend and opens the browser. Commit and push.

**M3 - Finish (about 30 min):** `scripts/eval.py` with 10 Q&A pairs -> metrics; docs (overview; how it works with one Mermaid diagram; how to run) and a README with features, quick start, demo login, evaluation results and a **documentation index**; copy `docs/03_HOW_TO_RUN.md` to `../18.FinalCodeExecutionSteps/HOW_TO_RUN.md`. Final check: smoke test passes and `npm run build` succeeds. Commit and push. Give the user a short summary: how to run, the demo login, defaults you chose.

---

## 9. Git rules (other sessions may be committing in sibling folders at the same time)

- From this folder: `git add -A .` then `git commit -m "<3-5 plain words>" -- .` - never a bare `git commit`. No message body, no co-author or AI-attribution lines. Never change git config.
- Push with `git push` (no pull needed). If rejected because the remote has newer commits, run `git pull --rebase --autostash` only when `git status` shows no changes outside this folder; otherwise wait a minute and retry.
- On `index.lock` / "another git process": wait 10 seconds and retry. Never delete the lock file.
- Never run `git stash`, `reset`, `checkout`, `restore`, `clean`, `rebase` or `push --force`.
- In M3, name the copied file explicitly: `git add -A . ../18.FinalCodeExecutionSteps/HOW_TO_RUN.md` and `git commit -m "<message>" -- . ../18.FinalCodeExecutionSteps/HOW_TO_RUN.md`.
- `.gitignore`: `venv/`, `node_modules/`, `__pycache__/`, `.env`, `dist/`, `data/app.db`.

---

## 10. Done when

**Demo (from a fresh `run.bat`):**
1. Log in with the demo account, upload a policy -> the Policy Card appears with values and page numbers, plus watch-outs.
2. Ask "Is cataract surgery covered and after what waiting period?" -> answer with [p. N] citations; clicking one opens the PDF at that page. Switch the language to Hindi and ask again.
3. Claim check for "knee replacement, 5 days in hospital" -> verdict, reasons, document checklist, steps.
4. Compare two policies -> side-by-side cards and a trade-off summary.

**Checklist:** F1-F8 work through the UI - smoke test passes - `npm run build` succeeds - eval metrics in the README - docs and HOW_TO_RUN copy done - no academic wording, no hard-coded secrets - everything committed and pushed.
