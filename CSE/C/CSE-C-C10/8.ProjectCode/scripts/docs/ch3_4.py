"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis)."""

from . import facts as F
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import cite


def blocks():
    return chapter3() + chapter4()


def chapter3():
    L = F.LAT
    rf = F.R["models"]["Random Forest"]
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether a project can be built and used with the resources at hand. For this project the question was answered partly by analysis and partly "
          "by building the system, so most entries below carry a measured value rather than an estimate. Where a question could not be answered favourably, the entry says so."),

        H2("3.1 Technical Feasibility"),
        P("The technical risk lay in four places: whether four classifiers and a sentence encoder could be trained and served on an ordinary computer without a graphics processor; "
          "whether a prediction that includes embedding a description and searching the training startups is fast enough for an interactive page; whether the required public "
          "data could be obtained; and whether the model reaches a useful level on real startups. "
          f"The development machine is {F.HARDWARE}. On that machine:"),
        TAB("Technical feasibility checks and what was measured", ["Question", "Measurement", "Verdict"], [
            ["Can the models be trained on a CPU?", f"All five models, five splits and the ten studies on the real table ({F.REAL_ROWS} rows) ran in {F.R['runtime_seconds']:.0f} s; the leakage, retrieval and per-industry studies in {F.X['runtime_seconds']:.0f} s", "Feasible"],
            ["Are predictions fast enough?", f"POST /predict median {L['predict_k10']['median_ms']:.0f} ms (k = 10) and {L['predict_k50']['median_ms']:.0f} ms (k = 50); 95th percentile {L['predict_k50']['p95_ms']:.0f} ms at k = 50; read-only endpoints {L['health']['median_ms']:.0f} to {L['insights']['median_ms']:.0f} ms", "Feasible"],
            ["Is the sentence encoder usable offline?", "all-MiniLM-L6-v2 (384 dimensions) runs on the CPU; it is downloaded once, and a deterministic hashing fallback of the same width is used if it cannot be loaded", "Feasible (first run needs a download)"],
            ["Can the real data be obtained?", f"The Kaggle download needs a login; the identical 923-row table was fetched from a public copy ({F.REAL_ROWS} rows after de-duplication)", "Feasible, with a workaround"],
            ["Is the accuracy useful?", f"Real table, 5 x 80/20 splits: Random Forest balanced accuracy {F.pm(rf)}, ROC-AUC {F.pm(rf, 'roc_auc')}", "Moderately useful; upper bound (Chapter 8)"],
            ["Is the model small enough to ship?", "The served model files total about 4.5 MB (best model 4 KB, preprocessor 6 KB, training vectors 2.1 MB, stored embeddings 2.0 MB, training frame 0.4 MB)", "Feasible"],
        ], widths=[1.7, 3.4, 1.2], size=9.5, align=["l", "l", "l"]),
        P(f"The weakest answer is the fifth. The real table is small, its test folds have 185 rows, and four of its fields are partly recorded around the outcome window; when they "
          "are removed the ROC-AUC of the best models drops from about 0.82 to about 0.72 (Chapter 8). Technical feasibility of building and running the system is therefore "
          "established; technical feasibility of the 85 to 92 % accuracy claimed by the base paper is not, on this data."),
        P("A smaller risk is the dependency chain. The first saved models had been written with newer library versions than those pinned in `requirements.txt` and could not be "
          "loaded; they were retrained with the pinned versions (scikit-learn 1.5.2, pandas 2.2.3), and `run.bat` builds its own virtual environment from that file."),

        H2("3.2 Economic Feasibility"),
        P("The system uses only free and open-source software, runs on one local computer and needs no cloud account, no graphics processor and no paid data. Its cost is therefore "
          "the development time of four students and the electricity of the machine, which we did not meter and do not estimate. The costs that would appear in a real deployment, "
          "namely data licences (for example a Crunchbase subscription), hosting and maintenance, are outside the project and are listed under future scope."),
        P("The benefit side is qualitative: a repeatable second opinion that costs a fraction of a second per startup, can be re-run on new data by a non-expert, and shows its "
          "reasons. We did not measure savings or investment outcomes, and no claim of financial benefit is made."),

        H2("3.3 Operational Feasibility"),
        P("Operationally the system is a small web application. One batch file (`run.bat`) creates the environment, trains the model if the saved files are missing, and starts the "
          "backend on port 8410 and the interface on port 5410. A user signs in with the demonstration account, fills one form and reads one result page. The form has defaults for "
          "every field, so a prediction can be requested with nothing typed (tested in Chapter 7), and invalid values are refused with a clear message. "
          "The interface works in light and dark themes and at narrow widths. The main operational constraint is the data: the person who enters the indicators must know them, and "
          "the model was trained on US startups of a past period, so predictions for other markets or periods are less reliable."),

        H2("3.4 Schedule Feasibility"),
        P("The project was carried out in phases that follow the objectives. The table lists the phases and their products; calendar dates are left as placeholders because the "
          "academic calendar of the institution is not recorded in the batch files."),
        TAB("Project phases (plan) and their products", ["Phase", "Work", "Product", "Period"], [
            ["1 Problem and survey", "Base paper, literature survey, objectives", "Abstract, survey, objectives", "[DATES]"],
            ["2 Data", "Obtain public table, synthetic fallback with the same schema, cleaning and target mapping", "`data/`, `app/ml/dataset.py`, `preprocessing.py`", "[DATES]"],
            ["3 Models", "Four classifiers, five repeated splits, representation and retrieval studies", "`app/ml/models.py`, `evaluation.py`, `evaluation_results.json`", "[DATES]"],
            ["4 Retrieval and explanation", "Sentence embedding, fusion, balanced cosine retrieval, explanations", "`embeddings.py`, `retrieval.py`, `predictor.py`", "[DATES]"],
            ["5 Application", "FastAPI service, original pages, React interface, demonstration sign-in", "`app/main.py`, `api_extra.py`, `frontend/`", "[DATES]"],
            ["6 Verification", "Unit, smoke and edge tests; latency; screenshots", "`tests/`, `scripts/`", "[DATES]"],
            ["7 Real-data study", "Ten studies on the real table; leakage ablation; documentation", "`run_experiments.py`, `extra_experiments.py`, this report", "[DATES]"],
        ], widths=[1.3, 2.3, 2.0, 0.7], size=9.5, align=["l", "l", "l", "c"]),

        H2("3.5 Advantages and Constraints"),
        H3("Advantages"),
        B("Runs locally on a normal computer: no cloud account, no GPU, no API key and no licence fee.",
          f"Fast at prediction time: a median of {L['predict_k10']['median_ms']:.0f} to {L['predict_k50']['median_ms']:.0f} ms for a complete prediction with retrieval of comparable startups.",
          "Every prediction carries its reasons: signed feature contributions, a risk label and a table of comparable historical startups with outcomes and similarity scores.",
          "Four classifiers are compared under one protocol; the best by balanced accuracy is served and the comparison is visible in the application.",
          f"Reproducible and measured: scripts regenerate every real-data number, and {F.N_TESTS} automated checks guard the application."),
        H3("Constraints"),
        B(f"The real-data performance is moderate (Random Forest ROC-AUC {F.pm(rf, 'roc_auc')}) and partly depends on fields recorded around the outcome window.",
          "The shipped model was trained on synthetic data; the application's own dashboard numbers describe that data.",
          "The text channel could not be tested on real data, because the real table has no descriptions.",
          "No temporal validation, no founder or market data, one US dataset of 922 rows.",
          "Demonstration sign-in only; one local user; no database."),

        H2("3.6 Risk Analysis"),
        P("The risks that were identified at the start, what happened to each, and what was done about it are listed below. They are the reasons for several design decisions "
          "described in Chapters 5 and 6."),
        TAB("Risks, outcome and mitigation", ["Risk", "What happened", "Mitigation"], [
            ["The public dataset cannot be downloaded without a login", "The shipped application had to start on a synthetic fallback with the same schema; the metadata and the dashboard note record this", "The identical table was fetched from a public copy for all real measurements; the report separates the two datasets"],
            ["Synthetic descriptions leak the label", "Text-only classification of the synthetic table reaches 0.599 balanced accuracy because success and failure templates differ in wording", "Synthetic text results are reported as a pipeline check; the text channel is listed as untested on real data"],
            ["Look-ahead bias in the real table", "Four fields (relationships, milestones, two milestone ages) are partly recorded around the outcome; the table has no dates", "A leakage ablation quantifies the effect (ROC-AUC about 0.82 to 0.72 for Random Forest); real figures are called an upper bound"],
            ["Small data and noisy comparisons", f"{F.REAL_ROWS} rows and 185-row test folds; Random Forest, XGBoost and HistGradientBoosting lie within one standard deviation", "Five repeated splits with means and standard deviations; no ranking is claimed inside the noise"],
            ["Library versions break the saved models", "Models saved with newer scikit-learn and pandas could not be loaded", "Models were retrained with the pinned versions; `run.bat` builds its own environment"],
            ["Sentence encoder unavailable offline", "Possible on a first run without a connection", "Deterministic hashing fallback of the same width, flagged in the response"],
        ], widths=[1.8, 2.4, 2.1], size=9, align=["l", "l", "l"]),

        H2("3.7 Feasibility Summary"),
        P("The project is technically feasible on a laptop, economically feasible because it uses only free software, operationally feasible because one start script and one "
          "form are enough, and feasible within a semester-length schedule. Its only limited feasibility is a scientific one: with the data that could be obtained, the "
          "accuracy claimed in the base paper cannot be reached or verified, and the honest result is a working, explained and measured system of moderate accuracy."),
    ]


def chapter4():
    L = F.LAT
    fr = [
        ["FR-1", "Predict SUCCESS or FAILURE for one startup from 9 numeric fields, 7 flags, state, industry and an optional description", "POST /predict; Analyze screen", "Analyze"],
        ["FR-2", "Refuse values outside the allowed ranges and a description over 2,000 characters; accept only k in {10, 20, 30, 50}", "Pydantic validation, HTTP 422", "Analyze"],
        ["FR-3", "Show the outcome, the success and failure probabilities, the confidence and a risk label", "Result card; Lower risk / Moderate risk / Higher uncertainty", "Result"],
        ["FR-4", "Name the features that drive the estimate", "Top five signed coefficients or importances", "Result"],
        ["FR-5", "Show comparable historical startups with similarity, outcome, industry, state, funding, rounds and summary", "Balanced top-k cosine retrieval over training rows; sortable, paged table", "Result"],
        ["FR-6", "Show the split of retrieved cases by outcome", "Evidence donut chart (SUCCESS / FAILURE counts)", "Result"],
        ["FR-7", "Show the model comparison, confusion matrix, representation study and retrieval-size study", "GET /api/model-metrics", "Model performance"],
        ["FR-8", "Show dataset insights: industry success rates, funding distributions, correlations", "GET /api/insights", "Insights"],
        ["FR-9", "Show the feature weights of the served model", "GET /api/feature-importance", "Performance"],
        ["FR-10", "Offer a demonstration sign-in that protects the React screens", "POST /api/auth/login, GET /api/auth/me, HMAC-signed token", "Login"],
        ["FR-11", "Report that the service is alive and which model it serves", "GET /api/health; status indicator", "All screens"],
        ["FR-12", "Keep the original server-rendered pages working", "GET /, /dashboard, /predict, /performance, /insights; POST /predict-form", "Legacy pages"],
        ["FR-13", "Offer light and dark themes and keyboard navigation", "Theme toggle; command palette (`/`) and key shortcuts", "All screens"],
    ]
    nfr = [
        ["NFR-1 Response time", "A prediction feels instant", f"Median {L['predict_k10']['median_ms']:.0f} ms (k = 10) and {L['predict_k50']['median_ms']:.0f} ms (k = 50); p95 {L['predict_k10']['p95_ms']:.0f} / {L['predict_k50']['p95_ms']:.0f} ms", "Met"],
        ["NFR-2 Read endpoints", "Dashboards load without delay", f"health {L['health']['median_ms']:.1f} ms, model-metrics {L['model_metrics']['median_ms']:.1f} ms, insights {L['insights']['median_ms']:.1f} ms (median)", "Met"],
        ["NFR-3 Accuracy", "Reported on held-out data with several metrics and a comparison of models", f"Real table: balanced accuracy up to {F.pm(F.R['models']['XGBoost'])}, ROC-AUC up to {F.pm(F.R['models']['Random Forest'], 'roc_auc')}", "Reported, moderate"],
        ["NFR-4 Input safety", "Bad input is refused with a clear message and changes nothing", "13 predict-payload cases and 2 form cases, all as expected", "Met"],
        ["NFR-5 Leakage control", "Retrieval and preprocessing use training data only", "Preprocessing fitted on the training split; retrieval searches training rows only; company names masked", "Met in the application; not possible for dates"],
        ["NFR-6 Privacy", "Inputs stay on the user's computer", "No external prediction service; the only download is the encoder, once", "Met"],
        ["NFR-7 Usability", "Usable by a non-expert, light and dark, narrow screens", "Defaults for every field; labels, hints, error sentences; responsive layout", "Met"],
        ["NFR-8 Portability", "Runs on a normal Windows PC", "Python 3.11, Node 24; `run.bat`; other systems untested", "Met on Windows only"],
        ["NFR-9 Maintainability", "Small modules with one job each", "Separate dataset, preprocessing, embeddings, retrieval, models, evaluation, services", "Met"],
        ["NFR-10 Testability", "Automated tests", f"{F.N_UNIT} unit, {F.N_SMOKE} smoke and {F.N_EDGE} edge checks pass", "Met"],
    ]
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),

        H2("4.1 Existing System and Its Limitations"),
        P("Today an early-stage startup is assessed in one of three ways. Investors and founders judge it from experience and intuition, which is quick but subjective, "
          f"inconsistent and open to bias {cite('base')}. Analysts compare it with a handful of remembered peers, which is slow and cannot be repeated by someone else. And some "
          f"published systems train a classifier on startup data and return a probability, as the base paper does with a Flask form {cite('base')}."),
        P("The limitations that follow are the ones named in the batch problem statement and the survey:"),
        B("Subjective judgement leads to inconsistent decisions.",
          "Failure causes become obvious only after capital has been committed.",
          "Success is rare in many datasets, so naive models under-predict it; imbalance is rarely examined (the base paper uses ADASYN without a comparison).",
          "A bare probability gives a founder nothing to act on: no drivers, no comparable cases.",
          "Reported accuracy levels cannot be checked when the data and the per-model results are not given, and leakage of post-outcome information is not controlled."),

        H2("4.2 Proposed System and Its Advantages"),
        P("The proposed system, VenturePulse, is a local web application over an ML pipeline. A user enters the indicators of a startup; the system scales and encodes them, "
          "embeds the optional description, fuses the two representations, estimates the outcome with the best of four compared classifiers, retrieves comparable startups "
          "from the training set in a balanced way and explains the estimate. The advantages follow from that design:"),
        B("The estimate comes with its reasons (signed feature terms) and its evidence (comparable startups with outcomes and similarity scores).",
          "Imbalance is handled explicitly with balanced class weights and a balanced retrieval quota, and compared with oversampling in a separate study.",
          "Evaluation follows a stated protocol (five repeated stratified 80/20 splits, balanced accuracy as the primary metric) that is the same as in the method paper.",
          "Everything runs locally and quickly, with no paid service.",
          "The measurements are repeatable by script, and the report states plainly which numbers come from synthetic and which from real data."),

        H2("4.3 Functional Requirements"),
        TAB("Functional requirements and how they are realised", ["ID", "Requirement", "Realisation", "Screen"], fr,
            widths=[0.55, 2.6, 2.3, 0.85], size=9, align=["c", "l", "l", "l"]),

        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements and the measured outcome", ["Requirement", "Target", "Measured or evidence", "Status"], nfr,
            widths=[1.05, 1.5, 2.85, 0.9], size=9, align=["l", "l", "l", "c"]),
        P("The accuracy requirement is a reporting requirement, not a target number. Objective 6 asks for accuracy, precision, recall, F1 and ROC-AUC, and these are reported "
          "with means and standard deviations. No target such as 85 % was set, because the achievable level on the available data was not known before the experiments."),

        H2("4.5 Hardware Requirements"),
        P("The system was developed and measured on one machine. We report its specification and do not invent a minimum; a smaller machine may work but was not tested."),
        TAB("Hardware used for development and measurement", ["Item", "Specification"], [
            ["Processor", "Intel Core i5-12500, 6 cores, 12 threads"],
            ["Memory", "15.7 GB RAM"],
            ["Graphics processor", "none used (CPU-only PyTorch)"],
            ["Storage", "about 4.5 MB for the served model files; 208 KB for the real table"],
            ["Display", "any browser window; the screenshots were taken at a width of 1440 pixels"],
            ["Operating system", "Windows 11 Pro"],
        ], widths=[1.7, 4.6], size=10.5, align=["l", "l"]),

        H2("4.6 Software Requirements"),
        TAB("Software used", ["Component", "Version", "Role"], [
            ["Python", "3.11.9", "Language of the pipeline and the API"],
            ["scikit-learn " + cite("sklearn"), "1.5.2", "Preprocessing, Logistic Regression, Decision Tree, Random Forest, metrics, splits"],
            ["pandas, NumPy, SciPy, joblib", "2.2.3, 1.26.4, 1.13.1, 1.4.2", "Tables, arrays, similarity, model files"],
            ["XGBoost " + cite("xgb"), "2.1.3", "Boosted-tree classifier"],
            ["sentence-transformers, PyTorch", "3.3.1, 2.5.1 (CPU)", "all-MiniLM-L6-v2 embeddings of the description"],
            ["FastAPI, uvicorn, Jinja2, python-multipart", "0.115.6, 0.34.0, 3.1.5, 0.0.20", "Web service, original pages, form posts"],
            ["pytest, httpx", "8.3.4, 0.28.1", "Automated tests"],
            ["Node.js and npm", "24.19.0 and 11.17.0", "Build and development server of the interface"],
            ["React, Vite, Tailwind CSS, Recharts, GSAP, Framer Motion", "18.3, 6.4, 4.3, 3.10, 3.15, 14.6", "Web interface, charts and motion"],
            ["Playwright with Chrome", "1.49.1", "Capturing the output screens"],
        ], widths=[2.3, 1.7, 2.3], size=10, align=["l", "l", "l"]),

        H2("4.7 User Roles"),
        P("The system has one kind of user. The **analyst** (an investor, an incubator officer or a founder) enters the indicators of a startup, reads the estimate, the drivers "
          "and the comparable startups, and looks at the model performance and insight pages to judge how far to trust the result. The **model owner** is the person who retrains "
          "or replaces the model by running the training script on a new table; this is done from the command line, not from the interface. The demonstration sign-in does not "
          "separate roles: it only protects the React screens with a signed token and a single account. A multi-user system would need real accounts, roles and storage, and is "
          "listed under future scope."),

        H2("4.8 Constraints and Assumptions"),
        N("The training data are US startups of a past period; the model is not validated on other markets or on recent years.",
          "The input fields follow the public table: ages are in years, funding in US dollars, state from ten codes plus Other, industry from ten names plus Other.",
          "The description is optional, at most 2,000 characters, and is truncated before it is embedded; an empty description is replaced by a short industry sentence.",
          "The first prediction downloads the sentence encoder if it is not cached; if it cannot be loaded the application uses a hashing fallback and records this in the response.",
          "The estimate is a statistical screening aid, not investment advice, and the interface says so on every result.",
          "The shipped model is trained on the synthetic fallback unless the public CSV is placed in `data/raw/`."),

        H2("4.9 Data Requirements"),
        P("The prediction request has 20 fields. The ranges below are enforced by the API (HTTP 422 outside them) and are the same in the React form. Ages are measured in years "
          "from the founding of the company, as in the public table."),
        TAB("Input fields of POST /predict", ["Field", "Type and range", "Default", "Meaning"], [
            ["funding_total_usd", "number, 0 to 1e10", "1,000,000", "Total funding raised in US dollars (also used as log1p)"],
            ["funding_rounds", "number, 0 to 20", "2", "Number of funding rounds"],
            ["age_first_funding_year / age_last_funding_year", "number, 0 to 30", "1.5 / 2.5", "Company age at the first and the latest funding round"],
            ["age_first_milestone_year / age_last_milestone_year", "number, 0 to 30", "1.0 / 2.0", "Company age at the first and the latest milestone"],
            ["relationships", "number, 0 to 200", "4", "Number of investor, advisor and partner relationships"],
            ["milestones", "number, 0 to 50", "2", "Number of recorded milestones"],
            ["avg_participants", "number, 0 to 50", "3", "Average number of investors per round"],
            ["has_VC, has_angel, has_roundA to has_roundD, is_top500", "boolean (7 flags)", "false", "Venture-capital or angel backing, the funding rounds reached, membership of a top-500 list"],
            ["state", "one of CA, NY, MA, TX, WA, IL, CO, FL, PA, OR, Other", "CA", "Location; unknown values are ignored by the one-hot encoder"],
            ["industry_type", "one of Software, E-Commerce, FinTech, HealthTech, EdTech, CleanTech, Media, Mobile, AI, Biotech, Other", "Software", "Sector"],
            ["description", "text, at most 2,000 characters", "empty", "Optional business description; company names are masked; empty text is replaced by an industry sentence"],
            ["k", "10, 20, 30 or 50", "50", "Number of comparable startups to retrieve"],
        ], widths=[1.9, 1.7, 0.8, 1.9], size=9, align=["l", "l", "c", "l"]),
        P("The training data have the same columns plus the outcome (status: acquired or closed, mapped to SUCCESS or FAILURE). Rows with an unknown status are dropped, "
          "duplicates are removed, numeric fields are coerced and missing values are imputed (median for numbers, most frequent for flags, a constant for categories)."),

        H2("4.10 Traceability of Requirements to Objectives"),
        TAB("Objectives, requirements and where they are verified", ["Objective", "Requirements", "Verified in"], [
            ["1 Collect a dataset", "FR-1, FR-8; data requirements 4.9", "Chapter 6 (data), Chapter 8"],
            ["2 Clean data, engineer features", "FR-2; NFR-5", "Chapter 6 (preprocessing), Chapter 7"],
            ["3 Address class imbalance", "NFR-5; balanced weights and quotas", "Chapter 8 (imbalance study)"],
            ["4 Train and compare models", "FR-7; NFR-3", "Chapter 8 (model comparison)"],
            ["5 Identify separating features", "FR-4, FR-9", "Chapter 8 (feature importance)"],
            ["6 Evaluate with five metrics", "NFR-3", "Chapter 8 (tables of results)"],
        ], widths=[2.1, 2.3, 1.9], size=10, align=["l", "l", "l"]),
    ]
