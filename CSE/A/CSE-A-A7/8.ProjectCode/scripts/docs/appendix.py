"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB


def src(rel, a, b):
    """Lines a..b (1-based, inclusive) of a repository file, exactly as they stand in 8.ProjectCode."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    return "\n".join(lines[a - 1:b])


EX = "backend/app/services/extract.py"
TR = "backend/app/services/triage.py"
FT = "backend/app/services/features.py"
API = "backend/app/routes/api.py"
TRAIN = "ml/train.py"
MK = "ml/make_data.py"


def _code_report():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The key functions are copied from `8.ProjectCode` in the state in which the results were measured (excerpts of whole statements; the full files are in the repository)."),
        H2("A.1 Report reading: negation and the sentence loop (`extract.py`)"),
        CODE(src(EX, 39, 39) + "\n    ...\n" + src(EX, 129, 152) + "\n                ...", 7.5),
        H2("A.2 Fusing the record and predicting the priority (`features.py`, `triage.py`)"),
        CODE(src(FT, 76, 87) + "\n\n" + src(TR, 35, 59), 7.5),
        H2("A.3 Training and calibration (`train.py`)"),
        CODE(src(TRAIN, 28, 45), 7.5),
        H2("A.4 The clinician override route (`routes/api.py`)"),
        CODE(src(API, 185, 199), 7.5),
    ]


def code_blocks():
    if F.REPORT:
        return _code_report()
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from the repository (`8.ProjectCode`) in the state in which the results of this report were measured. Docstrings and comments are kept as they are; "
          "each range is a whole statement or function."),
        H2("A.1 The report lexicon: negation and lab limits (`backend/app/services/extract.py`)"),
        P("Negation is a regular expression that looks back up to 45 characters inside the same sentence; each lab has a name pattern, a flag and a test for an abnormal value."),
        CODE(src(EX, 39, 53), 8),
        H2("A.2 Parsing a report"),
        P("`parse` walks the sentences of every page, reads lab values, matches the lexicon, drops negated matches and keeps the page of each item. A bleed described as intracranial is not "
          "counted as the symptom *bleeding*."),
        CODE(src(EX, 129, 175), 8),
        H2("A.3 The fused record (`backend/app/services/features.py`)"),
        CODE(src(FT, 62, 87), 8),
        H2("A.4 Calibrated prediction and SHAP attribution (`backend/app/services/triage.py`)"),
        P("`predict` builds the fused row, takes the calibrated probabilities, chooses the arg-max class and asks the tree explainer for the contribution of every input towards that class."),
        CODE(src(TR, 35, 73), 8),
        H2("A.5 Training and calibration (`ml/train.py`)"),
        CODE(src(TRAIN, 28, 47), 8),
        H2("A.6 The severity rule of the synthetic dataset (`ml/make_data.py`)"),
        CODE(src(MK, 44, 65), 8),
        H2("A.7 Creating a patient and recording a decision (`backend/app/routes/api.py`)"),
        P("The override route decides between *accept* and *change*, requires a reason for a change, stores the decision and keeps the model's own suggestion."),
        CODE(src(API, 138, 159) + "\n\n" + src(API, 185, 199), 8),
    ]


def _guide_report():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements and start"),
        B("Windows 10 or 11, Python 3.11 or newer and Node.js 18 or newer on the PATH, about 1.5 GB of free disk for the Python environment, and a current browser; internet access is needed for the first installation only "
          f"(measurements used Python 3.11.9 and Node 24.19.0).",
          f"Double-click `run.bat` in `8.ProjectCode`: on a fresh checkout it runs `setup.bat` (creates `venv/`, installs `requirements.txt`, trains the model if missing, generates the sample reports, "
          f"runs `npm install`), then starts the API (http://localhost:{F.API_PORT}) and the web application (http://localhost:{F.WEB_PORT}) in two minimised windows and opens the browser. Close those two windows to stop."),
        TAB("Demo accounts", ["Role", "E-mail", "Password"], [["Clinician", "clinician@athena.health", "Athena@123"], ["Admin", "admin@athena.health", "Athena@123"]],
            widths=[1.4, 3.0, 1.6], size=10, align=["l", "l", "l"]),
        H2("B.2 Using the application"),
        N("Sign in (the buttons on the login page fill the demo accounts). The *Triage queue* opens with twelve labelled sample cases.",
          "Open *New patient*. Pick a sample report (for example *report 01 chest pain stemi*) or drop your own PDF, PNG or JPG; the findings appear with their pages and the vitals fill in for samples.",
          "Check or enter the eight vitals and press *Assign priority*. The *Result* screen shows the priority, confidence, fused record and the *Why this priority* bars.",
          "Press *Accept or change*, choose a priority and give a reason if it differs; the queue reorders. *Summary PDF* downloads the triage summary.",
          "*Performance* shows the evaluation figures (synthetic data) and the live review counts."),
        H2("B.3 Checks and troubleshooting"),
        CODE("venv\\Scripts\\python -m pytest tests                  # 47 tests\n"
             "venv\\Scripts\\python scripts\\smoke_test.py            # 17 checks, API must be running\n"
             "venv\\Scripts\\python ml\\train.py                      # retrain; restart the API afterwards", 8.5),
        B("**\"Cannot reach the ATHENA API\":** the API window is not running; run `run.bat` again.  **Port in use:** another copy is running; close its windows.  "
          "**First scan is slow:** the OCR engine loads on first use; PDFs with a text layer are read instantly.  **Reset:** delete `data\\app.db`."),
    ]


def guide_blocks():
    if F.REPORT:
        return _guide_report()
    return _guide_full()


def _guide_full():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Windows with **Python 3.11 or newer** and **Node.js 18 or newer** on the PATH (the measurements in this report used Python 3.11.9 and Node 24.19.0).",
          "About 1.5 GB of free disk for the Python environment and packages.",
          "Internet access for the first run only (Python and npm packages). The synthetic dataset, the sample reports and the trained model are generated or included by the setup script."),
        H2("B.2 Quick start with run.bat"),
        N("Open the project folder (`8.ProjectCode`) and double-click `run.bat`. On a fresh checkout it first runs `setup.bat`: it creates the `venv/` Python environment and installs "
          "`requirements.txt`, generates the synthetic dataset and trains the model if `models/triage_model.joblib` is missing, generates the sample reports if missing, and runs `npm install` in `frontend/`.",
          f"It then starts the API on http://localhost:{F.API_PORT} and the web application on http://localhost:{F.WEB_PORT} in two minimised windows and opens the browser.",
          "Close the two minimised windows (*ATHENA API* and *ATHENA Web*) to stop the application."),
        H2("B.3 Manual start"),
        CODE("venv\\Scripts\\python -m pip install -r requirements.txt\n"
             "venv\\Scripts\\python ml\\make_data.py        # seeded synthetic dataset (only if data\\sample is missing)\n"
             "venv\\Scripts\\python ml\\train.py            # model and metrics (only if models\\ is empty)\n"
             f"venv\\Scripts\\python -m uvicorn backend.app.main:app --port {F.API_PORT}\n"
             "cd frontend\n"
             "npm install\n"
             "npm run dev                                 # proxies /api to the API", 8.5),
        P("Ports are fixed (API 8307, web 5307; set in `run.bat` and `frontend/vite.config.js`). An optional `.env` can set `DATABASE_URL` and `JWT_SECRET`; without it a local SQLite file and a "
          "development secret are used, which is acceptable for a demonstration only."),
        H2("B.4 Signing in and using the screens"),
        TAB("Demo accounts", ["Role", "E-mail", "Password"], [["Clinician", "clinician@athena.health", "Athena@123"], ["Admin", "admin@athena.health", "Athena@123"]],
            widths=[1.4, 3.0, 1.6], size=10, align=["l", "l", "l"]),
        TAB("Screens and what to do on each", ["Screen", "Route", "What to do"], [
            ["Landing", "/", "Read what ATHENA does and the headline numbers; they are marked as measured on a seeded synthetic dataset."],
            ["Sign in", "/login", "Type credentials or press the *Clinician* or *Admin* button."],
            ["Triage queue", "/app/queue", "See patients sickest first; filter with the priority tabs or the search box; the list refreshes every 15 seconds. A new database holds 12 sample cases."],
            ["New patient", "/app/new", "Pick a sample report or drop a PDF, PNG or JPG (15 MB at most); read the findings with their pages; enter or check the eight vitals; press *Assign priority*."],
            ["Result", "/app/patients/{id}", "Read the priority, risk and confidence, the fused record, *Why this priority* and the probabilities; *Accept or change* records a decision (a reason is required for a change); *Summary PDF* downloads the summary."],
            ["Model performance", "/app/performance", "Read accuracy, within-one accuracy, macro F1, recall per priority, the confusion matrix, seconds per patient and the live review counts."],
        ], widths=[1.2, 1.4, 3.9], size=9.5, align=["l", "l", "l"]),
        H2("B.5 A short demonstration"),
        N("Sign in as the clinician. Open *New patient* and choose *report 01 chest pain stemi* from the sample list. The report is read (two pages), the symptoms, the ST-elevation finding, the history and the abnormal troponin and lactate appear with their page numbers, and the vitals fill in.",
          "Press *Assign priority*. The result shows priority 1 (Critical) with a calibrated confidence, and the bars list ST elevation, troponin and lactate as the strongest factors.",
          "Press *Accept or change*, select priority 2 and type a reason, then *Save change*. The queue now shows the patient as *Changed*, and the performance page counts one review.",
          "Try an image: choose *scan 09 asthma*. The first scan takes a few seconds while the OCR engine starts."),
        H2("B.6 Checks, experiments and retraining"),
        CODE("venv\\Scripts\\python -m pytest tests                  # 47 tests: reading, model, API\n"
             "venv\\Scripts\\python scripts\\smoke_test.py            # 17 checks against the running API\n"
             "venv\\Scripts\\python ml\\eval.py                       # reading and timing -> experiments\\eval\\metrics.json\n"
             "venv\\Scripts\\python scripts\\run_experiments.py       # model comparison, ablation, calibration, robustness\n"
             "venv\\Scripts\\python scripts\\extract_stress.py        # 40-fragment reader stress test\n"
             "venv\\Scripts\\python scripts\\measure_api.py           # HTTP latency (use 127.0.0.1)\n"
             "python scripts\\capture_screens.py                      # regenerate docs\\screenshots (needs Playwright)\n"
             "venv\\Scripts\\python ml\\train.py                      # retrain; restart the API afterwards", 8.5),
        H2("B.7 Troubleshooting"),
        B("**\"Cannot reach the ATHENA API\" in the browser:** the API window is not running. Run `run.bat` again and read the minimised *ATHENA API* window for errors.",
          "**Port already in use:** another copy is running; close its windows first.",
          "**The first scan is slow:** the OCR engine loads on first use (a few seconds); PDFs with a text layer are read at once.",
          "**Package installation fails:** check the connection and run `setup.bat` again.",
          "**Reset the queue and the review log:** stop the application and delete `data\\app.db`.",
          "**Timing over HTTP looks four times too slow:** use `127.0.0.1` instead of `localhost`; on this Windows machine `localhost` added about two seconds per call."),
    ]


def screens_blocks():
    shots = [
        ("01_landing_light.png", "Landing page (light theme): headline, evaluation figures and a scrolling ticker of the key numbers.",
         "The landing page states what ATHENA does and shows four headline figures read from the API: hold-out accuracy, within-one-level accuracy, the number of test cases and the model time per patient. "
         "The note under them says that the figures were measured on a seeded synthetic dataset and not on patient data."),
        ("02_landing_dark.png", "Landing page (dark theme).",
         "The same page in the dark theme. The choice is kept in the browser and the design kit supplies both palettes."),
        ("03_login.png", "Sign-in page with the two demo accounts.",
         "Staff sign in with an e-mail and a password. The dashed panel under the form offers one-click sign-in for the demo clinician and administrator accounts; both use the published demo password."),
        ("05_new_patient_empty.png", "New patient screen before a report is chosen.",
         "The left card takes the scanned report: a drop zone for a PDF, PNG or JPG of up to 15 MB, or a list of generated sample reports. The right card takes the eight vitals and an optional patient label. "
         "A note says that triage on vitals alone is possible but that findings from the report will then be missing."),
        ("09_override_modal.png", "The accept-or-change dialog on the result screen.",
         "The clinician chooses a priority and types a reason, which is mandatory when the priority differs from the current one. Saving writes an override row with the clinician's name, and the model's original suggestion is kept."),
        ("11_queue_updated.png", "Triage queue after a clinician changed a priority.",
         "The queue lists patients sickest first and ties by arrival time, with the main drivers, the risk level, the confidence and the clinician status. The first patient carries the *Changed* badge, the others are pending sample cases."),
    ]
    out = [H1("APPENDIX C: ADDITIONAL SCREENS"),
           P("These screens complete the set of real captures of the running application (1440 x 900, with the seeded sample queue and one live patient). The screens used in Chapter 8 "
             "(queue, filled form, result, SHAP explanation, decision and performance) are not repeated here. All model figures shown in them come from the synthetic dataset.")]
    if F.REPORT:
        pairs = [(shots[0], shots[2]), (shots[3], shots[4])]
        for a, b in pairs:
            out.append(PAIR([(F.shot(a[0]), a[1]), (F.shot(b[0]), b[1])], 2.9))
        out.append(FIG(F.shot(shots[5][0]), shots[5][1], F.shot_w(F.shot(shots[5][0]), 4.6, 3.2)))
        return out
    for i, (fn, cap, text) in enumerate(shots, 1):
        out.append(H2(f"C.{i} {cap.split(':')[0].rstrip('.')}"))
        out.append(P(text))
        out.append(FIG(F.shot(fn), cap, F.shot_w(F.shot(fn), 5.2, 3.6)))
    return out
