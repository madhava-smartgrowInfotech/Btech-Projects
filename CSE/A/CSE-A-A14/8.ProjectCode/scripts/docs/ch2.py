"""Chapter 2: Literature survey."""

from . import facts as F
from .blocks import B, H1, H2, P, TAB
from .refs import cite
from .shared import GAP, LIT_HEADER, LIT_TABLE, NOT_LOCATED


def blocks():
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Approach to the Survey"),
        P("The survey starts from the base paper designated for the batch and follows its citations and the related work it names towards four topics that decide the design of this project: "
          "how churn is predicted from customer records, how the resulting models are explained, how class imbalance is handled, and which classifier families suit mixed categorical and numeric data. "
          "Only papers whose bibliographic details and quoted results could be read on the paper's own page (or, for results, its abstract) are described with numbers; "
          "where only the abstract could be read this is stated in the summary table of Section 2.7."),
        H2("2.2 The Base Paper"),
        P(f"Oprea and Bara {cite('oprea')}, \"Explaining customer churn through unified perturbation-based XAI soft computing\", IEEE Access, vol. 14, 2026, "
          "pose the question of which customer attributes matter most for retention and how to answer it quickly. Their method runs four perturbation-based explainers on a trained churn model: "
          "**Random Noise Perturbation (RNP)**, which adds noise to one feature at a time and measures the drop in recall; **Feature Ablation (FA)**, which removes a feature; "
          "**Input Marginalization (IM)**, which replaces its values by a reference; and **Adversarial Perturbation (AP)**, which builds adversarial examples. "
          "The four importance values are combined into one unified score, and only rows with a positive recall drop are kept."),
        P("The experiments use the public Telco customer churn data (7,043 customers, 21 columns, 26.5% churners) with a 70/30 split, so the test set has 2,113 rows. "
          "Seven classifiers are compared: Logistic Regression, SVC, Random Forest, Balanced Random Forest, CatBoost, XGBoost and LightGBM, with recall as the primary objective because a missed churner is costlier than a false alarm. "
          "The table below reproduces the metrics reported in the paper's own Table 2."),
        TAB("Metrics reported in the base paper (Table 2 of [1], Telco data, 30% test)", ["Model", "Accuracy", "Recall", "Precision"],
            [["Logistic Regression", "0.7120", "0.4112", "0.6210"], ["SVC", "0.7419", "0.5369", "0.6319"], ["Random Forest", "0.7932", "0.5634", "0.6734"],
             ["Balanced Random Forest", "0.7558", "0.8223", "0.6327"], ["CatBoost", "0.6990", "0.9077", "0.4719"], ["XGBoost", "0.7596", "0.7300", "0.5427"],
             ["LightGBM", "0.7317", "0.8293", "0.5037"]], widths=[2.4, 1.2, 1.2, 1.2], align=["l", "c", "c", "c"]),
        P("On explanation quality the paper reports high agreement between its unified perturbation score and SHAP (Spearman 0.8125, Kendall 0.7126, Jaccard 0.6885) and a large runtime advantage: "
          "about 289 s for SHAP, 35 s for LIME and 18 s for the perturbation explainers in its setting. Substantively it finds that customers on month-to-month contracts, customers with monthly charges above about $90 "
          "and customers with tenure below about 20 months are at the highest risk, and it recommends longer contracts, value-added services, personalised discounts and early engagement for new customers. "
          "In its discussion it proposes integrating the approach into a CRM as a decision-support layer and monitoring the stability of feature rankings as a drift signal."),
        P("The authors state their own limits: the conclusions are conditional on recall as the objective, the data set is a structured, moderate-dimensional table, and high-dimensional or highly correlated data "
          "may need staged or approximate ablation. The paper is a methods study; it does not describe a deployed application with scoring, risk bands and retention advice."),
        H2("2.3 Churn Prediction in Telecom"),
        P(f"Comparisons of classifiers for churn, such as Vafeiadis et al. {cite('vafeiadis')}, compare several machine learning techniques for churn prediction, the pattern that most later work follows: standard learners, one data set, a table of metrics. "
          f"Ahmad et al. {cite('ahmad')} apply machine learning to telecom churn on a big-data platform, which shows that the task is also a data-engineering problem at operator scale."),
        P(f"Recent work keeps the comparison style but adds explanation. El Attar and El-Hajj {cite('elattar')} compare eight models, including XGBoost, LightGBM and a soft-voting ensemble, on the same 7,043-customer Telco data with an 80/20 split "
          "and use SHAP to analyse features; they report XGBoost at accuracy 0.84 and ROC-AUC 0.932, with Logistic Regression at 0.78 and 0.864, and they caution that SHAP values describe the model's learned patterns and not causes. "
          f"Rasool et al. {cite('rasool')} use a stacking ensemble with SHAP on a different public data set (3,333 customers) and report accuracy 94.75%, recall 73.20% and F1 80.23%. "
          "These figures are quoted as reported by the authors; the three papers use different data, splits and sometimes balanced training sets, so they cannot be ranked against one another or against this project."),
        P(f"Sikri et al. {cite('sikri')} concentrate on the data side: a ratio-based balancing step applied to imbalanced churn data, followed by single and ensemble classifiers; ensembles outperform single models and XGBoost with a 75:25 ratio gives the best result "
          f"on their measures. Explainability for churn is also treated in {cite('leung')}, {cite('mohajon')} and {cite('wang')}, which the base paper cites; Szelag and Slowinski {cite('szelag')} explain churn with monotonic decision rules, "
          "a rule-based route to the same goal this project pursues with its retention engine."),
        H2("2.4 Explaining Predictions"),
        P(f"SHAP {cite('lundberg')} assigns each feature an additive contribution based on Shapley values and has a fast exact form for tree models {cite('treeshap')}; LIME {cite('ribeiro')} fits a simple surrogate model around one prediction. "
          f"Both are perturbation-based and both have known weaknesses: the base paper measures SHAP's runtime as the highest of the methods it compares, LIME's consistency as lower, and Slack et al. {cite('slack')} show that such explainers can be fooled by adversarial models. "
          "For a linear model the contribution of a feature is simply its coefficient times its (standardised) value; for tree ensembles, permutation importance measures how much a score falls when one feature is shuffled. "
          "This project uses these cheaper quantities as its built-in explanations and keeps an optional SHAP code path that was not exercised in this run because the library was not installed."),
        H2("2.5 Class Imbalance"),
        P(f"Churners are a minority, 26.5% of the Telco data and 26.4% of the synthetic data used here. A classifier trained on such data tends to favour the majority class and can reach high accuracy while missing most churners; "
          f"He and Garcia {cite('hegarcia')} survey the remedies. Two are used here: cost-sensitive learning through class weights, and SMOTE {cite('smote')}, which creates synthetic minority examples by interpolation and, to avoid leakage, "
          "is applied to the training split only. Chapter 8 measures what happens to recall when no handling is used."),
        H2("2.6 Classifier Families"),
        P(f"Logistic Regression is a transparent baseline whose coefficients can be read as effects. Decision trees give rules a business user can follow. Random forests {cite('breiman')} average many trees and handle mixed data and interactions with little tuning. "
          f"Gradient boosting {cite('friedman')} builds trees sequentially on the errors of the previous ones and is the family behind the XGBoost, LightGBM and CatBoost models of the base paper. "
          f"All five learners used in this project come from scikit-learn {cite('sklearn')}, which also provides the preprocessing, metrics and permutation-importance tools."),
        H2("2.7 Summary of Related Work"),
        TAB("Summary of the surveyed work (results as reported by the authors)", LIT_HEADER, LIT_TABLE, widths=[1.1, 1.5, 1.1, 1.3, 1.0], size=8.5),
        H2("2.8 Literature in the Batch Survey Document"),
        P("The batch's own literature-survey file lists five works. Two of them (the base paper and Sikri et al.) are analysed above, and the remaining three could not be located "
          "by a search on their titles in the public indexes available during this run, so they are neither described nor cited here:"),
        B(*NOT_LOCATED),
        P("The files that accompany the batch should be checked for the exact titles or links of these three. If they are found, they can be added to the summary table without changing the conclusions of this chapter."),
        H2("2.9 Research Gap"),
        P(GAP),
        P("Four specific gaps follow from the survey:"),
        B("Most churn studies stop at a model comparison. They report a table of metrics but not an application that scores every customer and keeps the result in a form a retention team can browse.",
          "Explanations are usually delivered as global importance plots. A retention agent needs the drivers of one customer and the effect of changing one attribute.",
          "Retention advice is generally left to the reader. Few papers link the drivers to concrete actions through rules that can be audited.",
          "Reported numbers depend heavily on the split, the balancing and the data set, and the same pipeline gives noticeably different scores on different 200-row test sets. This project therefore reports cross-validation and repeated-split spreads next to the headline figure."),
        P("This project addresses the first three directly and the fourth by measurement. It does not try to improve on the explainers of the base paper or to beat the metrics of boosted models on real data."),
    ]
