# REPORT_FACTS - ClauseGuard (Batch CSDS-A-A6)

Single source of truth for the submission documents. Every number below was measured in this run
(2026-10-26) from the artefacts named next to it. Nothing in the documents may disagree with this file.

## 1. Identity

| Item | Value |
|---|---|
| Product | ClauseGuard |
| Project title | Legal Contract Complexity & Predatory Clause Detector |
| Batch | CSDS-A, Batch A6 (Department of Computer Science and Engineering (Data Science), Section A) |
| Students | CH.PRANATHI 23K91A6744 · G.PRANAVI 23K91A6762 · G.CHARAN JOSEPH 23K91A6753 · G.BHAGWATH 23K91A6760 |
| Guide | **Not stated** - the batch file shows the placeholder "GUIDE NAME" (kept as `[GUIDE NAME]`) |
| College / HOD / Principal / academic year / designation | not in the batch files - square-bracket placeholders stay |
| Ports | backend 8106, frontend 5106 |
| Base paper (per `3.BASE PAPER.docx` and `Documentary/A6 Base paper.pdf`) | F. Almutairy, S. Almutairi, M. Abdullah, S. Salman, "SmartLaw Advisor: AI-Powered Legal Consultation and Contract Analysis for Saudi Arabia," IEEE Access, vol. 14, p. 32638 ff. (end page not verified), 2026, doi 10.1109/ACCESS.2026.3665420 |

Note: `archived_base_papers/BASEPAPER_REFERENCES.md` names a different 2026 paper ("A Few Good Clauses", arXiv 2605.05532) as base
and ContractEval as companion. The batch's own submitted documents (abstract, base paper, literature survey) name SmartLaw Advisor, so
**SmartLaw Advisor is the base paper**; the other three PDFs are used as supporting literature (read in full by this run).

## 2. What the code actually is (vs. the abstract)

Stack: React 19 + Vite + Tailwind (JavaScript/TypeScript mix) · FastAPI 0.115 · SQLAlchemy 2.0 + SQLite · PyMuPDF + python-docx ·
Google Gemini (`google-generativeai` 0.8.3) for embeddings, tie-break, explanations, summaries · NumPy cosine search · NetworkX 3.3 · JWT (PyJWT) + bcrypt.
Python 3.11.9, Node 24.19.0. Backend app code is about 1,250 lines in 17 files; `ml/eval.py` 144 lines.

| Abstract / objective says | The code does | Status |
|---|---|---|
| RAG with the **Claude API** | **Gemini** for everything generative (`gemini-flash-latest` default; this run used `gemini-3.1-flash-lite`) | differs |
| **pgvector** semantic search over clause embeddings | clause embeddings stored as float32 BLOBs in SQLite; NumPy cosine similarity (`services/vectorstore.py`) | differs |
| **Neo4j** graph of clause types, legal concepts, precedents | NetworkX in-memory graph, one node per clause, edges from **3 hard-coded combination patterns**; no legal-concept or precedent nodes; rebuilt per request, not stored | partial |
| RAG (retrieve legal context, then generate) | No retrieval over a legal corpus. "Retrieval" = nearest-centroid match against 20 CUAD category centroids. Gemini is prompted with the matched rule's hand-written `legal_basis` text (grounding by prompt, not by retrieval) | partial |
| Flag predatory clauses with **Indian contract-law criteria** | 8 hand-written regex rules, each tagged with an Indian statute (ICA 1872 s.27/s.74/s.73, Arbitration and Conciliation Act 1996, Copyright Act 1957, Consumer Protection Act 2019) | done (shallow) |
| Clause classification | Gemini `gemini-embedding-001` (3,072-d) nearest centroid over 20 CUAD categories; optional Gemini tie-break | done |
| Complexity score + plain summary | Flesch + legalese density + cross-references + sentence length -> 0-100 -> grade A-F; Gemini summary | done |
| Evaluate classification and predatory detection **separately** | `ml/eval.py` -> `experiments/eval/metrics.json`, shown on the Evaluation screen | done |

## 3. Pipeline (`backend/app/services/pipeline.py`)

1. **Parse** (`parsing.py`): PDF via PyMuPDF per page (real page numbers); DOCX via python-docx, whole document = page 1.
2. **Segment**: per page, split at numbered headings matched by `^\s*(Article|Section|Clause)?\s*\d{1,2}(\.\d{1,2})*[.):]?\s+\S`; if a page has fewer than 2 headings, merge blank-line paragraphs up to ~400 characters. Fragments under 25 characters are dropped.
3. **Classify** (`classification.py`): embed the clause (RETRIEVAL_QUERY), cosine against 20 centroids (mean of 25 CUAD training spans each, cached in `data/cuad_centroids.npz`); if top-1 minus top-2 < 0.03 **and** top-1 < 0.60, ask Gemini to choose among the top 3; if confidence < 0.35 label "Other / Unclassified".
4. **Detect** (`rules.py`): 8 case-insensitive regex rules; each hit -> one `Flag` row. Gemini then writes `reason`, quotes the `provision`, drafts `safer_wording` (one call per flag).
5. **Combine** (`graph.py`): 3 combinations (termination+no-refund+penalty; restraint+unlimited liability; auto-renewal+unilateral termination); a combination fires when all its rule ids occur anywhere in the contract.
6. **Score** (`complexity.py`): `score = 0.35*(100-Flesch) + 0.30*min(100, 8*legalese%) + 0.20*min(100, 40*xref/clauses) + 0.15*clip(3*(avgSentenceLen-15), 0, 100)`; grade A <20, B <40, C <60, D <80, F >=80.
7. **Summarise** (`explain.py`): one Gemini call over the first 40 clause excerpts + flag list -> `plain_summary`, `key_obligations`.
8. Persist (SQLite), return the report.

The 8 rules: restraint_of_trade (high), penalty_clause (medium), unilateral_termination (high), unlimited_liability (high), one_sided_arbitration (medium), auto_renewal (medium), ip_overreach (high), no_refund (medium).

## 4. API (all under `/api`)

| Method + path | Auth | Purpose |
|---|---|---|
| GET `/health` | no | status, `gemini_configured`, port |
| POST `/auth/register` | no | email + password (>= 6) -> JWT (HS256, 1,440 min), bcrypt-hashed password |
| POST `/auth/login` | no | -> JWT |
| POST `/contracts/upload` | Bearer | multipart PDF/DOCX -> full pipeline -> report (503 without key, 400 wrong type/empty, 502 Gemini failure) |
| GET `/contracts` | Bearer | caller's contracts with grade and flag count |
| GET `/contracts/{id}` | Bearer | report: grade, 4 component scores, summary, obligations, combos, clause list |
| GET `/contracts/{id}/clauses/{cid}` | Bearer | clause text, type, confidence, method, flags with reason/provision/safer wording |
| GET `/contracts/{id}/graph` | Bearer | nodes, edges, risky combinations |
| GET `/eval/metrics` | no | contents of `experiments/eval/metrics.json` |

Other users' contracts return 404 (ownership check in `_get_owned_contract`). Missing token -> 403, bad/expired token -> 401. CORS is `*`.

## 5. Database (SQLite, `data/app.db`, SQLAlchemy models in `db.py`)

`users(id, email UNIQUE, password_hash, created_at)` -> `contracts(id, user_id FK, filename, contract_type_guess [never set: always "general"], uploaded_at, complexity_grade, complexity_score, readability_score, legalese_density, cross_reference_count, avg_sentence_length, plain_summary, key_obligations JSON, combo_flags JSON)` -> `clauses(id, contract_id FK, index_in_doc, page_number, text, clause_type, classification_confidence, classification_method, embedding BLOB)` -> `flags(id, clause_id FK, rule_id, rule_label, severity, reason, provision, safer_wording)`. Cascade delete from user down. 4 tables, 3 foreign keys.

## 6. Data

| Dataset | Source / licence | Use |
|---|---|---|
| CUAD v1 (Atticus Project) | `github.com/TheAtticusProject/cuad`, CC BY 4.0; 510 contracts, 41 categories, `data/cuad/CUADv1.json` ~40 MB committed | classification centroids, held-out classification test, corpus-scale run |
| `data/sample/cuad_train_examples.json` | derived, seed 42 | 20 categories x 25 spans = 500 (497 distinct texts) |
| `data/sample/cuad_eval_set.json` | derived, seed 42 | 240 held-out spans, 12 per category |
| `data/sample/predatory_test_set.json` | authored by the project (same author as the rules) | 40 labelled clauses |
| `experiments/rules/` probe set | authored in this docs run (`scripts/exp_rules_corpus.py`, `PROBE`) | 24 predatory paraphrases + 16 benign look-alikes |

Split caveat found in this run: the train/eval split is by **span text, not by contract**. 192 of the 240 evaluation spans come from a contract that also supplied training spans, and 4 evaluation texts are exact duplicates of training texts.
Classification examples are CUAD *annotation spans* (median ~290 characters), not whole contract clauses (median segmented clause in CUAD = 1,158 characters).

## 7. Measured results

### 7.1 Predatory-clause rules (no API; `experiments/eval/metrics.json`, `experiments/rules/metrics.json`)

| Test set | n | Precision | Recall | F1 | Notes |
|---|---|---|---|---|---|
| Shipped set (authored with the rules) | 40 clauses (34 labelled rule hits) | 1.000 | 0.941 | 0.970 | TP 32, FP 0, FN 2 (a "shall not ... provide services ... compete" franchise clause; an "only the Company may refer ... arbitration" clause) |
| Independent probe set (this run) | 24 predatory + 16 benign | **0.786** | **0.458** | **0.579** | TP 11, FP 3, FN 13 |

Probe false alarms: fair capped *liquidated damages* flagged as penalty; "shall not engage in any outside activity that creates a conflict of interest" flagged as restraint of trade; "Both parties shall be liable for any and all losses caused by their own gross negligence" flagged as unlimited liability.
Probe misses (13): paraphrases without the keyword ("agrees not to accept any engagement...", "must not carry on ... a business similar", "forfeit Rs. 50,000 ... per day", "pay a sum equal to the full contract value as damages", "reserves the right to end this engagement whenever it chooses", "responsibility for every loss ... no upper cap", "liability ... shall be unlimited", "sole arbitrator appointed by the Company", "Only the Company has the right to initiate arbitration", "continue for further one-year periods unless", "Everything the Freelancer creates ... belongs to the Company", "cannot be returned for any reason", "shall not be entitled to any refund" ("not be entitled" does not match `not entitled`).
Probe per-rule recall: auto_renewal 0.667, ip_overreach 0.667, unilateral_termination 0.667, no_refund 0.333, one_sided_arbitration 0.333, penalty 0.333, restraint 0.333, unlimited_liability 0.333.

**Interpretation**: the headline 100 % / 94 % / 97 % is real but measured on clauses written by the rule author; on independently phrased clauses the same rules reach P 0.79 / R 0.46. The Evaluation screen's wording "measured on a held-out set. Nothing here is hand-picked" overstates what the 40-clause set is.

CUAD cross-check (`experiments/rules/metrics.json`, `cuad_spans`; CUAD categories are *not* the same concept as predatory, so this is a proxy):

| CUAD category -> rule | CUAD spans | Rule fires | Rate |
|---|---|---|---|
| Non-Compete -> restraint_of_trade | 257 | 21 | 8.2 % |
| Liquidated Damages -> penalty_clause | 121 | 68 | 56.2 % |
| Termination For Convenience -> unilateral_termination | 246 | 32 | 13.0 % |
| Uncapped Liability -> unlimited_liability | 167 | 0 | 0.0 % |
| Renewal Term -> auto_renewal | 208 | 69 | 33.2 % |
| Ip Ownership Assignment -> ip_overreach | 317 | 0 | 0.0 % |

On 5,032 distinct spans of 11 unrelated CUAD categories (governing law, audit, insurance, licence grant, warranty, revenue share, minimum commitment, post-termination, change of control, exclusivity, cap on liability) any rule fired on 37 (0.74 %): restraint 14, penalty 12, unilateral termination 10, no_refund 3.

### 7.2 CUAD clause classification (Gemini `gemini-embedding-001`, 3,072-d; `experiments/eval/metrics.json`, `experiments/classification/metrics.json`)

Produced by the **unmodified `ml/eval.py`**, with the embedding call answered from vectors cached by `scripts/exp_embed_cache.py` (the same API calls the product makes).

| Measure | Value |
|---|---|
| Held-out spans / categories | 240 / 20 |
| **Top-1 accuracy** | **0.792** (190/240); 0.797 after removing the 4 exact duplicates |
| **Top-3 accuracy** | **0.979** |
| Top-5 | 0.983 |
| Contract-disjoint top-1 (centroids rebuilt without any training span from the same contract) | 0.800 (192 of 240 items had a same-contract training span) |
| Chance | 0.05 |

Baselines on the same split (top-1): TF-IDF nearest centroid 0.621 · TF-IDF + logistic regression 0.675 · embedding 1-NN 0.604 · embedding 5-NN 0.746 · embedding + logistic regression 0.800 · **embedding nearest centroid (shipped) 0.792**.
Best categories (recall): Governing Law 1.00, Ip Ownership Assignment 1.00, Renewal Term 1.00. Weakest: Non-Compete 0.50, Cap On Liability 0.50, No-Solicit Of Customers 0.58 (precision 0.44), Exclusivity 0.67, Liquidated Damages 0.67, Uncapped Liability 0.67.
Top confusions: Uncapped -> Cap On Liability (4), Non-Compete -> No-Solicit Of Customers (4), No-Solicit Employees <-> Customers (3 + 3), License Grant -> Exclusivity (3), Cap On Liability -> Warranty Duration (3), Cap On Liability -> Uncapped (3).
Confusion matrix: `experiments/classification/confusion.csv`.

**Two thresholds never act**: on the 240 spans the top-1 cosine ranges 0.657-0.849 (median 0.767). The tie-break needs top-1 < 0.60 (0 of 240 trigger it) and the "Other / Unclassified" floor is 0.35 (0 of 240). The same holds in the three real uploads (all 30 clauses have method `embedding`, confidence 0.72-0.83). The margin test alone would fire on 152 of the 240 spans (top-1 minus top-2 < 0.03, median margin 0.023), but the tie-break needs the margin test **and** top-1 < 0.60, and no span is below 0.657. With this embedding model those two branches are dead code, so every clause is forced into one of the 20 labels. (Constants were tuned for a different embedding model's similarity scale.)

### 7.3 Corpus-scale run of the non-API pipeline (all 510 CUAD contracts; `experiments/corpus/metrics.json`, `contracts.csv`)

Segment -> rules -> combinations -> complexity, as the upload route does, on CUAD full texts treated as one page.
510/510 parsed. **28.5 s in total = 56 ms per contract**. 23,869 clauses (median 20.5 per contract, mean 46.8, min 1, max 611); median mean-clause length 1,158 characters. 444 contracts split on numbered headings; **84 contracts yield fewer than 5 clauses** (headings in other styles, e.g. "ARTICLE I", roman numerals, are not recognised).
2.2 % of clauses flagged; 255/510 contracts have at least one flag; 11 contracts show a risky combination (autorenew+unilateral termination 10, termination+no-refund+penalty 2). Clauses per rule: restraint 163, penalty 152, unilateral termination 84, no_refund 72, auto_renewal 66, unlimited_liability 4, one_sided_arbitration 0, ip_overreach 0.
Complexity grades: A 4, B 169, C 268, D 68, F 1 (score min 6.9, median 45.5, mean 45.8, max 85.5, sd 12.3). Median components: Flesch 25.7, legalese 1.13 per 100 words, cross-references 26, average sentence 28.9 words. Correlation of score with contract length 0.30.

### 7.4 Format parity - same contract as DOCX and as PDF (`experiments/parity/metrics.json`)

| File | Clauses | Rules found | Combinations |
|---|---|---|---|
| freelance_services_agreement.docx | 11 | **8 of 8** | 3 |
| freelance_services_agreement.pdf (identical text) | 11 | **6 of 8** (ip_overreach and one_sided_arbitration missed) | 3 |
| same PDF, whitespace collapsed before matching | 11 | 8 of 8 | 3 |
| balanced_consulting_agreement.docx | 8 | 0 | 0 |

Cause: PDF text keeps visual line breaks and several rules use `.{0,N}`, which does not cross a newline. Also, text before the first numbered heading (title, parties, recitals) is dropped whenever a page has >= 2 headings. (The CUAD-PDF-vs-original comparison in the same file is *not* like-for-like because the typeset PDF merged lines; do not quote it.)

### 7.5 End-to-end uploads through the UI (real Gemini calls; `experiments/ui/state.json`, SQLite `data/app.db`)

Run with `GEMINI_TEXT_MODEL=gemini-3.1-flash-lite` set on the backend process only.
Why: the default `gemini-flash-latest` resolves to `gemini-3.8-flash`, whose free tier allows **20 `generate_content` requests per day**; it returned 429 and timed out (504 after ~29 s) at the start of this run. `gemini-3.1-flash-lite` answers a trivial prompt in ~6 s. Embeddings were unaffected.

| Upload | Clauses | Flags | Combos | Grade (score) | Time |
|---|---|---|---|---|---|
| freelance_services_agreement.docx (invented, one-sided) | 11 | 8 (one per rule) | 3 | B (23.3) | **113.6 s** (11 embeddings + 8 explanations + 1 summary) |
| balanced_consulting_agreement.docx (invented, fair) | 8 | 0 | 0 | A (13.7) | **15.5 s** (8 embeddings + 1 summary) |
| supply_agreement_cuad.pdf (real CUAD contract: Fusion supply agreement, public SEC exhibit, typeset to a 10-page PDF) | 11 | 1 (unilateral termination) | 0 | C (53.8) | **54.6 s** (11 embeddings + 1 explanation + 1 summary) |

Roughly 12 s per Gemini text call. The frontend's upload request times out at 180 s, so a contract with ~14+ flags would fail in the UI even though the backend would finish.
Observations: the complexity grade of the one-sided freelance contract is **B** (plain words) - complexity measures wording, not fairness. The same original CUAD text gives 25 clauses / 2 flags / 1 combination, the typeset PDF 11 / 1 / 0 (typesetting artefact, see 7.4).
Clause-type labels on whole contract clauses (author's manual reading, indicative only, n = 19): freelance contract 5/11 plausible (Termination, Penalty, IP, Renewal, Governing Law right; Scope->"Ip Ownership Assignment", Fees->"Liquidated Damages", Liability->"Cap On Liability" [the opposite of the clause], Dispute->"Cap On Liability", Non-compete->"No-Solicit Of Customers", Confidentiality->"Non-Disparagement"); balanced contract 4/8 plausible. This is lower than the 79 % on spans because whole clauses carry a heading and several topics.
The Gemini summary of the freelance contract said the IP assignment covers "all your past and future intellectual property" and the summary of the CUAD contract called a contract party "Fusion and CPDC" - plausible paraphrase, not verified against the source by an expert.

### 7.6 API response times (`scripts/measure_api.py`, 127.0.0.1, 30 repeats; i5-12500, 15.7 GB, Windows 11; other sessions were also using the machine)

| Endpoint | Median | p95 |
|---|---|---|
| GET /health | 2.5 ms | 4.0 ms |
| POST /auth/login (bcrypt) | 254.7 ms | 260.8 ms |
| POST /auth/register (bcrypt) | 265.0 ms | 268.6 ms |
| GET /contracts | 15.3 ms | 19.0 ms |
| GET /contracts/{id} (report, 11 clauses) | 9.3 ms | 11.2 ms |
| GET /contracts/{id}/clauses/{cid} | 5.0 ms | 6.1 ms |
| GET /contracts/{id}/graph | 9.2 ms | 11.8 ms |
| GET /eval/metrics | 2.5 ms | 3.6 ms |
| no token (403) / unknown contract (404) / wrong file type (400) | 1.8 / 5.0 / 4.0 ms | 2.3 / 8.9 / 5.7 ms |

### 7.7 Automated tests (`tests/`, pytest 9.1.1, venv Python 3.11.9)

**68 passed, 5 xfailed (73 tests) in about 10 s**; Gemini is stubbed (deterministic fake embeddings and JSON), every API test runs on a temporary SQLite file.
Files: `test_rules_graph.py` (rules, shipped-set score, 3 combinations, graph JSON), `test_complexity_parsing.py` (syllables, Flesch, legalese, cross-references, 8 grade boundaries, heading split, fallback merge, preamble dropped, page numbers, DOCX and PDF extraction, vector store), `test_classification.py` (nearest centroid, tie-break trigger, tie-break failure fallback, invalid category, Unclassified floor), `test_api.py` (health, register/login, duplicate email, 422 validation, wrong password, hashed password, missing/garbage/expired/forged/deleted-user token, full upload pipeline, report/list/detail/graph, cross-user 404, unknown ids, wrong extension, empty text, 503 without key, 502 + temp file removed, eval endpoint, malformed Gemini JSON).
The 5 xfails document known limits: 3 keyword-free paraphrases the regexes miss, one fair liquidated-damages clause that is flagged, and malformed Gemini JSON (JSONDecodeError is a ValueError, so the upload route answers HTTP 400 instead of 502). Scripts `scripts/smoke_test.py` (live end-to-end, needs a key) pre-existed.
Not covered: no browser/UI automated tests, no load test, no security scan; Gemini output quality is never asserted.

## 8. Known defects and limitations (state plainly in every document)

1. Abstract promises Claude API, pgvector, Neo4j; build uses Gemini, SQLite BLOB + NumPy, in-memory NetworkX (Section 2).
2. Rules are 8 regexes: independent-probe recall 0.46, precision 0.79; paraphrases missed; fair clauses sometimes flagged.
3. The 40-clause test set was written by the rule author; the Evaluation screen presents it as a held-out set.
4. PDF line breaks defeat some rules (8 of 8 vs 6 of 8 on identical text); text before the first numbered heading is discarded; a clause spanning a page break is cut in two; DOCX has no page numbers; headings other than `1.`/`Section 1` are not recognised (84/510 CUAD contracts give < 5 clauses); scanned (image) PDFs are unreadable.
5. Classification: 79.2 % top-1 on spans, but the split is not contract-disjoint (checked: 0.800 when it is), tie-break and Unclassified branches never trigger (similarities 0.66-0.85), so clauses outside the 20 categories are forced into one; whole-clause labels look ~50 % plausible in 19 hand-read clauses.
6. Complexity score is lexical (readability, jargon, cross-references, sentence length); it does not measure fairness (the predatory contract scored B/23.3, the fair one A/13.7). Weights and grade cut-offs were chosen by the author and are not validated against human ratings.
7. Risk combinations: 3 fixed patterns, matched on rule ids anywhere in the contract (not on proximity or the same party).
8. Explanations, safer wording and summaries come from Gemini and are not verified by a lawyer; no hallucination measurement was made. Output is information, not legal advice.
9. Indian law: statute names are written into rule text; there is no Indian contract corpus - CUAD is US SEC filings. No evaluation on Indian contracts was possible.
10. Gemini dependency: free-tier quotas (20 text requests/day/model observed), ~12 s per call, 180 s UI timeout; a failed upload loses everything (no partial result is stored); CORS `*`; JWT secret from `.env`; no rate limiting; `contract_type_guess` is never set.
11. Frontend: table pagination is client-side (the list endpoint returns every contract); no automated UI tests.
12. Hardware: i5-12500 (12 threads), 15.7 GB RAM, no GPU used (all models are remote API calls).

## 9. Literature facts (read from the PDFs in `Documentary/` and `archived_base_papers/`; do not add numbers beyond these)

- **[1] SmartLaw Advisor** (base): Gemini 1.5 Flash with standard RAG over a custom Arabic Saudi corpus (GATE-AraBERT-v1 embeddings, Chroma; the paper also mentions a FAISS index of ~18,400 vectors, 152 MB), cross-encoder reranking, OCR-driven normalisation, JSON-constrained clause extraction at temperature 0.2. Two functions: legal chatbot and contract analysis (checklist of essential clauses validated by Saudi practitioners + LLM-assisted semantic check). Evaluated on 150 legal questions over 10 domains and **50 real contract drafts**; Gemini 1.5 Flash 98.67 % (148/150), 1.63 s average response (baseline); GPT-3.5 98.00 % (147), GPT-4 97.33 % (146), ALLaM 96.00 % (144). RAG similarity 96.57 % for Gemini at 143.52 s per query (evaluation pipeline, not deployed latency). Contract-analysis results are qualitative (clause-by-clause inspection of Gemini, ALLaM, Command-A, GPT-4 outputs on sample contracts). Failure cases: retrieval across chunk boundaries, clause misclassification. Cloud environment: Xeon Platinum 8272CL, 32 GB, Ubuntu 20.04. Limits: Arabic/Saudi law only, small expert-reviewed dataset, no graph reasoning, no clause-combination analysis, no complexity score.
- **[2] ContractEval** (Liu et al., arXiv:2508.03080, Aug 2025, supporting): CUAD test data, 41 risk categories, 19 LLMs (4 proprietary: GPT-4.1, GPT-4.1 mini, Gemini 2.5 Pro preview, Claude Sonnet 4; 15 open-source); metrics F1/F2, Jaccard, and "no related clause" laziness rate; proprietary > open-source; thinking mode raises effectiveness but lowers correctness; the top two models reach F2 of 0.672 and 0.678.
- **[3] A Few Good Clauses** (Lincoln et al., Onit, arXiv:2605.05532, May 2026): domain-trained SLM (Olava Extract) vs five frontier LLMs on 24 held-out contracts, 508 field instances, 26 targets: macro F1 0.812, micro F1 0.842; extraction cost down 78-97 % under batching.
- **[4] LDAS** (Dhaksha Charan R, Siddarth S, Jeevitha M, IJRASET vol. 14 issue IV, Apr 2026, doi 10.22214/ijraset.2026.79369): AWS Lambda/S3 + GenAI, 10 clause types, missing/risky clause detection against a template, weighted risk score 0-100; primary test document risk 87/100 with 6 high + 2 medium missing clauses; 94.2 % average extraction accuracy on 20 synthetic contracts; Pearson r = 0.87 between risk score and expert ratings on 30 contracts.
- **CUAD** (Hendrycks et al., 2021): 510 contracts, 41 categories, 13,000+ expert annotations; CC BY 4.0 (corpus facts as counted from the local copy: 510 contracts).
- Batch literature-survey items **not retrievable here** (title only, no results to be quoted): ClauseMiner (Eng. Appl. of AI, 2026); "Autonomous Contract Analysis and Clause Risk Detection using Legal-BERT" (ICSCN 2025); "A Study on LLM-Based Approach for Construction Contract Risk Detection" (2024 Int. Conf. on Big Data and Digital Management); ContractEval is available as [2].
- Standard method references for the paper/report: Devlin et al. BERT (2019); Lewis et al. RAG (2020); Chalkidis et al. Legal-BERT (2020); Hendrycks et al. CUAD (2021); Robertson & Zaragoza BM25; Flesch (1948); Reimers & Gurevych Sentence-BERT (2019); Hagberg et al. NetworkX (2008); Pedregosa et al. scikit-learn (2011). (Only cite what is verifiable; the Flesch, NetworkX, scikit-learn, RAG and BERT references are standard and well known.)

## 10. Objectives versus outcome (from `6.OBJECTIVES&PROBLEM STATEMENT.docx`)

| # | Objective | Outcome |
|---|---|---|
| 1 | Segment contracts into clauses and classify clause types | Achieved with limits: heading-based segmenter (84/510 CUAD contracts < 5 clauses); 79.2 % top-1 / 97.9 % top-3 on 240 CUAD spans |
| 2 | RAG pipeline with Claude API + pgvector | **Not as stated**: Gemini + SQLite/NumPy; no retrieval from a legal corpus |
| 3 | Neo4j knowledge graph of clause relationships, concepts, precedents | **Partly**: NetworkX per-contract graph, 3 combination patterns, no concepts/precedents |
| 4 | Flag predatory clauses and combinations under Indian law criteria | Achieved in a limited form: 8 rules + 3 combinations; shipped-set P 1.00 / R 0.94, independent probe P 0.79 / R 0.46 |
| 5 | Overall complexity score and plain-language risk summary | Achieved: A-F grade from 4 components; Gemini summary and obligations (quality not expert-verified) |
| 6 | Evaluate classification and predatory detection separately | Achieved: separate metrics, plus extra probe set and CUAD cross-check |

## 11. Screenshot inventory (`docs/screenshots/`, 1440x900, Playwright + Chrome, real data)

Demo user `neha.legal@example.com` registered through the UI; contracts 1-3 are the uploads of Section 7.5.

| File | Shows |
|---|---|
| 01_landing.png | Landing page with the four feature cards |
| 02_landing_how_it_works.png | Landing page scrolled: how it works and measured stats |
| 03_register.png | Sign-up form filled |
| 04_login.png | Log-in form |
| 05_upload_empty.png | Upload page, no file |
| 06_upload_file_selected.png | freelance_services_agreement.docx selected |
| 07_upload_analysing.png | Analysing state (indeterminate bar) |
| 08_report_freelance_top.png | Report: grade B / 23.3, six metrics, plain-language summary, severity chart |
| 09_report_freelance_clauses.png | Same report scrolled: obligations and risky combinations |
| 10_report_freelance_table.png | Clause table with type, flag count, risk |
| 11_clause_detail_termination.png | Clause 2: flag Unilateral Termination, reason, provision, safer wording |
| 12_clause_detail_penalty.png | Clause 4: penalty flag |
| 13_clause_detail_noncompete.png | Clause 5: restraint-of-trade flag |
| 14_clause_graph.png | Clause graph: 11 nodes, 3 combination edge groups, combination explanations |
| 15_report_balanced.png | Fair contract: grade A / 13.7, no flags |
| 16_report_cuad_pdf.png | Real CUAD contract PDF: grade C / 53.8, 1 flag |
| 17_report_cuad_pdf_table.png | Its clause table |
| 18_upload_wrong_type.png | Validation error for a .txt file |
| 19_contracts_list.png | My contracts list with the three uploads |
| 20_evaluation.png | Evaluation: precision 100 %, recall 94 %, F1 97 %, per-rule table |
| 21_evaluation_lower.png | Evaluation: per-rule table and CUAD classification 79 % / 98 % |

Sample inputs: `docs/sample_inputs/` (freelance_services_agreement.docx/.pdf, balanced_consulting_agreement.docx, supply_agreement_cuad.pdf; the first two are invented, the third is a real public CUAD contract).

## 12. How to reproduce

```
venv\Scripts\python.exe -m pytest                                  # 68 passed, 5 xfailed
venv\Scripts\python.exe scripts\exp_embed_cache.py                 # needs GEMINI_API_KEY (~740 embedding calls, ~7 min)
venv\Scripts\python.exe scripts\exp_classification.py              # runs ml/eval.py on the cache + extras
venv\Scripts\python.exe scripts\exp_rules_corpus.py                # rules, probe set, 510-contract run
venv\Scripts\python.exe scripts\exp_format_parity.py               # DOCX vs PDF
python scripts\capture_screens.py public|freelance|detail|others|eval
python scripts\measure_api.py
```
Servers for the captures: backend `uvicorn app.main:app --port 8106` with `GEMINI_TEXT_MODEL=gemini-3.1-flash-lite`, frontend `npm run dev` (port 5106, reach it as `localhost`, not 127.0.0.1).

## 13. Diagrams and charts (generated by `scripts/make_diagrams.py`, `scripts/make_charts.py`)

`docs/diagrams/`: 01_system_architecture, 02_high_level_workflow, 03_dfd_level0, 04_dfd_level1 (7 processes, 5 stores D1-D5), 05_dfd_level2 (process 3.0 Classify clauses, sub-processes 3.1-3.7), 06_er_diagram (4 tables), 07_uml_class_diagram, 08_use_case_diagram (UC1-UC7, actors Signatory, Visitor, Gemini, Evaluator), 09_sequence_diagram (upload and read), 10_algorithm_flowchart (Algorithm 1 process_upload, Algorithm 2 classify_clause).
`docs/charts/`: 01_classification_per_category, 02_classification_baselines, 03_rules_two_test_sets, 04_rule_recall, 05_confusion_matrix, 06_complexity_distribution, 07_cuad_rule_hits, 08_latency, 09_confidence_thresholds, 10_format_parity.

## 14. Extra code-reading findings (added during the build)

- `.env.example` sets `GEMINI_TEXT_MODEL=gemini-2.0-flash` and `GEMINI_EMBEDDING_MODEL=models/text-embedding-004`; both returned HTTP 404 on this key. `config.py` reads only `GEMINI_TEXT_MODEL` and `GEMINI_EMBEDDING_MODEL`; the later `GEMINI_MODEL` / `GEMINI_EMBED_MODEL` lines are ignored. The working `.env` of this run sets `gemini-flash-latest` and `models/gemini-embedding-001`.
- The upload route has no file-size limit and checks only the file extension (not the content).
- CUAD span length: mean about 306 characters (training) and 290 (held-out); the median clause segmented from a CUAD contract is 1,158 characters.
