"""Literature and framing data for the decks (Review 1, Review 2, final), the chapters and the IEEE paper.

Every literature fact traces to the base-paper PDF, the archived PDFs in this batch (Zhang 2018, Liao 2026), the arXiv abstract of Deng and Yiu,
or the entry notes in refs.py (REF_NOTES).  The four batch-survey items [2]-[5] have verified bibliographic records but no abstract could be
read, so they are never quoted for results.  Reference numbers match scripts/docs/refs.py (CITE keys).
Items quoted from the base paper's own related-work section are marked "(as reported in the base paper)".
"""
from . import facts as F
from .refs import CITE as R

BASE_PAPER_TITLE = "Enhancing Stock Market Prediction With Hybrid Deep Learning: Integrating LSTM, Transformer Attention, Federated Learning, and Sentiment Analysis"
BASE_PAPER_VENUE = "Y. Nejatbakhsh, M. Aliasgari - IEEE Access, vol. 14, 2026"

# [work, year, approach, finding / limitation]   (each cell <= 90 characters)
LIT_TABLE = [
    [f"Nejatbakhsh, Aliasgari [{R['base']}] (base paper)", "2026", "LSTM + multi-head attention + FinBERT-tone sentiment + simulated FedAvg; ten companies",
     "Average R2 0.91; baseline LSTM trend accuracy 65.36 %; sentiment limited to 30 days"],
    [f"Zhang et al. [{R['zhang']}]", "2018", "Multi-source MIL model: news events, Xueqiu sentiment, index data; Shanghai index",
     "F1 +6.9 % / +9.2 % over nMIL (2015 / 2016); one Chinese index, event extraction needed"],
    [f"Deng, Yiu [{R['deng']}]", "2022", "Each trading day is a bag of news instances, bag-level label; S&P 500 direction",
     "Reports better trend accuracy than baselines (abstract); news only, no price branch stated"],
    [f"Liao et al. [{R['liao']}]", "2026", "Attentive pooling of all daily news with stock-name queries; one model for many stocks",
     "7.11 % lower MAE (0.1913 to 0.1777) with pooling; six TWSE stocks plus BigData23"],
    [f"Officioso et al. [{R['s_llm']}]", "2026", "Large-language-model news sentiment combined with market data (title only)",
     "Batch survey item; abstract not available, results not quoted"],
    [f"Chang [{R['s_multimodal']}]", "2025", "Financial sentiment and feature fusion for Chinese-market prices (title only)",
     "Batch survey item; abstract not available, results not quoted"],
    [f"Xiao [{R['s_text']}]", "2024", "Financial news, text mining and investor sentiment for prediction (title only)",
     "Batch survey item; abstract not available, results not quoted"],
    [f"Batch item [{R['s_hybrid']}]", "2024", "Hybrid AI with news, social-media sentiment and corporate indicators (title only)",
     "Authors not in Crossref; abstract not available, results not quoted"],
    [f"Fischer, Krauss [{R['fischer']}]", "2018", "LSTM networks for financial market prediction (cited by the base paper for LSTM)",
     "LSTM suited to price sequences; used here only as the LSTM reference, no numbers quoted"],
    [f"Dong et al. (FNSPID) [{R['fnspid']}]", "2024", "Large public dataset of financial news aligned with stock prices",
     "Source of the real headlines in this project's offline MIL study"],
]

# [work, approach, data, reported result, limitation]  - short cells for the IEEE paper's TABLE I
PAPER_TABLE = [
    [f"Base paper [{R['base']}]", "LSTM + attention + FinBERT-tone + FedAvg", "10 tech stocks; 30-day news window", "Avg R2 0.91; LSTM trend 65.36 %", "30 days of news; FL simulated"],
    [f"Zhang et al. [{R['zhang']}]", "Multi-source MIL (events, sentiment, index)", "Shanghai index 2015-16; 38,727 / 39,465 news", "F1 +6.9 % / +9.2 % vs nMIL", "One index; event extraction"],
    [f"Deng, Yiu [{R['deng']}]", "Day = bag of news instances", "S&P 500, financial news", "Better trend accuracy (abstract)", "News only"],
    [f"Liao et al. [{R['liao']}]", "Attentive news pooling, one model", "6 TWSE stocks + BigData23", "MAE -7.11 % (0.1913 to 0.1777)", "Price regression, not direction"],
    [f"Fischer, Krauss [{R['fischer']}]", "LSTM for financial prediction", "Cited via base paper", "Not quoted", "Price data only"],
    [f"Survey items [{R['s_hybrid']}]-[{R['s_text']}]", "News / sentiment fusion (titles)", "Not verified", "Not quoted", "No abstract read"],
]

# the six objectives of the batch (6.OBJECTIVES&PROBLEM STATEMENT.docx), shortened for status tables
OBJECTIVES = [
    "Collect historical prices together with financial news and social-media text for the target stocks",
    "Preprocess and align the multi-source data into daily instances grouped per trading day",
    "Represent each trading day as a bag of news instances under the Multiple Instance Learning formulation",
    "Train a hybrid model combining sequence learning over prices with attention over news content",
    "Predict directional movement and evaluate with accuracy, precision, recall and F1-score",
    "Compare multi-source performance against a price-only baseline",
]

# the project description in the batch documentary (Documentary/Batch_C04_Stock_Market_Prediction_MIL.docx)
OBJECTIVES_DOC = [
    "Combine historical stock prices, financial news and social-media information",
    "Clean and organise the collected data so a machine-learning model can use it",
    "Use Multiple Instance Learning to find patterns related to stock price movements",
    "Predict whether a stock is likely to increase or decrease",
    "Implement in Python (Pandas, NumPy), serve through Flask, store in MySQL, plot with Matplotlib",
]

PROBLEM_STATEMENT = [
    "Price-only models miss the news and sentiment that move markets",
    "Labelling each news article individually is impractical and noisy",
    "Financial data is volatile and non-stationary, so models degrade quickly",
    "Predictions without explanation are not actionable for an investor",
    "Need: a prediction model that fuses price history with news and sentiment under a multiple-instance formulation",
]

EXISTING_SYSTEM = [
    "Statistical and classical models (ARIMA, SARIMAX, Prophet, random forest, SVR) forecast from price history alone [" + str(R["box"]) + "], [" + str(R["prophet"]) + "], [" + str(R["rf"]) + "], [" + str(R["svr"]) + "]",
    "LSTM models capture temporal dependence in prices [" + str(R["lstm"]) + "], [" + str(R["fischer"]) + "]; the base paper adds attention, FinBERT-tone sentiment and simulated federated averaging [" + str(R["base"]) + "]",
    "Multi-source multiple-instance models treat news events as instances of a day-level bag [" + str(R["zhang"]) + "], [" + str(R["deng"]) + "]",
    "Attentive pooling filters a day's news before fusing it with prices [" + str(R["liao"]) + "]",
    "News-sentiment features are usually one averaged score per day, from a recent window of headlines [" + str(R["base"]) + "]",
]

LIMITATIONS_OF_EXISTING = [
    "Price-only forecasters ignore the news and opinion that move prices",
    "The base paper's sentiment experiments cover only 30 days because the news API returns a month of history [" + str(R["base"]) + "]",
    "The base paper's federated learning is a single-process simulation, and its hybrid results rest on a one-month window [" + str(R["base"]) + "]",
    "The multiple-instance stock models surveyed use event extraction for one Chinese index [" + str(R["zhang"]) + "] or financial news alone [" + str(R["deng"]) + "]",
    "Several surveyed systems are known to us by title only; their results could not be verified [" + str(R["s_hybrid"]) + "]-[" + str(R["s_text"]) + "]",
]

GAPS = [
    "The base paper averages a day's headlines into one number; it does not treat the day's news as a bag of instances with only a bag-level label",
    "As far as their descriptions show, the day-bag multiple-instance models [" + str(R["deng"]) + "], [" + str(R["zhang"]) + "] are not paired with an LSTM price branch and multi-head attention as in the base paper",
    "Sentiment is tested over a 30-day window only in the base paper; archived multi-year headline data are not used there [" + str(R["base"]) + "], [" + str(R["fnspid"]) + "]",
    "Reported gains are mostly price-level errors; a direction metric with precision, recall and F1 against a price-only baseline is the project's stated objective",
    "Evaluation against a naive no-change forecast is rarely reported next to R2, although a level forecast one step ahead can score a high R2 by tracking the last price",
]
