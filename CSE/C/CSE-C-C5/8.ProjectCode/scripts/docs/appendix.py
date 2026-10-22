"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, TAB


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a project file, read from disk so the listing is always the real code."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().rstrip("\n").split("\n")
    a = (start or 1) - 1
    b = end or len(lines)
    return "\n".join(lines[a:b])


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from the repository (`8.ProjectCode`) at the state in which the results of this report were measured. They are read from the files when this document "
          "is built, so they cannot drift from the code. Only the most important functions are shown; line ranges are given with each heading."),
        H2("A.1 Feature construction (`src/preprocess.py`, lines 26-55)"),
        P("Builds the 24 features of one or many (student, company) rows: engineered skill index, hiring rate, interaction and three gaps against the company cut-offs, then frequency encoding "
          "and standardisation using maps that are fitted on the training split only (`fit=True`) and reused everywhere else."),
        CODE(src("src/preprocess.py", 26, 55), 8),
        H2("A.2 Calibration and the residual hybrid (`src/hybrid_model.py`, lines 93-122)"),
        P("Platt scaling of XGBoost, the residual set of the base paper (note that its first term uses the true test labels `yte`), and the replacement of residual predictions by the kNN and SVM models."),
        CODE(src("src/hybrid_model.py", 93, 122), 8),
        H2("A.3 Serving-time prediction (`src/recommend.py`, lines 70-79)"),
        P("The deployable form of the hybrid rule: only the borderline band is blended with the kNN probability, because the true label is not known when a student is scored."),
        CODE(src("src/recommend.py", 70, 79), 8),
        H2("A.4 Company-role recommendation: filters and scoring (`src/recommend.py`, lines 81-111)"),
        CODE(src("src/recommend.py", 81, 111), 8),
        H2("A.5 The prediction endpoint (`backend/main.py`, lines 188-201)"),
        CODE(src("backend/main.py", 188, 201), 8),
    ]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B(f"Windows PC. The build machine was an {F.ENV['cpu']} with {F.ENV['ram']} of memory and no GPU (these are the machine's figures, not stated minimums).",
          "Python 3.10 or newer on the PATH (the project was built with Python " + F.ENV["python"] + ") and Node.js 20 or newer.",
          "A current browser; the interface was captured in Chrome.",
          "An internet connection for the first installation (Python packages and the front-end packages are downloaded)."),
        H2("B.2 Installation and start"),
        N("Open the project folder `8.ProjectCode` and double-click `run.bat`. It creates `.venv`, runs `pip install -r requirements.txt` if packages are missing, trains the models if `models\\xgb_calibrated.pkl` does not exist, "
          "runs `npm install` in `frontend`, then starts both servers.",
          "The backend runs in its own window at `http://localhost:8405` (interactive documentation at `/docs`) and the front end in another at `http://localhost:5405`, which `run.bat` opens in the browser.",
          "To stop, close the two server windows. The ports are read from `.env` (`BACKEND_PORT`, `FRONTEND_PORT`); `run.bat` copies `.env.example` to `.env` if it is missing."),
        P("Manual start in two terminals: `.venv\\Scripts\\python.exe -m uvicorn backend.main:app --port 8405` and `cd frontend` then `npm install` (first time) and `npm run dev`. "
          "A production build of the interface is made with `npm run build` and served with `npm run preview` on port 5405. "
          "The original Flask application starts with `python app.py` and opens at `http://127.0.0.1:5000`."),
        H2("B.3 Retraining the models (optional)"),
        CODE("""python src/generate_dataset.py     # writes data/companies.csv and data/placement_dataset.csv (seed 42)
python src/preprocess.py           # fits the encoders and writes models/preprocess.pkl
python src/hybrid_model.py         # trains, calibrates, writes models/*.pkl, metrics.json and static/*.png""", 9),
        P("Retraining overwrites the files in `models/` and `static/`. A fresh run with the installed library versions can differ from the shipped `metrics.json` by up to about 0.01 in any metric."),
        H2("B.4 Using the screens"),
        TAB("User guide", ["Screen (route)", "How to use it"],
            [["Landing (`/`)", "Shows the dataset size, placed rate, hybrid AUC and the 30 companies. *Check my eligibility* and *Officer dashboard* open the main screens."],
             ["Eligibility (`/predict`)", "Choose a company and role, enter the profile (scores 0-100, CGPA 0-10, counts) and press *Run prediction*. The result card shows the probability, the label, the profile against the company cut-offs and tips. *Reset* restores the defaults."],
             ["Recommendations (`/recommend`)", "Enter a profile, optionally a target company, role and preferred location, and press *Recommend*. Read the base probability, average gain, match rate and top pick, then the tabs Hybrid, Company-only and Role-only."],
             ["Officer dashboard (`/dashboard`)", "Four tiles, a model comparison chart, placed rate by branch and tabs for the model table, SHAP importance, PCA errors and probabilities."],
             ["Recruiter (`/recruiter`)", "Set minimum CGPA, minimum aptitude and branch and press *Filter*. The table shows the top 50 by CGPA with the total number of matches; *Export CSV* saves the returned rows (at most 50) as `shortlist.csv`."],
             ["Companies (`/companies`)", "Search by name, city or type, filter by tier, sort any column, page through 30 companies; *Check* opens the eligibility screen for that company."]],
            widths=[1.7, 5.0], align=["l", "l"], size=9.5),
        P("**Keyboard.** `/` opens the command palette (search a company or jump to a screen), `g e`, `g r`, `g d`, `g u` and `g c` go to Eligibility, Recommendations, Officer dashboard, Recruiter and Companies, "
          "`g l` opens the activity log of the session's API calls, and `?` shows the shortcut help. The sun/moon button switches between dark and light themes and the choice is remembered."),
        H2("B.5 Running the tests and measurements"),
        CODE("""python scripts/smoke_test.py       # 15 live API checks (backend must be running on 8405)
python scripts/edge_tests.py       # 46 unit / integration / functional / validation / security checks + latency
python scripts/run_experiments.py  # confusion matrices, five-seed study, band and threshold sweeps, SHAP, recommender gain
python scripts/make_diagrams.py    # the design diagrams
python scripts/capture_screens.py  # screenshots (needs both servers and Playwright)""", 9),
        H2("B.6 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Fix"],
            [["\"Could not reach the placement API\"", "The backend is not running on port 8405. Start it as in B.2."],
             ["`ModuleNotFoundError: pyarrow`", "The pickled company table needs it: `.venv\\Scripts\\python.exe -m pip install -r requirements.txt`."],
             ["Port already in use", "Change `BACKEND_PORT` or `FRONTEND_PORT` in `.env` and restart both servers."],
             ["Models missing or incompatible after a library upgrade", "Run the three retraining commands in B.3."],
             ["Recommendation takes several seconds", "Expected: the four model files are reloaded for each candidate (about 5 s per request)."],
             ["Scripts using `localhost` are slow", "Use `127.0.0.1` in scripts; on this machine `localhost` added about 2 s per request."]],
            widths=[2.3, 4.4], align=["l", "l"], size=10),
    ]


def screens_blocks():
    s = F.shot
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("These captures complement Chapter 8. All were taken at 1440x900 pixels from the running application with the 3,000-student dataset and the trained models loaded."),
        FIG(s("01_landing_light.png"), "Landing page, light theme: hero text, live boot log, and the counters read from the API (3,000 students, 59.7% placed, hybrid AUC 0.8968, 30 companies).",
            F.shot_w(s("01_landing_light.png"), 5.6, 3.6)),
        FIG(s("01_landing_dark.png"), "Landing page, dark theme (the default): the same content with the theme switched.", F.shot_w(s("01_landing_dark.png"), 5.6, 3.6)),
        FIG(s("07_companies.png"), "Companies board: the first page of 30 companies sorted by package, with tier, type, CGPA, aptitude and technical cut-offs, package, location and hiring rate.",
            F.shot_w(s("07_companies.png"), 5.6, 3.6)),
        FIG(s("08_command_palette.png"), "Command palette after typing \"hyd\": companies located in Hyderabad with tier and package; Enter opens the selected company.", F.shot_w(s("08_command_palette.png"), 5.6, 3.6)),
        FIG(s("09_activity_log.png"), "Activity log drawer: real API calls of the session with their status codes and durations (for example GET /stats 200 in 122 ms).", F.shot_w(s("09_activity_log.png"), 5.6, 3.6)),
    ]
