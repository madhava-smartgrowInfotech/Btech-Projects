"""Chapter 2: Literature survey (text from lit.py / refs.py, which hold the verified entries)."""

from . import facts as F
from .blocks import B, EQ, H1, H2, H3, P, TAB
from .lit import BASE_PAPER_ANALYSIS, DATASET_NOTES, GAP, LIT_GROUPS, LIT_HEADER, LIT_TABLE
from .refs import NOT_VERIFIED, NUM


def _c(*keys):
    return "[" + ", ".join(str(NUM[k]) for k in keys) + "]"


def blocks():
    X = F.X
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview and Approach"),
        P("The survey starts from the base paper designated for the batch and from the five works listed in the batch literature survey, and widens to the benchmark data sets and methods that decide the design of this project: "
          "how single diseases are predicted from routine measurements, how several diseases have been handled together, how predictions are explained, and how models should be selected and evaluated. "
          "Every work described with numbers was checked against its own page, abstract or full text; where only the title and bibliographic record could be confirmed this is said in the text, and a title that could not be confirmed at all "
          "is listed separately in Section 2.8 and is not cited."),
        P("The survey is deliberately short on claims of superiority. The surveyed papers use different diseases, data sets, splits and metrics, so their accuracies cannot be ranked against one another or against this project; "
          "they are quoted as the authors reported them."),
        H2("2.2 Base Paper Analysis"),
        *[P(t) for t in BASE_PAPER_ANALYSIS],
        TAB("The base paper compared with this project", ["Aspect", "Base paper " + _c("base"), "This project"],
            [["Disease(s)", "Thyroid status (one organ)", "Diabetes, heart, liver and kidney disease"],
             ["Data", "UCI thyroid, 7,200 real samples, 21 features, three classes", f"Synthetic, {F.N_ROWS:,} rows per disease, binary high / low risk; real data only in a supplementary check"],
             ["Algorithms", "SVC, Random Forest, Extra Trees, AdaBoost, CatBoost", "Logistic Regression, Decision Tree, Random Forest, RBF SVM"],
             ["Validation", "Nested cross-validation: outer stratified 5-fold, inner 3-fold grid search", "Single stratified 80/20 split, fixed settings, selection by F1 on the test set; 5-fold CV and ten splits added afterwards"],
             ["Feature selection", "Consensus TOP-10 of six ranking methods", "None; all fields of each condition are used"],
             ["Imbalance", "SMOTE tested and rejected", "No class weights or resampling; F1 is used for selection"],
             ["Explanation", "SHAP and counterfactual analysis", "None in the application; permutation importance offline"],
             ["Deliverable", "A study with a proposed decision-support direction", "A working web application with API"]],
            widths=[1.2, 2.4, 2.4], size=9.5),
        P("The table shows what the project takes from the base paper (the comparison of several classical classifiers by held-out metrics, applied to routine clinical tables) and where it is weaker: "
          "data, validation protocol and explanation. These differences are the reason Chapter 8 compares the two works qualitatively and not numerically."),
        H2("2.3 Related Work by Theme"),
        *[x for theme, paras in LIT_GROUPS.items() if theme != "datasets" for x in ([H3(theme[0].upper() + theme[1:])] + [P(t) for t in paras])],
        H2("2.4 Datasets and Algorithms Used in the Literature and in This Project"),
        P("Four public benchmarks correspond to the four conditions of this project. They are described below as they are documented by their sources; this project did not train its shipped models on them (Chapter 6 explains why) "
          "but uses them in the supplementary check reported in Chapter 8."),
        B(*DATASET_NOTES),
        *[P(t) for t in LIT_GROUPS.get("datasets", [])],
        P(f"The four algorithms of this project are standard. **Logistic Regression** {_c('hosmer')} models the log-odds of the positive class as a linear function of the inputs and is the usual transparent baseline. "
          "A **Decision Tree** splits the inputs recursively into regions of similar outcome and yields readable rules, but a deep tree fits noise. "
          f"A **Random Forest** {_c('rf')} averages many trees grown on bootstrap samples with random feature subsets, which reduces variance. "
          f"A **Support Vector Machine** {_c('svm')} with a radial-basis-function kernel finds a maximum-margin boundary in a transformed space and returns probabilities through an extra calibration step. "
          f"All four, the scaler and the metrics are taken from scikit-learn {_c('scikit')}."),
        P("The metrics reported for every model are defined from the counts of true and false positives and negatives (TP, FP, TN, FN) on the held-out records:"),
        EQ("Accuracy = (TP + TN) / (TP + TN + FP + FN)        Precision = TP / (TP + FP)        Recall = TP / (TP + FN)"),
        EQ("F1 = 2 x Precision x Recall / (Precision + Recall)"),
        P(f"ROC-AUC is the area under the curve of true-positive rate against false-positive rate over all decision thresholds. On imbalanced data the precision-recall view and the Matthews coefficient are often preferred {_c('saito', 'chicco')}; "
          f"this project reports the first four metrics, as its abstract promises, and adds ROC-AUC afterwards (Chapter 8)."),
        H2("2.5 Summary of the Surveyed Work"),
        TAB("Summary of the surveyed work (results as reported by the authors; the studies are not comparable with one another)", LIT_HEADER, LIT_TABLE, widths=[1.15, 1.45, 1.2, 1.3, 0.9], size=8),
        H2("2.6 Strengths and Limitations of Existing Approaches"),
        P("Reading the table and the themes together gives a consistent picture."),
        B("**Strengths.** The single-disease studies are rigorous within their scope: real clinical data, several classifiers compared, and in the best cases leakage-safe validation and explanation (the base paper). "
          "Classical algorithms reach high scores on tabular laboratory data when the data are separable, and the benchmark data sets are public, small and easy to reproduce on.",
          "**Limitations: scope.** Almost every study addresses one disease; the multi-disease systems found use symptom flags or different conditions, and none combines diabetes, heart, liver and kidney risk from routine values.",
          "**Limitations: data.** The benchmarks are small (303 to 768 records), come from single populations, contain missing or implausible entries, and are rarely externally validated; "
          "authors of two of the surveyed studies say so themselves.",
          "**Limitations: evaluation.** Selection and reporting on the same split inflate results; a single split of a few hundred records has a spread that is rarely reported. Accuracy alone hides weak recall on the minority class.",
          "**Limitations: delivery.** Few studies deliver an application a non-programmer can run, and fewer still state openly how far the application's numbers can be trusted."),
        H2("2.7 Research Gap"),
        P(GAP),
        TAB("Gap and the response of this project", ["Gap in the literature", "Response in this project", "Status"],
            [["Single disease per tool", "Four conditions behind one interface and one API", "Achieved"],
             ["Different algorithms and protocols per study", "Same four algorithms, preprocessing, split and metrics for all conditions", "Achieved"],
             ["Few usable applications", "FastAPI service and React interface; Flask pages kept", "Achieved"],
             ["Optimistic selection on one split", "Selection by F1 on the test set was kept; CV and ten splits added to measure the effect", "Measured, not fixed"],
             ["Real data", "Shipped models use synthetic data; real benchmark data used only in a supplementary check", "Partly addressed"],
             ["Explanation of each prediction", "Not in the application; permutation importance offline only", "Not achieved"]],
            widths=[2.0, 3.2, 0.8], size=9.5, align=["l", "l", "c"]),
        P(f"The honest summary is that the project fills the scope gap (several conditions, one pipeline) but not the evidence gap: its headline accuracies of {', '.join(F.pct(X[d]['holdout'][F.BEST[d]]['accuracy']) for d in F.DISEASES)} "
          "are on synthetic data and say little about patients."),
        H2("2.8 Items Listed in the Batch Survey but Not Verified"),
        P("The batch literature survey names five works. The base paper, a chapter on kidney disease prediction, a chapter on deep learning for disease prediction and a chapter on skin disease prediction "
          f"were found and are listed in the references ({_c('base', 'kidneychap', 'dlchap', 'skinchap')}); the three book chapters were confirmed as bibliographic records only, and their results are not quoted. "
          "The remaining title could not be confirmed and is not cited:"),
        B(*NOT_VERIFIED),
    ]
