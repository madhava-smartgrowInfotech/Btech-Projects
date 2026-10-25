"""IEEE reference list for the Multi-Disease Prediction project (CSE-A-A3).

Every entry was checked against the paper itself (local PDF), the publisher / repository page, PubMed / Europe PMC,
Crossref or arXiv while this file was written.  Items that could not be confirmed are NOT in REFS (see NOT_VERIFIED).
Notes on how far each entry was read are in READ_LEVEL (used by the report's 'how the survey was done' text).
"""

_ENTRIES = [
    ("base",
     "M. Z. Alam, R. Rahman, H. M. Sozib, H. Ahmed, A. Hossain, A. A. Sabeena, A. F. Tasnim, F. Ahmed, M. I. Sarkar, and T. I. Erdei, "
     "\"Enhancing thyroid disease diagnosis with machine learning and counterfactual explainable AI,\" "
     "IEEE Access, vol. 14, pp. 80346-80370, 2026, doi: 10.1109/ACCESS.2026.3663497.", "full text"),
    ("bangla",
     "R. Zannat, A. Al Shafi, and A. Muntakim, \"Bridging the gap in Bangla healthcare: Machine learning based disease prediction using a "
     "symptoms-disease dataset,\" in Proc. Int. Conf. Elect., Comput. Commun. Eng. (ECCE), Chattogram, Bangladesh, Feb. 2025, "
     "doi: 10.1109/ECCE64574.2025.11012950 (arXiv:2601.12068).", "full text"),
    ("nahian",
     "J. Al Nahian, A. K. M. Masum, S. Abujar, and M. J. Mia, \"Common human diseases prediction using machine learning based on survey data,\" "
     "arXiv:2209.10750, Sep. 2022 (accepted in Bull. Elect. Eng. Informat.).", "abstract"),
    ("multi25",
     "V. Kamakshamma, G. M. Sumanth, K. R. G. N. K. Reddy, B. Pallavi, and C. S. Varshini, \"Multi-disease prediction system using machine learning,\" "
     "in Proc. 1st Int. Conf. Res. Develop. Inf., Commun., Comput. Technol. (ICRDICCT), vol. 2. SCITEPRESS, 2025, pp. 116-127, "
     "doi: 10.5220/0013878600004919.", "paper"),
    ("sun",
     "A. Sun and F. Sun, \"Prediction of diabetes using supervised classification,\" J. Emerg. Investigators, Mar. 2024, "
     "doi: 10.59720/23-062.", "abstract"),
    ("islam",
     "M. A. Islam, M. Z. H. Majumder, and M. A. Hussein, \"Chronic kidney disease prediction based on machine learning algorithms,\" "
     "J. Pathol. Inform., vol. 14, Art. no. 100189, 2023, doi: 10.1016/j.jpi.2023.100189.", "abstract"),
    ("straw",
     "I. Straw and H. Wu, \"Investigating for bias in healthcare algorithms: A sex-stratified analysis of supervised machine learning models "
     "in liver disease prediction,\" BMJ Health Care Inform., vol. 29, no. 1, Art. no. e100457, 2022, doi: 10.1136/bmjhci-2021-100457.", "abstract"),
    ("salekin",
     "A. Salekin and J. Stankovic, \"Detection of chronic kidney disease and selecting important predictive attributes,\" "
     "in Proc. IEEE Int. Conf. Healthcare Informat. (ICHI), 2016, pp. 262-270, doi: 10.1109/ICHI.2016.36.", "abstract"),
    ("kidneychap",
     "T. Choudhury, A. Sar, A. Katal, S. Aich, and P. Joshi, \"Kidney disease prediction by machine learning techniques,\" in "
     "Machine Learning for Disease Detection, Prediction, and Diagnosis. Singapore: Springer Nature, 2025, pp. 171-190, "
     "doi: 10.1007/978-981-96-4241-0_9.", "bibliographic record only"),
    ("dlchap",
     "A. Thakur and A. Kumar, \"Introduction to deep learning for disease prediction,\" in "
     "Machine Learning for Disease Detection, Prediction, and Diagnosis. Singapore: Springer Nature, 2025, pp. 33-66, "
     "doi: 10.1007/978-981-96-4241-0_3.", "bibliographic record only"),
    ("skinchap",
     "M. Patil, N. Shinde, R. K. Sharma, S. Kadam, and S. Kashte, \"Skin disease prediction using machine learning techniques,\" in "
     "Machine Learning for Disease Detection, Prediction, and Diagnosis. Singapore: Springer Nature, 2025, pp. 225-256, "
     "doi: 10.1007/978-981-96-4241-0_12.", "bibliographic record only"),
    ("pima",
     "J. W. Smith, J. E. Everhart, W. C. Dickson, W. C. Knowler, and R. S. Johannes, \"Using the ADAP learning algorithm to forecast the onset of "
     "diabetes mellitus,\" in Proc. Annu. Symp. Comput. Appl. Med. Care, 1988, pp. 261-265.", "record and abstract"),
    ("detrano",
     "R. Detrano, A. Janosi, W. Steinbrunn, M. Pfisterer, J. J. Schmid, S. Sandhu, K. H. Guppy, S. Lee, and V. Froelicher, "
     "\"International application of a new probability algorithm for the diagnosis of coronary artery disease,\" "
     "Amer. J. Cardiol., vol. 64, no. 5, pp. 304-310, Aug. 1989, doi: 10.1016/0002-9149(89)90524-9.", "PubMed record"),
    ("cleveland",
     "A. Janosi, W. Steinbrunn, M. Pfisterer, and R. Detrano, \"Heart Disease,\" UCI Machine Learning Repository, 1989 "
     "(303 instances, 13 features), doi: 10.24432/C52P4X.", "repository page"),
    ("ckd",
     "L. Rubini, P. Soundarapandian, and P. Eswaran, \"Chronic Kidney Disease,\" UCI Machine Learning Repository, 2015 "
     "(400 instances, 24 features), doi: 10.24432/C5G020.", "repository page"),
    ("ilpd",
     "B. Ramana and N. Venkateswarlu, \"ILPD (Indian Liver Patient Dataset),\" UCI Machine Learning Repository, 2012 "
     "(583 instances, 10 features), doi: 10.24432/C5D02C.", "repository page"),
    ("scikit",
     "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825-2830, 2011.", "journal page"),
    ("rf",
     "L. Breiman, \"Random forests,\" Mach. Learn., vol. 45, no. 1, pp. 5-32, 2001, doi: 10.1023/A:1010933404324.", "Crossref record"),
    ("svm",
     "C. Cortes and V. Vapnik, \"Support-vector networks,\" Mach. Learn., vol. 20, no. 3, pp. 273-297, 1995, doi: 10.1007/BF00994018.", "Crossref record"),
    ("hosmer",
     "D. W. Hosmer Jr., S. Lemeshow, and R. X. Sturdivant, Applied Logistic Regression. Hoboken, NJ, USA: Wiley, 2013, "
     "doi: 10.1002/9781118548387.", "Crossref record"),
    ("shap",
     "S. M. Lundberg and S.-I. Lee, \"A unified approach to interpreting model predictions,\" in Proc. Adv. Neural Inf. Process. Syst. "
     "(NIPS), vol. 30, 2017, arXiv:1705.07874.", "arXiv record"),
    ("wachter",
     "S. Wachter, B. Mittelstadt, and C. Russell, \"Counterfactual explanations without opening the black box: Automated decisions and the GDPR,\" "
     "arXiv:1711.00399, 2017 (Harvard J. Law Technol., 2018).", "arXiv record"),
    ("smote",
     "N. V. Chawla, K. W. Bowyer, L. O. Hall, and W. P. Kegelmeyer, \"SMOTE: Synthetic minority over-sampling technique,\" "
     "J. Artif. Intell. Res., vol. 16, pp. 321-357, 2002, doi: 10.1613/jair.953.", "Crossref record"),
    ("varma",
     "S. Varma and R. Simon, \"Bias in error estimation when using cross-validation for model selection,\" "
     "BMC Bioinformatics, vol. 7, Art. no. 91, 2006, doi: 10.1186/1471-2105-7-91.", "PubMed record"),
    ("chicco",
     "D. Chicco and G. Jurman, \"The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary "
     "classification evaluation,\" BMC Genomics, vol. 21, Art. no. 6, 2020, doi: 10.1186/s12864-019-6413-7.", "PubMed record"),
    ("saito",
     "T. Saito and M. Rehmsmeier, \"The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on "
     "imbalanced datasets,\" PLoS ONE, vol. 10, no. 3, Art. no. e0118432, 2015, doi: 10.1371/journal.pone.0118432.", "PubMed record"),
]

REFS = [e[1] for e in _ENTRIES]
NUM = {e[0]: i for i, e in enumerate(_ENTRIES, 1)}
READ_LEVEL = {e[0]: e[2] for e in _ENTRIES}

NOT_VERIFIED = [
    "Machine Learning Algorithms for Disease Prediction and Diagnosis (2025, Patient-Centric 6G): a chapter titled "
    "\"Machine Learning Algorithms for Disease Prediction\" appears in the contents listing of the book Patient-Centric 6G: A New Era in Smart "
    "Healthcare (Auerbach Publications, December 2025), but its authors, pages, DOI and abstract could not be confirmed.",
]
