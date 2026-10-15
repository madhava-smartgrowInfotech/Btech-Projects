"""Report text, part A: chapters 1-3 (introduction, literature survey, feasibility)."""
from common import *

# ---------------------------------------------------------------- 1. INTRODUCTION
INTRO = {}

INTRO["domain"] = [
    ("h2", "1.1 Domain Overview"),
    ("p", "The Goods and Services Tax (GST), introduced in India on 1 July 2017, replaced a patchwork of central and state indirect taxes with a single destination-based consumption tax. Its central mechanism is the Input Tax Credit (ITC): a business that pays GST on its purchases may set that tax against the GST it collects on its sales, so that tax is finally levied only on the value added at each stage [1]. The mechanism removes the cascading \"tax on tax\" effect of the earlier regime, but it also turns the tax invoice into something that carries money. An invoice that never corresponded to a real supply can still hand a buyer a credit that reduces the tax it pays in cash."),
    ("p", "GST is self-assessed. Each taxpayer files outward supplies in GSTR-1, receives an auto-drafted statement of the credit available from its suppliers' filings in GSTR-2B, and claims credit and pays tax through the summary return GSTR-3B. The tax administration therefore works with three views of the same trade (what the seller declared, what the buyer may claim and what the buyer actually claimed) and with a very large population of taxpayers whose filings it can compare but rarely verify physically. The base paper of this project describes how this design, together with asymmetric information between taxpayer and administration, makes the system an attractive target for organised fraud [1]."),
    ("p", "Three patterns dominate the fraud described in the base paper and in the wider literature. In **fake invoicing**, a network of paper firms issues invoices without any movement of goods, and genuine businesses claim ITC on them. In **circular trading**, a small group of firms passes the same value around a loop (A to B to C and back to A) to inflate turnover and generate credit without value being added [6]. **Shell entities** are young registrations, often sharing an address or contact number, that trade mostly with each other, pay almost no tax in cash and stop filing once credit has been passed on. The Directorate General of GST Intelligence reported detected evasion rising from Rs 1.01 lakh crore in FY 2022-23 to Rs 2.01 lakh crore in FY 2023-24, with cases booked rising from 4,872 to 6,084 [1]."),
    ("p", "This project, **TaxSentinel**, is a data-science system for this domain. It learns what normal GST behaviour looks like from unlabelled filings with a Joint Embedding Predictive Architecture (JEPA), combines that signal with buyer-seller network analysis and invoice-level checks, ranks taxpayers and invoice chains by risk, and uses a large language model (Gemini) to write an investigator-style note in which every statement cites the evidence behind it."),
]

INTRO["background"] = [
    ("h2", "1.2 Background and Motivation"),
    ("p", "Tax authorities currently rely on a mixture of return scrutiny, rule-based mismatch reports (for example, credit claimed in GSTR-3B above credit available in GSTR-2B), field audits and investigations launched once a suspicious case surfaces. These tools are necessary, but each has a known weakness. Audits are slow and detect fraud after the revenue has been lost. Fixed rules are transparent and therefore easy to evade: a fraudster who knows that a 20 % mismatch triggers a notice can stay below it. Checks applied to one taxpayer or one invoice at a time cannot see a loop of five firms that each look ordinary in isolation."),
    ("p", "Supervised machine learning is the obvious answer, and several recent studies apply it to income-tax and related fraud [2]-[5]. Its difficulty here is the labels. Confirmed ITC-fraud cases are scarce, they are decided years after the filings concerned, and they reflect the cases investigators happened to pursue rather than the fraud that exists. A classifier trained on them learns the past enforcement pattern. Self-supervised learning offers a different starting point: learn the structure of ordinary behaviour from the abundant unlabelled returns and invoices, and treat sustained departures from it as signals to review. JEPA [8], [9] is attractive for this purpose because it predicts the *representation* of the missing part of an input instead of reconstructing raw values. Raw GST features such as invoice values and turnover are heavy-tailed and noisy, and a model that must reproduce them spends its capacity on noise."),
    ("p", "The last motivation is trust. A risk score without a reason is difficult for an officer to act on, and a score that cannot be defended cannot support a notice. The project therefore treats explanation as part of the detection pipeline: every flag is backed by a numbered evidence list computed from the data, and the language model is allowed to say only what that list supports."),
]

INTRO["problem"] = [
    ("h2", "1.3 Problem Statement"),
    ("p", "Input Tax Credit fraud through fake invoices, circular trading and shell companies causes large revenue losses. Manual audits and rule-based checks are slow and reactive, confirmed fraud labels are scarce, which limits supervised learning, and existing systems rarely explain why a claim is flagged. The problem addressed by this project is therefore to **design and build a self-supervised, explainable framework that learns normal GST behaviour from largely unlabelled data, ranks taxpayers and invoice chains by their deviation from it, and explains each flagged claim in natural language that an investigator can verify.**"),
]

INTRO["need"] = [
    ("h2", "1.4 Need for the Work"),
    ("bul", [
        "**Scale.** A tax administration cannot audit every taxpayer. A ranking that puts real fraud in the first few dozen cases changes where limited audit effort goes. On the project's evaluation ecosystem the top 50 taxpayers contain no false alarms ({tab:main}).",
        "**Network visibility.** Circular trading and shell clusters are properties of groups of taxpayers. They are invisible to checks that look at one return at a time, and need graph analysis over the buyer-seller network.",
        "**Label scarcity.** A method that learns from unlabelled behaviour does not depend on a sample of past fraud cases and does not inherit their bias.",
        "**Accountability.** Flags that cite their evidence can be challenged, corrected and used as the starting point of an audit file; opaque scores cannot.",
        "**Low cost.** The whole system trains in seconds on a CPU and runs on commodity hardware, which matters for adoption by state units without specialised infrastructure.",
    ]),
]

INTRO["objectives"] = [
    ("h2", "1.5 Objectives"),
    ("p", "The six objectives approved for the project, and the section of this report that measures each one, are listed below."),
    ("num", [
        "Build a multi-layer GST dataset covering invoices, taxpayer behaviour and transaction networks (Section 6.2).",
        "Learn normal GST behaviour with a self-supervised JEPA encoder (Sections 6.5 and 6.6).",
        "Detect fraud patterns such as fake invoices, circular trading and shell-entity activity (Sections 6.7, 8.2 and 8.5).",
        "Score and rank suspicious taxpayers and invoice chains by deviation from learned behaviour (Sections 6.7 and 8.2).",
        "Generate natural-language explanations for flagged claims using an LLM (Sections 6.8 and 8.3).",
        "Evaluate detection accuracy and explanation quality (Sections 8.2, 8.3 and 8.6).",
    ]),
    ("p", "One clarification applies to objective 5. The approved title speaks of a *tuned* LLM. The implemented system does not fine-tune any model's weights. It *tunes the prompt*: a fixed system prompt, a fixed three-section output format, a restriction to facts in the supplied evidence list and a mandatory citation per claim, followed by an automatic grounding check. This choice is explained in Section 6.8 and listed as a limitation in Section 1.8."),
]

INTRO["scope"] = [
    ("h2", "1.6 Scope"),
    ("p", "**In scope.** A reproducible generator of GST ecosystems with injected, labelled fraud; three feature layers per taxpayer-month; a JEPA behaviour encoder; circular-trading and shared-identity detection; invoice-level anomaly scoring; a combined risk score; ranked taxpayers and invoice chains; evidence lists; Gemini-written case notes with automatic grounding checks; evaluation against a rule baseline with ablations; and a secure multi-user web application (FastAPI and React) that presents all of this."),
    ("p", "**Out of scope.** Connection to the live GST Network or any real taxpayer data; legal determination of fraud (the output is a risk indication for review); e-way-bill and e-invoice (IRN) integration beyond the flag already present in the data; real-time streaming; fine-tuning of language models; mobile applications; and multi-tenant administration. The companion scope-and-limitations document and Chapter 9 of this report list these exclusions in more detail."),
]

INTRO["contrib"] = [
    ("h2", "1.7 Contributions"),
    ("num", [
        "**A three-layer, self-supervised behaviour model for GST.** A small JEPA (53,420 parameters) over 19 invoice, behaviour and network features per taxpayer-month, trained without labels in about 12 s on a CPU. It uses four mask variants: whole-month prediction from history, and prediction of each feature layer from the other layers, so that a deviation can be attributed to a layer.",
        "**A multi-signal risk model that does not rely on JEPA alone.** An explicit noisy-OR combination of JEPA deviation, return-behaviour deviation, network evidence (loops, shell clusters, exposure) and invoice anomalies. Ablations show why: JEPA plus behaviour alone reaches F1 0.327, graph plus invoice reaches 0.887 and all layers reach 0.955.",
        "**Network detectors tailored to ITC fraud.** A scored circular-trading detector (balance, recurrence, concentration) that recovered all 5 injected rings, and a shared-identity shell-cluster detector scored from deviation, youth, intra-cluster trade and stopped filing.",
        "**Cited, checkable explanations.** Case notes in which every claim cites an evidence ID and which are checked automatically for invalid citations, evidence coverage, high-severity coverage and numeric grounding (0 invalid citations over the 6 notes evaluated).",
        "**An evaluation harness with an honest baseline.** Precision@k, recall@k, F1, ROC-AUC, per-pattern recall, invoice-level metrics, ring recovery, a transfer check on PaySim and a rule baseline built from standard scrutiny rules R1-R5.",
        "**A working product.** A secured web application with ranking, taxpayer profiles, an interactive fraud graph, invoice-chain drill-down, on-demand case notes, a performance page and run history, tested end to end.",
    ]),
]

INTRO["limits"] = [
    ("h2", "1.8 Limitations and Assumptions"),
    ("bul", [
        "**The data is synthetic.** Real GST returns were not available. The generator injects fraud with known labels and also injects legitimate hard negatives (festival seasonality, one-off capital purchases, new registrations, group companies sharing an address, late filers). All accuracy figures are measured against these injected labels and describe the method on this generator; they are not an estimate of performance on real filings.",
        "**Weights and thresholds were set on this generator.** The risk weights (0.75, 0.6, 0.7, 0.6) and thresholds (0.5) were chosen on the seed-42 ecosystem. A five-seed study (Section 8.2) shows how stable they are across other generated ecosystems; a real deployment would need recalibration on real returns.",
        "**The LLM is prompted, not fine-tuned.** Explanation quality was evaluated on 6 of the 10 planned cases because the free Gemini quota was exhausted for the other four.",
        "**No unit-test suite.** Testing consists of a 20-check end-to-end smoke test, 41 black-box edge and security checks and the evaluation harness (Chapter 7). There is no coverage figure and no user-acceptance study.",
        "**Shell entities look normal to JEPA.** Twenty-seven similar firms form their own \"normal\"; JEPA-only recall of shell entities is low and the network layer is what finds them.",
        "**Assumption.** The six feature layers described in Chapter 6 are assumed to be derivable from a state's GSTR-1, GSTR-2B and GSTR-3B data and taxpayer registration data; this is plausible but was not verified against real data schemas.",
    ]),
]

INTRO["org"] = [
    ("h2", "1.9 Organisation of the Report"),
    ("p", "Chapter 2 reviews the base paper and related work. Chapter 3 assesses feasibility. Chapter 4 sets out the existing and proposed systems and the requirements. Chapter 5 presents the design: architecture, workflow, data-flow diagrams, UML diagrams, database and user interface. Chapter 6 describes the methodology and its implementation, including the mathematical formulation. Chapter 7 reports testing. Chapter 8 presents results and output screens. Chapter 9 concludes and Chapter 10 outlines future scope. The references follow, and three appendices give important code, the installation and user guide, and additional screens."),
]

# ---------------------------------------------------------------- 2. LITERATURE SURVEY
LIT = {}

LIT["overview"] = [
    ("h2", "2.1 Overview"),
    ("p", "The literature relevant to this project falls into five groups: (i) descriptive and policy studies of GST ITC fraud, including the base paper; (ii) machine-learning studies of tax fraud; (iii) graph methods for circular trading and tax evasion; (iv) self-supervised predictive architectures; and (v) methods for explaining model outputs in natural language with controlled hallucination. The batch's literature survey lists five tax-fraud papers (the base paper and four others). The full texts of the four others were not part of the batch's archived documents and could not be retrieved, so they are discussed only at the level that their titles and venues support, and no results are quoted from them. The base paper [1] and the two graph papers [6], [7] were read in full."),
]

LIT["base"] = [
    ("h2", "2.2 Base Paper Analysis"),
    ("p", "The base paper is S. Datta, H. Thakkar and S. Dabhade, \"Combating GST Input Tax Credit Fraud in India: Forensic Accounting, Data Analytics, and Legal Enforcement Strategies,\" *International Journal of Management, Public Policy and Research*, vol. 5, issue 1, January-March 2026 [1]."),
    ("p", "**What it does.** It is a qualitative, evidence-synthesis paper. It explains why the self-assessed ITC design creates room for fraud, using asymmetric information, moral hazard and the Fraud Triangle of pressure, opportunity and rationalisation [29]. It describes how fraud is executed through fake invoices, circular trading and networks of shell companies, and it quantifies the problem using published government figures. Using data attributed to the Directorate General of GST Intelligence (DGGI) and the Central Board of Indirect Taxes and Customs (CBIC), it reports that detected evasion rose from Rs 1.01 lakh crore in FY 2022-23 to Rs 2.01 lakh crore in FY 2023-24, that cases booked rose from 4,872 to 6,084, that arrests rose from 97 to 140 and that voluntary payments rose from Rs 20,713 crore to Rs 26,605 crore. It also reports the special drives against fake registrations (21,791 fake GSTINs and Rs 24,010 crore of evasion detected in May-July 2023, and about 10,700 fake GSTINs and Rs 10,179 crore in August-October 2024, partial data)."),
    ("p", "**What it recommends.** It concludes that compliance-focused responses must give way to forensic, technology-enabled ones, and recommends a unified economic intelligence grid shared between agencies, dynamic AI-based risk modelling at GST registration, continuous capacity building of officers in forensic accounting and data analysis, faster prosecution and recovery, and forensic due diligence by businesses in vendor selection."),
    ("p", "**What it does not do.** By its own account the study relies on public government and media sources, is qualitative, contains no primary empirical data and does not implement or evaluate any detection model. It lists quantitative, AI-supported fraud detection as future work."),
    ("p", "**What this project adopts.** The three fraud patterns, the central role of fake registrations and invoicing, the call for data analytics and network analysis, and the recommendation of AI-based risk modelling are taken from the base paper and become this project's detection targets. What the paper leaves open (a concrete, evaluable model; learning from unlabelled data; machine-readable evidence; explanation) is what the project builds. Because the base paper reports no model metrics, a like-for-like numerical comparison with it is not possible; Section 8.6 compares the system with the paper's recommendations and with a rule-based baseline instead."),
]

LIT["related"] = [
    ("h2", "2.3 Related Work"),
    ("h3", "A. Machine learning for tax-fraud detection"),
    ("p", "Four further papers in the batch survey apply AI and machine learning to tax compliance and fraud detection in India: an overview of the role of AI and ML in tax compliance and fraud detection [2], two conference papers on income-tax fraud detection using machine learning and AI [3], [4], and a study of boosting-based learning for income-tax fraud [5]. Judging by their titles and venues, they use supervised classifiers on labelled taxpayer records (the boosting paper explicitly so). They share the strength of showing that tabular taxpayer data carries a learnable fraud signal. They also share the limitation that motivates this project: they need labelled fraud, they score taxpayers or returns individually and they offer no account of how taxpayers are connected. Neither GST invoice networks nor explanation is addressed in their titles."),
    ("h3", "B. Graph methods for circular trading and tax evasion"),
    ("p", "Mehta et al. [6] study circular trading in GST on real data from the Department of Commercial Taxes, Government of Telangana: 77,837,538 invoices among 388,448 taxpayers. They build a sales-flow graph, learn node embeddings with node2vec [18] and cluster them with DBSCAN to find communities of circular traders, then isolate illegitimate transactions within them. The work shows that graph representation learning scales to a state's data. It reports communities found rather than accuracy against labels, targets one pattern, and produces no explanation. Xu et al. [7] model the tax scenario as a heterogeneous graph with more than ten node and relation types and propose TED, a graph neural network that uses related-party transaction groups and hierarchical attention. On two real tax datasets it reports F1 scores between 76.35 % and 94.96 % depending on the dataset and the share of positive samples in the training set, and F1 up to 8.50 % higher than the best earlier method. TED is supervised and needs labels for training; it is a classifier, not an explainer. Graph convolutional networks [19] underlie much of this line of work."),
    ("h3", "C. Self-supervised predictive architectures"),
    ("p", "LeCun's proposal for joint-embedding predictive architectures [9] argues that prediction should be made in a learned representation space so that unpredictable detail can be ignored. I-JEPA [8] realised this for images by predicting the embeddings of masked blocks from a visible context block, with a target encoder updated as an exponential moving average, an idea inherited from BYOL [11]. V-JEPA [10] extended it to video. A variance term, as in VICReg [12], keeps representations from collapsing. These works are on images and video; this project transfers the same recipe to the very different setting of monthly tax behaviour vectors, where masking a whole month tests predictability from history and masking a feature layer tests consistency across layers."),
    ("h3", "D. Anomaly detection and network structure"),
    ("p", "Chandola et al. [13] survey anomaly detection; isolation forests [14] are the usual tabular baseline. Such methods score each record independently of its network. For graph structure, short directed cycles can be enumerated with Johnson-style algorithms [17] (the implementation in NetworkX [16] supports a length bound), and Louvain modularity optimisation [15] finds trade communities. The project uses these building blocks and adds fraud-specific scoring of loops (balance, recurrence and concentration)."),
    ("h3", "E. Grounded explanation with large language models"),
    ("p", "Large language models write fluent text but can state unsupported facts [24]. Retrieval-augmented generation [23] reduces this by supplying source passages. TaxSentinel follows the same principle in a stricter form: the model receives only a numbered list of computed evidence items, must cite one per claim, and the output is checked automatically for invalid citations and for numbers absent from the evidence. The model used is Gemini [25]."),
]

LIT["tables"] = [
    ("h2", "2.4 Datasets and Algorithms Used in the Literature"),
    ("tbl", "lit", "Summary of the surveyed works", ["Work", "Approach", "Data", "Reported result", "Limitation for this problem"], [
        ["Datta et al. [1] (base paper)", "Forensic accounting, data analytics and legal strategy review", "DGGI and CBIC statistics, case studies", "Detected evasion Rs 1.01 lakh crore (FY23) to Rs 2.01 lakh crore (FY24)", "Qualitative; no model or metrics"],
        ["[2]", "AI/ML in tax compliance (overview, per title)", "Not available to the team", "Not quoted", "Full text unavailable; no GST network or explanation in title"],
        ["[3], [4]", "ML / AI for income-tax fraud (per title)", "Not available to the team", "Not quoted", "Supervised on labelled records (per title); no network; income tax, not GST ITC"],
        ["[5]", "Boosting-based learning for income-tax fraud (per title)", "Not available to the team", "Not quoted", "Supervised; per-taxpayer scoring"],
        ["Mehta et al. [6]", "node2vec + DBSCAN communities of circular traders", "Telangana GST: 77.8 M invoices, 388 k taxpayers", "Communities of circular traders identified; no accuracy metric", "Circular trading only; no labels, no explanation"],
        ["Xu et al. [7] (TED)", "Heterogeneous graph neural network with related-party groups", "Two real tax datasets (T20H, T15S)", "F1 76.35-94.96 %; up to +8.50 % F1 over best baseline", "Supervised; needs labels; no explanation"],
        ["Assran et al. [8]", "I-JEPA: predict masked-block embeddings", "Images (ImageNet)", "Strong linear-probe transfer", "Not applied to tax or tabular behaviour"],
    ], [1.15, 1.55, 1.3, 1.45, 1.55]),
]

LIT["gap"] = [
    ("h2", "2.5 Strengths and Limitations of the Existing Work"),
    ("p", "**Strengths.** The base paper gives an authoritative, numerate picture of the problem and a convincing argument for technology-enabled forensics. The machine-learning studies show that fraud is learnable from taxpayer data. Mehta et al. show that graph methods work at state scale on real GST data and TED shows that heterogeneous graphs improve supervised detection. The JEPA line of work gives a mature recipe for learning without labels."),
    ("p", "**Limitations.** The policy paper offers no model. The supervised studies need labelled fraud, which is scarce, and score entities in isolation. The graph studies look at one pattern or need labels, and none of the surveyed GST work explains its output in language an officer can check."),
    ("h2", "2.6 Research Gap"),
    ("p", "Existing GST fraud work is largely descriptive or rule-based. Few systems (i) learn behavioural patterns from unlabelled tax data, (ii) combine invoice, return-behaviour and network evidence in one score, (iii) recover circular trading and shell networks without labels and (iv) explain every flag with cited evidence. This project addresses that combination. Its claims are limited by the data it was evaluated on (Section 1.8), and it does not claim to outperform supervised graph methods such as TED on real data, which it was not compared against."),
]

# ---------------------------------------------------------------- 3. FEASIBILITY
FEAS = {}

FEAS["all"] = [
    ("h2", "3.1 Technical Feasibility"),
    ("p", "Every component of the system is available as mature open-source software: PyTorch [20] for the JEPA, NumPy for the features, NetworkX [16] for graph analysis, FastAPI and SQLAlchemy with SQLite for the service, React and Vite for the interface and the Gemini API [25] for explanations. Feasibility was demonstrated rather than assumed: the complete system was built and run. On a mid-range desktop without a GPU (an Intel Core i5-12500 with 15.7 GB of RAM), generating an ecosystem of 600 taxpayers and 64,474 invoices, training the JEPA and running the full analysis takes about 19 to 29 s end to end in the application's run history, with the JEPA training alone taking 11.7 s. The risks that were real were the scarcity of real data (met by a synthetic generator with hard negatives, Chapter 6) and the availability of the LLM service (met by model fallbacks, retries and on-demand generation of notes)."),
    ("h2", "3.2 Economic Feasibility"),
    ("p", "All software is free and open source and the project needed no licence purchases. The only external service is Gemini; the free tier was sufficient to develop the system and to generate and check notes, but it ran out of quota for 4 of the 10 planned notes during evaluation, so a deployment that produces notes at volume would need a paid tier or a locally hosted model. Compute needs are minimal: training and scoring run on a CPU in seconds, so no GPU server is required. The expected benefit is the reallocation of scarce audit effort towards the cases most likely to be real fraud; the system's value in rupees was not measured and no saving is claimed. On the synthetic ecosystem, the Rs 25.62 Cr of ITC attached to flagged taxpayers is a measure of what the ranking puts in front of an investigator, not of recovery."),
    ("h2", "3.3 Operational Feasibility"),
    ("p", "The intended users are analysts and investigators in a tax-administration analytics unit, forensic accountants and compliance teams. The interface follows the workflow they already have (rank, open a case, read the evidence, decide), uses plain language, offers keyboard shortcuts and a command palette, and keeps every number traceable to evidence. Set-up on Windows needs two double-clicks (setup.bat and run.bat) and ports 8105 and 5105. Operation depends on the quality of the input returns; the system gives a prioritisation, not a decision, and the notes say so."),
    ("h2", "3.4 Schedule Feasibility"),
    ("p", "The work followed a short, staged schedule recorded in the project's version-control history and batch documents ({tab:sched}). The schedule was feasible because the model is small and the stack is familiar; the main schedule risk was the evaluation of explanations, which depended on external quota."),
    ("tbl", "sched", "Project schedule as recorded in the repository and batch documents", ["Date", "Milestone"], [
        ["06 Jul 2026", "Phase-I project abstract submitted (Major Project Phase-I, A.Y. 2026-27)"],
        ["19 Sep 2026", "Batch details, abstract, base paper, introduction, literature survey, objectives and problem statement finalised"],
        ["21 Sep 2026", "Project folder initialised; master prompts prepared"],
        ["28 Sep 2026", "Backend pipeline and API; evaluation, documentation and README; frontend screens and run script; Gemini models and explanation evaluation"],
        ["14 Oct 2026", "Frontend redesigned (control-room interface with dark mode, activity log, command palette)"],
        ["15 Oct 2026", "Screenshots, diagrams, edge and security tests, cross-seed study and this documentation set produced"],
    ], [1.3, 5.7]),
    ("h2", "3.5 Advantages and Constraints"),
    ("p", "**Advantages.** The method needs no labelled fraud; it uses three kinds of evidence and so is robust to a fraudster changing one behaviour; it recovers rings and clusters, not just single entities; it is explainable; it is small, fast and cheap; and the whole pipeline is reproducible from a seed. **Constraints.** The data is synthetic, thresholds need recalibration on real returns, notes depend on an external service, and the system supports prioritisation, not legal findings."),
]
