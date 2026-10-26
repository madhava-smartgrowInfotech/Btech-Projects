# REPORT FACTS - Smart Rider (CSE-A-A6)

Single source of truth for every submission document. Everything below was read from the code or measured on this
machine on 26 Oct 2026. Nothing here is copied from a template or from another project.

## 1. Identity

| Item | Value |
|---|---|
| Batch | CSE-A-A6 (Department of Computer Science and Engineering, section A) |
| Title (academic) | Smart Alcohol Intoxication Detection and Prevention System Using AI |
| Product / code name | **Smart Rider Impairment Warning System for Two-Wheelers** (code, UI and README use this name) |
| Students | B Pranitha 23K91A0522; Bantu Kavya 23K91A0531; Dasari Viveka Sarveshwari 23K91A0560; Bekkam Vamshi 23K91A0534 |
| Guide | N. Padmavathi |
| Base paper | C.-L. Feng and T.-H. S. Li, "Robust Driver State Assessment on an Embedded Platform Using a Fuzzy Belief Rule-Based Fusion of Eye Aspect Ratio and Voice Commands," IEEE Access, vol. 14, pp. 36158-36175, 2026, doi 10.1109/ACCESS.2026.3670924 |
| Unknown (keep `[ ]` placeholders) | college name, HOD, principal, academic year, student emails |
| Ports | backend 8306, frontend 5306 |

## 2. The honest scope gap (must appear in every document)

The batch abstract and objectives promise a **deep-learning sober-vs-intoxicated classifier**, **alcohol detection**
and a **prevention action** (ignition warning / notification to a contact). What exists:

| Batch objective | Status in the delivered system |
|---|---|
| 1. Webcam face + landmarks in real time | **Done.** MediaPipe Face Landmarker, 640x480, ~31 ms per API frame (p50). |
| 2. Impairment cues: eye closure ratio, blink frequency, gaze deviation, head movement | **Partly.** EAR, closure time, closed-eye fraction (10 s), blink rate (display only), image-plane head roll. **Gaze deviation is not measured.** |
| 3. Train a deep-learning sober-vs-intoxicated classifier | **Not done.** No intoxication dataset was available; live decisions are explainable rules. An offline nearest-centroid pipeline exists (`research.py`) but is "Model not trained"; the only report it has produced is from a **synthetic** demo file, flagged as such. |
| 4. Continuous inference, alert above a threshold | **Done** (rule engine, 3 outputs, on-screen warning + optional bell with 15 s cooldown). |
| 5. Prevention action (ignition warning / contact notification) | **Not done.** The app never controls ignition/brakes/power and sends no notification. On-screen warning and bell only. |
| 6. Evaluate accuracy, false-positive rate, low light, partial occlusion | **Partly.** Measured on public CEW eye-state data and on degraded images (section 7). **No intoxication accuracy and no road/rider study exist.** |

**A camera cannot confirm alcohol consumption.** The system outputs *Normal*, *Possible impairment or drowsiness* or
*Unable to assess*. It is a stationary demonstration prototype, not a medical device, not an alcohol test.

## 3. Architecture

Pipeline: `webcam/browser frame -> OpenCV pixels -> MediaPipe Face Landmarker (478 landmarks) + quality gates -> Observation(t, EAR, roll, quality) -> RiskEngine (3-sample median, calibration, rules) -> Decision -> UI + optional bell + SQLite -> history / CSV`.

Two front ends share the same Python modules:
* **Desktop** (original): Tkinter `app.py` (21,202 bytes), background camera thread, 2-item frame queue.
* **Web** (added Oct 2026): FastAPI `backend/` (port 8306) + React 18 / Vite 8 / Tailwind 4 `frontend/` (port 5306). The browser sends 640x480 JPEG frames (`getUserMedia`), the server runs `Vision.process`, returns the annotated JPEG. Frames live in RAM only.

| Module | Role |
|---|---|
| `core.py` | `Settings` (validated bounds), `Observation`, `Decision`, `eye_aspect_ratio`, `head_roll`, `RiskEngine`, `Calibration`, `simulate` (4 scripted scenarios) |
| `vision.py` | `Vision` (MediaPipe Tasks, VIDEO running mode, num_faces=2, confidences 0.7) + 7 quality gates; `CameraWorker` thread |
| `storage.py` | `Store`: SQLite `events` table, CSV export, JSON settings with atomic replace |
| `research.py` | offline CSV validation, 5 s windows, subject-disjoint split, NumPy standardised nearest-centroid, metrics, confusion-matrix PNG |
| `extract_video.py` | offline video -> measurement CSV |
| `backend/main.py` | FastAPI routes, HMAC-token demo login, CORS |
| `backend/session.py` | `RiderSession`: per-tab state mirroring `Application.consume/tick` |
| `backend/content.py`, `synthetic.py` | UI text from the README; seeded synthetic research CSV (6 subjects x 2 labels x 30 s @ 10 Hz) |
| `frontend/src/pages` | Landing, Login, Monitor, History, Thresholds, Research, About, NotFound |

Technology (pinned in `requirements.txt`): Python 3.14.7 (venv), NumPy 2.5.3, opencv-contrib-python 5.0.0.93, MediaPipe 1.0.1, Matplotlib 3.11.2, FastAPI 0.162.0, uvicorn 0.54.0, python-multipart 0.0.32, httpx 0.28.1, Pillow 13.0.0. Frontend: React ^18.3.1, react-router ^7.18.4, @tanstack/react-query ^5.103.2, recharts ^3.10.1, axios ^1.20.0, framer-motion ^14.2.0, gsap ^3.15.0, Tailwind ^4.3.3, Vite ^8.3.0, TypeScript ~5.9.3. Landmark model: Google `face_landmarker.task` float16 (about 3.7 MB, downloaded once by `setup_model.py`, not committed).

### Algorithms and constants (from `core.py` / `vision.py`)

* **EAR** = (|p2-p6| + |p3-p5|) / (2|p1-p4|) per eye, MediaPipe indices left [33,160,158,133,153,144], right [362,385,387,263,373,380]; mean of both eyes; 3-sample median.
* **Closed eye**: smoothed EAR < `ear_threshold` (default **0.21**). Bounds 0.08-0.40.
* **Blink**: completed closed interval 0.08-0.8 s. Blink rate = blinks in last 60 s / observed seconds (cap 60) x 60. Display only; never warns alone.
* **Closed fraction**: time-weighted closed time over the last 10 s (needs >= 8 s of history).
* **Head roll** = atan2(right_eye_y - left_eye_y, |right_eye_x - left_eye_x|) in degrees, outer corners 33 and 263. Image-plane only.
* **Warning rules** (any one starts an evidence timer): closure >= **1.5 s**; closed fraction >= **0.55** with >= 8 s history; |roll| >= **25 deg** with EAR below threshold. Evidence must persist **1.0 s** more with >= 2 s reliable history. Alert bell cooldown **15 s**.
* **Quality gates** (any failure -> *Unable to assess*, evidence cleared): mean gray <40 or >225; Laplacian variance <25; mean abs diff of 96x72 frames >35; no face / >1 face; eye width <14 px or patches outside the image; eye-region mean <35 or >230 or std <8; inter-eye EAR difference >0.12; gap >0.5 s or non-increasing time; EAR outside 0..0.65.
* **Calibration**: 8-15 s, >= 40 accepted frames and >= 70 % accepted (Good, EAR 0.15-0.50, |roll| < 15 deg), EAR std/median <= 0.15; threshold = clip(0.72 x median EAR, 0.12, 0.32).
* **Research classifier** (offline): 5 s non-overlapping windows (>= 20 frames, >= 4.5 s coverage, gaps <= 0.5 s, all Good, one label); features EAR mean/std/min, closed fraction (fixed 0.21), mean |roll|, roll std; standardise on training windows; nearest centroid; metrics per test window.
* Adjustable bounds: EAR 0.08-0.40; closure 0.5-5 s; persistence 0.5-5 s; closed fraction 0.3-0.9; tilt 10-45 deg; cooldown 5-120 s.

### Database (`data/events.sqlite3`, one table, numeric only, no images)

`events(id INTEGER PK, timestamp TEXT (UTC ISO), source TEXT ('LIVE CAMERA' | 'SIMULATION: <scenario>'), state TEXT, quality TEXT, reason TEXT, ear REAL, closure REAL, blink_rate REAL, closed_fraction REAL, roll REAL, alert INTEGER)`. Plus `data/settings.json` (six thresholds + `calibrated` flag) written atomically. The 34-event history shown in the screenshots (31 simulation, 3 live camera) came from the capture run's own database; the repo's `data/events.sqlite3` today holds 14 older rows (a 23 Sep live-camera diagnostic). Caption screenshots as "34 events at the time of capture".

### API endpoints (all under `/api`, FastAPI, interactive docs at `/docs`)

| Method + path | Auth | Purpose |
|---|---|---|
| POST `/auth/login` | - | demo login -> HMAC token (12 h) |
| GET `/auth/me`, `/auth/demo` | token / - | current user; demo credentials hint |
| GET `/health`, `/config`, `/about` | - | status; scenarios, bounds, gates, disclaimers; pipeline/formula text |
| POST `/session` | token | new monitoring session (idle ones dropped after 15 min) |
| GET / DELETE `/session/{id}` | token | snapshot / close |
| POST `/session/{id}/source` | token | camera / simulation (+ scenario) / none |
| POST `/session/{id}/monitoring` | token | start / stop monitoring |
| POST `/session/{id}/calibration` | token | start / cancel calibration |
| POST `/session/{id}/frame` | token | JPEG frame -> state + annotated preview |
| POST `/session/{id}/tick` | token | advance simulation one step |
| GET / PUT `/settings` | token | read / validate+save six thresholds |
| GET `/history`, `/history/export` | token | up to 500 events + summary; CSV download |
| GET `/research`, `/research/sample-csv`, `/research/confusion-matrix` | token | offline report status; synthetic CSV; matrix PNG |
| POST `/research/evaluate` | token | upload CSV + held-out subject IDs |

Demo login: `demo@smartrider.app` / `Demo@1234` (from `.env`). Security: HMAC-SHA256 signed token with expiry, constant-time compare, validated inputs (422), 401 without token, no image persistence, CORS open (local demo only).

## 4. Dataset facts

* **Intoxication data: none.** No dataset of intoxicated vs sober people was available or used. The DIF dataset's source videos are largely gone (per Baroutian et al. 2025); the Mendeley thermal set is a different modality.
* **Closed Eyes in the Wild (CEW)**, Song, Nie, Zhu, Wang, "Eyes closeness detection from still images with multi-scale histograms of principal oriented gradients," Pattern Recognition 47(9):2825-2838, 2014 (download from the NUAA PARNEC page). 2,423 faces: **1,192 both-eyes-closed** (Internet) and **1,231 eyes-open** (from LFW). Used here as the 100x100 warped-face version. Used only to evaluate the EAR component; **not redistributed in the repo** (kept in `C:\ceww`, outside the project).
* **Synthetic research CSV** (`backend/synthetic.py`): seeded generator, 6 subjects, 2 labels, 30 s at 10 Hz; held-out S05, S06; the resulting 100 % precision/recall (12/12 windows per class; 48 train, 24 test windows) is a pipeline check, **not performance** - the UI flags it "Synthetic data".
* Live-camera screenshots use one public-domain face photograph (scikit-image sample astronaut portrait) played as Chromium's fake webcam.

## 5. Tests (re-run 26 Oct 2026, project venv)

| Suite | Result |
|---|---|
| `python -m unittest discover -s tests -v` | **20 / 20 passed** in 0.574 s (EAR geometry & scale, degenerate eyes, roll units, warm-up, outlier suppression, sustained closure + cooldown, quality loss for 4 conditions, timing gap/NaN, blink-rate denominator, tilt needs low EAR, cooldown survives signal loss, 4 simulation scenarios, settings bounds, calibration success/failure, SQLite+CSV+settings, consent validation, subject separation, metric counts) |
| `scripts/smoke_test.py` (web API, temp storage) | **34 / 34 checks passed**: auth, 401, 409 guards, simulation, blank frame -> Poor lighting, garbage frame -> 422, calibration start, history/CSV, threshold validation + persistence, research "Model not trained", bad CSV -> 422, synthetic evaluation flagged, matrix PNG, session close |
| `pip check` (Sep 23 record in `VERIFICATION.md`) | no broken requirements |
| Tk `smoke_test.py`, `camera_check.py` (Sep 23 record) | passed; 81 real webcam frames over a bounded diagnostic, no accuracy claim |

## 6. Hardware used for all measurements

12th Gen Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Intel UHD Graphics 770 (no discrete GPU, no GPU use), Windows 11 Pro, Python 3.14.7, MediaPipe 1.0.1 on CPU (XNNPACK).

## 7. Measured results

All files in `experiments/**/metrics.json`; scripts in `scripts/measure_*.py` (seeded, re-runnable).

### 7.1 EAR eye-state classification on CEW (`experiments/cew_ear/`)

Only the eye-open/closed component is tested, on still images. 2,423 images through the shipped `Vision.process` (100x100 face upscaled to 480x480 on a 640x480 canvas).

**(a) Shipped pipeline with quality gates.** Only **1,068 / 2,423 (44.1 %)** images pass the gates (closed 529 = 44.4 %, open 539 = 43.8 %). Main rejection: "Blurred or hidden eyes" (Laplacian variance < 25: 480 closed, 581 open) because 100 px crops upscaled 4.8x are soft; "Multiple faces" 139 closed / 101 open (spurious second detection). End-to-end accuracy counting every unassessed image as wrong: 41.8 %. This low availability is a property of the low-resolution test images, not of webcam frames.

Among the 1,068 assessed images (threshold 0.21): TP 529, FP 55, FN 0, TN 484 -> accuracy **94.85 %**, precision 90.58 %, recall (closed) 100 %, specificity 89.80 %, F1 95.06 %. ROC **AUC 0.993**. EAR mean +/- sd: closed 0.059 +/- 0.038 (median 0.048), open 0.290 +/- 0.067 (median 0.300).

**(b) Geometry only** (same landmarks and `eye_aspect_ratio`, first detected face, no gates): 2,407 / 2,423 faces found (closed 1,176, open 1,231). Threshold 0.21: TP 1,167, FP 179, FN 9, TN 1,052 -> accuracy **92.19 %**, precision 86.70 %, recall 99.23 %, specificity 85.46 %, F1 92.55 %, **AUC 0.9888**. Mean EAR closed 0.065, open 0.286.

Threshold sweep (geometry only; accuracy / closed recall / open specificity): 0.15 94.8/95.4/94.2; 0.17 **94.7**/97.6/92.0; 0.18 94.6/98.5/91.0; 0.19 94.0/98.8/89.4; 0.20 93.3/99.1/87.7; **0.21 92.2/99.2/85.5**; 0.22 91.2/99.5/83.3; 0.24 88.0/99.7/76.8; 0.26 83.8/99.7/68.6; 0.28 78.8/99.7/58.7. Best in-sample threshold 0.17 (accuracy 94.72 %, recall 97.62 %, specificity 91.96 %; gated variant also 0.17: 96.16 %). **The default 0.21 is conservative: it never misses much but falsely calls about 1 in 7 open eyes closed on this data; a lower threshold (about 0.17-0.18) separates better.** Calibration (0.72 x personal median EAR) addresses this per rider.

Caveats: closed images from the Internet vs open images from LFW (different sources -> separation may be optimistic); still images (no blink dynamics); best threshold chosen in-sample; one dataset; the base paper's NTHU-DDD numbers are not comparable.

### 7.2 Quality gating under degraded conditions (`experiments/cew_ear/`, 272 open-eye faces)

Seeded sample of open-eye faces; baseline 267 / 272 assessed (98.2 %). Share assessed ("Good") and false-closure rate among assessed (EAR < 0.21):

| Condition | Assessed | Unable to assess | False closed among assessed |
|---|---|---|---|
| Baseline | 267 (98.2 %) | 5 | 12.0 % |
| Brightness x0.50 | 1 (0.4 %) | 271 (mostly "Blurred or hidden eyes": gate sees low contrast) | - |
| Brightness x0.25 | 0 | 272 ("Poor lighting" 264) | - |
| Brightness x0.12 | 0 | 272 ("Poor lighting") | - |
| Over-exposed (x1.8 + 25) | 154 (56.6 %) | 118 | 11.7 % |
| Gaussian blur sigma 2 / 5 | 0 / 0 | all | - |
| Gaussian noise sd 20 | 223 (82.0 %) | 49 | 14.8 % |
| Opaque sunglasses over both eyes | 2 (0.7 %) | 270 ("Hidden eyes or poor eye lighting" 257) | 50 % (n = 2) |
| Tinted lenses (55 % dark) | 177 (65.1 %) | 95 | 8.5 % |
| One eye covered | 0 | 272 | - |
| Lower face masked | 236 (86.8 %) | 36 | 12.7 % |

Reading: the gates fail **safe** (no verdict instead of a guess) for darkness, blur, sunglasses and a covered eye, but they are **strict**: halving brightness already blocks assessment, so availability in dim light is poor. Absolute rates depend on the 100 px source images (their Laplacian variance sits near the gate).

### 7.3 Speed (this machine)

* `Vision.process` on 640x480 canvases, 2,423 images: mean 12.1 ms, p50 13.1 ms, p95 26.9 ms, max 75.8 ms (includes landmarking; CPU only).
* HTTP on 127.0.0.1 (`experiments/api_latency/`): `/health` p50 2.6 ms; simulation tick p50 2.3 ms; **POST frame with a real face JPEG (21,350 bytes): mean 32.8 ms, p50 31.2 ms, p95 47.8 ms, max 56.1 ms (n = 150)** -> about 30 frames/s sustainable on one core path; `/history` (limit 500) p50 3.6 ms; starting the camera source (model load) 939 ms; login 2.2 ms.
* `RiskEngine.update`: 40.6 microseconds per observation (200,000 updates).
* Base paper reports 25 FPS on a Jetson Orin Nano; this project reaches about 30 frames/s on a laptop CPU for the vision path (different hardware, different pipeline).

### 7.4 Rule-engine behaviour on SCRIPTED streams (`experiments/rule_engine/`)

Generated streams (seeded), not recordings of people. Open EAR ~ N(0.30, 0.012); closed 0.12.

* **Closure length vs warning** (defaults, 30 runs each, 10 / 15 / 30 frames/s): closures of 0.5, 1.0, 1.5, 2.0 and 2.4 s never warn (0/30); closures of 2.6, 3, 4 and 6 s always warn (30/30). Warning latency from closure onset: 2.60 s at 10 and 15 frames/s, 2.53 s at 30 (1.5 s closure rule + 1.0 s persistence, plus median-filter lag). So **the minimum closure that warns is about 2.5 s**.
* **False warnings on blink streams** (300 sessions x 180 s at 15 frames/s each): normal blinks 17/min (0.1-0.4 s): 0 sessions warned (0.0 alerts/h); 35/min: 0; noisy EAR sd 0.04: 0; 5 % slow blinks (0.8-1.3 s): 0; 20 % slow blinks: 3 / 300 sessions, 0.2 alerts/h.
* **Parameter sweep** (closure x persistence; detection of a 3 s closure; alerts/h with 10 % slow blinks): (1.0, 0.5) 100 % / 3.0; (1.0, 1.0) 100 % / 0.33; (1.5, 0.5) 100 % / 0.33; **(1.5, 1.0) default 100 % / 0.0**; (2.0, 0.5) 100 % / 0.0; (2.0, 1.0) 0 % / 0.0; any setting with closure + persistence > 3 s misses a 3 s closure (e.g. (1.5, 2.0), (3.0, any)).
* **Other rules**: closed-fraction rule (0.9 s closures every 1.5 s, 60 % closed) warns 10.1 s after onset ("Closed-eye fraction 63 % over 10.0 s"); tilt rule (roll 30 deg + EAR 0.19) warns 1.07 s after onset; tilt alone never warns; first *Normal* after start at 2.0 s; after signal loss first *Normal* again after 2.13 s.

### 7.5 What was NOT measured (state as gaps)

* Any accuracy for alcohol / intoxication; sober-vs-intoxicated classification; deep learning (none was trained).
* Any study with riders, helmets, visors, glasses, vibration, night riding, or demographic robustness.
* Gaze deviation; ignition/contact prevention action (not implemented).
* A real labelled consented dataset through `research.py` (only the synthetic demo file, flagged).
* Audible-bell loudness; variable-frame-rate video extraction accuracy; long-duration (hours) false-alarm rate on real people.

## 8. Comparison with the base paper (Feng and Li, 2026) - state plainly where it differs

| Aspect | Base paper | This project |
|---|---|---|
| Target state | drowsiness, fatigue, distraction | drowsiness-type impairment indicator; **not** alcohol |
| Eye feature | EAR-4 (four upper-lid points) vs six-point EAR | conventional six-point EAR |
| Decision | Fuzzy Belief Rule-Based inference fusing EAR, head pose, voice | transparent if-then duration rules (EAR, closed fraction, roll) |
| Voice | Whisper-tiny wake words/commands | none |
| Calibration | personalised adaptive threshold from > 300 frames | 8-15 s, threshold = 0.72 x median EAR |
| Data | NTHU-DDD: 4 subjects, 65,834 frames (29,804 open / 36,030 closed), 80/20 split; RF and XGBoost | CEW 2,423 still faces for the EAR component; no rider dataset |
| Reported eye-state metric | EAR-4 recall 0.894, F1 0.845 (Subject 2, Random Forest; six-point EAR 0.856 / 0.813) | six-point EAR threshold: recall 0.992, specificity 0.855, F1 0.926 (CEW, threshold 0.21, geometry only) - **different datasets, not comparable** |
| Hardware / speed | Jetson Orin Nano 8 GB, 25 FPS | laptop i5-12500 CPU, ~30 frames/s through the API (31 ms p50) |

## 9. Screenshot inventory (`docs/screenshots/`, 1440x900 unless noted; real captures of the running app)

Captured 24 Oct 2026 with `scripts/capture_screens.py` (Playwright). Data in them: 34 logged events (31 simulation, 3 camera) and the synthetic research report (flagged on screen).

| File | Shows |
|---|---|
| 01_landing_dark / 02_landing_light | landing page, dark and light themes |
| 03_login | sign-in page with demo account hint |
| 04_monitor_simulation_warning | simulation "Prolonged eye closure" raising *Possible impairment or drowsiness* with reason |
| 05_monitor_calibrating | camera calibration in progress |
| 06_monitor_camera_normal | live camera path on a real face: landmarks drawn on eyes, *Normal*, EAR 0.254, calibrated threshold 0.183 |
| 07_monitor_idle | monitor before a source is chosen |
| 08_history | event history: 34 events, EAR chart live vs simulation, filters |
| 09_thresholds_validation / 10_thresholds | threshold form with a validation error / saved values |
| 11_research_empty | research screen, "Model not trained" |
| 12_research_report | synthetic-data evaluation report (confusion matrix 12/0/0/12) with the "Synthetic data" banner |
| 13_about / 14_about_formulas | pipeline, formulas, limitations |
| 15_monitor_light | monitor in the light theme |
| mobile_landing / mobile_monitor / mobile_history / mobile_research | 360 px wide layouts |

Use 06 and 04 for the "output screens"; always caption 12 as synthetic.

## 10. Figures produced (`experiments/**.png`)

`cew_ear/ear_histogram.png`, `threshold_sweep.png`, `roc.png`, `robustness.png`; `rule_engine/closure_vs_warning.png`, `parameter_tradeoff.png`. Architecture/DFD/UML/ER/sequence/use-case/flowchart diagrams go to `docs/diagrams/` in Step 2.

## 11. Literature (verified from supplied PDFs; others need web verification before citing numbers)

* Feng and Li 2026 (base): abstract claims EAR-4 recall 89.4 %, adaptive threshold from > 300 frames, Jetson Orin Nano 8 GB, 25 FPS; NTHU-DDD figures in section 8.
* Baroutian, Aghaei, Moghaddam, "Detection of Intoxicated Individuals from Facial Video Sequences via a Recurrent Fusion Model," arXiv:2512.04536, Dec 2025: GAT on landmarks + 3D ResNet, 202 individuals, 3,542 video segments, **95.82 % accuracy, 0.977 precision, 0.97 recall**, baselines 3D-CNN and VGGFace+LSTM.
* Deuber et al., "Detecting Drunk Driving Using Off-the-Shelf Smartwatches," arXiv:2605.23663, May 2026 (under review at ACM): wrist accelerometer + HRV, three-arm randomised test-track study N = 54, CNN participant-averaged **AUROC 0.88** (any alcohol) and **0.86** (above 0.05 g/dL).
* Batch literature survey items 2-5 (infrared deep-learning drunk detection 2024; AHFE IHSED2026 testing methodology; ICOEI 2026 alcohol detection + immobilisation for taxis; thermal facial images, Information 2025): titles only in the batch file - verify on the web before quoting any result; never invent numbers.
* Song et al. 2014 (CEW dataset); MediaPipe Face Landmarker guide (Google AI Edge).

## 12. Measurement caveats added after the first write-up

* **Run-to-run variation from tracking.** `Vision` runs MediaPipe in VIDEO mode, which tracks across consecutive frames. Feeding unrelated still images through it means the result for an image can depend on the previous image. Evidence: of 272 open-eye faces that were assessed in the first pass, 267 were assessed again in the baseline row of the robustness experiment (5 flipped to "Multiple faces"). Treat all CEW coverage figures as accurate to roughly +/- 2 percentage points, and the geometry-only numbers (which also use VIDEO mode) the same way.
* The sample of 272 (not 300) is the number of images for which a face box was found in the localisation step.
* Landmark figure `docs/figures/landmark_examples.png` shows only images that were assessed in the figure run itself.
* Figures available in `docs/figures/`: `ear_histogram.png`, `threshold_sweep.png`, `roc.png` (gated pipeline, 1,068 assessed images), `robustness.png`, `landmark_examples.png`, `api_latency.png`, `closure_vs_warning.png`, `parameter_tradeoff.png`.
* Reference numbering is fixed in `scripts/docs/refs.py` (30 entries; cite as `n(1, 9)`).
