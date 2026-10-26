"""Index of the TrendCast design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs/make_diagrams.py into docs/diagrams/ (matplotlib, 150 dpi).
Used by the block-diagram document (11), the full report, the decks and the paper.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Layered architecture of TrendCast: React console, Vite proxy, FastAPI application with 22 routes, the src/ pipeline modules, and in-memory state plus joblib model files.",
     "The presentation tier is the React console on port 5317 with thirteen pages; the Vite development server proxies every /api request to the FastAPI application on port 8317. "
     "The application exposes 22 routes and keeps one process-wide pipeline state, a dictionary guarded by a re-entrant lock, in the same way the original Streamlit page used its session state. "
     "Each route calls the same functions of the src/ package (loading, preprocessing, daily demand, feature engineering, baselines, XGBoost, domain adaptation, evaluation). "
     "Nothing is stored in a database: uploaded tables, features and results live in memory, and only the trained models are written to models/ as joblib files. "
     "The optional AI Insights route sends aggregated numbers (never raw rows) to the Gemini REST service using the key in .env. The original Streamlit application (app.py) remains as a separate front end over the same src/ package."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "End-to-end workflow: upload, clean and merge, daily demand, features, chronological split, baseline and XGBoost, domain adaptation, evaluation, forecast and optional AI explanation.",
     "A user uploads the transactions and articles files (customers optional). The data are validated, cleaned, merged and aggregated to units sold per article per day, with missing days filled by zero. "
     "Calendar, lag, rolling and encoded attribute features are added, the table is split by date, and a moving-average baseline and an XGBoost model are trained and compared. "
     "Domain adaptation then trains on a source domain and tests on a target domain with and without importance weights. The evaluation page shows the comparison and the feature importance, the forecast page rolls the model forward 7, 14 or 30 days, "
     "and the AI Insights page can explain the numbers in plain language. Every step is gated: a later page refuses to run until the earlier step has produced its output."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0): TrendCast as one process with the analyst, the dataset provider and the optional Gemini service.",
     "At level 0 the whole product is a single process. The analyst sends the transaction, article and customer files, a row limit, a training fraction, tuning and domain choices and a forecast request, and receives the data-quality report, "
     "exploration charts, model metrics, the domain-shift report, feature importance and forecasts. The dataset provider (the H&M competition files) supplies the three CSV tables. "
     "The Gemini service receives an aggregated summary and a question and returns an explanation; it is optional and the rest of the product works without it."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1: seven processes (ingest, aggregate, features, train, adapt, evaluate and forecast, explain) and the data stores.",
     "Level 1 splits the product into seven processes. Process 1.0 validates, cleans and merges the uploaded tables into the merged transactions store (D1). Process 2.0 aggregates them into the daily demand table (D2). "
     "Process 3.0 builds the feature table (D3). Process 4.0 splits by date and trains the moving average and XGBoost models, saving the model to D5. Process 5.0 trains the domain classifier and the weighted model on a chosen source and target. "
     "Process 6.0 computes metrics, importance and recursive forecasts from D3 and D5. Process 7.0 builds the aggregated context for the Gemini explanation. The results store (D4) holds the metric dictionaries shown on the evaluation page."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2: the domain-adaptation process 5.0 expanded into six sub-processes.",
     "Process 5.1 splits the feature table into source and target rows by the chosen column and values, and holds out the later half of the target dates as the test set. Process 5.2 trains XGBoost on source rows only and scores the held-out target rows, giving the before-adaptation metrics. "
     "Process 5.3 trains a logistic-regression domain classifier to tell source from target rows (the domain column is excluded from its inputs) and reports its accuracy and the per-feature shift table. "
     "Process 5.4 turns the classifier probabilities into importance weights p/(1-p) clipped at 20. Process 5.5 retrains XGBoost on the source rows with those weights, and process 5.6 scores it on the same target test rows and builds the before-and-after report."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram: the FastAPI application, request models, the shared state, and the src/ modules with their main functions.",
     "TrendCast is written mostly as functions grouped in modules, so the diagram shows each module as a class-like box with its main operations. The FastAPI application owns four request models (TrainRequest, DomainRequest, ForecastRequest, AskRequest) "
     "and the shared state S with its lock; it calls preprocessing, demand_forecasting, feature_engineering, baseline_models, xgboost_model, domain_adaptation and evaluation. "
     "domain_adaptation uses xgboost_model.train_xgboost with a sample_weight argument, which is the only place the two modules meet. gemini_api builds its prompt with src.gemini_helper and reads the key through state.env."),
    ("seq", "Sequence diagram of the main flow", "07_sequence_flow.png",
     "Sequence diagram: running domain adaptation from the browser, from the click to the before-and-after report.",
     "The browser posts the domain column, source and target to /api/domain/run. FastAPI takes the lock, checks that the feature table exists and that the two values differ, and splits the domains. "
     "It trains the source XGBoost model, scores the target test rows, trains the logistic domain classifier, computes the shift table and the clipped weights, trains the weighted model, scores it, saves the adapted model to models/ and returns the report. "
     "The React page then draws the shift histogram, the box plot and the before-and-after cards. The same pattern, with different calls, applies to training and forecasting."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use-case diagram with the analyst, the optional Gemini service and the developer or evaluator.",
     "The analyst can upload data, explore it, view the aggregated demand table, build features, train the baseline and XGBoost (with optional tuning), run domain adaptation, review the evaluation, generate a 7, 14 or 30-day forecast and ask for an AI explanation. "
     "Training includes building features, and domain adaptation includes training the source model. The AI explanation extends the evaluation and needs the external Gemini service. "
     "The developer or evaluator runs the experiment scripts, the tests and the screenshot scripts, which import the same src/ package. There is no sign-in: the product is a single-user tool."),
    ("er", "Entity-relationship diagram (logical)", "09_er_diagram.png",
     "Logical entity-relationship diagram: TrendCast has no database; the entities are the uploaded tables, derived tables and model files.",
     "A transaction row refers to one article and one customer; an article has many transactions. Aggregating transactions by date and article gives one daily-demand row, and each daily-demand row becomes one feature row. "
     "A training run produces one model file (and a feature-information file), and a domain run produces one adapted model and one result record that compares it with the source model. "
     "A forecast is a set of dated rows for one article. No foreign keys exist: the relations are columns shared by pandas tables in one process, which is why the diagram is logical. Only the model files survive a restart."),
    ("flow_algo", "Core algorithm flowchart: training and forecasting", "10_flowchart_algorithm.png",
     "Flowchart of the core algorithm: from raw transactions to the recursive forecast, with the leakage guards marked.",
     "Raw rows are cleaned (dates parsed, null ids, non-positive prices and exact duplicates removed), merged and counted per article per day. Missing days between an article's first and last sale are filled with zero. "
     "Lag and rolling features are computed from values shifted by one day so the current day never enters its own features. The table is split at the date that leaves 80 percent of the dates for training, the models are fitted and scored on the later 20 percent, "
     "and the saved model forecasts ahead recursively: each predicted day is appended to the history that produces the next day's lag and rolling features."),
    ("flow_da", "Domain-adaptation flowchart", "11_flowchart_domain_adaptation.png",
     "Flowchart of importance-weighted domain adaptation as implemented in domain_adaptation.py and the /api/domain/run route.",
     "After the source and target rows are separated and the later half of the target dates is held out for testing, a source-only XGBoost model gives the before-adaptation metrics. "
     "A logistic regression then separates source from target rows using the same features without the domain column; its probability p for each source row becomes the weight p/(1-p), clipped at 20. "
     "XGBoost is retrained on the source rows with those weights and scored on the same held-out target rows. The after-versus-before change is reported as it is, whether positive or negative."),
    ("model", "Model and feature architecture", "12_model_architecture.png",
     "Model architecture: 31 input features in four groups feeding one XGBoost regressor, with the baselines and the weighted variant.",
     "The model input has 31 columns in four groups: price and sales channel, six label-encoded product attributes, fourteen calendar features (including sine and cosine encodings of month and weekday) and nine lag and rolling features. "
     "One XGBoost regressor of 300 trees and depth 8 (or the tuned variant) predicts units sold for the article-day. The moving average is the baseline inside the product; the weighted variant adds only a per-row sample weight from the domain classifier."),
]
