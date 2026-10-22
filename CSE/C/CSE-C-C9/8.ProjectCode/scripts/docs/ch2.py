"""Chapter 2: Literature survey. Only facts recorded in docs/lit_notes.md or visible in the base paper are used."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F
from .shared import LIT_TABLE, RESEARCH_GAP  # noqa: F401  (re-exported)


def blocks():
    ba = F.BASE_PAPER
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("This chapter reviews the work on which the project rests. It starts with the base paper, which supplies the framework that the project adapts, and then "
          "groups the related work into four themes: machine learning for financial distress and credit risk, explainable artificial intelligence in finance, data "
          "quality and privacy in credit modelling, and forecasting. The batch literature survey lists five entries: the base paper, a 2025 study of sovereign credit "
          "risk forecasting, and three further entries recorded by title and year only. The base paper and the sovereign study were read and are discussed here; "
          f"the other three entries {n('survey1', 'survey2', 'survey3')} were recorded in the batch literature survey and could not be independently verified, so no claim is built on them. "
          "Two further credit-risk papers kept in the batch archive were read in full or in part and are used as related work, and the classical references are taken from the "
          "reference list of the base paper itself."),
        H2("2.2 Base paper analysis"),
        P(f"The base paper is: {ba}"),
        H3("Problem and contribution"),
        P(f"Kim and Sun {n('base')} observe that research on financial-distress prediction concentrates on publicly traded corporations and stock-market signals, while "
          "non-market organisations such as hospitals, universities and public bodies are under-studied, and that predictive accuracy alone is not enough for high-stakes "
          "financial use because regulators and managers need to know why an organisation is predicted to be in distress. They present a four-stage framework and instantiate it on "
          "Korean hospitals. They are explicit that the framework assembles standard components and that its contribution lies in the domain-adaptive integration of those components."),
        H3("The four stages"),
        N("**Domain-adaptive feature engineering.** Structured disclosures with 236 line items per hospital-year are reduced to 11 interpretable features: raw values are turned into "
          "ratios that are comparable across organisation sizes (for example labour cost over revenue), institutional characteristics are encoded as binary indicators, and time and size "
          "indices are added. Missing values are handled by listwise deletion when rare and ratios are winsorised at the 1st and 99th percentiles. Features with correlation above 0.85 are removed.",
          "**Multi-model training.** Logistic Regression (L2, C = 1.0, standardised features), Random Forest (100 trees), Gradient Boosting (100 trees, depth 3, learning rate 0.1), "
          "XGBoost (100 trees, default parameters) and a small neural network (two hidden layers of 64 and 32 units, early stopping). Hyperparameters are kept at defaults for reproducibility, "
          "and class rebalancing is not applied when the minority class exceeds 30%.",
          "**SHAP interpretation.** TreeExplainer provides global importance (mean absolute SHAP), directional effects through beeswarm plots, awareness of compositional collinearity among cost shares "
          "and a reconciliation of SHAP rankings with logistic-regression coefficients through a variance-versus-effect-size argument.",
          "**Domain-specific validation.** Hospital-level Group K-Fold (primary), a temporal hold-out, standard stratified K-Fold (reference), a counterfactual subsidy analysis and panel fixed-effects regression."),
        H3("Data"),
        P("The data are the mandatory public financial disclosures of Korean hospitals with 300 or more beds: a balanced panel of 165 hospitals observed from 2019 to 2023, giving 825 "
          "hospital-year observations. The target is a deficit indicator (net income below zero), positive for 41.2% of observations overall, with yearly deficit rates of 35.2%, 46.7%, 26.1%, "
          "29.7% and 69.1% from 2019 to 2023. The jump in 2023 follows the withdrawal of pandemic subsidies and makes the panel a test of robustness to distribution shift."),
        H3("Reported results"),
        TAB("Principal results reported in the base paper", ["Quantity", "Value"], [
            ["ROC-AUC under hospital-level Group K-Fold: XGBoost / Gradient Boosting / Random Forest", "0.842 / 0.840 / 0.831"],
            ["ROC-AUC under Group K-Fold: Logistic Regression / small neural network", "0.776 / 0.772"],
            ["Modified Altman Z'' score as a baseline", "0.680"],
            ["Temporal validation (train 2019-2022, test 2023); year-only baseline", "0.780; 0.659"],
            ["Forward prediction of next-year deficit (665 hospital-year pairs)", "0.772"],
            ["Rolling-origin AUC per split; mean", "0.731, 0.850, 0.808, 0.809; 0.800"],
            ["Random Forest under random CV versus Group K-Fold", "0.860 versus 0.831"],
            ["XGBoost after removing subsidy ratio and year; after also removing the three cost ratios", "0.794; 0.651"],
            ["XGBoost default versus best of a 25-configuration random search", "0.827 versus 0.834"],
            ["Mean |SHAP|: material cost ratio / labour cost ratio / university indicator", "0.777 / 0.729 / 0.537"],
            ["DeLong p-values: XGBoost vs Gradient Boosting / vs Random Forest / vs Logistic Regression", "0.396 / 0.546 / 0.028"],
            ["Counterfactual gap between observed and latent distress (2021); fixed-effects post-subsidy effect", "57.5 pp; 28.9 pp (p < 0.001)"],
        ], widths=[4.4, 1.9], size=10, align=["l", "c"]),
        P("Three observations matter for this project. First, the three ensemble models are statistically indistinguishable from one another (all pairwise DeLong p-values above 0.39), and only XGBoost "
          "is significantly better than Logistic Regression, so the ordering among ensembles should not be over-read. Second, the gap between random and entity-grouped cross-validation (0.860 versus 0.831 "
          "for Random Forest) quantifies leakage when the same entity appears on both sides of a split; the paper therefore treats the grouped protocol as primary. Third, the authors state that SHAP "
          "explains the model's learned associations and not causal mechanisms, that attributions of collinear shares are unstable, and that their econometric analysis has limits, which is the "
          "stance this project also adopts."),
        H3("Strengths and weaknesses of the base paper"),
        B("Strengths: a clear, stage-wise framework; entity-level and temporal validation; a significance test between models; robustness checks (ablation, forward prediction, rolling origin, tuning); and an honest discussion of SHAP's limits.",
          "Weaknesses for the purposes of this project: the unit is an organisation, not a person; the panel is small (825 rows); the label is mechanically linked to some features; and there is no application layer, so a non-expert cannot use the framework."),
        H3("What this project takes from it"),
        P("The project keeps the four-stage structure (engineered features, four of the five model families, SHAP, validation) and the discipline of stating the validation protocol next to every number. It does "
          "not reproduce the paper's temporal, counterfactual or econometric analyses, because the individual-level data used here have one row per person and no time dimension."),
        H2("2.3 Related work by theme"),
        H3("Machine learning for financial distress and credit risk"),
        P(f"The base paper describes three generations of methods {n('base')}. The first is linear: Altman's Z-score {n('altman')} and Ohlson's logistic model {n('ohlson')}. The second is ensemble learning: "
          f"random forests {n('breiman')}, gradient boosting {n('friedman')} and XGBoost {n('xgboost')}. Barboza et al. {n('barboza')} compared such methods extensively and, as summarised in the base paper, found that "
          f"ensembles outperform traditional statistical models for bankruptcy prediction; Zieba et al. {n('zieba')} showed that ensemble boosted trees with synthetic feature generation improve predictive performance further. "
          f"The third generation uses deep learning: Mai et al. {n('mai')} applied recurrent networks to textual disclosures, and Moscatelli et al. {n('moscatelli')} combined traditional financial features with machine learning "
          "for corporate default forecasting. Deep models trade interpretability for flexibility and typically need more data than organisational settings supply. For tabular data of moderate size, "
          f"Grinsztajn et al. {n('grinsztajn')} report that tree-based models still outperform deep learning, which supports the choice of tree ensembles here."),
        P(f"Abid {n('abid')} forecasts credit-default probabilities implied by credit-default-swap spreads for Egypt, Morocco and Saudi Arabia during periods of political crisis. Five machine-learning models (linear, ridge, lasso, "
          "XGBoost and kernel ridge regression) and four deep models (RNN, LSTM, BiLSTM and GRU) are compared; linear regression performs best and the RNN and GRU are competitive, and the forecast probabilities are mapped to implied "
          "ratings. Only the abstract of this study was available for this survey, so its data periods and error metrics are not discussed. Its relevance is the forecasting orientation and the observation that a simple model can be hard to beat."),
        H3("Explainable AI in finance"),
        P(f"The need for interpretability in financial applications has produced a large literature {n('arrieta')}. Ribeiro et al. {n('lime')} introduced LIME, which approximates a model locally with an interpretable surrogate; "
          f"Lundberg and Lee {n('shap')} grounded feature attribution in Shapley values from cooperative game theory, and Lundberg et al. {n('treeshap')} added TreeExplainer, which computes exact values for tree ensembles efficiently. "
          f"Cerneviciene and Kabasinskas {n('cerneviciene')} reviewed explainable AI in finance, identified SHAP as the most widely adopted method and noted that few studies provide systematic end-to-end frameworks. Bussmann et al. {n('bussmann')} "
          f"used Shapley values to explain credit-risk models for lending to small and medium enterprises, and Gramegna and Giudici {n('gramegna')} evaluated the discriminative power of SHAP and LIME in credit risk. Doshi-Velez and Kim {n('doshi')} "
          f"called for rigorous evaluation of interpretability claims, and Molnar et al. {n('molnar')} separated inherently interpretable models from post-hoc explanation, arguing that both are needed. This project follows that advice: "
          "it reports a logistic-regression baseline with its coefficients beside SHAP, and it labels every explanation as an association."),
        H3("Data quality and privacy in credit modelling"),
        P(f"Maurino {n('maurino')} studies how missing values, noise, outliers and label errors in the training data affect ten commonly used credit-risk models on an open-source dataset, using the Pucktrick library to inject "
          "controlled corruption. Some imperfections (outliers, missing values, duplicates) can sometimes improve a given model, with a reported gain of up to 17% in F1 for specific models, while noise and mislabelling generally degrade performance; "
          "the effect depends on the model, the feature and the type of error. The study suggests extending the work to multiclass tasks, other datasets and fairness. The lesson for this project is to treat data preparation as part of the model: "
          "the Adult data contain missing markers in workclass, occupation and native country, and the pipelines impute them inside cross-validation."),
        P(f"Zhang et al. {n('zhang')} address a different problem: credit-risk models improve when alternative data, such as mobile-phone or e-commerce records, are added to demographic, financial and credit-history data, but those data sit with "
          "external parties and sharing them infringes privacy. They propose PrivacyCredit, a privacy-preserving, model-confidential and lossless method based on vertical federated learning, and report that it matches the performance of the model "
          "trained on the insecure plaintext combination. The paper also notes that XGBoost is widely used for credit risk because of its interpretability and predictive performance. It is relevant here as a statement of what the "
          "project does not do: it uses only the data the user types in and stores nothing."),
        H3("Forecasting"),
        P(f"Exponential smoothing with trend and seasonality was introduced by Winters {n('winters')} building on Holt's work {n('holt')}; textbook treatments and accuracy measures are given by Hyndman and Athanasopoulos {n('hyndmanbook')} "
          f"and Hyndman and Koehler {n('hyndman06')}. The method is simple, has few parameters and produces forecasts with an interval, which suits an index with a stable trend and yearly seasonality. It is implemented in statsmodels {n('statsmodels')}. "
          "The survey found no study that places such a forecast beside an individual-level explainable assessment."),
        H3("Other entries recorded in the batch literature survey"),
        P(f"The batch literature survey also records a 2025 title on credit and financial cycle synchronisation and sovereign credit risk {n('survey1')}, a 2024 title on financial and credit risk research {n('survey2')} and a 2025 "
          f"conference title on a multimodal credit-risk forecasting system for financial text analysis {n('survey3')}. These entries give only a title and a year, were not independently verified, and are not used for any factual claim in this report."),
        TAB("Summary of the surveyed works", ["Work", "Approach", "Data", "Reported result", "Limitation"], LIT_TABLE,
            widths=[1.2, 1.5, 1.1, 1.4, 1.1], size=8.5, align=["l", "l", "l", "l", "l"]),
        H2("2.4 Datasets and algorithms used in the literature and in this project"),
        P(f"The datasets in the surveyed work are organisational or sovereign: a Korean hospital panel in the base paper {n('base')}, sovereign credit data in Abid {n('abid')}, an open-source credit-risk dataset in Maurino {n('maurino')}, "
          f"and a credit dataset linked with alternative data in Zhang et al. {n('zhang')}. None is a public file of individual demographic records. For the individual profile, this project uses the Adult (Census Income) data, "
          f"which were extracted from the 1994 US census and introduced to the research community by Kohavi {n('kohavi')}; they are distributed by the UCI Machine Learning Repository {n('uci')}. The data hold "
          f"{F.N_ROWS:,} records (32,561 in the training file and 16,281 in the test file) with 14 attributes and a binary income label, of which {F.pct(F.RM['positive_rate_all'], 2)} are in the higher-income class. "
          f"Missing values are marked with a question mark in workclass ({F.RM['missing_cells_raw']['workclass']:,} cells), occupation ({F.RM['missing_cells_raw']['occupation']:,}) and native country ({F.RM['missing_cells_raw']['native-country']:,})."),
        P("Because the Adult records have no time dimension, they cannot support forecasting. The forecasting component therefore uses a separate monthly series, the Household Financial Conditions Index, which is synthetic and documented as such "
          "(trend, yearly seasonality, noise and a mid-2020 downturn, 132 monthly values). It is used only to demonstrate the method, and every screen and document that shows it says so."),
        TAB("Algorithms in the base paper and in this project", ["Algorithm", "Base paper", "This project", "Role in this project"], [
            ["Logistic Regression", "Yes (L2, C = 1.0, standardised)", "Yes (C = 1.0, standardised)", "Interpretable baseline; statsmodels logit gives coefficients and p-values"],
            ["Random Forest", "Yes (100 trees)", "Yes (300 trees)", "Bagged-tree comparator"],
            ["Gradient Boosting", "Yes (100 trees, depth 3)", "Yes (scikit-learn defaults)", "Boosted-tree comparator"],
            ["XGBoost", "Yes (100 trees, defaults)", "Yes (400 trees, depth 6, learning rate 0.05)", "Selected model by ROC-AUC"],
            ["Neural network (MLP)", "Yes (64 and 32 units)", "No", "Not reproduced"],
            ["SHAP TreeExplainer", "Yes (global and local)", "Yes (global at training, local per request)", "Plain-language explanation"],
            ["Group K-Fold, temporal hold-out", "Yes", "No (one row per person)", "Replaced by stratified 5-fold CV and a stratified test split"],
            ["Counterfactual and fixed-effects analysis", "Yes", "No", "Replaced by a labelled what-if simulation"],
            ["Holt-Winters exponential smoothing", "No", "Yes (additive trend and season, 12 months)", "Forecast of the economic index"],
        ], widths=[1.4, 1.6, 1.7, 1.6], size=9.5, align=["l", "l", "l", "l"]),
        H2("2.5 Strengths and limitations of existing work"),
        TAB("Strengths and limitations of the surveyed approaches", ["Theme", "Strengths", "Limitations"], [
            ["Statistical scores (Z-score, logit)", "Transparent, cheap, long track record " + n("altman", "ohlson"), "Linear, few ratios; the base paper reports a Z'' AUC of 0.680 on its panel " + n("base")],
            ["Tree ensembles", "Capture non-linear interactions; strong on tabular data " + n("barboza", "grinsztajn"), "Opaque without an explanation layer; ensembles are statistically close to each other in the base paper"],
            ["Deep models", "Flexible; can use text and sequences " + n("mai", "abid"), "Need more data; weaker interpretability; no gain over linear regression in the sovereign study"],
            ["SHAP and LIME", "Local and global attribution " + n("shap", "treeshap", "lime"), "Associational, not causal; unstable for collinear features " + n("base", "doshi")],
            ["Data-quality studies", "Show which errors hurt which models " + n("maurino"), "One dataset, binary task, fairness not studied"],
            ["Privacy-preserving learning", "Uses more data without exposing it " + n("zhang"), "Needs partners that hold alternative data; does not address explanation to the end user"],
        ], widths=[1.5, 2.4, 2.4], size=9.5, align=["l", "l", "l"]),
        P("Across the themes, three weaknesses recur. The unit of analysis is the organisation or the country, not the person. The output is a score or a ranking and is not delivered to a user with an explanation. "
          "And the forecast, where one exists, is a separate exercise from the assessment. Existing work also rarely states the limits of the label: income, default and deficit are different things."),
        H2("2.6 Research gap"),
        P(RESEARCH_GAP),
        P(f"The base paper states that its framework is designed to be adaptable to other settings with structured financial data {n('base')}. Individual profiling is such a setting in which demographic context carries much of the signal, "
          "and it is the one chosen here. The gap is addressed in three steps: apply the framework to a public individual-level dataset with leakage-safe pipelines, explain each assessment in language a user can read, and serve the result with a forecast "
          "and a scenario tool in an application whose limits are stated on every screen."),
        TAB("The base paper and this project compared by setting", ["Aspect", "Base paper", "This project"], [
            ["Unit of analysis", "Hospital (organisation)", "Individual person"],
            ["Data", "165 hospitals, 825 hospital-year rows, 2019-2023", f"UCI Adult, {F.N_ROWS:,} records (1994 census extract)"],
            ["Target", "Deficit (net income below zero), 41.2% positive", f"Income above 50K, {F.pct(F.RM['positive_rate_all'], 1)} positive; used as a profile signal"],
            ["Features", "11 engineered ratios and indicators", "12 user inputs, 26 columns after engineering"],
            ["Validation", "Group K-Fold, temporal hold-out, stratified CV", "Stratified 80/20 split and 5-fold stratified CV"],
            ["Best model and score", "XGBoost, AUC 0.842 (Group K-Fold)", f"XGBoost, AUC {F.f3(F.METRICS['roc_auc'])} (test split)"],
            ["Explanation", "SHAP global and local, counterfactual analysis", "SHAP global and live local, plain language, what-if simulation"],
            ["Forecast", "Counterfactual trajectories", "12-month Holt-Winters forecast of a synthetic index"],
            ["Delivery", "Analysis code", "Flask API and React web application"],
        ], widths=[1.4, 2.4, 2.5], size=9.5, align=["l", "l", "l"]),
        P("The two columns describe different problems on different data, so the scores are not comparable; Chapter 8 repeats this caveat where the numbers are set side by side."),
    ]
