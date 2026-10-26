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
    d.p("Because the application reports its own verdict, a verdict alone is weak evidence. The evaluation therefore adds experiments that the "
        "application does not run itself (`scripts/run_experiments.py`, each writing `experiments/<name>/metrics.json`): the default configuration "
        f"(seed {base['config']['seed']}); a study of 50 seeds with all five clients removed in turn (250 unlearning requests); a sweep of the noise "
        "multiplier from 0.001 to 10 with 20 seeds per value; a comparison of the unlearned model with a true retrain that draws fresh noise (200 pairs "
        "at each of two noise levels); a noise-free run that shows what the attack sees without noise; sequential removal from five clients to one; "
        "seven tampering attacks on the ledger; scaling from 5 to 500 synthetic clients; and 100 requests per endpoint against the live server. All "
        "of them run on one Intel Core i5-12500 machine with 15.7 GB of RAM and use only the standard library.")


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
    d.bullets([f"{r[0].domain}: \"{r[0].records[0]}\"" for r in rows])
    d.p(f"The **public evaluation set** has {len(public)} sentences ({pub_tr} transitions) on privacy and learning themes and is used to compute "
        f"perplexity and next-character accuracy for every model state. The **non-member set** has {len(nonmember)} sentences ({non_tr} transitions) "
        "that no client holds; it supplies the negative class of the membership attack. Measured against the union of the client corpora, "
        f"{pub_un * 100:.1f} percent of the public-set transitions and {non_un * 100:.1f} percent of the non-member transitions never occur in "
        "training, which is why the smoothing constant of the model matters.")
    d.table([["Set", "Sentences", "Role", "Used by"],
             ["Client records", "5 per client, 25 in all", "Source of each client's update; the 'member' class of the attack", "`train()`, `membership_auc()`"],
             ["Public evaluation", "5", "Utility measurement on data that no client owns", "`metrics()`"],
             ["Non-member texts", "5", "'Non-member' class of the attack", "`unlearn()`"]],
            "Roles of the three fixed sets", widths=[0.2, 0.2, 0.38, 0.22], font=9.5)
    d.p("There is no train, validation and test split in the machine-learning sense, because nothing is fitted by optimisation; the three sets "
        "have disjoint roles instead. The size is the main limitation of the data. Twenty-five sentences give a membership attack with only 5 "
        "member and 5 non-member scores, so the AUC moves in steps of 0.04, and a single sentence can change it by 0.2. The experiments "
        "compensate by repeating the whole procedure over 50 seeds, but they cannot make the corpus larger.")


# ------------------------------------------------------------------------------------------------------------------ preprocessing
def sec_preprocessing(d):
    d.h2("Preprocessing")
    d.p("Preprocessing has three steps, all in `certified_unlearning/model.py`: text normalisation, bigram counting and clipping. Together they "
        "turn a client's sentences into the vector that the federated protocol treats as the client's update.")
    d.h3("Normalisation")
    d.code(_src("certified_unlearning/model.py", 12, 19, "ALPHABET", dedent=False), "alphabet, index and `normalize_text()` (model.py)")
    d.p("Text is lower-cased, every character outside the 33-symbol alphabet is replaced by a space, runs of whitespace are collapsed and the ends "
        "are stripped. The alphabet is the start marker `^`, the end marker `$`, the space, the 26 lower-case letters and the four punctuation "
        "marks `.`, `,`, `?` and `!`. Digits, accented letters and other punctuation are therefore lost, which is acceptable for the English "
        "sentences of the corpus and would be the first thing to change for a real tokenizer.")
    d.h3("Bigram counting")
    d.code(_src("certified_unlearning/model.py", 22, 33, "def _offset", dedent=False), "`_offset()` and `raw_update()` (model.py)")
    d.p("Each normalised record is wrapped as `^text$`, and every pair of adjacent symbols adds one to a cell of a 33 x 33 table stored as a flat "
        "list; the cell for the transition from `a` to `b` is at `index(a) * 33 + index(b)`. As a worked example, the record `go.` becomes "
        "`^go.$` and adds one to the cells (`^`, g), (g, o), (o, `.`) and (`.`, `$`). A client's raw update is the sum over its five records, "
        "and its largest single count in the corpus is 9. The vector is a count of events, which makes the aggregate linear in the data: adding "
        "or removing a record adds or removes its counts, the property that exact unlearning will rely on.")
    d.h3("Clipping")
    d.code(_src("certified_unlearning/model.py", 40, 44, "def clipped_update", dedent=False), "`clipped_update()` (model.py)")
    d.p("The raw update is scaled by `min(1, C / norm)` with C = 25. All five raw norms (25.219 to 28.231) exceed C, so all five clients are "
        "clipped, with scales from 0.886 to 0.991 and a clipped norm of exactly 25. Clipping serves two purposes: it bounds the influence of any one "
        "client, which is what the differential-privacy calibration needs, and it equalises the five clients. Its cost is distortion: the "
        "client with the largest raw norm (Healthcare, 28.231) is scaled down by 11.4 percent.")


# ------------------------------------------------------------------------------------------------------------------ algorithm choice
def sec_algorithm_choice(d):
    d.h2("Algorithm Choice and Justification")
    d.p("The central choice is how to remove a client's influence. The table lists the alternatives considered and the reason each was not "
        "adopted; the descriptions come from the cited works and are about the technique in general, not about their reported numbers.")
    d.table([["Alternative", "Idea", "Why it was not used here"],
             ["Retrain from scratch", "Train again on the retained clients", "Exact, but it is the cost that motivates the problem; used only as a reference"],
             ["SISA sharding [12]", "Train shard models and retrain only the shard that held the data", "Needs a different training architecture and an ensemble; no shard structure in a single aggregate"],
             ["Gradient ascent and weight heuristics", "Move the weights away from the data to be forgotten", "No evidence of removal and no clean reference; the batch literature survey lists this as a weakness"],
             ["Certified removal by a Newton step [13]", "One second-order update with noise gives an (epsilon, delta) removal guarantee for convex models", "Needs a convex loss and a Hessian; the proxy has no loss to optimise"],
             ["Influence-based unlearning [14]", "Remove influence with an approximate update and bounded excess risk", "Same requirement of a differentiable empirical risk"],
             ["FedEraser [17]", "Reconstruct the global model from stored historical client updates, calibrated with a few rounds", "Aimed at multi-round training; ForgetSafe aggregates once, so exact subtraction is possible"],
             ["Memorisation pruning [2]", "Reset parameters responsible for memorised content", "Needs a trained deep model and a memorisation metric"],
             ["Federated LLM unlearning [3]", "Unified framework of federated algorithms and unlearning algorithms for LLMs", "Needs an LLM and GPUs; the target of the future back end"]],
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


# ------------------------------------------------------------------------------------------------------------------ model and training
def sec_model_training(d):
    base = metrics("baseline")
    t = base["training"]
    d.h2("Model Architecture and Training")
    d.p("The language model is a character-bigram table: a 33 x 33 matrix of parameters that gives, for each previous character, a "
        "distribution over the next one. It has 1,089 parameters, no hidden layers and no gradient-trained weights. It is not a neural network and "
        "not a language model of the kind that the project title refers to; it is the smallest object that has the properties the federated "
        "unlearning protocol needs (a flat parameter vector, an additive update, a loss that can be measured per record) and runs offline. The "
        "source file says so, and the user interface repeats it in a standing note.")
    d.p("'Training' is correspondingly simple. There are no epochs, no optimiser and no learning rate. One federated round consists of computing "
        f"the five clipped updates, summing them, adding the noise and dividing by five; the default run took {t['train_ms']:.1f} ms. The "
        "configuration is fixed in the engine's constructor and shown in the next table.")
    d.table([["Setting", "Value", "Where set"],
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
             ["Sample length", "180 characters through the API, 120 by default", "`web.py`, `engine.generate()`"]],
            "Configuration of the demonstrator", widths=[0.28, 0.44, 0.28], font=9.5)
    d.h3("Why the default model is noise-dominated")
    d.p("The size of the signal and the noise explains the quality of the default model. Each client contributes at most 9 to a cell, and after "
        "division by five the largest signal in a cell is about 1.8. The noise has standard deviation 75 in the sum and 15 in the model. The model "
        "keeps only the positive part of each parameter and adds 0.15, so each row of the table is dominated by random positive values of mean about "
        "6 (15 divided by the square root of 2 pi) and spread of the same order, and the signal in the 268 non-zero cells is small against them. "
        f"The result on the public set is perplexity {t['perplexity']:.2f} and next-character accuracy {t['next_character_accuracy'] * 100:.2f} percent for "
        "seed 2026; over 50 seeds the perplexity is 142.2 plus or minus 27.5. Section 'Results' of the report shows how this changes with sigma: "
        "useful quality needs sigma of 0.1 or less, where epsilon is 48 or more.")
    d.p("The consequence for the design is that the default values were chosen to make the privacy figure look moderate, not to make the model "
        "useful. The demonstrator is honest about the pipeline and the verification, and the project reports its limits instead of tuning the "
        "defaults to hide them.")


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
    d.table([["Component", "Technology (as declared)", "Purpose"],
             ["Back end", "Python 3.10+ standard library (measured on 3.11.9)", "Engine, model, ledger, HTTP server"],
             ["UI framework", "React 19, React DOM 19", "Pages and components"],
             ["Routing", "React Router 7", "Seven routes: landing, five application pages and a not-found page"],
             ["Build and dev server", "Vite 8, `@vitejs/plugin-react`", "Bundling, hot reload, `/api` proxy"],
             ["Charts", "Recharts 3", "Bar, grouped-bar, line and area charts"],
             ["Motion", "Framer Motion 14, GSAP 3, Lenis", "Page transitions, count-up, smooth scrolling"],
             ["Icons and effects", "lucide-react, canvas-confetti", "Icons"],
             ["Desktop UI", "Tkinter (standard library)", "Original desktop window"]],
            "Technology stack", widths=[0.2, 0.42, 0.38], font=9.5)
    d.p("The front end can also be built for production with `npm run build`; `npm run preview` serves the build on the same port and keeps the "
        "same proxy. The Python server does not serve the React build, so a deployment would need a reverse proxy in front of both. This is "
        "recorded as future work and is not hidden by the run script.")


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
        "returns the HTML error page of the standard library, not a JSON error. Neither affects the main flow.")


# ------------------------------------------------------------------------------------------------------------------ security
def sec_security(d):
    audit = metrics("audit_tamper")
    d.h2("Security and Error Handling")
    d.p("ForgetSafe is a local demonstrator, and its security measures match that role. This section lists what the code does, and then what "
        "it does not do, because the second list matters more to anyone who might reuse the design.")
    d.h3("What the code does")
    d.bullets([
        "**Localhost binding.** The server binds to 127.0.0.1 unless `--host` is given, and the Vite server is bound to 127.0.0.1 too.",
        "**Input checks.** The body size is limited to 1,000,000 bytes, the body must be a JSON object, `client_id` must be present, and an id that "
        "is not one of the five known clients is rejected before any engine state changes. Seed text for generation is normalised to the 33-symbol "
        "alphabet, so it cannot carry markup into the model; a 5,000-character seed was accepted and processed (measured).",
        "**No file serving.** The server has no static-file route, so a path such as `/../../etc/passwd` returns 404 (measured). The ledger path is fixed in code.",
        "**Output escaping.** The legacy page escapes every server value with an `esc()` function before inserting it as HTML; React escapes by default.",
        "**Thread safety.** One re-entrant lock serialises engine access inside a process.",
        "**Failure isolation.** Exceptions are caught per request and returned as JSON; one failing request does not stop the server.",
        "**Tamper evidence.** The ledger detects ordinary edits, deletions and re-ordering.",
    ])
    d.h3("What the code does not do")
    d.table([["Gap", "Consequence"],
             ["No authentication or authorisation", "Anyone who can reach the port can train, remove a client or start a new session; there is no distinction between operator and auditor"],
             ["One global engine", "All callers share one session; a second tab can reset or modify the first user's state"],
             ["No TLS, no rate limit", "Acceptable on localhost, unacceptable on a network"],
             ["Noise reused across releases, no privacy accountant", "Releasing both the pre- and post-removal models would reveal the removed client's update exactly (Section 'Mathematical Formulation'); the certificate repeats the training-time epsilon"],
             ["Updates stored unprotected in memory", "They are the most sensitive artefacts; a real deployment would encrypt them and restrict access"],
             ["Ledger has no signature or external anchor", "Three of seven tampering attacks go undetected: " + "; ".join(a for a in audit["undetected_attacks"])],
             ["No file lock on the ledger", "Two server processes writing the same file could interleave records"],
             ["Error text echoed to the client", "Exception messages, including the unknown client id supplied by the caller, are returned in the JSON error"]],
            "Security gaps of the demonstrator", widths=[0.32, 0.68], font=9.5)
    d.h3("Error handling in the user interface")
    d.p("The front end turns every failed call into a toast that shows the server's message and stays for eight seconds, keeps the page "
        "usable, and offers a retry in the full-page error state when the first state request fails. Buttons are disabled while an action is "
        "running, which prevents double submission, and the unlearning page shows an explanatory empty state when fewer than two clients remain. "
        "These measures handle the user's mistakes; they are not security controls, because the server does not depend on them.")


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
           "python scripts/run_experiments.py               # writes experiments/*/metrics.json\npython scripts/make_charts.py                   # writes docs/charts/*.png",
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
