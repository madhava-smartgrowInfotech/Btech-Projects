"""Chapter 2: Literature survey."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, H3, N, P, TAB
from .lit import LIT_TABLE
from .refs import cite


def blocks():
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),

        H2("2.1 Overview"),
        P("This chapter reviews the work on which the project builds and against which it must be judged. It starts with the base paper declared for the batch "
          f"{cite('base')} and analyses it in detail. It then describes the two further papers that were supplied with the batch and that shaped the design, the method paper "
          f"of Maarouf, Bakiaj and Feuerriegel {cite('maarouf')} and the interpretable-learning paper of Mashhadi, Saghezchi and Kashani {cite('mashhadi')}, and groups the remaining "
          "related work by theme. It describes the datasets and algorithms the project itself uses, summarises strengths and limitations, lists the sources named in the batch "
          "literature survey, and ends with the research gap."),
        P("Two comments on method. Numerical results are quoted only where we read them in the paper itself (the base paper and the two papers just named) or where a web "
          "record of the paper was read (references 16 and 17). Works [4] to [15] are known to us only through the reference list and the literature review of the base paper; "
          "they are described \"as summarised by [1]\", with the details that [1] gives and nothing more, and no figure of their own is reproduced."),

        H2("2.2 Analysis of the Base Paper"),
        P("The declared base paper is \"Startup Success Prediction Using Machine Learning and Ensemble Techniques\" by Panjwani, Shrivastava, Hande, Meshram, Verma and Gotmare of "
          f"Priyadarshini College of Engineering, published in the International Journal for Research in Applied Science and Engineering Technology in April 2026 {cite('base')}. "
          "It proposes a web-based startup success prediction system and compares four classifiers on preprocessed startup data."),
        H3("2.2.1 Problem and motivation"),
        P("The paper starts from the high failure rate of startups (nearly 90 % within the first few years, citing its own references) and from the subjectivity of investor judgement. "
          "It lists four objectives: to analyse the key factors influencing startup success, to develop and compare several ML models, to identify the most accurate and reliable "
          "model, and to provide a decision-support tool for investors and entrepreneurs. Its literature review distinguishes ML prediction studies, feature-based analyses, "
          "bias and data challenges (look-ahead bias, imbalance, scarce early-stage data) and advanced techniques (ensembles, PCA, text and language models), and ends with five research "
          "gaps: limited handling of bias and imbalance, absence of scalable real-time systems, poor integration of data sources, restricted use of textual data, and a lack of "
          "systems that are easy for entrepreneurs and investors to use."),
        H3("2.2.2 Methodology"),
        P("The system has a data-processing layer, a model layer and an application layer. Preprocessing consists of mean or mode imputation and removal of inconsistent records, "
          "label or one-hot encoding of categorical fields such as location and industry, standard scaling of numeric fields such as funding amount and workforce, and ADASYN "
          "oversampling for class imbalance. The selected features are the amount and number of funding rounds, team size and experience, location and industry, and online and "
          "social-media presence. Four models are trained: Logistic Regression as the baseline, Random Forest, Support Vector Machine and Gradient Boosting, with hyper-parameter "
          "tuning. The data are split 70:30 into training and test sets, and the models are judged by accuracy, precision, recall, F1-score and ROC-AUC. The backend is a Flask "
          "application with a REST interface and the front end is a simple HTML, CSS and JavaScript form that returns a probability and a SUCCESS or FAILURE label."),
        H3("2.2.3 Data and results reported"),
        P("The data are described as startup information from public sources such as Crunchbase and Kaggle, with funding amount, number of rounds, industry type, number of "
          "employees and location; no number of rows, no class balance and no list of columns is given. In the results section the paper states that Random Forest and Gradient "
          "Boosting performed best, that the top model's accuracy lay between 85 and 92 %, that the Support Vector Machine performed well but was slower than Logistic Regression, "
          "and that Logistic Regression was the less accurate baseline. Feature importance is reported only as a list: funding amount and number of rounds, team size and experience, "
          "industry type and location."),
        TAB("What the base paper [1] reports", ["Item", "Content in the paper"], [
            ["Models compared", "Logistic Regression, Random Forest, Support Vector Machine, Gradient Boosting"],
            ["Imbalance handling", "ADASYN oversampling"],
            ["Split", "70:30 training : test"],
            ["Metrics named", "Accuracy, precision, recall, F1-score, ROC-AUC"],
            ["Best models", "Random Forest and Gradient Boosting"],
            ["Headline accuracy", "85 to 92 % for the top-performing model (no per-model table)"],
            ["Dataset size, class balance, columns", "Not stated"],
            ["Per-model values of precision, recall, F1, ROC-AUC", "Not stated"],
            ["Application", "Flask backend, HTML/CSS/JavaScript front end, real-time prediction"],
        ], widths=[2.6, 3.7], align=["l", "l"]),
        H3("2.2.4 Strengths and limits"),
        P("The paper states a clear workflow, names the standard metrics, includes the imbalance problem and look-ahead bias in its discussion, and ships a working web "
          "application. It also concedes its own limits: dependence on high-quality data, imbalance and missing values, no real-time data and little attention to external market "
          "conditions. What a reader cannot check is the central claim. Without a dataset size, a table of per-model results or a statement of how leakage was avoided, the "
          "85 to 92 % figure cannot be compared with anything, and a model that sees fields recorded after the outcome would reach that level without being useful."),
        H3("2.2.5 Relation to this project"),
        P("The project keeps the base paper's overall design (preprocessing, several classifiers, standard metrics, a web application) and its model list, and adds what the paper "
          "names as missing: an explicit comparison of imbalance handling, explanations for each prediction, use of text and of comparable startups, and a measured, reproducible "
          "evaluation with the leakage question stated openly. Chapter 8 compares its own numbers with the paper's claim in the 70:30 protocol of the paper, and says plainly "
          "that the datasets differ or are unknown."),

        H2("2.3 The Method Paper and the Reference Paper"),
        H3("2.3.1 Predicting startup success with in-context learning"),
        P("Maarouf, Bakiaj and Feuerriegel observe that many investors hold data on only a few dozen startups, which makes supervised ML unstable, and propose k-nearest-neighbour "
          f"in-context learning (kNN-ICL) {cite('maarouf')}. For a new startup, the k most similar past startups are retrieved and shown, with their outcomes, to a large language "
          f"model in the prompt, in the spirit of few-shot learning {cite('icl')}; no model is trained. Their database holds 4,034 Crunchbase startups, of which 1,418 (35.15 %) are "
          "successful and 2,616 are not. Inputs are structured fields (age, founders, industry, presence on professional platforms, founder attributes) and the free-text self-description; "
          "company names are replaced by a placeholder so that the model cannot rely on what it memorised. Evaluation uses five repeated stratified 80/20 splits with the mean and "
          "standard deviation reported, and balanced accuracy as the main metric because successful startups are the minority."),
        P("At k = 50 shots, kNN-ICL reaches a balanced accuracy of 0.713 and an F1-score of 0.632, against 0.631 and 0.488 for regularised Logistic Regression, 0.634 for Random "
          "Forest and 0.618 for XGBoost, and 0.696 for vanilla in-context learning with randomly chosen examples. Performance rises with k and saturates near 50. In an appendix, a fused "
          "language model trained on 20,172 startups reaches 0.743 balanced accuracy and 0.678 F1, which shows that more data still helps. This project takes three things from "
          "the paper: the evaluation protocol (five repeated stratified 80/20 splits with balanced accuracy as the primary metric), the idea of retrieving comparable startups "
          "and showing them with their outcomes, and the masking of company names. It does not use a language model for the decision."),
        H3("2.3.2 Interpretable machine learning for funding, patenting and exits"),
        P("Mashhadi, Saghezchi and Kashani build a Crunchbase firm-quarter panel for 2010 to 2023, matched to patent records, and forecast three outcomes: a new funding round within "
          f"12 months, growth of the patent stock within 24 months and an exit (IPO or acquisition) within 36 months {cite('mashhadi')}. Preprocessing is fitted on a development "
          "window (2010 to 2019) and applied unchanged to later cohorts to avoid leakage. Imbalance is handled with inverse-prevalence weights and SMOTE-NC, and Logistic Regression, Random "
          "Forest, XGBoost, LightGBM and CatBoost are compared by the area under the precision-recall curve (PR-AUC), with AUROC as a tie-breaker. The best models reach AUROC "
          "0.921 (patents, PR-AUC 0.631), 0.817 (next funding, PR-AUC 0.220) and 0.872 (exit, PR-AUC 0.559). SHAP analyses identify the time since the last funding round and the age of the "
          "firm as the leading drivers of funding and exit, and reliability curves show optimism at high scores, for which the authors recommend isotonic recalibration."),
        P("The paper matters here for three reasons. It uses the same model family as the batch objectives (logistic regression, Random Forest and boosting). It treats class imbalance "
          "with weights and oversampling and reports PR-AUC, which is more informative than ROC-AUC for rare outcomes. And it shows what a leakage-safe protocol looks like, which "
          "the public table used in this project does not allow because it carries no dates."),

        H2("2.4 Related Work by Theme"),
        H3("2.4.1 Machine-learning prediction of startup success"),
        P(f"As summarised by the base paper {cite('base')}, Krishna et al. applied Random Forest and Bayesian networks to startup data and stressed funding-related features and growth "
          f"milestones {cite('krishna')}; Razaghzadeh Bidgoli et al. compared Random Forest, Gradient Boosting, Support Vector Machine and Logistic Regression and found ensembles above 80 % "
          f"accuracy {cite('bidgoli')}; Li analysed large startup data with Support Vector Machine and Random Forest {cite('li')}; Camelo Martinez used logistic regression and found team size, "
          f"funding amount and market conditions to be important, with accuracy up to 76 % {cite('martinez')}; and Ross et al. built an ensemble model, CapitalVX, combining several data "
          f"sources, with accuracy up to 90 % {cite('ross')}. Tomy and Pardede stress uncertainty in startup settings {cite('tomy')}. These descriptions are those of [1]; the original papers "
          "were not re-read."),
        H3("2.4.2 Features, bias and interpretability"),
        P(f"Jafari et al. grouped predictors of startup success into investor structure, digital presence, funding history and business characteristics, finding finance and online "
          f"traction most important {cite('jafari')}; Zbikowski and Antosiuk proposed a bias-free approach on Crunchbase data and drew attention to look-ahead bias {cite('zbikowski')}; "
          f"Choi used PCA to improve model accuracy {cite('choi')}; and Bonaventura et al. showed that a startup's position in the network of investors and companies influences its "
          f"success {cite('bonaventura')} (all as summarised by [1]). The more general warning about information that is not available at prediction time is formulated in the "
          f"data-mining literature on leakage {cite('leakage')}, and Mashhadi et al. show how to respect it {cite('mashhadi')}."),
        H3("2.4.3 Text, retrieval and language models"),
        P(f"Maarouf et al. earlier proposed a fused large language model that combines structured variables with the text self-description {cite('fused')} (reported through [1] and, "
          f"with a balanced accuracy of 0.743 on the common test set, through [2]). The kNN-ICL paper replaces the trained model by retrieval and prompting {cite('maarouf')}. "
          f"This project uses the retrieval half of the idea with a compact sentence encoder, MiniLM {cite('minilm')} within the Sentence-BERT framework {cite('sbert')}, and a "
          f"classical nearest-neighbour rule {cite('knn')}, so that everything runs on a laptop."),
        H3("2.4.4 Economic evidence on venture finance"),
        P(f"Gius analysed 67 venture competitions and found that startups were more likely to succeed when the judges disagreed more about their quality, mostly when the idea was "
          f"unique {cite('gius')}. Bhandari used a questionnaire answered by 120 respondents in Nepal and a regression to relate venture capital, access to capital, networking and "
          f"market conditions to startup success {cite('bhandari')}. These studies explain why funding and relationship indicators matter, but they are association studies and "
          "not predictors."),
        TAB("Summary of the literature (works read in full or confirmed)", ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [r for r in LIT_TABLE], widths=[1.1, 1.6, 1.1, 1.4, 1.1], align=["l", "l", "l", "l", "l"], size=8.5),

        H2("2.5 Datasets and Algorithms Used in This Project"),
        H3("2.5.1 Datasets"),
        P(f"Two datasets are involved and they must not be confused. The public \"Startup Success Prediction\" table {cite('kaggle')} has 923 rows and 49 columns of US startups, with a "
          f"status of acquired (success) or closed (failure). After the application's own de-duplication {F.REAL_ROWS} rows remain: {F.REAL_SUCCESS} success ({F.pct(F.REAL_SUCCESS / F.REAL_ROWS)}) "
          f"and {F.REAL_FAILURE} failure. It has no free text. Because the Kaggle download needs a login, the same table was obtained from a public copy and is used for all real "
          f"measurements. The shipped application, in contrast, runs on a synthetic fallback of {F.SYN_ROWS:,} rows ({F.SYN_SUCCESS} success, {F.SYN_FAILURE} failure) with the same schema "
          "and a description generated from templates. Chapter 6 describes both."),
        H3("2.5.2 Algorithms"),
        B(f"**Logistic Regression** is a linear model whose coefficients can be read directly; it is the baseline in the base paper and, here, the model served by the application {cite('base')}.",
          f"**Decision Tree** is a single rule-based model, easy to explain but unstable.",
          f"**Random Forest** averages many decorrelated trees and reduces over-fitting {cite('rf')}.",
          f"**XGBoost** and **HistGradientBoosting** build trees one after another to correct the previous errors {cite('xgb', 'gbm')}.",
          f"**Class weighting and oversampling** handle imbalance at the algorithm and data level; SMOTE and ADASYN are the usual synthetic oversamplers {cite('imbalance', 'smote', 'adasyn')}.",
          f"**Sentence embeddings and cosine retrieval** turn the description into a 384-dimensional vector and find the nearest training startups {cite('sbert', 'minilm', 'knn')}.",
          f"**Metrics**: balanced accuracy, F1, ROC-AUC and PR-AUC {cite('roc', 'pr')}."),

        H2("2.6 Strengths and Limitations of the Surveyed Approaches"),
        TAB("Strengths and limitations of the main approaches", ["Approach", "Strengths", "Limitations"], [
            ["Ensembles of trees on structured data [1], [7], [11]", "Handle mixed data and non-linear effects; strong in all surveyed comparisons", "Hard to explain; accuracy claims depend on data and leakage control"],
            ["Logistic Regression [1], [5]", "Transparent coefficients; cheap; calibrated probabilities", "Misses interactions; lower accuracy in [1]"],
            ["Oversampling (SMOTE, ADASYN) [1], [3]", "Simple; widely used", "Synthetic points can add noise; changes the data, not the loss"],
            ["Leakage-aware protocols [3], [9]", "Realistic out-of-time estimates; interpretable", "Need dated panel data and patent matching"],
            ["Text and language models [2], [14]", "Use the business description; work with few labelled examples", "Need a language model; text must be available"],
            ["Economic and survey studies [16], [17]", "Explain why funding and networks matter", "Association only; small or special samples"],
        ], widths=[2.1, 2.1, 2.1], align=["l", "l", "l"], size=10),

        H2("2.7 Further Sources Named in the Batch Survey"),
        P(f"The batch literature survey (5.LITERATURE SURVEY) lists five sources. The first is the base paper itself. The sources by Gius {cite('gius')} and Bhandari {cite('bhandari')} were "
          f"confirmed by web search and are described above. The remaining two, an empirical study of the impact of venture capital on startup success rates across industries "
          f"(European Economic Letters, 2024) {cite('s1')} and a book chapter on the role of SICTIC in the Swiss startup ecosystem (2026) {cite('s2')}, could not be located; only their titles, "
          "years and venues are recorded, no result is quoted from them, and they are listed in the references for completeness. All five are economic or venture-finance studies; "
          "none is a machine-learning classifier, which is why the ML design of this project rests on [1] to [3]."),

        H2("2.8 Research Gap"),
        P(lit.GAP),
        P("Read against the surveyed papers, the gap has five parts, each of which the project addresses to the extent the data allow:"),
        N("**Evidence and reporting.** The base paper gives accuracy ranges without a dataset or a table. The project measures every model on a stated public table over repeated splits and reports means and standard deviations.",
          "**Feature engineering.** Funding velocity and team composition are named but not built. The project uses the funding-timing fields, the number of rounds and the relationship counts of the public table, and states that team-experience and market data are not available.",
          "**The rare-success class.** The batch assumes success is rare. The project handles imbalance with balanced weights, compares oversampling, and finds that on the real table success is the majority class, which changes what the trade-offs mean.",
          "**Explanation.** A prediction that names no drivers cannot be acted on. Each prediction here carries signed feature contributions and the comparable startups behind it.",
          "**Leakage.** Bias and look-ahead are named as gaps in [1] and solved only with dated panels in [3]. The project cannot solve it without dates, but quantifies how much of the real-data performance depends on four fields recorded around the outcome window."),
    ]
