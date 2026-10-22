"""Chapter 1: Introduction (the lists below are defined once in shared.py and re-exported for other modules)."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F
from .shared import (OBJECTIVES, OBJECTIVE_STATUS, SCOPE_IN, SCOPE_OUT, ASSUMPTIONS,  # noqa: F401  (re-exported)
                     LIMITATIONS, CONTRIBUTIONS)


def blocks():
    M = F.METRICS
    shot = F.shot("04_dashboard.png")
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Domain overview"),
        P("Financial identification is the task of describing where an individual stands financially: how strong the position is, how exposed it is to risk and "
          "where it is likely to move. Lenders, planners, policy makers and individuals all need such a picture, and the quality of the decisions that follow depends on how "
          "well it is drawn. The classical tools are statistical scores built from a few financial ratios. Altman's Z-score used five ratios in a linear discriminant "
          f"function and Ohlson's logistic model relaxed its distributional assumptions {n('altman', 'ohlson')}; both showed that financial ratios carry real "
          "information about viability, and both belong to a generation of methods that assume a largely linear relationship between inputs and outcome."),
        P("Machine learning replaced that assumption with models that learn non-linear interactions directly from data. Random forests, gradient boosting and XGBoost "
          f"{n('breiman', 'friedman', 'xgboost')} have repeatedly been reported to outperform traditional statistical models on bankruptcy and credit-risk problems "
          f"{n('barboza', 'zieba')}, and tree ensembles in particular remain strong on tabular data of moderate size {n('grinsztajn')}. At the same time, financial "
          f"decisions are regulated and contestable, so a prediction that cannot be explained is of limited use; this has driven the adoption of SHAP-style attribution "
          f"in finance {n('shap', 'treeshap', 'cerneviciene')}. The domain of this project is therefore Artificial Intelligence and Machine Learning applied to "
          "demographic analytics, financial profiling and economic forecasting."),
        H2("1.2 Background and motivation"),
        P("Individual financial circumstances are shaped by demographic context as much as by money figures. Age, education, occupation, hours of work, household role, "
          "region and the presence of investment income all move together, and they interact: the value of an additional year of education differs by age and by "
          "occupation. A score built on a narrow set of financial parameters ignores this context, so it can be inaccurate for the people it describes and unfair to "
          "those whose circumstances differ from the average. Forecasting adds a second dimension: knowing the present position matters less than knowing "
          "where conditions are heading."),
        P(f"The base paper for this project {n('base')} builds an explainable machine-learning framework for organisational financial distress, instantiated on 165 "
          "Korean hospitals. It combines domain-adaptive feature engineering, a comparison of linear, ensemble and boosted classifiers, SHAP interpretation and "
          "domain-specific validation. Its authors state that the approach is designed to be adaptable to other settings with structured financial data. The motivation "
          "of this project is to carry that approach to the individual: to apply the same chain of ideas to demographic and financial attributes of people, to wrap "
          "it in a usable application, and to measure honestly what it achieves."),
        P("The result is FinSight AI, a web application that accepts twelve demographic and financial inputs, returns a financial profile, a risk band and a "
          "financial-strength score, explains the score with SHAP contributions in plain language, compares a baseline with a changed scenario and shows a "
          "12-month economic forecast. Its dashboard is shown below."),
        FIG(F.shot_view("04_dashboard.png"), "FinSight AI dashboard: serving model, test metrics, top SHAP drivers and the economic outlook", F.shot_w(shot, 5.6)),
        H2("1.3 Problem statement"),
        B("Traditional statistical scoring misses non-linear interaction between demographic and financial factors.",
          "Assessment based on a limited set of parameters produces inaccurate and unfair outcomes.",
          "Static scoring describes the present position but does not forecast future risk.",
          "An unexplained financial decision cannot be defended to the customer or to a regulator."),
        P("The problem addressed here is: *given the demographic and financial attributes of one person, identify a financial profile and risk band with a "
          "calibrated strength score, show which factors drove the assessment and in which direction, let the user test what would change under a different "
          "scenario, and place the result beside a forecast of economic conditions, all through an interface a non-expert can use.*"),
        H2("1.4 Need for the system"),
        P("There is a need for a system that combines demographic and financial data to assess financial position and to forecast economic conditions, "
          "with explainable output. Research code in this area usually stops at a notebook and an accuracy figure; commercial scoring products are closed and "
          "cannot be inspected. An open, reproducible implementation lets students, analysts and developers study the whole path from raw data to an explained "
          "assessment, repeat the measurements and extend the work. It is equally important that such a system states its limits clearly, because a number on a "
          "screen is easily mistaken for a verdict about a person."),
        H2("1.5 Objectives"),
        P("The project was proposed with six objectives. The table after the list gives each one with its outcome; the evidence is in Chapter 8."),
        N(*OBJECTIVES),
        TAB("Objectives and where they are addressed", ["No.", "Objective (short)", "Outcome", "Where"],
            [["1", "Dataset of demographic and financial attributes", OBJECTIVE_STATUS[0][0], "Chapters 2, 6"],
             ["2", "Preprocessing, missing values, encoding", OBJECTIVE_STATUS[1][0], "Chapter 6"],
             ["3", "Classify financial profile, estimate risk", OBJECTIVE_STATUS[2][0], "Chapters 6, 8"],
             ["4", "Forecasting component", OBJECTIVE_STATUS[3][0], "Chapters 6, 8"],
             ["5", "Explainability layer", OBJECTIVE_STATUS[4][0], "Chapters 6, 8"],
             ["6", "Evaluate and deploy through a web interface", OBJECTIVE_STATUS[5][0], "Chapters 5, 7, 8"]],
            widths=[0.5, 3.0, 1.1, 1.7], align=["c", "l", "c", "l"]),
        H2("1.6 Scope"),
        P("**In scope.**"),
        B(*SCOPE_IN),
        P("**Out of scope.**"),
        B(*SCOPE_OUT),
        H2("1.7 Contributions"),
        P("The work is an application and an integration of established methods; its contributions are listed below, and Chapter 9 repeats them against the evidence."),
        N(*CONTRIBUTIONS),
        H2("1.8 Limitations and assumptions"),
        P("**Assumptions.**"),
        B(*ASSUMPTIONS),
        P("**Limitations.**"),
        B(*LIMITATIONS),
        P(f"To give a sense of scale: the selected model reaches an accuracy of {F.pct(M['accuracy'])} and a ROC-AUC of {F.f3(M['roc_auc'])} on {F.N_TEST:,} held-out records, "
          f"but it finds only {F.pct(M['recall'])} of the people who earn more than 50K at the default threshold, and every statement about it concerns income in a 1994 "
          "census extract, not creditworthiness today. The rest of the report keeps these limits in view."),
        H2("1.9 Organisation of the report"),
        TAB("Organisation of this report", ["Chapter", "Content"], [
            ["1  Introduction", "Domain, motivation, problem, objectives, scope, contributions, limitations."],
            ["2  Literature Survey", "The base paper in depth, related work by theme, datasets and algorithms, research gap."],
            ["3  Feasibility Study", "Technical, economic, operational and schedule feasibility."],
            ["4  System Requirements and Analysis", "Existing and proposed system, functional and non-functional requirements, hardware, software, users."],
            ["5  System Design", "Architecture, workflow, data-flow diagrams, UML, data model, modules, API and UI design."],
            ["6  Methodology and Software Implementation", "Dataset, preprocessing, models, mathematics, training, forecasting, application, security, installation."],
            ["7  System Testing", "Strategy and results of unit, integration, functional, security, performance and edge-case tests."],
            ["8  Results and Output Screens", "Model performance, comparison with the base paper, output screens, failure analysis, objectives versus outcomes."],
            ["9  Conclusion", "Summary, achievements, findings, applications, known limitations."],
            ["10 Future Scope", "Improvements, features, deployment and research directions."],
            ["Appendices", "A: important code; B: installation and user guide; C: additional screens."],
        ], widths=[2.3, 3.9]),
    ]
