"""Appendices A (important code), B (installation and user guide) and C (additional screens) for FINJARVIS.

Code excerpts are cut from the real files in 8.ProjectCode at build time, so they can never drift from the code.
"""
import ast
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB


# ------------------------------------------------------------------------------ source helpers
def _read(rel):
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        return f.read()


def fn(rel, name, doc=False):
    """Source of a module-level function exactly as it stands (docstring removed unless doc=True)."""
    text = _read(rel)
    lines = text.split("\n")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            start = min([d.lineno for d in node.decorator_list] + [node.lineno])
            end = node.end_lineno
            body = lines[start - 1:end]
            if not doc and ast.get_docstring(node):
                d = node.body[0]
                body = lines[start - 1:d.lineno - 1] + lines[d.end_lineno:end]
            return "\n".join(body)
    raise KeyError(name)


def between(rel, first, last):
    """Lines from the first line containing `first` to the first later line containing `last` (inclusive)."""
    lines = _read(rel).split("\n")
    i = next(k for k, l in enumerate(lines) if first in l)
    j = next(k for k in range(i, len(lines)) if last in lines[k])
    return "\n".join(lines[i:j + 1])


def _wrap(text, width=104):
    """Wrap over-long code lines at a space, indenting the continuation, so a listing never runs off the page."""
    out = []
    for line in text.split("\n"):
        while len(line) > width:
            cut = line.rfind(" ", 0, width)
            if cut < 20:
                cut = width
            out.append(line[:cut])
            line = " " * (len(line) - len(line.lstrip()) + 8) + line[cut:].lstrip()
        out.append(line)
    return "\n".join(out)


def _C(text, size):
    return CODE(_wrap(text), size)


# ------------------------------------------------------------------------------ Appendix A
def _intro():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The key functions are copied from `8.ProjectCode` as they stood when the results were measured; docstrings are removed to save space (the full files are in the repository). "
          "The categoriser and the forecast in Sections A.1 and A.2 and the health score in Section A.3 are explained with formulas in Chapter 6; Sections A.4 to A.6 show how alerts, tokens and the assistant's routing are written."),
    ]


def _common():
    return _intro() + [
        H2("A.1 Expense categoriser (ml/expense_classifier.py)"),
        P("The whole training set is the 51-pair seed list. The pipeline is TF-IDF over word unigrams and bigrams followed by a logistic regression. `predict_category` uses the trained model first and the keyword table only if the model cannot be loaded; "
          "the model never returns Other. `learn_from_correction` retrains on the seed list, the user's history and the correction."),
        _C(between("ml/expense_classifier.py", "SEED_TRAINING_DATA = [", "]"), 7.6),
        _C(fn("ml/expense_classifier.py", "_train_pipeline") + "\n\n" + fn("ml/expense_classifier.py", "train_and_save") + "\n\n" + fn("ml/expense_classifier.py", "predict_category") + "\n\n"
           + fn("ml/expense_classifier.py", "learn_from_correction"), 7.6),
        H2("A.2 Spending forecast (ml/spending_prediction.py)"),
        P("A least-squares line through the monthly expense totals, clipped at zero; with fewer than three months the function refuses to predict and says so. "
          "The category forecast repeats the fit per category, and the overrun check compares each category's forecast with this month's budgets."),
        _C(fn("ml/spending_prediction.py", "predict_next_month_expense") + "\n\n" + fn("ml/spending_prediction.py", "predict_category_spending") + "\n\n"
           + fn("ml/spending_prediction.py", "check_budget_overrun_risk"), 7.6),
        H2("A.3 Financial health score (ml/financial_health.py)"),
        P("Six clipped component scores are combined with fixed weights that sum to 1. The weakest component is reported with a plain-language reason."),
        _C(between("ml/financial_health.py", "WEIGHTS = {", "}") + "\n\n" + fn("ml/financial_health.py", "score_savings_rate") + "\n\n" + fn("ml/financial_health.py", "score_expense_ratio") + "\n\n"
           + fn("ml/financial_health.py", "score_budget_adherence") + "\n\n" + fn("ml/financial_health.py", "score_emergency_fund") + "\n\n" + fn("ml/financial_health.py", "score_investment_diversification")
           + "\n\n" + fn("ml/financial_health.py", "score_goal_progress"), 7.6),
        _C(fn("ml/financial_health.py", "calculate_financial_health"), 7.2),
        H2("A.4 Budget alerts (services/budget_service.py)"),
        P("One notification is written when a budget crosses 75, 90 or 100 % of its amount; an identical message is never written twice, which is why the Notifications page in Chapter 8 still shows the 75 % message for a budget that now stands at 88 %."),
        _C(fn("services/budget_service.py", "check_and_raise_alerts"), 7.4),
        H2("A.5 Tokens and the authentication dependency (backend/main.py)"),
        P("A token is a base64 payload with the user id and an expiry (seven days) followed by an HMAC-SHA256 signature; `current_user` is the FastAPI dependency that every protected route declares, so every query is scoped to the logged-in user."),
        _C(between("backend/main.py", "SECRET = ", "TOKEN_TTL") + "\n\n" + fn("backend/main.py", "make_token") + "\n\n" + fn("backend/main.py", "read_token") + "\n\n" + fn("backend/main.py", "current_user"), 7.4),
        H2("A.6 Assistant routing (services/ai_service.py)"),
        P("Five rule handlers are tried in order; the optional language model is consulted only if none matches, and a fixed help text is returned otherwise. This is the function whose behaviour is measured in Section 8.6."),
        _C(fn("services/ai_service.py", "answer_question"), 7.4),
        H2("A.7 Statement cleaning (services/data_import_service.py)"),
        P("Every row is parsed on its own; a bad date, a non-numeric or non-positive amount or a blank description skips only that row and adds a `Row n` warning. A blank category is filled by the categoriser."),
        _C(fn("services/data_import_service.py", "clean_and_prepare"), 7.2),
    ]


def _report():
    return _intro() + [
        H2("A.1 Expense categoriser (ml/expense_classifier.py)"),
        _C(fn("ml/expense_classifier.py", "_train_pipeline") + "\n\n" + fn("ml/expense_classifier.py", "predict_category") + "\n\n" + fn("ml/expense_classifier.py", "learn_from_correction"), 7.2),
        H2("A.2 Spending forecast (ml/spending_prediction.py)"),
        _C(fn("ml/spending_prediction.py", "predict_next_month_expense"), 7.2),
        H2("A.3 Financial health score (ml/financial_health.py)"),
        _C(between("ml/financial_health.py", "WEIGHTS = {", "}") + "\n\n" + fn("ml/financial_health.py", "score_savings_rate") + "\n\n" + fn("ml/financial_health.py", "score_emergency_fund")
           + "\n\n" + fn("ml/financial_health.py", "score_goal_progress"), 7.0),
        H2("A.4 Budget alerts (services/budget_service.py)"),
        _C(fn("services/budget_service.py", "check_and_raise_alerts"), 7.0),
        H2("A.5 Tokens and the authentication dependency (backend/main.py)"),
        _C(fn("backend/main.py", "make_token") + "\n\n" + fn("backend/main.py", "read_token") + "\n\n" + fn("backend/main.py", "current_user"), 7.0),
    ]


def code_blocks():
    return _report() if F.REPORT else _common()


# ------------------------------------------------------------------------------ Appendix B
def guide_blocks():
    out = [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        TAB("Requirements", ["Item", "Needed"],
            [["Operating system", "Windows 10 or 11 for `run.bat` (measured on Windows 11 Pro); the Python and Node commands also work on other systems"],
             ["Python", "3.11 or newer on PATH (the measurements used Python 3.11.9)"],
             ["Node.js and npm", "Node 20 or newer; the web app uses Vite, React 18, TypeScript, Tailwind CSS v4, Recharts and TanStack Query"],
             ["Python packages", "`backend/requirements.txt`: fastapi, uvicorn, python-multipart, httpx, sqlalchemy, pandas, numpy, scikit-learn, bcrypt 4.0.1 (pinned), passlib, python-dotenv, pydantic, yfinance, reportlab, openpyxl, requests, anthropic, pytest"],
             ["Extra for screenshots", "`pip install playwright` and `playwright install chromium` (or an installed Google Chrome)"],
             ["Hardware", "Any recent laptop; the measurements used an Intel Core i5-12500 with 15.7 GB of memory and no GPU"],
             ["Accounts and keys", "None required. `AI_API_KEY` (an Anthropic key) is optional and enables free-form assistant answers; without it the built-in analytics answers"]],
            widths=[1.7, 4.7], align=["l", "l"], size=10),
        H2("B.2 Installation and start with run.bat"),
        N("Copy or clone the project so that `8.ProjectCode` is on a local disk.",
          "Open the folder and double-click `run.bat` (or run it from a command prompt). It checks that Python and Node are installed, creates `.venv` if absent (and rebuilds one that was copied from another PC), "
          "installs `backend\\requirements.txt` and runs `npm install` in `frontend` the first time (a few minutes).",
          f"It starts the FastAPI backend on port {F.API_PORT} and the web app on port {F.WEB_PORT} in two minimised windows and opens the browser at `http://localhost:{F.WEB_PORT}`. Keep both windows open.",
          f"Log in with the built-in demo account `{F.DEMO_USER}` / `{F.DEMO_PASS}` (or press Try the demo account) or create your own account. To stop, close the two windows.",
          "For the documentation run the servers were started by `scripts/capture_screens.py` and the measurement scripts, which start their own backend on a throw-away database; a fresh-machine installation through `run.bat` was not repeated."),
        H2("B.3 Manual start and settings"),
        _C("# backend (from 8.ProjectCode)\n"
           "python -m venv .venv\n"
           ".venv\\Scripts\\python.exe -m pip install -r backend\\requirements.txt\n"
           f".venv\\Scripts\\python.exe -m uvicorn backend.main:app --port {F.API_PORT}\n\n"
           "# frontend (from 8.ProjectCode\\frontend)\n"
           "npm install\n"
           f"npm run dev          # http://localhost:{F.WEB_PORT}, proxies /api to {F.API_PORT}\n"
           "npm run build        # production build into frontend\\dist\n\n"
           "# the original Streamlit app over the same database\n"
           "streamlit run app.py   # http://localhost:8501", 8.0),
        P("Settings are read from `.env` (copy `.env.example`); every one is optional. `.env` is git-ignored and must never be committed."),
        TAB("Environment variables", ["Variable", "Meaning"],
            [["BACKEND_PORT / FRONTEND_PORT", f"Ports used by `run.bat` (default {F.API_PORT} / {F.WEB_PORT})"],
             ["APP_SECRET_KEY", "Signs the login tokens; set a long random string (a development default is used otherwise)"],
             ["AI_API_KEY", "Optional Anthropic key; enables free-form answers in the AI assistant"],
             ["MARKET_DATA_API_KEY", "Optional key for the market-data provider listed in `.env.example`"],
             ["DEFAULT_CURRENCY", "Display default (INR)"],
             ["FINJARVIS_DB", "Path of a different SQLite file; the tests and measurement scripts use it so that real data is never touched"]],
            widths=[2.4, 4.0], align=["l", "l"], size=9.5),
        H2("B.4 Using the web app"),
        TAB("Steps for each page", ["Page", "What to do", "What you see"],
            [["Landing /", "Read the product summary; press Create free account, Log in or Try the demo account", "A demo card with the health score and a six-month curve computed from the demo account"],
             ["Login and sign-up", "Enter a username or e-mail and a password, or create an account with a name, e-mail, username and a password with 8 or more characters, an upper-case and a lower-case letter, a digit and a special character", "Password-rule chips that tick as you type; a welcome toast"],
             ["Dashboard", "Read the eight summary cards, the health score and the budget alerts; press Add transaction", "Charts of income against expenses, spending by category, the monthly trend and the investment allocation"],
             ["Transactions", "Add: fill the form and leave the category on Auto-detect or choose one to teach the model. View / manage: filter, search, sort, edit or delete. Import: drop a CSV or Excel file with columns date, description, amount, category and type", "A preview with skipped-row warnings before anything is saved"],
             ["Analytics", "Choose a date range and what the category chart shows", "Totals, savings rate, daily average, largest expense, charts, the next-month prediction and any predicted budget overrun"],
             ["Budgets", "Pick a month, a category and an amount; saving again for the same category updates it", "Progress bars with On track, Getting close or Over budget badges; alerts at 75, 90 and 100 %"],
             ["Goals and Investments", "Add a goal with a target amount and date, update the saved amount; add holdings and press Price to refresh a live price (needs internet)", "Progress, the monthly saving needed, portfolio value, profit and loss"],
             ["AI Assistant", "Type a question or press a suggestion", "An answer calculated from your data, with a disclaimer; the insights panel on the right"],
             ["Reports", "Choose month and year; press Generate PDF, Generate Excel or Export CSV", "A downloaded file"],
             ["Notifications and Profile", "Mark alerts as read; edit name, income, savings target, currency and risk preference; Load demo data adds fictional records", "The unread count in the sidebar and the bell"]],
            widths=[1.2, 3.1, 2.2], align=["l", "l", "l"], size=9),
        P("The assistant understands questions of these kinds: how much did I spend on a category, where am I spending the most, can I save an amount this month, how can I reduce my expenses and what is my financial health. "
          "Other phrasings receive a fixed help text (Section 8.6). The application gives information, not financial advice, and says so on the assistant page."),
        H2("B.5 API quick reference"),
        P(f"Interactive documentation is served at `http://127.0.0.1:{F.API_PORT}/docs`. The commands below use `curl` with Git Bash quoting; replace TOKEN with the token returned by the login call. Use 127.0.0.1, not localhost, to avoid the IPv6 delay seen on this Windows machine."),
        _C(f"curl http://127.0.0.1:{F.API_PORT}/api/health\n"
           f"curl -X POST -H \"Content-Type: application/json\" -d '{{\"identifier\":\"demo\",\"password\":\"Demo@1234\"}}' http://127.0.0.1:{F.API_PORT}/api/auth/login\n"
           f"curl -H \"Authorization: Bearer TOKEN\" http://127.0.0.1:{F.API_PORT}/api/dashboard\n"
           f"curl -X POST -H \"Authorization: Bearer TOKEN\" -H \"Content-Type: application/json\" -d '{{\"description\":\"Swiggy order\"}}' http://127.0.0.1:{F.API_PORT}/api/transactions/predict-category\n"
           f"curl -X POST -H \"Authorization: Bearer TOKEN\" -H \"Content-Type: application/json\" -d '{{\"question\":\"How much did I spend on Food?\"}}' http://127.0.0.1:{F.API_PORT}/api/assistant/ask\n"
           f"curl -H \"Authorization: Bearer TOKEN\" -o report.pdf \"http://127.0.0.1:{F.API_PORT}/api/reports/pdf\"", 7.6),
        P("The field names of the login and prediction bodies follow the request models in `backend/main.py` (`LoginIn`, `PredictIn`, `AskIn`); check `/docs` for the exact schema of the other routes."),
        H2("B.6 Tests, experiments and screenshots"),
        _C(".venv\\Scripts\\python.exe -m pytest                       # 38 tests\n"
           ".venv\\Scripts\\python.exe scripts\\smoke_test.py           # 49 end-to-end checks on a throw-away database\n"
           ".venv\\Scripts\\python.exe scripts\\run_experiments.py      # classifier, forecast, health, assistant, import -> experiments\\metrics.json\n"
           ".venv\\Scripts\\python.exe scripts\\measure_api.py          # latency -> experiments\\api_latency.json\n"
           "python scripts\\capture_screens.py                         # 19 screenshots -> docs\\screenshots (starts the app itself if needed)", 8.0),
        H2("B.7 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Cause and fix"],
            [["Python or Node was not found", "Install it (tick Add python.exe to PATH for Python), reopen the terminal and run `run.bat` again"],
             ["Server offline in the top bar", "The API is not running. Start `run.bat` or read the FINJARVIS backend window for the error"],
             ["Port already in use", "Change BACKEND_PORT or FRONTEND_PORT in `.env`, or close the program that holds the port"],
             ["Sign-up says the password cannot be longer than 72 bytes", "bcrypt 5 is installed and breaks passlib; delete `.venv` and run `run.bat` again so that bcrypt 4.0.1 is installed"],
             ["`.venv` copied from another PC does not start", "`run.bat` detects this and rebuilds it"],
             ["Live investment price fails", "It needs internet and a ticker such as `NIFTYBEES.NS`; the last known price is kept"],
             ["The assistant says free-form chat is unavailable", "Set `AI_API_KEY` in `.env` and restart; the built-in analytics answers work without it"],
             ["API calls from Python take about 2 seconds", "Use `127.0.0.1` instead of `localhost`"]],
            widths=[2.4, 4.0], align=["l", "l"], size=9.5),
    ]
    return _guide_trim(out) if F.REPORT else out


def _guide_trim(out):
    """Compact variant for the full report: requirements as one sentence, short step table, short troubleshooting."""
    res, skip = [], False
    for b in out:
        if b[0] == "h2":
            skip = b[1].startswith(("B.1", "B.5", "B.6"))
            if b[1].startswith("B.1"):
                res.append(("h2", "B.1 Requirements"))
                res.append(("p", "Python 3.11 or newer, Node.js 20 or newer and the packages in `backend/requirements.txt` (bcrypt is pinned to 4.0.1). No account or key is required; `AI_API_KEY` is optional and enables free-form assistant answers."))
            if b[1].startswith("B.6"):
                res.append(("h2", "B.5 Tests and experiments"))
                res.append(("code", "python -m pytest\npython scripts/smoke_test.py\npython scripts/run_experiments.py\npython scripts/measure_api.py\npython scripts/capture_screens.py", 8.0))
        if skip:
            continue
        if b[0] == "h2" and b[1].startswith("B.7"):
            b = ("h2", "B.6 Troubleshooting")
        if b[0] == "tab" and b[1].startswith("Environment variables"):
            b = ("tab", b[1], b[2], b[3][:3]) + tuple(b[4:])
        if b[0] == "tab" and b[1].startswith("Common problems"):
            keep = ("Server offline", "Port already", "Sign-up says", "Live investment", "The assistant says")
            b = ("tab", b[1], b[2], [r for r in b[3] if r[0].startswith(keep)]) + tuple(b[4:])
        res.append(b)
    return res


# ------------------------------------------------------------------------------ Appendix C
def screens_blocks():
    SH = F.shot

    def pair(a, ca, b, cb):
        return PAIR([(SH(a), ca), (SH(b), cb)], 2.95)

    out = [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("The screens below are captures that are not shown in Chapter 8: the light theme of the landing page and of the dashboard, and the sign-up page. "
          "All were taken from the running application at 1440 x 900 pixels, logged in as the fictional demo account where a login is needed, on 22 October 2026."),
        H2("C.1 Light theme and sign-up pages"),
        pair("02_landing-light.png", "Additional screen: landing page, light theme, with the same demo card (health score 90, income INR 65K, spent INR 30.1K, saved 54 %).",
             "19_dashboard-light.png", "Additional screen: dashboard, light theme: the same eight cards and the health score card as in the dark theme."),
        P("Both themes use the same colour tokens; the toggle sits in the top bar. The light dashboard repeats the figures of the dark one exactly (total balance INR 1,98,382, net worth INR 2,82,632, health score 90), which confirms that the theme changes only the presentation."),
        FIG(SH("04_signup.png"), "Additional screen: sign-up page with the password-rule chips (8+ characters, upper-case, lower-case, a digit, a special character) that turn on as the password satisfies each rule.", F.shot_w(SH("04_signup.png"), 4.8, 3.6)),
        P("The page validates the rules in the browser and the server validates them again (username of 3 to 30 characters, a valid e-mail address, a matching confirmation and a password that meets all five rules). "
          "The name shown in the field is a placeholder, not an account."),
    ]
    if F.REPORT:
        out += [
            H2("C.2 Additional result charts"),
            P("The charts below belong to the measurements of Chapter 8 and are kept here to save space in the chapter."),
            FIG(F.fig("f03_per_category_prf.png"), "Precision, recall and F1 per category on the probe set; Transport recalls everything but is right on only 27 % of what it labels.", 5.4),
            FIG(F.fig("f04_confidence_coverage.png"), "Accuracy on kept predictions and share of items kept as the minimum probability rises (computed offline; the application applies no threshold).", 4.8),
            FIG(F.fig("f13_seed_distribution.png"), "The complete training set of the categoriser: 51 descriptions, 3 to 6 per category.", 4.8),
            FIG(F.fig("f07_sim_mape_noise.png"), "Simulated MAPE of the four forecasting methods against noise (2,000 synthetic users per point).", 4.6),
            FIG(F.fig("f10_health_distribution.png"), "Ratings of 5,000 random profiles under the health score.", 4.2),
            FIG(F.fig("f12_assistant_coverage.png"), "Outcome of the 26 test questions for the assistant's rule layer.", 4.4),
            FIG(F.fig("f11_api_latency.png"), "Median and 95th-percentile latency of every measured endpoint.", 5.2),
        ]
    return out
