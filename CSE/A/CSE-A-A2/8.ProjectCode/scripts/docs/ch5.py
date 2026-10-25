"""Chapter 5: System Design (ResQAI)."""

import glob
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, PAIR, TAB
from .diagram_index import DIAGRAMS
from .refs import CITE as R

_FILES = {k: f for k, _, f, _, _ in DIAGRAMS}
_CAPS = {k: c for k, _, _, c, _ in DIAGRAMS}


def _loc(*patterns):
    """Non-blank lines of the files matching the patterns (relative to 8.ProjectCode), counted at build time."""
    n = 0
    for pat in patterns:
        for p in glob.glob(os.path.join(F.CODE, pat), recursive=True):
            if "__pycache__" in p or "node_modules" in p or "dist" in p.split(os.sep) or not os.path.isfile(p):
                continue
            with open(p, encoding="utf-8", errors="ignore") as fh:
                n += sum(1 for line in fh if line.strip())
    return n


def dfig(key, width=5.6, max_h=6.6):
    """Real diagram, width limited so that its height stays below max_h inches."""
    path = F.diag(_FILES[key])
    return FIG(path, _CAPS[key], F.shot_w(path, width, max_h))


def spair(items, width=2.8):
    """Two screenshots side by side: items = [(file, caption), ...]."""
    return PAIR([(F.shot(n), c) for n, c in items], width)


def blocks():
    return design_goals() + workflow() + dataflow() + uml() + database() + modules() + algorithm_design() + ui_design() + decisions() + quality()


# =====================================================================================================================
def design_goals():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter turns the requirements of Chapter 4 into a design. It gives the architecture, the workflow of one event from sensor reading to dispatched alert, the data flow diagrams, the UML models, "
          "the data design, the module design, the algorithm design, the interface design and the reasons for the main design decisions. Every diagram was drawn from the code in the repository "
          "(`app.py`, `auth.py`, `train_models.py`, `data/` and `frontend/src`) and each is listed again, with a short explanation, in the block-diagram document. "
          "Where the design is simpler than a production system would need, the chapter says so; Chapter 10 lists the corresponding future work."),

        H2("5.1 Design Goals and Architecture"),
        P("Four goals shaped the design. The first is **end-to-end completeness**: the base paper and the other surveyed work stop at predicting severity from recorded crash data, whereas the problem statement asks for a loop that runs from sensing to a located, prioritised alert. "
          "The second is **false-alarm control**: an alert that reaches responders for a pothole or a hard stop costs trust, so a human confirmation step sits between the model and the alert. "
          "The third is **demonstrability without hardware**: no phone, vehicle or crash-test data was available, so the sensing stage is simulated by the backend and everything after it is real code. "
          "The fourth is **simplicity of deployment**: the application runs from one batch file on an ordinary Windows machine, with no database server and no cloud account."),
        P(f"The architecture has four tiers (see the figure below). The **presentation tier** is a React 19 and Vite 8 single-page application on port {F.WEB_PORT}. Its three console screens (live monitor, manual override, emergency response) share one state provider, `MonitorContext`, "
          "which owns the sensor history, the event log, the 15-second countdown and the dispatch result, and the only network code is the thin `fetch` wrapper in `lib/api.js`, which attaches the Bearer token and turns failures into a typed `ApiError`. "
          f"The **application tier** is one Flask 3 process on port {F.API_PORT}: `app.py` holds the five working endpoints and the helper functions, and `auth.py` is a blueprint that adds registration, login and an optional guard. "
          "The **machine-learning tier** is a scaler and two random forests loaded once at import time with `joblib`; if a pickle is missing the application sets `MODELS_LOADED = False` and answers from a three-threshold rule instead, so it never fails to respond. "
          "The **data tier** is two JSON files and four pickles; there is no database."),
        dfig("arch", 5.9),
        P("The tiers talk only in one direction through narrow interfaces. The browser sends JSON over HTTP and, when the optional guard is on, a signed Bearer token; the Vite development server proxies every `/api` request to the Flask port, which removes the need for cross-origin settings. "
          "The Flask process calls the models through ordinary Python calls. The only outside services are OpenStreetMap map tiles, which the Leaflet map requests from the browser, and the browser's own Geolocation API; neither is part of the server."),
        TAB("Technology used by tier", ["Tier", "Technology", "Role"],
            [["Presentation", "React 19, Vite 8, React Router 7, Recharts, Leaflet, framer-motion, GSAP", "pages, sensor chart, map, animations, theme"],
             ["Application", "Python 3.11, Flask 3.1, itsdangerous, werkzeug.security", "REST endpoints, accounts, signed tokens"],
             ["Machine learning", f"scikit-learn (RandomForestClassifier, StandardScaler), NumPy, pandas, joblib", "detection, severity grading, persistence"],
             ["Data", "JSON files (`users.json`, `hospitals.json`), pickles (`models/`)", "accounts, hospital directory, trained models"],
             ["Tooling", "Playwright, `scripts/smoke_test.py`, `scripts/run_tests.py`", "screen capture, regression and security checks"]],
            widths=[1.2, 3.1, 2.0], size=9.5),
    ]


# =====================================================================================================================
def workflow():
    return [
        H2("5.2 High-Level Workflow"),
        P("The figure below follows one event through the system. A reading of eleven features is produced; in a deployment the phone would supply it, here the backend's `/api/simulate` does. "
          "The reading is posted to `/api/predict`, where it is turned into a feature vector, scaled, and passed to the detector and the severity model. The browser then applies the rule that decides whether a person must be asked: "
          "only a **Moderate** or **Severe** grade opens the confirmation dialog, and a **Minor** crash or a normal reading is only written to the event log."),
        dfig("flow", 5.9),
        P("The numbered steps below are the behaviour of the console, taken from `MonitorContext.jsx`:"),
        N("The occupant presses a scenario button, starts live monitoring (one reading every 1.5 seconds, never two requests in flight) or submits manual values.",
          "The reading is sent to `POST /api/predict`; the response (accident flag, severity label, probability, the features used, the model source) is stored as the current result, a point is added to the sensor trace (the last 40 are kept) and a line is added to the event log (the last 25 are kept).",
          "If the label is Moderate or Severe and no alert is already pending, the result becomes the pending alert, live monitoring is stopped, and a dialog with a countdown from 15 seconds opens.",
          "The occupant can answer *I'm fine, cancel* or press Escape; either counts as a response, the pending alert is cleared and the event log records that the user confirmed they are all right.",
          "If the counter reaches zero, or the occupant presses *Send alert now*, the browser asks for its position (three-second timeout) and posts the severity, the confidence and, when known, the latitude and longitude to `POST /api/emergency`.",
          "The server ranks the hospitals, composes the dispatch message and returns it with an alert id; the dispatch dialog opens, the Emergency response screen draws the map, and the event log records the alert."),
        P("Nothing leaves the machine in step 6. The dispatch message is drafted and shown, with a copy button and tap-to-call links for 108, 112 and 103, and the interface states that the demo does not contact responders. "
          "This is the main gap between the system as built and the sixth objective's wording about dispatching to emergency contacts, and it is repeated in the limitations."),
        dfig("seq", 5.2, 7.2),
        P("The sequence diagram shows the same flow as messages between the five parties. Two details are worth noting. First, the detector and the severity model are called inside one request, so the browser sees one consistent answer rather than two. "
          "Second, the location is read in the browser, not on the server: the server only receives numbers, and if the position is unavailable it substitutes a random point within about six kilometres of the default Hyderabad location, which keeps the demonstration working on a machine with no location service."),
    ]


# =====================================================================================================================
def dataflow():
    return [
        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0 (context diagram)"),
        P("At level 0 ResQAI is a single process with one human entity and two outside services. The occupant supplies credentials, a scenario or manual sensor values, and the cancel-or-send decision, and receives the detection result, the countdown, the dispatch message, the hospitals, the map and the event log. "
          "The Geolocation API returns the device coordinates and the tile server returns map images. The diagram also records what is *not* an entity: there is no phone supplying readings, no responder receiving the message and no hospital system; those three would be added in a deployment."),
        dfig("dfd0", 5.4),
        H3("5.3.2 Level 1"),
        P("Level 1 splits the system into six processes. Authentication (1.0) is the only process that touches the users file; it issues the signed token. Reading acquisition (2.0) produces the eleven-feature record either from the simulator or from the typed values. "
          "Detection and grading (3.0) reads the model pickles and returns the accident flag, the probability and the severity. Alert confirmation (4.0) is entirely client-side and is the human-in-the-loop step. "
          "Location and hospital ranking (5.0) reads the directory, and dispatch composition (6.0) builds the message. The three data stores are the users file (D1), the hospital directory (D2) and the model pickles (D3)."),
        dfig("dfd1", 5.6),
        H3("5.3.3 Level 2"),
        P("Level 2 expands process 3.0, because it is where the machine learning happens and where the design makes its one non-obvious rule. The payload is completed with defaults (a missing `acc_z` becomes 9.81 m/s², a missing velocity field becomes zero) and the derived magnitudes are computed (3.1). "
          "The vector is scaled with the training mean and standard deviation (3.2). The detector (3.3) and the severity model (3.4) both receive the scaled vector; the gate (3.5) then forces the severity to None whenever the detector says no accident. "
          "Process 3.6, the rule-based fallback, is drawn dashed because it runs only when the model files cannot be loaded."),
        dfig("dfd2", 5.6),
    ]


# =====================================================================================================================
def uml():
    return [
        H2("5.4 UML Diagrams"),
        H3("5.4.1 Class diagram"),
        P("The backend is written as functions in two modules rather than as application classes, so the class diagram is a design-level view of the objects those functions pass around. "
          "`SensorReading` is the eleven-feature record built by `build_feature_vector`; `Prediction` is the response of `/api/predict`; `EmergencyAlert` is the response of `/api/emergency`. All three are transient and exist as JSON. "
          f"`RandomForestClassifier` appears once in the diagram but twice at run time: the detector ({F.SHIP['detector']['n_estimators']} trees, depth {F.SHIP['detector']['max_depth']}) and the severity model ({F.SHIP['severity']['n_estimators']} trees, depth {F.SHIP['severity']['max_depth']}). "
          "`StandardScaler` is shared. `HospitalDirectory` wraps the ten-entry JSON file with the great-circle distance and the nearest-k selection. "
          "On the client, `MonitorProvider` is the state machine; `AuthService` and `User` describe `auth.py` and the accounts file."),
        dfig("uml", 5.9),
        H3("5.4.2 Use-case diagram"),
        P("The occupant is the only interactive actor. The developer actor covers activities that happen on the command line: retraining the models with `train_models.py`, switching the API guard on with `REQUIRE_AUTH=1`, and running the test and measurement scripts. "
          "The two external services support the location and map use cases. The table after the diagram expands the eight use cases."),
        dfig("uc", 5.0, 6.0),
        TAB("Use cases of the occupant", ["ID", "Use case", "Pre-condition", "Main flow", "Outcome"],
            [["UC1", "Register / sign in", "none", "Enter name, e-mail, password (8 to 128 characters); receive a token", "console unlocked; five wrong passwords lock the account for 5 minutes"],
             ["UC2", "Run a scenario", "signed in", "Press Normal, Harsh brake, Minor, Moderate or Severe", "result panel, trace point and log line; countdown for Moderate / Severe"],
             ["UC3", "Live monitoring", "signed in", "Switch on; one random reading every 1.5 s", "stops itself when a countdown opens or the API fails"],
             ["UC4", "Manual override", "signed in", "Type seven values (client-side range checks), run detection", "result for a hand-made reading; derived acc. magnitude shown before the run"],
             ["UC5", "Confirm or cancel", "a Moderate / Severe result", "Cancel, press Escape, send now or let 15 s expire", "alert cancelled and logged, or dispatched"],
             ["UC6", "View response map", "signed in", "Open the Emergency response screen", "hospital directory before an alert; accident and 3 nearest hospitals after it"],
             ["UC7", "Call emergency numbers", "none", "Tap 108, 112 or 103", "the device dialler opens (tel: link)"],
             ["UC8", "Theme and log", "none", "Toggle light / dark; read the last 25 events", "preference kept in local storage"]],
            widths=[0.45, 1.15, 1.0, 2.0, 1.7], size=8.5),
    ]


# =====================================================================================================================
def database():
    return [
        H2("5.5 Data Design"),
        P("ResQAI has **no relational database**, and the report does not draw one. The data design follows from what must survive a restart. Only three things must: the accounts, the hospital directory and the trained models. "
          "Everything produced while the console is in use, namely readings, predictions and alerts, is transient. This is an honest simplification for a demonstration and one of the first things a production version would change."),
        dfig("er", 5.6, 5.6),
        TAB("Persisted records", ["Store", "Key", "Fields", "Size / count"],
            [["`data/users.json`", "lower-case e-mail", "id (16 hex), name (2 to 60), email, password_hash (scrypt:32768:8:1), created (ISO time)", "grows with sign-ups; written atomically through a temporary file and `os.replace` under a lock"],
             ["`data/hospitals.json`", "name", "lat, lon, phone, emergency flag; plus `default_location` (Hyderabad, 17.3850, 78.4867)", f"{F.N_HOSPITALS} hospitals"],
             ["`models/accident_detector.pkl`", "-", "RandomForest, 200 trees, depth 10", "385.5 KB"],
             ["`models/severity_predictor.pkl`", "-", "RandomForest, 250 trees, depth 12", "2,608.2 KB"],
             ["`models/feature_scaler.pkl`, `feature_names.pkl`", "-", "StandardScaler (11 means and scales); the ordered list of 11 feature names", "0.8 KB and 0.1 KB"]],
            widths=[1.5, 0.9, 2.6, 1.3], size=9),
        P("The three transient entities are shown dashed in the figure. A reading is the JSON body of one request; a prediction is its response; an alert is the response of `/api/emergency`. "
          "The browser keeps the last 40 trace points and the last 25 log lines in React state, and the current dispatch, so a page reload empties them. "
          "Two consequences follow and are recorded as limitations: the server keeps no history of events, and an alert carries no user id, so alerts cannot be tied to an account. "
          "The failed-login counters used for the lockout are also only in memory and reset when the server restarts."),
        P("The reasons for the design are practical. A JSON file for ten hospitals is easier to read and edit than a table, and swapping it for a call to a hospital-search service changes one function. "
          "Accounts in a file are acceptable for a single-machine demonstration, and the write path is safe against a torn file because the new content is written to a temporary file and then renamed. "
          "A database such as SQLite or PostgreSQL, with tables for users, alerts and events and a foreign key from each alert to a user, is the obvious next step (Chapter 10)."),
    ]


# =====================================================================================================================
def modules():
    py = _loc("app.py", "auth.py", "train_models.py")
    fe = _loc("frontend/src/**/*.jsx", "frontend/src/**/*.js", "frontend/src/**/*.css")
    sc = _loc("scripts/smoke_test.py", "scripts/capture_screens.py", "scripts/capture_extra_screens.py", "scripts/measure_metrics.py", "scripts/measure_api.py", "scripts/run_tests.py")
    return [
        H2("5.6 Module Design"),
        P(f"The delivered code is small and flat. The three Python modules of the product have about {py:,} non-blank lines, the React source about {fe:,} lines of JSX, JavaScript and CSS, and the scripts written for testing and measurement about {sc:,} lines. "
          "The table below lists each module with its responsibility and its main entry points."),
        TAB("Modules and their responsibilities", ["Module", "Responsibility", "Main functions or components"],
            [["`app.py`", "REST API, helpers, model loading", "`build_feature_vector`, `predict_from_features`, `rule_based_fallback`, `haversine_km`, `nearest_hospitals`, `random_nearby_point`; routes `/`, `/api/predict`, `/api/simulate`, `/api/hospitals`, `/api/emergency`, `/api/health`"],
             ["`auth.py`", "accounts and the optional API guard", "`register`, `login`, `me`, `status`, `user_from_request`, `init_app` (the `before_request` guard); in-memory lockout table"],
             ["`train_models.py`", "synthetic data and training", "`make_event`, `generate_dataset`, `main` (split, scale, fit, report, `joblib.dump`)"],
             ["`frontend/src/state/MonitorContext.jsx`", "client state machine", "`runReading`, `runScenario`, live-monitoring interval, `sendAlert`, `cancelAlert`, countdown effects"],
             ["`frontend/src/lib/`", "client infrastructure", "`api.js` (fetch wrapper, token), `auth.jsx` (session, 401 handling), `theme.jsx`, `format.js` (scenarios, severity colours, emergency numbers), `storage.js`"],
             ["`frontend/src/pages/`", "screens", "`Landing`, `Auth` (login and register), `Monitor`, `Manual`, `Response`, `NotFound`"],
             ["`frontend/src/features/`", "reusable parts", "`ResultPanel`, `SensorChart`, `EventLog`, `AlertOverlays` (countdown and dispatch dialogs), `MapView` (Leaflet), `ContactsCard`, `ApiError`"],
             ["`scripts/`", "verification", "`smoke_test.py`, `run_tests.py`, `measure_metrics.py`, `measure_api.py`, `capture_screens.py`, `capture_extra_screens.py`"],
             ["`templates/`, `static/`", "the original single-page dashboard", "served at `/`; still works beside the React console"]],
            widths=[1.8, 1.5, 3.0], size=9),
        P("**`app.py`** is organised in three layers: loading (the models and the hospital file are read once, inside a `try` that falls back to the rule engine), pure helpers that can be tested without a server, and thin route functions that only read the request, call a helper and return JSON. "
          "The helper `build_feature_vector` is the single place where the payload is normalised, so the manual form, the simulator and a future phone client all pass through the same code. "
          "**`auth.py`** keeps the accounts file and the signing serializer private and exposes a blueprint; its `init_app` registers a `before_request` hook that, only when `REQUIRE_AUTH` is set, rejects any `/api/` request except health and the auth routes unless a valid token is present. "
          "**`MonitorContext.jsx`** is the largest client module and the only one with logic that matters for safety: it decides when a countdown starts, stops live readings under an open dialog, cancels on Escape and calls the dispatch endpoint exactly once."),
    ]


# =====================================================================================================================
def algorithm_design():
    return [
        H2("5.7 Algorithm Design"),
        P("The core algorithm is the function `predict_from_features` and the client-side rule that follows it. The flowchart below shows it. "
          "In words: build the feature vector, check that the models are loaded, scale the vector, ask the detector for the class and the probability of an accident, ask the severity model for the grade, and set the grade to None if the detector said no. "
          "Only after the response reaches the browser does the confirmation rule apply: open the 15-second countdown when the grade is Moderate or Severe."),
        dfig("flowc", 5.0, 6.8),
        P("The gate is deliberate. The severity forest is trained on all events with None as class 0, so it can also say None; the detector is trained on the binary label. Letting the detector override the severity means that the two models can never contradict each other in the response "
          "(an event reported as *no accident* always has severity None), and it gives one place to adjust the system's willingness to alert. "
          f"On the 2,400 held-out events the gate changes nothing, because the severity model alone gives the same accuracy ({F.pct(F.SHIP['severity_test_raw']['accuracy'], 3)}); it matters when the two models would disagree, for example under noise."),
        P("The offline training pipeline is a separate algorithm, run once. It generates the data, splits it, fits the scaler on the training part only, trains the two forests with balanced class weights, prints the held-out accuracy and report, and writes the four pickles."),
        dfig("train", 5.8, 3.4),
    ]


# =====================================================================================================================
def ui_design():
    return [
        H2("5.8 User Interface Design"),
        P("The interface is a React console in a neo-brutalist visual style: heavy outlines, flat colour blocks, a lime accent and a coral accent reserved for danger, with a light and a dark theme that is remembered between visits. "
          "Colour is never the only carrier of meaning: every severity is also a text badge, the result headline says *No accident* or *Accident detected*, and the countdown is a large numeral with a progress bar. "
          "The countdown dialog is a real `dialog` with a focus-first *I'm fine, cancel* button, a polite live-region announcement of the remaining seconds, and an Escape-to-cancel rule, so keyboard and screen-reader users can answer in time."),
        spair([("01_landing_light.png", "Landing page, light theme."), ("04_login_light.png", "Sign-in form: the console is locked until an account signs in.")], 2.9),
        P("The landing page explains the pipeline in five steps (*Five steps, no hand-offs*) and links to sign-in. The three console screens sit behind the login: a signed-out visitor who opens `/monitor` is redirected to `/login` and returned to the page afterwards. "
          "Navigation is a left rail on wide screens; below 1,024 pixels the style sheet switches to a bottom bar (not captured as a screenshot in this report)."),
        spair([("08_monitor_live.png", "Live monitor: scenario buttons, live switch, detection result and the sensor trace."), ("09_alert_countdown.png", "Confirmation dialog for a Severe result with 11 seconds left.")], 2.9),
        P("The **Live monitor** has three zones: the scenario buttons and the live-monitoring switch; the detection result (headline, severity badge, accident probability bar and a key-value table of the features used); and the sensor trace, a two-axis line chart of acceleration magnitude (m/s²) and gyroscope magnitude (rad/s) over the last 40 readings, followed by the event log. "
          "The **Manual override** screen has seven fields (three accelerations, gyroscope magnitude, speed before, speed change, jerk) with range checks in the browser, a live display of the derived acceleration magnitude, a *Load simulated sample* button and *Reset*."),
        spair([("15_manual_form.png", "Manual override: seven inputs and the derived acceleration magnitude."), ("11_response_dispatched.png", "Emergency response after a dispatch: map, dispatch summary and nearest hospital.")], 2.9),
        P("The **Emergency response** screen shows the hospital directory around the default area before any alert, and after a dispatch it plots the accident position and the three nearest hospitals on an OpenStreetMap layer, with a summary table (alert id, status, severity, location, source, nearest hospital), a *Call* button for the nearest hospital, a *View message* dialog with a copy button, and the three emergency numbers. "
          "A banner inside the dispatch dialog says that the message is drafted but not sent."),
    ]


# =====================================================================================================================
def decisions():
    return [
        H2("5.9 Design Decisions and Trade-offs"),
        TAB("Main design decisions", ["Decision", "Alternative", "Reason for the choice", "Cost"],
            [["Two random forests (detect, grade)", "one 4-class model; a neural network", "forests need no feature engineering beyond magnitudes, train in seconds on a CPU, give a probability and have importance scores " + f"[{R['breiman']}]", "cannot extrapolate; ~2.6 MB for the severity model"],
             ["Detector gates the severity", "trust the severity model alone", "the response can never say *no accident* with a severity other than None", "one more rule to explain"],
             ["Confirmation window of 15 s, client-side", "alert at once; longer window", "gives a conscious occupant time to stop a false alarm; short enough for a real emergency", "an unconscious occupant delays the alert by 15 s"],
             ["Only Moderate / Severe start the countdown", "also Minor", "Minor crashes would interrupt the driver; they are logged", "a Minor crash with a hurt occupant is not escalated"],
             ["Simulated sensors served by the backend", "a real phone app", "no hardware or recordings were available; the simulator mirrors the training generator so the demo is repeatable", "results say nothing about real sensors"],
             ["JSON files instead of a database", "SQLite / PostgreSQL", "ten hospitals and a handful of accounts; zero set-up", "no event history, no alerts per user, no concurrency control beyond one lock"],
             ["Haversine ranking of a 10-hospital directory", "routing distance; a places API", f"closed form, no network [{R['haversine']}]; adequate for a demo", "straight-line distance ignores roads, traffic and capacity"],
             ["Signed tokens, optional guard", "mandatory guard; server sessions", "keeps the original dashboard working; tokens are stateless and expire in 12 h", "the guard is off by default, so a default install exposes the API to the local network"],
             ["Flask development server", "gunicorn / waitress", "single command start-up on Windows", "not a production server; `debug=True` must be off outside a demonstration"]],
            widths=[1.4, 1.2, 2.3, 1.4], size=8.5),
    ]


# =====================================================================================================================
def quality():
    ep = F.ENDPOINTS
    return [
        H2("5.10 Quality Attributes"),
        P(f"**Performance.** On loopback, `/api/predict` takes a mean of {ep['POST /api/predict']['mean']:.1f} ms (95th percentile {ep['POST /api/predict']['p95']:.1f} ms) and the three-call alert path takes a mean of {F.ALERT_PATH['mean']:.1f} ms; "
          f"the model call alone takes {F.INF['mean']:.1f} ms in process. The 15-second confirmation window therefore dominates the time to an alert by more than two orders of magnitude, which is the intended trade. "
          "The numbers were measured with the Flask development server on a machine that was short of memory (Chapter 7)."),
        P("**Reliability.** The application starts and answers without the model files, using the rule-based fallback; the front end shows an explicit *Cannot reach the ResQAI API* banner with a retry button instead of a blank screen, stops live monitoring on the first failure and logs the error. "
          "**Security.** Passwords are stored as scrypt hashes, tokens are signed and expire after 12 hours, repeated failures lock an account, and the guard can be switched on for the whole API; Chapter 6 lists the validation gaps that the tests found. "
          "**Usability.** One-click scenarios, an Escape key that answers the countdown, tap-to-call links and light and dark themes keep the console usable under stress. "
          "**Maintainability.** The helpers in `app.py` are pure functions, the front end is split into pages, features and a small UI kit, and every number in this report can be regenerated with three scripts."),
    ]
