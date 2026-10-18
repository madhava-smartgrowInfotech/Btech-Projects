"""Chapter 5: System design (also the source of the block-diagram document)."""

import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB


def loc(rel):
    p = os.path.join(F.CODE, rel)
    return sum(1 for _ in open(p, encoding="utf8")) if os.path.exists(p) else 0


SRC_MODULES = [
    ("data_loader.py", "Read a CSV; detect target and ID columns; coerce numeric-looking text; profile (missing, duplicates, warnings); normalise the target to 0/1; validate before training"),
    ("preprocessing.py", "Drop duplicates; stratified train/test split; ColumnTransformer (median + StandardScaler, most-frequent + OneHotEncoder); SMOTE on the training split"),
    ("train_models.py", "MODEL_REGISTRY (LR, DT, RF, GB, HGB); train the selected models under an imbalance strategy; select the best model on a chosen metric"),
    ("evaluation.py", "Accuracy, precision, recall, F1, ROC-AUC, confusion matrix, ROC and precision-recall curves"),
    ("explainability.py", "Global importance (built-in, permutation, optional SHAP); local explanation with a coefficient-times-value fallback; readable feature labels"),
    ("risk_segmentation.py", "Score every customer, assign risk bands, sort, summarise the distribution"),
    ("prediction.py", "Score customers; validate batch columns; build the batch prediction table with optional top drivers"),
    ("retention_engine.py", "Ten IF/THEN rules plus two fallbacks that turn a profile, probability and band into retention suggestions"),
    ("persistence.py", "Save and load model.pkl, preprocessor.pkl and model_metadata.pkl with joblib"),
    ("eda.py", "KPIs and the charts of the Explore page"),
    ("sample_data.py", "Seeded synthetic Telco-style data generator"),
    ("utils.py", "Risk-band assignment from editable thresholds; tenure and charge groups; safe numeric coercion"),
]

ENDPOINTS = [
    ["Health, auth", "GET /api/health; POST /api/auth/login; GET /api/auth/me; GET /api/state", "Public: health and login. Others need a bearer token"],
    ["Data", "POST /api/data/sample, /upload; GET /api/data/preview; GET, PUT /api/data/config; GET /api/data/quality; POST /api/data/prepare", "Load, configure, check, prepare"],
    ["Exploration", "GET /api/eda; GET /api/dashboard", "Charts, KPIs, portfolio summary"],
    ["Models", "POST /api/models/train; GET /api/models/results; POST /api/models/save; GET /api/evaluation", "Train, compare, save, evaluate"],
    ["Risk", "GET, PUT /api/risk/thresholds; GET /api/risk; GET /api/customers; GET /api/customers/{id}", "Bands and Customer 360"],
    ["Explanation", "GET /api/xai/global; GET /api/xai/local/{id}; GET /api/whatif/schema; POST /api/whatif", "Drivers and scenarios"],
    ["Retention", "GET /api/retention", "Rule-based actions"],
    ["Batch, monitoring", "GET /api/batch/template; POST /api/batch/predict; GET /api/monitoring; POST /api/monitoring/drift", "Scoring a new CSV; drift"],
]

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "System architecture of ChurnIQ",
     "The system has four layers. The presentation layer is the React interface (port 5314, which proxies /api to the API) and the original Streamlit interface (port 8501). The application layer is the FastAPI service in `backend/` "
     "with 31 route handlers, bearer-token authentication and an in-memory `AppState`. The core layer is the pure-Python package `src/`, which both interfaces call and which contains no interface code. The data layer is the CSV file, "
     "the three joblib files of the saved model and the in-memory state. There is no SQL database."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow of a retention analysis",
     "Eight steps from signing in to batch scoring and monitoring. Steps 3 to 5 are repeated whenever new data or settings are chosen; the saved model of step 5 is restored automatically after a restart."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Data flow diagram, level 0 (context)",
     "One process, the ChurnIQ system, exchanges data with the analyst and with the customer data source and uses three stores: the working dataset and session state, which are in memory, and the model files on disk."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "Data flow diagram, level 1",
     "Six processes: authenticate (1.0), load, profile and prepare (2.0), train, evaluate and select (3.0), score and segment risk (4.0), explain, what-if and retention (5.0) and batch scoring and monitoring (6.0). "
     "The model artefacts written by 3.0 and read by 4.0 and 6.0 are the link between training and use."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "Data flow diagram, level 2: train, evaluate and select",
     "Process 3.0 expanded into seven sub-processes: stratified split, preprocessor fit on the training split only, imbalance handling, model fitting, evaluation on the test split, selection of the best model and saving of the artefacts. "
     "SMOTE touches only the training split."),
    ("uml", "UML class diagram", "06_uml_class_diagram.png",
     "UML class diagram (modules drawn as classes)",
     "The code base is function-oriented, so the diagram draws each module of `src/` and `backend/` as a class with the data it holds and the operations it offers. `AppState` is the only real class (a dataclass) and owns the dataset, the trial results, "
     "the active model and the risk thresholds. Arrows show which module uses which."),
    ("seq", "Sequence diagram", "07_sequence_diagram.png",
     "Sequence diagram: sign in, train, save and open Customer 360",
     "The messages exchanged when an analyst signs in, loads and prepares the sample, trains and saves a model and then opens one customer. The API validates the token on every call after the login and returns the error codes listed at the foot of the figure."),
    ("uc", "Use-case diagram", "08_use_case_diagram.png",
     "Use-case diagram",
     "One actor, the retention analyst (who also trains models), and fifteen use cases. The actor is drawn twice only to keep the lines from crossing."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram (logical data model)",
     "The project has no database, so this is the logical data model of the entities the code handles: the dataset and its customers, the trial runs, the saved model artefact, the risk record of each customer, the thresholds and the recommendations. "
     "Relationships and keys are those of the in-memory tables and the files on disk."),
    ("flowchart", "Core algorithm flowchart", "10_core_algorithm_flowchart.png",
     "Flowchart of the core algorithm: train, select, score and recommend",
     "The decisions of the pipeline: validate the data, choose the imbalance strategy, fit and evaluate the models, select and save the best, score customers, and apply the retention rules to customers at or above 60%."),
]


def blocks():
    n_src = sum(loc(f"src/{m}") for m, _ in SRC_MODULES)
    n_be = sum(loc(f"backend/{m}") for m in ("main.py", "auth.py", "state.py", "helpers.py", "config.py"))
    n_pages = sum(loc(f"pages/{f}") for f in sorted(os.listdir(os.path.join(F.CODE, "pages"))) if f.endswith(".py"))
    d = {k: (t, f, c, x) for k, t, f, c, x in DIAGRAMS}
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        H2("5.1 Design Principles"),
        B("**Core independent of the interface.** All data, modelling and business logic lives in `src/` and imports nothing from Streamlit or FastAPI. The Streamlit pages and the FastAPI routes are thin callers, so the two interfaces cannot disagree.",
          "**Explainable by construction.** Every score can be traced: coefficients or importances for the model, a list of drivers for the customer, a named rule for each retention suggestion.",
          "**Honest evaluation.** The preprocessor is fitted on the training split only, SMOTE touches only the training split, and the best model is chosen on F1 and not on accuracy alone.",
          "**Fail early and clearly.** Settings and uploads are validated on the server and rejected with a plain message (401, 404, 409, 422) before any computation starts.",
          "**No hidden services.** Nothing leaves the machine: no external API, no language model, no database server."),
        H2("5.2 System Architecture"),
        P(d["arch"][3]),
        FIG(F.diag(d["arch"][1]), d["arch"][2], 6.0),
        P(f"The code base has about {n_src:,} lines in `src/` (12 modules), {n_be:,} lines in `backend/`, {n_pages:,} lines in the 13 Streamlit pages and the React interface in `frontend/`. "
          "The FastAPI layer was added for the web interface and changes nothing in `src/`."),
        H2("5.3 Module Design"),
        TAB("Modules of the core package src/", ["Module", "Lines", "Responsibility"],
            [[f"`{m}`", str(loc(f"src/{m}")), r] for m, r in SRC_MODULES], widths=[1.5, 0.5, 4.0], align=["l", "c", "l"], size=9),
        P("The API layer has five modules: `main.py` (route handlers), `auth.py` (token creation and checking), `state.py` (the in-memory `AppState`), `helpers.py` (conversion of pandas and numpy values to JSON) and `config.py` (settings read from `.env`)."),
        H2("5.4 Data Flow"),
        P(d["dfd0"][3]),
        FIG(F.diag(d["dfd0"][1]), d["dfd0"][2], 5.6),
        P(d["dfd1"][3]),
        FIG(F.diag(d["dfd1"][1]), d["dfd1"][2], 5.8),
        P(d["dfd2"][3]),
        FIG(F.diag(d["dfd2"][1]), d["dfd2"][2], 5.8),
        H2("5.5 Class and Sequence Design"),
        P(d["uml"][3]),
        FIG(F.diag(d["uml"][1]), d["uml"][2], 5.2),
        P(d["seq"][3]),
        FIG(F.diag(d["seq"][1]), d["seq"][2], 5.4),
        H2("5.6 Logical Data Model"),
        P(d["er"][3]),
        FIG(F.diag(d["er"][1]), d["er"][2], 5.8),
        TAB("Entities of the logical data model", ["Entity", "Where it lives", "Key and content"],
            [["DATASET", "DataFrame in `AppState`; CSV on disk", "Name, row and column counts, target and ID columns, lists of numeric and categorical columns"],
             ["CUSTOMER", "Rows of the DataFrame", "customerID; the 19 feature columns; Churn"],
             ["TRIAL_RUN", "`AppState.trial` (memory)", "Model name, imbalance strategy, test size, five metrics, confusion matrix, fit time"],
             ["MODEL_ARTEFACT", "models/model.pkl, preprocessor.pkl, model_metadata.pkl", "Model name, fitted model and preprocessor, feature columns, feature names, metrics"],
             ["RISK_RECORD", "Computed on demand", "customerID, probability 0-100, risk band, top drivers"],
             ["RISK_THRESHOLDS", "`AppState.risk_thresholds`", "low 30, medium 60, high 80 by default; editable and validated"],
             ["RECOMMENDATION", "Computed on demand", "Rule name, suggestion, linked to a customer"]],
            widths=[1.3, 2.0, 2.7], size=9),
        H2("5.7 Algorithm Design"),
        P(d["flowchart"][3]),
        FIG(F.diag(d["flowchart"][1]), d["flowchart"][2], 4.6),
        P("Chapter 6 gives each step in detail. Two design decisions are worth stating here. First, **model selection uses F1 by default** (user-selectable among accuracy, precision, recall, F1 and ROC-AUC), because "
          "on 26% churn a model that never predicts churn has 74% accuracy. Second, **the rule-based retention step is gated at 60%**: nine of the ten rules require a probability of at least 60 (the High or Critical band at default thresholds) "
          "and the tenth requires the Critical band, so that low-risk customers are not sent offers."),
        H2("5.8 API Design"),
        P("The API follows REST conventions: nouns in paths, GET for reads, POST for actions that compute or change state, PUT for settings. All routes except health and login need an `Authorization: Bearer` header. "
          "Interactive documentation is served at `/docs`. Errors use four codes with a plain-language `detail` field: 401 for a missing or expired token, 404 for an unknown customer, 409 when the data or the model is not ready, and 422 for invalid input."),
        TAB("API routes by group (31 handlers)", ["Group", "Routes", "Purpose"], ENDPOINTS, widths=[1.0, 3.5, 1.5], size=8.5),
        H2("5.9 State and Persistence Design"),
        P("`AppState` mirrors Streamlit's `st.session_state` for a single user: the raw and working data frames, the detected columns, the last training comparison (`trial`), the active model, its preprocessor and metadata, the cached explainer and importances and the risk thresholds. "
          "A re-entrant lock protects it because FastAPI may handle requests on several threads. Only the active model is persisted: `save_artifacts` writes three joblib files, and `restore_from_disk` loads them when the service starts. "
          "The dataset and the comparison table are session-only, as in the Streamlit application."),
        H2("5.10 Security Design"),
        B("Demo credentials come from `.env` (`DEMO_EMAIL`, `DEMO_PASSWORD`) and are compared in constant time.",
          "The token is `base64(payload).HMAC-SHA256(payload)` with an expiry claim (12 hours); tampering or expiry makes `read_token` return nothing and the route answers 401.",
          "Uploads are accepted only as CSV and are parsed in memory; thresholds are validated server-side (Low 5-50, Medium at least 5 points above Low and at most 85, High at least 5 points above Medium and at most 95).",
          "This is a demonstration login with one shared account. It is not a substitute for real authentication, authorisation or audit logging on real customer data."),
        H2("5.11 User-Interface Design"),
        P("The ChurnIQ interface has a landing page, a demo sign-in and thirteen working pages arranged in the order of the workflow. It follows a soft pastel design kit with light and dark themes, a skip-to-content link, visible keyboard focus, "
          "reduced-motion support and layouts checked at 360, 768 and 1440 px. Each page states what it needs when a step is missing and shows plain-language errors returned by the API. The pages are shown in Chapter 8 and Appendix C."),
    ]
