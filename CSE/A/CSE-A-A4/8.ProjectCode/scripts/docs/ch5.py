"""Chapter 5: System Design (SecurePay AI). blocks() returns the whole chapter, starting with its H1."""

import os

from . import facts as F
from .blocks import B, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import cite

_BACKEND = os.path.join(F.CODE, "backend")


def _loc(rel):
    """Lines of a real source file (so the module table cannot drift from the code)."""
    p = os.path.join(F.CODE, rel)
    with open(p, encoding="utf-8", errors="ignore") as f:
        return sum(1 for _ in f)


def dfig(filename, caption, width=5.6, max_h=6.4):
    if F.REPORT:
        max_h = min(max_h, 3.3)
    path = F.diag(filename)
    return FIG(path, caption, F.shot_w(path, width, max_h))


def sfig(name, caption, width=5.6, max_h=5.2):
    if F.REPORT:
        max_h = min(max_h, 3.3)
    path = F.shot(name)
    return FIG(path, caption, F.shot_w(path, width, max_h))


def blocks():
    return (goals_and_architecture() + workflow() + dataflow() + uml() + database() + algorithms()
            + modules() + api_design() + ui_design() + decisions())


# =====================================================================================================================
def goals_and_architecture():
    if F.REPORT:
        return _r_arch()
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter turns the requirements of Chapter 4 into a design. It gives the architecture, the high-level workflow, the data flow diagrams, the UML models, "
          "the persistence design, the core algorithms, the module and API design, the interface design and the reasons for the main decisions. Every diagram was drawn from the code in "
          "`backend/`, `scripts/` and `frontend/src/`, not from a plan, and where the code departs from good design practice the chapter says so instead of drawing an idealised picture."),

        H2("5.1 Design Goals and Architecture"),
        P("Four goals shaped the design. The first is **a product-grade face on a research model**: the base paper "
          f"{cite('base')} reports training curves and sampler statistics, whereas a merchant or analyst wants a verdict, a risk band and a recommended action, so the interface speaks in "
          "business terms and keeps the model internals on a separate, clearly labelled page. The second is **reproducibility on an ordinary laptop**: everything runs on the CPU in numpy, "
          "needs no quantum hardware or cloud account, and regenerates its data and models from scripts. The third is **graceful behaviour when something is missing**: if the API is down "
          "the interface shows an offline pill and retry buttons, and if a model file is absent the API says which one. The fourth is **simplicity of operation**: one launcher, one "
          "configuration file for the two ports and a handful of files on disk."),
        P("The architecture has four tiers over a set of local files. The presentation tier is a React single-page application served by the Vite development server on port "
          f"{F.WEB_PORT}; it has seven pages and a thin client module, `lib/api.js`, that wraps `fetch` and turns every failure into a short message that is safe to show. The application tier is a "
          f"Flask 3.1 service on port {F.API_PORT} that defines {F.N_ENDPOINTS} routes (twelve in `app.py` and four in the read-only blueprint `api_extra.py`), enables CORS and converts exceptions into JSON "
          "error bodies. The model tier is a set of plain Python modules: preprocessing, the RBM classifier, the two annealing-style samplers, the training loop, the evaluation helper and the synthetic-data "
          "generator. The data tier is local files only: a CSV of 39,000 transactions, a pickled preprocessing pipeline, three pickled models, three JSON training histories and the CSV written after each "
          "bulk upload. Nothing leaves the machine; there is no external service."),
        dfig("01_system_architecture.png", "System architecture of SecurePay AI: four tiers over local files; there is no SQL database and no external service.", 5.7),
        P("State is held in one in-memory dictionary, `store`, created when the Flask module is imported. It holds the raw frame, the fitted pipeline, the three models and their histories. At start-up "
          "the module loads the CSV, tries to unpickle `models/pipeline.pkl`, and loads whichever `grbmc_*.pkl` and `history_*.json` files exist. The design is therefore a single-process, "
          "single-user one: the dictionary is shared by all requests without locking, which is acceptable for a demonstration but would have to change before the service ran several workers."),
        TAB("Tiers, technologies and responsibilities", ["Tier", "Technology", "Responsibility"], [
            ["Presentation", "React, React Router, Vite, Recharts, Framer Motion", "Seven pages, forms, tables, charts, light and dark theme, toasts, loading, empty and error states"],
            ["Application", "Flask 3.1, Flask-CORS", "Routes, request parsing, defaults for missing fields, JSON error body, CSV upload and download"],
            ["Model", "numpy, pandas, scikit-learn, imbalanced-learn", "Pipeline, GRBMC, samplers, training loop, metrics, synthetic data"],
            ["Data", "CSV, joblib pickles, JSON", "Transactions, fitted pipeline, three models, three histories, batch predictions"],
        ], widths=[1.1, 2.4, 2.8], size=10, align=["l", "l", "l"]),
    ]


# =====================================================================================================================
def workflow():
    if F.REPORT:
        return _r_workflow()
    return [
        H2("5.2 High-Level Workflow"),
        P("The system has two paths. The **build path** produces the models: data is generated or loaded, preprocessed, reduced to the 18 most important columns, split 80/20 and used to train the "
          "three classifiers, whose files and per-epoch histories are saved. It runs from `seed_models.py` or from the Model lab page. The **score path** uses the models: the values typed in the "
          "Verify form, or the rows of an uploaded CSV, are completed with defaults, one-hot encoded, aligned to the 18 training columns, scored by the three models, averaged and mapped to a risk "
          "band. Both paths are drawn in the figure below; the orange scaling step marks the stage that does not behave as intended and is examined in Section 5.6."),
        dfig("02_high_level_workflow.png", "High-level workflow: the build path creates the model files and the score path uses them.", 5.7),
        P("The two paths meet only through files and through the in-memory store. This separation keeps scoring fast, because nothing is trained while a request is served, and it lets the "
          "interface present training as an advanced, confirmed action. The interface also shows the workflow to the user in plain words on the landing page: describe the payment, prepare the "
          "features, let three models vote and get a decision band."),
    ]


# =====================================================================================================================
def dataflow():
    if F.REPORT:
        return _r_dataflow()
    return [
        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0: context"),
        P("At the context level SecurePay AI is one process with two conceptual users and one store. A merchant or analyst sends transaction fields or a CSV file and receives a fraud score, a "
          "risk level and a decision. A risk-operations user sends retraining and viewing requests and receives analytics, model metrics and the predictions file. The application has no login, so the "
          "two roles are conceptual: they use the same screens and differ only in which functions they typically need. There is no external entity such as a payment network or a database server."),
        dfig("03_dfd_level0.png", "DFD level 0: SecurePay AI exchanges transactions, scores and reports with two kinds of user and reads and writes local files.", 5.0, 4.4),
        H3("5.3.2 Level 1: six processes"),
        P("Level 1 splits the system into six processes that correspond to groups of routes. Generating and preprocessing data (1.0) reads and writes the dataset file and produces the pipeline. "
          "Training (2.0) consumes the pipeline's train and test split and writes the model and history files. Single scoring (3.0) and batch scoring (4.0) read the pipeline and the three models. "
          "Analytics and model reports (5.0) read the dataset, histories and pipeline without changing them. Export (6.0) serves the predictions file written by batch scoring."),
        dfig("04_dfd_level1.png", "DFD level 1: six processes and four data stores (D1 dataset, D2 pipeline, D3 models and histories, D4 batch predictions).", 5.7),
        TAB("Level 1 processes", ["No.", "Process", "Routes", "Reads", "Writes"], [
            ["1.0", "Generate and preprocess data", "POST /api/generate_dataset, POST /api/preprocess", "D1", "D1 (new CSV), D2 (memory)"],
            ["2.0", "Train three models", "POST /api/train, GET /api/train_status", "D2", "D3"],
            ["3.0", "Score one transaction", "POST /api/predict_single", "D1 (defaults), D2, D3", "-"],
            ["4.0", "Score a CSV batch", "POST /api/predict_batch", "D2, D3", "D4"],
            ["5.0", "Analytics and model reports", "GET /api/dataset_stats, model_history, comparison, qubo, feature_importance, dataset_info, health", "D1, D2, D3", "-"],
            ["6.0", "Export predictions", "GET /api/export_predictions, GET /api/sample_batch", "D4, D1 sample", "-"],
        ], widths=[0.45, 1.5, 2.2, 1.0, 1.15], size=9.5, align=["c", "l", "l", "l", "l"]),
        H3("5.3.3 Level 2: scoring one transaction"),
        P("Level 2 expands process 3.0, the one a user meets most often. The request is validated and any missing field is filled with the dataset mean (numeric) or mode (categorical) (3.1). The two "
          "categorical fields are one-hot encoded, missing expected columns are added with value 0 and the numeric columns should be z-scored with the fitted scaler (3.2). Each of the three "
          "models returns a fraud probability (3.3), the mean is taken and compared with 0.5 (3.4), and the probability is mapped to a risk band (3.5). The note on the diagram records the "
          "defect in 3.2."),
        dfig("05_dfd_level2.png", "DFD level 2: the five steps of process 3.0, including the scaler step whose exception is swallowed.", 5.7, 4.2),
    ]


# =====================================================================================================================
def uml():
    if F.REPORT:
        return _r_uml()
    return [
        H2("5.4 UML Models"),
        H3("5.4.1 Class and module diagram"),
        P("The backend is not object-oriented apart from one class. `GRBMC` holds the weight matrices `W` (visible to hidden) and `U` (label to hidden), the three bias vectors `b`, `c` and `d`, the "
          "learning rate, batch size and a persistent chain, and offers `gibbs_step`, `pcd_step`, `train_epoch`, `predict_proba`, `predict` and `get_qubo_matrix`. The other modules are collections of "
          "functions: `preprocessing` (one-hot, z-score, correlation filter, importance filter, three balancers and `full_pipeline`), `samplers` (the simulated-annealing and quantum-inspired "
          "gradient estimators), `train` (`train_model` and the learning-rate schedules), `evaluation`, `synthetic_data` and the Flask module with its `store`. The diagram draws them as stereotyped "
          "classes to show who calls whom: `train` creates and trains a `GRBMC` and calls the samplers, the Flask module owns the `store` and up to three models, and `api_extra` only reads the store."),
        dfig("06_uml_class.png", "Class and module diagram of the Python backend: one real class (GRBMC) and the modules that create, train and serve it.", 5.4, 6.3),
        H3("5.4.2 Sequence diagram"),
        P("The sequence below follows one click on *Run fraud check*. The Verify page posts the form values; the Vite development server proxies the call to Flask; `predict_single` obtains the "
          "pipeline from the store (loading or rebuilding it on first use), builds the feature vector, asks each of the three models for `predict_proba`, averages the results and returns a JSON "
          "object with the prediction, label, fraud probability, risk level and the three individual probabilities. The page then draws the risk meter and the per-model bars. Measured on this PC, the "
          f"API call alone (to 127.0.0.1, without the browser) has a median of {F.LATENCY['predict_single_fraud_example']['median_ms']:.0f} ms (95th percentile {F.LATENCY['predict_single_fraud_example']['p95_ms']:.0f} ms)."),
        dfig("07_sequence_prediction.png", "Sequence diagram of POST /api/predict_single with mode ensemble.", 5.6, 5.0),
        H3("5.4.3 Use-case diagram"),
        P("Seven use cases exist in the interface: verify one transaction, bulk-verify a CSV file, download the predictions, view analytics, compare models and training curves, retrain in the "
          "Model lab and download the sample CSV. The merchant or analyst role mainly uses the first three and the sample download; the risk-operations role adds analytics, model comparison and "
          "retraining. Because there is no authentication, nothing enforces this split, which is listed as a limitation in Chapter 9."),
        dfig("08_use_case.png", "Use-case diagram: seven use cases and two conceptual roles; the application has no login.", 4.8, 4.8),
        TAB("Use cases and the screen that realises them", ["Use case", "Page", "API routes used", "Result"], [
            ["Verify one transaction", "Verify", "POST /api/predict_single", "Verdict, probability, risk band, per-model bars"],
            ["Bulk-verify a CSV file", "Bulk", "POST /api/predict_batch", "Counts, metrics if Class is present, preview of 10 rows"],
            ["Download predictions", "Bulk", "GET /api/export_predictions", "CSV with Predicted_Class, Fraud_Probability, Risk"],
            ["View analytics", "Analytics", "GET /api/dataset_stats", "Fraud rate by merchant, channel, hour, amount, card signals"],
            ["Compare models", "Model comparison", "comparison, model_history, feature_importance, qubo", "Metrics table, curves, features, QUBO heat map"],
            ["Retrain models", "Model lab", "generate_dataset, preprocess, train", "New dataset, pipeline and three models"],
            ["Download sample CSV", "Bulk", "GET /api/sample_batch", "20 labelled rows from the dataset"],
        ], widths=[1.5, 1.1, 1.9, 1.8], size=9.5, align=["l", "l", "l", "l"]),
    ]


# =====================================================================================================================
def database():
    if F.REPORT:
        return _r_database()
    import csv

    cols = next(csv.reader(open(os.path.join(F.CODE, "data", "creditcard_synthetic.csv"), encoding="utf-8")))
    return [
        H2("5.5 Persistence Design"),
        P("**SecurePay AI has no SQL database.** The base paper's data is held by a fintech and is not published, and the project works on a generated file, so a relational schema would add "
          "operational cost without adding a capability. Persistence is file-based, and the 'entity-relationship' view in the figure below therefore shows files and the code paths that relate them, "
          "not tables and foreign keys."),
        dfig("09_er_diagram.png", "File-based persistence: the relations are produced by code (preprocess, train, predict_batch), not by foreign keys.", 5.6, 5.0),
        TAB("Persisted entities", ["Entity (file)", "Written by", "Contents", "Read by"], [
            ["data/creditcard_synthetic.csv", "synthetic_data.py, POST /api/generate_dataset", f"{F.DATASET['rows']:,} rows x {F.DATASET['columns']} columns: 6 transaction fields, V1 to V22, Class", "app.py start-up, analytics, preprocess"],
            ["models/pipeline.pkl", "seed_models.py only", "X_train, X_test, y_train, y_test, fitted StandardScaler, 18 column names, feature importances", "app.py start-up"],
            ["models/grbmc_{classical,sa,qa}.pkl", "seed_models.py, POST /api/train", "GRBMC object: W, U, b, c, d, sigma, learning rate, batch size, chain state", "app.py start-up, scoring, QUBO"],
            ["models/history_{mode}.json", "seed_models.py, POST /api/train", "Per-epoch accuracy, precision, recall, F1, loss, elapsed seconds, paper time label", "comparison, curves"],
            ["data/batch_predictions.csv", "POST /api/predict_batch", "Uploaded columns plus Predicted_Class, Fraud_Probability, Risk (overwritten every upload)", "GET /api/export_predictions"],
            ["data/sample_batch.csv", "created once from the dataset", "20 labelled rows", "Bulk page, GET /api/sample_batch"],
        ], widths=[1.6, 1.4, 2.2, 1.1], size=9, align=["l", "l", "l", "l"]),
        P("The data dictionary is short. The dataset has the columns " + ", ".join(f"`{c}`" for c in cols[:6]) + f", `V1` to `V22` and `{cols[-1]}` (0 for legitimate, 1 for fraud). "
          "`Merchant_Category` has seven values and `Transaction_Type` four; `Card_Present` and `Country_Match` are 0 or 1; `Time` counts seconds over a three-month window; `V1` to `V22` are standard-normal "
          "features in which the generator shifts `V3`, `V7`, `V10`, `V14` and `V17` for fraud rows. The in-memory `store` mirrors the files: `df_raw`, `pipeline_res`, `models`, `histories`, `columns` and "
          "`feature_importance`."),
        P("Two consistency hazards follow from this design and are worth stating. First, `pipeline.pkl` is written only by `seed_models.py`; retraining in the Model lab replaces the pipeline in memory and "
          "rewrites the model and history files but not `pipeline.pkl`, so after a restart the API could pair new models with the old pipeline if the feature count had changed. The Lab page compares the "
          "feature count of a new pipeline with the one the models were trained on and warns before it is used. Second, in the environment used for the measurements in this report `pipeline.pkl` could not be "
          "unpickled (it was written by a different pandas version); the API handled this as designed by rebuilding the pipeline from the same 8,000-row sample with fixed random states, and the rebuilt "
          "pipeline reproduced the stored models' test results exactly, but it shows why a pickle is a fragile format for something that must survive library upgrades."),
    ]


# =====================================================================================================================
def algorithms():
    if F.REPORT:
        return _r_algorithms()
    return [
        H2("5.6 Core Algorithms"),
        H3("5.6.1 Building the models"),
        P("The build flowchart lists the steps in the order the code runs them. The notable design choice is that balancing and feature selection happen **before** the train-test split, exactly "
          f"as the base paper describes {cite('base')}: the random forest that ranks the features sees the rows that later form the test set. With a balanced synthetic file the effect is small, but it "
          "is a form of leakage, and the held-out figures of Chapter 8 should be read with that in mind. Inside the epoch loop the three modes differ only in the way the negative phase of the gradient "
          "is estimated, which the next subsection shows."),
        dfig("10_flowchart_training.png", "Flowchart of preprocessing and training: three modes share the pipeline and differ in how the model expectation is sampled.", 4.4, 6.4),
        H3("5.6.2 The classifier and its samplers"),
        P("The classifier is a Gaussian-Bernoulli restricted Boltzmann machine with a label layer. For a z-scored input vector `v` and a one-hot label `y` the hidden units are binary with "
          "`p(h=1 | v, y) = sigmoid(b + vW/sigma + yU)`. Prediction compares the free energy of the two label hypotheses and applies a softmax, so the output is a probability of fraud. Training moves "
          "`W`, `U`, `b`, `c` and `d` along the difference between a data term and a model term. The data term is computed from the training batch; the model term needs samples from the model, and the "
          "three trainers obtain them differently."),
        EQ("ΔW = lr · ( ⟨v hᵀ⟩data − ⟨v hᵀ⟩model ) / ( batch · σ )"),
        B("**Classical PCD:** one Gibbs step per batch on a persistent chain, 200 hidden units, batch 512, learning rate 0.01·exp(−0.08·epoch).",
          "**Simulated-annealing sampling (SAS):** same learning-rate schedule as PCD, 16 parallel reads and 10 sweeps with an inverse temperature that rises from 0.5 to 10; the expectations are averaged over the reads, 65 hidden units, batch 32, and each epoch uses a stratified subsample of 3,000 training rows.",
          "**Quantum-inspired sampling (QS):** the same structure with a schedule `s` from 0 to 1, `A = 0.8(1 − s)` and `B = s`, and random tunnelling flips with probability `0.3·A`; it is a classical simulation, "
          "65 hidden units, batch 32, learning rate 0.005·exp(−0.15·epoch) + 0.0005."),
        P("It is important to be exact about what SAS and QS are. They follow the *idea* of the base paper's annealing-assisted training but they are a simplified approximation written for speed: the hidden "
          "field is computed from the batch-mean visible vector rather than from each row, and only a few sweeps are run. They are therefore not a reproduction of the D-Wave or path-integral samplers, "
          "and the training times measured here (a few seconds) are not comparable with the hours reported in the base paper."),
        dfig("12_grbmc_structure.png", "Structure of the GRBMC: 18 visible, 200 or 65 hidden and 2 label units, with the three negative-phase samplers.", 5.7, 4.9),
        H3("5.6.3 Scoring and the unscaled-input defect"),
        P("Scoring has to reproduce the training preprocessing exactly. The scoring flowchart fills missing fields, one-hot encodes, adds missing columns with 0, applies the fitted scaler, selects the "
          "18 columns, collects the three probabilities, averages them and maps the mean to a band (above 0.7 high, above 0.4 medium, otherwise low; the label is fraud when the mean exceeds 0.5). "
          f"The scaler step contains a defect in the bulk route only. `predict_single` scales the full row first and selects the 18 columns afterwards, which is correct. `predict_batch` selects the 18 columns first, so it calls the scaler on only the {F.SERVING['selected_numeric_features']} numeric columns that survived feature selection, although it was fitted on all "
          f"{F.SERVING['scaler_features']}; scikit-learn raises an error, a bare `except: pass` swallows it and the models receive unscaled values. The defect was found by code review and measured: on a fresh "
          f"{F.SERVING['fresh_rows']:,}-row batch the ensemble's accuracy is {F.pct(F.SERVING['as_served_no_scaling']['ensemble']['accuracy'])} as served and "
          f"{F.pct(F.SERVING['with_scaling']['ensemble']['accuracy'])} when the same rows are scaled correctly. It is documented, not fixed, in this project; the dashed boxes in the figure show it honestly."),
        dfig("11_flowchart_decision.png", "Flowchart of scoring in the bulk route: the dashed boxes show the scaler step that fails silently.", 4.4, 6.4),
    ]


# =====================================================================================================================
def modules():
    if F.REPORT:
        return _r_modules()
    mods = [
        ["Flask application", "backend/app.py", "Routes, in-memory store, loading of data, pipeline and models, JSON errors", "ensure_data, ensure_pipeline, predict_single, predict_batch, train, preprocess, comparison, qubo"],
        ["Read-only API", "backend/api_extra.py", "Analytics and history endpoints used by the React pages", "dataset_stats, model_history, feature_importance, sample_batch"],
        ["Preprocessing", "backend/preprocessing.py", "Encoding, scaling, correlation filter, balancing, importance filter, split", "full_pipeline, one_hot_encode, zscore_normalize, balancing_*"],
        ["Classifier", "backend/rbm_classifier.py", "GRBMC parameters, Gibbs and PCD steps, probability, QUBO matrix", "pcd_step, train_epoch, predict_proba, get_qubo_matrix"],
        ["Samplers", "backend/samplers.py", "Annealing-style and quantum-inspired gradient estimators", "simulated_annealing_grad, quantum_sampling_grad"],
        ["Training loop", "backend/train.py", "Epoch loop, learning-rate schedules, per-epoch evaluation, history", "train_model, get_lr_schedule, ensemble_predict"],
        ["Evaluation", "backend/evaluation.py", "Accuracy, precision, recall, F1, ROC-AUC, confusion matrix", "evaluate"],
        ["Data generator", "backend/synthetic_data.py", "Synthetic legitimate and fraud rows, balanced 39,000-row file", "generate_synthetic_transactions, create_balanced_39k"],
        ["Seeding script", "seed_models.py", "Builds pipeline.pkl and the three models from an 8,000-row sample", "(script)"],
        ["Smoke test", "scripts/smoke_test.py", "20 API checks, read-only unless --full is given", "(script)"],
        ["Screenshot capture", "scripts/capture_screens.py", "Playwright capture of every page", "(script)"],
    ]
    rows = [[m[0], f"`{m[1]}`", m[2], m[3], str(_loc(m[1]))] for m in mods]
    fe = sum(_loc(os.path.join("frontend", "src", "pages", f)) for f in os.listdir(os.path.join(F.CODE, "frontend", "src", "pages")) if f.endswith(".jsx"))
    return [
        H2("5.7 Module Design"),
        P("The code has eleven pieces, eight backend modules and three scripts, each with one responsibility; the table lists them with their real sizes. The separation follows the data flow: `preprocessing` never imports the "
          "classifier, `rbm_classifier` knows nothing about Flask, and `train` is the only module that connects them. This made it possible to run the experiments of Chapter 8 by importing "
          "the modules directly and replacing one name in `train`, without starting the server."),
        TAB("Backend modules, files, responsibilities and size", ["Module", "File", "Responsibility", "Key functions", "Lines"], rows,
            widths=[1.05, 1.35, 1.85, 1.6, 0.5], size=8.5, align=["l", "l", "l", "l", "r"]),
        P(f"The frontend adds {F.FRONTEND_LINES:,} lines under `frontend/src`: seven page components ({fe:,} lines), a small UI kit (`components/ui`: buttons, cards, forms, tables, tabs, toasts, overlays, "
          "navigation), four application components (`RiskMeter`, `ConfusionMatrix`, `Heatmap`, `MetricTiles`), the API client and the theme provider. Every page is loaded lazily as its own chunk so that "
          f"the charting library is fetched only when a chart page is opened. The backend has {F.BACKEND_LINES:,} lines in total."),
    ]


# =====================================================================================================================
def api_design():
    if F.REPORT:
        return _r_api()
    rows = [
        ["GET", "/", "Legacy single-page Flask template (kept as a fallback)", "-", "HTML"],
        ["GET", "/api/health", "Liveness and loaded models; drives the status pill", "-", "status, models_trained[], data_rows"],
        ["POST", "/api/generate_dataset", "Regenerate the synthetic file; clears models in memory", "n_fraud, n_legit (clamped 500-50,000)", "rows, fraud, legit, message"],
        ["GET", "/api/dataset_info", "Dataset size, columns, first five rows, describe()", "-", "rows, columns, fraud_count, legit_count, head, describe"],
        ["POST", "/api/preprocess", "Run the pipeline on the whole dataset", "method (manual, smote, tomek), top_k", "columns, train_shape, test_shape, feature_importance, dropped_corr"],
        ["POST", "/api/train", "Train the chosen modes and save files", "modes[], epochs, n_hidden", "per mode: history, metrics, config"],
        ["GET", "/api/train_status", "Epoch count and best F1 per trained mode", "-", "per mode: epochs, best_f1, last_metrics"],
        ["GET", "/api/comparison", "Table at each mode's best-F1 epoch; shows the paper's Table 1 if no history exists", "-", "Method, mode, Accuracy, Precision, Recall, F1-Score, TotalTime, best_epoch"],
        ["GET", "/api/qubo", "QUBO matrix of one trained model", "mode", "shape, display_size, Q (40x40), stats; 404 if untrained"],
        ["POST", "/api/predict_single", "Score one transaction", "transaction fields or features[], mode", "prediction, label, fraud_probability, risk_level, individual_models"],
        ["POST", "/api/predict_batch", "Score a CSV (multipart field file)", "file; optional Class column", "rows, preview[10], fraud_detected, metrics"],
        ["GET", "/api/export_predictions", "Download the last predictions file", "-", "CSV or 404"],
        ["GET", "/api/dataset_stats", "Analytics over the full dataset", "-", "by_merchant, by_channel, by_hour, amount_buckets, card_present, country_match"],
        ["GET", "/api/model_history", "Per-epoch histories of all modes", "-", "mode -> history"],
        ["GET", "/api/feature_importance", "Importance ranking and selected columns", "-", "importance[], columns, dropped_corr, train_shape, test_shape"],
        ["GET", "/api/sample_batch", "Download the 20-row sample CSV", "-", "CSV"],
    ]
    return [
        H2("5.8 API Design"),
        P(f"The API has {F.N_ENDPOINTS} routes, listed below with the fields read from the code. The conventions are few. Bodies and responses are JSON except for the CSV upload (multipart) and "
          "the two downloads. Successful calls return HTTP 200; a missing upload or an untrained model returns 400 or 404 with `{\"error\": message}`; any unexpected exception is caught, printed to the "
          "console and returned as HTTP 500 with the same body, which is what lets the interface show a readable message. Cross-origin requests are allowed from any origin. The Vite proxy forwards "
          "`/api` to port 8304, so the browser sees one origin."),
        TAB("API routes", ["Method", "Path", "Purpose", "Request fields", "Response fields"], rows,
            widths=[0.5, 1.3, 1.7, 1.25, 1.6], size=8.5, align=["c", "l", "l", "l", "l"]),
        P("Three design details deserve a comment. **Defaults:** `predict_single` accepts a partial transaction and fills every missing column with the dataset mean or mode, which is why the "
          "Verify form needs only nine fields although the model sees eighteen. **Modes:** `mode` may be `ensemble` or one of `classical`, `sa` and `qa`; only the ensemble answer contains the risk "
          "level and the per-model probabilities. **Batch input:** extra columns in an uploaded file are dropped and missing feature columns are set to 0 instead of rejecting the file, so the Bulk page "
          "checks the header itself and warns about missing columns before upload."),
    ]


# =====================================================================================================================
def ui_design():
    if F.REPORT:
        return _r_ui()
    return [
        H2("5.9 User Interface Design"),
        P("The interface was designed as a banking risk dashboard, not as a research notebook. A calm pastel palette, rounded cards and a single accent colour keep the focus on verdicts; "
          "risk is always encoded three ways (colour, word and position on the meter) so that it is readable without colour. The landing page explains the four steps and links to the six working pages; the "
          "working pages share a sidebar, a top bar with the page title, an API status pill and a theme toggle."),
        TAB("Pages and the API calls behind them", ["Route", "Page", "Content", "API calls"], [
            ["/", "Landing", "Hero, how it works, feature cards, risk signals", "-"],
            ["/app", "Dashboard", "Four KPI tiles, fraud rate by merchant, model F1 chart, sample rows, what fraud looks like", "health, dataset_info, dataset_stats, comparison"],
            ["/app/verify", "Verify", "Nine-field form, two presets, model switch, verdict, risk meter, per-model bars", "predict_single"],
            ["/app/bulk", "Bulk", "File drop, three-step progress, counts, metrics, confusion matrix, sortable preview, downloads", "predict_batch, export_predictions, sample_batch"],
            ["/app/analytics", "Analytics", "Four tabs: where, when, how much, card signals", "dataset_stats"],
            ["/app/models", "Model comparison", "Four tabs: comparison, training curves, features, QUBO matrix", "comparison, model_history, feature_importance, qubo"],
            ["/app/lab", "Model lab", "Three steps: dataset, preprocessing, training, with confirmations", "dataset_info, generate_dataset, preprocess, train"],
        ], widths=[0.9, 1.1, 2.9, 1.4], size=9, align=["l", "l", "l", "l"]),
        sfig("03_dashboard.png", "Dashboard: KPI tiles computed from the dataset and the loaded models, with the fraud rate by merchant and the best-epoch F1 of each model."),
        P("**Dashboard.** Four tiles (transaction count, fraud-labelled count, best F1, models loaded) and two charts give the overview. The F1 chart is labelled 'at best epoch', which is the "
          "base paper's convention; because the best epoch is selected on the test split the value is slightly optimistic, and Chapter 8 reports final-epoch figures as well."),
        sfig("04_verify.png", "Verify page after a check of the large online example: probability, recommended action, per-model bars and the three risk bands."),
        P("**Verify.** Two presets (an everyday grocery purchase and a large online purchase abroad) fill the form so that a first-time user sees both outcomes in two clicks. Inputs are validated in "
          "the browser before any request: numbers must be numbers and amount and time cannot be negative. The verdict card shows a headline, a risk badge, the probability on a meter whose scale marks 40 % and "
          "70 %, a recommended action and the per-model probabilities. The three anonymised features are given friendly names (history signal, location variance, spending pattern); these are labels "
          "chosen for the demonstration and the features are synthetic, so they carry no real meaning. The headline flips at 50 % while the action bands are at 40 % and 70 %, and the page says so."),
        sfig("05_bulk.png", "Bulk verification after the sample file: counts, a warning that every row was flagged, and metrics against the Class column."),
        P("**Bulk.** A three-step indicator, a drop zone and a 'try the sample file' button lead to counts, metrics and a ten-row preview. The page contains a safeguard: "
          "if every row of a file of five or more is flagged, a warning suggests checking that the values are on the training scale. The screenshot shows that "
          "safeguard firing on the bundled sample, which is the visible symptom of the scaling defect of Section 5.6.3."),
        sfig("06_analytics-where.png", "Analytics, 'Where' tab: fraud rate by merchant category and by channel over the full dataset."),
        P("**Analytics.** Four tabs answer where, when, how much and with which card signals fraud occurs, computed from the full dataset by `dataset_stats`. Because the data is synthetic these "
          "charts describe the generator's assumptions (for example, online and electronics purchases are made riskier by construction), not real fraud behaviour."),
        sfig("10_models-comparison.png", "Model comparison: metrics at each model's best epoch and the notes that separate the paper's times from the times measured here."),
        P("**Model comparison and Model lab.** The comparison page shows the three trainers side by side, with a table that places the paper's training time next to the time measured on the "
          "machine, so a reader cannot mistake one for the other. Its tabs hold the per-epoch curves, the feature ranking and the QUBO heat map. The lab regenerates data, rebuilds the pipeline and retrains, with "
          "range checks on every number, a confirmation dialog before each destructive step, an elapsed-time counter and a warning when the new feature count differs from that of the loaded models."),
        H3("5.9.1 Interface design decisions"),
        B("**Theme:** light and dark themes follow the operating system until the user toggles one; the choice is stored in `localStorage` inside a try block so a blocked store cannot break the page.",
          "**Accessibility:** the risk meter exposes `role=\"meter\"` with its value, toasts use `aria-live` (`role=\"alert\"` for errors), forms have labels, errors and hints, and the celebratory animation in the Model lab is skipped when reduced motion is requested.",
          "**Offline and error states:** the status pill reads 'API offline' when the health call fails, every data page offers a retry, and the client turns network failures into 'Cannot reach the API server.'",
          "**Loading states:** skeleton placeholders replace spinners so that layout does not jump, and each page is a lazily loaded chunk.",
          "**Responsive layout:** the sidebar becomes a menu on narrow screens; mobile captures of the dashboard, verify and bulk pages are in Appendix C."),
    ]


# =====================================================================================================================
def decisions():
    if F.REPORT:
        return _r_decisions()
    return [
        H2("5.10 Design Decisions and Trade-offs"),
        P("The table collects the main decisions with the reason for each and the cost that was accepted. It includes the weaknesses a reviewer would find, because a design chapter that lists only "
          "strengths would misdescribe the system."),
        TAB("Design decisions, reasons and costs", ["Decision", "Reason", "Cost accepted"], [
            ["Numpy implementation of the RBM", "No deep-learning framework, runs in seconds on a laptop, easy to read against the paper's equations", "Slower than optimised libraries; samplers are simplified approximations"],
            ["Classical simulation of quantum sampling", "Quantum hardware and cloud time are unavailable", "Results say nothing about quantum advantage; the QS model is only quantum-inspired"],
            ["Ensemble of three models, threshold 0.5", "Smooths the unstable PCD model and gives one probability and three bands", "A poorly calibrated model (PCD) still pulls the mean; the 0.5 cut is not tuned"],
            ["Manual undersampling to 50/50", "The base paper found SMOTE and Tomek links unhelpful at extreme imbalance", "Discards most legitimate rows; the 1 % experiments of Chapter 8 show the cost in false alarms"],
            ["Synthetic dataset", "The base paper's data is proprietary and no public data was fixed for this project", "All performance figures describe the generator, not real fraud"],
            ["File-based persistence", "No SQL server to run, files are easy to inspect", "No transactions, shared single CSV for batch output, fragile pickles"],
            ["Single-process in-memory store", "Fast and simple for one user", "Not safe for several workers; no locking"],
            ["Broad `try/except` around the scaler", "Intended to tolerate missing columns", "Silently disables scaling, the defect measured in Chapter 8"],
            ["Flask development server with `debug=True`, host 0.0.0.0", "Convenient auto-reload for a demonstration", "Not for production: the debugger and an open host should be removed before any deployment"],
            ["No authentication", "Prototype scope", "Anyone who can reach the port can score, retrain or overwrite the models"],
        ], widths=[1.8, 2.3, 2.2], size=9, align=["l", "l", "l"]),
        P("In summary, the design separates the build path from the score path, keeps every stage replaceable and keeps all state in a few inspectable files. Its main weaknesses, the silent scaling "
          "failure, pre-split feature selection and a shared in-memory store, are the result of prototype-level shortcuts rather than of the architecture, and each can be removed without changing the "
          "structure drawn in this chapter."),
    ]


# =====================================================================================================================
# Compact variants used by the full report (F.REPORT). The chapter documents keep the full text above.
def _r_arch():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter turns the requirements of Chapter 4 into a design: architecture, workflow, data flow, UML models, persistence, core algorithms, modules, API and interface. "
          "Every diagram was drawn from the code in `backend/` and `frontend/src/`, and where the code departs from good practice the chapter says so."),
        H2("5.1 Design Goals and Architecture"),
        P("Four goals shaped the design: a product-grade face on a research model (verdict, risk band and action instead of training curves), reproducibility on an ordinary CPU with no quantum hardware or "
          f"cloud account, graceful behaviour when the API or a model file is missing, and simple operation (one launcher, two ports, a few files). The base paper {cite('base')} offered no interface, so this layer is ours."),
        P(f"The architecture has four tiers over local files: a React and Vite single-page application on port {F.WEB_PORT}, a Flask 3.1 service on port {F.API_PORT} with {F.N_ENDPOINTS} routes and JSON error bodies, "
          "plain Python model modules (preprocessing, the RBM classifier, two samplers, the training loop, evaluation, the data generator) and a data tier of a CSV, a pickled pipeline, three pickled models, "
          "three JSON histories and the last batch-prediction CSV. Nothing leaves the machine."),
        dfig("01_system_architecture.png", "System architecture of SecurePay AI: four tiers over local files; there is no SQL database and no external service.", 5.7),
        P("State lives in one in-memory dictionary, `store`, shared by all requests without locking, which suits a single-user demonstration but would have to change before several workers were used."),
    ]


def _r_workflow():
    return [
        H2("5.2 High-Level Workflow"),
        P("The **build path** generates or loads data, preprocesses it, keeps the 18 most important columns, splits 80/20, trains the three classifiers and saves files and histories; it runs from `seed_models.py` "
          "or the Model lab. The **score path** completes the form values or CSV rows with defaults, one-hot encodes, aligns to the 18 columns, scores with the three models, averages and maps to a risk band. "
          "The orange step marks the stage that misbehaves in the bulk route (Section 5.6)."),
        dfig("02_high_level_workflow.png", "High-level workflow: the build path creates the model files and the score path uses them.", 5.7),
    ]


def _r_dataflow():
    return [
        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0 and level 1"),
        P("At level 0 SecurePay AI is one process: a merchant or analyst sends transaction fields or a CSV file and receives a score, risk level and decision; a risk-operations user requests retraining and views "
          "analytics. There is no login, so the roles are conceptual, and no external entity."),
        dfig("03_dfd_level0.png", "DFD level 0: two kinds of user exchange transactions, scores and reports with the application, which reads and writes local files.", 5.0, 3.0),
        P("Level 1 has six processes: generate and preprocess data (1.0), train (2.0), score one transaction (3.0), score a CSV batch (4.0), analytics and model reports (5.0) and export (6.0), "
          "over four stores: dataset (D1), pipeline (D2), models and histories (D3) and batch predictions (D4)."),
        dfig("04_dfd_level1.png", "DFD level 1: six processes and four data stores.", 5.7),
        H3("5.3.2 Level 2: scoring one transaction"),
        P("Level 2 expands process 3.0: validate and fill defaults (3.1), align columns and scale numeric columns (3.2), score with the three models (3.3), average and threshold at 0.5 (3.4) "
          "and assign the risk band at 0.4 and 0.7 (3.5). This route scales correctly; the bulk route does not (Section 5.6)."),
        dfig("05_dfd_level2.png", "DFD level 2: the five steps of process 3.0 (POST /api/predict_single).", 5.7, 3.0),
    ]


def _r_uml():
    return [
        H2("5.4 UML Models"),
        P("Only one class exists: `GRBMC` holds the weights `W` and `U`, the biases `b`, `c` and `d` and a persistent chain, and offers `gibbs_step`, `pcd_step`, `train_epoch`, `predict_proba` and "
          "`get_qubo_matrix`. The other modules are function collections; `train` creates and trains a `GRBMC` and calls the samplers, the Flask module owns the `store`, and `api_extra` only reads it."),
        dfig("06_uml_class.png", "Class and module diagram of the Python backend.", 5.4, 3.3),
        P("The sequence diagram follows one click on *Run fraud check*: the Verify page posts the form, the Vite proxy forwards it, `predict_single` builds the feature vector, asks the three models for "
          f"`predict_proba`, averages and returns a JSON object. The API call alone has a median of {F.LATENCY['predict_single_fraud_example']['median_ms']:.0f} ms (95th percentile {F.LATENCY['predict_single_fraud_example']['p95_ms']:.0f} ms)."),
        dfig("07_sequence_prediction.png", "Sequence diagram of POST /api/predict_single with mode ensemble.", 5.6, 3.3),
        P("The seven use cases are verify, bulk-verify, download predictions, view analytics, compare models, retrain in the Model lab and download the sample CSV; without authentication nothing enforces the two roles."),
        dfig("08_use_case.png", "Use-case diagram: seven use cases and two conceptual roles.", 4.8, 3.2),
    ]


def _r_database():
    return [
        H2("5.5 Persistence Design"),
        P("**SecurePay AI has no SQL database.** The base paper's data is proprietary and the project works on a generated file, so persistence is file-based and the entity view shows files and the code "
          "paths that relate them, not tables and keys."),
        dfig("09_er_diagram.png", "File-based persistence: relations are produced by code, not by foreign keys.", 5.6, 3.3),
        TAB("Persisted entities", ["Entity (file)", "Written by", "Contents"], [
            ["data/creditcard_synthetic.csv", "synthetic_data.py, generate_dataset", f"{F.DATASET['rows']:,} rows x {F.DATASET['columns']} columns, Class label"],
            ["models/pipeline.pkl", "seed_models.py only", "Train and test split, fitted scaler, 18 column names, importances"],
            ["models/grbmc_*.pkl (3)", "seed_models.py, train", "W, U, b, c, d, sigma, learning rate, chain state"],
            ["models/history_*.json (3)", "seed_models.py, train", "Per-epoch accuracy, precision, recall, F1, loss, seconds"],
            ["data/batch_predictions.csv", "predict_batch", "Uploaded columns plus prediction, probability, risk"],
        ], widths=[1.9, 1.7, 2.7], size=9.5, align=["l", "l", "l"]),
        P("Two hazards follow. `pipeline.pkl` is written only by `seed_models.py`, so retraining in the lab can leave a stale pipeline on disk (the lab warns when the feature count differs). And in the measuring "
          "environment `pipeline.pkl` could not be unpickled (different pandas version); the API rebuilt it from the same 8,000-row sample and reproduced the stored models' results exactly, which shows why a pickle is fragile."),
    ]


def _r_algorithms():
    return [
        H2("5.6 Core Algorithms"),
        P("The build flowchart lists the steps in code order. Balancing and feature selection happen **before** the train-test split, as in the base paper "
          f"{cite('base')}, so the random forest that ranks the features sees rows that later form the test set; with a balanced synthetic file the effect is small, but it is leakage."),
        dfig("10_flowchart_training.png", "Flowchart of preprocessing and training: three modes share the pipeline and differ in how the model expectation is sampled.", 4.4, 3.3),
        P("The classifier is a Gaussian-Bernoulli RBM with a label layer: `p(h=1 | v, y) = sigmoid(b + vW/sigma + yU)`, and prediction compares the free energy of the two labels and applies a softmax. "
          "Training moves the parameters along the difference between a data term and a model term, and the three trainers differ only in how they sample the model term."),
        EQ("ΔW = lr · ( ⟨v hᵀ⟩data − ⟨v hᵀ⟩model ) / ( batch · σ )"),
        B("**PCD:** one Gibbs step on a persistent chain, 200 hidden units, batch 512, learning rate 0.01·exp(−0.08·epoch).",
          "**SAS:** 16 reads and 10 sweeps with inverse temperature rising from 0.5 to 10, 65 hidden units, batch 32, 3,000-row subsample per epoch.",
          "**QS:** schedule `s` from 0 to 1, `A = 0.8(1 − s)`, `B = s`, tunnelling flips with probability `0.3·A`; a classical simulation, 65 hidden units, batch 32."),
        P("SAS and QS follow the *idea* of the base paper's annealing-assisted training but are simplified approximations (the hidden field uses the batch-mean visible vector and only a few sweeps run); "
          "they are not the D-Wave or path-integral samplers, and their training times of a few seconds are not comparable with the paper's hours."),
        P(f"Scoring must reproduce the training preprocessing. `predict_single` scales the full row first and selects the 18 columns afterwards, which is correct. `predict_batch` selects first, so it calls the scaler on only "
          f"{F.SERVING['selected_numeric_features']} of the {F.SERVING['scaler_features']} columns it was fitted on; scikit-learn raises, a bare `except: pass` swallows it and the models receive unscaled values. On a fresh "
          f"{F.SERVING['fresh_rows']:,}-row batch the ensemble's accuracy is {F.pct(F.SERVING['as_served_no_scaling']['ensemble']['accuracy'])} as served and {F.pct(F.SERVING['with_scaling']['ensemble']['accuracy'])} scaled. "
          "The defect is documented, not fixed."),
        dfig("11_flowchart_decision.png", "Flowchart of scoring in the bulk route: the dashed boxes show the scaler step that fails silently.", 4.4, 3.3),
    ]


def _r_modules():
    mods = [
        ["Flask application", "backend/app.py", "Routes, in-memory store, loading, JSON errors"],
        ["Read-only API", "backend/api_extra.py", "Analytics and history endpoints"],
        ["Preprocessing", "backend/preprocessing.py", "Encoding, scaling, filters, balancing, split"],
        ["Classifier", "backend/rbm_classifier.py", "GRBMC, Gibbs and PCD steps, probability, QUBO"],
        ["Samplers", "backend/samplers.py", "Annealing-style and quantum-inspired gradients"],
        ["Training loop", "backend/train.py", "Epochs, schedules, per-epoch evaluation"],
        ["Evaluation", "backend/evaluation.py", "Accuracy, precision, recall, F1, ROC-AUC"],
        ["Data generator", "backend/synthetic_data.py", "Synthetic 39,000-row file"],
    ]
    rows = [[m[0], f"`{m[1]}`", m[2], str(_loc(m[1]))] for m in mods]
    return [
        H2("5.7 Module Design"),
        P(f"The backend ({F.BACKEND_LINES:,} lines) has eight modules with one responsibility each; `preprocessing` never imports the classifier, `rbm_classifier` knows nothing about Flask and `train` is the only "
          f"module that connects them, which let the experiments of Chapter 8 run without the server. The frontend adds {F.FRONTEND_LINES:,} lines: seven lazily loaded pages, a small UI kit and the API client."),
        TAB("Backend modules and their real size", ["Module", "File", "Responsibility", "Lines"], rows, widths=[1.2, 1.9, 2.5, 0.6], size=9, align=["l", "l", "l", "r"]),
    ]


def _r_api():
    rows = [
        ["GET", "/api/health", "Liveness, loaded models", "status, models_trained[]"],
        ["POST", "/api/generate_dataset", "Regenerate the synthetic file", "rows, fraud, legit"],
        ["GET", "/api/dataset_info", "Size, columns, first rows", "rows, columns, head"],
        ["POST", "/api/preprocess", "Run the pipeline (manual, smote, tomek)", "columns, shapes, importance"],
        ["POST", "/api/train", "Train chosen modes and save", "history, metrics, config"],
        ["GET", "/api/train_status", "Epochs and best F1 per mode", "per-mode summary"],
        ["GET", "/api/comparison", "Table at each best-F1 epoch", "Accuracy ... TotalTime"],
        ["GET", "/api/qubo", "QUBO matrix of a model", "shape, Q (40x40), stats"],
        ["POST", "/api/predict_single", "Score one transaction", "prediction, probability, risk_level"],
        ["POST", "/api/predict_batch", "Score a CSV upload", "rows, preview, metrics"],
        ["GET", "/api/export_predictions", "Last predictions CSV", "CSV or 404"],
        ["GET", "/api/dataset_stats", "Analytics over the dataset", "by_merchant, by_hour, ..."],
        ["GET", "/api/model_history", "Per-epoch histories", "mode -> history"],
        ["GET", "/api/feature_importance", "Importance ranking, columns", "importance[], columns"],
        ["GET", "/api/sample_batch", "20-row sample CSV", "CSV"],
        ["GET", "/", "Legacy Flask page (fallback)", "HTML"],
    ]
    return [
        H2("5.8 API Design"),
        P(f"The API has {F.N_ENDPOINTS} routes. Bodies are JSON except the CSV upload and two downloads; a missing upload or untrained model returns 400 or 404 with an error message, any other exception "
          "is caught and returned as HTTP 500, and CORS allows every origin. `predict_single` fills missing fields with the dataset mean or mode, and `predict_batch` drops extra columns and zero-fills missing ones."),
        TAB("API routes", ["Method", "Path", "Purpose", "Response fields"], rows, widths=[0.55, 1.75, 2.2, 1.8], size=8.5, align=["c", "l", "l", "l"]),
    ]


def _r_ui():
    return [
        H2("5.9 User Interface Design"),
        P("The interface is a banking risk dashboard, not a research notebook: a calm palette, rounded cards and one accent colour, with risk encoded by colour, word and meter position. "
          "Light and dark themes, an offline pill with retry, skeleton loading and reduced-motion handling are built in; mobile views are in Appendix C."),
        TAB("Pages and the API calls behind them", ["Route", "Page", "Content", "API calls"], [
            ["/", "Landing", "Hero, how it works, risk signals", "-"],
            ["/app", "Dashboard", "KPI tiles, fraud rate by merchant, model F1", "health, dataset_stats, comparison"],
            ["/app/verify", "Verify", "Nine-field form, presets, verdict, risk meter, per-model bars", "predict_single"],
            ["/app/bulk", "Bulk", "File drop, counts, metrics, preview, downloads", "predict_batch, export_predictions"],
            ["/app/analytics", "Analytics", "Where, when, how much, card signals", "dataset_stats"],
            ["/app/models", "Model comparison", "Comparison, curves, features, QUBO map", "comparison, model_history, qubo"],
            ["/app/lab", "Model lab", "Dataset, preprocessing, training with confirmations", "generate_dataset, preprocess, train"],
        ], widths=[0.9, 1.1, 2.9, 1.4], size=9, align=["l", "l", "l", "l"]),
        sfig("04_verify.png", "Verify page after the large online example: probability, recommended action, per-model bars and risk bands."),
        P("**Verify** has two presets so that a first-time user sees both outcomes in two clicks; the headline flips at 50 % while the action bands sit at 40 % and 70 %. The three anonymised features carry friendly names "
          "(history signal, location variance, spending pattern) chosen for the demonstration; the data is synthetic, so they have no real meaning."),
        sfig("05_bulk.png", "Bulk verification of the bundled sample: a warning that every row was flagged, and metrics against the Class column."),
        P("**Bulk** warns when every row of a file of five or more is flagged; the screenshot shows it firing on the bundled sample, the visible symptom of the scaling defect of Section 5.6."),
        sfig("10_models-comparison.png", "Model comparison: metrics at each model's best epoch, with the paper's training times kept apart from the times measured here."),
        P("The **Model lab** regenerates data, rebuilds the pipeline and retrains, with range checks, a confirmation before each destructive step and a warning when the feature count changes."),
    ]


def _r_decisions():
    return [
        H2("5.10 Design Decisions and Trade-offs"),
        TAB("Design decisions, reasons and costs", ["Decision", "Reason", "Cost accepted"], [
            ["Numpy RBM, simulated samplers", "Runs in seconds on a laptop; no quantum hardware or cloud time", "Simplified samplers; only quantum-inspired"],
            ["Ensemble of three, threshold 0.5", "One probability and three bands; smooths unstable PCD", "Poorly calibrated PCD still pulls the mean"],
            ["Manual undersampling to 50/50", "Base paper found SMOTE and Tomek unhelpful", "Discards rows; false alarms at 1 % fraud (Chapter 8)"],
            ["Synthetic dataset", "Base paper's data is proprietary", "Figures describe the generator, not real fraud"],
            ["File persistence, in-memory store", "No server to run; files are inspectable", "No locking, fragile pickles"],
            ["Broad `try/except` around the scaler", "Meant to tolerate missing columns", "Silently disables scaling in the bulk route"],
            ["Dev server, debug on, no authentication", "Convenient for a demonstration", "Not for production"],
        ], widths=[1.9, 2.3, 2.1], size=9.5, align=["l", "l", "l"]),
        P("The main weaknesses (the silent scaling failure, pre-split feature selection and a shared store) are prototype shortcuts, not architectural limits, and each can be removed without changing the structure drawn in this chapter."),
    ]
