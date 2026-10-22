"""Chapters 3 (feasibility study) and 4 (system requirements and analysis)."""

import json
import os

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F


def _pkg():
    try:
        return json.load(open(os.path.join(F.CODE, "frontend", "package.json"), encoding="utf-8"))
    except Exception:
        return {"dependencies": {}, "devDependencies": {}}


def _reqs():
    out = []
    p = os.path.join(F.CODE, "requirements.txt")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


def _model_mb():
    p = os.path.join(F.CODE, "models", "random_forest.pkl")
    return os.path.getsize(p) / 1e6 if os.path.exists(p) else 0.0


def blocks():
    env = F.MEAS["environment"]
    lat = F.MEAS["api_latency_ms_127_0_0_1"]
    pred = lat["POST /api/predict"]
    wi = lat["POST /api/whatif"]
    pk = _pkg()
    dep, dev = pk.get("dependencies", {}), pk.get("devDependencies", {})
    best_mb = os.path.getsize(os.path.join(F.CODE, "models", "best_model.pkl")) / 1e6
    py = F.MEAS["pytest"]
    sm = F.MEAS["smoke_test"]
    return [
        # =================================================================== CHAPTER 3
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        H2("3.1 Introduction"),
        P("A feasibility study asks whether the proposed system can be built, whether it is worth building and whether it can be used and kept running. For a student project the "
          "answers are mostly technical and operational, because the economic side is dominated by free software and existing hardware. This chapter answers each question with "
          "evidence from the build: the software that was installed, the machine that was used and the measurements that were taken."),
        H2("3.2 Technical feasibility"),
        P("The system needs tabular data, a machine-learning toolkit, an explanation library, a time-series library, a web framework and a browser front end. Each is available as open-source "
          f"software with a stable Python or JavaScript interface: scikit-learn {n('sklearn')} for pipelines and models, XGBoost {n('xgboost')} for the boosted trees, SHAP {n('shap', 'treeshap')} for explanations, "
          f"statsmodels {n('statsmodels')} for Holt-Winters smoothing and the logit statistics, Flask {n('flask')} for the API, and React {n('react')} with Vite {n('vite')} for the interface."),
        TAB("Technical feasibility: needs and evidence", ["Need", "Chosen solution", "Evidence that it works"], [
            ["Public individual-level data with demographic and financial attributes", f"UCI Adult / Census Income, {F.N_ROWS:,} records {n('uci')}", "Downloaded once into data/raw; loads in the training script"],
            ["Leakage-safe preprocessing and four models", "scikit-learn Pipeline with ColumnTransformer; LR, RF, GB, XGBoost", f"All four trained; test ROC-AUC {F.f3(F.COMPARE['logistic_regression']['roc_auc'])} to {F.f3(F.COMPARE['xgboost']['roc_auc'])}"],
            ["Per-request explanation", "SHAP TreeExplainer on the selected XGBoost model", f"Live explanation is part of every prediction; median {pred['median']:.0f} ms per request"],
            ["Forecast with an interval", "Holt-Winters (statsmodels), 12 months", f"Back-test MAE {F.f3(F.RM['forecast_backtest']['mae'])} on the synthetic series"],
            ["API and interface", "Flask JSON API on 8409; React SPA on 5409", f"{sm['passed']} of {sm['total']} smoke checks and {py['passed']} automated tests pass"],
            ["Reproducibility", "random_state 42, metrics written to JSON, report_metrics.py re-derives them", "Re-derived numbers equal the stored ones exactly"],
        ], widths=[2.1, 2.2, 2.0], size=9.5, align=["l", "l", "l"]),
        P(f"The main technical risk was size and speed. The Random Forest candidate is large (its saved file is about {_model_mb():.0f} MB because it holds 300 unpruned trees), while the selected XGBoost pipeline is "
          f"{best_mb:.1f} MB and is loaded once at start-up. A prediction including its SHAP explanation takes a median of {pred['median']:.0f} ms and a what-if comparison, which runs the model twice, {wi['median']:.0f} ms, both on a "
          "CPU-only desktop. The risk was therefore judged acceptable. A second risk is version drift: the saved pipelines were written with older scikit-learn and XGBoost releases and emit warnings when loaded by "
          "the newer versions used for the final measurements; the metrics reproduce exactly, and retraining with `python scripts/train.py` regenerates the files."),
        H3("Data feasibility"),
        P(f"The classification data are feasible because they are public, individual-level, large enough ({F.N_ROWS:,} records, {F.N_TRAIN:,} for training and {F.N_TEST:,} for testing) and rich in the attributes the abstract names: age, education, occupation, "
          "household role and location (through native country), plus capital gains and losses as the financial signal. Their weaknesses were known in advance and shaped the design. They are old; they have no time dimension, so a separate "
          "series is needed for forecasting; they hold no transaction-level data; and a small share of workclass, occupation and country values is missing, which the pipelines impute. The census sampling weight has no meaning for a new user "
          "and is therefore imputed with the training median at prediction time. A fallback that generates a synthetic dataset with the same schema exists in the training script for offline machines; it was not used for any result reported here."),
        H2("3.3 Economic feasibility"),
        P("Every software component is open source and free of licence cost, and the dataset is public. The project needs no cloud service, no paid API and no specialised hardware. "
          f"All development, training and measurement were done on one desktop ({env['cpu']}, {env['ram_gb']} GB of memory, {env['os']}) with no graphics processor, which is possible "
          "because the tabular data and the tree models are small by deep-learning standards."),
        TAB("Cost view of the project", ["Item", "Cost", "Note"], [
            ["Python, scikit-learn, XGBoost, SHAP, statsmodels, pandas, NumPy", "No licence fee", "Open-source libraries"],
            ["Flask, React, Vite, Recharts, Framer Motion and other front-end packages", "No licence fee", "Open-source packages installed with npm"],
            ["Dataset", "No fee", "Public UCI Adult file; attribution to the UCI repository"],
            ["Hardware", "Existing desktop", "No GPU, no server, no cloud account"],
            ["Hosting", "None", "Runs on localhost only (127.0.0.1)"],
            ["Effort", "Student team time", "Not costed"],
        ], widths=[3.0, 1.3, 2.0], size=10, align=["l", "c", "l"]),
        P("The system is therefore economically feasible for its purpose. A production deployment would add costs that this project does not estimate: hosting, security review, model monitoring and legal review of the use of "
          "demographic attributes in financial decisions."),
        H2("3.4 Operational feasibility"),
        P("The people who would use the system are an individual who wants to understand a financial profile and an analyst who wants to inspect the model. Both are served by a browser interface that needs no installation beyond "
          "starting the two servers. Operational feasibility rests on five points."),
        B("**Ease of use.** A single form of twelve fields with inline range hints and server-side validation; the result screen shows the profile, risk band, score and the factors behind it in plain language.",
          "**Ease of start-up.** `run.bat` creates the virtual environment, installs the requirements, trains the models if they are missing, builds the front end once and opens the application; the manual steps are in Appendix B.",
          "**Maintainability.** Retraining is one command; every metric is written to a JSON file that the interface reads, so a retrained model appears on the dashboard and performance screens without code changes.",
          f"**Verifiability.** {py['passed']} pytest tests, a {sm['total']}-check smoke test and a screenshot script can be run at any time to confirm that the system still works.",
          "**Responsible use.** Every analysis screen states that the output is informational, not financial advice, and the what-if screen states that it is a simulation and not a causal prediction."),
        P("Operational limits are equally clear. The login is a browser-only demo gate, nothing is stored about a person, and there is no administrator role, audit log or support process; a real service would need all three."),
        H2("3.5 Schedule feasibility"),
        P("The work was organised in the phases below. The order reflects the dependencies between them: the models cannot be explained before they are trained, and the interface cannot be built before the API exists. "
          "Calendar dates and durations are not recorded in the project artefacts and are not stated here."),
        TAB("Project phases in order", ["Phase", "Main activities", "Output", "Status"], [
            ["1  Problem identification and survey", "Abstract, base paper, literature survey, objectives", "Batch documents 2-6", "Completed"],
            ["2  Data and preprocessing", "Download Adult data, cleaning, missing values, feature engineering", "scripts/feature_engineering.py, data/", "Completed"],
            ["3  Modelling and validation", "Four pipelines, stratified split, 5-fold CV, selection, SHAP artefacts", "models/, artifacts/*.json", "Completed"],
            ["4  Forecasting", "Synthetic index, Holt-Winters model, 95% band", "scripts/forecast.py, artifacts/forecast.json", "Completed"],
            ["5  Flask application", "Validation, prediction service, what-if, server-rendered pages, JSON API", "app/", "Completed"],
            ["6  React front end", "Landing, sample login, dashboard, assessment, result, explain, forecast, what-if, performance", "frontend/", "Completed"],
            ["7  Testing and measurement", "pytest, smoke test, latency, screenshot walk-through, report metrics", "tests/, scripts/, artifacts/measured.json", "Completed"],
            ["8  Documentation", "Diagrams, figures, chapters, decks, report and paper", "Batch root documents", "Completed"],
        ], widths=[1.6, 2.4, 1.7, 0.7], size=9.5, align=["l", "l", "l", "c"]),
        H2("3.6 Advantages and constraints"),
        P("**Advantages.**"),
        B("Combines demographic and financial attributes in a non-linear model instead of a handful of ratios.",
          "Explains every assessment, globally and per person, and states that the explanation is associational.",
          "Adds a forecast and a scenario tool to the assessment in one application.",
          "Runs entirely on a desktop, offline after installation, with no data leaving the machine.",
          "Reproducible: fixed seeds, scripted training, metrics regenerated by a script and checked by tests."),
        P("**Constraints.**"),
        B("The data are a 1994 US census extract and the label is income, so the output is a profile signal and not a credit decision.",
          "The forecast series is synthetic; real macroeconomic indicators are not integrated.",
          "Sex, race and marital status are model inputs and no fairness audit was performed.",
          "No database, no real authentication and no multi-user support.",
          "Single-machine, CPU-only measurements; no load or concurrency tests."),
        P("The study concludes that the system is technically, economically and operationally feasible as a research and demonstration prototype, and not feasible without further work as a decision tool for real lending."),

        # =================================================================== CHAPTER 4
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing system and its limitations"),
        P("In the setting described by the problem statement, the existing practice is a traditional statistical score built from a small set of financial parameters. Its logic is fixed, "
          "it describes the present position only, and it does not say which factor moved the score. Research implementations of machine-learning alternatives, including the framework of the base paper "
          f"{n('base')}, are analysis code for organisations: they stop at a metric table and a SHAP plot and offer no interface for an individual."),
        TAB("Limitations of the existing approaches", ["Limitation", "Consequence"], [
            ["Narrow set of financial parameters", "Demographic context (age, education, occupation, region, household role) is ignored; outcomes can be inaccurate and unfair"],
            ["Linear or fixed scoring logic", "Non-linear interactions between factors are missed"],
            ["Static, present-only score", "No view of where economic conditions are heading"],
            ["No explanation", "The result cannot be justified to the person concerned or to a regulator"],
            ["Research code without an application", "Nothing a non-specialist can open, try or re-run; no what-if capability"],
            ["Silent about the label", "Income, default and distress are treated as interchangeable"],
        ], widths=[2.3, 4.0], size=10, align=["l", "l"]),
        H2("4.2 Proposed system and its advantages"),
        P(f"The proposed system, FinSight AI, takes twelve inputs, passes them through the same feature-engineering code that was used in training, scores them with the selected {F.MODEL_LABEL[F.BEST]} pipeline and returns "
          "a financial-strength score, a profile (Emerging, Developing or Established) and a risk band (High, Moderate or Low). The profile and risk follow fixed thresholds on the score: 0.60 or above is Established with Low risk, "
          "0.35 to 0.60 is Developing with Moderate risk and below 0.35 is Emerging with High risk. SHAP contributions for the individual case are converted into sentences, a what-if screen compares a baseline with a changed "
          "scenario, and a Holt-Winters forecast gives economic context."),
        FIG(F.diag("11_training_pipeline.png"), "Offline training and evaluation pipeline that produces the models and result files the application serves", 6.0),
        P("Its advantages over the existing approaches are the direct answers to the limitations in the table above: demographic and financial inputs together, a non-linear model selected on measured performance, "
          "a per-person explanation, a forecast, a scenario tool and a working interface. It keeps the discipline of the base paper in stating the validation protocol with every figure and in treating SHAP as association."),
        H2("4.3 Functional requirements"),
        TAB("Functional requirements and where they are implemented", ["ID", "Requirement", "Implementation"], [
            ["FR-1", "Let a user sign in with a sample account before using the analysis screens", "/login and the guarded /app routes (client-side demo gate)"],
            ["FR-2", "Collect twelve demographic and financial inputs with range hints", "/app/assess; ranges from GET /api/options"],
            ["FR-3", "Validate every field on the server and reject bad input with messages", "app/utils/validation.py; HTTP 400 with an error list"],
            ["FR-4", "Return profile, risk band, strength score and risk share for one person", "POST /api/predict; /app/result"],
            ["FR-5", "Explain each assessment with the strongest positive and negative factors in plain language", "Live SHAP in services/predictor.py; result screen"],
            ["FR-6", "Show global explainability (ranked features, importance charts)", "GET /api/explain; /app/explain; /artifacts PNGs"],
            ["FR-7", "Show a 12-month forecast with a 95% band and an interpretation", "GET /api/forecast; /app/forecast"],
            ["FR-8", "Compare a baseline with a scenario that changes gains, losses, hours or education", "POST /api/whatif; /app/whatif"],
            ["FR-9", "Show model comparison, validation protocol and statistical analysis", "GET /api/performance; /app/performance"],
            ["FR-10", "Show a dashboard of the serving model and headline metrics", "GET /api/dashboard; /app"],
            ["FR-11", "Report service health and model availability", "GET /health"],
            ["FR-12", "Offer light and dark themes and friendly 404 and error pages", "Front-end theme toggle; NotFound page; Jinja error page"],
            ["FR-13", "Keep the original server-rendered pages available", "Flask routes /, /assess, /explain, /forecast, /whatif, /performance, /about"],
            ["FR-14", "Retrain from the raw data and refresh every result file", "python scripts/train.py"],
        ], widths=[0.6, 3.1, 2.6], size=9.5, align=["c", "l", "l"]),
        H2("4.4 Non-functional requirements"),
        TAB("Non-functional requirements and the evidence", ["Quality", "Requirement", "Evidence"], [
            ["Performance", "A prediction with its explanation should feel immediate", f"Median {pred['median']:.1f} ms, 95th percentile {pred['p95']:.1f} ms for POST /api/predict (40 calls, 127.0.0.1, CPU only)"],
            ["Accuracy", "Rank profiles well and report the protocol", f"Test ROC-AUC {F.f3(F.METRICS['roc_auc'])}, accuracy {F.pct(F.METRICS['accuracy'])}, 5-fold CV AUC {F.f3(F.METRICS['cv_roc_auc_mean'])} +/- {F.f3(F.METRICS['cv_roc_auc_std'])}"],
            ["Explainability", "Every assessment shows its drivers", "Live SHAP contributions returned with every POST /api/predict"],
            ["Reliability", "Bad input must not crash the service", "Invalid age, unknown categories and empty bodies return HTTP 400; covered by tests"],
            ["Reproducibility", "Same data and seed give the same numbers", "random_state 42; re-derived metrics equal stored metrics"],
            ["Maintainability", "Small modules, tests, scripted checks", f"{py['passed']} pytest tests (all pass) and a {sm['total']}-check smoke test"],
            ["Security and privacy", "No personal data kept; local-only service", "Binds to 127.0.0.1; no storage of submitted profiles; demo login is not real authentication"],
            ["Usability", "Non-experts can complete an assessment", "One form, inline hints, plain-language result; screens captured at 1440 x 900"],
            ["Portability", "Run on a normal desktop", "run.bat on Windows; manual steps for other systems; Docker image for the Flask pages"],
        ], widths=[1.1, 2.1, 3.1], size=9.5, align=["l", "l", "l"]),
        P("Two qualities were not measured: behaviour under concurrent load and appearance on every browser and device. Chapter 7 says so where it reports testing."),
        H2("4.5 Hardware requirements"),
        P("Minimum requirements were not determined by experiment. The figures below describe the machine on which the system was built and measured, and are the only tested configuration."),
        TAB("Hardware used", ["Component", "Specification"], [
            ["Processor", env["cpu"]], ["Memory", f"{env['ram_gb']} GB"], ["Graphics processor", "Not used"],
            ["Disk", f"About 310 MB for the saved models (the Random Forest file alone is about {_model_mb():.0f} MB; the served model is {best_mb:.1f} MB), 6 MB for the raw data and space for the Python and Node.js packages"],
            ["Display", "1440 x 900 used for all screenshots"],
        ], widths=[1.7, 4.6], size=10, align=["l", "l"]),
        H2("4.6 Software requirements"),
        TAB("Software used and its version", ["Software", "Version", "Purpose"], [
            ["Operating system", env["os"], "Development and measurement"],
            ["Python", env["python"], "Training, API, scripts"],
            ["scikit-learn", env["scikit-learn"], "Pipelines, preprocessing, models, metrics"],
            ["XGBoost", env["xgboost"], "Selected classifier"],
            ["SHAP", env["shap"], "Global and local explanations"],
            ["statsmodels", env["statsmodels"], "Holt-Winters forecast; logit statistics"],
            ["Flask", env["flask"], "JSON API and server-rendered pages"],
            ["pandas, NumPy, joblib, matplotlib", "See requirements.txt", "Data handling, persistence, plots"],
            ["Node.js", env["node"], "Front-end build and preview"],
            ["React / React Router", f"{dep.get('react', '')} / {dep.get('react-router-dom', '')}", "Single-page application"],
            ["Vite", dev.get("vite", ""), "Build tool and preview server"],
            ["Recharts, Framer Motion, GSAP, Lucide", f"{dep.get('recharts', '')}, {dep.get('framer-motion', '')}, {dep.get('gsap', '')}, {dep.get('lucide-react', '')}", "Charts, motion and icons"],
            ["pytest, requests, Playwright", "pytest and requests from requirements.txt; Playwright installed separately", "Tests, smoke test, screenshot capture"],
            ["Browser", "Google Chrome", "Screenshots and manual checks"],
        ], widths=[2.1, 1.9, 2.3], size=9.5, align=["l", "l", "l"]),
        P("Front-end versions are the ranges declared in `frontend/package.json`; the Python packages are listed in `requirements.txt` as minimum versions: " + ", ".join(_reqs()) + "."),
        H2("4.7 User roles"),
        TAB("User roles", ["Role", "Description", "Can do"], [
            ["User (individual or analyst)", "Anyone who opens the web application and signs in with the sample account", "Enter a profile, read the result and its explanation, run what-if scenarios, view the forecast, explainability and performance screens"],
            ["Developer", "A person who runs the scripts on the machine", "Retrain the models, regenerate result files, run tests, smoke test and screenshot capture"],
        ], widths=[1.6, 2.3, 2.4], size=10, align=["l", "l", "l"]),
        P("There is no administrator role and no per-user data: the sample account (a fixed e-mail and password shown on the sign-in screen) only gates the screens and is stored in the browser."),
        H2("4.8 Input and output specification"),
        P("The interface between the user and the model is fixed by the twelve inputs and a small set of outputs. Allowed values are exactly the categories present in the training data, and the same lists drive the form drop-downs "
          "(through GET /api/options) and the server-side check."),
        TAB("Inputs of one assessment", ["Input", "Type", "Allowed values"], [
            ["Age", "Integer", "16 to 100"],
            ["Employment type (workclass)", "Choice", "8 values, for example Private, Self-emp-not-inc, State-gov"],
            ["Education", "Choice", "16 levels from Preschool to Doctorate; mapped to years of education (1 to 16)"],
            ["Marital status", "Choice", "7 values, for example Married-civ-spouse, Never-married"],
            ["Occupation", "Choice", "14 values, for example Exec-managerial, Sales, Other-service"],
            ["Household relationship", "Choice", "6 values, for example Husband, Wife, Own-child"],
            ["Race", "Choice", "5 values"],
            ["Sex", "Choice", "Female or Male"],
            ["Country", "Choice", "41 native-country values"],
            ["Investment gains (annual, dollars)", "Number", "0 to 1,000,000"],
            ["Investment losses (annual, dollars)", "Number", "0 to 1,000,000"],
            ["Hours worked per week", "Integer", "1 to 99"],
        ], widths=[2.4, 0.9, 3.0], size=9.5, align=["l", "c", "l"]),
        TAB("Outputs of one assessment", ["Output", "Meaning"], [
            ["Financial-strength score (strength %)", "The model's probability of the higher-income class, shown as a percentage"],
            ["Risk share", "100 minus the strength score"],
            ["Profile", "Emerging (score below 0.35), Developing (0.35 to below 0.60) or Established (0.60 and above)"],
            ["Risk band", "High, Moderate or Low, paired with the profile"],
            ["Strengthening and weakening factors", "Up to five positive and five negative SHAP contributions for this person, each with a plain-language sentence"],
            ["Insights", "Short informational messages derived from the inputs, the score and the strongest drivers, ending with a disclaimer"],
            ["Forecast context", "The 12-month index forecast with a 95% band, shown beside the result"],
        ], widths=[2.3, 4.0], size=10, align=["l", "l"]),
        P("Invalid input never reaches the model: a missing field, a value outside its set or range, or a non-numeric number produces HTTP 400 with one message per problem, and the interface shows the messages beside the fields."),
        H2("4.9 Constraints"),
        B("**Data constraint.** The only individual-level data are the 1994 Adult records; the forecast uses a synthetic series.",
          "**Label constraint.** The target is income above 50K; the system makes no statement about repayment or distress.",
          "**Input constraint.** The twelve inputs and their allowed values are the ones present in the training data; other countries or occupations cannot be entered.",
          "**Interpretation constraint.** SHAP values and what-if results describe the model, not causes in the person's life.",
          "**Resource constraint.** CPU-only training on one desktop; no hyperparameter search was run.",
          "**Regulatory constraint.** The system is informational and not financial advice; use of sex, race and marital status in a real decision would need legal and ethical review."),
    ]
