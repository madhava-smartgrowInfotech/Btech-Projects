"""Second half of the BotGraph diagrams: ER, pipeline flowchart, clustering flowchart, model architecture."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"


def er_diagram():
    fig, ax = canvas(10, 8.8, 100, 88)
    ax.text(50, 86, "SQLite tables (top) and the file-based graph artefacts treated as logical entities (bottom)", ha="center", fontsize=8.2, color=NAVY, fontweight="bold")
    uml_class(ax, 2, 82, 29, "reviews", ["id  PK", "target_type  account | cluster", "target_id", "decision  confirm | dismiss", "note, score, members (JSON)", "user_id  FK -> users.id", "created_at", "used_in_run  (run id or null)"], [], hdr=NAVY, stereotype="table", fs=6.6)
    uml_class(ax, 36, 82, 29, "users", ["id  PK", "email  unique", "name", "role  analyst | moderator", "password_hash  (bcrypt)"], [], hdr=NAVY, stereotype="table", fs=6.6)
    uml_class(ax, 70, 82, 29, "training_runs", ["id  PK", "started_at, finished_at", "status  running|done|error", "feedback_labels, best", "f1_before, f1_after (JSON)", "message", "user_id  FK -> users.id"], [], hdr=NAVY, stereotype="table", fs=6.6)
    uml_class(ax, 2, 44, 29, "TIE  (edge_index)", ["i < j  (undirected pair)", "edge_kind  0 real | 1 injected", "(94,456 ties)"], [], hdr=ORANGE, stereotype="file entity", fs=6.6)
    uml_class(ax, 36, 44, 29, "ACCOUNT  (graph.npz, accounts.csv)", ["id, handle, display_name", "23 features (X row)", "label  1 fake | 0 genuine", "botnet_truth  (-1 none)", "origin, split  train|val|test"], [], hdr=ORANGE, stereotype="file entity", fs=6.3)
    uml_class(ax, 70, 44, 29, "CLUSTER  (clusters.json)", ["id  BN-xxxxx", "kind  coordinated | diffuse", "size, density, mean_score", "peak_hour, created_span_days", "members: list of account ids"], [], hdr=ORANGE, stereotype="file entity", fs=6.4)
    uml_class(ax, 36, 19, 29, "SCORE  (scores.npz)", ["p_baseline, p_gcn, p_gat, p_sage", "emb  (64-d, served model)", "mu, sd  (standardisation)"], [], hdr=PURPLE, stereotype="file entity", fs=6.6)

    def line(p1, p2, c=NAVY, ls="-"):
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=c, lw=1.6, zorder=4, ls=ls)
    line((31, 74), (36, 74)); ax.text(33.5, 75.6, "decides", fontsize=6.6, ha="center", color=GREY)
    ax.text(31.4, 71.9, "n", fontsize=7); ax.text(34.4, 71.9, "1", fontsize=7)
    line((65, 74), (70, 74)); ax.text(67.5, 75.6, "starts", fontsize=6.6, ha="center", color=GREY)
    ax.text(65.4, 71.9, "1", fontsize=7); ax.text(68.6, 71.9, "n", fontsize=7)
    # logical (no foreign key) links from reviews
    line((16, 56.4), (16, 52.5), c=GREY, ls="--"); line((16, 52.5), (84.5, 52.5), c=GREY, ls="--"); line((84.5, 52.5), (84.5, 58.55), c=GREY, ls="--")
    ax.text(50, 53.6, "reviews.used_in_run -> training run id (logical, no foreign key)", fontsize=6.5, ha="center", color=GREY)
    line((8, 56.4), (8, 44.2), c=GREY, ls="--")
    ax.text(9.2, 48.2, "members and target_id ->\naccount ids (logical)", fontsize=6.4, color=GREY)
    line((31, 36), (36, 36)); ax.text(33.5, 37.6, "joins", fontsize=6.6, ha="center", color=GREY)
    ax.text(31.4, 33.9, "n", fontsize=7); ax.text(34.4, 33.9, "2", fontsize=7)
    line((65, 36), (70, 36)); ax.text(67.5, 37.6, "in", fontsize=6.6, ha="center", color=GREY)
    ax.text(65.4, 33.9, "n", fontsize=7); ax.text(68.6, 33.9, "0..1", fontsize=7)
    line((50, 24.85), (50, 19)); ax.text(51.5, 22, "one score row per model", fontsize=6.4, color=GREY)
    ax.text(68, 13, "Only users, reviews and training_runs\nare database tables; foreign keys exist\nonly on user_id. A cluster decision is\nstored once and fans out to its members.",
            fontsize=6.9, color=GREY, style="italic", va="center")
    save(fig, OUT / "09_er_diagram.png")


def pipeline_flowchart():
    fig, ax = canvas(10, 10.8, 100, 108)
    x = 40
    steps = [
        (101, 5.4, "Start: public datasets in data/raw (Facebook ego networks,\nInstagram profile rows, Twitter posting rows)", NAVY, "start"),
        (92, 6.4, "ml.data.build (seed 7): keep the 3,963 real accounts and 88,156 ties;\nadd 8 botnets (34-62 accounts each) and 150 lone spammers", BLUE, ""),
        (82, 6.4, "Assign profile rows and posting rows; add timing and interaction\nfeatures; camouflage 40% of botnet and 25% of lone spammers", BLUE, ""),
        (72, 6.4, "Result: 4,533 accounts, 94,456 ties, 23 features, 570 fake (12.6%).\nStratified split 60 / 20 / 20 = 2,719 / 906 / 908", TEAL, ""),
        (62, 5.4, "Standardise features (mean 0, sd 1); build sparse adjacency", BLUE, ""),
        (51, 8.4, "for each model in {MLP baseline, GCN, GAT, GraphSAGE}\nfor each seed in {0, 1, 2}: train up to 160 epochs\n(Adam lr 0.01, class-weighted loss, keep best validation F1,\nstop after 40 epochs without gain)", PURPLE, ""),
        (40, 6.4, "Tune the decision threshold on the validation set\n(grid 0.10 to 0.90, best F1); score the test split once", PURPLE, ""),
        (30, 5.4, "Mean and standard deviation over the 3 seeds per model", PURPLE, ""),
    ]
    for y, h, t, c, _k in steps:
        box(ax, x, y, 58, h, t, c, fs=7.1)
    for (y1, h1, *_), (y2, h2, *_) in zip(steps[:-1], steps[1:]):
        arrow(ax, (x, y1 - h1 / 2), (x, y2 + h2 / 2), color=NAVY)
    diamond(ax, x, 19.5, 34, 9, "Best graph model\n(validation F1)?", fs=7.4)
    arrow(ax, (x, 30 - 2.7), (x, 24), color=NAVY)
    box(ax, 18, 7.5, 30, 8.4, "Serve it: GraphSAGE\nweights, scores of all\nmodels, 64-d embeddings", ORANGE, fs=7.2)
    box(ax, 62, 7.5, 32, 8.4, "Cluster detection on the\nserved embeddings (Louvain);\nwrite clusters.json", ORANGE, fs=7.2)
    arrow(ax, (x - 12, 17), (22, 11.8), "", color=NAVY)
    ax.text(x - 14, 14.6, "best", fontsize=7, color=NAVY, ha="right")
    arrow(ax, (33, 7.5), (46, 7.5), "", color=NAVY)
    box(ax, 91, 51, 15, 18, "Loop body:\n4 models x 3 seeds\n= 12 training runs\n(best seed 0 weights\nare the ones saved)", WHITE, tc=INK, ec=PURPLE, fs=6.6)
    arrow(ax, (84, 51), (69.4, 51), "", color=PURPLE, ls="--")
    box(ax, 91, 18, 15, 12, "Outputs:\nmodels/, scores.npz,\nmeta.json,\nmetrics.json", WHITE, tc=INK, ec=NAVY, fs=6.6)
    arrow(ax, (78, 7.5), (84, 14), "", color=NAVY)
    save(fig, OUT / "10_flowchart_pipeline.png")


def clustering_flowchart():
    fig, ax = canvas(10, 10.4, 100, 104)
    x = 42
    box(ax, x, 98, 56, 5.8, "Input: fake-probability p and 64-d embedding of every account,\nthe list of real ties", NAVY, fs=7.2)
    box(ax, x, 88, 50, 5.6, "Candidates = accounts with p >= 0.30  (CANDIDATE_PROB)", BLUE, fs=7.4)
    diamond(ax, x, 77, 36, 9, "At least 5\ncandidates?", fs=7.4)
    box(ax, 85, 77, 22, 7, "no: return no\nclusters", GREY, fs=7.2)
    box(ax, x, 65, 56, 6.4, "L2-normalise the candidates' embeddings; cosine similarity matrix;\nlink each candidate to its 5 most similar candidates (weight = similarity)", BLUE, fs=7.1)
    box(ax, x, 55, 56, 6.4, "For every real tie between two candidates add weight 1.0\n(coordinated follows and likes strengthen the link)", BLUE, fs=7.1)
    box(ax, x, 45, 50, 5.6, "Louvain community detection (networkx, resolution 1, seed 0)", PURPLE, fs=7.4)
    box(ax, x, 36, 50, 5.6, "Drop groups with fewer than 5 accounts; sort by size", PURPLE, fs=7.4)
    box(ax, x, 26, 56, 6.4, "Describe each group: size, mean score, flagged share, tie density,\nbusiest 3-hour window, creation spread, median activity", TEAL, fs=7.1)
    diamond(ax, x, 14, 40, 9, "Tie density\n>= 5% ?", fs=7.4)
    box(ax, 13, 4.5, 24, 6.4, "kind = coordinated\n(botnet cluster)", ORANGE, fs=7.2)
    box(ax, 71, 4.5, 24, 6.4, "kind = diffuse\n(loose group)", GREY, fs=7.2)
    arrow(ax, (x, 95.1), (x, 90.8), color=NAVY)
    arrow(ax, (x, 85.2), (x, 81.5), color=NAVY)
    arrow(ax, (x + 18, 77), (74, 77), "no", lo=(0, 1.6), fs=7.2, color=NAVY)
    arrow(ax, (x, 72.5), (x, 68.2), "yes", lo=(2.5, 0), fs=7.2, color=NAVY)
    for ya, yb in [(61.8, 58.2), (51.8, 47.8), (42.2, 38.8), (33.2, 29.2), (22.8, 18.5)]:
        arrow(ax, (x, ya), (x, yb), color=NAVY)
    arrow(ax, (x - 20, 14), (13, 7.7), "yes", lo=(-3, 1.6), fs=7.2, color=NAVY)
    arrow(ax, (x + 20, 14), (71, 7.7), "no", lo=(3, 1.6), fs=7.2, color=NAVY)
    box(ax, 85, 36, 24, 14, "Result on the served\nmodel: 9 groups -\n8 coordinated botnets\n+ 1 loose group of\n160 accounts", WHITE, tc=INK, ec=ORANGE, fs=6.6)
    arrow(ax, (73, 36), (67.2, 36), "", color=ORANGE, ls="--")
    ax.text(85, 22, "Each cluster gets\nid BN-<lowest member id>\nand is written to\nclusters.json", fontsize=6.8, color=GREY, ha="center", style="italic")
    save(fig, OUT / "11_flowchart_clustering.png")


def model_architecture():
    fig, ax = canvas(10, 7.4, 100, 74)
    box(ax, 9, 56, 14, 14, "Account\nfeatures X\n4,533 x 23\nstandardised", BLUE, fs=7.4)
    flow = [("Dropout 0.3", PURPLE), ("Layer 1\n23 -> 64, ELU", PURPLE), ("Dropout 0.3", PURPLE), ("Layer 2\n64 -> 64, ELU", PURPLE), ("Dropout 0.3", PURPLE), ("Linear 64 -> 2\nsoftmax", ORANGE)]
    xs = [24, 36, 48, 60, 72, 86]
    ws = [9, 11, 9, 11, 9, 14]
    prev = 16
    for x, w, (t, c) in zip(xs, ws, flow):
        box(ax, x, 56, w, 12 if "\n" in t else 8, t, c, fs=6.8)
        arrow(ax, (prev, 56), (x - w / 2, 56), color=NAVY)
        prev = x + w / 2
    ax.text(60, 47.5, "embedding (64-d): used for botnet clustering", ha="center", fontsize=7, color=PURPLE)
    arrow(ax, (60, 50), (60, 49.0), "", color=PURPLE)
    ax.text(86, 47.5, "p(fake)", ha="center", fontsize=7.6, color=ORANGE, fontweight="bold")
    ax.text(50, 66.5, "Two message-passing layers (or two dense layers for the baseline) and a linear head; same sizes for every model", ha="center", fontsize=8.6, color=NAVY, fontweight="bold")
    panel(ax, 2, 3, 96, 40, "What one message-passing layer computes", LIGHT)
    rows = [
        ("Baseline MLP", GREY, r"$h_v' = \mathrm{ELU}(W\,x_v + b)$     no neighbours; the account's own features only"),
        ("GCN", BLUE, r"$H' = \mathrm{ELU}(\hat{A}\,H\,W)$,   $\hat{A} = D^{-1/2}(A + I)D^{-1/2}$     symmetric normalisation with self-loops"),
        ("GraphSAGE", TEAL, r"$h_v' = \mathrm{ELU}(W_s\,h_v + W_n \cdot \mathrm{mean}_{u \in N(v)}\,h_u)$     separate weights for self and neighbours"),
        ("GAT", PURPLE, r"$e_{uv} = \mathrm{LeakyReLU}(a_s \cdot W h_u + a_d \cdot W h_v)$,   $\alpha_{uv} = \mathrm{softmax}_u(e_{uv})$,   $h_v' = \mathrm{ELU}(\sum_u \alpha_{uv} W h_u)$"),
    ]
    for i, (n, c, f) in enumerate(rows):
        y = 33 - i * 7.6
        box(ax, 12, y, 14, 5.0, n, c, fs=7.6, bold=True)
        ax.text(21, y, f, fontsize=7.4, va="center", color=INK)
    ax.text(21, 5.8, "GAT: layer 1 has 4 heads of 16 units (concatenated, 64), layer 2 has 1 head of 64. Loss: cross-entropy, class weights 1 and sqrt(genuine / fake).\nAdam lr 0.01, weight decay 5e-4, up to 160 epochs, early stopping on validation F1 (patience 40).",
            fontsize=6.9, color=GREY, style="italic")
    save(fig, OUT / "12_model_architecture.png")


def main():
    er_diagram()
    pipeline_flowchart()
    clustering_flowchart()
    model_architecture()


if __name__ == "__main__":
    main()
