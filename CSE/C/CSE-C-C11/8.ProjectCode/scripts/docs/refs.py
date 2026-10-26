"""IEEE-style reference list. Order = citation number in the report; use N('key') for the number of a key.

Entries 1-5 were read in full or in their abstract/full text (PDFs in Documentary/ and archived_base_papers/, publisher pages fetched 2026-10-26).
Entries 6-7 are batch-survey titles (5.LITERATURE SURVEY.docx): 6 has an IEEE Xplore record (document 10914721) whose author list and
conference name could not be read here; 7 could not be located on the web. Both are listed as given in the batch survey and are never quoted for any result.
Entries 8-22 are standard, widely cited methods and background works; the text only states what those works are known for, never a numeric result.
"""

_R = [
    ("base", "R. Kharat, S. Solapurkar, A. Tikkas, M. Uttarwar and A. Yadav, \"A smart AI-based personal finance assistant: A multi-model approach for expense categorization, budgeting, forecasting and anomaly detection,\" Int. J. Research in Applied Science and Engineering Technology (IJRASET), vol. 13, no. XI, pp. 167-180, Nov. 2025, doi: 10.22214/ijraset.2025.75019."),
    ("to", "P. L. To, \"Enhancing financial literacy and management through goal-directed design and gamification in personal finance application,\" arXiv:2601.08640, Jan. 2026."),
    ("theerthala", "A. Theerthala, \"Synthesizing behaviorally-grounded reasoning chains: A data-generation framework for personal finance LLMs,\" arXiv:2509.14180 [cs.CL], Sep. 2025."),
    ("finsense", "V. Dilip and R. S. Janaki, \"FinSenseAI: An explainable AI-based personal finance recommendation and expense prediction system using hybrid machine learning models,\" Int. J. Innovative Science and Research Technology, vol. 11, no. 7, pp. 1637-1650, Jul. 2026, doi: 10.38124/ijisrt/26jul842."),
    ("leak", "F. R. Abiya, S. Parvathy, M. R. Devende, S. R. Ajmalsha and C. Viji, \"Personal expense leakage detection and budget optimization using machine learning,\" Int. J. Research in Applied Science and Engineering Technology (IJRASET), Apr. 2026, doi: 10.22214/ijraset.2026.79467."),
    ("s2", "\"AI-driven financial insights for personal budget planning: A smart approach to future expense prediction,\" in Proc. 2025 3rd Int. Conf. on Intelligent Data Communication Technologies and Internet of Things (IDCIoT), IEEE, 2025 (IEEE Xplore document 10914721; as listed in the batch survey, authors not verified)."),
    ("s3", "\"AI-driven finance management platform for intelligent expense tracking and budget automation,\" Int. Research J. of Modernization in Engineering Technology and Science, 2026 (as listed in the batch survey; not located, not verified)."),
    ("bert", "J. Devlin, M.-W. Chang, K. Lee and K. Toutanova, \"BERT: Pre-training of deep bidirectional transformers for language understanding,\" in Proc. NAACL-HLT, 2019, pp. 4171-4186."),
    ("finbert", "D. Araci, \"FinBERT: Financial sentiment analysis with pre-trained language models,\" arXiv:1908.10063, 2019."),
    ("iforest", "F. T. Liu, K. M. Ting and Z.-H. Zhou, \"Isolation forest,\" in Proc. 8th IEEE Int. Conf. on Data Mining (ICDM), 2008, pp. 413-422."),
    ("lstm", "S. Hochreiter and J. Schmidhuber, \"Long short-term memory,\" Neural Computation, vol. 9, no. 8, pp. 1735-1780, 1997."),
    ("qlearn", "C. J. C. H. Watkins and P. Dayan, \"Q-learning,\" Machine Learning, vol. 8, no. 3-4, pp. 279-292, 1992."),
    ("smote", "N. V. Chawla, K. W. Bowyer, L. O. Hall and W. P. Kegelmeyer, \"SMOTE: Synthetic minority over-sampling technique,\" J. Artificial Intelligence Research, vol. 16, pp. 321-357, 2002."),
    ("sklearn", "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Machine Learning Research, vol. 12, pp. 2825-2830, 2011."),
    ("tfidf", "G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" Information Processing & Management, vol. 24, no. 5, pp. 513-523, 1988."),
    ("hk", "R. J. Hyndman and A. B. Koehler, \"Another look at measures of forecast accuracy,\" Int. J. Forecasting, vol. 22, no. 4, pp. 679-688, 2006."),
    ("makri", "S. Makridakis, E. Spiliotis and V. Assimakopoulos, \"Statistical and machine learning forecasting methods: Concerns and ways forward,\" PLoS ONE, vol. 13, no. 3, e0194889, 2018."),
    ("fpp", "R. J. Hyndman and G. Athanasopoulos, Forecasting: Principles and Practice, 3rd ed. Melbourne, Australia: OTexts, 2021."),
    ("lusardi", "A. Lusardi and O. S. Mitchell, \"The economic importance of financial literacy: Theory and evidence,\" J. Economic Literature, vol. 52, no. 1, pp. 5-44, 2014."),
    ("bcrypt", "N. Provos and D. Mazieres, \"A future-adaptable password scheme,\" in Proc. USENIX Annual Technical Conf., FREENIX Track, 1999, pp. 81-91."),
    ("rest", "R. T. Fielding, \"Architectural styles and the design of network-based software architectures,\" Ph.D. dissertation, Univ. of California, Irvine, 2000."),
    ("sqla", "M. Bayer, \"SQLAlchemy,\" in The Architecture of Open Source Applications, Volume II, A. Brown and G. Wilson, Eds. 2012."),
    ("kohavi", "R. Kohavi, \"A study of cross-validation and bootstrap for accuracy estimation and model selection,\" in Proc. 14th Int. Joint Conf. on Artificial Intelligence (IJCAI), 1995, pp. 1137-1143."),
]

REFS = [t for _, t in _R]
_IDX = {k: i + 1 for i, (k, _) in enumerate(_R)}


def N(*keys):
    """Citation text like [3] or [3], [7] for one or more keys."""
    return ", ".join(f"[{_IDX[k]}]" for k in keys)
