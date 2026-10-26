"""Shared text used by the decks, the chapter documents, the report and (in condensed form) the paper: objectives, problem statement, literature table."""

# from 6.OBJECTIVES&PROBLEM STATEMENT.docx, verbatim
OBJECTIVES = [
    "Collect a startup dataset covering funding history, team background, sector, location and outcome.",
    "Clean the data and engineer features capturing funding velocity, team experience and market context.",
    "Address class imbalance between successful and failed startups.",
    "Train and compare Logistic Regression, Decision Tree, Random Forest and boosting ensembles.",
    "Identify the features that most strongly separate successful from failed startups.",
    "Evaluate using accuracy, precision, recall, F1-score and ROC-AUC.",
]

PROBLEM_POINTS = [
    "Startup success is judged subjectively, leading to inconsistent investment decisions.",
    "Failure causes become obvious only after capital has already been committed.",
    "Success is rare in the data, so naive models under-predict the positive class.",
    "A prediction without stated drivers gives a founder nothing to act upon.",
]
NEED = ("a machine learning model that predicts startup success early from structured indicators and names the factors driving each prediction.")

PROBLEM_STATEMENT = ("Given the funding history, team and ecosystem indicators, sector, location and (optionally) a short business description of an early-stage startup, "
                     "estimate whether it is more likely to reach SUCCESS (acquisition or IPO) or FAILURE (closure), report a confidence score, "
                     "name the features and the comparable historical startups that drive the estimate, and state plainly how reliable such an estimate is.")

GAP = ("The surveyed work applies ensemble methods to startup success prediction. The gap is systematic feature engineering around funding velocity and team "
       "composition, with explicit handling of the rare-success class.")

# (Work, Approach, Data, Reported result, Limitation); only facts from the PDFs read or confirmed pages
LIT_TABLE = [
    ["Panjwani et al. 2026 [1] (base paper)", "LR, Random Forest, SVM, Gradient Boosting on funding, team, industry and location features; ADASYN oversampling; 70:30 split; Flask web application",
     "Crunchbase / Kaggle startup data (size not stated)", "Best ensembles: accuracy 85-92 % (no per-model table)", "No dataset size, no table of results; no ROC-AUC values; no leakage control stated"],
    ["Maarouf et al. 2026 [2]", "kNN-based in-context learning: retrieve the k most similar past startups and show them with outcomes to an LLM; compared with LR, RF, XGBoost",
     "4,034 Crunchbase startups (1,418 successful, 35.15 %), 5 x 80/20 stratified splits", "Balanced accuracy 0.713 (F1 0.632) at k=50 vs LR 0.631, RF 0.634, XGBoost 0.618; fused LLM trained on 20,172 startups 0.743",
     "Needs an LLM; data-scarce setting; text descriptions required"],
    ["Mashhadi et al. 2026 [3]", "Interpretable ML (LR, RF, XGBoost, LightGBM, CatBoost) with inverse-prevalence weights and SMOTE-NC; SHAP; leakage-safe temporal splits",
     "Crunchbase firm-quarter panel 2010-2023 matched to USPTO data", "AUROC 0.921 (patents, 24 mo), 0.817 (next funding, 12 mo), 0.872 (exit, 36 mo); PR-AUC 0.631 / 0.220 / 0.559",
     "Panel data and patent matching not available to this project; no web tool"],
    ["Bidgoli et al. 2024 [7] (as summarised by [1])", "Comparison of RF, Gradient Boosting, SVM and LR on startup data", "Not restated in [1]", "Ensembles above 80 % accuracy, ahead of conventional models (per [1])",
     "Details not re-read; reported through [1]"],
    ["Zbikowski and Antosiuk 2021 [9] (as summarised by [1])", "Bias-free business-success prediction from Crunchbase; attention to look-ahead bias", "Crunchbase", "Shows that using future information gives unrealistic accuracy (per [1])",
     "Details not re-read; reported through [1]"],
    ["Ross et al. 2021 [11] (as summarised by [1])", "CapitalVX: ensemble model combining several data sources for startup selection and exit prediction", "Multiple sources", "Up to 90 % accuracy (per [1])",
     "Details not re-read; reported through [1]"],
    ["Choi 2024 [13] (as summarised by [1])", "PCA-enhanced ML models for startup success", "Not restated in [1]", "PCA improved classification accuracy (per [1])", "Details not re-read; reported through [1]"],
    ["Gius 2025 [16]", "Judge disagreement in 67 venture competitions as a predictor of startup success", "67 venture competitions", "More disagreement among judges predicts a higher chance of success, mostly when the idea is unique",
     "Competition entrants, not a general population; not an ML classifier"],
    ["Bhandari 2025 [17]", "Questionnaire survey with correlation and multiple regression on venture capital, access to capital, networking and market conditions", "120 survey respondents in Nepal",
     "Positive association of venture capital with startup success and growth", "Association from a small survey; no prediction"],
]

# one short statement per source for the survey chapter, grouped by theme (keys into refs.KEY)
THEMES = {
    "Machine-learning prediction of startup success": ["base", "krishna", "bidgoli", "li", "ross", "tomy", "hbg", "martinez"],
    "Features, bias and interpretability": ["jafari", "zbikowski", "mashhadi", "bonaventura", "choi"],
    "Retrieval, text and language models": ["maarouf", "fused", "icl"],
    "Economic evidence on venture finance": ["gius", "bhandari"],
}
