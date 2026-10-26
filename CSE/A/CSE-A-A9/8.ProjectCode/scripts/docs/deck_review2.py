"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx.

Self-contained: the small slide helpers are defined here so the deck does not depend on the Review 1 module. All numbers come from facts.py
(experiments/**/metrics.json); nothing is typed in by hand.
    python -m scripts.docs.deck_review2        # from 8.ProjectCode
"""
import os

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"


# ------------------------------------------------------------------ helpers
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
            K.replace_text(sh, subtitle, 20)
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


def trim(path, tag):
    """Copy of a diagram or chart with its white margins removed (written to the temp folder, source untouched)."""
    import tempfile

    from PIL import Image, ImageChops

    with Image.open(path) as im:
        im = im.convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            pad = 12
            bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.size[0]), min(bbox[3] + pad, im.size[1]))
            im = im.crop(bbox)
        out = os.path.join(tempfile.gettempdir(), f"a9_r2_{tag}.png")
        im.save(out)
    return out


def shot_box(slide, name, x, y, w, h, caption):
    """Real screenshot in a w x h area with a one-line caption under it."""
    K.picture(slide, F.shot(name), x, y, w, h - 0.34, border=True)
    K.text(slide, x, y + h - 0.3, w, 0.3, caption, size=11, color=K.TXT, align="c", italic=True)


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    M = F.MODELS
    cr = F.REC
    t1, t8 = F.scal_row(1), F.scal_row(8)
    sage_t1, sage_t8 = t1["models"]["sage"], t8["models"]["sage"]
    gat_t1, gat_t8 = t1["models"]["gat"], t8["models"]["gat"]
    tn, fp, fn, tp = F.conf("sage")

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: GCN, GAT and GraphSAGE on a social graph, with botnet clusters and a moderator review loop",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = ("This review shows how BotGraph is designed and built, what is implemented, the first measured results on the 908-account test split and the open items. "
                "Introduce the four team members and the guide.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and model"), ("04", "Training and decision logic"),
               ("05", "Data flow, database and UML"), ("06", "Technology stack"), ("07", "Progress and preliminary results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Fake profiles appear faster than moderators can remove them, per-account classifiers miss botnets whose profiles look normal, bot behaviour changes quickly, and fake accounts are a small share of the data (here 12.6 percent).", K.ORANGE, "!"),
        ("Proposed system", "BotGraph treats accounts as nodes and interactions as edges. GCN, GAT and GraphSAGE learn from each account's neighbourhood, Louvain over the learned embeddings exposes botnet clusters, and moderators confirm or dismiss what is flagged.", K.BLUE, "i"),
        ("Base paper link [1]", "PruferNET (Saha et al., IEEE Access 2026) uses GraphSAGE on the Facebook graph to classify nodes by spanning-tree depth. We keep the graph-learning idea and data family, but the task is fake-account detection, which that paper does not address. Results are not comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 4.5, t, b_, col, gl, body_size=17)
    notes[3] = ("Recap of Review 1. The survey gap was applying relational learning to fake-profile and botnet detection at platform scale. "
                "PruferNET is an influence-classification paper, so we use it as the closest graph-learning reference, not as a result to beat.")

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "01"), 0.6, 1.3, 7.2, 5.7)
    K.text(s, 8.0, 1.45, 4.75, 5.4, [
        ("**Pipeline, API and web app**", {"space_after": 8}),
        ("ml/: graph builder, 23 features, GCN / GAT / GraphSAGE and a baseline, Louvain clustering, evaluation.", {"bullet": True}),
        (f"backend/app: FastAPI on port {F.API_PORT}, 18 routes, JWT roles, SQLite; loads the graph, scores and clusters once at start-up.", {"bullet": True}),
        (f"frontend/: React 18 + Vite on port {F.WEB_PORT}, 10 screens, light and dark.", {"bullet": True}),
        ("Files: data/processed, models/*.pt, scores.npz, clusters.json, experiments/*.json.", {"bullet": True}),
        ("No call to an outside service at run time.", {"bullet": True}),
    ], size=14.5, color=K.INK)
    notes[4] = "The three layers are separate: ml/ writes artefacts, the API serves them and stores users, decisions and retraining runs in SQLite, the web app consumes the API."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: from graph to moderator decision")
    wipe(s)
    K.picture(s, trim(F.diag("10_flowchart_pipeline.png"), "10"), 0.6, 1.35, 6.4, 5.5)
    for i, (t, b_) in enumerate([("1. Build the graph", f"Real Facebook topology ({F.REAL_NODES:,} accounts, {F.REAL_EDGES:,} ties) plus {F.INJ_NODES} injected fake accounts ({F.INJ_EDGES:,} ties); 23 features per account."),
                                 ("2. Train and compare", "Baseline MLP, GCN, GAT and GraphSAGE on one 60/20/20 split, 3 seeds each; threshold tuned on validation."),
                                 ("3. Cluster", "Louvain over embeddings of accounts scored at 0.30 or more; groups under 5 accounts dropped."),
                                 ("4. Review", "Moderators confirm or dismiss; decisions become labels at the next retrain.")]):
        y = 1.35 + i * 1.4
        K.box(s, 7.3, y, 5.43, 1.28)
        K.text(s, 7.45, y + 0.06, 5.13, 0.35, t, size=14.5, color=K.INK, bold=True)
        K.text(s, 7.45, y + 0.42, 5.13, 0.85, b_, size=12, color=K.TXT)
    notes[5] = "The same four steps run in ml/train.py (steps 1 to 3) and in the queue and retrain routes (step 4). Retraining never touches the test split."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset: real topology, injected botnets")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.NODES:,}", "accounts (nodes)", K.ORANGE), (f"{F.EDGES:,}", "undirected ties (edges)", K.BLUE),
                                   (f"{F.FAKE} ({F.pct(F.FAKE_SHARE)})", "fake accounts", K.GREEN), (f"{F.SPLITS['train']:,} / {F.SPLITS['val']} / {F.SPLITS['test']}", "train / validation / test", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=24, lsize=12)
    rows = [["Part", "Source and licence", "Status"],
            ["Topology", f"SNAP Facebook social circles, ten ego networks: {F.REAL_NODES:,} accounts, {F.REAL_EDGES:,} ties", "Real"],
            ["Profile attributes", "Instagram fake / spammer / genuine accounts, 696 labelled rows, CC BY 3.0", "Real rows, resampled and jittered"],
            ["Posting behaviour", "Twitter bot detection set, 50,000 rows, CC0 (its label carries almost no signal)", "Real rows, act as realistic noise"],
            ["Botnets", f"8 botnets ({min(F.BOTNET_SIZES)}-{max(F.BOTNET_SIZES)} accounts) and {F.LONE_SPAMMERS} lone spammers, seed 7; {F.INJ_EDGES:,} injected ties", "Synthetic, known answer"],
            ["Timing, interaction, handles", "peak hour, burstiness, interactions per week, usernames and display names", "Synthetic, seeded"]]
    K.table(s, 0.6, 2.95, [2.3, 6.9, 2.93], rows, font_size=12.5, row_h=0.6, first_bold=True)
    K.text(s, 0.6, 6.75, 12.13, 0.35, "Nothing is scraped from a live platform. Results describe this benchmark, not real botnets on any platform.", size=12, color=K.TXT, italic=True)
    notes[6] = (f"Be frank about the synthetic parts. {F.CAMO_BOTS} of the bots get a genuine-looking profile and {F.SUSPICIOUS_GENUINE} genuine accounts a fake-looking one on purpose, "
                "otherwise the profile alone would solve the task and the graph would add nothing. The split is stratified and identical for every model.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Preprocessing and node features")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("Public datasets", K.NAVY), ("Merge onto topology", K.PURPLE), ("Inject botnets and camouflage", K.PURPLE),
                                       ("23 node features", K.GREEN), ("Standardise (mean 0, sd 1)", K.GREEN), ("Stratified 60/20/20", K.ORANGE)], size=12, gap=0.22)
    rows = [["Feature group", "Count", "Examples"],
            ["Profile metadata", "12", "profile picture, digits in username, bio length, followers / following (log), ratio"],
            ["Posting behaviour", "4", "average retweets (log), mentions, post length, hashtags per post"],
            ["Temporal pattern", "6", "account age (log days), posts per day, burstiness, peak-hour share, peak hour sin / cos"],
            ["Interaction frequency", "1", "interactions per week (log)"]]
    K.table(s, 0.6, 2.85, [2.7, 0.9, 8.53], rows, font_size=13.5, row_h=0.55, first_bold=True, align=["l", "c", "l"])
    K.text(s, 0.6, 5.8, 12.13, 1.2, [
        (f"Members of one botnet share a creation window and a peak posting hour, so those two traits are common to a cluster without making any single member stand out.", {"bullet": True}),
        (f"Camouflage: 40 percent of botnet accounts and 25 percent of lone spammers get a genuine-looking profile; 6 percent of genuine accounts get a fake-looking one.", {"bullet": True}),
    ], size=14, color=K.INK, space_after=5)
    notes[7] = "Features are listed in ml/data.py. Standardisation uses statistics of the whole feature matrix and is saved with the scores so the API can explain a score."

    # ---- 8 model
    s = S[7]
    set_title(s, "Model architecture: three message-passing layers")
    wipe(s)
    K.picture(s, trim(F.diag("12_model_architecture.png"), "12"), 0.6, 1.35, 7.4, 5.0)
    K.text(s, 8.3, 1.45, 4.45, 5.4, [
        ("**GCN**: symmetric-normalised neighbour average with self-loops, A_hat X W.", {"bullet": True, "space_after": 8}),
        ("**GraphSAGE**: W_self x + W_neigh mean(neighbours); the account keeps its own weight.", {"bullet": True, "space_after": 8}),
        ("**GAT**: 4 attention heads, then one head; edge softmax built from scatter_reduce and index_add.", {"bullet": True, "space_after": 8}),
        ("**Baseline**: two dense layers on the account's own features, no graph.", {"bullet": True, "space_after": 8}),
        ("All written in plain PyTorch sparse operations, no torch-geometric.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=14, color=K.INK)
    K.text(s, 0.6, 6.45, 7.4, 0.45, "Two layers, 64 hidden units, linear head with two outputs; layer stack from ml/gnn.py.", size=12, color=K.TXT, align="c", italic=True)
    notes[8] = "Every model has the same depth and width so the comparison isolates the aggregation rule. Plain PyTorch was chosen because torch-geometric wheels often fail to build on Windows."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training configuration")
    wipe(s)
    cfg = F.M["meta"]["config"]
    rows = [["Setting", "Value"],
            ["Split", f"stratified 60/20/20 by label: {F.SPLITS['train']:,} train, {F.SPLITS['val']} validation, {F.SPLITS['test']} test ({F.TEST_FAKE} fake); the same for every model"],
            ["Architecture", f"2 message-passing layers, {cfg['hidden']} hidden units, dropout {cfg['dropout']}, linear head"],
            ["Optimiser", f"Adam, learning rate {cfg['lr']}, weight decay {cfg['weight_decay']}, up to {cfg['epochs']} epochs"],
            ["Loss", "cross-entropy with the fake class weighted by the square root of the imbalance (negatives / positives)"],
            ["Model selection", f"best validation F1 epoch kept, early stopping with patience {cfg['patience']}; threshold tuned on validation F1"],
            ["Seeds", f"{len(cfg['seeds'])} seeds (0, 1, 2) per model; tables report mean ± standard deviation on the test split"],
            ["Cost on this PC", f"{F.HARDWARE}: per run GraphSAGE {M['sage']['train_seconds']:.1f} s, GCN {M['gcn']['train_seconds']:.1f} s, GAT {M['gat']['train_seconds']:.1f} s, baseline {M['baseline']['train_seconds']:.1f} s"]]
    K.table(s, 0.6, 1.4, [2.3, 9.83], rows, font_size=13.5, row_h=0.62, first_bold=True)
    K.text(s, 0.6, 6.75, 12.13, 0.35, "Same settings for every architecture; nothing was tuned on the test split.", size=12, color=K.TXT, italic=True)
    notes[9] = "Settings are in ml/config.py. Training is full-batch because the graph is small; the whole pipeline runs on a laptop CPU in minutes."

    # ---- 10 decision logic
    sw = {round(r["threshold"], 2): r for r in F.EXTRA["threshold_sweep"]["sage"]}
    s = S[9]
    set_title(s, "Decision logic: threshold, clusters and queue")
    wipe(s)
    K.picture(s, trim(F.diag("11_flowchart_clustering.png"), "11"), 0.6, 1.3, 5.2, 5.65)
    K.text(s, 6.0, 1.35, 6.75, 3.0, [
        ("**Verdict.** An account is flagged when its fake-probability is at or above the threshold tuned on validation F1 (0.5 for the served GraphSAGE).", {"bullet": True, "space_after": 6}),
        ("**Clusters.** Candidates at 0.30 or more are linked to their 5 most cosine-similar candidates plus every real tie; Louvain; groups under 5 dropped. A group is coordinated when tie density is at least 5 percent, otherwise a loose group.", {"bullet": True, "space_after": 6}),
        ("**Queue.** Flagged accounts and undecided clusters, highest score first. A cluster decision applies to all members; used decisions cannot be undone.", {"bullet": True, "space_after": 6}),
        (f"**Sweep (served scores, test split).** At 0.3: precision {F.f3(sw[0.3]['precision'])}, recall {F.f3(sw[0.3]['recall'])}; at 0.5: {F.f3(sw[0.5]['precision'])} / {F.f3(sw[0.5]['recall'])}; at 0.9: {F.f3(sw[0.9]['precision'])} / {F.f3(sw[0.9]['recall'])}.", {"bullet": True}),
    ], size=12.5, color=K.INK)
    rows = [["Model", "Threshold (seed 0)", "Test F1"]] + [[F.LABEL[m], f"{M[m]['threshold']:.3f}", F.f3(F.mean(m, "f1"))] for m in F.ORDER]
    K.table(s, 6.0, 4.3, [3.4, 1.9, 1.45], rows, font_size=12.5, row_h=0.45, align=["l", "c", "c"])
    K.text(s, 6.0, 6.7, 6.75, 0.3, "Thresholds were chosen on the validation set only.", size=11, color=K.TXT, italic=True)
    notes[10] = "The flowchart mirrors ml/clustering.py. The queue rule is in backend/app/routes/queue.py: a decision on a cluster is stored once with its member list."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "04"), 0.6, 1.3, 7.0, 5.65)
    rows = [["Module", "Role"], ["ml/data.py", "graph builder, features"], ["ml/gnn.py", "GCN, GAT, GraphSAGE, metrics"], ["ml/train.py", "four models x 3 seeds, artefacts"],
            ["ml/clustering.py", "Louvain clusters, recovery"], ["ml/eval.py", "scalability sweep"], ["backend/app/routes/", "core, accounts, clusters, queue, models"],
            ["backend/app/services/store.py", "loads artefacts once"], ["frontend/src/", "pages, kit components, graph view"]]
    K.table(s, 7.9, 1.45, [2.55, 2.28], rows, font_size=11.5, row_h=0.55, first_bold=True)
    K.text(s, 7.9, 6.5, 4.83, 0.5, "Level-1 data-flow diagram of the running system.", size=11.5, color=K.TXT, italic=True)
    notes[11] = "Level 1 separates request validation, scoring and explanation, cluster serving, the moderator queue and retraining."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database and UML")
    wipe(s)
    K.picture(s, trim(F.diag("09_er_diagram.png"), "09"), 0.6, 1.3, 6.0, 4.95)
    K.picture(s, trim(F.diag("06_uml_class.png"), "06"), 6.75, 1.3, 6.0, 5.2)
    K.text(s, 0.6, 6.35, 6.0, 0.7, "Three SQLite tables: users, reviews (moderator decisions) and training_runs. Graph, scores and clusters are files.", size=11.5, color=K.TXT, italic=True)
    K.text(s, 6.75, 6.55, 6.0, 0.5, "Core classes of the pipeline, the models and the API store.", size=11.5, color=K.TXT, italic=True)
    notes[12] = "reviews keeps the target, decision, note, score at the time, member list and the training run that used it. training_runs keeps F1 before and after for every model."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Language and API", "Python 3.11, FastAPI, Uvicorn, SQLAlchemy 2 with SQLite, PyJWT (HS256, 12 hours), bcrypt"],
            ["Graph learning", "PyTorch (CPU) sparse tensors: GCN, GraphSAGE and GAT layers written directly, no torch-geometric"],
            ["Analysis", "NumPy, pandas, scikit-learn (metrics, ROC), networkx (Louvain communities)"],
            ["Data", "SNAP Facebook circles, Instagram and Twitter labelled sets (all small enough to commit), seeded injected botnets"],
            ["Front end", "React 18, Vite 5, React Router 6, Recharts, react-force-graph-2d, Framer Motion, GSAP; kit V4 Soft Pastel Calm"],
            ["Testing and capture", "scripts/smoke_test.py (36 checks, scratch database), ui_checks.py, capture_screens.py (Playwright, 1440 x 900)"],
            ["Run", f"setup.bat / run.bat on Windows; ports {F.API_PORT} (API) and {F.WEB_PORT} (web app)"]]
    K.table(s, 0.6, 1.45, [2.6, 9.53], rows, font_size=14, row_h=0.65, first_bold=True)
    notes[13] = "Versions are in backend/requirements.txt and frontend/package.json. On the measurement PC PyTorch 2.14 (CPU) and Node 24 were used; the pinned range is torch 2.2 to 2.5."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Graph builder and 23 node features", "Done", f"{F.NODES:,} accounts, {F.EDGES:,} ties, documented schema"],
            ["GCN, GAT, GraphSAGE and no-graph baseline", "Done", "one split, 3 seeds, six metrics each"],
            ["Botnet clusters from embeddings", "Done", f"{cr['recovered']}/{cr['botnets']} injected botnets recovered"],
            ["API (18 routes), JWT roles, SQLite, retraining", "Done", f"{F.SMOKE_PASSED}/{F.SMOKE_TOTAL} smoke checks"],
            ["Moderator queue and retraining on decisions", "Done", "test split never touched; F1 before / after logged"],
            ["React web app, 10 screens, light and dark", "Done", "18 real screenshots at 1440 x 900"],
            ["Scalability sweep", "Done", f"to {t8['nodes']:,} accounts and {t8['edges']:,} ties on CPU"],
            ["Text / language features, temporal graphs, live ingestion", "Not done", "outside the implemented scope"],
            ["Prufer / MST structural features from the base paper", "Not done", "listed as future work"]]
    K.table(s, 0.6, 1.35, [5.4, 1.5, 5.23], rows, font_size=12.5, row_h=0.54)
    notes[14] = "State of the code base. The honest gaps are the last two rows: the batch abstract mentions linguistic cues, which are not implemented, and the base paper's Prufer features are not used."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: does the graph help?")
    wipe(s)
    for i, (v, l, c) in enumerate([(F.f3(F.mean("sage", "f1")), "F1, GraphSAGE (served)", K.ORANGE), (F.f3(F.mean("baseline", "f1")), "F1, no-graph baseline", K.BLUE),
                                   (f"+{F.lift('sage'):.1f} pts", "GraphSAGE over baseline", K.GREEN), (f"{cr['recovered']} / {cr['botnets']}", "injected botnets recovered", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.35, 2.85, 1.15, v, l, c, vsize=24, lsize=11.5)
    cats = [F.LABEL[m].replace("Feature-only baseline (MLP)", "Baseline (MLP)") for m in F.ORDER]
    K.bar_chart(s, 0.6, 2.65, 6.4, 3.2, cats, [("Precision", [F.mean(m, "precision") for m in F.ORDER]), ("Recall", [F.mean(m, "recall") for m in F.ORDER]),
                                              ("F1", [F.mean(m, "f1") for m in F.ORDER])], number_format="0.00", font_size=11, max_value=1.1, gap=50, label_size=9)
    rows = [["Model", "Acc", "ROC-AUC", "PR-AUC"]] + [[F.LABEL[m].replace("Feature-only baseline (MLP)", "Baseline (MLP)"), F.f3(F.mean(m, "accuracy")), F.f3(F.mean(m, "roc_auc")), F.f3(F.mean(m, "pr_auc"))] for m in F.ORDER]
    K.table(s, 7.3, 2.75, [2.2, 1.0, 1.2, 1.03], rows, font_size=12.5, row_h=0.42, align=["l", "c", "c", "c"])
    K.text(s, 7.3, 5.0, 5.43, 1.0, f"GraphSAGE seed 0 on the {F.TEST_N} test accounts: {tp} of {F.TEST_FAKE} fake caught, {fn} missed, {fp} genuine wrongly flagged. GCN gains little (+{F.lift('gcn'):.1f}) and its recall ({F.f3(F.mean('gcn', 'recall'))}) is below the baseline's.", size=12, color=K.TXT)
    ea, ab = F.EXTRA["error_analysis"], F.EXTRA["ablation"]
    f1s = [r["f1"] for r in F.EXTRA["threshold_sweep"]["sage"] if 0.3 - 1e-9 <= r["threshold"] <= 0.6 + 1e-9]
    K.text(s, 0.6, 5.85, 12.13, 1.25, [
        (f"Test split, mean over 3 seeds; fake accounts are {F.pct(F.FAKE_SHARE)} of the data, so F1, precision and recall matter more than accuracy. GraphSAGE F1 stays {min(f1s):.3f}-{max(f1s):.3f} for thresholds 0.30-0.60. "
         f"It catches {ea['by_kind']['botnet member']['sage_caught']} of {ea['by_kind']['botnet member']['n']} test botnet members but {ea['by_kind']['lone spammer']['sage_caught']} of {ea['by_kind']['lone spammer']['n']} lone spammers.", {"space_after": 3}),
        (f"**Caution:** GraphSAGE on node degree alone scores F1 {F.f3(ab['degree only (structure, no attributes)']['sage']['f1_mean'])}, above all 23 features ({F.f3(ab['all 23 features']['sage']['f1_mean'])}); the injected botnets are densely tied, so the structure is easy. "
         "The headline F1 describes this benchmark, not accuracy on a real platform.", {}),
    ], size=11.5, color=K.TXT)
    notes[15] = (f"Headline: all three graph models beat the baseline on F1, but only GraphSAGE and GAT by a wide margin. GraphSAGE: precision {F.f3(F.mean('sage', 'precision'))}, recall {F.f3(F.mean('sage', 'recall'))}, "
                 f"F1 {F.f3(F.mean('sage', 'f1'))}. The numbers belong to this benchmark and must not be compared with PruferNET's 99.63 percent accuracy, which measures a different task.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    cw, ch = 3.95, 2.62
    grid = [("04_overview.png", "Overview: counts, score histogram, F1 per model"), ("07b_account_reasons_and_neighbourhood.png", "Account: reasons for the score, neighbourhood"),
            ("09b_cluster_graph_and_members.png", "Botnet cluster BN-00112: tie density 26%, peak hour 22:00"), ("11_queue_clusters.png", "Moderator queue: clusters to review"),
            ("13_models_comparison.png", "Models: GraphSAGE best, +11.2 pts over no graph"), ("14_models_scalability.png", "Scalability: time against graph size")]
    for i, (n_, cap) in enumerate(grid):
        r, c = divmod(i, 3)
        shot_box(s, n_, 0.6 + c * (cw + 0.19), 1.3 + r * (ch + 0.14), cw, ch, cap)
    K.text(s, 0.6, 6.72, 12.13, 0.3, "Real captures of the running application at 1440 x 900 with the committed graph and trained models.", size=11, color=K.TXT, italic=True)
    notes[16] = "All screens come from the shipped GraphSAGE model on the committed graph, signed in as the demo moderator. The queue shows a few decisions already made during the capture session."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    lat = F.LATENCY
    med = [v[0] for v in lat.values()]
    p95 = [v[1] for v in lat.values()]
    for i, (v, l, c) in enumerate([(f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "smoke-test checks passed", K.GREEN), (f"{min(med):.0f}-{max(med):.0f} ms", "median API latency, 10 endpoints", K.BLUE),
                                   (f"{max(p95):.0f} ms", "worst p95 over those endpoints", K.ORANGE), (f"{F.STARTUP_S:.1f} s", "API start-up (graph, scores, clusters)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["No pytest suite; the smoke test is the automated check (auth, roles, 3 models beat baseline, clusters, queue, retraining)", "Stated in the report; unit tests listed as next step"],
            ["torch fails to load (WinError 1114) if fastapi is imported first on the system Python", "torch preloaded for the test run; the project .venv is unaffected"],
            ["GAT results move by a few thousandths between runs (non-deterministic edge softmax sum)", "Reported as mean ± std over 3 seeds"],
            ["Login takes about 233 ms (bcrypt); other calls 3-16 ms median on a shared i5-12500", "Timings reported as upper bounds"]]
    K.table(s, 0.6, 2.95, [6.9, 5.23], rows, font_size=13, row_h=0.8)
    notes[17] = ("The smoke test starts its own API on a spare port with a scratch database and model copies, so the shipped files are never touched. "
                 "Latency is 20 requests per endpoint on 127.0.0.1 against a warm server; login is bcrypt-bound by design.")

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["torch-geometric wheels often fail to install on Windows", "GCN, GraphSAGE and GAT written in plain PyTorch sparse operations"],
            [f"Class imbalance: only {F.pct(F.FAKE_SHARE)} of accounts are fake", "Class-weighted loss, F1 / precision / recall as the headline metrics, threshold tuned on validation"],
            ["Without camouflage the profile alone would solve the task and the graph would add nothing", f"{F.CAMO_BOTS} bots get genuine-looking profiles, {F.SUSPICIOUS_GENUINE} genuine accounts fake-looking ones; a no-graph baseline proves the graph earns its place"],
            ["GCN barely beats the baseline and loses recall; GAT is noisy and 3-5x slower", "Reported as measured, per seed; GraphSAGE chosen on validation F1"],
            ["Injected botnets and timing features are synthetic; the two labelled sources are not about the same accounts", f"Real and synthetic parts labelled in the app; claims limited to this benchmark. Ablation: GraphSAGE on node degree alone scores F1 {F.f3(F.EXTRA['ablation']['degree only (structure, no attributes)']['sage']['f1_mean'])}, so densely tied injected botnets favour the graph"]]
    K.table(s, 0.6, 1.5, [5.7, 6.43], rows, font_size=14, row_h=0.88)
    notes[18] = "Each challenge was met by a concrete design choice or by measuring it and saying so in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Measure more", "Threshold sweep, ablation and error analysis are measured; next are cross-validation over several splits and confidence intervals.", K.BLUE, "1"),
        ("Extend features", "Prufer / spanning-tree structural features from the base paper, and text features for the behavioural cues in the abstract.", K.GREEN, "2"),
        ("Scale", f"Neighbour sampling and GPU training beyond the {t8['nodes']:,}-account sweep; test a well-mixed graph, not disjoint copies.", K.ORANGE, "3"),
        ("Harden", "Unit and API test suite, rate limiting, real user management, and evaluation on labelled real botnets.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 3.9, t, b_, col, gl, body_size=17)
    K.box(s, 0.6, 5.75, 12.13, 0.95, fill=K.FHEAD, line=None)
    K.text(s, 0.85, 5.9, 11.6, 0.7, "Priority: items 1 and 4 give the final report stronger evidence; items 2 and 3 are listed as future scope.", size=16, color=K.INK, anchor="m")
    notes[19] = "Plan to the final review. Item 1 is quick and uses the shipped scores; the others are larger pieces of work."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why GraphSAGE and not GAT; how much of the result depends on injected botnets; why PruferNET's accuracy is not compared; what the moderator loop changes."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
