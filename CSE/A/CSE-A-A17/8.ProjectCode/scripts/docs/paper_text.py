"""Text of 19.IEEE_Paper.docx (TrendCast). Every number is read from facts.py (experiments/**/metrics.json) or typed from docs/REPORT_FACTS.md.

Citations are written {r:key,key} (keys of refs.py); Paper.expand numbers them in order of first appearance, the base paper being [1].
"""
import os

from . import facts as F
from . import paper_figs
from .paper import Paper


def build(path):
    figs = paper_figs.make()
    P = Paper()
    FC, DOM, REC, EX, INV, COLD, API, DS = F.FC, F.DOM, F.REC, F.EX, F.INV, F.COLD, F.API, F.DS
    M = FC["models"]
    xs = FC["xgboost_seed_stats"]
    ab = FC["ablation"]
    bt = FC["rolling_origin"]
    pairs = DOM["pairs"]
    sm = DOM["summary"]
    on, st = pairs[0], pairs[1]          # channel 2 -> 1 and channel 1 -> 2
    dep = pairs[4]                       # Knitwear -> Trouser
    rx = REC["results"]
    xapp, flat = rx["xgb_app"], rx["flat_ma7"]
    ix, im = INV["XGBoost"], INV["Moving average (7d)"]
    cs = COLD
    lat = API["latency_ms"]
    stg = API["stages_seconds"]
    tune_s = FC["tuning_seconds"]
    import pandas as pd
    dd = pd.read_csv(os.path.join(F.EXP, 'forecasting', 'test_daily_series.csv'), parse_dates=['t_dat']).set_index('t_dat')

    def r2(k):
        return f"{M[k]['R2']:.3f}"

    authors = [[n.upper(), f"Roll No. {r}", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "Hyderabad, India", "[EMAIL]"] for n, r in F.STUDENTS]
    authors.append([F.GUIDE.upper(), f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "Hyderabad, India", "[EMAIL]"])
    P.title_block("TrendCast: Fashion Demand Forecasting Using Machine Learning and Domain Adaptation", authors)
    P.begin_two_columns()

    P.abstract(
        "A fashion retailer must forecast demand for thousands of short-lived articles, and a model trained in one sales context often loses accuracy in another. "
        "This paper presents TrendCast, a web application that turns retail transactions into daily units sold per article, forecasts them with XGBoost from 31 calendar, price, attribute, lag and rolling features, "
        "and offers importance-weighted domain adaptation, in which a logistic domain classifier supplies a weight p/(1-p) for every source-domain row. "
        f"We evaluate it on a real subset of the H&M retail data: {DS['articles']} best-selling articles, {DS['raw_rows']:,} transactions and {107} days. "
        f"On a chronological test window XGBoost reaches RMSE {M[F.XGB]['RMSE']:.2f} against {M[F.MA]['RMSE']:.2f} for a moving average, but not against repeating yesterday's value ({M['Naive (lag 1)']['RMSE']:.2f}). "
        f"As shipped, adaptation lowers the target error on {sm['pairs_where_adaptation_helped']} of {sm['pairs_total']} source-target pairs; the one clear gain disappears when source rows that overlap the test dates are removed, "
        "and unnormalised weights can make the model collapse to a constant. We report these findings with controls, a one-line repair, and the measured speed of the software.",
        ["covariate shift", "demand forecasting", "domain adaptation", "fashion retail", "importance weighting", "XGBoost"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Fashion retail is driven by short product life cycles, seasons and promotions. Planners usually set stock from last year's sales and personal judgement; an over-forecast leaves unsold stock, "
           "an under-forecast loses the sale. Gradient-boosted trees are now the usual learner for such tabular demand data {r:base,m5}, and the base paper of this work adds layered explanations so that planners can trust them {r:base}. "
           "Two difficulties remain. A model fitted on one market, channel or product group is then used on another whose data are distributed differently, and its accuracy falls; and new articles have no history at all. "
           "Domain adaptation, which moves what was learned in a source domain to a shifted target domain {r:pan}, is the natural remedy, but it is rarely reported with controls that show whether it really helped.")
    P.para("Today a merchandiser typically combines a spreadsheet of last season's sales, a seasonal index and judgement, and then corrects the plan by hand when sales diverge. This is cheap but slow, "
           "it cannot use price, colour, department or promotion effects together, and it carries no measure of its own error. Machine-learning forecasts remove part of that work, yet they raise their own questions "
           "that planners ask first: is the model better than the naive rule they already use, will it still work in the next channel or season, and what does it get wrong? "
           "TrendCast is built so that these questions can be answered from its own screens and scripts.")
    P.para("This paper makes four contributions. (1) TrendCast, a tested pipeline and web console (FastAPI, React) from raw H&M-style files to forecasts, with a gate before every step. "
           "(2) An honest comparison of XGBoost with simple and tree baselines on real data, including a feature-group ablation and a rolling-origin backtest. "
           f"(3) A six-pair study of importance-weighted adaptation with five seeds and four controls (target-only model, pooled data, shuffled weights, time-clean source), which exposes two defects of the shipped method. "
           "(4) Offline measurements the product itself does not show: exact TreeSHAP attribution, inventory-unit impact and unseen-article error. "
           "Section II reviews related work, Section III describes the method, Section IV gives the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("All numbers were measured on one machine: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11 Pro, no GPU, with other jobs running at the same time.")
    P.sub("B", "Software Requirements")
    P.para("Python 3.11.9, scikit-learn 1.5.0 {r:sk}, XGBoost 2.0.3 {r:xgb}, LightGBM 4.7.0 {r:lgbm} (baseline only), pandas 2.2.1, NumPy 1.26.4, FastAPI 0.143.3; the console uses React 19, Vite 8 and Recharts. "
           "Tests use pytest and Playwright; the optional AI explanation calls the Gemini REST service.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Mishra et al. {r:base} forecast one-day-ahead SKU demand on UCI Online Retail II (1.07 million transactions, 4,631 SKUs) with LightGBM and 41 engineered features, tuned by Optuna (30 trials, three time-series folds), "
           "and compare it with naive lag-1, a 7-day moving average, linear regression, random forest {r:rf}, XGBoost and CatBoost. LightGBM reaches RMSE 33.71 and R2 0.243; CatBoost (33.83, p = 0.917) and XGBoost (33.89) are statistically close, and MASE is 0.799. "
           "Their contribution is explanation: permutation importance, partial dependence, SHAP {r:shap,treeshap} and ICE curves, with rolling statistics the dominant feature group (removing them changes R2 by -0.064). "
           "They state that validation uses a single dataset, that relationships are assumed stationary, that external factors are excluded and that one step ahead limits planning. Domain shift is not addressed.")
    P.para("**Boosting and competitions.** XGBoost {r:xgb} and LightGBM {r:lgbm} made boosted trees the default for tabular data, and in the M5 retail competition boosted trees with hand-built features matched or beat deep models {r:m5}. "
           "**Covariate shift.** When training and test inputs have different distributions, weighting each training row by the density ratio p_target(x)/p_source(x) restores consistency {r:shim}; "
           "a discriminative source-versus-target classifier estimates that ratio without density estimation {r:bickel}, importance-weighted validation selects models under shift {r:sugi}, and a learning bound ties target error to a domain divergence {r:bendavid}. "
           "Neural variants make features domain-invariant {r:dann}. **Fashion.** Thomassey {r:thom} reviews clothing sales forecasting, where volatile demand, seasonality and short-lived items dominate; "
           "recent work forecasts new fashion items from attributes {r:singh}, images and attributes with attention {r:ekam}, or images with Google Trends {r:skend}.")
    P.table("Related work compared", ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [["Mishra et al. {r:base}", "LightGBM + PFI, PDP, SHAP, ICE", "UCI Online Retail II, 4,631 SKUs", "RMSE 33.71, R2 0.243", "One dataset; no shift"],
             ["Bickel et al. {r:bickel}", "Logistic-classifier covariate-shift weights", "Benchmark tasks", "No density estimate needed", "Needs overlap"],
             ["Shimodaira {r:shim}", "Density-ratio weighted likelihood", "Theory, simulation", "Consistent if mis-specified", "Large weights"],
             ["Ekambaram et al. {r:ekam}", "Attention, images + attributes", "Large fashion data", "Beats k-NN baselines", "Needs images, history"],
             ["Singh et al. {r:singh}", "Attribute models, new items", "Fashion sales", "Finds demand drivers", "No market transfer"],
             ["Skenderi et al. {r:skend}", "Images + Google Trends", "VISUELLE, 5,577 items", "Whole-horizon forecast", "External signals"]],
            [0.62, 0.74, 0.66, 0.7, 0.68], size=6.0, align=["l", "l", "l", "l", "l"])
    P.para("**Gap.** The surveyed work either applies gradient boosting with explanations to one retail market, or builds neural models for new fashion items. A gradient-boosted demand model moved to a differently distributed domain by a simple, "
           "inspectable adaptation step, and then checked against honest controls, is not reported. TrendCast implements that step and tests it.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Architecture and Implementation")
    P.figure(figs["arch"], "TrendCast architecture: React console, FastAPI service with 22 routes over the src/ package, in-memory state and three model files; there is no database.", 3.3)
    P.para("After an upload the console shows a data-quality report (rows read and removed, missing values, duplicates, date range, customers and products), then exploration charts of daily, weekly and monthly demand, "
           "the ten best-selling articles and demand by department, colour and channel, so that the analyst sees what cleaning removed before any model is fitted. "
           "The FastAPI service keeps one pipeline state behind a lock. Each route calls the same src/ functions as the original Streamlit page; later steps answer HTTP 409 with a plain message until earlier ones are done, "
           "bad files or parameters return 400 or 422, and the Gemini route returns 502 or 503 when the service is unreachable. The React console has 13 pages. The 7, 14 or 30-day forecast is recursive: "
           "each predicted value is appended to the history that builds the next day's lag and rolling features. "
           f"The code is checked by {F.PYTEST_PASSED} pytest tests ({F.PYTEST_UNIT} unit, {F.PYTEST_API} API; all pass) and a {F.SMOKE_PASSED}-check end-to-end smoke test (all pass).")

    P.sub("B", "Data and Preparation")
    P.para(f"We use the H&M Personalized Fashion Recommendations data {{r:hm}}: transactions (date, customer, article, price, sales channel 1 or 2), articles (type, group, colour, department, section, garment group) and customers. "
           f"The first transaction shard (2018-09-20 to 2019-01-04) was restricted to its {DS['articles']} best-selling articles, giving {DS['raw_rows']:,} rows and {DS['customers']:,} customers. "
           f"Cleaning parses dates, drops rows with missing ids or non-positive price, and removes exact duplicate rows ({DS['raw_rows'] - DS['clean_rows']:,} rows, 11.6 %); the files code the channels only as 1 and 2. "
           f"Rows are then left-joined to the article table and counted per article and day, which gives the target y = units sold. Missing days between an article's first and last sale are filled with zero, "
           f"producing {DS['feature_rows']:,} article-days ({DS['zero_demand_share_pct']:.1f} % zero).")
    P.sub("C", "Features")
    P.para("The 31 model inputs are price, sales channel, six label-encoded attributes, fourteen calendar features and nine lag and rolling features. Month m and weekday d are also encoded cyclically,")
    P.eq("x_sin = sin(2πt/T),   x_cos = cos(2πt/T)")
    P.para("with T = 12 and 7. Lags are y(t-k) for k = 1, 7, 14, 28; rolling means (7, 14, 28 days) and standard deviations (7, 28) are computed on y shifted by one day, so the current day never enters its own features. "
           "The split is chronological: the first 80 % of dates train, the last 20 % test.")
    P.sub("D", "Model and Baselines")
    P.para(f"XGBoost {{r:xgb}} fits the regularised objective sum l(y, ŷ) + Σ Ω(f_k) with squared error, 300 trees, depth 8, learning rate 0.05, subsample and column sampling 0.8. "
           f"Optional tuning is a randomised search {{r:bergstra}} of 10 draws over six parameters with three time-ordered folds. Baselines are a 7-day moving average (the product's own), repeating yesterday, "
           f"random forest, and LightGBM. Metrics are RMSE, MAE, R2, MAPE on non-zero days (zero days are counted and excluded) and WAPE = Σ|y-ŷ| / Σy.")
    P.eq("RMSE = sqrt( mean (y - ŷ)² ),    WAPE = Σ|y - ŷ| / Σy,    safe MAPE = mean_{y>0} |y - ŷ| / y")
    P.para("Plain MAPE is undefined on days with no sales, which are common for single articles, so the product reports the average over days with y > 0 and states how many rows were left out. "
           "We add WAPE because it weights each article-day by its volume and so stays stable when many days are small, and R2 because it compares the model with always predicting the mean of the test window; a negative R2 therefore means worse than that constant.")
    P.sub("E", "Importance-Weighted Domain Adaptation")
    P.para("Source rows come from one value of a domain column (sales channel, product group or department), target rows from another; the column itself is removed from the inputs. "
           "A source-only model gives the before-adaptation error on the later half of the target dates. A logistic regression trained to separate source from target rows returns p = P(target | x), and each source row receives")
    P.eq("w(x) = min( p(x) / (1 - p(x)), 20 )")
    P.para("which equals the density ratio p_target/p_source up to a constant {r:shim,bickel}. XGBoost is refitted with these sample weights and scored on the same target rows. "
           "We add controls: a target-only model trained on the first half of the target dates, source plus target-train pooled without weights, shuffled weights, weights rescaled to mean 1, "
           "and a time-clean variant that drops source rows dated after the start of the target test window.")
    P.figure(figs["flow"], "Method: cleaning to features and the date split (left), and the domain-adaptation procedure (right); forecasts are made recursively.", 3.3)
    P.sub("F", "Evaluation Protocol and Reproducibility")
    P.para("Every number comes from scripted experiments that write JSON files. Forecast accuracy uses the single chronological split and a three-fold rolling-origin backtest; XGBoost is repeated with five random seeds (42-46) "
           "because row and column sampling make it stochastic. Domain pairs are scored on the later half of the target dates only, so no target test row is ever used for training or for estimating weights except through the unlabelled inputs "
           "of the domain classifier, which sees target rows without their demand. The multi-day forecast is scored on the 30 days after an origin at which the model was trained, against the demand actually observed. "
           "Offline extras are SHAP values from XGBoost's built-in exact tree routine (they sum to the prediction to within 1e-4), error expressed as under- and over-forecast units, and a five-fold group split by article for unseen articles. "
           "The experiments, the tests and the screenshot capture can be rerun with one command each; the LightGBM baseline needs the library to be imported before pandas on this machine, which is noted in the installation guide.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.sub("A", "Test Conditions and Forecast Accuracy")
    P.para(f"The test window has {FC['split']['test_rows']} article-days from {FC['split']['test_start'][:10]} to {FC['split']['test_end'][:10]}, which contains the Christmas peak and the January sales, "
           f"while the training window ({FC['split']['train_start'][:10]} to {FC['split']['train_end'][:10]}) holds no earlier year. XGBoost seeds vary little (RMSE {xs['RMSE']['mean']:.3f} ± {xs['RMSE']['std']:.3f}, five seeds). "
           f"Table II shows that XGBoost beats the product's moving average (RMSE {M[F.XGB]['RMSE']:.2f} against {M[F.MA]['RMSE']:.2f}) but not repeating yesterday ({M['Naive (lag 1)']['RMSE']:.2f}) or the shifted 7-day rolling mean ({M['Rolling mean 7 (shifted)']['RMSE']:.2f}); "
           f"tuning ({tune_s:.0f} s) and LightGBM close part of the gap ({M[F.XGB_T]['RMSE']:.2f} and {M['LightGBM']['RMSE']:.2f}).")
    order = ["Naive (lag 1)", "Rolling mean 7 (shifted)", "LightGBM", F.XGB_T, F.XGB, F.MA, "Random forest"]
    names = {F.XGB: "XGBoost (default, 5 seeds)", F.XGB_T: "XGBoost (tuned)", F.MA: "Moving average (7 d)", "Rolling mean 7 (shifted)": "Rolling mean 7 d"}
    P.table("Test-window accuracy, real H&M subset", ["Model", "RMSE", "MAE", "R2", "WAPE %"],
            [[names.get(k, k), f"{M[k]['RMSE']:.2f}", f"{M[k]['MAE']:.2f}", f"{M[k]['R2']:.3f}", f"{M[k]['WAPE (%)']:.1f}"] for k in order],
            [1.45, 0.45, 0.45, 0.5, 0.55], size=7.0, align=["l", "c", "c", "c", "c"])
    P.para(f"Mean absolute and percentage errors look large because demand is small and noisy: the mean article-day sells 19.5 units and MAPE, computed on non-zero days, is {M[F.XGB]['MAPE (%)']:.0f} % for XGBoost. "
           f"Summed over all articles per day the picture is different: daily-total WAPE is {FC['test_daily_totals_error']['xgb_daily_wape_pct']:.1f} % for XGBoost and {FC['test_daily_totals_error']['ma_daily_wape_pct']:.1f} % for the moving average, "
           "so the moving average tracks the aggregate level better even though XGBoost is more accurate article by article. "
           f"Figure 3 shows the cause: XGBoost follows the rise to the pre-Christmas peak, but on 25 December and 1 January it predicts {dd.loc['2018-12-25','xgb']:,.0f} and {dd.loc['2019-01-01','xgb']:,.0f} units when {dd.loc['2018-12-25','demand']:,.0f} and {dd.loc['2019-01-01','demand']:,.0f} were sold. "
           "No input flags holidays (the calendar encodes dates, not public holidays, and a lag feature cannot foresee a one-day drop), a gap that matters in fashion retail. "
           "The tuned model uses depth 12, 400 trees and a learning rate of 0.01 and is still not better than repeating yesterday.")
    P.figure(figs["daily"], "Daily units sold over the test window (sum of the 300 articles) with the XGBoost and moving-average forecasts; XGBoost follows the pre-Christmas rise but not the drops on 25 December and 1 January.", 3.3)
    a_all, a_nolag, a_cal, a_lag = ab["all features (as shipped)"], ab["no lag / rolling"], ab["calendar only"], ab["lag / rolling only"]
    P.para(f"The ablation explains why. Without lag and rolling features RMSE rises to {a_nolag['RMSE']:.2f} (R2 {a_nolag['R2']:.2f}); calendar features alone give {a_cal['RMSE']:.2f} (R2 {a_cal['R2']:.2f}). "
           f"A model using only the nine lag and rolling features scores {a_lag['RMSE']:.2f} (R2 {a_lag['R2']:.2f}) and beats the shipped 31-feature model ({a_all['RMSE']:.2f}), because absolute-time inputs such as quarter and day of year cannot extrapolate beyond the training dates. "
           f"In a three-fold rolling-origin backtest XGBoost beats the moving average in every fold (for example {bt[2]['xgboost']['RMSE']:.2f} against {bt[2]['moving_average']['RMSE']:.2f}) but beats repeating yesterday only in the first ({bt[0]['xgboost']['RMSE']:.2f} against {bt[0]['naive_lag1']['RMSE']:.2f}); "
           "this agrees with the base paper's finding that rolling statistics dominate.")
    P.sub("B", "Recursive Multi-Day Forecast")
    P.para(f"From the origin {REC['origin']}, over {REC['articles_scored']} articles, the app's recursive forecast has WAPE {xapp['by_band'][0]['WAPE (%)']:.0f} %, {xapp['by_band'][1]['WAPE (%)']:.0f} % and {xapp['by_band'][2]['WAPE (%)']:.0f} % on days 1-7, 8-14 and 15-30, "
           f"against {flat['by_band'][0]['WAPE (%)']:.0f} %, {flat['by_band'][1]['WAPE (%)']:.0f} % and {flat['by_band'][2]['WAPE (%)']:.0f} % for a flat mean of the last seven days. "
           "Refreshing the calendar features that the loop leaves frozen did not help. The multi-day feature should therefore be read as indicative only.")
    P.sub("C", "Domain Adaptation")
    P.figure(figs["results"], "Change in target RMSE from adaptation for six source-target pairs (positive is better), as shipped and with two repairs; Ch1, Ch2 are sales channels.", 3.3)
    P.para(f"Averaged over five seeds, adaptation as shipped lowers target RMSE on {sm['pairs_where_adaptation_helped']} of {sm['pairs_total']} pairs (mean {sm['mean_rmse_improvement_pct']:+.1f} %, range {sm['min']:+.1f} % to {sm['max']:+.1f} %). "
           f"The only clear gain is channel 2 to channel 1: RMSE {on['app']['before']['RMSE']['mean']:.2f} to {on['app']['adapted']['RMSE']['mean']:.2f} ({on['app']['rmse_improvement_pct_mean']:+.1f} %, better in {on['app']['adapted_beats_before_in_seeds']} of 5 seeds). "
           f"It is not an adaptation effect: with the time-clean source it becomes {on['time_clean']['rmse_improvement_pct_mean']:+.1f} %, and shuffled weights already give {on['app']['shuffled_improvement_pct_mean']:+.1f} %. "
           f"Channel 1 to channel 2 changes by {st['app']['rmse_improvement_pct_mean']:+.2f} %, and the product-group pairs worsen by {abs(pairs[2]['app']['rmse_improvement_pct_mean']):.1f} % and {abs(pairs[3]['app']['rmse_improvement_pct_mean']):.1f} %.")
    P.para(f"The department pairs fail badly ({dep['app']['rmse_improvement_pct_mean']:+.1f} % for knitwear to trousers). There the domain classifier separates the domains perfectly (accuracy {dep['diagnostics']['clf_accuracy'] * 100:.0f} %), so p/(1-p) is tiny for every source row "
           f"(mean weight {dep['diagnostics']['w_mean']:.1e}); XGBoost's minimum child weight of 1 can then never be met, the trees stop splitting and the model predicts a constant (R2 {dep['app']['adapted']['R2']['mean']:.2f}). "
           f"Rescaling the same weights to mean 1 removes the collapse ({dep['app']['normalised_improvement_pct_mean']:+.1f} %), and the mean change over all pairs improves from {sm['mean_rmse_improvement_pct']:+.1f} % to {sm['normalised_mean_rmse_improvement_pct']:+.1f} %. "
           f"Under the time-clean protocol the mean is {sm['time_clean_mean_rmse_improvement_pct']:+.1f} %, and with both repairs {sm['normalised_time_clean_mean_rmse_improvement_pct']:+.1f} %: adaptation is neutral. "
           f"Simply pooling the source with the first half of the target, without weights, beats weighted adaptation on five of six pairs, and a target-only model is worse than the source-only model on five of six, because half of a small target is too little data.")
    dr = []
    short = ["Ch2→Ch1", "Ch1→Ch2", "Upper→Lower", "Lower→Upper", "Knit→Trouser", "Jersey→Blouse"]
    for lab, p in zip(short, pairs):
        e, dg = p["app"], p["diagnostics"]
        dr.append([lab, f"{dg['clf_accuracy'] * 100:.0f}", f"{e['before']['RMSE']['mean']:.2f}", f"{e['adapted']['RMSE']['mean']:.2f}",
                   f"{e['pooled_unweighted']['RMSE']['mean']:.2f}", f"{e['target_only_oracle']['RMSE']['mean']:.2f}"])
    P.table("Domain adaptation, target RMSE (mean of 5 seeds)", ["Pair", "Clf acc %", "Source-only", "Adapted", "Pooled", "Target-only"], dr,
            [0.85, 0.45, 0.58, 0.5, 0.5, 0.52], size=6.8, align=["l", "c", "c", "c", "c", "c"])
    P.para("Table III also shows why the pairs behave differently. The channel pairs are only weakly separable (classifier accuracy 66 %), so the weights stay in a moderate range and adaptation changes little. "
           "Product groups and departments are separated almost perfectly by the encoded attributes that remain in the inputs, which leaves no overlap between the domains: "
           f"for upper body to lower body only {pairs[2]['diagnostics']['ess_share_pct']:.0f} % of the rows carry effective weight and {pairs[2]['diagnostics']['clipped_share_pct']:.1f} % are clipped at 20. "
           "Importance weighting needs overlap between source and target inputs {r:shim,bendavid}; where the domains are close to disjoint, a model cannot be moved by re-weighting rows, and the honest remedy is target data, as the pooled column shows. "
           "The shuffled-weights control is the safeguard against over-reading small gains: it gives the weights the same distribution but attaches them to random rows, so any improvement it also shows is noise or a side effect of re-weighting rather than of the learned density ratio. "
           f"Each XGBoost run is stable (RMSE standard deviation across seeds up to {max(p['app']['before']['RMSE']['std'] for p in pairs):.2f}), so the differences in the table are not seed noise except on the smallest target.")
    P.sub("D", "Explanations, Inventory Impact and New Articles")
    P.para(f"The app shows gain importance (top features is_month_end, lag_1, quarter). Exact TreeSHAP values, computed offline with XGBoost's own routine, rank lag_1 first (mean |SHAP| {EX['top10_by_shap'][0]['mean_abs_shap']:.1f} units) and agree only moderately with gain (Spearman {EX['spearman_rank_corr_shap_vs_gain']:.2f}): "
           f"gain over-rates calendar features that split often but contribute little. On the test window XGBoost over-forecasts total demand by {ix['bias_pct']:.1f} % yet under-forecasts {ix['understock_pct_of_demand']:.1f} % of units sold and over-forecasts {ix['overstock_pct_of_demand']:.1f} %; "
           f"the moving average under-forecasts {im['understock_pct_of_demand']:.1f} % and over-forecasts {im['overstock_pct_of_demand']:.1f} %. For articles never seen in training, attributes and calendar alone give R2 {cs['attributes_calendar_only_unseen_article']['R2']:.2f} "
           f"(product-type mean {cs['product_type_mean_baseline_unseen_article']['R2']:.2f}), against {cs['full_features_unseen_article_lags_assumed_known']['R2']:.2f} when the article's own history is known; the product itself has no cold-start mode.")
    P.sub("E", "Output Screens and Speed")
    P.figure(F.shot("16_domain-before-after.png"), "TrendCast domain-adaptation screen on the real subset: shift histogram and box plot of the most shifted feature, and the before-and-after cards (channel 1 to channel 2).", 3.3)
    P.figure(F.shot("19_forecast.png"), "TrendCast forecast screen: 60 days of history and a 14-day recursive forecast for one article, with the forecast table below.", 3.3)
    P.para(f"On the 684,392-row subset, upload with cleaning takes {stg['upload+clean+merge (684k rows)']:.1f} s, building features {stg['build features']:.1f} s, default XGBoost training {stg['train XGBoost (default)']:.1f} s, "
           f"tuning {stg['train XGBoost (tuned)']:.0f} s and a domain run {stg['domain adaptation run']:.1f} s; a 30-day forecast has a median latency of {lat['POST /api/forecast (30 d)']['median']:.0f} ms.")
    P.sub("F", "Comparison with the Base Paper")
    P.para("The base paper and this work use different data (UCI Online Retail II, a UK wholesaler, against H&M fashion sales), different aggregation and metric scales, so absolute figures cannot be compared. "
           f"Relative findings can: the base paper's LightGBM is 7.8 % better in RMSE than its moving average (33.71 against 36.57) and 29.4 % better than naive lag-1 (47.77), whereas XGBoost here is "
           f"{(1 - M[F.XGB]['RMSE'] / M[F.MA]['RMSE']) * 100:.1f} % better than the moving average but {(M[F.XGB]['RMSE'] / M['Naive (lag 1)']['RMSE'] - 1) * 100:.1f} % worse than lag-1. "
           f"Both studies find lag and rolling features dominant (base paper: R2 change of -0.064 on removal; here R2 falls from {a_all['R2']:.2f} to {a_nolag['R2']:.2f}). "
           "Our R2 (0.335) is higher than the base paper's 0.243 only because the series, window and target differ.")
    P.sub("G", "Failure Cases and Observed Limits")
    P.para("The window is 107 days of 300 best-selling articles, so no yearly seasonality can be learned and the test period is atypical. Cleaning removes repeat purchases that are real demand. "
           "The sales-channel and price of the target day are model inputs and are frozen during recursive forecasts; the domain label is the day's most frequent channel although demand counts both channels. "
           "The domain classifier does not converge on unscaled features. The product does not show SHAP or inventory impact, and the AI explanation depends on an external service that answered 503 or timed out when the screens were captured. "
           "No user study, load test or full-size data run was done. "
           "Two further threats to validity apply to every number above. The 300 articles are the best sellers of one shard, so they sell on most days and are easier to forecast than the long tail of articles that sell rarely; "
           "and the test window is a single three-week period, so a different window, such as a quiet month, could change the ranking of the models, although the three backtest folds point the same way. "
           "The comparison with the base paper is therefore a comparison of findings, not of scores.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion and Future Scope")
    P.para(f"TrendCast delivers a complete, tested path from retail transactions to forecasts and an inspectable domain-adaptation experiment. Against its objectives, the forecasting model beats the product's own baseline "
           f"(RMSE {M[F.XGB]['RMSE']:.2f} against {M[F.MA]['RMSE']:.2f}) but not repeating yesterday; explanations are partly met (gain importance in the app, SHAP offline); error is translated to inventory units only offline. "
           f"The central finding is negative and useful: as shipped, importance-weighted adaptation helps on {sm['pairs_where_adaptation_helped']} of {sm['pairs_total']} pairs, its one clear gain comes from time overlap, "
           "and unnormalised weights can collapse the model; with repairs it is neutral, and plain pooling does better. The limits are the short 107-day window, one data shard, mixed-channel domains and no new-product mode.")
    P.para("Practical use follows from the findings. A planner who adopts TrendCast should treat the repeat-yesterday and rolling-mean forecasts as the bar to beat, keep the multi-day forecast for orientation only, "
           "check any adaptation against a pooled model and a time-clean split before trusting it, and read the AI explanation as a summary of the shown numbers, not as new evidence.")
    P.para("Future work: normalise weights and use the time-clean protocol by default; refresh calendar features in recursive forecasts and add direct multi-horizon and probabilistic models; "
           "drop absolute-time inputs or add last-year seasonality from the full two-year data; add a cold-start model from attributes and images; show SHAP and inventory cost in the console; "
           "and test other adaptation methods such as adversarial or correlation alignment {r:dann} on regional or store domains.")

    P.references()
    P.save(path)
    return path
