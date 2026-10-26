"""Chapter 6: Methodology and Software Implementation for TrendCast.

methodology_blocks() is also rendered (renumbered) by document 9, application_blocks() by document 12; blocks() is the report chapter.
Numbers come from facts.py (experiments/**/metrics.json); formulas are exactly what src/*.py computes.
"""

import os

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .diagram_index import DIAGRAMS
from .refs import N as cite

_D = {k: (t, f, cap) for k, t, f, cap, _ in DIAGRAMS}


def _dg(key, caption=None, width=5.4):
    t, f, cap = _D[key]
    path = F.diag(f)
    return [FIG(path, caption or cap, width)] if os.path.exists(path) else []


def _fg(name, caption, width=5.6):
    path = F.fig(name)
    return [FIG(path, caption, width)] if os.path.exists(path) else []


def _m(model, key="RMSE", d=2):
    return f"{F.fm(model, key):.{d}f}"


def methodology_blocks():
    ds, fc = F.DS, F.FC
    seed = fc["xgboost_seed_stats"]
    dup = ds["raw_rows"] - ds["clean_rows"]
    abl = fc["ablation"]
    tuned = fc["tuned_best_params"]
    nm = F.pair("Knitwear")
    on = F.pair("Online")
    b = []

    # ------------------------------------------------------------------ 6.1
    b += [H2("6.1 Overall methodology"),
          P(f"TrendCast treats demand forecasting as a supervised regression on a daily panel: one row per article per day, with the number of units sold as the target. "
            f"The base paper {cite('base')} follows the same recipe with LightGBM on the UCI Online Retail II data and adds four layers of explanation; TrendCast keeps the recipe, uses XGBoost {cite('xgb')} as the batch abstract specifies, "
            f"and adds the step the base paper leaves out: moving a trained model between differently distributed parts of the business. The method has eight steps."),
          N("**Ingest.** Read the transactions and articles files (customers optional), check that the required columns exist and stop with a plain message if they do not.",
            "**Clean and merge.** Parse dates, remove unusable rows, left-join the product attributes so that no sale is lost because a catalogue entry is missing.",
            "**Aggregate.** Count the transactions of each article on each day (the demand), average the price, take the most frequent sales channel, and fill the days without a sale with zero.",
            "**Engineer features.** Add calendar, cyclical, lag, rolling and encoded attribute features, all computed only from the past.",
            "**Split by date.** The earliest 80 % of the dates train the model, the latest 20 % test it; tuning uses time-ordered folds.",
            "**Fit and compare.** Fit the moving-average baseline and XGBoost (optionally tuned) and report RMSE, MAE, safe MAPE and R2.",
            "**Adapt across domains.** Choose a domain column, a source value and a target value; train on the source, test on the later half of the target, estimate importance weights with a domain classifier, retrain with the weights and report the change.",
            "**Forecast and explain.** Roll the model forward 7, 14 or 30 days, show gain-based feature importance, and optionally ask Gemini to put the numbers in words."),
          *_dg("flow_algo", None, 5.2)]

    # ------------------------------------------------------------------ 6.2
    b += [H2("6.2 Dataset"),
          P(f"All measurements use the **H&M Personalized Fashion Recommendations** data {cite('hm')}: 31,788,324 transactions, 105,542 articles and 1,371,980 customers according to the dataset card of the parquet mirror we downloaded. "
            "The files are used under the competition's academic terms and are not redistributed in the repository. "
            f"Because the whole file is too large for the machine used (15.7 GB of memory, no GPU), we took the first transaction shard (4,541,190 rows from 2018-09-20 to 2019-01-04, 42,415 articles) "
            f"and kept the **300 best-selling articles** with all of their transactions: {ds['raw_rows']:,} rows over {ds['date_min']} to {ds['date_max']} (107 days), {ds['customers']:,} customers. "
            "`scripts/make_real_subset.py` rebuilds this subset in the exact CSV schema the application expects."),
          TAB("The real subset used for every reported number.",
              ["Quantity", "Value"],
              [["Transaction rows read", f"{ds['raw_rows']:,}"],
               ["Rows after cleaning", f"{ds['clean_rows']:,} ({dup:,} exact duplicates removed, {dup / ds['raw_rows'] * 100:.1f} %)"],
               ["Articles / customers", f"{ds['articles']} / {ds['customers']:,}"],
               ["Date range", f"{ds['date_min']} to {ds['date_max']} (107 days)"],
               ["Rows per channel (cleaned)", f"channel 1: {ds['channel_rows_raw']['1']:,}; channel 2: {ds['channel_rows_raw']['2']:,}"],
               ["Article-days with a sale", f"{ds['daily_rows']:,}"],
               ["Modelling rows after zero-filling", f"{ds['feature_rows']:,} ({ds['zero_demand_share_pct']:.2f} % zero demand)"],
               ["Model inputs", f"{ds['feature_cols']}"],
               ["Chronological split", f"train {fc['split']['train_rows']} rows (to {fc['split']['train_end'][:10]}), test {fc['split']['test_rows']} rows ({fc['split']['test_start'][:10]} to {fc['split']['test_end'][:10]})"]],
              widths=[2.4, 4.1], align=["l", "l"], size=10),
          P("Three properties of this subset shape every result. It covers only **107 days**, so no yearly seasonality can be learned; the test window contains the Christmas peak and the January sales, which the training window has never seen. "
            "It contains the **best-selling** articles, so zero-demand days are rare (2 %), whereas the full catalogue is intermittent. And the two sales channels are coded 1 and 2 in the files without a name; "
            "we call them channel 1 and channel 2 and use 'store' and 'online' in a few labels only as our own convention, which the data do not state. "
            "A synthetic file in the same schema (`data/sample_hm`, 90 articles) ships for smoke tests; no reported metric uses it.")]

    # ------------------------------------------------------------------ 6.3
    b += [H2("6.3 Preprocessing"),
          P("Preprocessing is implemented in `src/preprocessing.py` and `src/demand_forecasting.py` and is applied identically in the web application, the Streamlit application and the experiment script."),
          H3("6.3.1 Cleaning and merging"),
          P("`clean_transactions` parses `t_dat` to a date (invalid dates become missing), drops rows without a date, article id or customer id, keeps only rows with a positive numeric price, removes exact duplicate rows and sorts by date. "
            "`clean_articles` fills missing text attributes with `Unknown` rather than dropping the product, and `clean_customers` fills a missing age with the median. "
            "`merge_datasets` left-joins articles (and customers) onto the transactions, so a transaction whose article is absent from the catalogue survives with `Unknown` attributes. "
            "The data-quality report counts rows read and kept, missing values, duplicates, customers, products and the date range; the upload page shows it."),
          P(f"One cleaning rule deserves a warning. Removing exact duplicates dropped **{dup:,} rows ({dup / ds['raw_rows'] * 100:.1f} %)** of the subset. In the H&M file a repeated identical row is usually a customer buying two units of the same article on the same day, "
            "so the rule understates demand slightly and flattens the largest days. We kept the rule because it is part of the shipped pipeline and applied it in every experiment; Chapter 9 lists it among the limitations."),
          H3("6.3.2 From transactions to daily demand"),
          P("`aggregate_daily_demand` groups the cleaned rows by date and article. The **demand** is the number of rows, since each row is one unit sold; the **price** is the mean price of that day; the **sales channel** is the most frequent channel of that day; "
            "and the article's descriptive attributes are carried along from the first non-null value. `fill_missing_dates_per_article` then re-indexes each article onto a continuous daily range between its first and last sale, sets the missing demand to zero and forward- and back-fills price, channel and attributes. "
            "Articles with fewer than five sale-days are skipped by this function and therefore leave the modelling table; none of the 300 subset articles is affected."),
          P("Two consequences follow from using the day's mean price and modal channel. Both are computed from the very transactions that make up the target, so they are not strictly known before the day, and on a zero-demand day they are copied from a neighbouring day. "
            "We treat price as a planned input and report this as a limitation rather than silently excluding it; the ablation in Section 6.5 shows what it is worth. "
            "The channel is also a mixture: demand counts units from both channels, while the label is only the day's majority channel.")]

    # ------------------------------------------------------------------ 6.4
    b += [H2("6.4 Feature engineering"),
          P(f"`build_feature_table` produces the {ds['feature_cols']} model inputs in four groups. The calendar, lag and rolling groups follow the same temporal-integrity rule as the base paper {cite('base')}: a feature of day t may use only information from day t-1 and earlier."),
          TAB("The 31 model inputs.",
              ["Group", "Inputs", "Count"],
              [["Price and channel", "price, sales_channel_id", "2"],
               ["Product attributes (label-encoded)", "product_type, product_group, colour_group, department, section, garment_group", "6"],
               ["Calendar", "year, month, day, day_of_week, week_of_year, day_of_year, quarter, is_weekend, is_month_start, is_month_end, month_sin, month_cos, dow_sin, dow_cos", "14"],
               ["Lag and rolling (past demand of the same article)", "lag_1, lag_7, lag_14, lag_28, rolling_mean_7/14/28, rolling_std_7/28", "9"]],
              widths=[2.0, 3.9, 0.6], align=["l", "l", "c"], size=9.5),
          P("**Cyclical encoding.** Month and weekday are also given as a sine and cosine pair so that December and January, or Sunday and Monday, are neighbours; a tree model cannot infer this from the raw integer. "
            "**Lags.** `lag_k` is the article's demand k days earlier, computed with `groupby(article).shift(k)`. **Rolling statistics.** The demand is shifted by one day first and the window is applied afterwards, so the current day never enters its own mean or standard deviation. "
            "Rows without enough history take the value 0, which a tree reads as 'nothing observed'. **Attributes.** Text attributes are converted to integer codes with a stored mapping (one-hot would create hundreds of columns for the department and colour fields), "
            "which treats the codes as ordered numbers; trees cope with this, but the codes carry no meaning in themselves."),
          P("The domain-adaptation route removes the chosen domain column from this list, so a model or classifier cannot read the domain from a feature. The same list, saved as `models/feature_info.joblib`, is used to rebuild the input of a loaded model.")]

    # ------------------------------------------------------------------ 6.5
    b += [H2("6.5 Algorithm choice and justification"),
          P(f"The batch abstract names XGBoost as the learner, and the choice is easy to defend on engineering grounds: it handles mixed numeric and encoded features without scaling, trains in about a second on this table, "
            f"has regularisation built in {cite('xgb')} and, decisively for this project, accepts a per-row `sample_weight`, which is the entry point for domain adaptation. "
            f"Gradient boosting {cite('gbm')} also matched or beat deep learning in the M5 retail competition when given engineered features {cite('m5')}, which is the base paper's argument for its own choice."),
          P("Whether it is also the *most accurate* choice on our data is a separate, measured question. All learners below use the same 31 inputs and the same 80/20 split; the first four rows need no training."),
          TAB("Model comparison on the real subset (test window 2018-12-14 to 2019-01-04, 6,515 rows).",
              ["Model", "RMSE", "MAE", "R2", "WAPE %"],
              [[k, f"{v['RMSE']:.3f}", f"{v['MAE']:.3f}", f"{v['R2']:.3f}", f"{v['WAPE (%)']:.1f}"] for k, v in fc["models"].items()],
              widths=[2.9, 0.9, 0.9, 0.9, 0.9], align=["l", "r", "r", "r", "r"], size=9.5),
          *_fg("f01_model_comparison.png", "Test RMSE of every forecaster on the real H&M subset (XGBoost default: mean of five seeds with standard deviation)."),
          P(f"Three readings follow. **Gradient boosting beats the product's own baseline**: XGBoost reaches RMSE {_m(F.XGB)} against {_m(F.MA)} for the 7-day moving average, and {_m(F.XGB_T)} when tuned. "
            f"**Seed noise is small** (RMSE {seed['RMSE']['mean']:.3f} ± {seed['RMSE']['std']:.3f} over five seeds), so differences of more than about 0.1 are real. "
            f"**A one-line baseline is better still**: repeating yesterday's demand gives RMSE {_m('Naive (lag 1)')} and the shifted 7-day mean {_m('Rolling mean 7 (shifted)')}. "
            f"The base paper reports the same ordering of difficulty: its LightGBM beats a 7-day moving average by 2.86 RMSE but its naive lag-1 baseline is far worse on its much more intermittent SKU data {cite('base')}. "
            "On our best-selling articles, demand is smooth enough that yesterday is a strong predictor."),
          P("The ablation explains why. We refit XGBoost with groups of features removed (three seeds each)."),
          TAB("Feature-group ablation (XGBoost default, mean of three seeds).",
              ["Feature set", "Inputs", "RMSE", "R2", "WAPE %"],
              [[k, str(v["n_features"]), f"{v['RMSE']:.3f}", f"{v['R2']:.3f}", f"{v['WAPE (%)']:.1f}"] for k, v in abl.items()],
              widths=[2.6, 0.7, 0.9, 0.9, 0.9], align=["l", "c", "r", "r", "r"], size=9.5),
          P(f"The lag and rolling features carry the model: without them R2 falls to {abl['no lag / rolling']['R2']:.2f}, and calendar features alone are worse than predicting the mean of the test window. "
            f"The most striking row is the last but one: **a model that uses only the nine lag and rolling inputs (RMSE {abl['lag / rolling only']['RMSE']:.2f}) is better than the shipped 31-input model (RMSE {abl['all features (as shipped)']['RMSE']:.2f})**. "
            "The extra inputs include absolute-time features (year, quarter, day_of_year, month) whose test values lie beyond the training range; a tree can only predict the value of the last leaf it has seen for them. "
            "This agrees with the base paper's ablation, in which rolling statistics were the dominant group. We kept the shipped feature set for the product because changing it was outside the scope of a documentation run, and we report the better variant as a finding in Chapter 8."),
          *_fg("f02_ablation.png", "Feature-group ablation: lag and rolling inputs carry the forecast; the calendar group alone is not enough.", 5.4)]

    # ------------------------------------------------------------------ 6.6
    b += [H2("6.6 Mathematical formulation"),
          H3("6.6.1 Features"),
          P("Let y(a, t) be the units of article a on day t. The lag, rolling and cyclical features are"),
          EQ("lag_k(a, t) = y(a, t - k),   k in {1, 7, 14, 28}"),
          EQ("rolling_mean_w(a, t) = (1/w) * sum_{i=1..w} y(a, t - i),   w in {7, 14, 28}"),
          EQ("month_sin = sin(2*pi*month/12),   month_cos = cos(2*pi*month/12),   dow_sin = sin(2*pi*dow/7),   dow_cos = cos(2*pi*dow/7)"),
          P("The rolling standard deviation uses the same window over the shifted series (windows 7 and 28). Because every sum starts at i = 1, y(a, t) never appears in its own features."),
          H3("6.6.2 The XGBoost objective"),
          P(f"XGBoost {cite('xgb')} builds an additive ensemble of K regression trees, y_hat = sum_k f_k(x), by minimising a regularised squared-error objective. With per-row weights w_i, as used for domain adaptation, the objective is"),
          EQ("L = sum_i w_i * (y_i - y_hat_i)^2 + sum_k [ gamma * T_k + (lambda/2) * ||v_k||^2 ]"),
          P("where T_k is the number of leaves of tree k and v_k its leaf values (library defaults gamma = 0 and lambda = 1). For squared error the second derivative of each row's loss is proportional to w_i, "
            "so the sum of the second derivatives in a candidate leaf is the sum of the weights in it. XGBoost refuses a split whose child has a derivative sum below `min_child_weight`, which is 1 by default. "
            "This detail looks technical but it decides what happens when the weights are tiny (Section 6.8)."),
          H3("6.6.3 Importance weights for covariate shift"),
          P(f"Under covariate shift the inputs have different densities in the source (p_S) and target (p_T) domains but the relation between inputs and demand is the same. Training on the source with each row weighted by w(x) = p_T(x) / p_S(x) then minimises the target risk {cite('shim')}. "
            f"The ratio is not estimated directly. A classifier is trained to tell source rows (label 0) from target rows (label 1) {cite('bickel')}; by Bayes' rule its output p(x) = P(target | x) satisfies"),
          EQ("p(x) / (1 - p(x)) = [ p_T(x) / p_S(x) ] * [ n_T / n_S ]"),
          P("where n_S and n_T are the numbers of source and target rows the classifier saw. TrendCast uses the odds themselves as the weight, clipped to avoid a few dominating rows:"),
          EQ("w(x) = min( p(x) / (1 - p(x)), 20 ),   with p clipped to [1e-6, 1 - 1e-6]"),
          P(f"The odds therefore equal the density ratio **times n_T / n_S**: the weights are not normalised to a mean of one. This is visible in the data: for the pair channel 2 to channel 1 the mean weight was {on['diagnostics']['w_mean']:.3f} and n_T / n_S = 12,240 / 18,854 = 0.649. "
            "When the two classes are of similar size the factor is harmless; when the classifier separates the domains perfectly the odds become tiny and the factor no longer matters, because the weights are tiny anyway."),
          H3("6.6.4 Metrics"),
          EQ("RMSE = sqrt( (1/n) * sum (y_i - y_hat_i)^2 ),   MAE = (1/n) * sum |y_i - y_hat_i|"),
          EQ("safe-MAPE = (100/m) * sum_{y_i != 0} |y_i - y_hat_i| / |y_i|,   R2 = 1 - sum (y_i - y_hat_i)^2 / sum (y_i - mean(y))^2"),
          P(f"Safe MAPE skips the rows with zero demand (there are {fc['models'][F.MA]['MAPE_excluded_zero_rows']:.0f} in the test window) and reports their number. Even so it is very large here (about 140 %) because low-volume days dominate a ratio of errors, "
            f"so it is a poor guide on its own and we add the weighted absolute percentage error WAPE = sum|y - y_hat| / sum y (offline), which divides by total units and is stable {cite('mase')}. "
            "The improvement from adaptation is (before - after) / before for the error metrics, so a negative value means the adapted model is worse.")]

    # ------------------------------------------------------------------ 6.7
    b += [H2("6.7 Model architecture and training"),
          *_dg("model", None, 5.2),
          P("The model is a single `XGBRegressor`. Its defaults, set in `xgboost_model.DEFAULT_PARAMS`, are 300 trees, depth 8, learning rate 0.05, row and column subsampling of 0.8, squared-error objective and random state 42. "
            f"On this table a fit takes {fc['xgboost_fit_seconds_mean']:.1f} s and a prediction {fc['xgboost_prediction_us_per_row']:.1f} microseconds per row on the CPU."),
          P(f"**Tuning** is optional. `tune_xgboost` runs `RandomizedSearchCV` {cite('bergstra')} over six parameters (n_estimators 100-500, max_depth 4-12, learning_rate 0.01-0.2, subsample and colsample_bytree 0.6-1.0, min_child_weight 1-7), "
            f"with ten sampled settings, three `TimeSeriesSplit` folds (each validation fold lies after its training fold) and negative RMSE as the score; scikit-learn {cite('sk')} supplies the search. "
            f"The tuned model chose {tuned['n_estimators']} trees of depth {tuned['max_depth']}, learning rate {tuned['learning_rate']}, subsample {tuned['subsample']}, column sample {tuned['colsample_bytree']} and min_child_weight {tuned['min_child_weight']}; "
            f"the search took {fc['tuning_seconds']:.0f} s and improved the test RMSE from {_m(F.XGB)} to {_m(F.XGB_T)}. The training page shows the winning parameters."),
          P("**Baselines.** The moving average predicts each test row with the article's mean over the last seven training days, falling back to the article mean and then the global mean. "
            "A random forest (200 trees, depth 10) and LightGBM (300 trees, depth 8) are available as optional comparators. The trained default model is saved to `models/baseline_xgboost.joblib` together with its feature list.")]

    # ------------------------------------------------------------------ 6.8
    b += [H2("6.8 Domain adaptation procedure"),
          *_dg("flow_da", None, 5.2),
          P("The procedure is implemented in `backend/main.py::run_domain` using the functions of `src/domain_adaptation.py`. The analyst chooses one of three domain columns (sales channel, product group, department) and two different values. The steps are:"),
          N("Remove the domain column from the model inputs. Split the feature table into **source rows** (all dates) and **target rows**.",
            "Hold out the **later half of the target dates** as the test set; the earlier half is not used for fitting in the product.",
            "Train XGBoost on the source rows only and score the target test rows: the **before** metrics.",
            "Fit a logistic regression that separates source from target rows (25 % of the stacked rows are held out to report its accuracy; the accuracy measures how different the domains are). The target rows given to the classifier include the test dates, but only their inputs, never their demand.",
            "Compute the importance weight of each source row as p / (1 - p), clipped to [0, 20].",
            "Retrain XGBoost on the source rows with those weights and score the same test rows: the **after** metrics. Save the model and report the change in RMSE, MAE, MAPE and R2."),
          P("The experiments of Chapter 8 repeat this procedure for six source-target pairs with five XGBoost seeds each and add controls that the product does not have: a target-only model trained on the first half of the target; "
            "a pooled model trained on the source plus the first half of the target without weights; the same weights shuffled randomly; the weights rescaled to a mean of one; and a 'time-clean' variant in which the source rows are limited to dates before the target test window."),
          P(f"Reading the procedure against the controls produced two implementation findings that we report as facts. First, **the source model is trained on dates that overlap the target test window**; for the channel pair the gain of {on['app']['rmse_improvement_pct_mean']:+.1f} % turned into {on['time_clean']['rmse_improvement_pct_mean']:+.1f} % when the overlap was removed. "
            f"Second, **the weights are not normalised**: for the department pair Knitwear to Trouser the classifier is perfectly accurate, the mean weight is {nm['diagnostics']['w_mean']:.1e}, no split can reach min_child_weight = 1 (Section 6.6.2), "
            f"XGBoost stops splitting and predicts a constant, and the RMSE gets {-nm['app']['rmse_improvement_pct_mean']:.0f} % worse. Rescaling the same weights to a mean of one removed the collapse. "
            "Logistic regression is also fitted to unscaled features and does not reach convergence within 1,000 iterations, which scikit-learn reports as a warning on every run. None of these was changed in the product during this documentation; Chapter 8 gives the measurements and Chapter 10 the fixes.")]
    return b


def application_blocks():
    api = F.API
    st = api["stages_seconds"]
    lat = api["latency_ms"]
    b = []

    b += [H2("6.9 Application architecture"),
          P(f"The product exists in two front ends over one pipeline. The **Streamlit** application (`app.py`, 597 lines, 11 pages) is the original and is left unchanged. The **web application** has a FastAPI back end (`backend/main.py`, port {F.API_PORT}) and a React 19 front end built with Vite (port {F.WEB_PORT}). "
            "Both import the same `src/` modules, so a number computed in one is computed identically in the other."),
          *_dg("arch", None, 5.4),
          P("The back end is organised around one idea: **a route does only HTTP work**. It checks that the required state exists (the helper `need` raises a 409 with an instruction), validates the request with a pydantic model, takes the lock, calls the `src/` function, stores the result in the shared state `S`, and converts the result to JSON with `clean`, "
            "which turns NaN and infinity into null and dates into ISO strings so that the browser never receives invalid JSON. The helper below is the gate used by every downstream route."),
          CODE("def need(key: str, message: str):\n"
               "    \"\"\"Return S[key] or raise a 409 with a plain-language 'do this first' message.\"\"\"\n"
               "    value = S.get(key)\n"
               "    if value is None or (isinstance(value, pd.DataFrame) and value.empty):\n"
               "        raise HTTPException(status_code=409, detail=message)\n"
               "    return value", 8.5),
          P("The front end reads progress from `/api/state` through a context provider and renders each page inside a gate. Pages call the API through one fetch wrapper that turns FastAPI error details into readable messages and reports status 0 when the server cannot be reached ('Cannot reach the TrendCast API. Start the backend (run.bat) and retry.'). "
            "Charts use Recharts; the layout, theme toggle, toasts and tables come from a small in-house UI kit.")]

    b += [H2("6.10 API design"),
          P("Chapter 5 lists the 22 routes. This section shows the shape of the most important exchange, domain adaptation. The request is a three-field JSON document; the response carries everything the page draws, so the page makes one call and no further computation happens in the browser."),
          CODE("POST /api/domain/run\n"
               "{ \"domain_col\": \"sales_channel_id\", \"source\": 1, \"target\": 2 }\n\n"
               "200 OK\n"
               "{ \"source_label\": \"Channel 1\", \"target_label\": \"Channel 2\",\n"
               "  \"source_rows\": 12240, \"target_rows\": 18854, \"target_test_rows\": 9890,\n"
               "  \"classifier_accuracy\": 0.663,\n"
               "  \"shift\": [ {\"feature\": \"lag_1\", \"source_mean\": ..., \"target_mean\": ..., \"mean_diff\": ...}, ... 15 rows ],\n"
               "  \"top_shift_feature\": \"lag_1\", \"histogram\": [...30 bins...], \"box\": {...},\n"
               "  \"weights\": {\"mean\": 1.58, \"max\": 20.0, \"min\": 0.10},\n"
               "  \"before\": {\"RMSE\": 18.983, ...}, \"after\": {\"RMSE\": 18.989, ...},\n"
               "  \"report\": [ {\"Metric\": \"RMSE\", \"Before Adaptation\": ..., \"After Adaptation\": ..., \"Improvement (%)\": ...}, ... ] }", 8.5),
          P("The values shown are those of the capture run on the real subset: the adapted model's RMSE (18.989) is marginally worse than the source model's (18.983), and the interface labels that as '0.0 % worse' instead of rounding it into a success. "
            "The forecast route follows the same pattern: the request is `{article_id, horizon}` and the response holds the last 60 days of history, the forecast rows, their sum and the number of history days used."),
          P(f"**Measured behaviour** (real subset, 127.0.0.1, other jobs running on the same machine): upload, clean and merge {st['upload+clean+merge (684k rows)']:.1f} s; daily aggregation {st['explore (aggregate daily)']:.1f} s; feature building {st['build features']:.1f} s; "
            f"default XGBoost {st['train XGBoost (default)']:.1f} s; tuned XGBoost {st['train XGBoost (tuned)']:.1f} s; domain adaptation {st['domain adaptation run']:.1f} s. "
            f"Median latency of the forecast route over 20 calls is {lat['POST /api/forecast (7 d)']['median']:.0f} ms (7 days), {lat['POST /api/forecast (14 d)']['median']:.0f} ms (14 days) and {lat['POST /api/forecast (30 d)']['median']:.0f} ms (30 days); "
            f"the lightweight routes answer in about {lat['GET /api/state']['median']:.0f} ms. The forecast time grows linearly with the horizon because each day is one model call."),
          *_fg("f12_api_latency.png", "Measured pipeline stage times and median endpoint latency (real H&M subset, 127.0.0.1).", 5.4)]

    b += [H2("6.11 Security and error handling"),
          P("TrendCast is a single-user analysis tool and its security model is correspondingly simple. We list what exists and what does not, so that nobody assumes more."),
          B("**No authentication or accounts.** Anyone who can reach port 8317 can use the tool and read the shared state. This is acceptable on a student's machine and unacceptable on a server; it is listed in Chapter 9.",
            "**CORS** allows only `http://localhost:5317` and `http://127.0.0.1:5317`, so a page from another origin cannot call the API from a browser.",
            "**Input validation.** Uploads must contain the required columns (`t_dat`, `customer_id`, `article_id`, `price` for transactions; `article_id`, `prod_name` for articles) or the route answers 400 with the missing names; empty and unreadable files answer 400; the training fraction is limited to 0.5-0.95 by the request model; the horizon must be 7, 14 or 30; the domain column must be one of three offered names.",
            "**Secrets.** The Gemini key is read from `.env`, which is git-ignored (and `.streamlit/secrets.toml` for the Streamlit app). The repository contains only `.env.example`. `.env.example` also lists `DATABASE_URL` and `JWT_SECRET`, which this code does not use because there is neither a database nor a login.",
            "**Data sent to the outside.** Only the optional AI Insights route contacts an external service. Its context is built by `gemini_helper.build_context_summary` from the metric dictionary, the top ten feature importances, the domain-shift summary and a forecast summary; raw rows are never included. The prompt tells the model to use only that data.",
            "**Failure behaviour.** Missing prerequisites answer 409 and a missing saved model 404. If Gemini is not configured the route answers 503; if the call fails or times out the route answers 502 with a message that every other page still works. During our screenshot run the service answered 503 ('high demand') and later timed out; the page showed the message and nothing else broke.",
            "**Concurrency.** A re-entrant lock serialises routes that read or change the pipeline tables, so two requests cannot interleave a split or a model assignment. The state itself is global, so two users share it."),
          P("The automated tests cover the gating, the validation messages, the reset-on-upload rule and the AI-not-configured path (Chapter 7).")]

    b += [H2("6.12 Installation and execution"),
          P("The project needs Python 3.10 or newer and Node.js 18 or newer. `requirements.txt` lists streamlit, pandas, numpy, scikit-learn, xgboost, lightgbm, plotly, joblib, python-dateutil, google-generativeai, fastapi, uvicorn, python-multipart and requests. "
            "Measurements in this report were taken with Python 3.11.9, scikit-learn 1.5.0, XGBoost 2.0.3, LightGBM 4.7.0, pandas 2.2.1 and NumPy 1.26.4 (LightGBM was installed only for the baseline comparison)."),
          N("Open the project folder `8.ProjectCode`. Copy `.env.example` to `.env`; ports 8317 and 5317 are preset, and the Gemini key is optional.",
            "Run `run.bat`. It reads the ports from `.env`, creates `.venv` if it is absent, installs `requirements.txt` once (a marker file avoids repeating it), runs `npm install` in `frontend/` if needed, starts the back end with uvicorn and the front end with Vite in two console windows, and opens the browser at http://localhost:5317.",
            "Open **Data upload**, choose the transactions and articles CSV (customers optional), set the row limit (0 means no limit) and press 'Load & process data'. Then follow the pages in order; each one tells you if a step is missing.",
            "To check the installation run `run.bat test`: it starts the back end, creates the synthetic sample if needed and runs `scripts/smoke_test.py` (26 checks). `python -m pytest tests -q` runs the 39 unit and API tests.",
            "To use the original Streamlit application instead, run `streamlit run app.py`; to rebuild the real-data subset, run `scripts/make_real_subset.py` on the downloaded H&M files."),
          P("Appendix B gives the same instructions as a user guide with the screens. Two practical notes: a fresh environment may install newer package versions than those listed above, which is why the scikit-learn and XGBoost versions are recorded; "
            "and the first start of `run.bat` takes several minutes because of the package downloads.")]
    return b


def _trim(bl):
    """Report variant: the diagrams already appear in Chapter 5 and the result charts in Chapter 8, so only the text and tables are kept."""
    out = []
    for b in bl:
        if b[0] == "fig" and (os.sep + "diagrams" + os.sep in b[1] or os.path.basename(b[1]).startswith(("f01", "f02", "f12"))):
            continue
        out.append(b)
    return out


def blocks():
    bl = [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
    return _trim(bl) if F.REPORT else bl
