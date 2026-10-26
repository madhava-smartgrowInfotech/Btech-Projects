"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, copied verbatim for code listings."""
    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


GAP = "\n    # ...\n"


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("Excerpts from the repository (`8.ProjectCode`), copied without change from the state in which the results of this report were measured; the complete files are in `app/`. A line holding only `# ...` marks omitted lines."),
        H2("A.1 Fused representation and balanced retrieval (`app/ml/retrieval.py`)"),
        CODE(src("app/ml/retrieval.py", 12, 55), 7.2),
        H2("A.2 Cleaning and the preprocessing pipeline (`app/ml/preprocessing.py`)"),
        CODE(src("app/ml/preprocessing.py", 15, 60), 7.2),
        H2("A.3 The classifiers (`app/ml/models.py`)"),
        CODE(src("app/ml/models.py", 9, 27), 7.2),
        H2("A.4 Prediction, explanation and risk label (`app/services/predictor.py`)"),
        CODE(src("app/services/predictor.py", 38, 60) + GAP + src("app/services/predictor.py", 78, 97) + GAP + src("app/services/predictor.py", 104, 104), 7.2),
        H2("A.5 Request validation (`app/main.py`)"),
        CODE(src("app/main.py", 34, 43) + GAP + src("app/main.py", 56, 70), 7.2),
    ]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements and start"),
        B(f"A Windows PC (the measurements in this report were made on: {F.HARDWARE}); a GPU is not needed. Python 3.10 or newer (3.11 recommended), Node.js 18 or newer, a current Chrome or Edge, and internet access for the first installation "
          "(packages and the 90 MB text-embedding model `sentence-transformers/all-MiniLM-L6-v2`).",
          "Double-click `run.bat` in `8.ProjectCode`. It checks Python and Node.js, creates or rebuilds `.venv`, installs `requirements.txt` and the frontend packages, starts the FastAPI backend in a second window and the React app in the first, and opens "
          "`http://localhost:5410`. The backend listens on `http://127.0.0.1:8410` and also serves the original pages (`/dashboard`, `/predict`, `/performance`, `/insights`). Ports are set in `.env` (`BACKEND_PORT`, `FRONTEND_PORT`).",
          "On the first start the models are trained if they are missing (a few minutes); later starts load the saved artefacts from `models/` in seconds. If the public CSV is placed in `data/raw/` it is used; otherwise the synthetic fallback with the same schema is used and recorded in `models/metadata.json`.",
          "Demo sign-in: `demo@venturepulse.com` / `Demo@1234` (the sign-in page has a click-to-fill button); change it with `DEMO_EMAIL` and `DEMO_PASSWORD` in `.env`."),
        CODE("python -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt\npython -m uvicorn app.main:app --host 127.0.0.1 --port 8410      # terminal 1, backend\n"
             "cd frontend && npm install && npm run dev                                   # terminal 2, frontend\n"
             "docker build -t venturepulse:latest . && docker run --rm -p 8000:8000 venturepulse:latest   # backend and original pages only", 7.5),
        H2("B.2 Using the screens"),
        N("**Sign in** with the demo account.",
          "**Dashboard**: dataset counters, the serving model with its scores, class distribution and model comparison.",
          "**Analyze a startup**: enter funding, rounds, the ages at first and last funding and milestone, relationships, milestones, average participants, industry, state, the investor flags, "
          "the number of comparable cases k (10, 20, 30 or 50) and a description of up to 2,000 characters (\"Fill an example\" loads a sample); press \"Predict startup success\". Read the outcome, confidence and risk label, the key contributing features, the evidence split and the table of comparable historical start-ups.",
          "**Model performance**: model comparison, confusion matrix, retrieval-size and representation studies, feature importance. **Startup insights**: industry, state, funding and correlation summaries.",
          "Press `/` for the command palette and `g` followed by `d`, `a`, `p` or `i` to jump between screens."),
        P("Remember that the screens describe the model trained on the data in `data/` (the synthetic fallback unless the public CSV is present) and that every estimate is an analytical aid, not investment advice."),
        H2("B.3 Checks and troubleshooting"),
        P(f"`python -m pytest tests -q` ({F.N_UNIT} tests), `python scripts/smoke_test.py` ({F.N_SMOKE} checks), `python scripts/edge_tests.py` ({F.N_EDGE} cases), `python scripts/ui_checks.py` (browser checks), `python scripts/capture_screens.py` (screenshots, application running), "
          "`python scripts/run_experiments.py` and `python scripts/extra_experiments.py` (real-data studies, need `data/real/startup_data.csv`), `python scripts/measure_latency.py` (server running), `python scripts/train.py` (retrain the models)."),
        TAB("Common problems", ["Symptom", "Cause and remedy"],
            [["`python` or `node` is not recognised", "Install them and enable \"Add python.exe to PATH\"; reopen the terminal"],
             ["The page says \"Cannot reach the VenturePulse API\"", "The backend window is not running or crashed: start it again with `run.bat` and read the error"],
             ["HTTP 500 and \"model files may be missing or incompatible\"", "The saved models were written by other library versions: run `python scripts/train.py`, then restart"],
             ["HTTP 422 from `/predict`", "A value is outside its range (for example funding above 1e10, k not in 10, 20, 30, 50, description over 2,000 characters)"],
             ["Port already in use", "Change `BACKEND_PORT` / `FRONTEND_PORT` in `.env`"],
             ["First prediction is slow", "The embedding model is loaded on the first request (11 s in one measured run); later requests take about 0.15 to 0.2 s"]],
            widths=[2.4, 4.1], align=["l", "l"], size=9),
    ]


def screens_blocks():
    f = F.fig
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("Enlarged parts of the screens of Chapter 8, cropped without change from the original 1440-pixel captures. They show the synthetic-trained model serving the application, with the real submission of Section 8.5 on the result screen."),
        PAIR([(f("crop_landing_hero_dark.png"), "Landing page, top: headline, calls to action and the live terminal card (dark theme)."),
              (f("crop_landing_hero_light.png"), "The same top section in the light theme.")], 3.1),
        FIG(f("crop_landing_how_it_works.png"), "Landing page, \"How it works\": the four passes from entering the signals to an explained estimate.", 5.6),
        FIG(f("crop_result_top.png"), "Result screen, top: outcome SUCCESS, confidence 83.3 %, Lower risk, the key contributing features and the 25 / 25 evidence split (k = 50).", 5.8),
        FIG(f("crop_result_cases.png"), "Result screen: table of comparable historical start-ups with similarity, outcome, industry, state, funding, rounds and summary, and the submitted inputs below it.", 5.8),
        FIG(f("crop_performance_top.png"), "Model performance, upper part: comparison table of the four models with the best marked, balanced accuracy and F1 bars, the precision-recall scatter and the confusion matrix of Logistic Regression.", 5.6),
        FIG(f("crop_performance_bottom.png"), "Model performance, lower part: retrieval-size comparison, structured-versus-text-versus-combined representation study and the top-15 coefficients (green pushes towards SUCCESS, red towards FAILURE).", 5.6),
    ]
