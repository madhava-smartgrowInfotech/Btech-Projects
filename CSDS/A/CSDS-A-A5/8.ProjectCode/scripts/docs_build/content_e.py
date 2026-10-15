"""Report text, part E: chapter 10 (future scope) and the scope-and-limitations document."""
from common import *

FUT = {}
FUT["all"] = [
    ("h2", "10.1 Improvements to the Method"),
    ("bul", [
        "**Head-to-head baselines.** Train an isolation forest [14] and an autoencoder on the same 19 features and compare them with the JEPA, so that the choice of JEPA is supported by measurement and not only by design argument.",
        "**Calibration on real returns.** Replace the hand-set weights (0.75, 0.6, 0.7, 0.6) and thresholds with values fitted on a small set of confirmed cases, or learn the combination with a few labels (semi-supervised), while keeping the self-supervised encoder label-free. The cross-seed study in Chapter 8 shows that the present weights are not stable across generated ecosystems, which makes this the most important method improvement.",
        "**Longer and richer temporal context.** Extend the three-month window, add seasonality features and treat sector-specific norms explicitly, so that legitimate seasonal swings are less likely to look like deviations.",
        "**Learned graph representations.** Add node embeddings [18], [19] or a graph-level JEPA to complement the explicit loop and cluster detectors, keeping the explicit loop as the citable evidence.",
        "**Robustness to adaptive fraud.** Test the system against fraud that has been generated to avoid its signals (for example loops with unbalanced edge values or irregular months) and strengthen the detectors accordingly.",
    ]),
    ("h2", "10.2 Additional Features"),
    ("bul", [
        "**Role-based access.** Add reviewer and administrator roles, user management and a configurable threshold page.",
        "**Case management.** Let analysts assign, annotate and close cases and feed their decisions back as labels; export a case file (evidence and note) as a PDF.",
        "**More data sources.** Incorporate e-invoice (IRN) and e-way-bill records, annual returns (GSTR-9 and 9C), bank and payment data and registration verification history, which the base paper identifies as parts of a unified intelligence grid [1].",
        "**Language support.** Generate notes in regional languages used by state tax units.",
        "**Reports and alerts.** Scheduled reports and notifications for newly flagged taxpayers or rings.",
    ]),
    ("h2", "10.3 Scalability and Deployment"),
    ("bul", [
        "**Storage.** Move the analytical data from CSV and a pickle to a columnar store or PostgreSQL, and the application tables from SQLite to a server database.",
        "**State scale.** Real state data is several orders of magnitude larger: Mehta et al. [6] work with 77.8 million invoices and 388,448 taxpayers. The present in-memory design and the full cycle search would need sparse graph structures, partitioning by region or sector, incremental updates each filing cycle and bounded cycle enumeration with sampling.",
        "**Operations.** Package with containers, add HTTPS, rate limiting, account lockout, audit logging and monitoring, and move the generation to a job queue with workers.",
        "**LLM hosting.** Use a paid or self-hosted model for volume and data-residency reasons; the grounding checks and the evidence-only prompt are model-independent.",
    ]),
    ("h2", "10.4 Further Research"),
    ("bul", [
        "Fine-tune a model on real investigator notes with human feedback, and compare it with the prompted approach on the same grounding metrics.",
        "Run a human evaluation of explanations (clarity, usefulness, effort saved) in addition to the automatic checks.",
        "Validate the whole framework on real, anonymised returns with the co-operation of a tax administration, and report results with confidence intervals across several periods.",
        "Study fairness and error costs: which honest taxpayers are most likely to be flagged (for example new registrations, group companies, late filers), and how to limit the burden on them.",
        "Compare the approach with other jurisdictions' VAT carousel-fraud detection, as the base paper suggests [1].",
    ]),
]

SCOPE = {}
SCOPE["in"] = [
    ("h2", "In Scope"),
    ("p", "The project covers the following, all of which are implemented and were run for this report."),
    ("bul", [
        "A seeded generator of GST ecosystems with taxpayers, B2B invoices and monthly GSTR-1, GSTR-2B and GSTR-3B-style returns, four injected fraud patterns with labels and seven kinds of legitimate hard negative.",
        "Three feature layers (invoice, behaviour, network) with 19 features per taxpayer-month.",
        "A JEPA behaviour encoder trained without labels, with four mask variants.",
        "Detection of circular trading (bounded cycle search with scoring), shared-identity shell clusters, abnormal ITC spikes and fake-invoice exposure.",
        "Invoice-level anomaly scoring, a combined taxpayer risk and ranked invoice chains.",
        "Per-taxpayer evidence lists and Gemini-written case notes with automatic grounding checks.",
        "Evaluation against injected labels and a rule baseline, with ablations, per-pattern recall, ring recovery, a PaySim transfer check and a cross-seed study.",
        "A secured multi-user web application with ranking, profile, graph, chain, case, performance and history screens.",
    ]),
]
SCOPE["out"] = [
    ("h2", "Out of Scope"),
    ("bul", [
        "Connection to the live GST Network, real taxpayer data or any government system.",
        "Legal determination of fraud, notices, recovery or prosecution; the output is a risk indication for review.",
        "Sales-tax and VAT regimes of other jurisdictions (the title mentions \"Sales Tax\", but only the Indian GST structure of GSTR-1, 2B and 3B is modelled).",
        "Fine-tuning of language-model weights.",
        "E-invoice (IRN) and e-way-bill system integration beyond the e-way-bill flag in the data; bank and payment data.",
        "Real-time streaming analysis; the system analyses an ecosystem as a batch.",
        "Mobile applications, role-based access control and multi-tenant administration.",
        "Goods classification fraud (for example HSN misclassification) and refund fraud, which the base paper also mentions.",
    ]),
]
SCOPE["assume"] = [
    ("h2", "Assumptions"),
    ("bul", [
        "Filing data of the three GST returns and registration data (address, contact, date) can be obtained for each taxpayer-month, and the features in Chapter 6 can be computed from them.",
        "Normal behaviour is the majority behaviour in the data; fraud is a minority (13.2 % of taxpayers and 0.82 % of invoices in the bundled ecosystem).",
        "The generator's hard negatives are a reasonable stand-in for legitimate irregularity; this was not validated against real data.",
        "Gemini remains reachable during use of the case-note feature, and its free-tier limits are adequate for demonstrations.",
    ]),
]
SCOPE["limits"] = [
    ("h2", "Limitations"),
    ("bul", [
        "**Dataset size and realism.** One synthetic ecosystem of 600 taxpayers (and further generated ones of 150 to 1,500) with 12 months of filings; no real GST data. Results describe the method on this generator.",
        "**Cross-seed variability.** The weights and threshold were tuned on seed 42. On other generated ecosystems the F1 is lower and varies more (Chapter 8). The headline figures should therefore be read as the best case.",
        "**Hardware.** Everything was measured on one desktop CPU (Intel Core i5-12500, 15.7 GB RAM, no GPU), at times heavily loaded by other jobs; larger machines and larger data were not tried.",
        "**No held-out evaluation set.** The encoder is trained on all taxpayer-months of the ecosystem it later scores. This is the normal transductive setting for unsupervised anomaly detection, but it means there is no train/test split.",
        "**LLM.** Prompted, not fine-tuned. Note quality was evaluated on 6 of the 10 intended cases because the free quota ran out; the numeric-grounding score is 84 % over those notes, not 100 %.",
        "**Pattern coverage.** ITC-spike recall is 0.833, below the rule baseline's 1.00, and fake-invoice-buyer recall is 0.895.",
        "**Shell entities** look normal to the JEPA encoder (JEPA-only recall 0.203); detection depends on the network layer.",
        "**Testing.** No unit-test suite, no UI automation, no load test, no user-acceptance study.",
        "**Not implemented.** Role-based access, HTTPS, rate limiting, audit logging, case management, real-time processing.",
        "**Base-paper comparison.** The base paper has no model, so a numerical comparison with it is not possible; related supervised work (TED) used different, real data.",
    ]),
]

SCOPE["glance"] = [
    ("h2", "Scope at a Glance"),
    ("tbl", "glance", "Scope against the six approved objectives", ["Objective", "Covered", "Not covered"], [
        ["1. Multi-layer GST dataset", "Seeded synthetic ecosystem; invoice, behaviour and network layers; labels for evaluation", "Real GST data; other states' schemas; HSN-level or e-invoice fields"],
        ["2. Self-supervised JEPA", "JEPA over 19 features with 4 mask variants, 3-month window, CPU training", "Longer windows, larger models, pre-training on external data"],
        ["3. Fraud pattern detection", "Fake invoices (buyers and shells), circular trading, shell entities, ITC spikes", "Misclassification and refund fraud; cross-border and e-commerce schemes"],
        ["4. Scoring and ranking", "Taxpayer risk, invoice score, ranked invoice chains", "Calibrated probabilities; learned weights; case prioritisation by recoverable amount"],
        ["5. LLM explanations", "Prompted Gemini notes with citations and automatic grounding checks", "Fine-tuning; human review loop; multilingual notes"],
        ["6. Evaluation", "Precision@k, recall@k, F1, ROC-AUC, ablations, per-pattern recall, ring recovery, cross-seed study, PaySim transfer check", "Real-data validation; human evaluation of notes; confidence intervals over many periods"],
    ], [1.6, 2.9, 2.5]),
]
SCOPE["boundaries"] = [
    ("h2", "Boundary Conditions of the Implementation"),
    ("tbl", "bound", "Parameters that bound what the system accepts and analyses", ["Parameter", "Value", "Where enforced"], [
        ["Taxpayers per generated ecosystem", "150 to 1,500", "pydantic validation on POST /api/pipeline/run"],
        ["Generator seed", "0 to 10,000,000", "same"],
        ["Period analysed", "12 months (April 2025 to March 2026 in the bundled data)", "generator constant N_MONTHS"],
        ["Context window of the JEPA", "3 previous months", "ml/pipeline.py WINDOW"],
        ["Cycle length searched", "at most 5 parties; at most 20,000 cycles scanned", "ml/graph.py detect_cycles"],
        ["Page size of the taxpayer list", "1 to 500", "query validation"],
        ["Concurrent generations", "1", "Store.start_run returns 409 otherwise"],
        ["Session lifetime", "720 minutes", "JWT_EXPIRE_MINUTES"],
        ["Case-note length", "under 320 words, three sections", "system prompt in services/explainer.py"],
        ["Users", "Single role (analyst)", "no role-based access control"],
    ], [2.3, 2.4, 2.3]),
]
SCOPE["deviation"] = [
    ("h2", "Deviations from the Approved Title and Abstract"),
    ("bul", [
        "**\"Tuned LLM\".** The approved title and abstract speak of a tuned LLM. The system tunes the prompt and verifies the output; it does not fine-tune model weights. This is a deliberate scope decision: there is no corpus of real investigator notes to fine-tune on, and the grounding checks give a measurable quality signal without one.",
        "**\"GST and Sales Tax\".** Only the GST structure (GSTR-1, GSTR-2B, GSTR-3B, ITC) is modelled. The same ideas apply to other invoice-credit taxes, but no other tax regime was implemented or tested.",
        "**Base paper.** The batch's base paper is a qualitative study; the project builds the detection model that it calls for rather than reproducing a model from it.",
    ]),
]
