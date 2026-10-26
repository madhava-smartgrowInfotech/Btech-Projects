"""Chapters 9 (Conclusion) and 10 (Future scope), plus the shared block lists used by documents 9, 10, 12 and 15.

Every number is read from facts.py (experiments/metrics.json, experiments/api_latency.json); code excerpts are cut from the real files in 8.ProjectCode.
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
    """A result figure, only if it exists."""
    return [FIG(F.fig(name), caption, width)] if os.path.exists(F.fig(name)) else []


def _v():
    """Measured values used in the prose; all read from experiments/metrics.json and api_latency.json through facts.py."""
    c, fc, hl, a, im = F.CLS, F.FC, F.HL, F.AS, F.IMP
    bt = fc["demo_backtest"]
    lc = {d["corrections"]: d["tier_C_accuracy_mean"] for d in c["learning_from_corrections"]}
    cc = {d["threshold"]: d for d in c["confidence_curve"]}
    return dict(
        tests=F.PYTEST_PASSED, smoke=F.SMOKE_PASSED,
        acc=c["tfidf_lr"]["accuracy"], mf1=c["tfidf_lr"]["macro_f1"], tA=c["tfidf_lr"]["accuracy_by_tier"]["A"],
        tB=c["tfidf_lr"]["accuracy_by_tier"]["B"], tC=c["tfidf_lr"]["accuracy_by_tier"]["C"],
        kw=c["keyword_table"]["accuracy"], kwC=c["keyword_table"]["accuracy_by_tier"]["C"], maj=c["majority_class"]["accuracy"],
        loo=c["loo_cv_accuracy_on_seed"], sample=c["sample_csv_accuracy"], terr=c["errors_predicted_as_transport"], nerr=len(c["errors"]),
        tprec=c["per_category"]["Transport"]["precision"], conf_ok=c["mean_confidence_correct"], conf_bad=c["mean_confidence_wrong"],
        cov15=cc[0.15]["coverage"], acc15=cc[0.15]["accuracy_on_kept"],
        k0=lc[0], k48=lc[48], rep_b=c["repeat_merchant_learning"]["accuracy_before_correction"], rep_a=c["repeat_merchant_learning"]["accuracy_after_one_correction"],
        pred_ms=c["predict_ms_per_description"], retrain_ms=c["retrain_ms_seed_only"],
        mape_lin=bt["mape_pct"]["linear_trend (app)"], mape_mean=bt["mape_pct"]["mean_of_all"], mape_l3=bt["mape_pct"]["mean_of_last_3"], mape_last=bt["mape_pct"]["last_value"],
        mae_lin=bt["mae"]["linear_trend (app)"], mae_mean=bt["mae"]["mean_of_all"],
        next_pred=bt["app_prediction_for_next_month"]["predicted_next_month_expense"], recent3=bt["app_prediction_for_next_month"]["recent_average"],
        demo_score=F.LAT["demo_dashboard"]["health_score"], hl_mean=hl["score_mean"], hl_n=hl["random_profiles"], hl_min=hl["score_min"], hl_max=hl["score_max"],
        a_ok=a["answerable_handled_by_analytics"], a_n=a["answerable"], a_off=a["unanswerable_correctly_declined"], a_offn=a["not_answerable"],
        imp_n=im["rows_in_file"], imp_bad=im["rows_skipped"], imp_ok=im["rows_imported"], imp_rate=im["rows_per_second_commit"], imp_commit=im["commit_s"],
        l_login=F.lat("login"), l_dash=F.lat("GET /dashboard"), l_ana=F.lat("GET /analytics"), l_tx=F.lat("GET /transactions"),
        l_pred=F.lat("POST /transactions/predict-category"), l_add=F.lat("POST /transactions (auto"), l_pdf=F.lat("GET /reports/pdf"),
        l_xls=F.lat("GET /reports/excel"), l_prev=F.lat("POST /transactions/import/preview"), l_ask=F.lat("POST /assistant/ask (analytics"),
    )


def _sim_crossover(base="mean_of_all"):
    """Smallest history length (noise 0.10) at which the linear trend has a lower simulated MAPE than `base`."""
    for r in F.FC["sim_mape_by_history_pct_noise_0.10"]:
        if r["linear_trend (app)"] < r[base]:
            return r["history_months"]
    return None


# ---------------------------------------------------------------------------- novelty / contributions
def novelty_blocks():
    v = _v()
    return [
        H2("What the base paper contributes"),
        P(f"The registered base paper {C('base')} describes a Smart Personal Finance Assistant built from four separately trained models: a fine-tuned BERT classifier that sorts transactions into 50 expense categories (with SMOTE to balance classes), "
          "a Q-learning agent that recommends a budget, an LSTM that forecasts savings, and an Isolation Forest that flags anomalous transactions. It reports an accuracy of 92.3 percent, precision 90.8 percent, recall 91.5 percent and F1 91.1 percent for the classifier, "
          "RMSE 137.2, MAE 89.5 and R2 0.63 for the forecaster, and precision 0.93, recall 0.94 and F1 0.94 for the anomaly detector. The data are synthetic or private and are not released, and the paper's interface is a Streamlit prototype."),
        H2("What this project does differently"),
        P("FINJARVIS does not try to match those four models. It is deliberately a smaller system, and it differs from the base paper in the following ways."),
        B("**A complete, runnable web platform.** A person can sign up, log in, import a statement, see a dashboard, set budgets and goals, ask questions and download reports. The base paper describes models and a prototype interface; this project delivers the application around the models.",
          "**Every module is simple enough to inspect.** The categoriser is TF-IDF with logistic regression, the forecast is a least-squares line, the health score is six weighted sub-scores. Each can be explained in a sentence and reproduced with the code in the repository, at no licence or GPU cost.",
          "**An explainable financial health score.** Six components with published weights (0.30, 0.20, 0.15, 0.15, 0.10, 0.10) add up to a 0-100 score, and the screen shows the weakest component and a reason. The base paper has no equivalent summary measure.",
          "**Learning from the user's corrections.** When a manual category differs from the model's prediction, the model is retrained with the user's history and the correction. The measurement shows that this fixes repeat merchants completely and new merchants hardly at all.",
          "**An assistant grounded in the user's own data.** Questions are routed to five analytics handlers that compute the answer from the user's transactions; an optional language-model layer is used only when a key is configured. Answers carry a disclaimer, and off-topic questions are declined.",
          "**Measured failure modes.** The categoriser, the forecast, the health score, the assistant and the import pipeline were each measured on inputs the team wrote or simulated, and the places where they fail are reported rather than hidden."),
        H2("What is not new, and what is missing"),
        P(f"Nothing in the models is new. TF-IDF weighting {C('tfidf')}, logistic regression and a linear trend are standard tools, and the evaluation here is not comparable with the base paper's. The categoriser reaches {v['acc'] * 100:.1f} percent on a 198-description probe set the team wrote, "
          f"against 92.3 percent reported for BERT on a different, larger data set with 50 classes. The forecast covers expenses only, and the base paper's savings forecast, reinforcement-learning budget recommender and anomaly detector are not implemented. "
          "The batch abstract also names Flask and MySQL; the system was built with FastAPI and SQLite, and the abstract's loan tracking and scheduled digests are not implemented."),
        TAB("Base paper modules against this project", ["Base paper module", "Technique in the base paper", "In FINJARVIS"],
            [["Expense categorisation", "Fine-tuned BERT, 50 categories, SMOTE", "TF-IDF + logistic regression, 11 categories + Other, 51 seed examples, retrains on corrections"],
             ["Budget recommendation", "Q-learning agent", "Not implemented: budgets are set by the user; alerts at 75, 90 and 100 percent; rule-based trimming advice"],
             ["Savings forecasting", "LSTM on a synthetic series", "Least-squares line over monthly expense totals (expenses, not savings); refuses with fewer than 3 months"],
             ["Anomaly detection", "Isolation Forest, contamination 0.015", "Not implemented; only the largest expense in a window is shown"],
             ["User interface", "Streamlit", "React + FastAPI web application (the original Streamlit app is kept)"],
             ["Financial health", "Not present", "Six-component weighted score with explanation"]],
            widths=[1.5, 2.2, 2.9], align=["l", "l", "l"], size=10),
    ]


def contribution_blocks():
    v = _v()
    return [
        P("The contributions of the project, stated as what was built and what was measured, are the following."),
        N(f"A full-stack personal finance web platform: a React and TypeScript front end with {F.N_PAGES} pages, a FastAPI back end with {F.N_ROUTES} routes, a service layer shared with the original Streamlit application and a six-table SQLite database, with per-user data scoping and bcrypt-hashed passwords.",
          f"An expense categoriser (TF-IDF word 1-2-grams and logistic regression) with a keyword fallback and retraining on user corrections, evaluated on a 198-description probe set in three difficulty tiers: {v['tA'] * 100:.0f} percent on seed-like text, {v['tB'] * 100:.0f} percent on statement strings and {v['tC'] * 100:.1f} percent on unseen merchants.",
          f"A spending forecast with per-category trends and a budget-overrun check, together with a backtest and a synthetic simulation showing that the linear trend is no better than a plain average until about seven months of history exist.",
          f"An explainable 0-100 financial health score of six weighted components, checked by sensitivity sweeps and 5,000 random profiles (mean {v['hl_mean']:.1f}, range {v['hl_min']:.1f} to {v['hl_max']:.1f}, no decrease when the savings rate rises).",
          f"An assistant that answers from the user's own data ({v['a_ok']} of {v['a_n']} answerable test questions handled, all {v['a_off']} off-topic questions declined), automatic budget alerts, goals, a manual investment portfolio, and PDF, Excel and CSV reports.",
          f"A CSV and Excel import pipeline with row-level validation: in a 1,000-row test with {v['imp_bad']} injected bad rows, all {v['imp_bad']} were skipped and {v['imp_ok']} were imported and auto-categorised.",
          f"A test and measurement harness: {v['tests']} pytest tests, a {v['smoke']}-check end-to-end smoke test, API latency measurements for every endpoint and a reproducible experiment script that writes `experiments/metrics.json`.",
          "An honest account of what the system cannot do: unseen merchants are mislabelled (mostly as Transport), there is no anomaly detection, no reinforcement-learning budgeting and no time-series model beyond a line."),
    ]


# ---------------------------------------------------------------------------- scope / limits
def scope_blocks():
    return [
        H2("In scope"),
        P("The project covers the personal finance tasks of one person who records or imports their own transactions. The following were designed, built and tested."),
        B("**Accounts and security.** Sign-up and log-in with username or e-mail, password rules (eight characters or more with upper case, lower case, digit and special character), bcrypt hashing, signed bearer tokens with a seven-day expiry and per-user data scoping on every table.",
          "**Transactions.** Add, edit, delete, search, filter and sort; custom categories; payment method and notes; CSV or Excel import with a preview and row-level warnings.",
          "**Machine learning.** Automatic category labelling with learning from corrections; a next-month expense forecast, per-category forecasts and a budget-overrun check; a six-component health score.",
          "**Planning.** Monthly category budgets with alerts at 75, 90 and 100 percent; savings goals with progress and required monthly saving; a manual investment portfolio with six asset types and an optional live price refresh.",
          "**Assistant and reports.** A rule-routed assistant over the user's data with an optional language-model layer; rule-based insights; PDF, Excel and CSV reports; in-app notifications.",
          "**Interface.** A landing page, sign-up and log-in, and ten application pages (dashboard, transactions, analytics, budgets, goals, investments, assistant, reports, notifications, profile) in dark and light themes."),
        H2("Out of scope"),
        B("Anomaly detection, a reinforcement-learning budget recommender and deep models (BERT, LSTM), which the base paper uses and which were not built.",
          "Loan and debt tracking, amortisation and prepayment planning, named in the abstract.",
          "Scheduled jobs such as periodic digest e-mails; alerts are raised when the dashboard or notification list is read, not on a timer.",
          "Bank-API, SMS or account-aggregator integration; multiple linked accounts; multi-currency conversion.",
          "Native mobile applications, multi-user households, tax filing and any regulated financial advice."),
    ]


def assumption_blocks():
    return [
        P("The results and the design rest on the following assumptions."),
        B("Each person uses one account and records amounts in a single currency (Indian rupees by default).",
          "Transaction descriptions are short English phrases with Indian merchant or payment-network wording, like the seed list.",
          "The user enters or imports income and expense records honestly and reasonably completely; the health score and forecast are only as good as the records.",
          "Monthly totals are a useful unit for the forecast, and at least three months of history exist before a forecast is requested.",
          "The application runs on one machine with a local SQLite file and a trusted local network; the default token secret is replaced through the environment before any shared use.",
          "All demonstration data are fictional: the demo account and the 34-row sample file contain no real personal data."),
    ]


def limitation_blocks():
    v = _v()
    return [
        P("The limitations below were found by measuring the system or by reading the code, and each is stated with the evidence."),
        B(f"**Unseen merchants are silently mislabelled.** On the 66 tier-C descriptions the categoriser scores {v['tC'] * 100:.1f} percent. {v['terr']} of its {v['nerr']} errors are predicted as Transport, because text with no known word gives a zero feature vector and the decision then comes from the intercepts. The app applies no confidence threshold and the model never answers Other.",
          f"**The seed list is tiny.** Fifty-one descriptions (three to six per class) are the whole training set; leave-one-out accuracy on them is {v['loo'] * 100:.1f} percent. The 100 percent score on the bundled 34-row sample is optimistic because its wording overlaps the seed list.",
          f"**Corrections help repeat merchants only.** One correction lifts the same merchant, narrated three other ways, from {v['rep_b'] * 100:.1f} to {v['rep_a'] * 100:.0f} percent, but forty-eight corrections of other merchants raise tier-C accuracy only from {v['k0'] * 100:.1f} to {v['k48'] * 100:.1f} percent.",
          f"**The probe set is not an independent benchmark.** The team wrote the 198 descriptions before scoring and never trained on them, but the same people wrote the seed list.",
          f"**The forecast is a straight line.** On the demo account's three backtest points it has a MAPE of {v['mape_lin']:.1f} percent against {v['mape_mean']:.1f} percent for the mean of all months, and in simulation it only beats a plain average from about seven months of history. The three-month minimum is too low for this method.",
          "**Health-score weights are chosen, not fitted.** Savings rate and expense ratio together carry half of the score and are strongly correlated; no user study checked that the score matches how people judge their finances.",
          f"**The assistant is a rule router.** It handled {v['a_ok']} of {v['a_n']} answerable test questions; questions about groceries, the biggest expense or running out of money fell to the fixed help text. \"Am I overspending on shopping?\" is answered with the Shopping total, not a budget comparison.",
          f"**Import is slow per row.** Each row is committed in its own database session, giving {v['imp_rate']:.1f} rows per second.",
          "**Alerts and dates.** Budget alerts are de-duplicated by message text only, so a budget that crosses the same threshold in a later month raises no new alert; the month end is written as the 31st, which works for SQLite date strings but not for strict databases.",
          "**Weak token design.** Bearer tokens are home-made HMAC-SHA256 values without refresh or revocation, the default secret `finjarvis-dev-secret` is used if `APP_SECRET_KEY` is not set, and CORS allows only localhost:5411.",
          "**Single-user storage.** One SQLite file, no migrations, no backups; `passlib` needs `bcrypt==4.0.1` because bcrypt 5 breaks hashing."),
        *_fig("f01_classifier_tiers.png", "Accuracy of the shipped categoriser, the keyword table and the majority class on the three probe tiers.", 5.6),
        *_fig("f08_sim_mape_history.png", "Simulated one-step-ahead error against months of history: the linear trend overtakes a plain average only after several months.", 5.2),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, and no number for them appears in any document of this submission."),
        B("The optional language-model layer (`AI_API_KEY`): no measurement ran with a key, so its answers, cost and failure behaviour are unknown.",
          "The live price refresh through `yfinance`, which needs internet access.",
          "Concurrency and load: all latency figures are single-user, single-process, warm-server values on 127.0.0.1.",
          "Mobile browsers, accessibility and cross-browser behaviour; screens were captured with Playwright in Chromium and inspected by eye, with no automated UI tests.",
          "Security testing beyond the 49-check smoke test: no penetration test or dependency audit.",
          "Real personal data: every figure comes from fictional demo data, the team's probe set or seeded simulation.",
          "Any comparison with a commercial finance application, and any user study of whether the advice changes behaviour.",
          "Anomaly detection, reinforcement-learning budgeting and savings forecasting, which were not built, so no accuracy exists to report."),
    ]


# ---------------------------------------------------------------------------- code walk-throughs and decisions
def walkthrough_blocks():
    v = _v()
    return [
        H2("Categorisation and learning from corrections (`ml/expense_classifier.py`)"),
        P(f"The categoriser is a scikit-learn pipeline of a TF-IDF vectoriser over word one- and two-grams and a logistic regression. It is trained from the 51 seed pairs, pickled to `ml/expense_model.pkl` and re-created if the file is missing. Prediction takes {v['pred_ms']:.2f} ms and retraining on the seed takes {v['retrain_ms']:.1f} ms. "
          "If the model cannot be loaded the function falls back to a keyword table and finally to Other; the model itself never returns Other."),
        CODE(fn("ml/expense_classifier.py", "_train_pipeline") + "\n\n" + fn("ml/expense_classifier.py", "predict_category"), 8),
        P("The route that adds a transaction treats a manual category that differs from the prediction as a correction. It retrains on the seed, the user's whole history and the new pair; failures are swallowed so that adding the transaction never fails."),
        CODE(between("backend/main.py", "chosen = (body.category or \"\").strip()", "pass  # learning is best-effort"), 7.5),
        CODE(fn("ml/expense_classifier.py", "learn_from_correction"), 8),
        H2("Next-month forecast (`ml/spending_prediction.py`)"),
        P("Expenses are summed per calendar month and a degree-one least-squares polynomial is fitted over the month index. The next value is the line evaluated one step ahead and clipped at zero. The label is increasing if the slope exceeds 1, decreasing below -1 and stable otherwise, and the recent average is the mean of the last three months. "
          f"With fewer than three months the function declines. For the demo account it gives INR {v['next_pred']:,.0f} for November against a recent average of INR {v['recent3']:,.0f}."),
        CODE(fn("ml/spending_prediction.py", "predict_next_month_expense"), 8),
        H2("Financial health score (`ml/financial_health.py`)"),
        P("Each component is mapped to 0-100 and clipped. The savings rate gets full marks at 20 percent; the expense ratio at half of income or less; emergency cover at six months of expenses; diversification at five asset types. Missing budgets, goals or expenses give a neutral 50. "
          f"The weighted sum selects one of five bands and the lowest component becomes the explanation. The demo account scores {v['demo_score']:.1f}."),
        CODE(fn("ml/financial_health.py", "score_savings_rate") + "\n\n" + fn("ml/financial_health.py", "score_expense_ratio") + "\n\n" + fn("ml/financial_health.py", "score_emergency_fund"), 8),
        CODE(between("ml/financial_health.py", "total = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)", "weakest = min(components, key=components.get)"), 8),
        H2("Budget alerts (`services/budget_service.py`)"),
        P("After a budget or an expense changes, the function compares each category's spend with its budget and writes one notification per threshold crossing. It skips a message that already exists, which prevents duplicates but also suppresses the same alert in a later month."),
        CODE(fn("services/budget_service.py", "check_and_raise_alerts"), 7.5),
        H2("Signed tokens (`backend/main.py`)"),
        P("A token is a base64url JSON payload with the user id and an expiry, followed by an HMAC-SHA256 signature over that payload. Verification recomputes the signature, compares in constant time and checks the expiry. A tampered token was rejected in the smoke test."),
        CODE(fn("backend/main.py", "make_token") + "\n\n" + fn("backend/main.py", "read_token"), 8),
        H2("Assistant routing (`services/ai_service.py`)"),
        P("The question passes through five deterministic handlers in a fixed order. The first that matches answers from the user's data and the answer is tagged analytics; otherwise the optional language-model layer is tried, and finally a fixed help text is returned."),
        CODE(between("services/ai_service.py", "for handler in (", "return {\"answer\": result, \"disclaimer\": DISCLAIMER, \"source\": \"analytics\"}"), 8),
    ]


def decision_blocks():
    v = _v()
    return [
        P("The main implementation decisions, the reason for each and what the measurements later showed are listed in the table below."),
        TAB("Implementation decisions and their reasons", ["Decision", "Reason", "What the measurements showed"],
            [["SQLite file with SQLAlchemy", "No server to install; the same models run the Streamlit and web front ends", f"Dashboard {v['l_dash']:.0f} ms and transactions list {v['l_tx']:.0f} ms median; no concurrency test, no migrations"],
             ["FastAPI layer over unchanged services", "The business logic stays in one place and both front ends call it", f"33 routes with no logic of their own; {v['smoke']} of {v['smoke']} smoke checks passed"],
             ["TF-IDF + logistic regression, not BERT", "Runs on a CPU in milliseconds with no download; every weight is inspectable", f"{v['acc'] * 100:.1f} percent on the probe set, {v['tC'] * 100:.1f} percent on unseen merchants; {v['pred_ms']:.2f} ms per prediction"],
             ["Keyword table as fallback", "The app keeps working if the pickle cannot be loaded", f"Alone it scores {v['kw'] * 100:.1f} percent, so it is a safety net, not a second model"],
             ["Retrain on every correction", "Cheap enough to do inline and gives visible adaptation", f"Retrain {v['retrain_ms']:.1f} ms on the seed; repeat merchants {v['rep_a'] * 100:.0f} percent, new merchants barely move"],
             ["Least-squares line for the forecast", "Needs only three months and is easy to explain", f"MAPE {v['mape_lin']:.1f} percent on the backtest against {v['mape_mean']:.1f} percent for the mean; better only after about seven months in simulation"],
             ["Weighted health score with fixed weights", "Transparent and explainable with a named weakest area", f"Mean {v['hl_mean']:.1f} over {v['hl_n']:,} random profiles; no fitted validation"],
             ["Rule-routed assistant before any LLM", "Answers are computed from the user's data and cannot invent figures", f"{v['a_ok']} of {v['a_n']} answerable questions handled; the LLM layer was not tested"],
             ["bcrypt through passlib, pinned to 4.0.1", "Slow salted hashing; bcrypt 5 breaks passlib", f"Login costs {v['l_login']:.0f} ms by design"],
             ["Home-made HMAC token with seven-day expiry", "No extra dependency; stateless", "No refresh or revocation; default secret if the environment variable is unset"],
             ["Import commits row by row", "Simple code and per-row warnings", f"{v['imp_rate']:.1f} rows per second; preview of 100 rows {v['l_prev']:.0f} ms"],
             ["Reports generated on request", "No stored files", f"CSV {F.lat('GET /reports/csv'):.0f} ms, PDF {v['l_pdf']:.0f} ms, Excel {v['l_xls']:.0f} ms median"]],
            widths=[1.6, 2.4, 2.6], align=["l", "l", "l"], size=10),
        P("Three decisions deserve a longer note. The first is the choice of a small categoriser. A fine-tuned BERT model would almost certainly do better on unseen text, but it needs labelled data the team did not have, a download of several hundred megabytes and far more time per prediction. "
          "The measurement shows the price of the small model: it is accurate on wording it has seen and poor on wording it has not, and it fails silently. A confidence threshold would be the cheapest repair."),
        P("The second is to keep the service layer unchanged and wrap it in FastAPI. The original Streamlit application stays usable and every number on the web screens is computed by the same function the Streamlit pages used. "
          "The cost is that the services open a database session per call, which is simple but is why import is slow."),
        P("The third is the assistant design. Answering from handlers that query the user's data means a stated amount always matches the database, which was checked for the Food total and the top category. The price is limited coverage, "
          "and the fallback text is the honest response to a question the router does not recognise."),
    ]


# ---------------------------------------------------------------------------- conclusion
def _objective_table():
    v = _v()
    return TAB("Objectives against outcomes", ["Objective", "Outcome", "Evidence"],
               [["1 Secure accounts with transaction import and manual entry", "Achieved", f"bcrypt, signed tokens, per-user scoping; manual entry and CSV/Excel import ({v['imp_ok']} of {v['imp_n']:,} rows imported, {v['imp_bad']} bad rows skipped); {v['smoke']} of {v['smoke']} smoke checks"],
                ["2 Categorise expenses automatically from descriptions", "Partly achieved", f"{v['acc'] * 100:.1f} percent on the probe set but {v['tC'] * 100:.1f} percent on unseen merchants; 51 seed examples; 11 categories"],
                ["3 Forecast expenses and savings with time-series models", "Partly achieved", f"Linear trend on monthly expenses only; no ARIMA or LSTM; MAPE {v['mape_lin']:.1f} percent on the backtest, not better than a mean"],
                ["4 Detect anomalous transactions", "Not achieved", "No anomaly detector exists; only the largest expense in a window is shown"],
                ["5 Personalised budget recommendations and threshold alerts", "Partly achieved", "Alerts at 75, 90 and 100 percent and rule-based advice from the user's data; budgets are set by the user, no learned recommender"],
                ["6 Interactive dashboard of spending, categories and forecasts", "Achieved", f"13 pages in dark and light themes; dashboard {v['l_dash']:.0f} ms and analytics {v['l_ana']:.0f} ms median"]],
               widths=[2.4, 1.3, 2.9], align=["l", "l", "l"], size=10)


def _findings():
    v = _v()
    cross = _sim_crossover()
    return [
        f"The categoriser is accurate where its vocabulary overlaps the seed list ({v['tA'] * 100:.0f} percent on seed-like text, {v['tB'] * 100:.0f} percent on statement strings) and weak elsewhere ({v['tC'] * 100:.1f} percent on unseen merchants), against {v['kw'] * 100:.1f} percent for the keyword table over the whole probe set.",
        f"Its mistakes are not random: {v['terr']} of {v['nerr']} errors are labelled Transport (precision {v['tprec']:.3f}), because the model has no way to say it does not know.",
        f"A confidence threshold of 0.15 would keep {v['cov15'] * 100:.1f} percent of the probe items at {v['acc15'] * 100:.1f} percent accuracy, so abstaining is a practical improvement the app does not yet make.",
        f"One correction fixes a repeat merchant ({v['rep_b'] * 100:.1f} to {v['rep_a'] * 100:.0f} percent) but forty-eight corrections move unseen-merchant accuracy only to {v['k48'] * 100:.1f} percent.",
        f"The linear-trend forecast is not better than a plain average for short histories: MAPE {v['mape_lin']:.1f} against {v['mape_mean']:.1f} percent on the demo backtest, and in simulation it overtakes the mean of all months at {cross} months of history and the mean of the last three months only at {_sim_crossover('mean_of_last_3')} months, so the three-month minimum is too low.",
        f"The health score behaves sensibly (no decrease when the savings rate rises in {v['hl_n']:,} random profiles) but saturates: the savings-rate component stops changing at 20 percent, and its weights are not fitted.",
        f"The rule-based assistant is correct when it answers and silent about much of what users might ask: {v['a_ok']} of {v['a_n']} answerable questions handled, {v['a_off']} of {v['a_offn']} off-topic questions declined.",
        f"The application is fast for one user: every dashboard, list and analytics endpoint answers in under {max(v['l_dash'], v['l_ana']) + 10:.0f} ms median, reports in {v['l_pdf']:.0f} to {v['l_xls']:.0f} ms, with login ({v['l_login']:.0f} ms) the slowest by design.",
    ]


def conclusion_blocks():
    v = _v()
    return [
        H2("Summary"),
        P(f"FINJARVIS is a working AI-based personal finance manager. A person signs up, records or imports transactions, and sees a dashboard with income, expenses, savings, net worth, a categorised spending breakdown, a next-month forecast, budget alerts and a 0-100 financial health score. "
          f"An assistant answers questions from the person's own records, and reports can be downloaded as PDF, Excel or CSV. It is built from a React front end, a FastAPI back end with {F.N_ROUTES} routes, a service layer shared with the original Streamlit application and a SQLite database."),
        P(f"The work was verified by {v['tests']} pytest tests and a {v['smoke']}-check smoke test, and its machine-learning parts were measured on a probe set, a backtest, simulation and random profiles. The honest result is mixed: the platform and the explainable modules work, "
          "the categoriser and the forecast are simple and break in the ways reported, and the base paper's anomaly detector, budget recommender and deep models were not built."),
        H2("Objectives against outcomes"),
        _objective_table(),
        H2("Key findings"),
        N(*_findings()),
        *_fig("f02_confusion_matrix.png", "Confusion matrix of the shipped categoriser on the probe set: the Transport column collects the unseen-merchant errors.", 5.0),
        *_fig("f05_learning_from_corrections.png", "Learning from corrections: new merchants gain little, a repeat merchant is fixed by one correction.", 6.0),
        *_fig("f06_forecast_backtest.png", "Forecasts for months 4-6 of the demo account with four methods; the actual spend fell in the last month.", 5.4),
        H2("Limitations"),
        P("The evidence is a team-written probe set, fictional demo data and seeded simulation rather than field data, there was no user study, and the defects listed in the limitations section remain open. The results demonstrate a working, inspectable platform, not that its models are accurate on real transactions."),
    ]


def chapter9_blocks():
    v = _v()
    body = [
        H2("Summary"),
        P("The project set out to build a personal finance platform that records spending, categorises it, forecasts what is coming and gives advice grounded in the user's own data. FINJARVIS delivers the platform: a React and FastAPI web application over a SQLite database, "
          f"with secure accounts, transaction entry and import, budgets, goals, investments, an assistant, reports and notifications. Its machine-learning parts are a TF-IDF and logistic-regression categoriser, a least-squares spending forecast and a six-component health score."),
        P(f"The work was verified by {v['tests']} pytest tests, a {v['smoke']}-check end-to-end smoke test, a 198-description probe set, a rolling backtest, a synthetic forecasting simulation, 5,000 random health profiles, a 26-question assistant test, a 1,000-row import test and API latency measurements. "
          "The measurements are reported as they came out, including those that contradict the first draft of the design."),
        H2("Objectives achieved"),
        _objective_table(),
        H2("Key findings"),
        N(*_findings()),
        H2("Module-by-module conclusions"),
        P(f"**Accounts and data handling.** Every query is scoped by user, weak passwords, wrong passwords and tampered tokens are rejected, every import row is validated, and a keyword fallback keeps categorisation working if the model file is unreadable; the {v['smoke']} smoke checks and {v['tests']} unit tests cover these paths."),
        P(f"**Categorisation.** The model is a good lookup table for descriptions that resemble its seed list and a poor guesser for anything else. Its overall probe accuracy of {v['acc'] * 100:.1f} percent hides a split of {v['tA'] * 100:.0f}, {v['tB'] * 100:.0f} and {v['tC'] * 100:.1f} percent across the three tiers, which is why the tier breakdown, the confusion matrix and the Transport dump class are reported with it. "
          "Learning from corrections is worth keeping, because a merchant tagged once stays tagged, but it is no substitute for a larger training set."),
        P(f"**Forecasting.** The straight line follows a steady rise and over-shoots a sudden fall, as in the demo account's last month; with little history a mean is as good or better. It is useful as a prompt to look at a category, but should be presented with its limits."),
        P(f"**Health score and assistant.** The score gives one number and one reason, and the assistant repeats those figures in words; neither adds information that is not in the data, a strength for trust and a limit for insight."),
        H2("Practical applications"),
        B("A student or salaried person can keep all transactions in one place, import a bank statement as CSV, and see where the money goes without a subscription fee.",
          "Budget alerts and the health score show whether spending is on track and which area is weakest, with the reason.",
          "The assistant answers common questions (spend on a category, can I save a given amount, where can I cut) from the user's data and says plainly when it cannot answer.",
          "A teaching team can reuse the code and experiment script as an honest example of measuring simple models before trusting them."),
        H2("Closing remark"),
        P("The value of the project lies in a platform that works end to end and a measured account of how its simple models behave. The experiments do not show that TF-IDF and a line can replace the base paper's BERT, LSTM and Isolation Forest; "
          "they show where the simple versions fail and the first improvements: an abstain threshold and a mean fallback for short histories."),
        H2("Known limitations"),
        P(f"The categoriser fails silently on unseen merchants ({v['tC'] * 100:.1f} percent), the forecast is not better than a mean on short histories, the assistant answered {v['a_ok']} of {v['a_n']} answerable questions, the health weights are not fitted, and tokens use a home-made scheme with a default secret. "
          "The data are fictional or simulated, no user study was carried out, and the language-model layer, live prices and concurrency were not tested."),
    ]
    return [H1("CHAPTER 9: CONCLUSION")] + renum(body, "9")


# ---------------------------------------------------------------------------- future scope
def future_blocks():
    return [
        H2("Close the defects found"),
        B("**Let the categoriser abstain.** Return Other or ask the user when the top probability is below 0.15, which on the probe set keeps about 62 percent of items at about 94 percent accuracy; show the confidence next to the label.",
          "**Fall back to a mean for short histories.** Use the mean of the last three months until about seven months exist, and raise the minimum above three months.",
          "**Fix alert de-duplication and month ends** so that a budget crossing the same threshold in a later month raises a new alert, and compute month ends with the calendar.",
          "**Replace the token scheme** with a standard library, require `APP_SECRET_KEY` and refuse to start with the default, and add a login rate limit.",
          "**Batch the import commit** into one transaction so that a 1,000-row file takes seconds instead of tens of seconds."),
        H2("Complete the objectives that were missed"),
        B("**Anomaly detection.** Start with a robust z-score per category, then an Isolation Forest on amount, category and day features, and measure precision and recall on injected outliers as the base paper does.",
          "**Savings forecasting.** Forecast income minus expenses, and compare a seasonal mean, exponential smoothing and ARIMA with the current line using a rolling-origin backtest.",
          "**A learned budget recommender.** Begin with a rule that proposes budgets from the last three months, and consider reinforcement learning only if real histories justify it."),
        H2("Add features"),
        B("A **loan and debt tracker** with amortisation schedules and prepayment comparison, as named in the abstract.",
          "A **scheduler** for weekly or monthly digests and recurring-transaction detection.",
          "**Bank and SMS import** through statement parsers or an account-aggregator API, and merchant-name normalisation.",
          "A **larger labelled corpus** from consenting users and public sets, then a comparison of the current model with a linear model on character n-grams and a small transformer.",
          "**Testing the language-model layer** with a key, including answer faithfulness against the database."),
        H2("Deploy and scale"),
        B("Move to PostgreSQL with Alembic migrations, run several workers behind a reverse proxy and keep secrets in the environment.",
          "Add load tests, automated browser tests and a dependency audit to the test suite, and monitor latency and error rates."),
    ]


def chapter10_blocks():
    body = [
        H2("Improvements to the existing system"),
        B("**Abstain instead of guessing.** A threshold of 0.15 on the top class probability is the cheapest repair for the silent Transport errors; it should be judged by coverage and accuracy on a larger probe set that includes unseen merchants.",
          "**Grow the seed list.** Fifty-one examples, three to six per class, give a leave-one-out accuracy of 11.8 percent; several hundred labelled descriptions per class from consenting users would change the picture and allow a proper train and test split.",
          "**Make the forecast honest for short histories.** Use the mean of the recent months below about seven months, and report an interval rather than a single number.",
          "**Strengthen authentication.** Standard signed tokens with refresh and revocation, an enforced secret and rate-limited login.",
          "**Alert logic.** Key alert de-duplication by budget, month and threshold, not by message text."),
        H2("Additional features"),
        B("**Anomaly detection** for objective 4: a robust statistical rule first, then an Isolation Forest, evaluated against injected and labelled outliers.",
          "**Savings and income forecasting** with exponential smoothing or ARIMA, compared by rolling-origin backtest, for objective 3.",
          "**Loan tracking** with amortisation and prepayment advice, and **scheduled digests** for the abstract's loan tracking and task scheduling.",
          "**Statement parsers** for common Indian bank formats and UPI exports, so that import needs no preparation."),
        H2("Scalability and deployment"),
        P(f"FINJARVIS runs as one process with one SQLite file, which suits a single person or a demonstration; no load test was run. A shared deployment needs a server database with migrations, several workers behind a reverse proxy, HTTPS and a secret kept outside the code."),
        B("Replace the per-call database sessions with a connection pool and batch writes.",
          "Serve the built React bundle from a static host and keep the API behind HTTPS.",
          "Add monitoring of error rates and latency per endpoint, and nightly database backups."),
        H2("Evaluation plan for the next version"),
        B("**A held-out merchant split.** Divide the labelled descriptions by merchant, not by row, so that the test set contains only merchants the model has never seen; report accuracy and macro F1 for that split and for a random split.",
          "**Selective accuracy.** Report coverage and accuracy at several confidence thresholds.",
          "**Rolling-origin forecasting.** Evaluate every method on many months of many users, not three points of one account, with MAE, MAPE and a naive baseline.",
          "**Injected-anomaly benchmark.** Generate outliers of known size in real histories and measure precision, recall and the number of false alarms per user per month.",
          "**A small user study.** Ask a few users to categorise a week of their own transactions with and without the assistant and the score, and record time taken and corrections made."),
        H2("Order of work"),
        P("First the cheap repairs (abstain threshold, short-history fallback, alert de-duplication, token secret, batched import), each re-measured with the existing scripts. "
          "Then the missing models, anomaly detection and a savings forecast. Last loan tracking, scheduling and statement parsers, which need more design and real sample files."),
        H2("Risks and dependencies"),
        B("**Data and privacy.** A larger corpus and statement parsing mean handling real financial data; consent, minimisation and secure storage must come first.",
          "**Evaluation.** A bigger model that scores better on the team's probe set may only have learned its wording; any new model should be tested on merchants and months it has not seen.",
          "**Advice.** The assistant and health score are informational and must keep their disclaimer; a language-model layer needs checks that figures in its answers match the database."),
        H2("Further research"),
        B("How much labelled data does a TF-IDF model need before unseen-merchant accuracy becomes useful, and does a character n-gram or transformer model close the gap at a similar cost?",
          f"How should a forecast combine a trend with seasonal effects such as festivals and rent resets when only a few months exist? The base paper's LSTM result (R2 0.63 on synthetic savings, {C('base')}) does not answer this for real users."),
    ]
    return [H1("CHAPTER 10: FUTURE SCOPE")] + renum(body, "10")
