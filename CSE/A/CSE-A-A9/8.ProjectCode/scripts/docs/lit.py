"""Literature and framing data for the decks (Review 1, Review 2, final) and the IEEE paper.

Every literature fact was read in the PDFs of the base paper, RABot and HW-GNN, in the ICCS 2025 BotTGCL PDF, or in the arXiv abstract pages of LGB, BotDGT and MSGS
(see refs.REF_NOTES). Where a source gave no figure in what was read, the cell says so. Reference numbers match scripts/docs/refs.py (CITE keys).
The three batch-survey items that could not be verified (AdapTGN, the Arabic fake-news paper, the IJSR stacking paper) are not used for any claim here.
"""
from .refs import CITE as R

BASE_PAPER_TITLE = "PruferNET: An Augmented Graph Neural Network for Influential Node Detection in Social Networks"
BASE_PAPER_VENUE = "A. Saha, N. K. Sarkar, S. Pratihar - IEEE Access, vol. 14, 2026"

# [work, year, approach, finding / limitation]   (each cell <= 90 characters)
LIT_TABLE = [
    [f"Saha et al. [{R['base']}] (base paper)", "2026", "Prufer-sequence features from an MST + GraphSAGE; depth classes",
     "99.63 % vs 96.54 % accuracy on Facebook; influence task, no bot labels"],
    [f"Zhang et al., RABot [{R['rabot']}]", "2026", "Minority oversampling in subgraphs + RL edge filtering over GNN backbones",
     "Cresci-15 99.14 % acc / 98.94 % F1 (RGT); Twitter data; no cluster output"],
    [f"Liu et al., HW-GNN [{R['hwgnn']}]", "2025", "Learnable Gaussian-window spectral filters guided by homophily",
     "Five benchmarks, +4.3 % F1 on average; detection only, no coordinated groups"],
    [f"Zhou et al., LGB [{R['lgb']}]", "2024", "Fine-tuned language model on account text + pre-trained GNN",
     "Up to 10.95 % over baselines (two datasets); needs account text, not used here"],
    [f"He et al., BotDGT [{R['botdgt']}]", "2024", "Dynamic graph transformer over network snapshots",
     "Reports gains over static-graph methods; needs timestamped snapshots"],
    [f"Wang et al., BotTGCL [{R['bottgcl']}]", "2025", "Graph contrastive learning + temporal module on a dynamic graph",
     "Two benchmarks, low-label setting; abstract quotes no figure"],
    [f"Shi et al., MSGS [{R['msgs']}]", "2023", "Multi-scale graph filter with signed attention (high + low frequency)",
     "Outperforms several detectors; abstract quotes no figure"],
    [f"Feng et al., TwiBot-20 / BotRGCN [{R['twibot20']}], [{R['botrgcn']}]", "2021", "Twitter bot benchmark; relational GCN over follow and mention graphs",
     "Named as dataset / baseline in [" + str(R['rabot']) + "], [" + str(R['hwgnn']) + "]; not re-read here"],
    [f"Cresci [{R['cresci']}]", "2020", "Survey of a decade of social-bot detection work",
     "Overview of social-bot detection; cited in the introduction of [" + str(R['rabot']) + "]; not re-read here"],
]

# [work, approach, data, reported result, limitation]  - short cells for the IEEE paper's TABLE I
PAPER_TABLE = [
    [f"Base paper [{R['base']}]", "Prufer features + GraphSAGE", "SNAP Facebook, 4,039 nodes", "99.63 % vs 96.54 % acc.", "Influence task; no bots"],
    [f"RABot [{R['rabot']}]", "Oversampling + RL edge filter", "Cresci-15, Twibot-20, MGTAB", "99.14 % acc. (Cresci-15)", "Twitter only; no clusters"],
    [f"HW-GNN [{R['hwgnn']}]", "Gaussian-window spectral GNN", "Twibot-20/22, MGTAB, T-*", "+4.3 % F1 on average", "No coordinated groups"],
    [f"LGB [{R['lgb']}]", "Language model + GNN", "two real datasets", "up to +10.95 % over baselines", "Needs account text"],
    [f"BotDGT [{R['botdgt']}]", "Dynamic graph transformer", "bot benchmarks", "gain over static methods (no figure read)", "Needs snapshots"],
    [f"BotTGCL [{R['bottgcl']}]", "Contrastive + temporal GNN", "two benchmarks", "superior (no figure read)", "Needs time-stamped graph"],
    [f"MSGS [{R['msgs']}]", "Signed-attention multi-scale filter", "real bot datasets", "outperforms baselines (no figure read)", "Detection only"],
]

OBJECTIVES = [
    "Construct a graph of the platform: accounts as nodes, interactions as edges",
    "Engineer node features: profile metadata, posting behaviour, interaction frequency",
    "Implement and compare GCN, GAT and GraphSAGE for account classification",
    "Detect coordinated botnet clusters from the learned graph embeddings",
    "Evaluate accuracy, precision and recall against labelled fake-account data",
    "Assess scalability as the number of nodes and edges grows",
]

PROBLEM_STATEMENT = [
    "Fake profiles are created faster than manual moderation can remove them",
    "Per-account classifiers miss coordinated networks whose single profiles look legitimate",
    "Bot behaviour evolves quickly, so static rules and signatures go stale",
    "Class imbalance and label noise degrade conventional supervised models",
    "Need: a graph-based detector that classifies accounts from their relational context and exposes coordinated botnet clusters at scale",
]

EXISTING_SYSTEM = [
    "Manual moderation and user reports: slow, reactive, one account at a time",
    "Rule and signature filters on profile fields (no picture, digits in the username, low follower ratio)",
    "Per-account machine-learning classifiers on profile and posting features, with no view of who an account is tied to",
    "Graph-based bot detectors on Twitter benchmarks that output a label per account and no coordinated groups [" + str(R['rabot']) + "], [" + str(R['hwgnn']) + "]",
    "Influence-oriented GNN work on the same social graphs with no fake-account labels [" + str(R['base']) + "]",
]

LIMITATIONS_OF_EXISTING = [
    "Per-account models cannot see a botnet whose members each look genuine",
    "Static rules are learned by bot operators and evaded; they cannot adapt without a developer",
    "Imbalanced labels (about one fake account in eight here) inflate accuracy and hide poor recall",
    "Most bot-detection papers report a label per account, not the coordinated group, and rarely a moderator workflow",
    "Scalability is seldom measured, and GNN papers quote accuracy without cost per epoch or per inference",
    "The base paper's accuracy figures measure influence depth, not fake-account detection, so they cannot be reused as a bot-detection baseline",
]

GAPS = [
    "The base paper applies GNNs to influence and node classification; applying the same relational learning to fake-profile and botnet detection is the gap this project fills [" + str(R['base']) + "]",
    "Bot-detection GNN papers report per-account labels on Twitter benchmarks; coordinated clusters recovered from the learned embeddings, with a measured recovery rate, are rarely shown [" + str(R['rabot']) + "], [" + str(R['hwgnn']) + "]",
    "Architecture comparisons often change the data or tuning between models; GCN, GAT and GraphSAGE are rarely compared with a no-graph baseline on one split, features and training budget",
    "Moderator decisions are not fed back into training in the surveyed detectors, and the effect on a protected test split is not measured",
    "Scalability of training and inference as nodes and edges grow is seldom reported next to accuracy",
]
