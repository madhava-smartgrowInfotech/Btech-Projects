# Frontend Plan - Multi-Disease Prediction Using Machine Learning

Batch CSE-A-A3 | Design V3 Depth Studio | Backend port 8303 | Frontend port 5303

## 1. Existing backend endpoints (Flask, `app.py`, untouched)

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/` | - | HTML home: 4 disease cards, each with best model name + test accuracy |
| GET | `/diabetes` `/heart` `/liver` `/kidney` | - | HTML form built from `FIELD_META` + model name + accuracy |
| POST | `/diabetes` `/heart` `/liver` `/kidney` | form fields (one per feature, missing -> "0") | same HTML plus `result` ("Positive (High Risk)" / "Negative (Low Risk)" / "Error: ..."), `probability` (max class probability, %) |

There is **no JSON API**, so a thin FastAPI layer is added in `backend/` (port 8303). It imports `BUNDLES`,
`FIELD_META`, `DISEASE_TITLES`, `TRAINING_REPORT` from `app.py` and runs the same
scale -> predict -> predict_proba steps. `app.py` itself is not modified and still runs on port 5000.

### New FastAPI endpoints (all additive)

| Method | Path | Response |
|---|---|---|
| GET | `/api/health` | `{status}` |
| GET | `/api/diseases` | list: key, title, best model, accuracy, feature count |
| GET | `/api/diseases/{d}` | title, best model, metrics, `fields[]` (name, label, placeholder, type) |
| POST | `/api/predict/{d}` | body `{values:{feature:number}}` -> `{result, positive, probability, model, accuracy}`; 422 with message on bad input |
| GET | `/api/report` | full `training_report.json` (4 algorithms x accuracy/precision/recall/F1 per disease) |
| GET | `/api/datasets` | read-only: row count, class balance, feature names per `data/*.csv` (new, only to show real data on the Data screen) |

## 2. Existing features / screens

1. Home with 4 disease modules, each showing best model + accuracy.
2. Diabetes (8 inputs), Heart (13), Liver (10), Kidney (12) prediction forms with labels and placeholder hints.
3. Prediction result: High/Low risk + confidence %, plus model name and accuracy used.
4. Input error message when values are invalid.
5. Medical disclaimer (educational use only).
6. Model comparison done at training time (4 algorithms per disease, best by F1) - only in `training_report.json`, not shown in the old UI.
7. Responsive layout.

## 3. Screen map (React, kit V3)

| Route | Screen | Covers feature | API |
|---|---|---|---|
| `/` | Landing - three.js hero, scroll story, 4 disease tiles, disclaimer | 1, 5 | `/api/diseases` |
| `/app` | Overview - StatCards, accuracy chart, disease cards | 1 | `/api/diseases`, `/api/report` |
| `/app/predict/:disease` | Prediction form (4 diseases via Tabs/sidebar), result panel with risk + confidence gauge, validation, skeleton/error/success states | 2, 3, 4 | `/api/diseases/{d}`, `/api/predict/{d}` |
| `/app/models` | Model comparison - table + grouped chart (accuracy/precision/recall/F1), best model flagged | 3, 6 | `/api/report` |
| `/app/data` | Datasets - rows, class balance chart, features per disease | 6 | `/api/datasets` |
| `/app/about` | About and disclaimer | 5 | static text from README |
| `*` | Not found | - | - |

Shell: kit `AppShell` (sidebar -> drawer under 768px), topbar dark/light toggle (persisted), `ToastProvider`.

## 4. Decisions / defaults

- Plain JavaScript (.jsx) Vite project; kit copied into `frontend/src/`, nothing imported from outside the folder.
- `run.bat` starts uvicorn on 8303 and Vite on 5303; ports read from `.env` (ports only, no secrets). `.env` is git-ignored, `.env.example` is committed.
- Old Flask app left runnable (`python app.py`, port 5000).
- Note: dataset is synthetic (per README); the UI says so on the Data and About screens.

## 5. Feature checklist (verified in a real browser, Step 4)

- [x] Home shows 4 modules with model + accuracy
- [x] Diabetes prediction
- [x] Heart prediction
- [x] Liver prediction
- [x] Kidney prediction
- [x] Risk label + confidence shown
- [x] Model name + accuracy shown on each prediction screen
- [x] Invalid-input error shown
- [x] Disclaimer shown
- [x] Responsive layout

## 6. Verification log

- `npm run build` passes; `scripts/smoke_test.py` passes (26 checks); `scripts/capture_screens.py` walks 12 screens with 0 console errors, 0 failed requests.
- Predictions through the API match the Flask pages for all four conditions (same label and confidence).
- Checked at 360 / 768 / 1440 px in light and dark: no horizontal overflow on any route.
- Drawer opens/closes with Escape, invalid submit shows 8 field errors and focuses the first, theme persists across reload,
  `prefers-reduced-motion` swaps the WebGL hero for a static image, API-offline shows designed error states.
- Added beyond the old UI: Overview, Model comparison, Datasets screens, "sample record" buttons, training-range hints.
- Only console message ignored: a `THREE.Clock` deprecation warning emitted inside @react-three/fiber.
