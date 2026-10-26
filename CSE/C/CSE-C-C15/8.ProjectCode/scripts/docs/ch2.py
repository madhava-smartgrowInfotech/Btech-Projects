"""Chapter 2: Literature Survey (SentinelFlow, CSE-C-C15)."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def blocks():
    k = F.K()
    r = R
    return [
        H1("2. LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The batch literature survey (5.LITERATURE SURVEY.docx) lists five works: the base paper and four recent articles on DDoS detection and mitigation. This chapter reads them together with "
          "the works the base paper itself cites, two further papers found in the batch folder, and the dataset papers on which every result in this field depends. "
          f"Of the five survey items, only the base paper [{r['base']}] was available in full. For the PeerJ article [{r['s_wisne']}] only the abstract was available, and for the remaining three "
          f"[{r['s_ijesat']}], [{r['s_ddqn']}] and [{r['s_ijarcce']}] only the bibliographic record could be verified. Their results are therefore never quoted in this report; they are listed so that the survey is complete and honest about what was read."),
        P(f"The works fall into five groups: threshold and statistical detection, supervised machine learning, ensembles with feature selection (the base paper's family), deep, reinforcement and language-model approaches, "
          f"and studies of the data itself. Table 2.1 summarises the works whose content was read."),
        TAB("Summary of the surveyed works", ["Work", "Year", "Approach", "Finding / limitation"], [list(x) for x in lit.LIT_TABLE],
            widths=[1.5, 0.45, 2.2, 2.3], align=["l", "c", "l", "l"], size=9.5),
        H2("2.2 Base Paper Analysis"),
        P(f"**Reference.** {F.BASE_PAPER} The paper was received on 12 August 2025, accepted on 26 September 2025 and published on 7 October 2025. The batch record (3.BASE PAPER.docx) names it as the base paper of this project."),
        H3("2.2.1 Problem and motivation"),
        P("The paper starts from the observation that in software-defined networking (SDN) the central controller is both the source of visibility and a single point of failure: flooding it can destabilise the whole network. "
          "Detection therefore has to be accurate, general enough for low-rate and zero-day attacks, and light enough to run next to the controller without degrading it. The authors criticise earlier work on three grounds: "
          "models are evaluated on the dataset they were trained on, outdated datasets are used, and almost no paper reports memory, latency or model size."),
        H3("2.2.2 Method"),
        P("The contribution is a hybrid feature-selection method and a set of voting ensembles."),
        B("**RF-BPI feature selection.** Random Forest feature importance is combined with a Banzhaf Power Index from cooperative game theory. The index of a feature is the average marginal contribution of that feature over all subsets of the other features; "
          "because that is exponential, the paper estimates it by flipping the value of one feature in a sample of test rows and recording the share of rows whose predicted label changes, then normalises the scores. Features with negligible scores are dropped.",
          "**Classifiers.** XGBoost, Random Forest, Gradient Boosting, SVM, k-nearest neighbours, AdaBoost and Gaussian Naive Bayes are trained individually; eleven classifiers are compared in the paper's accuracy figures, and tree-based models perform best.",
          "**Ensembles.** Four hard-voting ensembles (clf1 to clf4) are built from the best base learners; clf4 deliberately mixes complex (XGBoost, SVM) and simple (Naive Bayes) models for diversity.",
          "**Resource profiling.** Training time (wall clock), inference time on the whole test set, peak memory (memory_profiler) and model size on disk (joblib) are recorded alongside accuracy, precision, recall and F1."),
        H3("2.2.3 Data and results"),
        P(f"Two datasets are used: an SDN flow dataset with 104,345 records and 23 features, and a subset of CIC-DDoS2023 with 1,754,109 rows and 47 features. All four ensembles reach 100 % accuracy, precision, recall and F1 on both. "
          "The differences lie in cost: the ensembles that contain an SVM (clf3 and clf4) needed more than 4,000 seconds to train on the SDN data, the ensemble with k-nearest neighbours (clf2) needed more than 150 seconds to classify the SDN test set, "
          "while clf1 stayed light in training time, inference time and size (below 1 MB on CIC-DDoS2023 for clf1 and clf3). On CIC-DDoS2023 all models trained in under 15 seconds. "
          "The paper concludes that clf1 is the deployment-ready choice and compares its accuracy with prior work, for instance 99 % on CICIDS2017 and CIC-DDoS2019 for the ensemble of Alduailij et al. "
          f"[{r['alduailij']}] and 99.97 % accuracy with 99.98 % F1 for Becerra-Suarez et al. [{r['becerra']}] (both as reported in the base paper)."),
        H3("2.2.4 Strengths"),
        B("Two datasets, one of them recent, and a stated attempt at cross-environment validation.",
          "Resource profiling is part of the evaluation, which is rare and directly relevant to deployment next to a controller.",
          "The feature-selection idea is interpretable: a feature is kept because flipping it changes decisions, not only because it splits trees well."),
        H3("2.2.5 Limitations and what it leaves open"),
        B("**Perfect scores on everything.** Accuracy of 100 % on four ensembles and two datasets suggests that the tasks are nearly separable or that the evaluation is easy; the paper itself notes that confusion rises with the number of classes in a multi-class setting.",
          "**Offline only.** Both datasets are stored files. The paper proposes a sidecar that would throttle or blackhole suspicious flows but does not build or test it; it names live testbeds and production traces as future work.",
          "**Detection only.** There is no mitigation component, no severity grading and no measure of the time from detection to action.",
          "**Binary labels.** Multi-class detection, online learning and federated deployment are future work."),
        P("SentinelFlow starts exactly at these gaps: it builds the capture-to-action loop on a commodity host and measures it, while accepting the base paper's own warning that high offline accuracy is not enough. "
          "It does not reproduce the Banzhaf selection or the voting ensembles; Chapter 8 instead compares single classifiers on real flows."),
        H2("2.3 Related Work by Theme"),
        H3("2.3.1 Threshold, statistical and early SDN detection"),
        P(f"Early SDN detectors watched flow-level statistics such as packet rates, destination entropy and connection counts collected from OpenFlow switches. Braga et al. [{r['braga']}] proposed a lightweight detector for NOX/OpenFlow that "
          "feeds flow statistics to a self-organising map. Such methods catch volumetric floods but, as the base paper observes, are poorly suited to low-rate or stealthy variants and depend on manual tuning. "
          f"The survey of Su et al. [{r['su']}] and the taxonomy of Mirkovic and Reiher [{r['mirkovic']}] organise this space of detection and mitigation technologies and are the best starting points for a reader new to the field."),
        H3("2.3.2 Supervised machine learning"),
        P(f"Most recent work trains a classifier on labelled flow features. Rahman [{r['rahman']}] compares logistic regression, a decision tree and an SVM on a CIC dataset sample and reports accuracies of 0.593, 0.827 and 0.971 respectively, "
          f"with the SVM the best. Zaman et al. [{r['zaman']}] study decision-tree algorithms for DDoS detection in SDN, and Raghavendran and Robinson [{r['s_wisne']}] evaluate KNN, XGBoost and Naive Bayes on a testbed dataset "
          "from a WISNE-SDN IoT controller, with accuracies of 97 % for KNN and 100 % for XGBoost according to the abstract. "
          f"Sahoo et al. [{r['sahoo']}] tune an SVM with an evolutionary algorithm for SDN DDoS detection, and Varghese and Muniyal [{r['varghese']}] propose an IDS framework for SDN. "
          "The common pattern is high accuracy on a single stored dataset and detection without action."),
        H3("2.3.3 Ensembles and feature selection"),
        P(f"Alduailij et al. [{r['alduailij']}] select features with mutual information and Random Forest importance and combine classifiers by voting; Hossain and Islam [{r['hossain']}] use hybrid feature selection with an ensemble to reduce false positives; "
          f"Becerra-Suarez et al. [{r['becerra']}] combine tree learners and deep networks with careful data processing. Alashhab et al. [{r['alashhab']}] go furthest towards the project's goal by using an ensemble *online* model for both detection and mitigation in SDN, "
          "although their record could only be verified bibliographically here. The base paper belongs to this family and adds the Banzhaf-based selection and resource profiling."),
        H3("2.3.4 Deep, reinforcement and language-model approaches"),
        P(f"Jadric and Mladenovic [{r['s_ddqn']}] apply double deep Q-networks to detection and mitigation, which treats mitigation as a learned policy; only the title could be verified. "
          f"Swileh et al. [{r['carpet']}] target *carpet-bombing* attacks in SDN with a retrieval-augmented framework: interface-level traffic features are turned into embeddings, similar past traffic is retrieved with FAISS and a large language model infers whether the traffic is an attack, "
          "without supervised training. Their best configuration (Gemma-4-31B-IT) reports 99.94 % accuracy with about two seconds per request on a Mininet and Ryu testbed with hping3-generated attack traffic. "
          "It is the closest published work to this project in intent (carpet bombing, detection and mitigation) and the most different in method: it needs an LLM service and about two seconds per decision, whereas SentinelFlow uses a 2.7 MB forest on the local machine."),
        H3("2.3.5 Programmable data planes and applied software"),
        P(f"Musumeci et al. [{r['musumeci']}] move part of the detection into a P4 programmable switch to reduce controller load, at the price of specialised hardware. Akroma and Mohamed [{r['akroma']}] analyse DDoS attacks and develop software for detection and mitigation with machine learning. "
          f"The batch survey also lists [{r['s_ijesat']}] and [{r['s_ijarcce']}] under similar titles; neither could be read."),
        H3("2.3.6 Studies of the data and of the method"),
        P(f"Two papers do not propose a detector but affect how every detector's numbers should be read. Engelen et al. [{r['engelen']}] audited CICIDS2017 and documented labelling and flow-construction problems, which is why the result of this project on that dataset "
          f"is reported with caveats. Sommer and Paxson [{r['sommer']}] explained why machine learning for intrusion detection is harder than in other fields, with a closed-world assumption that rarely holds, high cost of errors and difficulty of evaluation. "
          "Both support the decision to measure the shipped model on data it was not built from."),
        H2("2.4 Datasets and Algorithms Used in the Surveyed Work"),
        P(f"**Datasets.** The base paper uses an SDN flow dataset (104,345 records, 23 features) and CIC-DDoS2023 (1,754,109 rows, 47 features in the subset). Alduailij et al. and Becerra-Suarez et al. use CICIDS2017 and CIC-DDoS2019 (as reported in the base paper). "
          f"CICIDS2017 [{r['cicids']}] was produced by the Canadian Institute for Cybersecurity from five days of labelled traffic (Monday to Friday) and is distributed as CSV files of flow records computed with CICFlowMeter, each with 78 features and a label. "
          f"The Friday-afternoon file used in this project's real-data evaluation has {k['real_rows']:,} rows ({k['real_benign']:,} benign and {k['real_attack']:,} labelled DDoS) and 79 columns. The Swileh et al. work builds its own Mininet dataset [{r['carpet']}], and Raghavendran and Robinson a testbed dataset [{r['s_wisne']}]."),
        P(f"**Algorithms.** Random Forest [{r['breiman']}] averages many decision trees grown on bootstrap samples with random feature subsets; it handles non-linear interactions, needs no feature scaling and exposes feature importance, which is why the base paper and this project both use it. "
          "Gradient boosting and XGBoost build trees sequentially on the errors of earlier trees. SVMs separate classes with a maximum-margin hyperplane and become expensive on large data, as the base paper's clf3 and clf4 show. "
          "k-nearest neighbours is simple but its inference cost grows with the training set (clf2). Naive Bayes is the cheapest and assumes independent features. The ensembles combine these by hard voting."),
        H2("2.5 Strengths and Limitations of Existing Approaches"),
        TAB("Strengths and limitations of the main approach families", ["Family", "Strengths", "Limitations"],
            [["Threshold and statistical", "Cheap, easy to explain, catches large volumetric floods", "Manual tuning; misses low-rate and spread-out attacks"],
             ["Single supervised classifier", "High accuracy on benchmark flows; fast inference for trees", "Accuracy measured on one dataset; no action after detection"],
             ["Ensembles with feature selection", "More stable decisions; smaller feature space; resource profile in the base paper", "SVM and kNN members are slow; still offline"],
             ["Deep and reinforcement learning", "Can learn a mitigation policy; temporal patterns", "Heavy training; limited interpretability; specialised infrastructure"],
             ["Retrieval + LLM", "No retraining; works on carpet bombing; natural-language explanations", "About two seconds per request; depends on an external model"],
             ["P4 / in-network detection", "Offloads the controller", "Needs programmable hardware"]],
            widths=[1.5, 2.5, 2.5], align=["l", "l", "l"], size=10),
        P("Across the families the strengths are accuracy on stored data and, in the better papers, an awareness of resource cost. The shared weaknesses are the dependence on one dataset at a time, the absence of a measured detection-to-action loop, "
          "and the absence of an account of what a false positive costs the user who is wrongly blocked."),
        H2("2.6 Research Gap"),
        P("The batch survey states the gap as: the surveyed work applies ensemble detection within software-defined networks, and the gap is closing the loop from real-time detection to automatic adaptive mitigation with measured response latency. "
          "Reading the sources above refines it into three parts:"),
        N(*lit.GAPS),
    ]
