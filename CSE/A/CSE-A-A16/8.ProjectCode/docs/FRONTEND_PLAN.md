# Frontend Plan - SignSpeak (CSE-A-A16)

Design kit: **V1 - Aurora Glass** (TypeScript `.tsx`) · Ports: backend **8316**, frontend **5316**

The existing product is a **customtkinter desktop app** (`python run.py`). It has **no HTTP API**, so the
"existing endpoints" below are the functions the GUI calls. The desktop app stays untouched and working.
A thin FastAPI layer in `backend/` imports and exposes those **existing functions** (no logic rewritten), and a
new React app in `frontend/` talks to it.

Because the browser, not the server, owns the webcam, the camera is read with `getUserMedia`; each frame is
drawn to a 960x540 canvas (the desktop `FRAME_WIDTH x FRAME_HEIGHT`, mirrored like `camera.py`) and posted to
the API. The server then runs the **same** `get_roi_box -> crop_roi -> preprocess_roi -> SignRecognizer` code.

---

## 1. Backend inventory

### 1a. Existing functions the GUI calls (the real "backend")

| Module | Function | Used by |
|--------|----------|---------|
| `config` | `CLASSES` (A-Z, space, del, nothing), `ROI_BOX_SIZE`, `IMG_SIZE`, thresholds, training defaults | all tabs |
| `preprocessing` | `get_roi_box`, `crop_roi`, `segment_hand`, `preprocess_roi` | Collect, Recognize |
| `dataset` | `class_counts()`, `available_classes()`, `load_labels()`, `load_dataset()` | Collect, Train |
| `camera.Camera` | threaded OpenCV webcam | Collect, Recognize (replaced by browser camera) |
| `train` | `train_model(epochs, batch_size, learning_rate, data_progress_cb, epoch_cb, stop_flag)` | Train |
| `recognizer.SignRecognizer` | `load()`, `predict_frame(roi)` -> `{label, confidence, mask, stable_label, committed}` | Recognize |
| `tts` | `speak_async(text)` (pyttsx3) | Recognize |
| `gui/about_tab.py` | abstract, pipeline steps, base paper, adoption note (constants) | About |
| files | `models/classification_report.txt`, `training_history.json`, `labels.json`, `asl_cnn_model.keras` | Train, Model |

### 1b. New HTTP API (FastAPI, `backend/`, port 8316) - wraps the functions above

| # | Method | Path | Request | Response |
|---|--------|------|---------|----------|
| 1 | GET | `/api/health` | - | `{status, model_loaded, trained_classes, training_state}` |
| 2 | GET | `/api/config` | - | `{classes, frame{w,h}, roi{x1,y1,x2,y2}, img_size, segmentation_mode, thresholds{...}, training_defaults{...}}` |
| 3 | GET | `/api/about` | - | `{title, batch, abstract, pipeline[], base_paper{}, adoption_note}` |
| 4 | GET | `/api/dataset` | - | `{counts{class:n}, total, trained_classes, ready_to_train}` (`class_counts`) |
| 5 | GET | `/api/dataset/{cls}/images?limit=` | - | `{images[{name, url}]}` newest first (**additive, read-only**) |
| 6 | GET | `/api/dataset/{cls}/images/{name}` | - | PNG (**additive, read-only**) |
| 7 | POST | `/api/preview` | multipart `frame` (JPEG, 960x540) | `{mask: data-URL PNG}` segmentation preview |
| 8 | POST | `/api/collect/{cls}` | multipart `frame` (JPEG, 960x540) | `{class, saved, count}` - crop ROI, resize 200, save PNG like `_save_image` |
| 9 | POST | `/api/recognize/session` | - | `{session_id, model_loaded}` (own smoothing history per browser tab) |
| 10 | POST | `/api/recognize/frame` | multipart `frame`, `session_id` | `{label, confidence, stable_label, committed, mask}`; 409 if no model |
| 11 | POST | `/api/recognize/reload` | - | `{model_loaded, labels}` |
| 12 | POST | `/api/tts/speak` | `{text}` | `{spoken: bool}` (`tts.speak_async`, plays on the server's speakers) |
| 13 | POST | `/api/train/start` | `{epochs, batch_size, learning_rate}` | `{state}`; 400 invalid, 409 already running / <2 classes |
| 14 | POST | `/api/train/stop` | - | `{state}` (sets the `stop_flag`) |
| 15 | GET | `/api/train/status` | - | `{state: idle\|loading\|training\|done\|error, data{done,total}, epoch, epochs, history{acc,val_acc,loss,val_loss}, summary?, error?}` |
| 16 | GET | `/api/model` | - | `{trained, labels, test_accuracy, test_loss, report(text), report_rows[], history, confusion_matrix, trained_at}`; `{trained:false}` (200) if never trained |
| 17 | GET | `/docs` | - | Swagger UI |

Notes: the confusion matrix is only returned by `train_model()` in memory, so the train-job wrapper also writes it to
`models/confusion_matrix.json` (backend layer only; `train.py` is not edited). Endpoints 5, 6 and the confusion-matrix file
are the only additive pieces. CORS is open for the dev server.

## 2. Feature inventory (existing product)

| ID | Feature | Existing location |
|----|---------|-------------------|
| F1 | Start / stop camera, live feed with cyan ROI box, camera-error message | Recognize, Collect |
| F2 | Pick a class (A-Z, space, del, nothing) and see "N images collected for 'X'" | Collect |
| F3 | Live segmentation (mask) preview of the ROI | Collect, Recognize |
| F4 | Capture 1 image (warning "Start the camera first") | Collect |
| F5 | Burst capture N images (1-1000, default 60) with progress + "Done!" | Collect |
| F6 | Capture tips (plain background, even light, 150-250 images/class, vary angle) | Collect |
| F7 | Dataset summary per class + Refresh counts | Train |
| F8 | Hyperparameters: epochs, batch size, learning rate (defaults 25 / 32 / 1e-3) + validation | Train |
| F9 | Start training, live status (preprocessing n/total, epoch, acc, val_acc), error message | Train |
| F10 | Live accuracy / val-accuracy chart | Train |
| F11 | Stop training after the current epoch | Train |
| F12 | Completion summary: test accuracy; best model + labels + report saved | Train |
| F13 | Live prediction: stable letter, confidence bar + %, segmented mask | Recognize |
| F14 | "No trained model" warning with pointer to Train | Recognize |
| F15 | Auto-commit a letter after it is held steady (~18 frames); `space` / `del` gestures work | Recognize |
| F16 | Sentence box + manual Space, Backspace, Clear | Recognize |
| F17 | Speak the sentence (offline TTS) | Recognize |
| F18 | About: abstract, 8-step pipeline, base paper (MAG-KD, IEEE Access 2026, DOI), how this project adopts it | About |
| F19 | Classification report + test accuracy / loss (written to `models/`) | Train (files) |
| F20 | Input validation and API error messages shown to the user | everywhere |

## 3. Screen map (every feature appears)

Kit V1 has no auth and the product has none, so login / settings from the kit are dropped. Theme toggle (persisted) is in the topbar.

| Route | Screen | Features | Kit pieces |
|-------|--------|----------|------------|
| `/` | **Landing** - hero over aurora, "how it works" scroll steps, live stats strip (classes, images collected, model accuracy from the API), CTA to Recognize | F18 (summary) | `AuroraBackground`, `HowItWorks`, `StatsStrip`, `CountUp`, `Reveal`, `MagneticButton`, `Marquee` (A-Z) |
| `/app` | **Dashboard** - model status, dataset size, classes with data, last training result, quick actions | F7, F12, F14, F19 | `StatCard`, `ChartCard`, `EmptyState`, `Skeleton`, `Table` |
| `/app/recognize` | **Recognize** - camera, ROI overlay, letter + confidence + mask, sentence builder, speak | F1, F3, F13-F17 | `Card`, `Button`, `ProgressBar`, `Badge`, `Toast` |
| `/app/collect` | **Collect data** - camera, class picker, counts grid, capture 1 / burst, mask preview, recent captures, tips | F1-F6 | `Select`, `Segmented`, `ProgressBar`, `Table`, `Modal` |
| `/app/train` | **Train model** - dataset coverage, hyperparameters, start/stop, live status + accuracy / loss charts | F7-F12 | `FormField`, `Input`, `ProgressBar`, `ChartCard`, `ConfirmModal` |
| `/app/model` | **Model performance** - test accuracy / loss, per-class report table, confusion matrix, history | F12, F19 | `StatCard`, `Table`, `ChartCard`, `Tabs` |
| `/app/about` | **About** - abstract, pipeline stepper, base paper, adoption note | F18 | `Card`, `Stepper`, `KeyValueList` |

States on every screen: skeleton while loading, empty state with an action (e.g. "No model yet - Train one"), error state saying what failed and what to do, success toasts.

## 4. Environment facts found during the inventory

- Ports 8316 / 5316 are set in `.env` and currently free. **No backend exists yet** (nothing to start); it is built in Step 3 of the work.
- `data/` and `models/` are **empty**: no dataset and no trained model ship with the repo.
- `cv2`, `pyttsx3`, `customtkinter` are not installed in the system Python; TensorFlow 2.21 / FastAPI 0.110 / Playwright are. `run.bat` does not exist yet and will create a `.venv` from `requirements.txt` (+ `fastapi`, `uvicorn`, `python-multipart`).
- Kit V1 is product-coupled to "PolicyLens": `AppShell` imports `@/components/reactbits/AuroraBackground` and `@/lib/auth`; `StatsStrip` imports `@/lib/api`, `@/lib/queries`; `HowItWorks` imports `@/lib/gsap`. None of these exist in the kit, so they are written in this project's copy.

## 5. Tick-off (Step 4 results)

Verified in a real Chromium against the running app: `npm run build` clean; `scripts/smoke_test.py` all pass (API flow incl. stop and
validation); `scripts/capture_screens.py` walked every screen with a model trained **through the Train screen** on 7,250 real ASL
photos (250 per class from the Kaggle "ASL Alphabet" set via `scripts/prepare_data.py`), test accuracy **82.8%**; console, network and
asset 404s clean on every screen at 360 / 768 / 1440 px in light and dark; `run.bat` started both servers from a fresh shell.

- [x] F1 Start / stop camera, ROI box, camera error message (Recognize + Collect; fake camera in tests, permission/no-camera messages in `lib/camera.ts`)
- [x] F2 Class picker and per-class count (Collect, plus clickable coverage grid)
- [x] F3 Live segmentation preview (Collect, Recognize)
- [x] F4 Capture 1 image; "Start the camera first" warning toast
- [x] F5 Burst capture 1-1000 with progress, Stop and "Done!"
- [x] F6 Capture tips
- [x] F7 Dataset summary per class + Refresh (Train, Dashboard chart)
- [x] F8 Hyperparameters with defaults and validation messages
- [x] F9 Start training, live status (preprocessing n/total, epoch, acc, val_acc), error message
- [x] F10 Live accuracy / loss charts (with "show as table")
- [x] F11 Stop after the current epoch (smoke test: stopped at epoch 2 of 40)
- [x] F12 Completion summary: test accuracy, model saved, links to report / Recognize
- [x] F13 Live prediction: stable letter, confidence bar, mask (spelled H E L L O from the fake camera)
- [x] F14 "No trained model" warning with Go to Train
- [x] F15 Auto-commit on a steady sign; `space` / `del` handled in `commit()` (same rules as `_commit_letter`)
- [x] F16 Sentence box + Space, Back, Clear (also editable by hand)
- [x] F17 Speak sentence (server pyttsx3, browser voice fallback)
- [x] F18 About: abstract, 8-step pipeline, base paper + DOI link, adoption note
- [x] F19 Classification report, test accuracy / loss, per-class table, confusion matrix (Model screen)
- [x] F20 Validation and API error messages surfaced (form errors, toasts, error states with retry)

Deviations: the desktop webcam is replaced by the browser camera; the "Collect" burst delay and thresholds come from `config.py` via `/api/config`.
