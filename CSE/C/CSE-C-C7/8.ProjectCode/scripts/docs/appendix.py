"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

import os
import textwrap

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB

WRAP = 94


def source(rel, start, end=None):
    """Text of a source file from the line containing `start` up to (not including) the line containing `end`.

    Long lines are wrapped for print (the wrapping never changes a token); a continuation is indented by eight spaces.
    """
    path = os.path.join(F.CODE, rel)
    lines = open(path, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
    a = next(i for i, l in enumerate(lines) if start in l)
    b = len(lines)
    if end:
        b = next(i for i in range(a + 1, len(lines)) if end in lines[i])
    chunk = lines[a:b]
    while chunk and not chunk[-1].strip():
        chunk.pop()
    out = []
    for l in chunk:
        if len(l) <= WRAP:
            out.append(l)
            continue
        ind = len(l) - len(l.lstrip())
        out.extend(textwrap.wrap(l, width=WRAP, subsequent_indent=" " * (ind + 8), break_long_words=False, break_on_hyphens=False, drop_whitespace=True, replace_whitespace=False, initial_indent=""))
    return "\n".join(out)


def code_blocks():
    s = source
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings below are read from the repository by the document build script, so they are the code that was tested and measured. File paths are relative to `8.ProjectCode`. "
          "Lines longer than a printed line are wrapped, with the continuation indented; no token is changed."),
        H2("A.1 Score terms (`app/recommender.py`)"),
        P("Skill fit, text construction and TF-IDF content similarity:"),
        CODE(s("app/recommender.py", "def skill_compat", "def topic_interest_score"), 8),
        P("Topic overlap, behavioural boost and engagement level:"),
        CODE(s("app/recommender.py", "def topic_interest_score", "def load_ml_bundle"), 8),
        H2("A.2 Learner state and success model (`app/recommender.py`)"),
        CODE(s("app/recommender.py", "def load_ml_bundle", "def uplift_scores"), 8),
        H2("A.3 Action scores: T-learner at prediction time (`app/recommender.py`)"),
        CODE(s("app/recommender.py", "def uplift_scores", "ACTION_LABEL = {"), 8),
        H2("A.4 The hybrid ranking function (`app/recommender.py`)"),
        CODE(s("app/recommender.py", "def rank_courses"), 8),
        H2("A.5 Synthetic data and the learner-level split (`scripts/train_pipeline.py`)"),
        P("Generation of one learner's twelve weeks, the label rule, the observed-action proxy and the split by learner:"),
        CODE(s("scripts/train_pipeline.py", "    for lid in range(n_learners):", "    df = pd.DataFrame(rows)"), 8),
        CODE(s("scripts/train_pipeline.py", "    df = pd.DataFrame(rows)", "def split_learners"), 8),
        H2("A.6 Model comparison and T-learner training (`scripts/train_pipeline.py`)"),
        CODE(s("scripts/train_pipeline.py", "    scaler = StandardScaler().fit(Xtr)", "        results[name][\"proba\"] = proba"), 8),
        CODE(s("scripts/train_pipeline.py", "    uplift = {}", "    joblib.dump(uplift"), 8),
        H2("A.7 Offline policy evaluation (`scripts/train_pipeline.py`)"),
        CODE(s("scripts/train_pipeline.py", "        beh = LogisticRegression", "               \"limitation\""), 8),
        H2("A.8 Password hashing, tokens and sign-in (`app/security.py`, `app/api_routes.py`)"),
        CODE(s("app/security.py", "from passlib"), 8),
        CODE(s("app/api_routes.py", "def get_current_user", "def profile_dict"), 8),
        H2("A.9 Recommendation route (`app/api_routes.py`)"),
        CODE(s("app/api_routes.py", '@router.get("/api/recommendations")', '@router.post("/api/recommendations/refresh")'), 8),
    ]


def guide_blocks():
    env = F.ENV
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Windows 10 or 11 (also works on macOS and Linux with the manual start), Python 3.11 or newer on PATH, Node.js 20 or newer on PATH.",
          f"The versions used for every measurement in this report: Python {env['python']}, Node.js {env['node']}, npm {env['npm']}.",
          "About 500 MB of free disk space and 4 GB of memory (8 GB recommended), and a modern browser. No graphics card and no internet connection are needed after installation."),
        H2("B.2 One-click start"),
        N("Open the folder `8.ProjectCode` and double-click `run.bat`, or run it from a terminal in that folder.",
          "On the first run it creates `.venv`, installs `requirements.txt`, trains the models if `artifacts/metrics/model_metrics.json` is missing, and runs `npm install` in `frontend/`.",
          "Two console windows open, **LearnPathIQ API** (port 8407) and **LearnPathIQ Web** (port 5407), and the browser opens http://localhost:5407.",
          "The original server-rendered interface stays available at http://localhost:8407.",
          "Stop everything by closing the two windows."),
        P("The ports are set in `.env` (copy `.env.example` if it is missing): `BACKEND_PORT=8407`, `FRONTEND_PORT=5407` and a `SECRET_KEY` placeholder. The React server proxies `/api` and `/static` to the API, so no CORS setting is needed."),
        H2("B.3 Manual start"),
        CODE("# terminal 1, from 8.ProjectCode\n.venv\\Scripts\\python -m uvicorn app.main:app --host 127.0.0.1 --port 8407\n\n# terminal 2\ncd frontend\nnpm install\nnpm run dev"),
        P("On the first run of a fresh checkout the models must exist: `python scripts/train_pipeline.py` writes `models/*.joblib`, `artifacts/metrics/model_metrics.json` and three plots."),
        H2("B.4 Using the application"),
        TAB("Walk-through", ["Step", "Action", "Result"], [
            ["1", "Open http://localhost:5407 and choose **Create account**; enter a name, an e-mail address and a password of at least six characters", "The account is created and the profile form opens (\"Tell us what you want to learn\")"],
            ["2", "Choose education, skill level, learning style and weekly hours; type interests, preferred topics, goals and course preferences (comma separated); optionally age band and gender; save", "The profile is stored; the toast confirms"],
            ["3", "Open **Recommendations**", "Courses appear under \"Ranked for you\" with match percentage, success estimate, suggested action and reasons"],
            ["4", "Press **View**, **Start** or **Dismiss** on a card, or open a course and use its action buttons", "The event is stored; the next ranking changes"],
            ["5", "Press **Refresh** on the recommendations page", "The model files are reloaded and the ranking recomputed"],
            ["6", "Open **Learning path**", "Up to six staged steps and the next best action"],
            ["7", "Open **Insights**", "Engagement level, success estimate, action-benefit bars, strengths and areas to attend to"],
            ["8", "Open **Activity**", "Two tabs: the interaction log and the recommendation history"],
            ["9", "Open **Course catalog** (works without signing in) and **Model analytics**", "Search and filter 24 courses; four tabs: Models, Diagnostics, Offline policy and Fairness audit"],
            ["10", "Use the moon button at the top right", "Switch between light and dark themes"],
        ], widths=[0.5, 3.3, 2.5], size=9.5, align=["c", "l", "l"]),
        H2("B.5 Retraining the models"),
        CODE("python scripts/train_pipeline.py          # a few minutes at most; fixed seed 42\npython scripts/run_experiments.py all         # seed study, ceiling, personas, ablation, feedback loop\n# then press Refresh on the recommendations page, or restart the API"),
        P("The pipeline writes the metrics file that the analytics screen shows. Re-running it with the same seed reproduces the stored metrics exactly."),
        H2("B.6 Running the tests and checks"),
        CODE("python -m pytest tests -q                  # 5 tests\npython scripts/smoke_test.py                 # 33 checks, needs both servers running\npython scripts/check_responsive.py           # needs: pip install playwright; playwright install chromium\npython scripts/capture_screens.py            # regenerates docs/screenshots\npython scripts/measure_api.py                # latency on 127.0.0.1"),
        H2("B.7 Troubleshooting"),
        B("**The page shows a connection error:** the API window is not running. Check the **LearnPathIQ API** window, then reload.",
          "**Port already in use:** change `BACKEND_PORT` or `FRONTEND_PORT` in `.env` and start again.",
          "**`/api/metrics` answers 503:** the models have not been trained; run `python scripts/train_pipeline.py`.",
          "**Slow requests when using `localhost`:** on some Windows machines `localhost` falls back from IPv6 and adds about two seconds per call; use `127.0.0.1` instead.",
          "**`ModuleNotFoundError`:** install `requirements.txt` into the Python that runs the API (the `.venv` created by `run.bat`)."),
    ]


SCREENS = [
    ("01_landing_light.png", "Landing page in the light theme: headline, call to action and live catalogue statistics"),
    ("04_register.png", "Registration form: name, e-mail, password and confirmation, with validation messages"),
    ("12_activity_history.png", "Activity page, recommendation history: forty logged recommendations, each with its match percentage and the reasons given at the time"),
    ("20_dashboard_dark.png", "Dashboard in the dark theme: engagement, success estimate, event counts, next action and top recommendations"),
]


def screens_blocks():
    out = [H1("APPENDIX C: ADDITIONAL SCREENS")]
    out.append(P("All screenshots are captures of the running application at 1440 x 900 pixels, taken with Playwright from one registered learner who has a filled profile and twelve recorded interaction events. "
                 "Chapter 8 shows the login screen, the catalogue, the first-run profile form, the dashboard, the recommendations, the learning path, the insights, the course detail and the four model-analytics tabs; the screens below add the landing page, the registration form, the recommendation history and the dark theme."))
    for f, cap in SCREENS:
        if not os.path.exists(F.shot(f)):
            raise FileNotFoundError(F.shot(f))
        p = F.shot_view(f)
        out.append(FIG(p, cap, F.shot_w(p, 5.4)))
    return out
