"""Held-out probe set for the reviewer-matching evaluation (scripts/measure_metrics.py).

40 short paper abstracts written by the project team for this evaluation. Each carries the reviewer(s) whose
demo profile (app/services/seed.py) is the correct assignment. The labels are the authors' own judgement, not
independent expert judgement, and the abstracts deliberately avoid copying the reviewers' keyword lists.
Expected reviewer names are the seeded demo identities.
"""

A, B, G, D, E, Z = ("Reviewer Alpha", "Reviewer Beta", "Reviewer Gamma", "Reviewer Delta", "Reviewer Epsilon", "Reviewer Zeta")

PROBE = [
    # ---- vision (Alpha)
    ("Lightweight detector for small objects in aerial imagery",
     "We design a convolutional backbone with a feature pyramid that detects small vehicles in satellite photographs. On a public aerial benchmark the detector improves mean average precision over a standard anchor-based baseline while using fewer parameters.", [A]),
    ("Label-efficient image classification with contrastive pretraining",
     "Training a classifier on only ten percent of the labelled photographs, we pretrain a convolutional network with a contrastive objective and fine-tune it. Top-1 accuracy on the benchmark approaches the fully supervised result.", [A]),
    ("Pixel-accurate segmentation of street scenes",
     "An encoder-decoder network with skip connections produces dense masks for roads, pedestrians and vehicles in driving footage. We report intersection-over-union per class and analyse failures at night.", [A]),
    ("Data augmentation policies for visual recognition",
     "We search over cropping, colour and blur transformations applied to training photographs and show that a learned policy raises recognition accuracy on three image datasets without extra labels.", [A]),
    ("Robustness of image recognisers to weather corruption",
     "Fog, rain and snow filters are applied to benchmark photographs to measure how convolutional recognisers degrade. Adversarial fine-tuning recovers part of the lost accuracy.", [A]),
    ("Detecting surface defects on printed circuit boards",
     "A camera inspection line feeds board images to a deep detector that localises scratches and missing solder. The system reaches high recall with a controlled false alarm rate on a factory dataset.", [A]),
    # ---- language (Beta)
    ("Retrieval-grounded answer generation for customer questions",
     "A dense retriever fetches support articles that condition a language model when answering questions, reducing unsupported statements. Human raters judge faithfulness on a sample of replies.", [B]),
    ("Fine-tuning a transformer for legal clause classification",
     "We adapt a pretrained transformer encoder to label contract clauses into twelve categories and compare it with bag-of-words baselines using macro F1 on a corpus of agreements.", [B]),
    ("Abstractive summarisation of news with factual consistency checks",
     "A sequence-to-sequence model summarises articles and a verification step flags sentences that contradict the source. Evaluation combines ROUGE scores with human judgements of consistency.", [B]),
    ("Cross-lingual sentiment transfer with multilingual encoders",
     "Reviews in a high-resource language train a sentiment classifier that is applied zero-shot to four other languages through a shared multilingual representation.", [B]),
    ("Evaluating machine translation with learned metrics",
     "We study how neural translation metrics correlate with human ratings across language pairs and propose a calibration step that improves agreement for low-resource languages.", [B]),
    ("Instruction tuning of small language models",
     "Smaller decoder models are tuned on curated instruction data and compared with larger models on question answering, showing that data quality matters more than quantity.", [B]),
    # ---- applied ML / statistics (Gamma)
    ("Gradient-boosted trees versus linear models on tabular benchmarks",
     "We benchmark boosted tree ensembles against linear models on twenty tabular datasets with repeated cross-validation and report paired statistical tests of the differences.", [G]),
    ("A checklist for reproducible machine learning experiments",
     "We audit forty published papers for missing seeds, data splits and hyperparameters and propose a short checklist that lets a third party repeat the reported numbers.", [G]),
    ("Experimental design for comparing classifiers under small samples",
     "Using bootstrap and permutation tests, we show that many reported accuracy gains are within noise and give recommendations for the number of repeats needed.", [G]),
    ("Hyperparameter search budgets and reported performance",
     "We measure how the amount of tuning given to baselines changes conclusions drawn in comparisons and argue that equal budgets should be reported.", [G]),
    ("Feature engineering for customer churn prediction",
     "Aggregated usage features and a boosted classifier predict subscription cancellation. Calibration curves and a cost-based threshold analysis support deployment decisions.", [G]),
    ("Detecting leakage in machine-learning pipelines",
     "We catalogue ways in which test information reaches training in common workflows and provide an automatic checker evaluated on public notebooks.", [G]),
    # ---- security / systems (Delta)
    ("Anomaly detection in enterprise network flows",
     "Flow records from a campus network are modelled with an isolation-based detector and a graph of host communications to surface unusual behaviour. Analysts triage the alerts and we measure precision.", [D]),
    ("Large-scale measurement of exposed services on the internet",
     "We scan address blocks over six months and measure how long vulnerable services stay reachable, analysing patch delays across hosting providers.", [D]),
    ("Graph mining of botnet command infrastructure",
     "Domain and address relationships are connected in a bipartite graph whose communities reveal command-and-control clusters, validated against threat intelligence feeds.", [D]),
    ("Adversarial evasion of malware classifiers",
     "We craft binaries that evade a learned detector and evaluate hardening strategies, reporting detection rates before and after adversarial training.", [D]),
    ("Latency and throughput of encrypted traffic inspection",
     "A distributed inspection cluster is benchmarked for packet throughput and added delay under increasing load, identifying scheduling overheads.", [D]),
    ("Audit logging for tamper-evident storage",
     "A hash-chained log protects records against silent modification and we measure its overhead in a cloud storage service with a threat model for insiders.", [D]),
    # ---- medical (Epsilon)
    ("Bayesian prediction of sepsis from vital signs",
     "A hierarchical Bayesian model estimates the probability of sepsis from irregular vital-sign series and reports calibrated uncertainty on a retrospective cohort of intensive-care patients.", [E]),
    ("Clinical validation protocol for diagnostic prediction models",
     "We propose a staged evaluation framework covering retrospective validation, silent deployment and prospective study before a prediction model informs patient care.", [E]),
    ("Fairness assessment of risk scores across patient groups",
     "Using electronic health records we examine calibration and error rates of a mortality score across age and sex groups and suggest monitoring thresholds.", [E]),
    ("Survival analysis of cancer patients with missing covariates",
     "Multiple imputation combined with a Bayesian proportional hazards model handles incomplete laboratory data in an oncology registry.", [E]),
    ("Responsible deployment of medical imaging assistants",
     "We review regulatory and ethical requirements for assistive diagnostic software and describe an assessment checklist used in a hospital pilot.", [E]),
    ("Adaptive clinical trial design with Bayesian decision rules",
     "Interim analyses update the allocation probabilities in a trial of a new therapy, and simulation shows power and error rates for several stopping rules.", [E]),
    # ---- robotics (Zeta)
    ("Visual-inertial perception for a mobile robot in warehouses",
     "A mobile platform fuses camera and inertial data to localise among shelves, and we evaluate drift over long routes against a motion-capture reference.", [Z]),
    ("Trajectory optimisation for a quadruped on rough terrain",
     "A model-based planner optimises footholds and body motion in real time and is compared with a learned controller on uneven ground.", [Z]),
    ("Reinforcement learning for robotic grasping with sim-to-real transfer",
     "A policy trained in simulation with randomised physics is transferred to a robot arm and we report grasp success rates on unseen objects.", [Z]),
    ("Software architecture for autonomous inspection drones",
     "We describe the modular software stack of an inspection drone, its safety monitors and the field tests carried out on industrial sites.", [Z]),
    ("Obstacle avoidance with depth sensing for autonomous vehicles",
     "Depth maps from a stereo sensor drive a reactive controller that avoids dynamic obstacles, with collision statistics from a test track.", [Z]),
    ("Multi-robot path planning under communication limits",
     "A decentralised planner coordinates a team of robots exploring a building when radio links drop, evaluated in simulation and on three physical units.", [Z]),
    # ---- cross-area (two acceptable reviewers)
    ("Deep learning for chest radiograph triage",
     "A convolutional network flags abnormal chest radiographs for urgent reading and we assess calibration and subgroup errors on hospital data before deployment.", [A, E]),
    ("Language models for clinical note de-identification",
     "A transformer tags personal identifiers in physician notes and we validate recall against manual review under a clinical evaluation protocol.", [B, E]),
    ("Learning-based intrusion detection from textual logs",
     "System log lines are embedded with a language model and a classifier flags suspicious sessions, evaluated on a public intrusion dataset.", [B, D]),
    ("Statistical evaluation of robot perception benchmarks",
     "We re-analyse published perception benchmarks with confidence intervals and paired tests and show that several claimed improvements are not significant.", [G, Z]),
]

# Conflict-of-interest probes: (reviewer name, conflict kind, sentence injected into the paper text)
CONFLICT_INJECT = [
    ("Reviewer Alpha", "conflict term", "Part of this work was done with the northbridge-internal-xyz group."),
    ("Reviewer Beta", "conflict term", "We thank the harborview-internal-xyz team for data access."),
    ("Reviewer Gamma", "conflict term", "Funding came from civic-internal-xyz."),
    ("Reviewer Delta", "conflict term", "Infrastructure was provided by westfield-internal-xyz."),
    ("Reviewer Zeta", "conflict term", "Hardware support: robotics-internal-xyz."),
    ("Reviewer Epsilon", "conflict term", "Clinical partner lakeside-internal-xyz."),
    ("Reviewer Alpha", "affiliation", "Author affiliation: Northbridge Institute of Computing."),
    ("Reviewer Beta", "affiliation", "Author affiliation: Harborview Language Lab."),
    ("Reviewer Delta", "affiliation", "Author affiliation: Westfield Security Lab."),
    ("Reviewer Zeta", "affiliation", "Author affiliation: Open Robotics Collective."),
    ("Reviewer Beta", "full name", "We are grateful to Reviewer Beta for early feedback."),
    ("Reviewer Gamma", "full name", "Discussions with Reviewer Gamma shaped the study."),
    # paraphrased relations the string matcher cannot see (expected misses)
    ("Reviewer Alpha", "paraphrased affiliation", "Author affiliation: the Computing Institute at Northbridge."),
    ("Reviewer Delta", "paraphrased affiliation", "Author affiliation: the Security Lab of Westfield."),
    ("Reviewer Beta", "first name only", "Thanks to Beta for the review."),
]
