"""Chapter 8: Results and output screens. Every number is read from facts.py (experiments/**/metrics.json, experiments/extra/metrics.json)
or from docs/metrics/sample_io.json (API responses and retraining runs captured on 2026-10-26)."""
import json
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, PAIR, TAB

SH = F.shot
X = F.EXTRA


def S(name, caption, base=5.6, max_h=3.7):
    """Screenshot figure with a width that keeps the picture on one page."""
    return FIG(SH(name), caption, F.shot_w(SH(name), base, max_h))


def _io():
    path = os.path.join(F.DOCS, "metrics", "sample_io.json")
    return json.load(open(path, encoding="utf-8"))


def _r(x, d=3):
    return f"{x:.{d}f}"


# ------------------------------------------------------------------ screens (file, caption, description)
SCREENS = {
    "01_landing_light.png": ("Landing page (light theme).",
        "The public landing page. The headline reads *Fake accounts hide alone. Botnets can't hide together.*, followed by one sentence on what the product does and two buttons, *Try the live demo* and *See how it works*. "
        "Three chips name the content (GCN, GAT and GraphSAGE; runs locally; moderator in the loop). The panel on the right is labelled *Schematic illustration*: it is a drawing of a small graph with a cluster of rose-coloured fake accounts, "
        "not real data, and two floating cards beside it carry real counters from the API (8 botnets found by clustering, 4,533 accounts in the graph). The top bar links to the sections, the theme switch, *Sign in* and *Try the demo*."),
    "03_login.png": ("Sign-in page with the demo accounts.",
        "The sign-in page lists the two demo accounts with their roles and the shared password `Demo@1234`. A *Fill* button beside each copies the credentials into the form, and a one-click demo sign-in as the moderator sits under the *Sign in* button. "
        "The cards on the right restate the idea (*Accounts are judged by their company*) and the moderator's role (*You make the call*)."),
    "04_overview.png": ("Overview screen, light theme.",
        "The first screen after sign-in. Five counters read from the running API: 4,533 accounts and 94 thousand ties, 548 accounts flagged as fake (12.1 % of accounts), 8 botnet clusters plus one loose group, "
        "510 items waiting for review (with 8 clusters and 5 decisions made during the capture session), and the F1 of GraphSAGE, 93.9 %, which is 11.2 points above the no-graph model. "
        "Below them, a histogram shows that almost every account scores below 10 % and a small group sits at 90-100 %, and a bar chart compares the test-set F1 of the four models (82.7, 83.7, 90.0 and 93.9 %)."),
    "05_graph_and_features.png": ("Graph and features screen.",
        "The screen that explains how the graph is built. Counters give 4,533 nodes (3,963 real topology, 570 injected), 94,456 undirected ties (88,156 real, 6,300 injected), 570 fake accounts (12.6 %, *a heavily imbalanced set*) and 23 features per account with an average of 41.7 ties. "
        "A blue note states the schema: a node is an account with 23 features and a label used only for training and evaluation, an edge is a tie marked *real* or *injected*, and the split is 2,719 train, 906 validation and 908 test accounts, the same for every model. "
        "The charts below show the real and injected parts and the number of ties per account."),
    "06_accounts.png": ("Ranked accounts screen.",
        "Every account with its fake-probability. The filter bar offers a search box for the handle or name, a status filter, a botnet filter, a sort key and an order switch. The table shows handle and display name, a probability bar, the status badge, the botnet identifier, flagged neighbours out of all neighbours, followers and account age. "
        "The top rows are all members of BN-04235 at 100 %; their badges (*Confirmed fake*, *Dismissed*, *Needs review*) show decisions that had been recorded in the demonstration database before the capture, including a dismissal of an account whose dataset label is fake."),
    "07_account_detail.png": ("Account detail screen, upper half.",
        "The page for @quartzaurora00880118, an account added to the graph as an injected account. A gauge shows 100 % fake probability from GraphSAGE, above the 50 % flag threshold, and a button shows that it is a member of BN-04235 (56 accounts). "
        "*Same account, every model* lists the probability from each model: the no-graph baseline, GCN, GAT and GraphSAGE all score it near 100 %, so this is an easy case in which the graph adds nothing. "
        "The *Moderator decision* panel offers *Confirm fake* and *Dismiss* and shows the current status, *Confirmed fake*."),
    "08_clusters.png": ("Botnet clusters screen.",
        "Louvain communities over the account embeddings. A note explains the two types: a *coordinated* cluster has dense ties between members, a *loose group* is suspicious accounts that merely look similar. "
        "The table lists BN-00055 first as a loose group (160 accounts, average probability 75 %, tie density 0 %, spread over 2.8 years), followed by coordinated clusters from BN-00112 (65 accounts, 96 %, 26 % density, 94 % active around 22:00, created within 17 days) down to BN-04187 (48 accounts, 100 %, 33 %). "
        "Every row is still marked *Needs review*."),
    "09_cluster_detail.png": ("Cluster detail screen for BN-00112.",
        "A sentence summarises the cluster (65 accounts tied to each other, 26 % of possible ties, 94 % most active around 22:00, created within about 17 days of each other). Four tiles give the size (95 % flagged individually), the 544 ties inside it, the shared peak hour 22:00 (94 % within one hour) and 289 distinct outside accounts the members are tied to. "
        "Below are the cluster graph, a *Moderator decision* panel whose decision applies to all 65 members, and a *Shared behaviour* list (average fake probability 96 %, created within 17 days, median account age 8 months). "
        "In this capture the graph is drawn small, as a compact pink knot with a few detached real accounts, because the force layout had not yet spread out."),
    "10_queue_accounts.png": ("Moderator queue, accounts tab.",
        "The working screen for moderators. Four counters show 510 accounts and 8 clusters to review, 4 confirmed and 1 dismissed. Tabs switch between accounts, botnet clusters and the decision log, and a switch shows items that still need review or are already decided. "
        "The table lists flagged accounts from the highest score down. The panel on the right, *Next training run*, states that decisions become training labels and the test split is never touched, reports 38 labelled accounts ready to learn from and carries the *Retrain with decisions* button."),
    "11_queue_clusters.png": ("Moderator queue, botnet clusters tab.",
        "The same screen with the clusters tab selected: each cluster appears with its type, size, average fake probability and tie density, starting with the loose group BN-00055. A decision taken here applies to every member of the cluster and clears them from the account queue."),
    "13_models_comparison.png": ("Models and scale screen, comparison tab.",
        "Four tiles: the best architecture (GraphSAGE, chosen on validation F1 averaged over seeds), its F1 of 93.9 % with a deviation of 0.006 over seeds, the lift of 11.2 points over the no-graph baseline, and 8 of 8 botnets recovered (mean recall 100 %, precision 99 %). "
        "The table beneath compares the four models on the same 908-account test split (mean over three seeds, threshold tuned on the validation set) with accuracy, precision, recall, F1 with its deviation, ROC-AUC, PR-AUC, the F1 difference to the baseline and the training time."),
    "16_overview_dark.png": ("Overview screen, dark theme.",
        "The Overview screen in the dark theme, with the same counters and charts. The theme button at the top right switches between the two themes and the choice is remembered in the browser."),
    # screens placed in Appendix C in the full report (kept here for the stand-alone results document)
    "02_landing_dark.png": ("Landing page (dark theme).",
        "The landing page in the dark theme: the same content, with muted pastel shapes on a dark background."),
    "07b_account_reasons_and_neighbourhood.png": ("Account detail screen, reasons and neighbourhood.",
        "The lower half of the account page. *Why this score* lists the account's own traits that push towards fake (rose bars) in order of contribution: account age (+1.93), share of activity in the peak hour (+1.05), posting burstiness (+0.89), digits in the username (+0.55), interactions per week (+0.26), posts per day (+0.22) and followers (+0.17). "
        "A blue note says the accounts around it add +9.73 to the model margin, that 7 of the top 7 traits push towards fake, and that gradient times input is *an approximation, not a proof*. *Profile and behaviour* shows the raw values (22 followers and 22 following, 5 posts, 33 days old, no profile picture, no bio, 1.5 posts a day, 100 interactions a week, most active at 22:00) "
        "and a green note records that the dataset label (*fake*) is used only for evaluation and never shown to the model at scoring time."),
    "09b_cluster_graph_and_members.png": ("Cluster detail screen, second layout state.",
        "A second capture of the BN-00112 page while the force layout was still moving, showing the cluster as a tight pink group with a few outlying accounts."),
    "12_decision_log.png": ("Moderator queue, decision log tab.",
        "The decision log with a search box and a table of time, target, decision, accounts affected and moderator. The first rows are a *Confirmed fake* decision on cluster BN-04349 that affects 34 accounts and single-account decisions on @thistle4 (confirmed) and @dune.thistle26830652 (dismissed)."),
    "14_models_scalability.png": ("Models and scale screen, scalability tab.",
        "A note explains the sweep: the account graph is copied one to eight times as disjoint components, growing from 4,533 to 36,264 accounts and 94 thousand to 756 thousand ties; training time is averaged over 10 epochs and inference is the median of three forward passes, on CPU. "
        "Two line charts show training time per epoch (up to 2.2 s, GAT highest) and inference time (up to 0.6 s) against graph size."),
    "15_models_retraining.png": ("Models and scale screen, retraining tab before any run.",
        "Before any retraining run the tab shows an empty state (*No retraining runs yet*) that tells the moderator to confirm or dismiss a few accounts and then retrain. A note explains that each run adds the decisions to the training labels and that the test split is never touched, "
        "so the before and after F1 are measured on the same accounts with one training seed each. The results of two such runs are given in Section 8.9."),
}
MAIN = ["01_landing_light.png", "03_login.png", "04_overview.png", "05_graph_and_features.png", "06_accounts.png", "07_account_detail.png",
        "08_clusters.png", "09_cluster_detail.png", "10_queue_accounts.png", "11_queue_clusters.png", "13_models_comparison.png", "16_overview_dark.png"]
MOVED = ["03_login.png", "05_graph_and_features.png", "11_queue_clusters.png", "16_overview_dark.png"]   # shown in Appendix C of the full report
EXTRA_SCREENS = ["02_landing_dark.png", "07b_account_reasons_and_neighbourhood.png", "09b_cluster_graph_and_members.png", "12_decision_log.png",
                 "14_models_scalability.png", "15_models_retraining.png"]


# shorter descriptions used only in the full report (the stand-alone results document keeps SCREENS)
SHORT = {
    "01_landing_light.png": "The landing page: headline, two buttons and a schematic drawing (labelled as such, not real data) with two live counters from the API, 8 botnets found and 4,533 accounts in the graph.",
    "04_overview.png": "Five counters read from the API: 4,533 accounts, 548 flagged (12.1 %), 8 botnet clusters plus one loose group, 510 items waiting for review and GraphSAGE's F1 of 93.9 %, 11.2 points above the no-graph model. "
                       "A histogram shows nearly all accounts below 10 % and a small group at 90-100 %; a bar chart compares the F1 of the four models.",
    "06_accounts.png": "Every account with its fake-probability, filterable by name, status and botnet and sortable by five keys. The top rows are all members of BN-04235 at 100 %; their badges show decisions recorded before the capture, including a dismissal of an account whose dataset label is fake.",
    "07_account_detail.png": "The page for @quartzaurora00880118, an injected account: a 100 % gauge, membership of BN-04235 (56 accounts) and the probability from every model. All four models, including the baseline, score it near 100 %, so the graph adds nothing for this easy case. "
                             "The panel on the right offers *Confirm fake* and *Dismiss*.",
    "08_clusters.png": "Louvain communities over the embeddings. The loose group BN-00055 (160 accounts, tie density 0 %) comes first, followed by coordinated clusters from BN-00112 (65 accounts, 26 % density, 94 % active around 22:00) down to BN-04187 (48 accounts, 33 %); all are marked *Needs review*.",
    "09_cluster_detail.png": "BN-00112 in detail: 65 accounts with 544 ties among them, a shared peak hour of 22:00 and 289 outside accounts tied to them. A decision here applies to all 65 members. The cluster graph is drawn small because the force layout had not yet spread out.",
    "10_queue_accounts.png": "The moderator's working screen: 510 accounts and 8 clusters to review, 4 confirmed and 1 dismissed. The right-hand panel reports 38 labelled accounts ready for the next training run and carries the *Retrain with decisions* button.",
    "13_models_comparison.png": "The comparison tab: GraphSAGE is best (F1 93.9 %, +11.2 points over no graph), 8 of 8 botnets are recovered, and a table gives accuracy, precision, recall, F1, ROC-AUC, PR-AUC and training time for the four models on the same 908-account test split.",
}


def _screens():
    if F.REPORT:
        intro = ("The 18 screenshots in `docs/screenshots/` are real captures of the running application (1440 x 900) with the shipped GraphSAGE model and the committed graph, taken with `scripts/capture_screens.py` on 2026-10-24; "
                 "the decisions visible in the queue screens were made during that session, and accounts shown as *injected* are the seeded synthetic accounts of Section 8.1. The remaining ten screens are in Appendix C.")
    else:
        intro = ("All 18 screenshots in `docs/screenshots/` are real captures of the running application (1440 x 900, Chromium) with the shipped GraphSAGE model and the committed graph; nothing is a mock-up. "
                 "They were captured with `scripts/capture_screens.py` on 2026-10-24 and the decisions visible in the queue screens (four confirmations and one dismissal) were made during that session. "
                 "Accounts shown as *injected* are the seeded synthetic accounts described in Section 8.1; their handles and display names are generated.")
    out = [H2("8.10 Output screens"), P(intro)]
    main = [m for m in MAIN if m not in MOVED] if F.REPORT else MAIN
    for k, name in enumerate(main + ([] if F.REPORT else [e for e in EXTRA_SCREENS]), 1):
        cap, text = SCREENS[name]
        if F.REPORT:
            text = SHORT[name]
        out.append(H3(f"8.10.{k} {cap.rstrip('.')}"))
        out.append(P(text))
        out.append(S(name, cap, 5.0, 3.0 if F.REPORT else 3.9))
    return out


# ------------------------------------------------------------------ sections
def _setup():
    return [
        H2("8.1 Experimental set-up"),
        P(f"Every number in this chapter comes from files written by the project's own scripts: `experiments/metrics.json` (the three-seed comparison, written by `ml/train.py`), `experiments/scalability.json` and `experiments/eval/metrics.json` (`ml/eval.py`), "
          f"`experiments/extra/metrics.json` (`scripts/run_extra_experiments.py`: threshold sweep, error analysis, feature-group ablation) and, for the API samples and retraining runs, responses captured from a scratch copy of the application on 2026-10-26. No result was typed in by hand. "
          f"The measurements were made on one machine: {F.HARDWARE}, Python 3.11.9 and PyTorch 2.14.1 (CPU build). The machine was shared with other programs, so timings are indicative; accuracy figures do not depend on load."),
        TAB("Data used in the evaluation", ["Item", "Content", "Status"],
            [["Topology", f"{F.REAL_NODES:,} accounts and {F.REAL_EDGES:,} ties from ten SNAP Facebook ego networks", "Real public data"],
             ["Profile attributes", "696 labelled Instagram rows, resampled and jittered onto every account", "Real rows, resampled"],
             ["Posting behaviour", "50,000 labelled Twitter rows; retweets, mentions, post length, hashtags", "Real rows; the label carries almost no signal"],
             ["Injected botnets", f"8 botnets of sizes {', '.join(str(s) for s in F.BOTNET_SIZES)} (420 accounts) and {F.LONE_SPAMMERS} lone spammers; {F.INJ_EDGES:,} injected ties", "Synthetic, seeded (seed 7)"],
             ["Timing and interaction features, handles", "Posting rate, burstiness, peak hour, interactions per week, names", "Synthetic, seeded"],
             ["Camouflage", f"{F.CAMO_BOTS} bots given a genuine-looking profile; {F.SUSPICIOUS_GENUINE} genuine accounts given a fake-looking one", "Synthetic, by design"],
             ["Final graph", f"{F.NODES:,} accounts, {F.EDGES:,} ties, {F.FAKE} fake ({F.pct(F.FAKE_SHARE)})", "Stratified split 60/20/20: 2,719 / 906 / 908"]],
            widths=[1.5, 3.4, 1.6], align=["l", "l", "l"], size=9.5),
        P(f"The test split holds {F.TEST_N} accounts, {F.TEST_FAKE} of them fake. Because only 12.6 % of accounts are fake, a classifier that answers *genuine* for everybody would score 87.4 % accuracy, so the headline measure in this chapter is **F1** (with precision and recall), not accuracy. "
          "All four models use the same 23 features, the same split and the same training budget (two layers, 64 hidden units, dropout 0.3, Adam with learning rate 0.01, up to 160 epochs with early stopping on validation F1, class-weighted loss); the decision threshold is tuned on the validation set. "
          "Each model was trained with seeds 0, 1 and 2 and the tables give the mean and the standard deviation over the three seeds. Three seeds is a small sample, so deviations are indicative only."),
    ]


def _models():
    rows = []
    for m in F.ORDER:
        rows.append([F.LABEL[m] + (" (served)" if m == F.BEST else ""), F.mstd(m, "accuracy", 3), _r(F.mean(m, "precision")), _r(F.mean(m, "recall")), F.mstd(m, "f1", 3),
                     _r(F.mean(m, "roc_auc")), _r(F.mean(m, "pr_auc")), f"{MODEL_TRAIN[m]:.1f}"])
    seed_rows = []
    for m in F.ORDER:
        ps = F.MODELS[m]["per_seed"]
        seed_rows.append([F.LABEL[m]] + [f"{p['f1']:.3f} (thr {p['threshold']:.3f})" for p in ps])
    cm_rows = []
    for m in F.ORDER:
        tn, fp, fn, tp = F.conf(m)
        cm_rows.append([F.LABEL[m], str(tp), str(fn), str(fp), str(tn), f"{F.MODELS[m]['threshold']:.3f}"])
    gain = {m: F.lift(m) for m in ("gcn", "gat", "sage")}
    return [
        H2("8.2 Model performance"),
        P(f"The first table below compares the four models on the held-out test split. GraphSAGE has the best value on every column: F1 {F.mstd('sage', 'f1')}, precision {_r(F.mean('sage', 'precision'))}, recall {_r(F.mean('sage', 'recall'))} and ROC-AUC {_r(F.mean('sage', 'roc_auc'))}. "
          f"It was also chosen as the served model by the project's own rule, the best mean validation F1 among the three graph models ({_r(F.MODELS['sage']['val_f1'])}, against {_r(F.MODELS['gat']['val_f1'])} for GAT and {_r(F.MODELS['gcn']['val_f1'])} for GCN)."),
        TAB("Test-split results, mean ± standard deviation over three seeds (908 accounts, 114 fake)", ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC", "Train s"], rows,
            widths=[1.9, 1.1, 0.7, 0.7, 1.1, 0.7, 0.7, 0.6], align=["l", "c", "c", "c", "c", "c", "c", "c"], size=9),
        FIG(F.fig("f01_model_comparison.png"), "Precision, recall and F1 of the four models on the test split (mean over three seeds).", 5.6),
        P(f"The graph helps, but by very different amounts. Over the feature-only baseline (F1 {_r(F.mean('baseline', 'f1'))}), GCN gains {gain['gcn']:.1f} point, GAT {gain['gat']:.1f} points and GraphSAGE {gain['sage']:.1f} points. "
          f"GCN's small gain is a trade: its precision rises to {_r(F.mean('gcn', 'precision'))} but its recall ({_r(F.mean('gcn', 'recall'))}) is *lower* than the baseline's ({_r(F.mean('baseline', 'recall'))}), so it finds fewer fake accounts than a model that ignores the graph. "
          "A plausible reason, which these experiments do not prove, is that GCN's symmetric normalisation averages an account with its neighbours, so a fake account with a few genuine neighbours is pulled towards them, whereas GraphSAGE keeps the account's own features in a separate weight from the neighbourhood mean. "
          "GAT is in between and is the least stable: its F1 over the three seeds is 0.901, 0.877 and 0.922."),
        FIG(F.fig("f11_graph_lift.png"), "F1 gained over the feature-only baseline by each graph architecture, in F1 points.", 4.6),
        H3("8.2.1 Seed variation"),
        TAB("F1 by training seed (with the validation-tuned threshold)", ["Model", "Seed 0", "Seed 1", "Seed 2"], seed_rows, widths=[2.0, 1.5, 1.5, 1.5], align=["l", "c", "c", "c"], size=9.5),
        P("GraphSAGE's three values lie within 0.015 of each other and every one is above every value of GAT, GCN and the baseline, so its ranking does not depend on the seed. GAT's spread is large enough that its best seed (0.922) nearly reaches GraphSAGE's worst (0.931). "
          "GAT's edge softmax sums in a non-deterministic order, so re-running it can move its F1 by about 0.01."),
        FIG(F.fig("f04_seed_variance.png"), "F1 of every model for each of the three training seeds.", 5.0),
        H3("8.2.2 Confusion matrices and ROC curves"),
        P("The stored confusion matrices belong to the first seed. GraphSAGE misses 9 of the 114 fake accounts and wrongly flags 3 of 794 genuine accounts; the baseline misses 24 and wrongly flags 12."),
        TAB("Confusion counts on the 908-account test split (seed 0)", ["Model", "TP", "FN", "FP", "TN", "Threshold"], cm_rows, widths=[2.4, 0.7, 0.7, 0.7, 0.7, 1.0], align=["l", "c", "c", "c", "c", "c"], size=9.5),
        FIG(F.fig("f03_confusion_matrices.png"), "Confusion matrices of the four models on the test split (seed 0).", 5.8),
        FIG(F.fig("f02_roc_curves.png"), "ROC curves of the four models on the test split (seed 0).", 4.8),
        P("The ROC-AUC values are all high (0.967 to 0.990) because the classes are easy to rank; the PR-AUC column of the table above separates the models better (0.907 for the baseline, 0.974 for GraphSAGE) because it reflects the minority class."),
    ]


MODEL_TRAIN = {m: F.MODELS[m]["train_seconds"] for m in F.ORDER}


def _threshold():
    rows = []
    for r in X["threshold_sweep"]["sage"]:
        if round(r["threshold"] * 100) % 10 == 0 and 0.2 <= r["threshold"] <= 0.9:
            rows.append([f"{r['threshold']:.2f}", _r(r["precision"]), _r(r["recall"]), _r(r["f1"]), str(r["fp"]), str(r["fn"])])
    bsw = X["threshold_sweep"]["baseline"]
    best_b = max(bsw, key=lambda r: r["f1"])
    return [
        H2("8.3 Threshold analysis"),
        P("An account is flagged when its fake-probability reaches the threshold. The served model uses 0.5, which the validation set chose. To see how much the result depends on that choice, the stored GraphSAGE scores (seed 0) were swept over thresholds on the test split."),
        TAB("Served GraphSAGE at different thresholds (test split, seed 0)", ["Threshold", "Precision", "Recall", "F1", "False positives", "False negatives"], rows,
            widths=[1.0, 1.0, 1.0, 0.8, 1.3, 1.4], align=["c"] * 6, size=10),
        FIG(F.fig("f07_threshold_sweep.png"), "Precision, recall and F1 of the served GraphSAGE model against the decision threshold (test split, seed 0).", 5.2),
        P("F1 stays between 0.927 and 0.952 for every threshold from 0.30 to 0.60, so the result does not hinge on the tuned threshold. Raising the threshold buys precision at the cost of recall: at 0.90 only one genuine account is flagged but 23 of the 114 fake accounts are missed. "
          "Lowering it does the opposite: at 0.20, 21 genuine accounts are flagged and 5 fake accounts are missed. The peak of the sweep (F1 0.952 at 0.40) is measured on the test split itself, so it is shown for analysis only; the served threshold was fixed on validation data. "
          f"The baseline's best F1 over the same sweep is {best_b['f1']:.3f} (threshold {best_b['threshold']:.2f}); to reach a recall above 0.9 it has to accept a precision below 0.62, whereas GraphSAGE keeps a precision of 0.87 at a recall of 0.947. "
          "For a moderation team this is the useful reading: the graph model lets a team choose how many false alarms to accept without losing much recall."),
    ]


def _ablation():
    a = X["ablation"]
    rows = []
    for k, v in a.items():
        rows.append([k, str(v["n_features"]), f"{v['baseline']['f1_mean']:.3f} ± {v['baseline']['f1_std']:.3f}", f"{v['sage']['f1_mean']:.3f} ± {v['sage']['f1_std']:.3f}",
                     f"{v['sage']['precision_mean']:.3f} / {v['sage']['recall_mean']:.3f}"])
    return [
        H2("8.4 Which features matter: an ablation"),
        P("To find out where the performance comes from, the baseline and GraphSAGE were retrained with groups of features removed, three seeds each, in memory and without touching the shipped models. "
          "The row *all 23 features* (baseline 0.822, GraphSAGE 0.942) differs slightly from the main table (0.827 and 0.939) because it is a separate run with its own seeds' random draws."),
        TAB("Test F1 with feature groups removed (mean ± standard deviation over three seeds)", ["Variant", "Features", "Baseline MLP", "GraphSAGE", "GraphSAGE precision / recall"], rows,
            widths=[2.3, 0.7, 1.2, 1.2, 1.3], align=["l", "c", "c", "c", "c"], size=9),
        FIG(F.fig("f08_ablation.png"), "Test F1 of the baseline and GraphSAGE when feature groups are removed (three seeds).", 5.6),
        N("**The temporal group matters most.** Removing the temporal features (account age, posts per day, burstiness, peak-hour share and its sine and cosine) drops the baseline from 0.822 to 0.515 and GraphSAGE from 0.942 to 0.840. These features are synthetic: botnet members share a creation window and a peak hour by construction, so this is the place where the benchmark is most generous.",
          "**Posting behaviour adds nothing.** GraphSAGE scores 0.946 without it, which fits the finding that the Twitter bot label carries almost no signal.",
          "**The neighbourhood supplies what the profile lacks.** On the 12 profile features alone the baseline reaches only 0.512 while GraphSAGE reaches 0.831.",
          "**One structural feature is enough here.** GraphSAGE given nothing but the logarithm of each account's number of ties scores F1 0.965 (precision 0.962, recall 0.968), *above* the model with all 23 features (0.942). The no-graph model on the same single feature scores 0.338: an account's own degree is not enough, but its neighbours' degrees separate the classes."),
        P("The last finding changes how the headline result must be read. In this benchmark the injected botnets and lone spammers have a distinctive local degree pattern (dense ties inside a botnet, two to ten ties to real accounts), so message passing over degrees alone nearly solves the task. "
          "The benchmark therefore rewards structure more than a real platform would, and the graph lift of 11.2 F1 points is real for this data but partly produced by how the botnets were injected. **The F1 of 0.939 must not be read as accuracy on a real platform.** "
          "Showing this was the purpose of the ablation: a result that looks excellent should be asked what it depends on."),
    ]


def _clusters():
    rows = []
    for p in F.REC["per_botnet"]:
        rows.append([f"Botnet {p['botnet'] + 1}", str(p["size"]), f"cluster {p['matched_cluster']}", _r(p["recall"]), _r(p["precision"]), "yes" if p["recovered"] else "no"])
    return [
        H2("8.5 Botnet cluster detection"),
        P("The embeddings of every account scored at 0.30 or more were linked to their five most similar neighbours and to their real ties, and Louvain community detection was run on that graph. Groups under five accounts were dropped. "
          f"Nine groups remained: eight coordinated clusters and one loose group of 160 accounts. A botnet counts as *recovered* when one cluster contains at least 80 % of its accounts and at least 80 % of that cluster's accounts belong to it."),
        TAB("Recovery of the eight injected botnets", ["Botnet", "Accounts", "Matched cluster", "Recall", "Precision", "Recovered"], rows,
            widths=[1.1, 0.9, 1.3, 0.9, 0.9, 1.0], align=["l", "c", "c", "c", "c", "c"], size=10),
        FIG(F.fig("f06_cluster_recovery.png"), "Recall and precision of the cluster that best matches each injected botnet.", 5.2),
        P(f"All eight botnets are recovered as single communities: the mean recall is {_r(F.REC['mean_recall'])} and the mean precision {_r(F.REC['mean_precision'])}; the lowest precision is {_r(min(p['precision'] for p in F.REC['per_botnet']))} (botnet 4, whose cluster also contains five accounts that are not part of it). "
          f"The fake purity of all clustered accounts is {_r(F.REC['fake_purity'])}, which is lower than the botnet precision because the loose group of 160 accounts holds lone spammers together with look-alike genuine accounts: it has a tie density of 0.14 % and only 18 internal ties, "
          "and the application labels it *loose group* instead of *coordinated* because its density is below 5 %. That label is what separates a coordinated network from independent accounts that merely look alike."),
        P("This is a known-answer test. The botnets were injected with a tie probability of 0.28 between members, a shared creation window and a shared posting hour, so they are easy to find by construction. "
          "The result shows that the method recovers this kind of coordination; it says nothing about the recall of real botnets that hide their ties."),
        FIG(F.fig("f09_score_distribution.png"), "Distribution of GraphSAGE fake-probabilities for genuine and fake accounts.", 5.0),
    ]


def _scale():
    r1, r8 = F.scal_row(1)["models"], F.scal_row(8)["models"]
    return [
        H2("8.6 Scalability and response time"),
        P(f"The sweep of Section 7.7 grows the graph from {F.NODES:,} accounts and {F.EDGES:,} ties to {F.scal_row(8)['nodes']:,} accounts and {F.scal_row(8)['edges']:,} ties. A GraphSAGE epoch takes {r1['sage']['train_seconds_per_epoch']:.3f} s on the smallest graph and {r8['sage']['train_seconds_per_epoch']:.3f} s on the largest, "
          f"GCN {r1['gcn']['train_seconds_per_epoch']:.3f} s and {r8['gcn']['train_seconds_per_epoch']:.3f} s, GAT {r1['gat']['train_seconds_per_epoch']:.3f} s and {r8['gat']['train_seconds_per_epoch']:.3f} s; one forward pass over the whole graph takes {r8['sage']['inference_seconds']:.3f} s for GraphSAGE and {r8['gat']['inference_seconds']:.3f} s for GAT at the largest size. "
          "Cost grows roughly in proportion to the number of ties, and GAT is the most expensive. GraphSAGE is both the most accurate and, among the graph models, the cheapest, so on this benchmark there is no accuracy-for-speed trade-off to make."),
        FIG(F.fig("f05_scalability.png"), "Training time per epoch and inference time against graph size, CPU, for the four models.", 5.6),
        P(f"The API answers its read endpoints in 3 to 16 ms (median) and no 95th percentile exceeds 29 ms; sign-in takes about {F.LOGIN_MS} ms because of bcrypt, and the API needs {F.STARTUP_S} s to load the artefacts at start-up. "
          "The limits of these figures (a 36 thousand-account graph, disjoint copies, one machine) are stated in Section 7.7."),
    ]


def _base_paper():
    bp = F.BASE_PAPER_RESULTS
    return [
        H2("8.7 Comparison with the base paper"),
        P(f"The base paper [1] proposes PruferNET: Prufer-sequence features from a minimum spanning tree, added to classical centralities and fed to a GraphSAGE model that classifies each node by its depth in the tree. "
          "Its task is to find *influential* nodes, not fake ones, and its data carry no fake-account labels. The two works share a family of data (SNAP Facebook networks), a model family (GraphSAGE) and the idea that structure adds information a per-node model lacks, but they do not measure the same thing. "
          "**Their numbers cannot be compared like for like, and no ranking is claimed.**"),
        TAB("What each work reports", ["Aspect", "PruferNET (base paper)", "BotGraph (this project)"],
            [["Task", bp["task"], "Binary fake-account detection plus botnet cluster detection"],
             ["Labels", "Depth classes computed from the graph itself", "Dataset labels: genuine / fake (12.6 % fake); partly synthetic"],
             ["Data", bp["data"], f"{F.NODES:,} nodes, {F.EDGES:,} ties: SNAP Facebook topology ({F.REAL_NODES:,} nodes) plus injected accounts, real profile rows, synthetic timing features"],
             ["Model", bp["model"], "GCN, GAT and GraphSAGE, 2 layers, 64 hidden units, dropout 0.3, Adam 0.01, up to 160 epochs, plus an MLP baseline"],
             ["Features", "Prufer-sequence statistics, degree, closeness, PageRank, trust score", "23 attributes: profile, posting, temporal, interaction; no Prufer or centrality features"],
             ["Split", bp["split"], "Stratified 60/20/20 (2,719 / 906 / 908)"],
             ["Headline result", f"Test accuracy {F.pct(bp['with_prufer_acc'], 2)} with Prufer features, {F.pct(bp['without_prufer_acc'], 2)} without", f"GraphSAGE F1 {F.mstd('sage', 'f1')} (accuracy {F.pct(F.mean('sage', 'accuracy'))}); baseline F1 {_r(F.mean('baseline', 'f1'))}"],
             ["Hardware", bp["hardware"], "CPU only (i5-12500, 16 GB)"],
             ["Clusters, scalability, review loop", "None reported", "Louvain botnet clusters (8 of 8 recovered), scalability to 36 k accounts, moderator queue with retraining"]],
            widths=[1.2, 2.6, 2.7], align=["l", "l", "l"], size=9),
        P("Three points of reading follow. First, accuracy is not the right yardstick for BotGraph, because 87.4 % of accounts are genuine; the accuracy of 98.5 % corresponds to an F1 of 0.939. "
          "Second, PruferNET's classes are defined by the same graph from which its features are computed, which makes high scores likely, and its own caveat that the paper is not about a new network architecture applies equally here: BotGraph's contribution is the application, not a new layer. "
          "Third, the Prufer features were not used in BotGraph and testing whether they help bot detection is listed as future work. The companion works in the batch survey (RABot and HW-GNN) address imbalance, noisy ties and homophily in bot detection; they were used to frame the problem and were not reproduced, so no number from them is quoted."),
    ]


def _sample_io():
    io = _io()
    d = io["account_detail"]
    ex = d["explanation"]
    detail = {
        "id": d["id"], "handle": d["handle"], "score": round(d["score"], 4), "flagged": d["flagged"], "status": d["status"], "model": d["model"],
        "model_scores": {m["model"]: round(m["score"], 4) for m in d["model_scores"]},
        "cluster_id": d["cluster_id"], "cluster_size": d["cluster_size"],
        "explanation": {"margin": round(ex["margin"], 2), "own_total": round(ex["own_total"], 2), "network": round(ex["network"], 2),
                        "top": [{"feature": t["feature"], "value": round(t["value"], 3), "contribution": round(t["contribution"], 2)} for t in ex["top"][:3]]},
        "neighbourhood": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in d["neighbourhood"].items()},
    }
    first = io["accounts_page"]["items"][0]
    return [
        H2("8.11 Sample inputs and outputs"),
        P("The excerpts below are real responses of the API, captured on 2026-10-26 from a scratch copy of the application (long lists shortened with `...`). They show the shape of the data behind the screens."),
        H3("8.11.1 Sign-in and access control"),
        CODE("POST /api/auth/login   {\"email\": \"moderator@botgraph.app\", \"password\": \"x\"}\n"
             f"-> {io['login_wrong'][0]}  {json.dumps(io['login_wrong'][1])}\n\n"
             "GET /api/overview   (no token)\n"
             f"-> {io['anon_overview'][0]}  {json.dumps(io['anon_overview'][1])}\n\n"
             "POST /api/queue/decisions   (analyst token)\n"
             f"-> {io['analyst_decision'][0]}  {json.dumps(io['analyst_decision'][1])}", 8),
        H3("8.11.2 One ranked account and its explanation"),
        CODE("GET /api/accounts?page_size=3   -> first item\n" + json.dumps(first) + "\n\nGET /api/accounts/4286   (trimmed)\n" + json.dumps(detail, indent=1), 7.5),
        P("The three model scores in `model_scores` show that for this account every model, including the one that ignores the graph, is certain. The `explanation` says that the account's own traits contribute +5.38 to the fake-versus-genuine margin of 16.99 and that the other accounts' features, reached by message passing, contribute +9.73."),
        H3("8.11.3 A botnet cluster"),
        CODE("GET /api/clusters/BN-00112   -> headline\n" + json.dumps(io["cluster_headline"]) + "\n\nGET /api/clusters   -> second item\n" + json.dumps(io["cluster_first"]), 8),
        H3("8.11.4 A decision and an error"),
        CODE("POST /api/queue/decisions   {\"target_type\": \"account\", \"target_id\": \"4286\", \"decision\": \"confirm\", \"note\": \"sample\"}\n"
             f"-> {io['decision'][0]}  {json.dumps(io['decision'][1])}\n\n"
             "GET /api/accounts/99999999\n"
             f"-> {io['unknown_account'][0]}  {json.dumps(io['unknown_account'][1])}", 8),
    ]


def _retrain():
    io = _io()
    out = [H2("8.9 Learning from moderator decisions"),
           P("Two retraining runs were made from a scratch copy of the application with the shipped data, to see what the feedback loop does. Each run trains all four models with one seed on the original training labels plus the labels given by the decisions, and the F1 is measured before and after on the same 908 test accounts (decisions on test accounts are ignored). "
             "The before value is the first seed of the main run, so the two columns use the same seed.")]
    rows = []
    for key, title in (("retrain_correct", "A. Correct decisions"), ("retrain_wrong", "B. Includes two deliberate errors")):
        s = io[key]
        run = s["run"]
        for m in F.ORDER:
            rows.append([title if m == "baseline" else "", F.LABEL[m], _r(run["f1_before"][m]), _r(run["f1_after"][m]), f"{(run['f1_after'][m] - run['f1_before'][m]) * 100:+.1f}"])
    out.append(TAB("F1 on the test split before and after retraining on moderator decisions (one seed)", ["Scenario", "Model", "F1 before", "F1 after", "Change (points)"], rows,
                   widths=[1.8, 1.9, 0.9, 0.9, 1.0], align=["l", "l", "c", "c", "c"], size=9.5))
    for key, lab in (("retrain_correct", "A"), ("retrain_wrong", "B")):
        s = io[key]
        out.append(P(f"**Scenario {lab}.** {s['description']} {s['run']['feedback_labels']} accounts received a label; {s['run']['message'].split(' moderator')[0]} of them were outside the test split and were used. "
                     f"The run took {s['seconds']:.0f} s. Afterwards the application flagged {s['health_after']['flagged']} accounts (548 before) and showed {s['health_after']['botnets']} botnets (8 before)."))
    out.append(P(io["retrain_reading"]))
    return out


def _success_failure():
    ea = X["error_analysis"]
    bk = ea["by_kind"]
    return [
        H2("8.12 Success and failure analysis"),
        H3("8.12.1 Where the system succeeds"),
        B(f"**Coordinated accounts.** All {bk['botnet member']['n']} botnet members in the test split are caught by GraphSAGE; the feature-only baseline catches {bk['botnet member']['baseline_caught']}. The graph rescues {ea['rescued_by_graph']} fake accounts the baseline misses (a net gain of {bk['botnet member']['sage_caught'] - bk['botnet member']['baseline_caught']} botnet members), typically accounts with a camouflaged profile whose neighbours are not camouflaged.",
          "**Few false alarms.** At the served threshold 3 of 794 genuine accounts are flagged (0.4 %); all three are accounts of the real topology, with 4, 10 and 41 ties.",
          "**Stable ranking.** GraphSAGE leads on every metric and every seed (Section 8.2.1) and its F1 stays between 0.927 and 0.952 for any threshold from 0.30 to 0.60.",
          "**Cluster recovery.** Eight of eight injected botnets come back as single communities, and the density rule separates them from the loose group.",
          "**Cost.** A full pass over 36 thousand accounts and 756 thousand ties takes under 0.6 s on a laptop-class CPU, and the application answers requests in tens of milliseconds."),
        H3("8.12.2 Where it fails"),
        B(f"**Lone spammers.** Of {bk['lone spammer']['n']} lone spammers in the test split GraphSAGE catches {bk['lone spammer']['sage_caught']}, and the baseline {bk['lone spammer']['baseline_caught']}: for accounts with no coordinated neighbourhood the graph does not help, and it loses {ea['lost_by_graph']} accounts the baseline caught. "
          f"All 9 missed fake accounts are lone spammers with only 4 to 8 ties (median {ea['degree_fake_missed_median']:.0f}, against {ea['degree_fake_caught_median']:.0f} for caught fake accounts); their scores range from 0.02 to 0.50. {ea['missed_by_both']} fake accounts are missed by both models.",
          "**GCN loses recall** below the no-graph baseline (0.743 against 0.789), so a graph model is not automatically a better detector.",
          "**Moderator mistakes spread.** In the retraining experiment (Section 8.9), a wrong dismissal of a cluster relabelled every member as genuine and lowered the F1 of three of four models. The queue offers no second opinion or confidence check on a decision.",
          "**The loose group needs a person.** The 160-account group has no internal structure; it is flagged because its members individually look suspicious, and the system cannot say whether they are related.",
          "**Easy cases look the same as hard cases on screen.** The account shown on the account detail screen is scored 100 % by every model, including the baseline; the interface does not tell the moderator whether the graph contributed anything to a given score."),
        FIG(F.fig("f12_error_analysis.png"), "Test fake accounts caught and missed by GraphSAGE and by the baseline, by kind (botnet member, lone spammer).", 5.2),
        FIG(F.fig("f13_feature_means.png"), "Mean value of each feature for genuine and fake accounts (standardised).", 5.4),
        FIG(F.fig("f14_degree_distribution.png"), "Number of ties per account for genuine and fake accounts.", 5.0),
    ]


def _limits():
    return [
        H2("8.13 Limitations of the results"),
        B("**The data are partly synthetic.** The eight botnets, the 150 lone spammers, the timing and interaction features and the handles are generated, and the profile and posting rows come from different people. The results describe this benchmark, not Indian platforms such as ShareChat or Moj.",
          "**Structure alone nearly solves the benchmark** (Section 8.4): GraphSAGE on log degree alone scores F1 0.965. The graph lift is partly an effect of how the botnets were injected.",
          "**One split and three seeds.** There is no cross-validation, no second dataset and no significance test; the deviations are over three seeds only. The confusion matrices and the threshold sweep use the first seed.",
          "**No real botnets and no adversary.** Recovery is measured against seeded botnets that do not try to hide their ties, and no attack on the model was tried.",
          "**No text features.** The abstract mentions linguistic cues; the 23 features contain none.",
          "**The explanation is approximate.** Reasons are gradient times input of one forward pass, which is a first-order approximation, as the screen itself says.",
          "**Scale was measured on disjoint copies** of a 4.5 thousand-account graph, up to 36 thousand accounts, on one CPU.",
          "**The retraining experiment has two runs, one seed each**, so its before-and-after differences are not statistically supported."),
    ]


def _objectives():
    return [
        H2("8.14 Objectives against outcomes"),
        TAB("The six objectives of the project and what was measured", ["#", "Objective", "Outcome", "Evidence"],
            [["1", "Construct a graph of accounts (nodes) and interactions (edges)", "**Met.** 4,533 nodes, 94,456 undirected ties, documented schema; 88,156 real and 6,300 injected ties", "Graph & features screen; Section 8.1"],
             ["2", "Engineer node features: profile, posting behaviour, interaction frequency", "**Met.** 23 features in four groups; no text features", "Graph & features screen; ablation, Section 8.4"],
             ["3", "Implement and compare GCN, GAT and GraphSAGE", "**Met.** Same split, features and budget, three seeds, plus a no-graph baseline; GraphSAGE best (F1 0.939), GCN +1.0, GAT +7.3, GraphSAGE +11.2 points", "Sections 8.2-8.4"],
             ["4", "Detect coordinated botnet clusters from learned embeddings", "**Met on injected botnets.** 8 of 8 recovered, mean recall 1.000, precision 0.988; real-world botnets not tested", "Section 8.5"],
             ["5", "Evaluate accuracy, precision and recall against labelled data", "**Met.** Six metrics, ROC, confusion matrices, threshold sweep; labels are partly synthetic", "Sections 8.2-8.3"],
             ["6", "Assess scalability as nodes and edges grow", "**Met to 36 k accounts / 756 k ties** on CPU, roughly linear in ties; platform scale untested", "Section 8.6; Chapter 7.7"]],
            widths=[0.3, 2.0, 2.9, 1.3], align=["c", "l", "l", "l"], size=9),
        P("Beyond the six objectives the project added a moderator queue with a retraining loop, explanations for every score and an API with role-based access. Where an objective is marked as met, the margin of the claim is given in the evidence column and in Section 8.13."),
    ]


def _trim(blocks):
    """Full report only: drop or shorten text that restates a table (the stand-alone results document keeps everything)."""
    out, skip_next = [], False
    for b in blocks:
        if skip_next:
            skip_next = False
            continue
        k = b[0]
        if k == "p" and b[1].startswith("The ROC-AUC values are all high"):
            continue
        if k == "h3" and b[1].startswith("8.11.3 A botnet cluster"):
            skip_next = True
            continue
        if k == "h3" and b[1].startswith("8.11.4"):
            b = ("h3", "8.11.3 A decision and an error")
        if k == "p" and b[1].startswith("The three model scores in"):
            b = ("p", "Every model, including the one that ignores the graph, scores this account near 1. The explanation attributes +5.38 of the margin of 16.99 to the account's own traits and +9.73 to its neighbours through message passing.")
        if k == "p" and b[1].startswith("The API answers its read endpoints"):
            b = ("p", f"The API answers read requests in 3 to 16 ms (median; 95th percentile at most 29 ms), sign-in takes about {F.LOGIN_MS} ms because of bcrypt and start-up takes {F.STARTUP_S} s; the limits of these figures are in Section 7.7.")
        if k == "p" and b[1].startswith("Two retraining runs were made"):
            b = ("p", "Two retraining runs were made on a scratch copy of the application. Each trains all four models with one seed on the original labels plus the labels from the decisions, and F1 is measured before and after on the same 908 test accounts "
                      "(decisions on test accounts are ignored; the before value is the first seed of the main run).")
        if k == "p" and b[1].startswith("In scenario A every decision agrees"):
            b = ("p", "In scenario A every decision agrees with the dataset labels. Confirming botnets the model already scores near 100 % adds little, so F1 barely moves for the baseline (+0.2) and GraphSAGE (+0.1) and falls for GCN (-2.1) and GAT (-0.9), changes of the size of the seed-to-seed variation; "
                      "the run shows that the loop works, not that it improves the model. It also exposed a defect: the application then served GAT instead of GraphSAGE, because the best architecture is picked on the validation F1 of one seed after the reviewed accounts have left the validation set, "
                      "although GraphSAGE has the higher test F1 after the run (0.947 against 0.892). "
                      "In scenario B the two errors cost F1 for every model (GCN -8.2 points, GraphSAGE -4.1, GAT -1.5, baseline -0.3), the botnets shown fell from 8 to 7 because the 62 accounts of the wrongly dismissed botnet were relabelled genuine, and 534 accounts remained flagged instead of 548. "
                      "The loop learns whatever it is told, so moderator errors are costly; two runs with one seed each support no statistical statement.")
        if k == "b" and any(x.startswith("**Stable ranking.**") for x in b[1]):
            b = ("b", [x for x in b[1] if not x.startswith("**Stable ranking.**") and not x.startswith("**Cost.**")])
        out.append(b)
    return out


def blocks():
    out = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS"),
           P("This chapter reports what BotGraph achieved: the comparison of the models, what the result depends on, the botnet clusters, scalability, a comparison with the base paper, every output screen, sample API responses, the effect of moderator decisions on retraining, "
             "where the system succeeds and fails, and the objectives measured against the outcomes. Where a number looks better than it should, the chapter says what it rests on.")]
    out += _setup() + _models() + _threshold() + _ablation() + _clusters() + _scale() + _base_paper()
    out += [H2("8.8 Summary of the numbers"),
            TAB("Headline numbers", ["Measure", "Value"],
                [["Served model", "GraphSAGE"],
                 ["Test F1 (mean ± std, 3 seeds)", F.mstd("sage", "f1")],
                 ["Test precision / recall", f"{_r(F.mean('sage', 'precision'))} / {_r(F.mean('sage', 'recall'))}"],
                 ["Test ROC-AUC / PR-AUC", f"{_r(F.mean('sage', 'roc_auc'))} / {_r(F.mean('sage', 'pr_auc'))}"],
                 ["Lift over the no-graph baseline", f"+{F.lift('sage'):.1f} F1 points (baseline {_r(F.mean('baseline', 'f1'))})"],
                 ["Confusion (seed 0, 908 accounts)", "TP 105, FN 9, FP 3, TN 791"],
                 ["Botnets recovered", f"{F.REC['recovered']} of {F.REC['botnets']} (mean recall {_r(F.REC['mean_recall'])}, precision {_r(F.REC['mean_precision'])})"],
                 ["Accounts flagged at 0.5", f"{F.FLAGGED} of {F.NODES:,}"],
                 ["GraphSAGE epoch at 36,264 accounts", f"{F.scal_row(8)['models']['sage']['train_seconds_per_epoch']:.3f} s"],
                 ["API median response", "3-16 ms (p95 up to 28 ms)"],
                 ["Smoke test", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks pass"]],
                widths=[3.3, 3.2], align=["l", "l"], size=10)]
    out += _retrain() + _screens() + _sample_io() + _success_failure() + _limits() + _objectives()
    return _trim(out) if F.REPORT else out
