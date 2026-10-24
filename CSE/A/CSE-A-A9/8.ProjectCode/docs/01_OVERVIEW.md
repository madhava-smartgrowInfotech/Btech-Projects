# BotGraph - overview

BotGraph finds fake accounts and coordinated botnets from the **shape of the social graph**, not just from single profiles.

## The problem

- Fake profiles are created faster than manual moderation can remove them.
- Per-account classifiers miss coordinated networks whose individual profiles look legitimate.
- Bot behaviour changes quickly, so fixed rules and signatures go stale.
- Labelled data is heavily imbalanced (here about 1 in 8 accounts is fake) and noisy.

BotGraph classifies every account from its relational context (who it follows, likes and moves with) and exposes the
coordinated clusters that single-account models cannot see. It is aimed at large, regional platforms such as ShareChat and Moj.

## Who uses it

| Role | What they do in the app |
| --- | --- |
| Platform trust and safety team | Watch the overview, review the botnet clusters, read model results |
| Moderator | Work the queue: confirm or dismiss flagged accounts and whole clusters |
| Researcher | Compare GCN, GAT and GraphSAGE against a no-graph baseline, inspect scalability |

## What it does

| ID | Feature | Where to see it |
| --- | --- | --- |
| F1 | **Graph builder** - accounts become nodes, interactions become edges, assembled from the committed datasets into one graph with a documented schema | *Graph & features* |
| F2 | **Node features** - profile metadata, posting behaviour, timing and interaction frequency (23 features in four groups) | *Graph & features* |
| F3 | **Three architectures compared** - GCN, GAT and GraphSAGE on one split, with a feature-only baseline that proves the graph earns its place | *Models & scale* |
| F4 | **Account scoring** - a fake-probability for every account, the traits that drove it, and a map of its neighbourhood | *Accounts* |
| F5 | **Botnet clusters** - community detection over the learned embeddings; each cluster shows size, shared behaviour and an interactive graph | *Botnet clusters* |
| F6 | **Moderator queue** - confirm or dismiss an account or cluster; decisions are logged and feed the next training run | *Moderator queue* |
| F7 | **Evaluation** - accuracy, precision, recall and F1 per architecture, plus training and inference time as the graph grows | *Models & scale* |

## How it meets the six objectives

1. **Graph representation** - nodes are accounts, edges are interactions; schema in `02_HOW_IT_WORKS.md`.
2. **Node features** - profile metadata (age, follower / following ratio, bio and picture), posting behaviour and interaction frequency.
3. **Compare GCN, GAT and GraphSAGE** - same split, same features, same training budget, three seeds each.
4. **Detect coordinated botnet clusters** - Louvain communities over the learned embeddings.
5. **Evaluate against labelled data** - accuracy, precision, recall, F1, ROC-AUC and PR-AUC on a held-out test split.
6. **Assess scalability** - training and inference time as the graph grows from about 4.5 thousand to 36 thousand accounts.

## What is real and what is synthetic

| Part | Status |
| --- | --- |
| Social topology (about 3,960 accounts, 88 thousand ties) | **Real** - public Facebook ego networks |
| Profile attributes of every account | **Real rows** from a labelled Instagram fake-account dataset, resampled and jittered |
| Posting behaviour (retweets, mentions, post length, hashtags, account age) | **Real rows** from a labelled Twitter bot dataset |
| Eight botnets and 150 lone spammers added to the topology | **Synthetic**, seeded, so cluster detection can be scored against a known answer |
| Posting rate, burstiness, peak hour, interactions per week, handles and display names | **Synthetic**, seeded |

Nothing is scraped from a live platform. The synthetic parts are labelled wherever they are shown.

## Honest limits

- The botnets are injected, so cluster recovery measures how well the method finds *this kind* of coordination, not real-world botnets.
- Some injected bots are given genuine-looking profiles and some genuine accounts look suspicious on purpose; without that the profile alone would solve the task and the graph would add nothing.
- The two labelled sources are not about the same accounts. Profile rows and posting rows are combined per account by resampling, which keeps realistic value ranges but not real correlations between them.
- The Twitter dataset's bot label carries almost no signal by itself (its means are identical for both classes), so the posting-behaviour columns act as realistic noise rather than as evidence.
- Models are small and trained on CPU in minutes. Transformer-based text features, TwiBot-22-scale graphs and live platform ingestion are out of scope.
