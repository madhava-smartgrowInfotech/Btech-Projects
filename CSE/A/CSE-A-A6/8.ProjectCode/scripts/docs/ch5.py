"""Chapter 5: System design. The diagram explanations are shared with '11. BLOCK DIAGRAMS ALL.docx'."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

# (key, section title, file, caption, explanation)
DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png", "System architecture of the Smart Rider impairment warning system",
     "The architecture has four columns. The client tier holds the two ways to reach the system: the React single-page application (Vite and TypeScript, port 5306), which opens the "
     "rider's webcam with the browser's `getUserMedia` and sends 640 x 480 JPEG frames, and the original Tkinter desktop application `app.py`, which reads the webcam itself through "
     "a `CameraWorker` thread (OpenCV with DirectShow). The application tier is the FastAPI service `backend/main.py` (port 8306), which checks an HMAC-signed demo token and validates "
     "inputs, and `backend/session.py`, whose `RiderSession` keeps the source, calibration and monitoring state of one browser tab and is driven by its `frame()` and `tick()` methods. "
     "The third column is the shared Python modules, used by both front ends without any HTTP between them: `vision.py` (MediaPipe Face Landmarker, seven pixel and geometry quality "
     "gates, EAR and head roll), `core.py` (`RiskEngine`, `Calibration`, `Settings` and the scripted scenarios) and `storage.py` (SQLite and JSON), plus the offline `research.py`. "
     "The data tier holds the landmark model file (loaded once), `data/events.sqlite3` (table `events`), `data/settings.json` and `research_results/`. Because both front ends use the "
     "same modules they write to the same event file. Video frames exist only in memory; only numeric events are stored."),
    ("flow", "High-level workflow", "02_high_level_workflow.png", "High-level workflow of a monitoring session",
     "A session has eight steps. (1) Sign in with the demo account and receive a signed token valid for 12 hours. (2) Choose the source: the webcam, or Simulation with four "
     "scripted scenarios. (3) Calibrate, which applies to the camera only and is optional: with eyes open for 8 to 15 seconds the threshold is set to 0.72 times the median EAR; "
     "without it the default 0.21 is used, and simulation cannot write a calibration. (4) Monitor: each frame becomes an observation, passes the quality gates and is judged by the "
     "`RiskEngine`. (5) The verdict is one of Normal, Possible impairment or drowsiness, and Unable to assess. (6) A numeric event row is logged when the state changes, every five "
     "seconds, or when an alert fires. (7) The user reviews the history table, the EAR chart and the CSV export. (8) The user can tune the thresholds or run the offline "
     "evaluation, which never alters the live rules. The note on the diagram states the safety rule: a frame that fails a quality gate gives Unable to assess and clears the "
     "evidence, so the system never guesses."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png", "Data flow diagram, level 0 (context diagram)",
     "The context diagram shows the system as one process with three external entities. The rider or demonstrator sends credentials, the source choice, thresholds and the "
     "calibrate, start and stop commands, and receives the verdict, the reason, the warning and the measurements, and the history. The webcam supplies video frames, which are "
     "kept in memory only. The reviewer or researcher supplies a labelled, consented measurement CSV and the held-out subject IDs and receives the event history, the CSV export "
     "and the evaluation report. The note on the diagram repeats the central limit: the verdict is a possible-impairment or drowsiness indicator, not an alcohol result."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png", "Data flow diagram, level 1",
     "Level 1 has seven processes and three data stores. Authenticate (1) exchanges the email and password for a signed demo token. Capture and validate frame (2) takes the video "
     "frame from the webcam and passes on only a valid frame. Extract observation (3) turns it into an observation (time, EAR, roll, quality). Assess risk (4), the rule engine, "
     "turns observations and the thresholds read from the settings file (D2) into a decision, which goes to the rider and to Log and export events (5); process 5 writes event rows "
     "to the event database (D1), reads them back for the history and sends the history and the CSV export to the rider. Settings, calibration and session control (6) receives "
     "the rider's thresholds, source choice and calibrate, start and stop commands and the calibration observations, and writes validated settings to D2. Offline research evaluation "
     "(7) takes the reviewer's consented CSV and held-out IDs and writes the report, the model parameters and the confusion matrix to the research output folder (D3), "
     "returning the evaluation report to the reviewer."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png", "Data flow diagram, level 2: processes 3 and 4 in detail",
     "Level 2 expands extraction and the rule engine. A frame (BGR, 640 x 480) first meets the quality gates (3.1): seven checks on light, blur, motion, face count, eye size, "
     "eye patch and eye geometry. A frame that fails any gate ends in Unable to assess with the reason equal to the quality label and the evidence cleared; a frame that passes "
     "goes to the EAR and head-roll computation (3.2) and then to the 3-sample median (3.3). The smoothed EAR, the roll and the time then feed three parallel rule checks: the "
     "closure timer and blink counter (4.1), the closed fraction over 10 seconds (4.2) and head tilt combined with a low EAR (4.3). Their outputs, closure seconds, the fraction "
     "and the tilt-and-closed flag, go to the persistence check (4.4), which decides the warning state, and then to the alert cooldown (4.5), which sets the alert flag. The "
     "output is the decision with state, reason, measurements and alert. The settings file D2 supplies every limit; a failed gate resets processes 4.1 to 4.5 but keeps the "
     "cooldown clock."),
    ("uml", "UML class diagram", "06_uml_class_diagram.png", "UML class diagram (core, vision, storage and web session)",
     "The diagram draws the classes that carry the design. In `core.py`, `Settings` is a dataclass of the six thresholds and the `calibrated` flag with a `validate` method; "
     "`Observation` is one measurement (time, EAR, roll, quality, brightness, sharpness); `Decision` is the rule engine's answer (state, reason, quality, EAR, closure, blink rate, "
     "closed fraction, roll, alert). `RiskEngine` keeps the sample window, blinks and the closure and evidence timers, owns one `Settings` and returns a `Decision` from `update`; "
     "`Calibration` collects open-eye EAR values and returns a threshold or raises an error. `Vision` wraps the MediaPipe `FaceLandmarker` and creates `Observation` objects, and "
     "`CameraWorker` is the thread that runs it for the desktop app. `Store` writes events and settings. `Application` (Tkinter) and `RiderSession` (web) are two front ends over the "
     "same classes; each owns a `Store`, a `RiskEngine` and a `Calibration`, and `RiderSession` raises `SessionError` for user-facing failures. `Store` opens a fresh SQLite "
     "connection for each web call because connections are bound to their thread."),
    ("seq", "Sequence diagram", "07_sequence_diagram.png", "Sequence diagram: one camera frame (POST /api/session/{id}/frame)",
     "The sequence follows one camera frame between six participants: the browser, the FastAPI service, the `RiderSession`, `Vision`, `RiskEngine` and `Store`. The browser posts the "
     "JPEG with the bearer token. FastAPI verifies the HMAC token in `current_user` and calls `frame(data)` on the session. The session decodes the bytes with `cv2.imdecode` and "
     "resizes the image to 640 x 480, then calls `Vision.process(image, now)`, which applies the seven quality gates, runs the Face Landmarker and returns an `Observation` "
     "(time, EAR, roll, quality). `consume(o)` takes either the calibration step or the monitoring branch; while monitoring, `RiskEngine.update(o)` applies the median filter, "
     "timers, window, rules, persistence and cooldown and returns a `Decision`. If the state changed, five seconds have passed or an alert fired, `Store.add` writes the event row. "
     "The session returns the annotated JPEG bytes and the snapshot, and the API answers 200 with JSON containing the state, the reason, the metrics and the preview as a data URI. "
     "The note on the diagram lists the failure cases: a missing token gives 401, no active camera source gives 409, and an undecodable image gives 422 and logs nothing; frames are "
     "decoded in memory and never written to disk."),
    ("uc", "Use-case diagram", "08_use_case_diagram.png", "Use-case diagram",
     "Two actors use the system. The rider or demonstrator can sign in with the demo account, run a simulation scenario, start the webcam, calibrate the EAR threshold (camera only), "
     "start and stop monitoring, see the verdict, reason and measurements, edit the thresholds and switch on the optional alert sound; dotted lines show that this actor may also open the "
     "history, the export and the explanation page. The reviewer or researcher can view the event history and the EAR chart, export the history as CSV, read the How it works page "
     "(formulas and limits), run the offline evaluation with a CSV and held-out subjects, and view the research report and confusion matrix. Calibration needs a live camera, and the "
     "optional sound extends monitoring when a warning fires. A warning is advice to stop somewhere safe: the design contains no use case that controls ignition, brakes or vehicle power, "
     "contacts another person or reports alcohol consumption."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png", "Entity-relationship diagram (persisted data and in-memory session)",
     "The diagram separates three kinds of data by colour. Persisted by the live application: the SQLite table `events` with twelve columns (id, timestamp, source, state, quality, "
     "reason, ear, closure, blink_rate, closed_fraction, roll, alert), and the JSON document `settings` with the six thresholds, their allowed ranges and the `calibrated` flag. In "
     "memory only: `RiderSession`, one per browser tab, with its id, source, scenario, monitoring flag, calibration object, state, reason, alert, settings and the vision and engine "
     "objects; one session writes zero or many events and loads and saves the one settings document, and it is lost when the session closes. Files used or produced by the offline "
     "research tools only: the user-supplied measurement CSV (eight columns), the derived `window_features.csv` (one CSV gives many 5-second windows, each with its features, label "
     "and train or test split) and the `research_results/` folder (`report.json`, `centroid_model.npz` and `confusion_matrix.png`; one run gives one report, overwritten by the next). "
     "The `source` column is either LIVE CAMERA or SIMULATION with the scenario name, so simulated rows can never be mistaken for real ones, and no image or video is stored anywhere."),
    ("flowchart", "Flowchart of the core algorithm", "10_core_algorithm_flowchart.png", "Flowchart of the core algorithm (`RiskEngine.update`)",
     "The flowchart follows `RiskEngine.update` for one observation. First, if the quality is not Good, the time gap is outside (0, 0.5] seconds, or a value is not finite or the EAR "
     "is out of range, the engine clears its samples, blinks and timers (keeping the alert cooldown clock) and returns Unable to assess with the quality label or the reason "
     "'Unstable timing or invalid measurement'. Otherwise the last three EAR values are median-filtered and compared with the threshold; the closure timer runs while the eye is "
     "closed, and a closure of 0.08 to 0.8 s is counted as a blink. The last 10 seconds of samples give the span and the time-weighted closed fraction, and the blink rate is "
     "computed over 60 seconds. Three rule tests are then evaluated and their reasons collected: A, closure of 1.5 s or more; B, a span of at least 8 s and a fraction of at least 0.55; "
     "C, absolute roll of at least 25 degrees while the eye is closed. If any reason exists the evidence timer starts (if not already running), otherwise it is cleared. The state is "
     "Unable to assess while the span is under 2 s (warm-up) and Normal otherwise. If reasons are present, the span is at least 2 s and the evidence has lasted the persistence time "
     "(1.0 s), the state becomes Possible impairment or drowsiness with the collected reasons. Finally, if the state is the warning and the cooldown (15 s) has passed since the "
     "last alert, the alert flag is set (the on-screen warning, the optional bell and the marked event row), and the decision is returned."),
]

SCHEMA = [
    ["id", "INTEGER", "Primary key, auto-increment", "Event number shown in the history table"],
    ["timestamp", "TEXT", "UTC, ISO 8601", "Time the event was logged (`datetime.now(timezone.utc).isoformat()`)"],
    ["source", "TEXT", "", "`LIVE CAMERA` or `SIMULATION: <scenario>`, so simulated rows can never be mistaken for real ones"],
    ["state", "TEXT", "", "`Normal`, `Possible impairment or drowsiness` or `Unable to assess`"],
    ["quality", "TEXT", "", "Signal quality label of the frame, for example `Good`, `No face`, `Poor lighting`"],
    ["reason", "TEXT", "", "The rule(s) that fired, or the reason the frame could not be assessed"],
    ["ear", "REAL", "", "Smoothed eye aspect ratio (dimensionless)"],
    ["closure", "REAL", "", "Duration of the current continuous closure, in seconds"],
    ["blink_rate", "REAL", "", "Blinks per minute over the last 60 s (display only; never warns)"],
    ["closed_fraction", "REAL", "", "Share of the last 10 s spent with eyes closed, 0 to 1"],
    ["roll", "REAL", "", "Head roll in the image plane, degrees"],
    ["alert", "INTEGER", "", "1 if an alert (the optional bell) was raised for this event, else 0"],
]

SETTINGS_FIELDS = [
    ["ear_threshold", "0.21", "0.08 - 0.40", "Smoothed EAR below this counts as a closed eye; calibration overwrites it"],
    ["closure_seconds", "1.5", "0.5 - 5", "Continuous closure that starts a warning timer"],
    ["persistence_seconds", "1.0", "0.5 - 5", "Evidence must persist this long before the warning is shown"],
    ["closed_fraction", "0.55", "0.3 - 0.9", "Share of the last 10 s with eyes closed that starts a timer (needs 8 s of history)"],
    ["tilt_degrees", "25", "10 - 45", "Head roll that counts as risk together with a low EAR"],
    ["cooldown_seconds", "15", "5 - 120", "Minimum gap between two audible alerts"],
    ["calibrated", "false", "boolean", "Set to true when the threshold came from a successful calibration"],
]

CSV_COLUMNS = [
    ["subject_id", "text", "Pseudonymous person identifier; must be the same across all sessions of that person"],
    ["session_id", "text", "One recording session"],
    ["timestamp_s", "float", "Seconds within the session, non-negative, strictly increasing"],
    ["ear", "float", "0 to 0.65"],
    ["roll_deg", "float", "-90 to 90"],
    ["quality", "text", "`Good` for usable frames; any other label excludes the containing window"],
    ["label", "text", "`normal` or `possible_impairment`, from an independent study protocol"],
    ["consent", "text", "`yes` on every row, backed by real consent documents held separately"],
]

MODULES = [
    ["`core.py`", "Decision logic (no I/O)", "`Settings`, `Observation`, `Decision`, `eye_aspect_ratio`, `head_roll`, `RiskEngine`, `Calibration`, `simulate`"],
    ["`vision.py`", "Landmarks, image quality, camera thread", "`Vision.process`, `CameraWorker`, `LEFT`, `RIGHT` landmark indices"],
    ["`storage.py`", "Persistence", "`Store.add`, `recent`, `export`, `load_settings`, `save_settings`"],
    ["`research.py`", "Offline subject-separated evaluation", "`extract_windows`, `metrics`, `evaluate`"],
    ["`extract_video.py`", "Offline video to measurement CSV", "frame-by-frame EAR and roll extraction from consented clips"],
    ["`app.py`", "Original Tkinter desktop application", "`Application` (start/stop camera, calibrate, monitor, history, thresholds, research dialog)"],
    ["`backend/main.py`", "FastAPI routes and demo login", "22 routes under `/api`, `make_token`, `current_user`"],
    ["`backend/session.py`", "Per-tab session state", "`RiderSession` (`set_source`, `set_monitoring`, `set_calibration`, `frame`, `tick`, `consume`, `snapshot`)"],
    ["`backend/content.py`, `synthetic.py`", "UI text and demo data", "`config`, `about`; seeded synthetic research CSV"],
    ["`frontend/src/pages/*`", "React screens", "Landing, Login, Monitor, History, Thresholds, Research, About, NotFound"],
    ["`frontend/src/lib/*`", "Client logic", "`api.ts`, `auth.tsx`, `camera.ts`, `useRiderSession.ts`, `queries.ts`, `alertSound.ts`, `theme.tsx`"],
    ["`tests/`, `scripts/`", "Verification and measurement", f"{F.TESTS['unittest']['tests']} unit tests, API smoke test, `measure_cew.py`, `measure_rules.py`, `measure_api.py`, screenshot capture"],
]

ENDPOINTS = [
    ["POST", "/api/auth/login", "No", "Demo sign-in; returns a signed bearer token (valid 12 h)"],
    ["GET", "/api/auth/me", "Yes", "The signed-in user"],
    ["GET", "/api/auth/demo", "No", "Demo credentials shown on the sign-in page"],
    ["GET", "/api/health", "No", "Status, landmark model present, number of logged events, research report present"],
    ["GET", "/api/config", "No", "Scenarios, threshold bounds and defaults, quality gates, disclaimers, state names"],
    ["GET", "/api/about", "No", "Pipeline, formulas, rules, limitations, reference text"],
    ["POST", "/api/session", "Yes", "Create a monitoring session (idle ones are dropped after 15 minutes)"],
    ["GET", "/api/session/{id}", "Yes", "Snapshot of the session"],
    ["DELETE", "/api/session/{id}", "Yes", "Close the session and release the landmark model"],
    ["POST", "/api/session/{id}/source", "Yes", "Choose `camera`, `simulation` (with a scenario) or `none`"],
    ["POST", "/api/session/{id}/monitoring", "Yes", "Start or stop monitoring"],
    ["POST", "/api/session/{id}/calibration", "Yes", "Start or cancel calibration (camera only)"],
    ["POST", "/api/session/{id}/frame", "Yes", "Upload a JPEG frame; returns the snapshot and the annotated preview"],
    ["POST", "/api/session/{id}/tick", "Yes", "Advance a simulation by one sample"],
    ["GET", "/api/settings", "Yes", "The six thresholds and the calibrated flag"],
    ["PUT", "/api/settings", "Yes", "Validate and save thresholds; stops monitoring"],
    ["GET", "/api/history?limit=", "Yes", "Up to 500 events (newest first) and a summary"],
    ["GET", "/api/history/export", "Yes", "All events as CSV"],
    ["GET", "/api/research", "Yes", "Offline report status (`Model not trained` until one exists)"],
    ["GET", "/api/research/sample-csv", "Yes", "The seeded synthetic demonstration CSV"],
    ["POST", "/api/research/evaluate", "Yes", "Upload a CSV and held-out subject IDs; runs the offline evaluation"],
    ["GET", "/api/research/confusion-matrix", "Yes", "Confusion matrix PNG of the last evaluation"],
]

SCREENS = [
    ["Landing `/`", "Public introduction in dark and light themes, how it works, limits and a call to action"],
    ["Sign in `/login`", "Email and password with the demo account shown and a one-click button"],
    ["Monitor `/app`", "Camera or simulation preview with the verdict badge, state card, six measurement tiles, EAR chart, calibration card, source and monitoring controls, alert-sound switch and the disclaimer box"],
    ["Event history `/app/history`", "Summary tiles, EAR chart (live and simulation series), filters, search, sortable table, CSV export"],
    ["Thresholds `/app/thresholds`", "Six validated numeric fields with ranges, inline error messages, reset to defaults"],
    ["Research `/app/research`", "CSV format, synthetic sample, held-out subject IDs, report with confusion matrix and a Synthetic data banner"],
    ["How it works `/app/about`", "Pipeline, formulas and rules, quality gates, limits and reference, offline tools"],
    ["Not found `*`", "Friendly 404 with a way back"],
]

SECURITY_DESIGN = [
    ["Sign-in", "Demo account compared in constant time; wrong credentials answer 401 with a plain message"],
    ["Token", "Base64 payload (subject, expiry) plus an HMAC-SHA256 signature; checked with `hmac.compare_digest`; 12-hour expiry"],
    ["Authorisation", "Every route except health, config, about, login and the demo hint depends on `current_user` (401 otherwise)"],
    ["Input validation", "Thresholds are validated against fixed bounds (422); frames must decode as images (422); research CSVs are validated row by row (422)"],
    ["Privacy", "Frames are processed in memory and discarded; only numbers are logged; the interface says so on the monitor screen"],
    ["Concurrency", "One lock per session; a fresh SQLite connection for each call; one research evaluation at a time (409)"],
    ["Fail-safe output", "Any doubt about signal quality produces Unable to assess, never a guess"],
]


def diagram_blocks(heading_level=3):
    out = []
    for i, (key, title, file, caption, text) in enumerate(DIAGRAMS, 1):
        out.append(("h3" if heading_level == 3 else "h2", f"{title}"))
        out.append(FIG(F.diag(file), caption, 5.0))
        out.append(P(text))
    return out


def schema_blocks():
    return [
        TAB("Table `events` in `data/events.sqlite3`", ["Column", "Type", "Constraint", "Meaning"], SCHEMA, widths=[1.2, 0.8, 1.4, 2.9], size=9.5),
        P("The table is created by `Store.__init__` with `CREATE TABLE IF NOT EXISTS`, so a fresh checkout needs no migration. Inserts use bound parameters (`?`), never string "
          "formatting, which removes SQL injection through the free-text reason or source fields. Every row is numeric or a short label; the schema has no column that could "
          "hold an image."),
        TAB("Settings file `data/settings.json`", ["Field", "Default", "Allowed range", "Meaning"], SETTINGS_FIELDS, widths=[1.5, 0.7, 1.1, 3.0], size=9.5, align=["l", "c", "c", "l"]),
        P("The file is written atomically: the new content goes to `settings.tmp` and replaces `settings.json` in one step, so a crash cannot leave a half-written file. A corrupt "
          "or out-of-range file is rejected on load and the safe defaults are used with a visible note."),
        TAB("Research CSV format read by `research.py`", ["Column", "Type", "Rule"], CSV_COLUMNS, widths=[1.3, 0.8, 4.2], size=9.5),
        P("The CSV is the only dataset interface; no fixed folder layout is required. Windows of 5 seconds are built per subject and session, and the split between training and "
          "held-out evaluation is defined only by subject membership."),
    ]


def blocks():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        H2("5.1 Architecture"),
        P("The design follows three rules. The decision logic is kept free of input and output, so it can be tested without a camera and shared by two front ends. Anything the "
          "system cannot judge is reported as Unable to assess rather than guessed. And nothing that could identify the rider, such as an image, is stored. The original desktop "
          f"modules (`core.py`, `vision.py`, `storage.py`, `research.py`) are reused unchanged by the web layer, which adds a FastAPI service and a React interface on top "
          f"of them. Face landmarks come from the MediaPipe Face Landmarker {n(11, 24)}; the eye aspect ratio follows {n(9)}."),
        FIG(F.diag("01_system_architecture.png"), "System architecture of the Smart Rider impairment warning system", 5.0),
        P(DIAGRAMS[0][4]),
        H2("5.2 High-level workflow"),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow of a monitoring session", 5.0),
        P(DIAGRAMS[1][4]),
        H2("5.3 Data flow diagrams"),
        H3("Level 0"),
        FIG(F.diag("03_dfd_level0.png"), "Data flow diagram, level 0 (context diagram)", 5.6),
        P(DIAGRAMS[2][4]),
        H3("Level 1"),
        FIG(F.diag("04_dfd_level1.png"), "Data flow diagram, level 1", 5.8),
        P(DIAGRAMS[3][4]),
        H3("Level 2"),
        FIG(F.diag("05_dfd_level2.png"), "Data flow diagram, level 2: processes 3 and 4 in detail", 5.8),
        P(DIAGRAMS[4][4]),
        H2("5.4 UML diagrams"),
        H3("Class diagram"),
        FIG(F.diag("06_uml_class_diagram.png"), "UML class diagram (core, vision, storage and web session)", 5.0),
        P(DIAGRAMS[5][4]),
        H3("Sequence diagram"),
        FIG(F.diag("07_sequence_diagram.png"), "Sequence diagram: one camera frame (POST /api/session/{id}/frame)", 5.8),
        P(DIAGRAMS[6][4]),
        H3("Use-case diagram"),
        FIG(F.diag("08_use_case_diagram.png"), "Use-case diagram", 5.0),
        P(DIAGRAMS[7][4]),
        H3("Core algorithm flowchart"),
        FIG(F.diag("10_core_algorithm_flowchart.png"), "Flowchart of the core algorithm (`RiskEngine.update`)", 4.6),
        P(DIAGRAMS[9][4]),
        H2("5.5 Database design"),
        FIG(F.diag("09_er_diagram.png"), "Entity-relationship diagram (persisted data and in-memory session)", 5.0),
        P(DIAGRAMS[8][4]),
        *schema_blocks(),
        H2("5.6 Module design"),
        P("The Python modules sit in the project root so that the original desktop commands keep working; the web layer is in `backend/` and the browser code in `frontend/`. "
          "The table lists what each part is responsible for."),
        TAB("Modules and responsibilities", ["Module", "Responsibility", "Key names"], MODULES, widths=[1.7, 1.8, 2.8], size=9.5),
        H2("5.7 API design"),
        P("The API is JSON over HTTP, with a CSV download and one PNG route. Errors use the standard FastAPI body `{\"detail\": \"message\"}`: 401 for a missing, invalid or expired "
          "token, 404 for an unknown session, 409 when a request does not fit the current state (for example starting monitoring with no source, or calibrating in simulation), "
          "422 for invalid input, 503 when the landmark model file is missing, and a generic 500 handler that still returns JSON. A camera frame is the only large request "
          "(about 21 KB for a 640 x 480 JPEG in our measurement); everything else is a few hundred bytes."),
        TAB("REST endpoints", ["Method", "Path", "Token", "Purpose"], ENDPOINTS, widths=[0.7, 2.2, 0.6, 2.8], size=9, align=["c", "l", "c", "l"]),
        P("Interactive documentation generated by FastAPI is available at `/docs` while the server runs."),
        H2("5.8 User interface design"),
        P("The web interface is a dark, glass-style design with gradient accents and a light theme that the user can switch to; the choice is remembered. A collapsible sidebar "
          "holds the five application screens, the header shows whether the landmark model is ready, and a short disclaimer stays visible at the bottom of the sidebar on every "
          "screen: a camera cannot confirm alcohol use and Normal does not mean fit to ride. The verdict has three colours with an icon and a word each, so meaning never rests on "
          "colour alone: green with a shield for Normal, red with a warning shield for Possible impairment or drowsiness, and amber with a question mark for Unable to assess. "
          "Simulated data are always labelled SIMULATION, on the preview, in the alert text and in every stored row. Layouts adapt from a 360-pixel phone to a wide desktop."),
        TAB("Screens", ["Screen", "Content"], SCREENS, widths=[1.7, 4.6], size=10),
        FIG(F.shot_view("07_monitor_idle.png"), "The monitor screen before a source is chosen: Unable to assess, no source, and the calibration card", F.shot_w(F.shot_view("07_monitor_idle.png"), 5.6)),
        FIG(F.shot_view("13_about.png"), "The How it works screen: the six pipeline steps", F.shot_w(F.shot_view("13_about.png"), 5.6)),
        P("The interface is built with React, Vite, Tailwind CSS, a charting library for the EAR and history charts and accessible UI primitives. Each screen is loaded as its own "
          "chunk, so the landing page does not download the camera or chart code. Chapter 7 reports the layout checks at 360, 768 and 1440 pixels."),
        H2("5.9 Security and privacy design"),
        P("Because the system observes a person's face, privacy is a design requirement, not a later addition. The controls below are the design; Section 6.10 shows how they are "
          "implemented and Chapter 7 how they were checked."),
        TAB("Security and privacy controls", ["Area", "Design"], SECURITY_DESIGN, widths=[1.4, 4.9], size=9.5),
        P("The design also has known weaknesses, stated rather than hidden: the demo account is shared and its password is displayed on the sign-in page because this is a demonstration; "
          "the transport is plain HTTP on the local machine; the API allows any browser origin (CORS is open) because it is meant to run on a laptop; all users share one event "
          "database and one settings file; sessions live in memory and are lost when the server restarts; and there is no rate limiting. These must be changed before any use "
          "beyond a local demonstration."),
    ]
