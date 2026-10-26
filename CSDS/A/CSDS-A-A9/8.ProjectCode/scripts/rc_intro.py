"""Chapter 1 content: domain, motivation, problem, need, objectives, scope, contributions, limitations, organisation (ForgetSafe).

Every number is read from experiments/*/metrics.json through doc_common.metrics (see docs/REPORT_FACTS.md).
"""
from __future__ import annotations

from doc_common import CHARTS, PRODUCT, metrics

_b = metrics("baseline")
_s = metrics("seeds")
_dp = metrics("dp_accounting")
_t = _b["training"]
EPS = _t["epsilon"]
PPL0 = _t["perplexity"]
ACC0 = _t["next_character_accuracy"] * 100
PPL50 = _s["pre_unlearning_perplexity"]
ACC50 = _s["pre_unlearning_accuracy"]
AUCB = _s["membership_auc_before"]
AUCA = _s["membership_auc_after"]
RET = _s["utility_retention_percent"]
SIGMA_VALID = _dp["sigma_needed_for_epsilon_below_1"]
_nn = metrics("neural_adapter")
_sc = metrics("synthetic_corpus")
_sp = metrics("security_probe")
_ac = metrics("acceptance")
NN_PARAMS = _nn["base"]["base_parameters"]
NN_ADAPT = _nn["base"]["adapter_dimension"]
NN_CLIENTS = _nn["config"]["n_clients"]
NN_T = _nn["summary"]["timing"]
N_USEFUL = _sc["n_sweep"]["smallest_n_within_1_2x"]["4.85"]
EPS_USEFUL = _sc["n_sweep"]["unlearning_at_smallest_n"]["epsilon"]
SP = _sp["classification_counts"]


def sec_domain(d):
    d.h2("Domain and Background")
    d.p("Machine learning has moved from models trained on one organisation's data to models trained collaboratively across many organisations. "
        "**Federated learning** is the best-known form of this arrangement: a coordinating server sends a global model to the participating clients, each client "
        "improves it on data that never leaves its own device or premises, and the server aggregates the returned updates into a new global model [9]. The "
        "promise is that raw records stay where they were created, which matters most where the data is regulated or commercially sensitive, such as banking, "
        "healthcare, education and retail records.")
    d.p("**Large language models** (LLMs) are now trained and adapted in the same way. Full pre-training is out of reach for most organisations, but "
        "parameter-efficient adapters such as low-rank adaptation (LoRA) [22] make it practical for each client to fine-tune only a small set of added "
        "weights on private text and to share only those weights. A federated LLM pipeline therefore combines three ideas: a shared base model, "
        "client-side fine-tuning on private text, and server-side aggregation of adapter updates. The framework surveyed in the literature for this setting, "
        "Oblivionis [3], explicitly pairs federated fine-tuning of LLMs with several federated and unlearning algorithms.")
    d.p("Keeping raw data local does not mean that a client's data has no effect on the shared model. Every aggregated update carries a trace of the data that produced "
        "it, and language models are known to memorise parts of their training text: Carlini et al. extracted verbatim training sequences from a deployed "
        "language model [21]. In a federated pipeline the trace of one client is spread across the global parameters and cannot simply be deleted by "
        "deleting the client's files. **Machine unlearning** is the field that asks how to remove the influence of specific training data from a trained model "
        "without paying the full price of training again [18], [12], and **federated unlearning** is its form for the client-server setting [17], [7].")
    d.p("The legal background is the right to erasure, commonly called the Right to Be Forgotten, in Article 17 of the General Data Protection Regulation [20]. "
        "A person may ask a controller to erase personal data, and the controller must act without undue delay. Whether the obligation extends to a model "
        "trained on the data is still debated, but a system that can show it has removed a contributor's influence is better placed than one that cannot. "
        "This project concerns that second kind of system: not only removing a client's contribution, but producing evidence that the removal happened.")


def sec_motivation(d):
    d.h2("Motivation")
    d.p("Three observations motivate the project, each taken from the batch's abstract and literature survey and checked against the papers that were available.")
    d.numbered([
        "**Deleting a client from a federated model is expensive if done honestly.** The reference method is retraining the model without the client's data. For an LLM "
        "that is a repeat of the whole fine-tuning, and every deletion request triggers one. Sharded training (SISA) reduces the cost by retraining only the "
        "shard that held the data [12], but it changes how the model is trained from the start.",
        "**Cheap alternatives usually come without proof.** Approximate methods such as gradient ascent on the data to be forgotten, or heuristic changes to weights, "
        "are fast, but the literature reviewed in this project reports that they give no formal statement that the data was forgotten, and that aggressive "
        "unlearning can damage the model's usefulness on the remaining data.",
        "**A regulator or a user needs something they can check.** Even a correct removal is of little use in a compliance setting if the only evidence is the "
        "operator's word. The need is for a record of each request that can be inspected and that exposes later alteration.",
    ])
    d.p("Differential privacy [10] offers a vocabulary for the second observation: a mechanism that adds calibrated noise bounds how much any single client can "
        "change what is released. The literature on certified removal [13], [14] shows that this vocabulary can be turned into removal guarantees for well-behaved models. What "
        "is missing, and what the batch's research gap names, is a complete and inspectable pipeline in which training, removal, verification and record-keeping fit together "
        "for federated language-model workloads. ForgetSafe is a small, fully runnable version of such a pipeline, built so that each step can be executed, measured and "
        "criticised.")
    d.p("A further motivation is methodological. A demonstrator that prints \"CERTIFIED\" is easy to build and easy to misread. The project therefore treats its own "
        "certificate as something to be tested: the measurement study in Chapter 8 asks what the certificate really establishes, under which noise settings and federation sizes the "
        "membership-inference check is informative, and where the audit record can be defeated. These findings, obtained on three models and on synthetic data throughout, are part of the contribution.")


def sec_problem(d):
    d.h2("Problem Statement")
    d.p("The problem statement of the batch (`6.OBJECTIVES&PROBLEM STATEMENT.docx`) has four parts, which the project adopts without change:")
    d.bullets([
        "Client data influence remains embedded in federated LLM parameters after training.",
        "Retraining large models for every deletion request is impractical.",
        "Heuristic unlearning gives no formal proof that data was forgotten.",
        "Without verifiable unlearning, models cannot demonstrate compliance with the Right to Be Forgotten.",
    ])
    d.p("Stated as a design problem: given a set of clients that each contributed an update to a federated model, produce a procedure that (a) removes one client's "
        "contribution from the model without retraining from scratch, (b) states a privacy bound for what the model release reveals, (c) checks the result "
        "against a trusted reference and against an adversary that tries to tell whether the client's data was used, (d) reports how much usefulness remains, and (e) "
        "stores a record of the whole request that cannot be quietly changed. The project solves this design problem on small models so that every claim can be re-run: "
        "a five-client bigram product, a larger synthetic corpus, and a neural adapter model, all described in Chapter 6 and measured in Chapter 8.")


def sec_need(d):
    d.h2("Need for the Project")
    d.p("The need is stated in the batch as a certified unlearning framework that removes a client's influence efficiently and proves it to regulators and users. "
        "Four needs follow from that sentence.")
    d.table([["Need", "What it requires", "How ForgetSafe addresses it"],
             ["Efficiency", "Removal cost should not repeat the cost of training", "Stored clipped updates are subtracted from the aggregate; no client data is touched and no training round is repeated"],
             ["Evidence", "A statement that can be checked, not only asserted", "A certificate with reference-distance, membership-inference, utility and hash fields for every request"],
             ["Bounded release", "A formal statement of what the released model can reveal", "L2 clipping, Gaussian noise and a reported (epsilon, delta) bound, with its limits stated"],
             ["Accountability", "A record that outlives the session and exposes edits", "Append-only JSONL ledger with a SHA-256 chain, verified on demand"]],
            "Needs and how the project addresses them", widths=[0.16, 0.34, 0.5], font=10)
    d.p(f"Each need is met under measured conditions. Efficiency holds for a model whose aggregate is a sum of per-client updates: removing a client takes "
        f"{NN_T['subtract_us_median']:.0f} microseconds on the neural adapters against {NN_T['retrain_seven_adapters_s_median']:.1f} s for retraining the seven retained ones. "
        "Evidence is informative where leakage exists (no noise, small noise, domain level). Accountability holds against editing, deletion and re-ordering of the ledger, "
        "and the probes of Chapter 7 show what a file-level adversary can still do. Chapters 5 to 9 develop these conditions.")


def sec_objectives(d):
    d.h2("Objectives")
    d.p("The six objectives are those of the batch document `6.OBJECTIVES&PROBLEM STATEMENT.docx`. Chapter 8 measures each of them against the outcome.")
    d.numbered([
        "Set up federated fine-tuning of an LLM across multiple clients.",
        "Remove a client's data influence through parameter-level unlearning without full retraining.",
        "Certify forgetting with differential-privacy based guarantees.",
        "Verify unlearning using membership-inference tests and comparison with retraining.",
        "Preserve model utility on the remaining data.",
        "Provide auditable compliance records for each unlearning request.",
    ])
    d.p(f"Two clarifications bind the reading of these objectives. First, objective 1 is met at the scale that runs offline on one CPU workstation: five simulated "
        f"clients of the product (a character-level language model whose parameter vector stands in for an LLM adapter update) and, in the neural study, {NN_CLIENTS} synthetic "
        f"clients that fine-tune LoRA-style adapters ({NN_ADAPT:,} parameters each) of a frozen {NN_PARAMS:,}-parameter recurrent network; pre-trained billion-parameter "
        "models are outside the project's hardware and scope. Second, objective 3 is interpreted as reporting a one-shot Gaussian-mechanism bound for the noisy aggregate and "
        "checking the removal against a recomputation, with the conditions under which that bound is valid measured in Chapter 8.")


def sec_scope(d):
    d.h2("Scope of the Project")
    d.p("**In scope.** The project delivers the following, all present in `8.ProjectCode` and exercised by the tests and the measurement scripts:")
    d.bullets([
        "A federated training procedure over five simulated clients (Finance, Healthcare, Education, Retail, Travel), each holding five text records, with per-client "
        "L2 clipping and Gaussian noise on the aggregate (`certified_unlearning/engine.py`, `model.py`, `dataset.py`).",
        "Client-level unlearning by subtraction of the tracked clipped update, with renormalisation over the retained clients and a status of CERTIFIED or REVIEW_REQUIRED.",
        "A verification stack: reference recomputation, loss-based membership-inference AUC before and after, public-set perplexity and next-character accuracy, "
        "and a utility-retention percentage; and a hash-chained, append-only audit ledger with an on-demand verifier and a downloadable JSON certificate.",
        "A localhost JSON API (nine routes), a React web interface with a landing page and five screens, the original single-page interface, a Tkinter desktop "
        "interface and a command-line demonstration.",
        "Measurement on synthetic data at three scales: the product's 25-sentence corpus, a generated corpus of up to 4,000 clients, and a neural study in which "
        f"{NN_CLIENTS} clients fine-tune low-rank adapters of a {NN_PARAMS:,}-parameter recurrent network (`scripts/run_*.py`).",
        f"Testing: 5 unit tests, 14 smoke checks, a load and concurrency test, {_sp['n_probes']} security probes and {_ac['journeys']} scripted synthetic-user acceptance journeys.",
    ])
    d.p("**Out of scope.** The report does not claim:")
    d.bullets([
        "Pre-trained billion-parameter LLMs, GPU training and federated-learning libraries; the neural study stays on a CPU workstation.",
        "Sample-level or class-level unlearning (only whole-client removal is implemented) and multi-round federated averaging (one aggregation round).",
        "A privacy accountant for repeated releases, secure aggregation, authenticated or encrypted storage of the tracked updates, and signed audit records.",
        "User authentication, authorisation and multi-tenant operation; the interface has no login.",
        "Any legal determination of compliance. The software demonstrates a mechanism; it is not a compliance product.",
    ])


def sec_contrib(d):
    d.h2("Contributions")
    d.p("The contributions of the project are listed below as they will be defended in the later chapters. None is claimed as new to the field; the novelty "
        "statement is in the novelty section of the methodology document and in Chapter 2.")
    d.numbered([
        "**An end-to-end workflow** that joins federated training, parameter-level client removal, verification and compliance record-keeping in one runnable "
        "program, with the model isolated behind a small interface; the same method is then applied unchanged to neural adapter vectors.",
        "**Tracked-update unlearning with a certificate.** Each client's clipped update is stored; removing the client subtracts that update from the noisy aggregate "
        "and renormalises, in time independent of the amount of client data, and issues a certificate carrying the privacy parameters, the reference distance, "
        "the attack and utility measurements and the model hashes before and after.",
        "**A verification stack** of a reference recomputation, a loss-based membership-inference AUC, public-set perplexity and accuracy, and a utility-retention "
        "floor, applied to every request, plus a fresh-noise retraining comparison that tests what the certificate does not.",
        "**A hash-chained audit ledger** with a verifier and a tamper study that separates the edits it detects (field edits, deletions, re-ordering) from those "
        "it cannot (tail truncation, full re-hashing, forged appends, an emptied file).",
        "**A React demonstrator and a JSON API** that let an operator train, remove a client, read the certificate, sample the model and verify the ledger, with "
        "documented error handling for the invalid requests.",
        f"**A measurement study on synthetic data.** At the default setting the model is dominated by noise (perplexity {PPL50['mean']:.0f} against 32 for a uniform model) and the "
        f"reference check is an algebraic identity. The synthetic-corpus study shows that epsilon below 1 and a useful model coexist once the federation is large (within 1.2 times "
        f"the noise-free perplexity from {N_USEFUL:,} clients; five removals at epsilon {EPS_USEFUL:.3f} all certified). The neural study shows that removal is real and equals a fresh retraining "
        f"({NN_T['subtract_us_median']:.0f} microseconds against {NN_T['retrain_seven_adapters_s_median']:.1f} s).",
        f"**Testing evidence for the service.** Load and concurrency runs (one winner among 32 simultaneous removals of the same client, a valid chain after 16 simultaneous trainings), "
        f"{_sp['n_probes']} security probes with {SP['defect']} defects reported and ranked for repair, and {_ac['journeys_passed_all_steps']} of {_ac['journeys']} scripted synthetic-user acceptance journeys passed.",
    ])


def sec_limits(d):
    d.h2("Boundaries and Assumptions")
    d.p("The boundaries of the work are stated once here, each with the evidence that fixes it; Chapters 7 and 8 give the measurements and the scope-and-limitations document repeats them.")
    d.bullets([
        f"**Scale.** The product's model is a character-bigram model with 1,089 parameters; the neural study uses a frozen {NN_PARAMS:,}-parameter GRU with {NN_CLIENTS} synthetic clients and one "
        "aggregation round, on one CPU workstation. Exact subtraction relies on an aggregate that is a sum of stored updates; multi-round, non-linear LLM training would not have that property.",
        "**Data.** All data are synthetic: the product's 25 hand-written sentences (membership AUC resolves 0.04), a seeded-grammar corpus of 200 training and 200 held-out sentences per client, "
        "and the neural study's template language. No real-world corpus is used, and no result is presented as one.",
        f"**Noise at the default setting.** With noise multiplier 3 the model reaches perplexity {PPL0:.0f} on the baseline seed ({PPL50['mean']:.0f} "
        f"+/- {PPL50['sd']:.0f} over 50 seeds) and about {ACC50['mean'] * 100:.0f} % next-character accuracy; the membership attack is at chance before unlearning "
        f"(AUC {AUCB['mean']:.2f} +/- {AUCB['sd']:.2f}). Larger federations dilute the noise (useful from {N_USEFUL:,} clients at epsilon below 1).",
        f"**Epsilon range, noise reuse, accounting.** The reported epsilon of {EPS:.2f} follows the classical Gaussian-mechanism formula, valid only for epsilon below 1 "
        f"(noise multiplier above {SIGMA_VALID:.2f}). The same noise vector is kept after unlearning and the certificate repeats the training-time epsilon; there is no privacy accountant.",
        "**Certificate and ledger.** The reference model is rebuilt from the same stored updates and noise, so a distance near 1e-14 is expected by construction; the fresh-noise comparison supplies the independent evidence. "
        "The ledger is tamper-evident, not tamper-proof: it carries no signature or external anchor.",
        f"**Service.** One shared engine and no authentication; the security probes ({SP['defect']} defects, {SP['noteworthy']} noteworthy behaviours) rank the repairs in Chapter 10. "
        "Acceptance was exercised by scripted synthetic users, not by human participants.",
    ])
    d.p("The assumptions are equally explicit: the coordinator is trusted to store the clipped updates and the noise honestly; clients are honest-but-curious rather than "
        "malicious; the aggregate is a one-shot sum rather than a multi-round average; and the evaluation texts are fixed and public.")
    if not getattr(d, "report", False):
        d.figure(CHARTS / "c03_privacy_utility.png",
                 "Reported epsilon against perplexity across noise multipliers (20 seeds per point); the default sigma = 3 and the epsilon = 1 boundary are marked", width=4.6)


def sec_organisation(d):
    d.h2("Organisation of the Report")
    d.table([["Chapter", "Title", "Content"],
             ["1", "Introduction", "Domain, motivation, problem, need, objectives, scope, contributions, boundaries"],
             ["2", "Literature Survey", "Base-paper analysis, related work by theme, algorithms and datasets, strengths and limits, research gap, novelty"],
             ["3", "Feasibility Study", "Technical, economic, operational and schedule feasibility"],
             ["4", "System Requirements and Analysis", "Existing and proposed system, functional and non-functional requirements, platform, roles"],
             ["5", "System Design", "Architecture, workflow, data-flow diagrams, UML, data model, modules, user interface"],
             ["6", "Methodology and Software Implementation", "Pipeline, data, algorithm and its justification, mathematics, application, API, security, installation"],
             ["7", "System Testing", "Strategy and results of unit, integration, functional, security, validation, performance, load and acceptance tests"],
             ["8", "Results and Output Screens", "Output screens, measurements, comparison with the literature, success and failure analysis, objectives against outcomes"],
             ["9", "Conclusion", "Summary, objectives achieved, findings, applications, boundaries"],
             ["10", "Future Scope", "Improvements, features, deployment, research directions"],
             ["-", "References, Appendices A-C", "Numbered IEEE reference list; important code; installation and user guide; additional screens"]],
            "Organisation of the report", widths=[0.1, 0.3, 0.6], font=10)
    if not getattr(d, "report", False):
        d.p(f"The report is followed by the numbered reference list and three appendices: important code, installation and user guide, and additional screens. Throughout, "
            f"{PRODUCT} denotes the software, \"the batch\" denotes the supplied project documents, and numbers in square brackets refer to the reference list.")
    