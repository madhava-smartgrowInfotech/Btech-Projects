# LabLens - REPORT FACTS (single source of truth for all documents)

Batch CSE-A-A8 | AI-POWERED MEDICAL LAB REPORT ANALYSIS & HEALTH INSIGHTS PLATFORM | product name **LabLens**
Team: BANOTH SWAPNA (23K91A0528), BEKKAM VARSHITHA (23K91A0535), A NAVADEEP REDDY (23K91A0502), BUDIGAM MANOJ (23K91A0546). Guide: L.G REDDY.
Institution (from `Documentary/Batch_08...docx`): TKR College of Engineering & Technology (Autonomous), Department of CSE. College city, HOD, principal, academic year: unknown -> placeholders.

## 1. What the product really is (vs. the abstract)

The abstract (`2.ABSTRACT.docx`) proposes PP-OCR, CRF NER, RAG, Supabase, Tailwind, serverless Google Cloud Functions, <10 s/report.
**What was built** (read from the code, authoritative):

| Abstract says | Implemented | Honest status |
|---|---|---|
| PP-OCR text extraction | PyMuPDF text layer for digital PDFs; scanned pages/images -> OpenCV preprocessing (grayscale, fastNlMeansDenoising h=10, Gaussian adaptive threshold blockSize 31 C 15, minAreaRect deskew) -> Tesseract `--psm 6` via pytesseract at 300 dpi | PP-OCR not used. Tesseract path **could not be measured** (Tesseract binary is not installed on the test machine) |
| CRF-based NER | Regex line parser (name/value/unit/range) + TF-IDF char n-gram (2-4, `char_wb`) cosine matcher snapping noisy names to a 55-name dictionary (threshold 0.55); spaCy optional for patient name only (not installed here) | No CRF, no trained model, no learned weights |
| RAG explanations from trusted sources | Rule-based knowledge base `TEST_KNOWLEDGE` (17 tests, "measures / low / high" texts) + generic fallback; optional LLM rewrite (Anthropic API `claude-sonnet-4-6`, 300 max tokens) only if `ANTHROPIC_API_KEY` set, silent fallback | No retrieval, no vector store, no citations. LLM rewrite not exercised (no key) |
| Supabase (Postgres, RLS) | SQLite via SQLAlchemy 2.0 (`data/medical_lab.db`), 3 tables | Not Supabase, no row-level security, single shared library |
| React + Tailwind + Recharts | React 18.3.1 + Vite 5.4 + Recharts 2.15 + react-router 6, hand-written CSS "Depth Studio" kit V3, framer-motion/GSAP/Lenis/three.js landing visual; Streamlit app (`app.py`, 523 lines) also kept | Tailwind not used |
| Serverless Cloud Functions | FastAPI 0.143 + uvicorn on port 8308, Vite dev server 5308; local run via `run.bat` | Not serverless, not deployed to cloud |
| <10 s per report | measured 54 ms (14-row text PDF, pipeline + DB), 210 ms through the HTTP upload | met for text-layer PDFs; scanned images unmeasured |
| Low-quality scans tolerated | preprocessing code exists | **not measured** |
| Trend tracking, comparison, dashboards, alerts | implemented and tested | met |
| Auth | added for the new UI: single demo account (HMAC-signed 12 h token), `demo@lablens.com` / `Demo@1234`; the original product had no login | demo-grade only |

Base paper: **batch file `3.BASE PAPER.docx` names** "RAG-Based Blood Test Report Analysis to Reverse Metabolic Syndrome", Karhade, Verma, Gadaokar, Mahajan, *Communications on Applied Nonlinear Analysis* 32(10s), 2025, pp. 2771-2779, DOI 10.52783/cana.v32.5718 (PDF in `Documentary/`). `archived_base_papers/` holds two other papers: Checkup2Action (arXiv 2605.11533, 2026) and "Analysis of Blood Report Images Using General-Purpose VLMs" (Bakhsheshi & Beigy, arXiv 2509.06033, 2025). The documents use the batch-file paper as THE base paper and cite the other two as related work.

### Base paper facts (read from the PDF)
- LLaMA-3 8B + RAG; ChromaDB; LangChain `RecursiveCharacterTextSplitter` chunk 1024, overlap 100; top-k = 3 with similarity threshold; knowledge base 20 medical books + 383 YouTube transcripts (Whisper) + a 33-parameter document; PyMuPDF for PDF text; account login and encrypted report storage.
- Scope: Metabolic Syndrome only, 33 parameters (CBC, glucose/insulin, lipids, apolipoproteins, LFT, KFT, thyroid, vitamins, homocysteine, inflammation).
- Evaluation: 20 responses scored 1-100 by GPT-4 (human monitoring) on Correctness/Clarity/Helpfulness/Completeness. Conclusion states averages 92.4 / 89.7 / 91.1 / 88.9. **Averages recomputed from its Table 4: 94.0 / 94.9 / 90.1 / 88.65** (the stated and tabulated numbers disagree). No extraction accuracy, no latency, no trend tracking; future scope lists multilingual, personalisation over time, speech.
- Its Table 2 gives haemoglobin unit as mg/dL (g/dL is the clinical unit) - a typo-level inconsistency.

## 2. Architecture summary
Flow: upload (PDF/JPG/JPEG/PNG, <=15 MB) -> `ocr_processor.extract_text` (validate; PDF text layer per page, page with <30 chars -> render 300 dpi -> OpenCV preprocessing -> Tesseract) -> `ner_processor.extract_structured_tests` (line filter, name/value/unit regex, 2-sided `a-b | a to b | a–b` and 1-sided `<x | >x` range, trailing unit, test date, confidence 0.9/0.6 minus 0.1 if no unit, drop rows with neither range nor unit, de-duplicate by (name,value,unit)) -> `result_analyzer.classify_result` (LOW/NORMAL/HIGH/UNKNOWN) -> `database.save_test_results` -> `ai_insights.generate_insight` for LOW/HIGH -> status Completed. Failures at any stage mark the report Failed with an error message and keep partial raw text.
Modules (Python, root of 8.ProjectCode): `ocr_processor.py` 225 lines, `ner_processor.py` 289, `result_analyzer.py` 100, `ai_insights.py` 270, `report_processor.py` 148, `database.py` 251, `models.py` 97, `app.py` (Streamlit) 523, `backend/main.py` 352, `backend/demo_data.py` 98. Frontend: ~3,900 lines JS/JSX in 11 pages + kit. Scripts: `smoke_test.py`, `ui_check.py`, `capture_screens.py`, `run_experiments.py`, `measure_api.py`; tests `tests/test_lablens.py`.

Database (SQLite, SQLAlchemy ORM):
- `reports`(id PK, file_name, file_type, upload_date, processing_status [Pending/Processing/Completed/Failed], error_message, raw_text)
- `test_results`(id PK, report_id FK->reports, test_name, result_value, unit, reference_low, reference_high, status, test_date, confidence_score) cascade delete
- `health_insights`(id PK, test_result_id FK->test_results, explanation, possible_causes, recommendations, created_at) cascade delete
- Dashboard "critical" heuristic: LOW with value < 0.5 x reference_low, or HIGH with value > 1.5 x reference_high.

Endpoints (FastAPI, all but 3 need Bearer token): `GET /api/health`, `GET /api/config`, `POST /api/auth/login`, `GET /api/auth/me`, `GET /api/dashboard`, `GET /api/reports`, `POST /api/reports` (multipart file + use_llm), `GET /api/reports/{id}`, `DELETE /api/reports/{id}`, `GET /api/tests`, `GET /api/trends?test=`, `GET /api/compare?a=&b=`, `GET /api/insights`, `POST /api/demo/seed` (only into empty library, 5 synthetic PDFs). Trend "direction" = last value vs first value only.
UI pages: Landing, Login, Dashboard, Upload report, Report analysis, My reports, Health trends, Compare reports, Health insights, About, 404.
Security facts: HMAC-SHA256 token (12 h), `hmac.compare_digest`, CORS limited to localhost:5308, 15 MB limit, extension whitelist; no per-user data separation, no HTTPS, JWT secret default `change-me-on-first-run` unless set in `.env`.

## 3. Data
No dataset ships with the product and no real lab report was available. There is **no manually labelled corpus**. Two synthetic sources only:
1. Demo reports (`backend/demo_data.py`): 5 PDFs, 14 tests each, invented patient/values, April-October 2026 (used for all screenshots).
2. Evaluation corpus (`scripts/run_experiments.py`, seed 42): **120 generated PDF reports** = 8 layouts x 15; each has 12 dictionary tests (from 40) + 2 tests outside the dictionary (from 8), header decoys and a "Sample Collected" date line -> **1,680 ground-truth rows**. Values drawn ~55% in range / 25% low / 20% high. Ground-truth status uses the same rule as the code (so status accuracy measures propagation, not clinical truth). Licence: own generated data. Layouts: plain, paren, flag, colon, unit_last, mixed_sep, tabular (each cell a separate text object), ocr_noise (10% per-character noise on names, *simulated*, text-layer PDF).

## 4. Measured results (`experiments/lablens/metrics.json`, `api_latency.json`)
Machine: Intel Core i5-12500 (6 cores/12 threads), 15.7 GB RAM, Windows 11, Python 3.11.9, scikit-learn 1.5.0, PyMuPDF 1.28.2, OpenCV 4.11.0, SQLAlchemy 2.0.30, FastAPI 0.143.3, Node 24, no GPU.

**A. Field extraction, all 120 reports (text-layer PDFs)**
| Metric | Value |
|---|---|
| GT rows / predicted rows | 1,680 / 1,525 |
| Row precision / recall / F1 | 0.9626 / 0.8738 / 0.9161 |
| Name accuracy (detected rows) | 0.9564 (dictionary tests 0.9873; unseen tests 0.7714) |
| Unit accuracy | 0.8713 |
| Range accuracy | 0.9986 |
| Status accuracy | 0.9993 |
| Exact-row rate (name+unit+range+status all right, over all GT rows) | 0.7292 |
| False-positive rows | 57 = 55 "Sample Collected: 12-04-2026" date-line rows (test "Sample Collected", value 12, range -4 to 2026) + 2 others (paren_03: the date line value 12 equalled a real RDW value of 12, so the date row was matched to RDW and the genuine RDW row counted as extra; ocr_noise_03: a mis-read name row). The date line was read as a row in all 56 reports that carry a dd-mm-yyyy date |

Per layout (precision / recall / unit acc / exact-row): plain 0.968/1.000/0.938/0.929; paren 0.968/1.000/0.881/0.867; flag 0.968/1.000/**0.576**/0.562; colon 0.968/1.000/0.910/0.886; unit_last 0.968/1.000/0.943/0.914; mixed_sep 0.968/1.000/0.933/0.910; **tabular 0.000/0.000** (all 210 rows missed: cells arrive one per line); ocr_noise 0.963/0.991/0.918/0.767 (name acc 0.822).
Failure kinds: missed row 212 (210 tabular + 2), unit errors 179 (units outside the regex list: uIU/mL, mg/L, umol/L, ng/dL, ug/dL, pg/mL for some; a flag letter `L`/`H` between value and unit hides the unit), name errors 54 (mostly "Sodium Bicarbonate" -> "Sodium"), false positives 57.
Unit regex gaps found: `mg/L`, `umol/L`, `µmol/L`, `ng/dL`, `uIU/mL`, `µIU/mL`, `g/L`, `mmHg`, `mL/min` are not recognised.

**B. Test-name normalisation** (55 dictionary names, 30 trials each)
| Per-char noise | TF-IDF 0.55 (shipped) | difflib ratio 0.60 | exact |
|---|---|---|---|
| 0% | 1.000 | 1.000 | 1.000 |
| 5% | 0.961 | 0.994 | 0.686 |
| 10% | 0.890 | 0.981 | 0.493 |
| 20% | 0.731 | 0.946 | 0.237 |
Threshold sweep (TF-IDF): at 0.55 -> acc@10% 0.890, acc@20% 0.718, false-snap rate on 24 unseen names 0.167, synonym accuracy 0.526 (10/19). At 0.30 -> 0.965 / 0.907 / 0.542 / 0.737. At 0.80 -> 0.698 / 0.398 / 0.000 / 0.474. Synonyms handled: Haemoglobin, Platelets, SGPT (ALT), Serum Creatinine, Cholesterol Total, Triglyceride, Urea Nitrogen, Vitamin B-12, Total Bilirubin, Serum Sodium. Not handled: Hb, Hgb, Blood Sugar Fasting, Total Leucocyte Count, TLC, LDL, HDL, Red Blood Cell Count; wrong: Glycosylated Hemoglobin -> Hemoglobin. Unseen names wrongly snapped: Sodium Bicarbonate->Sodium, Lipoprotein (a)->Total Protein, Apolipoprotein B->Total Protein, Insulin Fasting->Fasting Glucose. (Dictionary size is 55 names, not "~50".) The sweep shows the shipped 0.55 is a middle compromise; a difflib matcher is more noise-tolerant (+9 points at 10% noise) - this baseline was not adopted.

**C. Classification**: 20,000 random cases vs an independently written rule: 0 disagreements; boundaries inclusive (5 and 10 in 5-10 -> NORMAL; 4.99 LOW; 10.01 HIGH).

**D. Insight coverage**: knowledge base has 17 entries = 17/55 (30.9%) of the dictionary tests; in the corpus 202 of 565 abnormal dictionary rows (35.8%) got test-specific text, the rest the generic "non-specific causes" text. Sodium, Potassium, Calcium, ALT/AST etc. have no specific text.

**E. Latency** (14-row, 1-page text PDF, 4,356 bytes; medians from metrics.json): PDF text layer 1.37 ms, field extraction 7.16 ms (14 rows), classification 0.02 ms, insight generation for all abnormal rows 0.01 ms, **end-to-end `process_uploaded_report` incl. SQLite 52.7 ms (mean 53.7, p95 61.0, max 85.4, n=40)**. Field extraction scales linearly with rows (medians): 14 rows 7.9 ms, 50 rows 29.3 ms, 100 rows 58.1 ms, 200 rows 113.0 ms (about 0.57 ms per row; the TF-IDF `transform` per row dominates).
API on 127.0.0.1 (medians, ms): health 0.9; login 1.0; dashboard 4.7; reports 2.9; report detail 7.2; trends 2.1; compare 4.4; insights 16.4; **PDF upload 209.8 (p95 414.2, n=30)**; seeding five reports 1.05 s.
Not measured: scanned-image OCR latency and accuracy (no Tesseract), LLM insight latency (no key), multi-user load, large database.

**F. Tests**: `python -m pytest tests -q` -> **36 passed** (classification boundaries, extraction, name normalisation, OCR validation, insights, pipeline, DB cascade, dashboard stats, API auth/upload/trend/compare/insights/seed). `scripts/smoke_test.py` -> 24 API checks + 7 browser checks, all passed ("All smoke checks passed"). `scripts/ui_check.py` exists (360/768/1440 px, light/dark, drawer, keyboard, reduced motion) - not re-run in this documentation pass.

## 5. Objectives vs outcomes
1. Accept PDF/scan and extract text with high-speed OCR - **partly**: PDF text layer 1.5 ms; image OCR via Tesseract implemented, untested here; not PP-OCR.
2. NER of parameters/values/units/ranges - **partly**: regex+TF-IDF (not CRF/NER model): row F1 0.916 on synthetic corpus, 0.984 on single-line layouts, 0 on cell-per-line tables.
3. Compare to reference range and flag - **met**: status accuracy 0.9993, rule verified on 20,000 cases.
4. Plain-language explanations grounded in trusted sources - **partly**: rule-based, curated text, 31% of dictionary tests; no retrieval/citations; optional LLM not tested.
5. Track parameters across reports - **met** (trend chart, first-vs-last direction, compare two reports); limitation: x-axis is upload date, not test date.
6. Dashboard and evaluate extraction accuracy against manually labelled reports - dashboard **met**; evaluation done on **generated** labelled reports, not manual real ones -> **gap**.

## 6. Screenshot inventory (`docs/screenshots`, all captured from the running app with the 5 demo reports + 1 uploaded sample)
01_landing_dark (1440x900), 02_landing_light, 03_login, 04_dashboard (6 reports, 82 tests, 54 normal, 28 abnormal, 2 critical), 05_upload_empty, 06_upload_done (1440x1846), 07_report_analysis (1440x3577; Health_Checkup_Aug2026: 14 tests, 5 normal, 9 abnormal), 08_my_reports, 09_health_trends (Hemoglobin 10.8 -> 13.1 g/dL), 10_compare_reports, 11_health_insights (1440x6714), 12_about, 13_dashboard_empty_state. The data is synthetic (stated on the pages).

## 7. Known issues found while documenting
- Date lines like `12-04-2026` parse as a test row (range -4 to 2026) - misread as a row in all 56 dd-mm-yyyy reports of the corpus (55 false-positive rows; in one report it displaced a real RDW row).
- Cell-per-line table PDFs produce zero rows (report then marked Failed with "no recognizable lab test rows").
- Unit list incomplete; a flag letter between value and unit drops the unit.
- Sodium Bicarbonate snaps to Sodium; unseen names can silently be renamed.
- `README`/abstract claims (CRF, PP-OCR, RAG, Supabase) do not match the code.
- Trend direction uses only first and last point; trend x-axis is upload time.
- Demo auth only; secret default; no per-user isolation.
- Verified by running the 15 cell-per-line ("tabular") reports through `process_uploaded_report` into a scratch database: 8 end as Failed ("Text was extracted, but no recognizable lab test rows were found...") and 7 end as Completed with exactly one nonsense row (`Sample Collected`, 12, NORMAL) taken from the dd-mm-yyyy date line - a silent wrong success, which is worse than the failure.
