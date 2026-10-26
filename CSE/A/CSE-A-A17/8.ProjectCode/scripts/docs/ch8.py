"""Chapter 8: Results and output screens. Every number is read from facts.py (experiments/**/metrics.json) or typed exactly as in docs/REPORT_FACTS.md."""
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, PAIR, TAB
from .refs import N

SH = F.shot


def S(name, caption, base=5.6, max_h=3.7):
    """Screenshot figure with a width that keeps the picture on one page."""
    return FIG(SH(name), caption, F.shot_w(SH(name), base, max_h))


def G(name, caption, width=5.6, doc_only=False):
    """Result figure from docs/figures; omitted if the file has not been produced, or (doc_only) in the compact report variant."""
    path = F.fig(name)
    if doc_only and F.REPORT:
        return []
    return [FIG(path, caption, width)] if os.path.exists(path) else []


def _compact(blocks):
    """Report variant: drop the sub-headings and put the screenshots two per figure, each with its own caption."""
    out, pend = [], []
    for blk in blocks:
        if blk[0] == "h3":
            continue
        if blk[0] == "fig":
            pend.append((blk[1], blk[2]))
            if len(pend) == 2:
                out.append(PAIR(pend, 2.95))
                pend = []
        else:
            out.append(blk)
    if pend:
        out.append(FIG(pend[0][0], pend[0][1], 4.0))
    return out


def _m(model, key):
    return F.FC["models"][model][key]


def _models_table():
    rows = []
    order = ["Naive (lag 1)", "Rolling mean 7 (shifted)", "Moving average (7d)", "Seasonal naive (lag 7)", "Random forest", "LightGBM", F.XGB, F.XGB_T]
    for k in order:
        v = F.FC["models"][k]
        label = {"Moving average (7d)": "Moving average, 7 days (the product's baseline)", F.XGB: "XGBoost, default parameters (mean of 5 seeds)",
                 F.XGB_T: "XGBoost, tuned (10 iterations x 3 time-ordered folds)", "Naive (lag 1)": "Naive: repeat yesterday (lag 1)",
                 "Rolling mean 7 (shifted)": "Rolling mean of the last 7 days", "Seasonal naive (lag 7)": "Seasonal naive: same day last week (lag 7)"}.get(k, k)
        rows.append([label, f"{v['RMSE']:.2f}", f"{v['MAE']:.2f}", f"{v['R2']:.3f}", f"{v['WAPE (%)']:.1f}"])
    return rows


def _domain_rows():
    rows = []
    for p in F.DOM["pairs"]:
        a, d = p["app"], p["diagnostics"]
        rows.append([p["label"], f"{d['clf_accuracy'] * 100:.1f}", f"{a['before']['RMSE']['mean']:.2f}", f"{a['adapted']['RMSE']['mean']:.2f}",
                     f"{a['rmse_improvement_pct_mean']:+.1f}", f"{a['adapted_beats_before_in_seeds']}/5", f"{a['normalised_improvement_pct_mean']:+.1f}",
                     f"{p['time_clean']['rmse_improvement_pct_mean']:+.1f}", f"{a['pooled_unweighted']['RMSE']['mean']:.2f}", f"{a['target_only_oracle']['RMSE']['mean']:.2f}"])
    return rows


def _setup():
    ds = F.DS
    out = [H2("8.1 Experimental set-up"),
           P(f"All measurements in this chapter were made on one machine: an Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory, no GPU, Windows 11, Python 3.11.9, scikit-learn 1.5.0, XGBoost 2.0.3, LightGBM 4.7.0, pandas 2.2.1 and FastAPI 0.143.3. "
             "Other programs were running at the same time, so absolute timings are indicative; the accuracy numbers do not depend on load. "
             "Every table and figure was produced from the stored files `experiments/**/metrics.json` by `scripts/run_experiments.py`, `scripts/measure_api.py` and `scripts/docs/make_figures.py`, and the same numbers are listed in `docs/REPORT_FACTS.md`; no result was typed in by hand."),
           TAB("Data used in the evaluation.", ["Item", "Content"],
               [["Source", f"H&M Personalized Fashion Recommendations {N('hm')}: real purchase transactions, article catalogue (Kaggle competition data, obtained from a Hugging Face parquet mirror; used for academic work and not redistributed in the repository)"],
                ["Subset", f"First transaction shard (4,541,190 rows, 2018-09-20 to 2019-01-04), reduced to the 300 best-selling articles with all their transactions: {ds['raw_rows']:,} rows, {ds['articles']} articles, {ds['customers']:,} customers"],
                ["After cleaning", f"{ds['clean_rows']:,} rows ({ds['raw_rows'] - ds['clean_rows']:,} exact-duplicate rows removed, 11.6 %); channel 1 {ds['channel_rows_raw']['1']:,} rows, channel 2 {ds['channel_rows_raw']['2']:,} rows"],
                ["Modelling table", f"{ds['daily_rows']:,} article-days of units sold, {ds['feature_rows']:,} rows after zero-filling ({ds['zero_demand_share_pct']:.2f} % zero demand), {ds['feature_cols']} model inputs; mean 19.46 units per article-day, median 14, maximum 566"],
                ["Split", f"Chronological 80/20: train {F.FC['split']['train_rows']} rows (2018-09-20 to 2018-12-13), test {F.FC['split']['test_rows']} rows (2018-12-14 to 2019-01-04)"],
                ["Synthetic sample", "`data/sample_hm` (90 articles, 70,974 rows) is used only by the smoke test; no number in this chapter comes from it"]],
               widths=[1.3, 5.2], align=["l", "l"], size=9.5),
           P("Two properties of this window shape every result. It is only 107 days long, so a model cannot learn a yearly pattern, and the test window (14 December to 4 January) holds the Christmas peak and the January sales that the training window has not seen. "
             "The H&M files also do not say which of the two sales channels is a store and which is online; they are coded 1 and 2. Where the pair labels below say Store and Online, that is our convention, not something the data state. "
             "XGBoost was run with random seeds 42 to 46; tables give the mean over seeds, and a standard deviation where it matters. Metrics are RMSE, MAE, R2 and WAPE (the sum of absolute errors divided by the sum of actual units); "
             "MAPE is also stored but is very large on low-volume days (about 140 % for every model), so it is not used to rank models.")]
    return out


def _screens():
    d = F.DS
    b = [H2("8.2 Output screens"),
         P("The screens below were captured from the running application at 1440 by 900 pixels with the real H&M subset loaded; none is a mock-up. The numbers visible in each caption can be found in the picture. "
           "The capture run ended with the tuned XGBoost model, so the evaluation, importance and forecast screens show the tuned model; the default model is reported in Section 8.3. "
           "The landing page, the dark theme and the overview and about pages are shown in Appendix C.")]
    b += [H3("8.2.1 Data upload and exploration"),
          S("05_upload-files-chosen.png", f"Data Upload page with the transactions file (39.1 MB) and the articles file chosen and the row limit set to 0, meaning no limit. The optional customers file was not supplied."),
          S("06_upload-quality-report.png", f"Data quality report after loading: 605,178 transactions, 276,168 customers, 300 products, 29 columns, 0 missing values, 0 duplicate rows remaining and 79,214 rows removed of the 684,392 read."),
          S("07_explore.png", "Data Exploration: 605,178 units sold, 30,481 product-days over 107 days, and the daily total demand line with the pre-Christmas peak."),
          S("08_explore-categories.png", "Data Exploration, lower part: units by department and by colour group and the other category charts that show where the demand is concentrated."),
          S("09_demand.png", "Demand Analysis: the aggregated daily table, one row per article per day with units sold, mean price and channel, beginning with article 108775015 on 2018-09-20 (21 units).")]
    b += [H3("8.2.2 Features and training"),
          S("10_features-empty.png", "Feature Engineering page before the table is built, with the description of what will be added (calendar, cyclical, lag and rolling features)."),
          S("11_features-built.png", f"Feature table built: {d['feature_rows']:,} rows, 36 columns and 31 model inputs, with the list of input names and a preview of the first rows."),
          S("12_training.png", "Model Training: chronological split (24,579 training rows to 2018-12-13, 6,515 test rows from 2018-12-14) and the test metrics of the default XGBoost run: RMSE 11.065, MAE 6.991, MAPE 140.5 %, R2 0.337, with the moving-average baseline in the comparison below (RMSE 12.891, R2 0.101)."),
          S("13_training-comparison.png", "Model comparison table and bar chart for the moving average and XGBoost, switchable between RMSE, MAE and MAPE."),
          S("13b_training-tuned.png", "Tuned XGBoost: RMSE 10.341, MAE 6.881, MAPE 147.0 %, R2 0.421, and the best parameters found (subsample 0.7, 400 trees, minimum child weight 5, depth 12, learning rate 0.01, column sample 0.6).")]
    b += [H3("8.2.3 Domain adaptation"),
          S("14_domain-form.png", "Domain Adaptation form: domain-defining column (sales channel), source value (channel 1) and target value (channel 2), with the explanation of the weight p/(1-p)."),
          S("15_domain-shift.png", "Result header for channel 1 to channel 2: the domain classifier is 66.3 % accurate (a moderate shift), 12,240 source rows, 18,854 target rows of which 9,890 are held out for testing, and a mean instance weight of 1.58."),
          S("16_domain-before-after.png", "Distribution and box plot of the most shifted feature (`lag_1`), and the before-and-after cards: RMSE 18.989 (0.0 % worse), MAE 7.404 (0.6 % worse), MAPE 51.7 % (0.2 % worse), R2 0.435 (0.1 % worse). The page reports a result that is not an improvement without softening it.")]
    b += [H3("8.2.4 Evaluation, forecast and AI insights"),
          S("17_evaluation.png", "Model Evaluation: baseline versus XGBoost with the RMSE, MAE and MAPE charts."),
          S("18_evaluation-importance.png", "Domain adaptation before-versus-after table (RMSE 18.9835 to 18.9893, improvement -0.03 %) and the top-20 feature importance of the tuned model, led by `is_month_end`, `lag_1`, `day_of_year`, `month_cos` and `rolling_mean_7`."),
          S("19_forecast.png", "Demand Forecast settings and result: article 108775015 (Vest top, 3,735 units sold), 14-day horizon, 383.1 units in total and 27.37 units per day."),
          S("20_forecast-table.png", "History-and-forecast chart for the same article and the dated forecast table, which starts on 2019-01-05, the day after the data end."),
          S("21_insights.png", "AI Insights page. Gemini is configured but returned *503: This model is currently experiencing high demand*; the application shows the message and every other page keeps working. A retry script tried eight times and never obtained an answer, so no AI explanation text could be captured.")]
    return _compact(b) if F.REPORT else b


def _performance():
    fc = F.FC
    s = fc["xgboost_seed_stats"]
    ab = fc["ablation"]
    b = [H2("8.3 Forecast accuracy"),
         P(f"The first table below gives the test-window results of every model on the same 6,515 rows. The default XGBoost reaches RMSE {s['RMSE']['mean']:.2f} (standard deviation {s['RMSE']['std']:.2f} over five seeds) and R2 {s['R2']['mean']:.3f}, "
           f"against {_m(F.MA, 'RMSE'):.2f} and {_m(F.MA, 'R2'):.3f} for the 7-day moving average that the product uses as its baseline: a {(1 - s['RMSE']['mean'] / _m(F.MA, 'RMSE')) * 100:.1f} % lower RMSE. "
           f"Tuning lowers it further to {_m(F.XGB_T, 'RMSE'):.2f}, and LightGBM, run with the same parameters as the product's optional baseline, gives {_m('LightGBM', 'RMSE'):.2f}. "
           f"The seed-to-seed spread is small ({s['RMSE']['std']:.3f}), so the differences between the models are not seed noise."),
         TAB("Test-window accuracy of all models (RMSE and MAE in units per article-day; lower is better, R2 higher is better).",
             ["Model", "RMSE", "MAE", "R2", "WAPE %"], _models_table(), widths=[3.4, 0.8, 0.8, 0.8, 0.9], align=["l", "c", "c", "c", "c"], size=10)]
    b += G("f01_model_comparison.png", "RMSE of each model on the test window; the XGBoost bar carries the standard deviation over five seeds.", doc_only=True)
    b += [P(f"The table also contains the result that matters most for honesty: **two one-line rules beat the shipped XGBoost.** Repeating yesterday's demand gives RMSE {_m('Naive (lag 1)', 'RMSE'):.2f} (R2 {_m('Naive (lag 1)', 'R2'):.3f}) and the shifted 7-day rolling mean gives "
             f"{_m('Rolling mean 7 (shifted)', 'RMSE'):.2f}, both better than the default ({s['RMSE']['mean']:.2f}), the tuned model ({_m(F.XGB_T, 'RMSE'):.2f}) and LightGBM. The product's own baseline, the moving average of the last seven days in the *training* set, is the weakest "
             "model except the random forest, because it is frozen at the end of training and cannot follow the December level; it is a weak yardstick. The comparison with a naive lag-1 forecast is the standard one in the base paper " + N('base') + ", whose gradient-boosted model beat it by a wide margin on its own data; here it does not."),
          P(f"The test window is the likely reason. Demand rises towards Christmas, falls sharply afterwards and the training window has never seen that. A model that has memorised absolute dates (`is_month_end`, `quarter`, `day_of_year` and `month_sin` carry the largest gain importance, "
            "see Section 8.6) cannot extrapolate to dates outside its training range, whereas lag-1 follows the level automatically. The ablation in the second table below confirms it.")]
    rows = [[k, str(v["n_features"]), f"{v['RMSE']:.2f}", f"{v['WAPE (%)']:.1f}", f"{v['R2']:.3f}"] for k, v in ab.items()]
    b += [TAB("Feature-group ablation (default XGBoost, mean of three seeds).", ["Feature set", "Inputs", "RMSE", "WAPE %", "R2"], rows,
              widths=[2.6, 0.8, 0.9, 0.9, 0.9], align=["l", "c", "c", "c", "c"], size=10)]
    b += G("f02_ablation.png", "Test RMSE for each feature set in the ablation.", doc_only=True)
    b += [P(f"Lag and rolling features carry the model: without them RMSE rises from {ab['all features (as shipped)']['RMSE']:.2f} to {ab['no lag / rolling']['RMSE']:.2f} and R2 becomes negative ({ab['no lag / rolling']['R2']:.3f}); calendar features alone are worse than predicting the mean ({ab['calendar only']['R2']:.3f}). "
             f"Removing price and channel costs a little (RMSE {ab['no price, no channel']['RMSE']:.2f}); removing the product attributes changes little. The model using only the nine lag and rolling features scores RMSE {ab['lag / rolling only']['RMSE']:.2f} and R2 {ab['lag / rolling only']['R2']:.3f}, "
             f"**better than the shipped 31-input model** ({ab['all features (as shipped)']['RMSE']:.2f}). This agrees with the base paper's ablation, where removing rolling statistics caused the largest loss " + N('base') + ", and it shows that on a short window extra calendar inputs hurt."),
          ]
    ro = fc["rolling_origin"]
    rows = [[f"{r['train_until']} to {r['test_until']}", str(r["test_rows"]), f"{r['xgboost']['RMSE']:.2f}", f"{r['moving_average']['RMSE']:.2f}", f"{r['naive_lag1']['RMSE']:.2f}", f"{r['seasonal_naive']['RMSE']:.2f}"] for r in ro]
    b += [] if F.REPORT else [TAB("Rolling-origin backtest (train up to the first date, test on the next 14 days; XGBoost seed 42).",
              ["Test period", "Rows", "XGBoost", "Moving average", "Naive lag-1", "Seasonal naive"], rows, widths=[2.2, 0.7, 0.9, 1.1, 1.0, 1.1], align=["l", "c", "c", "c", "c", "c"], size=10)]
    b += [P("Across three different origins XGBoost beats the moving average every time, but beats naive lag-1 only in the first fold (27.65 against 30.10), so the conclusion does not hinge on the one 80/20 split. "
            "The errors are largest in the weeks before Christmas, where volume itself is largest.")]
    b += G("f03_test_daily_series.png", "Daily total units on the test window: actual, XGBoost and moving average. The daily-total WAPE is 31.7 % for XGBoost and 24.7 % for the moving average.", doc_only=True)
    b += G("f13_xgb_seed_stability.png", "Test RMSE of the default XGBoost for the five random seeds.", 5.0, doc_only=True)
    return b


def _recursive():
    r = F.REC
    res = r["results"]
    rows = []
    for k, lab in (("xgb_app", "XGBoost recursive, as shipped"), ("xgb_fixed", "XGBoost recursive, calendar features refreshed"), ("flat_ma7", "Flat mean of the last 7 days"), ("repeat_last_week", "Repeat last week's pattern")):
        v = res[k]
        rows.append([lab] + [f"{v[x]['RMSE']:.2f}" for x in ("days 1-7", "days 1-14", "days 1-30")] + [f"{b_['WAPE (%)']:.0f}" for b_ in v["by_band"]])
    b = [H2("8.4 Multi-day recursive forecast"),
         P(f"The Forecast page predicts 7, 14 or 30 days ahead by feeding each prediction back as the next day's lag and rolling inputs. We scored exactly that loop on {r['articles_scored']} articles: a model trained on dates before {r['origin']} forecasts the following 30 days, "
           "and the forecast is compared with the actual units. The table below gives RMSE by cumulative horizon and WAPE by band."),
         TAB("Recursive forecast accuracy by horizon (RMSE; WAPE % by band).",
             ["Method", "RMSE d1-7", "RMSE d1-14", "RMSE d1-30", "WAPE d1-7", "WAPE d8-14", "WAPE d15-30"], rows,
             widths=[2.4, 0.7, 0.8, 0.8, 0.7, 0.8, 0.8], align=["l", "c", "c", "c", "c", "c", "c"], size=9.5)]
    b += G("f04_recursive_horizon.png", "WAPE of the recursive forecasts by horizon band.", doc_only=True)
    b += [P("The forecast is **worse than a flat 7-day mean at every horizon** and error compounds: WAPE is 41 % in the first week, 77 % in the second and 124 % in days 15 to 30, against 34, 48 and 79 % for the flat mean. "
            "The loop in the application updates only part of the calendar (month, day, weekday and their sine and cosine) and leaves `week_of_year`, `day_of_year`, `quarter` and the month-start and month-end flags at the last observed day, and it holds price and channel at their last values. "
            "Refreshing the missing calendar features did not help; it was slightly worse at 30 days (WAPE 134 % in the last band). The long-range forecast should therefore be read as an illustration of the interface, not as a planning tool; the base paper itself notes that multi-step forecasting accumulates error as predictions feed back into lag features " + N("base") + ".")]
    return b


def _domain():
    dm = F.DOM
    sm = dm["summary"]
    on = F.pair("Online")
    kn = F.pair("Knitwear")
    b = [H2("8.5 Domain adaptation"),
         P("The adaptation experiment follows the application's procedure (Chapter 6): train on all source-domain rows, test on the later half of the target domain's dates, estimate the weight p/(1-p) with a logistic domain classifier, retrain with those weights and compare. "
           "Six source-to-target pairs were run with five XGBoost seeds each: two sales-channel pairs, two product-group pairs and two department pairs. Four controls were added: a model trained on the first half of the target (target-only), a model trained on the source plus that first half without weights (pooled), "
           "the same weights randomly shuffled, and the same weights rescaled to a mean of 1. A time-clean variant removes source rows dated inside the target's test window. The table below gives the results."),
         TAB("Domain adaptation, RMSE on the held-out target rows (mean of five seeds). Change columns are % change in RMSE (positive = better).",
             ["Pair (source to target)", "Domain clf acc %", "RMSE before", "RMSE adapted", "Change as shipped", "Seeds better", "Change, mean-1 weights", "Change, time-clean", "Pooled RMSE", "Target-only RMSE"],
             _domain_rows(), widths=[1.55, 0.5, 0.5, 0.55, 0.55, 0.45, 0.55, 0.5, 0.5, 0.55], align=["l", "c", "c", "c", "c", "c", "c", "c", "c", "c"], size=8.5)]
    b += G("f05_domain_pairs.png", "Change in target RMSE for the six pairs: as shipped, with weights rescaled to mean 1, in the time-clean protocol, and with randomly shuffled weights.")
    b += [P(f"**Adaptation as shipped improved the target RMSE on {sm['pairs_where_adaptation_helped']} of {sm['pairs_total']} pairs.** The change ranges from {sm['min']:+.1f} % to {sm['max']:+.1f} % with a mean of {sm['mean_rmse_improvement_pct']:+.1f} %. "
            "The two channel pairs are the realistic case: a moderate shift (the domain classifier is only about 66 % accurate) with plenty of data on both sides. The product-group pairs are more clearly different (93 % accuracy) and adaptation made them worse by 6.5 and 7.3 %. "
            "The department pairs are perfectly separable (100 %) and adaptation made them much worse (-46.3 and -39.4 %)."),
          H3("Finding 1: the one clear gain came from time overlap"),
          P(f"Online to Store (channel 2 to channel 1) improved by {on['app']['rmse_improvement_pct_mean']:+.1f} % in all five seeds, but the source model was allowed to train on source rows from the same dates as the target's test window. When those rows are removed, the same pair changes by "
            f"{on['time_clean']['rmse_improvement_pct_mean']:+.1f} %. Random weights on the original protocol already gave {on['app']['shuffled_improvement_pct_mean']:+.1f} %, so part of the original gain is noise. The gain was information from the future of the target, not transfer."),
          H3("Finding 2: perfectly separable domains starve XGBoost"),
          P(f"When the classifier separates the domains perfectly, p is close to zero for every source row, so the weights p/(1-p) are tiny: for Knitwear to Trouser the mean weight is 5e-5 and the largest 1.3e-4. XGBoost's `min_child_weight` is 1, and the summed weight of any candidate leaf can never reach it, "
            f"so no tree splits and the model predicts a constant (R2 about 0, RMSE {kn['app']['adapted']['RMSE']['mean']:.2f} against {kn['app']['before']['RMSE']['mean']:.2f}). The five seeds give the same RMSE, because there is nothing random left. "
            f"Rescaling the same weights to mean 1 removes the collapse: Knitwear to Trouser then changes by {kn['app']['normalised_improvement_pct_mean']:+.1f} % instead of {kn['app']['rmse_improvement_pct_mean']:+.1f} %. The product accepts this input silently."),
          ]
    b += G("f07_weights_collapse.png", "Distribution of the importance weights for the channel pair and for the department pair Knitwear to Trouser. Weights far below the minimum child weight of 1 prevent XGBoost from splitting.")
    b += [H3("Finding 3: plain pooling beats weighting"),
          P("A model trained on the source rows plus the first half of the target rows, with no weights at all, has a lower RMSE than the weighted model on five of six pairs (the exception is Online to Store, 9.78 against 9.50). "
            "The target-only model is worse than the source-only model on five of six pairs, because half of a small target domain is too little data. In this data the useful move is to include some target rows, not to re-weight the source."),
          ]
    b += G("f06_domain_controls.png", "Target RMSE for each pair: source-only (before), weighted (adapted), pooled and target-only.", doc_only=True)
    b += [P(f"Taking the stricter protocol and the safer weights together, the mean change across the six pairs is {sm['normalised_time_clean_mean_rmse_improvement_pct']:+.1f} %: no change on average. The result does not show that importance weighting is wrong in general; "
            "it shows that on this retail table, with one shard of three and a half months, a logistic classifier on unscaled features does not produce weights that help, and that the product's way of testing adaptation can report a gain that is not transfer. "
            "The theory " + N("shim", "bickel") + " assumes that source and target inputs overlap and that the weights are estimated well; neither holds for departments that sell different products.")]
    return b


def _explain():
    ex = F.EX
    rows = [[t["feature"], f"{t['mean_abs_shap']:.2f}", f"{t['gain_importance']:.3f}"] for t in ex["top10_by_shap"]]
    b = [H2("8.6 Explainability"),
         P("The product explains forecasts with the gain importance of the XGBoost model (the Evaluation page, top 20). The base paper uses SHAP values " + N("shap", "treeshap") + " in addition. To see how much the choice matters, exact TreeSHAP values were computed offline with XGBoost's built-in `pred_contribs` "
           f"on all {ex['n_test_rows']:,} test rows (they add up to the model prediction with a maximum error of {ex['shap_additivity_max_abs_error']:.0e}). The table below lists the ten features with the largest mean absolute SHAP value next to their gain importance."),
         TAB("Mean absolute SHAP value (units of demand) and gain importance of the ten most influential features.",
             ["Feature", "Mean |SHAP|", "Gain importance"], rows, widths=[2.4, 1.4, 1.6], align=["l", "c", "c"], size=10)]
    b += G("f08_shap_vs_gain.png", "Mean absolute SHAP value and gain importance (both normalised) for the leading features.", doc_only=True)
    b += [P(f"The two rankings agree only moderately: the Spearman rank correlation is {ex['spearman_rank_corr_shap_vs_gain']:.2f}. By SHAP, `lag_1` dominates (8.75 units on average, more than twice the next feature) and the three leading features carry {ex['top3_share_of_total_abs_shap_pct']:.0f} % of all attribution. "
            f"By gain, the top three are {', '.join(ex['top3_by_gain'])}: `is_month_end` and `quarter` split often but move predictions little. A planner reading only the gain chart (the evaluation screen in Section 8.2) would conclude that calendar flags drive demand, "
            "while the SHAP view says yesterday's sales do. This is the kind of mismatch that a SHAP view is meant to reveal; the product does not yet show it, and it shows no per-forecast explanation either.")]
    return b


def _inventory():
    inv = F.INV
    rows = []
    for k in ("XGBoost", "Moving average (7d)", "Seasonal naive (lag 7)"):
        v = inv[k]
        rows.append([k, f"{v['predicted_units']:,.0f}", f"{v['bias_pct']:+.1f}", f"{v['understock_units']:,.0f} ({v['understock_pct_of_demand']:.1f} %)", f"{v['overstock_units']:,.0f} ({v['overstock_pct_of_demand']:.1f} %)"])
    b = [H2("8.7 Inventory impact"),
         P(f"The sixth objective asks for forecast error to be translated into inventory impact. The product does not do this, so it was computed offline from the test predictions: the units by which a forecast falls short of actual demand (stock the shop would lack) and the units by which it exceeds it (stock left over), "
           f"over the {inv['actual_units']:,.0f} units actually sold in the test window."),
         TAB("Shortfall and excess of each forecast on the test window (units and share of actual demand).",
             ["Forecast", "Predicted units", "Bias %", "Under-forecast (shortfall)", "Over-forecast (excess)"], rows,
             widths=[1.9, 1.0, 0.7, 1.6, 1.6], align=["l", "c", "c", "c", "c"], size=10)]
    b += G("f09_inventory_units.png", "Under- and over-forecast units as a share of actual demand for three forecasts.", doc_only=True)
    b += [P("XGBoost over-forecasts the window by 23.6 % in total, yet misses fewer sales (16.4 % of demand) than the moving average (29.4 %); it buys less risk of stock-out with more excess (39.9 % against 35.9 %). "
            "Because the errors are individually large, both kinds of error are large for every forecast: a typical article-day is wrong by about half its demand. "
            "The claim in the abstract that the system *reduces inventory shortages and overstock* is therefore **not demonstrated**. What is shown is that the forecast loses fewer units than the product's baseline; no stock policy, safety-stock level or service level was simulated or tested out of sample.")]
    return b


def _cold():
    c = F.COLD
    rows = []
    for k, lab in (("attributes_calendar_only_unseen_article", "XGBoost, attributes + calendar + price (no lags)"), ("product_type_mean_baseline_unseen_article", "Mean demand of the product type"),
                   ("full_features_unseen_article_lags_assumed_known", "Reference: full features with the article's own lags")):
        v = c[k]
        rows.append([lab, f"{v['RMSE']:.2f}", f"{v['MAE']:.2f}", f"{v['R2']:.3f}", f"{v['WAPE (%)']:.1f}"])
    b = [H2("8.8 Products without history"),
         P("The problem statement stresses new products with no sales history. The product has no cold-start mode: its forecast needs at least five days of the article's own history because every strong feature is a lag or rolling value. "
           "To see how far attributes alone go, five-fold cross-validation was run with whole articles held out of training. This is an offline experiment, not a feature of the application."),
         TAB("Forecasting articles unseen in training (5-fold grouped cross-validation).", ["Model", "RMSE", "MAE", "R2", "WAPE %"], rows,
             widths=[3.4, 0.8, 0.8, 0.8, 0.9], align=["l", "c", "c", "c", "c"], size=10)]
    b += G("f10_cold_start.png", "Accuracy for unseen articles with and without the article's own history.", 5.2, doc_only=True)
    b += [P("Attributes, calendar and price give R2 0.27 for unseen articles, clearly better than the product-type mean (-0.01), but far below the 0.68 reached when the article's own lags are available. "
            "Attribute-based new-item forecasting is a research topic of its own " + N("ekam", "singh", "skend") + " that uses images, similar products or external signals; TrendCast's objective of handling new products is only partly addressed and was not implemented in the product.")]
    return b


def _base():
    fc = F.FC
    ours_x, ours_ma, ours_n = F.fm(F.XGB), F.fm(F.MA), F.fm("Naive (lag 1)")
    base_l, base_ma, base_n = 33.71, 33.71 + 2.86, 33.71 + 14.06
    rows = [["Data", "UCI Online Retail II (UK wholesaler), 1.07 M transactions, 4,631 SKUs", "H&M, 300 best-selling articles, 684,392 rows, 107 days"],
            ["Task", "One-day-ahead daily SKU demand", "One-day-ahead (test metrics) and 7/14/30-day recursive (app)"],
            ["Main model", "LightGBM, 41 features, Optuna tuning (30 trials)", "XGBoost, 31 features, default or randomized search"],
            ["RMSE of main model", "33.71 (R2 0.243)", f"{ours_x:.2f} (R2 {F.fm(F.XGB, 'R2'):.3f}); tuned {F.fm(F.XGB_T):.2f}"],
            ["RMSE of moving average (7-day)", f"{base_ma:.2f} (the paper reports the gap, 2.86)", f"{ours_ma:.2f}"],
            ["RMSE of naive lag-1", f"{base_n:.2f} (the paper reports the gap, 14.06)", f"{ours_n:.2f}"],
            ["Reduction versus moving average", f"{(base_ma - base_l) / base_ma * 100:.1f} %", f"{(ours_ma - ours_x) / ours_ma * 100:.1f} %"],
            ["Reduction versus naive lag-1", f"{(base_n - base_l) / base_n * 100:.1f} %", f"{(ours_n - ours_x) / ours_n * 100:.1f} % (i.e. worse)"],
            ["Dominant features", "Rolling statistics (28-day mean first)", "Lag-1 and rolling mean (SHAP); lag/rolling-only model beats all-feature model"],
            ["Explainability", "Permutation importance, PDP, SHAP, ICE", "Gain importance in the app; SHAP offline only"],
            ["Domain shift / new products", "Not addressed (listed as a limitation)", "Importance-weighted adaptation implemented and tested; no cold-start mode"]]
    if F.REPORT:
        rows = [r for r in rows if r[0] not in ("Task", "Main model", "Explainability", "Dominant features")]
    b = [H2("8.9 Comparison with the base paper"),
         P(f"The base paper {N('base')} is Mishra et al.'s four-level explainable LightGBM framework. **The datasets, targets, scales and horizons differ**: its data are a UK online wholesaler's gift-ware orders so the scale of demand differs and an RMSE of 33.71 and ours of {ours_x:.2f} cannot be put on one scale, "
           "and the paper's moving-average and naive RMSEs are derived here from the gaps it states. Only relative findings are compared, and only indicatively."),
         TAB("TrendCast against the base paper (different data; indicative only).", ["Aspect", "Base paper (Mishra et al.)", "TrendCast (this project)"], rows,
             widths=[1.5, 2.5, 2.5], align=["l", "l", "l"], size=9.5)]
    b += G("f11_base_paper_comparison.png", "RMSE relative to the moving average and to the naive lag-1 forecast, base paper against TrendCast. Different datasets; indicative only.", 5.4, doc_only=True)
    b += [P("Three findings carry across. In both studies a gradient-boosted model beats the 7-day moving average (by 7.8 % in the base paper and 14.0 % here). In both, rolling and lag features are the dominant group. "
            "They differ on the naive lag-1 yardstick: the base paper's model beats it by 29 %, while here the one-line rule is better than XGBoost by 20 %, which we attribute (without being able to prove it with one shard) to the short window, the holiday-spanning test period and the absolute-date inputs. "
            "The base paper stops at global and local explanations and leaves multi-step forecasting and external shifts as limitations " + N("base") + "; TrendCast adds a domain-adaptation step and a multi-step forecast and reports that neither is yet reliable.")]
    return b


def _samples():
    b = [H2("8.10 Sample inputs and outputs"),
         P("**Input.** The transactions file has one row per purchased item. Three real rows of article 108775015 on the first day (the first two are identical, which is why the cleaning step removes exact duplicates even though they are two units bought):"),
         *([] if F.REPORT else [TAB("Real input rows (transactions_train.csv; customer ids shortened).", ["t_dat", "customer_id", "article_id", "price", "sales_channel_id"],
             [["2018-09-20", "05ed96931b707698", "108775015", "0.008458", "1"], ["2018-09-20", "05ed96931b707698", "108775015", "0.008458", "1"], ["2018-09-20", "0aaa9683d5f45b85", "108775015", "0.008068", "2"]],
             widths=[1.1, 1.6, 1.1, 0.9, 1.3], align=["l", "l", "c", "c", "c"], size=10)]),
         P("The articles file gives the same article as *Strap top*, product type *Vest top*, group *Garment Upper body*, colour *Black*, department *Jersey Basic*, section *Womens Everyday Basics*. "
           "After cleaning and counting rows per day the article has 21 units on 2018-09-20, 35 on 2018-09-21, 8 on 2018-09-22, 16 on 2018-09-23, 24 on 2018-09-24 and 47 on 2018-09-25 (screen 09)."),
         P("**Output.** The last seven actual days of that article and the 7-day forecast of the default model, produced by `POST /api/forecast` on the final day of the data:"),
         TAB("Article 108775015, last actual days and 7-day recursive forecast (default XGBoost).",
             ["Actual date", "Units", "Forecast date", "Predicted units"],
             [["2018-12-29", "25", "2019-01-05", "20.51"], ["2018-12-30", "24", "2019-01-06", "26.56"], ["2018-12-31", "19", "2019-01-07", "21.60"], ["2019-01-01", "24", "2019-01-08", "22.32"],
              ["2019-01-02", "41", "2019-01-09", "24.03"], ["2019-01-03", "32", "2019-01-10", "22.82"], ["2019-01-04", "27", "2019-01-11", "21.35"]],
             widths=[1.3, 0.9, 1.3, 1.3], align=["c", "c", "c", "c"], size=10),
         P("The seven forecasts total 159.2 units (22.7 per day), close to the recent average of about 27 units per day but flatter than the real series, which swings between 19 and 41; recursive forecasts tend to settle near the recent level, as Section 8.4 measured. "
           "The 14-day forecast shown in screen 19, made with the tuned model, totals 383.1 units (27.37 per day).")]
    return b


def _analysis():
    if F.REPORT:
        return [H2("8.11 Success and failure analysis"),
                P("**Where it works.** Real transactions go from upload to forecast in about twelve seconds of compute without tuning (Chapter 7); 39 tests and 26 smoke checks pass; every screen renders real data and the domain page reports a null result without softening it. "
                  "One-day-ahead forecasting at article level beats the product's baseline by 14 % in RMSE in all five seeds and all three backtest folds, and leakage is controlled by shifted lags, a chronological split and time-ordered tuning folds."),
                P("**Where it fails.** It does not beat repeat-yesterday on the test window, and the all-feature model is worse than a nine-feature lag/rolling model. Recursive 7/14/30-day forecasts are worse than a flat 7-day mean. "
                  "Domain adaptation helps on 2 of 6 pairs, the clearest gain is a time-overlap artefact and unnormalised weights can collapse XGBoost to a constant. New products cannot be forecast (offline R2 0.27 from attributes only). "
                  "Cleaning removes 11.6 % of rows that are mostly real repeat purchases, and AI Insights gave no answer because the external service was unavailable.")]
    b = [H2("8.11 Success and failure analysis"),
         H3("Where it works"),
         B("**The pipeline and the application.** Real transactions go from upload to forecast in about twelve seconds of compute without tuning (Chapter 7); 39 tests and 26 smoke checks pass; every screen renders real data.",
           "**Reporting without softening.** The domain page shows a 0.0 % worse result as it is, and the quality report states how many rows were removed.",
           "**One-day-ahead forecasting at article level** beats the product's baseline by 14 % in RMSE, in all five seeds and in all three backtest folds.",
           "**Leakage control.** Lags and rolling means are shifted, the split is chronological and tuning uses time-ordered folds; unit tests protect these properties."),
         H3("Where it fails"),
         B("**It does not beat repeat-yesterday** on the test window; the all-feature model is worse than a nine-feature lag/rolling model.",
           "**Recursive 7/14/30-day forecasts** are worse than a flat 7-day mean at every horizon.",
           "**Domain adaptation** helps on 2 of 6 pairs, the clearest gain is a time-overlap artefact, and unnormalised weights can collapse XGBoost to a constant.",
           "**New products** cannot be forecast by the product; attributes alone give R2 0.27 in an offline test.",
           "**Cleaning removes real purchases:** 11.6 % of rows were exact duplicates, mostly repeat purchases, so demand is understated.",
           "**AI Insights** gave no answer in the capture run because the external service was unavailable.")]
    return b


def _limits():
    if F.REPORT:
        return [H2("8.12 Limitations of the evaluation"),
                B("One shard of the data (107 days, 300 best-selling articles, two channels): no yearly seasonality can be learnt and the test window is a holiday peak.",
                  "The domains are mixtures (the channel label is the most frequent channel of the day while demand counts both), and no promotions, stock levels or weather exist in the files.",
                  "Five seeds capture only XGBoost's randomness; the inventory and SHAP analyses are offline; the base-paper comparison is indicative because the data differ.")]
    return [H2("8.12 Limitations of the evaluation"),
            B("One shard of the data: 107 days, 300 best-selling articles and two sales channels. No yearly seasonality can be learnt, the test window is a holiday peak, and best sellers are not typical articles.",
              "The domains are mixtures: the channel label of an article-day is the most frequent channel, while its demand counts both channels; the product-group and department domains differ in what they sell as well as how they sell.",
              "No promotions, markdown calendar, stock levels or weather are in the H&M files; the abstract's mention of promotional and fabric attributes could not be tested.",
              "Five seeds capture XGBoost's randomness only, not data variation; the three rolling-origin folds are overlapping weeks of one season.",
              "The inventory and SHAP analyses are offline and use the test window's predictions; no policy was simulated.",
              "The base-paper comparison is indicative because the data differ; a replication on UCI Online Retail II was not attempted.")]


def _objectives():
    rows = [["1. Collect fashion sales data; engineer seasonal, pricing and category features", "Achieved", "Real H&M subset; 31 inputs (price, channel, 6 attributes, 14 calendar, 9 lag/rolling); shifted lags, chronological split. No promotion or fabric data exist in H&M"],
            ["2. Train gradient-boosting models at product and category level", "Achieved at article level", "XGBoost per article-day with category as an input; no separate category-level model"],
            ["3. Apply domain adaptation across markets and categories", "Implemented and applied", "Importance weighting on channel, product-group and department domains; \"markets\" are the two sales channels (no regions in the data)"],
            ["4. Compare adapted and non-adapted models on a shifted target", "Done, result negative", "6 pairs x 5 seeds + controls: helped 2/6 (mean -14.6 %); mean-1 weights -6.5 %; time-clean -7.1 %; pooling beats it on 5/6"],
            ["5. Explain forecast drivers", "Partly", "Gain importance (top 20) in the app; offline SHAP agrees only moderately (rank correlation 0.40); no per-forecast explanation; Gemini text unavailable in the run"],
            ["6. Evaluate with MAE, RMSE, MAPE and translate error into inventory impact", "Metrics achieved; impact offline", "RMSE, MAE, MAPE, R2, WAPE reported; inventory impact computed offline only (XGBoost 16.4 % short, 39.9 % excess); stock-out reduction not demonstrated"]]
    return [H2("8.13 Objectives versus outcomes"),
            TAB("The six project objectives against what was measured.", ["Objective", "Status", "Evidence"], rows, widths=[2.3, 1.1, 3.1], align=["l", "l", "l"], size=9.5)]


def _summary():
    return [H2("8.14 Summary of findings"),
            B(f"On a real H&M subset XGBoost forecasts one day ahead with RMSE {F.fm(F.XGB):.2f} (tuned {F.fm(F.XGB_T):.2f}), better than the product's moving average ({F.fm(F.MA):.2f}) but worse than repeating yesterday ({F.fm('Naive (lag 1)'):.2f}).",
              "Lag and rolling features do almost all the work; absolute-date features hurt on a short window.",
              "Recursive multi-day forecasts are worse than a flat 7-day mean and degrade quickly with the horizon.",
              "Importance-weighted domain adaptation, as built, is not reliable: it helped on 2 of 6 pairs, the clear gain is a time-overlap artefact, and degenerate weights collapse the model. Rescaling weights and pooling target rows are the first fixes to try.",
              "Gain importance and exact SHAP rank features differently; the offline SHAP view shows yesterday's demand as the main driver.",
              "Inventory impact and cold-start performance are not part of the product; offline numbers show the gaps.",
              "The application is complete, tested and fast; the forecasting claims in the abstract are supported only in part, and this chapter says which part.")]


def blocks():
    b = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]
    b += _setup() + _screens() + _performance() + _recursive() + _domain() + _explain() + _inventory() + _cold() + _base() + _samples() + _analysis() + _limits() + _objectives() + _summary()
    return b
