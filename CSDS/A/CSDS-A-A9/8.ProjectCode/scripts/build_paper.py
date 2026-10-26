"""Build 19.IEEE_Paper.docx (6 pages, two columns) for ForgetSafe at the batch root.

    python scripts/paper_figs.py     # column-width figures (once)
    python scripts/build_paper.py
    python scripts/paper_finish.py   # Word: page count + PDF

Numbers come from experiments/*/metrics.json through doc_common.metrics(); citations are written as [[key,key]] and numbered
here in order of first citation (the base paper is always [1]); the reference list is built from doc_common.REFERENCES.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper_kit as K  # noqa: E402
from doc_common import BATCH, REF, REFERENCES, ROOT, TITLE, metrics  # noqa: E402

FIG = ROOT / "docs" / "paper_figs"

# ------------------------------------------------------------------ numbers
b, s, g, nf, sc, api = (metrics(n) for n in ("baseline", "seeds", "gold_retrain", "noise_free_leakage", "scaling", "api"))
sw = {r["noise_multiplier"]: r for r in metrics("noise_sweep")["rows"]}
dp = metrics("dp_accounting")
seq = metrics("sequential")
syn = metrics("synthetic_corpus")
nn = metrics("neural_adapter")
ld = metrics("load_test")
sp = metrics("security_probe")
ac = metrics("acceptance")
au = metrics("audit_tamper")
t = b["training"]
per = b["unlearning_per_client"]
auc_b0 = sum(c["membership_auc_before"] for c in per) / 5
auc_a0 = sum(c["membership_auc_after"] for c in per) / 5
g3, g05 = g["results"][0], g["results"][1]
nf_ret = sum(r["retention_percent"] for r in nf["rows"]) / 5
unl_row = {r["clients"]: r for r in sc["rows"]}
nns = {r["sigma"]: r for r in nn["summary"]["by_sigma"]}
nbase, nao, ntim = nn["base"], nn["summary"]["adapter_only"], nn["summary"]["timing"]
syn10 = {r["sigma"]: r for r in syn["sweep"]["rows"] if r["n_clients"] == 10}
syn_n = {(r["n_clients"], r["sigma"]): r for r in syn["n_sweep"]["rows"]}
syn_g = {r["sigma"]: r for r in syn["gold"]["results"]}
big = syn["n_sweep"]["unlearning_at_smallest_n"]
cnt = sp["classification_counts"]


def f(x, d=1):
    return f"{x:.{d}f}"


def mean(x):
    return x["mean"] if isinstance(x, dict) else x


def lvl(scn, c):
    return {x["concurrency"]: x for x in ld["scenarios"][scn]["levels"]}[c]


# ------------------------------------------------------------------ citation numbering
order = ["base"]


def C(text: str) -> str:
    def sub(m):
        nums = []
        for key in m.group(1).split(","):
            key = key.strip()
            if key not in order:
                order.append(key)
            nums.append(order.index(key) + 1)
        return "[" + ", ".join(str(n) for n in nums) + "]"
    return re.sub(r"\[\[([a-z, ]+)\]\]", sub, text)


P = K.Paper()
K.TITLE = TITLE
K.ABSTRACT = (
    "Federated language models keep raw data on client devices, yet every client's influence stays in the shared parameters, so a "
    "right-to-be-forgotten request can be met only by retraining or by an unverifiable heuristic. This paper presents ForgetSafe, a "
    "reproducible framework for certified client-level unlearning. Each client's clipped parameter update is tracked; a deletion request "
    "subtracts it from the noisy aggregate, and the result is checked against a retained-only recomputation, a membership-inference attack, "
    "a utility measure and a hash-chained audit ledger, which together issue a certificate. The method is measured on synthetic data with a "
    "bigram proxy, a larger synthetic corpus and LoRA-style adapters of a small neural language model. Removal is exact "
    f"(distance {s['reference_l2']['max']:.0e}) and matches a fresh-noise retrain in distribution; without noise the attack AUC falls from "
    f"{f(nf['mean_auc_before'], 2)} to {f(nf['mean_auc_after'], 2)} and, for adapters, from {f(nns[0.0]['client_auc_before']['mean'], 2)} to "
    f"{f(nns[0.0]['client_auc_after']['mean'], 2)}. The default noise (ε = {f(t['epsilon'], 2)}) leaves the five-client model worse than uniform, "
    "whereas ε < 1 and a useful model coexist once the federation reaches about 1,000 clients. Load, security and acceptance tests expose "
    f"{cnt['defect']} defects in the service."
)
K.KEYWORDS = "audit trail, differential privacy, federated learning, machine unlearning, membership inference, right to be forgotten"
P.front()
P.abstract()

# ================================================================== I. INTRODUCTION
P.h1("I. Introduction")
P.para(C(
    "Machine unlearning for federated large language models (LLMs) is a young field. Following the review method of the base paper "
    "[[base]], which organises a research area into a taxonomy, compares the strengths and limits of each class and states the open gap, this "
    "paper surveys the area (Section II) and then builds and measures a certified-unlearning framework (Sections III and IV). "
    "The base paper reviews sign-language recognition, so only its method, not its subject, is used."))
P.para(C(
    "In federated learning, clients train locally and send only parameter updates to a server [[fedavg]]; parameter-efficient adapters such as "
    "LoRA [[lora]] make this practical for LLMs. Raw text never leaves a client, but the client's influence stays in the shared parameters, "
    "and large models can reproduce training text [[carlini]]. Data-protection law gives individuals a right to erasure [[gdpr]], so a client "
    "may demand that its contribution be removed. Today this is done by retraining from scratch, which is exact but costs a full training run "
    "per request; by retraining only affected shards [[sisa]]; or by approximate weight edits that come with no proof [[federaser]]. Certified "
    "removal exists for convex, centralised models [[certremoval,sekhari]], but a federated pipeline that removes a client, proves the removal and "
    "leaves an audit record that a regulator can check is still missing."))
P.para(
    "The study asks four questions. Does removal by subtraction give the same model as retraining? Does the certificate's own check mean anything? "
    "What do the differential-privacy noise and its bound do to utility and to leakage? And can the audit ledger be trusted? All answers are measured "
    "on synthetic data and can be recomputed on an ordinary PC.")
P.para("The contributions of this work are:", indent=True, after=1)
P.numbered([
    "a tracked-update workflow: clipped client updates are stored, and removal is the subtraction of one stored update, with no raw data and no retraining;",
    "a verification stack that issues a certificate per request: retained-only recomputation, a loss-based membership attack, utility retention and a SHA-256-chained ledger;",
    "an evaluation that tests the certificate itself on three models (a bigram proxy, a larger synthetic corpus and LoRA-style neural adapters) with fresh-noise retraining, noise-free attacks, a noise sweep and an audit-tamper matrix;",
    "measurements of the service (load, concurrency, 58 hostile requests, scripted acceptance) and of the federation size at which ε < 1 and a useful model coexist.",
])
P.para("Section II surveys related work, Section III describes the method, Section IV reports measurements and Section V concludes.", after=2)
P.h2("A. System Hardware")
P.para("All measurements ran on one workstation: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11 Pro. No GPU was used.", after=1)
P.h2("B. Software Requirements")
P.para("The engine and server use only the Python 3.11.9 standard library (http.server, hashlib, unittest); the neural study uses PyTorch 2.14 (CPU). The "
       "interface is React 19 with Vite 8 and Recharts on Node.js 24.19; screens and acceptance runs use Playwright in Chrome.", after=2)

# ================================================================== II. LITERATURE SURVEY
P.h1("II. Literature Survey")
P.h2("A. Base Paper")
P.para(C(
    "Khan et al. [[base]] review deep-learning approaches to continuous sign language recognition (IEEE Access, 2025). They organise "
    "the studies into a taxonomy covering sign language, data collection, input method, gesture signals, identification methods and datasets, "
    "split the models into spatial, temporal and alignment approaches with their benefits and drawbacks, and close with challenges such as "
    "real-time processing, dataset diversity and signer variability. Its subject is unrelated to unlearning, so it offers no result that "
    "ForgetSafe could be compared with; what is taken from it is the taxonomy, compare, find-the-gap method used in this section."))
P.h2("B. Related Work")
P.para(C(
    "*Exact and sharded removal.* Cao and Yang [[caoyang]] make a learner forget by updating the sums it is built from, and SISA training "
    "[[sisa]] confines retraining to the shard that held the data. *Certified removal.* Guo et al. [[certremoval]] remove a point from a "
    "convex model with a Newton step plus noise and an (ε, δ) guarantee; Sekhari et al. [[sekhari]] bound how many deletions "
    "a learner can absorb. *Federated unlearning.* FedEraser [[federaser]] keeps the clients' historical updates on the server and "
    "calibrates them to rebuild a model without one client, the idea ForgetSafe reduces to its simplest form. A recent survey "
    "[[investigation]] compares FedEraser, FedCIO, FedRecovery and F2UL, finds a trade-off between removal precision and cost, and calls "
    "for standard evaluation metrics. *Recent systems.* FedMemPrune [[memprune]] argues that unlearning should remove only the information "
    "unique to the forgotten data and resets the parameters that memorise it. Oblivionis [[oblivionis]] unifies federated learning and "
    "unlearning for LLMs and compares six federated and five unlearning algorithms. FedORA [[fedora]] casts removal in vertical federated "
    "learning as a primal-dual problem with a bound to retraining. *Privacy tools.* The Gaussian mechanism [[dwork]] and its tighter "
    "calibration [[balle]] give the (ε, δ) bounds, and loss-based membership inference [[shokri,yeom]] is the standard empirical check. "
    "Three further items of the project's literature list could not be retrieved and are not used."))
P.para(C(
    "*Strengths and limits.* Retraining and sharding give exact removal, but cost grows with model size and request rate. Certified removal gives a "
    "formal guarantee, but only for convex models. Historical-update methods are cheap but approximate. The memorisation-aware and primal-dual methods "
    "target neural networks and report agreement with retraining on benchmarks, not a per-request proof, and the LLM framework [[oblivionis]] concentrates on "
    "measuring forgetting and utility rather than on evidence a regulator can check. A differential-privacy statement describes a release "
    "mechanism and says nothing about forgetting unless the noise and the accounting are handled again after the removal."))
P.table([
    ["Work", "Approach", "Data", "Reported result", "Limitation"],
    [C("Khan [[base]]"), "Taxonomy review of sign-language models", "Sign-language datasets", "None on unlearning", "Unrelated subject; method only"],
    [C("FedMemPrune [[memprune]]"), "Prune parameters that memorise", "CIFAR-10/100, EMNIST", "Close to retraining baselines", "Image models, not LLMs"],
    [C("Oblivionis [[oblivionis]]"), "FL + unlearning framework, 6 + 5 algorithms", "Llama-2/3 models; TOFU, MUSE", "Beats local training; balance of forgetting and utility", "No audit or certificate stage described"],
    [C("FedORA [[fedora]]"), "Primal-dual removal, bound to retrain", "Five tabular and image sets (vertical FL)", "Comparable to retraining at lower cost", "Vertical FL; no audit record"],
    [C("Zhang survey [[investigation]]"), "Review of FedEraser, FedCIO, FedRecovery, F2UL", "Review (no new data)", "Precision-cost trade-off", "Review only; no system"],
    [C("Guo [[certremoval]]"), "Newton step + noise", "Convex models", "(ε, δ) removal guarantee", "Not federated, not LLM"],
    ["ForgetSafe (this work)", "Tracked-update subtraction + certificate + ledger", "Synthetic: 5 bigram clients; 20-domain corpus; 8 neural-adapter clients", "Exact removal; certificate tested (Sec. IV)", "Linear one-round aggregate; small models"],
], "Related work compared", [0.2, 0.22, 0.18, 0.2, 0.2], size=6.5)
P.para(C(
    "*Gap.* The works above remove influence heuristically, with an empirical or a convex-model guarantee; none ties a federated removal to "
    "a certificate, an independent check and a tamper-evident record, and none asks whether such a certificate is itself sound. "
    "ForgetSafe provides the first and tests the second. The project's survey lists the same practice and its limits: full retraining is too "
    "expensive for large federated LLMs, heuristics give no formal guarantee, sharding adds complexity, differentially private training costs utility, "
    "and unlearning is mostly neither verifiable nor auditable. Those limits frame the four questions in Section I."), indent=True)

# ================================================================== III. METHODOLOGY
P.h1("III. Methodology")
P.h2("A. Pipeline")
P.para(
    "Fig. 1 shows the system and Fig. 2 the main flow. A Python standard-library server (port 8109) holds one engine; a React interface "
    "(port 5109) calls nine JSON endpoints. Training builds the noisy global model; an unlearning request removes one client and runs the checks; "
    "every training and unlearning event is appended to the ledger.")
P.figure(FIG / "fig1_architecture.png", "ForgetSafe architecture: React interface, standard-library server, engine, model and hash-chained ledger.", 3.2)
P.figure(FIG / "fig2_flow.png", "Main flow: train, unlearn, two checks, certificate status.", 3.0)
P.h2("B. Data and Models")
P.para(
    "*Bigram proxy.* Five simulated clients (Finance, Healthcare, Education, Retail, Travel) hold five hand-written sentences each; five "
    "public sentences measure utility and five unseen sentences serve as non-members. Text is lower-cased to a 33-symbol alphabet. A client's update u is the vector "
    "of its 33 × 33 = 1,089 bigram counts, and the next-character distribution is P(c′|c) ∝ max(0, θ[c, c′]) + 0.15.")
P.para(C(
    "*Synthetic corpus.* A seeded template grammar with 20 domains gives each client 200 training and 200 held-out sentences and a 300-sentence public set; the "
    "engine classes run unchanged. A raw update of such a client has norm about "
    f"{syn['raw_norms']['median']:,.0f}, so C = 25 would shrink it {syn['raw_norms']['ratio_median_norm_to_C25']:.0f}-fold; C is set to the median norm. The "
    "domain-level attack scores a client's training sentences against other clients' held-out sentences; the sample-level attack uses its own held-out sentences."))
P.para(C(
    f"*Neural adapters.* A character-level GRU ({nbase['base_parameters']:,} parameters) is pre-trained on a synthetic public pool and frozen. Each of eight synthetic clients "
    f"trains a rank-{nbase['adapter_rank']} LoRA-style adapter [[lora]] ({nbase['adapter_dimension']:,} parameters) on 150 sentences of its own grammar and vocabulary. "
    "The adapter vectors are clipped at the median raw norm (C ≈ 13), summed, noised and divided by n exactly as the bigram counts are, and removal subtracts "
    "the stored adapter."))
P.h2("C. Formulation")
P.para("With clip norm C, noise multiplier σ and n clients, training releases", indent=True, after=0, keep=True)
P.eq("û_{i} = u_{i} · min(1, C / ||u_{i}||)", 1)
P.eq("θ = ( Σ_{i} û_{i} + z ) / n,   z ~ N(0, σ²C² I)", 2)
P.eq("ε = √(2 ln(1.25/δ)) / σ,   δ = 1e-5", 3)
P.para("giving ε = " + f(t["epsilon"], 3) + " at C = 25, σ = 3. A request for client j stores nothing new and computes", indent=False, after=0, keep=True)
P.eq("θ_{−j} = ( Σ_{i} û_{i} + z − û_{j} ) / (n − 1)", 4)
P.eq("Δ_{j} = || θ_{−j} − ( z + Σ_{i≠j} û_{i} ) / (n − 1) ||₂ ≤ 1e-10", 5)
P.para(
    "Because the aggregate is linear, Δ is zero up to rounding: the certificate's reference check is an identity, not an independent "
    "retrain, since it reuses the stored noise z. The status is CERTIFIED only if Δ passes and utility retention stays at or above 70 %, where "
    "utility = 0.65·accuracy + 0.35/(1 + ln(1 + perplexity)) and retention is the ratio after to before.", indent=False)
P.h2("D. Why This Algorithm")
P.para(C(
    "Subtracting a stored update needs no raw data, costs O(d) in the parameter count d, and is exact for a linear aggregate; the price is that the server "
    "must store every client's clipped update, itself a sensitive artefact. For multi-round nonlinear fine-tuning an update influences later updates, so exact "
    "subtraction no longer holds and methods such as [[federaser,memprune]] become necessary. Adding or removing one client changes Σû by at most C in L2, "
    "so noise of standard deviation σC per coordinate is the Gaussian mechanism [[dwork]] with sensitivity C, and (3) is its classical calibration, formally "
    "valid only for ε < 1. The unlearned model reuses z: it is a second function of the same noisy release, not a fresh one, so ε in (3) is reported unchanged "
    "after a removal and is not, by itself, a statement about forgetting."))
P.h2("E. Verification, Algorithms and Audit")
P.para(C(
    "The attack scores a text by its negative loss and reports an AUC [[shokri,yeom]]; 0.5 means no leakage. Each ledger record stores the SHA-256 of the previous hash "
    "and its canonical JSON, so verification re-walks the chain. A certificate has 25 fields, among them status, ε, δ, C, σ, the reference distance, the attack AUC, "
    "perplexity and accuracy before and after, retention, model hashes and the hash of its own ledger record."))
P.eq("h_{k} = SHA-256( h_{k−1} | canonical(r_{k}) ),   h_{0} = 64 zeros", 6)
P.para(
    "*Training:* count and clip each client's update, store it with its raw norm, draw z once from the session seed, keep S = Σû + z, release θ = S/n and "
    "append a FEDERATED_TRAINING record. *Unlearning client j:* reject if untrained, unknown, already removed or last; measure metrics and attack; set "
    "S ← S − û_j and θ ← S/(n − 1); measure again; compute Δ; set the status; append a CLIENT_UNLEARNING record holding every certificate field; return the "
    "certificate. The server is trusted to hold the updates; malicious clients, secure aggregation and an adversary with write access to the ledger file are out of scope.")
P.h2("F. Evaluation Protocol")
P.para(
    "Every experiment runs the real engine on a throw-away ledger with seeded randomness. *Bigram proxy:* 50 seeds × 5 clients (250 requests); 12 noise values "
    "(20 seeds); 200 fresh-retrain pairs at σ = 3 and 0.5; a noise-free run; scaling from 5 to 500 synthetic clients; seven ledger edits. *Synthetic corpus:* "
    "n = 5, 10, 20 clients, σ from 1e-9 to 10 (10 seeds × 5 targets); n up to 4,000 for the ε < 1 question. *Neural adapters:* 8 clients, 9 noise values, 5 seeds. "
    "*Service:* 1 to 64 concurrent clients, three race tests, a 2,000-request soak, 58 hostile or malformed requests and 20 scripted synthetic-user browser journeys.")

# ================================================================== IV. RESULTS
P.h1("IV. Results")
P.para(
    f"*Conditions.* Default configuration is seed 2026, C = 25, σ = 3, δ = 1e-5 on the bigram proxy; seed studies use {s['n_seeds']} seeds × 5 clients "
    f"({s['n_unlearning_requests']} requests). Perplexity is on public sentences (5 for the proxy); AUC rows for the corpus and adapters are domain or client level. "
    "A model is 'destroyed' when its perplexity exceeds 1e8.")


def row(label, eps, ppl, acc, a_b, a_a, ret):
    return [label, eps, ppl, acc, f"{a_b} → {a_a}", ret]


rows2 = [["Setting", "ε", "Perplexity", "Accuracy", "AUC before → after", "Retention %"]]
rows2.append(row("Default, seed 2026 (n = 5)", f(t["epsilon"], 2), f(t["perplexity"]), f(100 * t["next_character_accuracy"]) + " %", f(auc_b0, 2), f(auc_a0, 2), f(b["mean_retention_percent"])))
rows2.append(row("Default, 50 seeds (250 requests)", f(t["epsilon"], 2), f(s["pre_unlearning_perplexity"]["mean"]) + "±" + f(s["pre_unlearning_perplexity"]["sd"], 0),
                 f(100 * s["pre_unlearning_accuracy"]["mean"]) + " %", f(s["membership_auc_before"]["mean"], 2), f(s["membership_auc_after"]["mean"], 2), f(s["utility_retention_percent"]["mean"])))
for sg in (0.1, 4.85):
    r = sw[sg]
    rows2.append(row(f"Bigram σ = {sg:g} (20 seeds)", f(r["epsilon"], 2 if r["epsilon"] < 10 else 1), f(r["perplexity"]["mean"]), f(100 * r["accuracy"]["mean"]) + " %",
                     f(r["membership_auc_before"]["mean"], 2), f(r["membership_auc_after"]["mean"], 2), f(r["retention_percent"]["mean"])))
rows2.append(row("Bigram, noise-free σ = 1e-6", "≈ 5e6", f(nf["rows"][0]["perplexity_before"]), "n/a", f(nf["mean_auc_before"], 2), f(nf["mean_auc_after"], 2), f(nf_ret)))
r = syn10[0.1]
rows2.append(row("Corpus n = 10, σ = 0.1", f(r["epsilon"], 1), f(r["ppl_before"]["mean"]), f(100 * r["acc_before"]["mean"]) + " %",
                 f(r["auc_other_before"]["mean"], 2), f(r["auc_other_after"]["mean"], 2), f(mean(r["retention"]))))
r = syn_n[(1000, 4.85)]
b1 = big["sequential_removals"][0]
rows2.append(row("Corpus n = 1,000, σ = 4.85", f(big["epsilon"], 3), f(r["perplexity"]["mean"]), f(100 * r["accuracy"]["mean"]) + " %",
                 f(b1["auc_other_before"], 2), f(b1["auc_other_after"], 2), f(b1["retention_percent"], 3)))
for sg, lab in ((0.0, "Adapters σ = 0"), (0.05, "Adapters σ = 0.05"), (0.1, "Adapters σ = 0.1")):
    r = nns[sg]
    rows2.append(row(f"{lab} (n = 8)", "∞" if sg == 0 else f(r["epsilon"], 1), f(mean(r["retained_ppl_before"])), f(100 * mean(r["retained_acc_before"])) + " %",
                     f(mean(r["client_auc_before"]), 2), f(mean(r["client_auc_after"]), 2), f(mean(r["retention_retained_ppl_percent"]))))
r = nns[0.3]
rows2.append(row("Adapters σ ≥ 0.3", "≤ 16", "destroyed", f"≤ {f(100 * mean(r['retained_acc_before']))} %", f(mean(r["client_auc_before"]), 2), f(mean(r["client_auc_after"]), 2), "n/a"))
P.table(rows2, "Measured unlearning results (mean over requests; adapter rows use retained-client perplexity and client-level AUC)", [0.31, 0.09, 0.14, 0.13, 0.19, 0.14], size=6.3)
P.figure(FIG / "fig3_results.png", "(a) Perplexity and attack AUC against the noise multiplier (bigram, 20 seeds). (b) L2 distance of the unlearned model to a fresh-noise retrain and between two retrains (200 pairs).", 3.4)
P.para(
    f"*Removal and utility.* On the proxy, removal is exact to {s['reference_l2']['max']:.1e} and all {s['n_unlearning_requests']} requests are certified. Retention averages "
    f"{f(s['utility_retention_percent']['mean'])} % (minimum {f(s['utility_retention_percent']['min'])} %); removing four of five clients raises perplexity from "
    f"{f(t['perplexity'], 0)} to {f(seq['steps'][4]['perplexity'], 0)} because the noise stays while the signal is divided by fewer clients, every step is certified, and the fifth "
    "removal is refused. With five members and five non-members one pair moves the AUC by 0.04, so the per-client AUC values at the default seed (0.04 to 0.48 before removal) carry no information.")
P.para(
    f"*The default model is noise-dominated.* The noise has standard deviation {dp['noise_std_per_coordinate_default']:.0f} per coordinate against a clipped update of norm 25 "
    f"spread over 1,089 coordinates. Perplexity is {f(s['pre_unlearning_perplexity']['mean'], 0)}, worse than the uniform model's 32, accuracy is "
    f"{f(100 * s['pre_unlearning_accuracy']['mean'])} %, and the attack is at chance before removal (AUC {f(s['membership_auc_before']['mean'], 2)} ± {f(s['membership_auc_before']['sd'], 2)}), so there is "
    f"nothing for removal to remove. On five clients, useful models need σ ≤ 0.1 (ε ≥ 48), whereas the classical bound is valid only for ε < 1 (σ > {f(dp['sigma_needed_for_epsilon_below_1'], 3)}), "
    f"where perplexity is 198 or more. Because retention is measured against a model that is already near-useless, the 70 % floor cannot fail at σ = 3; it failed once in the sweep, at σ = 0.3.")
P.para(
    f"*Is the removal real?* Without noise the attack separates members almost perfectly (AUC {f(nf['mean_auc_before'], 2)}) and removal brings it to "
    f"{f(nf['mean_auc_after'], 2)} with {f(nf_ret)} % retention. Against a true retrain with fresh noise the unlearned model lies "
    f"{f(g3['l2_unlearned_vs_fresh_retrain']['mean'], 0)} away at σ = 3 ({f(g05['l2_unlearned_vs_fresh_retrain']['mean'], 0)} at σ = 0.5), the same as two independent retrains "
    f"({f(g3['l2_fresh_retrain_vs_fresh_retrain']['mean'], 0)} and {f(g05['l2_fresh_retrain_vs_fresh_retrain']['mean'], 0)}): the distance is pure noise, so the unlearned model is distributed like a "
    "retrained one, which the 1e-14 certificate value alone does not show.")
P.figure(FIG / "fig4_certificate.png", "Output screen: certificate for Client 01 (Finance), ε 1.6149, AUC 0.200 → 0.160, retention 93.65 %.", 3.4)
P.figure(FIG / "fig5_audit.png", "Output screen: compliance ledger, chained records and a valid hash chain.", 3.4)
P.para(
    f"*Larger data and neural adapters.* With 200 sentences per client the bigram model still does not memorise sentences (sample-level AUC 0.50 at every σ) but leaks the domain: "
    f"the attack falls from {f(syn10[1e-9]['auc_other_before']['mean'], 3)} to {f(syn10[1e-9]['auc_other_after']['mean'], 3)} on removal without noise and from "
    f"{f(syn10[0.1]['auc_other_before']['mean'], 3)} to {f(syn10[0.1]['auc_other_after']['mean'], 3)} at σ = 0.1, and unlearned and fresh-retrain models are {f(syn_g[0.1]['l2_unlearned_vs_fresh_retrain']['mean'], 0)} and "
    f"{f(syn_g[0.1]['l2_fresh_retrain_vs_fresh_retrain']['mean'], 0)} apart. Since the noise is added once to the sum and divided by n, a large federation dilutes it: at σ = 4.85 (ε = {f(big['epsilon'], 3)}) "
    f"perplexity is {f(syn_n[(1000, 4.85)]['ratio_to_noise_free'], 2)} times the noise-free value at n = 1,000 clients and {f(syn_n[(4000, 4.85)]['ratio_to_noise_free'], 2)} at 4,000 (Fig. 6a), against "
    f"{f(syn_n[(5, 4.85)]['ratio_to_noise_free'], 0)} at n = 5, and five sequential removals at n = 1,000 are certified. For the neural adapters a single adapter is plainly attackable "
    f"(client-level AUC {f(nao['client_auc']['mean'], 2)}, sample-level {f(nao['sample_auc']['mean'], 2)}); the released average hides samples but not the domain "
    f"({f(nns[0.0]['client_auc_before']['mean'], 2)}), and removal returns the attack to {f(nns[0.0]['client_auc_after']['mean'], 2)}, equal to a fresh retrain ({f(nns[0.0]['client_auc_retrain']['mean'], 2)}), with "
    f"unlearned-to-retrain distance equal to retrain-to-retrain at every σ ({f(nns[0.1]['l2_unl_vs_retrain']['mean'], 1)} and {f(nns[0.1]['l2_retrain_vs_retrain']['mean'], 1)} at σ = 0.1). Retention is "
    f"{f(mean(nns[0.0]['retention_retained_ppl_percent']), 1)} % at σ = 0, {f(mean(nns[0.05]['retention_retained_ppl_percent']), 0)} % at 0.05 and {f(mean(nns[0.1]['retention_retained_ppl_percent']), 0)} % at 0.1 (below the floor, so "
    f"REVIEW_REQUIRED), and the models are destroyed from σ = 0.3 (Fig. 6b). Subtracting an adapter takes {f(ntim['subtract_us_median'], 0)} µs, the fully checked request {f(ntim['unlearn_with_metrics_ms_median'], 0)} ms, "
    f"and retraining the seven retained adapters {f(ntim['retrain_seven_adapters_s_median'], 1)} s.")
P.figure(FIG / "fig6_scale.png", "(a) Perplexity relative to the noise-free model against federation size (synthetic corpus). (b) Client-level attack AUC against σ for neural adapters.", 3.4)
P.para(
    f"*Audit, service and tests.* The ledger detects an edited field, a flipped status, a deleted record and swapped records, but not tail truncation, a re-hashed forgery or an appended forged record, "
    f"and an emptied ledger verifies as valid; an append re-reads the file ({f(sc['ledger_append_ms_at_length']['1'], 2)} ms at one record, {f(sc['ledger_append_ms_at_length']['2000'], 1)} ms at 2,000). "
    f"On the proxy, unlearning ({f(unl_row[5]['unlearn_ms_median'], 0)} ms) is slower than re-running the training ({f(unl_row[5]['full_retrain_ms_median'], 0)} ms) with 5 clients and "
    f"{f(unl_row[500]['speedup_retrain_over_unlearn'], 1)} times faster at 500. The five unit tests and 14 smoke checks pass. From 1 to 64 concurrent clients the server returns no 5xx error at "
    f"up to 8 clients; at 16 to 64 a handful of requests fail (at most {max(lvl('GET /api/state', 64)['errors_5xx_or_connection'], lvl('POST /api/generate', 64)['errors_5xx_or_connection'])} of 500), "
    f"and /api/state saturates near {f(lvl('GET /api/state', 16)['requests_per_s'], 0)} requests/s because it re-reads the ledger. 32 simultaneous removals of one client yield exactly one success, 16 simultaneous "
    f"trainings write 16 valid records, and a {ld['soak']['requests']:,}-request soak has no error. Of {sp['n_probes']} hostile or malformed requests {cnt['handled']} are handled, {cnt['noteworthy']} behave noteworthily and "
    f"{cnt['defect']} are defects: no read timeout and a negative Content-Length block a thread, a cross-site POST and a forged Host header are accepted, burst connections are refused, a corrupt "
    "ledger line breaks the interface, and no endpoint is authenticated. All "
    f"{ac['journeys']} scripted synthetic-user journeys in Chrome ({ac['desktop_journeys']} desktop, {ac['mobile_journeys']} phone, {ac['dark_mode_journeys']} dark mode; {ac['total_certificates_checked']} certificates) pass with no console error; "
    "this is a scripted test, not a human study.")
P.para(C(
    "*Comparison.* The base paper [[base]] reports no comparable metric. FedMemPrune [[memprune]], Oblivionis [[oblivionis]] and FedORA [[fedora]] use image, "
    "benchmark-LLM and vertical-federated data with neural models, so none of the numbers above is comparable with theirs; the comparison is qualitative: "
    "ForgetSafe is exact because its aggregate is linear and single-round, whereas those works handle nonlinear networks, and it adds a per-request certificate and a "
    "tamper-evident ledger."))

# ================================================================== V. CONCLUSION
P.h1("V. Conclusion")
P.para(
    "ForgetSafe meets its six objectives at the scale it was built for. Federated aggregation runs across five bigram clients and eight clients fine-tuning LoRA-style adapters of a "
    f"{nbase['base_parameters'] // 1000}k-parameter GRU; removal needs no retraining ({f(ntim['subtract_us_median'], 0)} µs for an adapter against {f(ntim['retrain_seven_adapters_s_median'], 1)} s); the (ε, δ) bound is reported, but at the default "
    "σ it lies outside the classical range, the noise is reused, no accountant exists, and ε < 1 with a useful model needs about 1,000 clients; the membership attack and the fresh-noise "
    f"retrain agree on all three models; retention is {f(s['utility_retention_percent']['mean'])} % at the default and {f(mean(nns[0.0]['retention_retained_ppl_percent']), 1)} % for adapters without noise; and every event is chained, with the "
    "blind spots and service defects measured above. The key finding is that the certificate proves the exactness of the arithmetic, not forgetting: the noise-free, fresh-noise and "
    "domain-level experiments supply that evidence. The study covers a 137k-parameter GRU on synthetic data in one aggregation round on one CPU workstation, and makes no claim "
    "about larger pretrained LLMs or multi-round training.")
P.para(C(
    "Future work: draw fresh noise or keep a privacy accountant [[balle]] after each removal; sign and externally anchor the ledger and add authentication, request timeouts "
    "and origin checks; extend the adapters to a pretrained language model over several rounds [[lora]]; and test stronger membership attacks. In short, removal by subtraction equals "
    "the retained-only aggregate exactly and a fresh retrain in distribution, the certificate's own check is an identity, the default noise removes the leakage and the utility together, "
    "and the ledger resists casual edits but not an adversary who can rewrite the file."))

# ================================================================== references
K.REFS = [REFERENCES[REF[k] - 1] for k in order]
P.references()
out = BATCH / "19.IEEE_Paper.docx"
P.d.core_properties.author = "Batch A9"
P.d.core_properties.title = TITLE
P.d.save(str(out))
print("saved", out.name, "| references:", len(K.REFS), "| order:", order)
