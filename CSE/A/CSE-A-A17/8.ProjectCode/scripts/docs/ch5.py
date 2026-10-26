"""Chapter 5: System Design for TrendCast.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
Line counts are measured from the code at build time; diagrams are drawn by make_diagrams.py.
"""

import os

from . import facts as F
from .blocks import B, EQ, FIG, H1, H2, H3, N, P, TAB
from .diagram_index import DIAGRAMS
from .refs import N as cite

_D = {k: (t, f, cap, txt) for k, t, f, cap, txt in DIAGRAMS}


def _lines(rel):
    path = os.path.join(F.CODE, rel)
    with open(path, encoding="utf-8", errors="ignore") as fh:
        return sum(1 for _ in fh)


def _tree_lines(rel, exts):
    total = 0
    for root, _, files in os.walk(os.path.join(F.CODE, rel)):
        for f in files:
            if f.endswith(exts):
                with open(os.path.join(root, f), encoding="utf-8", errors="ignore") as fh:
                    total += sum(1 for _ in fh)
    return total


def _dg(key, width=5.4):
    """Diagram figure block, or nothing if the file has not been drawn yet."""
    t, f, cap, _ = _D[key]
    path = F.diag(f)
    return [FIG(path, cap, width)] if os.path.exists(path) else []


_DROP_P = ("The deliberate gaps", "The console shows the stage reached", "Three decisions about this structure", "`POST /api/data/upload` is the only multipart",
           "Four design rules", "Every design has costs", "Two further choices", "The analyst is the only human actor", "Three files persist",
           "The domain-adaptation flowchart shows", "The model itself is a single regressor", "TrendCast has no database. Section 5.1")
_DROP_TAB = ("Principal modules and the data", "The shared pipeline state", "Console pages and the endpoints", "Principal design decisions")


def _trim(out):
    """Report variant: same 12 diagrams, but no design screenshots (Chapter 8 shows the screens), fewer tables and shorter prose."""
    res, skip_h2 = [], False
    for b in out:
        if b[0] == "h2":
            skip_h2 = b[1].startswith("5.10")
            if skip_h2:
                continue
        if skip_h2:
            continue
        if b[0] == "p" and b[1].startswith(_DROP_P):
            continue
        if b[0] == "tab" and b[1].startswith(_DROP_TAB):
            continue
        if b[0] == "fig" and os.sep + "screenshots" + os.sep in b[1]:
            continue
        if b[0] == "tab" and b[1].startswith("The 22 routes"):
            b = ("tab", b[1], b[2][:3], [r[:3] for r in b[3]], [0.6, 1.7, 4.2], ["c", "l", "l"], 8.5)
        res.append(b)
    return res


def blocks():
    a, w = F.API_PORT, F.WEB_PORT
    shot = lambda n, cap, base=5.0, mh=3.6: [FIG(F.shot(n), cap, F.shot_w(F.shot(n), base, mh))] if os.path.exists(F.shot(n)) else []  # noqa: E731
    mods = [
        ("`src/data_loader.py`", "src/data_loader.py", "Required-column lists and the friendly `DataValidationError`; Streamlit upload helpers (the API reuses only the validators)"),
        ("`src/preprocessing.py`", "src/preprocessing.py", "Clean transactions, articles and customers; left-join; data-quality report"),
        ("`src/demand_forecasting.py`", "src/demand_forecasting.py", "Aggregate to units per article per day; zero-fill the missing days"),
        ("`src/feature_engineering.py`", "src/feature_engineering.py", "Calendar, cyclical, lag and rolling features; label encoding; feature-column selection"),
        ("`src/baseline_models.py`", "src/baseline_models.py", "Chronological split, moving average, random forest, LightGBM"),
        ("`src/xgboost_model.py`", "src/xgboost_model.py", "XGBoost with optional sample weights; TimeSeriesSplit random search; importance"),
        ("`src/domain_adaptation.py`", "src/domain_adaptation.py", "Domain split, logistic domain classifier, importance weights, shift table, weighted model"),
        ("`src/evaluation.py`", "src/evaluation.py", "RMSE, MAE, safe MAPE, R2, comparison table, before-and-after report"),
        ("`src/visualization.py`", "src/visualization.py", "Plotly figures for the Streamlit app"),
        ("`src/gemini_helper.py`", "src/gemini_helper.py", "Builds the aggregated, raw-data-free context for AI Insights"),
        ("`backend/main.py`", "backend/main.py", "FastAPI application: 22 routes, request models, gating helpers"),
        ("`backend/state.py`", "backend/state.py", "Shared pipeline state `S`, lock, model paths, `.env` reader, JSON cleaner"),
        ("`backend/gemini_api.py`", "backend/gemini_api.py", "REST call to Gemini with the key and model from `.env`"),
        ("`app.py`", "app.py", "Original Streamlit application, 11 pages (kept unchanged)"),
    ]
    mod_rows = [[n, str(_lines(rel)), d] for n, rel, d in mods]
    fe_lines, test_lines = _tree_lines("frontend/src", (".jsx", ".js", ".css")), _tree_lines("tests", (".py",))
    mod_rows.append(["`frontend/src/`", f"{fe_lines:,}", "React 19 console: 13 pages, UI kit, charts, API client and pipeline-progress context"])
    mod_rows.append(["`tests/`", str(test_lines), f"{F.PYTEST_TOTAL} pytest tests ({F.PYTEST_UNIT} unit, {F.PYTEST_API} API)"])

    routes = [
        ["GET", "/api/health", "Liveness check", "-"],
        ["GET", "/api/state", "Nine progress flags (data_loaded, daily_ready, features_ready, baseline_ran, xgboost_trained, domain_done, forecast_done, saved_model_exists, gemini_configured)", "-"],
        ["POST", "/api/data/upload", "Multipart transactions, articles, optional customers and a row limit; cleans, merges, resets everything downstream; returns the quality report", "400 missing column / empty / unreadable file"],
        ["GET", "/api/data/report", "The last data-quality report", "409 before upload"],
        ["GET", "/api/explore", "Daily, monthly, weekly series, top-10 products, department, colour and channel totals, price histogram", "409"],
        ["GET", "/api/demand/table", "First `limit` rows (1-2,000) of the daily demand table", "409"],
        ["POST", "/api/features/build", "Zero-fill, build the 31-input feature table, clear models and results", "409"],
        ["GET", "/api/features", "Shape, feature columns and the first 50 rows", "409"],
        ["GET", "/api/training/split", "Date ranges and row counts for a training fraction", "400 if outside 0.5-0.95 or a side is empty; 409"],
        ["POST", "/api/training/baseline", "Moving-average baseline on the chronological split", "422 bad fraction; 409"],
        ["POST", "/api/training/xgboost", "Default or tuned XGBoost; saves the model and feature list", "422; 409"],
        ["POST", "/api/training/load", "Loads the saved model from `models/`", "404 if none saved"],
        ["GET", "/api/training/results", "Model comparison rows", "-"],
        ["GET", "/api/domain/options", "Offered domain columns (channel, product group, department) and their values", "409"],
        ["POST", "/api/domain/run", "Source model, domain classifier, shift table, weights, adapted model, before/after report", "400 same values, bad column, empty domain; 409"],
        ["GET", "/api/domain/last", "Most recent domain run, so the page survives a reload", "-"],
        ["GET", "/api/evaluation", "Comparison table, domain report, top-20 gain importance", "-"],
        ["GET", "/api/forecast/articles", "Article ids with product type and total units", "409 until a model is trained"],
        ["POST", "/api/forecast", "Recursive 7, 14 or 30-day forecast for one article with 60 days of history", "400 horizon or < 5 days of history; 409"],
        ["GET", "/api/ai/status", "Whether a Gemini key is configured and the model name", "-"],
        ["POST", "/api/ai/explain", "Plain-language answer built from aggregated metrics, importance and domain-shift numbers", "503 not configured; 502 service error"],
        ["POST", "/api/ai/forecast-summary", "Two-to-three-sentence summary of the latest forecast", "409; 503; 502"],
    ]

    out = [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes how TrendCast is put together: the architecture and workflow, the data flow, the UML and data design, the modules, the API and the user interface. "
          "The diagrams were drawn from the code in `src/` and `backend/`; the complete set, each with a longer explanation, is also in the Block Diagrams document. "
          "A note on scope: the product is a single-user analysis tool. It has no accounts, no database and no scheduler, and these absences are design choices that the sections below explain rather than hide."),

        H2("5.1 Design goals and architecture"),
        P("Five goals shaped the design. First, **every number on screen must be computed from the uploaded files**: nothing is hard-coded, and the project guide can upload a different slice of the H&M data and see different results. "
          "Second, **no data leakage**: lag and rolling features are shifted by one day, the train and test sets are split by date, and hyperparameters are tuned with time-ordered folds. "
          "Third, **honest evaluation**: every error is reported as measured, including negative improvements. Fourth, **gating**: a page that needs an earlier step refuses to run and says which step is missing. "
          "Fifth, **a thin web layer**: the machine-learning code stays in the `src/` package and is shared by the original Streamlit pages and the new web console, so the two cannot disagree."),
        *_dg("arch", 5.6),
        P(f"The React 19 console on port {w} reaches the FastAPI application on 127.0.0.1:{a} through the Vite development proxy, so the browser sees one origin. "
          "The application exposes 22 routes. It keeps a single process-wide dictionary of pipeline state, guarded by a re-entrant lock, in the way the Streamlit pages used `st.session_state`. "
          "Each route calls the same functions as the corresponding Streamlit page; only the HTTP and JSON handling is new. "
          "The two `src/` modules that import Streamlit (`data_loader`, `gemini_helper`) are used for their validators and context builder only, and the backend lowers the Streamlit logger to avoid its no-runtime warnings."),
        P("The deliberate gaps in this architecture are worth stating. There is no authentication because the tool runs on one machine for one analyst; the CORS list therefore allows only `localhost:5317` and `127.0.0.1:5317`. "
          "There is no database because the data are re-uploaded for each analysis and the pipeline takes seconds, not hours (Chapter 7 lists the measured stage times); only the trained models are persisted. "
          "State is shared by every browser tab, so two analysts on one server would overwrite each other; this is acceptable for a demonstration and is listed as a limitation in Chapter 9."),

        H2("5.2 High-level workflow"),
        *_dg("flow", 5.6),
        P("The workflow has eight stages and every stage maps to one page of the console. **Upload** reads the files and returns the quality report. **Explore** and **Demand** show the aggregated series. "
          "**Features** builds the 31-input table. **Training** splits by date, fits the moving average and XGBoost and keeps the comparison. **Domain** trains on a source and tests on a target, with and without weights. "
          "**Evaluation** collects the comparison, the before-and-after table and the feature importance. **Forecast** rolls a chosen article forward. **Insights** asks Gemini to explain what is already on screen."),
        P("The console shows the stage reached through the nine flags of `/api/state`. A small provider component reads that route at start-up and again after each action, and every page wraps its content in a gate: if the flag it needs is false it shows the missing step with a link instead of calling an endpoint that would answer 409. "
          "This keeps the browser console free of expected errors and means a page reload restores the progress indicators from the server rather than from browser storage."),

        H2("5.3 Data flow diagrams"),
        H3("5.3.1 Level 0: context"),
        *_dg("dfd0", 4.8),
        P("At level 0 TrendCast is one process with three external entities. The **analyst** supplies files and choices and receives reports, charts, metrics and forecasts. The **dataset provider** is the source of the three CSV tables, "
          "which in this project are the public H&M competition files. The **Gemini service** is optional and receives only an aggregated JSON summary and a question. "
          "Drawing the dataset provider and the analyst separately is deliberate: the product never downloads data, so every dataset arrives through the analyst's upload."),
        H3("5.3.2 Level 1: seven processes"),
        *_dg("dfd1", 5.4),
        P("Level 1 shows the seven processes and four data stores. **1.0 Ingest** validates the columns and writes the cleaned and merged tables (D1). **2.0 Aggregate** writes the daily demand table (D2). "
          "**3.0 Build features** writes the feature table (D3) and the category-code mappings. **4.0 Train** reads D3 and writes the models (D5, joblib files). **5.0 Adapt** reads D3 and writes the adapted model and the domain result. "
          "**6.0 Evaluate and forecast** reads D3, D5 and the results store (D4). **7.0 Explain** builds the aggregated context and calls Gemini. All stores except D5 are memory structures and are lost when the server stops."),
        H3("5.3.3 Level 2: domain adaptation"),
        *_dg("dfd2", 5.4),
        P("Domain adaptation is the part of the product the project title names, so it is expanded to level 2. Six sub-processes take the feature table to a before-and-after report. "
          "Two design points matter. The domain column itself is removed from the model inputs, so neither the source model nor the classifier can read the answer off a feature. "
          "And the held-out target test rows are the later half of the target dates; they are used only to score the two models, never to fit them or the classifier's weights."),

        H2("5.4 UML design"),
        H3("5.4.1 Class diagram"),
        *_dg("uml", 5.6),
        P("The code base is organised as modules of functions rather than as classes, which suits a data pipeline in which each step takes a table and returns a table. "
          "The only classes are the four pydantic request models of the API, which validate input: `TrainRequest` (training fraction between 0.5 and 0.95, tuning flag), `DomainRequest` (column, source, target), `ForecastRequest` (article id, horizon) and `AskRequest` (question). "
          "The diagram draws each module as a class-like box so the dependencies are visible."),
        TAB("Principal modules and the data they pass on.",
            ["Module", "Takes", "Returns"],
            [["preprocessing", "Raw transactions, articles, customers", "Cleaned and merged transactions; quality report"],
             ["demand_forecasting", "Merged transactions", "Daily demand table; zero-filled table"],
             ["feature_engineering", "Zero-filled daily table", "Feature table and category mappings"],
             ["baseline_models / xgboost_model", "Feature table, train fraction, optional weights", "Predictions, models, importance"],
             ["domain_adaptation", "Feature table, domain column and values", "Source and target rows, classifier, weights, shift table, weighted model"],
             ["evaluation", "Actual and predicted demand", "Metric dictionary, comparison and before-and-after tables"]],
            widths=[1.9, 2.2, 2.4], align=["l", "l", "l"], size=9.5),
        H3("5.4.2 Sequence diagram"),
        *_dg("seq", 5.4),
        P("The sequence follows `POST /api/domain/run`. The route takes the lock, checks the prerequisites (409 when the feature table is missing, 400 for an unknown column or equal values) and then runs six steps from the `src/` package. "
          "It stores the result in `S`, writes the adapted model to `models/adapted_xgboost.joblib` and returns a JSON document that the page draws as the shift histogram, the box plot and four before-and-after cards. "
          "Holding the lock for the whole run serialises requests, which is what keeps the shared state consistent; the measured run takes about 3.7 s on the real subset, so the wait is short."),
        H3("5.4.3 Use-case diagram"),
        *_dg("uc", 4.8),
        P("The analyst is the only human actor. Training includes building features and domain adaptation includes training the source model, so those relations are drawn as inclusions. "
          "The AI explanation extends evaluation and depends on the external Gemini service. The developer or evaluator is drawn at the edge because running the experiment, test and screenshot scripts is not part of the product but exercises the same package."),

        H2("5.5 Database and state design"),
        P("TrendCast has no database. Section 5.1 gave the reason; this section records what takes its place so that the design is complete."),
        *_dg("er", 5.4),
        P("The logical entities are the uploaded tables and the tables derived from them. A **transaction** row has the date, customer id, article id, price and sales channel. An **article** carries the product name and eight descriptive attributes (type, group, colour, department, section, garment group, index name and index group name) plus a free-text description. "
          "A **customer** row (optional) has age, club status and a postal code that the pipeline does not use. Aggregating by date and article gives the **daily demand** row: the count of transactions is the demand, the price is the mean of the day and the channel is the most frequent channel of the day. "
          "Each daily row becomes one **feature row**. A training run produces a **model file**, a domain run an **adapted model** and a result record, and a forecast a set of dated rows."),
        TAB("The shared pipeline state `S` (backend/state.py) and what each key holds.",
            ["Key", "Holds", "Reset by"],
            [["transactions_raw, articles_raw, customers_raw", "The cleaned tables (the names say _raw but upload stores the cleaned versions)", "Upload"],
             ["merged, quality_report", "Merged transactions and the data-quality report", "Upload"],
             ["daily_demand", "Aggregated daily demand, built on first use", "Upload"],
             ["feature_table, feature_mappings", "Feature table and integer-to-label maps for the six encoded attributes", "Upload, rebuild"],
             ["train_df, test_df", "The last chronological split", "Rebuild"],
             ["baseline_model, source_model, adapted_model", "Trained XGBoost objects", "Upload, rebuild"],
             ["domain_eval, domain_run", "Before-and-after metrics and the full domain result", "Upload, rebuild"],
             ["results", "Metric dictionaries keyed by model name", "Upload, rebuild"],
             ["last_forecast", "The latest forecast table (read by the AI summary)", "Upload, rebuild"]],
            widths=[2.1, 3.2, 1.2], align=["l", "l", "l"], size=9.5),
        P("Three files persist across restarts: `models/baseline_xgboost.joblib`, `models/adapted_xgboost.joblib` and `models/feature_info.joblib`, which stores the ordered list of feature columns so a loaded model can be used with a rebuilt table. "
          "The `models/` and `data/` folders are git-ignored. A new upload calls `reset_downstream`, so a model trained on old data can never be shown next to new data."),

        H2("5.6 Core algorithm design"),
        *_dg("flow_algo", 5.4),
        P("The core algorithm is a sequence of table transformations with three leakage guards: the shifted lag and rolling features, the date-based split and the `TimeSeriesSplit` folds used when tuning. "
          "It ends in a recursive forecast: each predicted day is appended to the history so that the next day's lag and rolling features can be computed. "
          "A design consequence, documented honestly in Chapter 8, is that errors compound along the horizon. The forecast also reuses the last observed price and sales channel, and refreshes only the calendar features the route updates (year, month, day, weekday, weekend and the sine and cosine encodings)."),
        *_dg("flow_da", 5.2),
        P("The domain-adaptation flowchart shows the procedure of Section 6.8. The design decision to clip the weights at 20 protects the weighted loss from a few extreme rows. The decision not to rescale the weights to a mean of one is simple to state and turned out to matter; Chapter 8 reports what happened when the two domains were perfectly separable. "
          f"The idea follows covariate-shift correction by importance weighting {cite('shim', 'bickel')}, with the logistic classifier standing in for a direct density-ratio estimate."),
        *_dg("model", 5.4),
        P("The model itself is a single regressor. The 31 inputs fall into four groups (price and channel, six encoded attributes, fourteen calendar features, nine lag and rolling features), and the weighted variant differs only in the per-row sample weights passed to `fit`. "
          "Keeping the adapted model identical in structure to the source model is intentional: any difference in the results can then be attributed to the weights."),

        H2("5.7 Module design"),
        P(f"The code is split so that each file has one reason to change. Line counts below were measured from the repository."),
        TAB("Modules, sizes and responsibilities.", ["Module", "Lines", "Responsibility"], mod_rows, widths=[2.0, 0.6, 3.9], align=["l", "r", "l"], size=9.5),
        P("Three decisions about this structure are worth recording. The backend does not re-implement any pipeline step: the forecast loop is the one piece of logic that exists twice, because the Streamlit version is written inside a page function. "
          "The experiment script `scripts/run_experiments.py` imports the same `src/` functions as the API, so the numbers in Chapter 8 come from the product's code, not from a parallel implementation. "
          "And the web console has its own small UI kit (buttons, cards, charts, tables, toasts), so the pages contain layout and calls, not styling."),

        H2("5.8 API design"),
        P("All routes live under `/api`. Reads are GET and actions are POST. Failures return the FastAPI `detail` string, which the console shows verbatim, so error messages are written for the analyst: 'Upload and process your data first (Data Upload).' is what a 409 says. "
          "The status codes follow one rule: 409 means an earlier step is missing, 400 means the request is well-formed but not acceptable, 422 means the request body failed validation, 404 means a saved model is absent, 502 and 503 are reserved for the optional AI service."),
        TAB("The 22 routes of the TrendCast API.", ["Method", "Path", "Purpose", "Errors"], routes, widths=[0.6, 1.5, 3.3, 1.3], align=["c", "l", "l", "l"], size=8.5),
        P("`POST /api/data/upload` is the only multipart route. It accepts a row limit because the full H&M transactions file has 31.8 million rows; a value of 0 means no limit. The limit reads the first rows of the file, which are the earliest dates, so a small limit gives a short date range rather than a random sample. "
          "`POST /api/forecast` accepts only the horizons 7, 14 and 30 and needs at least five days of history for the article."),

        H2("5.9 User interface design"),
        P("The console has thirteen pages: a public landing page, an about page, an overview that shows pipeline progress, seven working pages (upload, explore, demand, features, training, domain, evaluation, forecast), the AI insights page and a not-found page. "
          "The visual language is a flat, high-contrast grid with thick borders and one accent colour per state, which keeps charts and tables legible and prints well. A light and a dark theme are available from every page."),
        TAB("Console pages and the endpoints they use.", ["Page", "Route", "Endpoints used"],
            [["Landing, About", "/ and /about", "None (public)"],
             ["Overview", "/app", "/api/state"],
             ["Data upload", "/app/upload", "POST /api/data/upload, GET /api/data/report"],
             ["Data exploration", "/app/explore", "GET /api/explore"],
             ["Demand analysis", "/app/demand", "GET /api/demand/table"],
             ["Feature engineering", "/app/features", "POST /api/features/build, GET /api/features"],
             ["Model training", "/app/training", "/api/training/split, baseline, xgboost, load, results"],
             ["Domain adaptation", "/app/domain", "/api/domain/options, run, last"],
             ["Model evaluation", "/app/evaluation", "GET /api/evaluation"],
             ["Demand forecast", "/app/forecast", "/api/forecast/articles, POST /api/forecast"],
             ["AI insights", "/app/insights", "/api/ai/status, explain, forecast-summary"]],
            widths=[1.8, 1.5, 3.2], align=["l", "l", "l"], size=9.5),
        P("Four design rules were applied to every working page. Each page opens with its purpose and the step it belongs to. Long actions show a busy state and finish with a notice. "
          "Numbers are formatted the same way everywhere (thousands separators, three decimals for errors, a percentage for MAPE) and a result that is worse than the baseline is drawn in the warning colour with the word 'worse', not hidden. "
          "Errors from the API are shown in a panel with a retry button. Chapter 8 shows each working page with real data; the three screens below illustrate the design itself."),
        *shot("11_features-built.png", "Feature-engineering page after building the table: 31,094 rows, 36 columns, 31 model inputs.", 5.0, 3.5),
        *shot("14_domain-form.png", "Domain-adaptation page: the analyst chooses the domain-defining column and the source and target values before running.", 5.0, 3.5),
        *shot("22_overview.png", "Overview page: the pipeline progress is read from the server, with the next step highlighted.", 5.0, 3.5),

        H2("5.10 Design decisions and trade-offs"),
        P("Every design has costs. The table records the main decisions, what each bought and what it cost, so that the limitations in Chapter 9 can be traced back to a choice and not to an accident."),
        TAB("Principal design decisions.",
            ["Decision", "Reason", "Cost"],
            [["Keep the ML code in `src/` and wrap it with a thin API", "One implementation for both front ends; experiments and tests call the product's own functions", "Two `src/` modules still import Streamlit, and the forecast loop exists twice"],
             ["Hold all state in one in-memory dictionary", "No database to install; a new upload cleanly invalidates everything derived from the old one", "Single user only; everything except the model files is lost on restart"],
             ["Split by date, never randomly", "A random split would let the model see the future and give optimistic numbers", "The test window may contain events (here Christmas) the training window lacks"],
             ["Importance weighting for domain adaptation", "Simple, inspectable, works with any learner that takes sample weights", "Depends on a well-behaved classifier; weights are unnormalised (Chapter 8)"],
             ["Gate each page on the pipeline flags", "No expected errors in the browser; the analyst is told the next step", "Pages cannot be opened out of order"],
             ["Report results as measured, including negative changes", "The aim is to learn whether adaptation works, not to show that it does", "The headline numbers are modest"],
             ["Optional Gemini explanation with aggregated context only", "Plain-language help without sending raw data; the app works without a key", "Depends on an external service that was unavailable during our screen capture"]],
            widths=[2.0, 2.5, 2.0], align=["l", "l", "l"], size=9),
        P("Two further choices concern what was left out. Probabilistic forecasts, safety-stock calculation and per-forecast explanations were not built: the batch objectives mention explaining forecast drivers and translating error into inventory impact, "
          "but the product offers gain-based importance for the whole model only, and the inventory translation was done offline for Chapter 8. These are stated plainly as the gap between the objectives and the delivered design. "
          "Finally, the design does not include a cold-start path for articles without history: the forecast route needs five days of data per article and the lag features need more. Chapter 8 measures what an attribute-only model could do for unseen articles, "
          "and Chapter 10 proposes adding it."),
    ]
    return _trim(out) if F.REPORT else out
