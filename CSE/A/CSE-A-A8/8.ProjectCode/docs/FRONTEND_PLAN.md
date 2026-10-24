# Frontend plan - LabLens (CSE-A-A8)

Kit: **V3 Depth Studio** (`D:\abstracts\Frontend_Kits\V3`, copied into `frontend/src`).
Ports: backend **8308**, frontend **5308** (from `.env`).

## 1. What exists today

The product is a single **Streamlit** app (`app.py`) over plain Python modules in the project root. It has
**no HTTP API and no login**. The Streamlit app stays untouched and runnable (`streamlit run app.py`).

| Module | Role |
|---|---|
| `database.py` / `models.py` | SQLite (`data/medical_lab.db`) via SQLAlchemy: `Report`, `TestResult`, `HealthInsight` |
| `report_processor.py` | `process_uploaded_report(filename, bytes, use_llm_insights)` - whole pipeline |
| `ocr_processor.py` | PyMuPDF text layer, OpenCV + Tesseract OCR fallback, `SUPPORTED_EXTENSIONS`, 15 MB limit |
| `ner_processor.py` | regex + TF-IDF test-name normalisation, date / patient name |
| `result_analyzer.py` | LOW / NORMAL / HIGH / UNKNOWN classification |
| `ai_insights.py` | rule-based insight (+ optional Anthropic rewrite), `MEDICAL_DISCLAIMER` |

### Existing Streamlit screens (9) -> every one must exist in the new UI

| # | Streamlit page | Data used |
|---|---|---|
| 1 | Home (hero, 4 features, 5 steps, 3 benefits, disclaimer, "Get Started") | static copy, disclaimer |
| 2 | Dashboard (5 metrics, recent 10 reports, critical-alert banner) | `get_dashboard_stats`, `get_all_reports` |
| 3 | Upload Report (PDF/JPG/JPEG/PNG, size, progress stages, raw text preview, classified table, error) | `process_uploaded_report` |
| 4 | Report Analysis (pick report, all results, abnormal results, per-test AI insight, disclaimer) | `get_report_by_id`, `get_results_for_report`, `get_insight_for_test_result` |
| 5 | My Reports (history, type/status/error, per-report results, delete) | `get_all_reports`, `delete_report` |
| 6 | Health Trends (pick test, line chart + reference low/high, direction, table) | `get_distinct_test_names`, `get_results_by_test_name` |
| 7 | Compare Reports (2 completed reports, common tests, change, grouped bar chart) | `get_results_for_report` x2 |
| 8 | Health Insights (all abnormal results across reports with insight) | `get_all_test_results`, `get_insight_for_test_result` |
| 9 | About (purpose, tech stack, limitations, disclaimer) | static |
| - | Sidebar: "Use LLM for richer explanations" toggle | `ANTHROPIC_API_KEY` present? |

## 2. Backend endpoints (new thin FastAPI layer in `backend/main.py`, calls existing functions only)

No existing logic or contract is changed (there was no API). All routes are read wrappers except upload/delete.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/health` | - | `{status}` |
| GET | `/api/config` | - | `{disclaimer, supported_extensions, max_size_mb, llm_available}` |
| GET | `/api/dashboard` | - | `{stats{total_reports,total_tests,normal,abnormal,critical}, recent[ReportSummary]}` |
| GET | `/api/reports` | - | `[ReportSummary{id,file_name,file_type,upload_date,processing_status,error_message,test_count,abnormal_count}]` |
| POST | `/api/reports` | multipart `file`, form `use_llm` | `{status, report_id, stages_completed, error, raw_text, results[...]}` |
| GET | `/api/reports/{id}` | - | `{report, results[{..., reference_range, insight?}], raw_text}` |
| DELETE | `/api/reports/{id}` | - | `{deleted: id}` |
| GET | `/api/tests` | - | `[test_name]` |
| GET | `/api/trends?test=NAME` | query | `{test, points[{report_id,date,value,reference_low,reference_high,status}], direction}` |
| GET | `/api/compare?a=ID&b=ID` | query | `{report_a, report_b, rows[{test,a,b,unit,change}]}` |
| GET | `/api/insights` | - | `[{test_result_id, report_id, test_name, value, unit, status, insight{explanation,possible_causes,recommendations}}]` |

Additive read-only endpoints (`dashboard` recent list with counts, `trends`, `compare`, `insights`, `config`) exist because
Streamlit computed them inline in `app.py`; the maths is copied verbatim (direction rule, change = b - a, critical heuristic
stays in `database.get_dashboard_stats`).

## 3. Screen map (React, Vite, JavaScript)

| Route | Screen | Replaces |
|---|---|---|
| `/` | Landing - three.js hero, scroll story: features, how it works, benefits, disclaimer, CTA | Home |
| `/app` | Dashboard | Dashboard |
| `/app/upload` | Upload (FileDrop, stage stepper, preview, results table) + LLM toggle | Upload Report |
| `/app/reports/:id` (+ `/app/analysis`) | Report Analysis with report picker, all/abnormal tabs, insight cards | Report Analysis |
| `/app/reports` | My Reports (table/cards, expand row results, delete with confirm) | My Reports |
| `/app/trends` | Health Trends (test select, chart with reference band, direction, table) | Health Trends |
| `/app/compare` | Compare Reports (two selects, table, grouped bars) | Compare Reports |
| `/app/insights` | Health Insights (abnormal list across reports) | Health Insights |
| `/app/about` | About (stack, limitations, disclaimer) | About |

Shell: kit `AppShell` (drawer sidebar < 900px), theme toggle (persisted), disclaimer footer. No login (the product has none).
Every screen: skeleton -> empty state with action -> error state with retry -> success toast.

## 4. Feature checklist (tick during Step 4)

- [x] Landing: features, how-it-works, benefits, disclaimer, Get Started
- [x] Dashboard: 5 metrics, recent reports, critical banner
- [x] Upload: PDF/JPG/JPEG/PNG, size shown, stages, raw text preview, classified table, failure message
- [x] LLM toggle (disabled with explanation when no key)
- [x] Report Analysis: picker, all results, abnormal results, insight per test, disclaimer
- [x] My Reports: history, status/error, results, delete
- [x] Health Trends: test picker, line + reference lines, direction, table
- [x] Compare Reports: two reports, common tests, change, bar chart, same-report warning, "need two" state
- [x] Health Insights: all abnormal across reports
- [x] About: stack, limitations, disclaimer
- [x] Dark mode toggle persisted; reduced motion; 360 / 768 / 1440; keyboard
- [x] `npm run build`, smoke test, console clean, screenshots in `docs/screenshots/`

## 5. Environment findings

- Python 3.11, Node 24; FastAPI/uvicorn present, no `.venv`; `pytesseract`, `spacy`, `anthropic` and the Tesseract binary are **not installed here**.
  Text-layer PDFs process fully (verified with a generated sample: 4 tests, LOW/NORMAL/HIGH/NORMAL, insights stored);
  scanned images need Tesseract and will show the pipeline's own error until it is installed.
- `.env` holds `GEMINI_API_KEY`, but `ai_insights.py` only reads `ANTHROPIC_API_KEY` - so the LLM toggle is unavailable
  by default (UI says so). Not changing backend logic.

## 6. Verification (Step 4)

- `npm run build` passes (no errors). `python scripts/smoke_test.py`: 24 API checks + 7 browser checks pass against a temporary copy
  (also re-run with a freshly built `run.bat` virtual environment: latest FastAPI, SQLAlchemy 2.1, NumPy 2.4, scikit-learn 1.9 - pipeline unaffected).
- `python scripts/ui_check.py`: 60 layout checks (10 screens x 360/768/1440 px x light/dark: no horizontal overflow, theme applied, console clean),
  mobile drawer (open, Escape, navigate), theme persistence, reduced motion (static hero, no canvas), skip link + focus ring + labelled inputs,
  API-unreachable error state with working "Try again".
- `docs/screenshots/` holds 13 PNGs (1440x900; landing in dark and light) from `scripts/capture_screens.py`, taken against synthetic sample data.
- Console clean on every screen (no errors, no unhandled rejections, no 404s).

## 7. Additions beyond the Streamlit app

- Demo login (`demo@lablens.com` / `Demo@1234`) - the product had none.
- "Load sample reports" (`POST /api/demo/seed`): five synthetic reports rendered as PDFs and processed by the real pipeline.
- Compare chart is grouped by unit (the Streamlit chart mixed mg/dL with g/dL on one axis); trend chart shades the reference range.
- Default choices: dark theme unless the OS says light; Report 1 = second newest / Report 2 = newest (same as Streamlit).
