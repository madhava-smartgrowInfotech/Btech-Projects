# Frontend Plan - PeerScope (Kit V3 "Depth Studio")

Project: Paper Evaluation Using Artificial Intelligence (PeerScope). Backend: FastAPI on **8408**. Frontend: Vite + React (JS) on **5408**.
There was no `frontend/` before this job; the old UI was vanilla HTML/JS in `static/` served by FastAPI on port 8000.

## 1. Backend endpoint inventory

| # | Method | Path | Request | Response |
|---|--------|------|---------|----------|
| 1 | GET | `/api/health` | - | `{status, product, llm_status, embedding_status, model_loaded, reviewer_count, literature_retrieval}` |
| 2 | GET | `/api/model/metrics` | - | `models/metrics.json`: `accuracy, precision_macro, recall_macro, f1_macro, roc_auc, confusion_matrix, labels, test_samples, class_distribution, dataset_source, synthetic_fallback, dataset_rows, random_seed, model_type, features, trained_at`; or `{status:"missing", note}` |
| 3 | GET | `/api/reviewers` | - | `[ {id, display_name, affiliation, expertise_description, research_topics, methods, keywords, publication_titles, current_load, maximum_load, is_active, conflict_terms} ]` |
| 4 | POST | `/api/reviewers` | JSON `ReviewerIn` (display_name required) | 201 reviewer object; 400 on error |
| 5 | PUT | `/api/reviewers/{id}` | JSON `ReviewerIn` | reviewer object; 404 |
| 6 | DELETE | `/api/reviewers/{id}` | - | `{deleted: id}`; 404 |
| 7 | GET | `/api/reviewers/export/csv` | - | CSV download |
| 8 | POST | `/api/reviewers/import` | multipart `file` (CSV) | `{imported: n}`; 400 |
| 9 | POST | `/api/analyze` | multipart `file` (PDF, <=20 MB) + `active_only`, `min_score`, `topic`, `method` | full analysis object (paper, features, ml_decision_signal, structural_assessment, review, review_quality, literature, reviewers[], overall_assessment, concern_count, recommendation_count, top_reviewer, disclaimer, responsible_use, warning?, analysis_id); 400/413/500 `{detail}` |
| 10 | GET | `/api/analyses` | - | `[ {id, filename, created_at, overall_assessment, concern_count, recommendation_count, top_reviewer, status} ]` |
| 11 | GET | `/api/analyses/{id}` | - | stored analysis object; 404 |
| 12 | GET | `/api/analyses/{id}/export?format=json\|pdf` | - | JSON or PDF download |

No new endpoints are planned. (`/` and `/static` serve the old UI and stay as a fallback.)

## 2. Existing features (from README + old UI)

1. PDF intake: drag/drop upload, extension/type/size validation, clear errors
2. Analysis results: paper overview, preliminary assessment (ML decision signal + structural score + AI review status), strengths, major concerns, minor concerns, recommendations, review coverage bars, related literature (OpenAlex), recommended reviewers with audit breakdown, disclaimer, JSON/PDF export
3. Reviewer-match filters: active only, minimum score, topic, method
4. Reviewer directory: list, add, edit, activate/deactivate, delete, CSV import, CSV export
5. Model Performance page: real metrics, confusion matrix, class distribution, synthetic-fallback disclosure
6. Analysis history: list, reopen, JSON/PDF export
7. Dashboard: reviewer count, model status, analyses count, recent analyses
8. About / pipeline / matching weights / responsible use / privacy
9. Product-wide disclaimers (decision support, human judgment)

## 3. Screen map (kit AppShell + routes)

| Route | Screen | Kit pieces | API |
|-------|--------|-----------|-----|
| `/` | Landing (Depth Studio: three.js hero, scroll story, pipeline, CTA) | HeroVisual (lazy), Reveal, Parallax, Marquee, CountUp, MagneticButton | `/api/health` (live counts) |
| `/app` | Dashboard | StatCard, Table, ChartCard, EmptyState | health, analyses, metrics |
| `/app/analyze` | Analyze Paper (upload + filters + stepper + full result) | FileDrop, Input, Switch, Stepper, ProgressBar, Tabs, Card, Badge | POST analyze, GET analyses/{id}, export |
| `/app/analyses/:id` | Saved analysis (same result view) | same result component | analyses/{id}, export |
| `/app/reviewers` | Reviewer Directory + add/edit modal + confirm delete + CSV import/export | Table, Modal, Input, Textarea, Select, SearchField, Toast | reviewers CRUD, import, export |
| `/app/model` | Model Performance | StatCard, GroupedBar / Donut charts, confusion matrix | model/metrics |
| `/app/history` | Analysis History | Table, SearchField, EmptyState | analyses, export |
| `/app/about` | About / pipeline / weights / responsible use / privacy | Card, Timeline, KeyValueList | health |
| `*` | Not found | EmptyState | - |

Cross-cutting: dark/light toggle in topbar (ThemeProvider), toasts, mobile drawer nav, skeleton/empty/error states, reduced-motion.

## 4. Environment

- Backend port is hard-wired to 8000 in `run.bat`, `Dockerfile`, `app/config.py` default, docs, tests, old capture script. Plan: add `.env` (`PEERSCOPE_PORT=8408`, `FRONTEND_PORT=5408`), have `config.py` read it, and have `run.bat` start backend (8408) + Vite (5408). CORS is already open (`*`).
- `.venv` in the folder is stale (points to a non-existent `C:\Python314`). It is untracked; `run.bat` will detect a broken venv and recreate it. For my verification I use system Python 3.11 (fastapi/pymupdf/sklearn present; torch/transformers absent, so the app runs on its documented TF-IDF + "AI review unavailable" fallback).
- Confirmed: backend starts on 8408 and returns health, reviewers (6) and analyses (3).
- Repo root is `D:/abstracts/Madhav` (shared with many sibling projects); I will commit only this folder by explicit pathspec.

## 5. Verification checklist (every original feature still works)

Verified against the running app on API :8408 / web :5408 with Playwright (`scripts/capture_screens.py`), the HTTP smoke test (`scripts/smoke_test.py`, 24/24 pass) and `pytest tests` (7/7 pass).

- [x] 1 PDF intake + validation errors - upload via drop zone/browse; non-PDF rejected client-side and by the API (400), fake PDF rejected (400), 20 MB limit shown and enforced
- [x] 2 Analysis result - Overview (paper overview, preliminary assessment), Review (strengths, major/minor concerns, recommendations, coverage, AI synthesis, evidence), Literature, Reviewers, Audit & export (JSON + PDF download) all render from the real response
- [x] 3 Match filters - active-only, minimum score, topic, method are sent to `/api/analyze`
- [x] 4 Reviewer CRUD / activate-deactivate / CSV import / CSV export - add, edit, deactivate, delete (confirm dialog), import, export, search, all hit the API
- [x] 5 Model Performance - metrics, confusion matrix, class distribution, per-class table, synthetic-fallback disclosure, "no trained model" empty state
- [x] 6 History - list, search, reopen (`/app/analyses/:id`), JSON/PDF export, 404 state
- [x] 7 Dashboard - live reviewer/analysis/model/AI status, recent analyses, chart
- [x] 8 About - pipeline, weights, responsible use, privacy, live system status
- [x] 9 Disclaimers - in the shell footer on every app screen, in results/audit, on the landing page

## 6. Result and decisions

- Screens built: Landing, Dashboard, Analyze (+ result tabs), Saved analysis, Reviewers (+ add/edit modal, delete confirm), Model performance, History, About, 404 (11 routes).
- Kit V3 copied into `frontend/src` (no outside imports). Adapted in the copy only: `layout.jsx` (PeerScope nav/brand/footer, `lib/stats`), `controls.jsx` FileDrop (binary files, type check), `charts` HBarChart (name/label width/domain), `lib/format.js`, `lib/theme.jsx` storage key, `modal` CSS (pinned footer, scrolling body). The kit shipped no `lib/stats`, `main`, `App` or landing markup; those are new.
- Backend: no endpoint or logic changes. Config only: `app/config.py` reads `.env` and defaults to port 8408; `run.bat` starts API + web app and rebuilds a stale `.venv`; Dockerfile now listens on 0.0.0.0:8408.
- The old vanilla UI in `static/` is kept and still served by the API at `/` as a fallback.
- Environment note: this machine's saved decision model was trained with scikit-learn 1.9; with an older scikit-learn `predict_proba` fails and the API returns a label without probabilities. The UI handles that (no fake confidence bars). `run.bat`'s fresh venv installs a matching version.
- The local LLM (torch/transformers) was not installed during verification, so the AI-review "unavailable" state was exercised; the AI-synthesis renderer was checked only against stored output.
