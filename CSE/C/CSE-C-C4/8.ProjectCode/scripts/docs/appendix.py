"""Appendices A (important code), B (installation and user guide) and C (additional screens) for QuantPulse."""
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB


def src(rel, a, b):
    """Lines a..b (1-based, inclusive) of a repository file, exactly as they stand in 8.ProjectCode."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    return "\n".join(lines[a - 1:b])


MDL = "backend/app/models_dl.py"
FED = "backend/app/federated.py"
FOR = "backend/app/forecast.py"
SEN = "backend/app/sentiment.py"
MAIN = "backend/app/main.py"
MIL = "scripts/mil_study.py"
EXP = "scripts/run_experiments.py"


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The key functions are copied from `8.ProjectCode` in the state in which the results were measured (whole statements; the full files are in the repository). "
          "The product code is under `backend/app/`; the last two excerpts are from the experiment scripts added for the evaluation and are not part of the application."),
        H2("A.1 Windows and scalers (`models_dl.py`)"),
        CODE(src(MDL, 21, 44), 7.5),
        H2("A.2 Attention tier and training (`models_dl.py`)"),
        CODE(src(MDL, 59, 73) + "\n\n" + src(MDL, 75, 80), 7.5),
        H2("A.3 Federated averaging (`federated.py`)"),
        CODE(src(FED, 16, 22), 7.5),
        H2("A.4 Recursive forecast with confidence band (`forecast.py`)"),
        CODE(src(FOR, 6, 21), 7.5),
        H2("A.5 Aligning sentiment to trading dates (`sentiment.py`)"),
        CODE(src(SEN, 138, 148), 7.5),
        H2("A.6 Scoring against the real closes (`scripts/run_experiments.py`)"),
        CODE(src(EXP, 139, 148), 7.5),
        H2("A.7 Gated-attention pooling of a bag of headlines (`scripts/mil_study.py`)"),
        CODE(src(MIL, 128, 140), 7.5),
    ]


def guide_blocks():
    a, w = F.API_PORT, F.WEB_PORT
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        P("Windows 10 or 11 (the launcher is a batch file; the code is portable), Python 3.11 on PATH, Node.js 20 or newer for live reload (optional: the API serves the prebuilt site), about 3 GB of disk for TensorFlow, PyTorch and the FinBERT-tone weights, "
          "internet for the first install and for live prices, and optionally a NewsAPI key in `.env` or Docker Desktop."),
        H2("B.2 One-click start"),
        N("Open the folder that contains `run.bat`; copy `.env.example` to `.env` if there is no `.env`.",
          f"Double-click `run.bat`: it creates `.venv`, installs the dependencies once, trains the models only if `artifacts/metrics.json` is missing (five to ten minutes) and starts the API on port {a} and the website on port {w}.",
          f"The browser opens http://localhost:{w}; the top-bar pill should read \"API online, models ready\". To stop, close the two windows."),
        H2("B.3 Manual start"),
        CODE("py -3.11 -m venv .venv\n.venv\\Scripts\\Activate.ps1\npython -m pip install -r backend\\requirements.txt\npython -m backend.train        # first time, or to retrain\n"
             f"python -m uvicorn backend.app.main:app --host 127.0.0.1 --port {a}\n\n# second terminal, live reload\ncd frontend; npm install; npm run dev     # http://localhost:{w}", 8.5),
        H2("B.4 Using the screens"),
        TAB("Screens and how to use them", ["Screen", "What to do", "What to look for"],
            [["Dashboard", "Click a ticker card or sort the table", "Last close, trend flag, 5-day outlook, data-mode badge"],
             ["Forecast", "Choose ticker, 5- or 30-day horizon, 60 to 250 days of history", "Actual line, dashed forecast and band; actual close and forecast miss once a date has passed; stale-model banner"],
             ["Model comparison", "Pick a ticker; switch between the two tabs", "Best model per metric, ablation, nine-model MAE chart, loss curves, federated rounds"],
             ["News sentiment", "Pick a ticker; search and filter headlines", "News source badge (built-in fallback unless a key is set), daily chart; the first visit can take a minute while FinBERT loads"],
             ["Method and data", "Read the pipeline and data table", "Price mode, rows and headlines per ticker"]],
            widths=[1.4, 2.4, 2.8], align=["l", "l", "l"], size=9.0),
        P("The theme button switches between light and dark; **Refresh** reloads the current screen. Forecasts are statistical estimates for research and education, not financial advice."),
        H2("B.5 Checking, retraining and experiments"),
        CODE("python scripts\\smoke_test.py            # 26 checks against the running API and website\npytest tests                          # 56 unit and API tests (project venv)\npython scripts\\capture_screens.py     # refreshes docs\\screenshots\\*.png\n"
             "python -m backend.train                # rewrites artifacts/ (forecast origin moves to the latest price)\nset PYTHONHASHSEED=0 & python scripts\\run_experiments.py   # re-run, forward test (after fetch_snapshot.py)\npython scripts\\extract_news.py ; python scripts\\mil_features.py ; python scripts\\mil_study.py", 8.5),
        H2("B.6 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Fix"],
            [["API offline in the top bar, or port in use", "Run `run.bat` again and read the API window; change `BACKEND_PORT` / `FRONTEND_PORT` in `.env` if a port is taken"],
             ["Screens say the models are not trained (HTTP 503)", "Run `python -m backend.train` with the virtual environment active"],
             ["Forecast banner: trained on older prices", "Expected; retrain to forecast from the latest close"],
             ["Sentiment shows Built-in fallback", "No `NEWSAPI_KEY`; add one to `.env` and restart"],
             ["`import tensorflow` fails after scikit-learn", "Import TensorFlow first (tests and scripts do)"]],
            widths=[2.6, 4.0], align=["l", "l"], size=9.5),
    ]


def screens_blocks():
    SH = F.shot
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("The screens below complete the set of captures that are not shown in Chapter 8: the dashboard and the forecast screen in the dark theme, and the method and data screen. All were captured from the running application at 1440 by 900 pixels, with the shipped artefacts and live Yahoo Finance prices on them."),
        PAIR([(SH("10_dashboard_dark.png"), "Additional screen: dashboard, dark theme."),
              (SH("11_forecast_dark.png"), "Additional screen: AAPL forecast, dark theme.")], 2.95),
        P("Both themes use the same tokens and charts; the choice is stored in the browser. The dark dashboard shows the same four summary cards and ten ticker cards as the light one, and the dark forecast screen the same chart, band and table. "
          "In the AAPL capture the dashed forecast starts from the training close of 8 September 2026 and falls well below the actual closes that followed, which is the behaviour measured in Chapter 8."),
        FIG(SH("09_about.png"), "Additional screen: Method and data, with the modelling pipeline timeline, the live installation facts and the research-and-education notice (the per-ticker data table is below the fold).", F.shot_w(SH("09_about.png"), 5.4, 3.4)),
        P("The method and data screen reads `/api/health` and `/api/metrics`. The panel on the right reports, live from the API, that the models are trained, that there are ten tickers, that the news source is the built-in fallback scored by FinBERT, and the 20-day window and the 5- and 30-day horizons; the table further down the page lists, for each ticker, the price mode, the number of rows and the number of headlines scored, so a reader can verify that all ten price series are live and all ten sentiment sources are the fallback."),
    ]
