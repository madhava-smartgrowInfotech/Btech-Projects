"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, EQ, H1, H2, N, P, TAB
from .refs import N as C


def trim(blocks, drop=(), drop_sections=(), replace=None, table_rows=None):
    """Report-mode trimming helper (shared by the other chapter modules). drop: block-text prefixes to remove; drop_sections: heading
    prefixes whose whole section is removed; replace: {prefix: block}; table_rows: {caption prefix: keep(row)}."""
    replace = replace or {}
    table_rows = table_rows or {}
    out, skip_level = [], None
    for b in blocks:
        if b[0] in ("h1", "h2", "h3"):
            lvl = int(b[0][1])
            if skip_level is not None and lvl <= skip_level:
                skip_level = None
            if skip_level is None and any(b[1].startswith(x) for x in drop_sections):
                skip_level = lvl
        if skip_level is not None:
            continue
        v = b[1]
        k = v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else "")
        if any(k.startswith(x) for x in drop):
            continue
        hit = next((x for x in replace if k.startswith(x)), None)
        if hit:
            if replace[hit] is not None:
                out.append(replace[hit])
            continue
        if b[0] == "tab":
            cap = next((x for x in table_rows if b[1].startswith(x)), None)
            if cap:
                b = ("tab", b[1], b[2], [r for r in b[3] if table_rows[cap](r)], b[4], b[5], b[6])
        out.append(b)
    return out


def blocks():
    ds, fc, dom = F.DS, F.FC["models"], F.DOM
    xgb, ma, lag1 = fc[F.XGB]["RMSE"], fc[F.MA]["RMSE"], fc["Naive (lag 1)"]["RMSE"]
    on = F.pair("Online")
    dup = ds["raw_rows"] - ds["clean_rows"]
    out = [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Introduction to the Project Domain"),
        P("Fashion retail is one of the hardest settings for demand forecasting. A garment is designed, produced and sold within a season or two, so most articles have a short life; "
          "demand follows the calendar (weekday, month, holidays, sales periods) and the weather; prices and promotions move demand; and every new collection puts articles on the shelf that have no sales history at all. "
          "A retailer that forecasts too high is left with unsold stock that must be marked down; one that forecasts too low loses the sale and the customer. "
          "Demand forecasting, the task of predicting how many units of each product will sell on each future day, is therefore the input to purchasing, allocation to stores and channels, and replenishment."),
        P("Two families of tools are used. Classical statistical methods such as exponential smoothing and ARIMA describe each series with a few parameters and are easy to explain, but they assume smooth, stationary behaviour "
          f"that promotions and holidays routinely break. Machine-learning methods treat forecasting as supervised learning on a table of engineered features, and gradient-boosted decision trees {C('gbm', 'xgb', 'lgbm')} "
          f"have become the standard tool for such tables: in the large M5 retail forecasting competition, entries built on boosted trees with hand-made features were among the best {C('m5')}. "
          "This project follows that route and uses XGBoost, the regularised gradient-boosting library of Chen and Guestrin."),
        P("A second problem sits on top of the first. A model learned from one sales context, for example one channel, one product group or one season, is often used in another whose data are distributed differently. "
          f"Statisticians call this **covariate shift** when the inputs change but the relation between inputs and demand does not {C('shim')}, and **domain adaptation** is the family of methods that respond to it {C('pan')}. "
          f"This project implements the simplest and most inspectable of them, **importance weighting**, in which each source row is given a weight that says how much it resembles the target domain {C('shim', 'bickel')}, "
          "and measures honestly whether it helps."),
        P("Terms used throughout: an **article** is one sellable product variant (H&M's article_id); **demand** is the number of units of an article sold on a day; a **domain** is a subset of the data defined by a column such as the sales channel; "
          "the **source** domain is the one the model is trained on and the **target** domain the one it must serve; a **lag** feature is the demand a fixed number of days earlier; "
          "**RMSE**, **MAE** and **WAPE** (sum of absolute errors divided by the sum of actual demand) measure forecast error, and **R2** the share of variance explained."),
        H2("1.2 Background and Motivation"),
        P("The project starts from the batch's base paper, \"Explainable retail demand forecasting: a hybrid LightGBM-SHAP framework for inventory optimization\" "
          f"{C('base')}. Its authors pair a LightGBM forecaster with four explanation levels (permutation importance, partial-dependence plots, SHAP and individual conditional expectation) because planners distrust forecasts they cannot interpret, "
          "and validate it on the UCI Online Retail II transactions (1.07 million rows, 4,631 products), reporting an RMSE of 33.71 and an R2 of 0.243 on daily product-level demand. "
          "That paper tests one data set from one market. It does not ask what happens when the model leaves the market it was trained on, and it does not treat products with no history; "
          "its own limitations section says that multi-domain validation would strengthen the work."),
        P("This is the gap the batch abstract sets out to fill: add domain adaptation so that a model trained in one retail context can serve a differently distributed one, and measure forecasts with RMSE, MAE, MAPE and R2. "
          f"The data chosen is the H&M Personalized Fashion Recommendations release {C('hm')}: real transactions of a global fashion retailer with article attributes, two sales-channel codes and prices. "
          f"We used a real subset of it, the {ds['articles']} best-selling articles of the first transaction shard ({ds['raw_rows']:,} rows from {ds['date_min']} to {ds['date_max']}), "
          "because the full table of 31.8 million rows does not fit the in-memory design of the application on the machine used."),
        P(f"Two design choices need a word of justification. The base paper compares LightGBM, XGBoost and CatBoost and finds the three within about 0.5 % of each other in RMSE, so the choice of booster is not what decides accuracy; "
          f"we use XGBoost because the batch abstract names it and because it accepts a per-row sample weight directly, which is exactly what importance weighting needs. "
          f"And we choose importance weighting over adversarial or feature-alignment methods {C('dann', 'coral')} because it needs only the input columns of the target domain, no target labels, no neural network and no extra training loop: "
          "the whole adaptation is one logistic regression and one weighted fit, and every number it produces (classifier accuracy, weight range, before and after error) can be shown on a page and checked."),
        P("The motivation is practical as well as academic. A planner needs a tool that loads the files, shows what is in them, trains a model, says how good it is against something simple, shows which inputs it relies on, "
          "and lets them try the adaptation idea on data of their own. TrendCast is that tool, and because it is tested on real data it also tells them, with numbers, where the idea works and where it does not."),
        H2("1.3 Problem Statement"),
        P("The batch problem statement lists four difficulties: forecasting models trained on one market lose accuracy when applied to another; new products have no sales history, so conventional forecasting cannot cover them; "
          "fashion trends shift within a season and invalidate models trained on older data; and forecasts delivered without explanation are not trusted by inventory planners. "
          "The need is a forecasting system that adapts across markets and categories and explains the drivers behind each forecast."),
        P("We restate the problem as one we can test. **Given daily unit sales of fashion articles in a source domain, build a forecaster that is accurate on a held-out future period, "
          "and measure whether re-weighting the source rows by their similarity to a differently distributed target domain makes the forecaster more accurate on that target, "
          "compared with the same model without re-weighting and with simple controls.** Forecast accuracy, the effect of the adaptation and the explanation of the forecast drivers are each reported with the number that supports them."),
        P("In symbols, let x be the feature vector of an article-day, p(x) the probability that a domain classifier assigns to the target domain for a source row x, and y the demand. "
          "The importance weight of a source row and the weighted training objective are:"),
        EQ("w(x) = p(x) / (1 − p(x)),   minimise over f:  Σ (over source rows i)  w(xᵢ) · (yᵢ − f(xᵢ))²"),
        P("A source row that looks like the target gets a weight above one and a row that looks nothing like it a weight near zero; the model is then pushed to fit the part of the source data that matters for the target. "
          "Whether that is enough to improve forecasts on a real retail table is an empirical question, and it is the question this project answers."),
        H2("1.4 Need for the Proposed System"),
        B("**Accuracy across contexts.** Retailers sell through several channels, product groups and seasons. A single model fitted on pooled history can hide a context in which it performs badly; the first step to correcting that is to measure the shift and the loss it causes.",
          "**A tool, not a notebook.** Forecasting experiments usually live in notebooks that only their author can rerun. A guided, gated application (upload, explore, features, train, adapt, evaluate, forecast) lets a planner repeat the whole analysis on new files.",
          "**Honest baselines.** A model is only useful if it beats something simple. The system always shows a moving-average baseline next to the learned model, and our experiments add naive and rolling-mean forecasts.",
          "**Leakage-safe evaluation.** Random train and test splits let a time-series model see the future. The system splits by date, shifts every lag and rolling feature by a day, and tunes with time-ordered cross-validation.",
          "**Explanation.** Planners override forecasts they cannot interpret. The evaluation page shows which features the model relies on; this report adds an exact SHAP analysis offline."),
        H2("1.5 Project Objectives"),
        P("The six objectives set for the batch, and where this report addresses each, are listed in the table below. The outcome column is the short version; Chapter 8 gives the measurements and Chapter 9 the full verdict."),
        TAB("Objectives of the project and their outcome", ["No.", "Objective", "Outcome (summary)"],
            [["1", "Collect historical fashion retail sales data and engineer seasonal, pricing and category features", f"Achieved: real H&M subset, {ds['feature_cols']} model inputs, leakage guards. H&M has no promotion or fabric columns."],
             ["2", "Train gradient-boosting models such as XGBoost to forecast demand at product and category level", "Achieved at article (product) level; no separate category-level model."],
             ["3", "Apply domain adaptation to transfer the model across markets and product categories", "Implemented and applied to sales-channel, product-group and department domains; the two channels are the only 'markets' in the data."],
             ["4", "Compare adapted and non-adapted models on a target market with a different data distribution", f"Done on {dom['summary']['pairs_total']} pairs x 5 seeds with four controls; adaptation helped on {dom['summary']['pairs_where_adaptation_helped']} pairs."],
             ["5", "Explain forecast drivers so planners understand why demand is predicted to move", "Partly: gain importance in the application; exact TreeSHAP offline; no per-forecast explanation in the application."],
             ["6", "Evaluate with MAE, RMSE and MAPE, and translate error into inventory impact", "Metrics achieved; inventory impact (under- and over-stock units) computed offline only."]],
            widths=[0.45, 3.0, 3.1], align=["c", "l", "l"], size=10),
        H2("1.6 Scope of the Project"),
        P("**In scope.** Uploading the three H&M tables; validation, cleaning and merging; daily demand per article; exploration charts; feature engineering; chronological split; moving-average, XGBoost (with optional time-ordered tuning) and, as comparison, "
          "random-forest and LightGBM models; importance-weighted domain adaptation on a chosen column and pair of values with a before-and-after report; evaluation with RMSE, MAE, safe MAPE and R2; recursive 7, 14 and 30-day forecasts; "
          "an optional plain-language explanation from the Gemini service; a FastAPI back end with 22 routes and a React front end of 13 pages; the original Streamlit application; and the tests and scripts that reproduce every number in this report."),
        P("**Out of scope.** Training on the full 31.8 million-row table; images or text of the products; promotion, price-plan or weather data (not in the files); multi-store or regional hierarchies; probabilistic forecasts; "
          "deep-learning and adversarial domain adaptation; automatic ordering or optimisation of stock levels; multi-user accounts and persistent storage; and deployment beyond a single machine."),
        H2("1.7 Project Contributions"),
        N(f"**An end-to-end, gated forecasting application.** A pipeline from raw H&M tables to forecasts, exposed through 22 REST routes and a 13-page console, with plain-language gating messages and 400, 409 and 422 error handling, and covered by {F.PYTEST_PASSED} unit and API tests and a {F.SMOKE_TOTAL}-check smoke test.",
          "**Leakage-safe feature engineering and evaluation.** Lag and rolling features are built from values shifted by one day, the split is by date, and tuning uses time-ordered folds; this report adds a rolling-origin backtest.",
          "**A working implementation of importance-weighted domain adaptation** that reports the domain-classifier accuracy, a per-feature shift table, the weight statistics and a before-and-after metric table.",
          "**An honest evaluation of that adaptation.** Six source-target pairs, five seeds and four controls (target-only oracle, unweighted pooling, shuffled weights, a time-clean protocol) show when the adaptation helps and when it does not, and expose a weight-scaling defect that makes XGBoost predict a constant.",
          "**Measured comparison with simple forecasts and with the base paper's findings,** including a feature-group ablation, exact TreeSHAP attributions, an inventory-impact calculation and an unseen-article (cold-start) test, all reproducible from the scripts in the repository."),
        P(f"In one paragraph, what the measurements show: on the held-out last 20 % of the dates XGBoost's RMSE is {xgb:.2f} against {ma:.2f} for the moving average, but {lag1:.2f} for repeating yesterday's demand, so the learned model is better than the application's own baseline and worse than the strongest simple one; "
          f"removing the lag and rolling features collapses the model, which agrees with the base paper's finding that rolling statistics dominate; "
          f"and importance-weighted adaptation improved RMSE on {dom['summary']['pairs_where_adaptation_helped']} of {dom['summary']['pairs_total']} pairs, with a best case of {on['app']['rmse_improvement_pct_mean']:+.1f} % that turns into {on['time_clean']['rmse_improvement_pct_mean']:+.1f} % under a time-clean protocol. "
          "A negative or null result on the adaptation is still a result: it tells a planner not to rely on this step without checking it, and it tells the next project which defects to remove first."),
        H2("1.8 Limitations and Assumptions"),
        B(f"**Small slice of the data.** {ds['articles']} articles and 107 days ({ds['date_min']} to {ds['date_max']}); the training window contains no earlier year, so yearly seasonality cannot be learned and the test window (the Christmas peak and January sales) is unusually hard.",
          f"**Cleaning understates demand.** The pipeline drops exact duplicate rows ({dup:,} of {ds['raw_rows']:,}, {dup / ds['raw_rows'] * 100:.1f} %), but identical H&M rows are usually real repeat purchases.",
          "**Channel labels.** The files code the two sales channels 1 and 2 without saying which is which; the daily channel feature is the most frequent channel of that day while demand counts both, so a 'channel domain' is a mixture.",
          "**Known inputs.** The day's price and channel are model inputs and are assumed to be known when forecasting; in recursive forecasts they are held at their last value.",
          "**Adaptation protocol.** The source model may train on dates inside the target test window; the time-clean control measures what that costs.",
          "**No cold start, no in-application SHAP or inventory view.** These were measured offline and are reported as such.",
          "**External dependency.** The optional AI Insights page calls an external service that answered 503 or timed out during our screenshot run, so its output screen shows the error state."),
        H2("1.9 Organization of the Report"),
        P("Chapter 2 surveys the literature and analyses the base paper. Chapter 3 studies feasibility and Chapter 4 sets out the existing and proposed systems and the requirements. "
          "Chapter 5 gives the design: architecture, workflow, data flow and UML diagrams, the logical data model and the user interface. Chapter 6 describes the methodology and implementation: "
          "data, preprocessing, the XGBoost model, the domain-adaptation method with its mathematics, the API, security and error handling, and how to install and run it. Chapter 7 reports testing. "
          "Chapter 8 presents every output screen, the model results, the comparison with the base paper's findings and the objectives against outcomes. Chapter 9 concludes and Chapter 10 sets out the future scope. "
          "The references and three appendices (important code, installation and user guide, additional screens) follow."),
    ]
    if F.REPORT:   # compact report variant: drop passages that the abstract and later chapters repeat
        out = trim(out, drop=("In one paragraph, what the measurements show", "The motivation is practical as well as academic.",
                              "Two design choices need a word", "A source row that looks like the target gets", "In symbols, let x", "w(x) ="),
                   replace={"**Small slice of the data.**": B(
                       f"**Small slice of the data.** {ds['articles']} articles and 107 days ({ds['date_min']} to {ds['date_max']}); no earlier year to learn yearly seasonality from, and a test window (Christmas peak, January sales) that is unusually hard.",
                       f"**Cleaning understates demand.** Exact duplicate rows ({dup:,} of {ds['raw_rows']:,}, {dup / ds['raw_rows'] * 100:.1f} %) are dropped, but identical H&M rows are usually real repeat purchases.",
                       "**Channel labels and known inputs.** The files code the channels 1 and 2 without saying which is which; the daily channel is the most frequent channel of that day while demand counts both; the day's price and channel are assumed known when forecasting.",
                       "**Adaptation protocol.** The source model may train on dates inside the target test window; a time-clean control measures what that costs.",
                       "**Not in the application.** Cold start, SHAP and inventory impact were measured offline; the optional AI Insights page depends on an external service that answered 503 or timed out during our screenshot run.")})
    return out
