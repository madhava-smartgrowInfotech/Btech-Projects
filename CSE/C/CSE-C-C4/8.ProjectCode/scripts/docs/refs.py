"""
Reference list for the QuantPulse (CSE-C-C4) documents, IEEE style, numbered by list order (REFS[0] is [1]).

Content modules cite entries through CITE['key'] (a number).  REF_NOTES records how each entry was checked: Crossref REST API
(title, authors, venue, volume, pages read this run), arXiv / PMLR record pages, the base-paper PDF, or the archived PDFs in this batch.
Entries 2-5 are the batch literature survey (5.LITERATURE SURVEY.docx): their bibliographic records were verified with Crossref, but no
abstract or full text was available, so their results are never quoted.  Entry 2 has no author list in Crossref and is listed by title.
Italics use *...* markup (rendered by kit.add_runs).
"""

KEYS = [
    "base", "s_hybrid", "s_llm", "s_multimodal", "s_text",
    "zhang", "liao", "deng", "dietterich", "ilse", "fnspid",
    "lstm", "transformer", "fedavg", "fedml", "finbert_tone", "finbert",
    "fischer", "sezer", "lim", "tetlock", "bollen", "emh",
    "prophet", "rf", "svr", "box",
    "adam", "adamw", "tf", "pytorch", "sklearn",
    "yahoo", "newsapi", "hf_finbert_tone",
]

REFS = [
    # 1 - base paper
    "Y. Nejatbakhsh and M. Aliasgari, \"Enhancing stock market prediction with hybrid deep learning: Integrating LSTM, transformer attention, "
    "federated learning, and sentiment analysis,\" *IEEE Access*, vol. 14, pp. 3926-3942, 2026, doi: 10.1109/ACCESS.2025.3649668.",
    # 2-5 - the batch literature survey
    "\"A hybrid artificial intelligence model for stock market prediction using financial news, social media sentiment, and corporate performance indicators,\" "
    "*Revista Electronica de Veterinaria*, vol. 25, no. 1, 2024 (as listed in the batch literature survey; authors not available in Crossref).",
    "G. Officioso, G. Sperli and A. Vignali, \"Financial news sentiment meets market data: A large language model-based approach to stock price prediction,\" "
    "*Inf. Sci.*, vol. 754, Art. no. 123711, Oct. 2026, doi: 10.1016/j.ins.2026.123711.",
    "H. Chang, \"Multimodal stock price prediction in the Chinese market via financial sentiment analysis and feature fusion,\" in *Proc. 3rd Int. Conf. "
    "Data Anal. Mach. Learn.*, SCITEPRESS, 2025, pp. 211-216, doi: 10.5220/0014761600004818.",
    "P. Xiao, \"Stock market prediction based on financial news, text data mining, and investor sentiment analysis,\" *Int. J. Inf. Syst. Model. Des.*, "
    "vol. 15, no. 1, pp. 1-13, 2024, doi: 10.4018/ijismd.361593.",
    # 6-11 - multiple-instance learning, news fusion, news data
    "X. Zhang, S. Qu, J. Huang, B. Fang and P. Yu, \"Stock market prediction via multi-source multiple instance learning,\" *IEEE Access*, vol. 6, "
    "pp. 50720-50728, 2018, doi: 10.1109/ACCESS.2018.2869735.",
    "P.-J. Liao, H.-S. Lee, Y.-F. Cheng, L.-W. Chen, H.-y. Lee and H.-M. Wang, \"Generalized stock price prediction for multiple stocks combined with news fusion,\" "
    "arXiv:2603.19286, Mar. 2026.",
    "Y. Deng and S. M. Yiu, \"Deep multiple instance learning for forecasting stock trends using financial news,\" in *Artificial Intelligence Trends*, "
    "AIRCC, 2022, pp. 95-111, doi: 10.5121/csit.2022.121008 (arXiv:2206.14452).",
    "T. G. Dietterich, R. H. Lathrop and T. Lozano-Perez, \"Solving the multiple instance problem with axis-parallel rectangles,\" *Artif. Intell.*, "
    "vol. 89, no. 1-2, pp. 31-71, Jan. 1997, doi: 10.1016/S0004-3702(96)00034-3.",
    "M. Ilse, J. M. Tomczak and M. Welling, \"Attention-based deep multiple instance learning,\" in *Proc. 35th Int. Conf. Mach. Learn. (ICML)*, "
    "*PMLR*, vol. 80, 2018, pp. 2127-2136, arXiv:1802.04712.",
    "Z. Dong, X. Fan and Z. Peng, \"FNSPID: A comprehensive financial news dataset in time series,\" in *Proc. 30th ACM SIGKDD Conf. Knowl. Discovery "
    "Data Mining (KDD)*, Barcelona, Spain, Aug. 2024, pp. 4918-4927, doi: 10.1145/3637528.3671629.",
    # 12-17 - models used by the base paper and by QuantPulse
    "S. Hochreiter and J. Schmidhuber, \"Long short-term memory,\" *Neural Comput.*, vol. 9, no. 8, pp. 1735-1780, Nov. 1997, doi: 10.1162/neco.1997.9.8.1735.",
    "A. Vaswani *et al.*, \"Attention is all you need,\" in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 30, 2017, pp. 5998-6008, arXiv:1706.03762.",
    "H. B. McMahan, E. Moore, D. Ramage, S. Hampson and B. A. y Arcas, \"Communication-efficient learning of deep networks from decentralized data,\" in "
    "*Proc. 20th Int. Conf. Artif. Intell. Statist. (AISTATS)*, *PMLR*, vol. 54, 2017, pp. 1273-1282, arXiv:1602.05629.",
    "Q. Yang, Y. Liu, T. Chen and Y. Tong, \"Federated machine learning: Concept and applications,\" *ACM Trans. Intell. Syst. Technol.*, vol. 10, no. 2, "
    "pp. 1-19, Jan. 2019, doi: 10.1145/3298981.",
    "Y. Yang, M. C. S. Uy and A. Huang, \"FinBERT: A pretrained language model for financial communications,\" arXiv:2006.08097, Jun. 2020.",
    "D. Araci, \"FinBERT: Financial sentiment analysis with pre-trained language models,\" arXiv:1908.10063, Aug. 2019.",
    # 18-23 - forecasting, news and markets
    "T. Fischer and C. Krauss, \"Deep learning with long short-term memory networks for financial market predictions,\" *Eur. J. Oper. Res.*, vol. 270, no. 2, "
    "pp. 654-669, Oct. 2018, doi: 10.1016/j.ejor.2017.11.054.",
    "O. B. Sezer, M. U. Gudelek and A. M. Ozbayoglu, \"Financial time series forecasting with deep learning: A systematic literature review: 2005-2019,\" "
    "*Appl. Soft Comput.*, vol. 90, Art. no. 106181, May 2020, doi: 10.1016/j.asoc.2020.106181.",
    "B. Lim and S. Zohren, \"Time-series forecasting with deep learning: A survey,\" *Phil. Trans. R. Soc. A*, vol. 379, no. 2194, Art. no. 20200209, Feb. 2021, "
    "doi: 10.1098/rsta.2020.0209.",
    "P. C. Tetlock, \"Giving content to investor sentiment: The role of media in the stock market,\" *J. Finance*, vol. 62, no. 3, pp. 1139-1168, Jun. 2007, "
    "doi: 10.1111/j.1540-6261.2007.01232.x.",
    "J. Bollen, H. Mao and X. Zeng, \"Twitter mood predicts the stock market,\" *J. Comput. Sci.*, vol. 2, no. 1, pp. 1-8, Mar. 2011, doi: 10.1016/j.jocs.2010.12.007.",
    "E. F. Fama, \"Efficient capital markets: A review of theory and empirical work,\" *J. Finance*, vol. 25, no. 2, pp. 383-417, May 1970, doi: 10.2307/2325486.",
    # 24-27 - baselines
    "S. J. Taylor and B. Letham, \"Forecasting at scale,\" *Amer. Statistician*, vol. 72, no. 1, pp. 37-45, 2018, doi: 10.1080/00031305.2017.1380080.",
    "L. Breiman, \"Random forests,\" *Mach. Learn.*, vol. 45, no. 1, pp. 5-32, Oct. 2001, doi: 10.1023/A:1010933404324.",
    "A. J. Smola and B. Scholkopf, \"A tutorial on support vector regression,\" *Statist. Comput.*, vol. 14, no. 3, pp. 199-222, Aug. 2004, "
    "doi: 10.1023/B:STCO.0000035301.49549.88.",
    "G. E. P. Box, G. M. Jenkins, G. C. Reinsel and G. M. Ljung, *Time Series Analysis: Forecasting and Control*, 5th ed. Hoboken, NJ, USA: Wiley, 2015.",
    # 28-32 - optimisation and software
    "D. P. Kingma and J. Ba, \"Adam: A method for stochastic optimization,\" arXiv:1412.6980, Dec. 2014.",
    "I. Loshchilov and F. Hutter, \"Decoupled weight decay regularization,\" arXiv:1711.05101, Nov. 2017.",
    "M. Abadi *et al.*, \"TensorFlow: Large-scale machine learning on heterogeneous distributed systems,\" arXiv:1603.04467, Mar. 2016.",
    "A. Paszke *et al.*, \"PyTorch: An imperative style, high-performance deep learning library,\" arXiv:1912.01703, Dec. 2019.",
    "F. Pedregosa *et al.*, \"Scikit-learn: Machine learning in Python,\" *J. Mach. Learn. Res.*, vol. 12, pp. 2825-2830, 2011.",
    # 33-35 - web resources
    "Yahoo Finance, \"Historical market data,\" accessed through the yfinance Python package, Oct. 2026. [Online]. Available: https://finance.yahoo.com/",
    "NewsAPI, \"News API: JSON API for live news and blog articles.\" [Online]. Available: https://newsapi.org/",
    "Y. Yang, \"finbert-tone: FinBERT fine-tuned for financial tone (positive / neutral / negative),\" Hugging Face model card yiyanghkust/finbert-tone. "
    "[Online]. Available: https://huggingface.co/yiyanghkust/finbert-tone",
]

assert len(KEYS) == len(REFS), (len(KEYS), len(REFS))
CITE = {k: i + 1 for i, k in enumerate(KEYS)}

REF_NOTES = {
    "base": "Read in full from Documentary/BASEPAPER_*.pdf (17 pages); Crossref 10.1109/ACCESS.2025.3649668 confirms title, authors Yousef Nejatbakhsh and Malihe Aliasgari, vol. 14, pp. 3926-3942, 2026.",
    "s_hybrid": "Batch survey item 2. Crossref lists the title, Revista Electronica de Veterinaria vol. 25 no. 1, 2024 (DOI prefix 10.69980/redvet), with no author list and no abstract. Authors and results NOT verified; never quoted for numbers.",
    "s_llm": "Batch survey item 3. Crossref 10.1016/j.ins.2026.123711: Giovanni Officioso, Giancarlo Sperli, Andrea Vignali; Information Sciences vol. 754, article 123711, Oct 2026. No abstract available, so only the title is used.",
    "s_multimodal": "Batch survey item 4. Crossref 10.5220/0014761600004818: Heming Chang; SCITEPRESS, pp. 211-216, 2025. No abstract available, so only the title is used.",
    "s_text": "Batch survey item 5. Crossref 10.4018/ijismd.361593: Panzhang Xiao; IJISMD vol. 15 no. 1, pp. 1-13, published 21 Nov 2024. No abstract available, so only the title is used.",
    "zhang": "Crossref 10.1109/ACCESS.2018.2869735 confirms authors and pages; method and numbers read from archived_base_papers/REFERENCE_PAPER_*.pdf (9 pages): Shanghai Composite Index, 2015 and 2016, 38,727 and 39,465 news articles, 6,163,056 Xueqiu posts, first 10 months train / last 2 months test; M-MI beats nMIL by 6.9 % and 9.2 % F1 and 6.7 % and 9.4 % accuracy (history day 1, lead day 1).",
    "liao": "arXiv abs page confirms six authors; text read from archived_base_papers/BASEPAPER_Generalized_*.pdf (22 pages): six Taiwan Stock Exchange stocks plus the US BigData23 set, 70/10/20 split, attentive pooling of daily news with stock-name queries; 7.11 % MAE reduction (0.1913 to 0.1777) reported for self-attentive pooling on normalised prices.",
    "deng": "Crossref 10.5121/csit.2022.121008 (Yiqi Deng, Siu Ming Yiu; pp. 95-111, 18 Jun 2022) and arXiv:2206.14452 abstract read: each trading day is a bag of news instances, bag-level label, S&P 500 directional forecast; no numbers quoted.",
    "dietterich": "Crossref 10.1016/s0004-3702(96)00034-3: Dietterich, Lathrop, Lozano-Perez; Artificial Intelligence vol. 89 no. 1-2, pp. 31-71, Jan 1997.",
    "ilse": "arXiv:1802.04712 (Maximilian Ilse, Jakub M. Tomczak, Max Welling) and PMLR page proceedings.mlr.press/v80/ilse18a.html: ICML 2018, pp. 2127-2136.",
    "fnspid": "Crossref 10.1145/3637528.3671629: Zihan Dong, Xinyu Fan, Zhiyuan Peng; KDD 2024, pp. 4918-4927. The news portion was read from the public mirror idleengine/financial-news-multisource (subset fnspid_news).",
    "lstm": "Crossref 10.1162/neco.1997.9.8.1735: Hochreiter and Schmidhuber, Neural Computation 9(8), 1735-1780.",
    "transformer": "arXiv:1706.03762 record read (eight authors); NeurIPS vol. 30 pages 5998-6008 are taken from the base paper's reference list [11], not re-fetched.",
    "fedavg": "arXiv:1602.05629 (journal-ref AISTATS 2017, JMLR W&CP vol. 54) and PMLR page v54/mcmahan17a: pp. 1273-1282.",
    "fedml": "Crossref 10.1145/3298981: Qiang Yang, Yang Liu, Tianjian Chen, Yongxin Tong; ACM TIST 10(2), 1-19, 28 Jan 2019.",
    "finbert_tone": "arXiv:2006.08097 record read: Yi Yang, Mark Christopher Siy UY, Allen Huang, 15 Jun 2020. This is the paper behind the yiyanghkust/finbert-tone model used in the sentiment module.",
    "finbert": "arXiv abs page 1908.10063 read: Araci, Dogu, 27 Aug 2019 (title: FinBERT: Financial Sentiment Analysis with Pre-trained Language Models). Cited by the base paper as its FinBERT reference.",
    "fischer": "Crossref 10.1016/j.ejor.2017.11.054: Fischer and Krauss, EJOR 270(2), 654-669, Oct 2018. Used only as the LSTM-for-financial-prediction reference; no numbers quoted.",
    "sezer": "Crossref 10.1016/j.asoc.2020.106181: Sezer, Gudelek, Ozbayoglu, Appl. Soft Comput. 90, article 106181, May 2020.",
    "lim": "Crossref 10.1098/rsta.2020.0209: Bryan Lim and Stefan Zohren, Phil. Trans. R. Soc. A 379(2194), 20200209, 15 Feb 2021.",
    "tetlock": "Crossref 10.1111/j.1540-6261.2007.01232.x: Paul C. Tetlock, J. Finance 62(3), 1139-1168, 2007. Cited for the idea that media content carries information about prices; no numbers quoted.",
    "bollen": "Crossref 10.1016/j.jocs.2010.12.007: Johan Bollen, Huina Mao, Xiaojun Zeng, J. Comput. Sci. 2(1), 1-8, Mar 2011.",
    "emh": "Crossref 10.2307/2325486: Eugene F. Fama, J. Finance 25(2), 383 onwards, May 1970 (end page 417 from the standard record, not in Crossref). Also cited as [1] in Zhang et al. 2018.",
    "prophet": "Crossref 10.1080/00031305.2017.1380080: Taylor and Letham, The American Statistician 72(1), 37-45, 2018.",
    "rf": "Crossref 10.1023/a:1010933404324: Breiman, Machine Learning 45(1), 5-32, Oct 2001.",
    "svr": "Crossref 10.1023/b:stco.0000035301.49549.88: Smola and Scholkopf, Statistics and Computing 14(3), 199-222, Aug 2004.",
    "box": "Textbook entry copied from the base paper's reference list [1]; not re-fetched.",
    "adam": "arXiv:1412.6980 record read: Diederik P. Kingma, Jimmy Ba.",
    "adamw": "arXiv:1711.05101 record read: Ilya Loshchilov, Frank Hutter (used by the MIL study's optimiser).",
    "tf": "arXiv abs page 1603.04467 read (40 authors; Abadi et al.), 14 Mar 2016. The product uses TensorFlow 2.16.2 / Keras.",
    "pytorch": "arXiv abs page 1912.01703 read (21 authors; Paszke et al.), 3 Dec 2019. Used for FinBERT-tone inference and the MIL study.",
    "sklearn": "JMLR 12:2825-2830, 2011; cited from the standard record, not re-fetched.",
    "yahoo": "Web resource; prices were downloaded through yfinance 1.7.0 (this run).",
    "newsapi": "Web resource named by the base paper (its reference [30]) and by backend/app/sentiment.py.",
    "hf_finbert_tone": "Model card of the checkpoint loaded by backend/app/sentiment.py and scripts/mil_features.py.",
}
for _k in KEYS:
    assert _k in REF_NOTES, _k
