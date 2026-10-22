"""Chapter 1: Introduction."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, N, P, TAB
from .refs import cite


def blocks():
    a = F.A
    prop = a["proposed_test"]
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P("This chapter introduces the domain of the project, the motivation for building the fake news detection system, the problem it addresses, the objectives set for it, the "
          "scope that was actually delivered, the contributions, and the limitations and assumptions that govern every result reported later. It closes with a map of the rest "
          "of the report."),

        H2("1.1 Domain and Background"),
        P("Fake news is deliberately fabricated or misleading content presented as news. It is not new, but online platforms have changed its scale and speed: anyone can publish, "
          f"sharing costs nothing, and recommendation feeds reward content that attracts attention. A large-scale study of rumour cascades on Twitter found that false stories "
          f"travelled farther and faster than true ones {cite('vosoughi')}, and surveys of the field treat the problem as one of the main open issues of social media {cite('shu', 'survey')}. "
          "Professional fact-checkers examine claims one at a time, which is accurate but slow, so most false claims are read, believed and passed on long before a verdict is published."),
        P("Automatic fake news detection is the branch of natural language processing that tries to help. A classifier reads the text of a headline, a claim or an article and "
          f"predicts whether it is trustworthy. Early work used hand-made linguistic and n-gram features with classical learners {cite('ahmed', 'perez')}; later work uses contextual "
          f"embeddings from transformers {cite('bert', 'base')}. A parallel line of work studies the style of deceptive text, such as exaggerated wording, capital letters and "
          f"sensational vocabulary {cite('potthast', 'rashkin')}."),
        P("Most detectors treat the task as binary: a text is either real or fake. Real fact-checking is not binary. Organisations such as PolitiFact grade claims on a scale from "
          f"true to pants-on-fire, and the LIAR family of datasets keeps these six grades {cite('liar', 'liar2')}. A claim can mix accurate figures with an exaggerated conclusion, "
          "and a system that forces such a claim into one of two boxes either hides the nuance or misleads. This project therefore works with three verdicts: REAL, "
          "PARTIALLY TRUE and FAKE."),
        P("The technical idea of the project follows the batch title. Text is converted into a high-dimensional feature vector (word and word-pair weights plus a few "
          f"stylometric measures); Principal Component Analysis (PCA) {cite('pca', 'pca87')} compresses it; the Firefly algorithm {cite('firefly09', 'firefly10')}, a swarm "
          f"metaheuristic, chooses which compressed components to keep and sets the parameters of the classifier; and a multi-class Support Vector Machine (MSVM) {cite('svm', 'msvm')} makes the "
          "decision. The expectation behind the design, stated in the batch abstract, is a computationally light pipeline that does not need a graphics processor or a large "
          "pre-trained language model."),

        H2("1.2 Motivation"),
        P("Three observations motivate the project. First, the volume of published text is far beyond what human fact-checkers can examine, so a cheap automatic screening aid "
          "that flags suspicious items for a human is useful even if it is imperfect. The system built here is explicitly such an aid: its screens say that it judges writing "
          "style and vocabulary, not facts."),
        P("Second, many published detectors rely on large neural models that need specialised hardware. The base paper chosen for this batch uses CAMeLBERT embeddings on a "
          f"Tesla T4 graphics processor {cite('base')}. A pipeline of TF-IDF, PCA and an SVM can be trained and run on an ordinary laptop, and the batch asks whether feature "
          "reduction plus metaheuristic tuning can deliver comparable accuracy at lower cost. Whether it does is an empirical question, and the project sets out to answer it "
          "with measurements rather than assumptions."),
        P("Third, a classifier in a notebook is not a tool. A person who wants to screen one article, a spreadsheet of articles, or to retrain the model on their own labelled "
          "data needs an application. The team therefore delivered the whole chain: a web interface (named TruthGlow), a service layer and the library, together with a command "
          "line and a Streamlit app kept from the first version."),

        H2("1.3 Problem Statement"),
        P(lit.PROBLEM_STATEMENT),
        P("The project's own problem analysis lists four difficulties that the design must respect:"),
        B(*lit.PROBLEM_POINTS),

        H2("1.4 Need for the Project"),
        P("A usable screening tool has to satisfy several needs at once, and existing work tends to satisfy only some of them. It must give a graded verdict rather than a "
          "binary one, because partly true claims are common. It must be cheap to train and fast to run, so that it can be retrained on new topics, which change every week, "
          "without special hardware. It must say how confident it is, so that a reader knows how much weight to give the verdict. It must be usable by a person who is not a "
          "machine-learning engineer, and it must be reproducible: the data, the preprocessing, the optimisation and the measurements have to be inspectable and repeatable."),
        P(f"The survey in Chapter 2 shows that the strongest recent systems use transformer embeddings {cite('base', 'compare')}, while the gap named in the batch survey is a "
          "computationally light pipeline in which feature reduction and metaheuristic tuning replace model size. The project is built to test that idea and to report plainly "
          "what it achieves."),

        H2("1.5 Objectives"),
        P("The six objectives approved for the project are:"),
        N(*lit.OBJECTIVES),
        P("Chapter 8 measures each objective against the outcome. In short, the system was built and every stage exists; the dataset was assembled from the public LIAR2 benchmark "
          "(and a synthetic demonstration corpus for the shipped model); stemming, listed in objective 2, was not implemented; and for objectives 4 to 6 the evaluation shows that "
          "the Firefly optimisation did not give a measurable gain over its baselines on real data, so the aim of better accuracy at lower cost is not demonstrated."),

        H2("1.6 Scope"),
        P("In scope are the following items, all of which exist in the delivered code base:"),
        B("a text-classification library with three classes (REAL, PARTIALLY TRUE, FAKE): text cleaning, TF-IDF with word pairs, 25 stylometric features, standardisation and PCA;",
          "a Firefly optimiser that jointly selects PCA components and sets the SVM parameters C and gamma, with a size penalty on the selected subset;",
          "a multi-class RBF SVM with balanced class weights and probability output, with a default-parameter SVM as the built-in baseline;",
          "loaders for CSV files in several layouts (text and label columns, title plus text, LIAR statements) and a built-in synthetic demonstration corpus;",
          "a FastAPI service with eight endpoints (health, model information, samples, single prediction, batch preview and run, retraining and its status);",
          f"a React web application with a landing page and five application screens (Detect, Batch check, Model analytics, Retrain, About), about {F.LOC['frontend']:,} lines of TypeScript, plus the original command line and Streamlit app;",
          f"{F.N_TESTS} automated checks and a set of scripts that regenerate every measured number in this report from the real LIAR2 data."),
        P("Out of scope are fact checking against external sources, image or video analysis, languages other than English, social-network or propagation features, user "
          "accounts, deployment to a public server and any field study with real readers."),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow of the system: the training path and the inference path.", 5.6),

        H2("1.7 Contributions"),
        P("The contributions of the work are practical and are stated at the level the evidence supports:"),
        N("An end-to-end, runnable PCA + Firefly + MSVM pipeline with an explicit PARTIALLY TRUE class, packaged as a web application with single and batch detection, "
          "model analytics and in-browser retraining, in addition to the command line and Streamlit versions.",
          "A joint Firefly search over the PCA-component mask and the SVM parameters C and gamma, with a penalty on the share of components kept.",
          f"A reproducible real-data benchmark on LIAR2 ({F.NTRAIN:,} training statements, {F.NTEST:,} test statements, {len(F.SEEDS)} seeds) that compares the proposed pipeline with a default SVM, "
          "a Firefly mask without parameter tuning, an equal-budget random search and linear text classifiers: the proposed pipeline reaches a test macro-F1 of "
          f"{F.pm(prop)} and accuracy {F.pm(prop, 'accuracy')}.",
          "Honest findings: the optimiser's gain over its baselines is within the seed-to-seed noise; PCA capped at 300 components keeps only about "
          f"{F.pct(a['pca_variance']['mean'], 0)} of the variance of the real-text features; and the verdict and the displayed probabilities disagree on {F.pct(F.LV['disagree_rate'], 0)} of real test statements.",
          f"Measured cost: about {F.LAT[0]['predict_server_ms']['mean']:.1f} ms of server time per article and about {F.LAT[0]['batch']['2296']['server_s']:.1f} s for the {F.NTEST:,}-statement test split, "
          "on a CPU-only machine.",
          "Complete documentation and a verification script that checks the documents against the code and the measurements."),

        H2("1.8 Limitations and Assumptions"),
        P("The main limitations are stated here once and repeated where they matter:"),
        B(f"The model that ships with the project was trained on a synthetic template corpus of {F.DEMO['n_docs']} documents. Its perfect scores ({F.DEMO['accuracy']:.3f}) are a pipeline check, "
          f"not evidence; on real LIAR2 test statements the same model scores accuracy {F.A['demo_model_on_liar2_test']['accuracy']:.3f} and macro-F1 {F.A['demo_model_on_liar2_test']['f1_macro']:.3f}.",
          f"All real-data results come from a {F.NTRAIN:,}-statement training subsample (the Firefly search needs thousands of SVM fits) and {len(F.SEEDS)} seeds; no significance test was run.",
          f"On real data the system is a weak classifier: macro-F1 about {F.f2(prop['f1_macro']['mean'])}. PARTIALLY TRUE is the hardest class and the verdict and probabilities are inconsistent in many cases.",
          "Stemming, named in the second objective, is not implemented; the pipeline uses cleaning, stop-word removal and TF-IDF only.",
          "Only the statement text is used. No source, speaker, date or evidence is considered, so the system judges style and vocabulary, not facts.",
          "No other dataset (such as ISOT), no user study and no load test were carried out."),
        P("The assumptions are that the input is English text of at least five words, that labels in a retraining file follow the three project classes (or the LIAR and 0/1/2 conventions "
          "the loader recognises), and that the user runs the system on a personal computer. The system is a research and teaching prototype and is not a certified fact-checking service."),

        H2("1.9 Organisation of the Report"),
        TAB("Organisation of the report", ["Chapter", "Title", "Content"], [
            ["1", "Introduction", "Domain, motivation, problem, objectives, scope, contributions, limitations"],
            ["2", "Literature Survey", "Base paper analysis, related work by theme, datasets and algorithms, research gap"],
            ["3", "Feasibility Study", "Technical, economic, operational and schedule feasibility"],
            ["4", "System Requirements and Analysis", "Existing and proposed system, functional and non-functional requirements, environment"],
            ["5", "System Design", "Architecture, workflow, data-flow diagrams, UML, data model, modules, interface"],
            ["6", "Methodology and Software Implementation", "Dataset, preprocessing, PCA, Firefly, MSVM, API, security, installation"],
            ["7", "System Testing", "Strategy and results of unit, integration, functional, security and performance tests"],
            ["8", "Results and Output Screens", "Measured results, comparison with the base paper, screens, failures, objectives versus outcome"],
            ["9", "Conclusion", "Summary, findings, applications, known limitations"],
            ["10", "Future Scope", "Improvements, features, scalability, research directions"],
        ], widths=[0.7, 2.2, 3.3], align=["c", "l", "l"]),
        P("References and three appendices (important code, installation and user guide, additional screens) follow Chapter 10."),
    ]
