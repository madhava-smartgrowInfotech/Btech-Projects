# FRONTEND PLAN - TrendCast (CSE-A-A17)

Fashion Demand Forecasting Using Machine Learning And Domain Adaptation.
Design: **V2 Neo Brutal Grid** (kit copied into `frontend/src`). Ports: backend **8317**, frontend **5317** (from `.env`).

## 1. Starting point

The product is a **Streamlit app** (`app.py`, 597 lines) over a pure-Python pipeline in `src/`. There is **no HTTP API**.
The Streamlit app is left untouched. New code is additive:

- `backend/` - thin FastAPI layer that imports the existing `src/` functions (no logic rewritten) and holds the
  pipeline state in memory, exactly like `st.session_state` did.
- `frontend/` - new React (Vite, JavaScript) app built on kit V2.

`src/data_loader.py` and `src/gemini_helper.py` import `streamlit` (`st.cache_data`, `st.secrets`). The backend reuses their
validators / context builders and reads the CSV upload and the Gemini key (`.env`) itself.

## 2. Inventory - existing features (from `app.py`, README, `src/`)

| # | Streamlit page | What it does | Underlying functions |
|---|---|---|---|
| 1 | Home | pipeline overview, pointer to Data Upload | - |
| 2 | Data Upload | upload transactions (req) / articles (req) / customers (opt), row cap (default 200 000), clean + merge, data-quality report | `data_loader.validate_columns`, `preprocessing.clean_*`, `merge_datasets`, `data_quality_report` |
| 3 | Data Exploration | daily trend, monthly, weekly, top-10 products, demand by department / colour / sales channel, price histogram | `demand_forecasting.aggregate_daily_demand`, `visualization.plot_*` |
| 4 | Demand Analysis | aggregated daily demand table (first 200 rows) + leakage note | `daily_demand` |
| 5 | Feature Engineering | fill missing dates, build feature table (time, cyclical, lag, rolling, encoded categoricals), shape, head(50), model input feature list | `fill_missing_dates_per_article`, `feature_engineering.build_feature_table`, `get_feature_columns` |
| 6 | Model Training | chronological split slider (0.5-0.95), split summary, moving-average baseline, XGBoost train (optional RandomizedSearchCV tuning + best params), load saved model, model-comparison table + chart; model saved to `models/` | `baseline_models.*`, `xgboost_model.train_xgboost / tune_xgboost`, `evaluation.evaluate_model / compare_models` |
| 7 | Domain Adaptation | choose domain column (sales_channel_id / product_group_name / department_name), source & target value, domain classifier accuracy, shift table (top 15), histogram + box plot of top shifted feature, importance-weighted adapted model, before/after report | `domain_adaptation.*`, `evaluation.before_after_adaptation_report` |
| 8 | Model Evaluation | baseline vs XGBoost table + RMSE/MAE/MAPE charts, domain before/after table, feature importance (top 20) | `evaluation.*`, `xgboost_model.get_feature_importance` |
| 9 | Demand Forecast | pick article + horizon (7/14/30), recursive forecast table + history/forecast chart | recursive loop in `page_demand_forecast` |
| 10 | AI Insights | optional Gemini: free-form question over metrics + top features, "summarize latest forecast"; graceful notice when no key | `gemini_helper.*` |
| 11 | About Project | title, goal, techniques | static |

Cross-cutting behaviours to keep: page gating warnings ("upload first", "build features first", "train first"), spinners for
long jobs, friendly validation errors (`DataValidationError`), safe-MAPE exclusion count, model persistence to `models/*.joblib`.

## 3. Inventory - backend endpoints (to be added, all `/api`)

The product has no API today, so this is the thin layer. Every route calls an existing `src/` function.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/health` | - | `{status}` |
| GET | `/api/state` | - | progress flags: `data_loaded, daily_ready, features_ready, baseline_trained, domain_done, forecast_done, saved_model_exists, gemini_configured` |
| POST | `/api/data/upload` | multipart `transactions`, `articles`, `customers?`, `sample_rows` | data-quality report |
| GET | `/api/data/report` | - | data-quality report |
| GET | `/api/explore` | - | all exploration series (daily, monthly, weekly, top products, department, colour, channel, price histogram) |
| GET | `/api/demand/table` | `?limit=200` | rows + columns + total rows |
| POST | `/api/features/build` | - | shape, feature columns, head rows |
| GET | `/api/features` | - | same, if built |
| GET | `/api/training/split` | `?train_fraction=0.8` | split summary |
| POST | `/api/training/baseline` | `{train_fraction}` | metrics |
| POST | `/api/training/xgboost` | `{train_fraction, tune}` | metrics, best params |
| POST | `/api/training/load` | - | loaded flag (404-style error if none) |
| GET | `/api/training/results` | - | comparison rows |
| GET | `/api/domain/options` | - | domain columns, values per column |
| POST | `/api/domain/run` | `{domain_col, source, target}` | classifier accuracy, shift table, histogram + box data, before/after report |
| GET | `/api/evaluation` | - | comparison rows, domain report, feature importance |
| GET | `/api/forecast/articles` | - | article ids |
| POST | `/api/forecast` | `{article_id, horizon}` | history tail (60) + forecast rows |
| GET | `/api/ai/status` | - | `{configured, model}` |
| POST | `/api/ai/explain` | `{question}` | `{answer}` |
| POST | `/api/ai/forecast-summary` | - | `{answer}` |

State is process-wide in memory (single-user demo app, same as one Streamlit session).
No login exists in the product; none is added.

## 4. Screen map (React routes)

| Route | Screen | Covers feature # |
|---|---|---|
| `/` | Landing (Neo Brutal hero, pipeline, live-less static facts, CTA) | 1 |
| `/app` | Pipeline overview (progress stepper from `/api/state`, next action) | 1 |
| `/app/upload` | Data Upload | 2 |
| `/app/explore` | Data Exploration | 3 |
| `/app/demand` | Demand Analysis | 4 |
| `/app/features` | Feature Engineering | 5 |
| `/app/training` | Model Training | 6 |
| `/app/domain` | Domain Adaptation | 7 |
| `/app/evaluation` | Model Evaluation | 8 |
| `/app/forecast` | Demand Forecast | 9 |
| `/app/insights` | AI Insights | 10 |
| `/about` | About Project | 11 |
| `*` | Not found | - |

Kit components used: AppShell (rewritten nav), Button, Card, StatCard, Table, Modal, Toast, FileDrop (adapted to CSV),
Tabs, EmptyState, ErrorState, Skeleton, Stepper, charts (bar blocks + new line / scatter wrappers), motion helpers.

## 5. Feature checklist (tick in Step 4)

- [ ] 1 Home / pipeline overview
- [ ] 2 Data Upload (3 files, row cap, validation errors, quality report)
- [ ] 3 Data Exploration (all 8 charts)
- [ ] 4 Demand Analysis (table + leakage note)
- [ ] 5 Feature Engineering (build, shape, head, feature list)
- [ ] 6 Model Training (split slider + summary, baseline, XGBoost, tuning, load saved, comparison)
- [ ] 7 Domain Adaptation (options, classifier acc, shift table, hist, box, before/after)
- [ ] 8 Model Evaluation (comparison charts, domain report, feature importance)
- [ ] 9 Demand Forecast (article, horizon 7/14/30, table, chart)
- [ ] 10 AI Insights (explain, forecast summary, not-configured state)
- [ ] 11 About Project
- [ ] Landing page (light + dark), dark mode toggle, reduced motion, 360px, keyboard

## 6. Open risk

The repo ships **no H&M data** (`data/` is empty, none on this machine, the Kaggle files need an account). Real-data screenshots and the
end-to-end walk need H&M-shaped CSVs. See the proceed prompt.
