# NARRATIVE - the story every TrendCast document tells

Numbers come from `docs/REPORT_FACTS.md` / `experiments/**/metrics.json` (read them through `scripts/docs/facts.py` as `F.FC`, `F.DOM`, `F.REC`, `F.EX`, `F.INV`, `F.COLD`, `F.API`, `F.DS`). Never hard-code a number that facts.py can supply; if you must quote one, copy it exactly from REPORT_FACTS.md.

## One-paragraph story
TrendCast turns H&M-style retail transactions into daily units sold per article, forecasts them with XGBoost on calendar, price, attribute, lag and rolling features, and offers importance-weighted domain adaptation (a logistic domain classifier gives weights p/(1-p)) to move a model from a source sales domain to a shifted target domain. It ships as a FastAPI service (22 routes) with a 13-page React console (and the original 11-page Streamlit app), tested by 39 pytest tests and a 26-check smoke test. Measured on a real subset of the H&M data (300 best-selling articles, 684,392 rows, 2018-09-20 to 2019-01-04), the honest result is **mixed**: the model beats the product's moving-average baseline, but not the one-line "repeat yesterday" forecast; the multi-day recursive forecast is worse than a flat 7-day mean; and domain adaptation as shipped helps on only 2 of 6 source-target pairs, the one clear gain disappears once source rows are not allowed to overlap the target test dates, and degenerate weights can make XGBoost collapse to a constant until they are rescaled. Documents state these findings plainly; they are a strength (measured, explained, reproducible), not something to hide.

## Fixed vocabulary
- Product: **TrendCast**. Sales **channels** 1 and 2: the H&M files only code them 1 and 2. Say "channel 1" / "channel 2" in the documents. The pair labels in REPORT_FACTS.md say "Online -> Store (channel 2 -> 1)" and "Store -> Online (channel 1 -> 2)" - when you use those labels, say once that store/online is our convention, not stated by the data.
- **Domain adaptation (as built)** = importance weighting for covariate shift (Shimodaira; Bickel et al.). Not adversarial, not CORAL, not fine-tuning.
- **Base paper** = Mishra et al., IEEE Access 2026 (LightGBM + four-level XAI on UCI Online Retail II, RMSE 33.71, R2 0.243). Different data, different horizon (one-step), so numbers are never put on one scale; compare *relative* findings only (gradient boosting beats moving average; rolling/lag features dominate; naive lag-1 is a strong baseline).
- Honest limits: 107 days, 300 articles, one shard of H&M; test window = Christmas peak + January; cleaning drops 11.6 % exact-duplicate rows; no cold-start mode; no SHAP / inventory impact inside the app (offline only); AI Insights depends on an external service that was down during capture (503 / timeout).
- Test conditions: Intel i5-12500, 15.7 GB, no GPU, other jobs running; Python 3.11.9, XGBoost 2.0.3, scikit-learn 1.5.0.

## Objectives (from 6.OBJECTIVES&PROBLEM STATEMENT.docx) vs outcome
1. Collect historical fashion sales data, engineer seasonal, pricing, category features - **achieved** (real H&M subset; 31 inputs; leakage guards: shifted lags, chronological split, TimeSeriesSplit tuning). No promotion or fabric data exist in H&M; no regional seasonality.
2. Train XGBoost at product and category level - **achieved at article (product) level**; no separate category-level model (category enters as encoded features and in charts).
3. Apply domain adaptation across markets and categories - **implemented and applied** to channel, product-group and department domains; "markets" = the two sales channels (no regions in the data).
4. Compare adapted and non-adapted on a shifted target - **done**: 6 pairs x 5 seeds + controls. Adaptation as shipped helped 2/6 (mean -14.6 %); with mean-1 weights mean -6.5 %; time-clean mean -7.1 %; unweighted pooling beats it on 5/6.
5. Explain drivers - **partly**: app shows gain importance (top 20); exact TreeSHAP computed offline agrees only moderately (Spearman 0.40). No per-forecast explanation in the app; Gemini text is optional.
6. Evaluate with MAE, RMSE, MAPE and translate to inventory impact - **metrics achieved** (plus R2, WAPE); inventory impact only offline (XGBoost +23.6 % total bias, 16.4 % of demand under-forecast, 39.9 % over-forecast on the test window; moving average 29.4 % / 35.9 %).
Abstract claims "reduces inventory shortages and overstock" - **not demonstrated**; say so.

## Headline numbers (all from REPORT_FACTS.md)
- Test window 2018-12-14..2019-01-04, 6,515 rows. RMSE: moving average 12.89, XGBoost default 11.09 +/- 0.05 (5 seeds), tuned 10.34, LightGBM 10.06, naive lag-1 9.22, rolling-mean-7 9.31, RF 13.26. R2 XGBoost 0.335.
- Ablation: lag/rolling only 9.40 RMSE (R2 0.52) beats all-features 11.06; no lag/rolling 16.16 (R2 -0.41); calendar only 15.18.
- Rolling-origin backtest (3 folds): XGBoost beats moving average in all, beats lag-1 only in fold 1.
- Recursive forecast: WAPE 41 % (days 1-7), 77 % (8-14), 124 % (15-30) vs flat 7-day mean 34 / 48 / 79 %.
- Domain: see REPORT_FACTS section 8. Online->Store +11.95 % (time-clean -2.76 %); Store->Online +0.01 %; group pairs -6.5 / -7.3 %; department pairs -46.3 / -39.4 % (weights ~1e-5 starve min_child_weight; mean-1 weights: +1.9 % / -38.8 %).
- API: stages (upload 3.5 s, features 0.9 s, XGBoost 1.1 s, tuned 29.6 s, domain run 3.7 s); 30-day forecast median 156 ms.
- Tests: 39 pytest (22 unit + 17 API) pass; 26 smoke checks pass; 25 screenshots.

## Style rules
Plain, concrete, first-person plural ("we"). No filler claims ("state-of-the-art", "robust" unless measured). No invented numbers, no invented literature. Cite only keys in `scripts/docs/refs.py` via `N('key')`. The four batch-survey papers (s2-s5) are listed in the reference list only and are never used for facts.
