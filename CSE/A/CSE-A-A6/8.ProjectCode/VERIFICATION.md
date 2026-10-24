# Verification record

Executed on 23 September 2026 on the available Windows laptop, using the dedicated `.venv` and Python 3.14.6.

- Installed pinned NumPy 2.5.3, OpenCV contrib 5.0.0.93, MediaPipe 1.0.1 and Matplotlib 3.11.2. Removed the duplicate base OpenCV wheel so only contrib owns cv2.
- `python -m pip check`: passed, no broken requirements.
- `python -m unittest discover -s tests -v`: all 20 tests passed. Covers EAR geometry/scale, invalid geometry, roll units, warmup, isolated outliers, sustained closure, quality loss, invalid timing/NaN, blink-rate duration, combined tilt/eye evidence, alert cooldown, all four scenarios, settings validation, calibration success/failure, SQLite/CSV/settings, consent validation, subject separation and known metric counts.
- `python smoke_test.py`: passed. Real Tk widgets and Matplotlib chart, memory-only preview image, scripted warning/unavailable states, simulation controls, calibration refusal in simulation, history, threshold saving, research dialog, CSV export, stop and clean exit; temporary data only.
- `python camera_check.py`: passed model initialization, actual no-face inference on a non-face test frame, dark-frame gating, and camera worker cleanup. Captured 81 real webcam frames over the bounded diagnostic with no capture exception. Observed quality labels included Good, No face, small/out-of-view eyes, hidden/poorly-lit eyes and unreliable geometry. These observations are not evidence of detection accuracy. No images were saved.
- Live Tk button check: passed Start Camera, actual rendered webcam preview, Calibrate initiation, Stop Camera, worker release and clean exit. An initial diagnostic assumed a preview within 5 seconds and failed; the repeated check allowed up to 25 seconds and guaranteed cleanup. Its preview was dark/Unable to assess. The leftover failed test processes were stopped. This was a test timing assumption, not a claim of reliable face assessment.
- `python research.py` with no dataset: correctly reported Model not trained.
- Offline classifier/window extraction/artifact production tested only using explicitly synthetic temporary unit fixtures. Their metrics were not retained as research results.
- Source compilation passed for application, tools and tests.

Not established: scientific performance, real labeled-dataset evaluation, a complete successful real-rider calibration, controlled helmet/visor/lighting/vibration performance, audible system-bell output, variable-frame-rate research-video extraction accuracy, road readiness or alcohol detection. Webcam availability, frame rate and signal quality depend on hardware and scene. The software tests validate behavior, not medical or road-safety claims.

The desktop app is launched separately for interactive review after verification. The live application remains rule based. No consented training dataset is bundled.
