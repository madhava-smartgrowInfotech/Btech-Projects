"""Chapter 1: Introduction."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, N, P, TAB


def blocks():
    r = F.R
    ds = F.DS
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P("This chapter introduces the domain of the project, the motivation for building the Smart Campus Placement System, the problem it addresses, the objectives set for it, "
          "the scope that was actually delivered, the contributions, and the limitations and assumptions that govern every result reported later. It closes with a map of the rest of the report."),

        H2("1.1 Domain and Background"),
        P("Campus placement is the process through which companies recruit final-year students directly from their college. For most engineering students it is the first and often the only "
          "route to a job, and for the college the placement record is one of the most visible measures of the quality of its programmes. A placement season is a sequence of eligibility checks, "
          "aptitude tests, technical rounds and interviews, run by a placement cell that has to match hundreds of students with dozens of recruiters, each of whom publishes its own cut-offs "
          "for marks, backlogs and test scores."),
        P("Colleges already keep the raw material for a better process. Every student has an academic record (CGPA, school percentages, backlogs), scores from aptitude and technical tests, "
          "a count of projects, internships and certifications, and, for earlier batches, an outcome: placed or not placed. Educational data mining is the field that turns such records into "
          "decisions, and supervised machine learning (ML) is its main tool: a classifier learns from past students which combinations of attributes were followed by a placement, and then "
          "estimates the probability for a student whose outcome is not yet known [1]."),
        P("Two recent papers frame this project. The declared base paper, Prasanna Kumari et al. [1], builds a placement-prediction web application on a synthetic student dataset with "
          "Logistic Regression, Random Forest and Gradient Boosting, and adds batch prediction, skill-gap analysis and report generation. The technique on which the code of this project is built comes "
          "from Heidari Fard and Tabrizi [2], who predict graduate admission with XGBoost [3], calibrate the probabilities with Platt scaling [4], refine borderline cases with a local k-nearest-neighbour "
          "model [7], explain the model with SHAP [5] and recommend alternative universities and programmes. A placement is structurally the same decision as an admission: a student with a profile "
          "applies to an organisation and either is or is not accepted. The Smart Campus Placement System therefore carries the admission framework over to placements, with companies in place of "
          "universities and job roles in place of programmes."),

        TAB("Mapping of the admission framework [2] to placement (as implemented)", ["Base paper [2] (admission)", "This project (placement)"],
            [["University", "Company (30 companies in three tiers)"],
             ["Programme", "Job role (eight roles; four searched by the recommendation module)"],
             ["QS world rank", "Company tier (1 dream, 2 core, 3 mass recruiter)"],
             ["Applicant GPA and its proximity to a university requirement", "CGPA and its proximity to the company cut-off, with a tolerance that depends on the tier"],
             ["Programme admission rate", "Company hiring rate"],
             ["Programme x QS rank interaction", "CGPA x tier interaction, plus gap features against CGPA, aptitude and technical cut-offs"],
             ["Country and budget filters", "Location preference and minimum package"],
             ["Accepted or rejected", "Placed or not placed"]],
            widths=[3.2, 3.5], align=["l", "l"], size=10),
        P("The mapping is a design choice of this project, not a result: the base paper never claims that placements behave like admissions. What it does supply is a tested recipe (calibrate, refine borderline "
          "cases locally, recommend only feasible alternatives, explain with SHAP) that fits the structure of the placement decision."),

        H2("1.2 Motivation"),
        P("Four observations motivate the work. They come from the batch problem statement and from how placement cells are described in the base paper [1]."),
        B("**Data is stored but not used.** Placement cells keep student records in spreadsheets; none of the predictive signal in them is exploited before the season starts.",
          "**Students learn where they stand too late.** A student who is below a company's cut-off usually finds out when the shortlist is published, when there is no time left to improve.",
          "**Shortlisting is manual.** Recruiters ask for lists filtered by CGPA, aptitude and branch, and the cell prepares them by hand in different ways for different recruiters.",
          "**Feedback is generic.** \"Improve your skills\" does not say which skill, against which company, or by how much."),
        P("An early, probability-based estimate addresses the first two: it can be produced before the season, for every student and every company, and re-computed when a student improves. "
          "A recommender that searches companies and roles where the estimated probability is higher turns a rejection into a concrete next step. Dashboards and a filter for recruiters address the third and fourth."),

        H2("1.3 Problem Statement"),
        P("The batch problem statement lists four weaknesses of current practice:"),
        B(*lit.PROBLEM_POINTS),
        P("Taken together, and written as a task for software, the problem addressed by this project is:"),
        P("*" + lit.PROBLEM_STATEMENT + "*"),

        P("**Research gap.** The literature surveyed for this project (Chapter 2) predicts placement, but stops at a yes or no or at a list of weak attributes. It rarely calibrates its probabilities, "
          "rarely explains them per company, and does not turn a low probability into alternative company-role targets. Closing that gap, with an honest measurement of what the added components are worth, is the aim of this project."),

        H2("1.4 Need for the Proposed System"),
        P("The batch documents summarise the need in one sentence: " + lit.NEED[0].lower() + lit.NEED[1:] + " Three properties follow from it. The system must give a probability, not only a yes or no, "
          "because a probability can be ranked, compared across companies and calibrated against what actually happened [8], [9]. It must be explainable, because a placement officer who "
          "cannot say why a student was marked \"needs improvement\" cannot act on the result [5]. And it must be cheap to run: a placement cell has an ordinary PC, not a cluster, and the "
          "whole system here trains in about three seconds and answers a prediction request in about 66 milliseconds on a six-core desktop processor (Chapter 8)."),

        H2("1.5 Objectives"),
        P("The six objectives are those of the batch document 6.OBJECTIVES&PROBLEM STATEMENT. The table states, for each, how it was addressed and whether it was met. "
          "\"Partly\" and \"Not met\" are used where the work fell short; Chapter 8 gives the evidence."),
        TAB("Objectives and their status", ["No.", "Objective", "How it was addressed", "Status"],
            [["O1", lit.OBJECTIVES[0], f"No real placement data was available. A deterministic generator (`src/generate_dataset.py`, seed 42) produced {ds['rows']:,} synthetic students and a table of {ds['companies']} companies.", "Partly (synthetic)"],
             ["O2", lit.OBJECTIVES[1], f"Frequency encoding, standardisation and six engineered gap features (24 features). No missing values; classes are {ds['placed_rate']*100:.1f}% placed, so no resampling was applied; a stratified split keeps the ratio.", "Met"],
             ["O3", lit.OBJECTIVES[2], "Six baselines, a Platt-calibrated XGBoost and two hybrid variants were trained and compared on a held-out test set, plus a five-seed repetition.", "Met"],
             ["O4", lit.OBJECTIVES[3], "A company-role recommender ranks the 30 companies against a student profile using calibrated probabilities and feasibility filters (hybrid, company-only and role-only lists).", "Met (gains are model estimates)"],
             ["O5", lit.OBJECTIVES[4], "Rule-based skill-gap tips against the company's cut-offs for each prediction, and a SHAP ranking of the features that move the probability most.", "Met (rules, global SHAP)"],
             ["O6", lit.OBJECTIVES[5], "An officer dashboard (metrics, SHAP, PCA, probability histogram, branch placement rates) and a recruiter shortlist; accuracy, precision, recall, F1, ROC-AUC and Brier score are reported.", "Met"]],
            widths=[0.45, 2.1, 3.3, 0.9], align=["c", "l", "l", "c"], size=9.5),

        H2("1.6 Scope of the Project"),
        P("**In scope.** (i) Generation and preparation of a placement dataset; (ii) training, calibration and evaluation of the classifiers; (iii) placement-probability prediction with skill-gap tips for one "
          "student, one company and one role; (iv) company-role recommendation; (v) an officer dashboard and a recruiter shortlist; (vi) two interfaces over the same ML code: the original Flask application "
          "and a FastAPI service with a React front end; (vii) tests, measurements and documentation."),
        P("**Out of scope.** Real placement records, integration with a college information system, login and roles, storage in a relational database (the batch description names MySQL; this implementation "
          "reads CSV files and pickled models and uses no database), batch prediction from an uploaded file, generated reports and e-mail, and any longitudinal follow-up of what happened to recommended students."),

        H2("1.7 Contributions"),
        N("**Placement adaptation of a published hybrid framework.** The admission framework of [2] is mapped to placement: company for university, role for programme, company tier for QS rank, CGPA proximity for GPA proximity, company hiring rate for programme admission rate, and gaps against company cut-offs as features.",
          "**A working calibrated predictor with explanations.** Calibrated XGBoost probabilities, a kNN local model for borderline cases, SHAP importance and rule-based skill-gap tips, served through a validated API.",
          "**A three-strategy company-role recommender** with feasibility filters, returning the original-target probability, the average gain and the match rate.",
          "**Dashboards and a recruiter shortlist** for placement officers and recruiters, in a React application and the original Flask application.",
          "**An honest evaluation.** Besides the paper's metrics, the project measures what the paper's residual rule hides: it selects residual cases with the true labels, so its gain cannot be had at serving time. "
          f"A label-free version scores {r['hybrid_knn_labelfree']['accuracy']:.4f} against {r['xgb_calibrated']['accuracy']:.4f} for calibrated XGBoost (Chapter 8).",
          "**Reproducible tooling.** Scripts for the experiments, 46 automated checks, diagrams and screenshots, all re-runnable."),

        H2("1.8 Limitations and Assumptions"),
        P("The following limitations apply to everything in this report and are repeated where they matter."),
        B("**The data is synthetic.** All records are produced by a generator whose labels follow a logistic rule with noise. Models can recover that rule, so accuracy is not evidence about real students. "
          f"Even Logistic Regression reaches {r['logreg']['accuracy']:.4f} accuracy and the highest AUC ({r['logreg']['roc_auc']:.4f}).",
          "**The company table is invented.** The 30 companies, their cut-offs, packages and hiring rates are plausible values, not recruiter requirements.",
          "**The hybrid gain depends on the labels of the test set** in the form defined by the base paper; the deployable form gains almost nothing on this data.",
          "**No authentication, database or rate limiting.** Every endpoint is public on localhost.",
          "**Recommendation gains are model estimates** that were never checked against real outcomes, and the recommender is slow (about 5 seconds per request).",
          "**One machine, one dataset.** All measurements come from a single CPU-only desktop and one generated dataset."),
        P("Assumptions made: a student's profile is the set of 13 attributes in the form (CGPA, school percentages, four test scores, counts of projects, internships, certifications and backlogs, branch, degree); "
          "a placement is a binary outcome for one target company and role; the company table is current; and the probability threshold for \"placement ready\" is 0.5."),

        H2("1.9 Organisation of the Report"),
        TAB("Chapters of this report", ["Chapter", "Content"],
            [["1 Introduction", "Domain, motivation, problem, objectives, scope, contributions, limitations"],
             ["2 Literature Survey", "The two base papers, related work by theme, datasets and algorithms, research gap"],
             ["3 Feasibility Study", "Technical, economic, operational and schedule feasibility"],
             ["4 System Requirements and Analysis", "Existing and proposed system, requirements, hardware, software, user roles"],
             ["5 System Design", "Architecture, workflow, data flow diagrams, UML, database design, modules, user interface"],
             ["6 Methodology and Software Implementation", "Data, pre-processing, algorithms, formulation, API, security, installation"],
             ["7 System Testing", "Strategy, unit, integration, functional, security, validation, performance, limits"],
             ["8 Results and Output Screens", "Output screens, model performance, comparison with the base papers, failure analysis"],
             ["9 Conclusion", "Summary, objectives achieved, findings, applications, limitations"],
             ["10 Future Scope", "Improvements, features, scalability, further research"],
             ["References, Appendices A-C", "Reference list, important code, installation and user guide, additional screens"]],
            widths=[2.3, 4.4], align=["l", "l"], size=10),
    ]
