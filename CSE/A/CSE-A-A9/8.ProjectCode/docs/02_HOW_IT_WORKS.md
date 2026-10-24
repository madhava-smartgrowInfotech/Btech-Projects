# How BotGraph works

## 1. Architecture

```
data/raw  --ml.data-->  data/processed (graph.npz, accounts.csv)
                              |
                         ml.train  --> models/*.pt, scores.npz, clusters.json, meta.json
                              |        experiments/metrics.json
                         ml.eval   --> experiments/scalability.json, experiments/eval/metrics.json
                              |
backend/app (FastAPI + SQLite) -- loads the artifacts once, serves /api, stores users, decisions, retraining runs
                              |
frontend (React + Vite, kit V4) -- proxies /api to the backend
```

- **ml/** - graph builder (`data.py`), the three message-passing layers (`gnn.py`), training (`train.py`),
  clustering (`clustering.py`), evaluation and scalability (`eval.py`).
- **backend/app/** - `main.py`, `db.py`, `auth.py`, `routes/` (core, accounts, clusters, queue, models), `services/store.py`.
- **frontend/src/** - `pages/`, `components/` (the V4 kit under `ui`, `motion`, `charts`, plus `app` and `graph`), `lib/`.

## 2. Data

| Source | Licence | What is committed | Used for |
| --- | --- | --- | --- |
| Social circles: Facebook (SNAP mirror on Kaggle, `dhruvb2028/social-circles-facebook`) | public research data | the ten `.edges` files, 0.9 MB, in `data/raw/facebook/` | real topology: 3,963 accounts, 88,156 ties |
| Instagram fake, spammer and genuine accounts (`free4ever1/instagram-fake-spammer-genuine-accounts`) | CC BY 3.0 | `instagram_train.csv`, `instagram_test.csv` (696 labelled rows) | profile attributes |
| Twitter Bot Detection Dataset (`goyaladi/twitter-bot-detection-dataset`) | CC0 | `twitter_bot_detection.csv`, 7.4 MB (50,000 rows) | posting-behaviour rows |
| Injected botnets - `ml/data.py`, seed 7 | generated | `data/processed/` | known-answer clusters, timing features |

All sources are small enough to commit in full. `scripts/download_data.py` re-downloads them.

### Which edges are real and which are injected

- **Real:** the 88,156 ties of the Facebook ego networks (`edge_kind = 0`).
- **Injected (`edge_kind = 1`), 6,300 ties:**
  - inside each botnet, every pair is tied with probability 0.28, plus a ring so each botnet is connected (coordinated mutual follows and likes);
  - every bot also follows 2-7 real accounts (follow-spam), chosen in proportion to the square root of their degree;
  - some ties between botnets (probability 0.35 per pair);
  - 150 lone spammers, each tied to 3-10 real accounts and to no other bot.

### The graph schema

| Element | Fields |
| --- | --- |
| Node | `id`, 23 numeric features, `label` (1 fake, 0 genuine), `botnet_truth` (-1 for none), `origin` (real topology or injected), `split` |
| Edge | undirected pair `(i, j)` with `i < j`, `edge_kind` (0 real, 1 injected) |
| Size | 4,533 nodes (3,963 real + 570 injected), 94,456 ties, 570 fake accounts (12.6 %) |
| Split | stratified 60 / 20 / 20 by label: 2,719 train, 906 validation, 908 test, identical for every model |

To keep the task honest, 40 % of botnet accounts and 25 % of lone spammers get a **genuine-looking profile**
(camouflage), and 6 % of genuine accounts get a **fake-looking** one. A model that reads only the profile therefore
cannot reach perfect scores; the neighbourhood has to help.

## 3. Node features (F2)

| Group | Features |
| --- | --- |
| Profile metadata (12) | has profile picture, digits in username, words in display name, digits in display name, name equals username, bio length, has external link, private account, posts (log), followers (log), following (log), follower / following ratio |
| Posting behaviour (4) | average retweets (log), average mentions, average post length, hashtags per post |
| Temporal pattern (6) | account age (log days), posts per day (log), posting burstiness, share of activity in the peak hour, peak hour as sine and cosine |
| Interaction frequency (1) | interactions per week (log) |

Botnet members share a creation window and a peak posting hour, so those two traits are common to a cluster
without making any single member stand out. Features are standardised before training.

## 4. Models (F3)

Written directly against sparse tensors in PyTorch (no torch-geometric, whose Windows wheels are a frequent build failure).

| Model | Layer |
| --- | --- |
| Feature-only baseline | two dense layers on the account's own features (no graph) |
| GCN | `A_hat X W` with symmetric normalisation and self-loops |
| GraphSAGE | `W_self x + W_neigh mean(neighbours)` |
| GAT | 4 attention heads (edge softmax computed with `scatter_reduce` and `index_add`) then a single-head layer |

Common settings: two layers, 64 hidden units, dropout 0.3, Adam (lr 0.01, weight decay 5e-4), class-weighted
cross-entropy (positive class weighted by the square root of the imbalance), up to 160 epochs with early stopping
on validation F1. The decision threshold is tuned on the validation set. Every model is trained with three seeds
and the table reports mean ± standard deviation on the held-out test split.

## 5. Results (F7)

Test split, 908 accounts (114 fake). Mean over three seeds.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Feature-only baseline (MLP) | 0.959 | 0.868 | 0.789 | 0.827 ± 0.010 | 0.967 | 0.907 |
| GCN | 0.964 | 0.958 | 0.743 | 0.837 ± 0.009 | 0.988 | 0.939 |
| GAT | 0.977 | 0.963 | 0.845 | 0.900 ± 0.018 | 0.978 | 0.946 |
| **GraphSAGE** | **0.985** | **0.975** | **0.906** | **0.939 ± 0.006** | **0.990** | **0.974** |

All three graph models beat the baseline on F1. GCN's gain is small (+1.0 points F1) and comes from precision; its
recall is lower than the baseline's. GraphSAGE gains 11.2 points. The best architecture is chosen on validation F1 and is
the one the app serves. Numbers are in `experiments/metrics.json` and `experiments/eval/metrics.json`.
GAT's exact figures can move by a few thousandths between runs because its edge softmax sums in a non-deterministic order.

### Botnet recovery (F5)

Louvain over the embeddings of every account scored at 30 % or more finds 9 groups: **all 8 injected botnets are
recovered as single communities** (mean recall 100 %, mean precision 98.8 %), plus one loose group of 160 suspicious accounts
(lone spammers and look-alikes) with almost no ties between its members. The app labels a group *coordinated* when its
tie density is at least 5 % and *loose group* otherwise.

### Scalability

The account graph is copied 1, 2, 4 and 8 times as disjoint components. Training time is per epoch, inference is one forward
pass, both on CPU.

| Accounts | Ties | GCN train / infer | GAT train / infer | GraphSAGE train / infer |
| --- | --- | --- | --- | --- |
| 4,533 | 94,456 | 0.14 s / 0.04 s | 0.26 s / 0.05 s | 0.06 s / 0.03 s |
| 9,066 | 188,912 | 0.15 s / 0.07 s | 0.60 s / 0.13 s | 0.12 s / 0.05 s |
| 18,132 | 377,824 | 0.31 s / 0.14 s | 1.10 s / 0.26 s | 0.20 s / 0.10 s |
| 36,264 | 755,648 | 0.58 s / 0.24 s | 2.02 s / 0.58 s | 0.39 s / 0.19 s |

Cost grows roughly in proportion to the number of ties. GAT is the most expensive; GraphSAGE is the cheapest and the most accurate here.

## 6. Account scoring and explanations (F4)

Every account gets a fake-probability from the best architecture, plus the probability from every other model for comparison.
The **reasons** are a gradient x input attribution of the model's fake-versus-genuine margin: for each of the account's own
features, how far it pushes the margin (rose bar) or pulls it back (mint bar). A single extra number reports how much the *other*
accounts' features contribute through message passing. This is a first-order approximation, so the app says so. The
neighbourhood view draws the account and its highest-scoring neighbours with the ties between them.

## 7. Botnet clusters (F5)

1. Candidates: accounts with probability >= 0.30.
2. Link each candidate to its 5 most cosine-similar candidates in embedding space (weight = similarity), and add weight 1.0 for every real tie between two candidates.
3. Louvain community detection (`networkx`, seed 0); drop groups under 5 accounts.
4. Describe each group: size, tie density, busiest 3-hour window and the share of members in it, spread of creation dates, median posting rate, interactions and followers.

## 8. Moderator queue and feedback (F6)

- The queue lists flagged accounts (probability >= the tuned threshold) and clusters that nobody has decided yet, highest score first.
- A decision on a **cluster** applies to all its members. Decisions are stored in SQLite (`reviews`) with the moderator, the note and the model score at the time.
- **Retraining** (`POST /api/models/retrain`, moderators only): every logged decision becomes a training label (confirm -> fake, dismiss -> genuine).
  Reviewed accounts move into the training set; accounts in the **test split are never touched**, so before and after are measured on the same test accounts.
  The run trains all four models with one seed, rewrites the served scores and clusters, records F1 before and after in `training_runs`, and marks the decisions as used.
- A decision can be undone until a training run has used it.

## 9. API and storage

Endpoints are listed in `docs/FRONTEND_PLAN.md`; interactive docs are at `http://127.0.0.1:8309/docs`.
SQLite tables: `users` (bcrypt password hashes, role analyst or moderator), `reviews`, `training_runs`.
Login returns a signed JWT (12 hours). Moderator-only routes return 403 for analysts. CORS allows only the web app's origin.
The trained artifacts (`models/`, `experiments/`) can be redirected with `BOTGRAPH_MODELS_DIR` and `BOTGRAPH_EXPERIMENTS_DIR`,
which the smoke test uses to leave the real files untouched.
