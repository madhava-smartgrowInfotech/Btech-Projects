"""Text of 19.IEEE_Paper.docx (FINJARVIS). Every number is read from facts.py (experiments/metrics.json, experiments/api_latency.json) or typed from docs/REPORT_FACTS.md.

Citations are written {r:key,key} (keys of refs.py); Paper.expand numbers them in order of first appearance, the base paper being [1].
"""
from . import facts as F
from . import paper_figs
from .paper import Paper


def build(path):
    figs = paper_figs.make()
    P = Paper()
    C, FC, HL, AS, IMP = F.CLS, F.FC, F.HL, F.AS, F.IMP
    bt = FC["demo_backtest"]
    mape, mae = bt["mape_pct"], bt["mae"]
    simh = {r["history_months"]: r for r in FC["sim_mape_by_history_pct_noise_0.10"]}
    simn = {r["noise_ratio"]: r for r in FC["sim_mape_by_noise_pct"]}
    tl = C["tfidf_lr"]
    lc = {d["corrections"]: d["tier_C_accuracy_mean"] for d in C["learning_from_corrections"]}
    rm = C["repeat_merchant_learning"]
    cc = {d["threshold"]: d for d in C["confidence_curve"]}
    rc = HL["rating_counts"]

    authors = [[n.upper(), f"Roll No. {r}", "Dept. of CSE", F.COLLEGE_SHORT, "Hyderabad", "[EMAIL]"] for n, r in F.STUDENTS]
    authors.append([F.GUIDE.upper(), f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of CSE", F.COLLEGE_SHORT, "Hyderabad", "[EMAIL]"])
    P.title_block("FINJARVIS: An AI Based Personal Finance Manager with Expense Categorisation, Spending Forecast and Health Score", authors)
    P.begin_two_columns()

    P.abstract(
        "Most budgeting tools report what was spent but neither predict nor explain it, and manual entry is tedious. "
        "This paper presents FINJARVIS, a web application in which a user records or imports transactions, a TF-IDF and logistic-regression model labels each one, "
        "a linear trend forecasts next month's spending, six weighted components give a 0-100 financial health score, and a rule-routed assistant answers questions from the user's own records. "
        f"The system has {F.N_ROUTES} API routes and {F.N_TABLES} tables and passes {F.PYTEST_PASSED} unit tests and {F.SMOKE_TOTAL} end-to-end checks. "
        f"On a 198-description probe set the categoriser reaches {tl['accuracy'] * 100:.1f} % accuracy, but only {tl['accuracy_by_tier']['C'] * 100:.1f} % on merchants it has not seen, because it learns from just 51 examples. "
        f"On a six-month demo history the linear trend is not better than a plain average, and a simulation shows that it needs about seven months of data before it is. "
        f"The assistant answered {AS['answerable_handled_by_analytics']} of {AS['answerable']} answerable questions. "
        "Anomaly detection, reinforcement-learning budgeting and deep-learning forecasting from the base paper are not implemented.",
        ["budgeting", "expense categorisation", "financial health score", "forecasting", "logistic regression", "personal finance", "TF-IDF"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("People now hold salaries, cards, UPI payments, recurring bills and investments at once, and managing them well matters: financial literacy is linked to saving, investment and retirement planning {r:lusardi}, "
           "and low literacy is reported among young adults in particular {r:to}. In practice most people either keep no record or keep one by hand. A spreadsheet or a ledger shows what has already been spent, "
           "takes time to maintain, and says nothing about the month ahead; commercial applications add automation but are closed, paid and not adaptable to one household's commitments. "
           "The base paper of this project {r:base} proposes four models in one assistant (BERT categorisation, Q-learning budgeting, LSTM forecasting and Isolation Forest anomaly detection) and reports high scores, "
           "but on synthetic or privately collected data, and without a runnable application that others can inspect.")
    P.para("This paper makes four contributions. (1) FINJARVIS, a tested full-stack platform (FastAPI, React, SQLite; "
           f"{F.N_ROUTES} routes, {F.N_TABLES} tables) for accounts, transactions, CSV and Excel import, budgets with alerts, goals, investments, reports and an assistant. "
           "(2) Three transparent AI modules: a TF-IDF and logistic-regression categoriser that retrains on a user's corrections, a least-squares trend forecast, and a six-component health score. "
           f"(3) Verification with {F.PYTEST_PASSED} pytest tests, {F.SMOKE_TOTAL} end-to-end checks and measured response times. "
           "(4) An honest measurement of where the simple modules fail: on unseen merchants, on short histories and on questions outside five intents. Section II reviews related work, Section III the method, Section IV the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("All measurements were taken on one machine: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Intel UHD 770 graphics (no discrete GPU, none used), Windows 11 Pro, with other programs running.")
    P.sub("B", "Software Requirements")
    P.para("Python 3.11.9, FastAPI 0.159.1, SQLAlchemy 2.1.6 {r:sqla} on SQLite, scikit-learn 1.9.1 {r:sklearn}, pandas 3.0.6, NumPy 2.4.6, pydantic 2.14.1, passlib 1.7.4 with bcrypt 4.0.1 {r:bcrypt}, "
           "ReportLab 5.1.0 and openpyxl 3.1.5 for reports, React 18.3 with Vite 8, Tailwind 4, Recharts and TanStack Query on Node 24.19.0, pytest 8.2.0 and Playwright with Chrome for tests and screenshots.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Kharat et al. {r:base} build a Smart Personal Finance Assistant from four modules. A bert-base-uncased model is fine-tuned to classify transaction descriptions (128 tokens, learning rate 5e-5, batch 8, ten epochs, 80/20 split), "
           "with the category set widened from 16 to 50 and SMOTE {r:smote} used against class imbalance; a tabular Q-learning {r:qlearn} agent with states built from income, fixed and variable expenses and a savings goal, a reward of +1 or -1, "
           "alpha 0.1, gamma 0.95 and epsilon decaying from 0.995 to 0.01 over 300 episodes recommends one of three savings levels; an LSTM {r:lstm} with 64 units trained on 12-month savings sequences forecasts the next savings value; "
           "and an Isolation Forest {r:iforest} with 300 trees and a contamination of 0.015 flags unusual transactions from savings and expense ratios. The modules sit behind a Streamlit interface. "
           "Reported results are 92.3 % accuracy, 90.8 % precision, 91.5 % recall and 91.1 % F1 for categorisation, RMSE 137.2, MAE 89.5 and R2 0.63 for the savings forecast, and 93 %, 94 % and 94 % precision, recall and F1 for anomalies, "
           "plus improvements of 42 %, 31 %, 29 % and 27 % over rule-based, static, ARIMA and manual baselines. The data are synthetic or collected from financial APIs and labelled by hand, are not released, and the unit of the forecast errors is not stated.")
    P.para("**Related work.** For text categorisation, term weighting with TF-IDF {r:tfidf} is the classical, inspectable baseline, and pre-trained transformers such as BERT {r:bert} and its financial variant FinBERT {r:finbert} add context at the cost of data and compute. "
           "For forecasting, error measures such as MAPE need care {r:hk}, and the M3 comparison of Makridakis et al. {r:makri} found that simple statistical methods were at least as accurate as the machine-learning methods tested, "
           "which is relevant when a user has only a few months of history. Recent personal-finance systems combine such models: FinSenseAI {r:finsense} joins XGBoost, an LSTM and SHAP explanations for expense prediction, "
           "and a leakage-detection system {r:leak} uses an Isolation Forest and K-Means on synthetic transactions; a data-generation framework {r:theerthala} fine-tunes an 8-billion-parameter language model for personal-finance advice, "
           "and a design study {r:to} builds a gamified mobile app for young adults. Table I states what each work reports, using only what its text says.")
    P.table("Related work compared", ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [["Kharat et al. {r:base}", "BERT, Q-learning, LSTM, Isolation Forest; Streamlit", "Synthetic and labelled real data, 50 categories", "Accuracy 92.3 %; R2 0.63; anomaly F1 94 %", "Data not released; no deployed app"],
             ["Dilip, Janaki {r:finsense}", "XGBoost + LSTM + SHAP expense prediction", "Real transaction table, size not stated", "No numeric result in the text read", "Metrics listed, not reported"],
             ["Abiya et al. {r:leak}", "Isolation Forest + K-Means; subscription and balance forecast", "Synthetic transactions", "Better than rule-based budgeting (no metrics)", "Synthetic data only"],
             ["Theerthala {r:theerthala}", "Fine-tuned 8B LLM advisor on generated reasoning data", "19k synthetic samples", "Comparable to 14-32B models at about 80 % lower cost", "LLM-judged; no transaction pipeline"],
             ["To {r:to}", "Goal-directed design and gamification for a mobile app", "Survey 18-30; 10 card-sort, 6 test users", "Usability study, no model results", "Small samples; no forecasting"]],
            [0.62, 0.8, 0.62, 0.74, 0.62], size=5.8, align=["l", "l", "l", "l", "l"])
    P.para("**Positioning.** Against the base paper, FINJARVIS keeps the idea of one assistant over categorisation, budgeting and forecasting but changes every module. A BERT classifier over 50 categories becomes a TF-IDF and logistic-regression model over 11 categories; "
           "Q-learning budget recommendation becomes user-set monthly budgets with alerts at 75, 90 and 100 % of the limit and rule-based suggestions; the LSTM savings forecast becomes a least-squares trend over monthly expense totals; "
           "and the Isolation Forest has no counterpart, the nearest feature being the single largest expense in a chosen window. In place of a Streamlit demonstration there is a login-protected web application, and the product adds import with preview, goals, "
           "a manual investment portfolio, PDF, Excel and CSV reports, a financial health score and a rule-based assistant. These choices trade accuracy on hard inputs for a system that can be run, read and tested by one team on a laptop.")
    P.para("**Gap.** The works above either report scores on data that others cannot inspect, report no numbers, or study design without models, and none of them gives a runnable application together with a measurement of its simple modules on unseen input. "
           "FINJARVIS provides the application and the measurements; it deliberately implements simpler models than the base paper, and Section IV states what that costs.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Architecture and Implementation")
    P.figure(figs["arch"], "FINJARVIS architecture: React console, FastAPI service with 33 routes, a service layer, three small ML modules and a SQLite database.", 3.3)
    P.para("The console (Vite, port 5411) has thirteen pages and calls a FastAPI service (port 8411) whose routes hold no business logic: each calls the same service function that the original Streamlit pages call, "
           "so both interfaces share one SQLite file and one set of tests. Requests are validated by pydantic and protected by a bearer-token dependency; data are scoped by a user_id on every table and query. "
           "Passwords need eight characters with upper case, lower case, a digit and a symbol, and are stored as bcrypt hashes; tokens are HMAC-SHA256 signed and expire after seven days. "
           "Six tables (users, transactions, budgets, financial_goals, investments, notifications) are mapped with SQLAlchemy, with cascading deletes. "
           "Reports are written as PDF, Excel and CSV. An optional language-model layer is used only when a key is configured and is not part of any measurement here. "
           "The design follows the REST style {r:rest}; the choice of SQLite keeps installation to one file, at the price of a single writer. Fig. 2 summarises the flow of data through the modules described next.")
    P.sub("B", "Expense Categoriser")
    P.para("The categoriser is a scikit-learn pipeline: word 1-2-gram TF-IDF {r:tfidf} followed by multinomial logistic regression, trained on a built-in list of 51 description and category pairs in 11 categories (3 to 6 per category). "
           "For a description x with feature vector phi(x), the predicted category is")
    P.eq("k* = argmax_k P(k | x),   P(k | x) = exp(w_k·phi(x) + b_k) / Σ_j exp(w_j·phi(x) + b_j).")
    P.para("When a user adds a transaction with category 'Auto-detect' the label is stored; if the user chooses a different category, the model is retrained on the seed list, the user's whole history and the correction. "
           "A keyword table is used only if the stored model cannot be loaded, and the model never outputs 'Other'. Retraining takes about 5 ms.")
    P.figure(figs["flow"], "Main flow of FINJARVIS: transaction entry, automatic category, budget alert, monthly totals, forecast, health score and assistant.", 3.3)
    P.sub("C", "Forecast and Health Score")
    P.para("Monthly expense totals of n months (indexed 0 to n-1) are fitted by least squares and extrapolated one step, clipped at zero:")
    P.eq("ŷ_next = max(0, a·n + b),   (a, b) = argmin Σ_t (y_t − a·t − b)²,   t = 0, …, n−1.")
    P.para("The trend is labelled increasing if the slope exceeds 1 and decreasing if it is below -1; the tool refuses to predict with fewer than three months. The same fit per category gives a budget-overrun check. "
           "The health score is a weighted sum of six component scores, each clipped to [0, 100]:")
    P.eq("H = 0.30 s_sav + 0.20 s_exp + 0.15 s_bud + 0.15 s_cash + 0.10 s_div + 0.10 s_goal.")
    P.para("Here the savings-rate score is the savings rate divided by 20 %, the expense score the unspent share of income divided by 50 %, the budget score the share of budgets at or below 100 %, the cash-cushion score the months of expenses covered by the balance divided by six, "
           "the diversification score the number of distinct asset types divided by five and the goal score the mean goal completion; ratings are Excellent from 90, Good from 75, Fair from 60, Needs Improvement from 40 and Critical below. "
           "Budget alerts are raised at 75, 90 and 100 % of a category budget.")
    P.para("Four implementation decisions are worth stating with their reasons. The categoriser is a linear model on sparse features because it trains in milliseconds, can be retrained inside a request when a user corrects a label, "
           "and its decision can be traced to words; a transformer would need data and a GPU that a household application does not have. The forecast refuses to run on fewer than three months rather than guess. "
           "Import is a two-step flow: a preview parses the file, categorises blank rows and lists every skipped row as 'Row n' with the reason (unparsable date, non-numeric or non-positive amount, blank description), and only a second call commits it. "
           "Budget alerts are written to the notifications table by a check that runs only when the dashboard or the notifications list is read, not on a timer and not when a transaction is saved, so no scheduler process is needed but an alert appears only after the next such read, and goals and investments are kept as plain rows (target, saved amount, quantity, prices) so that their totals feed the health score.")
    P.para("The health score was added because a raw balance says little about resilience. Its six parts are explainable on their own: each has a plain-language meaning, the weakest part is named on the dashboard, "
           "and every part is computed from the user's rows, with a neutral value of 50 when there is nothing to measure (no budgets, no expenses or no goals) and 0 for diversification when there are no holdings. "
           "The same per-user scoping applies to the assistant, whose answers are prefixed by the amount computed and followed by a standing notice that they are informational and not financial advice.")
    P.sub("D", "Assistant, Data and Evaluation Protocol")
    P.para("The assistant routes a question by keyword to one of five handlers (can I save, reduce expenses, health score, where am I spending, spend on a named category) and answers from SQL aggregates of the user's own rows; "
           "other questions get a fixed help text. No external dataset is used. The demo account holds 68 fictional transactions over six months, built from a 34-row sample file plus synthetic earlier months, so every figure on screen is synthetic. "
           "Because the model has no train and test split, we evaluate it on a 198-description probe set written by the team before scoring and never used for training: 11 categories times three tiers of six, "
           "tier A phrases close to the seed, tier B upper-case statement strings that contain a seed keyword, tier C unseen merchants and phrases. This is not an independent benchmark. "
           "The forecast is evaluated by a one-step-ahead rolling backtest on the demo history and by a simulation of 2,000 users per setting (12-month level plus drift, Gaussian noise and a 10 % chance of a +50 % spike). "
           f"The rest is covered by {F.PYTEST_PASSED} pytest tests, {F.SMOKE_TOTAL} smoke checks, a 1,000-row import file with 84 injected bad rows, 26 assistant questions and response-time runs on 127.0.0.1. "
           "Cross-validation on 51 seeds is reported as leave-one-out {r:kohavi}.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.sub("A", "Expense Categoriser")
    P.para("Table II lists the headline measurements. "
           f"On the probe set the shipped model scores {tl['accuracy'] * 100:.1f} % accuracy (142 of 198) and macro-F1 {tl['macro_f1']:.3f}, against {C['keyword_table']['accuracy'] * 100:.1f} % for the keyword table and {C['majority_class']['accuracy'] * 100:.1f} % for always answering Food. "
           f"The overall figure hides a sharp split: {tl['accuracy_by_tier']['A'] * 100:.0f} % on tier A, {tl['accuracy_by_tier']['B'] * 100:.0f} % on tier B and {tl['accuracy_by_tier']['C'] * 100:.1f} % on tier C. "
           f"Of the 56 errors, {C['errors_predicted_as_transport']} are labelled Transport: a description with no word from the seed list gives an all-zero feature vector, the decision then comes from the intercepts, and Transport has the highest, "
           "so the class precision of Transport is 0.27 while its recall is 1.0. The model never says it does not know, although its probabilities could support that: keeping only predictions with a top probability of at least 0.15 retains "
           f"{cc[0.15]['coverage'] * 100:.1f} % of items at {cc[0.15]['accuracy_on_kept'] * 100:.1f} % accuracy, but the application applies no threshold. "
           f"Leave-one-out on the 51 seed pairs gives only {C['loo_cv_accuracy_on_seed'] * 100:.1f} %, since each phrase's words occur nowhere else.")
    rows = [["Categoriser, 198 probe items: accuracy / macro-F1", f"{tl['accuracy'] * 100:.1f} % / {tl['macro_f1']:.3f}"],
            ["Accuracy by tier A / B / C", f"{tl['accuracy_by_tier']['A'] * 100:.0f} / {tl['accuracy_by_tier']['B'] * 100:.0f} / {tl['accuracy_by_tier']['C'] * 100:.1f} %"],
            ["Keyword table / majority class (accuracy)", f"{C['keyword_table']['accuracy'] * 100:.1f} % / {C['majority_class']['accuracy'] * 100:.1f} %"],
            ["Repeat merchant, before / after one correction", f"{rm['accuracy_before_correction'] * 100:.1f} / {rm['accuracy_after_one_correction'] * 100:.0f} %"],
            ["Unseen merchants after 48 corrections", f"{lc[48] * 100:.1f} %"],
            ["Forecast MAPE, 3 backtest points: trend / mean of all / mean of last 3", f"{mape['linear_trend (app)']:.1f} / {mape['mean_of_all']:.1f} / {mape['mean_of_last_3']:.1f} %"],
            ["Simulated MAPE, 3 months: trend / mean of all", f"{simh[3]['linear_trend (app)']:.1f} / {simh[3]['mean_of_all']:.1f} %"],
            ["Simulated MAPE, 7 months: trend / mean of all", f"{simh[7]['linear_trend (app)']:.1f} / {simh[7]['mean_of_all']:.1f} %"],
            ["Demo health score", "90.4 (Excellent)"],
            ["5,000 random profiles: mean score, range", f"{HL['score_mean']:.1f}, {HL['score_min']}-{HL['score_max']}"],
            ["Assistant: answerable handled / off-topic declined", f"{AS['answerable_handled_by_analytics']} of {AS['answerable']} / {AS['unanswerable_correctly_declined']} of {AS['not_answerable']}"],
            ["Import of 1,000 rows: bad rows skipped / rows per s", f"{IMP['rows_skipped']} of {IMP['injected_bad_total']} / {IMP['rows_per_second_commit']:.1f}"],
            ["pytest / smoke checks passed", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} / {F.SMOKE_PASSED} of {F.SMOKE_TOTAL}"]]
    P.table("Measured results of FINJARVIS", ["Measure", "Result"], rows, [2.25, 1.1], size=6.4, align=["l", "l"])
    P.figure(figs["results"], "(a) Categoriser accuracy by probe tier for the shipped model, the keyword table and the majority class; (b) simulated forecast error against months of history; (c) demo-account forecasts of months four to six by four methods.", 3.3)
    P.para(f"Corrections help in one way only. When a user corrects one unseen merchant, the same merchant narrated three other ways is then labelled correctly {rm['accuracy_after_one_correction'] * 100:.0f} % of the time (from {rm['accuracy_before_correction'] * 100:.1f} %, 198 tests), "
           f"but adding up to 48 random corrections moves accuracy on other new merchants only from {lc[0] * 100:.1f} % to {lc[48] * 100:.1f} %; the repeat test is easy because the variants share the corrected words. "
           "The 34-row sample file is labelled with 100 % accuracy, but its vocabulary overlaps the seed list, so that figure is optimistic.")
    pc = C["per_category"]
    names = list(pc)
    half = (len(names) + 1) // 2
    rows_pc = []
    for i in range(half):
        a = names[i]
        r = [a, f"{pc[a]['precision']:.2f}", f"{pc[a]['recall']:.2f}", f"{pc[a]['f1']:.2f}"]
        if i + half < len(names):
            b = names[i + half]
            r += [b, f"{pc[b]['precision']:.2f}", f"{pc[b]['recall']:.2f}", f"{pc[b]['f1']:.2f}"]
        else:
            r += ["", "", "", ""]
        rows_pc.append(r)
    P.para("Table III gives the per-category scores. Healthcare, Rent, Travel, Investments and Salary reach precision 1.0 because only tier-A and tier-B items are ever assigned to them, "
           "recall lies between 0.61 (Shopping) and 0.78 (Education) for every other class, and the single poor precision is the catch-all Transport. "
           "The remaining tier-B errors are informative: 'UPI-AMAZON-PAY-8821' goes to Entertainment because the seed list contains 'amazon prime video', and 'UPI-HOSPITAL-BILL' goes to Bills.")
    P.table("Per-category scores on the probe set (18 items each)", ["Category", "P", "R", "F1", "Category", "P", "R", "F1"], rows_pc,
            [0.78, 0.28, 0.28, 0.3, 0.78, 0.28, 0.28, 0.3], size=6.2, align=["l", "c", "c", "c", "l", "c", "c", "c"])
    P.sub("B", "Forecast")
    P.para(f"On the demo account, with monthly expenses of 26,579; 26,878; 28,384; 36,118; 43,579 and 30,080 INR, we forecast months four to six from the months before them. The trend follows the August and September rise but overshoots October, "
           f"and its MAPE of {mape['linear_trend (app)']:.1f} % is worse than the mean of all history ({mape['mean_of_all']:.1f} %), the mean of the last three months ({mape['mean_of_last_3']:.1f} %) and repeating the last value ({mape['last_value']:.1f} %); MAE is "
           f"{mae['linear_trend (app)']:,.0f}, {mae['mean_of_all']:,.0f}, {mae['mean_of_last_3']:,.0f} and {mae['last_value']:,.0f} INR. Three test points prove little, so we simulated 2,000 users per setting. "
           f"At noise 0.10 the trend has a MAPE of {simh[3]['linear_trend (app)']:.1f} % with three months of history against {simh[3]['mean_of_all']:.1f} % for a plain mean, and it is better than the mean of all history only from about seven months "
           f"({simh[7]['linear_trend (app)']:.1f} against {simh[7]['mean_of_all']:.1f} %); the mean of the last three months was at least as good as the trend in every noise setting (e.g. {simn[0.2]['mean_of_last_3']:.1f} against {simn[0.2]['linear_trend (app)']:.1f} % at 0.20). "
           f"Across noise levels from 0.05 to 0.30 the trend's simulated MAPE rises from {simn[0.05]['linear_trend (app)']:.1f} to {simn[0.3]['linear_trend (app)']:.1f} %, the last-three-month mean from {simn[0.05]['mean_of_last_3']:.1f} to {simn[0.3]['mean_of_last_3']:.1f} %. "
           f"The minimum of three months is therefore too low for this method. For November the application predicts {FC['demo_backtest']['app_prediction_for_next_month']['predicted_next_month_expense']:,.0f} INR against a recent three-month average of "
           f"{FC['demo_backtest']['app_prediction_for_next_month']['recent_average']:,.0f} INR.")
    P.sub("C", "Health Score and Assistant")
    P.para(f"The demo account scores 90.4 (Excellent) with components 100, 100, 100, 100, 80 and 24; goal progress is the weakest. From a baseline profile of 80.7, raising the savings rate from 0 to 20 % lifts the score from 50.7 to 80.7 and then saturates; "
           f"over 5,000 random profiles the score ranges from {HL['score_min']} to {HL['score_max']} (mean {HL['score_mean']:.1f}; {rc['Critical']} Critical, {rc['Excellent']} Excellent), and raising the savings rate by five points never lowered it. "
           "The weights are chosen by the authors, not fitted, and savings rate and expense ratio, which together carry half the score, are strongly correlated. "
           f"The assistant handled {AS['answerable_handled_by_analytics']} of {AS['answerable']} answerable questions; it missed 'groceries', 'biggest expense', 'eating out', 'largest purchase', 'run out of money' and 'which category to cut', which fell to the help text, and it declined all {AS['not_answerable']} off-topic questions. "
           "Its numbers are correct: 'How much did I spend on Food?' returns INR 17,365, equal to a direct sum, and the top category Rent matches a group-by. One quirk remains: 'Am I overspending on shopping?' is answered with the Shopping total, not a comparison with its budget.")
    P.para("The sensitivity runs show how the score behaves. With expenses at 20,000, 32,500, 45,000, 55,000, 65,000 and 75,000 INR a month the score falls from 85.5 to 80.7, 70.9, 63.7, 56.8 and 56.3, "
           "and a balance of 0, 50,000, 100,000 and 195,000 INR or more gives 73.0, 76.8, 80.7 and 88.0, capped at six months of expenses. Goal progress from 0 to 100 % and the number of asset types from 0 to 5 each move the score by 10 points "
           "(76.7 to 86.7), the full weight of the part. The score therefore rewards a high savings rate and low spending most, and these two inputs overlap, so a household with high income but no goals or holdings still scores in the 70s.")
    P.sub("D", "Tests and Response Time")
    L = F.lat
    rows3 = [["Login (bcrypt verify)", f"{L('login'):.0f} / {L('login', 'p95_ms'):.0f}"],
             ["GET dashboard", f"{L('GET /dashboard'):.0f} / {L('GET /dashboard', 'p95_ms'):.0f}"],
             ["GET analytics", f"{L('GET /analytics'):.0f} / {L('GET /analytics', 'p95_ms'):.0f}"],
             ["POST predict-category", f"{L('POST /transactions/predict-category'):.1f} / {L('POST /transactions/predict-category', 'p95_ms'):.1f}"],
             ["POST transaction (auto-categorise)", f"{L('POST /transactions (auto'):.1f} / {L('POST /transactions (auto', 'p95_ms'):.1f}"],
             ["POST assistant ask (analytics)", f"{L('POST /assistant/ask (analytics)'):.1f} / {L('POST /assistant/ask (analytics)', 'p95_ms'):.1f}"],
             ["GET report CSV / PDF / Excel", f"{L('GET /reports/csv'):.0f} / {L('GET /reports/pdf'):.0f} / {L('GET /reports/excel'):.0f} (median)"],
             ["Import preview, 100 rows", f"{L('POST /transactions/import/preview'):.0f} / {L('POST /transactions/import/preview', 'p95_ms'):.0f}"]]
    P.table("Response time in ms, median / p95 (127.0.0.1, one user)", ["Endpoint", "ms"], rows3, [2.2, 1.15], size=6.4, align=["l", "l"])
    P.para(f"The {F.PYTEST_TOTAL} pytest tests (authentication 9, budgets 6, health score 6, ML 9, transactions 8) and {F.SMOKE_TOTAL} smoke checks pass, covering weak and wrong passwords, a tampered token, per-user isolation, CRUD, import, reports and validation. "
           "Ordinary calls take under 75 ms apart from login (bcrypt) and report generation. The import commit writes one row per database session and runs at "
           f"{IMP['rows_per_second_commit']:.1f} rows/s; of 1,000 rows, all 84 injected bad rows (bad dates, negative or non-numeric amounts, blank descriptions) were skipped and 916 imported with automatic categories.")
    P.sub("E", "Output Screens")
    P.para("Figures 4 and 5 were captured from the running application with the demo account. The dashboard shows the month's balance, income, expenses, savings, net worth and the health score of 90 with its six components; "
           "the assistant answers 'Where am I spending the most money?' and 'What is my financial health?' from the stored rows, each marked as calculated from the user's data.")
    P.figure(figs["dash"], "Real screen: dashboard of the demo account with balance, income, expenses, savings rate, net worth and the financial health score (90, Excellent).", 3.3)
    P.figure(figs["assist"], "Real screen: the assistant answering from the demo account's own transactions and health score.", 3.3)
    P.sub("F", "Comparison with the Base Paper")
    P.para("The base paper reports 92.3 % categorisation accuracy with BERT on 50 categories, R2 0.63 for LSTM savings forecasts and 94 % F1 for anomalies {r:base}. FINJARVIS measures 71.7 % on 11 categories with a 51-example model, "
           "evaluates a trend forecast by MAPE on a different series, and has no anomaly detector, so no number is comparable: the datasets, label sets, models and targets differ, and the base data are not available. "
           "What can be said is qualitative: a context-free bag-of-words model fails on unseen merchants, which a pre-trained language model {r:bert} is designed to reduce, and forecasting with few observations favours simple baselines {r:makri}. "
           "In return the system is inspectable end to end, runs in milliseconds on a CPU and has been run and tested.")
    P.para("**Threats to validity.** The probe set was written by the team that built the model, so tier A and B reflect the vocabulary it knows; the demo data are fictional with a seeded gentle upward drift, "
           "which flatters a trend model; the forecast backtest has three points; latency was measured once on a busy desktop and moves between runs, while accuracy figures did not; and the assistant questions were written after reading its handlers. "
           "The numbers should be read as a description of this implementation, not as an estimate of performance on real households.")
    P.sub("G", "Failure Cases and Observed Limits")
    P.para("Unseen merchants are mislabelled silently, mostly as Transport (tier C 18.2 %). The seed list is tiny and corrections do not generalise. The trend forecast is not better than an average below about seven months. "
           "Anomaly detection (objective 4), time-series models beyond a linear trend, a reinforcement-learning budget recommender, a loan tracker and scheduled alerts are not implemented; budgets are set by the user and advice comes from rules. "
           "The abstract names Flask and MySQL, whereas the shipped system uses FastAPI and SQLite. Tokens are home-made bearer tokens with no revocation and a default secret if none is set, import commits row by row, "
           "and budget-alert de-duplication is by message text, so a budget that is crossed again in a later month raises no new alert. The data are fictional; there was no user study, concurrency test or security scan, and the language-model layer and live price refresh were not run.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion and Future Scope")
    P.para(f"FINJARVIS delivers accounts, entry and import of transactions, automatic categories, budgets with alerts, goals, investments, a next-month forecast, a health score, an assistant and reports, verified by {F.PYTEST_PASSED} tests and {F.SMOKE_TOTAL} end-to-end checks. "
           "Against the six objectives, accounts and import, categorisation, forecasting of expenses, budget alerts and the dashboard are achieved in simple form; forecasting of savings with time-series models and anomaly detection are not. "
           f"The main finding is that the transparent models work where the input resembles their data ({tl['accuracy_by_tier']['B'] * 100:.0f} % on statement strings) and fail quietly where it does not ({tl['accuracy_by_tier']['C'] * 100:.1f} % on new merchants), "
           "and that three months are too little for a linear trend. The limits are the 51-example training set, synthetic data and the missing modules.")
    P.para("Future work: train the categoriser on a public or consented transaction corpus and abstain below a confidence threshold; require at least seven months, or switch to a recent average, for forecasts; "
           "add anomaly detection with a z-score or Isolation Forest rule and test it on injected outliers; fit the health-score weights to user outcomes; batch the import commit; and add refresh-token authentication and a user study.")

    P.references()
    P.save(path)
    return path
