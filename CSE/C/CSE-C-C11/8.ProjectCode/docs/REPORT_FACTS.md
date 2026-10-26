# REPORT_FACTS - AI Based Personal Finance Manager (FINJARVIS), batch CSE-C-C11

Single source of truth for every document in the submission set. Generated 2026-10-22 from this folder's own
artefacts: `experiments/metrics.json` (`scripts/run_experiments.py`), `experiments/api_latency.json`
(`scripts/measure_api.py`), `pytest`, `scripts/smoke_test.py`, and the code. Nothing below is taken from the base paper
except where it says "base paper".

## 1. Identity

| Item | Value |
|---|---|
| Project | AI Based Personal Finance Manager (product name **FINJARVIS**) |
| Batch / class | C11 / CSE-C, Department of Computer Science and Engineering |
| Students | Mekala Kalyan 23K91A05F0 · Rajanala Sai Hemanth 23K91A05K3 · Middala Surya Teja Reddy 23K91A05F2 · Manga Akash 23K91A05E5 |
| Guide | N Padmavathi |
| College | TKR College of Engineering & Technology (Autonomous), Department of CSE (named in `Documentary/Batch_C11_*.docx` and the final-review template letterhead) |
| Unknown (keep placeholders) | HOD, principal, academic year, guide designation, e-mails |
| Base paper | R. Kharat, S. Solapurkar, A. Tikkas, M. Uttarwar, A. Yadav, "A Smart AI-Based Personal Finance Assistant: A Multi-Model Approach for Expense Categorization, Budgeting, Forecasting and Anomaly Detection," IJRASET, vol. 13, no. XI, pp. 167-180, Nov. 2025, doi 10.22214/ijraset.2025.75019 (PDF in `Documentary/`) |
| Ports | backend 8411, frontend 5411 (Streamlit original: 8501) |

## 2. What was actually built (and what was not)

Built (all verified in code):
1. Accounts: sign-up / log-in with bcrypt-hashed passwords (passlib), password rules (8+ chars, upper, lower, digit, special),
   username 3-30 chars, login by username or e-mail, signed bearer tokens (HMAC-SHA256, 7-day expiry), per-user data scoping (`user_id` on every table and query).
2. Transactions: add / edit / delete / search / filter / sort, custom categories, payment method, notes, **CSV/Excel import with preview**.
3. **Expense categoriser**: TF-IDF (word 1-2-grams) + Logistic Regression, trained on a 51-example seed list; keyword table as fallback if the model cannot load; retrains on a user's correction (`learn_from_correction`).
4. **Spending forecast**: least-squares linear trend over monthly expense totals (`numpy.polyfit`, degree 1), clipped at 0; also per-category trends and a budget-overrun check; refuses to predict with fewer than 3 months.
5. **Financial health score**: 0-100, six weighted explainable components (weights 0.30 / 0.20 / 0.15 / 0.15 / 0.10 / 0.10), five rating bands, weakest-area explanation.
6. Budgets (monthly per category) with alerts at 75 / 90 / 100 % written to notifications (de-duplicated by message).
7. Savings goals with progress, required monthly saving, completion estimate; manual investment portfolio (6 asset types) with optional live price refresh via `yfinance`.
8. AI assistant: deterministic, rule-routed answers computed from the user's own data (5 intent handlers) + optional Anthropic LLM layer when `AI_API_KEY` is set (**not exercised in any measurement here**); rule-based insights; mandatory disclaimer.
9. Reports: PDF (ReportLab), Excel (OpenPyXL), CSV.
10. Notifications (unread count, mark all read), demo account (`demo` / `Demo@1234`, fictional data), landing page.
11. Two front ends over the same Python code and the same SQLite file: the original Streamlit app (`app.py`, `ui/`) and the React + FastAPI web app (`frontend/`, `backend/`) built in this phase.

**Not built - state plainly in every document:**
- **No anomaly detection** (objective 4 and a base-paper module). The nearest feature is `analytics_overview().largest_expense` (the single largest expense in a window). No Isolation Forest, no z-score rule, nothing flags an unusual transaction.
- **No time-series model beyond a linear trend** (objective 3 says "time-series models"): no ARIMA, no LSTM. Forecasts expenses only, not "savings" directly.
- **No reinforcement-learning budget recommender** (base paper module). Budgets are user-set; advice is rule-based (top categories, 10-15 % trim suggestion, threshold alerts).
- No BERT / transformer categoriser; no SMOTE; no 50-category taxonomy (11 categories + "Other").
- **No loan / debt tracker and no amortisation or prepayment calculator** (the abstract says "loan tracking"; `Documentary/Batch_C11_*.docx` lists a "Debt & Loan Amortization Tracker"). There is no loan table. **No task scheduler / periodic digest alerts** (alerts are raised on read: `check_and_raise_alerts` runs when the dashboard or the notifications list is requested, not on a timer and not when a transaction is saved). No multi-account or bank-statement sync.
- The abstract names **Flask + MySQL**; the shipped system is **FastAPI + SQLite** (Streamlit originally). Disclose this deviation.
- Not run in the measurements: LLM layer, live `yfinance` refresh (needs internet), multi-user concurrency, mobile browsers, bank-API / SMS parsing.

## 3. Architecture

Layers (top to bottom): React 18 + TypeScript SPA (Vite, Tailwind v4, Recharts, TanStack Query, Axios) -> FastAPI app `backend/main.py` (33 routes,
CORS for 5411, bearer-token dependency `current_user`) -> service layer `services/` (transaction, budget, goal, investment, analytics, ai, report, data_import)
-> ML modules `ml/` (expense_classifier, spending_prediction, financial_health) -> SQLAlchemy ORM `database/` -> SQLite file `finjarvis.db`
(or the path in `FINJARVIS_DB`). `auth/authentication.py` + `utils/security.py` (bcrypt via passlib) + `utils/validators.py`.
`backend/` contains no business logic: every route calls the same service function the Streamlit pages call.

Size: ~2,390 lines of Python (backend + services + ml + auth + database + utils + tests + smoke test), ~6,540 lines of TypeScript/TSX in 69 front-end files, 13 pages
(Landing, Login, Signup, Dashboard, Transactions, Analytics, Budgets, Goals, Investments, Assistant, Reports, Notifications, Profile) + NotFound.

### Database (6 tables, SQLite, SQLAlchemy 2)
| Table | Columns |
|---|---|
| users | id PK, name, email UNIQUE, username UNIQUE, password_hash, currency (INR), monthly_income, risk_profile (Conservative/Moderate/Aggressive), savings_target, created_at |
| transactions | id PK, user_id FK, date, description(255), category(80), amount, transaction_type (income/expense), payment_method, notes |
| budgets | id PK, user_id FK, category, budget_amount, month 1-12, year |
| financial_goals | id PK, user_id FK, goal_name, target_amount, current_amount, target_date, status (active/completed/abandoned) |
| investments | id PK, user_id FK, asset_name, symbol, asset_type (Stock/Mutual Fund/ETF/Gold/FD/Other...), quantity, purchase_price, current_price, purchase_date |
| notifications | id PK, user_id FK, message, notification_type (info/warning/danger/success), created_at, is_read |
All child tables `ON DELETE CASCADE` through the ORM relationship (`cascade="all, delete-orphan"`); one user -> many rows of each.

### API (33 routes, prefix `/api`)
health GET · public/showcase GET · auth/signup POST · auth/login POST · auth/me GET · meta GET · profile PUT · profile/demo-data POST ·
dashboard GET · transactions GET, POST · transactions/predict-category POST · transactions/{id} PUT, DELETE · transactions/import/preview POST · transactions/import/commit POST ·
analytics GET · budgets GET, POST · budgets/{id} DELETE · goals GET, POST · goals/{id} PUT, DELETE · investments GET, POST · investments/{id}/refresh POST · investments/{id} DELETE ·
assistant/insights GET · assistant/ask POST · reports/{pdf|excel|csv} GET · notifications GET · notifications/read-all POST.

### Algorithms and parameters
- Categoriser: `TfidfVectorizer(lowercase=True, ngram_range=(1,2), min_df=1)` -> `LogisticRegression(max_iter=1000)` (default C=1, lbfgs). Seed: 51 (description, category) pairs, 11 categories
  (Food 6, Transport 6, Entertainment 6, Bills 5, Shopping 5, Education 5, Healthcare 5, Travel 4, Rent 3, Investments 3, Salary 3). Model pickled at `ml/expense_model.pkl` (git-ignored; re-created if missing).
  `predict_category` order: ML model -> keyword table (only if the model fails to load) -> "Other". The ML model never outputs "Other".
  On add-transaction with "Auto-detect" the model's label is used; a manual category that differs from the model's prediction triggers `learn_from_correction` (retrain on seed + the user's whole history + the correction; best-effort, errors swallowed).
- Forecast: monthly expense totals -> `slope, intercept = polyfit(x, y, 1)`; next = max(0, slope * n + intercept); trend label increasing if slope > 1, decreasing if slope < -1, else stable; `recent_average` = mean of last 3 months; MIN_MONTHS_REQUIRED = 3. Category forecasts use the same fit per category (missing months filled with 0). `check_budget_overrun_risk` compares predicted category spend to this month's budgets.
- Health score = sum of w_k * s_k, s_k clipped to [0, 100]: savings_rate s=rate/20*100; expense_ratio s=(1-expenses/income)/0.5*100 (0 if no income); budget_adherence = share of budgets at <=100 % (50 if none); emergency_fund = months of expenses covered by balance / 6 * 100 (50 if no expenses); diversification = distinct asset types / 5 * 100 (0 if none); goal_progress = mean % complete (50 if none). Bands: >=90 Excellent, >=75 Good, >=60 Fair, >=40 Needs Improvement, else Critical.
- Budget alerts: used >= 100 % "exceeded" (danger); >= 90 % (warning); >= 75 % (warning); one notification per identical message.
- Import: required columns date, description, amount, category, type; rows with unparsable date, non-numeric or <=0 amount, or blank description are skipped with a "Row n" warning; blank category -> classifier; unknown type -> expense.
- Assistant routing order: can-I-save -> reduce-expenses -> health/score -> where-spending -> category-spend (category name appears in the question) -> optional LLM -> fixed fallback text.

## 4. Data facts

- **No training corpus beyond the 51-pair seed list** in `ml/expense_classifier.py`; no public dataset was used. The seed pairs are short, English, Indian-merchant style phrases.
- `data/sample_transactions.csv`: 34 fictional rows (Jun-Aug 2026), 10 categories (incl. Salary), amounts INR. Loaded for the demo user with dates shifted so the newest month is the current month, plus 3 earlier synthetic months (seeded RNG 411, ~+4 %/month gentle upward drift).
  Demo account after seeding (Oct 2026 run): 68 transactions, 6 monthly expense totals (May-Oct 2026), 5 budgets, 3 goals, 4 holdings.
  **All demo data is fictional/synthetic; nothing is real personal data.** Licence: own work, no third-party data.
- Probe set for the categoriser (`scripts/probe_data.py`): 198 descriptions, 11 categories x 18, three tiers of 6 per category - A seed-like wording, B upper-case UPI/POS/NEFT narrations containing a seed keyword, C unseen merchants/phrases. Written by the team before scoring, never used for training. **Not an independent benchmark.**
- There is no train/test split in the app itself (nothing is trained on a split); evaluation uses the probe set, leave-one-out on the seed set, and the 34-row sample file.

## 5. Measured results (all from `experiments/*.json`)

### 5.1 Expense categoriser (scikit-learn 1.9.1, model re-trained in memory from the seed, same code as the app)
| Measure | Value |
|---|---|
| Probe accuracy, TF-IDF + LR (shipped) | **0.7172** (142/198); macro-P 0.8847, macro-R 0.7172, macro-F1 **0.7614** |
| Tier A (seed-like) / B (statement strings) / C (unseen merchants) | **1.000 / 0.970 / 0.182** |
| Keyword table alone | accuracy 0.5152, macro-F1 0.6623 (A 0.712, B 0.727, C 0.106) |
| Majority class (Food) | accuracy 0.0909 |
| 34-row bundled sample CSV (labels from the file) | accuracy 1.000 (34/34) - the sample vocabulary overlaps the seed list, so this is an optimistic figure |
| Leave-one-out on the 51 seed pairs | accuracy **0.1176** (6/51) - each seed phrase's words appear only in itself, so held-out phrases are unrecognisable; shows how small and non-redundant the seed list is |
| Errors | 56 of 198; **48 predicted "Transport"** (all-unseen text gives a zero feature vector; the decision then comes from the intercepts, where Transport is highest: P(Transport)=0.121 vs 0.056-0.118 for the others). Remaining tier-B errors: `UPI-AMAZON-PAY-8821` -> Entertainment (seed has "amazon prime video"), `UPI-HOSPITAL-BILL` -> Bills |
| Confidence | mean max-probability 0.197 when correct vs 0.130 when wrong (low because 11 classes and 51 examples). Confidence threshold 0.15 keeps 62.1 % of items at 94.3 % accuracy; 0.20 keeps 32.3 % at 98.4 %; 0.25 keeps 7.6 % at 100 %. **The app applies no threshold.** |
| Per-category recall (probe) | 0.611 (Shopping) to 0.778 (Education); precision 1.0 for Healthcare, Rent, Travel, Investments, Salary; **Transport precision 0.273** (the dump class) |
| Learning from corrections (random k of the 66 tier-C items added, 30 draws, evaluated on the rest of tier C) | k=0 0.182; 3 0.188; 6 0.180; 12 0.179; 24 0.188; 36 0.217; 48 0.215 - **generalisation to new merchants barely moves** |
| Repeat-merchant test (one correction of an unseen merchant, then the same merchant narrated 3 other ways: `UPI-X-4412`, `POS X`, `X 2`; 198 tests) | 0.182 before -> **1.000 after one correction** (easy test: variants share the corrected tokens) |
| Speed | 0.84 ms per prediction (sklearn call, in-process); 5.2 ms to retrain from the 51-example seed |
| Note | the pickled model in `ml/` was trained under sklearn 1.5.0 and is loaded by 1.9.1 with an `InconsistentVersionWarning` (works; retrain to remove) |

Base paper (BERT, 50 categories, own data, 80/20 split): accuracy 92.3 %, precision 90.8 %, recall 91.5 %, F1 91.1 %. **Datasets, label sets and model sizes differ; the numbers are not comparable.**

### 5.2 Spending forecast
Demo account, one-step-ahead rolling-origin backtest on its 6 monthly expense totals (May-Oct 2026 = 26,579; 26,878; 28,384; 36,118; 43,579; 30,080 INR), forecasting months 4-6 from the months before (only **3 test points**):
| Method | Aug fcst | Sep fcst | Oct fcst | MAE (INR) | MAPE |
|---|---|---|---|---|---|
| Linear trend (app) | 29,085 | 37,021 | 45,280 | 9,597 | **28.4 %** |
| Mean of all history | 27,280 | 29,490 | 32,308 | 8,385 | **21.4 %** |
| Mean of last 3 | 27,280 | 30,460 | 36,027 | 9,301 | 24.8 % |
| Last value | 28,384 | 36,118 | 43,579 | 9,565 | 27.8 % |
Actuals: 36,118 / 43,579 / 30,080. The trend model followed the Aug-Sep rise but over-shot October. App output for November on the full history: **39,471** (recent 3-month average 36,592, trend "increasing", 6 months used).
Per-category forecast for the demo (INR): Rent 18,000; Investments 7,000; Travel 3,967; Shopping 3,314; Food 2,666; Bills 1,953; Entertainment 1,201; Healthcare 729; Transport 641.
**Synthetic simulation** (not real data; 2,000 users per setting, 12-month histories = level U(20k,60k) + linear drift N(0, 3 %/month) + Gaussian noise + 10 % chance of a +50 % spike; seed 7), one-step-ahead MAPE %:
| Noise (sd / level) | Linear trend (app) | Mean all | Mean last 3 | Last value |
|---|---|---|---|---|
| 0.05 | 13.99 | 16.77 | 13.11 | 13.19 |
| 0.10 | 18.62 | 20.72 | 17.07 | 18.84 |
| 0.20 | 30.84 | 31.06 | 28.23 | 32.44 |
| 0.30 | 53.99 | 54.26 | 51.11 | 56.11 |
By history length at noise 0.10 (linear / mean-all / last-3 / last): 3 months 22.5 / 14.9 / 14.9 / 17.1; 4: 20.8 / 15.9 / 16.0 / 18.1; 5: 18.8 / 15.3 / 15.2 / 17.7; 6: 17.6 / 16.6 / 15.7 / 17.3; 7: 16.9 / 17.8 / 15.8 / 18.0; 8: 17.8 / 20.4 / 17.7 / 19.1; 9: 17.8 / 24.0 / 18.6 / 20.2; 10: 17.9 / 28.0 / 19.7 / 20.9; 11: 17.5 / 33.7 / 20.2 / 21.2.
**Finding:** the linear trend only beats a plain average once ~7+ months exist, and a 3-month mean was at least as good in every simulated setting. The 3-month minimum is therefore too low for this method. Base paper: LSTM RMSE 137.2, MAE 89.5, R² 0.63 on a synthetic savings series (units unstated) - not comparable.

### 5.3 Health score
- Weights sum to 1.0. Demo account Oct 2026: **90.4 / 100, "Excellent"**; components 100 / 100 / 100 / 100 / 80 / 24 (goal progress is the weakest area).
- Sensitivity from a baseline profile (income 65,000; expenses 32,500; savings rate 20 %; balance 100,000; 2 budgets at 60 %/90 %; 2 asset types; goal 40 %): baseline 80.7. Savings rate -10/0/5/10/15/20/30 % -> 50.7 / 50.7 / 58.2 / 65.7 / 73.2 / 80.7 / 80.7 (saturates at 20 %). Expenses 20k/32.5k/45k/55k/65k/75k -> 85.5 / 80.7 / 70.9 / 63.7 / 56.8 / 56.3. Balance 0/50k/100k/195k+ -> 73.0 / 76.8 / 80.7 / 88.0 (caps at 6 months). Goal progress 0..100 % -> 76.7..86.7. Asset types 0..5+ -> 76.7..86.7.
- 5,000 random profiles: score range 8.7-98.2, mean 60.28; bands Critical 1,425, Needs Improvement 680, Fair 1,083, Good 1,594, Excellent 218. Raising the savings rate by 5 points never lowered the score (0 violations in 5,000).
- Savings rate and expense ratio together carry 50 % of the score and are strongly correlated (both derive from income minus expenses); the weights are expert-chosen, not fitted; no user study.

### 5.4 Assistant (rule layer only; LLM not tested)
26 questions written by the team (20 answerable from the user's data, 6 off-topic), demo account:
- Answerable questions handled by the analytics layer: **14 / 20 (70 %)**. Missed: "groceries", "biggest expense", "eating out", "largest purchase", "run out of money", "which category to cut" (all fell to the fixed help text).
- Off-topic questions correctly declined with the help text: 6 / 6; wrongly answered 0.
- Numeric correctness: "How much did I spend on Food?" -> INR 17,365.00 = direct SUM over the same data; top category Rent INR 108,000.00 matches `groupby().max()`.
- Known quirk: "Am I overspending on shopping?" is answered with the Shopping total, not a budget comparison.

### 5.5 Import pipeline
1,000-row CSV with 84 injected bad rows (28 bad dates, 17 negative amounts, 23 blank descriptions, 16 non-numeric amounts) and all categories blank: 84 skipped (exact match), 916 imported with auto-categories; clean + categorise 6.6 s; commit 26.04 s = **35.2 rows/s** (one database session per row - the slow part).

### 5.6 API latency (127.0.0.1, SQLite temp DB with demo data, 30 repetitions per endpoint, 10 for reports/import)
Machine: Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Intel UHD 770 (no discrete GPU, none used), Windows 11 Pro, Python 3.11.9.
| Endpoint | median ms | p95 ms |
|---|---|---|
| GET /health | 4.3 | 19.0 |
| POST /auth/login (bcrypt) | 304.9 | 367.4 |
| GET /dashboard | 67.2 | 129.3 |
| GET /transactions | 12.7 | 38.9 |
| GET /analytics | 72.1 | 128.5 |
| GET /budgets | 19.7 | 51.6 |
| GET /goals | 7.3 | 11.6 |
| GET /investments | 7.0 | 12.8 |
| GET /assistant/insights | 35.9 | 47.9 |
| GET /notifications | 18.1 | 33.2 |
| GET /meta | 7.2 | 11.8 |
| POST /transactions/predict-category | 7.9 | 20.5 |
| POST /assistant/ask (analytics / health) | 21.6 / 28.4 | 47.9 / 47.8 |
| POST /transactions (auto-categorise) | 15.2 | 20.2 |
| GET /reports/csv / excel / pdf | 17.7 / 209.4 / 135.5 | 30.5 / 341.6 / 201.8 |
| POST /transactions/import/preview (100 rows) | 667.0 | 933.3 |
Single user, single process, warm server. No load or concurrency test was run.

## 6. Testing (real runs, 2026-10-22)
- `pytest`: **38 passed**, 0 failed (auth 9, budget 6, financial_health 6, ml 9, transactions 8), 11.5 s; 16 warnings (sklearn pickle version). Tests use a temp SQLite file per test (`tests/conftest.py`).
- `scripts/smoke_test.py` (starts its own backend on a spare port + throw-away DB): **49 / 49 checks passed** - auth (weak password rejected, wrong password rejected, tampered token rejected, protected route returns 401), demo data, new-user isolation, transaction add/edit/delete, CSV import, budgets/goals/investments, analytics (bad range rejected), assistant, PDF/Excel/CSV downloads, profile (duplicate e-mail rejected), demo-data loader.
- Not tested: browser-level automated UI tests (screens were captured with Playwright and inspected by eye), concurrency, penetration/security scan, accessibility audit, LLM layer, `yfinance` refresh.

## 7. Screenshot inventory (`docs/screenshots/`, 1440x900, real app, demo account, Oct 2026)
01_landing-dark · 02_landing-light · 03_login · 04_signup · 05_dashboard · 06_dashboard-charts · 07_transactions-add · 08_transactions-manage · 09_transactions-import · 10_analytics · 11_analytics-prediction · 12_budgets · 13_goals · 14_investments · 15_assistant · 16_reports · 17_notifications · 18_profile · 19_dashboard-light (19 PNGs, 120-300 KB each). Produced by `scripts/capture_screens.py` in the frontend phase. Data on screen is the fictional demo account (net worth INR 2,82,632; health score 90).

## 8. Known defects and honest gaps (put these in Limitations/Results)
1. Unseen merchants are silently mis-labelled (mostly "Transport"); no abstain/threshold. Tier C accuracy 18.2 %.
2. Corrections help repeat merchants (100 % after one correction) but barely help new merchants (21.5 % after 48).
3. Seed list is tiny (51 pairs, 3-6 per class); LOO-CV 11.8 %.
4. Linear-trend forecast is not better than a mean with <7 months; demo backtest has only 3 points.
5. No anomaly detection, no RL budgeting, no LSTM/ARIMA, no BERT - the base paper's four-model design is only partly matched (categorisation and forecasting in simpler form; budgeting rule-based).
6. Import commits one row per transaction (35.2 rows/s); `get_budget_status` uses `<= YYYY-MM-31` as the month end (works on SQLite date strings, would break on strict databases); Budget alert de-duplication is by message text only, so a budget re-crossing in a later month raises no new alert.
7. Tokens are home-made HMAC bearer tokens (no refresh/revocation); default secret `finjarvis-dev-secret` if `APP_SECRET_KEY` is not set; CORS limited to localhost:5411.
8. `passlib` requires `bcrypt==4.0.1` (bcrypt 5 breaks hashing) - pinned in `backend/requirements.txt`.
9. Single-user SQLite, no migrations; data is local.
10. Not financial advice; assistant shows a disclaimer.
