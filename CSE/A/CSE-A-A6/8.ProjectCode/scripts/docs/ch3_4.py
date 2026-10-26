"""Chapters 3 (feasibility) and 4 (requirements and analysis)."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

_FRAME = (F.API_LAT or {}).get("POST frame (real face JPEG 640x480, monitoring on)", {})
_FP50, _FP95 = f"{_FRAME.get('p50_ms', 0):.0f}", f"{_FRAME.get('p95_ms', 0):.0f}"
_VIS = F.CEW["latency_ms_vision_process_640x480"]
_ENG = F.RULES["engine_cost"]["microseconds_per_update"]
_UT = (F.TESTS or {}).get("unittest", {})
_SM = (F.TESTS or {}).get("web_smoke", {})

FUNCTIONAL = [
    ["FR1", "Sign in with the demo account (email and password) and sign out; protected routes answer 401 without a valid token.", "Must"],
    ["FR2", "Start and stop the browser camera, show the preview with the eye landmarks drawn on it, and release the camera on stop.", "Must"],
    ["FR3", "Offer Simulation Mode with four scripted scenarios (Normal, Prolonged eye closure, Missing face, Poor lighting) so the system can be demonstrated without a camera; label every simulated event.", "Must"],
    ["FR4", "Calibrate the EAR threshold per rider over 8 to 15 seconds with natural open eyes; refuse calibration in simulation; keep the previous threshold on failure.", "Should"],
    ["FR5", "Start and stop monitoring and show one of three states, Normal, Possible impairment or drowsiness, or Unable to assess, with the reason for it.", "Must"],
    ["FR6", "Check signal quality first and return Unable to assess for no face, several faces, poor lighting, blur, unstable video, small or hidden eyes, unreliable eye geometry, irregular timing or a stalled camera.", "Must"],
    ["FR7", "Display the measurements behind the state: EAR, closure time, blink rate, closed-eye fraction over 10 s, head roll and the EAR threshold in use.", "Should"],
    ["FR8", "Show an on-screen warning while the warning state lasts and, if switched on, sound an alert with a cooldown between alerts.", "Must"],
    ["FR9", "Log numeric events (state changes, 5-second snapshots and alerts) to SQLite with UTC time and source; store no video and no face images.", "Must"],
    ["FR10", "List the history with search, source filter and an EAR chart; export every event as CSV.", "Should"],
    ["FR11", "Edit the six thresholds within validated bounds; saving stops monitoring and clears the calibrated flag.", "Should"],
    ["FR12", "Accept a consented, labelled measurement CSV and held-out subject IDs for offline evaluation; answer Model not trained when no suitable data exist; flag any report built from the synthetic demonstration file.", "Could"],
    ["FR13", "Explain the pipeline, formulas, quality gates, limitations and the reference on an About page.", "Should"],
    ["FR14", "State on every screen that a camera cannot confirm alcohol and that Normal does not mean fit to ride.", "Must"],
    ["FR15", "Reject invalid input with a readable message: undecodable frame, out-of-range threshold, malformed CSV, unknown session (HTTP 422, 404 or 409).", "Must"],
    ["FR16", "Offer light and dark themes and remember the choice.", "Could"],
    ["FR17", "Keep the original Tkinter desktop application working over the same modules and the same stored data.", "Could"],
]

NONFUNCTIONAL = [
    ["Performance", f"A camera frame is analysed and answered fast enough for about 30 frames per second on a laptop CPU.", f"Measured: {_FP50} ms median and {_FP95} ms 95th percentile through the API; `Vision.process` alone {_VIS['p50']:.1f} ms median (Chapter 7)"],
    ["Rule cost", "The rule engine adds negligible time per observation.", f"Measured: {_ENG:.1f} microseconds per update over 200,000 updates"],
    ["Reliability", "Poor input never produces a warning; a gap, NaN or non-increasing time clears the evidence.", f"{_UT.get('passed', 0)} unit tests (quality loss for four conditions, timing gap, NaN, cooldown after signal loss)"],
    ["Security", "Signed expiring token, constant-time comparison, validated inputs, no stored images.", f"{_SM.get('passed', 0)} API checks including 401, 409, 422 cases (Chapter 7)"],
    ["Privacy", "Frames exist only in memory; only numbers are logged; the dataset used for evaluation is kept outside the repository.", "Code review of `storage.py`, `backend/session.py`; Chapter 6"],
    ["Usability", "Every screen usable from 360 px to 1440 px, light and dark themes, keyboard operable.", "`scripts/check_layout.py` and `scripts/capture_screens.py`; screenshots in Chapter 8"],
    ["Portability", "Runs on Windows 10 or 11 with Python 3.12 or newer and Node.js 18 or newer; one script starts everything.", "`run.bat`, `docs/03_HOW_TO_RUN.md`"],
    ["Maintainability", "Decision logic, vision, storage, API and front end are separate modules with tests.", f"{_UT.get('passed', 0)} unit tests and {_SM.get('passed', 0)} API checks pass"],
    ["Honesty of output", "The system must never claim to detect alcohol and must say when it cannot assess.", "Three-state output; wording in `backend/content.py`; disclaimers on every screen"],
]


def blocks():
    ch3 = [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        H2("3.1 Technical feasibility"),
        P("Every component is free, mature open-source software and the whole system ran on one ordinary laptop with its built-in webcam. "
          f"MediaPipe {n(11, 24)} supplies the face landmarks, OpenCV {n(19)} the image operations, NumPy {n(20)} the arithmetic and Matplotlib {n(21)} the charts; FastAPI {n(22)} serves the API, "
          f"SQLite stores the history and React {n(23)} builds the interface, while the original desktop application uses only Python's standard Tkinter. No GPU is needed: the landmark model runs on the CPU, "
          f"and a camera frame goes through the whole API in about {_FP50} ms (median), so roughly 30 frames per second can be analysed (Chapter 7)."),
        P("Three technical risks were identified and handled. (i) **No data for a trained intoxication model.** No dataset of intoxicated and sober people was available, so the live system "
          "uses explainable rules and the learned pipeline is kept offline. (ii) **Unreliable pictures.** Dim light, blur and hidden eyes make EAR meaningless, so seven quality gates run before any rule. "
          "(iii) **Packaging.** The pinned packages need Python 3.12 or newer, so `run.bat` rebuilds the virtual environment when the shipped one points at a missing interpreter."),
        H2("3.2 Economic feasibility"),
        P("No licence, cloud service or special hardware was bought. The frameworks are open source, the landmark model is a free download of about 3.7 MB, and the evaluation dataset is public. "
          "The only recurring cost of running the system is the electricity of one computer; there is no per-use fee. The costs that a real product would add, namely a mounted camera, "
          "an embedded computer, validation with riders, certification and insurance, were not estimated and are not budgeted in this project."),
        TAB("Cost view", ["Item", "Cost to the project", "Remark"], [
            ["Software, frameworks, libraries", "None", "Open-source licences"],
            ["Landmark model", "None", "Google's face_landmarker.task, downloaded once"],
            ["Evaluation data", "None", f"Public CEW dataset {n(12)}, kept outside the repository"],
            ["Computer and webcam", "None additional", "The laptop already owned"],
            ["Hosting", "None", "Runs locally on ports 8306 (API) and 5306 (web app)"],
            ["Mounting, embedded hardware, validation, certification", "Not costed", "Out of scope (Section 1.6)"],
        ], widths=[2.4, 1.5, 2.5]),
        H2("3.3 Operational feasibility"),
        P("The web application has one main screen: choose a camera or a simulation, optionally calibrate, press Start monitoring. The state, its reason and the measurements are shown in plain "
          "language, and a disclaimer is visible throughout. Start-up is a single script (`run.bat`) that prepares the Python environment, downloads the landmark model if it is missing, installs the "
          "front-end packages and opens the browser. No database administration is needed: the SQLite file is created on first use. Operation has limits that are stated in the interface: "
          "browsers allow camera access only on localhost or HTTPS, the demo account is shared, and the prototype is for stationary demonstration."),
        H2("3.4 Schedule feasibility"),
        P("The work divides into phases with clear dependencies: (1) the core rules and landmark extraction, (2) storage and calibration, (3) the desktop interface, (4) the API layer, "
          "(5) the web interface, (6) measurement and testing, and (7) documentation. Phases 4 and 5 depend only on the public functions of the core modules, so they could proceed without "
          "changing the decision logic. Experiments are cheap: the 20 unit tests run in under a second, and the whole measurement set (2,423 still images through the vision pipeline, twelve degraded "
          "conditions, the scripted rule-engine streams and the API timing) re-runs in minutes on the laptop, so measurements could be repeated whenever the code changed. The batch objective that did "
          "not fit any schedule was a trained intoxication classifier, because it depends on data that must be collected from consenting people under ethical approval, not on development time. "
          "Calendar dates and effort in person-days were not recorded and are not reported."),
        H2("3.5 Legal and ethical considerations"),
        P("A camera pointed at a face raises privacy questions. The system keeps video frames in memory only, logs numbers (state, EAR, closure, roll) rather than images, and sends nothing to "
          "third parties. The offline research pipeline accepts only data with an explicit consent flag on every row and with pseudonymous subject identifiers, and the README warns that the flag cannot "
          "verify real consent. The public CEW images used for evaluation are research data released by their creators; they were used for measurement only and are not copied into the repository. "
          "Because safety is involved, the interface says on every page that a camera cannot confirm alcohol and that Normal does not mean fit to ride, and the system never controls a vehicle."),
        H2("3.6 Advantages and constraints"),
        B("**Advantages:** no sensor to wear or blow into; runs on a laptop CPU; every output comes with a reason and the measurements behind it; refuses to guess in poor conditions; "
          "reproducible by one script; thresholds adjustable and calibrated per rider; numeric-only logging.",
          "**Constraints:** no intoxication data, so no trained classifier and no alcohol claim; strict quality gates reduce availability in dim light; visible eyes are required (no sunglasses or visors); "
          "stationary demonstration only; one shared demo account; no prevention action."),
    ]

    ch4 = [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing system and its limitations"),
        P(f"Today impairment is judged at the roadside by an officer, with standardised field sobriety tests that include an eye test {n(18)} and with breath testers; neither monitors a rider "
          "during the journey. Vehicle-based alternatives such as breath-alcohol interlocks add hardware and can be bypassed by asking another person to blow, and the research prototypes surveyed in "
          f"Chapter 2 need purpose-collected data, a GPU, a thermal camera or a worn device {n(2, 3, 5, 8)}. The project started from a desktop prototype written in Python and Tkinter "
          "(`app.py`, `core.py`, `vision.py`, `storage.py`, `research.py`) that already contained the rule engine, the landmark extraction, the calibration, the history and the offline research tools."),
        B("**Roadside testing:** occasional, needs an officer, cannot watch a whole journey.",
          "**Hardware sensors and interlocks:** extra cost, can be bypassed, act only at start-up.",
          "**Research detectors:** need GPUs, thermal cameras, wearables or scraped data; seldom a runnable system with explanations.",
          "**The original prototype:** a single-machine Tkinter window; no web interface, no login, no API, so it could not be demonstrated in a browser or tested over HTTP."),
        H2("4.2 Proposed system and its advantages"),
        P("The proposed system keeps the original decision code unchanged and adds a FastAPI service and a React web application over it, with the browser camera as the video source. It "
          "keeps the desktop application working on the same data. It watches the eyes and head, runs seven quality checks before any rule, calibrates the EAR threshold per rider, and warns of "
          "possible impairment or drowsiness with the reason shown. It is a warning system, not an alcohol detector."),
        B("A three-state output, including Unable to assess, with the reason and the measurements for every state.",
          "Quality gates that take precedence over every rule, so a bad picture never produces a warning.",
          "A numeric, local event history with search, filter, chart and CSV export, and no stored images.",
          "A demonstration mode with four scripted scenarios, labelled as simulation everywhere.",
          "An offline research path that refuses to train without suitable consented data and flags synthetic reports.",
          "Reproducible measurements and automated tests, so the numbers in this report can be regenerated."),
        H2("4.3 Functional requirements"),
        TAB("Functional requirements", ["ID", "Requirement", "Priority"], FUNCTIONAL, widths=[0.5, 4.8, 0.8], align=["c", "l", "c"], size=9.5),
        H2("4.4 Non-functional requirements"),
        TAB("Non-functional requirements and how each is verified", ["Quality", "Requirement", "Evidence"], NONFUNCTIONAL, widths=[1.1, 2.7, 2.5], size=9),
        H2("4.5 Hardware requirements"),
        TAB("Hardware", ["Item", "Used for development and every measurement", "Note"], [
            ["Processor", F.HW["cpu"], "CPU only; no GPU was used"],
            ["Memory", F.HW["ram"], "Not measured at the limit"],
            ["Graphics", F.HW["gpu"], "Not required"],
            ["Camera", "Laptop webcam (640 x 480 requested)", "Frames are resized to 640 x 480"],
            ["Storage", "About 370 MB for the Python environment; the landmark model is about 3.7 MB", "Event history is a few kilobytes"],
            ["Display", "1440 x 900 reference screenshots; layouts also captured at 360 px", "Any modern browser"],
            ["Minimum machine", "Not measured", "Only the machine above was tested"],
        ], widths=[1.2, 3.0, 2.1]),
        H2("4.6 Software requirements"),
        TAB("Software", ["Layer", "Software"], [
            ["Operating system", f"{F.HW['os']} (development and measurement)"],
            ["Language and runtime", f"Python {F.HW['python']} (3.12 or newer required by the pinned packages); Node.js 18 or newer"],
            ["Vision and numerics", f"MediaPipe {F.HW['mediapipe']} Face Landmarker, opencv-contrib-python 5.0.0.93, NumPy 2.5.3, Matplotlib 3.11.2"],
            ["Desktop interface", "Tkinter (Python standard library)"],
            ["Web back end", "FastAPI 0.162.0 with uvicorn 0.54.0, python-multipart 0.0.32, httpx 0.28.1, Pillow 13.0.0"],
            ["Database", "SQLite (Python standard library)"],
            ["Front end", "React 18, React Router 7, TanStack Query 5, Recharts 3, Tailwind CSS 4, Vite 8, TypeScript 5.9, Framer Motion and GSAP for motion"],
            ["Testing", "unittest, FastAPI TestClient, Playwright for the screenshot and layout scripts"],
        ], widths=[1.6, 4.7]),
        H2("4.7 User roles"),
        TAB("Roles", ["Role", "Description", "Access"], [
            ["Rider or demonstrator", "Signs in, starts a camera or a simulation, calibrates, monitors and reads the state and its reason", "Monitor, history, thresholds, about"],
            ["Reviewer or researcher", "Reads the event history, exports CSV, runs the offline evaluation on a consented dataset", "History, research"],
            ["Developer", "Runs the tests and measurement scripts, edits thresholds and code", "Command line (`scripts/`, `run.bat`)"],
        ], widths=[1.6, 3.2, 1.5]),
        H2("4.8 Constraints"),
        B("The camera must see both eyes clearly; sunglasses, visors, dark or reflective eyewear and a covered eye stop the assessment by design.",
          "The prototype is for stationary demonstration. It has not been tested on a moving vehicle, with a helmet, at night or with vibration.",
          "No intoxication data exist in the project, so nothing in the system establishes alcohol use and no accuracy for intoxication can be given.",
          "Browsers allow webcam access only on localhost or HTTPS.",
          "One shared demo account; there is no user registration."),
    ]
    return ch3 + ch4
