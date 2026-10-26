"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for TrendCast."""

from . import facts as F
from .blocks import B, FIG, H1, H2, N, P, TAB
from .refs import N as C


def blocks():
    out = chapter3() + chapter4()
    if F.REPORT:   # compact report variant (the diagram is shown in Chapter 5, the phase list is a paragraph)
        from .ch1 import trim
        out = trim(out, drop=(F.diag("02_high_level_workflow.png"), "Manual practice, the Streamlit-only application and TrendCast compared",
                              "Project phases", "Environment problems that did occur.", "The hardware is a standard desktop", "The suggested minimums",
                              "Two design rules shape the proposed system", "Security is modest by design", "The schedule is feasible because"),
                   replace={"The work divides into phases": P(
                       "The work followed the dependencies of the pipeline, with calendar dates left as placeholders [DATES]: problem study and base-paper reading; the data pipeline (loading, cleaning, merge, daily demand); "
                       "features, split, baselines and XGBoost; domain adaptation and evaluation; the Streamlit application, then the FastAPI layer and the React console; testing, real-data experiments and screenshots; and documentation. "
                       "Each phase depends only on the previous one and the heaviest compute step is the 30-second tuned XGBoost fit, so the schedule risk was data, not computation: results on synthetic sample files looked far better than they are, and the real-data run changed the conclusions.")})
    return out


def st(key):
    return F.API["stages_seconds"][key]


def lat(key):
    return F.API["latency_ms"][key]


# =====================================================================================================================
def chapter3():
    ds = F.DS
    s_up, s_ex, s_ft = st("upload+clean+merge (684k rows)"), st("explore (aggregate daily)"), st("build features")
    s_x, s_t, s_d = st("train XGBoost (default)"), st("train XGBoost (tuned)"), st("domain adaptation run")
    f30, f7, ev = lat("POST /api/forecast (30 d)"), lat("POST /api/forecast (7 d)"), lat("GET /api/evaluation")
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        H2("3.1 Technical Feasibility"),
        P("**Hardware.** Every measurement in this report was taken on an Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory, no graphics card used for computation, running Windows 11 Pro, "
          "while other jobs ran on the same machine. The project therefore shows that the whole pipeline, including 300-tree XGBoost training and hyper-parameter search, runs on an ordinary office PC. Smaller machines were not tested."),
        P(f"**Software.** All components are mature open-source packages: Python 3.11, pandas, NumPy, scikit-learn {C('sk')}, XGBoost {C('xgb')}, FastAPI and Uvicorn for the service, and React with Vite and Recharts for the console. "
          "They install from the public package indexes; `run.bat` creates a virtual environment, installs the Python and Node packages and starts both servers on ports 8317 and 5317. LightGBM is used only for a comparison in the experiments."),
        P(f"**Data.** The H&M Personalized Fashion Recommendations release {C('hm')} is real, public for the competition and large (31.8 million transactions). The in-memory design of the application cannot hold all of it on the machine used, "
          f"so a subset was taken: the {ds['articles']} best-selling articles of the first transaction shard, {ds['raw_rows']:,} rows over 107 days. This keeps all experiments reproducible in minutes, at the price of a short history, discussed under limitations."),
        P("**Evidence from measurement.** The main technical risks were tested directly instead of argued, and are listed in the table below."),
        TAB("Technical risks and the measurements that retired them", ["Risk", "Measurement", "Verdict"],
            [["Loading and cleaning a realistic table is too slow", f"{ds['raw_rows']:,} rows uploaded, validated, cleaned and merged in {s_up:.1f} s; daily aggregation {s_ex:.1f} s", "Feasible"],
             ["Feature engineering too slow", f"{ds['feature_rows']:,} rows x {ds['feature_cols']} inputs built in {s_ft:.1f} s", "Feasible"],
             ["Model training too slow without a GPU", f"XGBoost default {s_x:.1f} s; with time-ordered tuning (10 iterations x 3 folds) {s_t:.1f} s", "Feasible"],
             ["Domain adaptation too slow for interactive use", f"One full run (source model, classifier, weights, adapted model) {s_d:.1f} s", "Feasible"],
             ["Forecast API too slow", f"Median {f7['median']:.0f} ms (7 days) to {f30['median']:.0f} ms (30 days), p95 {f30['p95']:.0f} ms; evaluation page {ev['median']:.0f} ms", "Feasible"],
             ["Forecasts accurate enough to be useful", "XGBoost beats the moving-average baseline but not repeating yesterday's demand; recursive forecasts are worse than a flat 7-day mean", "Partly: usable for one-day-ahead, weak beyond"],
             ["Domain adaptation improves the target", f"Improved RMSE on {F.DOM['summary']['pairs_where_adaptation_helped']} of {F.DOM['summary']['pairs_total']} pairs; not robust", "Not established"]],
            widths=[2.0, 3.3, 1.2], align=["l", "l", "l"], size=9.5),
        P("**Environment problems that did occur.** LightGBM 4.7 crashed with an access violation on this machine when pandas or XGBoost was imported before it, so the experiment script imports it first. "
          "scikit-learn's logistic regression, used as the domain classifier, does not converge in 1,000 iterations on the unscaled features and warns on every run. "
          "A Python client calling the service through the name localhost adds about two seconds per request on this machine because of an IPv6 fallback; all latencies in this report were measured on 127.0.0.1. "
          "None of these blocks the project, and each is recorded where it matters."),
        H2("3.2 Economic Feasibility"),
        P("The project was built with no licence cost: Python, the data libraries, XGBoost, FastAPI, React and Vite are open source, and the H&M files are released for the competition and used here for academic purposes only (the subset is not redistributed in the repository). "
          "The one paid-service dependency is optional: the AI Insights page calls the Gemini REST service with an API key from `.env`; the rest of the application works without it, and the page says so when no key is set."),
        P("The hardware is a standard desktop that the team already had. Electricity and the team's own time were the only costs. We do not put money figures on them, because none were recorded. "
          "For an operating retailer the economic question is different: the tool would replace manual spreadsheet forecasting for the articles in its scope, and its value would be the stock cost avoided by better forecasts. "
          "This project does not demonstrate that saving; the offline inventory calculation in Chapter 8 shows only how many units each forecast would have under- and over-stocked on the test window."),
        H2("3.3 Operational Feasibility"),
        P("A planner needs no programming to use the tool. The console follows the order of the work: Data upload, Data exploration, Demand analysis, Feature engineering, Model training, Domain adaptation, Model evaluation, Demand forecast, AI insights. "
          "Each page tells the user what to do first when an earlier step is missing, because the API answers a plain-language 409 message rather than an error trace, and the sidebar ticks the steps already done. "
          "Validation errors, such as a transactions file without the required columns, return a 400 message that names the missing columns."),
        P("Operation is deliberately simple. The application is single-user and single-process: the pipeline state sits in memory behind a lock, uploads are read into memory, and only the trained models are saved to the `models/` folder. "
          "That suits a demonstration or a planner working alone on one machine; it does not suit several simultaneous users or a restart-proof service, and Chapter 10 lists the changes needed for that. "
          "Maintenance is light: the `src/` modules are small and commented, the API layer adds no logic of its own, and 39 automated tests plus a 26-check smoke test catch regressions."),
        H2("3.4 Schedule Feasibility"),
        P("The work divides into phases that follow the dependencies of the pipeline. Calendar dates are left as placeholders because the batch file does not record them; the order and the output of each phase are what the report can state truthfully."),
        TAB("Project phases", ["Phase", "Work", "Output", "Dates"],
            [["1", "Problem study and base-paper reading", "Abstract, objectives, literature survey", "[DATES]"],
             ["2", "Data pipeline: loading, validation, cleaning, merge, daily demand", "src/ preprocessing and aggregation modules", "[DATES]"],
             ["3", "Features, split, baselines and XGBoost with tuning", "Models and metrics; saved joblib files", "[DATES]"],
             ["4", "Domain adaptation and evaluation", "Domain classifier, weights, before-and-after report", "[DATES]"],
             ["5", "Streamlit application, then FastAPI layer and React console", "app.py; backend/ with 22 routes; 13-page frontend", "[DATES]"],
             ["6", "Testing, real-data experiments, screenshots", "39 pytest tests, smoke test, experiments/, 25 screenshots", "[DATES]"],
             ["7", "Documentation: reviews, report, paper", "Decks, chapter documents, report, IEEE paper", "[DATES]"]],
            widths=[0.6, 2.6, 2.4, 0.9], align=["c", "l", "l", "c"], size=10),
        P("The schedule is feasible because every phase depends only on the previous one and each is small: the heaviest compute step is the 30-second tuned XGBoost fit, and the whole experiment suite runs in minutes. "
          "The risk to the schedule was not computation but data: until real data was used, results from synthetic sample files looked far better than they are, and the real-data run changed the conclusions."),
        H2("3.5 Advantages and Constraints"),
        B("**Advantages.** No licence cost; runs on a desktop; every number is reproducible by a script; the pipeline is gated and explains its refusals; adaptation, baselines and explanation are in one place; the code is modular enough to swap in another learner.",
          f"**Constraints.** Short history ({ds['date_min']} to {ds['date_max']}) and 300 articles; no promotion, weather or image data; single user and in-memory state; cleaning drops identical rows that are usually real repeat purchases; the optional AI explanation depends on an external service; "
          "no cold-start mode; multi-day forecasts are weak."),
    ]


# =====================================================================================================================
def chapter4():
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing System"),
        P("Two things count as the existing system. In practice, a merchandiser or planner without a forecasting tool estimates next period's demand from the last few days or weeks of sales, usually in a spreadsheet: "
          "a moving average per article, adjusted by judgement for season and promotions. This is the baseline the application itself uses, because it is what the learned model has to beat."),
        P("In the project's own history, the existing system was the Streamlit application `app.py` (597 lines, 11 pages) over the `src/` package. It already held the whole pipeline, from upload to forecast and domain adaptation, "
          "but exposed it only through Streamlit's session state: there was no HTTP interface, no automated tests, no gating messages through an API, and a user could only reach the functions through that one interface. "
          "It is kept, untouched, as a second front end; the FastAPI layer and the React console are additive."),
        H2("4.2 Limitations of the Existing System"),
        B("**Manual forecasting** ignores calendar effects beyond what the planner remembers, cannot use product attributes or price, and does not say how good it is or how it behaves when moved to another channel or product group.",
          "**The Streamlit-only application** could not be called by other programs or tested through an interface; its state lived in a browser session; and its pages could not be reused in a different front end.",
          "**Both** lack a way to test whether a model trained in one sales context holds in another, and neither shows which inputs drive a forecast beyond an overall importance chart."),
        H2("4.3 Proposed System"),
        P("TrendCast keeps the `src/` pipeline and adds three things: a FastAPI service that wraps every step in a documented route; a React console of thirteen pages that follows the work from upload to forecast; "
          "and a test and experiment layer (pytest, a smoke test, real-data experiment scripts, screenshot capture) that reproduces every number in this report. "
          "The pipeline is the one described in Chapter 6: validation and cleaning, daily article demand, leakage-safe features, a date split, a moving-average baseline and XGBoost with optional time-ordered tuning, "
          "importance-weighted domain adaptation, evaluation, recursive forecasts and an optional plain-language explanation."),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow of TrendCast from upload to the optional AI explanation.", 5.8),
        P("Two design rules shape the proposed system. First, **the API adds no logic**: every route calls the same `src/` function the Streamlit page calls, so the two front ends cannot disagree and the numbers in this report apply to both. "
          "Second, **every claim is checkable**: nothing in the application is hard-coded, and a result such as an adaptation gain is computed from the uploaded files at the moment it is shown."),
        H2("4.4 Advantages of the Proposed System"),
        B("A guided order of work with gating messages in plain language, so a step cannot silently run on missing input.",
          "A baseline is always shown next to the model, and domain adaptation always reports the domain-classifier accuracy, the weight statistics and the before-and-after metrics, whether they are good or bad.",
          "A documented API (22 routes) that any other front end or script can call; the Streamlit page and the React console use the same code.",
          f"Leakage guards by construction: lag and rolling features from shifted values, a split by date, tuning with time-ordered folds. Reproducibility: {F.PYTEST_PASSED} tests, a {F.SMOKE_TOTAL}-check smoke test and scripts for every experiment.",
          "Honest evaluation: a rolling-origin backtest, a feature-group ablation, controls for the adaptation and exact SHAP values offline."),
        TAB("Manual practice, the Streamlit-only application and TrendCast compared", ["Aspect", "Manual / spreadsheet", "Streamlit application only", "TrendCast"],
            [["Interface", "Spreadsheet", "One Streamlit session", "REST API (22 routes) plus React console, and the Streamlit page"],
             ["Features", "Last days' average, judgement", "Calendar, lag, rolling, attributes", "Same, with the pipeline callable and tested"],
             ["Baseline shown", "It is the baseline", "Moving average", "Moving average, with naive, rolling-mean, RF and LightGBM comparisons in the experiments"],
             ["Domain shift", "Not examined", "Importance weighting, no controls", "Importance weighting plus four controls and a time-clean protocol in the experiments"],
             ["Explanation", "None", "Gain importance", "Gain importance in the application; TreeSHAP offline"],
             ["Testing", "None", "None", f"{F.PYTEST_PASSED} pytest tests and a {F.SMOKE_TOTAL}-check smoke test"],
             ["Reproducibility", "Low", "Manual clicks", "Scripts regenerate every reported number"]],
            widths=[1.0, 1.4, 1.7, 2.4], align=["l", "l", "l", "l"], size=9.5),
        H2("4.5 Functional Requirements"),
        P("The requirements below are those the delivered system meets; each is tied to the console page that offers it and the route(s) behind it."),
        TAB("Functional requirements", ["ID", "Requirement", "Page", "Route(s)"],
            [["FR-1", "Upload the transactions and articles CSV files (customers optional) with a row limit; reject files with missing required columns", "Data upload", "POST /api/data/upload"],
             ["FR-2", "Clean (dates, null ids, non-positive prices, duplicates) and merge; show a data-quality report", "Data upload", "POST /api/data/upload, GET /api/data/report"],
             ["FR-3", "Show demand trends, top products, category and channel breakdowns and the price distribution", "Data exploration", "GET /api/explore"],
             ["FR-4", "Show the aggregated daily demand table", "Demand analysis", "GET /api/demand/table"],
             ["FR-5", "Build the feature table (calendar, cyclical, lag, rolling, encoded attributes) and list the model inputs", "Feature engineering", "POST /api/features/build, GET /api/features"],
             ["FR-6", "Split by date with an adjustable training fraction (0.5 to 0.95) and show the split", "Model training", "GET /api/training/split"],
             ["FR-7", "Train and score the moving-average baseline and XGBoost, with optional time-ordered tuning; save and reload the model", "Model training", "POST /api/training/baseline, /xgboost, /load; GET /api/training/results"],
             ["FR-8", "Run domain adaptation for a chosen column, source and target; show classifier accuracy, feature shift, weights and before-and-after metrics", "Domain adaptation", "GET /api/domain/options; POST /api/domain/run; GET /api/domain/last"],
             ["FR-9", "Compare models, show the domain report and the top-20 feature importance", "Model evaluation", "GET /api/evaluation"],
             ["FR-10", "Forecast one article for 7, 14 or 30 days and show history, forecast and total", "Demand forecast", "GET /api/forecast/articles; POST /api/forecast"],
             ["FR-11", "Explain results in plain language with the Gemini service when configured, from aggregated numbers only", "AI insights", "GET /api/ai/status; POST /api/ai/explain, /ai/forecast-summary"],
             ["FR-12", "Show pipeline progress and the next step", "Overview", "GET /api/state"],
             ["FR-13", "Report health and gate each step with a 409 message until its inputs exist", "All pages", "GET /api/health; all gated routes"],
             ["FR-14", "Describe the project, data and techniques", "About, Landing", "(static)"]],
            widths=[0.55, 3.15, 1.25, 1.6], align=["c", "l", "l", "l"], size=9),
        P("Input rules enforced by the routes: the training fraction must lie between 0.5 and 0.95 (otherwise a 422 response); the forecast horizon must be 7, 14 or 30 days; "
          "a domain run needs two different values and a target with enough dates to hold out a test half; a forecast needs at least five rows of history for the article; and the optional customers file is accepted but not needed by any model."),
        H2("4.6 Non-Functional Requirements"),
        TAB("Non-functional requirements and measured values", ["ID", "Requirement", "Measured value or evidence"],
            [["NFR-1", "Performance: pipeline steps respond within interactive time on the target machine", f"Upload {s_(F, 'upload+clean+merge (684k rows)')} s; features {s_(F, 'build features')} s; XGBoost {s_(F, 'train XGBoost (default)')} s; tuned {s_(F, 'train XGBoost (tuned)')} s; domain run {s_(F, 'domain adaptation run')} s"],
             ["NFR-2", "Latency: forecast and evaluation calls under half a second", f"Forecast median {lat('POST /api/forecast (7 d)')['median']:.0f} / {lat('POST /api/forecast (14 d)')['median']:.0f} / {lat('POST /api/forecast (30 d)')['median']:.0f} ms for 7 / 14 / 30 days; evaluation {lat('GET /api/evaluation')['median']:.0f} ms; health {lat('GET /api/health')['median']:.1f} ms"],
             ["NFR-3", "Correctness: no future information in features; chronological split", "Lag and rolling values shifted by one day (unit-tested); split by date; tuning with TimeSeriesSplit"],
             ["NFR-4", "Reliability: invalid input returns a clear error, not a crash", "400 for bad files and values, 409 for missing prerequisites, 422 for out-of-range fractions; tested"],
             ["NFR-5", "Reproducibility: every reported number can be regenerated", "scripts/run_experiments.py writes experiments/**/metrics.json; docs/REPORT_FACTS.md is generated from them"],
             ["NFR-6", "Usability: guided, accessible order of work", "Sidebar with progress ticks, gating messages, light and dark themes; no accessibility audit was done"],
             ["NFR-7", "Privacy: raw data stay on the machine", "Only aggregated metrics, top features and a forecast summary go to the optional Gemini call"],
             ["NFR-8", "Portability: runs on a standard desktop", "Windows 11, Python 3.11, Node; no GPU"],
             ["NFR-9", "Maintainability: tested, modular", f"{F.PYTEST_PASSED} pytest tests ({F.PYTEST_UNIT} unit, {F.PYTEST_API} API) and {F.SMOKE_TOTAL} smoke checks, all passing"]],
            widths=[0.65, 2.55, 3.3], align=["c", "l", "l"], size=9.5),
        P("Security is modest by design for a single-user tool. The API accepts cross-origin requests only from the console's own origin (localhost and 127.0.0.1 on port 5317); there is no sign-in; "
          "the Gemini key lives in the `.env` file, which is git-ignored, and is read by the server only, never sent to the browser; and uploaded data are held in memory and not written to disk. "
          "A deployment shared between users would need authentication, per-user state and storage, which are listed as future scope."),
        H2("4.7 Hardware Requirements"),
        TAB("Hardware", ["Item", "Minimum we would suggest", "Used for the measurements"],
            [["Processor", "Any recent 4-core CPU", "Intel Core i5-12500, 6 cores / 12 threads"],
             ["Memory", "8 GB", "15.7 GB (the 684k-row subset needs well under this)"],
             ["Storage", "2 GB free for packages, models and data", "Packages, models and the git-ignored data folder"],
             ["Graphics", "None", "No GPU used"],
             ["Display", "1280 x 800 or larger", "Screenshots at 1440 x 900"]],
            widths=[1.2, 2.5, 2.8], align=["l", "l", "l"], size=10),
        P("The suggested minimums are our estimates and were not tested; only the right-hand column was measured."),
        H2("4.8 Software Requirements"),
        TAB("Software", ["Component", "Version used", "Role"],
            [["Python", "3.11.9", "Language of the pipeline, the API and the experiments"],
             ["pandas / NumPy", "2.2.1 / 1.26.4", "Tables and arrays"],
             ["scikit-learn", "1.5.0", "Logistic regression, random forest, time-series split, randomised search, metrics"],
             ["XGBoost", "2.0.3", "Main model; exact TreeSHAP through pred_contribs"],
             ["LightGBM", "4.7.0", "Comparison model in the experiments only"],
             ["FastAPI / Uvicorn", "0.143.3 / 0.54.0", "REST service"],
             ["Streamlit", "1.66.0", "Original front end"],
             ["React 19, Vite 8, Recharts", "as in package.json", "Console"],
             ["Playwright, pytest", "installed in the environment", "Screenshot capture and tests"],
             ["Operating system / browser", "Windows 11 Pro / Chrome", "Platform used"]],
            widths=[1.9, 1.7, 2.9], align=["l", "l", "l"], size=10),
        H2("4.9 User Roles and System Constraints"),
        P("There is one role, the **analyst** (a planner, student or evaluator) who runs the whole pipeline; there is no sign-in, because the product is a single-user tool run on one machine. "
          "A second role, the **developer or evaluator**, runs the scripts and tests that import the same `src/` package. The optional Gemini service is an external actor that receives aggregated numbers."),
        B("**Single user and in-memory state.** One shared pipeline state, protected by a lock; a second browser tab shares it. A new upload resets everything downstream.",
          "**Order of work.** Later steps refuse to run until earlier ones have produced their inputs; the domain pair must have two different values and enough dates in the target to hold out a test half.",
          "**Data shape.** The required columns are t_dat, customer_id, article_id and price in the transactions file and article_id and prod_name in the articles file; other columns are used when present.",
          "**Forecast horizon.** 7, 14 or 30 days, for an article with at least five rows of history; the forecast is recursive and is weak beyond a week.",
          "**Network.** The browser console talks to the API on the same machine; only the optional AI explanation needs internet access."),
    ]


def s_(F_, key):
    return f"{F_.API['stages_seconds'][key]:.1f}"
