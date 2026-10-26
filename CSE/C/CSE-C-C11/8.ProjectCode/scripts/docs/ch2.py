"""Chapter 2: Literature survey."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import N as C


def lit_rows():
    return [[w, a, d, r, l] for _, w, a, d, r, l in lit.ROWS]


def blocks():
    c = F.CLS
    bt = F.FC["demo_backtest"]
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The survey has four threads: the registered base paper, a multi-model personal finance assistant; automatic categorisation of transaction text; "
          "forecasting of personal expenses, where the question is how much model is worth having with only a few months of history; and the recent personal-finance systems around the base paper. "
          f"The base paper {C('base')} is analysed in Section 2.2 and every claim about it was checked against the PDF in the batch folder. "
          "Claims about the other works are limited to what their own abstracts and text say; where a paper reports no result the tables say so."),
        P("The batch literature survey (5.LITERATURE SURVEY.docx) lists five works: the base paper and four papers from 2025 and 2026. A search on 26 October 2026 located two of the four "
          f"({C('finsense')} and {C('leak')}), found an IEEE Xplore record for a third whose authors and conference could not be read {C('s2')}, "
          f"and found no record of the fourth {C('s3')}; the last two are listed as the batch gave them and nothing here depends on their content. "
          f"The two papers in the batch's base-paper archive {C('to')}, {C('theerthala')} were read in full and are used as supporting work."),
        H2("2.2 Base Paper Analysis"),
        H3("2.2.1 Registered base paper: Kharat et al., IJRASET, 2025"),
        P(f"**Reference.** R. Kharat, S. Solapurkar, A. Tikkas, M. Uttarwar and A. Yadav, \"A Smart AI-Based Personal Finance Assistant: A Multi-Model Approach for Expense Categorization, Budgeting, Forecasting and Anomaly Detection,\" "
          f"IJRASET, vol. 13, no. XI, pp. 167-180, November 2025, doi 10.22214/ijraset.2025.75019 {C('base')}. The authors are from the Department of Computer Engineering, Pimpri Chinchwad College of Engineering, Pune."),
        P("**Problem.** Users struggle to categorise expenses, plan budgets, forecast savings and spot fraudulent transactions; existing tools rely on manual input and rule-based approaches that are error-prone and not personalised. "
          "The paper proposes one assistant that automates all four tasks and adapts to the user's behaviour."),
        P(f"**Method.** Four independent modules form a pipeline. (1) *Expense categorisation*: transaction descriptions are cleaned, tokenised with the BERT tokenizer and classified by a fine-tuned bert-base-uncased model {C('bert')}; "
          f"the label set is extended from 16 to 50 categories and class imbalance is handled with SMOTE {C('smote')}; training uses learning rate 5e-5, batch size 8, 10 epochs, dropout 0.1 and an 80/20 split. "
          f"(2) *Budget recommendation*: a Q-learning agent {C('qlearn')} with a state made of income, fixed and variable expenses and savings goal, rewards of +1 and -1, alpha 0.1, gamma 0.95 and epsilon decaying from 0.995 to 0.01 over 300 episodes, producing a \"High\", \"Moderate\" or \"Low\" savings recommendation. "
          f"(3) *Savings forecasting*: an LSTM {C('lstm')} with 64 and 32 units trained on 12-month sequences of a synthetic savings series (min-max scaling, trend features, 50 epochs). "
          f"(4) *Anomaly detection*: an Isolation Forest {C('iforest')} with 300 trees, contamination 0.015 and savings and expense ratios as features. The modules are served through a Python back end (Flask or Streamlit) and a Streamlit interface."),
        P("**Evaluation and findings.** The classifier is reported at accuracy 92.3 %, precision 90.8 %, recall 91.5 % and F1 91.1 %, better than rule-based keyword matching (a stated +42 % accuracy) and than Random Forest and SVM baselines; "
          "the Q-learning reward rises and converges after about 150 to 200 of 300 episodes; the LSTM reaches RMSE 137.2, MAE 89.5 and R-squared 0.63; the Isolation Forest reaches precision 0.93, recall 0.94, F1 0.94 and R-squared 0.87. "
          "A comparison table claims improvements of 42 % (categorisation accuracy), 31 % (budget efficiency), 29 % (RMSE reduction against ARIMA) and 27 % (anomaly recall against manual review)."),
        P("**Strengths and limits.** The paper sets out a clear modular architecture, states its hyper-parameters, and covers the whole chain from raw text to alerts. For the purpose of this project its limits are that the data are synthetic or collected by the authors and not released, "
          "so none of the numbers can be reproduced; that the reinforcement-learning state and action spaces are only sketched and its evaluation is a reward curve rather than a measured saving; that the LSTM errors have no stated units and the forecaster is trained on a synthetic series; "
          "that the anomaly detector is scored on injected outliers, which makes a high score easy; and that there is no deployed multi-user application, authentication or test suite. The forecasting section also calls an R-squared of 0.63 \"accuracy of 63 %\", which is a different quantity."),
        H3("2.2.2 Supporting papers read in full"),
        P(f"**To (arXiv:2601.08640, January 2026)** {C('to')} designs a mobile finance application, Mabu, for young adults with Alan Cooper's Goal-Directed Design and gamification. "
          "It uses interviews, a survey of respondents aged 18 to 30, a closed card sort with 10 participants and think-aloud and usability tests with 6 participants, and it quotes a 2023 UK test in which only 17 % of 18 to 24 year olds showed sufficient financial literacy. "
          "The paper contributes a design method and a usability study, not a model; it supports the claim that a finance app must serve personal goals and be easy to use, which shaped the dashboard and goals pages of this project."),
        P(f"**Theerthala (arXiv:2509.14180, September 2025)** {C('theerthala')} builds a 19,000-sample reasoning dataset that combines financial context with behavioural-finance studies and fine-tunes an 8-billion-parameter model on it; "
          "a blind study with language models as judges finds the model comparable to 14 to 32-billion-parameter baselines on factual accuracy, fluency and personalisation at about 80 % lower cost. "
          "It shows why advice has to be grounded in the user's goals and constraints. This project does not use a fine-tuned language model; its assistant computes answers from the user's own records, with an optional external model, and the paper's judgement protocol is not applied."),
        H3("2.2.3 What FINJARVIS takes from the base paper, and what it does not"),
        TAB("Relation of FINJARVIS to the base paper", ["Module", "Base paper [1]", "FINJARVIS (as built)", "Status"],
            [["Expense categorisation", "Fine-tuned BERT, 50 categories, SMOTE, 80/20 split", "TF-IDF (1-2-grams) + logistic regression, 11 categories + Other, 51 seed examples, retrain on correction", "Same task, much simpler model"],
             ["Budget recommendation", "Q-learning agent, 3 savings levels", "User-set monthly budgets, alerts at 75/90/100 %, rule-based advice, 6-component health score", "Replaced by rules"],
             ["Savings forecasting", "LSTM on 12-month synthetic savings", "Least-squares line through monthly expense totals, minimum 3 months", "Expenses, not savings; linear"],
             ["Anomaly detection", "Isolation Forest, contamination 0.015", "None (only the largest expense of a period is reported)", "Not built"],
             ["Interface", "Streamlit", "React + FastAPI, 13 pages, login, reports", "Extended"],
             ["Evidence", "Metrics on unreleased data", f"{F.PYTEST_PASSED} tests, probe set, backtest, simulation, latency", "Own measurements"]],
            widths=[1.2, 1.7, 2.3, 1.2], align=["l", "l", "l", "l"], size=9),
        P("FINJARVIS does not claim to match the base paper's accuracy figures: the data, the label set (11 against 50 categories) and the model all differ. "
          "It takes the paper's modular structure and pipeline order (categorise, budget, forecast, advise) and builds the lightest version that runs on an ordinary laptop with a short seed list, then measures how far it goes."),
        H2("2.3 Expense Categorisation"),
        P(f"Classifying transaction descriptions is a short-text classification problem. Classical systems weight words by TF-IDF {C('tfidf')} and feed them to a linear classifier from a standard library {C('sklearn')}; they are fast, need little data and can be inspected word by word. "
          f"Pre-trained transformers such as BERT {C('bert')} read each word in the context of the whole text and are fine-tuned on labelled examples; FinBERT continues the pre-training on financial text {C('finbert')}. "
          f"The base paper uses BERT and reports that it beats keyword matching and classical learners {C('base')}. The price is a labelled corpus large enough to fine-tune (the base paper uses 50 categories) and the computing power to train and serve it."),
        P("FINJARVIS takes the classical route because no labelled corpus of Indian bank and UPI narrations is available and the product must run on one CPU. "
          f"It keeps the keyword table of the first Streamlit version as a fallback. The cost is measured in Chapter 8: {c['tfidf_lr']['accuracy_by_tier']['A'] * 100:.0f} % accuracy on text that resembles the seed phrases and {c['tfidf_lr']['accuracy_by_tier']['C'] * 100:.1f} % on unseen merchants."),
        H2("2.4 Expense Forecasting"),
        P(f"Forecasting a person's monthly spending is a short time series problem: after six months there are six numbers. The forecasting literature compares simple methods (last value, mean, trend, exponential smoothing) with ARIMA-style models and with neural networks {C('fpp')}. "
          f"A well-known comparison of statistical and machine-learning forecasts over many series found that simple statistical methods were at least as accurate as complex learners and far cheaper {C('makri')}; "
          f"the same literature warns that percentage errors misbehave when values are small and recommends reporting several error measures {C('hk')}. "
          f"The base paper uses an LSTM {C('lstm')} on a synthetic savings series and reports an R-squared of 0.63 {C('base')}; FinSenseAI combines XGBoost and LSTM with SHAP explanations but states in its results section that the models are intended to be evaluated and gives no numbers {C('finsense')}."),
        P(f"FINJARVIS fits a straight line to the monthly totals, which is the simplest trend model, and refuses to predict with fewer than three months. Because the literature suggests that simple baselines are strong, the project compares the line with three baselines (mean of all history, mean of the last three months, last value) "
          f"on the demo account (MAPE {bt['mape_pct']['linear_trend (app)']:.1f} % for the line, {bt['mape_pct']['mean_of_all']:.1f} % for the mean) and on 2,000 simulated users per setting; the result is given in Chapter 8."),
        H2("2.5 Anomaly Detection and Budget Recommendation"),
        P(f"The Isolation Forest isolates unusual points by random partitioning: points that need few splits get high anomaly scores {C('iforest')}, and no labelled fraud is needed. "
          f"The base paper sets the expected share of anomalies (contamination) to 0.015 {C('base')}; the leakage paper pairs the forest with K-Means clustering of small recurring purchases {C('leak')}. "
          f"Budget recommendation by Q-learning {C('qlearn')} treats the budget level as an action chosen to maximise a reward, which needs a well-defined reward and many episodes of data. "
          "FINJARVIS builds neither: it reports the single largest expense of a period, lets the user set budgets, and raises alerts when a budget reaches 75, 90 and 100 %, with a rule-based suggestion to trim the top categories by 10 to 15 %. These are stated as gaps against objectives 4 and 5."),
        H2("2.6 Recent Personal-Finance Systems"),
        P(f"The remaining batch papers are close in aim. FinSenseAI {C('finsense')} (IJISRT, July 2026) predicts future expenses with an XGBoost-LSTM ensemble explained by SHAP on a transaction table of unstated size; its results section lists RMSE, MAE, MAPE and R-squared as metrics without reporting values. "
          f"The leakage-detection paper {C('leak')} (IJRASET, April 2026) uses an Isolation Forest and K-Means to flag unexpected charges and group small purchases on synthetic data, and its abstract gives no metrics. "
          f"The IEEE title {C('s2')} and the 2026 platform paper {C('s3')} could not be read or located and are not discussed. "
          f"Financial-literacy work {C('lusardi')} supplies the motivation: planning and saving depend on seeing one's own money clearly."),
        H2("2.7 Datasets and Algorithms Used in Related Work and in This Project"),
        P(f"FINJARVIS uses no external data set. Its categoriser is trained on a seed list of {c['seed_examples']} short descriptions in {c['seed_categories']} categories (figure below). It is evaluated on a probe set of {c['probe_examples']} descriptions written by the team before scoring, and the forecast on the six months of the fictional demo account and on simulated users. "
          "The algorithms used, with the source of each idea, are listed below."),
        FIG(F.fig("f13_seed_distribution.png"), "The 51-example seed list on which the shipped categoriser is trained (examples per category).", 4.9),
        TAB("Algorithms used in FINJARVIS and where each comes from", ["Algorithm", "Used for", "Source of the idea"],
            [["TF-IDF word 1-2-grams + multinomial logistic regression", "Expense categoriser", f"Term weighting {C('tfidf')}; scikit-learn {C('sklearn')}"],
             ["Keyword table (substring match)", "Fallback categoriser; comparison baseline", "Original Streamlit version of the product"],
             ["Least-squares line through monthly totals", "Next-month and per-category forecast", f"Trend extrapolation {C('fpp')}"],
             ["Mean of history, mean of last 3, last value", "Baselines in the forecast study", f"Simple baselines {C('fpp')}, {C('makri')}"],
             ["Weighted sum of six clipped component scores", "Financial health score", "Developed in this project; weights chosen by the team"],
             ["Rule routing over five intents", "AI assistant", "Developed in this project"],
             ["bcrypt password hashing; HMAC-SHA256 signed tokens", "Accounts and sessions", f"{C('bcrypt')}"],
             ["Cross-validation style probes (leave-one-out, probe tiers)", "Evaluating the categoriser", f"{C('kohavi')}"]],
            widths=[2.4, 1.8, 2.2], align=["l", "l", "l"], size=9.5),
        H2("2.8 Strengths and Limitations of Existing Research"),
        TAB("Comparison of the surveyed work", ["Work", "Approach", "Data", "Reported result", "Limitation"], lit_rows(),
            widths=[0.9, 1.7, 0.95, 1.5, 1.35], align=["l", "l", "l", "l", "l"], size=8),
        P("**Strengths.** The literature establishes that transaction text can be classified automatically with a pre-trained language model, that unsupervised detectors can flag unusual spending without labelled fraud, "
          "that forecasts and recommendations are more useful when explained, that financial advice must be personalised, and that a finance application must be designed around the user's goals."),
        P("**Limitations.** Most sources evaluate on synthetic or private data; two report no numeric result at all; none releases its data; none describes a tested, multi-user web service; and none checks how a simple trend or a small classifier behaves on inputs it has not seen. "
          "Some report percentage improvements over weak baselines (manual review, rule-based matching) rather than over a plain average or a keyword table, and none reports response time, defects or tests of an operating service."),
        H2("2.9 Research Gap"),
        P(lit.GAP),
        P("The project's answer has three parts. It builds the platform as one running, tested system with accounts and a demo. "
          "It builds the simplest inspectable version of the base paper's categorisation and forecasting modules and a rule-based version of its advice, and says plainly that anomaly detection and reinforcement learning are not built. "
          f"And it measures the weak points: the categoriser scores {c['tfidf_lr']['accuracy_by_tier']['C'] * 100:.1f} % on unseen merchants, learning from corrections helps repeat merchants but barely helps new ones, and a linear trend needs about seven months of history to beat a mean."),
    ]
