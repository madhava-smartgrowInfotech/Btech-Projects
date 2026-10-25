"""Appendices A (important code), B (installation and user guide) and C (additional screens) of the ResQAI report.

The code listings are read from the repository at build time (by function name or by anchor lines), so they always match the shipped files.
"""

import ast
import os

from . import facts as F
from .blocks import B, CODE, H1, H2, N, P, PAIR, TAB


def _read(rel):
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as fh:
        return fh.read()


def src_fn(rel, name):
    """Source of a top-level function, exactly as written in the file (decorators included)."""
    text = _read(rel)
    tree = ast.parse(text)
    lines = text.split("\n")
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            start = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1
            return "\n".join(lines[start:node.end_lineno])
    raise KeyError(f"{name} not found in {rel}")


def src_between(rel, first, last=None, include_last=True):
    """Lines from the first line containing `first` to the first later line containing `last` (or to the end of the block when last is None)."""
    lines = _read(rel).split("\n")
    a = next(i for i, ln in enumerate(lines) if first in ln)
    if last is None:
        return "\n".join(lines[a:a + 1])
    b = next(i for i in range(a, len(lines)) if last in lines[i])
    return "\n".join(lines[a:b + (1 if include_last else 0)])


def code_blocks():
    mon = "frontend/src/state/MonitorContext.jsx"
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from the repository (`8.ProjectCode`) in the state in which the results of this report were measured. Comments are kept as they are; the listings are whole functions or whole blocks. "
          "Long functions are cut at a natural boundary and the cut is stated in the heading."),
        H2("A.1 Synthetic data generator (`train_models.py`)"),
        CODE(src_fn("train_models.py", "generate_dataset"), 7.5),
        CODE(src_between("train_models.py", 'elif kind == "moderate_crash":', "severity = 2", True) + "\n    # ... the other four kinds follow the same pattern; magnitudes and spreads are listed in Chapter 6", 7.5),
        H2("A.2 Training the two models (`train_models.py`, from `main`)"),
        CODE(src_between("train_models.py", "scaler = StandardScaler()", "severity_clf.fit"), 7.5),
        H2("A.3 Feature vector, prediction and the detector gate (`app.py`)"),
        CODE(src_fn("app.py", "build_feature_vector"), 7.5),
        CODE(src_fn("app.py", "predict_from_features"), 7.5),
        H2("A.4 Hospital ranking and the dispatch message (`app.py`)"),
        CODE(src_fn("app.py", "haversine_km"), 7.5),
        CODE(src_fn("app.py", "nearest_hospitals"), 7.5),
        CODE(src_between("app.py", "message = (", 'message += "No response received'), 7.5),
        H2("A.5 Login with lockout (`auth.py`)"),
        CODE(src_fn("auth.py", "login"), 7.5),
        H2("A.6 Confirmation countdown and dispatch (`frontend/src/state/MonitorContext.jsx`)"),
        CODE(src_between(mon, "if ((r.severity_label === 'Moderate'", "setLive(false)"), 7.5),
        CODE(src_between(mon, "const sendAlert = useCallback", "}, [logEvent, toast])"), 7.5),
        CODE(src_between(mon, "// Countdown ticks while an alert is pending", "}, [pending, countdown, sendAlert])"), 7.5),
    ]


def _env_rows():
    return [["`BACKEND_PORT` / `FRONTEND_PORT`", f"{F.API_PORT} / {F.WEB_PORT}", "ports of the Flask API and the Vite server (`.env`)"],
            ["`REQUIRE_AUTH`", "0", "1 makes the API reject calls without a login token (the original dashboard then stops working)"],
            ["`SECRET_KEY`", "generated once into `data/.secret`", "key that signs login tokens; set it for any shared use"],
            ["`PORT`", "5000 when `app.py` is run by hand", "set by `run.bat` from `BACKEND_PORT`"]]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Windows 10 or 11 with **Python 3.10 or later** and **Node.js 18 or later** on the PATH.",
          "Free disk space for the Python packages and `node_modules`, and some free memory: the Flask reloader starts a second Python process, and the measurements in this report were disturbed by out-of-memory errors on a machine with little free RAM.",
          "A current Chrome, Edge or Firefox. Internet access is needed only for map tiles and fonts; detection and dispatch composition work offline."),
        H2("B.2 Installation"),
        N("Open the `8.ProjectCode` folder in a terminal or Explorer.",
          "Run `setup.bat` once. It creates `venv`, installs `requirements.txt` (Flask, scikit-learn, joblib, NumPy, pandas), runs `npm install` in `frontend/` and copies `.env.example` to `.env`.",
          "Optional: run `python train_models.py` to regenerate the four model files in `models/`. The shipped pickles were written by scikit-learn 1.9.0; `requirements.txt` does not pin a version, so retraining after set-up avoids any version difference.",
          f"Run `run.bat`. It starts the API on port {F.API_PORT} and the web app on port {F.WEB_PORT} in two windows and opens `http://localhost:{F.WEB_PORT}`.",
          "Stop everything with `stop.bat` or by closing the two windows."),
        TAB("Settings in `.env`", ["Variable", "Default", "Meaning"], _env_rows(), widths=[2.0, 1.7, 2.7], size=9),
        H2("B.3 Using the console"),
        N("On the landing page press **Sign in**, then **Create an account** the first time (name, e-mail, a password of 8 to 128 characters). The console screens open only after sign-in.",
          "**Live monitor.** Press a scenario button (Normal driving, Harsh brake, Minor crash, Moderate crash, Severe crash) to send one simulated reading through the models, or switch on **Start live monitoring** for one random reading every 1.5 seconds. The result panel shows the verdict, the severity, the accident probability and the features; the chart shows the last 40 readings and the event log the last 25 events.",
          "**Confirmation.** A Moderate or Severe result opens *Possible accident detected* with a 15-second countdown. Press **I'm fine, cancel** (or Escape) if it is a false alarm; press **Send alert now** or wait to dispatch. Live monitoring pauses while the dialog is open and must be switched on again afterwards.",
          "**Dispatch.** The *Emergency alert dispatched* dialog shows the alert id and the drafted message (with a copy button). Choose **View on map** for the **Emergency response** screen: the accident, the three nearest hospitals, a dispatch summary, a call button for the nearest hospital and the numbers 108, 112 and 103. No message is actually sent.",
          "**Manual override.** Type values for the three accelerations, the gyroscope magnitude, the speed before, the speed change and the jerk, or press **Load simulated sample** and edit it, then **Run detection**. The derived acceleration magnitude is shown above the buttons.",
          "Use the moon / sun button for the dark or light theme and **Sign out** to lock the console again."),
        H2("B.4 Interpreting the result"),
        TAB("Reading the verdict", ["Shown", "Meaning", "What happens next"],
            [["No accident, severity None", "the detector says the reading is not a crash (normal driving, harsh braking)", "logged only"],
             ["Accident, severity Minor", "a crash-like spike graded Minor", "logged only; no countdown"],
             ["Accident, severity Moderate / Severe", "a crash-like spike graded Moderate or Severe", "15-second countdown, then dispatch unless cancelled"],
             ["Accident probability", "the average of the 200 detector trees' class probabilities for *accident*", "it is not the probability that the severity grade is right"],
             ["Model: Trained ML model / rule-based fallback", "which engine answered", "the fallback appears only if the model files are missing"]],
            widths=[1.8, 2.8, 1.8], size=9),
        H2("B.5 Checks and troubleshooting"),
        TAB("Commands and common problems", ["Task or problem", "What to do"],
            [["Check that everything works", "with the app running: `python scripts/smoke_test.py` (33 checks)"],
             ["Run the unit, edge-case and security checks", "start a second API with `REQUIRE_AUTH=1` on port 8399, then `python scripts/run_tests.py`"],
             ["Regenerate the metrics and the latency numbers", "`python scripts/measure_metrics.py` and `python scripts/measure_api.py` (write to `experiments/resqai_eval/`)"],
             ["Port already in use", f"run `stop.bat`, or change `BACKEND_PORT` / `FRONTEND_PORT` in `.env` (ports {F.API_PORT} and {F.WEB_PORT} by default)"],
             ["*Cannot reach the ResQAI API*", "the Flask window is closed or crashed; start it again with `run.bat` and press Retry"],
             ["Version warning when the API starts", "the pickles come from a newer scikit-learn; run `python train_models.py` to rebuild them"],
             ["API timing is slow in a script", "use `127.0.0.1` instead of `localhost` (IPv6 fallback)"],
             ["No location is used", "allow location access in the browser; otherwise the server picks a point near the default Hyderabad location"],
             ["Out-of-memory errors on a small machine", "close other programs; run the API without the reloader (`debug=False`) for measurements"]],
            widths=[2.2, 4.2], size=9),
    ]


def screens_blocks():
    from . import ch8

    shots = [(n, ch8.CAPTIONS[n]) for n in ch8.APPENDIX_C]
    out = [H1("APPENDIX C: ADDITIONAL SCREENS"),
           P("These screens complete the set of captures described in Chapter 8: theme variants, the sign-in error, registration, the manual form, the response map before any alert and the not-found page. "
             "All were captured at 1440 by 900 pixels from the running application with the demo account, with readings produced by the real models.")]
    for i in range(0, len(shots), 2):
        out.append(PAIR([(F.shot(n), c) for n, c in shots[i:i + 2]], 2.9))
    return out
