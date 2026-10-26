"""Chapter 6 content: methodology and software implementation (ForgetSafe).

Numbers come from experiments/*/metrics.json and from small computations done here at build time (the exact Gaussian-mechanism
epsilon, the differencing check); code excerpts are read from the source files so that they are verbatim.
"""
from __future__ import annotations

import json
import math
import sys
import tempfile
import textwrap
from pathlib import Path

from doc_common import ROOT, SHOTS, metrics, REF

sys.path.insert(0, str(ROOT))


# ------------------------------------------------------------------------------------------------------------------ helpers
def _src(rel: str, start: int, end: int, must: str, dedent: bool = True) -> str:
    """Lines start..end (1-based, inclusive) of a project file; fails loudly if the file no longer matches."""
    lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
    assert must in lines[start - 1], f"{rel}:{start} no longer contains {must!r}"
    chunk = "\n".join(lines[start - 1:end])
    return textwrap.dedent(chunk) if dedent else chunk


def _trim(d, rows, drop):
    """Report mode: drop rows whose first cell starts with one of `drop`; chapter documents keep every row."""
    if not getattr(d, "report", False):
        return rows
    return [r for r in rows if not any(str(r[0]).startswith(x) for x in drop)]


def _phi(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def _eps_exact(sigma: float, delta: float = 1e-5) -> float:
    """Smallest epsilon at which the Gaussian mechanism (sensitivity C, noise std sigma*C) is (epsilon, delta)-DP: Balle and Wang [19]."""
    def d_of(eps: float) -> float:
        a = 1.0 / (2.0 * sigma)
        return _phi(a - eps * sigma) - math.exp(eps) * _phi(-a - eps * sigma)
    lo, hi = 0.0, 60.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if d_of(mid) > delta:
            lo = mid
        else:
            hi = mid
    return hi


def _eps_classical(sigma: float, delta: float = 1e-5) -> float:
    return math.sqrt(2.0 * math.log(1.25 / delta)) / sigma


def _nn():
    return metrics("neural_adapter")


def _syn():
    return metrics("synthetic_corpus")


def _differencing_error() -> float:
    """||n*theta_before - (n-1)*theta_after - u_removed||: the removed client's clipped update is recoverable from the two released models."""
    from certified_unlearning.engine import FederatedUnlearningEngine
    from certified_unlearning.model import l2_norm

    with tempfile.TemporaryDirectory() as tmp:
        e = FederatedUnlearningEngine(audit_path=Path(tmp) / "a.jsonl")
        e.train()
        before = list(e.model.parameters)
        n = len(e.active_client_ids)
        e.unlearn("client_finance")
        after = list(e.model.parameters)
        rec = [n * a - (n - 1) * b for a, b in zip(before, after)]
        return l2_norm([a - b for a, b in zip(rec, e.updates["client_finance"])])


def _dataset_rows():
    from certified_unlearning.dataset import CLIENTS, NON_MEMBER_TEXTS, PUBLIC_EVALUATION
    from certified_unlearning.model import l2_norm, normalize_text, raw_update

    rows, union = [], [0.0] * 1089
    for c in CLIENTS:
        u = raw_update(c.records)
        for i, v in enumerate(u):
            union[i] += v
        rows.append((c, sum(len(normalize_text(r)) for r in c.records), int(sum(u)), sum(1 for v in u if v), l2_norm(u), max(u)))
    seen = {i for i, v in enumerate(union) if v}

    def unseen(texts):
        u = raw_update(texts)
        return sum(v for i, v in enumerate(u) if i not in seen) / sum(u), int(sum(u))

    return rows, union, unseen(PUBLIC_EVALUATION), unseen(NON_MEMBER_TEXTS), PUBLIC_EVALUATION, NON_MEMBER_TEXTS


# ------------------------------------------------------------------------------------------------------------------ overview
def sec_method_overview(d):
    base = metrics("baseline")
    d.h2("Overall Methodology")
    d.p("The methodology has two layers: the method that the product implements, and the method by which it was evaluated. The product method "
        "is a single pipeline of seven steps, from client updates to an audit record. The evaluation method is a set of repeatable experiments "
        "that treat the product as a black box and measure what its certificate does and does not establish.")
    if getattr(d, "report", False):
        d.p("The design followed the review method of the base paper [1], whose subject (sign-language recognition) is unrelated, so nothing but the method was taken: "
            "organise the approaches, compare strengths and limitations, read the gap. Applied to unlearning (Chapter 2) it gave these decisions: full retraining only as the reference "
            "computation; no heuristic methods for certification; sharded training [12] left as a future back end; Gaussian noise with an (epsilon, delta) figure [10], [11]; "
            "and exact subtraction of tracked additive updates.")
    else:
        d.p("The design of the product followed the review method of the base paper [1]: organise the existing approaches into a taxonomy, compare "
            "their strengths and limitations, and read the open gap from the comparison. The base paper applies that method to continuous sign-language "
            "recognition; the subject is unrelated, so no algorithm and no result was taken from it. Applied to machine unlearning, the method gave the "
            "decisions in the table below.")
        d.table([["Approach class", "Strength", "Limitation", "Decision in ForgetSafe"],
                 ["Full retraining", "Strongest removal baseline", "Cost grows with model and data", "Used as the reference computation, and in the retrain-from-scratch experiment"],
                 ["Gradient or weight heuristics", "Fast", "No evidence that the data is gone", "Not used for certification"],
                 ["Sharded training (SISA) [12]", "Limits the retraining scope", "Adds training-architecture complexity", "Left as a future back end"],
                 ["Differentially private training [10], [11]", "Bounds one client's influence", "Privacy-utility trade-off", "Gaussian noise and an (epsilon, delta) figure included"],
                 ["Tracked additive updates", "Exact subtraction at O(d) cost", "Requires protected storage of every update", "Used by the demonstrator"]],
                "Approach classes and the resulting design decisions", widths=[0.22, 0.2, 0.25, 0.33], font=9.5)
    d.h3("The product pipeline")
    d.numbered([
        "**Build client updates.** Each client's records are normalised and turned into a vector of character-bigram counts (1,089 coordinates).",
        "**Clip.** The vector is scaled so that its L2 norm is at most C = 25; the original norm and the scale are kept.",
        "**Aggregate with noise.** The coordinator sums the clipped updates, adds one Gaussian noise vector with standard deviation sigma times C "
        "(sigma = 3) per coordinate, and divides by the number of clients. The result is the global model.",
        "**Record.** A `FEDERATED_TRAINING` event with the configuration and the model's SHA-256 fingerprint is appended to the ledger.",
        "**Remove a client.** The client's stored clipped update is subtracted from the noisy sum, the sum is divided by the remaining client count, "
        "and the model is rebuilt. No raw record is read and nothing is retrained.",
        "**Verify.** The engine recomputes a retained-only aggregate, measures the loss-based membership attack on the removed client's records before "
        "and after, measures perplexity and next-character accuracy on a public evaluation set, and computes the utility retained.",
        "**Certify and record.** If the reference distance is at most 1e-10 and the retention is at least 70 percent the status is `CERTIFIED`, "
        "otherwise `REVIEW_REQUIRED`; the certificate is appended to the ledger, whose hash chain can be verified at any time.",
    ])
    d.h3("The evaluation method")
    d.p("Because the application reports its own verdict, a verdict alone is weak evidence. Four sets of experiments therefore treat the product as a "
        "black box. (1) `scripts/run_experiments.py` runs the default configuration "
        f"(seed {base['config']['seed']}), 50 seeds with every client removed in turn (250 requests), a noise sweep from 0.001 to 10, a comparison with a true "
        "retrain that draws fresh noise, a noise-free run, sequential removal, seven ledger attacks, scaling to 500 synthetic clients and 100 requests per "
        "endpoint. (2) `scripts/run_synthetic_corpus.py` repeats the study with the real engine on a larger synthetic corpus (20 domains, 200 sentences per "
        "client) and finds the federation size at which epsilon below 1 and a useful model coexist. (3) `scripts/run_neural_experiment.py` applies the same "
        "clip, noise and subtract rules to LoRA-style adapters of a small neural language model trained on synthetic text. (4) "
        "`scripts/run_testing_experiments.py` measures load and concurrency, 58 security probes and 20 scripted synthetic-user acceptance journeys against "
        "the running application. All of them run on one Intel Core i5-12500 workstation with 15.7 GB of RAM, write `experiments/<name>/metrics.json`, and use "
        "synthetic data only.")


# ------------------------------------------------------------------------------------------------------------------ dataset
def sec_dataset(d):
    rows, union, (pub_un, pub_tr), (non_un, non_tr), public, nonmember = _dataset_rows()
    d.h2("Dataset")
    d.p("ForgetSafe uses no external dataset. The corpus is defined in `certified_unlearning/dataset.py` and consists of three fixed sets of short "
        "English sentences: the records of five simulated clients, a public evaluation set, and a set of non-member sentences. It was written for "
        "the demonstrator, is shipped inside the source file, and so involves no download, licence or personal data. The clients are named by "
        "domain: Finance, Healthcare, Education, Retail and Travel, each holding five sentences.")
    table = [["Client", "Domain", "Records", "Characters", "Bigram transitions", "Non-zero cells", "Raw L2 norm", "Largest count"]]
    for c, chars, trans, nz, norm, mx in rows:
        table.append([c.display_name, c.domain, str(len(c.records)), str(chars), str(trans), f"{nz} of 1,089", f"{norm:.3f}", f"{mx:.0f}"])
    d.table(table, "The five client corpora and their update vectors", widths=[0.12, 0.13, 0.09, 0.12, 0.15, 0.14, 0.13, 0.12], font=9,
            align=["l", "l", "c", "c", "c", "c", "c", "c"])
    d.p(f"Together the clients hold 25 sentences, 1,258 bigram transitions, and {sum(1 for v in union if v)} distinct non-zero cells out of the 1,089 "
        "possible. The samples below show the character of the text; every sentence is a short, generic statement tied to the client's domain.")
    if not getattr(d, "report", False):
        d.bullets([f"{r[0].domain}: \"{r[0].records[0]}\"" for r in rows])
    if getattr(d, "report", False):
        d.p(f"The public evaluation set has {len(public)} sentences and measures perplexity and accuracy; the non-member set has {len(nonmember)} sentences and supplies the "
            f"negative class of the attack. {pub_un * 100:.1f} percent of the public-set transitions and {non_un * 100:.1f} percent of the non-member transitions never occur in "
            "training, which is why the smoothing constant matters.")
    else:
        d.p(f"The **public evaluation set** has {len(public)} sentences ({pub_tr} transitions) on privacy and learning themes and is used to compute "
            f"perplexity and next-character accuracy for every model state. The **non-member set** has {len(nonmember)} sentences ({non_tr} transitions) "
            "that no client holds; it supplies the negative class of the membership attack. Measured against the union of the client corpora, "
            f"{pub_un * 100:.1f} percent of the public-set transitions and {non_un * 100:.1f} percent of the non-member transitions never occur in "
            "training, which is why the smoothing constant of the model matters.")
    if not getattr(d, "report", False):
        d.table([["Set", "Sentences", "Role", "Used by"],
                 ["Client records", "5 per client, 25 in all", "Source of each client's update; the 'member' class of the attack", "`train()`, `membership_auc()`"],
                 ["Public evaluation", "5", "Utility measurement on data that no client owns", "`metrics()`"],
                 ["Non-member texts", "5", "'Non-member' class of the attack", "`unlearn()`"]],
                "Roles of the three fixed sets", widths=[0.2, 0.2, 0.38, 0.22], font=9.5)
    d.p("There is no train, validation and test split in the machine-learning sense, because nothing is fitted by optimisation; the three sets "
        "have disjoint roles instead. Twenty-five sentences are too few for a bigram model to learn from and give the membership attack only 5 member "
        "and 5 non-member scores (AUC steps of 0.04). The study therefore adds two larger synthetic corpora, described next, which supply the data for "
        "every result beyond the default run.")
    d.h3("Two larger synthetic corpora")
    d.p("**Synthetic-grammar corpus** (`scripts/run_synthetic_corpus.py`). A seeded template grammar with 12 sentence templates, and 3 more that insert one "
        "of six private pseudo-words per client, generates sentences for 20 domains (Finance, Healthcare, Education, Retail, Travel and 15 more, each with "
        "its own roles, nouns, adjectives, verbs and adverbs). Client i holds 200 training sentences of domain i. Its non-members are 200 held-out "
        "sentences of the same generator that were never trained on (the sentence-level attack) and 200 held-out sentences of other clients (the "
        "domain-level attack); a 300-sentence public set spread over the domains measures utility. With 200 against 200 scores the attack resolution is "
        "5e-5 instead of 0.04. **Neural corpus** (`scripts/run_neural_experiment.py`). A second grammar builds 8 client domains from pseudo-word "
        "vocabularies (14 syllables, 20 nouns, 15 verbs and 15 adjectives per domain, 6 to 10 sentence skeletons), so no real-language knowledge can "
        "leak in. Each client has 150 training and 150 held-out sentences (overlap checked: 0); a 6,000-sentence public pool pre-trains the base network, a "
        "200-sentence public set measures utility, and 150 sentences of an outsider domain that never joins the federation form the negative class of the "
        "client-level attack.")
    d.table([["Source", "Clients x sentences", "Non-members of the attack", "Used for"],
             ["Product corpus", "5 x 5", "5 fixed sentences", "Default run, 50 seeds, noise sweep, API tests"],
             ["Synthetic-grammar corpus", "up to 20 x 200; up to 4,000 x 100", "200 held-out of the same client; 200 of other clients", "Clip norm, domain-level attack, epsilon against federation size, timing"],
             ["Neural corpus", "8 x 150", "150 held-out of the same client; 150 outsider", "Adapter study"]],
            "The three data sources (all synthetic)", widths=[0.2, 0.22, 0.3, 0.28], font=9)


# ------------------------------------------------------------------------------------------------------------------ preprocessing
def sec_preprocessing(d):
    d.h2("Preprocessing")
    d.p("Preprocessing has three steps, all in `certified_unlearning/model.py`: text normalisation, bigram counting and clipping. Together they "
        "turn a client's sentences into the vector that the federated protocol treats as the client's update.")
    d.h3("Normalisation")
    d.code(_src("certified_unlearning/model.py", 12, 19, "ALPHABET", dedent=False), "alphabet, index and `normalize_text()` (model.py)")
    if getattr(d, "report", False):
        d.p("Text is lower-cased, characters outside the 33-symbol alphabet (start and end markers, space, 26 letters, `. , ? !`) become spaces, whitespace runs are "
            "collapsed and the ends stripped; digits and accents are therefore lost, which a real tokenizer would change.")
    else:
        d.p("Text is lower-cased, every character outside the 33-symbol alphabet is replaced by a space, runs of whitespace are collapsed and the ends "
            "are stripped. The alphabet is the start marker `^`, the end marker `$`, the space, the 26 lower-case letters and the four punctuation "
            "marks `.`, `,`, `?` and `!`. Digits, accented letters and other punctuation are therefore lost, which is acceptable for the English "
            "sentences of the corpus and would be the first thing to change for a real tokenizer.")
    d.h3("Bigram counting")
    d.code(_src("certified_unlearning/model.py", 22, 33, "def _offset", dedent=False), "`_offset()` and `raw_update()` (model.py)")
    if getattr(d, "report", False):
        d.p("Each record is wrapped as `^text$` and every adjacent pair adds one to a cell of a 33 x 33 table stored as a flat list (the cell for `a` to `b` is at "
            "`index(a) * 33 + index(b)`); `go.` adds one to (`^`, g), (g, o), (o, `.`) and (`.`, `$`). The vector counts events, so the aggregate is linear in the data: "
            "the property that exact unlearning relies on.")
    else:
        d.p("Each normalised record is wrapped as `^text$`, and every pair of adjacent symbols adds one to a cell of a 33 x 33 table stored as a flat "
            "list; the cell for the transition from `a` to `b` is at `index(a) * 33 + index(b)`. As a worked example, the record `go.` becomes "
            "`^go.$` and adds one to the cells (`^`, g), (g, o), (o, `.`) and (`.`, `$`). A client's raw update is the sum over its five records, "
            "and its largest single count in the corpus is 9. The vector is a count of events, which makes the aggregate linear in the data: adding "
            "or removing a record adds or removes its counts, the property that exact unlearning will rely on.")
    d.h3("Clipping")
    d.code(_src("certified_unlearning/model.py", 40, 44, "def clipped_update", dedent=False), "`clipped_update()` (model.py)")
    if getattr(d, "report", False):
        d.p("The raw update is scaled by `min(1, C / norm)` with C = 25. All five raw norms (25.219 to 28.231) exceed C, so all five clients are clipped (scales 0.886 to 0.991, "
            "clipped norm exactly 25). Clipping bounds one client's influence, which the differential-privacy calibration needs, at the cost of distortion (Healthcare is scaled down by 11.4 percent).")
    else:
        d.p("The raw update is scaled by `min(1, C / norm)` with C = 25. All five raw norms (25.219 to 28.231) exceed C, so all five clients are "
            "clipped, with scales from 0.886 to 0.991 and a clipped norm of exactly 25. Clipping serves two purposes: it bounds the influence of any one "
            "client, which is what the differential-privacy calibration needs, and it equalises the five clients. Its cost is distortion: the "
            "client with the largest raw norm (Healthcare, 28.231) is scaled down by 11.4 percent.")


# ------------------------------------------------------------------------------------------------------------------ algorithm choice
def sec_algorithm_choice(d):
    d.h2("Algorithm Choice and Justification")
    d.p("The central choice is how to remove a client's influence. The table lists the alternatives considered and the reason each was not "
        "adopted; the descriptions come from the cited works and are about the technique in general, not about their reported numbers.")
    d.table(_trim(d, [["Alternative", "Idea", "Why it was not used here"],
             ["Retrain from scratch", "Train again on the retained clients", "Exact, but it is the cost that motivates the problem; used only as a reference"],
             ["SISA sharding [12]", "Train shard models and retrain only the shard that held the data", "Needs a different training architecture and an ensemble; no shard structure in a single aggregate"],
             ["Gradient ascent and weight heuristics", "Move the weights away from the data to be forgotten", "No evidence of removal and no clean reference; the batch literature survey lists this as a weakness"],
             ["Certified removal by a Newton step [13]", "One second-order update with noise gives an (epsilon, delta) removal guarantee for convex models", "Needs a convex loss and a Hessian; the proxy has no loss to optimise"],
             ["Influence-based unlearning [14]", "Remove influence with an approximate update and bounded excess risk", "Same requirement of a differentiable empirical risk"],
             ["FedEraser [17]", "Reconstruct the global model from stored historical client updates, calibrated with a few rounds", "Aimed at multi-round training; ForgetSafe aggregates once, so exact subtraction is possible"],
             ["Memorisation pruning [2]", "Reset parameters responsible for memorised content", "Needs a trained deep model and a memorisation metric"],
             ["Federated LLM unlearning [3]", "Unified framework of federated algorithms and unlearning algorithms for LLMs", "Needs an LLM and GPUs; the target of the future back end"]], ("Influence-based", "Memorisation pruning", "Federated LLM unlearning")),
            "Alternatives considered", widths=[0.22, 0.39, 0.39], font=9.5)
    d.p("**Why tracked additive updates.** The aggregate is a sum. If the coordinator stores each client's clipped update, then removing client j "
        "is the subtraction of a stored vector, and the result is the same vector that a recomputation over the remaining clients would give. "
        "The cost is one vector operation, independent of the amount of data; the evidence is an identity that can be checked to floating-point "
        "precision; and the method needs no access to the removed client's raw records. These properties fit the six objectives of the project "
        "better than any approximate method could, and they make the verification step meaningful to implement.")
    d.p("**What the choice costs.** Exact subtraction is possible only because the model is a linear function of a single round of updates. Real "
        "federated averaging [9] runs many rounds in which each client's update depends on the global model of the previous round, so a client's "
        "influence is entangled with later updates and cannot be removed by subtracting one stored vector; this is the reason the literature "
        "turns to approximate and statistical removal. The method also requires the coordinator to keep every update, which are the most sensitive "
        "artefacts in the system. The project therefore describes the result as an exact removal in a one-round linear setting, not as a method "
        "for LLM unlearning in general.")
    d.p("**Gaussian mechanism with clipping.** Clipping bounds the L2 sensitivity of the sum to C when a client is added or removed, and Gaussian "
        "noise scaled to that sensitivity is the standard mechanism for L2-bounded releases [10]. Its use here follows the practice of DP training "
        "[11], applied once to the aggregate. **Loss-threshold membership inference.** An example is predicted to be a training member when its loss "
        "is low [15], [16]; the AUC of that score over member and non-member texts is a threshold-free summary. It is the simplest attack that "
        "needs only the model's outputs, and it is the one most often used as a first check of unlearning claims. **SHA-256 hash chain.** Linking "
        "each record to its predecessor makes ordinary edits detectable with the standard library alone; signatures and external anchoring were "
        "left out of scope.")
    syn = _syn()
    rn = syn["raw_norms"]
    d.p("**Clip norm and adapters.** The clip norm decides how much of each update survives. On the 25-sentence corpus the product's C = 25 is close to the raw "
        f"norms (25.2 to 28.2). On 200-sentence clients the raw norms have median {rn['median']:,.0f}, so C = 25 scales every update by "
        f"{rn['scale_applied_by_product_C25']['mean']:.3f}, about {rn['ratio_median_norm_to_C25']:.0f} times down, and the noise-free perplexity is 11.1 instead of 8.8. "
        "The larger studies therefore set C to the median raw norm of the clients, which leaves most updates unclipped and keeps the sensitivity bound. For the "
        "neural model the communicated update is a LoRA-style adapter [22] whose down-projection is fixed and shared by all clients (LoRA-FA), so the average of "
        "the trained factors equals the factor of the average weight update: aggregation stays linear, which is the only property exact subtraction needs.")


# ------------------------------------------------------------------------------------------------------------------ mathematics
def sec_math(d):
    dp = metrics("dp_accounting")
    base = metrics("baseline")
    d.h2("Mathematical Formulation")
    d.p("The formulation below is written in plain text and is exactly what the code computes. Let V = 33 be the alphabet size, d = V x V = 1,089 "
        "the number of parameters, K = 5 the number of clients and n the number of active clients.")
    d.code("""Client update      phi_k in R^d,  phi_k[a,b] = number of times symbol b follows symbol a in "^record$", summed over client k's records
Clipping           u_k = phi_k * min(1, C / ||phi_k||_2),                 C = 25
Noisy aggregate    s   = sum_{k active} u_k + z,                          z ~ N(0, (sigma*C)^2 I_d),  sigma = 3
Global model       theta = s / n
Release (epsilon)  epsilon = sqrt(2 ln(1.25 / delta)) / sigma,            delta = 1e-5""", "training")
    d.p(f"With delta = 1e-5 the numerator is sqrt(2 ln 125000) = {dp['numerator']:.4f}, so sigma = 3 gives epsilon = {dp['default_epsilon']:.4f}, "
        f"and the noise has standard deviation {dp['noise_std_per_coordinate_default']:.0f} per coordinate of the sum and 15 per coordinate of the model. "
        "Adding or removing one client changes the sum s by at most C in L2 norm, so the release of s is a Gaussian mechanism with sensitivity C and "
        "noise scale sigma times C; theta is a post-processing of it.")
    d.h3("Validity of the reported epsilon")
    d.p("The expression above is the classical calibration of the Gaussian mechanism [10], which is proved for epsilon below 1, that is for sigma above "
        f"{dp['sigma_needed_for_epsilon_below_1']:.3f}. The default sigma = 3 gives epsilon = 1.615, outside that range. The exact condition for a Gaussian "
        "mechanism with sensitivity ratio 1/sigma to be (epsilon, delta)-differentially private is given by Balle and Wang [19]: "
        "Phi(1/(2 sigma) - epsilon sigma) - e^epsilon Phi(-1/(2 sigma) - epsilon sigma) <= delta, where Phi is the standard normal distribution function. "
        "Solving it numerically for delta = 1e-5 gives the table below.")
    rows = [["sigma", "epsilon reported (classical formula)", "epsilon exact (analytic Gaussian) [19]", "Reported value is"]]
    for s in (0.5, 1.0, 2.0, 3.0, 4.85, 10.0):
        c, e = _eps_classical(s), _eps_exact(s)
        rows.append([f"{s:g}", f"{c:.3f}", f"{e:.3f}", "conservative (larger than exact)" if c >= e else "optimistic (smaller than exact)"])
    d.table(rows, "Reported and exact epsilon for the Gaussian mechanism (delta = 1e-5)", widths=[0.12, 0.28, 0.32, 0.28], font=9.5,
            align=["c", "c", "c", "l"])
    if getattr(d, "report", False):
        d.p("At the default noise level the reported figure is conservative (exact epsilon about 1.27, below 1.615); below sigma of about 0.6 the classical formula reports a smaller "
            "epsilon than the exact one, which is the region where the model is useful. The application does not distinguish the two cases or account for repeated releases. The table was "
            "computed when this report was built, by `_eps_exact` in `scripts/rc_method.py` from the formula of [19]; it is not an output of the application.")
    else:
        d.p("At the default noise level the reported figure is conservative: the exact value is about 1.27, lower than 1.615. At low noise it is not: "
            "below sigma of about 0.6 the classical formula reports a smaller epsilon than the exact one, which is the region where the model is useful. The "
            "application does not distinguish the two cases, and it does not account for repeated releases. Both are stated as limitations. The table "
            "was computed when this report was built, by the function `_eps_exact` in `scripts/rc_method.py`, from the formula of [19]; it is not an "
            "output of the application.")
    d.h3("Unlearning, reference and certificate")
    d.code("""Unlearning of j    s' = s - u_j ,   n' = n - 1 ,   theta' = s' / n'
Reference          theta_ref = ( z + sum_{k active, k != j} u_k ) / n'         (same stored z and u_k)
Reference distance D = || theta' - theta_ref ||_2                              (floating-point rounding only)
Residual influence R = D                                                      (reported twice in the certificate)
Status             CERTIFIED  iff  D <= 1e-10  and  retention >= 70""", "unlearning and certification")
    d.p("Because s = z + sum of all u_k and the engine stores z and every u_k, the identity theta' = theta_ref holds exactly in real arithmetic, and "
        f"D is only rounding error: {base['max_reference_l2']:.2e} at most over the five removals of the default run, and 3.25e-14 at most over the 250 "
        "requests of the seed study. The check therefore confirms that the code subtracted the right vector; it does not test the claim "
        "that the model is statistically indistinguishable from a model trained without the client. Section 'Key Code Walkthroughs' shows the lines, "
        "and the results chapter tests the stronger claim with fresh noise.")
    d.h3("A consequence of reusing the noise")
    d.p("The noise vector z is drawn once and kept for the whole session, so the model before and after a removal contain the same noise. If an "
        "observer saw the parameter vectors of both, the noise would cancel: n x theta - (n - 1) x theta' = u_j. The function `_differencing_error()` "
        f"performed this computation on the default run when this report was built and recovered the removed client's clipped update to within "
        f"{_differencing_error():.1e} (L2). The API never returns parameter vectors, only metrics, hashes and generated text, so the issue is not "
        "reachable through the application, but a deployment that published both models would give away exactly the information that the "
        "unlearning is meant to protect. Drawing fresh noise at each release, with a privacy accountant, is the corrective design.")
    d.h3("Model and metrics")
    d.code("""Row probabilities  p(b | a) = (max(0, theta[a,b]) + 0.15) / sum_b' (max(0, theta[a,b']) + 0.15),   p(^ | a) = 0
Loss of a record   L(r) = -(1/T) sum_t ln p(x_t | x_{t-1})                       (T transitions of "^r$")
Perplexity         PPL = exp( mean over records of L(r) )
Accuracy           fraction of transitions whose true next symbol is the arg max of p(. | previous)
Utility            Q = 0.65 * accuracy + 0.35 / (1 + ln(1 + PPL))
Retention          100 * min(1, Q_after / Q_before)
Membership AUC     fraction of (member, non-member) pairs with  -L(member) > -L(non-member),  ties counted 1/2""", "model and metrics")
    d.p("A uniform model over the 32 symbols that can be emitted has perplexity 32 and accuracy near 1/32, which gives a reference for the numbers "
        f"that follow. The default model has perplexity {base['training']['perplexity']:.2f} and accuracy {base['training']['next_character_accuracy'] * 100:.2f} percent, so it "
        "is worse than uniform. The utility score weights accuracy more than perplexity and compresses perplexity logarithmically; it is a "
        "dashboard indicator that the project defined, not a standard metric, and a retention of 100 percent means only that the score did not fall.")
    d.h3("Clip-norm rule and the neural adapter")
    d.code("""Clip-norm rule           C = median_k ||phi_k||_2                      (larger studies; the product keeps C = 25)
Adapter vector           theta_k = [B_h (192 x 64), B_o (31 x 64)] flattened,     dim = (192 + 31) * 64 = 14,272
Forward pass             H = GRU(embedding(x));  H' = H + (H A_h^T) B_h^T;  logits = H' W^T + b + (H' A_o^T) B_o^T
                         A_h, A_o: fixed random matrices (rank 64) shared by all clients;  GRU, W, b frozen
Same protocol            u_k = theta_k * min(1, C / ||theta_k||),   s = sum u_k + z,   z ~ N(0, (sigma*C)^2 I),   theta = s / n
Unlearning of j          s' = s - u_j,   theta' = s' / (n - 1)                                  (identical to the bigram product)""", "adapter formulation")
    d.p("Because A is shared, the mean of the factors B is exactly the factor of the mean weight update, so the aggregate is linear in the stored "
        "vectors. The larger studies use three scores. The *sentence-level AUC* compares a client's training sentences with its own held-out sentences (does the "
        "model memorise sentences?). The *domain-level* (bigram corpus) or *client-level* (neural corpus) AUC compares the client's text with other "
        "clients' or an outsider domain's text (does the model carry the client's domain?). *Retention* on the neural model is 100 min(1, PPL_before / "
        "PPL_after) over the retained clients, and is undefined once perplexity reaches the cap of 1e9, because the model is then destroyed by the noise.")


# ------------------------------------------------------------------------------------------------------------------ model and training
def sec_model_training(d):
    base = metrics("baseline")
    t = base["training"]
    d.h2("Model Architecture and Training")
    d.p("The language model is a character-bigram table: a 33 x 33 matrix of parameters that gives, for each previous character, a "
        "distribution over the next one. It has 1,089 parameters, no hidden layers and no gradient-trained weights. It is not a neural network; the "
        "neural adapter study below applies the same protocol to one. It is the smallest object that has the properties the federated "
        "unlearning protocol needs (a flat parameter vector, an additive update, a loss that can be measured per record) and runs offline. The "
        "source file says so, and the user interface repeats it in a standing note.")
    d.p("'Training' is correspondingly simple. There are no epochs, no optimiser and no learning rate. One federated round consists of computing "
        f"the five clipped updates, summing them, adding the noise and dividing by five; the default run took {t['train_ms']:.1f} ms. The "
        "configuration is fixed in the engine's constructor and shown in the next table.")
    d.table(_trim(d, [["Setting", "Value", "Where set"],
             ["Clients / records", "5 clients, 5 sentences each (25 records)", "`dataset.py`"],
             ["Parameter dimension", "1,089 (33 x 33)", "`model.py`, `DIMENSION`"],
             ["Clip norm C", "25.0", "`FederatedUnlearningEngine(clip_norm=25.0)`"],
             ["Noise multiplier sigma", "3.0 (noise std 75 per coordinate of the sum)", "`noise_multiplier=3.0`"],
             ["Delta", "1e-5", "`delta=1e-5`"],
             ["Reported epsilon", "1.6149", "`epsilon` property"],
             ["Random seed", "2026", "`random_seed=2026`"],
             ["Probability smoothing", "0.15", "`CharacterLanguageModel.smoothing`"],
             ["Utility weights", "0.65 accuracy, 0.35 perplexity term", "`metrics()`"],
             ["Certification thresholds", "reference distance <= 1e-10, retention >= 70 percent", "`unlearn()`"],
             ["Sample length", "180 characters through the API, 120 by default", "`web.py`, `engine.generate()`"]], ("Probability smoothing", "Utility weights", "Sample length", "Random seed")),
            "Configuration of the demonstrator", widths=[0.28, 0.44, 0.28], font=9.5)
    d.h3("Why the default model is noise-dominated")
    if getattr(d, "report", False):
        d.p("Each client contributes at most 9 to a cell, so the largest signal in a cell of the model is about 1.8, while the noise has standard deviation 15 in the model; "
            "keeping the positive part of each parameter and adding 0.15 leaves every row dominated by random values, and the 268 non-zero cells carry little against them. "
            f"The result on the public set is perplexity {t['perplexity']:.2f} and next-character accuracy {t['next_character_accuracy'] * 100:.2f} percent for seed 2026 "
            "(142.2 plus or minus 27.5 over 50 seeds); useful quality needs sigma of 0.1 or less, where epsilon is 48 or more.")
    else:
        d.p("The size of the signal and the noise explains the quality of the default model. Each client contributes at most 9 to a cell, and after "
            "division by five the largest signal in a cell is about 1.8. The noise has standard deviation 75 in the sum and 15 in the model. The model "
            "keeps only the positive part of each parameter and adds 0.15, so each row of the table is dominated by random positive values of mean about "
            "6 (15 divided by the square root of 2 pi) and spread of the same order, and the signal in the 268 non-zero cells is small against them. "
            f"The result on the public set is perplexity {t['perplexity']:.2f} and next-character accuracy {t['next_character_accuracy'] * 100:.2f} percent for "
            "seed 2026; over 50 seeds the perplexity is 142.2 plus or minus 27.5. Section 'Results' of the report shows how this changes with sigma: "
            "useful quality needs sigma of 0.1 or less, where epsilon is 48 or more.")
    if not getattr(d, "report", False):
        d.p("The consequence for the design is that the default values were chosen to make the privacy figure look moderate, not to make the model "
            "useful. The demonstrator is honest about the pipeline and the verification, and the project reports its limits instead of tuning the "
            "defaults to hide them.")
    nn = _nn()
    cs = [x["C"] for x in nn["per_seed"]]
    d.h3("Configuration of the neural adapter study")
    d.table([["Setting", "Value"],
             ["Base network", f"Character GRU, embedding 32, hidden 192, {nn['base']['base_parameters']:,} parameters, frozen after pre-training"],
             ["Pre-training", "6,000 synthetic public sentences, 2,500 steps, batch 64, learning rate 3e-3 then 1e-3"],
             ["Adapter", f"LoRA-FA, rank {nn['base']['adapter_rank']}, on the hidden-state residual and the output projection; {nn['base']['adapter_dimension']:,} trainable parameters per client"],
             ["Adapter training", f"Adam, learning rate 5e-3, 256 tokens per batch, {nn['config']['chosen']['epochs']} epochs; rank and epochs chosen by a pilot on one client (lowest held-out perplexity)"],
             ["Federation", f"8 clients, one aggregation round, C = median raw norm ({min(cs):.1f} to {max(cs):.1f}), delta 1e-5, 5 seeds, 40 removal requests per sigma"],
             ["Noise multipliers", ", ".join(f"{x:g}" for x in nn["config"]["sigmas"])],
             ["Cost", f"{nn['runtime_seconds']:.0f} s for the whole experiment on 4 CPU threads (pre-training cached)"]],
            "Configuration of the neural adapter study", widths=[0.24, 0.76], font=9.5)
    d.p("The bigram product and the neural study share every rule of the protocol (clip, sum, Gaussian noise, divide, subtract) and differ in the "
        "vector that is aggregated: 1,089 bigram counts in one case, 14,272 adapter coefficients in the other. The neural study shows that the method does "
        "not depend on the bigram table; its scale (a 137k-parameter network, 8 clients, one round) is the boundary of what the project demonstrates, and "
        "billion-parameter pretrained models are outside its scope and hardware.")


# ------------------------------------------------------------------------------------------------------------------ application architecture
def sec_app_arch(d):
    d.h2("Application Architecture")
    d.p("At run time ForgetSafe is two processes. The Python process serves the API on port 8109 (`python app.py --port 8109`; the default when "
        "no port is given is 8000, which serves the original interface). The Node process runs the Vite development server on port 5109 with "
        "`strictPort`, bound to 127.0.0.1, and proxies `/api` to the Python process, so the browser sees one origin and no cross-origin headers "
        "are needed. The two port numbers are read from the project's environment file by `run.bat` and by `vite.config.js` "
        "(`BACKEND_PORT` and `FRONTEND_PORT`), with 8109 and 5109 as defaults.")
    d.p("Inside the Python process `ThreadingHTTPServer` starts one thread per connection. A single `ApplicationState` holds the engine and a "
        "re-entrant lock; every route that touches the engine runs inside `with application.lock`, so two simultaneous requests are serialised and "
        "the engine never sees a half-updated state. The engine is replaced as a whole on `POST /api/session`, and there is exactly one engine for "
        "all callers: two browser tabs share one session.")
    d.table(_trim(d, [["Component", "Technology (as declared)", "Purpose"],
             ["Back end", "Python 3.10+ standard library (measured on 3.11.9)", "Engine, model, ledger, HTTP server"],
             ["UI framework", "React 19, React DOM 19", "Pages and components"],
             ["Routing", "React Router 7", "Seven routes: landing, five application pages and a not-found page"],
             ["Build and dev server", "Vite 8, `@vitejs/plugin-react`", "Bundling, hot reload, `/api` proxy"],
             ["Charts", "Recharts 3", "Bar, grouped-bar, line and area charts"],
             ["Motion", "Framer Motion 14, GSAP 3, Lenis", "Page transitions, count-up, smooth scrolling"],
             ["Icons and effects", "lucide-react, canvas-confetti", "Icons"],
             ["Desktop UI", "Tkinter (standard library)", "Original desktop window"]], ("Motion", "Icons and effects", "Desktop UI")),
            "Technology stack", widths=[0.2, 0.42, 0.38], font=9.5)
    if not getattr(d, "report", False):
        d.p("The front end can also be built for production with `npm run build`; `npm run preview` serves the build on the same port and keeps the "
            "same proxy. The Python server does not serve the React build, so a deployment would need a reverse proxy in front of both. This is "
            "recorded as future work and is not hidden by the run script.")
    ld = metrics("load_test")
    d.h3("Measured load behaviour")
    rows = [["Scenario", "Clients 1", "Clients 4", "Clients 16", "Clients 64"]]
    for name, v in ld["scenarios"].items():
        lv = {x["concurrency"]: x for x in v["levels"]}
        rows.append([name] + [f"{lv[c]['requests_per_s']:.0f} req/s, p95 {lv[c]['p95_ms']:.0f} ms, {lv[c]['errors_5xx_or_connection']} err" for c in (1, 4, 16, 64)])
    d.table(rows, "Throughput, tail latency and errors under concurrent clients (127.0.0.1, 500 requests or 20 s per level)", widths=[0.2, 0.2, 0.2, 0.2, 0.2], font=8.5)
    r1 = ld["races"]["32 simultaneous unlearn requests for the same client"]
    r2 = ld["races"]["16 simultaneous train requests"]
    so = ld["soak"]
    if getattr(d, "report", False):
        d.p(f"The lock holds: 32 simultaneous removals of one client gave one success and 31 refusals (chain valid), 16 simultaneous trainings gave {r2['ledger_records']} contiguous "
            "records, and a verifier racing 8 writers never read an invalid chain. Capacity is bounded by the design: `/api/state` re-reads and re-verifies the whole ledger on every call, so it "
            f"saturates near 80 requests per second and its median rose from {so['state_ms_first50']['p50_ms']:.0f} to {so['state_ms_last50']['p50_ms']:.0f} ms over a {so['requests']:,}-request "
            f"soak (0 errors) as the ledger grew to {so['ledger_records_end']} records; at 64 simultaneous clients up to 19 of 500 `/api/state` requests failed.")
    else:
        d.p(f"The lock does its job: 32 simultaneous removals of one client produced exactly one success and 31 refusals ({r1['ledger_records']} ledger records, chain valid); "
            f"16 simultaneous training requests produced {r2['ledger_records']} contiguous records; 8 writers and a verifier found no invalid read. Capacity is limited by the design, not "
            f"by the lock alone: `/api/state` re-reads and re-verifies the whole ledger on every call, so it saturates near 80 requests per second, and over a "
            f"{so['requests']:,}-request soak (0 errors) its median rose from {so['state_ms_first50']['p50_ms']:.0f} to {so['state_ms_last50']['p50_ms']:.0f} ms as the ledger "
            f"grew to {so['ledger_records_end']} records. At 64 simultaneous clients a few connections fail (up to 19 of 500 on `/api/state`); there is no queue "
            "or pool, only one thread per connection.")


# ------------------------------------------------------------------------------------------------------------------ code walkthrough
def sec_walkthrough(d):
    d.h2("Key Code Walkthroughs")
    d.p("Five short excerpts carry the logic of the system. They are copied from the source files without change."
        + (" Here the two central ones are shown; the other listings are in Appendix A." if getattr(d, "report", False) else ""))
    d.h3("Training: clip, sum, add noise")
    d.code(_src("certified_unlearning/engine.py", 131, 147, "def train"), "`FederatedUnlearningEngine.train()` (engine.py)")
    d.p("The random generator is seeded, so the same seed reproduces the same noise and the same model hash. Each client's update is computed by "
        "`clipped_update`, stored in `self.updates` together with its original norm and scale, and added to `clean_sum`. The noise vector is drawn "
        "once, with a standard deviation of noise multiplier times clip norm for every coordinate, and added to form `noisy_sum`; the model is "
        "`noisy_sum` divided by the client count. Only `noisy_sum` and the model are used for the model; the stored `updates` and `noise` are what "
        "make removal possible later.")
    if not getattr(d, "report", False):
        d.h3("Unlearning: guards")
        if not getattr(d, "report", False):
            d.code(_src("certified_unlearning/engine.py", 221, 229, "def unlearn"), "guards of `unlearn()` (engine.py)")
        d.p("Four conditions raise before any state changes: the model has not been trained, the client id is unknown, the client was already "
            "removed, or only one client is left. The untrained case raises `RuntimeError`, the unknown id `KeyError`, and the other two `ValueError`; the web "
            "layer maps all of them to HTTP 400.")
    d.h3("Unlearning: subtraction, reference and decision")
    d.code(_src("certified_unlearning/engine.py", 236, 250, "target_update"), "core of `unlearn()` (engine.py)")
    d.p("The first three statements are the unlearning: subtract the stored update from the noisy sum, drop the client from the active list and "
        "rebuild the model. The reference is then recomputed by `_reference_parameters`, which starts from the same stored noise and adds the "
        "retained updates. The comment in the source records the point made earlier in this chapter: the coefficient of the removed update in "
        "the retained aggregate is zero by algebra, so the distance is rounding error. The decision on the last line combines that distance with "
        "the retention threshold.")
    if not getattr(d, "report", False):
        d.code(_src("certified_unlearning/engine.py", 208, 213, "def _reference_parameters"), "`_reference_parameters()` (engine.py)")
    d.h3("Membership inference")
    if not getattr(d, "report", False):
        d.code(_src("certified_unlearning/model.py", 107, 121, "def membership_auc"), "`membership_auc()` (model.py)")
    d.p("The score of a text is its negative loss, so a lower loss means a higher membership score. The function counts the fraction of (member, "
        "non-member) pairs that the score orders correctly, with ties worth one half, which is the Mann-Whitney form of the area under the ROC "
        "curve. With five texts on each side there are 25 pairs, so the value moves in steps of 0.04. When a set is empty the function returns 0.5.")
    d.h3("The audit ledger")
    if not getattr(d, "report", False):
        d.code(_src("certified_unlearning/audit.py", 37, 64, "def append"), "`AuditLedger.append()` and `verify()` (audit.py)")
    d.p("`append` reads the whole ledger, takes the previous record's hash (or 64 zeros), adds the sequence number and the previous hash to the "
        "record, hashes the string of previous hash, a bar and the canonical JSON (sorted keys, compact separators, ASCII only), and writes the "
        "record with its own hash as one line. `verify` walks the file from the start, recomputes each hash from the record minus its "
        "`record_hash` field, and checks the sequence number, the link and the hash; it returns the number of the first record that fails. "
        "Reading the file in `append` is why the cost grows with the ledger, and the absence of any secret in the hash is why a forger who "
        "recomputes every hash cannot be detected.")


# ------------------------------------------------------------------------------------------------------------------ API
def sec_api(d):
    api = metrics("api")
    base = metrics("baseline")
    cert = base["unlearning_per_client"][0]
    d.h2("API Design")
    d.p("The API is a small JSON interface over HTTP defined in `certified_unlearning/web.py`. All responses use `Content-Type: application/json; "
        "charset=utf-8` and `Cache-Control: no-store`, except the legacy page at `/`, which is HTML. Errors are always an object with one `error` "
        "string. Request bodies are JSON objects; the only endpoints that read a body are `/api/unlearn` (`client_id`) and `/api/generate` (`seed`).")
    d.table([["Method", "Path", "Request body", "Success response", "Error responses"],
             ["GET", "`/`", "-", "HTML page of the original interface", "-"],
             ["GET", "`/api/health`", "-", "`{status, service}`", "-"],
             ["GET", "`/api/state`", "-", "`{trained, session_id, metrics, contributions[], active_clients[], latest_certificate, audit{valid, detail, records[]}}`", "500"],
             ["GET", "`/api/certificate/latest`", "-", "Certificate fields plus `audit_valid`, `audit_verification`; `Content-Disposition` attachment", "404 if none"],
             ["POST", "`/api/train`", "none", "`TrainingMetrics`", "400, 500"],
             ["POST", "`/api/session`", "none", "`{session_id}`", "400, 500"],
             ["POST", "`/api/unlearn`", "`{client_id}`", "`UnlearningCertificate` (25 fields)", "400 untrained, unknown, repeated, last client, missing id"],
             ["POST", "`/api/generate`", "`{seed}`", "`{text}`", "400 before training"],
             ["POST", "`/api/audit/verify`", "none", "`{valid, detail}`", "400, 500"]],
            "API endpoints", widths=[0.09, 0.19, 0.14, 0.38, 0.2], font=9)
    d.p("The handler maps exceptions to status codes in one place: `ValueError`, `KeyError`, `RuntimeError` and `json.JSONDecodeError` raised in a POST "
        "become HTTP 400 with the exception text; any other exception becomes HTTP 500; an unknown route is HTTP 404. A certificate request before any "
        "removal is HTTP 404. The example below is the certificate returned when Client 01 (Finance) is removed in the default run (seed 2026); the fields are "
        "abbreviated to the ones that decide the outcome.")
    show = {k: cert[k] for k in ("certificate_id", "client_name", "status", "epsilon", "delta", "reference_retrain_l2", "membership_auc_before",
                                 "membership_auc_after", "perplexity_before", "perplexity_after", "utility_retention_percent", "clients_before", "clients_after")}
    show["certificate_id"] = "(random per run)"
    d.code("POST /api/unlearn   {\"client_id\": \"client_finance\"}\n" + json.dumps(show, indent=2), "request and (abbreviated) response")
    if getattr(d, "report", False):
        d.p("The 19 edge cases measured against the live server are tabulated in the testing chapter; two of them are defects.")
    else:
        d.p("Behaviour at the edges was measured against the live server (the results chapter discusses it). The table gives the observed status for "
            "each case; an oversized body does not reach the client as an HTTP response.")
        rows = [["Case", "HTTP status", "Observed response"]]
        for e in api["edge_cases"]:
            status = "connection aborted" if e["status"] == -1 else str(e["status"])
            resp = str(e["response"]).replace("\n", " ")
            resp = "stdlib HTML 501 page" if resp.startswith("<!DOCTYPE") else (resp[:70] + ("..." if len(resp) > 70 else ""))
            if e["response"] == "ok":
                resp = "accepted"
            rows.append([e["case"], status, resp])
        d.table(rows, "Measured API behaviour at the edges", widths=[0.38, 0.17, 0.45], font=8.5)
    d.p("Two behaviours are defects rather than design. When a body exceeds 1,000,000 bytes the handler raises before reading it and the "
        "connection is closed, so a client sees a reset instead of a clean 400. And a method that the handler does not define (for example PUT) "
        "returns the HTML error page of the standard library, not a JSON error. Neither affects the main flow; the security probes below add eight further defects.")


# ------------------------------------------------------------------------------------------------------------------ security
def sec_security(d):
    from collections import Counter

    sp = metrics("security_probe")
    ac = metrics("acceptance")
    cc = sp["classification_counts"]
    d.h2("Security and Error Handling")
    d.p("ForgetSafe is a local demonstrator, so its controls are modest; what matters is that they were measured. `scripts/run_testing_experiments.py` "
        f"sent {sp['n_probes']} synthetic malicious or malformed requests to the running server, classified each result as handled, handled with noteworthy "
        "behaviour or defect, and checked after every group that `/api/health` still answered.")
    d.h3("What the code does")
    d.bullets([
        "**Localhost binding** of both servers; **no file serving** (a path such as `/../../etc/passwd` returns 404); a fixed ledger path.",
        "**Input checks.** Body limited to 1,000,000 bytes, JSON object required, `client_id` required and validated against the five known clients before any "
        "state changes; seed text is normalised to the 33-symbol alphabet (a 5,000-character seed was accepted).",
        "**Output escaping.** The legacy page escapes every server value; React escapes by default.",
        "**One re-entrant lock** serialises engine access; exceptions are caught per request and returned as JSON, so one failure does not stop the server.",
        "**Tamper evidence.** The ledger detects edits, deletions and re-ordering; three attack classes go undetected (Chapter 7 and the results chapter).",
    ])
    d.h3("Measured security probes")
    if not getattr(d, "report", False):
        groups = Counter()
        kinds = {}
        for pr in sp["probes"]:
            groups[pr["group"]] += 1
            kinds.setdefault(pr["group"], Counter())[pr["classification"]] += 1
        rows = [["Probe group", "Probes", "Handled", "Noteworthy", "Defects"]]
        for g, n in groups.most_common():
            k = kinds[g]
            rows.append([g, str(n), str(k["handled"]), str(k["noteworthy"]), str(k["defect"])])
        rows.append(["**Total**", str(sp["n_probes"]), str(cc["handled"]), str(cc["noteworthy"]), str(cc["defect"])])
        d.table(rows, "Security probes by group", widths=[0.4, 0.15, 0.15, 0.15, 0.15], font=9.5, align=["l", "c", "c", "c", "c"])
    d.p(f"{cc['handled']} probes were handled correctly, {cc['noteworthy']} were handled with behaviour worth knowing, and {cc['defect']} are defects. The server stayed "
        f"alive after all of them (alive: {sp['server_alive_after_all']}). The defects, with their evidence and the fix each one calls for, are:")
    d.table([["Defect", "Evidence", "Fix"],
             ["Negative Content-Length", "`Content-Length: -1` with the socket left open: the handler thread blocks in `rfile.read(-1)`, no response within 4 s", "Reject negative lengths with 400; set a socket timeout"],
             ["No read timeout", "500 bytes declared, 30 sent: the server waits indefinitely for the rest", "Per-connection timeout on the handler"],
             ["Cross-site POST accepted (CSRF)", "`text/plain` POST with a foreign Origin: HTTP 200 and the removal is executed", "Require JSON content type and an authentication header or token; check Origin"],
             ["Host header not validated", "Host `evil.example`: HTTP 200 (DNS-rebinding precondition)", "Allow-list the Host header"],
             ["Connection bursts", "64 simultaneous new connections: 34 served, 30 refused (WinError 10061)", "Bounded worker pool, larger listen backlog, reverse proxy"],
             ["One bad ledger line stops the UI", "A garbage line appended to the file: `/api/state` returns 500 and the interface cannot load", "Quarantine unreadable lines; keep `/api/state` alive and report the failure"],
             ["Empty ledger verifies as valid", "File truncated to zero bytes: verify answers valid with 0 records", "Anchor record count and last hash outside the file (signature or external store)"],
             ["No authentication", "Every route works without credentials: read the full audit log, erase a client, retrain and discard certificates", "Authentication, operator and auditor roles, TLS"]],
            "Defects found by the security probes", widths=[0.22, 0.46, 0.32], font=8.5)
    if getattr(d, "report", False):
        d.p("The 15 noteworthy behaviours are not defects: duplicate JSON keys resolve to the last, a 100 kB client id is echoed back, unsupported methods return the "
            "standard-library HTML 501 page, security headers are absent, 200 idle connections each hold a thread, and a half-closed request that the client abandoned is still executed.")
    else:
        d.p("The noteworthy behaviours are not defects but should be known. Two Content-Length headers are resolved by taking the first (HTTP 400 on the "
            "mismatch); duplicate JSON keys resolve to the last; a 100 kB client id is echoed back in the 400 response; an HTTP/0.9-style request line is served; "
            "OPTIONS, HEAD, TRACE, PUT, DELETE and PATCH return the standard-library HTML 501 page; the security headers X-Content-Type-Options, "
            "Content-Security-Policy and X-Frame-Options are absent and the server banner shows the Python version; a POST without a Content-Type is accepted; 200 idle "
            "connections each hold a thread (4 to 204) while the health check stays at p95 12.6 ms; and a half-closed request that was abandoned by the client is still "
            "executed afterwards.")
    d.h3("Error handling in the user interface")
    d.p("The front end turns every failed call into a toast that shows the server's message, keeps the page usable and offers a retry when the first state "
        "request fails; buttons are disabled while an action runs, and the unlearning page shows an explanatory empty state when fewer than two clients remain. "
        f"These measures handle mistakes, not attacks. A scripted run of {ac['journeys']} randomised synthetic-user journeys (desktop and phone width, light and dark "
        f"theme, cancelled dialogs) passed every step in {ac['journeys_passed_all_steps']} of {ac['journeys']} journeys with {ac['console_error_journeys']} console errors.")


# ------------------------------------------------------------------------------------------------------------------ installation
def sec_install(d):
    d.h2("Installation and Execution")
    d.p("The prerequisites are Python 3.10 or newer, with no third-party packages, and Node.js 18 or newer with npm for the React front end. "
        "The system was developed and measured with Python 3.11.9 and Node.js 24.19 on Windows 11.")
    d.h3("One command (Windows)")
    d.code("run.bat", "starts both servers and opens the browser")
    d.p("`run.bat` reads `BACKEND_PORT` and `FRONTEND_PORT` from the environment file when it exists, opens one console for the API "
        "(`python app.py --port 8109`) and one for the UI (`npm run dev` in `frontend`), installs `frontend/node_modules` on the first run, waits four "
        "seconds and opens http://127.0.0.1:5109.")
    d.h3("Manual start")
    d.code("python app.py --port 8109          # API; also serves the original page at /\ncd frontend\nnpm install\nnpm run dev                     # UI on 5109, proxies /api to 8109", "manual start")
    d.table([["Command", "What it starts"],
             ["`python app.py`", "Original single-page interface on http://127.0.0.1:8000"],
             ["`python app.py --port 8109`", "API and original page on the chosen port"],
             ["`python app.py --desktop`", "Tkinter desktop window"],
             ["`python app.py --demo`", "Headless demonstration: trains, removes the first client and prints the certificate as JSON"],
             ["`npm run build`, `npm run preview`", "Production build of the React front end and a preview server on port 5109"]],
            "Ways to run the application", widths=[0.38, 0.62], font=9.5)
    d.h3("Tests and measurements")
    d.code("python -m unittest discover -s tests -v     # 5 tests\npython scripts/smoke_test.py                    # 14 end-to-end API checks\n"
           "python scripts/run_experiments.py               # writes experiments/*/metrics.json\npython scripts/run_synthetic_corpus.py          # larger synthetic corpus study and git timeline\n"
           "python scripts/run_neural_experiment.py         # neural adapter study (needs torch and numpy, CPU is enough)\npython scripts/run_testing_experiments.py       # load, security probes, scripted acceptance (needs Chrome and Playwright)\n"
           "python scripts/make_charts.py                   # writes docs/charts/*.png",
           "verification commands")
    if not getattr(d, "report", False):
        d.p("The smoke test starts its own server on a spare port with a throw-away working directory, so it does not touch the real audit "
            "ledger; with `--url` it tests an already running server instead. The ledger of a normal run is `data/audit_log.jsonl` under the directory "
            "from which the server was started.")
    if getattr(d, "report", False):
        return   # the troubleshooting table is in Appendix B
    d.table([["Symptom", "Likely cause", "Remedy"],
             ["Page loads but shows 'Could not load the lab'", "API not running or on another port", "Start `python app.py --port 8109`; check the ports in the environment file"],
             ["`npm run dev` fails with a port error", "Port 5109 already in use (`strictPort` is set)", "Stop the other process or change `FRONTEND_PORT`"],
             ["Ledger shows a broken chain", "The file was edited by hand", "Compare the reported record number with the file; delete the file only for a fresh demonstration"],
             ["Certificates disappear after pressing Train", "Training clears the session's certificates", "Expected; the ledger keeps the history"]],
            "Troubleshooting", widths=[0.3, 0.32, 0.38], font=9.5)
