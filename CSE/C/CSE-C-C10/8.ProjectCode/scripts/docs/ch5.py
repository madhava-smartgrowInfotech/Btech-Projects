"""Chapter 5: System Design. Also holds DIAGRAMS, the list used by 11. BLOCK DIAGRAMS ALL.docx."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, PAIR, TAB

_PK = F.LAT["predict_k50"]
_P10 = F.LAT["predict_k10"]

# (key, title, file, caption, explanatory paragraph(s)); every box and arrow of the images mirrors the code
DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "System architecture of VenturePulse: presentation, application and domain tiers over two stores.",
     "The system has three tiers over two stores. The presentation tier is a React 18 single-page application built with Vite 6 and Tailwind CSS 4 and served on port 5410; it has six screens (the landing page, the "
     "sign-in and the Dashboard, Analyze, Performance and Insights screens), an API client that adds the bearer token and sends every call through the Vite proxy to port 8410, and a UI kit with Recharts "
     "charts and a light and dark theme. The application tier is the FastAPI service (`app/main.py` and `app/api_extra.py`, port 8410) with four groups of routes: prediction (`POST /predict`, `POST /predict-form`), "
     "model and data (`/api/health`, `/api/model-metrics`, `/api/insights`), React helpers (`/api/config`, `/api/feature-importance`, `/api/auth/login` and `/api/auth/me`) and the original Jinja pages. "
     "Three services (`store.ensure_artifacts`, `predictor.predict_one` and `insights.compute_insights`) and one `STATE` dictionary, loaded once, keep the routes thin. The domain tier is `app/ml/` with six modules "
     "(dataset, preprocessing, embeddings, retrieval, models and evaluation) built on scikit-learn, XGBoost and sentence-transformers. The two stores are the `models/` folder (best model, preprocessor, fused training "
     "vectors, metadata) and the CSV in `data/raw/` or, if there is none, the synthetic fallback. There is no SQL database."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow: the training path (first start or `scripts/train.py`) and the inference path (every `POST /predict`).",
     "The workflow has two paths that share the saved artefacts. Path A starts from the startup table (the public CSV or the synthetic fallback), removes duplicates, maps the target (acquired or IPO to 1, closed to 0), adds "
     "the log of the funding and masks company names, embeds every description once with MiniLM, and runs five stratified 80/20 splits with seed 42. In each split the preprocessor is fitted on the training part only, "
     "the blocks are fused and four models are fitted; the mean and standard deviation are taken, the best model by balanced accuracy is refitted on all rows and seven artefacts are saved. Path B takes a startup profile "
     "(19 fields) and k, validates it against the Pydantic ranges and the 2,000-character limit, scales and one-hot encodes the structured fields and embeds the description, fuses the two, and obtains the probabilities "
     "and the balanced top-k retrieval; the result is the outcome, confidence, risk label, explanation and the similar startups. The same fitted preprocessor, model and training matrix are loaded once into `STATE` and used by "
     "every request and by the Jinja pages."),
    ("dfd0", "Data flow diagram, level 0 (context)", "03_dfd_level0.png",
     "Level 0 data flow diagram: the system as one process with three external entities.",
     "At the context level VenturePulse is one process. The founder or investor (the analyst) sends the demo credentials and a startup profile with a description and k, and receives the outcome, probabilities, "
     "confidence, risk and explanation, and also the similar startups, charts, model metrics and insights. The model owner (the trainer) sends a train and evaluate request and receives the evaluation results and the saved "
     "artefacts. The startup table, a CSV or the synthetic generator, supplies the startup records."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "Level 1 data flow diagram: five processes and four data stores.",
     "Level 1 has five processes. 1.0 Validate input receives the startup profile from the founder or investor, answers with a 422 error if a value is outside its range, and otherwise passes a valid payload on. "
     "2.0 Predict outcome loads the model and the preprocessor from D1 (joblib files and `metadata.json`) and produces the fused vector and the probabilities. 3.0 Retrieve and explain runs the cosine search over "
     "D2 (`train_fused.npz` and `train_frame.pkl`, training rows only) and returns the outcome, confidence, risk, explanation and the similar startups to the user. 4.0 Serve metrics and insights reads the results "
     "from D3 (`evaluation_results.json`) and returns metrics, insights and feature weights on request. 5.0 Train takes the train request of the model owner and the startup rows from D4 (the startup CSV) and writes "
     "the artefacts and results. The demo sign-in (`/api/auth/login`) is not drawn as a process because it handles no startup data. Processes 2.0 and 3.0 are expanded in the level 2 diagram."),
    ("dfd2", "Data flow diagram, level 2 (processes 2.0 and 3.0)", "05_dfd_level2.png",
     "Level 2 data flow diagram: the steps inside 2.0 Predict outcome and 3.0 Retrieve and explain (`predict_one`).",
     "Process 2.0 has five steps. 2.1 `build_input_row` turns the validated payload into a typed one-row table and adds the log of the funding. 2.2 `pre.transform` imputes, scales and one-hot encodes it into "
     "37 structured values using the fitted preprocessor from D1. 2.3 `embed_texts` embeds the description into 384 values, or the text \"<industry> startup\" when the description is empty. 2.4 fuses the two blocks with "
     "weight 0.5 each and scales to unit length, giving a 421-value vector. 2.5 `predict_proba` gives the probabilities and the outcome is the larger one. Process 3.0 has three steps. 3.1 `retrieve_similar` ranks the "
     "training matrix D2 by cosine similarity and keeps a balanced top-k. 3.2 builds the explanation from the top five model weights and the retrieval statistics. 3.3 adds the risk label and returns the JSON "
     "response to the Analyze screen."),
    ("uml", "UML class diagram", "06_uml_class_diagram.png",
     "UML class diagram of the main classes and modules.",
     "The code is organised as small modules with one validation class, and the diagram shows both. `PredictPayload` is the Pydantic model with the field ranges and the validators `check_desc` and `check_k`. "
     "The FastAPI app (`app/main.py` plus `app/api_extra.py`) holds the route functions (`predict_api`, `predict_form_post`, `health`, `model_metrics`, `insights`, `config`, `feature_importance`, `login`, `me`). "
     "The `Store` module owns the `STATE` dictionary and `ensure_artifacts`. The `Predictor` module has `build_input_row` and `predict_one`, which uses `Retrieval` (`fuse`, `retrieve_similar`, with the constant ALPHA = 0.5), "
     "`Embeddings` (`load_model`, `embed_texts`, `l2norm`) and `Preprocessing` (`prepare_frame`, `build_preprocessor`, `feature_names`). `Evaluation + Models` holds `get_models`, `run_evaluation` and `compute_metrics` "
     "with N_SPLITS = 5, TEST_SIZE = 0.2 and RANDOM_STATE = 42, and `Dataset + Insights` holds `load_dataset`, `generate_synthetic`, `map_target`, `clean_text` and `compute_insights`. "
     "Arrows show which module calls which: the app validates and calls the store and the predictor; the store reads the artefacts and, on a first run, loads the dataset and runs the evaluation."),
    ("seq", "Sequence diagram: predicting one startup", "07_sequence_diagram.png",
     "Sequence diagram of one `POST /predict` request, from the Analyze screen to the model and back.",
     "The Analyze page posts the fields, the description and k (step 1). FastAPI validates them with the Pydantic model (2) and returns 422 if they are invalid. The route calls `ensure_artifacts` (3) and gets the "
     "loaded `STATE` (4), then calls `predict_one` (5). The predictor builds the typed row with the log of the funding (6) and transforms it with the preprocessor into 37 values (7), asks the embedding module "
     "for the 384-value description vector (8), fuses the two (9) and calls `predict_proba` on the best model (10), which returns P(failure) and P(success); the outcome is the arg-max and the confidence the maximum. "
     "It then retrieves the k comparable rows, half SUCCESS and half FAILURE (11), builds the explanation bullets and the risk label (12) and returns the result (13). The route answers with 200 and the JSON, or 422 or 500 "
     "with a detail message (14)."),
    ("uc", "Use case diagram", "08_use_case_diagram.png",
     "Use case diagram: two actors and eight use cases of VenturePulse.",
     "The founder or investor signs in with the demo account, which precedes the other use cases, and can view the dashboard, analyse a startup, view the model performance and view the startup insights. "
     "Analysing a startup includes validating the inputs, inspecting the comparable startups and seeing the key contributing features. The model owner can train and evaluate the models (the scripts and the first-start training) "
     "and view the startup insights. The product has one demo account; the two actors only show who typically starts which use case."),
    ("er", "Entity-relationship diagram (file-based data model)", "09_er_diagram.png",
     "Entity-relationship diagram of the data model; the product has no SQL database.",
     "VenturePulse stores its data in files. The STARTUP_RECORD table (`train_frame.pkl`) holds the 20 raw columns of a startup, the label, the outcome and the log of the funding; it is aligned one to one with "
     "the FUSED_MATRIX (`train_fused.npz`, 421 values per row) and the TEXT_EMBEDDING (`text_embeddings.npz`, 384 values per row). A PREDICTION_REQUEST (the `PredictPayload`) produces one PREDICTION_RESULT, which "
     "contains up to k SIMILAR_CASE items taken from STARTUP_RECORD at request time, and names the best model. The fitted PREPROCESSOR and BEST_MODEL (`.joblib`) are described by the METADATA file (best model, "
     "model names, 37 feature names, alpha, class counts, dataset source), and the EVALUATION_RESULTS file holds the mean and standard deviation of every metric for each model. Requests and results are transient; the "
     "`STATE` dictionary holds the loaded files while the server runs."),
    ("algo", "Flowchart of the core algorithm", "10_core_algorithm_flowchart.png",
     "Flowchart of the core algorithm: validation, fusion, classification, balanced retrieval and the risk label.",
     "The flowchart follows `POST /predict`. The payload is validated (types, ranges, description at most 2,000 characters, k in the whitelist) and an invalid payload ends in HTTP 422. `ensure_artifacts` loads "
     "or, if files are missing, builds the artefacts. The typed row with the log of the funding is transformed into the structured vector; an empty description is replaced by \"<industry> startup\"; the text is "
     "embedded and fused with alpha = 0.5 into a unit-length 421-value vector. The model gives the probabilities; the outcome is the arg-max and the confidence the maximum. `retrieve_similar` picks k//2 SUCCESS and "
     "k - k//2 FAILURE rows by cosine similarity (a shortfall is filled from the nearest remaining rows) and the explanation is built from the top five model weights and the retrieval statistics. Finally the risk label "
     "is \"Lower risk\" if the outcome is SUCCESS with confidence at least 0.70, \"Moderate risk\" if the confidence is at least 0.55, and \"Higher uncertainty\" otherwise, and the JSON response is returned."),
    ("eval", "Evaluation protocol", "11_evaluation_protocol.png",
     "Evaluation protocol: (A) the study that selects the shipped model and (B) the studies on the real public table.",
     "Part A is `run_evaluation` on the shipped table. The 1,400-row startup table is prepared, all descriptions are embedded once, and five stratified 80/20 splits (seed 42) are drawn. In each split the "
     "preprocessor is fitted on the training part only and the blocks are fused; four models are fitted; logistic regression is fitted on structured, text and combined vectors; and the similarity-weighted vote is "
     "scored for k = 10 to 50. The test metrics (accuracy, balanced accuracy, precision, recall, F1 and the confusion matrix) are averaged over the five splits, the model with the highest balanced accuracy is "
     "refitted on all rows and the artefacts and the evaluation file are saved. Part B repeats the protocol with `scripts/run_experiments.py` and `scripts/extra_experiments.py` on the real table (923 rows, 922 after "
     "de-duplication, structured columns only, no text): five models with ROC-AUC and PR-AUC, imbalance, threshold, calibration, forest-size, 70:30 and synthetic-to-real studies, the leakage ablation, the "
     "retrieval-only classifier and the per-industry accuracy."),
]
_DG = {k: (t, f, c, x) for k, t, f, c, x in DIAGRAMS}


def _fig(key, width=5.6):
    t, f, c, x = _DG[key]
    return FIG(F.diag(f), c, width)


def blocks():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes how VenturePulse is organised: its design goals, architecture, data flow, main classes, stored data, core algorithm, modules and user interface. "
          "Every diagram was drawn from the real code (`app/`, `scripts/` and `frontend/src/`) and reads the way the program runs."),

        H2("5.1 Design Goals"),
        B("**One fitted preprocessor, one model, one set of training vectors.** They are created together and stored together, so training and prediction cannot disagree.",
          "**A prediction plus its evidence.** Every result carries the probability of both outcomes, the features that drove the model and the comparable historical startups, so that the number is never shown alone.",
          "**Leakage-safe retrieval.** The comparable startups are searched among training rows only, the company name is masked in descriptions, and the evaluation fits every transformation on the training part of each split.",
          "**Runs on a student laptop.** CPU only, open-source packages, no external prediction service and no API key; everything stays on localhost.",
          "**Measured, not promised.** The performance and insights screens read the numbers from the stored evaluation files and the loaded training table, so the screens cannot show a figure that was not computed."),

        H2("5.2 System Architecture"),
        _fig("arch", 5.4),
        P("There are three tiers over two stores. The **presentation tier** is a React 18 application (Vite 6, Tailwind CSS 4, Recharts, port 5410) with six screens: the landing page, the sign-in and the four "
          "application screens under `/app`. The Vite server proxies `/api` and `/predict` to the backend, so the browser talks to one origin. The **application tier** is a FastAPI service on port 8410: `app/main.py` "
          "(209 lines) holds the original routes and the validation model, `app/api_extra.py` (160 lines) adds the read-only routes and the demo sign-in for the React screens, and three services keep the routes thin. "
          "The **domain tier** in `app/ml/` has six modules (dataset, preprocessing, embeddings, retrieval, models and evaluation). The **two stores** are the `models/` folder and the startup CSV or synthetic "
          "fallback; no SQL database is used. The original Jinja pages (`/dashboard`, `/predict`, `/performance`, `/insights`) are served by the same backend and use the same services, so the two front ends show the same numbers."),

        H2("5.3 High-Level Workflow"),
        _fig("flow", 5.4),
        P("The offline path prepares the data, compares four classifiers over five repeated splits, selects the best by balanced accuracy and stores the artefacts; it runs automatically on the first start if "
          "any artefact is missing. The online path applies the stored objects to one submitted startup. Both paths use the same fusion function, so a submitted startup is represented exactly like a training row. "
          f"On the development machine one prediction takes a median of {_P10['median_ms']:.0f} ms at k = 10 and {_PK['median_ms']:.0f} ms at k = 50 (measured through HTTP on 127.0.0.1)."),

        H2("5.4 Data Flow Diagrams"),
        _fig("dfd0", 4.8),
        P("**Level 0.** The founder or investor sends credentials and a startup profile and receives an outcome estimate with evidence; the model owner sends a train and evaluate request and receives the "
          "evaluation results and the saved artefacts; the startup table supplies the records."),
        _fig("dfd1", 5.0),
        P("**Level 1.** Five processes: 1.0 Validate input, 2.0 Predict outcome, 3.0 Retrieve and explain, 4.0 Serve metrics and insights and 5.0 Train. The stores are D1 (model, preprocessor and metadata), D2 (fused "
          "training matrix and training table), D3 (evaluation results) and D4 (the startup CSV). Process 5.0 is the only one that writes D1, D2 and D3; the others only read them."),
        _fig("dfd2", 5.2),
        P("**Level 2.** Process 2.0 follows `predict_one` through five steps: build the input row (2.1), transform the structured values (2.2), embed the description (2.3), fuse (2.4) and classify (2.5). "
          "Process 3.0 has three: retrieve the comparable startups (3.1), build the explanation (3.2) and add the risk label and the JSON response (3.3). Steps 2.5 and 3.1 both use the fused vector and are independent of each other."),

        H2("5.5 UML Diagrams"),
        _fig("uml", 5.4),
        P("**Class diagram.** `PredictPayload` validates the input. The `Store` module owns the loaded artefacts in `STATE`; `Predictor` converts a payload into a result using `Preprocessing`, `Embeddings` and `Retrieval` and the best "
          "model; `Evaluation + Models` is the only code that fits and saves models; `Dataset + Insights` loads or generates the table and summarises it. The model objects themselves are standard scikit-learn and XGBoost classes."),
        _fig("seq", 5.2),
        P(f"**Sequence: one prediction.** The page posts the payload, FastAPI validates it, the predictor builds the row, transforms, embeds, fuses and classifies, retrieval picks the comparable startups, and the explanation is built "
          f"from the model weights. The measured end-to-end time is a median of {_PK['median_ms']:.0f} ms at k = 50 (95th percentile {_PK['p95_ms']:.0f} ms, maximum {_PK['max_ms']:.0f} ms over {_PK['n']} requests)."),
        _fig("uc", 4.8),
        P("**Use cases.** After signing in, the founder or investor views the dashboard and analyses a startup (which includes validation, the comparable startups and the key features), and opens the model performance and "
          "insights screens. The model owner trains and evaluates the models from the scripts. The product has one demo account and no role model."),

        H2("5.6 Data Design"),
        _fig("er", 5.4),
        P("The product has no SQL database because it keeps no per-user records; the diagram shows the file-based data model. The startup table, the fused matrix and the embeddings are aligned row by row; "
          "the preprocessor and the model are fitted from them; the metadata and evaluation files describe them; requests and results are transient."),
        TAB("Stored artefacts", ["Artefact", "Location", "Content"], [
            ["Historical table", "`models/train_frame.pkl`", f"{F.SYN_ROWS:,} rows x 23 columns (inputs, description, status, label, outcome, log funding)"],
            ["Fused training vectors", "`models/train_fused.npz`", f"{F.SYN_ROWS:,} x 421 float32 (37 structured + 384 text values), unit length"],
            ["Text embeddings", "`models/text_embeddings.npz`", f"{F.SYN_ROWS:,} x 384 MiniLM vectors"],
            ["Preprocessor", "`models/preprocessor.joblib`", "ColumnTransformer: median imputer + scaler, most-frequent imputer, one-hot encoder"],
            ["Best model", "`models/best_model.joblib`", "Logistic Regression (selected by balanced accuracy)"],
            ["Metadata", "`models/metadata.json`", "best model, feature names, alpha, embedding backend, class counts, dataset source and the synthetic-fallback flag"],
            ["Evaluation results", "`evaluation/evaluation_results.json`", "mean and standard deviation of five metrics for each model, representation study, retrieval-k study"],
            ["Real-data results", "`evaluation/real_results.json`, `extra_results.json`", "Studies on the 922-row public table (Chapter 8)"],
        ], widths=[1.5, 2.1, 2.7], size=9.5, align=["l", "l", "l"]),
        P("The shipped artefacts were produced from the synthetic fallback table (`data/raw/SYNTHETIC_FALLBACK.txt` and the `synthetic_fallback` flag in the metadata say so). If a CSV of the public table is placed in "
          "`data/raw/` and the artefacts are deleted, the next start retrains on it without a code change. The description column of the historical table is the only free text; company names matching a simple "
          "pattern are replaced by \"this company\" and the text is cut at 2,000 characters."),

        H2("5.7 Algorithm Design"),
        _fig("algo", 4.6),
        P("**Fused representation.** The structured vector s is the output of the preprocessor (nine numeric fields and the log of funding scaled, seven flags, and ten state and ten industry indicator columns, 37 values). The "
          "text vector t is the 384-value MiniLM embedding of the description. Both are scaled to unit length, so each block has the same norm; the fused vector is [alpha s, (1 - alpha) t] with alpha = 0.5, scaled to unit length "
          "again, which makes cosine similarity equal to a dot product."),
        P("**Classification.** The model compared in the application are Logistic Regression, Decision Tree, Random Forest and XGBoost, all with class balancing. The best one by mean balanced accuracy serves the predictions; "
          "the outcome is the class with the larger probability, which for two classes means a threshold of 0.5 on P(success)."),
        P("**Balanced retrieval.** The training vectors are sorted by cosine similarity to the fused vector of the submitted startup. The first k//2 successes and k - k//2 failures are kept, so the evidence shown is "
          "half and half even when the table is imbalanced; if one class has too few rows the quota is filled from the remaining nearest rows. The displayed list is sorted by similarity. Search uses training rows only."),
        P("**Explanation and risk label.** For a linear model the five features with the largest absolute coefficients are listed with the scaled value and the sign of coefficient x value (supports SUCCESS or supports FAILURE); "
          "for a tree model the five largest importances are listed. Two lines summarise the retrieval (the class counts and the top similarity, and the mean similarity to each class). The risk label is "
          "\"Lower risk\" if the outcome is SUCCESS with confidence at least 0.70, \"Moderate risk\" if the confidence is at least 0.55, and \"Higher uncertainty\" otherwise."),
        _fig("eval", 5.4),
        P("**Evaluation.** The protocol of the figure is applied to every model and every representation, and the real-data studies of Chapter 8 repeat it on the public table with extra models, "
          "imbalance strategies and a threshold sweep."),

        H2("5.8 Module Design"),
        TAB("Modules and their responsibilities", ["Module", "Lines", "Main contents"], [
            ["`app/main.py`", "209", "FastAPI app, `PredictPayload` with range and k validators, `/api/health`, `/api/model-metrics`, `/api/insights`, `POST /predict`, the Jinja pages and `/predict-form`"],
            ["`app/api_extra.py`", "160", "`/api/config`, `/api/feature-importance`, `/api/auth/login`, `/api/auth/me`, token functions, field ranges"],
            ["`app/services/store.py`", "41", "`ensure_artifacts`: load artefacts into `STATE`; train first if a file is missing"],
            ["`app/services/predictor.py`", "117", "`build_input_row`, `predict_one`: embedding, fusion, classification, retrieval, explanation, risk label"],
            ["`app/services/insights.py`", "31", "`compute_insights`: counts, success rate by industry and state, median funding, correlations"],
            ["`app/ml/dataset.py`", "237", "Local CSV / Kaggle loader, `generate_synthetic`, target mapping, `clean_text`, `load_dataset`"],
            ["`app/ml/preprocessing.py`", "75", "`prepare_frame` (dedup, target, coercion, log funding), `build_preprocessor`, `feature_names`"],
            ["`app/ml/embeddings.py`", "70", "MiniLM loader and `embed_texts`, deterministic hashing fallback, `l2norm`"],
            ["`app/ml/retrieval.py`", "55", "`fuse`, `retrieve_similar` (balanced cosine top-k)"],
            ["`app/ml/models.py`", "27", "`get_models`: four classifiers with their hyper-parameters"],
            ["`app/ml/evaluation.py`", "273", "`run_evaluation`: 5 x 80/20 study, representation and retrieval-k studies, refit, charts, JSON"],
            ["`app/templates/`", "143", "Six Jinja templates (base, dashboard, predict, result, performance, insights)"],
            ["`frontend/src/`", "3,045", "Pages (923 lines), components (UI kit, charts), API client, auth, theme and activity log"],
            ["`scripts/`", "612", "`run_experiments.py`, `extra_experiments.py`, `edge_tests.py`, `smoke_test.py`, `measure_latency.py`, `train.py`"],
        ], widths=[1.9, 0.6, 3.8], size=9.5, align=["l", "c", "l"]),
        P("The services cache everything in `STATE`, so the artefacts are read from disk once per process. Server state in the React application is handled by a small `useApi` hook with an error-description "
          "helper that turns a failed request into a message and a hint (for example, a 422 asks the user to correct the highlighted values)."),

        H2("5.9 User Interface Design"),
        P("The interface follows a dark, monospace-accented layout with a light theme that can be switched and is remembered in the browser. The application screens share one shell: a sidebar with the four screens "
          "and their keyboard shortcuts, a top bar with a screen-jump search box (press `/`) and the theme toggle, and a card showing the serving model and the number of historical startups. Colour is never "
          "the only signal: each outcome has a label and each probability bar has its value written next to it; every form field has a label and an error message."),
        TAB("Screens", ["Route", "Screen", "Main elements"], [
            ["/", "Landing", "Hero, technology strip, how it works, feature overview, link to the demo sign-in"],
            ["/login", "Sign in", "Email and password, a button that fills the demo account, error message on a wrong password"],
            ["/app", "Dashboard", "Four statistic cards, best validated model, class distribution donut, model comparison bars, how it works, pipeline configuration"],
            ["/app/analyze", "Analyze a startup", "Cards for funding and traction, company profile (industry, state, k), investor signals, description (2,000 characters); result with outcome, probability bars, explanation, evidence donut, comparable startups table, submitted inputs"],
            ["/app/performance", "Model performance", "Comparison table (mean and standard deviation), balanced accuracy and F1 bars, precision against recall, confusion matrix, retrieval-size and representation studies, feature importance"],
            ["/app/insights", "Startup insights", "Success rate by industry and state, industry table, median funding by outcome, correlation of five fields with SUCCESS"],
        ], widths=[1.1, 1.3, 3.9], size=9.5, align=["l", "l", "l"]),
        PAIR([(F.shot("03_login.png"), "Sign-in screen with the demo account."),
              (F.shot("06_analyze_form_filled.png"), "Analyze screen with a submitted example filled in.")], 2.9),
        P("The original server-rendered pages show the same four views without a sign-in and are kept so that the backend remains usable on its own. Their prediction form insists on a description (status 400 "
          "if it is empty), whereas the JSON route `POST /predict` accepts an empty description and embeds the industry name instead. The results of every screen are shown and discussed in Chapter 8."),

        H2("5.10 Design Decisions and Their Consequences"),
        TAB("Design decisions", ["Decision", "Reason", "Consequence"], [
            ["Fuse structured and text vectors by concatenation with weight 0.5", "Gives one vector for classification and retrieval; no extra training", "Both blocks count equally whatever their usefulness; alpha was fixed, not tuned"],
            ["Balanced retrieval quota", "Shows evidence for both outcomes even when the table is imbalanced", "The displayed counts are always about k/2 each, so they do not show the real class ratio"],
            ["Logistic Regression as served model", "Highest balanced accuracy on the shipped (synthetic) table; transparent coefficients", "On the real table Random Forest and XGBoost score higher (Chapter 8); the served model was chosen on synthetic data"],
            ["Search training rows only", "No test row can retrieve itself", "A new startup cannot be compared with startups added after training until the artefacts are rebuilt"],
            ["Artefacts as files, no database", "Simple local deployment; nothing to administer", "No audit trail, no per-user history; one process holds the state"],
            ["Deterministic explanation", "Same input gives the same text; no sampling", "Coefficient-based reasons describe the model, not causes in the real world"],
            ["Synthetic fallback when the public CSV is absent", "The application always starts", f"Shipped statistics come from {F.SYN_ROWS:,} generated rows and must not be read as real performance"],
            ["Hash-based embedding fallback", "The application still runs if the transformer cannot be loaded", "Retrieval quality would drop; the backend name is returned in every result"],
            ["Demo token in a header", "Lets the React screens demonstrate a sign-in", "Not a security boundary: one shared account, and the prediction route itself needs no token"],
        ], widths=[1.9, 2.1, 2.3], size=9, align=["l", "l", "l"]),
        P("The design favours a system that can be run, inspected and measured over a large one. The cost shows in the missing founder and team-experience inputs, the single demo account and the fixed fusion weight; "
          "these are listed with the other limits in Chapters 9 and 10."),
    ]
