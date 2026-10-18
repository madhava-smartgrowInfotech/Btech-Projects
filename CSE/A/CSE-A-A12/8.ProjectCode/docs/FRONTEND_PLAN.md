# Frontend Plan - Pneumonia Detection Using Deep Learning

Design: **V2 Neo Brutal Grid** (kit copied into `frontend/src/`). Ports: backend **8312**, frontend **5312** (`.env`).

## 1. Existing backend (Flask `app.py`, untouched)

The Flask app has no JSON API. It serves Jinja templates on port 5000 and renders from the same Python modules the new API will reuse.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/` | - | `index.html` (upload form, demo-mode banner) |
| POST | `/predict` | multipart field `xray_image` (png/jpg/jpeg, max 8 MB) | 302 to `/result/<id>`; on bad input flashes a message and redirects to `/` |
| GET | `/result/<id>` | - | `result.html` (original, Grad-CAM, prediction, 3 probabilities); unknown id flashes and redirects |
| GET | `/history` | - | `history.html` (up to 200 predictions, newest first) |
| GET | `/about` | - | `about.html` (static project text) |
| GET | `/static/uploads/*`, `/static/heatmaps/*` | - | saved X-ray / Grad-CAM overlay images |

Data: SQLite `pneumonia_app.db`, table `predictions(id, filename, original_path, heatmap_path, prediction, confidence, prob_normal, prob_bacterial, prob_viral, created_at)`.
Model: `saved_models/pneumonia_model.h5` is **not shipped**, so the app runs in **Demo Mode** (untrained 3-class CNN, flagged in the UI). Classes: Normal / Bacterial Pneumonia / Viral Pneumonia.

## 2. New thin API (`backend/main.py`, FastAPI, port 8312)

Imports the existing `model.*` and `database.db` functions and `app.get_model()`. No logic is rewritten.

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | status, `demo_mode`, class names |
| POST | `/api/predict` | same pipeline as Flask `/predict`; returns the saved record as JSON; 400 JSON errors for the same bad-input cases |
| GET | `/api/predictions?limit=200` | same as `get_all_predictions` |
| GET | `/api/predictions/{id}` | same as `get_prediction`; 404 JSON if missing |
| GET | `/api/stats` | **additive, read-only**: totals and per-class counts derived from the same table (feeds the dashboard) |
| DELETE | `/api/predictions/{id}` | **additive**: removes a scan and its two image files |
| POST | `/api/auth/login`, `/api/auth/logout` | **additive**: demo login, signed HttpOnly cookie (no demo login existed before) |
| GET | `/api/auth/me` | **additive**: signed-in user, or `null` (200) when signed out |
| GET | `/api/files/{uploads\|heatmaps}/{name}` | the saved images (same folders as Flask), behind the login |

## 3. Features to preserve (tick off in Step 4)

- [x] F1  Upload a chest X-ray by file picker or drag and drop (png/jpg/jpeg, 8 MB limit)
- [x] F2  Image preview before analysing
- [x] F3  Validation messages: no file, empty name, unsupported type, too large
- [x] F4  Preprocess, CNN classify, per-class probabilities (Normal / Bacterial / Viral)
- [x] F5  Grad-CAM heatmap overlay next to the original
- [x] F6  Result page: label badge, confidence, three probability bars
- [x] F7  Demo Mode banner on Detect and Result when no trained model is loaded
- [x] F8  Result stored in SQLite and viewable later
- [x] F9  History table: id, thumbnail, filename, prediction, confidence, date, link to result
- [x] F10 History empty state with link to analyse an X-ray
- [x] F11 "Analyze another image" action from the result
- [x] F12 "How it works" five-step pipeline explanation
- [x] F13 About page: title, abstract, pipeline, tech stack, disclaimer
- [x] F14 Clinical disclaimer visible site-wide (footer)
- [x] F15 Unknown result id handled (not found state)

## 4. Screen map

| Route | Screen | Covers |
|---|---|---|
| `/login` | Sign in (demo credentials shown and one-click fill) | demo login |
| `/` | Landing (brutalist hero, pipeline, class explainer, disclaimer, CTA) | F7, F12, F14 |
| `/app` | Dashboard (stat cards, class-distribution chart, recent scans) - uses `/api/stats` | F8 |
| `/app/detect` | Detect (FileDrop, preview, analyse, progress, errors) | F1-F3, F7, F12 |
| `/app/result/:id` | Result (original vs Grad-CAM, badge, probability bars, new-scan action, not-found state) | F4-F6, F11, F15 |
| `/app/history` | History (table with thumbnails, search/filter by class, empty state, cards on mobile) | F8-F10 |
| `/app/about` | About (abstract, pipeline, stack, disclaimer) | F13, F14 |

Shared: AppShell with sidebar (drawer on mobile), topbar theme toggle (persisted), toasts, skeletons, 404 route.

## 5. Notes / assumptions

- The shipped `venv/` was created on another machine and is not usable; `run.bat` creates a fresh `.venv`.
- No X-ray dataset ships with the repo (`dataset_sample/` is empty), so there is no sample image to demo with.
- `opencv-python-headless` was missing from the system Python and was installed to run the backend.

## 6. Verification (all run against the live stack)

- `npm run build` passes.
- `scripts/smoke_test.py`: 25 checks pass (login, 401s, upload validation 400/413, predict x4 samples, images served, history, stats, 404, delete, logout). Also run against a fresh `.venv` built by `run.bat` from `requirements.txt` (TensorFlow 2.16.1) on other ports.
- `scripts/capture_screens.py`: walks every screen with real uploads, 13 PNGs in `docs/screenshots/`, console clean, no 4xx/5xx.
- `scripts/verify_ui.py`: 360, 768 and 1440 px in light and dark on all screens with no horizontal overflow; mobile drawer and delete dialog close on Escape with focus trapped inside; theme persists after reload; visible focus ring; landing visible with `prefers-reduced-motion`.

## 7. Extras added beyond the original features

Dashboard with stats and charts, demo login and sign-out, delete scan, heatmap blend slider, side-by-side view, print report, download heatmap, CSV export, history search and class filter, sortable and paginated table (cards on mobile), upload progress, persisted dark mode, 404 page, "Demo model" badge in the top bar.
