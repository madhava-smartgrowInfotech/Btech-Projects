"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

import os

from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from . import facts as F

# Screenshots already placed in Chapter 5 and (by agreement with the Chapter 8 author) in the Results chapter.
CH5_USED = {"07_monitor_idle.png", "13_about.png"}
CH8_ASSUMED = {"04_monitor_simulation_warning.png", "06_monitor_camera_normal.png", "08_history.png", "12_research_report.png"}


def source(rel, start, end=None, strip_docstring=False):
    """Return the text of a source file from the line containing `start` up to (not including) the line containing `end`."""
    path = os.path.join(F.CODE, rel)
    lines = open(path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    a = next(i for i, l in enumerate(lines) if start in l)
    b = len(lines)
    if end:
        b = next(i for i in range(a + 1, len(lines)) if end in lines[i])
    chunk = lines[a:b]
    while chunk and not chunk[-1].strip():
        chunk.pop()
    return "\n".join(chunk)


def code_blocks():
    s = source
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings below are extracted from the repository by the document build script, so they are the code that was tested and measured. "
          "File paths are relative to `8.ProjectCode`. The decision logic is in `core.py`, the image and landmark handling in `vision.py`, "
          "the storage in `storage.py`, the web session glue in `backend/session.py` and `backend/main.py`, and the offline study tool in `research.py`."),
        H2("A.1 Settings and their bounds (`core.py`)"),
        CODE("@dataclass\n" + s("core.py", "class Settings", "@dataclass")),
        H2("A.2 Eye aspect ratio and head roll (`core.py`)"),
        CODE(s("core.py", "def eye_aspect_ratio", "class RiskEngine")),
        H2("A.3 The rule engine (`core.py`)"),
        CODE(s("core.py", "class RiskEngine", "class Calibration")),
        H2("A.4 Calibration (`core.py`)"),
        CODE(s("core.py", "class Calibration", "def simulate")),
        H2("A.5 Image-quality checks and landmark geometry (`vision.py`)"),
        CODE(s("vision.py", "class Vision", "class CameraWorker")),
        H2("A.6 Event log and settings storage (`storage.py`)"),
        CODE(s("storage.py", "class Store")),
        H2("A.7 Session logic of the web layer (`backend/session.py`)"),
        P("`consume` is the web counterpart of the desktop application's method of the same name: it feeds one observation to calibration or to the rule engine and logs events."),
        CODE(s("backend/session.py", "    def consume(self, o):", "    def _watchdog")),
    ]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Windows 10 or 11, Python 3.12 or newer on PATH (the pinned packages were tested on Python 3.14; `run.bat` prefers `py -3.14` when it exists), and Node.js 18 or newer on PATH.",
          "About 1 GB of disk space for the Python environment (OpenCV, MediaPipe, NumPy, Matplotlib, FastAPI) and the front-end packages, and a modern Chrome or Edge browser.",
          "A webcam for the live path; the simulation scenarios need no camera.",
          "Internet access once, to install packages and download Google's landmark model (about 3.7 MB); normal operation is local."),
        H2("B.2 One-click start"),
        N("Open the folder `8.ProjectCode` and double-click `run.bat`, or run it from a terminal in that folder.",
          "The script rebuilds `.venv` if it was copied from another computer, installs `requirements.txt` and `backend/requirements.txt`, downloads `models/face_landmarker.task` if it is missing, and runs `npm install` in `frontend/` on first use.",
          "It starts the API in its own window (port 8306) and the web application (port 5306) and opens http://localhost:5306 after a few seconds. Use Chrome or Edge on `localhost`: browsers allow webcam access only there or on https.",
          "Sign in with the demo account shown on the sign-in page: `demo@smartrider.app` / `Demo@1234`.",
          "Stop everything by closing the API window and pressing Ctrl+C in the web window."),
        P("The ports, the demo credentials and the token secret are set in `.env` (copy `.env.example` if it is missing). The interactive API documentation is at http://127.0.0.1:8306/docs."),
        H2("B.3 Manual start"),
        CODE("py -3.14 -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt -r backend/requirements.txt\npython setup_model.py                                              # once\npython -m uvicorn backend.main:app --host 127.0.0.1 --port 8306   # terminal 1\ncd frontend && npm install && npm run dev                          # terminal 2"),
        P("The original desktop application still works: `.venv\\Scripts\\python.exe app.py`, or with `--simulation` to start straight in simulation. Both front ends share `data/events.sqlite3` and `data/settings.json`."),
        H2("B.4 Using the application"),
        TAB("Walk-through", ["Step", "Action", "Result"], [
            ["1", "Open http://localhost:5306, choose **Sign in** and use the demo account", "The Monitor screen opens"],
            ["2", "Without a camera: choose **Simulation mode**, pick a scenario (Normal, Prolonged eye closure, Missing face, Poor lighting) and press **Start monitoring**", "The state card, measurement tiles and EAR chart update; simulated data are labelled SIMULATION"],
            ["3", "With a camera: press **Start camera** and allow the browser prompt", "A live preview with the eye points drawn on it; signal quality is shown"],
            ["4", "Press **Calibrate**, look forward with eyes naturally open and keep still for 8 to 15 seconds", "A progress bar runs; the personal EAR threshold is saved (the default 0.21 is kept if it fails)"],
            ["5", "Press **Start monitoring**", "After about 2 seconds of good signal the state becomes Normal; sustained closure shows Possible impairment or drowsiness with its reason"],
            ["6", "Turn on **Alert sound** if wanted", "Three short beeps when a warning fires, at most once per cooldown"],
            ["7", "Open **Event history**; filter live or simulation, search, sort, or **Export CSV**", "The table and chart update; a CSV downloads"],
            ["8", "Open **Thresholds**; change a value and **Save**; a value outside its range shows an error", "Saving stops monitoring and clears the calibrated flag"],
            ["9", "Open **Research**; use the synthetic sample or upload a consented CSV and held-out subject IDs", "A report appears; reports from the sample are marked Synthetic data"],
            ["10", "Open **How it works**", "Pipeline, formulas, quality gates, limits"],
        ], widths=[0.5, 3.6, 2.2], size=9.5, align=["c", "l", "l"]),
        P("Always remember the limits shown in the sidebar: a camera cannot confirm alcohol consumption, Normal does not mean fit to ride, and this is a stationary demonstration prototype."),
        H2("B.5 Command-line tools"),
        CODE("python setup_model.py                                   # download the landmark model and print its SHA-256\npython camera_check.py                                   # bounded webcam and model diagnostic, saves no frames\npython extract_video.py clip.mp4 frames.csv --subject S01 --session s1 --label normal --consent\npython research.py measurements.csv --test-subjects S05 S06 --output research_results"),
        P("`extract_video.py` turns an existing consented, labelled video into the measurement CSV; `research.py` trains and evaluates the nearest-centroid classifier with held-out subjects. "
          "Neither is used by the live rules."),
        H2("B.6 Running the tests and measurements"),
        CODE("python -m unittest discover -s tests -v          # 20 unit tests\npython scripts/smoke_test.py                          # 34 API checks in temporary storage\npython scripts/measure_cew.py --cew <CEW 100x100 folder>   # EAR eye-state and robustness measurements\npython scripts/measure_rules.py                       # rule engine on scripted streams\npython scripts/measure_api.py --face <face.jpg>       # API latency\npython scripts/capture_screens.py --video face.y4m    # regenerate docs/screenshots (needs the app running and Playwright)"),
        H2("B.7 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Fix"], [
            ["\"Can't reach the Smart Rider server\"", "The API window is not running or is still starting. Wait a few seconds or run `run.bat` again."],
            ["Camera permission message", "Allow the camera in the address bar and close other programs that use the webcam."],
            ["\"Landmark model missing\" badge", "Run `python setup_model.py` (needs internet once). Simulation works without it."],
            ["Signal quality stays Poor lighting or No face", "Face the camera, light your face from the front and keep both eyes in view. The gates are deliberately strict: the system will not guess."],
            ["Port already in use", "`netstat -ano | findstr :5306`, then `taskkill /PID <pid> /F`, or change the ports in `.env`."],
            ["Signed out unexpectedly", "The demo token lasts 12 hours, and changing `AUTH_SECRET` invalidates it. Sign in again."],
        ], widths=[2.3, 4.0], size=9.5),
    ]


def _mobile_composite():
    """The four 360 x 740 phone-width captures side by side, written once to docs/figures/_crops."""
    from PIL import Image

    names = ["mobile_landing.png", "mobile_monitor.png", "mobile_history.png", "mobile_research.png"]
    out = os.path.join(F.FIGS, "_crops", "mobile_screens.png")
    if os.path.exists(out) and os.path.getmtime(out) >= max(os.path.getmtime(F.shot(n)) for n in names):
        return out
    os.makedirs(os.path.dirname(out), exist_ok=True)
    ims = [Image.open(F.shot(n)).convert("RGB") for n in names]
    gap = 24
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    h = max(i.height for i in ims)
    sheet = Image.new("RGB", (w, h), (255, 255, 255))
    x = 0
    for im in ims:
        sheet.paste(im, (x, 0))
        x += im.width + gap
    sheet.save(out)
    return out


SHOTS = [
    ("01_landing_dark.png", "Landing page, dark theme: the headline, a live scripted-simulation card showing the rule engine's state, and the three outputs the system can give"),
    ("02_landing_light.png", "Landing page, light theme"),
    ("03_login.png", "Sign-in screen with the demo account box and a one-click button to use it"),
    ("05_monitor_calibrating.png", "Monitor screen during calibration: the progress bar and the count of usable frames (19 of 19 so far); monitoring is stopped, so the tiles show raw readings and the state is Unable to assess"),
    ("09_thresholds_validation.png", "Thresholds screen rejecting a closure time of 9 s with the message that it must be between 0.5 and 5; the stored EAR threshold 0.183 came from a calibration, and a toast from an earlier action is still visible"),
    ("10_thresholds.png", "Thresholds screen after reset: the six default values, the Not calibrated badge, and the confirmation that monitoring was stopped"),
    ("11_research_empty.png", "Research screen before any evaluation: the required CSV columns, the synthetic-sample buttons, the held-out subject field and the Model not trained badge"),
    ("14_about_formulas.png", "How it works screen, Formulas and rules tab: the six formulas, the three warning rules and the default values with their ranges"),
    ("15_monitor_light.png", "Monitor screen in the light theme before a source is chosen"),
]


def screens_blocks():
    out = [H1("APPENDIX C: ADDITIONAL SCREENS")]
    out.append(P("All screenshots are captures of the running application at 1440 x 900 (the phone-width ones at 360 x 740), taken with the scripted simulation, a real face photograph as the "
                 "browser's fake webcam, and the synthetic research sample, which the screen itself labels as synthetic. The main output screens are in Chapter 8; this appendix "
                 "holds the rest."))
    for f, cap in SHOTS:
        if f in CH5_USED or f in CH8_ASSUMED:
            continue
        if os.path.exists(F.shot(f)):
            out.append(FIG(F.shot_view(f), cap, F.shot_w(F.shot_view(f), 5.6)))
    mob = _mobile_composite()
    out.append(FIG(mob, "Phone-width layouts (360 x 740) of the landing page, the monitor, the event history and the research screen", 6.0))
    return out
