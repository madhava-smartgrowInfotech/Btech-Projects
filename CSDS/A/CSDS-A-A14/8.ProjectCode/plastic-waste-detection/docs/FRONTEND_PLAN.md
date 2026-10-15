# Frontend plan - PlastiScan (CSDS-A-A14)

Project: Automated Plastic Waste Detection in Oceans Using Artificial Intelligence
Design: **V4 - Soft Pastel Calm** (kit copied into `frontend/src/`) · Ports: **backend 8114, frontend 5114**

The existing Streamlit app (`app.py`, `pages/`) is left untouched and still runs with `streamlit run app.py`.
The new UI is a React (Vite, JavaScript) app in `frontend/`, talking to a thin FastAPI layer in `backend/`
that imports the **existing** functions from `src/` (no logic is rewritten).

---

## 1. Backend inventory

### 1a. HTTP endpoints that exist today

**None.** The product is Streamlit pages calling Python functions directly. There is no HTTP API, so
`backend/api.py` (FastAPI) is added. It only wraps existing functions.

### 1b. Existing Python functions the API wraps

| Function | File | What it does |
|---|---|---|
| `load_model()` -> `(model, device, used_fallback, message)` | `src/model.py` | Loads `models/best.pt`, else falls back to COCO `yolov8n.pt`; picks cuda/cpu |
| `preprocess_image(img, ...)` | `src/preprocessing.py` | resize -> grey-world colour fix -> denoise -> CLAHE |
| `run_detection(model, img, conf_threshold)` | `src/detection.py` | YOLO predict, draws boxes, returns `(annotated, [Detection])` sorted by confidence |
| `detections_to_rows(dets)` | `src/detection.py` | Table rows: Object, Class, Confidence, BBox |
| `add_record / get_history / clear_history` | `src/database.py` | SQLite `detection_history.db` |
| `is_valid_image_file / timestamp_now / RESULTS_DIR` | `src/utils.py` | jpg/jpeg/png check, timestamp, folders |
| `results/eval_summary.json` + `results/*.png` | written by `evaluate.py` / `train.py` | Precision, Recall, mAP50, mAP50-95 and plots |

### 1c. New API (thin, additive; wraps the functions above)

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/health` | - | `{status, device, model:{ready, used_fallback, message, error?}}` |
| POST | `/api/detect` | multipart: `file` (jpg/jpeg/png), `conf` 0.1-0.9 (default 0.5), `preprocess` bool (default true) | `{filename, timestamp, detection_count, average_confidence_percent, detections:[{index,class_name,confidence,confidence_percent,bbox:[x1,y1,x2,y2]}], rows, annotated_image (data URL), image_size, logged, saved_as, model:{...}}` - 400 for a bad extension, 422 for an unreadable image, 503 if the model cannot load |
| GET | `/api/history` | - | `[{filename, object_count, avg_confidence, timestamp}]` (newest first) |
| DELETE | `/api/history` | - | `{cleared:true}` |
| GET | `/api/evaluation` | - | `{available:false}` or `{available:true, metrics:{precision,recall,map50,map50_95}, plots:[{key,label,url}]}` |
| GET | `/api/evaluation/plots/{name}` | whitelisted PNG names only | image/png |

Behaviours kept exactly as Streamlit has them: history is logged only when at least one object is detected;
the annotated image is also saved to `results/detected_<stem>.jpg`; the JSON report and the image download are
built from the same data (the report is generated in the browser, as Streamlit's download button does).

---

## 2. Feature / screen inventory (everything the product already has)

Source: `README.md`, `app.py`, `pages/1..4`, CLI scripts.

| # | Feature | Where today | Where in the new UI | Done |
|---|---|---|---|---|
| F1 | Upload JPG/JPEG/PNG; reject wrong format; reject corrupted image | Detection | `/app/detect` FileDrop + error states | [x] |
| F2 | Confidence threshold 0.1-0.9, step 0.05 (default 0.5) | Detection sidebar | `/app/detect` slider | [x] |
| F3 | "Apply preprocessing pipeline" toggle (colour correction, denoise, CLAHE) | Detection sidebar | `/app/detect` switch | [x] |
| F4 | Device used (GPU/CPU) + model status: trained vs COCO fallback warning | Detection sidebar | `/app/detect` model card + topbar status | [x] |
| F5 | Original vs detected image side by side | Detection | `/app/detect` | [x] |
| F6 | Detected object count, "Plastic i -> x%" list, detection table (Object/Class/Confidence/BBox) | Detection | `/app/detect` result panel | [x] |
| F7 | Zero-detection message (lower threshold / model not trained) | Detection | `/app/detect` empty state | [x] |
| F8 | Download annotated image + JSON report | Detection | `/app/detect` buttons | [x] |
| F9 | Run saved to detection history (when >=1 object) | Detection | API + visible "logged" feedback | [x] |
| F10 | Dashboard: 4 summary cards, objects-per-image bar, confidence histogram, history line, history table, empty state | Dashboard | `/app/dashboard` | [x] |
| F11 | Clear history | Dashboard | `/app/dashboard` button + confirm Modal | [x] |
| F12 | Evaluation: Precision/Recall/mAP@0.5/mAP@0.5:0.95 + up to 7 plots + "not run yet" and "no plots" states | Evaluation | `/app/evaluation` | [x] |
| F13 | About: architecture diagram, base-paper connection, not-implemented warning, why YOLOv8, future scope, 3 viva Q&As | About | `/app/about` | [x] |
| F14 | Home: overview, problem statement, 6 objectives, technology stack, how it works, navigation hint | Home | Landing page `/` | [x] |
| F15 | CLI `train.py`, `evaluate.py`, `predict.py` unchanged | scripts | untouched, still work | [x] |
| F16 | GPU auto-detect with CPU fallback | `src/model.py` | shown in F4 | [x] |
| F17 | Streamlit app still runs untouched | `app.py`, `pages/` | untouched | [x] |

---

## 3. Screen map (what gets built)

| Route | Screen | Kit pieces | API |
|---|---|---|---|
| `/` | **Landing** - hero, how it works (stepper), objectives, problem, tech stack, CTA | motion helpers, Card, Button, Stepper | `/api/health` (status pill) |
| `/app/detect` | **Detection** - FileDrop, settings, model card, original/annotated, count, scores, table, downloads | FileDrop, Segmented/Switch, Card, StatCard, Table, Badge, Toast, Skeleton, EmptyState, ErrorState | `/api/detect`, `/api/health` |
| `/app/dashboard` | **Dashboard** - 4 StatCards, 3 charts, history table, clear | StatCard, chart wrappers, Table, Modal, EmptyState | `/api/history`, `DELETE /api/history` |
| `/app/evaluation` | **Evaluation** - 4 metrics, plot gallery (Modal zoom) | StatCard, Card, Modal, EmptyState | `/api/evaluation` |
| `/app/about` | **About** - architecture, base paper, why YOLOv8, future scope, viva FAQ | Card, Timeline, Tabs/accordion, Badge | none (static project text) |
| `*` | Not found | EmptyState | - |

Shell: kit `AppShell` (sidebar -> drawer under 900px, topbar theme toggle, API status pill, bottom bar on phones).

---

## 4. Ports and run

- Backend `8114`, frontend `5114` (Vite proxies `/api` to 8114 in dev). Stored in `.env.example` and in `run.bat`.
- `run.bat` (new, at the top of `plastic-waste-detection/`) starts API + Vite together.

## 5. Open issues found in Step 1

- `ultralytics` and `opencv` are not installed in this Python (3.11.9). `streamlit` is also absent. They are
  needed to run detection at all (and by the existing Streamlit app). Plan: a project-local `.venv`
  (system-site-packages so the existing torch 2.2.0 is reused) with `ultralytics`, `torchvision==0.17.0`,
  `opencv-python-headless` installed there only.
- No `models/best.pt` and no dataset are bundled, so the app runs on the COCO `yolov8n.pt` fallback (first load
  downloads it). The UI states this clearly, exactly as Streamlit does. Evaluation shows its "not run yet" state
  until `evaluate.py` is run with real weights.
- No ports exist in any `.env`. The parent-folder `.env` holds an unrelated Gemini key; it is not touched and is
  kept out of the commit.

---

## 6. Verification record (Step 4)

- `npm run build` passes; `python scripts/smoke_test.py` passes (API, error paths, proxy).
- Every screen was walked in real Chrome (Playwright) at 360 / 768 / 1440 px, light and dark: no horizontal
  scroll, no console errors apart from the deliberate invalid-file request, no asset 404s.
- Verified in the browser: upload + detect, invalid file (API 400 message shown), threshold change and re-run,
  zero-detection state with "lower threshold" action, preprocessing toggle, image and JSON downloads, history
  logging, dashboard stats/charts/table, clear-history confirm (Escape cancels), evaluation empty state and the
  metrics/plots layout (checked with temporary placeholder files that were deleted afterwards), About tabs and FAQ,
  theme toggle persisted across reload, `prefers-reduced-motion`, mobile drawer navigation.
- F15 / F17: `train.py`, `evaluate.py`, `predict.py`, `app.py`, `pages/` and `src/` have no changes in git.
