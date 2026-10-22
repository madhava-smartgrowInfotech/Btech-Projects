# FRONTEND PLAN - FINJARVIS (AI Based Personal Finance Manager)

Batch CSE-C-C11 · Design **V1 Aurora Glass** · Backend port **8411** · Frontend port **5411**

## 1. Starting point

The product is a **Streamlit** app (`app.py` + `ui/*.py`) on top of a plain-Python service layer
(`services/`, `ml/`, `auth/`, `utils/`) and SQLite (`finjarvis.db`, SQLAlchemy). It has **no HTTP API**.

Plan: leave the Streamlit app and every service function untouched. Add a thin FastAPI layer in `backend/`
that imports those existing functions, and a new React/Vite/TypeScript frontend in `frontend/`.

Findings from the inventory (not changed in the existing code):
- `passlib` 1.7.4 + `bcrypt` 5.x fails with "password cannot be longer than 72 bytes" (19 of the existing tests
  fail for this reason, plus Windows temp-file locking in `conftest.py`). `backend/requirements.txt` pins
  `bcrypt==4.0.1`, which is what `requirements.txt` (`bcrypt>=4.1.2`) cannot guarantee.
- `finjarvis.db` is committed (empty). The backend accepts `FINJARVIS_DB` to point at another file for tests,
  by rebinding the session, without editing `database/`.
- `data/sample_transactions.csv` is dated June 2026; "Load Demo Data" therefore fills older months, not the current one.
- The shipped `venv/` points at a missing Python 3.14. `run.bat` builds a fresh `.venv`.

## 2. Features and screens that exist today (Streamlit)

| # | Streamlit page | Features |
|---|---|---|
| F1 | Login / Sign Up | signup (name, email, username, password+confirm, strength rules), login by username or email, logout, per-user isolation |
| F2 | Dashboard | 8 KPI tiles (balance, income, expenses, savings, savings rate, investment value, net worth, avg budget usage); financial health gauge + rating + weakest area; budget alerts (>=75/90/100%); 6 charts: income vs expenses, spending by category, monthly trend, investment allocation, budget vs actual, goal progress; raises notifications as a side effect |
| F3 | Transactions - Add | date, description, amount, type, category (Auto-detect AI / existing / new custom), payment method, notes; AI category shown; manual pick that differs from model = correction the model learns from |
| F4 | Transactions - View/Manage | filters (from, to, category, type), search, sort (date/amount/category, asc/desc), edit (description, amount, category), delete |
| F5 | Transactions - Import | CSV/Excel upload, column validation, row cleaning with per-row warnings, auto-categorise missing categories, preview, confirm import |
| F6 | Analytics | date range + type filter; income, expenses, savings rate, avg daily spend, largest expense, top category; category distribution; income vs expense split; spending trend; ML next-month expense prediction (honest "not enough history" message), recent 3-month average, trend, per-category predictions and predicted budget overruns |
| F7 | Budgets | month/year selector, set/update budget per category, status with progress and 75/90/100% states, delete |
| F8 | Goals | add (preset or custom name, target, saved so far, target date), progress %, required monthly savings, update saved amount (auto-completes), delete |
| F9 | Investments | add holding (name, symbol, type, qty, buy price, current price, date), portfolio totals + return %, allocation + P/L charts, holdings list, refresh live price (yfinance, graceful failure), delete |
| F10 | AI Assistant | insights list, chat (analytics layer + optional Anthropic LLM when `AI_API_KEY` set), example prompts, disclaimer, "analytics only" notice when no key |
| F11 | Reports | month/year; generate and download PDF, Excel, transactions CSV |
| F12 | Notifications | list (type icon, NEW marker, time), mark all as read |
| F13 | Profile | name, email, monthly income, currency, risk preference, savings target; Load Demo Data |
| F14 | Cross-cutting | sidebar navigation, welcome name, currency formatting (INR default) |

## 3. API (new `backend/` FastAPI layer; every route wraps an existing function)

Auth is a signed bearer token (HMAC with `APP_SECRET_KEY`); all routes except health/auth need it.
Requests are JSON unless marked.

| Method | Path | Wraps | Request | Response |
|---|---|---|---|---|
| GET | `/api/health` | - | - | `{status, ai_llm_enabled}` |
| POST | `/api/auth/signup` | `auth.signup` | `{name,email,username,password,confirm_password}` | `{message,user_id}` / 400 `{detail}` |
| POST | `/api/auth/login` | `auth.login` | `{identifier,password}` | `{token,user}` / 401 |
| GET | `/api/auth/me` | `User` row | - | `user` |
| PUT | `/api/profile` | profile page logic | `{name,email,monthly_income,currency,risk_profile,savings_target}` | `user` |
| POST | `/api/profile/demo-data` | `utils.demo_data.load_demo_data` | - | `{message}` |
| GET | `/api/dashboard` | `summary_metrics`, `get_budget_status`, `portfolio_summary`, `get_goals`, `calculate_financial_health`, `check_and_raise_alerts`, `spending_by_category`, `monthly_trend` | - | metrics, health, budget_status, alerts, charts data |
| GET | `/api/transactions` | `get_transactions` | query: start,end,category,type,q,sort,order | `{items,total}` |
| GET | `/api/transactions/categories` | `get_all_categories` | - | `{categories,payment_methods}` |
| POST | `/api/transactions/predict-category` | `predict_category` | `{description}` | `{category}` |
| POST | `/api/transactions` | `add_transaction` (+ `predict_category`, `learn_from_correction`) | `{date,description,amount,transaction_type,category?,payment_method,notes}` | `{id,category,auto_categorised}` |
| PUT | `/api/transactions/{id}` | `update_transaction` | `{description,amount,category}` | `{ok}` / 404 |
| DELETE | `/api/transactions/{id}` | `delete_transaction` | - | `{ok}` / 404 |
| POST | `/api/transactions/import/preview` | `load_and_validate`, `clean_and_prepare` | multipart file | `{rows,warnings,errors}` |
| POST | `/api/transactions/import/commit` | `commit_import` | multipart file | `{imported}` |
| GET | `/api/analytics` | `analytics_overview`, `spending_by_category`, `monthly_trend`, `transactions_dataframe`, `predict_*`, `check_budget_overrun_risk` | query: start,end,type | overview, charts, prediction |
| GET | `/api/budgets` | `get_budget_status` | query: month,year | `{items}` |
| POST | `/api/budgets` | `set_budget` | `{category,budget_amount,month,year}` | `{id}` |
| DELETE | `/api/budgets/{id}` | `delete_budget` | - | `{ok}` |
| GET | `/api/goals` | `get_goals` | - | `{items}` |
| POST | `/api/goals` | `add_goal` | `{goal_name,target_amount,current_amount,target_date}` | `{id}` |
| PUT | `/api/goals/{id}` | `update_goal_progress` | `{current_amount}` | `{ok}` |
| DELETE | `/api/goals/{id}` | `delete_goal` | - | `{ok}` |
| GET | `/api/investments` | `portfolio_summary` | - | summary + holdings |
| POST | `/api/investments` | `add_investment` | form fields | `{id}` |
| POST | `/api/investments/{id}/refresh` | `refresh_price` | - | `{success,message}` |
| DELETE | `/api/investments/{id}` | `delete_investment` | - | `{ok}` |
| GET | `/api/assistant/insights` | `generate_insights` | - | `{insights,disclaimer,llm_enabled}` |
| POST | `/api/assistant/ask` | `answer_question` | `{question}` | `{answer,disclaimer,source}` |
| GET | `/api/reports/{pdf,excel,csv}` | `generate_pdf_report`, `generate_excel_report`, `generate_csv_report` | query: month,year | file download |
| GET | `/api/notifications` | `Notification` query | - | `{items,unread}` |
| POST | `/api/notifications/read-all` | `Notification` update | - | `{ok}` |

Additive pieces with no Streamlit equivalent (needed for a browser client): bearer-token issue/verify, `/api/auth/me`,
`/api/health`, the unread count, and a combined `/api/dashboard` read. They do not alter any service behaviour.

## 4. Screen map (every feature F1-F14 appears)

| Route | Screen | Covers |
|---|---|---|
| `/` | Landing (Aurora Glass hero, live-looking feature sections, how it works, stats strip, CTA) | marketing, F14 |
| `/login`, `/signup` | Auth (glass card) | F1 |
| `/app` | Dashboard | F2 |
| `/app/transactions` | Tabs: Add - View/Manage - Import | F3, F4, F5 |
| `/app/analytics` | Analytics + ML prediction | F6 |
| `/app/budgets` | Budgets | F7 |
| `/app/goals` | Goals | F8 |
| `/app/investments` | Investments | F9 |
| `/app/assistant` | AI Assistant | F10 |
| `/app/reports` | Reports | F11 |
| `/app/notifications` | Notifications | F12 |
| `/app/profile` | Profile + demo data | F13 |
| `*` | Not found | - |

Shell: kit `AppShell` (sidebar becomes a drawer below lg), topbar with theme toggle (persisted), notification bell with unread
count, user menu with logout.

## 5. Kit adaptation notes

The kit's `AppShell`, landing parts, and tokens file (`src/index.css`, not `styles/tokens.css`) are product-coupled; the copies in
`frontend/src` are adapted, the kit folder is not touched. Missing from the kit and written locally: `lib/api`, `lib/format`,
`lib/gsap`, `AuroraBackground`, `ThemeToggle`, tsconfigs, `vite.config.ts` (proxy `/api` to 8411, port 5411).

## 6. Feature check (verified in Step 4)

Verified by `scripts/smoke_test.py` (49 API checks), a 31-step browser walk (Playwright, real Chrome), and the original 38 unit tests.

- [x] F1 Auth: sign-up (with the same strength rules), login by username or email, logout, guarded routes, per-user isolation
- [x] F2 Dashboard: 8 KPI tiles, health score with factor breakdown, budget alerts, six charts
- [x] F3 Add transaction: auto-detect with live AI suggestion, custom category, learning from corrections
- [x] F4 View / edit / delete: date, category and type filters, search, sort, edit dialog, delete confirmation
- [x] F5 Import CSV / Excel: validation, per-row warnings, auto-category, preview, confirm
- [x] F6 Analytics + ML prediction: range filter, overview, charts, next-month forecast, honest "not enough history", overrun risks
- [x] F7 Budgets: month / year, set, status with 75 / 90 / 100% states, delete
- [x] F8 Goals: preset or custom, progress, required monthly saving, update (auto-complete), delete
- [x] F9 Investments: add, totals, allocation and P/L charts, live-price refresh with graceful failure, delete
- [x] F10 AI Assistant: insights, chat, examples, disclaimer, "analytics only" notice when no key
- [x] F11 Reports: PDF, Excel, transactions CSV download
- [x] F12 Notifications: list, unread markers, mark all read, live unread badge
- [x] F13 Profile: details, currency, risk, targets, demo data
- [x] F14 Navigation and currency formatting (drawer sidebar on phones, user currency everywhere)

## 7. Differences from the plan above

- Added `GET /api/meta` (form choices), `GET /api/public/showcase` (landing numbers from the demo account) and the demo account itself
  (`demo` / `Demo@1234`, created on first start). Both are additive and read-only.
- The Analytics "Type" filter was decorative in Streamlit; it now switches the category chart between spending and income.
- "Load demo data" shifts the sample CSV to the current month instead of using its fixed June-August 2026 dates.
- `backend/requirements.txt` pins `bcrypt==4.0.1` (passlib is incompatible with bcrypt 5).
- Nothing in `services/`, `ml/`, `auth/`, `database/`, `utils/` or `ui/` was changed. The only edited existing files are `tests/conftest.py`
  (dispose the engine before deleting the temp DB), `.env.example` (ports) and `README.md` (a pointer to the web app).
