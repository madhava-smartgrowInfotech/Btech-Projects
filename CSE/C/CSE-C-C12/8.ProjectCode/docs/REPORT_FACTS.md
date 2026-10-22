# REPORT_FACTS - SymptoTrackAI (CSE-C-C12)

Everything in the documents must agree with this file. Numbers come from `docs/metrics/*.json` (measured on 2026-10-22 by `scripts/measure_metrics.py`, `scripts/measure_latency.py`, pytest and `scripts/smoke_test.py`); nothing here is estimated.

## 1. Identity

- Project title: **SymptoTrackAI: Hybrid RAG Based Symptom Tracking and Health Monitoring System**. The application is implemented, and shown on screen, as **CareLens AI** (name in the code); the documents call the project SymptoTrackAI and name CareLens AI as the implemented web application.
- Batch C12 (CSE-C); guide Dr. Ch. B. Naga Lakshmi; students: Mariyada Karthika Reddy (23K91A05E9); Nacharam Akshaya (23K91A05G6); Madoori Prabath Teja (23K91A05D6); Pulimadhi Keerthan (23K91A05K1).
- Base paper: U. S. Madhury and M. Ramesh, "A hybrid retrieval-augmented generation framework for intelligent symptom monitoring and disease guidance," *Int. J. Eng. Res. Sci. Technol.*, vol. 22, no. 3, pp. 702-707, 2026, doi: 10.62643/ijerst.2026.v22.n3.4170.  It reports **no numbers** (qualitative 'experimental observations'; one example: constipation + stomach ache + high fever + swollen lymph nodes -> Typhoid). It uses a 'Sequence-NQ transformer' + FAISS + RAG over a symptom-disease knowledge base, with registration/login and a stored consultation history.
- Ports: backend 8412, frontend 5412. Demo login `demo@carelens.ai` / `Demo@1234`.

## 2. Architecture (from the code)

`symptoms -> normalise -> HyDE-style template expansion -> MiniLM embedding -> FAISS (IndexFlatIP, 384-d) + BM25 (rank-bm25) -> min-max fusion 0.65/0.35 (top 15) -> MS-MARCO MiniLM cross-encoder rerank (top 5) -> grounded generation (Flan-T5-small, or evidence-based fallback) -> regex safety layer + answer filter -> UI + SQLite`
- Backend: FastAPI + Uvicorn, SQLAlchemy/SQLite (`users`, `consultations`), bcrypt, PyJWT HS256 (httponly cookie `carelens_token`, 1440 min), Pydantic v2. Frontend: React 19 + Vite 8 (kit V2 'Neo Brutal Grid'), react-router 7, recharts. Legacy Jinja pages remain served by the backend (`/`, `/login`, `/dashboard` ...).
- Models (all local, CPU): `sentence-transformers/all-MiniLM-L6-v2` (384-d), `cross-encoder/ms-marco-MiniLM-L-6-v2`, `google/flan-t5-small` (77 M parameters class, T5-small family); fallbacks: TF-IDF (384 features) for embeddings, hybrid order without rerank, evidence-based template answer.
- Config: candidate pool 15, top-k 5, weights (0.65, 0.35), query max 2000 chars (min 3), token life 1440 min.
- Relevance display: `relevance = (rerank - min)/(max - min)` over the 15 candidates, so the **top record is always 1.00**; labels Strong >= 0.66, Moderate >= 0.33, Weak.
- Safety: 10 emergency regex rules, 6 caution keywords (`chest pain, breathing, bleeding, pregnant, infant, newborn`), permanent disclaimer, answer filter with 5 banned phrases (case-sensitive replace).
- Code size (non-blank lines): backend app 800 (24 files), legacy templates/static 159, React frontend 2,820 JS/JSX + 580 CSS, scripts 453, tests 60.

## 3. Endpoints

- `GET /api/health` - auth: no
- `POST /api/auth/register` - auth: no
- `POST /api/auth/login` - auth: no
- `POST /api/auth/logout` - auth: no
- `GET /api/auth/me` - auth: cookie
- `POST /api/chat` - auth: yes
- `GET /api/history?search=` - auth: yes
- `GET /api/history/{id}` - auth: yes
- `DELETE /api/history/{id}` - auth: yes
- `GET /api/about/metrics` - auth: no (reads results/metrics.json + KB size)

Tables: `users(id, email unique, password_hash, created_at)`; `consultations(id, user_id FK, symptom_query, generated_response, top_condition, retrieved_evidence JSON text, retrieval_score, safety_flag, created_at)`; one user has many consultations (cascade delete).

## 4. Knowledge base and data

- 176 records, 30 conditions (Allergic Rhinitis 6, Anaphylaxis 6, Anemia 6, Anxiety 6, Appendicitis 6, Asthma 6, Bronchitis 6, COVID-19 6, Chickenpox 5, Common Cold 6, Conjunctivitis 6, Dengue 6, Depression 6, Diabetes 6, Ear Infection 6, Eczema 6, Food Poisoning 6, Gastritis 6, Gastroenteritis 6, Heart Attack 6, Hypertension 5, Influenza 6, Malaria 6, Measles 6, Migraine 6, Pneumonia 6, Sinusitis 6, Stroke 6, Typhoid 4, Urinary Tract Infection 6); severity: {'low': 36, 'moderate': 88, 'high': 28, 'emergency': 24}; 3.98 symptoms per record (range 3-5); symptom vocabulary 97; **30 distinct description/guidance pairs** (one per condition, shared by all of its records).
- Source: `scripts/prepare_data.py` builds records from a hand-written table of 30 conditions with 6 random symptom-subset variants each (seed 42, de-duplicated). `source_type = synthetic` ('CareLens AI curated local knowledge (synthetic fallback)'). **No public dataset, no clinical validation, no licence issue (written by the team).**
- The shipped `results/metrics.json` (served on the About page): n=30, Top-1 = Top-3 = F1 = MRR = 1.0, mean latency 245 ms. It evaluates held-out records that are **still in the index** with the query = the record's own symptom list, so it is an upper bound for wiring, not an accuracy claim (the About page says so).

## 5. Retrieval results (top-1 condition accuracy; Wilson 95% CI for the shipped configuration)

### S1 shipped protocol (30; held-out record still indexed)

| Configuration | Top-1 | Top-3 | Top-5 | MRR@5 | distinct conditions in top 5 |
|---|---|---|---|---|---|
| BM25 only (lexical) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.2 |
| Dense only (MiniLM + FAISS) | 0.9000 | 0.9000 | 0.9333 | 0.9083 | 1.233 |
| Hybrid fusion (0.65/0.35) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.267 |
| Hybrid + cross-encoder (shipped) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.3 |
| Shipped, without HyDE expansion | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.167 |
| Dense TF-IDF fallback | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.2 |
| Hybrid with TF-IDF fallback (offline mode) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.2 |

Shipped configuration Top-1 95% CI: 88.6-100.0%; misses: 0.

### S1 leave-one-out (30)

| Configuration | Top-1 | Top-3 | Top-5 | MRR@5 | distinct conditions in top 5 |
|---|---|---|---|---|---|
| BM25 only (lexical) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.3 |
| Dense only (MiniLM + FAISS) | 0.8667 | 0.8667 | 0.8667 | 0.8667 | 1.3 |
| Hybrid fusion (0.65/0.35) | 0.9667 | 0.9667 | 0.9667 | 0.9667 | 1.4 |
| Hybrid + cross-encoder (shipped) | 0.9667 | 0.9667 | 0.9667 | 0.9667 | 1.4 |
| Shipped, without HyDE expansion | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.3 |
| Dense TF-IDF fallback | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.333 |
| Hybrid with TF-IDF fallback (offline mode) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.333 |

Shipped configuration Top-1 95% CI: 83.3-99.4%; misses: 1.

### S2 verbatim, leave-one-out (176)

| Configuration | Top-1 | Top-3 | Top-5 | MRR@5 | distinct conditions in top 5 |
|---|---|---|---|---|---|
| BM25 only (lexical) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.256 |
| Dense only (MiniLM + FAISS) | 0.8636 | 0.8750 | 0.8864 | 0.8709 | 1.341 |
| Hybrid fusion (0.65/0.35) | 0.9659 | 0.9659 | 0.9716 | 0.9673 | 1.307 |
| Hybrid + cross-encoder (shipped) | 0.9716 | 0.9716 | 0.9716 | 0.9716 | 1.335 |
| Shipped, without HyDE expansion | 0.9943 | 0.9943 | 0.9943 | 0.9943 | 1.29 |
| Dense TF-IDF fallback | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.295 |
| Hybrid with TF-IDF fallback (offline mode) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.273 |

Shipped configuration Top-1 95% CI: 93.5-98.8%; misses: 5.

### S3 two random symptoms, leave-one-out (176)

| Configuration | Top-1 | Top-3 | Top-5 | MRR@5 | distinct conditions in top 5 |
|---|---|---|---|---|---|
| BM25 only (lexical) | 0.8977 | 0.9148 | 0.9659 | 0.9157 | 1.523 |
| Dense only (MiniLM + FAISS) | 0.7045 | 0.7500 | 0.7898 | 0.7322 | 1.517 |
| Hybrid fusion (0.65/0.35) | 0.8580 | 0.8693 | 0.9148 | 0.8726 | 1.602 |
| Hybrid + cross-encoder (shipped) | 0.8807 | 0.8807 | 0.9205 | 0.8903 | 1.483 |
| Shipped, without HyDE expansion | 0.8977 | 0.9261 | 0.9318 | 0.9096 | 1.489 |
| Dense TF-IDF fallback | 0.8920 | 0.9148 | 0.9261 | 0.9062 | 1.625 |
| Hybrid with TF-IDF fallback (offline mode) | 0.9034 | 0.9318 | 0.9545 | 0.9205 | 1.648 |

Shipped configuration Top-1 95% CI: 82.5-92.1%; misses: 21.

### S4 lay-language probes (60)

| Configuration | Top-1 | Top-3 | Top-5 | MRR@5 | distinct conditions in top 5 |
|---|---|---|---|---|---|
| BM25 only (lexical) | 0.8833 | 0.8833 | 0.8833 | 0.8833 | 1.2 |
| Dense only (MiniLM + FAISS) | 0.9000 | 0.9333 | 0.9500 | 0.9172 | 1.233 |
| Hybrid fusion (0.65/0.35) | 0.9000 | 0.9167 | 0.9167 | 0.9083 | 1.25 |
| Hybrid + cross-encoder (shipped) | 0.9667 | 0.9833 | 0.9833 | 0.9722 | 1.2 |
| Shipped, without HyDE expansion | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.133 |
| Dense TF-IDF fallback | 0.7667 | 0.7833 | 0.8167 | 0.7789 | 1.283 |
| Hybrid with TF-IDF fallback (offline mode) | 0.8167 | 0.8167 | 0.8500 | 0.8233 | 1.233 |

Shipped configuration Top-1 95% CI: 88.6-99.1%; misses: 2.

Per-query timing is not in these tables because embeddings are cached across query sets in the measurement script; use section 9 for latency.

Notes: 'Top-3' counts the first three retrieved *records*; because a condition has 4-6 near-identical records, the five evidence cards usually show one or two conditions (mean distinct conditions in top 5: 1.2 on S4), so the 'possible conditions' list is not a differential diagnosis. S4 queries were written by the authors in everyday language (2 per condition); they are not clinician-validated. Leave-one-out removes only the held-out record; its sibling records remain.

Misses of the shipped configuration on S4: 'My nose will not stop running and I have a slight cough, nothing serious' (Common Cold -> Allergic Rhinitis); 'A slow-rising fever for days, feeling weak, no appetite, abdominal pain' (Typhoid -> Appendicitis).

## 6. Displayed relevance versus what the model knows

- 60 in-KB lay queries and 15 out-of-KB complaints (tooth ache, sprained ankle, back pain ...): the top record has displayed relevance 1.00 in **all** of them; all 15 out-of-KB queries are shown as 'Strong match' (also via `pipeline.answer`: {'Strong match': 15}).
- The raw cross-encoder score does separate them: in-KB mean 2.481 (min -4.52, max 6.494) vs out-of-KB mean -6.336 (min -9.116, max -4.766); AUROC in-KB vs out-of-KB = 1.0 (raw rerank) and 0.9322 (raw hybrid). The information exists but the min-max normalisation hides it.

## 7. Generation

- Installed transformers 5.20.2: task `text2text-generation` is **unavailable: KeyError** (removed from transformers 5), so `Generator` falls back to `text-generation`, which for T5 returns the prompt unchanged: **30/30 answers (100%) are an echo of the prompt** (instruction + retrieved context), labelled `local-generator:google/flan-t5-small`. Mean generation time 808.1 ms.
- Evidence-based fallback (offline mode, `CARELENS_GENERATOR_MODEL` unavailable): deterministic text built from the retrieved records, 0.031 ms; in 30/30 answers every named condition is one of the retrieved records (by construction).
- Consequence: groundedness holds structurally (nothing is generated beyond the retrieved text) but answers are not synthesised, do not cite per statement, and there is no human or model groundedness judgement.

## 8. Safety layer (author-written probes, not clinical validation)

- Emergency flag on 40 emergency descriptions: 27 detected, recall 0.675 (Wilson [0.5202, 0.7992]); literal wording 27/28, **paraphrased wording 0/12** (none flagged, not even as caution).
- On 30 non-emergency texts: 20 ordinary -> 0 false alarms; 10 hard negatives (negation or history) -> 6 false emergencies, 4 caution flags (precision 0.8182).
- Answer filter: 6/14 test sentences cleaned; for the 5 listed phrases 6/10 cases (case-sensitive replace misses 'Take ibuprofen', 'Dosage:', 'Prescribe'); unlisted drugs (paracetamol, amoxicillin) pass through.

## 9. Latency (CPU only, i5-12500, 15.7 GB, warm models, 30 queries)

| Stage | mean ms | median | p95 |
|---|---|---|---|
| expand | 0.03 | 0.03 | 0.05 |
| embed | 92.96 | 56.21 | 269.18 |
| faiss | 0.19 | 0.13 | 0.46 |
| bm25 | 2.46 | 2.13 | 4.19 |
| fuse | 0.07 | 0.06 | 0.11 |
| rerank | 554.66 | 542.57 | 841.96 |
| safety | 0.04 | 0.04 | 0.08 |

- `pipeline.answer` in-process: with local generator mean 978.97 ms (p95 1376.4); fallback only mean 483.87 ms (p95 697.31). The cross-encoder (15 query-record pairs, mean 554.66 ms when timed alone) is the dominant stage; the stages were timed in separate passes, so they do not add up exactly to the totals.
- `POST /api/chat` over HTTP on 127.0.0.1, fallback generator: mean 403.1 ms, median 396.8, p95 569.3, first request 339.6 ms; login ~249.1 ms (bcrypt); history list ~32.4 ms; health ~8.4 ms.
- `POST /api/chat` over HTTP on 127.0.0.1, Flan-T5 generator: mean 765.8 ms, median 736.8, p95 1077.3, first request 580.2 ms; login ~284.3 ms (bcrypt); history list ~95.3 ms; health ~13.8 ms.
- Model load at first request ~62 s (cold start in the measurement script; embedding + reranker + generator).

## 10. Tests

- pytest: 9/9 passed in 34.09 s (normalise/expand, safety emergency, safety filter, password hashing, fuse, generator fallback, auth + history isolation, API validation, retrieval round trip).
- `scripts/smoke_test.py` (end-to-end via the Vite proxy): 22/22 checks passed.
- `scripts/measure_security.py` (in-process TestClient, scratch DB): 35/38 black-box probes passed; failed: A5, A11, T6 (no Secure cookie flag, no sign-in rate limit, default JWT signing key in use). Details in `docs/metrics/security.json`.
- Not done: load/concurrency test, browser accessibility audit, user study, clinical review, security penetration test.

## 11. Screenshot inventory (`docs/screenshots/`, 1440x900 unless noted, captured by `scripts/capture_docs_screens.py` on 2026-10-22 with the real running app)

- `01_landing_light.png`
- `02_landing_dark.png`
- `03_landing_bottom_dark.png`
- `04_register.png`
- `05_login.png`
- `06_assistant_empty.png`
- `07_assistant_answer.png`
- `08_assistant_emergency.png`
- `09_history.png`
- `10_history_search.png`
- `11_consultation_detail.png`
- `12_delete_confirm.png`
- `13_about_metrics.png`
- `14_about_dark.png`
- `15_mobile_assistant.png`
- `16_mobile_history.png`
- `17_not_found.png`
- `18_assistant_lay_query.png`
- `19_assistant_caution.png`
- `20_assistant_evidence.png`
- `21_assistant_generator_echo.png`

Screens 07, 08, 18, 19, 20 and the history/detail screens were captured with the evidence-based fallback generator (backend started with an unavailable generator model; the supported offline mode). `21_assistant_generator_echo.png` was captured with the default Flan-T5 generator and shows the prompt echo (defect). The About page shows the shipped 100% figures with the app's own synthetic-data caveat.

## 12. Objectives (6.OBJECTIVES&PROBLEM STATEMENT.docx) versus outcome

1. Curated knowledge base indexed for retrieval - **achieved with a synthetic 176-record, 30-condition base** (FAISS flat index + BM25 index); not clinically curated.
2. NL symptoms with query expansion - **achieved**; expansion is a rule-based template (not an LLM HyDE) and measured effect is neutral-to-negative (no-HyDE variant scores as high or higher).
3. Hybrid retrieval with neural reranking - **achieved and measured** (hybrid + cross-encoder top-1 0.967 on S4, 0.881 on S3).
4. Grounded responses citing the retrieved source for every statement - **partly**: answers are built from retrieved records and each is shown with evidence cards (record id, symptoms, guidance), but there is no per-statement citation and the local generator path echoes its prompt.
5. Track reported symptoms over time to reveal progression and trends - **not achieved beyond storage**: consultations are saved, searchable, viewable and deletable; there is no trend, timeline or progression analysis.
6. Evaluate retrieval relevance, groundedness and response time - **retrieval and time measured; groundedness only checked structurally** (no judge).

## 13. Defects found while measuring (documented, not fixed)

1. Local generator returns its own prompt (transformers 5 removed `text2text-generation`).
2. Displayed relevance is relative: top record always 100%, out-of-KB complaints still 'Strong match'.
3. Safety rules miss paraphrased emergencies (0/12) and fire on negations/history (6/10 hard negatives); answer filter replace is case-sensitive.
4. Shipped `results/metrics.json` evaluates records that are in the index (100% is an upper bound).
5. Evidence cards show near-duplicate records of the same condition, not a differential.
6. Symptom-trend tracking is not implemented.
7. `tests/test_auth_and_history_isolation` writes users into the real `data/carelens.db` (the file is git-ignored).
