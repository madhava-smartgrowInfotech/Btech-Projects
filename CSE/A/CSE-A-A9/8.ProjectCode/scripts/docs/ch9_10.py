"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10) for BotGraph."""
import os

from . import facts as F
from .blocks import B, CODE, H1, H2, H3, N, P, TAB

try:
    from .refs import CITE as _R
except Exception:  # pragma: no cover
    _R = {}


def c(*keys):
    ids = [str(_R[k]) for k in keys if k in _R]
    return (" [" + "], [".join(ids) + "]") if ids else ""


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


def _x():
    """Frequently quoted measured values (strings)."""
    ex = F.EXTRA
    ab, ea, ts = ex["ablation"], ex["error_analysis"], {r["threshold"]: r for r in ex["threshold_sweep"]["sage"]}
    bt = {r["threshold"]: r for r in ex["threshold_sweep"]["baseline"]}
    f1s = [ts[t]["f1"] for t in ts if 0.30 - 1e-9 <= t <= 0.60 + 1e-9]
    return {
        "deg": f"{ab['degree only (structure, no attributes)']['sage']['f1_mean']:.3f}",
        "deg_mlp": f"{ab['degree only (structure, no attributes)']['baseline']['f1_mean']:.3f}",
        "all": f"{ab['all 23 features']['sage']['f1_mean']:.3f}", "all_mlp": f"{ab['all 23 features']['baseline']['f1_mean']:.3f}",
        "no_t": f"{ab['without temporal pattern']['sage']['f1_mean']:.3f}", "no_t_mlp": f"{ab['without temporal pattern']['baseline']['f1_mean']:.3f}",
        "no_p": f"{ab['without profile metadata']['sage']['f1_mean']:.3f}", "no_post": f"{ab['without posting behaviour']['sage']['f1_mean']:.3f}",
        "prof": f"{ab['profile metadata only']['sage']['f1_mean']:.3f}", "prof_mlp": f"{ab['profile metadata only']['baseline']['f1_mean']:.3f}",
        "f1_lo": f"{min(f1s):.3f}", "f1_hi": f"{max(f1s):.3f}",
        "peak_t": "0.40", "peak_f1": f"{ts[0.4]['f1']:.3f}",
        "bn_n": ea["by_kind"]["botnet member"]["n"], "bn_s": ea["by_kind"]["botnet member"]["sage_caught"], "bn_b": ea["by_kind"]["botnet member"]["baseline_caught"],
        "ls_n": ea["by_kind"]["lone spammer"]["n"], "ls_s": ea["by_kind"]["lone spammer"]["sage_caught"], "ls_b": ea["by_kind"]["lone spammer"]["baseline_caught"],
        "rescued": ea["rescued_by_graph"], "lost": ea["lost_by_graph"], "both": ea["missed_by_both"],
        "deg_caught": f"{ea['degree_fake_caught_median']:.0f}", "deg_missed": f"{ea['degree_fake_missed_median']:.0f}",
        "t30_p": f"{ts[0.3]['precision']:.2f}", "t30_r": f"{ts[0.3]['recall']:.2f}", "base_best": f"{max(r['f1'] for r in bt.values()):.3f}",
    }


# ---------------------------------------------------------------- document 9: novelty and contributions
def novelty_blocks():
    R = F.BASE_PAPER_RESULTS
    return [
        H2("2.1 The base paper in brief"),
        P("The base paper, PruferNET" + c("base") + ", proposes structural features for node classification in social networks. It builds a minimum spanning tree of the SNAP Facebook graph, "
          "encodes the tree as a Prüfer sequence" + c("prufer") + ", derives features from it (label frequency, entropy, unique-label ratio, transition influence, subtree depth) and adds degree, closeness and PageRank centralities and a trust score. "
          f"A GraphSAGE network ({R['model']}) then assigns each node to one of three classes defined by its depth in the tree: Very Shallow, Shallow or Deep. "
          f"The authors report a test accuracy of {F.pct(R['with_prufer_acc'], 2)} with the Prüfer features against {F.pct(R['without_prufer_acc'], 2)} with traditional features on the Facebook graph (4,039 nodes, 88,234 edges, split {R['split']}), "
          "and a check on the Email-Eu-core network (986 nodes, 16,064 edges)."),
        P("The paper is about influence. Its labels are derived from the graph itself, so it contains no fake accounts, no class imbalance, no bots, no coordinated groups, no human review and no measurement of cost as the graph grows. "
          "The survey in Chapter 2 identified exactly this gap: the same relational learning has to be applied to fake-profile and botnet detection at platform scale."),
        H2("2.2 What BotGraph takes from it"),
        B("**The data family and graph view.** The same SNAP Facebook ego networks supply the topology, and accounts and interactions are nodes and edges.",
          "**GraphSAGE as a backbone.** It is the best of the three architectures here, as in the base paper's choice of model.",
          "**The evaluation protocol.** A 60/20/20 split, a fixed seed for reproducibility, model selection on validation data and one report on the held-out test set.",
          "**The argument that structure adds information a per-node model lacks.** The no-graph baseline in BotGraph is the analogue of the paper's traditional-features-only comparison."),
        H2("2.3 What is different"),
        TAB("Base paper compared with BotGraph", ["Aspect", "PruferNET (base paper)", "BotGraph (this project)"],
            [["Task", "3-class node classification by MST depth (influence)", "Binary fake-account detection plus botnet cluster discovery"],
             ["Labels", "Derived from the graph's own tree depth", "Fake / genuine labels from labelled datasets; known botnet membership for scoring clusters"],
             ["Class balance", "Balanced by percentile construction", "12.6 % fake; class-weighted loss and tuned threshold"],
             ["Models", "GraphSAGE only", "GCN, GAT, GraphSAGE and a no-graph baseline on one split, three seeds"],
             ["Features", "Prüfer-sequence structure + centralities + trust", "23 attribute features: profile, posting, temporal, interaction"],
             ["Groups of accounts", "Not addressed", "Louvain over embeddings; 8 of 8 injected botnets recovered"],
             ["Human in the loop", "None", "Moderator queue; decisions become training labels; test split untouched"],
             ["Scale", "Not measured", "Training and inference time up to 36,264 accounts and 755,648 ties"],
             ["Delivery", "Method and experiments", "Working API, database, web app and a 36-check end-to-end test"],
             ["Hardware", R["hardware"], "CPU only, 16 GB RAM"]],
            widths=[1.2, 2.6, 2.8], align=["l", "l", "l"], size=9.5),
        H2("2.4 What is new and what is standard"),
        P("None of the three layer types is new: GCN" + c("gcn") + ", GAT" + c("gat") + " and GraphSAGE" + c("sage") + " are implemented as published, and Louvain" + c("louvain") + " is the standard algorithm. "
          "The contribution of BotGraph is the combination and its evaluation: a fair comparison of the three architectures with a no-graph control on a graph that has known botnets; clustering driven by what the classifier learned rather than by structure alone; "
          "a moderator loop that keeps the test split fixed so that before-and-after F1 is comparable; per-account explanations that separate an account's own traits from what its neighbours add; and a scalability measurement, all inside one usable application. "
          "The same imbalance and noise concerns that RABot" + c("rabot") + " addresses with learned augmentation and HW-GNN" + c("hwgnn") + " with spectral filtering are handled here more simply, with a class-weighted loss and a validation-tuned threshold, and neither method is reproduced or compared numerically."),
        H2("2.5 Why the numbers cannot be compared with the base paper"),
        P(f"The base paper's {F.pct(R['with_prufer_acc'], 2)} is accuracy on a three-class depth label whose classes are balanced by construction; BotGraph's headline is F1 on a binary label where a model that says 'genuine' every time already scores {F.pct(1 - F.TEST_FAKE / F.TEST_N)} accuracy. "
          f"The data differ (the base paper's graph has 4,039 nodes and its labels come from the graph; this graph has {F.NODES:,} nodes, part of it generated), the model sizes and optimisers differ, and the base paper's hardware was a T4 GPU. "
          f"BotGraph's own accuracy on the test split is {F.f3(F.mean('sage', 'accuracy'))} for GraphSAGE, but that figure is shown only to be complete and is not set against the paper's. "
          "What can be compared is the direction of the finding: in both studies, adding structural information to a GraphSAGE model helps."),
    ]


def contribution_blocks():
    x = _x()
    return [
        P("The work makes the following contributions."),
        N("**An assembled benchmark graph with a documented schema.** Real Facebook ego-network topology, real labelled profile and posting rows and seeded injected botnets are combined into one graph of "
          f"{F.NODES:,} accounts and {F.EDGES:,} ties, with every real and synthetic part labelled, a 23-feature node schema in four groups and a fixed stratified split.",
          f"**A controlled comparison of GCN, GAT and GraphSAGE.** The three architectures and a no-graph baseline share features, split, optimiser, loss and seeds. GraphSAGE reaches F1 {F.mstd('sage', 'f1')} against {F.mstd('baseline', 'f1')} for the baseline "
          f"(+{F.lift('sage'):.1f} points), GAT {F.mstd('gat', 'f1')} (+{F.lift('gat'):.1f}) and GCN {F.mstd('gcn', 'f1')} (+{F.lift('gcn'):.1f}); GCN's recall is below the baseline's.",
          f"**Botnet detection from learned embeddings.** Louvain over embedding similarity and real ties recovers {F.REC['recovered']} of {F.REC['botnets']} injected botnets as single communities (mean recall {F.f3(F.REC['mean_recall'])}, mean precision {F.f3(F.REC['mean_precision'])}), "
          "and each cluster is described by size, density, shared peak hour and creation spread so that a moderator can judge it.",
          "**A moderator loop that keeps evaluation honest.** Confirm and dismiss decisions on accounts and whole clusters become training labels at the next run; reviewed accounts move into training, the test split is never relabelled, and F1 before and after is stored with the run.",
          "**Explainable scores.** Every account shows its probability, the seven own traits that moved the score most (gradient × input) and a separate figure for what the neighbourhood contributes.",
          f"**A scalability measurement.** Training and inference time were measured from {F.NODES:,} accounts and {F.EDGES:,} ties to {F.scal_row(8)['nodes']:,} accounts and {F.scal_row(8)['edges']:,} ties.",
          f"**A diagnosis of the benchmark itself.** The ablation shows that GraphSAGE on node degree alone reaches F1 {x['deg']}, so the injected structure is easy and the headline score must not be read as real-platform accuracy.",
          f"**A working application.** FastAPI with JWT roles and SQLite, a React moderator interface, one-click setup, and a smoke test of {F.SMOKE_TOTAL} checks that all pass."),
    ]


# ---------------------------------------------------------------- document 10: scope and limitations
def scope_blocks():
    return [
        H2("1.1 In scope"),
        B("Building one social graph from public data and a seeded generator, with accounts as nodes and interactions (ties) as undirected edges.",
          "Engineering 23 node features from profile metadata, posting behaviour, temporal pattern and interaction frequency.",
          "Training and comparing GCN, GAT and GraphSAGE against a feature-only baseline on one stratified split, with three seeds.",
          "Scoring every account, explaining the score and showing the account's neighbourhood.",
          "Detecting coordinated clusters with Louvain over embeddings and scoring them against the injected botnets.",
          "Evaluation with accuracy, precision, recall, F1, ROC-AUC and PR-AUC, confusion matrices, a threshold sweep, an error analysis and a feature-group ablation.",
          "A scalability sweep of training and inference time on CPU up to 36,264 accounts.",
          "A moderator queue with logged decisions and retraining; an analyst role that can only read.",
          "A local web application with an API, a database and a demonstration login, run on one Windows computer."),
        H2("1.2 Out of scope"),
        B("Collecting data from any live platform, or any use of real users' personal data.",
          "Text and linguistic features of posts (behavioural NLP is named in the batch abstract but is not implemented).",
          "Dynamic or temporal graph models; the graph is one static snapshot.",
          "Structural features from the base paper (Prüfer sequences, minimum spanning trees, closeness and PageRank); node degree enters the models only through message passing.",
          "Graph sampling, mini-batch training, GPU training and distributed processing for platform-scale graphs.",
          "Adversarial robustness: bots that adapt to the detector were not simulated.",
          "Production features: single sign-on, multi-factor authentication, rate limiting, TLS, auditing, monitoring and deployment automation.",
          "Automatic blocking or removal of accounts: BotGraph flags and a human decides."),
        H2("1.3 Users and environment"),
        P("The intended users are a platform trust-and-safety team (overview, clusters), moderators (queue, decisions, retraining) and researchers (model comparison and scalability). "
          "The brief names large regional platforms such as ShareChat and Moj as the motivation; no data from them was used. "
          f"All measurements were made on one machine: {F.HARDWARE}."),
    ]


def assumption_blocks():
    return [
        P("The results depend on the following assumptions, which were made on purpose and are stated so that they can be challenged."),
        B("**Public data stands in for platform data.** Real topology plus real labelled profile rows is assumed to resemble the structure and attributes of a social platform closely enough to compare architectures; it is not assumed to match any specific platform.",
          "**Injected botnets stand in for coordination.** Bots that follow each other densely (probability 0.28 per pair), share a creation window and a peak hour, and follow some real accounts are assumed to be a reasonable model of one kind of coordination.",
          "**Camouflage sets the difficulty.** Giving 40 % of botnet members and 25 % of lone spammers a genuine-looking profile, and 6 % of genuine accounts a fake-looking one, is assumed to keep the task from being solved by the profile alone.",
          "**Labels are correct.** The label of every account is taken as ground truth, apart from the deliberate camouflage; no label noise was added or measured.",
          "**Transductive setting.** The whole graph, including test accounts' features and ties, is visible during training; only training labels are used in the loss. This matches a platform scoring its own existing accounts but not scoring a new account that was never in the graph.",
          "**Undirected, unweighted ties.** Follows, likes and mentions are collapsed into one kind of tie.",
          "**Static snapshot.** Account behaviour is summarised in one set of features per account, without a timeline.",
          "**Moderators are right.** A confirm or dismiss decision is treated as the true label of every affected account; a wrong decision would be learned.",
          "**Timings are indicative.** The machine was shared with another job during the latency measurements."),
    ]


def limitation_blocks():
    x = _x()
    return [
        P("The limitations below are listed in order of how much they affect the reading of the results."),
        N(f"**The benchmark is easier in structure than a real platform.** The ablation trains GraphSAGE on a single feature, the logarithm of an account's number of ties, and obtains F1 {x['deg']}, above the model with all 23 features ({x['all']}); the no-graph model on the same single feature scores {x['deg_mlp']}. "
          "The injected botnets and lone spammers have a distinctive local pattern of ties, and message passing over degrees alone nearly solves the task. The headline F1 of "
          f"{F.f3(F.mean('sage', 'f1'))} therefore describes this benchmark and should not be read as accuracy on a real platform, and the graph's lift over the baseline (+{F.lift('sage'):.1f} points) is genuine for this data but partly produced by how the botnets were injected.",
          "**Half of the attribute signal is synthetic.** The temporal and interaction features are generated by the seeded script. They are the most valuable attribute group: removing the temporal group drops the baseline from "
          f"{x['all_mlp']} to {x['no_t_mlp']} and GraphSAGE from {x['all']} to {x['no_t']}. Posting behaviour adds nothing (GraphSAGE {x['no_post']} without it), because the Twitter bot label carries almost no signal.",
          "**Botnets are injected and seeded.** Recovery of 8 of 8 botnets measures how well the method finds this kind of coordination, a known-answer test; it says nothing about the recall of real botnets, whose members need not be densely tied or share a peak hour.",
          "**Profile rows and posting rows are not about the same people.** They are combined by resampling, which keeps realistic value ranges but not the real correlations between them.",
          f"**Lone spammers are the weak spot.** On the test split GraphSAGE caught all {x['bn_n']} botnet members (the baseline {x['bn_b']}) but only {x['ls_s']} of {x['ls_n']} lone spammers (the baseline {x['ls_b']}); all nine missed accounts are lone spammers with only 4 to 8 ties (median {x['deg_missed']} ties against {x['deg_caught']} for the fakes that were caught). "
          "Without a coordinated neighbourhood the graph has little to add.",
          "**One split and three seeds.** No cross-validation and no confidence interval beyond the standard deviation over three seeds; with 114 fake accounts in the test split, one account changes recall by 0.9 percentage points. GAT is the least stable (F1 from 0.877 to 0.922 across seeds) and is not deterministic between runs.",
          "**Confusion matrices are for one seed.** The stored confusion matrices and ROC curves belong to seed 0; the tables report means over three seeds.",
          f"**The threshold sweep is on the test split.** F1 stays between {x['f1_lo']} and {x['f1_hi']} for every threshold from 0.30 to 0.60, so the result does not hinge on the threshold, but the sweep's maximum ({x['peak_f1']} at {x['peak_t']}) is chosen on the test split itself and is for analysis only; the served threshold (0.5) was chosen on validation.",
          f"**Scalability was measured on copies.** Larger graphs are disjoint copies of the 4,533-account graph, which understates the cost of a well-mixed graph, and the largest ({F.scal_row(8)['nodes']:,} accounts) is far below a platform of millions. Full-batch training on a graph of millions of accounts would be a memory problem; sampling was not implemented.",
          "**Explanations are approximations.** Gradient × input is a first-order attribution; it does not prove that a trait caused the score.",
          "**Retraining evidence is thin.** The loop is demonstrated end to end, but F1 before and after a handful of demo decisions is a single-seed comparison and shows no reliable gain.",
          "**Security is for a demonstration.** Two seeded users with a shared password, a development JWT secret fallback, no TLS, no rate limiting and no token revocation.",
          "**No unit-test suite.** Testing consists of a 36-check end-to-end smoke test and the build-time interface checks; there is no pytest suite, load test or adversarial test.",
          "**Environment.** The system Python on the measuring machine needed PyTorch imported before FastAPI to load (WinError 1114 otherwise); the project's own `.venv`, created by `setup.bat`, is not affected and is not shipped."),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, and no figure for them appears in any document."),
        B("Performance on real, independently labelled botnets or on a benchmark such as TwiBot-22.",
          "Cross-validation, repeated random splits, and significance tests between architectures.",
          "Robustness to label noise, to missing ties and to an adversary that adds ties or copies profiles.",
          "A direct numerical comparison with the base paper, RABot or HW-GNN on a shared dataset.",
          "The contribution of individual features inside a group; only whole groups were ablated.",
          "Accuracy on accounts that were absent from the graph at training time (inductive use).",
          "Memory use, and training or inference on graphs larger than 36,264 accounts; GPU timing.",
          "Behaviour under many simultaneous users; only single-client latency was measured.",
          "Gain from moderator feedback on real decisions; only the mechanism was tested.",
          "Usability with real moderators; the interface was checked by script at three screen widths in light and dark themes, not by a user study."),
    ]


# ---------------------------------------------------------------- document 12: walkthroughs and decisions
def walkthrough_blocks():
    return [
        P("This section walks through the code that carries the design. The listings are copied from the repository at the state in which the results were measured."),
        H2("3.1 The graph object and the GraphSAGE layer"),
        CODE(src("ml/gnn.py", 16, 32), 8),
        CODE(src("ml/gnn.py", 44, 51), 8),
        P("`Graph` is built once from the undirected tie list: both directions of every tie are stacked, self-loops are added for GCN and GAT, and two sparse matrices are prepared. `a_hat` holds the symmetric normalisation D̃^(-1/2) Ã D̃^(-1/2) used by GCN, "
          "and `a_mean` divides each row by the number of neighbours, so that a sparse product with a feature matrix returns the mean of each account's neighbours. "
          "`SAGELayer` then adds two linear maps: one for the account's own features and one, without a bias, for that neighbour mean. The separate weights are what distinguishes GraphSAGE from GCN here, "
          "and the two-line `forward` is the whole of the layer; no external graph library is involved."),
        H2("3.2 The class weights"),
        CODE(src("ml/gnn.py", 113, 116), 8.5),
        P("The loss gives genuine accounts weight 1 and fake accounts the square root of the ratio of genuine to fake accounts in the training labels. With about one fake account in eight the weight is about 2.6, a middle course between ignoring the imbalance and weighting by the full ratio, which would favour recall at the cost of many false alarms. "
          "The counts are taken from the labels the loss will actually see, so after moderator feedback the weight changes with them."),
        H2("3.3 Botnet clustering"),
        CODE(src("ml/clustering.py", 17, 41), 8),
        P("`detect` keeps only accounts with a probability of at least 0.30, normalises their embeddings to unit length so that a matrix product gives cosine similarities, and takes each candidate's five most similar candidates with `argpartition`. "
          "Each similarity becomes a weighted edge (negative similarities are dropped). The loop over `edge_index` then adds weight 1.0 for every real tie between two candidates, creating the edge if it does not exist. "
          "Louvain runs on the weighted graph with a fixed seed so that clusters are reproducible, groups smaller than five accounts are discarded and the rest are sorted by size. "
          "The quadratic similarity matrix is acceptable because it covers only the few hundred candidates, not all accounts."),
        H2("3.4 Recording a moderator decision"),
        CODE(src("backend/app/routes/queue.py", 80, 101), 8),
        P("`require_moderator` is a dependency, so an analyst never reaches the body: the request returns 403 first. For an account the identifier must be a number inside the graph (422 and 404 otherwise); "
          "for a cluster the identifier must be a cluster that exists in the store, and the error message explains that cluster identifiers change after a retraining run. "
          "A decision on a cluster stores the full member list, so one row affects every member; the model's score at that moment is kept with it. "
          "The route only writes the row. The queue and the retraining job derive everything else (who is still pending, which labels to use) from the stored reviews, which makes undo a plain delete."),
        H2("3.5 Moderator labels enter training without touching the test split"),
        CODE(src("ml/train.py", 35, 45), 8.5),
        P("`feedback` maps account identifiers to 1 (confirmed) or 0 (dismissed). Accounts in the test split (`split == 2`) are filtered out before anything else, so they keep their original label in every evaluation. "
          "Labels of the remaining accounts replace the training labels in a copy (`y_train`), those accounts are added to the training set and removed from the validation set, and the number used is recorded. "
          "Evaluation always uses the original `y`, so a wrong moderator decision can distort training but cannot improve the reported test score."),
        H2("3.6 Explaining a score"),
        CODE(src("backend/app/services/store.py", 131, 152), 8),
        P("The method makes one forward pass with gradient tracking on the whole standardised feature matrix and back-propagates the margin between the fake and genuine logits for one account. "
          "Multiplying the gradient by the input gives, for every account's every feature, a signed contribution to that margin. The account's own row becomes the bars the moderator sees; the sum of all other rows is reported as a single 'what the neighbours add' figure. "
          "Results are cached per account with `lru_cache`, the store's lock serialises access to the shared model, and the cache is cleared when the store reloads after retraining."),
    ]


def decision_blocks():
    return [
        P("Each decision below was taken for a reason that can be traced to the code, the data or the machine."),
        TAB("Implementation decisions and their reasons", ["Decision", "Reason"],
            [["Layers written in plain PyTorch on sparse tensors instead of torch-geometric", "torch-geometric wheels on Windows are a frequent build failure, which would break the one-click setup; the three layers are short, and writing them made the aggregation (mean, symmetric normalisation, edge softmax) explicit. The cost is that GAT, written with `scatter_reduce` and `index_add_`, is not bit-for-bit reproducible between runs."],
             ["Full-batch training on the whole graph", "The graph has 4,533 nodes, so one forward pass takes tens of milliseconds; full batch is the simplest correct choice. It does not scale beyond a graph that fits in memory, which is listed as a limitation."],
             ["One stratified split shared by every model", "Differences between models must come from the model, not from the accounts it happened to see. Stratification keeps the 12.6 % fake share in every part."],
             ["Feature-only baseline with the same budget", "It is the control that shows what the graph adds."],
             ["Three seeds, mean and standard deviation", "A single seed could not separate GAT's variation from a real difference; three seeds on a CPU still take only a few minutes."],
             ["Square-root class weights and a validation-tuned threshold", "Accuracy is meaningless at a 12.6 % fake share; a full-ratio weight floods the moderator queue with false alarms; tuning on validation uses no test information."],
             ["Candidates at p ≥ 0.30 for clustering but flagging at the tuned threshold", "A looser cut lets borderline members of a botnet join their cluster through similarity and real ties; the cluster's *flagged share* still shows how many were confidently flagged."],
             ["Louvain over embedding kNN plus real ties", "Needs no number of clusters, is available in NetworkX without extra packages, and combines two kinds of evidence."],
             ["Reviewed accounts move to training; the test split is never relabelled", "Before and after retraining are measured on the same untouched test accounts, so the comparison is meaningful."],
             ["Used decisions cannot be undone", "A decision that has already shaped a trained model cannot be erased by deleting its row; the API answers 409 instead of pretending."],
             ["Artefacts loaded once into one in-memory `Store`", "Scores, clusters and the neighbour index are read-only between retraining runs, so every request is answered from memory in a few milliseconds; a lock protects the reload."],
             ["SQLite with write-ahead logging", "Only three small tables exist (users, decisions, runs); a file database needs no server and keeps the setup to one click. Foreign keys are switched on explicitly because SQLite ignores them by default."],
             ["JWT with a 12-hour lifetime and two roles", "Stateless sign-in is enough for a local demonstration; the role claim lets the same code serve analysts and moderators."],
             ["Retraining as a background thread with a status route", "Training all four models takes about a minute on this machine; the page stays responsive and shows progress. Only one run at a time is allowed."],
             ["Models and clusters committed as files", "The application starts in seconds and the reported numbers can be reproduced without training; `ml.train` regenerates them."],
             ["Real topology with seeded injected botnets", "No platform data can be shared; injected botnets give a known answer against which cluster recovery can be scored. The price is the benchmark bias described in the limitations."],
             ["No `.env` committed; fixed development secret as fallback", "The file may hold keys of other services; the application needs none of them, so a fresh checkout still runs."]],
            widths=[2.2, 4.4], align=["l", "l"], size=9.5),
    ]


# ---------------------------------------------------------------- Chapter 9
def conclusion_blocks():
    x = _x()
    sm, bm = F.MODELS["sage"], F.MODELS["baseline"]
    tn, fp, fn, tp = F.conf("sage")
    return [
        H2("9.1 Summary of the work"),
        P(f"This project built BotGraph, a system that finds fake accounts and coordinated botnets from the shape of a social graph. It assembles a graph of {F.NODES:,} accounts and {F.EDGES:,} ties from real Facebook ego-network topology, real labelled profile and posting rows and seeded injected botnets; "
          f"describes each account with {F.N_FEATURES} features; trains a feature-only baseline and GCN, GAT and GraphSAGE models on one split; clusters suspicious accounts with Louvain over the learned embeddings; "
          f"and serves scores, explanations, clusters and a moderator queue through a FastAPI backend and a React interface. The work was measured on a held-out test split, in a threshold sweep, an error analysis, a feature-group ablation and a scalability sweep, and verified with a smoke test of {F.SMOKE_TOTAL} checks."),
        H2("9.2 Objectives achieved"),
        TAB("The six objectives of the batch against the outcome", ["#", "Objective", "Outcome"],
            [["1", "Graph of accounts (nodes) and interactions (edges)", f"Met: {F.NODES:,} nodes, {F.EDGES:,} undirected ties ({F.REAL_EDGES:,} real, {F.INJ_EDGES:,} injected), documented schema"],
             ["2", "Node features: profile, posting behaviour, interaction frequency", f"Met: {F.N_FEATURES} features in four groups; no text features"],
             ["3", "Implement and compare GCN, GAT, GraphSAGE", f"Met: same split, features and budget, 3 seeds, plus a no-graph baseline; GraphSAGE best (F1 {F.f3(F.mean('sage', 'f1'))})"],
             ["4", "Detect botnet clusters from embeddings", f"Met on injected botnets: {F.REC['recovered']} of {F.REC['botnets']} recovered; real botnets not tested"],
             ["5", "Evaluate accuracy, precision, recall", "Met: six metrics, ROC and PR curves, confusion matrices, threshold sweep; labels are partly synthetic"],
             ["6", "Assess scalability", f"Met up to {F.scal_row(8)['nodes']:,} accounts and {F.scal_row(8)['edges']:,} ties on CPU, roughly linear; platform scale not tested"]],
            widths=[0.35, 2.3, 3.9], align=["c", "l", "l"], size=9.5),
        H2("9.3 Key findings"),
        N(f"**The graph helps, but not every architecture equally.** On the {F.TEST_N}-account test split GraphSAGE reaches F1 {F.mstd('sage', 'f1')} (precision {F.f3(F.mean('sage', 'precision'))}, recall {F.f3(F.mean('sage', 'recall'))}, ROC-AUC {F.f3(F.mean('sage', 'roc_auc'))}) against {F.mstd('baseline', 'f1')} for the no-graph baseline, a gain of {F.lift('sage'):.1f} points. "
          f"GAT gains {F.lift('gat'):.1f} points and GCN only {F.lift('gcn'):.1f}, with a recall ({F.f3(F.mean('gcn', 'recall'))}) below the baseline's ({F.f3(F.mean('baseline', 'recall'))}). In the seed-0 confusion matrix GraphSAGE makes {fp} false positives and {fn} false negatives among {F.TEST_N} accounts.",
          f"**The result does not hinge on the threshold.** F1 stays between {x['f1_lo']} and {x['f1_hi']} for every threshold from 0.30 to 0.60; the tuned threshold of 0.5 gave precision 0.972 and recall 0.921 at seed 0.",
          f"**Botnets are found, lone spammers less so.** All {x['bn_n']} botnet members in the test split were caught (the baseline {x['bn_b']}), but only {x['ls_s']} of {x['ls_n']} lone spammers (the baseline {x['ls_b']}); the graph rescued {x['rescued']} fake accounts the baseline missed, lost {x['lost']} and left {x['both']} missed by both. "
          f"Louvain over the embeddings recovered {F.REC['recovered']} of {F.REC['botnets']} injected botnets as single communities (mean recall {F.f3(F.REC['mean_recall'])}, mean precision {F.f3(F.REC['mean_precision'])}).",
          f"**The benchmark is structurally easy, and this limits what the headline number means.** GraphSAGE on node degree alone scores F1 {x['deg']}, above the model with all features ({x['all']}); the synthetic temporal group is the most valuable attribute group (removing it lowers GraphSAGE to {x['no_t']} and the baseline to {x['no_t_mlp']}), and posting behaviour adds nothing. "
          "The high scores describe this benchmark with injected botnets, not a real platform.",
          f"**Cost grows roughly in proportion to the number of ties.** From {F.scal_row(1)['nodes']:,} to {F.scal_row(8)['nodes']:,} accounts a GraphSAGE epoch took {F.scal_row(1)['models']['sage']['train_seconds_per_epoch']:.3f} s and then {F.scal_row(8)['models']['sage']['train_seconds_per_epoch']:.3f} s; GAT took {F.scal_row(1)['models']['gat']['train_seconds_per_epoch']:.3f} s and then {F.scal_row(8)['models']['gat']['train_seconds_per_epoch']:.3f} s. GraphSAGE is both the most accurate and the cheapest graph model here.",
          f"**The application behaves as specified.** The smoke test passes {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks, API reads take a median of 3 to 16 ms, and the moderator loop records decisions, retrains and logs F1 before and after without touching the test split.",
          f"**Against the base paper.** PruferNET{c('base')} classifies nodes by spanning-tree depth and reports {F.pct(F.BASE_PAPER_RESULTS['with_prufer_acc'], 2)} accuracy; BotGraph detects fake accounts on a partly synthetic imbalanced graph. The tasks, labels and data differ, so the numbers are not compared; the shared finding is that structural information improves a GraphSAGE node classifier."),
        H2("9.4 Practical applications"),
        B("**Trust-and-safety triage.** A ranked queue of flagged accounts with reasons and neighbourhood, in place of a flat list of reports.",
          "**Coordinated-behaviour review.** A moderator can act on a whole botnet in one decision after inspecting its shared peak hour, creation spread and tie density.",
          "**Model selection for graph-based moderation tools.** The comparison with a no-graph control shows how much a graph model is worth before its cost is accepted.",
          "**Teaching and research.** The code is a compact, readable reference implementation of three GNN layers, community detection and a human-in-the-loop workflow."),
        H2("9.5 Known limitations"),
        P(f"The injected botnets are densely tied and share timing, so cluster recovery and the graph's lift are measured on an easy case (degree alone gives F1 {x['deg']}); half of the attribute signal is synthetic; text features, temporal graphs and real labelled botnets are absent; "
          "evaluation uses one split and three seeds; scalability was tested to 36 k accounts with copies of the graph; and security is for a demonstration. Chapter 10 turns each into future work."),
    ]


def future_blocks():
    x = _x()
    return [
        H2("10.1 Improvements to the models and the evidence"),
        N(f"**Harder, less structurally distinctive botnets.** The degree-only result ({x['deg']}) shows that the injected botnets are easy. A next benchmark should vary botnet density, mix bots into the real community structure, use bots with ordinary degree and add bots that imitate real neighbourhoods.",
          "**Real labelled botnets.** Evaluate on public bot-detection benchmarks with real accounts and labels (for example TwiBot-20 and TwiBot-22" + c("twibot20", "twibot22") + ") to replace the known-answer test with real-world evidence.",
          "**Structural features from the base paper.** Add Prüfer-sequence, closeness, PageRank and trust features" + c("base") + " to the node features and measure their value with the ablation already built, now that node degree is known to carry so much.",
          "**Text and behavioural NLP.** Add features from post text and language-model embeddings, as the batch abstract proposed and as LGB" + c("lgb") + " does for sparsely connected accounts, which would address the lone spammers that the graph does not catch.",
          "**Imbalance and noise handling.** Compare the class-weighted loss with graph augmentation and edge filtering in the style of RABot" + c("rabot") + " and with homophily-aware filtering as in HW-GNN" + c("hwgnn") + ".",
          "**Temporal graphs.** Replace the one-snapshot graph with a sequence of snapshots or a dynamic graph model" + c("botdgt", "bottgcl") + " so that bots can be found by how their ties and activity change.",
          "**Rigorous evaluation.** Repeated stratified cross-validation, confidence intervals, significance tests between architectures, and a held-out set of accounts that were never in the graph (inductive evaluation)."),
        H2("10.2 Additional features"),
        B("Pairwise and group evidence in the queue: why two accounts are in one cluster, with the shared traits highlighted.",
          "Active learning: ask moderators about the accounts whose decisions would change the model most.",
          "Appeals and decision review by a second moderator; decision statistics per moderator.",
          "Export of confirmed accounts and clusters, and a feed of new flags.",
          "Alerts when a new cluster appears between two scoring runs."),
        H2("10.3 Scalability and deployment"),
        B("Neighbour sampling and mini-batch training (as in GraphSAGE's original design" + c("sage") + "), and a GPU path, so that graphs of millions of accounts fit in memory; measure on a real, well-mixed graph rather than copies.",
          "Incremental scoring of new accounts and ties without retraining the whole model.",
          "A pytest suite for the ML and API layers, a load test with many concurrent users, and a continuous-integration run of the smoke test.",
          "A production database (PostgreSQL), containerised deployment, TLS, single sign-on with multi-factor authentication, rate limiting, token revocation and an audit log.",
          "Monitoring for drift in score distributions and in the share of flagged accounts, with a scheduled retraining policy."),
        H2("10.4 Further research"),
        B("Robustness to adaptive bots that add ties to genuine accounts or copy profiles, and defences such as edge filtering.",
          "Explanations that are faithful rather than first-order: integrated gradients or subgraph explainers, compared with the gradient × input bars used here.",
          "Joint learning of classification and clustering, so that the embeddings are trained to separate botnets directly.",
          "Fairness and privacy: whether regional or language communities are flagged more often, and how to review accounts without exposing private content.",
          "A study with real moderators of whether the queue and the explanations speed up decisions and reduce errors."),
        H2("10.5 Priority of the future work"),
        TAB("Suggested order of future work", ["#", "Item", "Effort", "Why it matters"],
            [["1", "Harder benchmark and real labelled botnets", "Medium to large", "Replaces the known-answer test with evidence that survives outside the generator"],
             ["2", "Text features and the base paper's structural features", "Medium", "Targets the lone spammers the graph misses"],
             ["3", "Cross-validation, intervals, inductive evaluation", "Small", "Shows how much of the gap between models is noise"],
             ["4", "Neighbour sampling, GPU, real large graph", "Medium to large", "Tests the scalability claim where it matters"],
             ["5", "Authentication hardening, TLS, tests and deployment", "Medium", "Moves the demonstration towards a service"],
             ["6", "Adversarial testing", "Large", "Shows whether the detector survives bots that adapt"]],
            widths=[0.4, 2.7, 1.1, 2.4], align=["c", "l", "l", "l"], size=9.5),
    ]


def _future_trim(bl):
    if not F.REPORT:
        return bl
    out, skip = [], False
    for b in bl:
        if b[0] == "h2" and b[1].startswith("10.5"):
            skip = True
            continue
        if not skip:
            out.append(b)
    return out


_REPORT_DROP_ITEMS = ("**Model selection for graph-based", "**Teaching and research", "Active learning:", "Appeals and decision review", "Alerts when a new cluster",
                      "Incremental scoring", "Monitoring for drift", "Joint learning of classification", "Fairness and privacy", "A study with real moderators")


def _report_trim(bl):
    """Report mode only: shorter application and future-scope lists (documents 9, 12 and 15 keep the full text)."""
    out = []
    for b in bl:
        if b[0] in ("b", "n"):
            keep = [i for i in b[1] if not i.startswith(_REPORT_DROP_ITEMS)]
            if not keep:
                continue
            b = (b[0], keep)
        out.append(b)
    return out


def chapter9_blocks():
    bl = [H1("CHAPTER 9: CONCLUSION")] + conclusion_blocks()
    return _report_trim(bl) if F.REPORT else bl


def chapter10_blocks():
    bl = [H1("CHAPTER 10: FUTURE SCOPE")] + _future_trim(future_blocks())
    return _report_trim(bl) if F.REPORT else bl
