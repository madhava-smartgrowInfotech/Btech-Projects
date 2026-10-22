# Frontend plan - Fake News Detection (PCA + Firefly + MSVM)

Batch CSE-C-C6 · design **V1 Aurora Glass** · ports **backend 8406 / frontend 5406**

## 1. What exists today (inventory)

The product is a **Streamlit app** (`app.py`) over a pure-Python library (`src/`). There is **no HTTP API**, no `.env`,
no `run.bat`, no `docs/`. The legacy Streamlit app and the CLI (`train.py`, `predict.py`) stay untouched.

### 1.1 Library functions the UI relies on (not changed)

| Function | Used for |
|---|---|
| `FakeNewsMSVMPipeline.load(path)` / `.predict(texts)` -> `(ids, proba)` | single + batch detection |
| `FakeNewsMSVMPipeline(max_tfidf, n_fireflies, n_generations).fit(texts, y)` / `.save(path)` | retraining |
| `pipe.stats_` | analytics (accuracy, F1, PCA, Firefly curve, confusion matrix, report, baseline) |
| `load_csv(path)` / `build_demo_dataset(n_per_class)` | retraining data |
| `clean_text`, `ID2LABEL`, `LABELS` | cue extraction, class names |

### 1.2 Features / screens in the Streamlit app (5 tabs)

| # | Feature | Detail |
|---|---|---|
| F1 | **Detect** | headline (optional) + article text, min 5 words; shows verdict badge, latency ms, class-probability bar chart, confidence %, sensational cues, credibility cues, "PARTIALLY TRUE" tip, "How it works" 4-step panel |
| F2 | **Batch Check** | CSV upload, 10-row preview, text-column selector (auto-guess text/news/content/statement/article), run detection, "Screened N articles", first 50 rows (text, predicted, confidence), verdict distribution pie, download results CSV |
| F3 | **Model Analytics** | Accuracy, Macro F1, Features (total -> selected), Train time; PCA/Firefly caption (components, variance, C, gamma, baseline accuracy, pp gain); confusion matrix; Firefly optimisation curve; classification report text; baseline-vs-proposed comparison table |
| F4 | **Retrain** | optional labelled CSV, sliders Fireflies 4-20, Generations 3-30, Max TF-IDF 1000-8000 (step 500), retrain (demo corpus 300/class if no CSV), success message with accuracy/F1, hot reload of the model |
| F5 | **About** | pipeline table, output classes, keywords, run instructions |
| F6 | Cross-cutting | model auto-trains if `models/msvm_model.pkl` is missing |

### 1.3 CLI (kept, not part of the UI)
`train.py` (--csv --n --fireflies --generations --max-tfidf --out), `predict.py` (--text / --csv).

## 2. Backend endpoints

Everything below is **new and thin** (`backend/main.py`, FastAPI): each endpoint calls the functions in 1.1.
No logic in `src/` changes. Additive read-only endpoints are marked *(read-only)*.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/health` | - | `{status, model_loaded, model_path}` |
| GET | `/api/model` *(read-only)* | - | `{labels, stats{...without y_test/y_pred}, pipeline[...]}` |
| GET | `/api/samples` *(read-only)* | - | `{samples:[{label, title, text}]}` one real corpus document per class from `build_demo_dataset` |
| POST | `/api/predict` | `{title?, text}` (>= 5 words, else 422) | `{label, label_id, confidence, probabilities{label:p}, latency_ms, cues{sensational[], credibility[]}}` |
| POST | `/api/batch/preview` | multipart `file` (.csv) | `{filename, n_rows, columns[], guessed_column, preview[10 rows]}` |
| POST | `/api/batch/run` | multipart `file`, `column` | `{n_rows, column, rows[{text, predicted, confidence}], distribution{label:n}, columns, csv}` |
| POST | `/api/retrain` | multipart `file?`, `fireflies`, `generations`, `max_tfidf` | `202 {job_id}` (runs in a background thread) |
| GET | `/api/retrain/{job_id}` | - | `{status: running/done/error, elapsed_s, result{accuracy,f1_macro,...}?, error?}` |

Retrain is a background job (the Streamlit tab blocks on a spinner; a browser request would time out). On completion the
loaded model is swapped in memory and saved to `models/msvm_model.pkl`, same as the Streamlit tab, so no page reload is needed.

## 3. Screen map

Route -> kit pieces -> API.

| Route | Screen | Covers | Kit components | API |
|---|---|---|---|---|
| `/` | **Landing** (aurora hero, live demo verdict, how it works, real metric strip, CTA) | F5 | AuroraBackground, Reveal, Stagger, CountUp, MagneticButton, HowItWorks, StatsStrip, ExampleAnswer | `/api/model`, `/api/samples`, `/api/predict` |
| `/app` | **Detect** (default app screen) | F1 | AppShell, Card, Field/Textarea, Button, Badge, Chart (bar), Skeleton, EmptyState, Toast | `/api/predict`, `/api/samples` |
| `/app/batch` | **Batch Check** | F2 | FileDrop, Table, Select, Chart (pie), Button, Toast | `/api/batch/preview`, `/api/batch/run` |
| `/app/analytics` | **Model Analytics** | F3 | StatCard, Chart (heatmap grid / line), Table, Tabs, Skeleton | `/api/model` |
| `/app/retrain` | **Retrain** | F4 | FileDrop, Slider, Button, progress, Modal (confirm overwrite), Toast | `/api/retrain`, `/api/retrain/{id}` |
| `/app/about` | **About** | F5 | Card, Table, Badge | `/api/model` |
| `*` | 404 | - | EmptyState | - |

No login: the Streamlit product has none and the prompt says not to change contracts, so none is added.
Shell: sidebar (drawer < 1024px) + topbar with light/dark toggle (persisted) + mobile bottom bar, as in the kit.

## 4. Kit adaptations (copy only, kit folder untouched)

* Kit tokens live in `src/index.css` (the prompt says `styles/tokens.css`); import that once in `main.tsx`.
* Kit `AppShell` is coupled to another product (auth, nav, branding): rewrite the copy for this nav.
* Kit imports files it does not ship: `lib/gsap`, `components/reactbits/AuroraBackground`, `lib/api`, `lib/queries`, `lib/auth`. Write them here.
* Product-neutral: Logo, landing pieces and storage keys renamed for this product.

## 5. Environment findings (Step 1.4)

* No `.env` -> create `.env` (`BACKEND_PORT=8406`, `FRONTEND_PORT=5406`) + `.env.example`.
* Shipped `.venv/` is a copy from another PC (points at `C:\Python314`, missing) -> `run.bat` rebuilds it.
* `models/msvm_model.pkl` was written by scikit-learn 1.9.0; the system Python has 1.5.0 -> the backend venv installs current scikit-learn.
* The shipped model was trained on the template-generated demo corpus (750 docs); its 100% test accuracy is a property of that
  synthetic data, and the UI states this next to the metrics.

## 6. Verification checklist (Step 4)

Walked in a real browser (Playwright, Chrome) against the running app; smoke test `scripts/smoke_test.py` passes 16/16;
`npm run build` passes; screenshots in `docs/screenshots/` (made by `scripts/capture_screens.py`).

- [x] F1 **Detect** - verdict badge, latency, class-probability chart (with table view), confidence, sensational + credibility cues, PARTIALLY TRUE tip, "How it works" panel, 5-word minimum (inline message), examples from the corpus, Ctrl+Enter
- [x] F2 **Batch Check** - CSV upload with validation, 10-row preview, column selector (auto-guessed), run, "Screened N articles", first 50 rows (sortable, paged), distribution chart, download CSV (all rows), example CSV download
- [x] F3 **Model Analytics** - Accuracy, Macro F1, Features (total -> selected), Train time; PCA / Firefly summary with baseline gain in pp; confusion matrix; Firefly curve; classification report (table + raw text); baseline-vs-proposed table
- [x] F4 **Retrain** - optional labelled CSV, Fireflies 4-20, Generations 3-30, Max TF-IDF 1000-8000 (step 500), confirm dialog, live progress, accuracy / F1 on completion, model hot-swapped (no reload), resumes after a page reload
- [x] F5 **About** - pipeline, classes, keywords, run instructions (+ landing page)
- [x] F6 **Auto-train fallback** - backend trains the demo model when `models/msvm_model.pkl` is missing (same code path as `app.py`; not exercised in the browser)

Cross-cutting, all checked: light/dark (persisted), 360 / 768 / 1440 px with no sideways scroll, drawer + bottom bar on phones,
Escape closes dialog and drawer, visible focus rings, `prefers-reduced-motion`, skeleton / empty / error / success states
(including the backend being down), console clean in normal use (the only logged error is the deliberate 400 for an unreadable CSV).

## 7. Backend / contract changes
None to `src/`, `app.py`, `train.py`, `predict.py`. New: `backend/` (the API above), `run.bat`, `.env`, `.env.example`,
`scripts/`, `docs/`. Additive read-only endpoints: `/api/model`, `/api/samples`, `/api/health`.
