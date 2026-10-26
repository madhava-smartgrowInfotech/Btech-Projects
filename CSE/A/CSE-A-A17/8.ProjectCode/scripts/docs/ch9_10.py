"""Chapters 9 (Conclusion) and 10 (Future scope), plus the shared block lists used by documents 9, 10, 12 and 15.

Every number is read from facts.py (experiments/**/metrics.json); code excerpts are cut from the real files in 8.ProjectCode.
"""
import ast
import os
import textwrap

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB, renum
from .refs import N as C


# ---------------------------------------------------------------------------- helpers
def _read(rel):
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        return f.read()


def fn(rel, name, doc=False):
    """Source of a module-level function exactly as it stands (docstring removed unless doc=True)."""
    text = _read(rel)
    lines = text.split("\n")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            start = min([d.lineno for d in node.decorator_list] + [node.lineno])
            end = node.end_lineno
            body = lines[start - 1:end]
            if not doc and ast.get_docstring(node):
                d = node.body[0]
                body = lines[start - 1:d.lineno - 1] + lines[d.end_lineno:end]
            return "\n".join(body)
    raise KeyError(name)


def between(rel, first, last):
    """Lines from the first line containing `first` to the first later line containing `last` (inclusive), dedented."""
    lines = _read(rel).split("\n")
    i = next(k for k, l in enumerate(lines) if first in l)
    j = next(k for k in range(i, len(lines)) if last in lines[k])
    return textwrap.dedent("\n".join(lines[i:j + 1]))


def _fig(name, caption, width=5.6):
    """A result figure, only if the figure fork has written it."""
    return [FIG(F.fig(name), caption, width)] if os.path.exists(F.fig(name)) else []


def _m(model, key="RMSE"):
    return F.FC["models"][model][key]


def _v():
    ab = F.FC["ablation"]
    rec = F.REC["results"]
    s = F.DOM["summary"]
    return dict(
        x=_m(F.XGB), xr2=_m(F.XGB, "R2"), xsd=F.FC["xgboost_seed_stats"]["RMSE"]["std"], ma=_m(F.MA), lag1=_m("Naive (lag 1)"), rm7=_m("Rolling mean 7 (shifted)"),
        lgb=_m("LightGBM"), tuned=_m(F.XGB_T), rf=_m("Random forest"), allf=ab["all features (as shipped)"]["RMSE"], lagonly=ab["lag / rolling only"]["RMSE"],
        lagonly_r2=ab["lag / rolling only"]["R2"], nolag=ab["no lag / rolling"]["RMSE"], nolag_r2=ab["no lag / rolling"]["R2"], cal=ab["calendar only"]["RMSE"],
        b1=rec["xgb_app"]["by_band"][0]["WAPE (%)"], b2=rec["xgb_app"]["by_band"][1]["WAPE (%)"], b3=rec["xgb_app"]["by_band"][2]["WAPE (%)"],
        f1=rec["flat_ma7"]["by_band"][0]["WAPE (%)"], f2=rec["flat_ma7"]["by_band"][1]["WAPE (%)"], f3=rec["flat_ma7"]["by_band"][2]["WAPE (%)"],
        helped=s["pairs_where_adaptation_helped"], total=s["pairs_total"], mean=s["mean_rmse_improvement_pct"], mn=s["min"], mx=s["max"],
        norm=s["normalised_mean_rmse_improvement_pct"], tc=s["time_clean_mean_rmse_improvement_pct"], nrm_tc=s["normalised_time_clean_mean_rmse_improvement_pct"],
        spear=F.EX["spearman_rank_corr_shap_vs_gain"], top3=F.EX["top3_share_of_total_abs_shap_pct"],
        ix=F.INV["XGBoost"], im=F.INV["Moving average (7d)"],
        cold=F.COLD["attributes_calendar_only_unseen_article"], cold_b=F.COLD["product_type_mean_baseline_unseen_article"], cold_l=F.COLD["full_features_unseen_article_lags_assumed_known"],
        online=F.pair("Online"), store=F.pair("Store ->"),
    )


def _pairs_table():
    rows = []
    for p in F.DOM["pairs"]:
        a, t = p["app"], p["time_clean"]
        rows.append([p["label"], f"{p['diagnostics']['clf_accuracy'] * 100:.1f}", f"{a['before']['RMSE']['mean']:.2f}", f"{a['adapted']['RMSE']['mean']:.2f}",
                     f"{a['rmse_improvement_pct_mean']:+.1f}", f"{a['normalised_improvement_pct_mean']:+.1f}", f"{t['rmse_improvement_pct_mean']:+.1f}"])
    return TAB("Domain adaptation on six source-target pairs (RMSE on held-out target rows, mean of 5 seeds; improvement in percent)",
               ["Pair", "Clf acc. %", "Before", "Adapted", "As shipped", "Mean-1 weights", "Time-clean"], rows,
               widths=[2.0, 0.7, 0.7, 0.7, 0.8, 0.8, 0.8], align=["l", "c", "c", "c", "c", "c", "c"], size=9.5)


# ---------------------------------------------------------------------------- novelty / contributions
def novelty_blocks():
    v = _v()
    return [
        H2("What the base paper contributes"),
        P(f"The base paper {C('base')} pairs a LightGBM demand model with a four-level explainability pipeline: permutation importance, partial dependence, SHAP and individual conditional expectation (ICE) curves. "
          "It is validated on the UCI Online Retail II data (1.07 million transactions, 4,631 products, 41 engineered features, one-day-ahead forecasts) and reports RMSE 33.71 and R2 0.243, with paired significance tests against six baselines. "
          "Its own ablation finds that rolling statistics are the dominant feature group, and its limitations section names single-dataset validation, a stationary-relationship assumption and one-step forecasts. "
          "It does not address transfer to a differently distributed market, new products or domain shift."),
        H2("What is new in TrendCast"),
        B("**A domain-adaptation workflow on top of gradient boosting.** The batch gap is that a model trained in one retail context should transfer to a new one. TrendCast adds an importance-weighted step (a logistic domain classifier gives each source row the weight p/(1-p), clipped at 20) "
          "to a gradient-boosted demand model, with a shift table, the classifier accuracy, weight statistics and a before-and-after report on screen. The technique itself is the covariate-shift weighting of Shimodaira and Bickel et al. "
          f"{C('shim', 'bickel')}; what is new is its inspectable use inside a demand-forecasting product.",
          "**A gated, tested web console.** The original Streamlit script was wrapped in a FastAPI service with 22 routes and a 13-page React console in which every page refuses to run until the earlier step is done, validation errors are explained in plain language, "
          f"and {F.PYTEST_PASSED} pytest tests plus a {F.SMOKE_PASSED}-check smoke test cover the pipeline and the API.",
          "**Controls that test the adaptation honestly.** Besides the before-and-after pair the evaluation harness trains a target-only oracle, a pooled source-plus-target model, a shuffled-weights control, a mean-1 rescaling of the weights and a time-clean protocol. "
          "These controls are what exposed that the one clear gain came from time overlap and that degenerate weights collapse XGBoost.",
          "**A like-for-like baseline set.** Naive lag-1, a seven-day moving average, a shifted rolling mean, random forest and LightGBM are scored on the same split as XGBoost, because the base paper's own baselines showed how strong naive lag-1 can be."),
        H2("What is standard"),
        P(f"XGBoost {C('xgb')}, gradient boosting {C('gbm')}, random forests {C('rf')}, calendar and lag features, chronological splitting, TimeSeriesSplit tuning and random search {C('bergstra')} are established techniques used as they are. "
          f"Gain importance is the library's default; TreeSHAP {C('treeshap')} was used only offline through XGBoost's built-in contributions. The importance-weighting idea is from the covariate-shift literature."),
        H2("What the base paper has and TrendCast does not"),
        B("**No ICE, PDP or permutation-importance layers.** The app shows gain importance for the top 20 features; exact SHAP values were computed offline and agree only moderately with gain "
          f"(Spearman {v['spear']:.2f}). There is no per-forecast explanation in the product.",
          "**No statistical significance tests or Optuna tuning.** TrendCast reports five-seed means with standard deviations and a ten-iteration random search.",
          "**No external validation set.** One 107-day window of one retailer was measured, so even the ranking of models is specific to that window; the base paper's single-dataset caveat applies here more strongly."),
    ]


def contribution_blocks():
    v = _v()
    return [
        P("The contributions of the project, stated at the strength the evidence supports, are:"),
        N("**A working end-to-end pipeline, TrendCast**: upload, validate, clean, merge, daily demand, features, chronological split, baselines, XGBoost, domain adaptation, evaluation, recursive forecast and optional AI explanation, "
          "served by a 22-route FastAPI application and a 13-page React console, with the original 11-page Streamlit app kept unchanged.",
          "**A leakage-aware feature and evaluation design** on real H&M data: lags and rolling statistics computed from shifted values, a split by date, TimeSeriesSplit tuning and a safe MAPE that reports how many zero-demand rows it excludes.",
          "**An inspectable importance-weighted domain-adaptation workflow** for three domain columns (sales channel, product group, department), showing the shift table, classifier accuracy, weight statistics and the before-and-after metrics.",
          f"**An honest measurement harness**, `scripts/run_experiments.py`, covering baselines, a feature-group ablation, a rolling-origin backtest, a recursive-horizon test, {v['total']} domain pairs x 5 seeds with four controls, offline TreeSHAP, inventory units and an unseen-article test; every number in the documents is read from its output.",
          f"**Findings that a plain before-and-after report would have hidden**: adaptation as shipped helped {v['helped']} of {v['total']} pairs, its one clear gain disappears under a time-clean protocol, unnormalised weights can starve XGBoost into a constant, and the recursive multi-day forecast is worse than a flat seven-day mean.",
          f"**A tested, reproducible artefact**: {F.PYTEST_PASSED} passing pytest tests, a {F.SMOKE_PASSED}-check smoke test, a screenshot script that drives the real interface with real data, and scripts that regenerate the facts file."),
    ]


# ---------------------------------------------------------------------------- scope and limitations
def scope_blocks():
    return [
        P("The scope follows the six batch objectives and the data that could be obtained. It is stated first as what the product and its measurements cover, then as what they deliberately leave out, so a reader does not mistake an offline experiment for a product feature."),
        H2("In scope"),
        B("**Data:** the three H&M tables (transactions, articles, optional customers) uploaded as CSV; a measured subset of 300 articles, 684,392 rows and 107 days, plus a synthetic sample for smoke tests.",
          "**Target:** units sold per article per day, forecast one day ahead for evaluation and recursively for 7, 14 or 30 days in the app.",
          "**Models:** a seven-day moving-average baseline, XGBoost (default or randomised-search tuned), and an importance-weighted XGBoost for domain adaptation; random forest and LightGBM only as offline comparisons.",
          "**Domains:** sales channel, product group and department as the domain-defining column, chosen in the interface.",
          "**Evaluation:** RMSE, MAE, safe MAPE and R2 in the app; WAPE, SHAP, inventory units and an unseen-article test offline.",
          "**Product:** the FastAPI service, the React console, the original Streamlit app, tests, screenshot and experiment scripts."),
        H2("Out of scope"),
        B("New-store or new-region transfer (the data hold two sales channels and no geography), promotions, weather, holidays as flags, stock levels, lead times and costs.",
          "A cold-start mode for products with no history; the forecast route needs at least five days of history and lag features.",
          "Probabilistic forecasts, direct multi-horizon models, hierarchical reconciliation and deep-learning forecasters.",
          "Adversarial or correlation-alignment domain adaptation; only importance weighting is implemented.",
          "Authentication, multiple users, a database, deployment to a cloud service and monitoring: the console is a single-user local tool.",
          "Computing inventory cost in money or setting reorder points inside the product."),
        P("Table 1 sets the scope against the six objectives, separating what the product does, what only the offline harness measures and what was not done."),
        TAB("Scope against the batch objectives", ["Objective", "In the product", "Offline only", "Not done"],
            [["1 Data and features", "Upload, clean, 31 features", "-", "Promotions, fabric, regional seasonality (not in H&M)"],
             ["2 XGBoost forecasts", "Article level, 7/14/30 days", "-", "Separate category-level model"],
             ["3 Domain adaptation", "Importance weighting, 3 domain columns", "Controls, mean-1 weights", "New markets, other methods"],
             ["4 Adapted vs non-adapted", "Before/after report", "6 pairs x 5 seeds, 4 controls", "-"],
             ["5 Explain drivers", "Gain importance, optional Gemini text", "TreeSHAP", "Per-forecast explanation in the app"],
             ["6 MAE, RMSE, MAPE, inventory", "RMSE, MAE, safe MAPE, R2", "WAPE, under/over-stock units", "Money-valued inventory impact"]],
            widths=[1.6, 1.8, 1.6, 1.6], align=["l", "l", "l", "l"], size=10),
    ]


def assumption_blocks():
    return [
        B("The 300 best-selling articles of the first transaction shard are representative enough to compare methods; they are the products with enough daily sales for lag features, which also makes them easier than the long tail.",
          "One transaction row is one unit sold, so the daily count of rows per article is demand; returns and stock-outs are not visible.",
          "The price and sales channel of the forecast day are known inputs (planned price, expected channel) - the same-day values are used as features.",
          "A chronological 80/20 split mimics deployment; the last 20 percent of dates (14 December 2018 to 4 January 2019) is a fair, if hard, test period.",
          "Channel, product group and department are treated as domains; their difference in feature distribution is taken as the covariate shift to adapt to, and the labels are used only to split the rows.",
          "The H&M files code the sales channels only as 1 and 2; the documents call them channel 1 and channel 2 and do not claim which is the store.",
          "A single user runs the console on one machine, so one shared in-memory state is sufficient."),
    ]


def limitation_blocks():
    v = _v()
    return [
        H2("Data"),
        B("**Short window.** 107 days of one retailer: no earlier year exists in the training window, so yearly seasonality cannot be learned, and the test window holds the Christmas peak and the January sales.",
          "**A selected subset.** 300 best-selling articles of one shard (about 0.7 percent of the 42,415 articles sold in it); results for slow movers and new articles are not measured.",
          "**Cleaning understates demand.** Dropping exact duplicate rows removed 79,214 of 684,392 rows (11.6 percent), although in this dataset a repeated identical row is usually a real repeat purchase.",
          "**Channel domains are mixtures.** The domain label is the channel of most of that day's sales, while demand counts both channels."),
        H2("Forecasting"),
        B(f"**Not better than the simplest rule.** Naive lag-1 reaches RMSE {v['lag1']:.2f} against {v['x']:.2f} for XGBoost; the model beats the app's moving average ({v['ma']:.2f}) but not the naive forecast.",
          f"**Absolute-time features hurt.** A model using only lag and rolling features scores RMSE {v['lagonly']:.2f}, better than the shipped all-feature model ({v['allf']:.2f}), because year, quarter and day of year cannot extrapolate beyond the training dates.",
          f"**The multi-day forecast degrades fast.** WAPE is {v['b1']:.0f}, {v['b2']:.0f} and {v['b3']:.0f} percent for days 1-7, 8-14 and 15-30, against {v['f1']:.0f}, {v['f2']:.0f} and {v['f3']:.0f} percent for a flat seven-day mean. "
          "The loop also leaves week of year, day of year, quarter and month-start flags frozen and holds price and channel at their last values.",
          "**Leaky inputs.** The day's own price and channel are features; they are known only if prices and channel mix are planned in advance."),
        H2("Domain adaptation"),
        B(f"**Mostly no gain.** As shipped, adaptation improved RMSE on {v['helped']} of {v['total']} pairs (range {v['mn']:+.1f} to {v['mx']:+.1f} percent, mean {v['mean']:+.1f}).",
          f"**The clear gain is not adaptation.** Online-to-store improves {v['online']['app']['rmse_improvement_pct_mean']:+.1f} percent, but {v['online']['time_clean']['rmse_improvement_pct_mean']:+.1f} percent when source rows are limited to dates before the target test window; the source model otherwise trains on the future of the target test.",
          "**Weights are not normalised.** When the classifier separates the domains perfectly the weights are about 1e-5, XGBoost's min_child_weight of 1 can never be met and the model predicts a constant.",
          "**Weak classifier.** Logistic regression on unscaled features does not converge in 1,000 iterations, and unweighted pooling of source and target data beats weighting on 5 of 6 pairs."),
        H2("Product and evidence"),
        B("**Explanations.** The app shows gain importance, which overstates calendar features; there is no per-forecast attribution, no cold-start mode and no inventory view in the product.",
          "**Single user, in memory.** State is lost on restart, and concurrent users would overwrite each other's data.",
          "**External service.** AI Insights depends on the Gemini service, which returned 503 or timed out during the screenshot run, so its screen shows the error state.",
          "**Testing.** Tests use small synthetic frames; full-size H&M (31.8 million rows), load, accessibility and non-Chrome browsers were not tested."),
        H2("Hardware, software and process"),
        B("**One machine.** All timings come from one 12-thread desktop processor with other jobs running at the same time, so latencies are indicative; accuracy numbers did not change between runs.",
          "**Library behaviour.** The optional LightGBM baseline crashes with an access violation on this machine when pandas or XGBoost are imported before LightGBM; the harness imports it first. The logistic domain classifier prints a convergence warning on every run.",
          "**No peer review of the code.** The product was developed and checked by the team and the tests listed in Chapter 7; no independent review or security audit was carried out."),
        H2("How the limits affect the reading of the results"),
        P("The data limits mean the model ranking is specific to one winter window: a different window, with a previous year in the training data, could favour XGBoost over naive lag-1. "
          "The domain-adaptation limits mean the six-pair result should be read as a test of the shipped procedure, not of importance weighting in general: with mean-1 weights and a time-clean source the average change is close to zero, "
          f"{v['nrm_tc']:+.1f} percent, so the honest statement is that no benefit was demonstrated. The product limits mean TrendCast is a study tool for one analyst, not a service."),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, so no document claims anything about them. Each is either impossible with the 107-day public subset or outside what the product does."),
        B("Multi-year seasonality and a test window outside the Christmas period: the data hold one autumn and winter.",
          "Transfer to a genuinely new store, region or market; the two sales channels are the only market-like split.",
          "Promotions, price changes as experiments, weather and holiday effects.",
          "Inventory cost in money, service levels or reorder points; only under- and over-forecast units were counted, offline.",
          "Cold start inside the product (the offline attribute-only test is not a product feature).",
          "User behaviour: no usability study or planner trust test was run.",
          "Load, concurrency and full-dataset scale of the API.",
          "The quality and correctness of the Gemini explanations: the service was unavailable when screens were captured."),
        P("None of these is hidden in a headline number: the abstract's statements about fewer shortages, less overstock and transfer to new markets are therefore treated as aims, not as results."),
    ]


# ---------------------------------------------------------------------------- code walk-throughs
def walkthrough_blocks():
    run_split = between("backend/main.py", "cols = [c for c in feature_cols_of(ft) if c != req.domain_col]", "target_test_X, target_test_y")
    run_core = between("backend/main.py", "source_model = xgboost_model.train_xgboost", "metrics_after = evaluation.evaluate_model")
    loop = between("backend/main.py", "for step in range(1, req.horizon + 1):", "recent_demand.append(pred)")
    return [
        H2("Leakage-safe lag and rolling features (`feature_engineering.py`)"),
        P("The strongest predictor of tomorrow's demand is recent demand, so the main risk is a feature that quietly contains today's value. Lags use `shift(n)` per article. Rolling statistics are computed on a series that has already been shifted by one day, "
          "so a window of seven days ends yesterday. Rows at the start of an article's history, which lack a full window, are filled with zero."),
        CODE("# inside add_lag_rolling_features(df, group_col, date_col, target_col)\n" + between("src/feature_engineering.py", "out = df.sort_values([group_col, date_col]).copy()", "out = out.drop(columns=[\"_shifted_demand\"])"), 7.5),
        H2("Importance weights (`domain_adaptation.py`)"),
        P("The domain classifier is a logistic regression trained on source rows (label 0) and target rows (label 1) with the model's own features. Each source row then receives the odds that it looks like a target row. "
          "The ratio is clipped at 20 so a few rows cannot dominate the loss, but nothing stops it from becoming tiny, which is the defect found in Chapter 8."),
        CODE(fn("src/domain_adaptation.py", "train_domain_classifier") + "\n\n" + fn("src/domain_adaptation.py", "compute_instance_weights"), 7.5),
        H2("Domain run (`backend/main.py`, route `/api/domain/run`)"),
        P("The domain column is removed from the features so the classifier cannot read its own label. The later half of the target dates is held out as the test set; the source model trains on all source rows, "
          "which is why source dates can overlap the target test window. The same held-out rows score the model before and after weighting."),
        CODE(run_split + "\n...\n" + run_core, 7.5),
        H2("Recursive forecast (`backend/main.py`, route `/api/forecast`)"),
        P("Each predicted day is appended to the history so that the next day's lags and rolling statistics are built from predictions. Only some calendar columns are refreshed; price and channel stay at the last observed values, "
          "and the prediction is clipped at zero."),
        CODE(loop, 7.5),
        H2("Chronological split (`baseline_models.py`)"),
        P("The split is taken on unique dates, never on rows, so every test date is later than every training date."),
        CODE(fn("src/baseline_models.py", "chronological_split"), 7.5),
    ]


def decision_blocks():
    return [
        P("The main implementation decisions, the reason for each and what the measurements later showed are listed in Table 1."),
        TAB("Implementation decisions and their reasons", ["Decision", "Reason", "What the measurements showed"],
            [["Split by date, 80/20", "A random split would let the model train on days after its test days", "Test window is the hardest part of the year; scores are lower than a random split would give"],
             ["TimeSeriesSplit for tuning", "Folds are always later than their training part", "Tuned XGBoost improves RMSE from 11.09 to 10.34 but is still behind naive lag-1"],
             ["Safe MAPE", "Plain MAPE divides by zero on zero-demand days", "MAPE is still above 100 percent because low-volume days dominate; WAPE is the readable measure"],
             ["Label encoding of attributes", "One-hot of product names would explode the feature space", "Gain importance later ranks the codes low; no ordering is implied for trees"],
             ["Weights p/(1-p) clipped at 20", "A few rows with p near 1 would dominate the loss", "No lower bound: weights near 1e-5 starve min_child_weight"],
             ["Domain column excluded from features", "Otherwise the classifier reads its label", "Correlated attributes still allow perfect separation for department pairs"],
             ["Target test = later half of target dates", "Keeps the target evaluation chronological", "Source rows still overlap that window, which inflated one pair"],
             ["FastAPI over the Streamlit script", "A separate API lets a React console, tests and scripts share one pipeline", "22 routes, 39 tests, a 30-day forecast in a median 156 ms"],
             ["In-memory state with a lock", "Single-user demo, no database to install", "Fast, but lost on restart and not multi-user"],
             ["409 gating messages", "Each page tells the user which earlier step is missing", "Smoke test checks upload, training and forecast gating"],
             ["Optional Gemini, aggregates only", "Raw rows never leave the machine; the app works without a key", "Service unavailable during capture; nothing else was affected"]],
            widths=[1.6, 2.4, 2.6], align=["l", "l", "l"], size=10),
        P("Three decisions deserve a longer note. The first is the split. Splitting by date makes the test window the last 21 days, which contain the Christmas peak and the January sales; "
          "a random split would have scored the model on days between training days and flattered it. The price of honesty is a lower R2, 0.34 for the default model. "
          "The second is the choice to keep one shared state behind a lock. It is what the Streamlit session state did, it needs no installation, and it makes every route a thin call into src/; "
          "the cost is that two browsers share one dataset. The third is the gating. Each route that needs earlier output returns HTTP 409 with a sentence such as Build the feature table first, and the React pages read the progress flags from /api/state "
          "before calling, so a user who skips a step sees a message, not a stack trace."),
    ]


# ---------------------------------------------------------------------------- conclusion
def _lessons():
    v = _v()
    return [
        f"**The model is useful but not unbeatable.** On the real test window XGBoost (RMSE {v['x']:.2f}, R2 {v['xr2']:.2f}) beats the moving average ({v['ma']:.2f}) and random forest ({v['rf']:.2f}); LightGBM ({v['lgb']:.2f}) and the tuned model ({v['tuned']:.2f}) come closer to naive lag-1 ({v['lag1']:.2f}), which still wins.",
        f"**Recent demand does the work.** Without lag and rolling features R2 falls to {v['nolag_r2']:.2f}; with only those features RMSE is {v['lagonly']:.2f}, better than the shipped all-feature model. This agrees with the base paper's own ablation on different data.",
        f"**Domain adaptation, as shipped, is not a reliable gain.** It improved {v['helped']} of {v['total']} pairs; the one clear gain disappears when source rows may not overlap the target test dates ({v['tc']:+.1f} percent on average in that protocol).",
        "**Weights must be normalised.** Perfectly separable domains produce weights near 1e-5 and XGBoost predicts a constant; rescaling the same weights to mean 1 removes the collapse.",
        f"**Multi-day forecasts are weak.** WAPE grows from {v['b1']:.0f} to {v['b3']:.0f} percent over the horizon, worse than a flat seven-day mean at every horizon.",
    ]


def _objective_table():
    v = _v()
    return TAB("Objectives against outcomes", ["Objective", "Outcome", "Evidence"],
               [["1 Collect real data, engineer seasonal, price and category features", "Achieved", "H&M subset, 31 inputs, shifted lags, no promotions or fabric in the data"],
                ["2 Train XGBoost at product and category level", "Product level achieved", "Article-level model; category enters as features only"],
                ["3 Apply domain adaptation across markets and categories", "Implemented", "Importance weighting on channel, group and department; no regional markets in the data"],
                ["4 Compare adapted and non-adapted on a shifted target", "Done; result negative or mixed", f"{v['helped']} of {v['total']} pairs improved; mean {v['mean']:+.1f} percent"],
                ["5 Explain forecast drivers", "Partly", f"Gain importance in the app; offline SHAP agrees only moderately (Spearman {v['spear']:.2f})"],
                ["6 Evaluate with MAE, RMSE, MAPE and inventory impact", "Metrics yes; inventory offline", f"XGBoost under-forecasts {v['ix']['understock_pct_of_demand']:.1f} percent and over-forecasts {v['ix']['overstock_pct_of_demand']:.1f} percent of test demand"]],
               widths=[2.4, 1.4, 2.8], align=["l", "l", "l"], size=10)


def conclusion_blocks():
    v = _v()
    return [
        H2("Summary"),
        P(f"TrendCast is a working forecasting product: it turns H&M-style transactions into daily demand per article, forecasts it with XGBoost and offers an importance-weighted domain-adaptation workflow, behind a gated 22-route API and a 13-page console. "
          f"Measured on 684,392 real transactions of 300 articles over 107 days, the honest outcome is mixed, and the documents say so."),
        H2("Objectives against outcomes"),
        _objective_table(),
        H2("Key findings"),
        N(*_lessons()),
        P("The abstract's claim that the system reduces shortages and overstock is not demonstrated: on the test window XGBoost over-forecasts total demand by "
          f"{v['ix']['bias_pct']:.1f} percent while losing fewer sales than the moving average ({v['ix']['understock_pct_of_demand']:.1f} against {v['im']['understock_pct_of_demand']:.1f} percent of demand)."),
        H2("Closing remark"),
        P("The project's value is the measured, reproducible pipeline and the controls that expose where adaptation and recursive forecasting fail. With normalised weights, a time-clean protocol and refreshed calendar features, the same code is a sound base for a real study."),
    ]


def chapter9_blocks():
    v = _v()
    body = [
        H2("Summary"),
        P("TrendCast was built to forecast fashion demand with machine learning and to move a model from one retail context to another by domain adaptation. The product takes the three H&M tables, validates, cleans and merges them, aggregates units sold per article per day, "
          "fills quiet days with zero, builds calendar, price, attribute, lag and rolling features without leakage, splits by date, trains a moving-average baseline and an XGBoost model, adapts a source-domain model to a target domain with importance weights, "
          "evaluates with RMSE, MAE, safe MAPE and R2, forecasts 7, 14 or 30 days ahead and, optionally, asks Gemini to explain the numbers in words. It runs as a FastAPI service with 22 routes and a 13-page React console; the original Streamlit app is unchanged."),
        P(f"The system was measured on real data: 684,392 transactions of the 300 best-selling articles between 20 September 2018 and 4 January 2019, giving 31,094 article-days. "
          f"{F.PYTEST_PASSED} pytest tests and a {F.SMOKE_PASSED}-check smoke test pass, and 25 screenshots were taken from the running interface with this data loaded."),
        H2("Objectives achieved"),
        _objective_table(),
        P("Objectives 1, 2 and 3 were met as built; objective 4 was carried out and answered with a mostly negative result; objectives 5 and 6 were met in part, because SHAP and inventory units exist only in the offline harness."),
        H2("Key findings"),
        N(*_lessons()),
        P(f"Two further findings come from the controls. The offline TreeSHAP ranking puts lag_1 first, with three features carrying {v['top3']:.0f} percent of the total attribution, while gain importance puts is_month_end and quarter first: "
          f"gain overstates calendar features that split often. And an unseen-article test shows what a cold-start mode could offer: attributes and calendar alone reach R2 {v['cold']['R2']:.2f} against {v['cold_b']['R2']:.2f} for the product-type mean, "
          f"but far below the {v['cold_l']['R2']:.2f} reached when the article's own history is available."),
        *_fig("f01_model_comparison.png", "RMSE of every model on the 2018-12-14 to 2019-01-04 test window.", 5.4),
        P("The domain-adaptation result is easiest to read pair by pair. Table 2 repeats the six pairs: the first two use the sales channel, the next two the product group and the last two the department. "
          "The classifier separates the department pairs perfectly, which is exactly where the shipped weights collapse; the product-group pairs are separated 93 percent of the time and lose 6-7 percent; "
          "only the first pair gains, and its gain vanishes in the time-clean column. The mean-1 column shows that rescaling repairs the collapse but does not turn adaptation into a gain."),
        _pairs_table(),
        P("What the project learned about method is as important as the numbers. A before-and-after report with one seed would have shown the +12 percent on the first pair and stopped. "
          "The controls (shuffled weights, pooling, a target-only model, a time-clean source) are what turned a headline into an explanation, and they cost a few minutes of CPU. "
          "The same habit exposed that the shipped model loses to naive lag-1 and that the recursive forecast loses to a flat mean: results that matter for anyone who would deploy the forecasts."),
        H2("Practical applications"),
        B("**A data-quality and exploration tool.** The upload report, exploration charts and daily-demand table let a planner see duplicates, zero-demand days and channel mix before any model is trained.",
          "**A forecasting baseline with a built-in sanity check.** The comparison table puts XGBoost beside a moving average; adding the naive lag-1 forecast to it, as the offline harness does, is the check a planner should demand before trusting a model.",
          "**A transfer-risk check.** The shift table and the domain-classifier accuracy show how different two domains are. An accuracy near 100 percent is a warning that weights will be degenerate; near 50 percent says transfer is unnecessary.",
          "**Short-horizon planning only.** Seven-day forecasts are the most trustworthy output; 15-30 day forecasts should not drive orders."),
        H2("Known limitations"),
        P("The data cover 107 days and one retailer, so seasonality, new-market transfer and slow movers were not measured. The cleaning step removes repeat purchases, the price and channel of the forecast day are inputs, and the recursive loop freezes several calendar features. "
          "The product has no cold-start mode, no per-forecast explanation and no inventory view, runs for one user with in-memory state, and depends on an external service for AI Insights, which was unavailable during capture. Chapter 8 and the limitations chapter give the full list."),
        *_fig("f05_domain_pairs.png", "RMSE improvement of the adapted model for the six source-target pairs under four protocols.", 5.4),
    ]
    if F.REPORT:
        body = _ch9_trim(body)
    return [H1("CHAPTER 9: CONCLUSION")] + renum(body, "9")


def _ch9_trim(body):
    """Report variant: one figure, no method paragraph, four practical-application bullets cut to two, second summary paragraph cut."""
    out, skip = [], False
    for b in body:
        if b[0] == "fig" and "f01" in b[1]:
            continue
        if b[0] == "p" and (b[1].startswith("What the project learned about method") or b[1].startswith(f"{F.PYTEST_PASSED} pytest") or b[1].startswith("The system was measured on real data")):
            continue
        if b[0] == "p" and b[1].startswith("The domain-adaptation result is easiest"):
            b = ("p", "Table 2 repeats the six pairs (channel, product group, department). The department pairs are separated perfectly and collapse under the shipped weights; the product-group pairs lose 6-7 percent; only the first pair gains, and its gain vanishes in the time-clean column.")
        if b[0] == "b" and b[1][0].startswith("**A data-quality and exploration tool"):
            b = ("b", [b[1][1], b[1][3]])
        if b[0] == "p" and b[1].startswith("Two further findings come from the controls"):
            b = ("p", b[1].split(" And an unseen-article")[0])
        out.append(b)
    return out


# ---------------------------------------------------------------------------- future scope
def _roadmap():
    return TAB("Roadmap", ["Stage", "Work", "Done when"],
               [["1. Repair what was measured", "Normalise weights, time-clean protocol as default, refresh all calendar features in recursion, keep duplicate rows, drop absolute-time features", "The six-pair study improves or is neutral, and the recursive forecast beats a flat seven-day mean"],
                ["2. Explain and plan", "SHAP per forecast, WAPE and under/over-stock units in the app, a naive lag-1 row in the comparison table", "Planners see why a number moved and how much stock it risks"],
                ["3. Widen the data", "Full H&M, regions and promotions where available, a second retailer", "Results repeat on a window with a previous year"],
                ["4. Deploy", "Authentication, a database, scheduled retraining and monitoring", "Several users can work on separate datasets"]],
               widths=[1.5, 3.1, 2.0], align=["l", "l", "l"], size=10)


def future_blocks():
    return [
        H2("Repair the weaknesses found"),
        B("**Normalise the weights** to mean 1 and floor them, and report the effective sample size on screen; the offline study shows this removes the collapse on perfectly separable domains.",
          "**Make the time-clean protocol the default**: train the source model only on dates before the target test window, so the before-and-after comparison cannot gain from the future.",
          "**Refresh every calendar feature in the recursive loop**, update price and channel from a plan, and compare against a flat seven-day mean automatically.",
          "**Drop or regularise absolute-time features** (year, quarter, day of year) and keep duplicate rows, which are repeat purchases."),
        H2("Add features"),
        B("A **cold-start mode** that forecasts a new article from attributes, calendar and similar products, in the spirit of the new-product models in the literature " + C('ekam', 'cdlf') + ".",
          "**SHAP in the app** for global and per-forecast attribution, as in the base paper " + C('base') + ", plus an inventory view that turns error into under- and over-stock units.",
          "**Direct multi-horizon models and probabilistic forecasts** (quantiles) instead of recursion."),
        H2("Data, methods and deployment"),
        B("Run on the **full H&M dataset** and add promotion, regional and weather data where they exist; test transfer to a genuinely new market.",
          "Compare importance weighting with **CORAL and adversarial adaptation** " + C('coral', 'dann') + " and with simple pooling.",
          "Add **authentication, a database, multi-user sessions, scheduled retraining and drift monitoring**, and measure load on the full dataset."),
        P("The order matters: the repairs in the first stage are small, testable and should be done before any new feature is added, because the other stages build on a forecast that must at least match a flat seven-day mean."),
        _roadmap(),
    ]


def chapter10_blocks():
    body = [
        H2("Improvements to the existing system"),
        P("Every improvement below answers a defect that Chapter 8 measured, so each has a test it must pass."),
        B("**Normalise and floor the importance weights.** Rescaling the same weights to mean 1 removed the constant-prediction collapse on the department pairs in the offline study (Knitwear to Trouser from -46.3 to +1.9 percent). The product should do this by default and show the effective sample size beside the clipped share.",
          "**Time-clean adaptation by default.** Restrict source rows to dates before the target test window and report the gap to the current protocol, so a gain that comes from time overlap is visible.",
          "**A correct recursive forecast.** Refresh week of year, day of year, quarter and month-start flags, take price and channel from a plan, and accept the forecast only if it beats a flat seven-day mean on a backtest; otherwise fall back to that mean.",
          "**Remove the features that cannot extrapolate.** Year, quarter and day of year hurt on a window beyond the training dates; the lag-and-rolling-only model scored better.",
          "**Stop dropping duplicate rows,** and scale the features of the domain classifier so logistic regression converges."),
        P("Two of these repairs change numbers that appear in earlier chapters. Normalising the weights turns the two department pairs from the worst results of the study into neutral ones, and the time-clean protocol would replace the +12 percent headline of the first pair by a small loss. "
          "That is the intended effect: the default behaviour of the product should be the one that cannot flatter itself."),
        H2("Additional features"),
        P("The features below are ordered by how directly they answer the batch objectives that were only partly met: explanation of drivers (objective 5), inventory impact (objective 6) and new products (the problem statement)."),
        B("**Cold-start forecasting.** The offline test shows attributes and calendar reach R2 0.27 on unseen articles; a product mode with nearest-neighbour or diffusion-style life-cycle models " + C('ekam', 'cdlf') + " would serve new fashion items.",
          "**Explanations.** SHAP values per forecast in the console, ICE-style curves for the strongest features as in the base paper, and a naive lag-1 row in every comparison table.",
          "**Inventory view.** Convert error into under- and over-stock units, then into reorder points and cost, using service levels set per product class.",
          "**Probabilistic and direct multi-horizon forecasts** so that a planner sees a range, and error does not accumulate through recursion."),
        H2("Scalability and deployment"),
        P("TrendCast was built for one analyst and a sampled file. Its state is a Python dictionary, its upload is read whole into memory and its long operations hold one lock, which is enough for the 684,392-row subset (upload in 3.5 seconds, features in 0.9 seconds, a tuned model in 29.6 seconds) and not enough for a production system."),
        B("Replace the in-memory dictionary with a database and a job queue, so uploads, models and results belong to a user and survive restarts.",
          "Read the full 31.8-million-row file in chunks and aggregate to daily demand before it enters memory; the subset here loads in 3.5 seconds, the full file will not.",
          "Add authentication, a container build, scheduled retraining and drift monitoring based on the shift table and the classifier accuracy.",
          "Measure concurrent load; the current API serialises long operations behind one lock."),
        P("Deployment also needs a decision about who owns the data. The H&M files used here are public competition data; a retailer's own transactions would need access control, retention rules and an audit of what is sent to the optional Gemini service (today only aggregates, never rows)."),
        H2("Further research"),
        P("The open questions are scientific rather than engineering ones, and the offline harness is already set up to answer them once more data are available."),
        B("Compare importance weighting with CORAL and adversarial alignment " + C('coral', 'dann') + ", and with the simple pooled model that won here, on a window that includes a previous year.",
          "Test transfer to real new markets (stores, countries) and measure how many target rows are needed before adaptation beats pooling.",
          "Quantify the value of explanations: do planners override fewer forecasts when they see SHAP? The base paper's motivation " + C('base') + " is a trust gap that a user study could measure.",
          "Study hierarchical forecasting from article up to department with consistent totals."),
        H2("Risks and dependencies"),
        B("**Data access.** The full H&M files and any further retailer data must be obtained under their licences; the subset used here is not redistributed.",
          "**Evaluation drift.** Every repair must be judged on a window with a previous year in the training data, otherwise the Christmas-window result is simply repeated.",
          "**External services.** AI Insights depends on the availability and terms of the Gemini service; a local explanation (SHAP text) would remove the dependency."),
        P("The order of work matters: the repairs in the first section are small and testable, and they should be done before any new feature, because every later stage builds on a forecast that must at least match a flat seven-day mean and an adaptation step that must at least match simple pooling."),
        _roadmap(),
    ]
    if F.REPORT:
        body = _ch10_trim(body)
    return [H1("CHAPTER 10: FUTURE SCOPE")] + renum(body, "10")


def _ch10_trim(body):
    """Report variant: no roadmap table, no risks section, lead paragraphs and the last bullets of each list cut."""
    out, skip = [], False
    for b in body:
        if b[0] == "h2":
            skip = b[1].startswith("Risks")
        if skip or b[0] == "tab":
            continue
        if b[0] == "p" and b[1].startswith(("Two of these repairs", "The features below", "Deployment also needs", "The open questions", "The order of work", "Every improvement below")):
            continue
        if b[0] == "b" and len(b[1]) > 3:
            b = ("b", b[1][:3])
        out.append(b)
    return out
