"""Literature-survey content (table, themed paragraphs, base-paper analysis, gap, dataset notes).

Only facts read in the source (see refs.READ_LEVEL) are stated; numbers are copied from the papers' own text or abstracts.
The three Springer chapters (2025) were verified as bibliographic records only, so nothing about their results is claimed.
"""

from .refs import NUM

n = NUM

LIT_HEADER = ["Work", "Approach", "Data", "Reported result", "Limitation"]

LIT_TABLE = [
    [f"Alam et al., 2026 (base paper) [{n['base']}]",
     "Five classifiers, nested cross-validation, full and TOP-10 feature sets, SHAP and counterfactual explanations",
     "UCI thyroid, 7,200 samples, 21 features, 3 classes",
     "Random Forest / CatBoost accuracy 0.996-0.997, AUC 0.999-1.000; SVC 0.965-0.967",
     "One disease; class imbalance; no external validation"],
    [f"Zannat et al., 2025 [{n['bangla']}]",
     "Eight classifiers plus soft and hard voting ensembles; PCA; 5-fold CV tuning",
     "Bangla symptoms-disease set: 758 relations, 85 diseases, 172 symptoms; 607 train / 151 test",
     "Ensembles accuracy 0.98; Random Forest 0.97; Decision Tree 0.78",
     "Symptom flags only, no laboratory values; small data; single 80/20 split"],
    [f"Al Nahian et al., 2022 [{n['nahian']}]",
     "Several classifiers on survey-based symptom data",
     "Survey data for 11 common diseases (e.g. flu, migraine, heart disease, diabetes)",
     "Abstract names a best classifier but gives no numbers",
     "No quantitative result in the abstract; symptom survey, not clinical measurements"],
    [f"Kamakshamma et al., 2025 [{n['multi25']}]",
     "Django web app with one model per disease; recall prioritised; threshold lowered to 0.2 for diabetes",
     "Kaggle: stroke 5,110, student depression 27,901, diabetes 100,000 records",
     "Recall 94.73% (stroke), 88.39% (depression), 91.02% (diabetes)",
     "Different diseases; public Kaggle data; no liver or kidney module"],
    [f"Sun and Sun, 2024 [{n['sun']}]",
     "Six supervised classifiers compared with accuracy, precision, recall and F1",
     "Pima Indians Diabetes dataset",
     "Gradient boosting best, 81.8% accuracy",
     "Authors state results may apply only to this sub-population"],
    [f"Islam et al., 2023 [{n['islam']}]",
     "12 supervised classifiers after reducing 25 variables to about 30% of them",
     "Chronic kidney disease data, 25 variables including the class",
     "XGBoost best: accuracy 0.983, precision, recall and F1 0.98",
     "Single disease; one data set; no external test"],
    [f"Salekin and Stankovic, 2016 [{n['salekin']}]",
     "Classifier over 24 predictive parameters; attribute ranking; cost-accuracy trade-off",
     "400 individuals, 250 with CKD",
     "F1 0.993, RMSE 0.1084; error 56% lower than CKD-EPI equation",
     "Small cohort; kidney only"],
    [f"Straw and Wu, 2022 [{n['straw']}]",
     "Re-created published liver-disease models; sex-stratified error analysis, 100 repeats",
     "Indian Liver Patient Dataset",
     "Accuracy about 71% (logistic regression) to about 79% (SVM); higher false-negative rate in women",
     "Shows bias, does not propose a deployable fix"],
    [f"Smith et al., 1988 [{n['pima']}]",
     "ADAP neural-network learner forecasting diabetes onset; sensitivity-specificity analysis",
     "High-risk Pima Indian population (origin of the Pima data set)",
     "Cut-off 0.448 gave 76% sensitivity and specificity on 192 held-out cases",
     "Early method; one population"],
]

LIT_GROUPS = {
    "single-disease classical ML": [
        f"Most published systems model one disease at a time. For diabetes, a 2024 comparison of six classifiers on the Pima data found gradient boosting best at 81.8% accuracy "
        f"and warned that the result may apply only to that sub-population [{n['sun']}]; the data set itself goes back to a 1988 study that forecast diabetes onset in a Pima Indian cohort "
        f"with 76% sensitivity and specificity [{n['pima']}].",
        f"For kidney disease, twelve supervised classifiers were compared on chronic-kidney-disease data and XGBoost scored best with 0.983 accuracy [{n['islam']}], "
        f"while an earlier study on 400 individuals (250 with CKD) reported an F1-measure of 0.993 and ranked which attributes predict the disease [{n['salekin']}]. "
        f"A 2025 Springer chapter also treats kidney disease prediction with machine-learning techniques [{n['kidneychap']}].",
        f"For liver disease, re-created models on the Indian Liver Patient Dataset reached about 71% (logistic regression) to about 79% (SVM) accuracy, and showed a higher false-negative rate for female patients [{n['straw']}].",
    ],
    "multi-disease and symptom-based systems": [
        f"Multi-disease work tends to use symptoms rather than laboratory values. A Bangla symptoms-disease data set of 758 relations covering 85 diseases was used to compare eight classifiers; "
        f"soft and hard voting ensembles reached 0.98 accuracy, Random Forest 0.97 and Decision Tree 0.78 [{n['bangla']}]. A survey-based study predicted 11 common diseases from reported symptoms [{n['nahian']}].",
        f"A 2025 Django application bundles three separate models (stroke, student depression, diabetes) and favours recall over accuracy, lowering the diabetes threshold to 0.2 "
        f"to raise recall from 71.97% to 91.02% [{n['multi25']}]. None of the surveyed multi-disease systems combines diabetes, heart, liver and kidney risk from routine clinical values behind one interface.",
        f"Two further 2025 chapters in the same Springer volume cover deep learning for disease prediction [{n['dlchap']}] and skin disease prediction [{n['skinchap']}]; they were confirmed as bibliographic records only.",
    ],
    "explainability": [
        f"The base paper pairs SHAP attributions with counterfactual 'what-if' analysis for thyroid classification [{n['base']}]. SHAP assigns each feature an additive contribution to a single prediction [{n['shap']}], "
        f"and counterfactual explanations describe the smallest change to the inputs that would alter the decision without opening the model [{n['wachter']}].",
        f"The base paper also notes that SHAP and counterfactuals add computational overhead that may hinder real-time use in resource-constrained settings [{n['base']}]. "
        f"This project's application shows only a class and a confidence, so explanation remains an open objective (Chapter 10 of the report).",
    ],
    "imbalance, validation and evaluation practice": [
        f"Selecting a model on the same data used to report its error gives optimistic estimates; cross-validation used for both selection and assessment is biased [{n['varma']}], "
        f"which is why the base paper nests its tuning inside an outer cross-validation loop [{n['base']}]. This project selected a model on one hold-out split, so its reported best-model scores carry that bias.",
        f"Oversampling with SMOTE [{n['smote']}] was tried by the base paper and rejected because minority recall rose by less than 2% while precision fell [{n['base']}]. "
        f"On imbalanced data the precision-recall plot is more informative than the ROC plot [{n['saito']}], and the Matthews correlation coefficient is more reliable than F1 or accuracy for binary evaluation [{n['chicco']}].",
        f"The classical algorithms used here are standard: logistic regression [{n['hosmer']}], random forests [{n['rf']}] and support-vector machines [{n['svm']}], implemented in scikit-learn [{n['scikit']}].",
    ],
    "datasets": [
        f"Four public benchmarks match this project's four conditions: Pima Indians Diabetes [{n['pima']}], UCI Heart Disease (Cleveland) [{n['cleveland']}, {n['detrano']}], "
        f"the Indian Liver Patient Dataset [{n['ilpd']}] and UCI Chronic Kidney Disease [{n['ckd']}]. They are small (303 to 768 records) and the kidney, heart and Pima files contain missing or implausible entries that need handling.",
        f"Reported accuracies on these data sets depend heavily on preprocessing and split: the Pima comparison above gave 81.8% at best [{n['sun']}], whereas kidney data reached 0.983 [{n['islam']}].",
    ],
}

BASE_PAPER_ANALYSIS = [
    f"The base paper, Alam et al., \"Enhancing Thyroid Disease Diagnosis With Machine Learning and Counterfactual Explainable AI\" (IEEE Access, vol. 14, 2026) [{n['base']}], "
    "builds an interpretable classifier for three-class thyroid status (Normal, Hypothyroid, Hyperthyroid) from the UCI thyroid data set. The ann-train and ann-test files were merged into "
    "7,200 samples with 21 clinical features (demographics, treatment history and laboratory markers such as TSH, T3, TT4, T4U and FTI); the paper reports 6,666 normal, 368 hyperthyroid and 166 hypothyroid cases.",
    "Five classifiers are compared: Support Vector Classifier, Random Forest, Extra Trees, AdaBoost and CatBoost. Evaluation uses nested cross-validation: an outer stratified 5-fold loop gives the reported scores "
    "and an inner 3-fold grid search on accuracy selects hyper-parameters, so model selection never sees the outer test folds. Scaling is fitted on training folds only. Two feature regimes are tested, all 21 features and a "
    "TOP-10 consensus set (TSH, FTI, T3, TT4, T4U, on thyroxine, query hypothyroid, psych, thyroid surgery, sex) chosen by agreement of six ranking methods.",
    "The results are very high: Random Forest and CatBoost reach 0.996-0.997 accuracy and F1 with AUC 0.999-1.000 under both feature sets, while SVC trails at 0.965-0.967 accuracy and 0.990-0.992 AUC. "
    "The TOP-10 set matches or slightly improves on the full set. SMOTE was tried and rejected because minority-class recall rose by less than 2% for hyperthyroid cases while precision fell. "
    "Random Forest is chosen for deployment, and SHAP plus counterfactual analysis show TSH and FTI as the main drivers, consistent with endocrine physiology.",
    "Strengths: a real clinical data set, leakage-safe nested validation, consensus feature selection, and two complementary explanation methods. The authors acknowledge class imbalance, the absence of etiological markers "
    "and of external validation, the overhead of SHAP and counterfactuals in real-time use, and demographic imbalance that raises fairness concerns.",
    "Relation to this project: the project adopts the base paper's central idea of comparing several classical classifiers by held-out metrics and extends the scope from one disease to four behind one interface. "
    "It does not reproduce the thyroid experiment, and it is weaker in three respects that the report states plainly: its data are synthetic rather than clinical, it uses one stratified 80/20 split with fixed settings "
    "instead of nested cross-validation, and the application shows no SHAP-style or counterfactual explanation. Because disease, data, class structure and protocol all differ, accuracy figures cannot be compared with the paper's.",
]

GAP = (
    "The surveyed papers each target one disease in isolation, or use symptom flags rather than routine laboratory values, and the one multi-disease web application found covers different conditions "
    f"(stroke, depression, diabetes) [{n['multi25']}]. The base paper offers rigorous validation and explanation for a single disease [{n['base']}]. The gap is a single pipeline that screens several conditions "
    "(diabetes, heart, liver and kidney) from one set of routine clinical parameters, compares the same four classical algorithms on each, evaluates them honestly, and, ideally, explains which parameters drove each prediction."
)

DATASET_NOTES = [
    f"Pima Indians Diabetes: 768 female patients aged 21 or over of Pima heritage, 8 clinical features plus an outcome; origin in the 1988 ADAP study [{n['pima']}]; physiologically impossible zeros in glucose, blood pressure, skin thickness, insulin and BMI behave as missing values.",
    f"UCI Heart Disease (Cleveland): 303 instances, 13 features plus a diagnosis, donated in 1988 by Janosi, Steinbrunn, Pfisterer and Detrano; CC BY 4.0 [{n['cleveland']}, {n['detrano']}].",
    f"Indian Liver Patient Dataset (ILPD): 583 instances (416 liver patients, 167 non-patients), 10 features plus a selector label, from north-east Andhra Pradesh; CC BY 4.0 [{n['ilpd']}].",
    f"UCI Chronic Kidney Disease: 400 instances (250 CKD), 24 features plus the class, with missing values, donated in 2015; CC BY 4.0 [{n['ckd']}, {n['salekin']}].",
]
