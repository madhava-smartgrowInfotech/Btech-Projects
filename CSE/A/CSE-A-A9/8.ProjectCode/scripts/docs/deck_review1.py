"""7.Review_1_PPT.pptx: 16 slides, problem identification and research. Built from D:\\abstracts\\Templates\\Review_1_PPT.pptx.

Content is written here (batch documents + verified facts only); numbers come from facts.py.
"""

import os

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_1_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"


def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.FULL_TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.keywords = "graph neural networks, fake profile detection, botnet detection, GCN, GAT, GraphSAGE, social network analysis"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text, size)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors, cols=3):
    n = len(items)
    rows = (n + cols - 1) // cols
    gx, gy = 0.29, 0.3
    w = (12.13 - gx * (cols - 1)) / cols
    h = min(1.45, (5.3 - gy * (rows - 1)) / rows)
    x0, y0 = 0.6, 1.55
    for i, (n_, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + gy)
        K.box(slide, x, y, w, h)
        K.text(slide, x + 0.25, y + 0.14, 1.0, 0.5, n_, size=26, color=colors[i % len(colors)], bold=True, font="Cambria")
        K.text(slide, x + 0.25, y + 0.72, w - 0.5, 0.65, label, size=16, color=K.INK, bold=True)


def title_slide(s, subtitle, label):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE, 30)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 18)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"{F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


# ---------------------------------------------------------------- slide text (batch documents + verified facts only)
PROBLEM_STATEMENT = [
    "Fake profiles are created faster than manual moderation can remove them",
    "Per-account classifiers miss coordinated networks whose individual profiles look legitimate",
    "Bot behaviour evolves quickly, so static rules and signatures become obsolete",
    "Class imbalance and label noise degrade conventional supervised models",
    "Need: a graph-based detector that classifies accounts from their relational context and exposes coordinated botnet clusters at scale",
]
OBJECTIVES = [
    "Construct a graph of the platform: accounts as nodes, interactions as edges",
    "Engineer node features: profile metadata, posting behaviour and interaction frequency",
    "Implement and compare GCN, GAT and GraphSAGE for account classification",
    "Detect coordinated botnet clusters from the learned graph embeddings",
    "Evaluate accuracy, precision and recall against labelled fake-account data",
    "Assess scalability as the number of nodes and edges grows",
]
# (work, year, approach, finding / limitation) - verified from the PDFs in Documentary/ and archived_base_papers/, or from the arXiv records
LIT = [
    ["PruferNET (base paper) [1]", "2026", "MST + Prufer-sequence features with degree, closeness, PageRank; GraphSAGE node classifier",
     "99.63% vs 96.54% accuracy on Facebook depth classes; influence task, no fake labels"],
    ["RABot [2]", "2026", "Neighbourhood-aware oversampling and reinforcement-learned edge filtering for GNN bot detectors",
     "Targets class imbalance and noisy links; three benchmarks, four backbones; no cluster output"],
    ["HW-GNN [3]", "2025", "Homophily-aware spectral GNN with learnable Gaussian windows",
     "+4.3% F1 on average over earlier methods; per-account scores, no botnet grouping"],
    ["LGB [4]", "2024", "Language model plus GNN for accounts with few links",
     "Up to 10.95% over baselines on two datasets; needs account text"],
    ["BotDGT [5]", "2024", "Dynamic graph transformer over snapshots of the network",
     "Models change over time; heavier model, no moderator workflow"],
    ["Metadata + stacking (nearest match) [11]", "2026", "Account-level features, Spearman selection, stacked classifiers",
     "Random forest 89%, stacked 90%; ignores the graph entirely"],
]
REFS = [
    "A. Saha, N. K. Sarkar and S. Pratihar, \"PruferNET: An augmented graph neural network for influential node detection in social networks,\" IEEE Access, vol. 14, 2026, doi: 10.1109/ACCESS.2026.3695637.",
    "L. Zhang, X. Wang, H. Du, Y. Xu, Z. Liu and Y. Liu, \"RABot: Reinforcement-guided graph augmentation for imbalanced and noisy social bot detection,\" arXiv:2602.21749, 2026.",
    "Z. Liu, J. Gao, Z. Ji and L. Zhao, \"HW-GNN: Homophily-aware Gaussian-window constrained graph spectral network for social network bot detection,\" arXiv:2511.22493, 2025.",
    "\"LGB: Language model and graph neural network-driven social bot detection,\" arXiv:2406.08762, 2024.",
    "\"BotDGT: Dynamicity-aware social bot detection with dynamic graph transformers,\" arXiv:2404.15070, 2024.",
    "T. N. Kipf and M. Welling, \"Semi-supervised classification with graph convolutional networks,\" in Proc. ICLR, 2017.",
    "P. Velickovic et al., \"Graph attention networks,\" in Proc. ICLR, 2018.",
    "W. L. Hamilton, R. Ying and J. Leskovec, \"Inductive representation learning on large graphs,\" in Proc. NeurIPS, 2017.",
    "V. D. Blondel, J.-L. Guillaume, R. Lambiotte and E. Lefebvre, \"Fast unfolding of communities in large networks,\" J. Stat. Mech., 2008, P10008.",
    "J. Leskovec and J. J. McAuley, \"Learning to discover social circles in ego networks,\" in Proc. NeurIPS, 2012.",
    "J. Sharma and S. Borah, \"Stacking of machine learning classifiers for bot detection using account level data,\" Int. J. Informatics Commun. Technol., vol. 15, no. 2, pp. 477-487, 2026.",
]


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 1")
    S = list(prs.slides)
    assert len(S) == 16, len(S)
    notes = {}
    C = [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE]
    bp = F.BASE_PAPER_RESULTS

    # ---- 1 title
    title_slide(S[0], F.SUBTITLE, "REVIEW 1  ·  PROBLEM IDENTIFICATION AND RESEARCH")
    notes[1] = ("Introduce the team and the title. One sentence: BotGraph treats accounts as nodes and interactions as edges, lets graph neural networks learn from each account's neighbourhood, "
                "and groups flagged accounts into botnet clusters that a moderator can review.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Abstract and overview"), ("02", "Base paper"), ("03", "Literature survey and evidence"), ("04", "Existing system and limitations"),
               ("05", "Research gap"), ("06", "Problem statement and objectives"), ("07", "Proposed approach and architecture"),
               ("08", "Expected outcomes"), ("09", "References")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda. This review is about why the problem matters and what is missing in current work; design details and measured results come in the later reviews."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract: look at the network, not just the profile")
    wipe(s)
    W, H = 3.85, 5.0
    for i, (t, body, col, gl) in enumerate([
        ("The problem", "Indian social platforms such as ShareChat and Moj face a surge of fake profiles and automated botnets. Rule-based filters and per-account classifiers examine each account alone, so coordinated networks of normal-looking profiles slip through.", K.ORANGE, "!"),
        ("Our idea", "Map the platform as a graph: accounts are nodes, interactions such as follows and likes are edges. GCN, GAT and GraphSAGE learn from each account's neighbourhood and its own features, and community detection over the learned embeddings exposes coordinated clusters.", K.BLUE, "i"),
        ("The deliverable", "BotGraph: a graph builder with 23 node features, a comparison of three architectures against a no-graph baseline, botnet clusters, an API and a web app where moderators confirm or dismiss what the model flags.", K.GREEN, "✓"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, H, t, body, col, gl, body_size=18)
    notes[3] = "Three points: why per-account detection falls short, the graph idea, and what is delivered. Everything runs on one laptop CPU."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base paper")
    wipe(s)
    K.box(s, 0.6, 1.4, 12.13, 1.1, fill=K.CARD)
    K.text(s, 0.82, 1.48, 11.7, 0.95, F.BASE_PAPER, size=13, color=K.INK, anchor="m")
    cw = 3.85
    cards = [
        ("Method", "Builds a minimum spanning tree of the Facebook graph, derives a Prufer sequence and features from it (label frequency, entropy, unique-label ratio, transition influence, subtree depth), adds degree, closeness, PageRank and a trust score, and classifies nodes with GraphSAGE.", K.BLUE, "M"),
        ("Data and reported results", f"SNAP Facebook, 4,039 nodes and 88,234 edges; Email-Eu-core as a second network. Three depth classes, 60/20/20 split. Test accuracy {bp['with_prufer_acc'] * 100:.2f}% with Prufer features against {bp['without_prufer_acc'] * 100:.2f}% without.", K.GREEN, "R"),
        ("Relevance to this project", "Shared ground: the same family of ego-network data, GraphSAGE and the idea that structure adds information a per-node model lacks. Different task: it finds influential nodes, with no fake labels, no botnets and no scalability study.", K.ORANGE, "L"),
    ]
    for i, (t, b_, col, gl) in enumerate(cards):
        K.card(s, 0.6 + i * (cw + 0.29), 2.75, cw, 4.0, t, b_, col, gl, body_size=17)
    notes[4] = ("Read the citation. PruferNET adds global tree-based structure to a GraphSAGE node classifier. Its accuracy figures measure a depth-classification task and cannot be compared "
                "with fake-account detection; we reuse the idea that structure helps, and name the Prufer features as possible future work.")

    # ---- 5 literature survey table
    s = S[4]
    set_title(s, "Literature survey")
    wipe(s)
    rows = [["Work", "Year", "Approach", "Reported result / limitation"]] + LIT
    K.table(s, 0.6, 1.3, [2.7, 0.65, 4.6, 4.18], rows, font_size=13.5, row_h=0.74, header_size=14, align=["l", "c", "l", "l"])
    K.text(s, 0.6, 6.7, 12.13, 0.4, "The batch survey also lists AdapTGN (2026) and an Arabic fake-news GNN (2026); neither could be verified from public records, so no result is quoted from them.", size=12, color=K.TXT, italic=True)
    notes[5] = ("Six works whose content was read from the paper or its public record. Figures are quoted only as the sources state them. "
                "Two further titles from the batch survey could not be located and are listed in the report as not verified.")

    # ---- 6 supporting evidence
    s = S[5]
    set_title(s, "Supporting evidence: neighbourhood information helps")
    wipe(s)
    cats = [F.LABEL[m].replace("Feature-only baseline (MLP)", "No-graph\nbaseline (MLP)") for m in F.ORDER]
    vals = [F.mean(m, "f1") for m in F.ORDER]
    gf = K.bar_chart(s, 0.6, 1.4, 6.2, 5.0, cats, [("F1 on the test split", vals)], colors=[K.BLUE], number_format="0.000", font_size=12, max_value=1.0)
    pt = gf.chart.plots[0].series[0].points[0]
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = K.ORANGE
    K.text(s, 7.1, 1.45, 5.65, 4.9, [
        ("**Early pilot on our benchmark** (F1, mean of 3 seeds, 908 test accounts; botnets are injected, features partly synthetic):", {"space_after": 8}),
        (f"Own features only: {vals[0]:.3f}. GraphSAGE, which also reads neighbours: {vals[3]:.3f}. The direction is encouraging; the size of the gain is not a platform result.", {"bullet": True, "space_after": 8}),
        ("The graph does not help automatically: GCN adds only about one point of F1.", {"bullet": True, "space_after": 8}),
        ("Reported bot-detection work shows the same direction: HW-GNN reports +4.3% F1 on average over earlier methods [3].", {"bullet": True, "space_after": 8}),
        ("Injected botnets are densely tied, which makes them easier to find than real ones: real-world gains may be smaller.", {"bullet": True, "space_after": 8}),
        ("Fake accounts are 12.6% of the data, so F1 and recall matter more than accuracy.", {"bullet": True}),
    ], size=14.5, color=K.INK)
    K.text(s, 7.1, 6.4, 5.65, 0.6, "Not real-platform accuracy. Early numbers to frame the problem; full protocol in Review 2.", size=12, color=K.TXT, italic=True)
    notes[6] = ("These are our own pilot runs, shown only to motivate the approach. The benchmark mixes public ego-network topology with injected, seeded botnets, so the values describe this benchmark and not live platforms. "
                "The no-graph baseline is the bar we must beat.")

    # ---- 7 existing system
    s = S[6]
    set_title(s, "Existing system and current approaches")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.1, [("Account profile", K.NAVY), ("Hand-written rules or classifier", K.NAVY), ("Score per account", K.NAVY), ("Manual moderation queue", K.NAVY)], size=15, gap=0.5)
    K.card(s, 0.6, 2.95, 5.95, 3.8, "Rules and per-account classifiers",
           "Filters look at one profile at a time: posting rate, follower ratio, bio, picture.\nClassical models such as random forests treat each account as an independent row.\nA botnet of normal-looking profiles passes every individual check.", K.BLUE, "1", body_size=20)
    K.card(s, 6.78, 2.95, 5.95, 3.8, "Graph-based research prototypes",
           "Recent GNN work improves single-account scores under imbalance, noise or time change [2]-[5].\nIt is normally evaluated on benchmark files, and rarely gives a cluster of coordinated accounts or a workflow for a moderator.", K.ORANGE, "2", body_size=20)
    notes[7] = "Today detection is either rule-based or per account; the research prototypes improve the score but stop at the score. Nobody hands a moderator a botnet to confirm in one click."

    # ---- 8 limitations
    s = S[7]
    set_title(s, "Limitations of existing methods")
    wipe(s)
    heads = ["Blind to coordination", "Static rules go stale", "Imbalance and noise", "Hard to deploy and trust"]
    bodies = [
        "Isolated-account models cannot see that fifty similar accounts follow each other and act in the same hour.",
        "Fixed rules and signatures stop working as soon as bot behaviour changes.",
        "Only about 1 in 8 accounts is fake in our data; plain supervised models favour the majority class and suffer from wrong labels.",
        "Scores without reasons, clusters or a review step leave moderators with a list they cannot act on; scalability is seldom measured.",
    ]
    for i in range(4):
        r, c = divmod(i, 2)
        K.card(s, 0.6 + c * 6.18, 1.45 + r * 2.35, 5.95, 2.15, heads[i], bodies[i], C[i], str(i + 1), body_size=19)
    K.box(s, 0.6, 6.25, 12.13, 0.75, fill=K.CARD)
    K.text(s, 0.85, 6.25, 11.7, 0.75, "Also: the base paper's accuracy comes from an influence task and cannot be used as a bot-detection benchmark [1].", size=15, color=K.INK, anchor="m")
    notes[8] = "Four limitations from the batch problem statement and the survey. Each maps to a design choice: graph context, learned embeddings, a class-weighted loss and a moderator queue."

    # ---- 9 research gap
    s = S[8]
    set_title(s, "Research gap")
    wipe(s)
    gaps = [
        "Surveyed GNN work targets influence and node classification in social graphs; relational learning for fake-profile and botnet detection at platform scale remains thin.",
        "Most bot detectors return one score per account; few expose the coordinated groups and describe what they share.",
        "GCN, GAT and GraphSAGE are seldom compared on one split against a no-graph baseline with the same features, so the benefit of the graph is unproven.",
        "Scalability is claimed more often than measured, and review decisions rarely feed back into the model.",
    ]
    for i, g in enumerate(gaps):
        y = 1.4 + i * 1.38
        K.circle(s, 0.6, y + 0.15, 0.62, C[i % 4], str(i + 1), 18)
        K.text(s, 1.55, y, 11.15, 1.2, g, size=19, color=K.INK, anchor="m")
    notes[9] = ("The first gap is the batch survey's own statement. Gaps 2 to 4 come from reading the related work: score-only outputs, missing baseline comparisons, and unmeasured scale. "
                "BotGraph addresses each of them.")

    # ---- 10 problem statement
    s = S[9]
    set_title(s, "Problem statement")
    wipe(s)
    K.box(s, 0.6, 1.45, 12.13, 3.1, fill=K.CARD)
    K.text(s, 0.95, 1.6, 11.45, 2.85, [(p, {"bullet": True, "space_after": 8}) for p in PROBLEM_STATEMENT], size=19, color=K.INK, anchor="m")
    for i, (t, b_) in enumerate([("Input", "A social graph: accounts with 23 profile, posting, timing and interaction features, and the ties between them"),
                                 ("Output", "A fake-probability for every account with the traits behind it, plus botnet clusters of coordinated accounts"),
                                 ("Record", "Moderator decisions, retraining runs with F1 before and after, model comparison and scalability timings")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 4.8, 3.85, 1.95)
        K.text(s, x + 0.25, 4.9, 3.4, 0.4, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 5.35, 3.4, 1.35, b_, size=16, color=K.TXT)
    notes[10] = "Read the statement slowly. The need is a graph-based detector that classifies accounts from relational context and exposes coordinated botnet clusters at scale."

    # ---- 11 objectives
    s = S[10]
    set_title(s, "Objectives")
    wipe(s)
    K.text(s, 0.6, 1.4, 12.13, 4.9, [(f"{i}.  {o}", {"space_after": 14}) for i, o in enumerate(OBJECTIVES, 1)], size=22, color=K.INK)
    K.text(s, 0.6, 6.35, 12.13, 0.7, "Scope note: topology comes from public ego networks; botnets are injected and seeded so that cluster detection can be scored against a known answer.", size=14, color=K.TXT, italic=True)
    notes[11] = ("The six objectives from the proposal. Later reviews report which were met. We will state plainly that the botnets are injected, "
                 "and that the abstract's linguistic cues are not part of the 23 features.")

    # ---- 12 proposed approach
    s = S[11]
    set_title(s, "Proposed approach")
    wipe(s)
    cw = 2.88
    for i, (t, b_, col, gl) in enumerate([
        ("Build the graph", "Real Facebook ego-network ties plus labelled profile and posting rows; 23 features in four groups; a documented node and edge schema.", K.BLUE, "1"),
        ("Learn and compare", "GCN, GAT and GraphSAGE (two layers, 64 units) and a no-graph baseline on one stratified 60/20/20 split, three seeds each, class-weighted loss.", K.GREEN, "2"),
        ("Find botnets", "Louvain communities over the embeddings of accounts scored at 0.30 or more; each cluster gets size, tie density and shared behaviour.", K.ORANGE, "3"),
        ("Review and scale", "A moderator confirms or dismisses accounts or clusters; decisions feed retraining; timings are measured as the graph grows.", K.PURPLE, "4"),
    ]):
        K.card(s, 0.6 + i * (cw + 0.2), 1.45, cw, 3.7, t, b_, col, gl, body_size=16.5)
    K.box(s, 0.6, 5.35, 12.13, 1.4)
    K.circle(s, 0.85, 5.65, 0.7, K.NAVY, "G", 18)
    K.text(s, 1.8, 5.5, 10.7, 0.45, "Node = account  ·  edge = tie  ·  embedding = what a GNN learns about its neighbourhood", size=16, color=K.INK, bold=True)
    K.text(s, 1.8, 5.95, 10.7, 0.75, "Delivered as a FastAPI service with SQLite and a React web app; models are small enough to train on a laptop CPU, with no GPU and no outside service.", size=15, color=K.TXT)
    notes[12] = ("Four stages. The no-graph baseline uses the same features and split, so any gain is due to the graph. "
                 "Retraining never touches the test split, so before-and-after figures stay comparable.")

    # ---- 13 architecture
    s = S[12]
    set_title(s, "High-level proposed architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.2, 7.5, 5.9)
    K.text(s, 8.3, 1.5, 4.4, 5.2, [
        ("**Four layers**", {"space_after": 8}),
        ("Data: public datasets and the injected botnets become one graph on disk.", {"bullet": True}),
        ("ML pipeline: feature builder, GCN / GAT / GraphSAGE, clustering, evaluation.", {"bullet": True}),
        (f"API: FastAPI on port {F.API_PORT}, JWT roles (analyst, moderator), SQLite for users, decisions and runs.", {"bullet": True}),
        (f"Web app: React on port {F.WEB_PORT} with overview, accounts, clusters, queue and model screens.", {"bullet": True}),
    ], size=18, color=K.INK)
    notes[13] = "Follow the diagram from the data layer up to the web app. Model files and scores are loaded once when the API starts."

    # ---- 14 expected outcomes
    s = S[13]
    set_title(s, "Expected outcomes and contributions")
    wipe(s)
    heads = ["Working platform", "Architecture comparison", "Botnet clusters", "Scale evidence", "Stated limits"]
    bodies = [
        "Graph builder, account scores with reasons, cluster explorer, moderator queue and retraining in one app.",
        "GCN, GAT and GraphSAGE against a no-graph baseline on one split, with precision, recall, F1 and ROC-AUC.",
        "Coordinated groups recovered from embeddings and scored against the injected, known botnets.",
        "Training and inference time as accounts and ties grow, on an ordinary CPU.",
        "Injected botnets, partly synthetic features, no text features and no live platform data: each limit documented, not hidden.",
    ]
    for i, (h, b_) in enumerate(zip(heads, bodies)):
        if i < 3:
            K.card(s, 0.6 + i * 4.14, 1.5, 3.85, 2.65, h, b_, C[i % 4], str(i + 1), body_size=18)
        else:
            K.card(s, 0.6 + (i - 3) * 6.18, 4.35, 5.95, 2.4, h, b_, C[i % 4], str(i + 1), body_size=19)
    notes[14] = "These are the outcomes we commit to; at this stage they are targets. Review 2 and the final review report what was actually measured, including what could not be."

    # ---- 15 references
    s = S[14]
    set_title(s, "References")
    wipe(s)
    K.text(s, 0.6, 1.25, 12.13, 5.85, [(f"[{n}] {r}", {"space_after": 4}) for n, r in enumerate(REFS, 1)], size=14, color=K.INK)
    notes[15] = "Selected references; the complete numbered list, including items marked as not verified, is in the project report."

    # ---- 16 thank you
    thank_you(S[15])
    notes[16] = ("Likely questions: why compare three architectures (the batch objective, and GCN, GAT and GraphSAGE aggregate neighbours differently); "
                 "why injected botnets (public data has no labelled botnet groups, so recovery needs a known answer); why not the base paper's Prufer features (a different task; kept as future work).")

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "7.Review_1_PPT.pptx")))
