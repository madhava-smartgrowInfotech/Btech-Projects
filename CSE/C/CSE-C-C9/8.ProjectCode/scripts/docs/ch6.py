"""Chapter 6: Methodology and software implementation.

methodology_blocks()  -> sections 6.1-6.6 (reused in '9.METHODOLOGY&NOVELTY&KEY CONTRIBUTIONS.docx')
application_blocks()  -> sections 6.7-6.10 (reused in '12.DESIGN &IMPLEMENTATION.docx')
"""

import os

from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F


def _src(rel, start, end=None):
    """Lines of a source file from the line containing `start` up to (not including) the line containing `end`."""
    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    a = next(i for i, l in enumerate(lines) if start in l)
    b = len(lines)
    if end:
        b = next(i for i in range(a + 1, len(lines)) if end in lines[i])
    chunk = lines[a:b]
    while chunk and not chunk[-1].strip():
        chunk.pop()
    return "\n".join(chunk)


def _models_table():
    rows = []
    for m in F.MODELS:
        c = F.COMPARE[m]
        mark = "**" if m == F.BEST else ""
        rows.append([f"{mark}{F.MODEL_LABEL[m]}{mark}", F.f4(c["accuracy"]), F.f4(c["precision"]), F.f4(c["recall"]), F.f4(c["f1"]),
                     F.f4(c["roc_auc"]), f"{c['cv_roc_auc_mean']:.4f} +/- {c['cv_roc_auc_std']:.4f}"])
    return rows


def methodology_blocks():
    M = F.METRICS
    cm = F.CM[F.BEST]
    miss = F.RM["missing_cells_raw"]
    ms = F.MEAS["environment"]
    out = [
        H2("6.1 Overall methodology"),
        P(f"The methodology adapts the four-stage explainable machine-learning framework of the base paper {n('base')} (domain-adaptive feature engineering, multi-model training, SHAP interpretation and "
          "domain-specific validation) from organisations to individuals, and adds the parts that turn a model into a product: input validation, a forecast, a what-if comparison and a web interface. "
          "The work has two halves. An offline half prepares data, trains and evaluates models and writes artifacts; an online half loads those artifacts and answers one request at a time."),
        N("**Acquire** the UCI Adult / Census Income files (48,842 individual records) and a monthly economic index series for forecasting.",
          "**Clean** the records: strip whitespace, turn '?' into missing values, coerce numeric columns and drop rows without a target.",
          "**Engineer** twelve interpretable derived features (net capital, capital intensity, log scales, flags, age and hours bands, education tier, region, employment stability, capital position).",
          "**Split** the rows with a stratified 80/20 split (random state 42) and keep the 20% for the final test.",
          "**Train** four classifiers, each inside a scikit-learn Pipeline whose preprocessing is fitted on training data only.",
          "**Validate** with 5-fold stratified cross-validation on the training split, then evaluate on the held-out test split.",
          "**Select** the model with the highest test ROC-AUC and persist all pipelines, metrics, plots, SHAP importance and the forecast.",
          "**Serve**: validate an input record, derive features, predict, map the probability to a profile and risk band, compute local SHAP contributions, write plain-language insights, and optionally compare a what-if scenario.",
          "**Forecast** a 12-month horizon of the economic index with Holt-Winters exponential smoothing and a 95% band."),
        TAB("Stages of the base-paper framework and how this project realises them", ["Base-paper stage", "Base paper (hospitals)", "This project (individuals)"], [
            ["1. Domain-adaptive feature engineering", "236 line items reduced to 11 ratio, scale and categorical features", "14 raw census fields extended to 26 columns with 12 derived features; 145 columns after one-hot encoding"],
            ["2. Multi-model training", "LR, RF, GB, XGBoost, MLP at default settings", "LR, RF, GB, XGBoost; fixed hyperparameters, no search; no neural baseline"],
            ["3. SHAP interpretation", "Global importance and beeswarm; cost ratios dominate", "TreeExplainer: global top-15 at training time and live local contributions for every request"],
            ["4. Domain-specific validation", "Hospital-level Group K-Fold, temporal hold-out, counterfactuals, panel regression", "Stratified 5-fold CV and 80/20 test split (one row per person); logistic statistics; what-if comparison"],
        ], widths=[1.6, 2.35, 2.55], size=9.5),
        H2("6.2 Dataset"),
        P(f"The classification data are the Adult (Census Income) extract {n('uci')}, which originates in the 1994 US census database and was prepared for classification by Kohavi {n('kohavi')}. "
          f"The project uses both published files, `adult.data` (32,561 rows) and `adult.test` (16,281 rows), joined into {F.N_ROWS:,} individual records with 15 columns. The positive class, income above 50K "
          f"per year, covers {F.pct(F.RM['positive_rate_all'], 2)} of the rows. Missing values are written as '?' in three columns: workclass ({miss['workclass']:,} cells), occupation ({miss['occupation']:,}) "
          f"and native-country ({miss['native-country']:,}). The records are public and anonymous, and no personal data were collected for this project."),
        P("The income label is used as a **financial-profile signal**. It is not a credit score, a repayment record or a distress indicator, and the report never claims otherwise. This is the main difference "
          f"from the base paper, whose label is a hospital deficit derived from net income {n('base')}, and the reason the comparison in Chapter 8 is given as context only."),
        TAB("Facts about the classification dataset", ["Item", "Value"], [
            ["Source", "UCI Machine Learning Repository, Adult (Census Income), 1994 US census"],
            ["Files used", "`data/raw/adult.data` (32,561 rows) and `data/raw/adult.test` (16,281 rows)"],
            ["Records after joining", f"{F.N_ROWS:,} rows, 15 columns (14 inputs and the target)"],
            ["Target", "income above 50K (positive) versus 50K or less; test labels carry a trailing '.' that the cleaner removes"],
            ["Positive-class share", F.pct(F.RM["positive_rate_all"], 2)],
            ["Training / test rows", f"{F.N_TRAIN:,} / {F.N_TEST:,} (stratified 80/20, random state 42)"],
            ["Test class balance", f"{F.TEST_NEG:,} at 50K or less, {F.TEST_POS:,} above 50K"],
            ["Form option counts", "workclass 8, education 16, marital status 7, occupation 14, relationship 6, race 5, sex 2, country 41"],
            ["Not available", "transactions, balances, credit history, repayment records, time stamps"],
        ], widths=[1.8, 4.7], size=9.5, align=["l", "l"]),
        P("The Adult data are cross-sectional: every person appears once and there is no date. They therefore cannot be used to forecast the future. A second, separate series is used for the "
          "forecasting component: a monthly **Household Financial Conditions Index** from January 2015 to December 2025 (132 points) generated by `build_index_series()` with a fixed seed. "
          "The index is the sum of a linear trend (100 plus 0.35 per month), a yearly seasonal term of amplitude 4, a six-month downturn of 7 points from March to August 2020 and Gaussian noise with standard deviation 1.6. "
          "The series is **synthetic**, documented as such in `data/README.md`, and chosen so that the forecasting method can be demonstrated and tested end to end; it carries no information about any real economy, "
          "and the abstract's real indicators (inflation, lending rates, GDP) are not integrated."),
        H2("6.3 Preprocessing and feature engineering"),
        P("Preprocessing is split in two places on purpose. Operations that need no fitted state (cleaning and derived features) are plain functions in `scripts/feature_engineering.py` and are applied "
          "to all rows before the split. Operations that learn from data (imputation values, category lists, scaling) live in a `ColumnTransformer` inside each Pipeline and are therefore fitted on training rows only."),
        P("`clean_frame` strips whitespace from text columns, converts '?' to a missing value, coerces `age`, `fnlwgt`, `education-num`, `capital-gain`, `capital-loss` and `hours-per-week` to numbers and "
          "removes the trailing '.' from test-file labels. `add_derived_features` then adds twelve columns, each computable from the raw fields of a new user:"),
        TAB("Derived features added by add_derived_features()", ["Feature", "Rule", "Reason"], [
            ["net-capital", "capital-gain minus capital-loss", "single investment-position signal"],
            ["capital-intensity", "capital-gain plus capital-loss, at least 0", "overall investment activity"],
            ["log-capital-gain, log-capital-loss", "log(1 + value)", "both are highly skewed; helps the linear model"],
            ["has-capital-gain, has-capital-loss", "1 if the value is above 0, else 0 (as text)", "interpretable yes / no indicators"],
            ["hours-band", "up to 29 Part-time; 30-40 Full-time; 41-60 Extended; above 60 Very-long", "earning-effort proxy"],
            ["age-band", "up to 25; 26-35; 36-50; 51-65; above 65", "life-stage proxy"],
            ["education-tier", "education-num up to 9 Secondary-or-below; 10-12 Higher-secondary; 13 or more Tertiary", "groups 16 levels into 3"],
            ["region", "native-country mapped to North America, Latin America, Europe, Asia, Middle East or Other", "regional economic category"],
            ["employment-stability", "government Stable-public; Self-emp-inc Business-owner; Self-emp-not-inc Self-employed; Private with 35 or more hours Stable-private, otherwise Variable-private; Without-pay or Never-worked Not-employed", "employment security proxy"],
            ["capital-position", "net-capital below 0 Net-loss; 0 No-capital; 1 to 4,999 Moderate-gain; 5,000 or more High-gain", "categorical view of net-capital"],
        ], widths=[1.5, 3.4, 1.6], size=9),
        P("The result has 26 columns: 10 numeric (`age`, `fnlwgt`, `education-num`, `capital-gain`, `capital-loss`, `hours-per-week`, `net-capital`, `capital-intensity` and the two log columns) and 16 categorical. "
          "In the ColumnTransformer, numeric columns receive median imputation (and standard scaling for logistic regression only, because trees are insensitive to scale) and categorical columns receive imputation with the constant "
          "\"Unknown\" followed by one-hot encoding with `handle_unknown=\"ignore\"`, so a category never seen in training cannot crash a request. After encoding the fitted pipeline outputs **145 columns**."),
        CODE(_src("scripts/feature_engineering.py", "def build_preprocessor", "def get_output_feature_names"), 8.5),
        P("The census sampling weight `fnlwgt` describes how many people a record represents and has no meaning for a new user. It is kept as a training feature, as in the original data, and left missing at prediction time, "
          "where the pipeline imputes the training median; its small SHAP importance (0.101) is reported rather than hidden."),
        H2("6.4 Algorithm choice and justification"),
        P(f"Four classifiers span the range used by the base paper {n('base')}: a linear baseline, a bagging ensemble and two boosting ensembles. Tree ensembles are the natural choice for mixed, tabular data with "
          f"interactions and skewed numeric columns, and Grinsztajn et al. {n('grinsztajn')} show that they still outperform deep networks on typical tabular data, which is why no neural network was trained. "
          "Explainability, the fifth objective, favours models for which exact attributions exist, which led to SHAP."),
        TAB("Methods used and the reason for each", ["Method", "Role", "Why chosen", "Known limitation"], [
            [f"Logistic regression {n('hosmer')}", "Interpretable baseline (scaled inputs)", "Coefficients readable; performance floor", "Cannot represent interactions"],
            [f"Random forest {n('breiman')}", "Bagged-tree comparator", "Robust, little tuning, captures non-linearity", "Less accurate than boosting here; large model"],
            [f"Gradient boosting {n('friedman')}", "Boosted-tree comparator (scikit-learn)", "Sequential error correction; strong on tabular data", "Fewer regularisation options than XGBoost"],
            [f"XGBoost {n('xgboost')}", "Primary classifier", "Regularised boosting; best ROC-AUC in this study; exact TreeExplainer support", "Needs care with extrapolation; many hyperparameters (not tuned)"],
            [f"SHAP TreeExplainer {n('shap', 'treeshap')}", "Global and local explanation", "Shapley-value attributions, exact and fast for trees; consistent with the base paper", "Associational, not causal; correlated features share credit"],
            [f"Holt-Winters smoothing {n('winters', 'holt')}", "12-month forecast", "Simple, interpretable trend and seasonality; fits a single monthly series", "Assumes the pattern continues; interval is constant in width"],
            [f"Stratified K-fold {n('stone')}", "Validation", "Keeps the 24% positive share in every fold", "Not entity-aware (unnecessary: one row per person)"],
        ], widths=[1.35, 1.35, 2.2, 1.6], size=8.5),
        P(f"SHAP was preferred to LIME {n('lime')} for the reasons the base paper gives: Shapley values satisfy efficiency, symmetry and additivity, TreeExplainer computes them exactly for tree models, and one method supplies both the "
          f"global ranking and the per-person explanation; comparisons of the two in credit risk {n('gramegna')} and applications to credit decisions {n('bussmann')} point the same way. The base paper's caution also applies here: "
          "SHAP attributions describe what the model relies on, not what would happen if a person changed a value."),
        H2("6.5 Mathematical formulation"),
        P("**Logistic regression** models the log-odds of the positive class as a linear function of the encoded and scaled feature vector x:"),
        EQ("P(y = 1 | x) = 1 / (1 + exp( -(β0 + βᵀx) ))"),
        P("**Gradient boosting** builds an additive model of M shallow trees, each fitted to the gradient of the loss at the current prediction, with learning rate ν. **XGBoost** adds an explicit regularisation term "
          "to the training objective, where T is the number of leaves of a tree and w its leaf weights:"),
        EQ("F(x) = Σ_{m=1..M} ν · f_m(x),     P(y = 1 | x) = 1 / (1 + exp(-F(x)))"),
        EQ("L = Σ_i l(y_i, ŷ_i) + Σ_m Ω(f_m),     Ω(f) = γ·T + ½·λ·‖w‖²"),
        P("In this project λ = 1 (the library default L2 weight written explicitly), the learning rate is 0.05, 400 trees of depth at most 6 are grown, and each tree sees 90% of the rows and 90% of the columns."),
        P("**Shapley values** attribute a prediction to features. For a model f with feature set N of size M, the contribution of feature i is the weighted average of its marginal effect over all feature subsets S:"),
        EQ("φ_i = Σ_{S ⊆ N∖{i}}  [ |S|! (M − |S| − 1)! / M! ] · [ f(S ∪ {i}) − f(S) ]"),
        EQ("f(x) = φ_0 + Σ_{i=1..M} φ_i     (local accuracy; for XGBoost the sum is in log-odds)"),
        P(f"For the selected model the base value φ_0 is -1.1765 in log-odds, about a 24% probability, which is the share of positive records. The global importance of a feature is the mean of |φ_i| over a sample of "
          "500 training rows; the local explanation of one request uses the five largest positive and five largest negative φ_i."),
        P("**Profile mapping.** The predicted probability p of income above 50K is the financial-strength score. It is converted to a profile and a risk band by two fixed cut-offs chosen for this project:"),
        EQ("(profile, risk) = (Established, Low) if p ≥ 0.60;   (Developing, Moderate) if 0.35 ≤ p < 0.60;   (Emerging, High) otherwise"),
        EQ("strength = 100·p,     risk score = 100·(1 − p)"),
        P("**Holt-Winters (additive trend and additive seasonality)** keeps a level ℓ, a trend b and m = 12 seasonal terms s, updated with smoothing weights α, β and γ that are estimated by optimisation:"),
        EQ("ℓ_t = α (y_t − s_{t−m}) + (1 − α)(ℓ_{t−1} + b_{t−1})"),
        EQ("b_t = β (ℓ_t − ℓ_{t−1}) + (1 − β) b_{t−1}"),
        EQ("s_t = γ (y_t − ℓ_{t−1} − b_{t−1}) + (1 − γ) s_{t−m}"),
        EQ("ŷ_{t+h} = ℓ_t + h·b_t + s_{t+h−m(k+1)},     k = ⌊(h − 1)/m⌋"),
        P(f"The 95% band used by the application is ŷ ± 1.96·σ, where σ is the standard deviation of the in-sample residuals ({F.FORECAST['residual_std']}). It is an approximation with constant width, not a full "
          f"prediction interval whose width grows with the horizon {n('hyndmanbook')}. The synthetic series itself is y_t = 100 + 0.35t + 4 sin(2π(month_t − 1)/12) + shock_t + ε_t with ε_t ~ N(0, 1.6²)."),
        P("**Evaluation metrics** are computed from the confusion matrix (TP, FP, TN, FN) of the positive class, income above 50K:"),
        EQ("accuracy = (TP + TN) / (TP + TN + FP + FN);   precision = TP / (TP + FP);   recall = TP / (TP + FN);   F1 = 2·precision·recall / (precision + recall)"),
        EQ("ROC-AUC = P( score(positive) > score(negative) ),   the area under the TPR-versus-FPR curve"),
        P(f"As a check, the selected model's test confusion matrix is TN {cm['tn']:,}, FP {cm['fp']:,}, FN {cm['fn']:,}, TP {cm['tp']:,}, so precision is {cm['tp']:,} / {cm['tp'] + cm['fp']:,} = {F.f4(M['precision'])}, "
          f"recall is {cm['tp']:,} / {cm['tp'] + cm['fn']:,} = {F.f4(M['recall'])} and accuracy is {cm['tn'] + cm['tp']:,} / {F.N_TEST:,} = {F.f4(M['accuracy'])}, matching the stored report. "
          f"ROC-AUC {n('fawcett', 'hanley')} equals the probability that a randomly chosen positive record receives a higher score than a randomly chosen negative one."),
        H2("6.6 Model training and selection"),
        P("Training is performed by `python scripts/train.py`. The four candidates are defined in `scripts/models.py` with fixed hyperparameters and `random_state = 42`; no grid or random search was run, which "
          f"follows the base paper's choice of defaults for reproducibility {n('base')} but means the models may be under-tuned."),
        TAB("Hyperparameters of the four candidate classifiers", ["Model", "Settings"], [
            ["Logistic Regression", "C = 1.0, max_iter 2000; numeric inputs standardised"],
            ["Random Forest", "300 trees, unlimited depth, min_samples_split 2, all cores"],
            ["Gradient Boosting", "scikit-learn defaults (100 trees, depth 3, learning rate 0.1)"],
            ["XGBoost", "400 trees, max_depth 6, learning_rate 0.05, subsample 0.9, colsample_bytree 0.9, reg_lambda 1.0, logloss"],
        ], widths=[1.6, 4.9], size=9.5),
        P(f"Each candidate is wrapped as `Pipeline([preprocess, model])`. The 5-fold stratified cross-validation (shuffled, seed 42) is run on the {F.N_TRAIN:,} training rows with ROC-AUC as the score; the pipeline is then fitted on "
          f"all training rows and evaluated once on the {F.N_TEST:,} test rows at the 0.5 threshold. The best model is the one with the highest **test** ROC-AUC. Selecting on the test split slightly favours the winner and "
          "no separate validation set was held out; the cross-validation ranking is identical, which reduces but does not remove that concern. The time taken to train was not recorded."),
        TAB("Test-split metrics and cross-validated ROC-AUC of the four models", ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "CV ROC-AUC (mean +/- sd)"], _models_table(),
            widths=[1.45, 0.75, 0.75, 0.7, 0.65, 0.75, 1.45], size=9, align=["l", "c", "c", "c", "c", "c", "c"]),
        FIG(F.fig("model_comparison.png"), "The four classifiers compared on the held-out test split", 5.6),
        FIG(F.fig("cv_folds.png"), "ROC-AUC of every cross-validation fold for each model", 4.9),
        P(f"{F.MODEL_LABEL[F.BEST]} leads on every metric, with Gradient Boosting a close second (precision {F.f4(F.COMPARE['gradient_boosting']['precision'])} against {F.f4(F.COMPARE[F.BEST]['precision'])}); the spread between folds is at most {max(F.VALID['cv_roc_auc'][F.BEST]) - min(F.VALID['cv_roc_auc'][F.BEST]):.4f} AUC for XGBoost, "
          "so the ranking is stable across folds. Chapter 8 gives the confusion matrices and the threshold analysis."),
    ]
    return out


def application_blocks():
    env = F.MEAS["environment"]
    lat = F.MEAS["api_latency_ms_127_0_0_1"]
    ex_ok = ('{"ok": true,\n'
             ' "result": {"proba": 0.0109, "strength_pct": 1.1, "risk_pct": 98.9,\n'
             '            "profile": "Emerging", "risk": "High", "model": "xgboost",\n'
             '            "inputs": {...12 fields + education-num...},\n'
             '            "shap": {"available": true, "expected_value": -1.1765,\n'
             '                     "positives": [{"feature": "education-num", "label": "Years of education",\n'
             '                                    "shap": 0.545, "value": 13.0, "sentence": "..."}, ...],\n'
             '                     "negatives": [{"feature": "capital-gain", "shap": -1.6264, ...}, ...]},\n'
             '            "insights": ["...", "..."]}}')
    out = [
        H2("6.7 Application architecture and what-if logic"),
        P("`create_app()` builds the Flask application, reads the session secret from the environment, preloads the persisted pipeline so that the first request is as fast as later ones, and registers the two blueprints. "
          "A failed preload is logged as a warning and the application still starts; `/health` then reports `degraded` and prediction routes return an explanatory error until the model is trained."),
        P("`predict_profile(cleaned)` is the heart of the service. It builds a one-row frame from the validated record, applies `clean_frame` and `add_derived_features`, calls `predict_proba` on the cached pipeline, maps the "
          "probability with `profile_from_proba`, asks `local_shap` for the contributions and `build_insights` for the advice, and returns one dictionary. The TreeExplainer is built lazily on first use "
          "with `feature_perturbation=\"tree_path_dependent\"`, which needs no background data and keeps each request fast."),
        CODE(_src("app/services/predictor.py", "def profile_from_proba", "def local_shap"), 9),
        P("`local_shap` transforms the row with the pipeline's preprocessor, computes SHAP values for the single row, keeps the eight most negative and eight most positive, and returns the five strongest of each sign. Each "
          "item carries a human-readable label and a sentence. One-hot columns need care: for a feature such as `occupation = Sales` a value of 0 means the category does not apply, so the sentence reads "
          "\"absence of occupation = Sales ...\" instead of claiming the opposite. Failures are caught and returned as a note, so an explanation problem never blocks the prediction."),
        P("`build_insights` is rule-based and independent of SHAP: one message per profile, extra messages when weekly hours are below 35, when gains or losses are reported or when education is at or below high-school level, "
          "a sentence quoting up to four SHAP drivers and always a closing disclaimer. Because the rules look only at the inputs, an insight can disagree with the SHAP sign for the same person (for a never-married "
          "39-year-old with gains of 2,174 the rule says gains are a positive signal while SHAP assigns them a contribution of -1.63, because the rule is fixed text keyed on the input and SHAP reflects what the model learned). "
          "This is a known weakness of mixing two explanation sources and is listed as future work."),
        P("**What-if comparison.** `run_whatif(baseline, overrides)` predicts the baseline, copies the record, replaces the overridden fields (investment gains, investment losses, weekly hours, education with its numeric "
          "equivalent), predicts again and reports the change in probability. A change above +0.02 is described as an improvement, below -0.02 as a decline and anything in between as roughly unchanged; the response also "
          "lists the changed fields and whether the profile or risk band changed. The verdict always ends with the warning that this is a model simulation, not a causal prediction. At least one scenario field must be "
          "supplied, and the scenario values obey the same ranges as the form. The React pages keep the baseline in the browser session; the original Flask pages keep it in the Flask session cookie."),
        P("**Forecast service.** `get_forecast()` loads `artifacts/forecast.json` (history, fitted values, 12 forecast points with lower and upper bounds, direction, percentage change and an interpretation sentence) and "
          "returns an `available: false` structure if the file is missing, so the interface degrades gracefully."),
        P("**Front end.** The React application talks to the API through one small client (`lib/api.js`) that wraps `fetch`, converts failures into an `ApiError` carrying the server's message list, and exposes one function per "
          "endpoint. Pages load data with a `useAsync` hook and show a skeleton, an error message or the content. Charts are drawn with Recharts and follow the active theme. In development and preview, Vite proxies "
          "`/api`, `/artifacts` and `/health` to port 8409, so the browser talks to one origin and no cross-origin configuration is needed."),
        H2("6.8 API design"),
        P("All routes are served by Flask on port 8409 (and through the Vite proxy on 5409). JSON routes return `{ok, result}` on success and `{ok: false, errors: [...]}` with status 400 or 500 on failure. "
          "The page routes return HTML and are kept for the original interface."),
        TAB("Endpoints of FinSight AI", ["Method and path", "Request", "Response", "Errors"], [
            ["POST `/api/predict`", "JSON with the 12 assessment fields", "`{ok, result}`: proba, strength_pct, risk_pct, profile, risk, model, inputs, shap, insights", "400 validation list; 500 model missing or failure"],
            ["POST `/api/whatif`", "the 12 fields plus `scenario_capital_gain`, `scenario_capital_loss`, `scenario_hours`, `scenario_education` (at least one)", "`{ok, result}`: baseline, scenario, changed, delta, delta_pct, verdict, profile_changed, risk_changed", "400 for bad input, no scenario field or out-of-range value; 500"],
            ["GET `/api/forecast`", "none", "history, fitted, 12 forecast points with bounds, method, trend, interpretation", "always 200; `available: false` if missing"],
            ["GET `/api/options`", "none", "option lists for the seven dropdowns and the numeric limits", "-"],
            ["GET `/api/dashboard`", "none", "model name, metrics, top-5 SHAP, outlook, training summary", "-"],
            ["GET `/api/explain`", "none", "global SHAP importance (top 15)", "-"],
            ["GET `/api/performance`", "none", "model comparison, validation report, statistics, training summary", "-"],
            ["GET `/health`", "none", "status ok or degraded, model name, model_loaded, forecast_available", "-"],
            ["GET `/artifacts/<name>`", "one of four PNG names", "confusion matrix, ROC, SHAP bar or beeswarm image", "404 for any other name"],
            ["GET, POST `/`, `/assess`, `/explain`, `/forecast`, `/whatif`, `/performance`, `/about`", "form fields for the two POST pages", "server-rendered HTML pages", "400 / 500 re-render the form with messages; 404 page"],
        ], widths=[1.45, 1.75, 2.1, 1.2], size=8.5),
        P("Example of a successful `/api/predict` response for the first record of the Adult file (a 39-year-old state employee with a bachelor's degree, never married, gains of 2,174, 40 hours per week); the arrays are abbreviated:"),
        CODE(ex_ok, 8.5),
        P("Example of a failed request with the age set to -5: HTTP 400 and `{\"ok\": false, \"errors\": [\"Age must be between 16 and 100.\"]}`."),
        H2("6.9 Security and error handling"),
        P("The application is a local research prototype and its security is deliberately modest; the measures that exist are listed together with their limits."),
        B("**Input validation.** `validate_assessment` requires every field, restricts the seven categorical fields to fixed allowed lists and checks the numeric fields for type and range (age 16-100, hours 1-99, gains and losses 0-1,000,000). "
          "Because values are only ever compared with allowed lists or converted to numbers and the application has no database, shell call or template that echoes raw input into code, injection through the form is not a realistic path."),
        B("**Error paths.** Invalid input returns HTTP 400 with every message at once; a missing model file or a failure inside prediction returns 500 with a safe message while the stack trace goes to the log; "
          "unknown URLs and server errors render a friendly error page; the React client shows the first message in a toast and the full list above the form."),
        B("**What is exposed.** `/artifacts/<name>` serves only four whitelisted PNG names; the process binds to 127.0.0.1, so it is reachable only from the same machine; Flask debug mode is off."),
        B("**No personal data is stored.** Inputs are used for one computation; the what-if baseline is held in the browser session (React) or the signed Flask session cookie (original pages)."),
        B("**Demo login.** The sign-in gate is client-side and its credentials are shown on the login page. It is not authentication and protects nothing; real accounts, hashed passwords and server-side sessions are future work."),
        B("**Secrets.** The Flask secret key is read from `FINSIGHT_SECRET_KEY` and falls back to a fixed development value, which must be replaced in any shared deployment."),
        B("**Transport and abuse.** Traffic is plain HTTP on localhost, there is no rate limiting, and the Flask development server is not meant for production; a WSGI server and a reverse proxy with TLS would be required."),
        H2("6.10 Installation and execution"),
        P(f"The project needs Python 3.11 or newer and Node.js 18 or newer. The measured environment was {env['os']}, {env['cpu']}, {env['ram_gb']} GB RAM, Python {env['python']}, scikit-learn {env['scikit-learn']}, "
          f"XGBoost {env['xgboost']}, SHAP {env['shap']}, statsmodels {env['statsmodels']}, Flask {env['flask']} and Node {env['node']}; no GPU is used. `requirements.txt` lists 12 packages (pandas, numpy, scikit-learn, xgboost, shap, statsmodels, Flask, "
          "joblib, matplotlib, pytest, requests and fpdf2)."),
        P("**Automatic.** Double-clicking `run.bat` reads the ports from `.env` (API 8409, front end 5409), creates `.venv`, installs the requirements, trains the models if `models/best_model.pkl` is missing, runs `npm install` and "
          "`npm run build` on the first run, starts the API in a second window, opens the browser and serves the built front end with `npm run preview`."),
        P("**Manual.**"),
        CODE("python -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt\npython scripts\\train.py        # only if models\\best_model.pkl is missing\npython run.py                   # API on http://localhost:8409\n\n"
             "cd frontend\nnpm install\nnpm run dev                     # http://localhost:5409 (proxies /api to 8409)\n# production-style:  npm run build  then  npm run preview", 9),
        P("Sign in with the sample account `demo@finsight.ai` and password `finsight123` (the login page has a button that fills them). The original server-rendered pages remain available at http://localhost:8409."),
        P(f"**Checks.** `pytest` runs {F.MEAS['pytest']['passed']} tests (seven in `tests/test_app.py` covering health, page loading, input-dependent predictions, validation errors, the JSON API, the what-if route and artifact presence, "
          f"and two in `tests/test_features.py` covering the derived features and missing-value handling) in about {F.MEAS['pytest']['seconds']:.0f} seconds. With both servers running, `python scripts/smoke_test.py` "
          f"performs {F.MEAS['smoke_test']['total']} live checks of the API and the proxy, and `python scripts/capture_screens.py` walks every screen with Playwright and fails on any console error. A single prediction takes "
          f"a median of {lat['POST /api/predict']['median']:.1f} ms (95th percentile {lat['POST /api/predict']['p95']:.1f} ms) and a what-if comparison {lat['POST /api/whatif']['median']:.1f} ms when measured on 127.0.0.1 over 40 calls."),
    ]
    return out


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
