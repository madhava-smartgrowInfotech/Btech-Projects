"""Appendices A (important code), B (installation and user guide) and C (additional screens) for SentinelFlow."""
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB


def src(rel, a, b):
    """Lines a..b (1-based, inclusive) of a repository file, exactly as they stand in 8.ProjectCode."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    return "\n".join(lines[a - 1:b])


APP = "app.py"
SEV = "security/severity.py"
DST = "security/distributed_analysis.py"
MIT = "security/mitigation.py"
AGG = "monitoring/traffic_aggregator.py"
FEA = "ml/features.py"
TRN = "ml/train_model.py"


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The key functions are copied from `8.ProjectCode` in the state in which the results were measured (whole statements; the full files are in the repository)."),
        H2("A.1 The per-window pipeline (`app.py`)"),
        CODE(src(APP, 55, 113), 7.5),
        H2("A.2 Severity assessment (`security/severity.py`)"),
        CODE(src(SEV, 4, 78), 7.5),
        H2("A.3 Distributed-risk score (`security/distributed_analysis.py`)"),
        CODE(src(DST, 12, 45), 7.5),
        H2("A.4 Mitigation policy and quarantine (`security/mitigation.py`)"),
        CODE(src(MIT, 32, 72), 7.5),
        H2("A.5 Packet aggregation into the ten features (`monitoring/traffic_aggregator.py`)"),
        CODE(src(AGG, 14, 65), 7.5),
        H2("A.6 Feature validation (`ml/features.py`)"),
        CODE(src(FEA, 39, 59), 7.5),
        H2("A.7 Window augmentation and model fit (`ml/train_model.py`)"),
        CODE(src(TRN, 168, 187) + "\n    ...\n" + src(TRN, 304, 318), 7.5),
    ]


def guide_blocks():
    a, w = F.API_PORT, F.WEB_PORT
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        P("Windows 10 or 11 (or a modern Linux distribution), Python 3.11 or 3.12 on PATH, Node.js 20 or newer for the React console, and a modern browser. About 1 GB of disk is enough; no GPU is needed. "
          "Live capture additionally needs Npcap (https://npcap.com) on Windows and an Administrator (or root) terminal; Simulation Mode needs neither. No dataset download is required: if CICIDS2017 files are absent, training uses the labelled synthetic fallback."),
        H2("B.2 One-click start"),
        N("Open the `8.ProjectCode` folder and double-click `run.bat`; a command window opens and stays open.",
          "The script creates `.env` (ports) if missing, creates `.venv` and installs `requirements.txt`, trains the model only if `models/sentinelflow_rf.joblib` is missing (about 22 seconds for the shipped configuration), runs `npm install` on the first start, starts the API in a minimised window and the console in the main window.",
          f"The browser opens http://127.0.0.1:{w}. Sign in with `{F.DEMO_EMAIL}` / `{F.DEMO_PASSWORD}` (the login page has a Fill demo credentials button). To stop, press Ctrl+C in the main window and close the SentinelFlow API window.",
          f"The original server-rendered dashboard remains available at http://127.0.0.1:{a}/."),
        H2("B.3 Manual start"),
        CODE("python -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt\npython ml\\train_model.py        # only if models\\ is empty\n"
             f"python app.py                    # terminal 1: API on {a}\n\ncd frontend\nnpm install\nnpm run dev                      # terminal 2: console on {w}\n\n"
             "# production-style build\ncd frontend && npm run build && npm run preview", 8.5),
        H2("B.4 Using the console"),
        TAB("Screens and how to use them", ["Screen", "What to do", "What to look for"],
            [["Overview", "Choose an interface and a window length; press Start simulation (works everywhere) or Start live (needs Npcap and Administrator); press Stop to end", "Mode pill and Simulation banner; capture-problem banner if live capture cannot start; six cards; packet-rate sparkline; latest windows"],
             ["Detections", "Filter, sort, click a row", "Prediction, confidence, severity, sources, destinations, mitigation; the drawer lists the severity factors and the recommendation"],
             ["Analytics", "Watch the donut and bars grow", "Benign versus attack counts, severity distribution, packet-rate timeline"],
             ["Network health", "Leave it open", "CPU, memory, bytes and packets in and out"],
             ["Mitigation", "Watch countdown bars", "Active quarantines with seconds left, history, quarantine length"],
             ["Model", "Read the metrics", "Accuracy, precision, recall, F1, ROC-AUC; the SYNTHETIC TRAINING DATA warning; confusion matrix, importance, plots"],
             ["Settings", "Change window (2-120 s) or quarantine length (5-3600 s) and save", "Validation messages for out-of-range values"]],
            widths=[1.2, 2.6, 2.8], align=["l", "l", "l"], size=9.0),
        P("Keyboard: `/` opens search, `g` then `o`, `d`, `a`, `n`, `m`, `p` or `s` jumps between screens, `?` lists the shortcuts, `Esc` closes an overlay; the sun and moon button toggles the dark theme."),
        H2("B.5 Retraining on real CICIDS2017 files"),
        N("Download the MachineLearningCSV files of CICIDS2017 (for example the Friday-WorkingHours-Afternoon-DDos CSV) and place them in `8.ProjectCode/data/raw/`.",
          "Run `python ml/train_model.py`. The script reads every CSV in `data/raw`, maps it to the ten features, adds the 6,000 window-scale rows, trains the Random Forest and rewrites `models/` and `results/`; the provenance in `metadata.json` then names CICIDS2017 and the Model screen no longer shows the synthetic warning.",
          "Restart the API so that the new model is loaded. Rows are capped at 120,000 for practical training time."),
        H2("B.6 Checks"),
        CODE("python -m pytest tests                  # 95 tests on a scratch SQLite file\npython scripts\\smoke_test.py             # 25 backend checks (+3 proxy checks if the console runs)\n"
             "python scripts\\run_experiments.py all    # the measurements in this report (needs the CICIDS2017 file; CICIDS_CSV)\npython scripts\\measure_api.py http://127.0.0.1:8415   # use a scratch copy of the backend", 8.5),
        H2("B.7 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Fix"],
            [["Live start fails with a driver message mentioning winpcap or Npcap", "Install Npcap, run the terminal as Administrator, or use Simulation Mode"],
             ["Capture permission denied", "Run as Administrator (Windows) or root (Linux)"],
             ["Port already in use", "Change BACKEND_PORT or FRONTEND_PORT in `.env` and start again"],
             ["Model not trained message", "Run `python ml/train_model.py`"],
             ["Many Attack labels on quiet benign windows with short windows", "Use the default 10-second window; the model was calibrated on it"],
             ["sklearn InconsistentVersionWarning when loading the model", "The model was saved with scikit-learn 1.9.0 and is loaded with 1.9.1; it is only a warning. Retrain to remove it"],
             ["Console shows no data", "Press Start simulation; check that the API window is running on the configured port"]],
            widths=[3.0, 3.6], align=["l", "l"], size=9.5),
    ]


def screens_blocks():
    SH = lambda n: os.path.join(F.CODE, "screenshots", n)  # noqa: E731
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("The captures below are of the original server-rendered dashboard that the Flask application still serves at `/` (the screens of the React console are in Chapter 8). They were taken in Simulation Mode with the real model scoring simulated windows. "
          "Three further captures (01, 02 and 03) are not shown: the full-page capture has the sticky header drawn in the middle of the page and the network-health and analytics crops are cut by the header; the same information is on the console screens of Chapter 8. "
          "The file names of captures 05, 06 and 07 do not match their content (for example the file called model_performance shows the Mitigation Center), so the captions below describe what each image shows."),
        PAIR([(SH("04_live_table.png"), "Original dashboard: live detection table (simulation, real inference)."),
              (SH("05_threat_and_mitigation.png"), "Original dashboard: Threat Detail of a Critical window with its factors and recommendation.")], 3.0),
        P("The live table shows the same columns as the console's Detections screen: time, interface, source, prediction, confidence, severity, sources, destinations, packets per second and mitigation. "
          "Weak benign windows have confidences of 56 to 78 %, Medium windows carry the rate-limit recommendation, and High and Critical windows carry a quarantine. "
          "The Threat Detail shows 1,592 packets per second from 37 sources to 8 destinations scored Critical (85) with five severity factors, and states that quarantines auto-expire."),
        PAIR([(SH("06_model_performance.png"), "Original dashboard: Mitigation Center with active quarantines (seconds left) and history."),
              (SH("07_settings.png"), "Original dashboard: Model Performance with the dataset-provenance note, confusion matrix, ROC curve and feature importance.")], 3.0),
        P("The Mitigation Center lists active quarantines with the seconds left (4 to 72 in the capture) and a history of the latest actions. The Model Performance panel shows the synthetic-fallback provenance sentence "
          "directly under the headline figures, which is why the original dashboard, unlike the React landing page, never presents 99.71 % without its caveat."),
        FIG(SH("07_simulation_mode.png"), "Original dashboard: header with the Simulation Mode pill, interface selector and Start live, Start simulation and Stop buttons.", 6.0),
        P("The header shows the Simulation Mode pill and the interface list; in this capture the first interface is a Bluetooth network connection, showing that interface names come from the operating system rather than from the application."),
    ]
