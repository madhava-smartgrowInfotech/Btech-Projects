"""Literature and framing data for the decks (Review 1, Review 2, final), the chapters and the IEEE paper.

Every literature fact traces to the base-paper PDF (Documentary/), the archived PDFs in this batch (Swileh 2026, Rahman 2025), the Crossref
abstract of Raghavendran and Robinson, or the entry notes in refs.py (REF_NOTES).  The batch-survey items [2], [4], [5] have verified
bibliographic records but no abstract could be read, so they are never quoted for results.  Reference numbers match refs.py (CITE keys).
Items quoted from the base paper's own related-work section are marked "(as reported in the base paper)".
"""
from . import facts as F
from .refs import CITE as R

BASE_PAPER_TITLE = "Resource-Aware Ensemble Framework for DDoS Detection in SDN via Novel Game-Theoretic Feature Selection"
BASE_PAPER_VENUE = "M. M. Trigui, M. S. Islam, M. D. Gambo, M. S. Alam, T. Helmy - IEEE Access, vol. 14, 2026"

# [work, year, approach, finding / limitation]   (each cell <= 90 characters)
LIT_TABLE = [
    [f"Trigui et al. [{R['base']}] (base paper)", "2026", "RF + Banzhaf feature selection; seven classifiers; four hard-voting ensembles; SDN",
     "100 % on SDN flows and CIC-DDoS2023; SVM/kNN ensembles slow; no live mitigation"],
    [f"Swileh et al. [{R['carpet']}]", "2026", "Carpet-bombing DDoS in SDN: RAG + FAISS + LLM, no supervised training; Mininet + Ryu",
     "Accuracy 99.94 % (Gemma-4-31B-IT), about 2 s per request; needs an LLM service"],
    [f"Raghavendran, Robinson [{R['s_wisne']}]", "2026", "WISNE-SDN IoT controller; KNN, XGBoost, Naive Bayes on a testbed dataset",
     "97 % (KNN), 100 % (XGB) from the abstract; testbed data, detection only"],
    [f"Jadric, Mladenovic [{R['s_ddqn']}]", "2025", "Double deep Q-networks for DDoS detection and mitigation (title only)",
     "Batch survey item; abstract not available, results not quoted"],
    [f"Alashhab et al. [{R['alashhab']}]", "2024", "Ensemble online machine learning for DDoS detection and mitigation in SDN",
     "Cited by the base paper; record verified, results not quoted"],
    [f"Rahman [{R['rahman']}]", "2025", "Logistic regression, decision tree, SVM on a CIC dataset sample",
     "SVM 0.971, decision tree 0.827, logistic regression 0.593; detection only"],
    [f"Zaman et al. [{R['zaman']}]", "2025", "Decision-tree algorithms for DDoS detection in SDN",
     "Cited by the base paper; record verified, results not quoted"],
    [f"Alduailij et al. [{R['alduailij']}]", "2022", "Mutual information + RF feature importance; ensemble voting",
     "99 % on CICIDS2017 and CIC-DDoS2019 (as reported in the base paper)"],
    [f"Becerra-Suarez et al. [{R['becerra']}]", "2024", "Tree learners and deep networks with data processing",
     "99.97 % accuracy, 99.98 % F1 (as reported in the base paper)"],
    [f"Areef, Vijayasri [{R['s_ijesat']}]", "2026", "DDoS detection and mitigation (title only)", "Batch survey item; abstract not available, results not quoted"],
    [f"IJARCCE item [{R['s_ijarcce']}]", "2025", "AI-driven DDoS detection and mitigation in SDN (title only)", "Batch survey item; abstract not available, results not quoted"],
    [f"Engelen et al. [{R['engelen']}]", "2021", "Audit of CICIDS2017: labelling and flow-construction problems",
     "Warns that CICIDS2017 results need care; relevant to every claim made on this dataset"],
]

# [work, approach, data, reported result, limitation]  - short cells for the IEEE paper's TABLE I
PAPER_TABLE = [
    [f"Base paper [{R['base']}]", "RF-BPI selection, 4 voting ensembles", "SDN flows 104,345; CIC-DDoS2023 1.75 M rows", "100 % acc./F1 on both", "SVM/kNN costly; no mitigation"],
    [f"Swileh et al. [{R['carpet']}]", "RAG + FAISS + LLM, carpet bombing", "Mininet/Ryu, hping3 traffic", "99.94 % acc., ~2 s/request", "Needs an LLM service"],
    [f"Raghavendran, Robinson [{R['s_wisne']}]", "KNN, XGBoost, Naive Bayes", "WISNE-SDN testbed", "97 % (KNN), 100 % (XGB)", "Testbed data; detection only"],
    [f"Rahman [{R['rahman']}]", "LR, decision tree, SVM", "CIC dataset sample", "SVM 97.1 %, DT 82.7 %, LR 59.3 %", "Detection only"],
    [f"Alduailij et al. [{R['alduailij']}]", "MI + RF importance, voting", "CICIDS2017, CIC-DDoS2019", "99 % (via base paper)", "Older datasets"],
    [f"Becerra-Suarez et al. [{R['becerra']}]", "Trees + deep nets", "Public DDoS datasets", "99.97 % acc. (via base paper)", "No resource profile"],
    [f"Engelen et al. [{R['engelen']}]", "Dataset audit", "CICIDS2017", "Labelling flaws found", "Dataset study, no detector"],
]

# the six objectives of the batch (6.OBJECTIVES&PROBLEM STATEMENT.docx), shortened for status tables
OBJECTIVES = [
    "Acquire a benchmark intrusion dataset and extract network flow features",
    "Capture live traffic and compute the same features in real time",
    "Train a classifier to distinguish DDoS traffic from legitimate traffic",
    "Implement adaptive mitigation that rate-limits or blocks identified attack sources",
    "Build a dashboard showing live traffic, detection events and mitigation actions",
    "Evaluate detection accuracy, false positive rate and time from detection to mitigation",
]

PROBLEM_STATEMENT = [
    "Signature-based defences cannot detect novel or modified attack patterns.",
    "Detection without mitigation leaves the service unavailable while the attack continues.",
    "Blocking legitimate users through false positives is itself a denial of service.",
    "Attack traffic must be classified fast enough to act before resources are exhausted.",
]
NEED = "A framework that detects DDoS traffic in real time and applies adaptive mitigation without blocking legitimate users."

# research gaps, stated from the batch survey and from what the sources above report
GAPS = [
    "The surveyed work applies ensemble detection within software-defined networks; closing the loop from real-time detection to automatic, adaptive mitigation with measured response latency is the gap named in the batch survey.",
    "Reported accuracies of 99-100 % come from offline evaluations on one dataset at a time; few works run a live (or live-like) capture-to-action loop on a commodity host.",
    "False-positive cost is rarely measured at the level where it hurts (a legitimate source quarantined), and carpet-bombing traffic that spreads across many destinations is seldom scored with a distributed-traffic signal.",
]
