"""
Reference list (IEEE style); the position in REFS (1-based) is the number used in the text, [n].

Entries 1-3 were read from the PDFs in the batch folder (archived_base_papers/, Documentary/) and entry 4 from the LIAR2 dataset card;
5-26 are standard, widely cited works whose bibliographic details are given as recorded in their publishers' records. Entries 27-30 are the sources named in
the batch literature survey (5.LITERATURE SURVEY.docx): only title, year and venue are recorded there, and a web search could not locate them, so their authors
and findings are NOT verified, no result is quoted from them and they are never cited in the IEEE paper.
"""

REFS = [
    # 1 base paper
    "M. Saad, S. Abdelrazek and I. R. Abdelmaksoud, \"An algorithmic system for Arabic fake news detection using neural networks and transformer embeddings "
    "with class weighting,\" Scientific Reports, vol. 16, Art. no. 12226, 2026, doi: 10.1038/s41598-026-45653-4.",
    # 2
    "P. Dell'Oglio, A. Bondielli, F. Marcelloni and L. C. Passaro, \"An experimental comparison of the most popular approaches to fake news detection,\" "
    "Information Sciences, 2026, doi: 10.1016/j.ins.2026.123407; arXiv:2603.25501.",
    # 3
    "T. Huang, Z. Xu, P. Yu, J. Yi and X. Xu, \"A hybrid transformer model for fake news detection: Leveraging Bayesian optimization and bidirectional recurrent unit,\" "
    "2025, arXiv:2502.09097.",
    # 4
    "C. Xu and M.-T. Kechadi, \"An enhanced fake news detection system with fuzzy deep learning,\" IEEE Access, vol. 12, pp. 88006-88021, 2024, "
    "doi: 10.1109/ACCESS.2024.3418340.",
    # 5
    "W. Y. Wang, \"'Liar, liar pants on fire': A new benchmark dataset for fake news detection,\" in Proc. 55th Annu. Meeting Assoc. Comput. Linguistics "
    "(ACL), Vol. 2: Short Papers, Vancouver, Canada, 2017, pp. 422-426, doi: 10.18653/v1/P17-2067.",
    # 6
    "X.-S. Yang, \"Firefly algorithms for multimodal optimization,\" in Stochastic Algorithms: Foundations and Applications (SAGA 2009), Lecture Notes in "
    "Computer Science, vol. 5792. Berlin, Germany: Springer, 2009, pp. 169-178.",
    # 7
    "X.-S. Yang, \"Firefly algorithm, stochastic test functions and design optimisation,\" Int. J. Bio-Inspired Computation, vol. 2, no. 2, pp. 78-84, 2010.",
    # 8
    "C. Cortes and V. Vapnik, \"Support-vector networks,\" Machine Learning, vol. 20, no. 3, pp. 273-297, Sep. 1995.",
    # 9
    "C.-W. Hsu and C.-J. Lin, \"A comparison of methods for multiclass support vector machines,\" IEEE Trans. Neural Netw., vol. 13, no. 2, pp. 415-425, Mar. 2002.",
    # 10
    "I. T. Jolliffe and J. Cadima, \"Principal component analysis: a review and recent developments,\" Phil. Trans. R. Soc. A, vol. 374, no. 2065, "
    "Art. no. 20150202, 2016.",
    # 11
    "S. Wold, K. Esbensen and P. Geladi, \"Principal component analysis,\" Chemometrics and Intelligent Laboratory Systems, vol. 2, nos. 1-3, pp. 37-52, 1987.",
    # 12
    "J. C. Platt, \"Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods,\" in Advances in Large Margin "
    "Classifiers. Cambridge, MA, USA: MIT Press, 1999, pp. 61-74.",
    # 13
    "G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" Information Processing & Management, vol. 24, no. 5, pp. 513-523, 1988.",
    # 14
    "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825-2830, 2011.",
    # 15
    "H. He and E. A. Garcia, \"Learning from imbalanced data,\" IEEE Trans. Knowl. Data Eng., vol. 21, no. 9, pp. 1263-1284, Sep. 2009.",
    # 16
    "K. Shu, A. Sliva, S. Wang, J. Tang and H. Liu, \"Fake news detection on social media: A data mining perspective,\" ACM SIGKDD Explorations Newsletter, "
    "vol. 19, no. 1, pp. 22-36, 2017.",
    # 17
    "S. Vosoughi, D. Roy and S. Aral, \"The spread of true and false news online,\" Science, vol. 359, no. 6380, pp. 1146-1151, Mar. 2018.",
    # 18
    "X. Zhou and R. Zafarani, \"A survey of fake news: Fundamental theories, detection methods, and opportunities,\" ACM Comput. Surv., vol. 53, no. 5, "
    "Art. no. 109, 2020; arXiv:1812.00315.",
    # 19
    "H. Ahmed, I. Traore and S. Saad, \"Detection of online fake news using N-gram analysis and machine learning techniques,\" in Intelligent, Secure, and "
    "Dependable Systems in Distributed and Cloud Environments (ISDDC 2017), Lecture Notes in Computer Science, vol. 10618. Cham, Switzerland: Springer, 2017, pp. 127-138.",
    # 20
    "V. Perez-Rosas, B. Kleinberg, A. Lefevre and R. Mihalcea, \"Automatic detection of fake news,\" in Proc. 27th Int. Conf. Comput. Linguistics (COLING), "
    "Santa Fe, NM, USA, 2018, pp. 3391-3401.",
    # 21
    "M. Potthast, J. Kiesel, K. Reinartz, J. Bevendorff and B. Stein, \"A stylometric inquiry into hyperpartisan and fake news,\" in Proc. 56th Annu. Meeting "
    "Assoc. Comput. Linguistics (ACL), Melbourne, Australia, 2018, pp. 231-240.",
    # 22
    "H. Rashkin, E. Choi, J. Y. Jang, S. Volkova and Y. Choi, \"Truth of varying shades: Analyzing language in fake news and political fact-checking,\" in "
    "Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP), Copenhagen, Denmark, 2017, pp. 2931-2937.",
    # 23
    "J. Devlin, M.-W. Chang, K. Lee and K. Toutanova, \"BERT: Pre-training of deep bidirectional transformers for language understanding,\" in Proc. NAACL-HLT, "
    "Minneapolis, MN, USA, 2019, pp. 4171-4186.",
    # 24
    "B. Xue, M. Zhang, W. N. Browne and X. Yao, \"A survey on evolutionary computation approaches to feature selection,\" IEEE Trans. Evol. Comput., vol. 20, "
    "no. 4, pp. 606-626, Aug. 2016.",
    # 25
    "L. Zhang, K. Mistry, C. P. Lim and S. C. Neoh, \"Feature selection using firefly optimization for classification and regression models,\" Decision Support "
    "Systems, vol. 106, pp. 64-85, 2018.",
    # 26
    "Y. Al-Tarawneh, H. Kanj and W. Aly, \"Enhancing fake news detection with word embedding: A machine learning and deep learning approach,\" Computers, "
    "vol. 13, no. 9, Art. no. 239, 2024.",
    # 27-30: named in the batch literature survey, details NOT verified (title, year, venue only)
    "\"Word embedding and classification methods and their effects on fake news detection,\" 2024. [Listed in the batch literature survey; authors and venue not verified.]",
    "\"A deep learning ensemble framework for fake news stance detection and classification,\" Nanotechnology Perceptions, 2024. [Listed in the batch literature survey; authors not verified.]",
    "\"Fake news detection using machine learning techniques,\" 2025. [Listed in the batch literature survey; authors and venue not verified.]",
    "\"Analysis of fake news detection and prevention of various fake news detection algorithms and their research challenges,\" in Text and Social Media Analytics "
    "for Fake News and Hate Speech Detection, 2024. [Listed in the batch literature survey; authors not verified.]",
]

# short keys for citing from content modules: cite("base") -> "[1]"
KEY = {"base": 1, "compare": 2, "hybrid": 3, "liar2": 4, "liar": 5, "firefly09": 6, "firefly10": 7, "svm": 8, "msvm": 9, "pca": 10, "pca87": 11, "platt": 12, "tfidf": 13,
       "sklearn": 14, "imbalance": 15, "shu": 16, "vosoughi": 17, "survey": 18, "ahmed": 19, "perez": 20, "potthast": 21, "rashkin": 22, "bert": 23, "fs_survey": 24,
       "ffs": 25, "embed": 26, "s1": 27, "s2": 28, "s3": 29, "s4": 30}


def cite(*keys):
    return "[" + ", ".join(str(KEY[k]) for k in keys) + "]"
