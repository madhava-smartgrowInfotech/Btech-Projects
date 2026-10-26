"""
Reference list (IEEE style); the position in REFS (1-based) is the number used in the text, [n].

Entries 1-3 were read in full from the PDFs in the batch folder (Documentary/, archived_base_papers/). Entries 4-15 are the works that the declared base paper [1]
lists in its own reference list; their bibliographic details are copied from that list and any finding attributed to them is only what [1] says about them
(they were not re-read). Entries 16-17 were confirmed by web search (title page / abstract). Entries 18-33 are standard, widely cited works whose bibliographic details
are given as recorded in their publishers' records. Entries 34-35 are items named in the batch literature survey (5.LITERATURE SURVEY.docx) that a web search could
not locate: they are listed for completeness, no result is quoted from them and they are never cited in the IEEE paper.
"""

REFS = [
    # 1 base paper (declared in 3.BASE PAPER.docx)
    "M. Panjwani, P. Shrivastava, P. Hande, G. Meshram, N. Verma and D. Gotmare, \"Startup success prediction using machine learning and ensemble techniques,\" "
    "Int. J. Res. Appl. Sci. Eng. Technol. (IJRASET), vol. 14, no. IV, Apr. 2026, doi: 10.22214/ijraset.2026.80226.",
    # 2
    "A. Maarouf, A. Bakiaj and S. Feuerriegel, \"Predicting startup success using large language models: A novel in-context learning approach,\" "
    "arXiv:2601.16568, Jan. 2026.",
    # 3
    "S. Mashhadi, A. Saghezchi and V. G. Kashani, \"Interpretable machine learning for predicting startup funding, patenting, and exits,\" arXiv:2510.09465, 2026.",
    # 4-15 as listed in the reference list of [1]
    "A. Krishna, A. Agrawal and A. Choudhary, \"Predicting the outcome of startups: Less failure, more success,\" Northwestern University, 2016.",
    "D. Camelo Martinez, \"Startup success prediction in the Dutch startup ecosystem,\" M.S. thesis, Delft University of Technology, Delft, The Netherlands, 2019.",
    "H. B. G, A. Kumar and R. Kumar, \"Startup success prediction using machine learning algorithms,\" JNNCE J. Eng. Manage., 2024.",
    "M. Razaghzadeh Bidgoli, I. Raeesi Vanani and M. Goodarzi, \"Predicting the success of startups using a machine learning approach,\" J. Innov. Entrepreneurship, vol. 13, 2024.",
    "J. Li, \"Prediction of the success of startup companies based on support vector machine and random forest,\" in Proc. Int. Workshop Artif. Intell. Educ. (WAIE), 2020.",
    "K. Zbikowski and P. Antosiuk, \"A machine learning, bias-free approach for predicting business success using Crunchbase data,\" Inf. Process. Manage., vol. 58, no. 2, 2021.",
    "S. M. A. Jafari, A. M. Dehkordi and E. Chitsaz, \"A quantitative meta-analysis of AI-based predictors for startup success,\" 2024.",
    "G. Ross, S. Das, D. Sciro and H. Raza, \"CapitalVX: A machine learning model for startup selection and exit prediction,\" J. Finance Data Sci., vol. 7, pp. 94-114, 2021.",
    "S. Tomy and E. Pardede, \"From uncertainties to successful start-ups: A data analytic approach to predict success in technological entrepreneurship,\" Sustainability, vol. 10, no. 3, 2018.",
    "Y. Choi, \"Startup success prediction with PCA-enhanced machine learning models,\" J. Technol. Manage. Innov., vol. 19, no. 4, 2024.",
    "A. Maarouf, S. Feuerriegel and N. Prollochs, \"A fused large language model for predicting startup success,\" Eur. J. Oper. Res., 2025.",
    "M. Bonaventura, V. Ciotti, P. Panzarasa, S. Liverani, L. Lacasa and V. Latora, \"Predicting success in the worldwide start-up network,\" Sci. Rep., vol. 10, 2020.",
    # 16-17 verified by web search
    "L. Gius, \"Disagreement predicts startup success: Evidence from venture competitions,\" Strategy Sci., vol. 10, no. 2, pp. 93-108, Jun. 2025, doi: 10.1287/stsc.2024.0169.",
    "I. B. Bhandari, \"Impact of venture capital on startup success and economic growth in Nepal,\" Nepalese J. Finance, vol. 12, no. 1, Jan. 2025.",
    # 18-33 standard references
    "L. Breiman, \"Random forests,\" Mach. Learn., vol. 45, no. 1, pp. 5-32, Oct. 2001.",
    "T. Chen and C. Guestrin, \"XGBoost: A scalable tree boosting system,\" in Proc. 22nd ACM SIGKDD Int. Conf. Knowl. Discovery Data Mining, San Francisco, CA, USA, 2016, pp. 785-794.",
    "J. H. Friedman, \"Greedy function approximation: A gradient boosting machine,\" Ann. Statist., vol. 29, no. 5, pp. 1189-1232, Oct. 2001.",
    "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825-2830, 2011.",
    "H. He and E. A. Garcia, \"Learning from imbalanced data,\" IEEE Trans. Knowl. Data Eng., vol. 21, no. 9, pp. 1263-1284, Sep. 2009.",
    "N. V. Chawla, K. W. Bowyer, L. O. Hall and W. P. Kegelmeyer, \"SMOTE: Synthetic minority over-sampling technique,\" J. Artif. Intell. Res., vol. 16, pp. 321-357, 2002.",
    "H. He, Y. Bai, E. A. Garcia and S. Li, \"ADASYN: Adaptive synthetic sampling approach for imbalanced learning,\" in Proc. IEEE Int. Joint Conf. Neural Netw. (IJCNN), Hong Kong, 2008, pp. 1322-1328.",
    "N. Reimers and I. Gurevych, \"Sentence-BERT: Sentence embeddings using Siamese BERT-networks,\" in Proc. Conf. Empirical Methods Natural Lang. Process. (EMNLP-IJCNLP), Hong Kong, 2019, pp. 3982-3992.",
    "W. Wang, F. Wei, L. Dong, H. Bao, N. Yang and M. Zhou, \"MiniLM: Deep self-attention distillation for task-agnostic compression of pre-trained transformers,\" in Advances in Neural Information Processing Systems, vol. 33, 2020, pp. 5776-5788.",
    "T. Saito and M. Rehmsmeier, \"The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets,\" PLoS ONE, vol. 10, no. 3, Art. no. e0118432, 2015.",
    "T. Fawcett, \"An introduction to ROC analysis,\" Pattern Recognit. Lett., vol. 27, no. 8, pp. 861-874, Jun. 2006.",
    "S. Kaufman, S. Rosset, C. Perlich and O. Stitelman, \"Leakage in data mining: Formulation, detection, and avoidance,\" ACM Trans. Knowl. Discovery Data, vol. 6, no. 4, Art. no. 15, 2012.",
    "T. Cover and P. Hart, \"Nearest neighbor pattern classification,\" IEEE Trans. Inf. Theory, vol. 13, no. 1, pp. 21-27, Jan. 1967.",
    "T. B. Brown et al., \"Language models are few-shot learners,\" in Advances in Neural Information Processing Systems, vol. 33, 2020, pp. 1877-1901.",
    "M. KC, \"Startup success prediction,\" Kaggle dataset (public domain), https://www.kaggle.com/datasets/manishkc06/startup-success-prediction.",
    "S. M. Lundberg and S.-I. Lee, \"A unified approach to interpreting model predictions,\" in Advances in Neural Information Processing Systems, vol. 30, 2017, pp. 4765-4774.",
    # 34-35: named in the batch literature survey, details NOT verified
    "\"Impact of venture capital on startup success rates across industry: An empirical study,\" Eur. Econ. Lett., 2024. [Listed in the batch literature survey; authors not verified.]",
    "\"The role and impact of SICTIC in the Swiss startup ecosystem,\" book chapter, 2026. [Listed in the batch literature survey; authors and publisher not verified.]",
]

KEY = {"base": 1, "maarouf": 2, "mashhadi": 3, "krishna": 4, "martinez": 5, "hbg": 6, "bidgoli": 7, "li": 8, "zbikowski": 9, "jafari": 10, "ross": 11, "tomy": 12,
       "choi": 13, "fused": 14, "bonaventura": 15, "gius": 16, "bhandari": 17, "rf": 18, "xgb": 19, "gbm": 20, "sklearn": 21, "imbalance": 22, "smote": 23, "adasyn": 24,
       "sbert": 25, "minilm": 26, "pr": 27, "roc": 28, "leakage": 29, "knn": 30, "icl": 31, "kaggle": 32, "shap": 33, "s1": 34, "s2": 35}


def cite(*keys):
    return "[" + ", ".join(str(KEY[k]) for k in keys) + "]"
