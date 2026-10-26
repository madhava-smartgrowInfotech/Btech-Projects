"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB


def src(rel, a, b):
    """Lines a..b (1-based, inclusive) of a repository file, exactly as they stand in 8.ProjectCode."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    return "\n".join(lines[a - 1:b])


SIM = "smart_traffic/sim.py"
PRE = "smart_traffic/predictor.py"
VIS = "smart_traffic/vision.py"
SVC = "backend/service.py"
MAIN = "backend/main.py"
EXP = "scripts/run_experiments.py"


def _code_intro():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The key functions are copied from `8.ProjectCode` in the state in which the results were measured (excerpts of whole statements; the full files are in the repository). "
          "The decision rule and the pressure function of the advanced controller are listed in Chapter 6 and are not repeated here."),
    ]


def _code_common():
    return _code_intro() + [
        H2("A.1 Simulation step, arrivals and discharge (`sim.py`)"),
        CODE(src(SIM, 159, 170) + "\n    ...\n" + src(SIM, 172, 193), 7.5),
        CODE(src(SIM, 311, 342), 7.5),
        H2("A.2 Forecaster features and summary (`sim.py`)"),
        CODE(src(SIM, 358, 380), 7.5),
        H2("A.3 Queue forecaster (`predictor.py`)"),
        CODE(src(PRE, 32, 59), 7.5),
        H2("A.4 YOLOv8 detection with the light-bar rule (`vision.py`)"),
        CODE(src(VIS, 71, 94), 7.5),
    ]


def _code_report():
    return _code_intro() + [
        H2("A.1 Simulation step and arrivals (`sim.py`)"),
        CODE(src(SIM, 159, 170) + "\n    ...\n" + src(SIM, 172, 185), 7.5),
        H2("A.2 Queue forecaster (`predictor.py`)"),
        CODE(src(PRE, 32, 59), 7.5),
        H2("A.3 YOLOv8 detection with the light-bar rule (`vision.py`)"),
        CODE(src(VIS, 71, 94), 7.5),
        H2("A.4 Benchmark service (`service.py`)"),
        CODE(src(SVC, 266, 285), 7.5),
    ]


def code_blocks():
    if F.REPORT:
        return _code_report()
    return _code_common() + [
        H2("A.5 Benchmark endpoint (`main.py`, `service.py`)"),
        CODE(src(MAIN, 146, 175) + "\n    ...\n" + src(SVC, 266, 316), 7.5),
        H2("A.6 Vision payload and synthetic route (`service.py`)"),
        CODE(src(SVC, 337, 360), 7.5),
        H2("A.7 Ablation variants and forecaster validation (`run_experiments.py`)"),
        CODE(src(EXP, 131, 161), 7.5),
    ]


# ------------------------------------------------------------------------------ Appendix B
def guide_blocks():
    out = [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        TAB("Requirements to run FlowSense", ["Item", "Requirement"],
            [["Operating system", "Windows 10 or 11 (the launcher `run.bat` is for Windows; the commands in B.3 work on other systems)"],
             ["Python", "3.10 or newer, with *Add to PATH* ticked (tested with 3.11.9)"],
             ["Node.js", "20 or newer (tested with 24.19) for the React console"],
             ["Memory and disk", "About 8 GB of memory is comfortable; the first run downloads PyTorch (CPU) and Ultralytics, a few hundred MB"],
             ["Network", "Needed for the first install and for the first YOLOv8 run, which downloads `yolov8n.pt` if it is not already in the project folder"],
             ["GPU", "Not needed; everything in this report ran on a CPU"]],
            widths=[1.5, 5.0], align=["l", "l"], size=10),
        H2("B.2 One-click start"),
        N("Open the folder `8.ProjectCode` and double-click **`run.bat`**. On the first run it creates `.venv`, installs `backend/requirements.txt`, tries to install `backend/requirements-yolo.txt` (Ultralytics and PyTorch) and runs `npm install` in `frontend/`.",
          f"Two minimised windows open (*FlowSense API* on port {F.API_PORT}, *FlowSense Web* on port {F.WEB_PORT}) and the browser opens http://localhost:{F.WEB_PORT}. `run.bat nobrowser` starts both without opening the browser.",
          f"Sign in with the demo account printed on the sign-in page: `{F.DEMO_EMAIL}` / `{F.DEMO_PASSWORD}` (set in `.env`; the button *Use demo account* fills the fields).",
          "Wait about 10 seconds after the first start: the forecasting model trains in the background and the sidebar shows *API online - model ready* when it is done.",
          "To stop, close the two windows named *FlowSense*."),
        H2("B.3 Starting by hand and running the checks"),
        CODE("python -m venv .venv\n.venv\\Scripts\\python -m pip install -r backend\\requirements.txt -r backend\\requirements-yolo.txt\n"
             ".venv\\Scripts\\python -m uvicorn backend.main:app --port 8310      # API, run from 8.ProjectCode\n\n"
             "cd frontend\nnpm install\nnpm run dev                                            # console on http://localhost:5310\n\n"
             "python scripts/smoke_test.py http://127.0.0.1:8310                     # 33 end-to-end checks against the running API\n"
             "python -m pytest tests -q                                              # 38 unit and API tests\n"
             "python scripts/run_experiments.py                                      # regenerates experiments/**/metrics.json (about 2 minutes)\n"
             "python scripts/fetch_real_images.py 300 && python scripts/eval_real_vision.py   # real-image vision evaluation\n"
             "python scripts/measure_api.py                                          # API latency (needs the API running)\n"
             "python scripts/make_report_facts.py                                    # docs/REPORT_FACTS.md from the metrics", 8),
        H2("B.4 Settings (`.env`)"),
        TAB("Settings read from `.env`", ["Key", "Default", "Meaning"],
            [["`BACKEND_PORT`, `FRONTEND_PORT`", "8310, 5310", "Fixed so that several products can run side by side"],
             ["`DEMO_EMAIL`, `DEMO_PASSWORD`, `DEMO_NAME`", "operator@flowsense.app, Flow@1234, Control Room Operator", "The demo operator account"],
             ["`JWT_SECRET`", "development key if missing or a placeholder", "Signs the sign-in token; use 32 or more random characters outside a demonstration"]],
            widths=[2.2, 2.2, 2.1], align=["l", "l", "l"], size=9.5),
        H2("B.5 Using the console"),
        TAB("Pages of the console", ["Page", "What to do", "What to look for"],
            [["Landing (public)", "Read the capabilities; press *Sign in*", "A live preview of the advanced controller on a 2x2 grid and a terminal of signal changes"],
             ["Live control", "Choose a controller and a demand level, press *Run live (60 s)* or *Skip 5 min*, then *Send ambulance*; change the grid or the ML forecast in the sidebar", "KPIs, the road map with signal heads and queues, the junction table with the 30 s forecast, and the red banner when pre-emption starts; switch to *Fixed-time* while an ambulance is active to see the banner say it is ignored"],
             ["Benchmark", "Pick duration, demand, number of seeds and start hour, press *Run*; use *Run again* for the demand sweep", "Four controllers on identical traffic; the tiles show reductions against fixed-time and the base-paper-style controller"],
             ["Vision", "Synthetic scene: move the sliders and switch flash frame A/B; YOLOv8 sample photo; YOLOv8 upload (JPG or PNG, up to 12 MB)", "Boxes with class and confidence, magenta ring on a light-bar cluster, density in PCU, congestion level and recommended green time"],
             ["Prediction", "Read the model metrics; if the live forecast is empty press *Simulate 3 minutes now* (or run the Live page for a minute)", "MAE, R2, the comparison with persistence, and the build-up warning"],
             ["Violations", "Press *Simulate 10 more minutes*", "Counts, charts by junction and minute, the evidence log, and the per-controller table from the last benchmark; events are simulated"],
             ["About & paper", "Read how FlowSense relates to the base paper", "What is adopted and what is added; the pipeline diagram"]],
            widths=[1.2, 2.7, 2.6], align=["l", "l", "l"], size=9),
        H2("B.6 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Cause", "Fix"],
            [["`OSError: [WinError 1114] ... c10.dll` when importing Ultralytics or torch", "On Windows PyTorch's DLLs must load before scikit-learn or OpenCV", "The backend imports `torch` first (top of `backend/main.py`); in your own scripts do the same"],
             ["The Vision page says YOLOv8 is not available (HTTP 503)", "`ultralytics` is not installed", "`pip install -r backend/requirements-yolo.txt` and restart the API; all other pages work without it"],
             ["The first YOLOv8 call is slow or fails (HTTP 502)", "`yolov8n.pt` is downloaded on first use and needs internet", "Connect once, or copy `yolov8n.pt` into `8.ProjectCode`; later calls are much faster (the detector alone takes about 51 ms on the sample photo)"],
             ["Prediction or benchmark returns 503 *still training*", "The forecaster trains in the background for about 6-10 s after start", "Wait a few seconds and retry; turn *ML queue forecast* off to benchmark without it"],
             ["Benchmark rejected with 422 and a hint", "Out-of-range setting", "Duration 5-60 min, demand 0.5-1.8, 1-5 seeds, start hour 0-23"],
             ["`Sign in required` after some time", "The token lasts 12 hours, or the API was restarted with a new key", "Sign in again"],
             ["API calls take about 2 s each in your own script", "`localhost` resolves through IPv6 first on some Windows machines", "Use `http://127.0.0.1:8310`"],
             ["Port 8310 or 5310 already in use", "Another program holds the port", "Close it, or change the ports in `.env`"],
             ["`run.bat` stops while installing", "No internet, or Python/Node not on PATH", "Install Python 3.10+ and Node 20+, tick *Add to PATH*, run `run.bat` again"]],
            widths=[2.0, 2.2, 2.3], align=["l", "l", "l"], size=9),
        H2("B.7 API quick reference"),
        CODE("# sign in, then call an endpoint with the token\n"
             "curl -s http://127.0.0.1:8310/api/auth/demo\n"
             "curl -s -X POST http://127.0.0.1:8310/api/auth/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"operator@flowsense.app\\\",\\\"password\\\":\\\"Flow@1234\\\"}\"\n"
             "curl -s http://127.0.0.1:8310/api/live -H \"Authorization: Bearer <token>\"\n"
             "curl -s -X POST http://127.0.0.1:8310/api/live/step -H \"Authorization: Bearer <token>\" -H \"Content-Type: application/json\" -d \"{\\\"seconds\\\":120}\"\n"
             "curl -s \"http://127.0.0.1:8310/api/vision/synthetic?vehicles=9&ambulance=true&flash=A&seed=3\" -H \"Authorization: Bearer <token>\"\n"
             "# interactive documentation (FastAPI): http://127.0.0.1:8310/docs", 8),
    ]
    if F.REPORT:
        out[0:0] = []
        return _guide_trim(out)
    out += [
        H2("B.8 Repository layout"),
        TAB("Where things are in `8.ProjectCode`", ["Path", "Content"],
            [["`smart_traffic/`", "The engine: `sim.py` (simulator and four controllers), `predictor.py` (queue forecaster), `vision.py` (YOLOv8, light-bar rule, density, synthetic scenes)"],
             ["`backend/`", "FastAPI layer: `main.py` (routes), `service.py` (live simulation, benchmark, vision, prediction payloads), `auth.py` (token), `config.py` (`.env`)"],
             ["`frontend/`", "React 19 console: `src/pages` (Landing, Login, Live, Benchmark, Vision, Prediction, Violations, About), `src/components`, `src/lib`"],
             ["`app.py`", "The original Streamlit application over the same engine (kept; run with `streamlit run app.py`)"],
             ["`scripts/`", "`smoke_test.py`, `run_experiments.py`, `eval_real_vision.py`, `fetch_real_images.py`, `measure_api.py`, `capture_screens.py`, `make_report_facts.py`, and `docs/` (the documentation build)"],
             ["`tests/`", "Pytest suite: `test_engine.py` (24 tests) and `test_api.py` (14 tests)"],
             ["`experiments/`", "`metrics.json` for each experiment: controllers, demand sweep, emergency, ablation, predictor, vision, throughput, API latency"],
             ["`docs/`", "`REPORT_FACTS.md`, `NARRATIVE.md`, `screenshots/`, `diagrams/`, `figures/`, `metrics/`"],
             ["`data/external/`", "Downloaded public real-image sets (git-ignored); fetched by `scripts/fetch_real_images.py`"]],
            widths=[1.6, 4.9], align=["l", "l"], size=9.5),
    ]
    return out


def _guide_trim(out):
    """Compact variant for the full report: shorter API quick reference, two fewer troubleshooting rows, no repository table."""
    res = []
    for b in out:
        if b[0] == "tab" and b[1].startswith("Common problems"):
            b = ("tab", b[1], b[2], [r for r in b[3] if not (r[0].startswith("Port 8310") or r[0].startswith("`run.bat` stops") or r[0].startswith("API calls take"))]) + tuple(b[4:])
        elif b[0] == "code" and b[1].startswith("# sign in, then call"):
            lines = b[1].split("\n")
            b = ("code", "\n".join(lines[:3] + lines[-1:]), b[2])
        res.append(b)
    return res


# ------------------------------------------------------------------------------ Appendix C
def screens_blocks():
    SH = F.shot
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("The screens below complete the set of captures that are not shown in Chapter 8: the public landing page in both themes and the live control centre in the light theme. All were captured from the running application at 1440 by 900 pixels."),
        PAIR([(SH("01_landing_dark.png"), "Additional screen: landing page, dark theme, with the live preview simulation and the terminal log."),
              (SH("02_landing_features_dark.png"), "Additional screen: landing page capability cards.")], 2.95),
        P("The landing page is public. Its right-hand panel runs a separate preview simulation of the advanced controller on a 2x2 grid and prints signal changes; the counters below the headline (vehicles in the network, queued, average delay and completed trips) come from the same preview. "
          "The six capability cards restate the objectives of the batch (detect, prioritise, predict, coordinate, enforce, validate). The card on enforcement describes simulated violation events; Chapter 8 gives the measured status of every capability."),
        PAIR([(SH("03_landing_light.png"), "Additional screen: landing page, light theme."),
              (SH("19_live_control_light.png"), "Additional screen: Live control centre, light theme.")], 2.95),
        P("Both themes use the same tokens and charts; the choice is stored in the browser and defaults to the operating-system setting. The light-theme live screen shows the same KPI strip, scenario controls and road map as the dark one."),
    ]
