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
au = metrics("audit_tamper")
dp = metrics("dp_accounting")
seq = metrics("sequential")
t = b["training"]
per = b["unlearning_per_client"]
auc_b0 = sum(c["membership_auc_before"] for c in per) / 5
auc_a0 = sum(c["membership_auc_after"] for c in per) / 5
g3, g05 = g["results"][0], g["results"][1]
lat = api["latency"]
unl_row = {r["clients"]: r for r in sc["rows"]}
nf_ret = sum(r["retention_percent"] for r in nf["rows"]) / 5


def f(x, d=1):
    return f"{x:.{d}f}"


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
    "reproducible demonstrator of certified client-level unlearning for federated language models. Each client's clipped parameter update "
    "is tracked; a deletion request subtracts that update from the noisy aggregate, and the result is checked against a retained-only "
    "recomputation, a membership-inference attack, a utility measure and a hash-chained audit ledger, which together issue a certificate. "
    "The model is a character-bigram proxy for an LLM adapter, trained on 25 sentences held by five simulated clients. Over 250 requests, "
    f"removal is exact by construction (distance {s['reference_l2']['max']:.0e}) and utility retention is {f(s['utility_retention_percent']['mean'])} %, "
    f"but the default noise leaves the model worse than a uniform one (perplexity {f(s['pre_unlearning_perplexity']['mean'], 0)}) and the attack at chance "
    f"(AUC {f(s['membership_auc_before']['mean'], 2)}). Without noise, attack AUC falls from {f(nf['mean_auc_before'], 2)} to {f(nf['mean_auc_after'], 2)} after removal. "
    "We report these limits, the audit ledger's blind spots and the route to real LLM adapters."
)
K.KEYWORDS = "audit trail, differential privacy, federated learning, machine unlearning, membership inference, right to be forgotten"
P.front()
P.abstract()

# ================================================================== I. INTRODUCTION
P.h1("I. Introduction")
P.para(C(
    "Machine unlearning for federated large language models (LLMs) is a young field. Following the review method of the base paper "
    "[[base]], which organises a research area into a taxonomy, compares the strengths and limits of each class and states the open gap, this "
    "paper surveys the area (Section II) and then builds and measures a small certified-unlearning framework (Sections III and IV). "
    "The base paper itself reviews sign-language recognition, so only its method, not its subject, is used."))
P.para(C(
    "In federated learning, clients train locally and send only parameter updates to a server [[fedavg]]; parameter-efficient adapters such as "
    "LoRA [[lora]] make this practical for LLMs. Raw text never leaves a client, but the client's influence stays in the shared parameters, "
    "and large models can reproduce training text [[carlini]]. Data-protection law gives individuals a right to erasure [[gdpr]], so a client "
    "may demand that its contribution be removed. Today this is done in one of three ways: retraining from scratch, which is exact but "
    "costs a full training run per request; retraining only affected shards [[sisa]]; or approximate weight edits that come with no proof "
    "[[federaser]]. Certified removal exists for convex, centralised models [[certremoval,sekhari]], but a federated pipeline that removes "
    "a client, proves the removal and leaves an audit record that a regulator can check is still missing."))
P.para(
    "The study asks four questions. Does removal by subtraction give the same model as retraining? Does the certificate's own check mean anything? "
    "What do the differential-privacy noise and its bound do to utility and to leakage? And can the audit ledger be trusted by a regulator? "
    "The answers are measured on a small, fully reproducible system, so that every number can be recomputed in minutes on an ordinary PC.")
P.para("The contributions of this work are:", indent=True, after=1)
P.numbered([
    "a tracked-update workflow: clipped client updates are stored, and removal is the subtraction of one stored update, with no raw data and no retraining;",
    "a verification stack that issues a certificate per request: retained-only recomputation, a loss-based membership attack, utility retention and a SHA-256-chained ledger;",
    "an evaluation that tests the certificate itself (50 seeds, a noise sweep, a fresh-noise retrain comparison, a noise-free attack and an audit-tamper matrix);",
    "a plain account of what is not shown: the model is a bigram proxy, the default noise swamps the signal, and the ledger has blind spots.",
])
P.para("Section II surveys related work, Section III describes the method, Section IV reports measurements and Section V concludes.", after=2)
P.h2("A. System Hardware")
P.para("All measurements ran on one workstation: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11 Pro. No GPU was used.", after=1)
P.h2("B. Software Requirements")
P.para("The backend uses only the Python 3.11.9 standard library (http.server, hashlib, unittest). The interface is React 19 with Vite 8 and "
       "Recharts on Node.js 24.19; screens were captured with Playwright in Chrome.", after=2)

# ================================================================== II. LITERATURE SURVEY
P.h1("II. Literature Survey")
P.h2("A. Base Paper")
P.para(C(
    "Khan et al. [[base]] review deep-learning approaches to continuous sign language recognition (IEEE Access, 2025, 21 pages). They organise "
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
    "calibrates them to rebuild a model without one client, which is the idea ForgetSafe reduces to its simplest form. A recent survey "
    "[[investigation]] compares FedEraser, FedCIO, FedRecovery and F2UL and finds a trade-off between removal precision and cost, and calls "
    "for standard evaluation metrics. *Recent systems.* FedMemPrune [[memprune]] argues that unlearning should remove only the information "
    "unique to the forgotten data and resets the parameters that memorise it. Oblivionis [[oblivionis]] unifies federated learning and "
    "unlearning for LLMs and compares six federated and five unlearning algorithms. FedORA [[fedora]] casts removal in vertical federated "
    "learning as a primal-dual problem with a bound to retraining. *Privacy tools.* The Gaussian mechanism [[dwork]] and its tighter "
    "calibration [[balle]] give the (ε, δ) bounds, and loss-based membership inference [[shokri,yeom]] is the standard empirical check. "
    "Three further items of the project's literature list could not be retrieved and are not used."))
P.para(C(
    "*Strengths and limits.* Retraining and sharding give exact removal, but their cost grows with model size and request rate. Certified removal gives a "
    "formal guarantee, but only for convex models. Historical-update methods are cheap but approximate. The memorisation-aware and primal-dual methods "
    "target neural networks and report agreement with retraining on benchmarks, not a per-request proof, and the LLM framework [[oblivionis]] concentrates on measuring "
    "forgetting and utility rather than on evidence a regulator can check. The survey [[investigation]] names the needs that remain open: standard "
    "metrics, efficiency and non-IID data. The privacy literature adds a warning that matters here: a differential-privacy statement describes a release "
    "mechanism, and it says nothing about forgetting unless the noise and the accounting are handled again after the removal."))
P.table([
    ["Work", "Approach", "Data", "Reported result", "Limitation"],
    [C("Khan [[base]]"), "Taxonomy review of sign-language models", "Sign-language datasets", "None on unlearning", "Unrelated subject; method only"],
    [C("FedMemPrune [[memprune]]"), "Prune parameters that memorise", "CIFAR-10/100, EMNIST", "Close to retraining baselines", "Image models, not LLMs"],
    [C("Oblivionis [[oblivionis]]"), "FL + unlearning framework, 6 + 5 algorithms", "Llama-2/3 models; TOFU, MUSE", "Beats local training; balance of forgetting and utility", "No audit or certificate stage described"],
    [C("FedORA [[fedora]]"), "Primal-dual removal, bound to retrain", "Five tabular and image sets (vertical FL)", "Comparable to retraining at lower cost", "Vertical FL; no audit record"],
    [C("Zhang survey [[investigation]]"), "Review of FedEraser, FedCIO, FedRecovery, F2UL", "Review (no new data)", "Precision-cost trade-off", "Review only; no system"],
    [C("Guo [[certremoval]]"), "Newton step + noise", "Convex models", "(ε, δ) removal guarantee", "Not federated, not LLM"],
    ["ForgetSafe (this work)", "Tracked-update subtraction + certificate + ledger", "25 sentences, 5 clients", "Exact removal; certificate tested (Sec. IV)", "Bigram proxy; noise-dominated default"],
], "Related work compared", [0.2, 0.22, 0.18, 0.2, 0.2], size=6.5)
P.para(C(
    "*Gap.* The works above remove influence heuristically, with an empirical or a convex-model guarantee; none ties a federated removal to "
    "a certificate, an independent check and a tamper-evident record, and none asks whether such a certificate is itself sound. "
    "ForgetSafe addresses the first part at demonstrator scale and the second part by testing its own certificate. The project's own survey lists "
    "the same existing practice and its limits: full retraining is too expensive for large federated LLMs, gradient-ascent or weight-adjustment heuristics give no "
    "formal guarantee, sharded training adds architectural complexity, differentially private training limits individual influence but costs utility, "
    "and unlearning is generally not verifiable or auditable for a regulator and mostly targets centralised rather than federated LLM models. Those five limits frame the four questions in Section I."), indent=True)

# ================================================================== III. METHODOLOGY
P.h1("III. Methodology")
P.h2("A. Pipeline")
P.para(
    "Fig. 1 shows the system and Fig. 2 the main flow. A Python standard-library server (port 8109) holds one engine; a React interface "
    "(port 5109) calls nine JSON endpoints: health, state, train, session, unlearn, generate, audit verify, latest certificate and the legacy page. "
    "Training builds the noisy global model; an unlearning request removes one client and runs the checks; every training and unlearning event is "
    "appended to the ledger.")
P.figure(FIG / "fig1_architecture.png", "ForgetSafe architecture: React interface, standard-library server, engine, model and hash-chained ledger.", 3.2)
P.figure(FIG / "fig2_flow.png", "Main flow: train, unlearn, two checks, certificate status.", 3.0)
P.h2("B. Data and Model")
P.para(
    "Five simulated clients (Finance, Healthcare, Education, Retail, Travel) hold five hand-written sentences each, 25 records in all; five "
    "public sentences measure utility and five unseen sentences serve as non-members. No external dataset is used. Text is lower-cased to a "
    "33-symbol alphabet with start and end markers. The model is a character bigram: a client's update u is the vector of its 33 × 33 = 1,089 "
    "bigram counts, standing in for an LLM adapter update, and the next-character distribution is P(c′|c) ∝ max(0, θ[c, c′]) + 0.15.")
P.h2("C. Formulation")
P.para("With C = 25, noise multiplier σ = 3 and n clients, training releases", indent=True, after=0, keep=True)
P.eq("û_{i} = u_{i} · min(1, C / ||u_{i}||)", 1)
P.eq("θ = ( Σ_{i} û_{i} + z ) / n,   z ~ N(0, σ²C² I)", 2)
P.eq("ε = √(2 ln(1.25/δ)) / σ,   δ = 1e-5", 3)
P.para("giving ε = " + f(t["epsilon"], 3) + ". A request for client j stores nothing new and computes", indent=False, after=0, keep=True)
P.eq("θ_{−j} = ( Σ_{i} û_{i} + z − û_{j} ) / (n − 1)", 4)
P.eq("Δ_{j} = || θ_{−j} − ( z + Σ_{i≠j} û_{i} ) / (n − 1) ||₂ ≤ 1e-10", 5)
P.para(
    "Because the aggregate is linear, Δ is zero up to floating-point error: the certificate's reference check is an identity, not an independent "
    "retrain, since it reuses the stored noise z. The status is CERTIFIED only if Δ passes and utility retention stays at or above 70 %, where "
    "utility = 0.65·accuracy + 0.35/(1 + ln(1 + perplexity)) and retention is the ratio after to before.", indent=False)
P.h2("D. Why This Algorithm")
P.para(C(
    "Subtracting a stored update was chosen because it needs no raw data, costs O(d) in the parameter count d, and is exact for a linear "
    "aggregate; the price is that the server must store every client's clipped update, itself a sensitive artefact. For multi-round "
    "nonlinear LLM fine-tuning an update influences later updates, so exact subtraction would no longer hold and methods such as "
    "[[federaser,memprune]] become necessary. The Gaussian noise gives the one-shot release bound in (3); it is the classical calibration "
    "[[dwork]], which is formally valid only for ε < 1. Adding or removing one client changes Σû by at most C in L2, so noise of standard deviation σC per "
    "coordinate is the Gaussian mechanism with L2 sensitivity C, and the model θ and anything computed from it are post-processing of that one release. "
    "The unlearned model reuses z: it is a second function of the same noisy release, not a fresh one. That is why ε in (3) is reported unchanged "
    "after a removal and why it is not, by itself, a statement about forgetting."))
P.h2("E. Verification and Audit")
P.para(
    "A bigram proxy was chosen because it keeps what matters for the question, a linear federated aggregate, clipping, noise, an attack and an audit "
    "record, and removes what would hide it, namely GPU training time and nonlinearity, so the whole stack runs offline on a classroom PC and the full "
    "measurement suite finishes in about three minutes.")
P.para(C(
    "The attack scores a text by its negative loss and reports the AUC of the client's five records against five non-members [[shokri,yeom]]; "
    "0.5 means no leakage. Each ledger record stores the SHA-256 of the previous hash and its canonical JSON, so verification re-walks the chain. "
    "The software has five unit tests and a 14-check end-to-end smoke test; the measurement suite adds 11 experiments."))
P.eq("h_{k} = SHA-256( h_{k−1} | canonical(r_{k}) ),   h_{0} = 64 zeros", 6)
P.para(
    "A certificate has 25 fields: identifiers, status, method, ε, δ, C, σ, the residual and reference distances, the attack AUC, perplexity and accuracy "
    "before and after, retention, client counts, model hashes before and after, and the hash of its own ledger record h. It is returned by the "
    "API and can be downloaded as JSON.")
P.h2("F. Algorithms and Threat Model")
P.para(
    "*Algorithm 1 (train).* 1) Count the bigrams of each client's normalised records to obtain u; 2) clip to norm C and store the clipped update with "
    "its raw norm and scale; 3) draw z once from N(0, σ²C²I) with the session seed and store it; 4) keep the sum S = Σû + z; 5) release θ = S/n, "
    "evaluate perplexity and accuracy on the public sentences, hash θ with SHA-256 and append a FEDERATED_TRAINING record.")
P.para(
    "*Algorithm 2 (unlearn client j).* 1) Reject the request if the model is untrained, the client is unknown or already removed, or only one client "
    "remains; 2) measure the metrics and the attack AUC on j's records; 3) set S ← S − û_j, drop j from the active set and θ ← S/(n − 1); 4) measure again; "
    "5) compute Δ against the retained-only aggregate; 6) set the status and append a CLIENT_UNLEARNING record that carries every certificate field; "
    "7) return the certificate with its record hash.")
P.para(
    "*Threat model.* The server is trusted to hold the clipped updates. The questioner is a party who later asks whether a removed client's text is "
    "still in the model (membership inference) or an auditor who wants a record. Malicious clients, a malicious server, secure aggregation and any "
    "adversary with write access to the ledger file are out of scope.")
P.h2("G. Implementation")
P.para(
    "The server wraps one engine in a re-entrant lock, so requests are serialised and every caller shares one session; POST /api/session replaces "
    "the engine but keeps the ledger. The React interface has six pages (landing, dashboard, training, unlearning, explorer and audit) that call the "
    "same endpoints through a Vite proxy, show the certificate with a before-and-after chart and the ledger table, and download the certificate as "
    "JSON. The original single-page interface and a Tkinter client remain available.")
P.h2("H. Evaluation Protocol")
P.para(
    "Every experiment runs the real engine on a throw-away ledger. The seed study repeats the default configuration for 50 seeds and removes each of the five "
    "clients in turn (250 requests). The sweep varies σ over 12 values from 0.001 to 10 with 20 seeds each. The retrain comparison draws, for each of 40 seeds "
    "and five clients, a fresh-noise retrain on the retained clients and a second independent one, at σ = 3 and σ = 0.5. The noise-free run sets σ = 1e-6. "
    "The scaling run uses synthetic clients drawn from a 20-word vocabulary, from 5 to 500 clients, with the median of five repeats; the baseline is the "
    "proxy training on the retained clients. API timings are taken on 127.0.0.1 over 30 to 100 calls per endpoint. The tamper run applies seven edits "
    "to a three-record ledger. All randomness is seeded.")

# ================================================================== IV. RESULTS
P.h1("IV. Results")
P.para(
    f"*Conditions.* Default configuration is seed 2026, C = 25, σ = 3, δ = 1e-5; seed studies use {s['n_seeds']} seeds × 5 clients "
    f"({s['n_unlearning_requests']} requests); the noise sweep uses 20 seeds per σ; the retrain comparison uses 200 pairs per σ; the noise-free run uses σ = 1e-6. "
    "Perplexity is on five public sentences. The seed study measures spread, the sweep measures the privacy-utility trade-off, the noise-free run shows "
    "what the removal changes when nothing hides it, the fresh-noise comparison tests the certificate against a real retrain, and the tamper and "
    "scaling runs probe the ledger and the cost.")
rows2 = [["Setting", "ε", "Perplexity", "Accuracy", "AUC before → after", "Retention %"]]
rows2.append(["Default, seed 2026 (n = 5)", f(t["epsilon"], 2), f(t["perplexity"]), f(100 * t["next_character_accuracy"]) + " %",
              f"{f(auc_b0, 2)} → {f(auc_a0, 2)}", f(b["mean_retention_percent"])])
rows2.append(["Default, 50 seeds (n = 250)", f(t["epsilon"], 2), f(s["pre_unlearning_perplexity"]["mean"]) + "±" + f(s["pre_unlearning_perplexity"]["sd"], 0),
              f(100 * s["pre_unlearning_accuracy"]["mean"]) + " %", f"{f(s['membership_auc_before']['mean'], 2)} → {f(s['membership_auc_after']['mean'], 2)}",
              f(s["utility_retention_percent"]["mean"])])
for sg in (0.1, 1.0, 4.85):
    r = sw[sg]
    rows2.append([f"σ = {sg:g} (20 seeds)", f(r["epsilon"], 2 if r["epsilon"] < 10 else 1), f(r["perplexity"]["mean"]), f(100 * r["accuracy"]["mean"]) + " %",
                  f"{f(r['membership_auc_before']['mean'], 2)} → {f(r['membership_auc_after']['mean'], 2)}", f(r["retention_percent"]["mean"])])
rows2.append(["Noise-free σ = 1e-6 (n = 5)", "≈ 5e6", f(nf["rows"][0]["perplexity_before"]), "n/a", f"{f(nf['mean_auc_before'], 2)} → {f(nf['mean_auc_after'], 2)}", f(nf_ret)])
P.table(rows2, "Measured unlearning results (mean over requests)", [0.28, 0.1, 0.15, 0.14, 0.19, 0.14], size=6.5)
P.figure(FIG / "fig3_results.png", "(a) Perplexity and attack AUC against the noise multiplier (20 seeds). (b) L2 distance of the unlearned model to a fresh-noise retrain and between two retrains (200 pairs).", 3.4)
P.para(
    f"*Removal and utility.* Removal is exact to {s['reference_l2']['max']:.1e} and all {s['n_unlearning_requests']} requests are certified. Retention averages "
    f"{f(s['utility_retention_percent']['mean'])} % (minimum {f(s['utility_retention_percent']['min'])} %); removing four of five clients raises perplexity from "
    f"{f(b['training']['perplexity'], 0)} to {f(seq['steps'][4]['perplexity'], 0)} because the noise stays while the signal is divided by fewer clients; every step is certified and "
    "the ledger verifies, and the fifth removal is refused with the message that at least one client must remain. At the default seed the attack AUC before removal is "
    + ", ".join(f(c["membership_auc_before"], 2) for c in per) + " for the five clients (after: " + ", ".join(f(c["membership_auc_after"], 2) for c in per) +
    "); with five members and five non-members one pair moves the AUC by 0.04, and values far below 0.5 are as uninformative as values above it.")
P.para(
    f"*The default model is noise-dominated.* The noise has standard deviation {dp['noise_std_per_coordinate_default']:.0f} per coordinate against a clipped client update of norm 25 "
    f"spread over 1,089 coordinates. Perplexity is {f(s['pre_unlearning_perplexity']['mean'], 0)}, worse than the uniform model's 32, and next-character accuracy "
    f"is {f(100 * s['pre_unlearning_accuracy']['mean'])} %. The attack is already at chance before removal (AUC {f(s['membership_auc_before']['mean'], 2)} ± {f(s['membership_auc_before']['sd'], 2)}), so "
    f"the mean change of {f(s['membership_auc_change']['mean'], 2)} is within noise. Useful models (perplexity < 20) need σ ≤ 0.1, i.e. ε ≥ 48, while the "
    f"classical bound is valid only for ε < 1 (σ > {f(dp['sigma_needed_for_epsilon_below_1'], 2)}), where perplexity is 198 or more: no setting is both private by this bound and useful. "
    f"Between σ = 0.001 and 0.1 accuracy stays at {f(100 * sw[0.1]['accuracy']['mean'])}-{f(100 * sw[0.001]['accuracy']['mean'])} % and perplexity at {f(sw[0.001]['perplexity']['mean'])}-{f(sw[0.1]['perplexity']['mean'])}; "
    f"at σ = 0.3 mean retention dips to {f(sw[0.3]['retention_percent']['mean'])} % and one of the 100 requests falls below the 70 % floor and is marked REVIEW_REQUIRED, "
    "the only such case in the sweep. Because the retention floor is measured against a model that is already near-useless at σ = 3, it cannot fail there: none of the "
    f"{s['n_unlearning_requests']} default requests did.")
P.para(
    f"*Is the removal real?* Without noise the attack separates members almost perfectly (AUC {f(nf['mean_auc_before'], 2)}) and removal brings it to "
    f"{f(nf['mean_auc_after'], 2)} with {f(nf_ret)} % retention, so the subtraction does erase the signal. Against a true retrain with fresh noise, the "
    f"unlearned model lies {f(g3['l2_unlearned_vs_fresh_retrain']['mean'], 0)} ± {f(g3['l2_unlearned_vs_fresh_retrain']['sd'], 0)} away at σ = 3 "
    f"({f(g05['l2_unlearned_vs_fresh_retrain']['mean'], 0)} at σ = 0.5), the same as two independent retrains are from each other "
    f"({f(g3['l2_fresh_retrain_vs_fresh_retrain']['mean'], 0)} and {f(g05['l2_fresh_retrain_vs_fresh_retrain']['mean'], 0)}). That distance is pure noise, which supports the claim "
    "that the unlearned model is distributed like a retrained one, but the 1e-14 certificate value alone does not.")
P.figure(FIG / "fig4_certificate.png", "Output screen: certificate for Client 01 (Finance), ε 1.6149, AUC 0.200 → 0.160, retention 93.65 %.", 3.4)
P.figure(FIG / "fig5_audit.png", "Output screen: compliance ledger, four chained records and a valid hash chain.", 3.4)
P.table([["Clients", "Records", "Train ms", "Unlearn ms", "Retrain ms", "Retrain / unlearn"]] +
        [[str(r["clients"]), f"{r['total_records']:,}", f(r["train_ms_median"]), f(r["unlearn_ms_median"]), f(r["full_retrain_ms_median"]), f(r["speedup_retrain_over_unlearn"], 2) + "×"]
         for r in sc["rows"]], "Median cost of unlearning and of retraining the proxy", [0.14, 0.16, 0.16, 0.18, 0.18, 0.18], size=6.5)
P.figure(FIG / "fig6_tamper.png", "Audit-ledger tamper matrix: seven attacks on a three-record ledger; green = detected, red = not detected.", 3.4)
P.para(
    f"*Audit and service behaviour.* The ledger detects an edited field, a flipped status, a deleted record and swapped records, but misses tail truncation, "
    f"a full re-hash forgery and an appended forged record (no signature or anchor). An append re-reads the file: {f(sc['ledger_append_ms_at_length']['1'], 2)} ms at one record "
    f"and {f(sc['ledger_append_ms_at_length']['2000'], 1)} ms at 2,000. Unlearning ({f(unl_row[5]['unlearn_ms_median'], 0)} ms) is slower than re-running the proxy training "
    f"({f(unl_row[5]['full_retrain_ms_median'], 0)} ms) with 5 clients, {f(unl_row[100]['speedup_retrain_over_unlearn'], 1)} times faster at 100 clients and {f(unl_row[500]['speedup_retrain_over_unlearn'], 1)} times faster at 500; this says nothing about LLM-scale retraining. "
    f"On localhost the median latency is {f(lat['POST /api/train']['p50_ms'], 0)} ms for training and {f(lat['POST /api/unlearn']['p50_ms'], 0)} ms for unlearning. A 2 MB body aborts the connection "
    "instead of returning an error, unsupported methods return an HTML page, and no endpoint is authenticated.")
P.para(
    f"*Testing.* The five unit tests and the 14 smoke checks pass. {len(api['edge_cases'])} further edge-case calls (malformed JSON, a JSON array body, an unknown and an "
    "SQL-like client id, an empty, Unicode and 5,000-character seed, a repeated removal, removal of the last client, a path-traversal URL) return JSON errors with status "
    "400 or 404 or succeed as intended, apart from the oversized body and the unsupported method noted above. Not tested: concurrent load, a real LLM, "
    "GPU training and any penetration test.")
P.para(
    "*Observed limits.* The attack has a resolution of 0.04 and uses only ten texts; state lives in memory and is lost on restart while the ledger persists; "
    "one engine is shared by every caller; the 25 sentences cannot show generalisation; and exactness of subtraction holds for one aggregation round only. "
    "These limits, not the arithmetic, bound what the certificate can claim.")
P.para(C(
    "*Comparison.* The base paper [[base]] reports no comparable metric. FedMemPrune [[memprune]], Oblivionis [[oblivionis]] and FedORA [[fedora]] use image, "
    "benchmark-LLM and vertical-federated data with neural models, so none of the numbers above is comparable with theirs; the comparison is qualitative: "
    "ForgetSafe is exact only because its aggregate is linear and single-round, whereas those works handle nonlinear networks. It adds a per-request certificate and a "
    "tamper-evident ledger; FedORA certifies through a bound to retraining, and the other two works describe no audit record."))
P.para(
    "*Implications.* Four practical rules follow. Report utility next to ε, because a bound that leaves the model worse than uniform protects nothing "
    "useful. Test a certificate against a fresh-noise retrain and a noise-free attack, because an identity check cannot fail. Draw fresh noise or "
    "re-account the budget after a removal, because reused noise makes the reported ε a statement about training, not about forgetting. Treat a "
    "hash chain as evidence of casual edits only; signatures or an external anchor are needed to detect truncation or re-hashing.")

# ================================================================== V. CONCLUSION
P.h1("V. Conclusion")
P.para(C(
    "ForgetSafe meets its objectives on a bigram proxy: federated aggregation across five clients (partly, no LLM), parameter-level removal without "
    "retraining (met), a differential-privacy bound (partly: ε = 1.61 lies outside the range of the classical bound, the noise is reused and no "
    "accountant exists), attack and retrain verification (met, but the attack is uninformative at the default noise), utility retention (97.1 %, on a near-useless "
    "baseline) and per-request audit records (met, with the blind spots above). The key finding is that the certificate proves exactness of the "
    "arithmetic, not forgetting of an LLM; the fresh-noise and noise-free experiments supply the evidence the certificate cannot. Future work: replace the "
    "proxy with LoRA adapters of a small Hugging Face model over several federated rounds [[lora]]; add privacy accounting [[balle]] and fresh noise after "
    "removal; sign and externally anchor the ledger; and test stronger membership attacks. Until then ForgetSafe is a reproducible demonstrator of the workflow "
    "(train, remove, check, certify, record) and of how to test such a certificate, not a compliance product and not a claim that an LLM has been formally erased. "
    "Every number in this paper is regenerated by one script from fixed seeds."))
P.para(
    "In answer to the four questions: removal by subtraction equals the retained-only aggregate exactly and matches a fresh retrain in distribution; the certificate's "
    "own check is an identity and cannot fail; the default noise removes the leakage and the utility together; and the ledger resists casual edits but not an "
    "adversary who can rewrite the file.")

# ================================================================== references
K.REFS = [REFERENCES[REF[k] - 1] for k in order]
P.references()
out = BATCH / "19.IEEE_Paper.docx"
P.d.core_properties.author = "Batch A9"
P.d.core_properties.title = TITLE
P.d.save(str(out))
print("saved", out.name, "| references:", len(K.REFS), "| order:", order)
