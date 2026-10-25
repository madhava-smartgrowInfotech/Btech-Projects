"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, FIG, H1, H2, N, P, TAB
from .shared import INTRO_POINTS, NEED, OBJECTIVES, PROBLEM_POINTS, PROBLEM_STATEMENT, SYNTHETIC_NOTE


def _c(*keys):
    from .refs import NUM

    return "[" + ", ".join(str(NUM[k]) for k in keys) + "]"


def blocks():
    X, R = F.X, F.REAL
    best_acc = ", ".join(f"{F.NAME[d].lower()} {F.pct(X[d]['holdout'][F.BEST[d]]['accuracy'])}" for d in F.DISEASES)
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Background"),
        P("Diabetes, heart disease, liver disease and kidney disease are among the chronic conditions that develop slowly and often give few symptoms until they are advanced. "
          "By the time a patient is referred to a specialist the condition may already need expensive long-term treatment. The early signals are, however, usually present in tests that are cheap and routine: "
          "blood glucose, blood pressure, cholesterol, bilirubin and liver enzymes, serum creatinine, urea and haemoglobin. A clinician reads these values against reference ranges and against each other; "
          "in a busy or understaffed health centre that reading may be delayed, or the combination of mildly abnormal values may not be noticed at all."),
        P("Machine learning offers a way of learning such combinations from past records. A supervised classifier is shown many patients whose condition is known and learns which patterns of values go with "
          "which outcome; given a new patient it returns a predicted class and a measure of how sure it is. Published work on this idea is large, but most of it treats one disease at a time, "
          f"as the literature survey in Chapter 2 shows. The base paper of this project {_c('base')} is a typical strong example from the recent literature: it studies a single organ, the thyroid, "
          "on a real benchmark data set and adds explanations to its predictions."),
        P("Four conditions were chosen because they share a common kind of input and because public data on all of them exist: diabetes and heart disease are assessed from a few measurements and a history, "
          "liver disease from a panel of blood enzymes and proteins, and kidney disease from blood chemistry and urine tests. All four are tabular, numeric and low-dimensional, so classical algorithms are appropriate "
          "and no image, signal or text processing is needed. The same property keeps the system small: a saved model file is between about 1 and 60 kilobytes, a prediction takes a fraction of a millisecond, and the whole application runs on a laptop."),
        P("This project takes the multi-disease view. It puts four conditions behind one application so that a user does not have to find and learn a different tool for each, and it uses the same four "
          "classical algorithms, the same preprocessing and the same evaluation for every condition so that the results can be compared fairly."),
        H2("1.2 Motivation"),
        P("The motivation for the work comes from six observations that were set down at the start of the project:"),
        B(*INTRO_POINTS),
        P("The first four points explain why prediction from routine parameters is worth attempting; the last two explain why a single interface is attractive. "
          "The fifth point also turned out to be a hypothesis worth testing: Chapter 8 shows that on this project's data the simple Logistic Regression model matched or beat the Random Forest, "
          "because the Random Forest fitted the noise in the labels."),
        P("Why these four algorithms? Logistic Regression is the standard transparent baseline for a binary outcome and its coefficients can be read as effects. A Decision Tree gives rules a person can follow. "
          "A Random Forest averages many trees and usually handles interactions and mixed scales well. A Support Vector Machine with an RBF kernel is a strong general-purpose classifier for small numeric data. "
          f"They are the four algorithms named in the project abstract, they are all available in scikit-learn {_c('scikit')}, and together they span linear, rule-based, ensemble and kernel methods, "
          "so a comparison between them says something about what kind of structure the data contain."),
        H2("1.3 Problem Statement"),
        P("The problem as it appears in current practice has four parts:"),
        B(*PROBLEM_POINTS),
        P(f"**Need.** {NEED}"),
        P(f"**Formal statement.** {PROBLEM_STATEMENT}"),
        H2("1.4 Objectives"),
        P("The project has six objectives, taken from the project proposal. Chapter 8 measures them and Chapter 9 states, for each, whether it was met, partly met or not met."),
        N(*OBJECTIVES),
        H2("1.5 Scope of the Project"),
        P("The work covers the path from a table of clinical records to a risk indication shown to a user: generation of the training data, scaling of the inputs, training and comparison of four classifiers for each of four conditions, "
          "selection and saving of the best model per condition, a JSON API that serves the saved models, and a web interface with a prediction form for each condition, a model-comparison page and a dataset page. "
          "An earlier Flask version of the same prediction pages is kept and shares the same saved models."),
        P("The work does not cover the collection of real patient data, clinical validation, a database or user accounts, per-prediction explanations in the application, treatment recommendations, imaging or free-text records, "
          "or the diagnosis of any condition other than the four named. These limits are stated in full in the Scope and Limitations document and in Chapter 9."),
        H2("1.6 Proposed System in Brief"),
        P(f"The system, named the **{F.PRODUCT}**, holds one trained model for each of four conditions. For every condition the training script splits {F.N_ROWS:,} records 80/20 with stratification, "
          "standardises the inputs with a scaler fitted on the training part only, and trains four classifiers: Logistic Regression, a Decision Tree of depth 6, a Random Forest of 200 trees and an RBF Support Vector Machine. "
          "It evaluates all four on the 400 held-out records with accuracy, precision, recall and F1-score and saves the one with the highest F1."),
        P("A FastAPI service with seven routes loads the saved models and exposes them to a React interface. The user chooses a condition, types the clinical values (or loads a real record from the data set to pre-fill the form) "
          "and presses a button; the interface shows the predicted risk class, the model's confidence, the name of the model used and its hold-out accuracy, together with a notice that the result is not a diagnosis. "
          "The figure below shows the workflow."),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow of a prediction in the Intelligent Health Assistant", 6.0),
        H2("1.7 Contributions"),
        P("The contributions of the project, stated as precisely as the evidence allows, are:"),
        N("A single application that screens four chronic conditions (diabetes, heart, liver and kidney disease) through one interface and one API, with a common pipeline and a common evaluation protocol.",
          f"A like-for-like comparison of 16 models (four algorithms for each of four conditions) on the same split and settings, with the model served for each condition chosen on F1-score.",
          "A React interface and a FastAPI layer over the original Flask code, with form validation, out-of-training-range warnings, real-record pre-filling, a model-comparison page and a dataset page that states openly that the data are synthetic.",
          "An evaluation that goes beyond the training script: ROC-AUC, confusion matrices, 5-fold cross-validation, ten random splits, a decision-threshold sweep, permutation importance and hyper-parameter sensitivity (Chapter 8).",
          "A supplementary check on real public data (Pima diabetes, UCI Cleveland heart, UCI ILPD liver and UCI chronic kidney disease) that measures how the same algorithms and the shipped models behave outside the synthetic data.",
          "A reproducible set of scripts for data generation, training, experiments, API tests, screen capture and diagrams, so that every number in this report can be regenerated."),
        H2("1.8 Relation to the Base Paper"),
        P(f"The base paper, Alam et al. {_c('base')}, applies five classifiers to the UCI thyroid data set under nested cross-validation and explains the predictions with SHAP and counterfactual analysis. "
          "This project is an **applied extension of its general idea**, comparing several classifiers on clinical tabular data under held-out evaluation, to four other conditions behind one interface. "
          "It is not a reproduction: the data are different and synthetic, the task is binary and not three-class, the evaluation is a single split and not nested cross-validation, no hyper-parameters are tuned, "
          "and the application does not show SHAP or counterfactual explanations. Chapter 8 sets out the differences, and the metrics of the two works are not comparable."),
        H2("1.9 Data Used and a Caution"),
        P(SYNTHETIC_NOTE),
        P(f"Each of the four files holds {F.N_ROWS:,} rows, with no missing values and no duplicates; the share of high-risk records is {F.pct(X['diabetes']['positive'] / F.N_ROWS)} for diabetes, "
          f"{F.pct(X['heart']['positive'] / F.N_ROWS)} for heart disease, {F.pct(X['liver']['positive'] / F.N_ROWS)} for liver disease and {F.pct(X['kidney']['positive'] / F.N_ROWS)} for kidney disease. "
          f"The hold-out accuracies reported by the application ({best_acc}) are therefore a measure of how well the pipeline recovers a known rule from noisy labels, and not a measure of clinical performance. "
          "Every result in this report is labelled accordingly, and Chapter 8 adds the supplementary real-data check so that the reader can see how far the two differ."),
        H2("1.10 Limitations and Assumptions"),
        B("The training data are synthetic, so the reported metrics cannot be read as clinical accuracy.",
          "Model selection used the same 400-row test set as the reported metrics, and a single split; the selection for diabetes (SVM) is not supported by cross-validation, which favours Logistic Regression.",
          "The application shows a class and a confidence only; the parameters that drove a prediction are not shown, and no recommendations are generated.",
          "No missing-value or outlier handling exists beyond scaling, and the API does not reject physiologically impossible values; the form only warns when a value lies outside the training range.",
          "There is no authentication, database or audit trail, and the system has not been clinically validated; it is a demonstration and must not be used for real patients.",
          "Assumptions: inputs are routine laboratory and examination values entered correctly in the units shown on the form, one patient at a time, and one condition is assessed per form."),
        H2("1.11 Organisation of the Report"),
        TAB("Organisation of the report", ["Chapter", "Content"],
            [["1", "Introduction: background, motivation, problem statement, objectives, scope, contributions, limitations"],
             ["2", "Literature survey: base paper, related work by theme, datasets and algorithms, research gap"],
             ["3", "Feasibility study: technical, economic, operational, schedule, legal and ethical aspects, risks"],
             ["4", "System requirements and analysis: existing and proposed system, requirements, hardware, software, use cases"],
             ["5", "System design: architecture, data flow, UML, logical data model, database design, modules, user interface"],
             ["6", "Methodology and software implementation: data, preprocessing, algorithms, formulation, training, API, security, installation"],
             ["7", "System testing: strategy, unit, integration, functional, security, validation, performance, acceptance and limits"],
             ["8", "Results and output screens: metrics, stability, thresholds, real-data check, base-paper comparison, screens"],
             ["9", "Conclusion: summary, objectives achieved, key findings, applications, known limitations"],
             ["10", "Future scope: improvements, features, deployment, further research"],
             ["", "References, Appendix A (important code), Appendix B (installation and user guide), Appendix C (additional screens)"]],
            widths=[0.8, 5.2], align=["c", "l"]),
    ]
