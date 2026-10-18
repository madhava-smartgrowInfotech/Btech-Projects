# Report facts - SignSpeak (CSE-A-A16)

Single source of truth for every submission document. All numbers come from this project's own artefacts:
`docs/metrics/metrics.json` (written by `scripts/measure_metrics.py`), `models/*`, `tests/`, `scripts/smoke_test.py`.
Measured on 18 October 2026.

## 1. Identity

| Item | Value |
|---|---|
| Product | SignSpeak |
| Title | Sign Language Recognition System Based on Convolutional Neural Networks (CNNs) |
| Batch | CSE-A, Batch 16 (A16) |
| Students | AJAY - 24K95A0502 · A NAVADEEP REDDDY - 23K91A0514 · B MANIDEEP - 23K91A0540 · B MAHESHWARI - 23K91A0536 |
| Guide | V. PALLAVI (designation not given in the batch files) |
| College | TKR College of Engineering & Technology (An Autonomous Institution) - from `Documentary/Batch_16_*.docx` |
| Unknown (left as placeholders) | HOD name, Principal name, academic year, place/date, guide designation |
| Base paper | D. T. D. Vo, V. D. Nguyen, T. H. M. Nguyen, M. H. Vo, "MAG-KD: Mask-Guided Adaptive Gating Knowledge Distillation for Skeleton-Based Sign Language Recognition on Edge Devices," IEEE Access, vol. 14, pp. 54761-, 2026, doi 10.1109/ACCESS.2026.3681176 |
| Spelling note | names are used verbatim from `Students.txt` / `1.A16_BATCH_DETAILS.docx`, including "A NAVADEEP REDDDY" (three D's in the source files - possibly a typo; confirm with the student) and the hall ticket "24k95A0502" is written "24K95A0502" |

(Names are used exactly as in `Students.txt` and `1.A16_BATCH_DETAILS.docx`.)

## 2. What was built

The product started as a customtkinter desktop app (`python run.py`). It now also has a web app:

* `sign_language_app/` (1,648 lines of Python) - the original modules, unchanged: `config`, `preprocessing`, `camera`, `dataset`, `model`, `train`, `recognizer`, `tts`, `gui/`.
* `backend/` (530 lines) - thin FastAPI layer (port 8316) over those modules: 16 JSON/image endpoints + `/docs`.
* `frontend/` (5,268 lines TypeScript/TSX) - React 18 + Vite 8 + Tailwind 4 + TanStack Query + Recharts (port 5316); landing page + 6 app screens.
* `scripts/` - `smoke_test.py`, `measure_metrics.py`, `capture_screens.py`, `capture_extra_screens.py`, `prepare_data.py`, `verify_docs.py`, `docs_build/*`.
* `tests/` - 52 pytest tests (398 lines).

Browser owns the webcam (`getUserMedia`); each frame is cover-cropped to 16:9, mirrored, drawn to a 960x540 canvas and posted as a JPEG
(quality 0.8, about 27 KB). The server runs the same pipeline as the desktop app. One request is in flight at a time, at least 60 ms apart.

### Pipeline (identical for collection, training, recognition)
frame 960x540 -> ROI crop 300x300 at x 620-920, y 90-390 -> grayscale -> Gaussian blur 7x7 -> Otsu threshold (invert if mean > 127) ->
morphology open x1, close x2 (3x3) -> resize 64x64 (INTER_AREA) -> /255 -> CNN -> softmax over 29 classes.

### Decision logic (`SignRecognizer.predict_frame`)
confidence >= **0.75** else label := "nothing" -> history of last **15** -> majority vote -> stable counter -> commit when stable
count >= **18** frames, label != "nothing" and != last committed letter; "nothing" resets the repeat guard. `space` and `del` are commit labels.

### CNN (Keras Sequential "asl_cnn")
Input 64x64x1 -> [Conv3x3x32, BN, MaxPool] -> [Conv3x3x64, BN, MaxPool, Dropout .25] -> [Conv3x3x128, BN, MaxPool, Dropout .25] ->
Flatten (8,192) -> Dense 256 ReLU, BN, Dropout .4 -> Dense 29 softmax. **2,199,453 parameters**, model file **26.48 MB**.

### Training configuration
Adam, lr 1e-3, batch 32, categorical cross-entropy, split 70/15/15 stratified, seed 42, augmentation (rotation 12 deg, shift 10%, zoom 12%, shear 8%),
EarlyStopping(val_accuracy, patience 6, restore best) + ModelCheckpoint. Defaults in the UI are 25 epochs; the saved run used **30 epochs**.
TensorFlow 2.15 (the pinned version), CPU only.

### Endpoints (all under `/api`)
`GET /health` · `GET /config` · `GET /about` · `GET /dataset` · `GET /dataset/{cls}/images` · `GET /dataset/{cls}/images/{name}` ·
`POST /preview` · `POST /collect/{cls}` · `POST /recognize/session` · `POST /recognize/frame` · `POST /recognize/reload` ·
`POST /tts/speak` · `POST /train/start` · `POST /train/stop` · `GET /train/status` · `GET /model` (+ Swagger at `/docs`).
Validation: epochs 1-500, batch 1-1024, learning rate 1e-6..1, at least 2 classes with images (409), 2,000-character speech limit, image name regex.

### Storage - there is **no SQL database**
Training images live in `data/<CLASS>/*.png|jpg`; the model, `labels.json`, `training_history.json`, `classification_report.txt`
and `confusion_matrix.json` live in `models/`. Recognition sessions are in memory (at most 20). The ER diagram therefore shows the
file-system entities, and the documents say so plainly.

## 3. Dataset

| Item | Value |
|---|---|
| Source | "ASL Alphabet", Kaggle (`grassknoted/asl-alphabet`); the archive on disk has `asl_alphabet_train` and `asl_alphabet_test` |
| Size on disk | 87,000 training images (29 classes x 3,000, 200x200 colour JPEG) + 28 official test images (no `del`) |
| Classes | 29 = A-Z + `space`, `del`, `nothing` |
| Licence | not bundled in the archive; the Kaggle page lists GPL 2 (recalled, re-check before redistributing) |
| Used for training | evenly spaced subset, **250 per class = 7,250 images** (`scripts/prepare_data.py`) |
| Split (seed 42) | train **5,075** · validation **1,087** · test **1,088** (37-38 per class) |
| Load + preprocess time | 75 s for 7,250 images on this machine |

Important caveat (stated in every document): the dataset is frames from video of a few recordings; neighbouring images are
near-duplicates, and no signer identifier is provided. Therefore the test split is **not** an unseen-signer test.

## 4. Measured results (`docs/metrics/metrics.json`)

### Held-out test split (n = 1,088; the 15% never used for training or model selection)
| Metric | Value |
|---|---|
| Accuracy | **82.81%** (0.8281) |
| Test loss | 0.5569 |
| Macro F1 | 0.8302 |
| Weighted F1 | 0.8298 |
| Top-3 accuracy | 92.92% |
| Best classes (F1) | nothing 0.99 · C 0.96 · Q 0.96 · G 0.93 · K 0.93 |
| Weakest classes (F1) | Y 0.62 · V 0.69 · X 0.69 · U 0.70 · W 0.70 · E 0.70 |
| Most frequent confusions | see `docs/metrics/top_confusions.json` (e.g. E to B 7, V to W 7, V to U 6, S to Y 6) |

Reproduced independently by `measure_metrics.py` from the saved model and the same seed: 0.8281 / loss 0.5569 (matches `classification_report.txt`).

### Training run (30 epochs, `models/training_history.json`)
Final train accuracy 0.7291, final validation accuracy 0.8473, best validation accuracy 0.8473 at epoch **30** (the run reached the epoch cap; early stopping did not trigger and
accuracy was still rising). Final train loss 0.8551, validation loss 0.4881. Validation accuracy is above training accuracy because dropout and augmentation act only on the training pass.
The validation loss spiked in the first epochs (peak about 24, BatchNorm warm-up) and settled by epoch 6.

### Other held-out photos (not copied into `data/`; n = 2,900, 100 per class)
Accuracy **87.24%**, macro F1 0.8735, top-3 96.10%. **Caveat:** these come from the same recordings as the training images; neighbouring frames are
near-duplicates of trained frames (training used every 12th image), so this number is optimistic and is *not* used as the headline.
Official Kaggle test photos: **26 of 28** correct (A read as S at 0.675, I read as D at 0.734).

### Confidence threshold (test split)
| Threshold | 0.50 | 0.60 | 0.70 | **0.75** | 0.80 | 0.90 | 0.95 | 0.99 |
|---|---|---|---|---|---|---|---|---|
| Frames accepted | 84.2% | 79.2% | 73.5% | **70.3%** | 67.6% | 59.1% | 48.9% | 31.9% |
| Accuracy on accepted | 92.4% | 94.9% | 96.3% | **97.1%** | 97.7% | 98.3% | 99.3% | 99.7% |

### Robustness (580 photos, 20 per class, accuracy)
clean 85.0% · brightness x0.5 85.3% · brightness x1.5 73.3% · noise s=10 85.3% · noise s=25 83.3% · blur 5x5 85.0% · rotate +10 deg **67.6%** · rotate -10 deg **68.6%**.

### Latency (CPU only: Intel Core i5-12500, 6 cores / 12 threads, 15.7 GB RAM, no GPU; median of 300 frames)
| Stage | median | p95 |
|---|---|---|
| JPEG decode 960x540 | 1.67 ms | 2.01 ms |
| ROI crop + segmentation + normalise | 0.83 ms | 1.30 ms |
| CNN forward, batch 1 (`model.predict`) | 50.35 ms | 55.29 ms |
| Server total per frame | 52.93 ms (about 18.9 fps ceiling) | 57.92 ms |
| HTTP `/recognize/frame` round trip (localhost, one at a time) | 56.70 ms (about 17.6 fps) | 67.61 ms |
| HTTP `/health` | 1.05 ms | 1.27 ms |

Training speed (2-epoch benchmark into a temp folder, `training_speed` in metrics.json): about **9.9 s per epoch** (52.7 s for the whole 2-epoch run including data loading). The saved 30-epoch run's own wall-clock time was not recorded.

### Comparison with the base paper (context only)
MAG-KD is a skeleton-based **video** sign-recognition method (GCN students distilled from multiple GCN teachers), evaluated on AUTSL (94.25% +/- 0.19 Top-1, 0.48 M parameters) and
WLASL-100 (66.33% +/- 0.54), 33.13 FPS and 6.23 W on an NVIDIA Jetson Nano. SignSpeak is a **static-image CNN** for the 26-letter ASL alphabet + 3 control classes
(82.81%, 2.20 M parameters, 17-19 fps on a desktop CPU). Different task (isolated word signs from video vs fingerspelled letters from single frames), data, hardware and
metrics: the numbers are **not directly comparable**, and no claim of superiority is made.

## 5. Tests

| Suite | Result |
|---|---|
| `pytest tests/` (`.venv`, TF 2.15) | **52 passed** in about 4 s: 27 API/integration, 10 preprocessing, 7 recognizer logic, 8 dataset + model |
| `scripts/smoke_test.py` (own temp copy, port 8399, synthetic frames) | **26 / 26 PASS** (validation, collect 80 images, long run stopped at epoch 2, 3-epoch train, model report, recognise, unknown session) |
| `npm run build` (`tsc -b && vite build`) | passes (frontend rebuild, 18 Oct 2026) |
| Browser walk (Playwright + Chromium fake camera fed real ASL photos) | every screen at 360 / 768 / 1440 px, light and dark, reduced-motion at 360 px: console, network and 404 clean; drawer closes with Esc; form validation works (frontend rebuild session) |
| `run.bat` from a fresh shell | brought up API (8316) and web (5316), model loaded |

Not done: unit tests of the React components, load/stress testing, a user study, testing on a physical webcam (only Chromium's fake camera was used), security audit beyond input validation.

## 6. Screenshots (`docs/screenshots/`, 1440x900 unless noted; real app, trained model, 7,250 real images)

| File | Shows |
|---|---|
| `01_landing_dark.png`, `01b_landing_features_dark.png`, `02_landing_light.png` | landing page (dark, features, light) |
| `03_dashboard.png` | dashboard: model ready, 7,250 images, 29/29 classes, 82.8%, images per class, last run |
| `04_recognize.png` | live recognition: letter H at 87%, mask preview, sentence "HELLOH" (fake camera clip of real photos) |
| `05_collect.png` | collection: ROI box, class L, "Captured 5 images for L", mask preview, recent captures |
| `06_train.png`, `06b_train_charts.png` | training: dataset coverage 7,250, hyper-parameters, "Finished" 82.8%, accuracy and loss charts |
| `07_model_per_class.png`, `07b_model_confusion.png`, `07c_model_curves.png` | model performance: per-class table, confusion matrix, training curves |
| `08_about.png` | about: abstract, pipeline, base paper |
| `09_dashboard_light.png`, `10_model_light.png` | light theme |
| `11_mobile_dashboard.png`, `12_mobile_recognize.png` | 390x844 phone layout |

The recognition screenshot uses a clip assembled from real held-out photos fed to Chromium's fake camera (no physical webcam on the build machine);
for each letter the clip uses the first of 12 photos the live model reads correctly at >= 0.8 confidence, so that the demo is legible. The Model screen shows the true accuracy.

## 7. Figures and diagrams (all generated from the code and metrics)

`docs/diagrams/`: 01 system architecture · 02 high-level workflow · 03 DFD 0 · 04 DFD 1 · 05 DFD 2 · 06 UML class · 07 sequence (recognition) · 08 use case ·
09 ER (file store) · 10 core-algorithm flowchart · 11 CNN architecture · 12 training pipeline.
`docs/figures/`: f01 training curves · f02 per-class scores · f03 confusion matrix · f04 top confusions · f05 threshold trade-off · f06 robustness · f07 latency ·
f08 split and class counts · f09 dataset samples · f10 preprocessing stages · f11 failure cases.

## 8. Objectives vs outcome (from `6.OBJECTIVES&PROBLEM STATEMENT.docx`)

| # | Objective | Outcome |
|---|---|---|
| 1 | Dataset covering the sign alphabet **and common words** | Alphabet + 3 control classes: yes (7,250-image working set from the public archive, plus in-app collection). Common words: **not done** (static letters only). |
| 2 | Preprocess with segmentation, resizing, augmentation | Done (Otsu segmentation, 64x64 normalisation, training-time augmentation). Weakness: Otsu does not isolate the hand on cluttered backgrounds (Fig f10). |
| 3 | Design and train a CNN | Done: 3-block CNN, 2.20 M parameters, 82.81% test accuracy. |
| 4 | Optimise for real-time inference | Partly: 17-19 fps end to end on a CPU with no model optimisation (no quantisation / graph export); the CNN call dominates (50 ms via `model.predict`). |
| 5 | Text and synthesised speech | Done: sentence builder + offline pyttsx3 (browser-voice fallback). |
| 6 | Evaluate accuracy, per-class performance, latency **on unseen signers** | Accuracy, per-class P/R/F1, confusion matrix, latency measured. **Unseen signers: not done** (no signer ids; all images from the same recordings). |

## 9. Honest gaps (to be stated, not hidden)

1. No evaluation on unseen signers or new backgrounds. The Otsu masks often contain background structure, so the CNN partly learns the scene; real-world accuracy is expected to be lower.
2. Model trained on 250 of 3,000 available images per class; no hyper-parameter search; no ablation of preprocessing choices.
3. Static letters only - no words, no motion signs (J and Z are read from a single frame), no two-hand or two-way translation.
4. Only a fake camera was used for the end-to-end browser test; the live webcam was not tested on the build machine.
5. No saved wall-clock time for the 30-epoch run (about 9.9 s/epoch measured in a 2-epoch benchmark).
6. Rotation of +/-10 degrees drops accuracy from 85.0% to about 68% - the model is sensitive to hand orientation.
7. The comparison with the base paper is contextual only (different task, data, hardware).
