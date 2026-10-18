"""
Reference list (IEEE style). Every entry was checked against a source during this run:
 - [1] full text of the base paper (Documentary/BASEPAPER_*.pdf);
 - [2] [3] [4] publisher / indexing pages (Europe PMC, Frontiers, IIETA) for authors, venue, year and the quoted results;
 - [8] [11] [12] [14] publisher / repository records found by web search;
 - [7] [10] [15] [16] [17] [18] [9] as listed in the reference list of the base paper [1];
 - [13] [20] standard, long-established citations (Breiman 2001, Friedman 2001).
Results quoted from a paper are only those that were read on its page (see ch2.LIT_TABLE).

Three papers named in the batch's own literature-survey file (5.LITERATURE SURVEY.docx) could not be located
by a title search and are therefore NOT cited or described: "Explainable Machine Learning for Telecom Customer Churn
Prediction and Actionable Retention Strategies", "A Novel SHAP-Guided Bayesian Optimization Method for Telecom
Customer Churn Prediction and Retention" and "Enhanced Customer Retention: Deep Learning-Based Churn Prediction for Telecom Industry".
"""

BASE = ("S.-V. Oprea and A. Bara, \"Explaining customer churn through unified perturbation-based XAI soft computing,\" "
        "IEEE Access, vol. 14, pp. 24460-24478, 2026, doi: 10.1109/ACCESS.2026.3663648.")

REF_BY_KEY = {
    "oprea": BASE,
    "sikri": ("A. Sikri, R. Jameel, S. M. Idrees and H. Kaur, \"Enhancing customer retention in telecom industry with machine learning "
              "driven churn prediction,\" Sci. Rep., vol. 14, no. 1, 2024, doi: 10.1038/s41598-024-63750-0."),
    "elattar": ("A. El Attar and M. El-Hajj, \"Explainable AI-driven customer churn prediction: a multi-model ensemble approach with "
                "SHAP-based feature analysis,\" Front. Artif. Intell., vol. 9, Feb. 2026, doi: 10.3389/frai.2026.1748799."),
    "rasool": ("H. A. Rasool, K. K. Aljawaheri and A. A. M. Karram, \"Explainable customer churn prediction in telecom using ensemble "
               "learning and SHAP analysis,\" Math. Model. Eng. Probl., pp. 4373-4386, Dec. 2025, doi: 10.18280/mmep.121226."),
    "ahmad": ("A. K. Ahmad, A. Jafar and K. Aljoumaa, \"Customer churn prediction in telecom using machine learning in big data platform,\" "
              "J. Big Data, vol. 6, no. 1, Mar. 2019, doi: 10.1186/s40537-019-0191-6."),
    "vafeiadis": ("T. Vafeiadis, K. I. Diamantaras, G. Sarigiannidis and K. Ch. Chatzisavvas, \"A comparison of machine learning techniques "
                  "for customer churn prediction,\" Simul. Model. Pract. Theory, vol. 55, 2015."),
    "lundberg": "S. M. Lundberg and S.-I. Lee, \"A unified approach to interpreting model predictions,\" in Proc. Adv. Neural Inf. Process. Syst. (NeurIPS), vol. 30, 2017.",
    "ribeiro": ("M. T. Ribeiro, S. Singh and C. Guestrin, \"'Why should I trust you?': Explaining the predictions of any classifier,\" in Proc. 22nd ACM SIGKDD "
                "Int. Conf. Knowl. Discovery Data Mining, 2016, pp. 1135-1144, doi: 10.1145/2939672.2939778."),
    "slack": ("D. Slack, S. Hilgard, E. Jia, S. Singh and H. Lakkaraju, \"Fooling LIME and SHAP: Adversarial attacks on post hoc explanation methods,\" "
              "in Proc. AAAI/ACM Conf. AI, Ethics, Soc., 2020, doi: 10.1145/3375627.3375830."),
    "treeshap": ("S. M. Lundberg et al., \"From local explanations to global understanding with explainable AI for trees,\" Nature Mach. Intell., "
                 "vol. 2, no. 1, pp. 56-67, Jan. 2020, doi: 10.1038/s42256-019-0138-9."),
    "smote": ("N. V. Chawla, K. W. Bowyer, L. O. Hall and W. P. Kegelmeyer, \"SMOTE: Synthetic minority over-sampling technique,\" "
              "J. Artif. Intell. Res., vol. 16, pp. 321-357, 2002, doi: 10.1613/jair.953."),
    "hegarcia": "H. He and E. A. Garcia, \"Learning from imbalanced data,\" IEEE Trans. Knowl. Data Eng., vol. 21, no. 9, pp. 1263-1284, Sep. 2009.",
    "breiman": "L. Breiman, \"Random forests,\" Mach. Learn., vol. 45, no. 1, pp. 5-32, Oct. 2001, doi: 10.1023/A:1010933404324.",
    "sklearn": "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825-2830, 2011.",
    "leung": ("C. K. Leung, A. G. M. Pazdor and J. Souza, \"Explainable artificial intelligence for data science on customer churn,\" in Proc. IEEE 8th Int. "
              "Conf. Data Sci. Adv. Anal. (DSAA), Oct. 2021, pp. 1-10, doi: 10.1109/DSAA53316.2021.9564166."),
    "mohajon": ("J. Mohajon and A. S. Mohammad Arif, \"Churn prediction with explainability for the customers of telecom industry,\" in Proc. Int. Conf. "
                "Inf. Commun. Technol. Sustain. Develop. (ICICT4SD), Sep. 2023, pp. 179-183, doi: 10.1109/ICICT4SD59951.2023.10303395."),
    "wang": ("D. Y. C. Wang, L. A. Jordanger and J. C.-W. Lin, \"Explainability of leverage points exploration for customer churn prediction,\" in Proc. "
             "IEEE Int. Conf. Big Data (BigData), Dec. 2023, pp. 5997-6004, doi: 10.1109/BigData59044.2023.10386857."),
    "szelag": ("M. Szelag and R. Slowinski, \"Explaining and predicting customer churn by monotonic rules induced from ordinal data,\" "
               "Eur. J. Oper. Res., vol. 317, no. 2, pp. 414-424, Sep. 2024, doi: 10.1016/j.ejor.2023.09.028."),
    "telco": "IBM, \"Telco customer churn,\" sample data set (7,043 customers, 21 columns), distributed through Kaggle; also used in [1] and [3].",
    "friedman": "J. H. Friedman, \"Greedy function approximation: A gradient boosting machine,\" Ann. Statist., vol. 29, no. 5, pp. 1189-1232, 2001.",
    "fastapi": "S. Ramirez, \"FastAPI documentation,\" https://fastapi.tiangolo.com (framework used for the API layer).",
}

# Order of the full report (numbers [1]..[n] follow this list)
ORDER = ["oprea", "sikri", "elattar", "rasool", "ahmad", "vafeiadis", "lundberg", "ribeiro", "slack", "treeshap", "smote", "hegarcia",
         "breiman", "sklearn", "leung", "mohajon", "wang", "szelag", "telco", "friedman", "fastapi"]
REFS = [REF_BY_KEY[k] for k in ORDER]
NUM = {k: i + 1 for i, k in enumerate(ORDER)}


def cite(*keys):
    """'[1], [3]' style citation for the full-report numbering."""
    return ", ".join(f"[{NUM[k]}]" for k in keys)
