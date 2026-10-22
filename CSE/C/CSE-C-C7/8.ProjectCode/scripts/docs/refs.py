"""
IEEE-style reference list for batch C7. Every entry is either
  (a) taken from the base paper's own reference list (checked against its PDF),
  (b) one of the two companion papers kept in archived_base_papers/ (author names read from the PDFs),
  (c) a standard, well-known publication, or
  (d) a title/year pair recorded in the batch literature survey (authors were not recorded and are not guessed).
NOTE: the batch prompt forbids the exact phrase "recommender system(s)" anywhere in the documents, so the four standard works whose titles contain it (Salau et al., Burke, Koren et al., the Recommender Systems Handbook) are deliberately left out.
Cite with refs.n(refs.K["xgboost"]) or refs.c("xgboost", "sklearn") -> "[13], [14]".
"""

_ENTRIES = [
    ("base", "C. P. Isiwu, L. C. Nnadi, and Y. Watanobe, \"From prediction to prescription: A Causal-AI for personalized learning path optimization in MOOCs,\" IEEE Access, vol. 14, pp. 29105-29118, 2026, doi: 10.1109/ACCESS.2026.3666619."),
    ("khreis", "A. Khreis, A. Nasr, and Y. Hilal, \"Isotropy-optimized contrastive learning for semantic course recommendation,\" arXiv:2601.11427, Jan. 2026."),
    ("gharahighehi", "A. Gharahighehi, A. Ghinis, M. Venturini, F. Cornillie, and C. Vens, \"Enhancing collaborative filtering-based course recommendations by exploiting time-to-event information with survival analysis,\" arXiv:2503.00072, 2025."),
    ("oulad", "J. Kuzilek, M. Hlosta, and Z. Zdrahal, \"Open university learning analytics dataset,\" Sci. Data, vol. 4, no. 1, pp. 1-8, Nov. 2017."),
    ("dudik", "M. Dudik, D. Erhan, J. Langford, and L. Li, \"Doubly robust policy evaluation and optimization,\" Stat. Sci., vol. 29, no. 4, pp. 485-511, Nov. 2014."),
    ("pearl", "J. Pearl, Causality, 2nd ed. Cambridge, U.K.: Cambridge Univ. Press, 2009."),
    ("imbens", "G. W. Imbens and D. B. Rubin, Causal Inference in Statistics, Social, and Biomedical Sciences. Cambridge, U.K.: Cambridge Univ. Press, 2015."),
    ("uplift", "P. Gutierrez and J.-Y. Gerardy, \"Causal inference and uplift modelling: A review of the literature,\" in Proc. Int. Conf. Predictive Appl. APIs, 2016, pp. 1-13."),
    ("hrl", "J. Zhang, B. Hao, B. Chen, C. Li, H. Chen, and J. Sun, \"Hierarchical reinforcement learning for course recommendation in MOOCs,\" in Proc. AAAI Conf. Artif. Intell., vol. 33, 2019, pp. 435-442."),
    ("saito", "T. Saito and Y. Watanobe, \"Learning path recommendation system for programming education based on neural networks,\" Int. J. Distance Educ. Technol., vol. 18, no. 1, pp. 36-64, Jan. 2020."),
    ("yu", "H. Yu, C. Miao, C. Leung, and T. J. White, \"Towards AI-powered personalization in MOOC learning,\" npj Sci. Learn., vol. 2, no. 1, p. 16, Dec. 2017."),
    ("xgboost", "T. Chen and C. Guestrin, \"XGBoost: A scalable tree boosting system,\" in Proc. 22nd ACM SIGKDD Int. Conf. Knowl. Discovery Data Mining, 2016, pp. 785-794."),
    ("sklearn", "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825-2830, 2011."),
    ("tfidf", "G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" Inf. Process. Manage., vol. 24, no. 5, pp. 513-523, 1988."),
    ("breiman", "L. Breiman, \"Random forests,\" Mach. Learn., vol. 45, no. 1, pp. 5-32, 2001."),
    ("kunzel", "S. R. Kunzel, J. S. Sekhon, P. J. Bickel, and B. Yu, \"Metalearners for estimating heterogeneous treatment effects using machine learning,\" Proc. Nat. Acad. Sci. USA, vol. 116, no. 10, pp. 4156-4165, 2019."),
    ("lightgcn", "X. He, K. Deng, X. Wang, Y. Li, Y. Zhang, and M. Wang, \"LightGCN: Simplifying and powering graph convolution network for recommendation,\" in Proc. 43rd Int. ACM SIGIR Conf. Res. Develop. Inf. Retrieval, 2020, pp. 639-648."),
    ("sutton", "R. S. Sutton and A. G. Barto, Reinforcement Learning: An Introduction, 2nd ed. Cambridge, MA, USA: MIT Press, 2018."),
    ("lpnav", "J.-Y. Chen, S. Saeedvand, and I.-W. Lai, \"Adaptive learning path navigation based on knowledge tracing and reinforcement learning,\" arXiv:2305.04475, 2023."),
    ("ramo", "J. Rao and J. Lin, \"RAMO: Retrieval-augmented generation for enhancing MOOCs recommendations,\" arXiv:2407.04925, 2024."),
    ("fastapi", "S. Ramirez, \"FastAPI framework, high performance, easy to learn, fast to code, ready for production.\" [Online]. Available: https://fastapi.tiangolo.com"),
    ("sqlalchemy", "M. Bayer, \"SQLAlchemy,\" in The Architecture of Open Source Applications, vol. 2, A. Brown and G. Wilson, Eds. 2012."),
    ("eduguide", "S. Sujay, G. Harshitha, and M. Monisha, \"EduGuide: A hybrid NLP-driven course recommendation system ... TF-IDF and ML,\" Int. J. Innov. Res. Technol., vol. 13, no. 3, 2026 (listing confirmed by web search; the batch survey records the title with an ellipsis)."),
    ("s_ml", "\"Personalized course recommendation system using machine learning,\" 2025 (entry recorded in the batch literature survey; authors and venue not recorded)."),
    ("s_lightgcn", "\"Personalized course recommendation model based on LightGCN and learning behavior data,\" in Proc. ICIDML, 2025 (entry recorded in the batch literature survey; authors not recorded)."),
    ("s_review", "\"Literature review on course recommendation system for personalized e-learning,\" Int. J. Drug Delivery Technol., 2026 (entry recorded in the batch literature survey; authors not recorded)."),
]

REFS = [t for _, t in _ENTRIES]
K = {k: i + 1 for i, (k, _) in enumerate(_ENTRIES)}


def n(*nums):
    """Citation string for reference numbers, e.g. n(1, 3) -> '[1], [3]'."""
    return ", ".join(f"[{k}]" for k in nums)


def c(*keys):
    """Citation string for reference keys, e.g. c('base', 'oulad') -> '[1], [4]'."""
    return n(*[K[k] for k in keys])
