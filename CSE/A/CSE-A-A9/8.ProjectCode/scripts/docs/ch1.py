"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB
from .refs import CITE as R


def _key(b):
    """First piece of text of a block, used to find blocks to drop or replace in report mode."""
    v = b[1]
    return v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else "")


def trim(blocks, drop=(), drop_sections=(), replace=None, table_rows=None):
    """Report-mode trimming. drop: block-text prefixes to remove; drop_sections: heading prefixes whose whole section
    (up to the next heading of the same or higher level) is removed; replace: {prefix: block}; table_rows: {caption prefix: keep(row)}."""
    replace = replace or {}
    table_rows = table_rows or {}
    out, skip_level = [], None
    for b in blocks:
        if b[0] in ("h1", "h2", "h3"):
            lvl = int(b[0][1])
            if skip_level is not None and lvl <= skip_level:
                skip_level = None
            if skip_level is None and any(b[1].startswith(x) for x in drop_sections):
                skip_level = lvl
        if skip_level is not None:
            continue
        k = _key(b)
        if any(k.startswith(x) for x in drop):
            continue
        hit = next((x for x in replace if k.startswith(x)), None)
        if hit:
            if replace[hit] is not None:
                out.append(replace[hit])
            continue
        if b[0] == "tab":
            cap = next((x for x in table_rows if b[1].startswith(x)), None)
            if cap:
                b = ("tab", b[1], b[2], [r for r in b[3] if table_rows[cap](r)], b[4], b[5], b[6])
        out.append(b)
    return out


def blocks():
    b = _full()
    if not F.REPORT:
        return b
    return trim(b, drop=("A last piece of motivation", "In outline, the pipeline has five steps", "None of the limits above changes"))


def _full():
    base = R["base"]
    sage, base_f1, gcn_l, gat_l = F.mean("sage", "f1"), F.mean("baseline", "f1"), F.lift("gcn"), F.lift("gat")
    obj_rows = [
        ["1", "Construct a graph representation of the platform with accounts as nodes and interactions as edges",
         f"Graph builder: {F.NODES:,} accounts and {F.EDGES:,} undirected ties ({F.REAL_EDGES:,} real, {F.INJ_EDGES:,} injected), documented node and edge schema"],
        ["2", "Engineer node features covering profile metadata, posting behaviour and interaction frequency",
         f"{F.N_FEATURES} features in four groups (12 profile, 4 posting, 6 temporal, 1 interaction); no text features"],
        ["3", "Implement and compare GCN, GAT and GraphSAGE for account classification",
         "Three architectures written in plain PyTorch, one stratified split, same features and budget, three seeds, plus a no-graph baseline"],
        ["4", "Detect coordinated botnet clusters from the learned graph embeddings",
         f"Louvain over an embedding-similarity graph; {F.REC['recovered']} of {F.REC['botnets']} injected botnets recovered"],
        ["5", "Evaluate detection accuracy, precision and recall against labelled fake-account data",
         "Accuracy, precision, recall, F1, ROC-AUC and PR-AUC on a held-out test split of 908 accounts"],
        ["6", "Assess scalability as the number of nodes and edges grows",
         f"Training and inference time timed from {F.NODES:,} to {F.scal_row(8)['nodes']:,} accounts ({F.scal_row(8)['edges']:,} ties) on CPU"],
    ]
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P(f"This chapter introduces the domain of the project, the motivation for building {F.PRODUCT}, the problem it addresses, the objectives set for it, the scope that "
          "was actually delivered, its contributions, and the limitations and assumptions that govern every result reported later. It closes with a map of the rest of the report."),

        H2("1.1 Domain"),
        P("An online social platform is a network. Accounts are connected by follows, likes, comments and mentions, and what a user sees, believes and shares is shaped by the people "
          "around them. The same property that makes the platform useful makes it a target. A fake account is a profile that does not belong to the person or organisation it "
          "claims to represent; a bot is an account operated by software; a botnet is a set of such accounts run together by one operator. Their uses are well documented: "
          f"spreading misinformation, inflating follower and engagement counts, amplifying chosen content and manipulating public opinion [{R['ferrara']}], [{R['cresci']}]."),
        P("Detecting them is a classification problem, but not a standard one. The label of interest, fake or genuine, depends on the account's own attributes and also on who it is "
          "connected to and who those accounts are connected to. This is why the domain is called deep learning for social network security: the data is a graph, and the models "
          "that read graphs directly are graph neural networks. A graph neural network (GNN) repeatedly lets every node collect a summary of its neighbours' features, so that after "
          f"two rounds an account's representation already reflects the accounts two ties away [{R['gcn']}], [{R['sage']}]."),

        H2("1.2 Background and Motivation"),
        P("The motivation is stated in the project abstract. Indian social platforms are growing quickly, and with them the number of fake profiles and automated botnets that "
          "threaten user privacy and digital trust. Regional platforms with very large user bases, such as ShareChat and Moj named in the batch abstract, cannot staff moderation "
          "at the pace at which accounts are created, so the moderators who remain need to be pointed at the accounts and groups that matter most."),
        P("Two approaches dominate current practice. Rule-based filters look at profile fields, for example a missing profile picture, many digits in a username or a very low "
          "follower-to-following ratio. Classical machine-learning classifiers combine such fields with posting statistics. Both examine each account alone. A botnet defeats "
          "them by design: each member can be given a plausible profile, while the members follow and like one another and are created and active in the same time windows. "
          "The coordination is a property of the group and of the ties, so it is visible in the graph and invisible in any single row of a table."),
        P("Graph-based bot detectors exist and report strong results on Twitter benchmarks. Two recent examples concentrate on the difficulties named in this project's problem "
          f"statement: RABot addresses class imbalance and noisy links with minority oversampling and reinforcement-learned edge filtering [{R['rabot']}], and HW-GNN uses spectral "
          f"filters guided by the homophily of the graph [{R['hwgnn']}]. The base paper of this project, PruferNET [{base}], applies GraphSAGE to the Facebook social-circles graph with "
          "structural features derived from a minimum spanning tree and a Prufer sequence, but its task is to find influential nodes, not fake ones. What is missing is a complete, "
          "runnable system that takes the GNN idea through to the output a trust-and-safety team needs: a score per account, the coordinated group the account belongs to, and a way "
          "for a moderator to confirm or dismiss it and teach the model."),

        P("Class imbalance deserves its own mention because it shapes every number in the report. In the data used here about one account in eight is fake. On such data accuracy is a weak "
          "measure: a classifier that never raises an alarm is right for most accounts. A moderator's cost is counted in two ways, accounts that are wrongly flagged (precision) and fake "
          "accounts that are missed (recall), so the project reports both, together with F1 and the area under the ROC and precision-recall curves, and tunes the decision threshold on a "
          "separate validation split and not on the test accounts."),
        P("A last piece of motivation is the human side. A score alone does not remove an account. A trust-and-safety team has to decide, and in doing so produces exactly the labelled "
          "examples that the next training round needs. The project therefore keeps the moderator in the loop: the queue lists flagged accounts and clusters, each decision is stored with "
          "the model's score at that moment, and a retraining run turns the decisions into labels without ever touching the test accounts."),

        H2("1.3 Problem Statement"),
        P("The batch problem statement lists four weaknesses of current practice:"),
        B("fake profiles are created faster than manual moderation can remove them;",
          "per-account classifiers miss coordinated networks whose individual profiles appear legitimate;",
          "bot behaviour evolves quickly, so static rules and signatures become obsolete;",
          "class imbalance and label noise degrade conventional supervised models."),
        P("The problem addressed here is to build and evaluate a graph-based detector that classifies every account from its relational context, exposes coordinated botnet "
          "clusters, and does so at a scale that grows in proportion to the size of the graph rather than faster."),

        H2("1.4 Need for the Work"),
        B("**Relational evidence.** A fake account with a genuine-looking profile can only be recognised from its neighbourhood. The project needs to show how much the graph adds "
          "over the same features without it, on the same split.",
          "**Coordinated groups, not isolated labels.** Moderators act on groups. A detector that returns a probability per account but no cluster leaves the grouping to a human.",
          "**Honest measurement under imbalance.** About one account in eight is fake in this data, so a model that predicts \"genuine\" for everyone is "
          f"{F.pct(1 - F.FAKE_SHARE)} accurate. Precision, recall and F1 on the fake class are the numbers that matter, and the report leads with them.",
          "**A system a reviewer can run.** A scored account list, a cluster view, a moderator queue with retraining and a model-comparison page make the method inspectable by people "
          "who do not read code."),

        H2("1.5 Objectives"),
        P("The six objectives set for the project, and what each became, are summarised in Table 1.1. Chapter 8 returns to this table with the measured outcome for each."),
        TAB("Project objectives and how each was addressed", ["No.", "Objective", "How it was addressed"], obj_rows, widths=[0.5, 2.8, 3.0], align=["c", "l", "l"], size=10),
        P("Objective 2 lists profile metadata, posting behaviour and interaction frequency, and all three are covered. The batch abstract also mentions linguistic cues; text features "
          "were not built, and the report says so wherever the feature set is described."),

        H2("1.6 Scope"),
        P(f"{F.PRODUCT} consists of a machine-learning pipeline, a service and a web application:"),
        B(f"**Graph builder and features**: the social topology of ten Facebook ego networks ({F.REAL_NODES:,} accounts, {F.REAL_EDGES:,} ties), labelled profile rows from an Instagram "
          f"fake-account set, posting rows from a Twitter bot set, and {F.INJ_NODES} injected accounts (eight botnets and {F.LONE_SPAMMERS} lone spammers) with {F.INJ_EDGES:,} injected ties, "
          f"giving {F.N_FEATURES} node features.",
          "**Models**: a feature-only baseline and GCN, GAT and GraphSAGE, trained with a class-weighted loss, early stopping on validation F1 and a validation-tuned threshold; "
          "gradient-times-input attribution for the traits behind each score.",
          "**Botnet clusters**: Louvain community detection over the embeddings of accounts scored at 0.30 or more, with a description of each cluster.",
          f"**Service and application**: a FastAPI service (port {F.API_PORT}) with JWT sign-in, two roles and a SQLite store for users, moderator decisions and retraining runs; a React "
          f"application (port {F.WEB_PORT}) with a landing page, sign-in and eight working screens: overview, graph and features, accounts, account detail, clusters, cluster detail, moderator queue and models.",
          f"**Evidence**: a three-seed comparison, a scalability sweep, a threshold sweep, an error analysis, a feature-group ablation, a {F.SMOKE_TOTAL}-check smoke test and measured API latency."),
        P("In outline, the pipeline has five steps. The graph builder merges the real topology with the injected accounts and writes one graph file with node features, labels and a "
          "fixed split. Training fits the four models on the training accounts, picks the epoch and the threshold on the validation accounts, and scores every account once. Clustering takes the "
          "accounts scored at 0.30 or more and groups them by embedding similarity and shared ties. The service loads these artefacts once at start-up and answers every request from memory and "
          "from a small SQLite store. The web application shows the results and sends moderator decisions back to the service."),
        P("Out of scope are live platform ingestion, text and language-model features, dynamic (time-evolving) graphs, training on GPUs or on graphs of millions of accounts, adversarial "
          "robustness testing, and the Prufer-sequence features of the base paper. Section 1.8 and Chapter 8 return to these."),

        H2("1.7 Contributions"),
        N("An end-to-end graph-based fake-account system, from graph builder to moderator queue, with a documented schema, a REST API, role-based access and a smoke test that passes "
          f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks.",
          f"A controlled comparison of GCN, GAT and GraphSAGE with a no-graph baseline on one split: mean F1 over three seeds is {F.f3(base_f1)} for the baseline, "
          f"{F.f3(F.mean('gcn', 'f1'))} for GCN, {F.f3(F.mean('gat', 'f1'))} for GAT and {F.f3(sage)} for GraphSAGE (precision {F.f3(F.mean('sage', 'precision'))}, recall {F.f3(F.mean('sage', 'recall'))}). "
          f"The comparison shows that the gain is not automatic: GCN adds only {gcn_l:.1f} F1 point and loses recall.",
          f"Botnet clusters recovered from the learned embeddings: all {F.REC['recovered']} injected botnets come back as single communities (mean recall {F.f3(F.REC['mean_recall'])}, "
          f"mean precision {F.f3(F.REC['mean_precision'])}), together with one loose group that the application labels as diffuse.",
          "A moderator feedback loop whose retraining leaves the test split untouched, so the effect of each round is measured on the same accounts.",
          f"A scalability measurement from {F.NODES:,} to {F.scal_row(8)['nodes']:,} accounts showing training and inference time growing roughly in proportion to the number of ties."),

        H2("1.8 Limitations and Assumptions"),
        P("The conclusions of this report hold under the following limitations and assumptions."),
        B("The botnets are injected into the real topology with known membership. Cluster recovery therefore measures how well the method finds this kind of coordination, "
          "not how well it finds botnets in the wild.",
          f"Several feature columns are synthetic: the six temporal features and the interaction-frequency feature (generated with a bot-leaning setting for non-camouflaged bots, so they carry label signal by construction), and the handles and display names. Profile rows and posting rows come from different datasets and are combined by "
          f"resampling, which keeps realistic value ranges but not real correlations. {F.CAMO_BOTS} bots were given genuine-looking profiles and {F.SUSPICIOUS_GENUINE} genuine accounts "
          "fake-looking ones on purpose, because otherwise the profile alone would solve the task.",
          "The graph is a single static snapshot; there is no time dimension in the ties.",
          "Evaluation uses one stratified split and three training seeds, with no cross-validation. GAT results can shift by about a hundredth between runs because its edge softmax "
          "sums in a non-deterministic order.",
          "Scalability was measured to 36 thousand accounts by copying the graph as disjoint components, on a CPU. This does not establish behaviour on a platform with millions of accounts.",
          f"The base paper's numbers measure a different task and are not comparable with these results. All timings come from one shared machine ({F.HARDWARE}) and are indicative.",
          "Authentication is a demonstration: two seeded users, JWT sign-in, no password reset, multi-factor step or rate limiting."),
        P("None of the limits above changes the comparison between the four models, which uses one dataset and one split for all of them. They do limit what the absolute numbers say about real platforms."),

        H2("1.9 Organisation of the Report"),
        B("**Chapter 2** surveys the literature, analyses the base paper and states the research gap.",
          "**Chapter 3** studies feasibility; **Chapter 4** analyses the existing system and the requirements of the proposed one.",
          "**Chapter 5** presents the system design: architecture, data flow diagrams, UML, database, modules and screens.",
          "**Chapter 6** describes the methodology and the software implementation: data, features, models, clustering, API, security and installation.",
          "**Chapter 7** reports system testing; **Chapter 8** reports results and output screens, with the position against the base paper.",
          "**Chapters 9 and 10** give the conclusion and the future scope, followed by the references and three appendices (important code, installation and user guide, additional screens)."),
    ]
