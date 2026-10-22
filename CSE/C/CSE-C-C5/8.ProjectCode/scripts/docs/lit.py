"""Shared text used by the decks, the chapter documents, the report and (in condensed form) the paper: objectives, problem statement and the literature table."""

# from 6.OBJECTIVES&PROBLEM STATEMENT.docx, verbatim
OBJECTIVES = [
    "Collect student academic records, technical skills, aptitude scores and historical placement outcomes.",
    "Clean and encode the data and address imbalance between placed and unplaced students.",
    "Train and compare classifiers to predict placement eligibility for each student.",
    "Recommend suitable companies by matching student profiles against recruiter requirements.",
    "Identify the skill gaps that most reduce a student's placement probability.",
    "Provide dashboards for placement officers and evaluate using accuracy, precision and recall.",
]

PROBLEM_POINTS = [
    "Placement cells store student data but perform no predictive analysis on it.",
    "Students receive no early indication of readiness while there is still time to improve.",
    "Shortlisting is manual, slow and inconsistent across recruiters.",
    "No feedback identifies which specific skills a student should acquire next.",
]

NEED = "A system that predicts placement readiness early, recommends suitable companies, and tells each student which skills to close."

PROBLEM_STATEMENT = ("Given a student's academic record, skill and aptitude scores and a target company and role, estimate the probability that the student is "
                     "placed, explain which gaps against the company's requirements hold it back, recommend company-role alternatives where the estimated "
                     "probability is higher, and give placement officers and recruiters dashboards and shortlists - through a web application that a "
                     "placement cell can run on an ordinary PC, with accuracy reported honestly on the data actually available.")

# (Work, Approach, Data, Reported result, Limitation). Only facts from sources that were read or checked; the literature agent extends this list.
LIT_TABLE = [
    ["Prasanna Kumari et al. 2026 [1] (declared base paper)", "Logistic Regression, Random Forest and Gradient Boosting on student attributes; Streamlit app with batch CSV prediction, skill-gap analysis, PDF report and e-mail",
     "Synthetic student records (size not stated); 80:20 split", "No accuracy, F1 or AUC is reported in the paper", "No numeric evaluation; no company recommendation; synthetic data"],
    ["Heidari Fard and Tabrizi 2026 [2] (technique base)", "XGBoost with Platt calibration; kNN / SVM refinement of residual (misclassified or borderline) cases; university-program recommendation with feasibility filters; SHAP",
     "13,000 real GradCafe admission records, 2021-2025, enriched with QS rankings", "XGBoost 0.7241 accuracy; XGBoost + kNN hybrid 0.8723; Brier 0.1864; recommendation raised mean acceptance probability by 65.1%",
     "Residual set uses true labels; US-centric self-reported data; admissions, not placements"],
    ["Thangavel et al. 2017 [21]", "Decision-tree classifiers on historical student data; predicts one of five placement statuses (Dream, Core, Mass Recruiter, Not Eligible, Not Interested)",
     "Historical student records (size not read)", "Abstract only: identifies students needing technical and interpersonal support", "Categorical status, no probability; no company-level recommendation"],
    ["Khandale and Bhoite 2019 [22]", "Logistic, SVM, kNN, decision tree, random forest, bagging, boosting and voting compared",
     "Past placed / unplaced student records", "About 78% accuracy for XGBoost and for AdaBoost (abstract)", "Moderate accuracy; full results table not read"],
    ["Baffa et al. 2023 [15]", "Logistic regression, decision tree and random forest for graduate employability from CGPA, work-experience score, union group and gender",
     "218 Computer Science graduates, 2016-2021, one university", "Random forest 98% accuracy, F1 0.99", "Tiny single-department dataset; six variables"],
    ["Ambili and Abraham 2024 [16]", "Stacking ensemble on 20 student attributes to predict campus placement", "Student database records (size not stated in the abstract)",
     "90.21% accuracy", "No calibration, explanation or recommendation"],
    ["Gupta et al. 2024 [17] (ML-CPC)", "Exploratory analysis plus supervised classifiers and an ensemble to predict placement", "A recruitment dataset (size not named in the abstract)",
     "Accuracy 0.9524, precision 0.8667, recall 1.0, F1 0.9286", "Dataset size unstated; single split"],
    ["Pathak et al. 2025 [18]", "Voting classifier with hyper-parameter search and cross-validation", "Public Kaggle placement dataset",
     "Accuracy 0.8923, precision 0.9430, recall 0.8567, F1 0.8978, AUC 0.9433", "Public tabular benchmark; no recommendation layer"],
    ["Kumar et al. 2025 [19]", "Logistic regression, random forest and XGBoost on academics, projects, internships, certificates and aptitude; React + MongoDB application",
     "Student profiles (size not read)", "XGBoost best on accuracy and recall (values not in the abstract)", "Numbers not available from the abstract"],
    ["Sanjana et al. 2025 [20]", "SVM for placement prediction plus a Deep Q-Network for scheduling and job matching", "Dataset size not stated; 80:20 split",
     "87.4% accuracy (SVM); 21% better job-matching accuracy and 28% fewer scheduling conflicts (DQN)", "Data not described; no calibration"],
]

# Theme grouping used by chapter 2 and the paper: reference numbers per theme
THEMES = {
    "placement classification": [15, 16, 17, 18, 19, 21, 22],
    "placement systems and matching": [20, 21],
    "educational data mining": [23],
    "calibration and explanation": [4, 5, 8, 9],
    "recommendation": [13],
}
