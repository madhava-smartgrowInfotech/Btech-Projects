"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, EQ, H1, H2, N, P, TAB
from .refs import N as C


def trim(blocks, drop=(), drop_sections=(), replace=None, table_rows=None):
    """Report-mode trimming helper (shared by the other chapter modules). drop: block-text prefixes to remove; drop_sections: heading
    prefixes whose whole section is removed; replace: {prefix: block}; table_rows: {caption prefix: keep(row)}."""
    replace = replace or {}
    table_rows = table_rows or {}
    out, skip_level = [], None
    for b in blocks:
        if b[0] in ("h1", "h2", "h3"):
            lvl = int(b[0][1])
            if skip_level is not None and lvl <= skip_level:
                skip_level = None
            if skip_level is None and any(b[1].startswith(x) for x in drop_sections):
                skip_level = lvl
        if skip_level is not None:
            continue
        v = b[1]
        k = v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else "")
        if any(k.startswith(x) for x in drop):
            continue
        hit = next((x for x in replace if k.startswith(x)), None)
        if hit:
            if replace[hit] is not None:
                out.append(replace[hit])
            continue
        if b[0] == "tab":
            cap = next((x for x in table_rows if b[1].startswith(x)), None)
            if cap:
                b = ("tab", b[1], b[2], [r for r in b[3] if table_rows[cap](r)], b[4], b[5], b[6])
        out.append(b)
    return out


def blocks():
    c = F.CLS
    bt = F.FC["demo_backtest"]
    out = [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Introduction to the Project Domain"),
        P("Almost everyone who earns money in a city today also leaves a trail of small digital transactions: a UPI payment for a meal, a card debit for a bus pass, a standing order for rent, a mutual-fund instalment. "
          "The batch introduction records the consequence: individuals now hold several accounts, income sources, recurring bills and investments at once, and manual expense tracking is tedious enough that most users abandon it within weeks. "
          f"Financial literacy research links the ability to plan, save and respond to unexpected expenses with long-term well-being {C('lusardi')}, and a recent user-centred study of a finance app for young adults begins from the same worry, "
          f"that people lack the skills and the habit to manage money {C('to')}. Software that records spending without effort and turns the record into a forecast and a warning is the subject of this project."),
        P("Four ideas from machine learning meet in a personal finance manager: **text classification** of a description such as \"Swiggy order\", **time-series forecasting** of next month's spending, "
          "**anomaly detection** of transactions that do not fit a person's pattern, and **recommendation** of advice that fits the person's income. "
          f"The registered base paper combines all four in one assistant {C('base')}. This project builds the first two, a rule-based form of the fourth, and a scoring model the base paper does not have; it does not build the third (Section 1.5)."),
        P("Terms used in this report: a **transaction** is one dated income or expense with a description, amount, category and payment method; a **category** is one of eleven expense labels (Food, Transport, Entertainment, Bills, Shopping, Education, Healthcare, Rent, Travel, Investments, Salary) or \"Other\"; "
          "a **budget** is a monthly limit for one category; a **goal** is a savings target with a deadline; a **holding** is one investment entered by the user; "
          "the **health score** is a 0-100 number from six weighted components; the **assistant** answers questions from the user's records."),
        H2("1.2 Background and Motivation"),
        P(f"The batch registers a 2025 paper in the International Journal for Research in Applied Science and Engineering Technology as the base paper: \"A Smart AI-Based Personal Finance Assistant: A Multi-Model Approach for Expense Categorization, Budgeting, Forecasting and Anomaly Detection\" {C('base')}. "
          "Its authors argue that existing tools depend on manual categorisation and static budgeting rules and propose four models in one pipeline: a fine-tuned BERT classifier that sorts transactions into 50 categories (extended from 16, with SMOTE oversampling), "
          "a Q-learning agent that recommends a budget level, an LSTM that forecasts savings from twelve months of history, and an Isolation Forest that flags unusual transactions. "
          "It reports an accuracy of 92.3 % (precision 90.8 %, recall 91.5 %, F1 91.1 %) for the classifier, an RMSE of 137.2, MAE of 89.5 and R-squared of 0.63 for the forecaster, and precision 0.93, recall 0.94 and F1 0.94 for the anomaly detector, "
          "on data the paper describes as synthetic or collected and labelled by the authors; the data are not released."),
        P(f"The paper is a research prototype with a Streamlit interface; the batch's gap statement is to deliver the multi-model idea as an affordable, customisable web platform. "
          f"Similar recent work includes an explainable XGBoost and LSTM hybrid {C('finsense')}, an Isolation Forest and K-Means leakage detector {C('leak')} and a data-generation framework for finance language models {C('theerthala')} (Chapter 2)."),
        P(f"{F.PRODUCT} is a working application, not a notebook: a person signs up, adds transactions by hand or imports a CSV or Excel file, "
          "sees each category filled in by a trained model, watches budgets and goals, reads a forecast and a health score, asks questions in plain language and downloads reports. "
          "For the user it is a free, inspectable alternative to commercial finance apps; for the project it is a chance to build simple versions of the base paper's modules and measure honestly where they work and where they do not."),
        H2("1.3 Problem Statement"),
        P("The batch problem statement lists four difficulties. Manual expense recording is tedious and is quickly abandoned. Existing applications report past spending but do not forecast what is coming. "
          "Generic budgeting advice ignores individual income patterns and commitments. Unusual transactions go unnoticed until the statement is reviewed much later. "
          "The stated need is a platform that categorises spending automatically, forecasts future expenditure and gives advice grounded in the user's own data."),
        P("We restate the problem so that it can be tested. **Build a personal finance platform in which each new transaction is categorised by a trained model, the next month's spending is forecast from the recorded months, "
          "budget thresholds raise alerts, a single explainable score summarises financial health, and questions are answered from the user's own records; then measure how each part behaves, including where it fails.** "
          "The two quantitative parts can be written down. If the recorded monthly expense totals are y1 ... yn (n at least 3), the forecast for the next month is the value at x = n of the least-squares line through the points (i, yi), clipped at zero. "
          "The health score is the weighted sum of six component scores s1 ... s6, each clipped to the range 0 to 100:"),
        EQ("forecast = max(0, a*n + b),  where (a, b) minimise the sum of (yi - a*i - b)^2        score = 0.30*s1 + 0.20*s2 + 0.15*s3 + 0.15*s4 + 0.10*s5 + 0.10*s6"),
        P("Neither formula needs a large dataset: the project asks how far such simple, inspectable models go. "
          f"The measurements show that the categoriser is right for {c['tfidf_lr']['accuracy_by_tier']['A'] * 100:.0f} % of descriptions that resemble its training phrases but for only {c['tfidf_lr']['accuracy_by_tier']['C'] * 100:.1f} % of unseen merchants, "
          "and that the linear trend is not better than a plain average until about seven months of history exist (Chapter 8)."),
        H2("1.4 Need for the Proposed System"),
        B("**Effortless record keeping.** A model suggests the category when a description is typed and learns from a correction.",
          "**Looking forward, not only back.** A next-month and per-category forecast, checked against budgets, lets a user act before a limit is crossed.",
          "**Advice from the person's own numbers.** The health score names the weakest of six areas, and the assistant answers from the user's recorded data instead of giving general tips.",
          "**Alerts at thresholds.** Budget alerts at 75 %, 90 % and 100 % of a limit are written to a notification list while the month is still running.",
          "**Affordable and open.** Python, FastAPI, SQLite and React are free; the data stays in one local file; nothing is sent to a cloud service unless the user adds an optional language-model key.",
          "**Evidence, not assertion.** The platform carries its own tests, a probe set and measured response times, so a reader can check what works."),
        H2("1.5 Project Objectives"),
        P("The six objectives set for the batch, and the outcome of each, are listed below. The outcome column is the short version; Chapter 8 gives the measurements and Chapter 9 the verdict. "
          "Two objectives were not met, and the table says so plainly."),
        TAB("Objectives of the project and their outcome", ["No.", "Objective", "Outcome (summary)"],
            [["1", "Build secure user accounts with transaction import and manual entry",
              f"Achieved: sign-up and login with bcrypt-hashed passwords and signed bearer tokens, per-user data scoping, manual entry and CSV or Excel import with preview; {F.PYTEST_PASSED} unit tests and {F.SMOKE_PASSED} smoke checks pass."],
             ["2", "Categorise expenses automatically from descriptions using text classification",
              f"Achieved in a small form: TF-IDF with logistic regression on a 51-example seed list; {c['tfidf_lr']['accuracy'] * 100:.1f} % accuracy on a 198-description probe set but {c['tfidf_lr']['accuracy_by_tier']['C'] * 100:.1f} % on unseen merchants."],
             ["3", "Forecast upcoming expenses and savings using time-series models",
              f"Partly achieved: a linear trend forecasts next month's expenses (INR {bt['app_prediction_for_next_month']['predicted_next_month_expense']:,.0f} for the demo account); no ARIMA, LSTM or direct savings forecast; backtest MAPE {bt['mape_pct']['linear_trend (app)']:.1f} % on three points."],
             ["4", "Detect anomalous transactions that deviate from an established pattern",
              "Not achieved: no anomaly detector exists in the product. The nearest feature reports the single largest expense of a period."],
             ["5", "Generate personalised budget recommendations and alerts on threshold breaches",
              "Partly achieved: user-set budgets with alerts at 75, 90 and 100 %, a six-component health score and rule-based advice; no learned (reinforcement-learning) recommender."],
             ["6", "Visualise spending, category breakdown and forecasts on an interactive dashboard",
              f"Achieved: a React dashboard and analytics page with {F.N_PAGES} pages, charts of monthly trend and category split, and a prediction panel; {len(__import__('os').listdir(F.SHOTS))} screens captured."]],
            widths=[0.45, 2.3, 3.65], align=["c", "l", "l"], size=10),
        P("The batch abstract also promises a Flask and MySQL application with loan tracking, and the batch notes mention a loan amortisation tracker and scheduled digest alerts. "
          "The shipped system uses FastAPI and SQLite (it began as a Streamlit application); it has no loan table, no amortisation calculator and no timer-driven alerts. These are deviations from the abstract and are repeated in Chapters 9 and 10."),
        H2("1.6 Scope of the Project"),
        P("**In scope.** Accounts with strong-password rules and per-user data; manual and file-based transaction entry; search, filter, edit and delete; a trained expense categoriser with a keyword fallback and learning from corrections; "
          "monthly budgets with threshold alerts; savings goals with required monthly saving; a manual investment portfolio with optional live price refresh; analytics (monthly trend, category split, largest expense); "
          "a next-month and per-category spending forecast; the six-component health score; a rule-routed assistant with an optional language-model layer; PDF, Excel and CSV reports; notifications; "
          f"a demo account with fictional data; and the tests, probe set and measurement scripts that produce every number in this report. The web application has {F.N_PAGES} pages over {F.N_ROUTES} REST routes and {F.N_TABLES} database tables."),
        P("**Out of scope.** Anomaly or fraud detection; reinforcement-learning budgeting; deep sequence models (BERT, LSTM); loan, debt and tax tools; bank-API or SMS import; multi-currency conversion; "
          "multi-user households or sharing; scheduled digests; mobile apps; production hosting, backups and migrations; and any study with real users or real financial records."),
        H2("1.7 Project Contributions"),
        N("**A complete, runnable finance platform.** One code base covers accounts, entry and import, categorisation, budgets, goals, investments, analytics, forecasting, a health score, an assistant and reports, "
          f"behind {F.N_ROUTES} REST routes and a {F.N_PAGES}-page React console, started with one command.",
          "**An explainable health score.** Six weighted components with published weights and bands; a sensitivity study and a 5,000-profile check show that the score is monotone in the savings rate and where it saturates.",
          "**A learn-from-correction categoriser.** The model retrains on the user's history plus the correction; a measured test shows that one correction fixes a repeat merchant in every variant tested while barely helping new merchants.",
          "**A forecast with a stated floor.** The module refuses to predict with fewer than three months, and a simulation shows that three months is too few for a linear trend to beat a mean.",
          f"**An honest evaluation.** {F.PYTEST_PASSED} passing tests, {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks, a 198-description probe set, a rolling-origin backtest, a 1,000-row import test and measured response times, "
          "reported together with the defects they exposed."),
        P(f"In brief, the shipped categoriser reaches {c['tfidf_lr']['accuracy'] * 100:.1f} % accuracy on the probe set (macro F1 {c['tfidf_lr']['macro_f1']:.3f}) against {c['keyword_table']['accuracy'] * 100:.1f} % for the keyword table, "
          f"but {c['tfidf_lr']['accuracy_by_tier']['A'] * 100:.0f} % on seed-like text and {c['tfidf_lr']['accuracy_by_tier']['C'] * 100:.1f} % on unseen merchants, where {c['errors_predicted_as_transport']} of the {len(c['errors'])} errors are labelled Transport. "
          f"The demo forecast has a MAPE of {bt['mape_pct']['linear_trend (app)']:.1f} % against {bt['mape_pct']['mean_of_all']:.1f} % for a plain mean. "
          "The base paper's accuracy figures are neither reproduced nor contradicted: its data, labels and model are different. All results come from a very small seed list and synthetic demo data."),
        H2("1.8 Limitations and Assumptions"),
        B("**Tiny training set.** The classifier learns from 51 short phrases, 3 to 6 per category; leave-one-out accuracy on that list is 11.8 %.",
          "**Synthetic data.** The demo account is fictional and the probe set was written by the team, so it is not an independent benchmark.",
          "**Simple models.** The forecast is a straight line through monthly totals and the advice is rule-based; there is no anomaly detector, reinforcement learning or deep model.",
          "**Optional language model untested.** The optional Anthropic layer was never exercised in any measurement.",
          "**Known defects.** Unseen merchants are silently labelled, mostly as Transport, because the app applies no confidence threshold; imports commit one row at a time (35.2 rows per second); alerts are de-duplicated by message text only; tokens are home-made HMAC bearer tokens with a default development secret.",
          "**Single machine, single user.** Concurrency, mobile browsers and live price refresh were not tested.",
          "**Not financial advice.** Advice screens carry a disclaimer."),
        H2("1.9 Organization of the Report"),
        P("Chapter 2 surveys the literature and analyses the base paper. Chapter 3 studies feasibility, and Chapter 4 sets out the existing and proposed systems and the requirements. "
          "Chapter 5 gives the design: architecture, workflow, data flow and UML diagrams, the database, the modules and the user interface. Chapter 6 describes the methodology and implementation: "
          "the data, the categoriser, the forecast and the health score with their mathematics, the API, security and error handling, and how to install and run the system. "
          "Chapter 7 reports testing. Chapter 8 presents every output screen, the measured results, the comparison with the base paper and the objectives against outcomes. "
          "Chapter 9 concludes and Chapter 10 sets out the future scope. The references and three appendices (important code, installation and user guide, additional screens) follow."),
    ]
    return out
