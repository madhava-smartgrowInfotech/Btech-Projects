"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

import os

from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from . import facts as F


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
          "File paths are relative to `8.ProjectCode`. Only the parts that carry the method are shown; routine plumbing (routes that render templates, "
          "plotting code) is left out."),
        H2("A.1 Input validation (`app/utils/validation.py`)"),
        P("Every request, whether from the React form or the JSON API, passes through this function. It checks that each field is present, belongs to its "
          "allowed set or numeric range, and derives `education-num` from the education label."),
        CODE(s("app/utils/validation.py", "def validate_assessment")),
        H2("A.2 Cleaning and derived features (`scripts/feature_engineering.py`)"),
        P("`add_derived_features` creates the interpretable columns that are used identically in training and at prediction time."),
        CODE(s("scripts/feature_engineering.py", "def add_derived_features", "NUMERIC_FEATURES = [")),
        H2("A.3 Leakage-safe preprocessing (`scripts/feature_engineering.py`)"),
        CODE(s("scripts/feature_engineering.py", "NUMERIC_FEATURES = [", "def _onehot")),
        CODE(s("scripts/feature_engineering.py", "def build_preprocessor", "def get_output_feature_names")),
        H2("A.4 Candidate models (`scripts/models.py`)"),
        CODE(s("scripts/models.py", "def get_candidate_models")),
        H2("A.5 Split, cross-validation and model selection (`scripts/train.py`)"),
        CODE(s("scripts/train.py", "    # Cross-sectional: one row per person", "    best_pipe = joblib.load")),
        H2("A.6 Forecasting (`scripts/forecast.py`)"),
        CODE(s("scripts/forecast.py", "def build_index_series", "def fit_forecast")),
        CODE(s("scripts/forecast.py", "def fit_forecast", "def main")),
        H2("A.7 Profile mapping, prediction and live SHAP (`app/services/predictor.py`)"),
        CODE(s("app/services/predictor.py", "def profile_from_proba", "def local_shap")),
        CODE(s("app/services/predictor.py", "def local_shap", "def predict_profile")),
        CODE(s("app/services/predictor.py", "def predict_profile", "def build_insights")),
        H2("A.8 What-if comparison (`app/services/whatif.py`)"),
        CODE(s("app/services/whatif.py", "def run_whatif")),
        H2("A.9 What-if API route (`app/api.py`)"),
        CODE(s("app/api.py", "def _parse_overrides", '@api_bp.route("/whatif"')),
        CODE(s("app/api.py", '@api_bp.route("/whatif"')),
    ]


def guide_blocks():
    lat = F.MEAS["api_latency_ms_127_0_0_1"]["POST /api/predict"]
    py = F.MEAS["pytest"]
    sm = F.MEAS["smoke_test"]
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        TAB("Software and hardware needed to run FinSight AI", ["Item", "Requirement"], [
            ["Operating system", "Windows 10 or 11 (developed and measured on Windows 11 Pro); the Python and Node steps are the same on other systems"],
            ["Python", "3.11 or newer (measured with 3.11.9) with pip"],
            ["Node.js", "18 or newer (measured with 24.19.0) for the React front end"],
            ["Python packages", "pandas, numpy, scikit-learn, xgboost, shap, statsmodels, Flask, joblib, matplotlib, pytest, requests, fpdf2 (see `requirements.txt`)"],
            ["Hardware", "Any ordinary laptop; no GPU. Measured on an Intel Core i5-12500 with 15.7 GB of RAM"],
            ["Disk and network", "About 1.5 GB for the virtual environment and `node_modules`; internet only for the first install"],
        ], widths=[1.5, 4.8], size=10, align=["l", "l"]),
        H2("B.2 Automatic start with run.bat"),
        P("Double-click `run.bat` in `8.ProjectCode`. The script reads the ports from `.env` (`PORT=8409` for the Flask API and `FRONTEND_PORT=5409` for the React app) and then performs six steps:"),
        N("Checks that Python and Node.js are on the PATH and prints their versions.",
          "Creates the `.venv` virtual environment if it does not exist.",
          "Activates it and runs `pip install -r requirements.txt`.",
          "Trains the models with `python scripts\\train.py` if `models\\best_model.pkl` is missing (a few minutes; the persisted models and artifacts are already in the repository).",
          "Runs `npm install` and `npm run build` inside `frontend` on the first run.",
          "Starts the API in a second window (`python run.py`), opens http://localhost:5409 and serves the built front end with `npm run preview`."),
        H2("B.3 Manual start"),
        CODE("python -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt\npython scripts\\train.py          :: only if models\\best_model.pkl is missing\npython run.py                    :: API on http://localhost:8409\n\ncd frontend\nnpm install\nnpm run dev                      :: http://localhost:5409 (proxies /api to 8409)", 9),
        P("For a production-style run use `npm run build` followed by `npm run preview`, which also serves port 5409. The original server-rendered Flask pages remain available at http://localhost:8409. "
          "`python scripts\\report_metrics.py` re-derives the confusion matrices, threshold sweep, calibration bins and forecast back-test from the saved models."),
        H2("B.4 Sample login"),
        P("The application opens at a sign-in screen for the `/app` area. Use the email **demo@finsight.ai** and the password **finsight123**, or press *Use demo credentials*. "
          "This is a browser-only demonstration gate stored in `localStorage`: it does not authenticate anyone and FinSight AI has no user accounts or stored personal data."),
        H2("B.5 User guide, screen by screen"),
        TAB("Screens of the application and what to do on each", ["Screen (route)", "What it shows", "What to do"], [
            ["Landing (`/`)", "Headline *Understand your financial profile, gently.*, a live forecast chart, sections *How it works*, *Features*, *Numbers* with real model figures, a light / dark switch",
             "Press *Start your assessment*, *Explore the dashboard* or *Open the app*; use *Sign in* if not yet signed in"],
            ["Sign in (`/login`)", "*Sample login* card with the demo credentials, *Email*, *Password*, *Show password*", "Press *Use demo credentials*, then *Sign in*; a guarded address redirects here first and returns afterwards"],
            ["Dashboard (`/app`)", "Cards *Serving model*, *Accuracy*, *ROC-AUC*, *F1 score*; *Top drivers in the trained model*; *Economic outlook*; *What you can do here*",
             "Read the model snapshot; press *Start assessment*, *Open explainability* or *Explore the forecast*"],
            ["Assessment (`/app/assess`)", "*Financial assessment* form titled *Your information* with twelve fields: Age, Employment type, Education, Marital status, Occupation, Household relationship, Race, Sex, Country, Investment gains, Investment losses, Hours worked per week",
             "Fill the fields or press *Use sample profile*; press *Analyse my profile*; *Clear* empties the form. Out-of-range values are rejected with a message beside the field"],
            ["Result (`/app/result`)", "*Your financial profile*: *Predicted profile* (Emerging / Developing / Established), risk band, *Financial-strength score*, *What shaped your score* (strengthening and weakening SHAP factors), *Actionable insights*, *Your inputs*, a mini forecast",
             "Press *Try a what-if scenario*, *Why this result?* or *Edit inputs*"],
            ["Explainability (`/app/explain`)", "*Explainability (SHAP)*: *Global importance* bar chart, *SHAP summary (beeswarm)*, *Original SHAP bar chart*, searchable *Ranked features* table, *How to read this*",
             "Search or sort the table; press *Get my local explanation* to run an assessment"],
            ["Forecast (`/app/forecast`)", "*Economic forecast*: cards *Horizon*, *Trend*, *Projected change*, *Residual std*; chart *Index history and forecast* with a 95% band and range tabs; *Interpretation*; *Forecast values* table",
             "Choose *Full history*, *Last 5 years* or *Last 2 years*; page through the table"],
            ["What-if (`/app/whatif`)", "*What-if financial scenario*: *Baseline information* (pre-filled from the last assessment), *Scenario changes* (gains, losses, hours per week, education), baseline and scenario cards and a *Comparison*",
             "Change at least one scenario field, leave others blank, press *Compare scenarios*"],
            ["Performance (`/app/performance`)", "*Model performance*: *Model comparison* table, *Metrics at a glance*, *Confusion matrix*, *ROC curves*, *Validation strategy*, *Cross-validation fold AUCs*, *Statistical analysis*",
             "Sort the comparison table; read the validation protocol"],
            ["About (`/app/about`)", "*About FinSight AI*: *How it works* (six steps), *Technology*, *Responsible use*", "Read the responsible-use statement"],
            ["Not found", "*Page not found* with *Go to the dashboard* and *Landing page*", "Follow either button"],
        ], widths=[1.35, 2.9, 2.05], size=8.5, align=["l", "l", "l"]),
        H2("B.6 Troubleshooting"),
        TAB("Common problems and fixes", ["Symptom", "Cause", "Fix"], [
            ["run.bat says Python or Node.js was not found", "Not installed or not on the PATH", "Install Python 3.11+ and Node.js 18+, tick *Add python.exe to PATH*, reopen the window"],
            ["Port 8409 or 5409 already in use", "Another program holds the port", "Change `PORT` or `FRONTEND_PORT` in `.env` and restart"],
            ["Header pill shows *API offline*, or the form says *make sure the API is running (run.bat)*", "The Flask window was closed or failed to start", "Restart `python run.py`; open http://localhost:8409/health, which should answer `status: ok`"],
            ["Result page asks for an assessment first", "The last result and baseline are kept in the browser tab's session storage only and are cleared on sign-out", "Press *Start assessment* and analyse a profile again"],
            ["Version warnings about scikit-learn or XGBoost when the API starts", "The `.pkl` files were written by an older library version", "Retrain with `python scripts\\train.py`; the numbers reproduce exactly"],
            ["`shap` or `xgboost` fails to install", "No wheel for the Python version", "Use Python 3.11 and upgrade pip first"],
            ["Screenshots script cannot find a browser", "Chrome missing", "`pip install playwright` then `playwright install chromium`"],
        ], widths=[2.0, 1.8, 2.5], size=9, align=["l", "l", "l"]),
        H2("B.7 Running the tests"),
        P(f"With the virtual environment active run `pytest` in `8.ProjectCode`: {py['passed']} tests pass in about {py['seconds']:.0f} seconds (7 in `tests/test_app.py`, 2 in `tests/test_features.py`). "
          f"With both servers running, `python scripts\\smoke_test.py` performs {sm['total']} checks against the API and the front-end proxy and all {sm['passed']} pass. "
          f"On the development machine a prediction request takes a median of {lat['median']:.1f} ms (95th percentile {lat['p95']:.1f} ms) measured on 127.0.0.1."),
    ]


def _shot(name, caption, max_h=1500, base=5.6):
    p = F.shot_view(name, max_h)
    return FIG(p, caption, F.shot_w(p, base))


def screens_blocks():
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("The screens below complement those shown in Chapter 8. All were captured at 1440 x 900 pixels (full-page captures are cropped to their upper part) from the running application "
          "with real model output; none is a mock-up."),
        _shot("01_landing-light.png", "Landing page in light mode: headline, call-to-action buttons, the live Household Financial Conditions Index chart with its 12-month forecast band, and badges *Informational, not advice* and *Explained with SHAP*"),
        _shot("02_landing-dark.png", "Landing page in dark mode, reached with the theme switch in the header; the choice is kept in the browser and survives a reload"),
        _shot("03_login.png", "Sample login screen: the demo account card with the email and password, the *Use demo credentials* shortcut, the form, and the note that the login runs in the browser and stores nothing", base=4.8),
        _shot("11_about.png", "About screen: the six-step description of how the system works, the technology list and the responsible-use statement"),
        _shot("12_not-found.png", "Page-not-found screen shown for an unknown address inside the application, with buttons back to the dashboard and the landing page", base=5.0),
        _shot("13_validation-error.png", "Validation failure: an age of 7 is below the allowed 16-100, the field is outlined in red with the message *Must be between 16 and 100* and the form shows *Could not analyse this profile*; no model call is made"),
        _shot("15_result-established-full.png", "Result for a 52-year-old married executive with a Master's degree, gains of 7,688 and 50 working hours: profile *Established*, risk *Low*, strength 99.9% (upper part of the page, with the strengthening factors led by investment gains)", max_h=1500, base=5.2),
        _shot("17_explainability-full.png", "Explainability screen (upper part): global importance bars for the top twelve features, the SHAP beeswarm summary and the original bar chart rendered at training time", base=5.2),
        _shot("18_forecast-full.png", "Forecast screen: horizon, trend, projected change (+3.46%) and residual standard deviation (1.659); the history-and-forecast chart with its 95% band; the interpretation text that names the series as synthetic; and the first six forecast months"),
        _shot("19_performance-full.png", "Performance screen (upper part): best model, dataset rows, train / test split, the four-model comparison table, the metrics-at-a-glance bars and the XGBoost confusion matrix with the ROC curves", base=5.2),
    ]
