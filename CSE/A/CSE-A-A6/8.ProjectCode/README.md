# Smart Rider Impairment Warning System for Two-Wheelers

A Python-only Windows desktop **stationary demonstration prototype**. It estimates possible drowsiness or impairment from visible eye and head observations. **A camera cannot confirm alcohol consumption.** Normal does not mean fit to ride. This is not a medical device, alcohol test, or road-ready safety system. It never controls ignition, brakes or vehicle power.

The existing expense tracker in the parent directory is preserved. The desktop application itself uses no HTML, JavaScript, CSS or server. An optional **web interface** (FastAPI in `backend/`, React in `frontend/`, started by `run.bat`) wraps the same `core`, `vision`, `storage` and `research` modules; see `docs/03_HOW_TO_RUN.md`.

## Installation and launch (Windows PowerShell)

Tested with 64-bit Python 3.14.6. Install Python with Tcl/Tk support. Run:

```powershell
Set-Location 'D:\kavya\project\my_project\expense_tracker\smart_rider'
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe setup_model.py
.\.venv\Scripts\python.exe app.py
```

No environment activation or PowerShell execution-policy change is needed. `opencv-contrib-python` provides OpenCV (`cv2`) and is required by this MediaPipe version; do not install a second OpenCV wheel in the same environment. Tkinter, SQLite and unittest come with Python. Matplotlib installs its own required supporting packages. Internet is needed for initial package/model downloads; normal operation is local.

Launch directly from the original parent workspace with this single command:

```powershell
.\smart_rider\.venv\Scripts\python.exe .\smart_rider\app.py
```

Simulation does not require a webcam or downloaded landmark model:

```powershell
.\.venv\Scripts\python.exe app.py --simulation
```

## Live demonstration and every control

1. Secure the laptop/camera while stationary. Face the rider, place both eyes fully in view, and use diffuse front lighting. Any two-wheeler mounting must avoid obstructing vision or controls. This laptop prototype is for stationary demonstration only.
2. Choose camera index 0 (try another index if necessary), then **Start Camera**. Enable Windows Settings > Privacy & security > Camera > desktop app access. Close other applications holding the webcam.
3. Remove dark/reflective eyewear. Helmet use is supported only with both eyes visible; a visor, shadows or camera geometry may prevent assessment. Read the displayed quality status.
4. Select **Calibrate**. Keep eyes naturally open, look forward with little head tilt, and remain still. The progress bar represents the initial 8-second collection period; collection may continue to 15 seconds to obtain usable data. On success the personalized EAR threshold is saved. On failure the previous valid threshold (or 0.21 default) is retained; improve conditions and recalibrate. Monitoring is stopped during calibration. Simulation cannot write rider calibration.
5. Select **Start Monitoring**. Two seconds of continuous good observations are required before Normal can appear. The three outputs are **Normal**, **Possible impairment or drowsiness**, and **Unable to assess**. The reason and contributing measurements appear beside the preview. Signal loss clears evidence and restarts warmup.
6. **Stop Monitoring** stops assessment and logging apart from a final stop event, retaining the preview. **Stop Camera** ends the source and releases the device. Closing the window also releases the camera and SQLite connection. Native camera-driver hangs can delay shutdown; the app waits for cleanup without blocking Tk's event loop.
7. **Simulation Mode** releases an active camera and switches to scripted measurements. Select a scenario using the dropdown. Start Monitoring to log the demonstration.
8. **History** shows up to 500 recent event rows and an EAR chart with distinct live/simulation series. These are sparse event samples, not raw video or a continuous physiological recording. Timestamps are UTC. Scroll the table horizontally and vertically with its scrollbar / mouse wheel.
9. **Export CSV** exports all event rows, including source, UTC timestamp, quality, reasons and measurements; the file dialog asks before overwriting existing files.
10. **Thresholds** validates and saves adjustable baseline thresholds. Saving stops monitoring and clears calibration status; restart monitoring after review. **Optional alert sound** uses Tk's system bell; actual audibility depends on Windows sound settings. On-screen warnings remain visible throughout the warning state, while sound is rate limited.
11. **Research / Evaluation** accepts a consented measurement CSV and explicit held-out subject IDs. Its trained classifier is offline only; it never replaces live rules.

## College-review simulation script

All scenarios are visibly marked **SIMULATION**, including stored source fields. These are deterministic software demonstrations, not trained model predictions or research validation.

| Scenario | Demonstration |
|---|---|
| Normal | Start monitoring; after roughly 2 seconds of warmup show Normal and periodic short blinks. |
| Prolonged eye closure | Open eyes for 3 seconds, then low EAR. A warning normally appears around 6 seconds after monitoring starts. Show the closure duration and persistence explanation. |
| Missing face | Immediately Unable to assess, without an impairment prediction. |
| Poor lighting | Immediately Unable to assess, with the poor-lighting reason. |

Changing scenarios resets evidence while retaining whether monitoring was active. Show History and export the labeled rows. The normal fallback threshold is intended for demonstration; changing thresholds may change timing. Camera calibration requires a real rider and is not simulated.

## Processing flow and modules

`camera -> OpenCV pixels -> MediaPipe landmarks + quality checks -> Observation -> calibration / rolling feature calculations -> explainable rules -> Tk display, optional bell, SQLite -> history / CSV`.

The camera and MediaPipe run on a background thread. A two-item queue drops old frames instead of building latency. Tk updates and SQLite writes stay on the UI thread. Research training has its own background worker. A stale-frame watchdog invalidates stalled camera observations. Video frames exist only in RAM.

| File | Responsibility |
|---|---|
| `app.py` | Tkinter UI, connected controls, preview, calibration progress, monitoring lifecycle, source labeling, alerts, history charts, settings and research dialogs. |
| `core.py` | Independent feature formulas, time windows, quality gates, calibration, threshold validation, sustained rule decisions and scripted scenarios. |
| `vision.py` | OpenCV webcam, MediaPipe Tasks Face Landmarker, eye geometry, head roll and image reliability heuristics; worker cleanup. |
| `storage.py` | SQLite numeric events, CSV export, validated settings and atomic JSON replacement. |
| `research.py` | CSV validation, feature-window extraction, subject separation, NumPy nearest-centroid training and held-out metrics/artifacts. |
| `extract_video.py` | Optional offline feature extraction from existing consented, labeled video clips, without copying frames. |
| `setup_model.py` | Explicit one-time download of Google's official face-landmark model; prints its SHA-256. |
| `tests/test_system.py` | Automated feature, temporal rule, calibration, settings, event export and research pipeline tests. |
| `smoke_test.py` | Desktop integration checks with temporary storage; verifies preview, warning display, dialogs/chart, export and exit. |
| `camera_check.py` | Bounded real webcam diagnostic and model initialization/inference checks; saves no frames. |
| `requirements.txt` | Pinned primary dependencies tested on this machine. |
| `VERIFICATION.md` | Actual environment and check results, with untested limitations. |
| `.gitignore` | Excludes environment, local measurements, downloaded model and research outputs. |

Runtime files: `data/events.sqlite3`, `data/settings.json` after a successful calibration/settings save, `models/face_landmarker.task`, and optional `research_results/`. These contain potentially sensitive numerical event history: keep local access restricted and retain only as long as needed. Deleting `data` while the application is closed clears local history/settings. No external telemetry or image uploads are implemented.

## Formulas, units and experimental defaults

- **EAR** for six eye perimeter points: `(distance(p2,p6) + distance(p3,p5)) / (2 * distance(p1,p4))`. Pixel coordinates preserve image aspect ratio. Dimensionless; calculate each eye and average. MediaPipe indices: left `[33,160,158,133,153,144]`, right `[362,385,387,263,373,380]`. A 3-sample median suppresses isolated outliers (latency depends on frame rate).
- **Closed eye**: smoothed EAR below `ear_threshold` (default **0.21**). This is an engineering heuristic, not a validated clinical cutoff.
- **Closure duration**: elapsed monotonic seconds since continuous low EAR began. Reopening or quality loss resets it.
- **Blink**: a completed low-EAR interval lasting **0.08-0.8 s**, followed by reopening. **Blink rate**: completed blinks during the most recent 60 seconds divided by available uninterrupted good-signal observation seconds (capped at 60), multiplied by 60. Early rates are unstable; blink rate is displayed but not independently used to warn.
- **Closed fraction**: time-weighted low-EAR duration / reliable observed duration within the last **10 s**. It is a short-window closed-eye fraction, not a validated clinical PERCLOS measurement. It uses intervals between observations; irregular frame rates do not multiply votes.
- **Head roll**: `atan2(right_eye_y-left_eye_y, abs(right_eye_x-left_eye_x))` converted to degrees, using outer eye corners 33 and 263. This measures image-plane tilt, not full 3D yaw/pitch or gaze. Camera tilt affects it.
- **Calibration**: collect 8-15 seconds, at least 40 accepted frames and >=70% accepted observations. Accept Good quality, EAR 0.15-0.50 and absolute roll <15 degrees; require EAR standard deviation / median <=0.15. Set threshold to `clip(0.72 * median_EAR, 0.12, 0.32)`. Eyes must be naturally open: calibration cannot independently certify the rider's normal alertness.
- **Quality gates**: frame mean grayscale below 40 or above 225 (0-255 scale); Laplacian variance below 25; mean absolute difference of 96x72 consecutive grayscale frames above 35; no face or multiple faces; eye width below 14 pixels; eye patches outside image; eye-region mean below 35 or above 230 or standard deviation below 8; inter-eye EAR difference above 0.12. Detector/presence/tracking confidence thresholds are 0.7. These are heuristic reliability checks, not proven occlusion detection. Blank/dark visors often fail them, but patterned occlusions or inferred hidden landmarks can pass. Do not rely on assessment with covered eyes.
- A non-increasing timestamp or >0.5-second sample gap invalidates evidence. UI frames older than 0.5 seconds are stale; no output for one second produces Unable to assess.

Any of the following can start an evidence timer: closure >= **1.5 s**; closed fraction >= **0.55** with >=8 s available; or absolute roll >= **25 degrees** together with low EAR. Evidence must then persist for **1 additional second**, with at least 2 s of reliable history, before warning. Quality failures always take precedence. A warning says to stop somewhere safe. Optional bell cooldown is **15 s** and is preserved through quality interruptions; explicitly restarting monitoring begins a new session. Normal returns when the rule conditions clear (the closure-fraction window can keep a warning active).

Adjustable bounds: EAR 0.08-0.40; closure 0.5-5 s; persistence 0.5-5 s; closed fraction 0.3-0.9; tilt 10-45 degrees; cooldown 5-120 s. Defaults and bounds are demonstration choices, not measured safety specifications.

## Consented research dataset and evaluation

Without a suitable real dataset the status is **Model not trained**. No participant dataset, research accuracy value or production impairment classifier is bundled. Synthetic fixtures exist solely inside software tests and are deleted from temporary directories after use. Simulation events must never be used as evidence of research performance.

Acceptable input is a UTF-8 CSV, one row per measured video frame, with these exact columns:

```text
subject_id,session_id,timestamp_s,ear,roll_deg,quality,label,consent
```

Use pseudonymous subject IDs; **the same person must keep the same ID across all sessions**. Timestamps are seconds within the session, strictly increasing and nonnegative. EAR is 0-0.65 and roll is -90 to 90 degrees. Quality is `Good` for usable measurements (other quality strings exclude the containing window). Labels are `normal` or `possible_impairment`; labels must come from a documented independent study protocol, not the app's own rules or assumptions about alcohol. `consent` must be `yes` on every row, backed by actual consent documentation held separately. CSV consent flags cannot verify real consent. Use >=2 subjects with both classes represented in the training group and the held-out group; scientifically meaningful studies need substantially more participants and balanced conditions.

The CSV is the dataset format; no fixed video folder layout is required. Optional extraction for a clip whose whole duration has one independently established label:

```powershell
.\.venv\Scripts\python.exe extract_video.py 'D:\consented_study\clip.mp4' 'D:\consented_study\clip_frames.csv' --subject S01 --session session01 --label normal --consent
```

The extractor requires the model, reads existing video only, preserves quality flags, and refuses to overwrite output. Use constant-frame-rate recordings with reliable FPS metadata; timestamps are frame index / FPS. Split clips at label changes and use distinct session IDs. Combine extracted CSVs with one header using Python's csv module or a spreadsheet, preserving identities and timestamps. Review output quality; do not change failed measurements to Good to force training.

Evaluation extracts nonoverlapping **5-second** windows per subject/session, requiring >=20 frames, >=4.5 seconds coverage, <=0.5-second gaps, all Good quality and one label. It rejects duplicate timestamps, missing consent, invalid values and unsuitable splits. Incomplete/mixed/poor-quality windows are counted as excluded. Features are EAR mean, standard deviation, minimum, time-weighted closed fraction using fixed 0.21 threshold, mean absolute roll and roll standard deviation. The first valid frame anchors the window bins. Exclusions can bias results toward easy conditions: always report them.

Choose held-out subjects before inspecting outcomes. Supply their IDs to the UI or CLI:

```powershell
.\.venv\Scripts\python.exe research.py 'D:\consented_study\measurements.csv' --test-subjects S05 S06 --output research_results
```

Subject membership exclusively defines the split; no subject appears in both sets. Feature standardization and class centroids are fitted on training windows only. The simple classifier assigns the nearest standardized Euclidean class centroid. Never repeatedly tune thresholds against the same test subjects; use separate training-only validation subjects for model selection. This implementation does not claim model optimality.

Outputs: `report.json`, `centroid_model.npz`, `window_features.csv` with split labels, and `confusion_matrix.png`. Matrix rows are true labels, columns predicted labels, ordered normal/possible_impairment. Positive-class precision=TP/(TP+FP), recall=TP/(TP+FN), F1=2TP/(2TP+FP+FN), and false-alarm rate=FP/(FP+TN) **per test window**, not alarms per hour. Undefined ratios are JSON null. The report records subjects, window counts, exclusions and input SHA-256. Metrics are descriptive of that held-out dataset, without confidence intervals or road-safety claims. No model is automatically loaded into the live baseline.

## Research inspiration and distinction

Feng and Li (2026), *Robust Driver State Assessment on an Embedded Platform Using a Fuzzy Belief Rule-Based Fusion of Eye Aspect Ratio and Voice Commands*, IEEE Access 14, 36158-36175, [DOI 10.1109/ACCESS.2026.3670924](https://doi.org/10.1109/ACCESS.2026.3670924). The [authors' institutional abstract](https://researchoutput.ncku.edu.tw/zh/publications/robust-driver-state-assessment-on-an-embedded-platform-using-a-fu/) describes camera/microphone fusion for drowsiness, fatigue and distraction on embedded hardware. This application borrows the general idea of combining observable signals and personal calibration. It does **not** reproduce their EAR4, voice interface, fuzzy belief rule engine, embedded deployment or measured results. It uses conventional six-point EAR, image-plane roll and transparent duration rules in a two-wheeler stationary prototype. Its proposed possible-impairment warning is not an alcohol detector. No paper accuracy is attributed to this application.

Face landmarks follow the official [MediaPipe Face Landmarker Python guide](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python). Download source: `https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task`. The landmark model estimates geometry; it is not a trained impairment classifier. Review Google's model documentation/licensing for redistribution.

## Verification and limitations

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe smoke_test.py
.\.venv\Scripts\python.exe camera_check.py
.\.venv\Scripts\python.exe -m pip check
```

The desktop smoke test opens temporary test windows and uses temporary storage. The camera diagnostic briefly opens the webcam and saves no imagery. See `VERIFICATION.md` for results actually observed on the development machine.

Limitations include visible-eye requirements, helmets/visors/glasses, skin/lighting variation, blur, vibration, dropped frames, subtle occlusion missed by heuristics, camera-relative head tilt, false alerts and missed events. Closed eyes and low EAR have many explanations; open eyes do not establish alertness. Head roll is not full head pose. Calibration may be wrong if the rider is already fatigued. The prototype has no validated demographic robustness, sensitivity, specificity or safety assurance. A laptop display and sound may be unsuitable for real riding. Use stationary review demonstrations only. No camera-only observation establishes alcohol use or confirms impairment.
