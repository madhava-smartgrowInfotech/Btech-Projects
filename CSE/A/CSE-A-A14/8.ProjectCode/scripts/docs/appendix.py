"""Appendices of the full report: A important code, B installation and user guide, C additional screens."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, TAB
from .ch9_10 import func_src


def code_blocks():
    parts = [
        ("A.1 Preprocessing pipeline (`src/preprocessing.py`)", "src/preprocessing.py", ["build_preprocessor", "train_test_split_data", "apply_smote"]),
        ("A.2 Model training and selection (`src/train_models.py`)", "src/train_models.py", ["train_selected_models", "select_best_model"]),
        ("A.3 Evaluation (`src/evaluation.py`)", "src/evaluation.py", ["evaluate_model"]),
        ("A.4 Risk bands and risk table (`src/utils.py`, `src/risk_segmentation.py`)", None, None),
        ("A.5 Scoring and batch prediction (`src/prediction.py`)", "src/prediction.py", ["score_customers", "build_batch_predictions"]),
        ("A.6 Local explanation (`src/explainability.py`)", "src/explainability.py", ["local_explanation"]),
        ("A.7 Retention rules (`src/retention_engine.py`)", "src/retention_engine.py", ["generate_recommendations"]),
        ("A.8 Saving and loading the model (`src/persistence.py`)", "src/persistence.py", ["save_artifacts", "load_artifacts"]),
        ("A.9 What-if route (`backend/main.py`)", None, None),
        ("A.10 Bearer-token authentication (`backend/auth.py`)", "backend/auth.py", ["make_token", "read_token", "require_user"]),
    ]
    out = [H1("APPENDIX A: IMPORTANT CODE"),
           P("The listings are copied from the code base at build time, so they are exactly what runs. Only the most important functions are shown; the complete source is in `8.ProjectCode`.")]
    for title, rel, names in parts:
        out.append(H2(title))
        if title.startswith("A.4"):
            out.append(CODE(func_src("src/utils.py", "assign_risk_category") + "\n\n" + func_src("src/risk_segmentation.py", "build_risk_table"), 7.5))
        elif title.startswith("A.9"):
            out.append(CODE(_route_src("whatif"), 7.5))
        else:
            out.append(CODE("\n\n".join(func_src(rel, n) for n in names), 7.5))
    return out


def _route_src(name):
    import ast
    import os

    path = os.path.join(F.CODE, "backend", "main.py")
    text = open(path, encoding="utf8").read()
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            lines = text.splitlines()
            start = node.decorator_list[0].lineno - 1 if node.decorator_list else node.lineno - 1
            return "\n".join(lines[start:node.end_lineno])
    raise KeyError(name)


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Prerequisites"),
        B("Windows with Python 3.10 or newer and Node.js 18 or newer on the PATH (development used Python 3.11.9 and Node 24.19.0).",
          "Internet access on the first run only, to download Python and Node packages.",
          "A modern browser; the interface was checked in Chrome."),
        H2("B.2 One-command start"),
        P("From the folder `8.ProjectCode`, run `run.bat`. On the first run it creates the virtual environment `.venv`, installs `backend\\requirements.txt`, runs `npm install` in `frontend\\`, starts the API on port 8314 and the web interface on port 5314 and opens the browser. Later runs start in a few seconds."),
        TAB("Launcher commands", ["Command", "What it does"],
            [["`run.bat`", "Start the API (port 8314) and the React interface (port 5314)"],
             ["`run.bat streamlit`", "Start the original Streamlit application (port 8501)"],
             ["`run.bat smoke`", "Run the end-to-end API test against the running API"],
             ["`run.bat build`", "Production build of the web interface into `frontend/dist`"]], widths=[1.8, 4.2], size=10),
        P("To start the two halves by hand: create the environment with `python -m venv .venv`, install with `.venv\\Scripts\\python -m pip install -r backend\\requirements.txt`, start the API with "
          "`.venv\\Scripts\\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8314`, and in a second terminal run `npm install` and `npm run dev` in `frontend`. Vite proxies `/api` to the backend, so no cross-origin setup is needed. "
          "Interactive API documentation is at `http://127.0.0.1:8314/docs`."),
        H2("B.3 Demo sign-in"),
        P("The sign-in page offers one-click demo sign-in. The demo account is `demo@churniq.com` with password `Demo@1234`; both and the signing secret can be changed in `.env` (`DEMO_EMAIL`, `DEMO_PASSWORD`, `AUTH_SECRET`) and the API restarted. Tokens last 12 hours. "
          "This is a demonstration login for one shared account and not a security feature."),
        H2("B.4 First five minutes"),
        N("Sign in and press **Quick start with sample data** on the dashboard. It loads the 1,000 synthetic customers, prepares them, trains Logistic Regression, Decision Tree and Random Forest and saves the best one; it takes a few seconds.",
          "Open **Customer risk** to see the bands and to change the thresholds, then **Customer 360** for one customer's score, drivers and suggested actions.",
          "Open **Explainable AI** for the global drivers, **What-if** to change a customer's contract or charges and see the new score, and **Retention actions** for the list of suggestions.",
          "To use your own data, open **Data upload**, drop a CSV, check the detected churn and ID columns, press **Prepare data**, then train on **Model training** and press **Save as active model**."),
        H2("B.5 The pages"),
        TAB("Pages of the ChurnIQ interface", ["Page", "Use"],
            [["Dashboard", "Portfolio KPIs, churn split, risk distribution, customers to contact first"],
             ["Data upload", "Load the sample or a CSV, preview, set target and ID columns, data-quality report, prepare"],
             ["Exploration", "Churn rate by attribute and numeric field, with filters"],
             ["Model training", "Choose models, imbalance strategy, test size and selection metric; compare; save the active model"],
             ["Evaluation", "ROC and precision-recall curves; confusion matrix per model"],
             ["Customer risk", "Edit thresholds; customers per band; ranked table"],
             ["Customer 360", "One customer: profile, score, band, drivers, retention actions"],
             ["Explainable AI", "Global importance; local explanation of one customer"],
             ["What-if", "Change attributes and re-score"],
             ["Retention actions", "Rule-based suggestions for chosen risk bands"],
             ["Batch prediction", "Download a template, upload a CSV, get scores, bands and top factors"],
             ["Monitoring", "Active model details; drift check on a new file"],
             ["About project", "Description, pipeline and limits"]], widths=[1.6, 4.4], size=10),
        H2("B.6 Reproducing the experiments"),
        TAB("Scripts that regenerate the documents' numbers", ["Script", "Output"],
            [["`scripts/run_experiments.py`", "`experiments/churn_synthetic/metrics.json`: all metrics, cross-validation, repeated splits, drivers, risk bands, latency"],
             ["`scripts/make_figures.py`", "`docs/figures/*.png` and `extra_analysis.json` (threshold sweep, calibration, lift)"],
             ["`scripts/make_diagrams.py`", "`docs/diagrams/*.png`"],
             ["`scripts/measure_api_latency.py [url]`", "`api_latency.json`: response times of the running API (use `http://127.0.0.1:8314`)"],
             ["`scripts/smoke_test.py [url]`", "63-check end-to-end API test"],
             ["`python -m pytest tests -q`", "44 unit tests"],
             ["`scripts/capture_screens.py`, `capture_extra.py`", "Screenshots in `docs/screenshots/`"]], widths=[2.3, 3.7], size=9.5),
        H2("B.7 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Fix"],
            [["The pages say the API is offline", "Start the API (port 8314); the web interface proxies `/api` to it"],
             ["A page says to load data or train first", "Use Quick start on the dashboard, or Data upload then Model training; only the saved model survives a restart, the dataset does not"],
             ["Every request takes about 2 seconds more", "Use `127.0.0.1` instead of `localhost` (IPv6 name resolution on some Windows machines)"],
             ["Explanations say SHAP is not installed", "Optional: `pip install shap` and restart the API; otherwise the built-in explanations are used"],
             ["A batch upload is rejected with 422", "The file lacks columns the model was trained on; download the template and compare"]], widths=[2.4, 3.6], size=9.5),
    ]


def screens_blocks():
    s = F.shot
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("These screens complete the set in Chapter 8: the landing page in both themes, the sign-in page, the About page, and the dark, tablet and phone layouts. All are real captures of the running application."),
        FIG(s("01_landing_light.png"), "Landing page (light theme)", 5.2),
        FIG(s("02_landing_dark.png"), "Landing page (dark theme)", 5.2),
        FIG(s("03_login.png"), "Sign-in page with the one-click demo account", 5.2),
        FIG(s("16_about.png"), "About page", 5.2),
        FIG(s("17_dashboard_dark.png"), "Dashboard in the dark theme", 5.2),
        FIG(s("18_risk_tablet.png"), "Customer risk page at tablet width (768 px)", 3.4),
        FIG(s("19_customer360_phone.png"), "Customer 360 at phone width (360 px)", 2.2),
        FIG(s("20_dashboard_phone.png"), "Dashboard at phone width (360 px)", 2.2),
    ]
