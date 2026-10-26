"""Chapter 2: Literature Survey."""

from . import facts as F
from .blocks import B, H1, H2, H3, N, P, TAB
from .lit import GAPS
from .refs import CITE as R


def blocks():
    b = _full()
    if not F.REPORT:
        return b
    from .ch1 import trim
    return trim(b, drop=("Three difficulties recur", "The paper reports per-class precision", "The real and the synthetic parts of the data",
                         "The surveyed graph methods are strong detectors"))


def _full():
    base = R["base"]
    bp = F.BASE_PAPER_RESULTS
    base_rows = [
        ["Task", "Three-class node classification: each node of the SNAP Facebook graph is labelled Very Shallow, Shallow or Deep from its depth in a minimum spanning tree (MST), read as an influence proxy"],
        ["Data", "SNAP Facebook social circles, 4,039 nodes and 88,234 edges after pre-processing (largest connected component, self-loops and duplicates removed); Email-Eu-core (986 nodes, 16,064 edges) as a second network"],
        ["Features", "Degree, closeness and PageRank; a trust score (mean PageRank of the neighbours); and five features taken from the Prufer sequence of the MST: label frequency, sequence entropy, unique-label ratio, edge-transition influence and subtree depth"],
        ["Tree", "Edge weight 1 / (deg u + deg v); MST of the weighted graph; Prufer sequence of the tree"],
        ["Model", "GraphSAGE with 64 hidden units, dropout 0.5, AdamW (learning rate 0.003), 300 epochs, model chosen on validation accuracy"],
        ["Split", "60 % train, 20 % validation, 20 % test, one fixed random permutation; 5-fold cross-validation on Facebook reported as stable (the fold values are not given in the text)"],
        ["Reported result", "Test accuracy 99.63 % with Prufer features against 96.54 % without them on Facebook; on Email-Eu-core 93.43 % against 80.30 %"],
        ["Hardware", "Python on a machine with a T4 GPU and 16 GB of RAM"],
    ]
    compare_rows = [
        ["Task", "Influence: classify nodes by MST depth", "Fraud: classify accounts as fake or genuine, then group them into botnets"],
        ["Labels", "Derived from the graph itself (percentiles of MST depth); no fake-account labels", f"External labels: {F.FAKE} fake accounts ({F.pct(F.FAKE_SHARE)}) from labelled profile data and injected botnets"],
        ["Data", "SNAP Facebook (4,039 nodes / 88,234 edges); Email-Eu-core", f"SNAP Facebook topology ({F.REAL_NODES:,} nodes / {F.REAL_EDGES:,} ties) plus {F.INJ_NODES} injected accounts; Instagram and Twitter rows for attributes"],
        ["Features", "Centrality, trust score and Prufer-sequence features", f"{F.N_FEATURES} node attributes: profile, posting, temporal, interaction; structure enters through message passing"],
        ["Model", "GraphSAGE only", "GCN, GAT and GraphSAGE against a no-graph baseline, three seeds"],
        ["Output", "A depth class per node", "A fake-probability per account, the traits behind it, and a botnet cluster per flagged group"],
        ["Evaluation", "Accuracy, precision, recall, F1 over three depth classes", "Accuracy, precision, recall, F1, ROC-AUC, PR-AUC under a 1-in-8 class imbalance; cluster recovery; scalability"],
        ["Human in the loop", "None", "Moderator confirms or dismisses; decisions feed retraining on a protected test split"],
        ["Scale", "Not measured", f"Timed from {F.NODES:,} to {F.scal_row(8)['nodes']:,} accounts on CPU"],
    ]
    survey_rows = [
        ["1", "PruferNET (base paper)", "2026", "Read in full (PDF)"],
        ["2", "AdapTGN: adaptive temporal-relational GNN for bot detection", "2026", "Not verified: a web search found no page under this title"],
        ["3", "GNN approach for fake-news identification in Arabic", "2026", "Not verified: listed in the batch survey only"],
        ["4", "Bot detection using account metadata, feature selection and stacking (IJSR)", "2026", f"Exact title not found; the nearest match is Sharma and Borah on stacking over account-level data [{R['sharma']}]"],
        ["5", "LGB: language model and GNN-driven social bot detection", "2024 preprint", f"Found as an arXiv preprint [{R['lgb']}]; the venue named in the batch survey was not confirmed"],
    ]
    rel_rows = [
        [f"RABot [{R['rabot']}]", "Neighbourhood-aware oversampling of the minority class; reinforcement-learned edge filtering", "Cresci-15 99.14 % accuracy, 98.94 % F1 (RGT backbone); Twibot-20 87.92 % / 88.40 %; MGTAB 91.16 % / 89.03 % (RGCN)", "Twitter benchmarks only; a label per account; no clusters, no moderator loop"],
        [f"HW-GNN [{R['hwgnn']}]", "Learnable Gaussian windows over a spectral filter, steered by the homophily ratio", "Five benchmarks, average +4.3 % F1 over the best baselines", "Detection only; spectral filtering is costly to extend to new graphs"],
        [f"LGB [{R['lgb']}]", "Fine-tuned language model on account text, refined by a pre-trained GNN", "Up to 10.95 % better than baselines on two real datasets", "Needs account text, which this project does not use"],
        [f"BotDGT [{R['botdgt']}]", "Dynamic graph transformer over network snapshots", "Reports gains over static-graph methods (no figure read)", "Needs time-stamped snapshots"],
        [f"BotTGCL [{R['bottgcl']}]", "Graph contrastive learning plus a temporal module", "Two benchmarks; strong when labels are scarce (no figure read)", "Needs a time-stamped graph"],
        [f"MSGS [{R['msgs']}]", "Multi-scale graph filter with signed attention", "Outperforms several detectors (no figure read)", "Detection only"],
    ]
    algo_rows = [
        ["Topology", "SNAP Facebook ego networks", f"Real friendship ties between {F.REAL_NODES:,} accounts [{R['snap']}]; the same graph family as the base paper"],
        ["Profile attributes", "Labelled Instagram fake / spammer / genuine rows", f"Real labelled profile fields; CC BY 3.0 [{R['insta']}]"],
        ["Posting behaviour", "Twitter bot detection rows", f"Real posting statistics; CC0 [{R['twitter']}]; the label carries almost no signal, so these columns act as realistic noise"],
        ["Botnets", "Seeded generator, seed 7", f"{len(F.BOTNET_SIZES)} botnets of 34 to 62 accounts and {F.LONE_SPAMMERS} lone spammers so that clusters can be scored against a known answer"],
        ["Message passing", "GCN, GAT, GraphSAGE", f"Neighbourhood aggregation with symmetric normalisation [{R['gcn']}], attention [{R['gat']}] or a separate self weight and neighbour mean [{R['sage']}]"],
        ["Optimiser and regularisation", "Adam, dropout, ELU", f"Adam [{R['adam']}], dropout 0.3 [{R['dropout']}], ELU activation [{R['elu']}], class-weighted loss"],
        ["Community detection", "Louvain", f"Modularity optimisation [{R['louvain']}] through NetworkX [{R['networkx']}]"],
        ["Explanation", "Gradient times input", f"First-order attribution of the fake-versus-genuine margin [{R['gradxinput']}]"],
    ]
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        P("This chapter reviews the work on which the project builds. It first places the problem among the approaches to detecting fake accounts and bots, then analyses the base paper in detail, "
          "reviews related work by theme, lists the data and algorithms the project uses, and ends with the research gap that the design answers."),

        H2("2.1 Overview"),
        P(f"Social bot detection has been studied for more than a decade [{R['ferrara']}], [{R['cresci']}]. The methods fall into two broad families, as the introductions of recent papers "
          f"describe [{R['rabot']}]. Feature-based methods classify each account from its metadata or its text. Graph-based methods add the relations between accounts, and in the last "
          "five years most of them use graph neural networks. The graph-based turn was driven by a practical observation: operators of bots can imitate a human profile, and increasingly "
          "imitate human posting, but they cannot easily imitate a human's position in the network, and bots that are run together tend to be tied to one another."),
        P("Three difficulties recur in the recent papers and match the problem statement of this project. Bots are rare, so labelled data is heavily imbalanced. Bots forge links to genuine "
          f"accounts, which adds noise to the neighbourhood that a GNN aggregates [{R['rabot']}]. And the best-performing methods are tuned for one network, so a method that wins on one "
          f"benchmark may not transfer to another [{R['hwgnn']}]. The survey below is organised around those difficulties and around what each paper outputs: a label per account or something more."),
        P("The batch literature survey lists five works. Table 2.1 states how each was checked in this project; only checked items are used for any claim in this report."),
        TAB("Batch literature survey and its verification", ["No.", "Work as listed in the batch survey", "Year", "Status in this project"], survey_rows,
            widths=[0.4, 2.8, 0.9, 2.2], align=["c", "l", "c", "l"], size=9.5),

        H2("2.2 Base Paper Analysis"),
        H3("2.2.1 Problem and approach"),
        P(f"The base paper is PruferNET by Saha, Sarkar and Pratihar [{base}], published in IEEE Access in May 2026. Its starting point is that classical GNNs aggregate local neighbourhoods and "
          "struggle to capture global or hierarchical structure. To add such structure, the authors build a minimum spanning tree of the graph, convert the tree into a Prufer sequence "
          f"[{R['prufer']}] (a sequence of n-2 integers that encodes a labelled tree uniquely), and derive node features from that sequence. These are concatenated with degree, closeness, PageRank "
          "and a trust score, and passed to a GraphSAGE classifier. The authors state that their contribution is not a new GNN architecture but a tree-based global structural encoding that "
          "can be attached to an existing one, and that the encoding is deterministic and independent of training."),
        P("The target is also derived from the tree: nodes are labelled by their depth in the MST, split by percentiles into Very Shallow, Shallow and Deep, and the authors read depth as a "
          "proxy for how deeply embedded, and therefore influential, a node is."),
        H3("2.2.2 Evaluation protocol and reported numbers"),
        TAB("The base paper at a glance", ["Item", "As reported in the paper"], base_rows, widths=[1.3, 5.0], align=["l", "l"], size=10),
        P("The paper reports per-class precision, recall and F1 of 0.99 to 1.00 with Prufer features, and a weaker recall (0.93) for the Very Shallow class without them. It also reports a "
          "confusion matrix and a systematic ablation of the features."),
        H3("2.2.3 Strengths"),
        B("The idea is cheap and general: the encoding is computed once, needs no training, and can be attached to any GNN.",
          "Ablation (with and without Prufer features) isolates the contribution of the new features on the same model and split.",
          "A second network (Email-Eu-core) and 5-fold cross-validation are used to argue that the gain is not an accident of one graph or one partition.",
          "GraphSAGE is chosen for the right reason: it is inductive and aggregates sampled neighbourhoods, which suits large social graphs."),
        H3("2.2.4 Limitations"),
        B("**The target and the features come from the same tree.** Labels are percentiles of MST depth, and the feature set includes subtree depth and other quantities derived from the same "
          "MST. A large gain from such features is therefore not surprising; this report notes it as an observation about the setup, not as a claim made by the authors.",
          "**It is not a fraud task.** There are no fake-account labels, no class imbalance of the kind that bot detection faces, no coordinated groups and no adversary who is trying to "
          "avoid detection.",
          "**Evaluation is on accuracy over three depth classes.** The paper reports precision, recall and F1 per class, but none of the cost measures that matter to a moderator, "
          "such as false alarms among genuine users.",
          "**No scalability measurement**, although scalability is cited as a motivation; no run time or memory figures are given for the MST and Prufer step.",
          "**No end-user output.** The paper stops at a classification report."),
        H3("2.2.5 What this project keeps from the base paper and what it changes"),
        P(f"BotGraph keeps the family of data (the SNAP Facebook ego networks), GraphSAGE as one of the backbones, the 60/20/20 split and the idea that structure adds information a per-node "
          "model lacks. It changes the task, the labels, the model set, the outputs and the evaluation, as Table 2.3 shows. The Prufer-sequence features themselves are not implemented; they are "
          "listed as future work in Chapter 10."),
        TAB("Base paper compared with this project", ["Aspect", "Base paper", "This project"], compare_rows, widths=[1.0, 2.6, 2.7], align=["l", "l", "l"], size=9.5),
        P(f"The accuracy figures of the base paper (99.63 % and 96.54 %) measure how well depth classes are recovered. They say nothing about fake-account detection and are not used as a "
          "benchmark for BotGraph's results anywhere in this report."),

        H2("2.3 Related Work"),
        H3("2.3.1 Feature-based detection"),
        P(f"Early detectors treat each account as a row of metadata or text features and train a classifier [{R['cresci']}]. These models are fast and easy to explain, and the profile fields they "
          "use are the same ones this project keeps in its feature set: whether there is a picture, how many digits are in the username, how long the bio is, the follower-to-following ratio. Their "
          "weakness is the one named in the problem statement: a bot given a careful profile looks genuine row by row. The batch survey lists a 2026 study of stacking classifiers over "
          f"account metadata; the nearest match that could be found is [{R['sharma']}], cited here only to show that metadata-only stacking remains an active line. This project's no-graph baseline "
          "plays the role of the feature-based family: same features, same split, same training budget."),
        H3("2.3.2 Graph-based detection and the architectures compared here"),
        P(f"Graph convolutional networks [{R['gcn']}] update a node from a symmetrically normalised sum over its neighbours and itself. Graph attention networks [{R['gat']}] learn a weight for "
          f"each neighbour. GraphSAGE [{R['sage']}] keeps a separate weight for the node's own features and for the mean of its neighbours, and was designed to generalise to unseen nodes. "
          f"A relational variant, BotRGCN, was applied to Twitter bot detection with separate relation types [{R['botrgcn']}], and the TwiBot benchmarks [{R['twibot20']}], [{R['twibot22']}] "
          f"standardised evaluation; both are described in the recent papers [{R['rabot']}], [{R['hwgnn']}] that this survey did read in full. The three architectures chosen by the batch "
          "objectives are the standard spatial GNNs, and the survey shows them used as backbones and baselines in current work; this project compares them head to head, which the surveyed "
          "papers use mainly as baselines."),
        H3("2.3.3 Imbalance and noisy links"),
        P(f"RABot [{R['rabot']}] treats two practical problems together. Because bots are costly to create, the minority class is small; the authors interpolate minority-class embeddings "
          "within local subgraphs to stabilise the decision boundary. Because bots forge links, they train a reinforcement-learning agent to remove spurious edges during message passing. "
          "On three benchmarks and four GNN backbones (GCN, GAT, RGT and RGCN) the paper reports the best accuracy and F1 in each case, for example 99.14 % accuracy and 98.94 % F1 on Cresci-15 and "
          "87.92 % and 88.40 % on Twibot-20, and average gains of 2.0 to 3.0 points over the plain backbones. The framing is the one adopted here: imbalance is handled in this project by "
          f"a class-weighted loss with a validation-tuned threshold (the classic alternative is oversampling [{R['smote']}]), and noisy or forged links are not filtered out: camouflage is built into the data ("
          "40 % of botnet accounts have genuine-looking profiles) so that every model is tested against it."),
        H3("2.3.4 Spectral and multi-scale filters"),
        P(f"HW-GNN [{R['hwgnn']}] argues that low homophily corresponds to high-frequency spectral energy and that bots live in particular frequency bands, so it uses learnable Gaussian windows to "
          "focus a polynomial spectral filter, and a loss that ties the windows to the graph's homophily ratio. It evaluates on five benchmarks that range from 39,357 users (T-Finance) to "
          "5,781,065 users (T-Social), and reports an average gain of 4.3 % in F1. MSGS [" + str(R['msgs']) + "] uses a multi-scale filter with signed attention so that both low- and high-frequency "
          "information is retained and over-smoothing is reduced. Both show that GNN bot detection is still developing; neither returns coordinated groups, and both are heavier than the "
          "spatial layers used here."),
        H3("2.3.5 Language and time"),
        P(f"LGB [{R['lgb']}] observes that many bots have few connections and so escape purely graph-based methods; it fine-tunes a language model on account text and refines the result with a "
          "pre-trained GNN, reporting gains of up to 10.95 % over baselines on two real datasets. Dynamic-graph methods such as BotDGT "
          f"[{R['botdgt']}] and BotTGCL [{R['bottgcl']}] model how the network evolves, on the grounds that a static snapshot can be evaded by bots that interact with real users. "
          "Both lines are outside the scope of this project, which uses a single static graph and no text, and both are listed as future work."),
        H3("2.3.6 Community detection and coordinated behaviour"),
        P(f"Coordinated accounts form dense groups. The standard way to find such groups is modularity-based community detection, and Louvain [{R['louvain']}] is the usual algorithm because it "
          "scales to large graphs. The surveyed bot detectors stop at a per-account label. This project applies Louvain to a graph built from the learned embeddings (which carry the "
          "attribute and neighbourhood signal) and from real ties between flagged accounts, so that the group, and not only the account, becomes the unit a moderator acts on."),

        H2("2.4 Datasets and Algorithms Used in This Project"),
        TAB("Data and algorithms of this project", ["Element", "Choice", "Note"], algo_rows, widths=[1.3, 1.7, 3.3], align=["l", "l", "l"], size=9.5),
        P("The real and the synthetic parts of the data are kept apart throughout the report: the topology and the profile and posting rows are real, the botnets, the timing and interaction "
          "features and the handles are generated, and the two labelled sources describe different people. Chapter 6 gives the details."),

        H2("2.5 Strengths and Limitations of the Surveyed Work"),
        TAB("Related work compared", ["Work", "Approach", "Reported result", "Limitation for this project"], rel_rows,
            widths=[1.0, 1.9, 1.9, 1.5], align=["l", "l", "l", "l"], size=8.5),
        P("The surveyed graph methods are strong detectors. In the parts read for this survey they share three properties that matter here: they are evaluated on Twitter-style benchmarks with a label "
          "per account, none of them returns coordinated groups, and none describes a workflow in which a moderator's decisions feed back into the model. Whether they were compared with a no-graph "
          "baseline on identical features, and how their cost grows with the graph, is left open by this survey and is measured directly for the four models of this project."),

        H2("2.6 Research Gap"),
        P("The batch survey states the gap in one sentence: the surveyed work applies GNNs to influence and node classification in social graphs, and the gap is applying the same relational "
          "learning specifically to fake-profile and botnet detection at platform scale. The survey above refines it into five points:"),
        N(*GAPS),
        P("BotGraph answers these points on a benchmark of 4,533 accounts: it applies GCN, GAT and GraphSAGE to fake-account labels, compares them with a feature-only baseline under identical conditions, "
          "recovers coordinated clusters from the embeddings, closes the loop with moderator decisions, and measures cost as the graph grows. What it does not answer is also part of the gap: "
          "real-world botnets, platform-scale graphs, text and time."),
    ]
