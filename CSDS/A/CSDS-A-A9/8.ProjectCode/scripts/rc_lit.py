"""Chapter 2 content: literature survey, base-paper analysis, related work by theme, algorithms and datasets, strengths and limits, gap, novelty.

Facts about [2]-[4] were read from the PDFs in archived_base_papers/ ; [1] from Documentary/ ; [7] from its published abstract.
Items [5], [6], [8] (batch survey) could not be retrieved and are only listed.
"""
from __future__ import annotations

from doc_common import metrics

_g = metrics("gold_retrain")["results"]
_s = metrics("seeds")
_nf = metrics("noise_free_leakage")


def sec_lit_overview(d):
    d.h2("Overview of the Survey")
    d.p("The survey has three layers. The first is the batch's own literature table (`5.LITERATURE SURVEY.docx`), which lists five papers; the second is the three "
        "papers kept in the batch's archive of base papers, which were read in full for this report; the third is a set of standard method references on "
        "federated learning, differential privacy, unlearning, membership inference, the regulation and LLM adapters, whose bibliographic details are well established. "
        "The table below records what each batch item is and how much of it could be checked.")
    d.table([["Ref.", "Work", "Year / venue", "Status in this report"],
             ["[1]", "Deep learning approaches for continuous sign language recognition: a comprehensive review", "2025, IEEE Access", "Read; base paper recorded in the batch; its review method is adopted"],
             ["[5]", "Federated illusion: multi-level geometric privacy audit for federated graph unlearning", "2026, Information", "Listed in the batch survey; not independently verified"],
             ["[6]", "Computationally efficient federated unlearning", "2025, 26th Int. Middleware Conf.", "Listed in the batch survey; not independently verified"],
             ["[7]", "A comprehensive investigation of federated unlearning", "2024, 2nd Int. Conf. DAML", "Verified through its published abstract"],
             ["[8]", "Unlearning under siege: robustness risks of certified machine unlearning", "2026, Neurocomputing", "Listed in the batch survey; not independently verified"],
             ["[2]", "Rethinking federated unlearning via the lens of memorization", "2026, KDD", "Read in full (archived base paper)"],
             ["[3]", "Oblivionis: lightweight learning and unlearning for federated LLMs", "2025, arXiv", "Read in full (companion reference paper)"],
             ["[4]", "Certifying the right to be forgotten: primal-dual optimisation (FedORA)", "2025, arXiv", "Read in full (archived paper)"]],
            "Literature items and how they were used", widths=[0.07, 0.43, 0.2, 0.3], font=9.5)
    d.p("Three of the batch items, [5], [6] and [8], could not be located by searching their titles, so nothing is said here about their methods or results beyond what "
        "their titles state: [5] concerns auditing privacy in federated graph unlearning, [6] concerns the computational efficiency of federated unlearning, and [8] concerns the "
        "robustness of certified machine unlearning. They are kept in the reference list because the batch lists them, and they are not used as evidence anywhere in this report.")


def sec_base_paper(d):
    d.h2("Analysis of the Base Paper")
    d.p("The base paper recorded in the batch files is Khan et al., \"Deep learning approaches for continuous sign language recognition: a comprehensive review\" "
        "(IEEE Access, volume 13, 2025) [1]. It is a survey of continuous sign language recognition (CSLR), the task of identifying consecutive signs in video streams "
        "without prior knowledge of their temporal boundaries. Its subject is therefore unrelated to federated learning, language models or unlearning, and the batch's own "
        "base-paper document says so: what the project adopts is the paper's **review method**, not its technology.")
    d.h3("What the paper does")
    d.p("Reading its abstract and section structure shows the method clearly. The authors argue that earlier CSLR research lacked a unified framework joining spatial, "
        "temporal and alignment approaches, and respond by organising the literature into a taxonomy. The taxonomy covers the sign language studied, data collection, "
        "input method, gesture signals, identification methods, the datasets applied and overall efficiency. The paper's sections move from the task and its input "
        "modalities, through acquisition devices (sensor-based, vision-based and hybrid), to the methods and materials, including the datasets used. The deep-learning "
        "models are then grouped by spatial, temporal and alignment approach, and for each group the paper describes the benefits and the drawbacks. It closes with the "
        "open challenges, which it lists as the need for diverse and naturalistic datasets, signer diversity and real-time systems.")
    d.h3("The method adopted here")
    d.p("Three steps of that method are reused. First, **organise** existing work into classes rather than listing papers one by one; for this project the classes are the "
        "approaches to removing a client from a federated model (the table of approaches below). Second, **compare** each class on strengths and limitations against the same criteria; "
        "here the criteria are cost, strength of evidence, utility impact, applicability to federated LLM pipelines and auditability (the comparison of classes). Third, **name the gap** "
        "that the comparison leaves open (the research-gap section), and let the gap define the objectives.")
    d.h3("What is not drawn from the paper")
    d.p("No algorithm, dataset, metric or result of the sign-language paper is used in ForgetSafe, and no numerical comparison between the two is possible or made: they "
        "address different tasks, data and measures. Where the report compares the project with published work numerically or in kind, the comparison is with the technically "
        "closest papers, [2], [3] and [4], and even there it is qualitative, because their datasets (image classification benchmarks, LLM unlearning benchmarks) and "
        "models differ from the character-level proxy used here.")


def sec_related(d):
    d.h2("Related Work")
    d.p("The related work is grouped by theme. The first group is the closest technically; the later groups supply the methods that ForgetSafe relies on.")
    d.h3("Federated unlearning")
    d.p("Wei et al. [2] revisit federated unlearning through memorisation. Their argument is that existing federated unlearning methods may overlook the information "
        "shared between the data to be forgotten and the remaining data, which leads to ineffective unlearning and unfairness between clients. Unlearning, they argue, "
        "should remove the unique memorised information of the forgotten data and keep overlapping patterns that the remaining data also supports. They propose Grouped "
        "Memorization Evaluation, an example-level metric separating memorised from overlapping knowledge, and Federated Memorization Pruning (FedMemPrune), which resets the "
        "parameters responsible for memorisation. They evaluate on CIFAR-10, CIFAR-100 and EMNIST with ResNet-18, ResNet-34 and VGG-9 models, including a non-IID partition "
        "with a Dirichlet concentration of 0.5, and report that the method closely matches retraining-based baselines while removing memorisation more effectively than the "
        "other federated unlearning algorithms they compare.")
    d.p("Zhang et al. (Oblivionis) [3] address the federated LLM setting directly. They present a lightweight framework that unifies federated learning and unlearning "
        "as a dual optimisation objective and incorporates six federated-learning algorithms (FedAvg, FedAvgM, FedAdagrad, FedAdam, FedYogi and FedProx) and five "
        "unlearning algorithms (gradient ascent, gradient difference, NPO, SimNPO and retraining) for comparison. Their setting is LoRA fine-tuning of Llama-family "
        "models, evaluated on the TOFU and MUSE unlearning benchmarks, motivated by the Right to Be Forgotten, and they report a balance between forgetting efficacy and model "
        "utility. It is the nearest published match to the batch's title, and it is the reason the project keeps a LoRA-style adapter as the model it stands in for.")
    d.p("Jiang et al. (FedORA) [4] treat vertical federated learning, where parties hold different features of the same samples. They formulate removal of samples or labels "
        "as a constrained optimisation solved with a primal-dual method, with an unlearning loss that promotes classification uncertainty rather than misclassification, an adaptive "
        "step size, and an asymmetric batch design. Their theoretical analysis bounds the model difference between FedORA and training from scratch, and they evaluate on a "
        "tabular dataset (Income) and image datasets (MedMNIST, CIFAR-10, CIFAR-100, Tiny-ImageNet), including resilience to membership-inference and backdoor attacks. "
        "It is the most explicit among the papers read about tying an unlearning procedure to a bound against the retraining reference.")
    d.p("FedEraser (Liu et al.) [17] is the best-known client-level method and the closest in mechanism to ForgetSafe: the server retains the clients' historical updates "
        "and, when a client leaves, calibrates the retained updates of the other clients to reconstruct an unlearned model instead of retraining. Zhang's review [7] surveys "
        "this family (it names FedEraser, FedCIO, FedRecovery and F2UL), and concludes that future work should concentrate on standardised evaluation metrics, computational "
        "efficiency and non-IID data. The batch lists three further works on auditing, efficiency and robustness of unlearning [5], [6], [8]; they are listed but not analysed, as "
        "explained in the overview of the survey.")
    d.h3("Exact, sharded and certified removal")
    d.p("Cao and Yang [18] introduced the idea of making a system forget by converting learning into a summation form over transformed data points, so that removing a point "
        "means subtracting its term; this is the idea that ForgetSafe's linear aggregate relies on. Bourtoule et al. [12] proposed SISA training, which shards the data, "
        "trains an isolated model per shard and slices each shard's training so that a deletion retrains only one shard from a recent checkpoint; the price is a training "
        "architecture and an ensemble at inference. Guo et al. [13] defined certified removal in the language of differential privacy: a removal mechanism is "
        "(epsilon, delta)-certified if the model after removal is statistically indistinguishable from the model retrained without the point, and they achieved it for "
        "linear, convex models with a Newton-style update and added noise. Sekhari et al. [14] studied how many deletions an algorithm can absorb, their \"deletion "
        "capacity\", at a given accuracy and privacy level, and showed that the capacity depends on the dimension of the model and the privacy budget.")
    d.h3("Differential privacy and the Gaussian mechanism")
    d.p("Dwork and Roth [10] give the Gaussian mechanism: adding noise of standard deviation sigma times the L2 sensitivity to a query output satisfies (epsilon, delta)-"
        "differential privacy when sigma is large enough relative to epsilon and delta, for epsilon in the open interval (0, 1). Their analysis yields the formula "
        "that the application evaluates. Abadi et al. [11] extended the idea to deep learning (DP-SGD) with clipping of per-example gradients and a moments accountant that "
        "tracks the cumulative privacy loss over many steps, which a one-shot formula cannot. Balle and Wang [19] showed how to calibrate the Gaussian mechanism analytically "
        "so that it is valid for all epsilon, not only below 1. McMahan et al. [9] introduced federated averaging, the aggregation rule that federated LLM pipelines build "
        "on.")
    d.p("The derivation that matters for this project is short. If each client's contribution is clipped to L2 norm at most C, then adding or removing one client changes the "
        "sum of contributions by a vector of norm at most C, so the L2 sensitivity of the sum is C. Noise drawn from a Gaussian with standard deviation sigma times C, with sigma the "
        "\"noise multiplier\", then gives (epsilon, delta)-differential privacy with epsilon = sqrt(2 ln(1.25/delta)) / sigma, provided epsilon is below 1 [10]. Dividing the "
        "noisy sum by the number of clients afterwards is post-processing and does not change the guarantee. Two consequences are used later: the guarantee concerns the one "
        "noisy release only, and for delta = 1e-5 the formula requires a multiplier above about 4.84 before epsilon drops below 1, a range in which [19] is the remedy.")
    d.h3("Membership inference and memorisation")
    d.p("Shokri et al. [15] showed that an adversary with query access can often tell whether a record was in a model's training set, using shadow models trained to imitate "
        "the target. Yeom et al. [16] connected this to overfitting and gave a simpler attack that predicts membership when a record's loss is below a threshold; the "
        "loss-based attack used in this project is of that family, summarised as an AUC over the member and non-member scores. For language models, Carlini et al. [21] "
        "extracted verbatim training sequences, which shows that the influence a client leaves in a text model can be concrete and not only statistical.")
    d.h3("Regulation and adapters")
    d.p("Article 17 of the GDPR [20] grants the right to erasure, the legal anchor of the whole field. LoRA [22] fixes the pretrained weights and trains low-rank update "
        "matrices, so the object a client contributes in a federated LLM pipeline is a small tensor, which is why the project's per-client vector is a reasonable, if "
        "much smaller, stand-in for it.")


def sec_lit_algorithms(d):
    d.h2("Datasets and Algorithms in the Literature and in This Project")
    d.p("The next table lists the removal approaches that appear in the papers read, the model and data used where the paper states them, and the corresponding choice made in ForgetSafe.")
    d.table([["Approach", "Source", "Models and data reported", "In ForgetSafe"],
             ["Retraining without the client", "reference method in [2]-[4], [12]", "Used as the baseline in all three papers read", "Used as the reference for comparison, in two forms: recomputation from stored updates, and a retrain with fresh noise (Chapter 8)"],
             ["Sharded retraining (SISA)", "[12]", "Shard-and-slice training of isolated models", "Not implemented; named as a future backend"],
             ["Gradient ascent, gradient difference, NPO, SimNPO", "reported in [3]", "Llama-family LoRA models; TOFU and MUSE benchmarks", "Not implemented; the proxy model has no gradient training"],
             ["Memorisation pruning (FedMemPrune)", "[2]", "ResNet-18/34, VGG-9; CIFAR-10, CIFAR-100, EMNIST; Dirichlet 0.5 non-IID", "Not implemented"],
             ["Primal-dual constrained optimisation (FedORA)", "[4]", "Income, MedMNIST, CIFAR-10/100, Tiny-ImageNet; vertical FL", "Not implemented"],
             ["Calibration with stored updates (FedEraser)", "[17]", "Server keeps clients' historical updates", "Related mechanism: updates are stored; removal is exact subtraction rather than calibration"],
             ["Newton-step certified removal", "[13]", "Convex, linear models", "Not implemented; ForgetSafe's certificate is a different, simpler check"],
             ["Summation-form unlearning", "[18]", "Statistical-query learners", "Implemented: the aggregate is a sum of per-client terms"],
             ["Gaussian mechanism on a clipped sum", "[10], [11]", "Noise standard deviation = multiplier x clipping norm", "Implemented with one release and no accountant"]],
            "Approaches reported in the literature and the choice made in this project", widths=[0.22, 0.14, 0.3, 0.34], font=9)
    d.p("**Data in this project.** ForgetSafe uses no benchmark. Its corpus is the built-in set of 25 training sentences (five clients with five records each), five public "
        "evaluation sentences and five non-member sentences in `certified_unlearning/dataset.py`. The choice follows from the objective of a fully offline, reproducible demonstrator, "
        "and it is the main reason that the project's numbers cannot be compared with those of papers evaluated on CIFAR or TOFU. **Algorithms in this project** are a "
        "character-bigram language model, L2 clipping, a Gaussian-noise sum, subtraction-based removal, a loss-based membership attack and a SHA-256 hash chain, each justified in Chapter 6.")
    d.p("**Why subtraction is exact here and not in LLM training.** Removal by subtraction is exact when the released model is a function of the clients' contributions that "
        "is linear in them and when each contribution depends only on that client's data. ForgetSafe's aggregate is of this form: every client's bigram-count vector is computed "
        "from its own records alone, the vectors are clipped and summed once, and the sum is divided by a count. Removing a client therefore leaves exactly the sum of the "
        "others. In federated LLM training the situation is different. Training runs for many rounds, and each client's update in round t is computed from the global model "
        "produced in round t-1, which already contains every other client's earlier contributions; the update is also a non-linear function of the weights. Subtracting the "
        "client's recorded updates then removes only the first-order, direct part of its influence. This is why the surveyed methods calibrate stored updates [17], retrain "
        "shards [12], prune memorised parameters [2] or optimise an unlearning objective [3], [4], and why the project's claim of exactness is restricted to its one-shot linear aggregate.")


def sec_lit_strengths(d):
    d.h2("Strengths and Limitations of Existing Approaches")
    d.p("Following the base paper's method, each class is compared on the same criteria. The comparison draws on the batch's list of existing systems and on the papers above.")
    d.table([["Class", "Strengths", "Limitations"],
             ["Full retraining", "Strongest removal reference; no assumption about the model", "Cost of the whole training for every request; impractical for large federated LLMs"],
             ["Approximate unlearning (gradient ascent, heuristic weight edits)", "Fast; works on pre-trained models", "No formal statement that the data is forgotten; aggressive settings damage utility on retained data; mostly studied on centralised models"],
             ["Sharded training (SISA)", "Limits retraining to one shard; exact in the shard sense", "Needs the sharded architecture from the start; ensemble cost; weaker fit for federated LLM adapters"],
             ["Differentially private training", "Formal bound on the influence of one client or example", "Privacy-utility trade-off; needs an accountant over many rounds; does not itself remove anything"],
             ["Certified removal for convex models", "A formal (epsilon, delta) statement against retraining", "Established for convex, linear models; not for deep, non-convex LLMs"],
             ["Stored-update methods (FedEraser)", "Avoids client data; reuses history", "Storage of updates; calibration costs; evidence for the removal is empirical"],
             ["Memorisation-aware pruning", "Targets what was actually memorised; preserves shared knowledge", "Evaluated on vision benchmarks; an audit record is not part of the method as described"]],
            "Comparison of classes of approach", widths=[0.24, 0.34, 0.42], font=9.5)
    d.p("What a certificate can mean depends on the definition. In the sense of [13], a removal is certified when the output distribution of the removal mechanism is within (epsilon, delta) of the output distribution of retraining without the point; this is a statement about distributions, proved for a model class. A weaker, operational meaning is that a check passed: a reference recomputation agreed, an attack failed, utility stayed above a floor. The first meaning gives a guarantee and the second gives evidence. A certificate should say which it is, and ForgetSafe's does the second.")
    d.p("A theme across the classes is that *removal* and *evidence of removal* are treated separately. Methods that remove well rarely produce a record a third party can "
        "inspect, and methods that give guarantees are restricted to models far simpler than an LLM. This is the observation that the research gap formalises.")


def sec_gap(d):
    d.h2("Research Gap")
    d.p("The batch states the gap in one sentence: federated unlearning methods mostly remove client influence heuristically, and certified, auditable unlearning designed "
        "for federated LLM pipelines remains an open problem. The survey supports that statement in four parts.")
    d.numbered([
        "**Certification is concentrated in convex or centralised settings** [13], [14]; federated LLM unlearning work [3] concentrates on forgetting-quality and utility measures rather than certified bounds.",
        "**Verification evidence is rarely packaged.** FedORA reports membership-inference resilience as an experimental finding [4]; in the parts of [2]-[4] that were read, no per-request certificate "
        "that an operator can hand to a user or regulator is described.",
        "**Auditability is not part of the algorithms.** The papers read focus on the removal procedure; a tamper-evident record of each request is not part of the methods as described.",
        "**Little attention is given to how reliable the evidence is.** A certificate or attack score is useful only if its limits are known: the noise level at which the attack is "
        "informative, whether the reference comparison is independent, and whether the recorded privacy parameter is valid.",
    ])
    d.p("ForgetSafe addresses the first three parts at demonstrator scale and addresses the fourth by measuring its own evidence. It does not close the gap for real LLMs: it "
        "shows the shape of the pipeline and where its weak points are on a model small enough to examine completely.")


def sec_novelty(d):
    d.h2("Novelty Compared with the Base Paper and the Closest Work")
    d.p("The base paper [1] contributes a review method; the closest technical papers [2]-[4] contribute unlearning algorithms and evaluations. The table states what "
        "ForgetSafe adds or does differently. None of it is claimed as new to the field, and the systems are not compared numerically, because their tasks, data and metrics differ.")
    d.table([["Element", "Base paper [1]", "Closest technical work [2]-[4]", "ForgetSafe (this project)"],
             ["Nature of the work", "Survey of sign-language recognition; taxonomy and gaps", "New unlearning algorithms with experiments", "Runnable system joining training, removal, verification and audit, plus a measurement study"],
             ["Subject", "Continuous sign language recognition", "Federated and federated-LLM unlearning", "Federated unlearning with certificates for an LLM-adapter stand-in"],
             ["What is reused", "The method: taxonomy, comparison, gap", "The problem setting and the retraining reference", "Method from [1]; setting and reference from [2]-[4]"],
             ["Removal mechanism", "Not applicable", "Pruning [2]; unlearning algorithms [3]; primal-dual optimisation [4]", "Exact subtraction of the tracked clipped update from a noisy sum"],
             ["Evidence of removal", "Not applicable", "Experimental metrics (forgetting, utility, attacks)", "Per-request certificate: reference distance, attack AUC before and after, utility retention, model hashes"],
             ["Record keeping", "Not applicable", "Not part of the methods", "Hash-chained ledger with a verifier and a documented tamper study"],
             ["Models and data", "Sign-language video datasets", "CIFAR, EMNIST, MedMNIST, Income, TOFU and MUSE with deep models", "Character-bigram proxy (1,089 parameters) on 25 synthetic sentences"],
             ["Self-assessment", "Lists open research gaps of CSLR", "Reports gains over baselines", "Tests its own certificate: noise dominance, identity-style reference, epsilon validity range, ledger blind spots"]],
            "Differences from the base paper and the closest technical work", widths=[0.15, 0.2, 0.3, 0.35], font=9)
    g = _g[0]
    d.p("The last row is the contribution the project is most ready to defend. With the default noise, an unlearned model lies at an L2 distance of "
        f"{g['l2_unlearned_vs_fresh_retrain']['mean']:.0f} from a retrain that draws fresh noise, and two independent retrains lie at "
        f"{g['l2_fresh_retrain_vs_fresh_retrain']['mean']:.0f} from each other (200 pairs): the gap is the noise, not a residue of the removed client. "
        f"Without noise, the attack AUC falls from {_nf['mean_auc_before']:.2f} to {_nf['mean_auc_after']:.2f}. These two measurements, rather than the 1e-14 reference distance, "
        "are the evidence that removal worked, and they are reported in Chapter 8.")
