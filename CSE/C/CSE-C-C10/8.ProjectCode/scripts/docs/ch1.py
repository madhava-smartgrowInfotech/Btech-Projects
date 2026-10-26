"""Chapter 1: Introduction."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, N, P, TAB
from .refs import cite


def blocks():
    R = F.R
    rf, xg, lr = R["models"]["Random Forest"], R["models"]["XGBoost"], R["models"]["Logistic Regression"]
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P("This chapter introduces the domain of the project, the motivation for building the startup outcome prediction system, the problem it addresses, the objectives set for it, "
          "the scope that was actually delivered, the contributions, and the limitations and assumptions that govern every result reported later. It closes with a map of the "
          "rest of the report."),

        H2("1.1 Domain and Background"),
        P("A startup is a young company that tries to grow quickly around a new product or business model, usually with money from angel investors and venture capital. "
          "Startups drive innovation, create jobs and open new markets, but most of them do not survive. The base paper of this batch repeats the commonly quoted figure that "
          f"nearly nine in ten fail within the first few years because of a lack of capital, a poor fit with the market, weak management and strong competition {cite('base')}; "
          f"the method paper that this project follows closely quotes a similar failure rate of about 90 % and treats an exit through acquisition or an initial public offering as success {cite('maarouf')}."),
        P("Investors and founders still judge most early-stage ventures by experience and intuition. That works when the person has seen many similar companies, but it is "
          f"subjective, hard to repeat and open to bias {cite('base')}. At the same time, structured data about funding rounds, team, sector and location exists from the very first "
          "months of a company's life. Machine learning (ML) can learn which combinations of these indicators historically preceded success and which preceded closure."),
        P("Predicting startup success is therefore a supervised classification problem on mostly tabular data. Studies reported through the base paper use logistic regression, "
          f"Random Forest, support vector machines and gradient boosting, and find that ensembles of trees usually do best {cite('base', 'bidgoli', 'li')}. Recent work adds "
          f"text, such as the free-text description a startup writes about itself, and uses language models to compare a new startup with similar past ones {cite('maarouf', 'fused')}, "
          f"or builds leakage-safe temporal panels with interpretable models {cite('mashhadi')}. A recurring warning is look-ahead bias: when a model sees information that "
          f"became known only after the outcome, its accuracy is unrealistically high {cite('zbikowski', 'leakage')}."),
        P("This project, VenturePulse, takes that background into an application. A user enters the funding, team and ecosystem indicators of a startup and, optionally, a short "
          "business description. The system returns an estimated outcome (SUCCESS or FAILURE) with a probability, the features that pushed the estimate up or down, and the "
          "comparable historical startups behind it. The technical core is a structured preprocessing pipeline, four compared classifiers, a sentence embedding of the description "
          f"{cite('sbert', 'minilm')} fused with the structured vector, and a balanced nearest-neighbour search over the training startups {cite('knn')}."),

        H2("1.2 Motivation"),
        P("Three observations motivate the project. First, a wrong early judgement is expensive. Capital that is committed to a venture that was visibly weak, or withheld from one "
          "that was visibly strong, cannot be recovered. A cheap, repeatable and explainable second opinion, built from the same indicators every time, helps to reduce "
          "inconsistency even if it is imperfect."),
        P("Second, a bare number is not enough. A founder or an analyst who is told that a startup has a 0.83 chance of success learns nothing that can be acted on. The project "
          "therefore attaches to each prediction the factors that drove it and a table of the most similar historical startups with their outcomes, so that the reader can judge "
          "whether the comparison is sensible."),
        P("Third, published studies often leave a reader unable to judge how far the numbers can be trusted. The declared base paper, for example, reports accuracies of 85 to "
          f"92 % for its best ensembles but, in the version available to us, gives neither the size of its dataset nor a table of per-model results {cite('base')}. The team decided "
          "to measure everything itself, on a real public table, to separate what was measured on real data from what was measured on the synthetic data that the shipped "
          "application had to fall back on, and to say plainly where the evidence is weak."),

        H2("1.3 Problem Statement"),
        P(lit.PROBLEM_STATEMENT),
        P("The project's own problem analysis lists four difficulties that the design must respect:"),
        B(*lit.PROBLEM_POINTS),

        H2("1.4 Need for the Project"),
        P("A usable early-stage screening aid has to satisfy several needs at once, and existing work tends to satisfy only some of them. It has to learn from historical outcomes "
          "instead of opinion. It has to cope with imbalance between successful and failed startups, because a model that favours the majority class looks accurate while being "
          "useless for the minority. It has to name the drivers of each prediction, because a founder cannot act on an unexplained score. It has to run on an ordinary computer "
          "without paid services, so that a student team, a small fund or an incubator can reproduce it. And it has to be honest about its reliability."),
        P(f"The survey in Chapter 2 shows that the base paper stops at a Flask form with a probability {cite('base')}, and that the batch survey names the gap: "
          "systematic feature engineering around funding velocity and team composition, with explicit handling of the rare-success class. The project is built to address "
          "that gap as far as the available data allow, and to report plainly where it could not."),

        H2("1.5 Objectives"),
        P("The six objectives approved for the project are:"),
        N(*lit.OBJECTIVES),
        P(f"Chapter 8 measures each objective against the outcome. In short: the real public table of {F.REAL_ROWS} startups was collected and analysed, while the shipped "
          f"application runs on a synthetic fallback of {F.SYN_ROWS:,} rows with the same schema (objective 1, partly met); cleaning and log-scaling of funding were done, but "
          "funding velocity is only approximated by the age fields and the number of rounds, and no team-experience or market-context data exist in either dataset (objective 2, "
          "partly met); class imbalance was handled with balanced class weights and compared with oversampling (objective 3); four classifiers plus a second boosting model were "
          "trained and compared (objective 4); the separating features were identified with three methods (objective 5); and accuracy, precision, recall, F1 and ROC-AUC were "
          "all measured on the real data (objective 6), although ROC-AUC was not recorded for the fused model that the application ships."),

        H2("1.6 Scope"),
        P("In scope are the following items, all of which exist in the delivered code base:"),
        B("a structured preprocessing pipeline with de-duplication, target mapping, median and most-frequent imputation, scaling, one-hot encoding of state and industry, and a log-scaled funding feature (37 encoded features);",
          "four classifiers (Logistic Regression, Decision Tree, Random Forest, XGBoost) compared over five repeated stratified 80/20 splits, with the best by balanced accuracy served;",
          "a 384-dimensional sentence embedding of the optional business description (company names masked), fused with the structured vector and searched by cosine similarity over training startups only, with balanced k = 10, 20, 30 or 50;",
          "deterministic explanations (top signed coefficients or importances plus retrieval statistics) and a three-level risk label;",
          "a FastAPI service with prediction, model-metric, insight, configuration, feature-importance and demonstration sign-in endpoints, and the original server-rendered pages;",
          f"a React web application with a landing page, a demonstration sign-in and four screens (Dashboard, Analyze with its result view, Model performance, Insights), about {F.LOC['frontend']:,} lines of JavaScript and styles;",
          f"{F.N_TESTS} automated checks and scripts that regenerate every measured number in this report from the real public table."),
        P("Out of scope are investment advice, founder-level and market-level data collection, temporal (out-of-time) validation, deployment to a public server, multi-user "
          "accounts and databases, and any field study with real investors or founders."),

        H2("1.7 Contributions"),
        P("The contributions are modest and are stated as such:"),
        N("An end-to-end startup-outcome application that returns the prediction, the feature drivers and the comparable historical startups together, with a React front end and local-only inference.",
          "A fused structured-plus-text representation with balanced, training-only cosine retrieval, adapted from the retrieval idea of the method paper without a large language model, and with company names masked to avoid memorisation.",
          f"A reproducible benchmark on the real public table ({F.REAL_ROWS} startups) with ten studies: model comparison, class imbalance, decision threshold, calibration, forest size, the 70:30 protocol of the base paper, synthetic-to-real transfer, a leakage ablation, a retrieval-only classifier and per-industry errors.",
          "Findings that are useful beyond this implementation: the ensemble ranking of the base paper is reproduced but its 85 to 92 % accuracy level is not; fields recorded around the outcome window raise ROC-AUC by about 0.1; retrieval alone matches logistic regression; and synthetic text can leak the label."),

        H2("1.8 Summary of the Results"),
        P(f"On the real table, with five repeated 80/20 splits and structured features only, Random Forest and XGBoost are the best models: balanced accuracy {F.pm(rf)} and "
          f"{F.pm(xg)}, ROC-AUC {F.pm(rf, 'roc_auc')} and {F.pm(xg, 'roc_auc')}, accuracy {F.pm(rf, 'accuracy')} and {F.pm(xg, 'accuracy')}. Logistic Regression reaches balanced "
          f"accuracy {F.pm(lr)} and ROC-AUC {F.pm(lr, 'roc_auc')}. These figures are well below the 85 to 92 % accuracy claimed by the base paper, whose dataset is not specified. "
          f"The shipped application reports a balanced accuracy of {F.syn_app('Logistic Regression')} for Logistic Regression, but that number comes from the synthetic fallback "
          "whose descriptions differ in wording between the two classes; it is a check of the pipeline, not evidence of real-world skill."),
        FIG(F.fig("f13_class_balance.png"), f"Class balance of the two datasets: the real table ({F.REAL_ROWS} startups) has SUCCESS as the majority class, the synthetic fallback ({F.SYN_ROWS:,}) has FAILURE as the majority.", 4.8),

        H2("1.9 Limitations and Assumptions"),
        P("The main limitations are listed here and discussed in detail in Chapters 7 and 8."),
        B("The shipped model was trained on synthetic data because the public dataset could not be downloaded without a login when the application was built; all real measurements come from a separate study of the same pipeline.",
          "The real table has no free-text description, so the text channel and the fusion were not evaluated on real data.",
          "No dates are available, so no temporal split could be made and look-ahead bias cannot be excluded; four fields (relationships, milestones and two milestone ages) are partly recorded after the outcome.",
          f"The real table is small ({F.REAL_ROWS} rows), concerns US companies only and gives test folds of 185 rows, so differences of a few points between models are within noise.",
          "Founder experience, team size and market-trend data named in the abstract are not part of either dataset."),
        P("The assumptions are that the labels of the public table (acquired = success, closed = failure) are correct, that the historical relationships between indicators and outcomes "
          "carry over to the companies being scored, that the inputs entered by a user are truthful, and that the machine used for measurement (an Intel Core i5-12500 with 15.7 GB "
          "of memory and no graphics processor) is representative of an ordinary laptop."),

        H2("1.10 Organisation of the Report"),
        TAB("Organisation of the report", ["Chapter", "Content"], [
            ["1 Introduction", "Domain, motivation, problem, objectives, scope, contributions, limitations"],
            ["2 Literature Survey", "The base paper, the method and reference papers, related work by theme, datasets and algorithms, research gap"],
            ["3 Feasibility Study", "Technical, economic, operational and schedule feasibility"],
            ["4 System Requirements and Analysis", "Existing and proposed system, functional and non-functional requirements, hardware, software, user roles"],
            ["5 System Design", "Architecture, workflow, data flow diagrams, UML, data model, modules, user interface"],
            ["6 Methodology and Software Implementation", "Data, preprocessing, models, fusion and retrieval, application, API, security, installation"],
            ["7 System Testing", "Unit, integration, functional, security, validation, performance tests and their limits"],
            ["8 Results and Output Screens", "Measured results, output screens, comparison with the base papers, objectives versus outcomes"],
            ["9 Conclusion", "Summary, findings and applications"],
            ["10 Future Scope", "Improvements, further data, deployment and research"],
        ], widths=[2.3, 4.0], align=["l", "l"]),
    ]
