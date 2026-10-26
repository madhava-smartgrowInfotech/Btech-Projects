"""Chapter 6: Methodology and Software Implementation. methodology_blocks() feeds document 9, application_blocks() feeds document 12."""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import cite

R = F.R
S = F.S


def methodology_blocks():
    d = R["dataset"]
    b = []

    # ------------------------------------------------------------------ 6.1
    b += [H2("6.1 Overall methodology"),
          P("The method is a supervised classification pipeline on a mixed table of numbers, flags and categories, extended with a text channel and an evidence channel. A startup is described by nine numeric fields "
            "(funding total and rounds, ages at the first and last funding and milestone, relationships, milestones and average participants), seven flags (venture capital, angel investors, rounds A to D and a top-500 "
            "mark), a state, an industry and, optionally, a short business description. The structured part is imputed, scaled and one-hot encoded into 37 values. The description is turned into a 384-value sentence "
            f"embedding by all-MiniLM-L6-v2 {cite('sbert', 'minilm')}. The two blocks are fused into one unit-length vector that is used twice: by the classifier, which gives the probability of SUCCESS, and by a "
            f"nearest-neighbour search over the training startups, which gives comparable historical cases in the spirit of the retrieval idea of {cite('maarouf')} and the classical nearest-neighbour rule {cite('knn')}. The steps are:"),
          N("**Load** a startup table: a local CSV of the public Kaggle table if present, otherwise the built-in synthetic generator with the same columns.",
            "**Prepare**: remove duplicate rows, map the status to a label (acquired and IPO to SUCCESS, closed to FAILURE), coerce numbers, normalise categories and add the logarithm of the funding total.",
            "**Encode**: median imputation and standardisation of the numbers, most-frequent imputation of the flags, one-hot encoding of state and industry, giving 37 structured values.",
            "**Embed** the description (company names masked, at most 2,000 characters) with MiniLM and **fuse** it with the structured vector with weight 0.5 each.",
            "**Compare** Logistic Regression, Decision Tree, Random Forest and XGBoost on five repeated stratified 80/20 splits, with the preprocessor fitted on the training part only.",
            "**Select** the model with the highest mean balanced accuracy, refit it on all rows and store it with the preprocessor and the fused training vectors.",
            "**Serve**: for a submitted startup compute the probability of SUCCESS, retrieve k comparable startups with an equal quota of each outcome, and return an explanation and a risk label."),
          FIG(F.diag("11_evaluation_protocol.png"), "Evaluation protocol used for model selection and for the reported metrics.", 5.4),
          P("**Two sets of measurements.** The shipped application was trained on the synthetic fallback table, so the statistics it displays (Logistic Regression 0.749 balanced accuracy) test whether the pipeline "
            "recovers a signal that the generator planted. For real evidence the same code (`app.ml.preprocessing`, `app.ml.models` and the same split protocol) was run by `scripts/run_experiments.py` and "
            f"`scripts/extra_experiments.py` on the real public table of {d['rows']} startups, structured features only, in {R['runtime_seconds']:.0f} s on the CPU. Those runs add ROC-AUC and PR-AUC, a fifth model "
            "(HistGradientBoosting), two imbalance strategies, a decision-threshold sweep, calibration bins, a forest-size study, the 70:30 protocol of the base paper, a synthetic-to-real transfer test, a "
            "leakage ablation and a retrieval-only classifier. Chapter 8 reports them; this chapter describes how they were made.")]

    # ------------------------------------------------------------------ 6.2
    b += [H2("6.2 Dataset"),
          H3("6.2.1 The public Startup Success Prediction table (all real measurements)"),
          P(f"The real data is the public \"Startup Success Prediction\" table of {cite('kaggle')} (listed as public domain): 923 start-ups, 49 columns, almost all in the United States. The outcome column `status` is "
            f"`acquired` for 597 companies and `closed` for 326. The Kaggle download requires a login, so the identical 923-row CSV was fetched from a public GitHub copy into `data/real/startup_data.csv`; it was "
            f"deliberately kept out of `data/raw/` so that the shipped application is not changed. The application's own de-duplication leaves **{d['rows']} rows, {d['success']} SUCCESS "
            f"({d['success_share'] * 100:.1f} %) and {d['failure']} FAILURE**. Success is therefore the majority class, the reverse of the situation assumed in the project objectives. The table has 9 numeric columns, 7 flags, "
            "a state code and an industry category code that the script maps to the ten industry names of the application (software, e-commerce, mobile, media, biotech, health technology, clean technology, "
            "education; anything else becomes Other); states outside the ten most common become Other. The table has **no free-text description**, so the text and retrieval channels cannot be evaluated on it."),
          P("Three of the numeric columns (relationships, milestones and the two milestone ages) are recorded at or after the end of the observation window for part of the companies, and the table has no time stamps with which "
            f"to remove them. They are kept for the main results and removed in a separate ablation (Chapter 8); this is the look-ahead problem that the base paper itself cites {cite('zbikowski', 'leakage')}."),
          H3("6.2.2 The synthetic fallback table (the shipped application)"),
          P(f"If no CSV is found the loader calls `generate_synthetic` (seed 42), which creates {F.SYN_ROWS:,} rows with the same columns: {F.SYN_SUCCESS} SUCCESS and {F.SYN_FAILURE} FAILURE (the success probability of "
            "a row is 0.42). Every numeric field is drawn from a distribution whose parameters differ slightly by class (for example, successful companies get a larger mean number of rounds, milestones and relationships, "
            "and a higher chance of venture capital and later rounds). The description is built from one of nine templates: with probability 0.35 a template shared by both classes, with 0.45 a template that "
            "matches the class, and with 0.20 a template of the other class. The wording of the text therefore depends on the label **by construction**. The signal in this table is the one the generator planted, "
            "so a model that scores well on it shows that the pipeline recovers a planted signal, not that startups can be predicted this well. The fallback is recorded in the metadata "
            "(`synthetic_fallback: true`), in `data/raw/SYNTHETIC_FALLBACK.txt` and in the dataset note shown on the dashboard."),
          TAB("The two data sources", ["", "Real public table", "Synthetic fallback"],
              [["Rows used", f"{d['rows']} ({d['success']} SUCCESS, {d['failure']} FAILURE)", f"{F.SYN_ROWS:,} ({F.SYN_SUCCESS} SUCCESS, {F.SYN_FAILURE} FAILURE)"],
               ["Share of SUCCESS", f"{d['success_share'] * 100:.1f} % (majority class)", f"{F.SYN_SUCCESS / F.SYN_ROWS * 100:.1f} % (minority class)"],
               ["Description text", "None", "Template sentences, wording depends on the label"],
               ["Used for", "All real measurements (structured features only)", "The shipped model, the dashboard, the screenshots, the representation and retrieval-size studies"],
               ["Origin", "Public Kaggle table, copy from a public GitHub repository", "`generate_synthetic`, seed 42"],
               ["Evaluation", "5 x 80/20 stratified splits, seed 42 (185 test rows per split)", "The same protocol (280 test rows per split)"]],
              widths=[1.4, 2.5, 2.4], align=["l", "l", "l"], size=10),

          ]

    # ------------------------------------------------------------------ 6.3
    b += [H2("6.3 Preprocessing and feature construction"),
          H3("6.3.1 Cleaning and the target"),
          P("`prepare_frame` removes duplicate rows, maps `status` to the label (acquired, success, IPO, true, yes and 1 to SUCCESS = 1; closed, failure, no and 0 to FAILURE = 0; any other value is dropped), converts the "
            "numeric and flag columns with `to_numeric` (bad values become missing), strips and normalises the state and industry strings (missing becomes Unknown), adds the column "
            "`log_funding_total_usd = log(1 + funding)` to reduce the heavy tail of funding amounts, and cleans the description. No outlier removal is done."),
          H3("6.3.2 Structured preprocessor"),
          TAB("The 37 structured features", ["Group", "Fields", "Treatment", "Columns"], [
              ["Numeric", "age_first_funding_year, age_last_funding_year, age_first_milestone_year, age_last_milestone_year, relationships, funding_rounds, funding_total_usd, milestones, avg_participants, log_funding_total_usd",
               "Median imputation, standardisation", "10"],
              ["Flags", "has_VC, has_angel, has_roundA, has_roundB, has_roundC, has_roundD, is_top500", "Most-frequent imputation", "7"],
              ["State", "CA, CO, FL, IL, MA, NY, OR, PA, TX, WA (and Other when present)", "Constant imputation (Unknown), one-hot, unknown categories ignored", "10"],
              ["Industry", "AI, Biotech, CleanTech, E-Commerce, EdTech, FinTech, HealthTech, Media, Mobile, Software (and Other when present)", "Same as state", "10"],
          ], widths=[0.9, 3.0, 1.7, 0.7], size=9, align=["l", "l", "l", "c"]),
          P("The preprocessor is a scikit-learn `ColumnTransformer` that is fitted on the training part of every split, so no test statistic reaches the scaler or the imputers. The 37 columns are the same for the shipped "
            "table and for the real table fitted on all 922 rows."),
          H3("6.3.3 Text cleaning and embedding"),
          P("The description is cleaned by `clean_text`: a regular expression replaces a capitalised company name followed by Inc, LLC, Labs, Technologies or Systems with \"this company\", whitespace is collapsed and the "
            f"text is cut at 2,000 characters. Masking names follows the practice of {cite('maarouf')}, which prevents a language model from recognising a famous company. The text is embedded by "
            "`sentence-transformers/all-MiniLM-L6-v2`, a 22-million-parameter model that gives a 384-value vector per text on a CPU. If the model cannot be loaded, a deterministic hashing embedding of the same size is "
            "used and the backend name (`sentence-transformers` or `hash-fallback`) is returned in every result. An empty description is replaced by the text \"<industry> startup\"."),
          H3("6.3.4 Fusion"),
          P("Each block is scaled to unit length and the fused vector is [0.5 s, 0.5 t], scaled to unit length again (equation in Section 6.5). The weight alpha = 0.5 is a fixed constant in `app/config.py`; it was not tuned."),
          H3("6.3.5 Class imbalance"),
          P("All classifiers are trained with balanced class weights (`class_weight=\"balanced\"` for Logistic Regression, Decision Tree and Random Forest). XGBoost is used with its default class handling, and the "
            "retrieval step enforces equal quotas. The base paper oversamples with ADASYN " + cite('adasyn') + "; oversampling by random duplication of the minority rows was compared with class weights on the real table "
            "(Chapter 8, where the minority class is FAILURE). SMOTE-type synthetic oversampling " + cite('smote') + " was not implemented.")]

    # ------------------------------------------------------------------ 6.4
    b += [H2("6.4 Algorithm choice and justification"),
          TAB("Algorithms and why they are used", ["Component", "Choice", "Reason"], [
              ["Baseline classifier", "Logistic Regression", "Transparent, fast, signed coefficients give the explanation, and it is the baseline of the base paper [1] and of [2]"],
              ["Single tree", "Decision Tree (depth 8)", "Readable rules; high variance, so it shows what ensembling improves"],
              ["Bagged ensemble", f"Random Forest (300 trees) {cite('rf')}", "Handles mixed variables and interactions with little tuning; named best model of the base paper"],
              ["Boosted ensemble", f"XGBoost {cite('xgb')}; HistGradientBoosting in the real-data study", "The boosting family of the objectives (gradient boosting " + cite('gbm') + "); a second boosting implementation checks that the result is not specific to XGBoost"],
              ["Text representation", "all-MiniLM-L6-v2 sentence embeddings", "Small, runs on a CPU, no key or service; captures meaning beyond keywords; used by the base-paper family for startup descriptions"],
              ["Fusion", "Weighted concatenation, unit length", "One vector serves the classifier and the search; cosine similarity becomes a dot product"],
              ["Evidence", "Balanced top-k cosine retrieval", "Shows comparable startups of both outcomes; retrieval was the idea of [2]; fixes the evidence view when classes are imbalanced"],
              ["Selection metric", "Balanced accuracy", "Insensitive to class ratio; the primary metric of [2]"],
              ["Explanation", "Coefficients or importances plus retrieval counts", "Deterministic, no sampling, no extra library; SHAP " + cite('shap') + " was not used"],
          ], widths=[1.3, 2.1, 2.9], size=9.5, align=["l", "l", "l"]),
          P("Support vector machines and gradient boosting are named in the base paper; an SVM was not implemented here because Logistic Regression already serves as the linear baseline and the objectives name "
            "Logistic Regression, Decision Tree, Random Forest and boosting ensembles. Deep networks were excluded: with 922 or 1,400 rows they would overfit and could not be tuned reliably, a point made in {} "
            "for few-shot settings.".format(cite('maarouf')))]

    # ------------------------------------------------------------------ 6.5
    b += [H2("6.5 Mathematical formulation"),
          H3("6.5.1 Standardisation and the logistic model"),
          P("Each numeric column is standardised with the training mean and standard deviation. Logistic Regression models the probability of SUCCESS as a sigmoid of a linear score and is fitted by minimising the "
            "class-weighted log-loss with an L2 penalty (C = 1):"),
          EQ("z = (x - mean) / sd          P(y = 1 | x) = 1 / (1 + exp(-(w . x + b)))"),
          EQ("minimise  sum_i  c(y_i) * [ -y_i log p_i - (1 - y_i) log(1 - p_i) ]  +  (1 / 2C) ||w||^2,     c(y) = n / (2 n_y)"),
          H3("6.5.2 Trees and ensembles"),
          P("A tree chooses splits that reduce the Gini impurity of the child nodes. A Random Forest averages the votes of many trees grown on bootstrap samples with random feature subsets; its Gini importance is the "
            "total impurity decrease of a feature, and its permutation importance is the drop in the test ROC-AUC when one feature is shuffled. XGBoost adds trees one by one, each fitted to the gradient of the "
            "regularised objective:"),
          EQ("G = 1 - sum_c p_c^2          y_hat(x) = sum_k f_k(x)          Obj = sum_i l(y_i, y_hat_i) + sum_k [ gamma T_k + (lambda / 2) ||w_k||^2 ]"),
          H3("6.5.3 Fused vector, cosine similarity and the retrieval vote"),
          P("With s the structured vector and t the text embedding, both scaled to unit length, and alpha = 0.5, the fused vector and the similarity of two startups are"),
          EQ("x = [ alpha s , (1 - alpha) t ] / || [ alpha s , (1 - alpha) t ] ||          sim(x, x') = x . x'"),
          P("For a submitted startup the training rows are ranked by similarity and the first k//2 SUCCESS rows and k - k//2 FAILURE rows are kept (the set N_k). The similarity-weighted vote used in the "
            "retrieval-size study and in the retrieval-only classifier is"),
          EQ("p_vote = sum_{i in N_k} max(0, sim_i) * y_i  /  sum_{i in N_k} max(0, sim_i)          predict SUCCESS if p_vote >= 0.5"),
          H3("6.5.4 Decision rule and risk label"),
          EQ("outcome = SUCCESS if P(y = 1 | x) >= 0.5 else FAILURE          confidence = max(P(y = 1), P(y = 0))"),
          P("The risk label is \"Lower risk\" if the outcome is SUCCESS and the confidence is at least 0.70, \"Moderate risk\" if the confidence is at least 0.55, and \"Higher uncertainty\" otherwise. "
            "The threshold of 0.5 is the default; Chapter 8 shows what other thresholds would do on the real data."),
          H3("6.5.5 Metrics"),
          P("With TP, FP, TN and FN counted for SUCCESS as the positive class:"),
          EQ("accuracy = (TP + TN) / n     precision = TP / (TP + FP)     recall = TP / (TP + FN)     F1 = 2 P R / (P + R)"),
          EQ("balanced accuracy = (1/2) [ TP / (TP + FN) + TN / (TN + FP) ]"),
          EQ("ROC-AUC = P( score of a random SUCCESS > score of a random FAILURE ) = integral of TPR d(FPR)"),
          P(f"Balanced accuracy is the selection metric because it does not reward predicting the majority class. ROC-AUC {cite('roc')} measures ranking quality independently of the threshold; PR-AUC "
            f"{cite('pr')} is stored beside it in the real-data results. Every value is the mean and the standard deviation over five splits.")]

    # ------------------------------------------------------------------ 6.6
    b += [H2("6.6 Model architecture and training configuration"),
          H3("6.6.1 Hyper-parameters"),
          TAB("Classifiers and their exact settings (`app/ml/models.py`)", ["Model", "Settings"], [
              ["Logistic Regression", "solver lbfgs, class_weight balanced, max_iter 1000, C 1.0"],
              ["Decision Tree", "max_depth 8, min_samples_split 10, min_samples_leaf 5, class_weight balanced, random_state 42"],
              ["Random Forest", "n_estimators 300, class_weight balanced, min_samples_leaf 2, n_jobs -1, random_state 42"],
              ["XGBoost", "n_estimators 400, max_depth 6, learning_rate 0.05, subsample 0.8, colsample_bytree 0.8, reg_lambda 1.0, eval_metric logloss, random_state 42 (a scikit-learn HistGradientBoosting with the same depth and rate is the code's fallback)"],
              ["HistGradientBoosting (real-data study only)", "max_iter 300, max_depth 4, learning_rate 0.05, l2_regularization 1.0, random_state 42"],
          ], widths=[1.9, 4.4], size=9.5, align=["l", "l"]),
          TAB("Constants (`app/config.py`)", ["Constant", "Value", "Meaning"], [
              ["RANDOM_STATE", "42", "Seed of the splits and the tree models"],
              ["N_SPLITS / TEST_SIZE", "5 / 0.2", "Five stratified shuffle splits, 20 % test"],
              ["ALPHA", "0.5", "Weight of the structured block in the fused vector"],
              ["EMBEDDING_MODEL_NAME / EMBEDDING_DIM", "all-MiniLM-L6-v2 / 384", "Text encoder and its output size"],
              ["DEFAULT_K / RETRIEVAL_KS", "50 / [10, 20, 30, 50]", "Number of comparable startups and the values the API accepts"],
              ["MAX_DESC_LEN", "2,000", "Longest accepted description (characters)"],
          ], widths=[2.4, 1.5, 2.4], size=9.5, align=["l", "c", "l"]),
          H3("6.6.2 Training and selection"),
          P(f"`run_evaluation` embeds all descriptions once, runs the five splits and fits the four models on the fused vectors of each split. It also fits Logistic Regression on structured-only, text-only and combined "
            f"vectors and scores the similarity-weighted vote for each k. The model with the highest mean balanced accuracy is refitted on all {F.SYN_ROWS:,} rows. On the shipped table that is "
            f"**Logistic Regression** ({F.syn_app('Logistic Regression')}), ahead of XGBoost ({F.syn_app('XGBoost')}), Random Forest ({F.syn_app('Random Forest')}) and Decision Tree ({F.syn_app('Decision Tree')}). "
            f"On the real table the order differs: XGBoost and Random Forest reach {F.real('XGBoost')} and {F.real('Random Forest')}, and Logistic Regression {F.real('Logistic Regression')} (Chapter 8). "
            "The served model was therefore selected on synthetic data, and rebuilding the artefacts from a real CSV can select a different model without any code change."),
          H3("6.6.3 Cost of training"),
          P(f"All studies were run on {F.HARDWARE}. The whole real-data study (five models, five splits, imbalance, threshold, calibration, size and transfer studies and permutation importance) took "
            f"{R['runtime_seconds']:.0f} s, and the extra studies {F.X['runtime_seconds']:.1f} s. Training the shipped models on 1,400 rows with embeddings, five splits and charts takes a few minutes the first time, "
            "mostly for downloading and running the embedding model; later starts load the stored artefacts in seconds.")]
    return b


def application_blocks():
    lat = F.LAT
    b = []

    # ------------------------------------------------------------------ 6.7
    b += [H2("6.7 Application architecture"),
          P("**Backend.** `app/main.py` creates the FastAPI application, mounts the static folder, includes the router of `app/api_extra.py` and defines the routes. Each route calls `ensure_artifacts()`, which fills the "
            "module-level `STATE` dictionary once per process: it loads `best_model.joblib`, `preprocessor.joblib`, `train_fused.npz`, `train_frame.pkl`, `metadata.json` and the evaluation results; if any of the "
            "first five files is missing it loads the dataset, prepares it and runs `run_evaluation` first, which is why the first start takes several minutes. `predict_one` is a plain function, so the same code is used by "
            "the JSON route and by the form route of the original pages."),
          P("**Frontend.** The React application is a set of lazily loaded pages (`Landing`, `Login`, `Dashboard`, `Analyze`, `Performance`, `Insights`) under `react-router`. A `Guard` component redirects an "
            "unauthenticated visitor from `/app` to `/login`. The sign-in token is stored in the browser's local storage (`vp_token`) and an axios interceptor adds it as a bearer header. Pages fetch their data with a "
            "small `useApi` hook; charts use Recharts; the layout is a Tailwind CSS 4 design with light and dark tokens; an activity log records every API call with its status and time. The production build splits "
            "vendor code into separate chunks (React, charts, motion, three.js for the background grid)."),
          P(f"**Size.** The backend is {F.LOC['backend']:,} lines of Python, the original templates {F.LOC['templates']} lines, the React source {F.LOC['frontend']:,} lines, the tests {F.LOC['tests']} lines and the "
            f"experiment and test scripts {F.LOC['experiment_scripts']} lines (measured with `wc -l`).")]

    # ------------------------------------------------------------------ 6.8
    b += [H2("6.8 API design"),
          TAB("Endpoints", ["Method and path", "Request", "Response"], [
              ["GET /api/health", "none", "`status`, `app`, `records` (training rows), `best_model`; 500 with `detail` on failure"],
              ["GET /api/model-metrics", "none", "Evaluation JSON: `models` (mean and std of accuracy, balanced_accuracy, precision, recall, f1, confusion matrix), `best_model`, `representations`, `retrieval_k`, `metadata`"],
              ["GET /api/insights", "none", "`total`, `success`, `failure`, `success_rate`, `industries[]`, `states[]`, median funding by outcome, `correlations`"],
              ["POST /predict", "JSON payload (below)", "`outcome`, `probability_success`, `probability_failure`, `confidence`, `model`, `risk`, `similar[]`, `similar_counts`, `explanation[]`, `embedding_backend`, `k`; 422 on invalid input, 500 on error"],
              ["GET /api/config", "none", "States, industries, allowed k values, field ranges and defaults, `max_description`, best model, class counts, alpha, embedding backend, dataset note, demo email"],
              ["GET /api/feature-importance?top=N", "N (default 15)", "`model`, `kind` (abs_coefficient or importance), `features[]` with value and, for linear models, the signed coefficient"],
              ["POST /api/auth/login", "`email`, `password`", "`token`, `user`; 401 with `detail` if wrong"],
              ["GET /api/auth/me", "`Authorization: Bearer <token>`", "`name`, `email`; 401 if the token is missing, altered or expired"],
              ["GET /, /dashboard, /predict, /performance, /insights", "none", "Original server-rendered pages"],
              ["POST /predict-form", "Form fields", "Result page; 400 with a message if the description is empty or too long, or the values are invalid"],
          ], widths=[1.9, 1.6, 2.8], size=9, align=["l", "l", "l"]),
          P("The payload of `POST /predict` has 20 fields, all optional with defaults: the nine numeric fields (funding_total_usd, funding_rounds, age_first_funding_year, age_last_funding_year, "
            "age_first_milestone_year, age_last_milestone_year, relationships, milestones, avg_participants), the seven flags (has_VC, has_angel, has_roundA, has_roundB, has_roundC, has_roundD, is_top500), `state`, "
            "`industry_type`, `description` and `k`."),
          CODE('POST /predict\n{"funding_total_usd": 2500000, "funding_rounds": 2, "relationships": 6, "milestones": 3,\n "has_VC": true, "has_roundA": true, "state": "CA", "industry_type": "Software",\n'
               ' "description": "A subscription analytics platform for small retailers ...", "k": 50}\n\n'
               '200 OK\n{"outcome": "SUCCESS", "probability_success": 0.83, "probability_failure": 0.17, "confidence": 0.83,\n "model": "Logistic Regression", "risk": "Lower risk",\n'
               ' "similar_counts": {"SUCCESS": 25, "FAILURE": 25}, "k": 50,\n "similar": [{"similarity": 0.58, "outcome": "SUCCESS", "industry": "Software", "state": "CO", ...}, ...],\n'
               ' "explanation": ["has_roundC: value 0.00 (scaled), weight 2.495 - supports FAILURE", ..., "Retrieved 50 comparable historical startups ..."],\n "embedding_backend": "sentence-transformers"}', 8.5),
          P(f"Measured on 127.0.0.1 with the model loaded (`scripts/measure_latency.py`): GET /api/health median {lat['health']['median_ms']:.1f} ms, GET /api/model-metrics {lat['model_metrics']['median_ms']:.1f} ms, "
            f"GET /api/insights {lat['insights']['median_ms']:.1f} ms, POST /predict {lat['predict_k10']['median_ms']:.1f} ms at k = 10 and {lat['predict_k50']['median_ms']:.1f} ms at k = 50.")]

    # ------------------------------------------------------------------ 6.9
    b += [H2("6.9 Security and error handling"),
          B("**Input validation.** The Pydantic model rejects values outside fixed ranges: funding 0 to 1e10, rounds 0 to 20, ages 0 to 30, relationships 0 to 200, milestones 0 to 50, average participants 0 to 50; non-numeric "
            "values and a description longer than 2,000 characters are rejected; `k` must be one of 10, 20, 30 or 50. The response is status 422 with the field names. Unknown industries or states are accepted and handled by the "
            "one-hot encoder (unknown categories become all zeros).",
            "**Form route.** The original form refuses an empty description (400), clamps negative numbers to zero and replaces an invalid k with the default.",
            "**Failures.** Route functions catch exceptions, log them and return status 500 with a `detail` string; the React page turns a failed request into a message with a hint (for example, \"Start the app with run.bat\" "
            "when the server cannot be reached). The embedding step falls back to the hashing embedding if the transformer cannot be loaded.",
            "**Demo sign-in.** The credentials come from the environment or from `.env` (`DEMO_EMAIL`, `DEMO_PASSWORD`, `DEMO_SECRET`); the defaults are the demo account. The email and the password are compared with "
            "`hmac.compare_digest`. The token is a URL-safe base64 string of `email|expiry|signature`, where the signature is an HMAC-SHA256 of the email and the expiry; the lifetime is 12 hours and a changed or expired token is "
            "rejected with 401.",
            "**What is not protected.** The sign-in is for the React screens only: `POST /predict` and the original pages need no token, there is one shared account, no rate limit, no HTTPS and no audit log. Detailed "
            "exception messages are returned to the client. The application is meant to run on localhost and must not be exposed to a network as it is. No security audit or penetration test was carried out."),
          P(f"The 29 API edge cases of `scripts/edge_tests.py` (Chapter 7) check the ranges, the k whitelist, the description limit, empty and extreme values, the form route, every GET route and the token cases; all {F.N_EDGE} pass.")]

    # ------------------------------------------------------------------ 6.10
    b += [H2("6.10 Installation and execution"),
          H3("6.10.1 One-click start (Windows)"),
          P("Install Python 3.10 or newer (3.11.9 was used) and Node.js 18 or newer, open the `8.ProjectCode` folder and double-click `run.bat`. The script (1) checks Python and Node, (2) creates `.venv`, or rebuilds it if "
            "it was copied from another machine and is broken, (3) installs `requirements.txt` (FastAPI 0.115.6, scikit-learn 1.5.2, pandas 2.2.3, XGBoost 2.1.3, sentence-transformers 3.3.1, torch 2.5.1 and others), "
            "(4) runs `npm install` in `frontend/` on the first run, and (5) starts the backend in a second window on port 8410, opens the browser at http://localhost:5410 and runs the Vite server on port 5410. The first "
            "start downloads the embedding model (about 90 MB) and trains the artefacts if they are missing; later starts take seconds. The ports are set in `.env` (`BACKEND_PORT`, `FRONTEND_PORT`)."),
          H3("6.10.2 By hand"),
          CODE("python -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt\npython -m uvicorn app.main:app --host 127.0.0.1 --port 8410\n\n# second terminal\ncd frontend\nnpm install\nnpm run dev", 9),
          P("Sign in with the demo account `demo@venturepulse.com` / `Demo@1234` (the sign-in page has a button that fills it), then use the Dashboard, Analyze a startup, Model performance and Startup insights screens. "
            "To use real data, copy the public CSV into `data/raw/`, delete the files in `models/` and restart; the artefacts are rebuilt and the metadata then records the source."),
          H3("6.10.3 Checks and scripts"),
          CODE(".venv\\Scripts\\python.exe -m pytest tests -q               # 7 tests\n.venv\\Scripts\\python.exe scripts\\smoke_test.py            # 15 checks against a running server\n"
               ".venv\\Scripts\\python.exe scripts\\edge_tests.py            # 29 API edge cases\n.venv\\Scripts\\python.exe scripts\\run_experiments.py      # real-data study -> evaluation/real_results.json\n"
               ".venv\\Scripts\\python.exe scripts\\extra_experiments.py    # leakage ablation, retrieval-only, per industry\n.venv\\Scripts\\python.exe scripts\\measure_latency.py      # latency of the API", 9),
          P("A Docker route (`run-docker.bat`, `Dockerfile`) starts the backend and the original pages only; it was not exercised in this documentation run.")]
    return b


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
