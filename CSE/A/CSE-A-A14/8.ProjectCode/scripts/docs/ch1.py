"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, FIG, H1, H2, N, P, TAB
from .refs import cite
from .shared import INTRO_POINTS, NEED, OBJECTIVES, PROBLEM_POINTS, PROBLEM_STATEMENT


def blocks():
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Background"),
        P("A telecom operator earns its revenue from a base of subscribers who can leave at almost no cost. When a customer stops using the services of a company and moves to a competitor, "
          "the event is called **churn**. Churn is expressed as the share of customers lost in a period, and in a market where most people already own a connection it is the main way a "
          "provider's customer base shrinks. Replacing a lost customer needs advertising, sales effort, handset or plan subsidies and activation work, and the literature on "
          f"telecom churn therefore treats retention as the cheaper route to stable revenue {cite('ahmad', 'vafeiadis')}."),
        P("Operators already hold the data needed to see churn coming. Every customer record carries the length of the relationship (tenure), the type of contract, the monthly and total charges, "
          "the internet and phone services taken, the add-ons such as online security or tech support, and the way the bill is paid. Patterns in these fields separate customers who stay from those who leave: "
          "short tenure, month-to-month contracts, higher monthly charges and electronic-check payment are the ones most often reported, and they are also the ones recovered by the models in this project (Chapter 8)."),
        P("Machine learning turns such records into a **churn probability** for each customer. A probability on its own, however, does not tell a retention team what to do. "
          f"The base paper of this project {cite('oprea')} makes the point from the explainability side: a churn model is only useful when the reasons behind its predictions can be inspected, "
          "so that a manager can decide which customers to call and what to offer. This project follows that motivation and builds a working application around it."),
        H2("1.2 Motivation"),
        P("The motivation for the work comes from six observations that were set down at the start of the project:"),
        B(*INTRO_POINTS),
        P("The first four points explain why prediction is worth doing; the last two explain why prediction alone is not enough. A model that returns only a yes or a no cannot guide a retention budget, "
          "because every flagged customer then receives the same treatment. A model that also shows the drivers of each prediction lets a team choose between, for example, offering a longer contract to a "
          "month-to-month customer and offering a support add-on to a customer who has none."),
        H2("1.3 Problem Statement"),
        P("The problem as it appears in current practice has four parts:"),
        B(*PROBLEM_POINTS),
        P(f"**Need.** {NEED}"),
        P(f"**Formal statement.** {PROBLEM_STATEMENT}"),
        H2("1.4 Objectives"),
        P("The project has six objectives, taken from the project proposal. Chapter 9 reports, for each of them, whether it was met."),
        N(*OBJECTIVES),
        H2("1.5 Scope of the Project"),
        P("The work covers the whole path from a customer table to a retention action: data loading and profiling, cleaning, exploratory analysis, preparation of features, training and comparison of "
          "classifiers, evaluation, risk segmentation, explanation of individual predictions, what-if analysis, rule-based retention advice, batch scoring and a drift check. "
          "These functions are delivered in two interfaces that share one code base: the original Streamlit application (13 pages) and the ChurnIQ web interface (React) served by a thin FastAPI layer."),
        P("The work does not cover the collection of real operator data, a production database, user accounts with roles, integration with a CRM, or the measurement of the financial effect of a retention campaign. "
          "These limits are stated in full in the Scope and Limitations document and in Section 9.3."),
        H2("1.6 Proposed System in Brief"),
        P(f"The system, named **{F.PRODUCT}**, accepts a customer CSV (or generates a sample of {F.DS['rows']:,} customers), detects the churn and identifier columns, cleans the table and "
          "builds a preprocessing pipeline that imputes, scales and one-hot encodes the fields. It trains Logistic Regression, Decision Tree and Random Forest classifiers (Gradient Boosting and "
          "Histogram Gradient Boosting are optional), handles class imbalance with class weights or SMOTE, and compares the models on accuracy, precision, recall, F1-score and ROC-AUC. "
          "The best model, chosen on F1 by default, is saved to disk and used to score every customer. Scores are grouped into Low, Medium, High and Critical risk with thresholds the user can edit."),
        P("For each customer the system shows a profile (Customer 360), the factors pushing the score up or down, the effect of changing an attribute (what-if) and a list of retention actions produced "
          "by transparent IF/THEN rules. It can also score a new CSV in one step and check whether new data have drifted from the data the model was trained on. The figure below shows the workflow."),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow of a retention analysis in ChurnIQ", 6.0),
        H2("1.7 Relation to the Base Paper"),
        P(f"The base paper, Oprea and Bara {cite('oprea')}, proposes a unified perturbation-based explainer for churn models and compares it with SHAP and LIME on the public Telco data. "
          "This project is an **applied extension of its motivation**, not a reproduction of its experiments. It adopts the paper's emphasis on explaining churn predictions and its finding that contract type, "
          "monthly charges and tenure drive churn, and it builds the surrounding application: scoring, risk bands, per-customer explanation, what-if analysis and retention advice. "
          "It does not implement the paper's unified perturbation explainer, LIME, or the gradient-boosting libraries it uses, and it does not use the real Telco data; Section 8.9 sets out the differences."),
        H2("1.8 Data Used and a Caution"),
        P(f"No real operator data were available to the team. The dataset used throughout the project (`data/customer_churn.csv`) is therefore **synthetic**: {F.DS['rows']:,} customers generated by "
          f"`src/sample_data.py` with a fixed random seed, using the same 21-column schema as the public Telco churn data {cite('telco')} and a churn rate of {F.DS['churn_rate_pct']}%. "
          "Churn is generated from a latent risk score built from contract type, tenure, payment method, services and charges, plus random noise. "
          "Models trained on it will recover those relationships, which is a useful check of the pipeline, but the metrics say nothing about accuracy on a real operator's customers. "
          "Every result in this report is labelled accordingly."),
        H2("1.9 Organisation of the Report"),
        TAB("Organisation of the report", ["Chapter", "Content"],
            [["1", "Introduction: background, motivation, problem statement, objectives, scope"],
             ["2", "Literature survey: base paper, related work, research gap"],
             ["3", "Feasibility study: technical, economic, operational, schedule and risk"],
             ["4", "System requirements and analysis: functional and non-functional requirements, hardware, software, use cases"],
             ["5", "System design: architecture, data flow, UML, logical data model, algorithm flowchart"],
             ["6", "Methodology and software implementation: pipeline, algorithms, modules, API, interface"],
             ["7", "System testing: unit, integration, smoke and interface tests, defects found"],
             ["8", "Results and output screens: metrics, stability, analysis, performance, base-paper comparison, screens"],
             ["9", "Conclusion"],
             ["10", "Future scope"],
             ["", "References, Appendix A (important code), Appendix B (installation and user guide), Appendix C (additional screens)"]],
            widths=[0.8, 5.2], align=["c", "l"]),
    ]
