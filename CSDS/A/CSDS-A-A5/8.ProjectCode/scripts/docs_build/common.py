"""Shared constants for the documentation build: identity, paths, figure registry, reference list."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # 8.ProjectCode
BATCH = os.path.dirname(ROOT)                                                            # batch folder
DIAG = os.path.join(ROOT, "docs", "diagrams")
CH = os.path.join(ROOT, "docs", "charts")
SS = os.path.join(ROOT, "docs", "screenshots")

PROJECT = "JEPA-LLM Tuning Framework for Combating GST and Sales Tax Input Tax Credit Fraud Pattern Detection"
PRODUCT = "TaxSentinel"
STUDENTS = [("B.ASHRITHA", "23K91A6732"), ("B.DIVYA", "23K91A6739"), ("A.KISHORE", "23K91A6716"), ("A.YAGNESH", "23K91A6711")]
GUIDE = "Dr. N. Ch. Ravi"
GUIDE_DESIG = "Professor in CSE (Data Science)"
COLLEGE = "TKR College of Engineering and Technology (Autonomous)"
DEPT = "Department of Computer Science and Engineering (Data Science)"
YEAR = "2026-27"


def D(n):
    return os.path.join(DIAG, n)


def C(n):
    return os.path.join(CH, n)


def S(n):
    return os.path.join(SS, n)


# ---- diagrams ----
ARCH, FLOW, DFD0, DFD1, DFD2 = D("01_system_architecture.png"), D("02_high_level_workflow.png"), D("03_dfd_level0.png"), D("04_dfd_level1.png"), D("05_dfd_level2.png")
UML, SEQ, UC, ER, ALGO = D("06_uml_class_diagram.png"), D("07_sequence_diagram.png"), D("08_use_case_diagram.png"), D("09_er_diagram.png"), D("10_core_algorithm_flowchart.png")

# ---- screenshots (name, caption) ----
SCREENS = {
    "landing": ("01_landing.png", "Landing page: product summary, live health card (API, pipeline and Gemini status) and the call to action."),
    "login": ("02_login.png", "Sign-in screen with the API, pipeline and Gemini status panel."),
    "login_demo": ("03_login_demo_filled.png", "Sign-in with the demo account filled in by the one-click helper."),
    "ov_before": ("04_overview_before_run.png", "Overview (control room) before a new generation: generate controls, activity log, headline counts and the monthly ITC pulse."),
    "ov_run": ("05_overview_generating.png", "Overview while a run is in progress: the stage stepper shows JEPA training at epoch 10 of 100 (25 %) and the activity log streams the pipeline messages."),
    "ov_done": ("06_overview_results.png", "Overview after the run completes (seed 42, 600 taxpayers): 64,474 invoices, 78 flagged taxpayers, ITC at risk of Rs 25.62 Cr of Rs 187.59 Cr claimed, and precision@79 of 95 % against 62 % for the rule baseline."),
    "ov_full": ("06b_overview_results_full.png", "Full-page overview: detection against the rule baseline, risk histogram, pattern counts, top-ranked taxpayers and top invoice chains."),
    "tp_list": ("07_taxpayers_ranking.png", "Taxpayer risk ranking with search, pattern, sector and flag filters and sort order; the top rows are circular-trading and shell-entity taxpayers."),
    "tp_sig": ("08_profile_signals.png", "Taxpayer profile, Signals tab (Lotus Manufacturing Pvt Ltd, rank 1, risk 0.97): the four risk layers, the rules triggered and monthly ITC available (GSTR-2B) against ITC claimed (GSTR-3B) with the JEPA deviation line."),
    "tp_ev": ("09_profile_evidence.png", "Taxpayer profile, Evidence tab: the numbered evidence list (E1 to E5) with layer, severity and concrete figures."),
    "tp_net": ("10_profile_network_ring.png", "Taxpayer profile, Network tab: the local trading network with the circular-trading loop in red and the main trading partners."),
    "tp_inv": ("11_profile_invoices.png", "Taxpayer profile, Invoices tab: anomalous invoices with value, tax, e-way bill, GSTR-1 reporting status and the signals that fired."),
    "tp_spike": ("12_profile_itc_spike.png", "Profile of an ITC-spike and shell-entity taxpayer (Ganga Wholesale): the monthly chart shows the claim far above the credit available in GSTR-2B."),
    "tp_shell": ("13_profile_shell_cluster.png", "Profile of a shell-cluster taxpayer (Pioneer Services): the shared-identity cluster S-card and the partners it trades with."),
    "graph": ("14_fraud_graph.png", "Fraud rings: the whole buyer-seller network with loop edges in red and shared-identity members ringed."),
    "rings": ("15_fraud_rings_list.png", "Fraud rings, full page: the nine trade loops and twelve identity clusters with their scores, and the ranked invoice chains."),
    "chain_c": ("16_chain_circular.png", "Invoice chain CH-R01: a five-party circular-trading loop of 98 invoices worth Rs 44.65 Cr passing Rs 9.78 Cr of ITC."),
    "chain_s": ("17_chain_shell.png", "Invoice chain CH-S37: a shell-supply chain of three linked registrations billing three buyers."),
    "case0": ("18_case_before_explanation.png", "Case page before a note is written: the evidence list is ready and the note is requested on demand."),
    "case1": ("19_case_explanation.png", "Case page with the Gemini case note: every claim ends in an [E#] citation chip that links to its evidence item."),
    "case_full": ("19b_case_explanation_full.png", "Full case page: the three-section note (Summary, Why it was flagged, Suggested next steps) beside the evidence list."),
    "perf": ("20_performance.png", "Model performance: precision@k, recall@k, F1, ROC-AUC and the JEPA training loss for the current ecosystem."),
    "perf_full": ("20b_performance_full.png", "Full model-performance page: taxpayer-level table with ablations, per-pattern recall, invoice-level and ring results."),
    "runs": ("21_run_history.png", "Run history: the last ten generations with status, seed, taxpayers, flagged count and duration, and the ecosystem currently loaded."),
    "dark": ("22_overview_dark.png", "Overview in dark mode (the theme follows the operating-system setting and can be toggled)."),
    "palette": ("23_command_palette.png", "Command palette (key /): search taxpayers or jump to a screen from the keyboard."),
}


def SCR(key, width=6.2, label=None):
    f, cap = SCREENS[key]
    return ("fig", label or f"s_{key}", S(f), cap, width)


# ---- IEEE references: base paper first, then the literature-survey sources, then the technical references ----
REFS = [
    "S. Datta, H. Thakkar and S. Dabhade, \"Combating GST input tax credit fraud in India: Forensic accounting, data analytics, and legal enforcement strategies,\" *Int. J. Manage., Public Policy Res.*, vol. 5, no. 1, pp. 37-46, Jan.-Mar. 2026, doi: 10.55829/ykz3ea41.",
    "\"The role of artificial intelligence and machine learning in enhancing tax compliance and fraud detection in India,\" *J. Informatics Educ. Res.*, 2025.",
    "\"Income tax fraud detection using machine learning,\" in *Proc. 8th Int. Conf. Trends Electron. Informatics (ICOEI)*, 2025.",
    "\"Income tax fraud detection system using AI and machine learning,\" in *Proc. Int. Conf. Comput. Commun. (COMPUTINGCON)*, 2025.",
    "\"Boosting-based machine learning for efficient income tax fraud detection,\" *Int. J. Res. Trends Innov.*, 2026.",
    "P. Mehta, S. Bhargava, M. R. Kumar, K. S. Kumar and C. S. Babu, \"Representation learning on graphs to identifying circular trading in Goods and Services Tax,\" arXiv:2208.07660, Aug. 2022.",
    "Y. Xu, B. Shi, B. Dong, J. Wang, H. Wei and Q. Zheng, \"TED: Related party transaction guided tax evasion detection on heterogeneous graph,\" arXiv:2605.26984, May 2026.",
    "M. Assran *et al.*, \"Self-supervised learning from images with a joint-embedding predictive architecture,\" in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2023, pp. 15619-15629.",
    "Y. LeCun, \"A path towards autonomous machine intelligence,\" version 0.9.2, OpenReview, Jun. 2022.",
    "A. Bardes *et al.*, \"Revisiting feature prediction for learning visual representations from video,\" arXiv:2404.08471, 2024.",
    "J.-B. Grill *et al.*, \"Bootstrap your own latent: A new approach to self-supervised learning,\" in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 33, 2020, pp. 21271-21284.",
    "A. Bardes, J. Ponce and Y. LeCun, \"VICReg: Variance-invariance-covariance regularization for self-supervised learning,\" in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2022.",
    "V. Chandola, A. Banerjee and V. Kumar, \"Anomaly detection: A survey,\" *ACM Comput. Surv.*, vol. 41, no. 3, pp. 1-58, 2009.",
    "F. T. Liu, K. M. Ting and Z.-H. Zhou, \"Isolation forest,\" in *Proc. IEEE Int. Conf. Data Mining (ICDM)*, 2008, pp. 413-422.",
    "V. D. Blondel, J.-L. Guillaume, R. Lambiotte and E. Lefebvre, \"Fast unfolding of communities in large networks,\" *J. Stat. Mech.*, vol. 2008, no. 10, P10008, 2008.",
    "A. A. Hagberg, D. A. Schult and P. J. Swart, \"Exploring network structure, dynamics, and function using NetworkX,\" in *Proc. 7th Python Sci. Conf. (SciPy)*, 2008, pp. 11-15.",
    "D. B. Johnson, \"Finding all the elementary circuits of a directed graph,\" *SIAM J. Comput.*, vol. 4, no. 1, pp. 77-84, 1975.",
    "A. Grover and J. Leskovec, \"node2vec: Scalable feature learning for networks,\" in *Proc. 22nd ACM SIGKDD Int. Conf. Knowl. Discovery Data Mining*, 2016, pp. 855-864.",
    "T. N. Kipf and M. Welling, \"Semi-supervised classification with graph convolutional networks,\" in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2017.",
    "A. Paszke *et al.*, \"PyTorch: An imperative style, high-performance deep learning library,\" in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 32, 2019, pp. 8024-8035.",
    "E. A. Lopez-Rojas, A. Elmir and S. Axelsson, \"PaySim: A financial mobile money simulator for fraud detection,\" in *Proc. 28th Eur. Model. Simul. Symp. (EMSS)*, 2016.",
    "J. Pearl, *Probabilistic Reasoning in Intelligent Systems: Networks of Plausible Inference*. San Mateo, CA, USA: Morgan Kaufmann, 1988.",
    "P. Lewis *et al.*, \"Retrieval-augmented generation for knowledge-intensive NLP tasks,\" in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 33, 2020, pp. 9459-9474.",
    "Z. Ji *et al.*, \"Survey of hallucination in natural language generation,\" *ACM Comput. Surv.*, vol. 55, no. 12, pp. 1-38, 2023.",
    "Gemini Team, Google, \"Gemini: A family of highly capable multimodal models,\" arXiv:2312.11805, 2023.",
    "I. Loshchilov and F. Hutter, \"Decoupled weight decay regularization,\" in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2019.",
    "M. Jones, J. Bradley and N. Sakimura, \"JSON Web Token (JWT),\" IETF RFC 7519, May 2015.",
    "N. Provos and D. Mazieres, \"A future-adaptable password scheme,\" in *Proc. USENIX Annu. Tech. Conf.*, 1999, pp. 81-91.",
    "D. R. Cressey, *Other People's Money: A Study in the Social Psychology of Embezzlement*. Glencoe, IL, USA: Free Press, 1953.",
    "J. L. Ba, J. R. Kiros and G. E. Hinton, \"Layer normalization,\" arXiv:1607.06450, 2016.",
    "D. Hendrycks and K. Gimpel, \"Gaussian error linear units (GELUs),\" arXiv:1606.08415, 2016.",
]

ABBREV = [
    ("API", "Application Programming Interface"), ("AP", "Average Precision"), ("AUC", "Area Under the Curve"), ("CBIC", "Central Board of Indirect Taxes and Customs"),
    ("CORS", "Cross-Origin Resource Sharing"), ("CSV", "Comma-Separated Values"), ("DFD", "Data Flow Diagram"), ("DGGI", "Directorate General of GST Intelligence"),
    ("EMA", "Exponential Moving Average"), ("ER", "Entity-Relationship"), ("GELU", "Gaussian Error Linear Unit"), ("GSP", "-"), ("GST", "Goods and Services Tax"),
    ("GSTIN", "GST Identification Number"), ("GSTR", "GST Return (GSTR-1 outward supplies, GSTR-2B auto-drafted ITC statement, GSTR-3B summary return)"),
    ("HS256", "HMAC using SHA-256"), ("ITC", "Input Tax Credit"), ("JEPA", "Joint Embedding Predictive Architecture"), ("JSON", "JavaScript Object Notation"),
    ("JWT", "JSON Web Token"), ("LLM", "Large Language Model"), ("MSE", "Mean Squared Error"), ("ORM", "Object-Relational Mapping"), ("P@k", "Precision at k"),
    ("R@k", "Recall at k"), ("REST", "Representational State Transfer"), ("ROC", "Receiver Operating Characteristic"), ("SPA", "Single-Page Application"),
    ("SQL", "Structured Query Language"), ("UML", "Unified Modeling Language"), ("UI", "User Interface"), ("UX", "User Experience"),
]
ABBREV = [a for a in ABBREV if a[0] != "GSP"]
