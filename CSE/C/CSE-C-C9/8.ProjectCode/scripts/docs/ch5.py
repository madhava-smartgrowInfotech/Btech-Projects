"""Chapter 5: System design. The diagram explanations are shared with '11. BLOCK DIAGRAMS ALL.docx'."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

# (key, section title, file, caption, explanation)
DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png", "System architecture of FinSight AI",
     "The system has four tiers. In the presentation tier the React single-page application (served by Vite on port 5409) and the server-rendered Jinja pages of the "
     "original Flask project are the two ways a user reaches the system. The application tier is the Flask service on port 8409: `app/api.py` holds the JSON routes written "
     "for the React front end, `app/routes.py` holds the page routes plus `/api/predict` and `/api/forecast`, `app/utils/validation.py` checks every input and "
     "`app/__init__.py` builds the application and preloads the model. The model and service tier contains `predictor.py` (prediction, SHAP and insights), `whatif.py`, "
     "`forecaster.py` and the shared `feature_engineering.py`. The data tier is made of files: the persisted pipeline in `models/`, the JSON and PNG artifacts, the raw census files and browser storage."),
    ("flow", "High-level workflow", "02_high_level_workflow.png", "High-level workflow of one assessment, from sign-in to exploration",
     "One assessment passes through eight steps. The user signs in through the demo gate and enters the twelve demographic and financial fields. The server validates "
     "that every field is present, belongs to its allowed set and lies in its numeric range; a failure ends the flow with HTTP 400 and a list of messages, and no model is run. "
     "Valid input is cleaned and extended with the derived features, and the saved XGBoost pipeline returns the probability of income above 50K, which is the financial-strength "
     "score. The probability is mapped to a profile and a risk band, and SHAP contributions plus rule-based insights explain it. The user can then open the forecast, "
     "the what-if comparison and the performance screens."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png", "Data flow diagram, level 0 (context diagram)",
     "The context diagram shows FinSight AI as one process with one external entity, the user. The user sends profile fields, scenario changes and requests for the "
     "other screens; the system returns the profile, risk band, SHAP drivers, insights, forecast, metrics and what-if comparison. Three data stores surround the process. "
     "D1 holds the trained model files, which are loaded and never modified while the application runs. D2 holds the result artifacts (metrics, SHAP importance, forecast and "
     "validation reports as JSON and PNG), which are read. D3 is the Adult census data; it is touched only by the offline training run, drawn as a dashed arrow, "
     "which is the only place where D1 and D2 are written."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png", "Data flow diagram, level 1",
     "Level 1 splits the system into six processes. Validate input (1.0) turns the raw form values into a valid record or an error list. Engineer features and predict (2.0) "
     "builds the feature row and obtains the probability from the pipeline stored in D1. Explain and advise (3.0) computes SHAP contributions and plain-language insights and returns the "
     "profile, risk band, drivers and insights to the user. What-if comparison (4.0) receives a baseline and a scenario and calls process 2.0 twice. Serve forecast and metrics (5.0) answers "
     "screen requests by reading D2. Train and evaluate (6.0) runs offline: it reads the census data (D3) and writes the model files (D1) and the artifacts (D2)."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png", "Data flow diagram, level 2: processes 2.0 and 3.0 expanded",
     "Level 2 expands the prediction and explanation processes in the order the code executes them. The validated record becomes a one-row frame in which the census weight is "
     "left missing (2.1); `clean_frame` converts '?' markers to missing values (2.2); `add_derived_features` adds the net-capital, band, tier, region and stability columns, giving "
     "26 columns (2.3); the preprocessing step of the saved pipeline imputes, one-hot encodes and, for logistic regression only, scales (2.4); XGBoost returns the probability (2.5). "
     "The probability becomes a profile and risk band (2.6). In parallel the same row goes to the TreeExplainer (3.1), the five strongest positive and negative contributions are selected (3.2) "
     "and the insight rules write the advice (3.3). All of it is assembled into one result record."),
    ("uml", "UML class diagram", "06_uml_class_diagram.png", "UML class diagram (modules drawn as classes)",
     "The code base is function-oriented, so each Python module is drawn as a class stereotyped as a module, listing its constants and public functions. `RoutesBlueprint` and `ApiBlueprint` "
     "are the two Flask blueprints; both depend on `Validation` for input checking, and the routes call `Predictor`, which owns the cached model, the cached explainer and the prediction, SHAP and insight "
     "functions. `WhatIf` calls `predict_profile` twice, `Forecaster` reads the forecast artifact, and `FeatureEngineering` supplies cleaning, derived features and the preprocessor. "
     "A scikit-learn `Pipeline` combines the preprocessor with one of four classifier realisations, XGBoost being the selected one. `TrainScript` and `ForecastScript` are the offline modules."),
    ("seq", "Sequence diagram", "07_sequence_diagram.png", "Sequence diagram: one financial assessment",
     "The sequence follows one assessment. The user fills the twelve fields in the React page, which first checks the ranges in the browser and then posts the values as JSON to "
     "`/api/predict`. The route calls `validate_assessment`; on success it calls `predict_profile`, which builds the frame, derives the features and obtains the probability from the pipeline. It then asks the "
     "TreeExplainer for the SHAP values of that single row, maps the probability to a profile and band, and builds the insights. The result dictionary travels back as an HTTP 200 JSON body; the page "
     "stores it in the browser session and navigates to the result screen, which shows the profile, score bar, SHAP factors, insights and the forecast. Invalid input short-circuits with HTTP 400."),
    ("uc", "Use-case diagram", "08_use_case_diagram.png", "Use-case diagram",
     "The user can sign in with the demo account, enter a demographic and financial profile, view the profile, risk band and strength score, read the SHAP drivers and insights, explore the global "
     "explainability charts, view the 12-month forecast, run a what-if scenario, review the model performance and switch between light and dark themes. Every case except signing in sits behind the "
     "sample login gate. The second actor, the developer, trains the models and runs the tests and smoke checks from the command line; those activities are outside the web interface and are drawn "
     "separately to show that the running application never retrains a model."),
    ("er", "Entity-relationship (data model) diagram", "09_er_diagram.png", "Entity-relationship (data model) diagram",
     "FinSight AI has no relational database, so the diagram shows the data model instead of tables. Dashed boxes are transient objects that exist only inside one request: the assessment record "
     "(the twelve inputs, with education-num derived), the prediction result and the SHAP contributions, between one and ten per result. Solid boxes are persisted as JSON: the model-metrics "
     "rows (four models, with test and cross-validation scores) and the forecast points (132 history points and 12 forecast points). One request produces one result, which holds many SHAP items. "
     "Nothing about a person is written to disk; the what-if baseline lives only in browser or session storage."),
    ("flowchart", "Flowchart of the core algorithm", "10_core_algorithm_flowchart.png", "Flowchart of the core algorithm (POST /api/predict)",
     "The flowchart gives the decision logic of the prediction endpoint. A JSON profile is received and validated; a missing, disallowed or out-of-range field returns HTTP 400 with the error list. "
     "Otherwise the input frame is built (education-num looked up from the education level, census weight left missing), the cleaning and feature-derivation functions run, and "
     "`predict_proba` returns the probability p of income above 50K. Two comparisons decide the label: p of at least 0.60 gives Established with Low risk, p of at least 0.35 gives Developing with "
     "Moderate risk, and anything lower gives Emerging with High risk. The SHAP contributions and insights are then computed, strength is set to 100p and risk to 100(1-p), and a 200 response is returned."),
    ("train", "Offline training and evaluation pipeline", "11_training_pipeline.png", "Offline training and evaluation pipeline (scripts/train.py)",
     f"Training is a separate offline script with eight steps. It loads `adult.data` and `adult.test` ({F.N_ROWS:,} rows), cleans them ('?' to missing, whitespace stripped, rows without a target "
     f"dropped), engineers 26 feature columns from the 14 raw fields, and makes a stratified 80/20 split ({F.N_TRAIN:,} training and {F.N_TEST:,} test rows). Each of four classifiers is wrapped in its own "
     "Pipeline together with its preprocessor, scored by 5-fold stratified cross-validation on the training split and then fitted and evaluated on the test split. The model with the highest test "
     "ROC-AUC is selected, and the pickles, JSON reports, charts, SHAP importance and forecast are persisted for the web application to load."),
]

# Data-model table: (entity, field, type, rule, where it lives)
SCHEMA = [
    ["AssessmentRecord", "age", "integer", "16 to 100", "request body only"],
    ["AssessmentRecord", "workclass, education, marital-status, occupation, relationship, race, sex, native-country", "text (enumerations)", "must belong to the allowed list in `validation.py`", "request body only"],
    ["AssessmentRecord", "capital-gain, capital-loss", "number", "0 to 1,000,000", "request body only"],
    ["AssessmentRecord", "hours-per-week", "integer", "1 to 99", "request body only"],
    ["AssessmentRecord", "education-num", "integer (derived)", "looked up from `EDU_NUM_MAP`, 1 to 16", "added by the validator"],
    ["PredictionResult", "proba, strength_pct, risk_pct", "float", "0 to 1; 0 to 100; 100 minus strength", "response body, browser session"],
    ["PredictionResult", "profile, risk, model", "text", "Emerging / Developing / Established; Low / Moderate / High; model name", "response body"],
    ["PredictionResult", "insights", "list of text", "2 to 7 rule-generated sentences", "response body"],
    ["ShapContribution", "feature, label, shap, value, sentence", "text, text, float, float, text", "up to 5 positive and 5 negative per result", "response body"],
    ["ModelMetrics", "model, accuracy, precision, recall, f1, roc_auc, cv_roc_auc_mean, cv_roc_auc_std", "text and floats", "one row per model, four rows", "`artifacts/model_comparison.json`"],
    ["ForecastPoint", "date, value, lower, upper", "text and floats", "132 history points, 12 forecast points with a 95% band", "`artifacts/forecast.json`"],
    ["Pipeline", "preprocess + model", "scikit-learn object", "one pickle per candidate and `best_model.pkl`", "`models/*.pkl`"],
]


def diagram_blocks(heading_level=3):
    out = []
    for key, title, file, caption, text in DIAGRAMS:
        out.append(("h3" if heading_level == 3 else "h2", f"{title}"))
        out.append(FIG(F.diag(file), caption, 6.0))
        out.append(P(text))
    return out


def schema_blocks():
    return [
        P("The product has **no relational database**. The batch proposal mentioned MySQL, but nothing that FinSight AI handles needs to be stored: an assessment is computed from the request alone, "
          "the result is returned to the browser and then discarded by the server, and the only data that outlive a request are the trained pipelines and the evaluation artifacts, which are written once by the "
          "training script and then only read. Leaving out a database removes a whole class of risks (stored personal data, injection, schema migration) and keeps the system runnable with two commands. "
          "It also means there is no user history, no audit trail and no multi-user state; Chapter 10 lists this as future work."),
        TAB("Data model of FinSight AI (transient objects and persisted files)", ["Entity", "Fields", "Type", "Rule", "Where it lives"], SCHEMA,
            widths=[1.15, 1.9, 0.95, 1.5, 1.1], size=8.5),
    ]


MODULES = [
    ["`app/__init__.py`", "`create_app()`", "Application factory: reads the secret key and port, preloads the model, registers both blueprints."],
    ["`app/routes.py`", "`index`, `assess`, `explain`, `forecast`, `whatif`, `performance`, `about`, `health`, `api_predict`, `api_forecast`, error handlers", "Server-rendered pages, health check, `/api/predict`, `/api/forecast`, whitelist of served artifact images."],
    ["`app/api.py`", "`options`, `dashboard`, `explain`, `performance`, `whatif`, `_parse_overrides`", "Thin read-only JSON layer for the React front end; adds `/api/whatif`."],
    ["`app/utils/validation.py`", "`validate_assessment()`, option lists, `EDU_NUM_MAP`", "Required, allowed-set and numeric-range checks; returns a cleaned dictionary or a list of messages."],
    ["`app/services/predictor.py`", "`get_model`, `get_explainer`, `build_input_frame`, `profile_from_proba`, `local_shap`, `predict_profile`, `build_insights`, `load_json_artifact`", "Prediction, profile and risk mapping, live SHAP, plain-language insights and artifact loading."],
    ["`app/services/whatif.py`", "`run_whatif()`", "Predicts a baseline and a changed scenario and reports the score change and the verdict."],
    ["`app/services/forecaster.py`", "`get_forecast()`", "Loads the forecast artifact and flags it unavailable when it is missing."],
    ["`scripts/feature_engineering.py`", "`clean_frame`, `add_derived_features`, `build_preprocessor`, `get_output_feature_names`, `human_label`", "Cleaning, 12 derived features, the leakage-safe ColumnTransformer and readable feature names."],
    ["`scripts/models.py`", "`get_candidate_models()`", "The four classifiers and their hyperparameters."],
    ["`scripts/train.py`", "`main`, `evaluate_binary`, `save_confusion_matrix`, `save_roc_curves`", "Offline training, cross-validation, selection, SHAP artifacts, plots, reports."],
    ["`scripts/forecast.py`", "`build_index_series`, `fit_forecast`", "Synthetic index series and the Holt-Winters forecast."],
    ["`scripts/report_metrics.py`", "`main`", "Re-derives confusion matrices, threshold sweep, calibration and the forecast back-test."],
    ["`tests/`, `scripts/smoke_test.py`", "`test_app.py`, `test_features.py`", "Nine automated tests and a 35-check live smoke test."],
    ["`frontend/src/`", "11 pages, `lib/`, `components/`", "The React interface: routing, API client, theme, auth gate and charts."],
]


def blocks():
    ur = F.shot_view("01_landing-light.png")
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        H2("5.1 Architecture"),
        P("The design follows three rules: keep the model, the explanation and the user interface separate; load heavy objects once and reuse them; and write nothing about a person to disk. "
          "The original Flask project (server-rendered pages) is kept working, and a thin JSON layer and a React interface are added on top of the same service code, so there is one source of truth for every prediction."),
        FIG(F.diag("01_system_architecture.png"), "System architecture of FinSight AI", 6.0),
        P(DIAGRAMS[0][4]),
        H2("5.2 High-level workflow"),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow of one assessment, from sign-in to exploration", 6.0),
        P(DIAGRAMS[1][4]),
        H2("5.3 Data flow diagrams"),
        P("The data flow diagrams follow Yourdon notation: circles are processes, rectangles with a bold border are external entities and open-ended rectangles are data stores."),
        H3("Level 0"),
        FIG(F.diag("03_dfd_level0.png"), "Data flow diagram, level 0 (context diagram)", 5.6),
        P(DIAGRAMS[2][4]),
        H3("Level 1"),
        FIG(F.diag("04_dfd_level1.png"), "Data flow diagram, level 1", 5.6),
        P(DIAGRAMS[3][4]),
        H3("Level 2"),
        FIG(F.diag("05_dfd_level2.png"), "Data flow diagram, level 2: processes 2.0 and 3.0 expanded", 5.6),
        P(DIAGRAMS[4][4]),
        H2("5.4 UML diagrams"),
        H3("Class diagram"),
        FIG(F.diag("06_uml_class_diagram.png"), "UML class diagram (modules drawn as classes)", 6.0),
        P(DIAGRAMS[5][4]),
        H3("Sequence diagram"),
        FIG(F.diag("07_sequence_diagram.png"), "Sequence diagram: one financial assessment", 5.8),
        P(DIAGRAMS[6][4]),
        H3("Use-case diagram"),
        FIG(F.diag("08_use_case_diagram.png"), "Use-case diagram", 4.8),
        P(DIAGRAMS[7][4]),
        H2("5.5 Database and data design"),
        FIG(F.diag("09_er_diagram.png"), "Entity-relationship (data model) diagram", 5.6),
        P(DIAGRAMS[8][4]),
        *schema_blocks(),
        P("All trained objects are stored with `joblib`. The pickles record the scikit-learn and XGBoost versions that wrote them, so loading them under a newer release prints a version warning; "
          "the metrics were re-derived with the newer release and match the stored values exactly, but a production deployment should re-train and pin versions."),
        H2("5.6 Module design"),
        P("Each module has one responsibility and the dependencies point in one direction: routes call services, services call the feature-engineering code and the saved pipeline, and nothing in "
          "the online path imports the training script. The table below lists the modules and the public functions they offer."),
        TAB("Modules of FinSight AI and their responsibilities", ["Module", "Public functions", "Responsibility"], MODULES, widths=[1.5, 2.4, 2.6], size=9),
        H2("5.7 User interface design"),
        P("The React interface follows a calm, pastel design kit: a warm off-white page background, white cards with soft shadows, six pastel accents (lavender, mint, peach, sky, rose and butter) used "
          "to tell sections apart, and Plus Jakarta Sans for headings with Inter for body text. All colours, radii, shadows and the sidebar and top-bar sizes are CSS custom properties on `:root`, "
          "and a dark theme overrides the same tokens under `data-theme=\"dark\"`. The theme follows the operating system until the user presses the toggle, after which the choice is kept in browser storage."),
        P("The interface has eleven routes: a landing page, a sign-in page and, behind the sign-in gate, the dashboard, assessment, result, explainability, forecast, what-if, performance and about pages, plus a "
          "not-found page. Pages are loaded lazily, so the first load carries only the shell. A fixed sidebar with colour-coded icons gives navigation on screens of 900 pixels and wider; below that "
          "it is replaced by a bottom bar and a drawer, and the form and card grids collapse to one column below 1,000 pixels. Loading states use skeletons, results arrive with short spring animations, "
          "toasts confirm actions, errors are shown above the form with the offending field marked `aria-invalid`, and focus moves to the first invalid field."),
        FIG(ur, "Landing page of the React interface (light theme)", F.shot_w(ur, 5.6, 4.6)),
        FIG(F.shot("02_landing-dark.png"), "The same landing page in the dark theme", F.shot_w(F.shot("02_landing-dark.png"), 5.6, 4.6)),
        P("Signing in is a **demo gate**, not authentication. The login page offers a sample account (demo@finsight.ai) with a button that fills the credentials; the check runs in the browser, the user "
          "record is kept in browser storage and the guarded routes redirect signed-out visitors to the login page and return them to the page they asked for. The product stores no accounts, so there is nothing "
          "for a real login to protect; the gate exists so that the interface looks and behaves like a product, and Section 6.9 states this limit."),
        FIG(F.shot("03_login.png"), "Sign-in page with the sample account", F.shot_w(F.shot("03_login.png"), 5.6, 4.6)),
        P("The assessment form groups the twelve inputs in a four-column grid with a label, a unit or range hint under each field, validation on submit and an option to fill a sample profile. "
          "Results are shown as a profile badge, a risk badge, a score bar, strengthening and weakening SHAP factors, actionable insights, an echo of the inputs and a mini forecast chart."),
        FIG(F.shot("05_assessment.png"), "Assessment form filled with a sample profile", F.shot_w(F.shot("05_assessment.png"), 5.6, 4.6)),
        H2("5.8 Core algorithm and training pipeline"),
        P("The core algorithm is the prediction endpoint. Its decision logic is short on purpose: validate, build the frame, derive the features, call `predict_proba`, compare the probability with two "
          "fixed cut-offs, explain and return. The cut-offs 0.60 and 0.35 are design choices of this project, not learned values; on the test split they separate three groups whose observed share of "
          f"income above 50K is {F.pct(F.RM['profile_band_actual_positive_rate']['Emerging'])}, {F.pct(F.RM['profile_band_actual_positive_rate']['Developing'])} and "
          f"{F.pct(F.RM['profile_band_actual_positive_rate']['Established'])} (Chapter 8)."),
        FIG(F.diag("10_core_algorithm_flowchart.png"), "Flowchart of the core algorithm (POST /api/predict)", 4.6),
        P(DIAGRAMS[9][4]),
        FIG(F.diag("11_training_pipeline.png"), "Offline training and evaluation pipeline (scripts/train.py)", 6.0),
        P(DIAGRAMS[10][4]),
        H2("5.9 Design decisions and trade-offs"),
        P("Several decisions shaped the design. Each was a trade-off between simplicity, honesty about the data and the objectives in the project proposal, and the table records the alternative that was rejected and why."),
        TAB("Design decisions and their reasons", ["Decision", "Alternative considered", "Reason for the choice"], [
            ["Serve the saved scikit-learn Pipeline, not a separate preprocessor and model", "Pickle the model and re-implement encoding in the service", "One object guarantees that serving applies exactly the preprocessing that was measured; no training-serving skew"],
            ["Compute SHAP live for every request with `tree_path_dependent`", "Pre-compute explanations or use a background sample", "Exact per-person attributions without extra data, at a median cost of tens of milliseconds"],
            ["Fixed profile cut-offs of 0.60 and 0.35", "Learn the bands from quantiles or a third model", "Easy to explain and to audit; the observed share of income above 50K rises monotonically across the three bands"],
            ["No database", "SQLite or MySQL for assessment history", "Nothing needs to persist; avoids storing personal data; history is listed as future work"],
            ["Thin JSON layer in `app/api.py` over the existing services", "Rewrite the back end as a new service", "No duplicated logic; the original pages keep working and both front ends call the same functions"],
            ["Forecast on a separate synthetic index", "Pretend the census data can be forecast, or download a real indicator", "The census rows carry no time; a documented synthetic series lets the method be shown honestly and be replaced later"],
            ["Sample login in the browser", "Server-side accounts", "There are no accounts or stored data to protect; real authentication is deferred"],
        ], widths=[2.0, 1.9, 2.6], size=9),
        P(f"Two design choices keep the evaluation honest. First, imputation, one-hot encoding and scaling live inside the Pipeline, so cross-validation refits them on each training fold and no "
          f"information from a validation fold reaches the preprocessing step, which is the leakage the base paper {n('base')} guards against with entity-level folds. Second, the same Pipeline object "
          "is used for training, evaluation and serving, so the model that was measured is the model that answers requests."),
    ]
