"""IEEE-style reference list. Order = citation number in the report. Use N('key') to get the number for a key.

Every entry was checked against the paper itself (base paper PDF in Documentary/), the arXiv abstract page, or a publisher/index record.
The four batch-survey titles (keys s2..s5) could not be located on the web; they are listed as given in 5.LITERATURE SURVEY.docx and are never quoted for numbers.
"""

_R = [
    ("base", "L. N. Mishra, B. Senapati, S. K. Nayak and A. J. Rangari, \"Explainable retail demand forecasting: A hybrid LightGBM-SHAP framework for inventory optimization,\" IEEE Access, vol. 14, pp. 43613-43633, 2026, doi: 10.1109/ACCESS.2026.3675540."),
    ("xgb", "T. Chen and C. Guestrin, \"XGBoost: A scalable tree boosting system,\" in Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, Aug. 2016, pp. 785-794."),
    ("lgbm", "G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye and T.-Y. Liu, \"LightGBM: A highly efficient gradient boosting decision tree,\" in Proc. Advances in Neural Information Processing Systems (NIPS), 2017, pp. 3146-3154."),
    ("shap", "S. M. Lundberg and S.-I. Lee, \"A unified approach to interpreting model predictions,\" in Proc. Advances in Neural Information Processing Systems (NIPS), 2017, pp. 4765-4774."),
    ("treeshap", "S. M. Lundberg et al., \"From local explanations to global understanding with explainable AI for trees,\" Nature Machine Intelligence, vol. 2, no. 1, pp. 56-67, Jan. 2020."),
    ("m5", "S. Makridakis, E. Spiliotis and V. Assimakopoulos, \"M5 accuracy competition: Results, findings, and conclusions,\" International Journal of Forecasting, vol. 38, no. 4, pp. 1346-1364, Oct. 2022."),
    ("rf", "L. Breiman, \"Random forests,\" Machine Learning, vol. 45, no. 1, pp. 5-32, 2001."),
    ("gbm", "J. H. Friedman, \"Greedy function approximation: A gradient boosting machine,\" The Annals of Statistics, vol. 29, no. 5, pp. 1189-1232, 2001."),
    ("mase", "R. J. Hyndman and A. B. Koehler, \"Another look at measures of forecast accuracy,\" International Journal of Forecasting, vol. 22, no. 4, pp. 679-688, 2006."),
    ("shim", "H. Shimodaira, \"Improving predictive inference under covariate shift by weighting the log-likelihood function,\" Journal of Statistical Planning and Inference, vol. 90, no. 2, pp. 227-244, 2000."),
    ("sugi", "M. Sugiyama, M. Krauledat and K.-R. Mueller, \"Covariate shift adaptation by importance weighted cross validation,\" Journal of Machine Learning Research, vol. 8, pp. 985-1005, 2007."),
    ("bickel", "S. Bickel, M. Brueckner and T. Scheffer, \"Discriminative learning under covariate shift,\" Journal of Machine Learning Research, vol. 10, pp. 2137-2155, 2009."),
    ("pan", "S. J. Pan and Q. Yang, \"A survey on transfer learning,\" IEEE Transactions on Knowledge and Data Engineering, vol. 22, no. 10, pp. 1345-1359, Oct. 2010."),
    ("bendavid", "S. Ben-David, J. Blitzer, K. Crammer, A. Kulesza, F. Pereira and J. W. Vaughan, \"A theory of learning from different domains,\" Machine Learning, vol. 79, no. 1-2, pp. 151-175, 2010."),
    ("dann", "Y. Ganin et al., \"Domain-adversarial training of neural networks,\" Journal of Machine Learning Research, vol. 17, no. 59, pp. 1-35, 2016."),
    ("coral", "B. Sun and K. Saenko, \"Deep CORAL: Correlation alignment for deep domain adaptation,\" in Proc. ECCV Workshops, 2016, pp. 443-450."),
    ("thom", "S. Thomassey, \"Sales forecasts in clothing industry: The key success factor of the supply chain management,\" International Journal of Production Economics, vol. 128, no. 2, pp. 470-483, Dec. 2010."),
    ("ekam", "V. Ekambaram, K. Manglik, S. Mukherjee, S. S. K. Sajja, S. Dwivedi and V. Raykar, \"Attention based multi-modal new product sales time-series forecasting,\" in Proc. 26th ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, 2020, pp. 3110-3118, doi: 10.1145/3394486.3403362."),
    ("singh", "P. K. Singh, Y. Gupta, N. Jha and A. Rajan, \"Fashion retail: Forecasting demand for new items,\" arXiv:1907.01960, 2019."),
    ("skend", "G. Skenderi, C. Joppi, M. Denitto and M. Cristani, \"Well Googled is half done: Multimodal forecasting of new fashion product sales with image-based Google Trends,\" arXiv:2109.09824, 2021 (rev. 2024)."),
    ("muqar", "S. I. Papadopoulos, C. Koutlis, S. Papadopoulos and I. Kompatsiaris, \"Multimodal quasi-autoregression: Forecasting the visual popularity of new fashion products,\" arXiv:2204.04014, 2022."),
    ("cdlf", "R. Zhou, Z. Zhang, J. Han, Y. Peng and X. Zhang, \"Cold-start forecasting of new product life-cycles via conditional diffusion models,\" arXiv:2604.20370, Apr. 2026."),
    ("hm", "H&M Group, \"H&M Personalized Fashion Recommendations,\" Kaggle competition data (articles, customers, transactions), 2022. [Online]. Available: https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations"),
    ("sk", "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" Journal of Machine Learning Research, vol. 12, pp. 2825-2830, 2011."),
    ("bergstra", "J. Bergstra and Y. Bengio, \"Random search for hyper-parameter optimization,\" Journal of Machine Learning Research, vol. 13, pp. 281-305, 2012."),
    ("s2", "\"Impact of AI-driven demand forecasting on retail inventory efficiency,\" 2026 (title as listed in the batch literature survey; not located online and not quoted)."),
    ("s3", "\"Enhancing inventory planning in retail SMEs through data-driven demand forecasting,\" Int. J. of Innovative Inventions in Social Science and Humanities, 2026 (title as listed in the batch literature survey; not located online and not quoted)."),
    ("s4", "\"Does the forecaster matter? A systematic evaluation of demand forecasting and inventory control policies across retail demand regimes,\" 2026 (title as listed in the batch literature survey; not located online and not quoted)."),
    ("s5", "\"Predictive inventory management for retail distribution networks: Reorder point optimization and machine learning demand forecasting,\" 2026 (title as listed in the batch literature survey; not located online and not quoted)."),
]
REFS = [t for _, t in _R]
_IDX = {k: i + 1 for i, (k, _) in enumerate(_R)}


def N(*keys):
    """Citation text like [3] or [3], [7] for one or more keys."""
    return ", ".join(f"[{_IDX[k]}]" for k in keys)
