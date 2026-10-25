"""
Numbered IEEE reference list (single source). Base paper first, then the batch literature survey, then the
supporting papers. Every entry was either read in full (base paper and the two arXiv papers in archived_base_papers),
confirmed on the publisher/arXiv page, or is a standard textbook/journal reference whose citation details are
well established. Entries 7-9 come from the batch literature survey with title/year only and could not be verified;
they are listed with a note and are NOT cited in the text, the decks or the IEEE paper.

Use `cite("smote")` -> "[12]" so numbers never drift.
"""

_ENTRIES = [
    ("base", "J. M. C. de Albuquerque Neto, G. C. do Amaral and G. P. Temporao, \"Fraud detection in credit card transactions using quantum-assisted restricted Boltzmann machines,\" *IEEE Access*, vol. 14, pp. 62923-62932, 2026, doi: 10.1109/ACCESS.2026.3683308."),
    ("rfpaper", "A. H. M. Aburbeian and H. I. Ashqar, \"Credit card fraud detection using enhanced random forest classifier for imbalanced data,\" arXiv:2303.06514, Mar. 2023."),
    ("cfa", "X. Han and C. Wu, \"Validation-stage combinatorial fusion analysis for imbalanced credit-card fraud detection,\" arXiv:2606.10393, Jun. 2026."),
    ("shi", "J. Shi, \"Credit card fraud detection based on ANN and XGBoost,\" in *Proc. 1st Int. Conf. E-commerce and Artificial Intelligence (ECAI)*, SciTePress, 2024, pp. 195-199, doi: 10.5220/0013212700004568."),
    ("bhatt", "S. Bhattacharyya, S. Jha, K. Tharakunnel and J. C. Westland, \"Data mining for credit card fraud: A comparative study,\" *Decision Support Systems*, vol. 50, no. 3, pp. 602-613, 2011."),
    ("dp18", "A. Dal Pozzolo, G. Boracchi, O. Caelen, C. Alippi and G. Bontempi, \"Credit card fraud detection: A realistic modeling and a novel learning strategy,\" *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 29, no. 8, pp. 3784-3797, Aug. 2018."),
    ("pyspark", "\"Research on credit card fraud detection based on PySpark,\" in *Proc. 3rd Int. Conf. Computer Science and Mechatronics*, 2025. [Listed in the batch literature survey; authors and pages could not be verified, so it is not cited in the text.]"),
    ("ecom", "\"Enhancing e-commerce security: A novel approach to credit card fraud detection,\" 2025. [Listed in the batch literature survey; venue and authors could not be verified, so it is not cited in the text.]"),
    ("ijrpr", "\"Credit card fraud detection,\" *Int. J. Research Publication and Reviews*, 2025. [Listed in the batch literature survey; authors and volume could not be verified, so it is not cited in the text.]"),
    ("carcillo", "F. Carcillo, Y.-A. Le Borgne, O. Caelen, Y. Kessaci, F. Oble and G. Bontempi, \"Combining unsupervised and supervised learning in credit card fraud detection,\" *Information Sciences*, vol. 557, pp. 317-331, 2021."),
    ("dp15", "A. Dal Pozzolo, O. Caelen, R. A. Johnson and G. Bontempi, \"Calibrating probability with undersampling for unbalanced classification,\" in *Proc. IEEE Symp. Series on Computational Intelligence (SSCI)*, 2015, pp. 159-166."),
    ("smote", "N. V. Chawla, K. W. Bowyer, L. O. Hall and W. P. Kegelmeyer, \"SMOTE: Synthetic minority over-sampling technique,\" *J. Artif. Intell. Res.*, vol. 16, pp. 321-357, Jun. 2002."),
    ("tomek", "I. Tomek, \"Two modifications of CNN,\" *IEEE Trans. Syst., Man, Cybern.*, vol. SMC-6, no. 11, pp. 769-772, Nov. 1976."),
    ("hegarcia", "H. He and E. A. Garcia, \"Learning from imbalanced data,\" *IEEE Trans. Knowl. Data Eng.*, vol. 21, no. 9, pp. 1263-1284, Sep. 2009."),
    ("fernandez", "A. Fernandez, S. Garcia, M. Galar, R. C. Prati, B. Krawczyk and F. Herrera, *Learning From Imbalanced Data Sets*. Cham, Switzerland: Springer, 2018."),
    ("saito", "T. Saito and M. Rehmsmeier, \"The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets,\" *PLoS ONE*, vol. 10, no. 3, Art. no. e0118432, 2015."),
    ("fawcett", "T. Fawcett, \"An introduction to ROC analysis,\" *Pattern Recognition Letters*, vol. 27, no. 8, pp. 861-874, 2006."),
    ("powers", "D. M. W. Powers, \"Evaluation: From precision, recall and F-measure to ROC, informedness, markedness and correlation,\" arXiv:2010.16061, 2020."),
    ("breiman", "L. Breiman, \"Random forests,\" *Machine Learning*, vol. 45, no. 1, pp. 5-32, 2001."),
    ("xgb", "T. Chen and C. Guestrin, \"XGBoost: A scalable tree boosting system,\" in *Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining*, 2016, pp. 785-794."),
    ("catboost", "J. T. Hancock and T. M. Khoshgoftaar, \"CatBoost for big data: An interdisciplinary review,\" *J. Big Data*, vol. 7, no. 1, p. 94, Dec. 2020."),
    ("hinton06", "G. E. Hinton, S. Osindero and Y.-W. Teh, \"A fast learning algorithm for deep belief nets,\" *Neural Computation*, vol. 18, no. 7, pp. 1527-1554, Jul. 2006."),
    ("cd", "G. E. Hinton, \"Training products of experts by minimizing contrastive divergence,\" *Neural Computation*, vol. 14, no. 8, pp. 1771-1800, Aug. 2002."),
    ("pcd", "T. Tieleman, \"Training restricted Boltzmann machines using approximations to the likelihood gradient,\" in *Proc. 25th Int. Conf. Machine Learning (ICML)*, 2008, pp. 1064-1071."),
    ("guide", "G. E. Hinton, \"A practical guide to training restricted Boltzmann machines,\" in *Neural Networks: Tricks of the Trade*, 2nd ed. Berlin, Germany: Springer, 2012, pp. 599-619."),
    ("fischer", "A. Fischer and C. Igel, \"Training restricted Boltzmann machines: An introduction,\" *Pattern Recognition*, vol. 47, no. 1, pp. 25-39, 2014."),
    ("larochelle", "H. Larochelle, M. Mandel, R. Pascanu and Y. Bengio, \"Learning algorithms for the classification restricted Boltzmann machine,\" *J. Mach. Learn. Res.*, vol. 13, pp. 643-669, 2012."),
    ("liao", "R. Liao, S. Kornblith, M. Ren, D. J. Fleet and G. Hinton, \"Gaussian-Bernoulli RBMs without tears,\" arXiv:2210.10318, 2022."),
    ("anneal", "S. Kirkpatrick, C. D. Gelatt Jr. and M. P. Vecchi, \"Optimization by simulated annealing,\" *Science*, vol. 220, no. 4598, pp. 671-680, 1983."),
    ("adachi", "S. H. Adachi and M. P. Henderson, \"Application of quantum annealing to training of deep neural networks,\" arXiv:1510.06356, 2015."),
    ("ajagekar", "A. Ajagekar and F. You, \"Quantum computing assisted deep learning for fault detection and diagnosis in industrial process systems,\" *Computers & Chemical Engineering*, vol. 143, Art. no. 107119, Dec. 2020."),
    ("sklearn", "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" *J. Mach. Learn. Res.*, vol. 12, pp. 2825-2830, 2011."),
    ("imblearn", "G. Lemaitre, F. Nogueira and C. K. Aridas, \"Imbalanced-learn: A Python toolbox to tackle the curse of imbalanced datasets in machine learning,\" *J. Mach. Learn. Res.*, vol. 18, no. 17, pp. 1-5, 2017."),
    ("davis", "J. Davis and M. Goadrich, \"The relationship between precision-recall and ROC curves,\" in *Proc. 23rd Int. Conf. Machine Learning (ICML)*, 2006, pp. 233-240."),
]

REFS = [t for _, t in _ENTRIES]
KEYS = {k: i for i, (k, _) in enumerate(_ENTRIES, 1)}
UNVERIFIED = {"pyspark", "ecom", "ijrpr"}


def n(key):
    return KEYS[key]


def cite(*keys):
    """cite('smote','tomek') -> '[12], [13]'"""
    return ", ".join(f"[{KEYS[k]}]" for k in keys)
