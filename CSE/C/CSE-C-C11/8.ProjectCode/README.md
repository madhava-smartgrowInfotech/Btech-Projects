# FINJARVIS — Your AI-Powered Personal Finance Assistant

FINJARVIS is a local, single-user-per-account personal finance manager built
entirely in Python. It runs as a Streamlit app backed by a local SQLite
database — no external services are required to use the core features.

## 1. Features

- **Authentication**: signup/login/logout with bcrypt-hashed passwords, per-user data isolation
- **Dashboard**: balance, income/expenses, savings rate, net worth, financial health gauge, 7 interactive charts
- **Transactions**: add/edit/delete/search/filter/sort, custom categories, CSV/Excel import with preview
- **AI Expense Categorization**: TF-IDF + Logistic Regression model that learns from your corrections
- **Budgets**: monthly per-category budgets with 75/90/100% threshold alerts
- **Goals**: savings goals with progress bars, required-monthly-savings and completion estimates
- **AI Assistant (FINJARVIS)**: answers questions about *your own* data; optional LLM layer if `AI_API_KEY` is set
- **Financial Health Score**: explainable 0–100 score across 6 weighted factors
- **Spending Prediction**: linear-trend ML prediction of next month's expenses (says so if there's not enough history — never invents numbers)
- **Investments**: manual portfolio tracking with optional live price refresh via `yfinance`
- **Reports**: PDF (ReportLab), Excel (OpenPyXL), and CSV export
- **Notifications**: budget/goal alerts surfaced in-app
- **Offline mode**: everything except live market prices and LLM chat works with no internet connection
- **Demo data**: one-click fictional sample data (₹) to try the app immediately

## 2. Technology Stack

Python 3.11+, Streamlit, SQLite + SQLAlchemy, Pandas, NumPy, Plotly, scikit-learn,
bcrypt/passlib, python-dotenv, Pydantic, yfinance, ReportLab, OpenPyXL, Anthropic SDK (optional).

## 3. Installation

### Windows
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Environment Variables

Copy `.env.example` to `.env` and fill in what you need:

```bash
cp .env.example .env
```

- `AI_API_KEY` — optional. Enables free-form LLM answers in the AI Assistant. Leave blank to use the built-in analytics-only assistant.
- `MARKET_DATA_API_KEY` — currently unused by the bundled `yfinance` integration (which needs no key), reserved for swapping in a paid provider.
- `APP_SECRET_KEY` — set to any long random string.
- `DEFAULT_CURRENCY` — display default, e.g. `INR`.

Never commit your real `.env` file or paste real API keys into source code.

## 5. Database Setup

Nothing to do manually — the SQLite database (`finjarvis.db`) is created and
initialized automatically the first time you run the app.

## 6. Running the Application

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).

On first use: sign up for an account, then optionally click **Load Demo Data**
on the Profile page to populate a few months of fictional sample transactions,
budgets, goals, and investments.

## 7. Running Tests

```bash
pytest
```

Tests run against an isolated temporary SQLite database (see
`tests/conftest.py`) and never touch your real `finjarvis.db`.

## 8. Project Structure

```
FINJARVIS/
  app.py                     Streamlit entry point, routing, session state
  requirements.txt
  .env.example
  database/
    database.py              Engine/session management, init_db()
    models.py                SQLAlchemy models
  auth/
    authentication.py        Signup/login, password hashing
  services/
    transaction_service.py
    budget_service.py
    goal_service.py
    investment_service.py
    analytics_service.py
    ai_service.py             FINJARVIS AI Assistant (analytics + optional LLM)
    report_service.py         PDF/Excel/CSV generation
    data_import_service.py    CSV/Excel transaction import
  ml/
    expense_classifier.py     TF-IDF + Logistic Regression auto-categorization
    spending_prediction.py    Linear-trend next-month spending prediction
    financial_health.py       0-100 explainable health score
  ui/
    dashboard.py, transactions.py, budgets.py, goals.py, investments.py,
    analytics.py, ai_assistant.py, reports.py, notifications.py, profile.py
  utils/
    validators.py, helpers.py, security.py, demo_data.py
  data/
    sample_transactions.csv
  reports/                    Generated report files land here
  tests/
    test_auth.py, test_transactions.py, test_budget.py,
    test_financial_health.py, test_ml.py, conftest.py
```

## 9. AI Configuration

The AI Assistant works out of the box using a deterministic analytics layer —
it can already answer questions like "How much did I spend on Food?" or
"What is my financial health?" using only your own data, no API key required.

To enable richer free-form conversation, set `AI_API_KEY` in `.env` to an
Anthropic API key. If the key is missing or a request fails, the assistant
automatically falls back to the analytics layer rather than erroring out.

FINJARVIS never claims to be a certified financial advisor, and every AI
response includes a disclaimer that its suggestions are informational only.

## 10. Market Data Configuration

Live investment prices use `yfinance`, which needs no API key for publicly
traded tickers. If a symbol can't be resolved or you're offline, the app
falls back to your manually entered current price and tells you so — it
never silently fabricates a price.

## 11. Deploying to Railway

The repo already includes `Procfile`, `railway.json`, `runtime.txt`, and
`.streamlit/config.toml` for Railway.

1. Push this project to a GitHub repo (or use `railway up` from this folder with the Railway CLI).
2. In Railway, create a new project from that repo — it auto-detects Python via Nixpacks and uses the `Procfile`/`railway.json` start command.
3. In the service's **Variables** tab, set whatever you need from `.env.example` (`AI_API_KEY`, `APP_SECRET_KEY`, etc.) — Railway injects these as real environment variables, so `.env` itself isn't needed in production.
4. Railway sets `$PORT` automatically; the start command already binds to it (`--server.port=$PORT --server.address=0.0.0.0`).
5. Deploy. Railway gives you a public URL once the build finishes.

**Important — SQLite persistence**: Railway's default filesystem is ephemeral, so `finjarvis.db` will reset on every redeploy/restart unless you attach a [Railway Volume](https://docs.railway.app/reference/volumes) and mount it at the project root (or point `DB_PATH` in `database/database.py` at the mounted volume path). Without a volume, treat deployments as suitable for demos/testing rather than durable production data.

## 12. Troubleshooting

- **`streamlit: command not found`** — activate your virtual environment first, or run `python -m streamlit run app.py`.
- **Charts look empty** — add a few transactions first, or click **Load Demo Data** on the Profile page.
- **AI Assistant says free-form chat is unavailable** — set `AI_API_KEY` in `.env` and restart the app.
- **Investment price refresh fails** — this usually means no internet connection or an unrecognized ticker symbol; enter the current price manually instead.
- **`ModuleNotFoundError`** — make sure your virtual environment is activated and `pip install -r requirements.txt` completed without errors.
- **Database looks out of date after editing models** — delete `finjarvis.db` (you'll lose data) and restart the app to reinitialize a fresh schema.
