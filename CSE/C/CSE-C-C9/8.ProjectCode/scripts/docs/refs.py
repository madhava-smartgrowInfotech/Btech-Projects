"""
IEEE-style reference list for FinSight AI.

Every entry is either (a) taken from the reference list of the base paper (checked against the PDF in
Documentary/), (b) read from the PDFs in archived_base_papers/, (c) verified by web search (marked in
the lit notes), (d) a standard, well-known publication, or (e) a title/year pair recorded in the batch
literature survey whose authors could not be verified (flagged "not independently verified"; never cited
in the paper or in factual claims).

Use keys, not numbers:   n("base", "shap")  ->  "[1], [14]"      num("base") -> 1
"""

_R = [
    ("base", "Y. Kim and E. J. Sun, \"An explainable machine learning framework for organizational financial distress detection: Evidence from Korean hospital panel data,\" IEEE Access, vol. 14, pp. 100337-100350, 2026, doi: 10.1109/ACCESS.2026.3709346."),
    ("abid", "A. Abid, \"Forecasting sovereign credit risk amidst a political crisis: A machine learning and deep learning approach,\" J. Risk Financial Manag., vol. 18, no. 6, Art. no. 300, Jun. 2025, doi: 10.3390/jrfm18060300."),
    ("maurino", "A. Maurino, \"How data quality affects machine learning models for credit risk assessment,\" in Proc. Workshop AI Data Sci. Digit. Finance, held with ACM Int. Conf. AI Finance (ICAIF), Singapore, 2025."),
    ("zhang", "H. Zhang, J. Xu, J. He, and X. Fang, \"Privacy-preserving credit risk prediction with alternative data,\" arXiv:2606.10333, Jun. 2026."),
    ("altman", "E. I. Altman, \"Financial ratios, discriminant analysis and the prediction of corporate bankruptcy,\" J. Finance, vol. 23, no. 4, pp. 589-609, Sep. 1968."),
    ("ohlson", "J. A. Ohlson, \"Financial ratios and the probabilistic prediction of bankruptcy,\" J. Accounting Res., vol. 18, no. 1, pp. 109-131, 1980."),
    ("breiman", "L. Breiman, \"Random forests,\" Mach. Learn., vol. 45, no. 1, pp. 5-32, 2001."),
    ("friedman", "J. H. Friedman, \"Greedy function approximation: A gradient boosting machine,\" Ann. Statist., vol. 29, no. 5, pp. 1189-1232, Oct. 2001."),
    ("xgboost", "T. Chen and C. Guestrin, \"XGBoost: A scalable tree boosting system,\" in Proc. 22nd ACM SIGKDD Int. Conf. Knowl. Discovery Data Mining, Aug. 2016, pp. 785-794."),
    ("barboza", "F. Barboza, H. Kimura, and E. Altman, \"Machine learning models and bankruptcy prediction,\" Expert Syst. Appl., vol. 83, pp. 405-417, Oct. 2017."),
    ("zieba", "M. Zieba, S. K. Tomczak, and J. M. Tomczak, \"Ensemble boosted trees with synthetic features generation in application to bankruptcy prediction,\" Expert Syst. Appl., vol. 58, pp. 93-101, Oct. 2016."),
    ("moscatelli", "M. Moscatelli, F. Parlapiano, S. Narizzano, and G. Viggiano, \"Corporate default forecasting with machine learning,\" Expert Syst. Appl., vol. 161, Art. no. 113567, Dec. 2020."),
    ("mai", "F. Mai, S. Tian, C. Lee, and L. Ma, \"Deep learning models for bankruptcy prediction using textual disclosures,\" Eur. J. Oper. Res., vol. 272, no. 2, pp. 743-758, 2019."),
    ("shap", "S. M. Lundberg and S.-I. Lee, \"A unified approach to interpreting model predictions,\" in Proc. Adv. Neural Inf. Process. Syst., vol. 30, 2017, pp. 4765-4774."),
    ("treeshap", "S. M. Lundberg et al., \"From local explanations to global understanding with explainable AI for trees,\" Nature Mach. Intell., vol. 2, no. 1, pp. 56-67, Jan. 2020."),
    ("lime", "M. T. Ribeiro, S. Singh, and C. Guestrin, \"'Why should I trust you?': Explaining the predictions of any classifier,\" in Proc. 22nd ACM SIGKDD Int. Conf. Knowl. Discovery Data Mining, 2016, pp. 1135-1144."),
    ("bussmann", "N. Bussmann, P. Giudici, D. Marinelli, and J. Papenbrock, \"Explainable machine learning in credit risk management,\" Comput. Econ., vol. 57, no. 1, pp. 203-216, Jan. 2021."),
    ("gramegna", "A. Gramegna and P. Giudici, \"SHAP and LIME: An evaluation of discriminative power in credit risk,\" Frontiers Artif. Intell., vol. 4, Art. no. 752558, Sep. 2021."),
    ("cerneviciene", "J. Cerneviciene and A. Kabasinskas, \"Explainable artificial intelligence (XAI) in finance: A systematic literature review,\" Artif. Intell. Rev., vol. 57, no. 8, pp. 1-80, Jul. 2024."),
    ("arrieta", "A. Barredo Arrieta et al., \"Explainable artificial intelligence (XAI): Concepts, taxonomies, opportunities and challenges toward responsible AI,\" Inf. Fusion, vol. 58, pp. 82-115, Jun. 2020."),
    ("doshi", "F. Doshi-Velez and B. Kim, \"Towards a rigorous science of interpretable machine learning,\" arXiv:1702.08608, 2017."),
    ("molnar", "C. Molnar, G. Casalicchio, and B. Bischl, \"Interpretable machine learning - A brief history, state-of-the-art and challenges,\" in Proc. ECML PKDD Workshops, 2020, pp. 417-431."),
    ("grinsztajn", "L. Grinsztajn, E. Oyallon, and G. Varoquaux, \"Why do tree-based models still outperform deep learning on typical tabular data?\" in Proc. Adv. Neural Inf. Process. Syst., 2022, pp. 507-520."),
    ("sklearn", "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825-2830, 2011."),
    ("esl", "T. Hastie, R. Tibshirani, and J. Friedman, The Elements of Statistical Learning: Data Mining, Inference, and Prediction, 2nd ed. New York, NY, USA: Springer, 2009."),
    ("stone", "M. Stone, \"Cross-validatory choice and assessment of statistical predictions,\" J. Roy. Stat. Soc., Ser. B, vol. 36, no. 2, pp. 111-133, 1974."),
    ("hosmer", "D. W. Hosmer, S. Lemeshow, and R. X. Sturdivant, Applied Logistic Regression, 3rd ed. Hoboken, NJ, USA: Wiley, 2013."),
    ("fawcett", "T. Fawcett, \"An introduction to ROC analysis,\" Pattern Recognit. Lett., vol. 27, no. 8, pp. 861-874, Jun. 2006."),
    ("hanley", "J. A. Hanley and B. J. McNeil, \"The meaning and use of the area under a receiver operating characteristic (ROC) curve,\" Radiology, vol. 143, no. 1, pp. 29-36, 1982."),
    ("delong", "E. R. DeLong, D. M. DeLong, and D. L. Clarke-Pearson, \"Comparing the areas under two or more correlated receiver operating characteristic curves: A nonparametric approach,\" Biometrics, vol. 44, no. 3, pp. 837-845, Sep. 1988."),
    ("kohavi", "R. Kohavi, \"Scaling up the accuracy of Naive-Bayes classifiers: A decision-tree hybrid,\" in Proc. 2nd Int. Conf. Knowl. Discovery Data Mining (KDD), 1996, pp. 202-207."),
    ("uci", "UCI Machine Learning Repository, \"Adult (Census Income) data set.\" [Online]. Available: https://archive.ics.uci.edu/dataset/20/census+income"),
    ("winters", "P. R. Winters, \"Forecasting sales by exponentially weighted moving averages,\" Manage. Sci., vol. 6, no. 3, pp. 324-342, Apr. 1960."),
    ("holt", "C. C. Holt, \"Forecasting seasonals and trends by exponentially weighted moving averages,\" Int. J. Forecasting, vol. 20, no. 1, pp. 5-10, 2004."),
    ("hyndman06", "R. J. Hyndman and A. B. Koehler, \"Another look at measures of forecast accuracy,\" Int. J. Forecasting, vol. 22, no. 4, pp. 679-688, 2006."),
    ("hyndmanbook", "R. J. Hyndman and G. Athanasopoulos, Forecasting: Principles and Practice, 3rd ed. Melbourne, Australia: OTexts, 2021."),
    ("guo", "C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, \"On calibration of modern neural networks,\" in Proc. Int. Conf. Mach. Learn. (ICML), 2017, pp. 1321-1330."),
    ("niculescu", "A. Niculescu-Mizil and R. Caruana, \"Predicting good probabilities with supervised learning,\" in Proc. 22nd Int. Conf. Mach. Learn. (ICML), 2005, pp. 625-632."),
    ("hardt", "M. Hardt, E. Price, and N. Srebro, \"Equality of opportunity in supervised learning,\" in Proc. Adv. Neural Inf. Process. Syst., vol. 29, 2016, pp. 3315-3323."),
    ("mehrabi", "N. Mehrabi, F. Morstatter, N. Saxena, K. Lerman, and A. Galstyan, \"A survey on bias and fairness in machine learning,\" ACM Comput. Surv., vol. 54, no. 6, Art. no. 115, 2021."),
    ("statsmodels", "S. Seabold and J. Perktold, \"Statsmodels: Econometric and statistical modeling with Python,\" in Proc. 9th Python Sci. Conf. (SciPy), 2010, pp. 92-96."),
    ("flask", "Pallets Projects, \"Flask: Web development, one drop at a time.\" [Online]. Available: https://flask.palletsprojects.com"),
    ("react", "Meta Platforms, Inc., \"React: The library for web and native user interfaces.\" [Online]. Available: https://react.dev"),
    ("vite", "Vite contributors, \"Vite: Next generation frontend tooling.\" [Online]. Available: https://vite.dev"),
    ("survey1", "\"Credit and financial cycle synchronization: Impact on sovereign credit risk,\" 2025 (entry recorded in the batch literature survey; not independently verified)."),
    ("survey2", "\"Financial and credit risk research,\" 2024 (entry recorded in the batch literature survey; not independently verified)."),
    ("survey3", "\"Design of a multimodal credit risk forecasting system for financial text analysis,\" in Proc. 2nd Int. Symp. Integr. Circuit Design Integr. Syst., 2025 (entry recorded in the batch literature survey; not independently verified)."),
]

REFS = [t for _, t in _R]
KEYS = [k for k, _ in _R]
TEXT = dict(_R)
VERIFIED_KEYS = [k for k in KEYS if not k.startswith("survey")]


def num(key):
    return KEYS.index(key) + 1


def n(*keys):
    """Citation string for reference keys, e.g. n('base', 'shap') -> '[1], [14]'."""
    return ", ".join(f"[{num(k)}]" for k in keys)
