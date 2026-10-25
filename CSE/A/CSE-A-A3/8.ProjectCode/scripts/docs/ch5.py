"""Chapter 5: System design (also the source of the block-diagram document)."""

import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB


def loc(rel):
    p = os.path.join(F.CODE, rel)
    return sum(1 for _ in open(p, encoding="utf8")) if os.path.exists(p) else 0


def loc_dir(rel, exts):
    base = os.path.join(F.CODE, rel)
    n = 0
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(exts):
                n += sum(1 for _ in open(os.path.join(root, f), encoding="utf8", errors="ignore"))
    return n


MODULES = [
    ("generate_data.py", "Draws four synthetic clinical datasets (2,000 rows each, numpy seed 42): feature distributions, a linear risk score per disease, a sigmoid, a 0.5 threshold and 8% label flipping (`add_noise_labels`)"),
    ("train_models.py", "For each disease: stratified 80/20 split, StandardScaler fitted on the training part, four classifiers (`MODEL_BUILDERS`), accuracy / precision / recall / F1, selection of the model with the highest F1, `joblib.dump` of model, scaler and feature list, `training_report.json`"),
    ("app.py", "Original Flask application: loads the three pickles of each disease into `BUNDLES`, holds `FIELD_META` (label, placeholder, input type of every feature), `DISEASE_TITLES` and `TRAINING_REPORT`; routes `/`, `/diabetes`, `/heart`, `/liver`, `/kidney`; `handle_prediction()`"),
    ("backend/main.py", "FastAPI service that imports `app.py` (without modifying it) and exposes seven JSON routes; builds form metadata (`_fields`, `_options`) from `FIELD_META` and the CSV ranges; validates the request and predicts with the same steps as `handle_prediction()`"),
    ("templates/ and static/", "The two Jinja2 templates (`index.html`, `predict.html`) and the stylesheet of the original Flask pages"),
    ("frontend/src/", "React 19 single-page application: `App.jsx` (routes), `pages/` (Landing, Overview, Predict, Models, Datasets, About, NotFound), `lib/api.js` (the only network layer), `components/ui` (design-system components), `components/charts` (Recharts), `components/three` (landing-page 3-D hero)"),
    ("scripts/", "`smoke_test.py`, `api_tests.py`, `run_experiments.py`, `real_data_check.py`, `capture_screens.py`, `capture_extra.py`, `make_diagrams.py`, `make_figures.py` and the documentation builders in `scripts/docs/`"),
]

ENDPOINTS = [
    ["GET", "/api/health", "Liveness; returns the four disease keys"],
    ["GET", "/api/diseases", "Summary of each condition: best model, accuracy, F1, number of features"],
    ["GET", "/api/diseases/{d}", "Form fields (label, type, min, max, median, options), metrics of the best model, scores of all four algorithms"],
    ["GET", "/api/diseases/{d}/sample?outcome=0|1", "One random real row of `data/<d>.csv`, optionally of a given label, to pre-fill the form"],
    ["POST", "/api/predict/{d}", "Body `{\"values\": {...}}`; returns class, confidence, model and accuracy; 422 for a missing or non-finite value, 404 for an unknown disease"],
    ["GET", "/api/report", "The complete `training_report.json`"],
    ["GET", "/api/datasets", "Rows, class balance, feature list and a `synthetic: true` flag for every CSV"],
]

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "System architecture of the Intelligent Health Assistant",
     "The figure separates an offline pipeline from the online application. Offline, `generate_data.py` writes the four CSV files in `data/`, and `train_models.py` reads them and writes twelve pickle files "
     "(model, scaler and feature list for each disease) and `training_report.json` into `models/`. Online, `run.bat` starts the FastAPI service on port 8303 and the React application on port 5303; the React application "
     "calls the API with JSON over HTTP, the API imports `app.py` (which loads the pickles at start-up and holds the field metadata), and `app.py` calls scikit-learn for scaling and prediction. The API also reads the CSV files "
     "for the sample rows and dataset counts. The original Flask pages on port 5000 use the same bundles and the same arithmetic. The footnote states the main design fact: there is no SQL database, no authentication and no stored patient data."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow of the system",
     "Eight steps in two rows. Steps 1 to 3 (generate data, train and compare, select and save) are offline and are repeated only to regenerate the data or retrain. Steps 4 to 8 happen at run time: the API loads the bundles, "
     "the user chooses a disease, enters values or loads a real sample row, the API validates, scales and predicts, and the interface shows the class, the confidence, the model and its hold-out accuracy."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Data flow diagram, level 0 (context)",
     "One process, the Multi-Disease Prediction System, exchanges data with two external entities. The user sends a disease choice, patient values or a sample request and receives a risk class, a confidence, the model and its accuracy, "
     "and metrics and dataset facts. The developer runs the data generator and the training script and receives the training report. Two data stores are used: D1, the four CSV files, and D2, the pickle files and the training report."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "Data flow diagram, level 1",
     "The system is decomposed into four processes. Process 1.0 generates the datasets and writes them to D1. Process 2.0 reads D1, trains and selects the models and writes the bundles and report to D2. "
     "Process 3.0 serves form metadata, metrics and sample rows to the user from D1 and D2. Process 4.0 receives a disease and patient values from the user, reads the bundle from D2 and returns the risk class, confidence, model and accuracy."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "Data flow diagram, level 2: process 4.0 (predict risk) expanded",
     "Process 4.0 expands into five sub-processes: 4.1 validates the disease key (an unknown key returns 404 to the user), 4.2 converts every value to a finite number in the saved feature order (a missing or non-finite value returns 422), "
     "4.3 scales the vector with the saved StandardScaler, 4.4 predicts the class and the class probabilities with the saved model, and 4.5 formats the JSON result. Processes 4.2 to 4.4 read the feature order, the scaler and the model from the D2 bundle. "
     "The footnote records that validation happens twice: in the React form and again in the API."),
    ("uml", "UML class diagram", "06_uml_class_diagram.png",
     "UML class diagram (modules, tuples and scikit-learn classes of the project)",
     "The code base is function-oriented, so most boxes are modules or plain data structures drawn with a stereotype: the FastAPI routes of `backend/main.py` (with the `PredictBody` pydantic model), the Flask module `app.py` that holds "
     "`TRAINING_REPORT`, `BUNDLES`, `FIELD_META` and `DISEASE_TITLES`, the `ModelBundle` tuple (model, scaler, features), the training script, the data generator, and the four scikit-learn estimator classes with their constructor settings. "
     "Solid arrows mean uses or contains; dashed arrows mean writes files. The only real classes are the pydantic `PredictBody` and the scikit-learn estimators; no class was invented for the diagram."),
    ("seq", "Sequence diagram", "07_sequence_diagram.png",
     "Sequence diagram: predict the risk of one patient record",
     "The messages exchanged when a user opens the heart-disease page, loads a positive sample row and presses Predict risk. The React page fetches the field metadata, then the sample row, validates the form locally, and posts the values; "
     "the API checks the disease key, takes the bundle from `app.py`, converts the values, scales them, calls the model and returns the JSON result that the page shows as a result card. The footnote records that the API keeps no state between requests."),
    ("uc", "Use-case diagram", "08_use_case_diagram.png",
     "Use-case diagram",
     "Two actors and eleven use cases. The user can browse the landing page and overview, choose a disease, enter patient values, load a real sample record, predict disease risk (which includes validation of the input), "
     "view the model comparison, view the training datasets and read the about page. The developer can generate the synthetic datasets, train and select the best models and run the smoke test of the API. "
     "There is no sign-in: every user sees every screen, and predicting needs the models that the developer use cases create."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram (logical data model)",
     "The project has no database, so this is the logical data model of the artefacts the code handles. A DISEASE has one DATASET_CSV, many FEATUREs (the form inputs), one MODEL_BUNDLE (model, scaler and feature-list pickles plus the name of the best model), "
     "four ALGORITHM_RESULTs (the metrics of the four algorithms in `training_report.json`) and many PREDICTIONs; a PREDICTION is transient and exists only for the duration of one request."),
    ("flowchart", "Core algorithm flowchart", "10_core_algorithm_flowchart.png",
     "Flowchart of the core algorithm: offline training and online prediction",
     "Panel A is the offline training loop of `train_models.py`: read the CSV of a disease, split 80/20 with stratification and seed 42, fit the StandardScaler on the training part, fit and score the four algorithms, keep the one with the highest F1, "
     "dump model, scaler and features, repeat for the next disease, and finally write the training report. Panel B is the online prediction of `POST /api/predict/{d}`: check the disease key (404), convert every feature to a float and check that it is finite (422), "
     "scale, predict, derive the class and the confidence, and return the JSON."),
]


def blocks():
    d = {k: (t, f, c, x) for k, t, f, c, x in DIAGRAMS}
    n_py = sum(loc(f) for f in ("app.py", "backend/main.py", "train_models.py", "generate_data.py"))
    n_scripts = sum(loc(f"scripts/{f}") for f in os.listdir(os.path.join(F.CODE, "scripts")) if f.endswith(".py"))
    n_fe = loc_dir("frontend/src", (".jsx", ".js", ".css"))
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        H2("5.1 Design Principles"),
        B("**One set of models, two front doors.** The trained bundles and the field metadata live in `app.py`. The FastAPI service imports them instead of copying them, so the React interface and the original Flask pages cannot give different answers.",
          "**Train offline, predict online.** Training is a separate script that writes files; the web application only loads them. Nothing is trained while a user waits.",
          "**Stateless prediction.** A request carries every value it needs and the answer is computed and returned; nothing about the patient is stored or logged.",
          "**Fail early and clearly.** The form checks required and numeric fields; the API rejects a missing or non-finite value with a plain message (422) and an unknown disease with 404 before any model is called.",
          "**Say what the data is.** The Datasets page, the About page and the result card state that the training data is synthetic and that the output is not a diagnosis."),
        H2("5.2 System Architecture"),
        P(d["arch"][3]),
        FIG(F.diag(d["arch"][1]), d["arch"][2], 4.50),
        P(f"The Python code that makes the system work is small: {n_py:,} lines in the four core files (`generate_data.py`, `train_models.py`, `app.py`, `backend/main.py`), {n_scripts:,} lines in the test, measurement and documentation scripts, "
          f"and about {n_fe:,} lines in the React interface. The FastAPI layer was added for the web interface and leaves `app.py` unchanged."),
        H2("5.3 High-Level Workflow"),
        P(d["flow"][3]),
        FIG(F.diag(d["flow"][1]), d["flow"][2], 4.67),
        H2("5.4 Module Design"),
        TAB("Modules and what each is responsible for", ["Module", "Lines", "Responsibility"],
            [[f"`{m}`", (str(loc(m)) if m.endswith(".py") else {"templates/ and static/": str(loc("templates/index.html") + loc("templates/predict.html") + loc("static/style.css")),
                                                                  "frontend/src/": f"{n_fe:,}", "scripts/": f"{n_scripts:,}"}[m]), r] for m, r in MODULES],
            widths=[1.4, 0.6, 4.0], align=["l", "c", "l"], size=9),
        P("`backend/main.py` contains thirteen functions: seven route handlers (`health`, `diseases`, `disease`, `sample`, `predict`, `report`, `datasets`), the request model `PredictBody`, and five helpers (`_best`, `_options`, `_fields`, `_summary`, `_check`). "
          "`_fields` builds the form description of a disease from `FIELD_META` and from the minimum, maximum and median of each column of its CSV; `_options` turns labels such as \"Sex (1 = Male, 0 = Female)\" "
          "into drop-down options, or, for integer columns with at most six distinct values, into a list of those values."),
        H2("5.5 Data Flow"),
        P(d["dfd0"][3]),
        FIG(F.diag(d["dfd0"][1]), d["dfd0"][2], 3.74),
        P(d["dfd1"][3]),
        FIG(F.diag(d["dfd1"][1]), d["dfd1"][2], 3.91),
        P(d["dfd2"][3]),
        FIG(F.diag(d["dfd2"][1]), d["dfd2"][2], 4.50),
        H2("5.6 Class, Sequence and Use-Case Design"),
        P(d["uml"][3]),
        FIG(F.diag(d["uml"][1]), d["uml"][2], 3.74),
        P(d["seq"][3]),
        FIG(F.diag(d["seq"][1]), d["seq"][2], 3.31),
        P(d["uc"][3]),
        FIG(F.diag(d["uc"][1]), d["uc"][2], 3.74),
        H2("5.7 Database Design (Logical Data Model)"),
        P(d["er"][3]),
        FIG(F.diag(d["er"][1]), d["er"][2], 4.25),
        TAB("Entities of the logical data model", ["Entity", "Where it lives", "Key and content"],
            [["DISEASE", "Constants in `train_models.py`, `app.py`, `backend/main.py`", "Key diabetes / heart / liver / kidney; title, blurb, target column, number of features"],
             ["DATASET_CSV", "`data/<disease>.csv`", f"2,000 rows; {', '.join(str(F.CSV_FEATURES[k]) for k in F.DISEASES)} feature columns (diabetes, heart, liver, kidney) plus a 0/1 target; synthetic"],
             ["FEATURE", "Headers of the CSV; `FIELD_META` in `app.py`", "Name; label, placeholder and input type; minimum, maximum and median computed from the CSV; options for categorical inputs"],
             ["MODEL_BUNDLE", "`models/<d>_model.pkl`, `_scaler.pkl`, `_features.pkl`", "The fitted best estimator, the fitted StandardScaler, the ordered list of feature names"],
             ["ALGORITHM_RESULT", "`models/training_report.json`", "Per disease and algorithm: accuracy, precision, recall, F1 (4 decimals); name of the best model"],
             ["PREDICTION (transient)", "Request and response of one call", "Disease, values per feature; result text, positive flag, probability, model, accuracy. Not stored"]],
            widths=[1.4, 2.0, 2.6], size=9),
        P("This is a file-based design chosen for simplicity: the data are small (8,000 rows in total), read-only at run time, and contain no personal information, so a database server would add operational cost and nothing else. "
          "The consequence is that nothing can be audited afterwards, because no prediction is recorded."),
        H2("5.8 Algorithm Design"),
        P(d["flowchart"][3]),
        FIG(F.diag(d["flowchart"][1]), d["flowchart"][2], 3.31),
        P("Chapter 6 gives each step in detail. Two design decisions are worth stating here. First, **the model is selected on F1**, not on accuracy, because several of the classes are unbalanced "
          "(for example only about 28% of the liver rows and 41% of the diabetes rows are positive). Second, **the selection is made on the same 400-row test set that is then reported**; this is simple but makes the reported number of the winner slightly optimistic, "
          "and Chapter 8 shows with cross-validation and ten random splits that it also picked a model for diabetes that the repeated evidence does not support."),
        H2("5.9 API Design"),
        P("The API follows REST conventions: nouns in paths, GET for reads and POST for the one action that computes. Responses are JSON; errors carry a plain-language `detail` field. FastAPI generates interactive documentation at `/docs`. "
          "Three status codes are used by the application code: 404 for an unknown disease, 422 for a request whose values are missing or not finite numbers (and for malformed JSON, which pydantic rejects), and 200 otherwise. "
          "Cross-origin requests are allowed only from `http://localhost:5303` and `http://127.0.0.1:5303`, the origins of the React application."),
        TAB("The seven routes of backend/main.py", ["Method", "Path", "Purpose"], ENDPOINTS, widths=[0.7, 2.1, 3.2], size=9),
        H2("5.10 State and Persistence Design"),
        P("The API process holds four read-only structures built once at start-up: `BUNDLES` (the four model bundles, loaded by `app.py`), `FIELD_META`, `REPORT` (the parsed training report) and `DATA` (the four CSV files as pandas data frames, used for the sample rows, the field ranges and the dataset counts). "
          "No request changes any of them, which is why the service is safe to run with several worker threads and why a restart changes nothing. The only things written to disk are written by the training script: twelve pickle files and one JSON file."),
        H2("5.11 Security Design"),
        B("There is **no authentication, authorisation or session**: every visitor can use every route. This is acceptable for a local demonstration of a model and would not be acceptable for a service handling real patients.",
          "No patient data is stored, logged by the application code or sent to any external service; the prediction is returned to the caller only.",
          "The API accepts only JSON bodies of the form `{\"values\": {...}}` (validated by pydantic) and converts every value with `float()`, rejecting `nan` and infinity; unknown extra fields are ignored.",
          "CORS is restricted to the two origins of the React application (Section 5.9).",
          "The original Flask application starts with `debug=True` and `host=\"0.0.0.0\"` (`app.py`). That is convenient in development but exposes the Werkzeug debugger to the local network; it should not be used outside a development machine and was not changed in this project.",
          "Model files are unpickled with `joblib.load`. Pickle files from an untrusted source can execute code, so `models/` must only ever contain files produced by `train_models.py`."),
        H2("5.12 User-Interface Design"),
        P("The React interface has a landing page with a three-dimensional hero, an overview page, one prediction page per disease (the four forms share one component, `Predict.jsx`, driven by the metadata returned by the API), a model-comparison page, a dataset page, an about page and a not-found page. "
          "It has dark and light themes, a collapsible sidebar on small screens, and a status badge that polls `/api/health` every 30 seconds so that the interface says honestly when the API is not running. "
          "Each prediction form offers two buttons, Positive sample and Negative sample, that load a real row of the CSV (which does not mean the model will agree with that row's label), shows the training range under every numeric field and warns when a value is outside it, "
          "and marks missing fields as Required. The result card shows the risk class, a confidence bar, the condition, the model used, that model's hold-out accuracy and a not-a-diagnosis notice."),
        P("The layout was checked at a phone width of 390 px as well as at 1440 px; the sidebar becomes a menu and the form fields stack in one column. "
          "The overview, validation-error and phone-layout screens are shown as Figures in Chapter 8 (Section 8.12)."),
        P("The prediction and result screens, the model comparison and the dataset page are shown with their data in Chapter 8 and in Appendix C."),
    ]
