"""Chapter 6 - Methodology and software implementation (BotGraph).

methodology_blocks()  -> 6.1-6.8  (document 9 part 1; full report)
application_blocks()  -> 6.9-6.12 (document 12 part 2; full report)
blocks()              -> chapter heading + both halves
"""
import os

import numpy as np

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB

try:
    from .refs import CITE as _R
except Exception:  # pragma: no cover - refs.py is written by another module
    _R = {}


def c(*keys):
    """Citation such as ' [3], [7]' from CITE keys; empty when a key is not in the reference list."""
    ids = [str(_R[k]) for k in keys if k in _R]
    return (" [" + "], [".join(ids) + "]") if ids else ""


def _fig(name, caption, width=5.6, kind="figs"):
    path = F.fig(name) if kind == "figs" else F.diag(name)
    if not os.path.exists(path):
        print("ch6: missing", path)
        return []
    return [FIG(path, caption, width)]


_LABELS = {
    "has_profile_pic": "Has profile picture", "username_digit_ratio": "Digits in username", "fullname_words": "Words in display name",
    "fullname_digit_ratio": "Digits in display name", "name_equals_username": "Name equals username", "bio_length": "Bio length",
    "has_external_url": "Has external link", "is_private": "Private account", "log_posts": "Posts (log)", "log_followers": "Followers (log)",
    "log_following": "Following (log)", "follower_following_ratio": "Follower / following ratio (log1p)",
    "log_avg_retweets": "Average retweets (log)", "avg_mentions": "Average mentions per post", "avg_post_length": "Average post length",
    "hashtags_per_post": "Hashtags per post", "log_account_age_days": "Account age (log days)", "log_posts_per_day": "Posts per day (log)",
    "posting_burstiness": "Posting burstiness", "peak_hour_share": "Share of activity in peak hour", "peak_hour_sin": "Peak hour (sine)",
    "peak_hour_cos": "Peak hour (cosine)", "log_interactions_per_week": "Interactions per week (log)",
}
_GROUPS = ([("Profile metadata", 12)] + [("Posting behaviour", 4)] + [("Temporal pattern", 6)] + [("Interaction frequency", 1)])
_ORIGIN = {"Profile metadata": "real rows (Instagram labelled set)", "Posting behaviour": "real rows (Twitter set; label carries almost no signal)",
           "Temporal pattern": "age from Twitter set, rest synthetic", "Interaction frequency": "synthetic"}


def _feature_rows():
    z = np.load(os.path.join(F.CODE, "data", "processed", "graph.npz"), allow_pickle=False)
    X, y, names = z["X"], z["y"], [str(n) for n in z["features"]]
    rows, k = [], 0
    for grp, cnt in _GROUPS:
        for _ in range(cnt):
            f = names[k]
            rows.append([grp, _LABELS[f], f"{X[y == 0, k].mean():.2f}", f"{X[y == 1, k].mean():.2f}"])
            k += 1
    return rows


def _ablation_text():
    ex = F.EXTRA
    if not ex or "ablation" not in ex:
        return None
    return ex["ablation"]


# ============================================================================ 6.1 - 6.8
def methodology_blocks():
    b = []
    base, sage = F.mean("baseline", "f1"), F.mean("sage", "f1")

    b += [H2("6.1 Overall methodology"),
          P("BotGraph treats fake-account detection as semi-supervised-style node classification on a social graph and botnet discovery as community detection on what the classifier has learned. "
            f"The work follows seven steps, run in order by the `ml` package and then served by the API: (1) assemble one graph of {F.NODES:,} accounts and {F.EDGES:,} ties from public data and a seeded generator; "
            f"(2) build {F.N_FEATURES} numeric features per account; (3) split the accounts once, stratified by label, into 60 % training, 20 % validation and 20 % test; "
            "(4) train a feature-only baseline and three message-passing networks (GCN, GAT, GraphSAGE) on that split with three seeds each; "
            "(5) tune the decision threshold on the validation set and report every metric on the untouched test set; (6) keep the architecture with the best validation F1 as the served model, "
            "write its fake-probabilities and 64-dimensional embeddings to disk; (7) cluster the suspicious accounts in embedding space with Louvain community detection and describe every cluster."),
          P("Two further stages sit outside the offline pipeline. The backend loads the stored scores once, answers every request from memory, and keeps moderator decisions in SQLite. "
            "When a moderator asks for it, the pipeline is run again with the logged decisions as extra training labels, and the F1 before and after is recorded."),
          N("**Build the graph** (`ml/data.py`): real topology plus labelled profile rows, posting rows and injected botnets.",
            "**Engineer features** (`ml/data.py`): profile metadata, posting behaviour, temporal pattern and interaction frequency.",
            "**Split once** (`ml/data.py`): stratified 60/20/20, identical for every model.",
            "**Train and compare** (`ml/gnn.py`, `ml/train.py`): four models, three seeds, class-weighted loss, early stopping on validation F1.",
            "**Evaluate** (`ml/train.py`, `ml/eval.py`): accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, and a scalability sweep.",
            "**Cluster** (`ml/clustering.py`): Louvain over the embeddings of suspicious accounts, scored against the injected botnets.",
            "**Serve and learn** (`backend/app`): scores, explanations and clusters through the API; moderator decisions feed the next training run."),
          ]
    b += _fig("10_flowchart_pipeline.png", "Flow of the offline pipeline from raw data to served artefacts.", 5.4, "diag")

    # ----------------------------------------------------------------- dataset
    b += [H2("6.2 Dataset"),
          P("No platform data can be scraped or shared, so the graph is assembled from three public datasets and a documented generator. The split between real and synthetic parts is kept visible in the app, in the schema and in every table below."),
          TAB("Data sources and what each contributes", ["Source", "Licence", "Size used", "Used for"],
              [["SNAP Facebook social circles" + c("snap") + " (ten ego networks, Kaggle mirror)", "Public research data", f"{F.REAL_NODES:,} accounts, {F.REAL_EDGES:,} ties", "All real nodes and ties"],
               ["Instagram fake, spammer and genuine accounts", "CC BY 3.0", "696 labelled rows", "Profile attributes (resampled and jittered)"],
               ["Twitter Bot Detection Dataset", "CC0", "50,000 rows", "Retweets, mentions, post length, hashtags, account age"],
               ["Injected botnets (`ml/data.py`, seed 7)", "Generated", f"{F.INJ_NODES} accounts, {F.INJ_EDGES:,} ties", "Known-answer clusters, timing and interaction features, handles"]],
              widths=[2.3, 1.1, 1.4, 1.9], align=["l", "l", "l", "l"], size=9.5),
          H3("6.2.1 How the graph is assembled"),
          P(f"The ten Facebook ego networks are merged into one undirected graph of {F.REAL_NODES:,} accounts and {F.REAL_EDGES:,} ties. Every real account receives a profile row and a posting row by resampling the labelled datasets. "
            "Accounts that will stay genuine draw a genuine profile; accounts that are bots draw a fake profile, except for the camouflaged ones described below."),
          P(f"Eight botnets of {min(F.BOTNET_SIZES)} to {max(F.BOTNET_SIZES)} accounts ({sum(F.BOTNET_SIZES)} accounts in all; sizes {', '.join(str(s) for s in F.BOTNET_SIZES)}) and {F.LONE_SPAMMERS} lone spammers are added. The botnet recipe is:"),
          B("every pair of accounts inside a botnet is tied with probability 0.28, plus a ring through all members so the botnet is connected (coordinated mutual follows and likes);",
            "every bot also follows 2 to 7 real accounts, chosen in proportion to the square root of their degree (follow-spam);",
            "each pair of botnets has a 0.35 chance of one tie between them;",
            "each lone spammer follows 3 to 10 real accounts and no other bot;",
            "members of one botnet share a creation window (about 6 days of spread) and a peak posting hour (within one hour of the botnet's hour)."),
          P(f"This adds {F.INJ_EDGES:,} injected ties to the {F.REAL_EDGES:,} real ones, giving {F.EDGES:,} in total. Fake accounts number {F.FAKE} ({F.pct(F.FAKE_SHARE)} of {F.NODES:,}); genuine accounts are the other {F.NODES - F.FAKE:,}."),
          H3("6.2.2 Camouflage"),
          P(f"If every bot carried an obviously fake profile, the profile alone would solve the task and the graph would add nothing. Two rules prevent that. {F.CAMO_BOTS} bots (40 % of botnet members and 25 % of lone spammers) are given a genuine-looking profile, "
            f"and {F.SUSPICIOUS_GENUINE} genuine accounts (6 % of real accounts) are given a fake-looking one. A model that reads only the profile therefore cannot be perfect; the neighbourhood has to help. "
            "This design choice is deliberate and is also a limitation: the difficulty of the benchmark was set by the authors, not observed on a platform."),
          H3("6.2.3 Split"),
          P(f"Accounts are split once, stratified by label, with a fixed seed: {F.SPLITS['train']:,} for training, {F.SPLITS['val']} for validation and {F.SPLITS['test']} for testing ({F.TEST_FAKE} fake accounts in the test split). "
            "Because message passing needs the whole graph, all four models see every account's features and ties at training time (transductive setting); only the labels of the training accounts enter the loss. "
            "Validation labels select the threshold and the early-stopping epoch; test labels are used for reporting only."),
          ]
    b += _fig("f14_degree_distribution.png", "Degree distribution of genuine and fake accounts in the assembled graph.", 5.2)

    # ----------------------------------------------------------------- features
    b += [H2("6.3 Data preparation and node features"),
          P(f"Each account is described by {F.N_FEATURES} numeric features in four groups. Heavy-tailed counts (posts, followers, following, retweets, account age, posting rate, interactions) are log-transformed, the peak posting hour is encoded as a sine and a cosine so that 23:00 and 01:00 are close, "
            "and every column is standardised to zero mean and unit variance with the training mean and standard deviation before it reaches a model (the same statistics are stored in `scores.npz` so the explanation code can reverse them)."),
          TAB("The 23 node features with the mean value for genuine and fake accounts (stored scale, before standardisation)", ["Group", "Feature", "Genuine mean", "Fake mean"],
              _feature_rows(), widths=[1.5, 2.4, 1.0, 1.0], align=["l", "l", "r", "r"], size=9),
          P("Two things stand out in the table. The profile features separate the classes well on average (profile pictures 0.94 against 0.62, bio length 40 against 21 characters, posts and followers lower for fake accounts), "
            "and the timing features separate them even more (burstiness 0.28 against 0.46, share of activity in the peak hour 0.13 against 0.26). "
            "The four posting-behaviour features, in contrast, are practically identical for the two classes: the Twitter dataset's bot label carries almost no signal, so these columns behave as realistic noise and are not evidence. "
            "The temporal and interaction features are generated by the seeded script, with a bot-leaning and a human-leaning distribution; this matters for how the results are read (Section 6.4 and Chapter 8)."),
          ]
    b += _fig("f13_feature_means.png", "Standardised difference between fake and genuine accounts for each feature group.", 5.4)

    # ----------------------------------------------------------------- algorithm choice
    b += [H2("6.4 Algorithm choice and justification"),
          H3("6.4.1 Why a graph neural network"),
          P("A per-account classifier sees only the account's own columns. A bot that copies a genuine profile and posts at human-like rates gives such a classifier nothing to work with, yet its ties are unusual: "
            "it follows and is followed by other accounts of the same operation. A graph neural network lets each account's representation depend on its neighbours' features, "
            "so the evidence from a camouflaged account's neighbourhood reaches the account itself. The base paper uses the same idea for a different goal, classifying nodes of the Facebook graph by structural role with GraphSAGE" + c("base", "sage") + ", "
            "and the project brief asks for the three standard architectures to be compared."),
          H3("6.4.2 Why these three architectures"),
          TAB("The three message-passing layers compared", ["Model", "How a node combines its neighbourhood", "Why it is in the study"],
              [["GCN" + c("gcn"), "Symmetrically normalised sum over neighbours and self; one weight matrix for both", "The standard baseline for graph learning; smoothing is strong, so it tests whether plain smoothing helps"],
               ["GAT" + c("gat"), "Attention-weighted sum over neighbours; four heads in the first layer", "Lets the model weigh suspicious neighbours more than ordinary ones"],
               ["GraphSAGE" + c("sage"), "Separate weights for the node itself and the mean of its neighbours", "Keeps the account's own evidence apart from the neighbourhood; the base paper's backbone"]],
              widths=[1.0, 2.6, 3.1], align=["l", "l", "l"], size=9.5),
          H3("6.4.3 Why a feature-only baseline"),
          P(f"A graph model that beats nothing proves nothing. The baseline is a two-layer dense network with the same width, dropout, optimiser, loss, split, seeds and early stopping as the graph models, fed the same 23 features, with the graph removed. "
            f"Its F1 of {F.f3(base)} is the number every graph model has to beat. The difference between a graph model and the baseline is the measured contribution of the ties."),
          H3("6.4.4 Why class weights and a tuned threshold"),
          P(f"Only {F.pct(F.FAKE_SHARE)} of accounts are fake, so plain cross-entropy would reward saying 'genuine' for everything (a classifier that does so scores {F.pct(1 - F.TEST_FAKE / F.TEST_N)} accuracy on the test split). "
            "The loss therefore weights the fake class by the square root of the class ratio, which is a milder correction than full inverse-frequency weighting and avoids flooding the queue with false alarms. "
            "The decision threshold is then chosen on the validation set from a grid of 33 values between 0.1 and 0.9 to maximise F1, instead of being fixed at 0.5. The headline metric is F1 with precision and recall alongside; accuracy is reported but not used to rank models."),
          H3("6.4.5 Why Louvain over the embeddings"),
          P("A botnet is a group of accounts that look alike to the model and are tied to each other. The second hidden layer of the served network gives each account a 64-dimensional embedding in which such accounts are close. "
            "Louvain" + c("louvain") + " finds densely connected groups by maximising modularity, needs no preset number of clusters and runs in seconds on a few hundred nodes. "
            "Combining embedding similarity with real ties lets a group form either because its members behave alike or because they follow each other, and rejects accounts that only happen to share one of the two."),
          ]

    # ----------------------------------------------------------------- maths
    b += [H2("6.5 Mathematical formulation"),
          P("Let the graph have n accounts, adjacency matrix A (symmetric, no self-loops), feature matrix X ∈ R^(n×23) after standardisation, and labels y_i ∈ {0, 1} (1 = fake). "
            "Every model has two hidden layers of width 64, an ELU activation and a linear head with two outputs. H⁽⁰⁾ = X, and for layer l = 1, 2:"),
          H3("6.5.1 Message-passing layers"),
          P("**GCN.** With self-loops added, Ã = A + I and D̃ the diagonal degree matrix of Ã:"),
          EQ("H⁽ˡ⁾ = ELU( D̃^(-1/2) Ã D̃^(-1/2) H⁽ˡ⁻¹⁾ W⁽ˡ⁾ + b⁽ˡ⁾ )"),
          P("In `ml/gnn.py` the normalised matrix is built once as a sparse tensor and applied with a sparse matrix product."),
          P("**GraphSAGE (mean aggregator).** With N(i) the neighbours of account i:"),
          EQ("h_i⁽ˡ⁾ = ELU( W_self⁽ˡ⁾ h_i⁽ˡ⁻¹⁾ + b⁽ˡ⁾ + W_neigh⁽ˡ⁾ · mean_{j ∈ N(i)} h_j⁽ˡ⁻¹⁾ )"),
          P("The self term and the neighbour term have separate weight matrices; this is the only one of the three layers that treats 'me' and 'my neighbours' differently."),
          P("**GAT.** Attention coefficients are computed per head k over the neighbours of i and over i itself:"),
          EQ("e_ij = LeakyReLU₀.₂( a_srcᵀ W h_j + a_dstᵀ W h_i ),   α_ij = exp(e_ij) / Σ_{m ∈ N(i) ∪ {i}} exp(e_im),   h_i' = ELU( ‖_k Σ_j α_ij^k W^k h_j )"),
          P("The first layer uses four heads of 16 units whose outputs are concatenated into 64 units; the second layer uses one head of 64 units. The softmax over each node's incoming edges is implemented with `scatter_reduce` (maximum) and `index_add_` (sum), which is why GAT results can move by about 0.01 F1 between runs: the summation order is not deterministic."),
          P("**Baseline.** The same two layers with the graph removed: H⁽ˡ⁾ = ELU( H⁽ˡ⁻¹⁾ W⁽ˡ⁾ + b⁽ˡ⁾ )."),
          H3("6.5.2 Classifier and loss"),
          P("The head maps the second embedding z_i = H⁽²⁾_i to two logits, and the fake-probability is the softmax of the second component:"),
          EQ("p_i = softmax( W_o z_i + b_o )₁"),
          P(f"Training minimises class-weighted cross-entropy over the training accounts T, with weight 1 on the genuine class and w₁ = √(n₀ / n₁) on the fake class, where n₀ and n₁ are the class counts in T:"),
          EQ("L = − Σ_{i ∈ T} w_{y_i} · log p(y_i | i)  /  Σ_{i ∈ T} w_{y_i}"),
          P("(PyTorch normalises the weighted sum by the sum of the weights.) The network is regularised with dropout" + c("dropout") + " 0.3 on the input, between layers and before the head, and L2 weight decay 5 × 10⁻⁴ in Adam" + c("adam") + "."),
          H3("6.5.3 Threshold and metrics"),
          EQ("τ* = argmax_{τ ∈ {0.10, 0.125, …, 0.90}}  F1( y_val , 1[p_val ≥ τ] )"),
          P("An account is flagged when p_i ≥ τ*. With TP, FP, FN, TN counted on the test split:"),
          EQ("Precision = TP / (TP + FP),   Recall = TP / (TP + FN),   F1 = 2 · Precision · Recall / (Precision + Recall)"),
          P("ROC-AUC is the probability that a randomly chosen fake account receives a higher p than a randomly chosen genuine one, and PR-AUC is the area under the precision-recall curve (computed as average precision). Because fake accounts are 12.6 % of the data, PR-AUC is the stricter of the two."),
          H3("6.5.4 Clustering"),
          P("Let S = {i : p_i ≥ 0.30} be the candidate accounts. Each candidate is linked to its K = 5 most similar candidates by cosine similarity of embeddings, with edge weight max(cos(z_i, z_j), 0), and every real tie between two candidates adds weight 1.0 to the pair. Louvain maximises the weighted modularity"),
          EQ("Q = 1/(2m) · Σ_{ij} [ w_ij − k_i k_j / (2m) ] · δ(c_i, c_j)"),
          P("where w_ij is the edge weight, k_i the weighted degree, m the total weight and c_i the community of node i. Communities with fewer than 5 accounts are dropped. For each cluster of size s with E internal real ties:"),
          EQ("density = E / ( s (s − 1) / 2 )"),
          P("A cluster is labelled *coordinated* when its density is at least 5 % and *diffuse* otherwise. Recovery of an injected botnet is measured with recall = |botnet ∩ cluster| / |botnet| and precision = |botnet ∩ cluster| / |cluster| for the best-overlapping cluster; a botnet counts as recovered when both are at least 0.8."),
          H3("6.5.5 Explanation of a score"),
          P("For an account i, the app reports gradient × input attribution" + c("gradxinput") + " of the fake-versus-genuine margin m_i = logit₁ − logit₀. Writing x for the standardised feature matrix:"),
          EQ("contribution(i, f) = x_if · ∂m_i / ∂x_if,   own total = Σ_f contribution(i, f),   network = Σ_{j ≠ i} Σ_f x_jf · ∂m_i / ∂x_jf"),
          P("The seven largest own contributions are shown as bars, and the network term reports how much the other accounts' features push the margin through message passing. This is a first-order approximation of feature importance, not a proof of cause, and the app says so on the screen."),
          ]

    # ----------------------------------------------------------------- model architecture and training
    b += [H2("6.6 Model architecture and training configuration")]
    b += _fig("12_model_architecture.png", "Two-layer message-passing network with a classifier head, and the three layer types that fill the layer slots.", 5.4, "diag")
    b += [P("All four models are written in plain PyTorch" + c("pytorch") + " on sparse tensors; `torch-geometric` is not used, because its Windows wheels are a frequent build failure and the three layers are short enough to write directly. The models are small enough to train on a laptop CPU in seconds to a minute."),
          TAB("Parameter counts and mean training time per model (3 seeds, CPU)", ["Model", "Trainable parameters", "Mean training time per run (s)", "Uses graph"],
              [["Feature-only baseline (MLP)", "5,826", f"{F.MODELS['baseline']['train_seconds']:.1f}", "No"],
               ["GCN", "5,826", f"{F.MODELS['gcn']['train_seconds']:.1f}", "Yes"],
               ["GAT", "6,082", f"{F.MODELS['gat']['train_seconds']:.1f}", "Yes"],
               ["GraphSAGE", "11,394", f"{F.MODELS['sage']['train_seconds']:.1f}", "Yes"]],
              widths=[2.3, 1.5, 1.8, 0.9], align=["l", "r", "r", "c"], size=10),
          P("GraphSAGE has about twice the parameters of the other models because each layer holds two weight matrices. The parameter counts were taken from the instantiated models on 23 input features."),
          TAB("Training configuration (identical for all models)", ["Setting", "Value"],
              [["Hidden width", "64"], ["Layers", "2 message-passing (or dense) layers + linear head"], ["Activation", "ELU"], ["Dropout", "0.3 (GAT attention dropout 0.2)"],
               ["Optimiser", "Adam, learning rate 0.01, weight decay 5 × 10⁻⁴"], ["Loss", "Cross-entropy, fake-class weight √(n_genuine / n_fake)"],
               ["Epochs", "up to 160, early stopping with patience 40 on validation F1 at threshold 0.5"], ["Model selection", "best-validation-F1 epoch restored"],
               ["Seeds", "0, 1, 2 (mean and standard deviation reported)"], ["Threshold", "tuned on validation, grid 0.10 to 0.90 in steps of 0.025"],
               ["Served model", "best validation F1 among GCN, GAT, GraphSAGE (GraphSAGE: 0.959)"]],
              widths=[1.6, 4.9], align=["l", "l"], size=10),
          P("Training is full-batch: every epoch runs one forward and backward pass over the whole graph. After each epoch the validation F1 is computed at 0.5 and the weights of the best epoch are kept. "
            "After training, the probabilities of seed 0 are stored as the served scores, and that run's threshold is the served threshold (0.5 for GraphSAGE)."),
          ]

    # ----------------------------------------------------------------- clustering
    b += [H2("6.7 Botnet cluster detection")]
    b += _fig("11_flowchart_clustering.png", "Steps of botnet cluster detection from model scores and embeddings.", 5.0, "diag")
    b += [P("Cluster detection runs on the served model's output. Candidates are accounts with p ≥ 0.30, a looser cut than the flagging threshold so that borderline members of a botnet can still be pulled in by their neighbours. "
            "Each cluster is described by its size, mean score, share flagged, internal ties and density, the busiest three-hour window and the share of members in it, the spread of creation dates (10th to 90th percentile of account age), "
            "and median posting rate, interactions, followers and follower ratio. These descriptions are what the moderator reads in the app before confirming or dismissing a whole cluster."),
          P(f"On the shipped model the procedure finds {REC_N()} groups: {F.REC['recovered']} of {F.REC['botnets']} injected botnets, each as a single community (mean recall {F.f3(F.REC['mean_recall'])}, mean precision {F.f3(F.REC['mean_precision'])}), "
            f"plus one loose group of 160 accounts (lone spammers and look-alikes) whose members have almost no ties between them, which the app labels *diffuse* because its density is 0.0014. Results are discussed in Chapter 8."),
          ]

    # ----------------------------------------------------------------- moderator feedback
    b += [H2("6.8 Moderator feedback and retraining"),
          P("A moderator confirms or dismisses a flagged account, or a whole cluster. Each decision is stored with the moderator, the note, the model's score at that moment and the list of affected accounts. "
            "A cluster decision applies to all of its members. When a moderator starts a retraining run, every logged decision becomes a training label (confirm → fake, dismiss → genuine); the latest decision on an account wins."),
          B("Reviewed accounts that lie in the training or validation split join the training set (and leave the validation set); accounts in the test split are never relabelled, so before and after are measured on the same test accounts.",
            "The run trains all four models with one seed, rewrites the served scores and clusters, and stores the F1 of each model before and after in `training_runs`.",
            "The decisions it used are marked with the run number and can no longer be undone.",
            "Decisions that cannot be used (test-split accounts) are still kept in the log."),
          P("The comparison before and after is a single-seed run against the three-seed mean, so small changes in F1 should not be over-read; the purpose of the loop is to show that moderator knowledge can enter the model, not to claim a measured gain from a few demo decisions."),
          ]
    return b


def REC_N():
    return F.REC["clusters_found"]


# ============================================================================ 6.9 - 6.12
def application_blocks():
    b = []
    b += [H2("6.9 Application architecture"),
          P("The application has three tiers. The **ML package** (`ml/`) is run from the command line and writes files: `data/processed/graph.npz` and `accounts.csv`, `models/*.pt`, `scores.npz`, `clusters.json`, `meta.json`, and `experiments/*.json`. "
            "The **API** (`backend/app/`) is a FastAPI application served by Uvicorn on port 8309. At start-up it creates the SQLite tables, seeds the two demo users and loads the graph, scores, embeddings and clusters into one in-memory `Store`. "
            "The **web app** (`frontend/`) is a React 18 single-page application built with Vite on port 5309 that proxies `/api` to the API."),
          TAB("Backend modules", ["Module", "Responsibility"],
              [["`main.py`", "Creates the app, lifespan hook (tables, demo users, store), CORS, registers five routers"],
               ["`settings.py`", "Reads `.env.example` then `.env`; ports, database URL, JWT secret and lifetime"],
               ["`db.py`", "SQLAlchemy 2 models `User`, `Review`, `TrainingRun`; SQLite with WAL journal and foreign keys on"],
               ["`auth.py`", "bcrypt password hashing, JWT creation and checking, `current_user` and `require_moderator` dependencies, demo users"],
               ["`services/store.py`", "In-memory view of artefacts: graph, scores, clusters, neighbour index, gradient × input explanation (cached)"],
               ["`routes/core.py`", "Health, login, current user, graph summary, overview"],
               ["`routes/accounts.py`", "Ranked account list with filters, account detail, neighbourhood graph"],
               ["`routes/clusters.py`", "Cluster list and cluster detail"],
               ["`routes/queue.py`", "Moderator queue, decisions, undo, decision log"],
               ["`routes/models.py`", "Model comparison, scalability, retraining job and its status"]],
              widths=[1.6, 5.0], align=["l", "l"], size=10),
          P("The web app has eleven pages: landing, sign-in, overview, graph and features, accounts, account detail, botnet clusters, cluster detail, moderator queue, models and scale, and a not-found page. "
            "Every data page shows a loading skeleton, an empty state with an action, an error state with a retry, and a toast after every action. The layout works at 360, 768 and 1440 px in light and dark themes."),
          ]

    b += [H2("6.10 API design"),
          P("All routes sit under `/api` and exchange JSON. Every route except `GET /api/health` and `POST /api/auth/login` needs an `Authorization: Bearer <token>` header. Routes that change data or start training additionally need the moderator role."),
          TAB("API endpoints", ["Method", "Path", "Role", "Purpose"],
              [["GET", "/api/health", "public", "Status, account and tie counts, served model, flagged count, botnet count, best and baseline F1"],
               ["POST", "/api/auth/login", "public", "Email and password in, token and user out"],
               ["GET", "/api/auth/me", "any", "The signed-in user"],
               ["GET", "/api/graph/summary", "any", "Node and tie counts (real and injected), class balance, split, feature summaries, degree histogram, dataset provenance"],
               ["GET", "/api/overview", "any", "KPIs, score histogram, model F1 list, top accounts, top clusters, recent decisions"],
               ["GET", "/api/accounts", "any", "Ranked accounts with search, status, cluster and flag filters, sorting and paging"],
               ["GET", "/api/accounts/{id}", "any", "Score, per-model scores, top contributing features, neighbourhood summary, profile, decision history"],
               ["GET", "/api/accounts/{id}/neighbourhood", "any", "Nodes and links of the account's neighbourhood for the graph view"],
               ["GET", "/api/clusters", "any", "Detected clusters with size, density, shared hour and status"],
               ["GET", "/api/clusters/{id}", "any", "Members, shared behaviour, reach, graph and headline of one cluster"],
               ["GET", "/api/queue", "any", "Pending or decided accounts and clusters, with summary counts"],
               ["POST", "/api/queue/decisions", "moderator", "Confirm or dismiss an account or cluster (201)"],
               ["DELETE", "/api/queue/decisions/{id}", "moderator", "Undo a decision not yet used in training"],
               ["GET", "/api/decisions", "any", "The decision log"],
               ["GET", "/api/models", "any", "Per-architecture metrics, ROC points, confusion matrices, cluster recovery, retraining runs"],
               ["GET", "/api/models/scalability", "any", "Training and inference time as the graph grows"],
               ["POST", "/api/models/retrain", "moderator", "Start a retraining run on the logged decisions (202)"],
               ["GET", "/api/models/retrain/status", "any", "State, progress and message of the running job"]],
              widths=[0.6, 2.1, 0.8, 3.1], align=["c", "l", "c", "l"], size=9),
          P("Request bodies are validated with Pydantic models: a decision must name a `target_type` (account or cluster), a `target_id`, a `decision` (confirm or dismiss) and a note of at most 500 characters; list endpoints bound `page` (at least 1) and `page_size` (at most 100). "
            "FastAPI also serves interactive documentation of every route at `/docs`."),
          P(f"Measured on 127.0.0.1 with a warm server, the read endpoints answered in a median of {min(v[0] for v in F.LATENCY.values()):.1f} to {max(v[0] for v in F.LATENCY.values()):.1f} ms (95th percentile at most {max(v[1] for v in F.LATENCY.values()):.1f} ms); "
            f"sign-in took a median of {F.LOGIN_MS} ms because bcrypt is deliberately slow, and the API needed {F.STARTUP_S} s from launch to its first healthy answer. These figures come from one shared laptop-class machine and are upper bounds (Chapter 7)."),
          ]

    b += [H2("6.11 Security and error handling"),
          B("**Authentication.** Passwords are hashed with bcrypt (the password is cut at bcrypt's 72-byte limit before hashing). A successful login returns an HS256 JSON Web Token that carries the user id, the role and an expiry 12 hours ahead.",
            "**Authorisation.** `current_user` rejects a missing header, a malformed or expired token and a token for a user that no longer exists with 401 and a plain-language message. `require_moderator` returns 403 for analysts on decision, undo and retrain routes. The smoke test checks that an anonymous request gets 401 and that an analyst cannot record a decision.",
            "**Wrong credentials.** An unknown email or a wrong password gives the same 401 message, so the response does not reveal which accounts exist.",
            "**Input validation.** Unknown account ids give 404, non-numeric account ids give 422, unknown cluster ids give 404 with a hint that clusters change after retraining, paging bounds are enforced by the framework, and notes longer than 500 characters are refused.",
            "**State conflicts.** Undoing a decision already used in training gives 409; starting a second retraining run while one is running gives 409; retraining with no decisions gives 409 with an instruction.",
            "**Retraining failures.** The job runs in a background thread; an exception is stored on the `training_runs` row with status `error` and shown in the app, and the served model is left unchanged.",
            "**Cross-origin requests.** CORS allows only the web app's own origins (`localhost` and `127.0.0.1` on port 5309).",
            "**Secrets.** The JWT secret comes from `.env`; if it is missing or still the placeholder, a fixed development secret is used, which is acceptable for a local demo only. `.env` is excluded from version control and nothing is sent to any outside service."),
          P("These measures suit a local demonstration. They do not amount to a production security design: there are two seeded accounts with a shared demo password, no password reset, no multi-factor sign-in, no rate limiting, no token revocation and no audit trail beyond the decision log, and TLS is not configured (Chapter 10)."),
          ]

    b += [H2("6.12 Installation and execution"),
          P("BotGraph runs on one Windows computer with Python 3.11 or newer and Node.js (LTS). About 3 GB of disk space is needed, mostly for PyTorch, and an internet connection for the first setup."),
          N("Open the `8.ProjectCode` folder and double-click `run.bat`. On the first run it calls `setup.bat`, which creates `.venv`, installs the Python packages from `backend/requirements.txt` and the web packages with `npm install`, and copies `.env.example` to `.env`.",
            "`run.bat` starts the API (`uvicorn backend.app.main:app` on 127.0.0.1:8309) and the web app (`npm run dev` on 5309) in two minimised windows, waits up to about 90 seconds for `/api/health` to answer, and opens http://localhost:5309.",
            "Sign in with `moderator@botgraph.app` (can decide and retrain) or `analyst@botgraph.app` (read-only); the password is `Demo@1234` and the sign-in page fills it with one click.",
            "Close the two windows to stop the application."),
          P("The trained models, scores and clusters are included, so nothing needs training before the first start. The pipeline can be re-run with `python -m ml.data` (rebuild the graph), `python -m ml.train` (train all models, a few minutes on CPU) and `python -m ml.eval` (scalability sweep), "
            "and `python scripts/smoke_test.py` runs the end-to-end test on a scratch database. Appendix B gives the full guide and troubleshooting."),
          ]
    return b


_REPORT_DROP_P = ("Two further stages sit outside", "In `ml/gnn.py` the normalised matrix", "The self term and the neighbour term",
                  "GraphSAGE has about twice the parameters", "The comparison before and after is a single-seed", "The web app has eleven pages",
                  "Training is full-batch", "ROC-AUC is the probability")


def _report_trim(bl):
    """Report mode only: drop passages that repeat a figure, a table or another chapter (documents 9 and 12 keep the full text)."""
    out = []
    for b in bl:
        if b[0] == "p" and b[1].startswith(_REPORT_DROP_P):
            continue
        if b[0] == "n" and b[1][0].startswith("**Build the graph**"):
            continue
        out.append(b)
    return out


def blocks():
    bl = [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
    return _report_trim(bl) if F.REPORT else bl
