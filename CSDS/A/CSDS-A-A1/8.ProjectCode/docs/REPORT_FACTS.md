# REPORT FACTS - PolicyLens (CSDS-A-A1)

Single source of truth for every submission document (chapter documents, decks, final report, IEEE paper).
Every number below comes from this project's own artefacts - `experiments/eval-20260922-0027/metrics.json`,
`pytest` and `npm run build` run on 15 Oct 2026, `data/processed/*/document.json`, the code, and the live demo
run of 15 Oct 2026. Nothing here is estimated. Gaps are listed in section 12.

---

## 1. Identity

| Item | Value |
|---|---|
| Product | **PolicyLens** - "Understand your health insurance, clause by clause" |
| Project title | AI Health Insurance Assistance Using LLM + RAG |
| Batch | CSDS-A-A1 (CSE - Data Science, Section A) |
| Students | G. PRANATHI - 23K91A6764 · CH. AISHWARYA - 23K91A6747 · BHAVANSH MANE - 23K91A6728 · B. DEEKSHITH - 24K95A6701 |
| Guide | **Not stated** in `1.A1_BATCH_DETAILS.docx` or `Students.txt` ("GUIDE NAME") - placeholder `[GUIDE NAME]` kept |
| Department | Department of Computer Science and Engineering (Data Science) |
| College / principal / HOD / academic year | Not stated - square-bracket placeholders kept |
| Base paper | M. A. A. Albayati and O. Findik, "A Hybrid Transformer-Based Framework for Multi-Document Summarization of Turkish Legal Documents," *IEEE Access*, vol. 13, pp. 37165-37181, 2025, DOI 10.1109/ACCESS.2025.3545750 |
| Ports | API 8101 · web 5101 |

### Base paper facts (read from `Documentary/BASEPAPER_A_Hybrid_Transformer_Based_Framework_for.pdf`, 17 pages)
- Task: multi-document **summarisation** of Turkish court rulings (consumer-rights cases). Dataset: **2,000** Turkish legal documents scraped from a public court-ruling site.
- Extractive: TF-IDF and TextRank (TF-IDF with keywords: content F1 = 0.47). Abstractive/hybrid: LED, Long-T5, BART-large, GPT-3.5 Turbo, fed with the extractive summaries.
- Best result: GPT-3.5 Turbo, **ROUGE-1 55 %, ROUGE-2 35 %, ROUGE-L 42 %, ROUGE-Sum 44 %**.
- Contributions it claims: first Turkish legal summarisation framework; validated dataset; evidence that hybrid extractive+abstractive works; Turkish-specific preprocessing.
- It does **not** do question answering, retrieval, citations, claim guidance or insurance.
- Therefore **no like-for-like numeric comparison is possible**: different task (summarisation vs. grounded QA), language (Turkish vs. English/Hindi/Telugu), domain (court rulings vs. health-insurance wordings), metric (ROUGE vs. hit@k / answer accuracy). The comparison in the documents is on approach and design only, and says so.

---

## 2. Measurement machine (paper "System Hardware")

| Item | Value |
|---|---|
| CPU | 12th Gen Intel Core i5-12500 - 6 cores / 12 threads |
| RAM | 15.7 GB |
| GPU | none used (Intel UHD Graphics 770 integrated; all local models run on CPU) |
| OS | Windows 11 Pro 10.0.26200 |
| Python | 3.11.9 (recorded in `metrics.json`) |
| Node / build | Vite 8.3.0 production build succeeds |
| External service | Google Gemini API (free tier) |

Software requirements (`backend/requirements.txt`, `frontend/package.json`): FastAPI ≥0.115, Uvicorn, Pydantic ≥2.7, SQLAlchemy ≥2.0 (SQLite), PyJWT, passlib + bcrypt 4.0.1, google-genai ≥1.0, chromadb ≥1.0, rank-bm25 ≥0.2.2, PyMuPDF ≥1.24, sentence-transformers ≥3.0, torch ≥2.3, numpy, pandas, matplotlib, scikit-learn, pytest ≥8, httpx. Web: React 18.3, Vite, TypeScript, Tailwind CSS, shadcn/ui (Radix), React Router 7, TanStack Query 5, Axios, Recharts 3, Framer Motion/GSAP/Lenis.

Code size (lines): backend `app/` 5,927 · `ml/` 949 · backend tests 523 · web `src/` 9,851 (TS/TSX).

---

## 3. Architecture summary

Single-machine app: **React 18 + Vite** web app (5101) → **FastAPI** REST API (8101, JWT auth) → services; storage in `data/` (SQLite `app.db`, ChromaDB `chroma/`, PDFs, page images, response cache); three CPU models in `models/hf`; one external service (Gemini).

Pipeline (upload → processing, background ingestion worker, resumes after restart):
`queued → parsing → indexing → extracting → ready | failed`
1. **Validate** PDF, SHA-256 (documents shared by content hash), reject scans/encrypted/oversize.
2. **Parse** (`pdf_parser.py`, PyMuPDF): lines with page/position/font; remove running headers/footers; two-column reading order; join justified text and letter-spaced headings; tables as rows.
3. **Segment** (`segmenter.py`): clause starts (`4.2.1`, `Def. 5`, `Excl03`, `Section C`, Roman/bold headings); IRDAI exclusion-code list items become their own clause; heading path; chunks of 12-380 words with highlight boxes.
4. **Index**: BM25 Okapi (k1 1.4, b 0.7, insurance synonym list) + MiniLM embeddings (384-d) in ChromaDB (cosine).
5. **Extract Policy Card**: one long-context Gemini call per policy with a Pydantic JSON schema; every value's quote located in the clauses to confirm clause + page (`verified`); rule-based + AI risk highlights de-duplicated with severity.
6. **Ask** (`answerer.py`): language detect/translate query (Hindi/Telugu) → BM25 top 30 + dense top 30 → RRF (k 60) → re-rank pool (fused top 20 + each retriever's top 8) with cross-encoder → top 7 clauses (+ the rule a retrieved table belongs to / tables a rule governs, up to 4) → abstain without AI call if re-rank < 0.004 **and** BM25 < 9.0 → Gemini with `[C##]` tags and JSON schema → drop tags not retrieved → NLI faithfulness 0-100.
7. **Claim Copilot** (`claim_copilot.py`, `eligibility.py`): 7-9 targeted searches merged to the 16 best clauses; rule engine calculates waiting-period checks, age/network co-payment, sub-limits, cost estimate; Gemini returns verdict/reasons/checklist/steps; a failed calculated waiting period can never be "covered".
8. **Compare** (`comparator.py`): field-by-field table with "better" markers + AI trade-offs citing both policies.
9. **Languages**: English, Hindi, Telugu (query translation, answer language, card/risk translation cached).

Gemini client: JSON-schema output, fallback chain (`gemini-3.8-flash` → `gemini-3.6-flash` → `gemini-3.5-flash-lite` in the evaluated configuration; `.env` now uses `gemini-flash-latest` as primary), 10-minute cool-down for overloaded models, RPM pacing (`LLM_MAX_RPM` 10), disk cache by content hash, usage log (`llm_calls`).

### Database (SQLite, 12 tables)
`users`, `documents`, `policies`, `clauses`, `policy_cards`, `risk_flags`, `conversations`, `messages`, `claim_cases`, `comparisons`, `translations`, `llm_calls` (ORM model files in `backend/app/models/`: chat, claim, comparison, document, llm_call, policy, translation, user).

### Backend modules
`api/` (auth, users, policies, conversations, claims, comparisons, dashboard, evaluation, health, deps) · `core/` (config, db, errors, logging, security) · `models/` · `schemas/` · `services/` (answerer, claim_copilot, comparator, eligibility, extractor, gemini_client, ingestion, language, page_renderer, pdf_parser, risk_engine, seed, segmenter, text_match) · `ml/` (embeddings, faithfulness, local_models, `retrieval/` bm25_index, clause_cache, dense_index, fusion, hybrid, reranker, text) · evaluation harness `ml/` (common, eval_answers, eval_claims, eval_extraction, eval_retrieval, experiment, metrics, plots, run_all).

### Web pages (12)
Landing, Login, Register, Dashboard, My policies, Policy view (tabs: Policy Card · Risks · Document · Clause search), Ask your policy (chat), Claim Copilot (4-step wizard), Compare plans, Model performance (public data), Settings, Not found.

---

## 4. Endpoints (42 route handlers, base `/api`)

| Group | Endpoints |
|---|---|
| Health | `GET /health` |
| Auth / user | `POST /auth/register` · `POST /auth/login` · `GET /auth/me` · `PATCH /users/me` · `POST /users/me/password` · `GET /users/languages` |
| Policies | `GET /policies` · `POST /policies` (multipart) · `POST /policies/samples` · `GET /policies/{id}` · `PATCH /policies/{id}` · `DELETE /policies/{id}` · `GET /policies/{id}/status` · `GET /policies/{id}/file` · `GET /policies/{id}/pages` · `GET /policies/{id}/pages/{n}` · `GET /policies/{id}/clauses` · `GET /policies/{id}/clauses/{ordinal}` · `GET /policies/{id}/card` · `POST /policies/{id}/extract` · `GET /policies/{id}/risks` · `POST /policies/{id}/search` |
| Chat | `POST /conversations` · `GET /conversations` · `GET /conversations/{id}` · `DELETE /conversations/{id}` · `POST /conversations/{id}/messages` |
| Claims | `POST /claims` · `GET /claims` · `GET /claims/{id}` · `DELETE /claims/{id}` · `PATCH /claims/{id}/checklist` |
| Compare | `POST /comparisons` · `GET /comparisons` · `GET /comparisons/{id}` · `DELETE /comparisons/{id}` |
| Dashboard | `GET /dashboard/summary` |
| Evaluation (no login) | `GET /evaluation/latest` · `GET /evaluation/runs` · `GET /evaluation/runs/{run}` · `GET /evaluation/runs/{run}/plots/{file}` |

Errors: `{detail, code}` (`unauthorized`, `token_invalid`, `not_found`, `email_taken`, `duplicate_policy`, `busy`, `ai_quota` 429, `ai_unavailable` 503, `ai_not_configured` 503, `not_pdf`, `too_large` 413, `encrypted`, `bad_pdf`). Password rule: ≥ 8 characters with a letter and a number. Passwords hashed with bcrypt; access token JWT (HS256 via PyJWT), expiry ≈ 24 h.

---

## 5. Dataset (no training - evaluation only)

PolicyLens trains nothing; it works on uploaded wordings. Data = 4 sample policy wordings + a hand-built evaluation set. ~4.7 MB total, all committed; no Kaggle dataset.

| Sample | Insurer | UIN | Pages | Words | Clauses | Layout | Parse time |
|---|---|---|---|---|---|---|---|
| Family Health Optima | Star Health and Allied Insurance | SHAHLIP26046V092526 | 44 | 17,135 | 219 | two-column A4 | 3.2 s |
| my: Optima Secure | HDFC ERGO General Insurance | HDFHLIP25041V062425 | 53 | 20,958 | 207 | single column, `Def. N` | 4.2 s |
| ReAssure 2.0 | Niva Bupa Health Insurance | NBHHLIP23169V012223 | 24 | 12,852 | 166 | single column, multi-level | 3.2 s |
| Care Supreme | Care Health Insurance | CHIHLIP23128V012223 | 45 | 22,056 | 209 | small-page two-column | 4.1 s |
| **Total** | | | **166** | **73,001** | **801** | | |

Licence: public documents published by the insurers (copyright with each insurer), stored unmodified as sample input only; not affiliated or endorsed. Source URLs in `docs/04_DATASET.md`.

Evaluation set `data/eval/` (hand-written from the PDFs, evidence snippets verbatim): `qa.jsonl` **57** questions (51 answerable, 6 out-of-scope; Star 14, HDFC 13, Niva 12, Care 12, +6 out-of-scope), `qa_multilingual.jsonl` **5** (Hindi/Telugu), `claims.jsonl` **14** scenarios (covered 5, partly 1, not covered 7, needs info 1), `cards.json` **52** hand-checked Policy Card values. **Split: the whole set is a held-out test set; no model is trained or fitted on it.** Question categories: waiting_period 14, benefit 15, claim_process 8, exclusion 5, policy_terms 4, room_rent 3, sub_limit 2, out_of_scope 6.

Policy Card values verified in text (stored `verified_ratio`): Star 0.909, HDFC 1.000, Niva 1.000, Care 0.967. Risk highlights stored: Star 9, HDFC 4, Niva 6, Care 4 (23 total across the four samples).

---

## 6. Models and settings

| Role | Model | Notes |
|---|---|---|
| Generation, card, claim, comparison, translation | Google Gemini (`gemini-3.8-flash` → `gemini-3.6-flash` → `gemini-3.5-flash-lite`) | JSON schema, thinking level low, temperature 0.2 (answers) / 0.1 (card). **In the evaluation run every call was served by `gemini-3.5-flash-lite`** (free-tier quota of the larger two was exhausted). |
| Dense retrieval | `sentence-transformers/all-MiniLM-L6-v2`, 384-d, 91.6 MB, Apache-2.0 | local CPU |
| Re-ranker | `cross-encoder/ms-marco-MiniLM-L6-v2`, 91.8 MB, Apache-2.0 | local CPU |
| Faithfulness | `cross-encoder/nli-deberta-v3-xsmall`, 294.5 MB, Apache-2.0 | local CPU |
| Keyword | BM25 Okapi, k1 = 1.4, b = 0.7 + synonym list | `rank-bm25` |
| Vector store | ChromaDB persistent, cosine | collection `clauses_minilm`, 801 vectors |

Pipeline settings: answer_top_k 7 · candidates_per_retriever 30 · rerank_pool 20 · per_retriever_in_pool 8 · rrf_k 60 · abstain_below_rerank 0.004 · abstain_below_bm25 9.0 · temperature 0.2 · embedding provider local.

---

## 7. Results - run `eval-20260922-0027` (22 Sep 2026)

Headline: retrieval hit@5 **100 %** (51/51) · answer accuracy **100 %** (51/51) · citation accuracy **100 %** · faithfulness mean **87.0** (median 91.7) · abstention **6/6**, **0** false abstentions · Hindi/Telugu **5/5** · Claim verdicts **14/14** · Policy Card **51/52 = 98.08 %** (verified ratio 96.9 %) · median answer time **4.34 s** (p95 18.18 s).

### 7.1 Retrieval (51 answerable questions)

| Method | hit@1 | hit@3 | hit@5 | MRR@10 | recall@5 | median ms | p95 ms |
|---|---|---|---|---|---|---|---|
| BM25 | 0.6471 | 0.9216 | 1.0000 | 0.7791 | 1.0000 | 1.1 | 32.2 |
| Dense (MiniLM + Chroma) | 0.4902 | 0.7647 | 0.8039 | 0.6325 | 0.7941 | 10.7 | 15.7 |
| Hybrid (RRF) | 0.6863 | 0.8824 | 0.9608 | 0.7948 | 0.9510 | 11.0 | 16.6 |
| **Hybrid + re-rank (used)** | **0.8039** | **0.9804** | **1.0000** | **0.8971** | **0.9902** | 878.9 | 995.5 |

### 7.2 Answers (n = 62 incl. 5 multilingual + 6 out-of-scope; 0 errors)
answerable 51 → answer accuracy 1.0, key-fact recall 1.0, citation accuracy 1.0. By category: waiting period 14/14, benefit 15/15, claim process 8/8, exclusion 5/5, policy terms 4/4, room rent 3/3, sub-limit 2/2.
Faithfulness (56 scored answers): mean 87.0, median 91.7; bins 80-100: **45**, 50-79: **8**, 0-49: **3** (all three still correct and correctly cited).
Multilingual: 5/5 in requested script, key-fact recall 1.0.
Latency, all 62 live-Gemini answers: mean 5,544 ms, **p50 4,340**, p95 18,183, max 24,772. Per stage: retrieval mean 910 / p50 861 / p95 1,834 ms; generation (n 56) mean 4,158 / p50 2,528 / p95 17,155; faithfulness (n 56) mean 971 / p50 831 / p95 1,716.

### 7.3 Claim Copilot (n = 14, 0 errors)
Confusion matrix (rows expected, columns predicted: covered, partly covered, not covered, needs info):

| | covered | partly | not covered | needs info |
|---|---|---|---|---|
| covered (5) | 5 | 0 | 0 | 0 |
| partly covered (1) | 0 | 1 | 0 | 0 |
| not covered (7) | 0 | 0 | 7 | 0 |
| needs info (1) | 0 | 0 | 0 | 1 |

Accuracy 1.0; precision = recall = F1 = 1.0 for every label. Reasons' mean faithfulness 82.7; average 7.3 documents and 4.3 steps per check. Latency (the 4 timed live calls, others cached): mean 13,776 ms, p50 12,309, p95 22,761.

### 7.4 Policy Card extraction (52 values)
Overall 0.9808. By policy: Star 14/14 (1.0), HDFC 13/14 (0.9286), Niva 11/11 (1.0), Care 13/13 (1.0). Only miss: `cumulative_bonus` (0.5 over 2 policies) - HDFC document covers seven variants (10 % Optima Suraksha/Lite, 25 % Optima Select, none for Optima Secure which has a 50 %/year Plus Benefit); reference takes the general clause (10 %), card reports the Optima Secure figure - ambiguity in the wording. All other 16 fields: 1.0.

### 7.5 Abstention thresholds (from `docs/05_MODELS_AND_TRAINING.md` §4.3)
Out-of-scope (6): best re-rank ≤ 0.0029, best BM25 ≤ 7.3. Answerable (51): re-rank as low as 0.0020, BM25 as low as 7.1; the 3 answerable questions with re-rank < 0.004 had BM25 ≥ 15.5. Neither score separates alone; both together (re-rank < 0.004 AND BM25 < 9.0) → 6/6 declined, 0 false.

### 7.6 Improvement across the three kept runs

| Run | Change | hit@5 | Answer acc. | Citation acc. | False abstentions | Claim verdicts |
|---|---|---|---|---|---|---|
| eval-20260921-2353 | baseline | 98.0 % | 88.2 % | 92.2 % | 5 | 14/14 |
| eval-20260922-0008 | abstain only if both scores low; a rule and the tables it governs sent together | 98.0 % | 98.0 % | 96.1 % | 1 | 14/14 |
| eval-20260922-0027 | exclusion-code list items become separate clauses; prompt says an exclusion *is* an answer; non-network co-pay no longer applied to cashless | 100 % | 100 % | 100 % | 0 | 14/14 |

### 7.7 Honest limits of these numbers
- 51 answerable questions over 4 policies: "100 %" means no error found on this set, not that errors cannot occur.
- Abstention thresholds and parser fixes were made after studying failures on the same set → optimistic. A fresh unseen set is future work.
- Evaluated with the smallest model in the chain (`gemini-3.5-flash-lite`) because of free-tier quota.
- Faithfulness of 3 correct answers scored < 50 (NLI limits: exclusion item vs heading; inverted rule; abbreviation vs defined term). Adding the heading to the evidence lifted one case (0.003 → 0.92) but also confirmed a wrong statement (0.87 for "ectopic pregnancy is excluded"), so the change was **not** adopted.

---

## 8. Tests (run 15 Oct 2026)

- **Backend: 25 tests passed** (`pytest -q`, ≈ 15 s; tests/: auth 6, faithfulness 3, parser 3, policy_flow 7, units 6). Gemini never called in tests (schema-valid stand-in); real local models and a deterministic synthetic 2-page PDF.
- **Web: `npm run build` succeeds** (`tsc -b` strict + Vite 8 production build, 7.6 s Vite time).
- Evaluation harness: `ml/run_all.py` (≈ 10 min, ≈ 80 Gemini calls; `--skip-llm` for retrieval/card only).
- Demo scenario (5 steps) was run end-to-end against the live API and in a browser; screens captured at 1440 px (light, dark) and 390 px (mobile). Per `docs/09_TESTING.md`: no horizontal scroll at 360 px, no console errors (documented in the project, not re-run here).
- **Not tested**: concurrent users/load, penetration testing, other browsers, scanned-PDF OCR, user acceptance with real policyholders. See section 12.

---

## 9. Live demo run - 15 Oct 2026 (used for the screenshots)

Real calls to the running app (demo account, 4 sample policies, live Gemini; answers came from `gemini-3.5-flash-lite` / `gemini-3.6-flash`):

| Action | Outcome | Faithfulness | Time |
|---|---|---|---|
| "Is cataract surgery covered and after how long?" (Star) | answered - covered after the 24-month specified-disease wait, per-eye limits; citations Clause 2 p. 10, Clause Excl02 p. 28 | 88.1 | 6.2 s |
| "Is there a co-payment in this policy?" (Star) | answered | **37.9** (the same question scored **99.0** in an earlier seeding run the same day - the NLI score is sensitive to answer phrasing) | 5.6 s |
| "Does this policy insure my house against fire?" (Star) | `not_in_policy` - "not covered in this policy document", no AI call | n/a | 1.7 s |
| Hindi room-rent question (HDFC) | answered in Hindi with 4 citations | 91.5 | 10.0 s |
| Claim Copilot: knee replacement, Star, cashless, planned, started 2023-10-01, age 64, ₹3,50,000 | **partly covered** - waiting periods complete (36 months of cover), mandatory 20 % co-payment at age ≥ 61 | 86.8 | 14.2 s |
| Claim Copilot: knee replacement, cover started 2026-04-01, age 45, ₹3,00,000 | **not covered** (24-month specified-disease wait not complete; 6 months of cover) | 75 | 11.7 s |
| Compare Star vs HDFC Optima Secure | 21-row table; A better on 0 measurable items, B better on 2; overview + choose-A/B-if | - | - |

Observed defects (reported as limitations, not hidden): (a) Telugu translation of the Policy Card (`25_card_telugu.png`) contains one "Suits" line with **Bengali/Gurmukhi script mixed into the Telugu text**, and leaves bracketed English terms ("[sum insured]", "[claim]", "[co-payment]") untranslated; (b) faithfulness for an identical question varied 99.0 → 37.9 between two runs; (c) dashboard tiles at 1440 px show wrapped values ("10.8 / s") and uneven tile heights.

Demo account state: language `en`, theme `light` (it had been left on Telugu / dark by an earlier session; reset through `PATCH /users/me`).
Note: the frontend working tree contains an uncommitted rebuild; screenshots show the current working tree.

---

## 10. Screenshot inventory - `docs/screenshots/` (1440×900 unless noted; produced by `scripts/capture_screenshots.py` after `scripts/seed_docs_demo.py`)

| File | Screen |
|---|---|
| 01_landing, 01b_landing_full (1440×6744) | Landing page |
| 02_login, 03_register | Sign in / Create account |
| 04_dashboard, 04b_dashboard_full | Dashboard with real activity (4 questions, average faithfulness 73/100 over the 3 scored answers, median response 5.9 s, 2 claim checks, 9 high risks) |
| 05_policies | My policies - four ready sample policies |
| 06_policy_card, 06b_policy_card_full | Policy Card (English) with clause·page chips |
| 07_policy_risks, 07b_policy_risks_full | Risk highlights (9 for Star) |
| 08_policy_document, 08b_policy_document_highlight | Original page 28 with the Excl02 clause highlighted |
| 09_clause_search | Hybrid + re-rank clause search "cataract waiting period" with scores/timings |
| 10_chat_policy_picker | Ask your policy - choose policy |
| 11_chat_answer | Cataract answer with citations + faithfulness 88 + follow-ups |
| 11c_chat_copay | Co-payment answer (faithfulness 38 - weak-score case) |
| 11d_chat_not_in_policy | Out-of-scope question → "Not covered in this policy document" |
| 12_chat_citation | Citation sheet with highlighted source page |
| 13_chat_hindi | Hindi answer with "Show in English" |
| 14_claim_policy_step, 15_claim_treatment_step | Claim Copilot wizard steps 1-2 |
| 16_claim_result_partly, 16b_… full | Verdict "Partly covered" with pre-checks, documents, steps, estimate |
| 17_claim_result_not_covered, 17b_… full | Verdict "Not covered" |
| 18_compare_form, 19_compare_result, 19b_… full | Plan comparison form and result |
| 20_model_performance, 20b_… full | Measured quality page (public evaluation run) |
| 21_settings | Settings |
| 22_chat_dark, 22b_policy_card_dark | Dark theme |
| 23_mobile_chat, 24_mobile_policy_card (780×1688, 390 px @2×) | Phone layout |
| 25_card_telugu | Telugu Policy Card (limitation: mixed-script line) |

Plots from the evaluation run (`experiments/eval-20260922-0027/plots/`): `retrieval_ablation`, `faithfulness_distribution`, `latency_by_stage`, `answer_accuracy_by_category`, `claims_confusion_matrix`, `extraction_accuracy_by_field`.

---

## 10b. Extra analyses produced for the documents

- `scripts/abstention_scan.py` (through the live API, `POST /policies/{id}/search`, hybrid + re-rank, k = 7) re-measured the two scores behind the abstention rule for all 57 questions: answerable questions - 0 wrongly abstained, minimum best re-rank score 0.0020, minimum best BM25 7.1; out-of-scope - 6 of 6 abstained, maximum best re-rank 0.0029, maximum best BM25 7.3. Output `docs/charts/abstention_scan.json`, `abstention_scatter.png` (matches section 7.5).
- `scripts/make_charts.py` (from `experiments/*/metrics.json`): `headline_metrics.png`, `improvement_runs.png`, `claims_confusion.png`, `paper_results.png`.
- Deliverable page counts (Word, 15 Oct 2026): 17.Final Document 95 pages; 9: 10; 10: 6; 11: 10; 12: 9; 14: 25; 15: 7; IEEE paper 6 (PDF `19.IEEE_Paper.pdf`).

---

## 11. Documentation tooling

Diagrams (Step 2) → `docs/diagrams/` (matplotlib, 150 dpi). Decks and chapter documents are built by scripts in `scripts/` (`docs_build.py`, `build_*.py`, `verify_docs.py`). Commit by explicit pathspec only (the tree has modified `.env`, `MASTER_PROMPT*.md`, `data/app.db-*`, `logs/`, and an uncommitted frontend rebuild that must not be swept in).

---

## 12. What was NOT measured / not achieved (state plainly in every document)

1. **No numeric comparison with the base paper** - different task, language, domain and metric (section 1). No ROUGE was computed; PolicyLens does not summarise.
2. **No user study / user-acceptance test** with real policyholders; usability claims rest on the scripted demo scenario only.
3. **No load or concurrency testing**; single-user, single-machine measurements only. No GPU measurements.
4. **No security audit / penetration test**; security rests on JWT + bcrypt, owner-only access checks (covered by `test_policy_flow.py`), input validation and error handling.
5. **Evaluation is small (51 answerable questions, 4 policies, 14 claim scenarios) and partly tuned on itself**; not yet repeated on unseen policies or a larger set.
6. **Scanned PDFs (no text layer) are rejected**; no OCR. English wordings only for retrieval (Hindi/Telugu supported for questions, answers and card/risk translation, not for uploads).
7. **Claim Copilot gives guidance, not an insurer decision**; cost estimates depend on Policy Card values; plan-variant selection (e.g. HDFC seven variants) is not yet implemented.
8. **Translation quality** limited (Telugu card line with mixed scripts; bracketed English terms left in place).
9. **Evaluated with the smallest Gemini model** because of free-tier quota; larger-model results not measured.
10. **Faithfulness is a heuristic** (small NLI model + number check): 3 of 56 correct answers scored < 50; one identical question scored 99.0 and 37.9 in two runs.
11. Guide name, college, HOD, principal, academic year and all author e-mail addresses are **not available** - placeholders kept; no e-mail invented.
