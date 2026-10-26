"""Text of 19.IEEE_Paper.docx (SentinelFlow). Every number is read from facts.py (results/metrics.json, results/experiments/*.json).

Citations are written {r:N} with the global reference numbers of refs.py; Paper.expand renumbers them in order of first appearance.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

from . import facts as F
from .paper import Paper
from .refs import CITE

NAVY, BLUE, TEAL, ORANGE, RED, GREY, PURPLE = "#1B2A41", "#2F6DB5", "#1E9E8F", "#E08A1E", "#C0392B", "#8A94A6", "#6B52D6"
PALE = {"blue": "#E4EEF9", "teal": "#DFF3EF", "orange": "#FCEBD3", "grey": "#EEF0F4", "purple": "#ECE8FA", "red": "#F9E0DC"}


def c(*keys):
    return "{r:" + ",".join(str(CITE[k]) for k in keys) + "}"


# ----------------------------------------------------------------------------- figures drawn at column width
def _save(fig, name):
    os.makedirs(F.FIGS, exist_ok=True)
    p = os.path.join(F.FIGS, name)
    fig.savefig(p, dpi=220, facecolor="white")
    plt.close(fig)
    return p


def _canvas(w, h, xmax, ymax):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.axis("off")
    return fig, ax


def _box(ax, x, y, w, h, text, fc="grey", fs=5.4, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=PALE.get(fc, fc), ec=NAVY, lw=0.7))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=NAVY, fontweight="bold" if bold else "normal", linespacing=1.15)


def _arrow(ax, x1, y1, x2, y2, style="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=6, lw=0.8, color=NAVY, shrinkA=0, shrinkB=0))


def fig_arch():
    plt.rcParams["font.family"] = "DejaVu Serif"
    fig, ax = _canvas(3.5, 3.0, 100, 86)
    _box(ax, 1, 73, 98, 11, "Browser: React 19 + Vite (port 5415)\nOverview · Detections · Analytics · Health · Mitigation · Model", "blue", 5.3, True)
    _arrow(ax, 50, 73, 50, 69.5, "<|-|>")
    _box(ax, 1, 56, 98, 12, "Flask app (port 8415): 12 JSON endpoints\nprocess_window(): one inference path for live and simulated windows", "purple", 5.3, True)
    _arrow(ax, 50, 56, 50, 52.5)
    mods = [("monitoring\nScapy sniff or\nsimulator;\naggregator", "orange"), ("ml\n10-feature\nschema, RF\nloader", "teal"), ("security\ndistributed risk\nseverity\nmitigation", "teal"), ("database\nSQLite:\n4 tables", "grey")]
    for i, (t, col) in enumerate(mods):
        _box(ax, 1 + i * 24.8, 29, 23.2, 23, t, col, 5.0)
    _arrow(ax, 50, 29, 50, 25.5, "<|-|>")
    _box(ax, 1, 10, 98, 15, "Files: data/sentinelflow.db · models/sentinelflow_rf.joblib\nresults/metrics.json, plots · docs/ (offline experiments)", "grey", 5.0)
    ax.text(50, 4, "OS firewall is never touched; REST API has no authentication", ha="center", fontsize=5.2, color=RED, fontweight="bold")
    return _save(fig, "paper_arch.png")


def fig_flow():
    plt.rcParams["font.family"] = "DejaVu Serif"
    fig, ax = _canvas(3.5, 2.4, 100, 69)
    ax.text(1, 66, "(A) per window, every 2-120 s (default 10 s)", fontsize=5.2, color=NAVY, fontweight="bold")
    steps = [("capture /\nsimulate", "orange"), ("aggregate\n10 features\n+ context", "orange"), ("Random\nForest:\nlabel,\nconf.", "teal"), ("risk 0..1\n+ severity\nscore", "teal"), ("act:\nquarantine /\nrecommend /\nmonitor", "purple")]
    for i, (t, col) in enumerate(steps):
        _box(ax, 1 + i * 19.8, 38, 17.2, 22, t, col, 4.9)
        if i < 4:
            _arrow(ax, 18.2 + i * 19.8, 49, 20.8 + i * 19.8, 49)
    _box(ax, 50, 22, 49, 10, "store row in SQLite;\nconsole polls every 2 s", "grey", 4.9)
    _arrow(ax, 89, 38, 89, 32.5)
    ax.text(1, 18, "(B) offline: CICIDS2017 CSV -> clean + map -> (+ 6,000 window rows)\n-> stratified 80/20 -> RF 200 trees -> joblib + metrics", fontsize=4.9, color=NAVY, va="top", linespacing=1.3)
    ax.text(1, 3, "quarantine lasts 40 s (80 s Critical), then the source recovers automatically", fontsize=4.9, color=GREY, style="italic")
    return _save(fig, "paper_flow.png")


def fig_results():
    plt.rcParams["font.family"] = "DejaVu Serif"
    K = F.K()
    fig, ax = plt.subplots(1, 2, figsize=(3.5, 2.1), gridspec_kw={"width_ratios": [1.15, 1]})
    labs = ["shipped\nown split", "shipped\nreal flows", "retrained\nreal flows"]
    acc = [K["ship_acc"], K["shipreal_acc"], K["rr_acc"][0]]
    fpr = [K["ship_fpr"], K["shipreal_fpr"], K["rr_fpr"][0]]
    x = np.arange(3)
    ax[0].bar(x - 0.2, acc, 0.4, color=NAVY, label="accuracy")
    ax[0].bar(x + 0.2, fpr, 0.4, color=ORANGE, label="FPR")
    for i, (a, b) in enumerate(zip(acc, fpr)):
        ax[0].text(i - 0.2, a + 0.015, f"{a * 100:.1f}", ha="center", fontsize=4.8)
        ax[0].text(i + 0.2, b + 0.015, f"{b * 100:.1f}", ha="center", fontsize=4.8)
    ax[0].set_xticks(x)
    ax[0].set_xticklabels(labs, fontsize=4.8)
    ax[0].tick_params(axis="y", labelsize=5)
    ax[0].legend(fontsize=4.6, frameon=False, ncol=2, loc="upper center", handlelength=1, columnspacing=0.8)
    ax[0].set_ylim(0, 1.3)
    ax[0].set_title("(a) data matters (%)", fontsize=5.6)
    w = ["2 s", "5 s", "10 s"]
    ml = [K["w2_fpr_ml"], K["w5_fpr_ml"], K["w10_fpr_ml"]]
    act = [K["w2_fpr_act"], K["w5_fpr_act"], K["w10_fpr_act"]]
    x = np.arange(3)
    ax[1].bar(x - 0.2, ml, 0.4, color=ORANGE, label="RF label")
    ax[1].bar(x + 0.2, act, 0.4, color=TEAL, label="High/Critical")
    for i, (a, b) in enumerate(zip(ml, act)):
        ax[1].text(i - 0.2, a + 0.012, f"{a * 100:.1f}", ha="center", fontsize=4.8)
        ax[1].text(i + 0.2, b + 0.012, f"{b * 100:.1f}", ha="center", fontsize=4.8)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(w, fontsize=5)
    ax[1].tick_params(axis="y", labelsize=5)
    ax[1].set_ylim(0, 0.55)
    ax[1].legend(fontsize=4.8, frameon=False, loc="upper right")
    ax[1].set_title("(b) benign FPR by window (%)", fontsize=5.6)
    for a in ax:
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.4)
    return _save(fig, "paper_results.png")


def shot_crop(name, out, box=None, width=1100):
    im = Image.open(F.shot(name)).convert("RGB")
    if box:
        im = im.crop(box)
    im.thumbnail((width, width * 2))
    p = os.path.join(F.FIGS, out)
    im.save(p, optimize=True)
    return p


# ----------------------------------------------------------------------------- the paper
def build(path):
    K = F.K()
    R, W, H, L, A = F.REAL, F.WIN, F.HYB, F.LAT, F.API
    figs = {"arch": fig_arch(), "flow": fig_flow(), "results": fig_results(),
            "detail": shot_crop("06_threat_detail.png", "paper_shot_detail.png", (880, 0, 1440, 640), 700),
            "overview": shot_crop("04_overview.png", "paper_shot_overview.png", (256, 56, 1440, 900), 1100),
            "model": shot_crop("10_model.png", "paper_shot_model.png", (256, 56, 1440, 560), 1100)}
    P = Paper()
    bs = R["baselines_seed42"]
    lat = {d["path"]: d for d in A["latency"] if d["method"] == "GET"}
    w2, w5, w10 = W["window_2s"], W["window_5s"], W["window_10s"]

    def pc(x, d=1):
        return f"{x * 100:.{d}f}"

    authors = [[n, f"Roll No. {r}", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY], India", "[EMAIL]"] for n, r in F.STUDENTS_UPPER]
    authors.append([F.GUIDE.upper(), f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY], India", "[EMAIL]"])
    P.title_block("SentinelFlow: Real-Time DDoS Detection and Adaptive Mitigation Using a Random Forest", authors)
    P.begin_two_columns()

    P.abstract(
        "A denial-of-service flood is only half handled when it is detected: the service stays down until traffic is actually contained, and blocking legitimate users is itself an outage. "
        "This paper presents SentinelFlow, a working host-level system that captures traffic with Scapy or a built-in simulator, reduces each rolling window to ten flow features, classifies it with a 200-tree Random Forest, "
        "scores how widely the traffic is spread over sources and destinations, assigns an explainable severity, and quarantines the busiest sources for a limited time before they recover automatically. "
        f"The shipped model was trained on a synthetic fallback and scores {pc(K['ship_acc'])} % on its own split, but only {pc(K['shipreal_acc'])} % on {K['real_rows']:,} real CICIDS2017 DDoS-day flows. "
        f"Retrained on those flows, the same forest reaches {pc(K['rr_acc'][0], 2)} % over five seeds. The severity layer removes most false alarms, window length matters, and mitigation is application-level only. "
        f"{F.PYTEST_PASSED} automated tests pass; live capture was not tested.",
        ["adaptive mitigation", "CICIDS2017", "DDoS detection", "network security", "Random Forest", "Scapy"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para(f"Distributed denial-of-service (DDoS) attacks exhaust a victim's bandwidth or processing capacity with traffic from many sources {c('mirkovic')}. "
           f"Rule and signature defences miss patterns they have not seen, and a variant called carpet bombing spreads the load over many destinations so that each flow looks small {c('carpet')}. "
           f"Machine-learning detectors are the usual answer, and recent surveys of detection and mitigation in software-defined networks (SDN) are extensive {c('su')}. "
           "The cost of the usual practice is that evaluation stops at an offline accuracy figure: nothing is blocked, no recovery is shown, and the false-positive cost, a legitimate source quarantined, is never priced.")
    P.para("Four problems motivate the work. Signature-based defences cannot detect novel or modified attack patterns. Detection without mitigation leaves the service unavailable while the attack continues. "
           "Blocking legitimate users through false positives is itself a denial of service. And attack traffic must be classified quickly enough to act before resources are exhausted. "
           "A usable system therefore needs a classifier, a decision rule that is cautious about acting, an action that expires by itself, and a way for an operator to see why a decision was taken.")
    P.para(f"The base paper {c('base')} builds an ensemble for SDN detection from Random Forest feature importance combined with a Banzhaf power index, compares seven classifiers and four voting ensembles on two datasets, "
           "reports 100 % on both and profiles training time, latency and model size; live deployment and mitigation are left as future work. "
           "The gap this project addresses is the closed loop from real-time detection to adaptive mitigation with a measured response.")
    P.para("The contributions are: (1) SentinelFlow, a tested end-to-end product with a React console, twelve JSON endpoints and a SQLite history; "
           "(2) an explainable distributed-risk and severity layer that lists its contributing factors and cuts false alarms; "
           "(3) a temporary, self-recovering quarantine with a safe Simulation Mode that drives the identical pipeline; and "
           "(4) an evaluation that separates synthetic from real data and states the gap. Section II surveys related work, Section III gives the method, Section IV the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("All measurements ran on one CPU-only desktop: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11, no GPU. "
           "Other jobs kept the processor at 100 % during the latency runs, so the timings below are upper bounds. Npcap was not installed.")
    P.sub("B", "Software Requirements")
    P.para(f"Python 3.11, Flask 3.1.3 {c('flask')}, scikit-learn 1.9.1 {c('sklearn')}, pandas 3.1.0, NumPy 2.4.6, psutil 7.2.2, Scapy 2.8.0 {c('scapy')} and SQLite; "
           "React 19 with Vite 8 for the console; pytest for the tests. Live capture needs Npcap and Administrator rights on Windows.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para(f"**Base paper.** Trigui et al. {c('base')} select features with Random Forest importance and a Banzhaf-index perturbation score, benchmark XGBoost, Random Forest, Gradient Boosting, SVM, kNN, AdaBoost and Naive Bayes, "
           "and combine the best learners in four hard-voting ensembles. They use an SDN flow dataset of 104,345 records with 23 features and a 1,754,109-row, 47-feature subset of CIC-DDoS2023. "
           "All four ensembles reach 100 % accuracy, precision, recall and F1 on both. The resource profile is the paper's strongest point: the two SVM ensembles needed more than 4,000 s to train on the SDN data and the kNN ensemble more than 150 s to classify its test set, while the lightest ensemble was small and fast.")
    P.para(f"**ML detection in SDN.** Alashhab et al. {c('alashhab')} use an online ensemble for detection and mitigation; Zaman et al. {c('zaman')} study decision trees; Alduailij et al. {c('alduailij')} combine mutual information with forest importance and report 99 % on CICIDS2017 and CIC-DDoS2019, "
           f"and Becerra-Suarez et al. {c('becerra')} report 99.97 % accuracy (both as quoted in the base paper). Raghavendran and Robinson {c('s_wisne')} report 97 % for kNN and 100 % for XGBoost on a testbed dataset, and Rahman {c('rahman')} reports 97.1 %, 82.7 % and 59.3 % for SVM, decision tree and logistic regression on a CIC sample. "
           f"Three further survey items {c('s_ijesat', 's_ddqn', 's_ijarcce')} (one uses double deep Q-networks) are cited by title only, as their abstracts were unavailable.")
    P.para(f"**Carpet bombing and dataset caution.** Swileh et al. {c('carpet')} detect carpet-bombing traffic in SDN with retrieval-augmented generation and a large language model (99.94 % accuracy, about 2 s per request, no supervised training). "
           f"Two warnings apply to every number in this field: CICIDS2017 {c('cicids')} has labelling and flow-construction flaws {c('engelen')}, and detectors tuned on one closed dataset often fail in operation {c('sommer')}.")
    P.table("Selected related work",
            ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [[f"Base paper {c('base')}", "RF-BPI selection, 4 voting ensembles", "SDN 104,345; CIC-DDoS2023 1.75 M", "100 % on both", "SVM/kNN costly; no mitigation"],
             [f"Swileh {c('carpet')}", "RAG + FAISS + LLM", "Mininet/Ryu, hping3", "99.94 %, ~2 s/request", "Needs an LLM service"],
             [f"Raghavendran {c('s_wisne')}", "KNN, XGBoost, NB", "WISNE-SDN testbed", "97 % (KNN), 100 % (XGB)", "Testbed; detection only"],
             [f"Rahman {c('rahman')}", "LR, tree, SVM", "CIC sample", "SVM 97.1 %", "Detection only"],
             [f"Alduailij {c('alduailij')}", "MI + RF importance", "CICIDS2017, CIC-DDoS2019", "99 % (via base)", "Older datasets"],
             [f"Becerra-Suarez {c('becerra')}", "Trees + deep nets", "Public DDoS data", "99.97 % (via base)", "No resource profile"],
             [f"Engelen {c('engelen')}", "Dataset audit", "CICIDS2017", "Label flaws found", "No detector"],
             ["This work", "RF + risk + severity + quarantine", "Synthetic; CICIDS2017 DDoS day", "Section IV", "No live capture test"]],
            [0.62, 0.72, 0.68, 0.7, 0.68], size=6.0)
    P.para("**Mitigation in the literature.** Mitigation is usually described as throttling or blackholing flows through SDN rules, or as ingress filtering against spoofed sources, and is rarely evaluated beyond a description. "
           "Where a response is evaluated it is tied to a controller or a testbed switch, which a single host does not have. The practical lesson for a host-level tool is conservative: act on the strongest evidence, expire the action, and never touch addresses that carry the operator's own traffic.")
    P.para("**Positioning.** The works above run in SDN controllers or testbeds and judge themselves by offline accuracy; the base paper adds resource profiling, the carpet-bombing study adds a realistic attack pattern. "
           "SentinelFlow works at host level on a single machine, uses a deliberately small feature set that both a packet sniffer and a flow dataset can supply, and puts its effort into what happens after the label: how confident to be, what to do, for how long, and what to show the operator. "
           "That choice trades the scale of an SDN deployment for a loop that can be run, inspected and tested on a laptop.")
    P.para("**Research gap.** Reported accuracies of 99-100 % come from offline runs on one dataset. Missing are a capture-to-action loop on a commodity host, a score that flags carpet-bombing spread, "
           "and an evaluation that prices false positives at the level where they hurt and says how far a synthetic training set carries.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Data and Features")
    P.para(f"Each monitoring window is reduced to ten features: received and sent packets, bytes, packets per second, bytes per second and average packet size. "
           f"Packets whose destination is a local address are received, those from a local address to a remote one are sent, and transit traffic counts as received. "
           f"The same schema is built from CICIDS2017 rows {c('cicids')}: forward packets and bytes become sent, backward become received, rates are counts over flow duration. "
           f"The training script looks for CICIDS2017 CSV files in data/raw; none was present when the product was built, so it generated a labelled synthetic fallback of 9,000 benign and 9,000 attack flows and added 6,000 windows from the simulator "
           f"aggregated through the real monitoring pipeline: {K['ship_n_train']:,} training and {K['ship_n_test']:,} test rows. For this paper we also downloaded the CICIDS2017 Friday-afternoon DDoS file from a public mirror: "
           f"{K['real_rows']:,} flows, {K['real_benign']:,} benign and {K['real_attack']:,} DDoS.")
    P.para("Cleaning follows the product's preprocessing module: column names are normalised, infinite values are dropped, every label other than BENIGN becomes Attack, missing packet or byte columns are treated as zero, flow durations are clipped to 1 microsecond-1 hour before rates are computed, and averages are zero when a direction has no packets. "
           "The simulator that produces demonstration and augmentation windows has four traffic styles: benign mixes of 60-600 packets between one local host and a few remote servers; floods of 2,500-9,000 small packets from 8-40 sources to one host; carpet-bombing windows of 1,800-6,000 packets from 10-45 sources to 6-20 victims; and slow windows of 300-1,200 TCP packets from many sources.")
    P.sub("B", "Classifier")
    P.para(f"A Random Forest {c('breiman')} of 200 trees with balanced class weights and seed 42 was chosen because it handles skewed, non-linear count features without scaling, trains in seconds, gives importances for the report and produces a probability that serves as confidence. "
           "Given a feature vector x, the forest votes with probability")
    P.eq("p(attack | x) = (1/T) Σ_t 1[ tree_t(x) = attack ],   T = 200")
    P.sub("C", "Distributed Risk and Severity")
    P.para("A transparent rule layer measures how distributed the window is. With n_s unique sources, n_d destinations, packet rate r and the mean r̄ of the last twelve windows:")
    P.eq("R = 0.30 min(n_s/30, 1) + 0.30 min(n_d/15, 1) + 0.25 min(r/1500, 1) + 0.15 min(max(r/r̄ − 1, 0)/4, 1)")
    P.para("The severity score S adds fixed points for an Attack label (30), confidence of 0.9 or more (15), packet rate (up to 20), R of 0.7 or more (20), a wide spread (8) and persistence over consecutive suspicious windows (up to 10); "
           "benign windows are capped at 45. Low, Medium, High and Critical start at 0, 28, 50 and 70, and every contributing factor is stored as text. "
           "High and Critical windows quarantine the three busiest non-protected sources for T_q = 40 s (80 s for Critical); Medium only recommends rate limiting; expiry marks the record recovered.")
    P.para("Two safeguards follow from the cost of false positives. Loopback, the simulator's own host and every local interface address are protected and never quarantined; if no unprotected source remains the system only recommends rate limiting. "
           "A quarantined address cannot be quarantined again while its record is active, so a long attack produces one record per source, not one per window. "
           "The persistence counter rises by one for every consecutive window that the forest calls Attack or whose R is at least 0.7, and resets on the first clean window.")
    P.sub("D", "Evaluation Protocol")
    P.para("Accuracy, precision, recall, F1 and ROC-AUC are computed from the confusion matrix with the attack class as positive; the false-positive rate is")
    P.eq("FPR = FP / (FP + TN)")
    P.para("because an ill-judged quarantine is the cost that matters most here. Three questions are asked separately: how the shipped model performs on its own held-out split, how it performs on real flows it never saw, and how the whole pipeline behaves on windows of 2, 5 and 10 s. "
           "A chronological block split (first 70 % of the file's rows for training, last 30 % for testing) and five random seeds check that the real-data result does not depend on one lucky split; a feature-group ablation and five alternative classifiers check what the 10 features carry.")
    P.sub("E", "Architecture and Implementation")
    P.para(f"A Flask service holds one function, process_window(), which both the Scapy engine and the simulator call, so live and simulated windows take the same path {c('flask')}. "
           "Detections, quarantines, health samples and settings go to SQLite; a background thread samples CPU and memory every five seconds; the React console polls every two seconds. "
           "The operating-system firewall is never changed: quarantine is a denylist inside SentinelFlow.")
    P.para("The REST layer exposes status, health, interfaces, detections (with a limit that is clamped to 1-500), the latest detection, mitigations, settings (window 2-120 s, quarantine 5-3600 s), start and stop for live capture and for simulation, and the stored model metrics; "
           "bad input returns HTTP 400, a second start returns 409 and an unknown path returns a JSON 404. The console shows a banner whenever the data are simulated and a separate warning on the Model screen when the model was trained on synthetic data. "
           "Access to the console is a browser-side demo sign-in; the API itself has no authentication and binds to 127.0.0.1 only.")
    P.figure(figs["arch"], "SentinelFlow architecture: browser, Flask API, pipeline modules and local files.", 3.3)
    P.figure(figs["flow"], "Main flow: (A) one pass per monitoring window and (B) offline training.", 3.3)

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.sub("A", "Test Conditions")
    P.para(f"Metrics were computed with scikit-learn on a stratified 80/20 split (seed 42; five seeds where stated). The window experiments used 4,000 windows per length from the product's own simulator generator (35 % attack, seed 2026), "
           f"aggregated and scored statefully as in the application. {F.PYTEST_PASSED} pytest tests (scratch database) and {F.SMOKE_PASSED} backend smoke checks passed. Timings are on the saturated host of Section I-A.")
    P.table("Detection results (positive class = attack)",
            ["Setting", "Acc. %", "Rec. %", "FPR %", "F1 %"],
            [["Shipped RF, own synthetic split (4,800)", pc(K["ship_acc"], 2), pc(K["ship_rec"], 2), pc(K["ship_fpr"], 2), pc(K["ship_f1"], 2)],
             [f"Shipped RF, real DDoS-day flows ({K['real_rows']:,})", pc(K["shipreal_acc"]), pc(K["shipreal_rec"]), pc(K["shipreal_fpr"]), pc(K["shipreal_f1"])],
             ["RF retrained on real flows (5 seeds)", f"{pc(K['rr_acc'][0], 2)}±{pc(K['rr_acc'][1], 2)}", f"{pc(K['rr_rec'][0], 2)}±{pc(K['rr_rec'][1], 2)}", f"{pc(K['rr_fpr'][0], 2)}±{pc(K['rr_fpr'][1], 2)}", f"{pc(K['rr_f1'][0], 2)}±{pc(K['rr_f1'][1], 2)}"],
             ["Retrained, first 70 % train / last 30 % test", pc(K["blk_acc"], 2), pc(K["blk_rec"], 2), pc(K["blk_fpr"], 2), pc(R["real_rf_block_split"]["f1"], 2)],
             ["Product recipe (real + window rows), mixed test", pc(H["mixed_test"]["accuracy"], 2), pc(H["mixed_test"]["recall"], 2), pc(H["mixed_test"]["fpr"], 2), pc(H["mixed_test"]["f1"], 2)]],
            [1.5, 0.45, 0.45, 0.45, 0.45], size=6.4, align=["l", "c", "c", "c", "c"])
    P.sub("B", "Real Data Against Synthetic Data")
    P.para(f"The shipped model's {pc(K['ship_acc'], 2)} % is a property of its synthetic data. On real flows it scores {pc(K['shipreal_acc'])} % accuracy, {pc(K['shipreal_rec'])} % recall and {pc(K['shipreal_fpr'])} % false-positive rate "
           f"(ROC-AUC {pc(K['shipreal_auc'])} %: the ranking is useful but the 0.5 threshold is not): {R['shipped_on_real_all']['fn']:,} of {K['real_attack']:,} DDoS flows were missed. "
           f"Retrained on real flows with the same ten features, 200 trees and settings, the forest reaches {pc(K['rr_acc'][0], 2)} % over five seeds and {pc(K['blk_acc'], 2)} % on a chronological block split, in {R['real_rf_per_seed'][0]['train_seconds']:.0f} s with a {R['real_rf_model_mb']} MB model. "
           f"On the same split a decision tree scores {pc(bs['DecisionTree']['accuracy'], 2)} %, gradient boosting {pc(bs['HistGradientBoosting']['accuracy'], 2)}, logistic regression {pc(bs['LogisticRegression(scaled)']['accuracy'])} and Gaussian Naive Bayes {pc(bs['GaussianNB']['accuracy'])} %, "
           f"so the forest is not special on this file. A feature ablation shows sent-side features alone give {pc(R['ablation_seed42']['sent_only']['accuracy'], 2)} % and received-side features alone {pc(R['ablation_seed42']['received_only']['accuracy'])} %. "
           "The model also shifts what it relies on: the shipped forest ranks sent and received packet counts first, the real-data forest ranks average sent packet size first.")
    P.figure(figs["results"], "(a) Accuracy and false-positive rate by training data; (b) false-positive rate on benign simulator windows by window length, RF label alone and High/Critical severity.", 3.4)
    P.sub("C", "Window Length and the Severity Layer")
    P.para(f"The model was calibrated on 10 s windows. At 10 s the forest is perfect on simulator windows, but only because the training augmentation came from the same generator; this is not evidence about real attacks. "
           f"At shorter windows packet rates rise and benign traffic looks like attack: the label alone raised {pc(K['w2_fpr_ml'])} % false positives at 2 s and {pc(K['w5_fpr_ml'])} % at 5 s. "
           f"Acting only on High or Critical severity gives {pc(K['w2_fpr_act'], 2)} % and {pc(K['w5_fpr_act'], 2)} % with attack recall {pc(K['w2_rec_act'])} % and {pc(K['w5_rec_act'])} %. "
           f"At 10 s that gate had {pc(K['w10_fpr_act'])} % false positives but missed {w10['actionable_high_or_critical']['fn']} of {w10['attack_windows']:,} attack windows (recall {pc(K['w10_rec_act'])} %), which stayed at Medium. "
           f"The distributed-risk score on its own is precise but weak: at a threshold of 0.7 it flagged no benign window yet found only {pc(w10['distributed_risk_ge_0.7_only']['recall'], 0)} % of attacks at 10 s and {pc(w2['distributed_risk_ge_0.7_only']['recall'], 0)} % at 2 s; it helps inside the severity score, not as a detector.")
    bf = W["window_5s"]["by_style"]
    P.table("Pipeline on 4,000 simulator windows per length (35 % attack)",
            ["Window", "RF acc. %", "RF FPR %", "Sev. acc. %", "Sev. FPR %", "Sev. rec. %"],
            [[f"{k[7:]}", pc(W[k]["ml_only"]["accuracy"]), pc(W[k]["ml_only"]["fpr"]), pc(W[k]["actionable_high_or_critical"]["accuracy"]), pc(W[k]["actionable_high_or_critical"]["fpr"], 2), pc(W[k]["actionable_high_or_critical"]["recall"])]
             for k in ("window_2s", "window_5s", "window_10s")],
            [0.5, 0.58, 0.58, 0.6, 0.58, 0.56], size=6.4, align=["c"] * 6)
    P.para(f"By traffic style at 5 s, floods averaged {bf['flood']['mean_packet_rate']:.0f} packets/s, carpet-bombing windows {bf['carpet']['mean_packet_rate']:.0f}, slow windows {bf['slow']['mean_packet_rate']:.0f} and benign windows {bf['benign']['mean_packet_rate']:.0f}; "
           f"every attack window of every style reached High or Critical, and of the {bf['benign']['n']:,} benign windows {bf['benign']['severity_counts']['Medium']} were Medium, {bf['benign']['severity_counts']['High']} High and none Critical. "
           f"Slow attacks are the weakest case: {bf['slow']['severity_counts']['High']} of {bf['slow']['n']} reached only High, because their packet rate (about {bf['slow']['mean_packet_rate']:.0f}/s) earns few rate and spread points and they depend on the model label and persistence. "
           f"In a 2 s live-simulation run through the real HTTP API, the first detection was stored {A['first_detection_after_start_seconds']:.1f} s after Start; {A['live_sim_windows_scored']} windows were scored ({A['live_sim_by_prediction']['Attack']} Attack, {A['live_sim_by_prediction']['Benign']} Benign) and {A['live_sim_quarantines_recorded']} quarantine rows were written.")
    P.sub("D", "Speed and Interface")
    P.para(f"From a finished feature vector to the mitigation decision took a median of {L['detect_to_mitigation_ms']['p50']:.0f} ms (95th percentile {L['detect_to_mitigation_ms']['p95']:.0f} ms) on the saturated host; aggregation was {L['aggregate_ms']['p50']:.1f} ms and risk plus severity {L['risk_severity_ms']['p50']:.2f} ms. "
           f"Most of the rest is forest inference: the saved model uses n_jobs=-1, which costs {L['single_inference_ms_n_jobs_-1']['p50']:.0f} ms per single window against {L['single_inference_ms_n_jobs_1']['p50']:.0f} ms with one worker. "
           f"The real delay is the window itself (default 10 s). Over HTTP on 127.0.0.1 the status endpoint answered in {lat['/api/status']['p50_ms']:.1f} ms median and the 500-row detections list in {lat['/api/detections?limit=500']['p50_ms']:.1f} ms. "
           f"All {A['probes_total']} malformed-input probes (bad limits, out-of-range settings, path traversal, a second start) were refused or tolerated as intended and the service stayed healthy.")
    P.figure(figs["overview"], "Overview screen in Simulation Mode: session control, the real capture-driver warning (Npcap absent), status cards and the packet-rate history.", 3.4)
    P.figure(figs["model"], "Model screen: held-out metrics with the “synthetic training data” warning, confusion matrix and feature importance.", 3.4)
    P.figure(figs["detail"], "Threat Detail screen for one scored window (Simulation Mode): verdict, measured traffic, distributed-risk components and severity factors.", 2.3)
    P.para("Figs. 4-6 show the operator's view. The Overview screen labels the session as simulated and shows the real capture-driver warning; the Model screen carries the synthetic-data warning next to its 99.71 % accuracy; "
           "the Threat Detail screen lists, for one window, the measured traffic, the four components of R and every severity factor, together with the recommended action, so that a quarantine can be traced to its causes. "
           "These screens were captured from the running application with data scored by the real model at 2 s windows, and the Analytics screen of that session counted 155 of 237 windows as Attack although the simulator draws only 35 % attack windows, consistent with the 2 s false-positive rate above.")
    P.sub("E", "Threats to Validity")
    P.para("Four threats limit these numbers. First, the real-data result rests on one capture day and one attack type, so it says nothing about other attacks; random splits of flow data let neighbouring flows of one attack appear on both sides, which the block split only partly answers. "
           f"Second, CICIDS2017 labels are known to contain errors {c('engelen')}. Third, the window results come from a simulator whose generator also produced part of the training rows, so they test calibration, not generalisation. "
           "Fourth, no live capture, real service outage or real carpet-bombing traffic was available, so detection-to-mitigation time is a decision latency, not the time a victim would wait.")
    P.sub("F", "Comparison with the Base Paper and Failure Cases")
    P.para(f"The base paper's 100 % {c('base')} is on a 104,345-row SDN dataset and a 1.75 M-row CIC-DDoS2023 subset with ensembles and Banzhaf-selected features; our {pc(K['rr_acc'][0], 2)} % is on CICIDS2017 DDoS-day flows with ten features and a single forest. "
           "The datasets, labels and protocols differ, so the figures are indicative only, and the CICIDS2017 file contains one attack type. On cost, our forest trains in seconds and the model is small, in line with the paper's lightest ensemble; "
           "we did not reproduce its Banzhaf selection or voting ensembles. Mitigation, which the paper leaves as future work, is implemented here only at application level.")
    P.para("Failures observed: the shipped model misses 37 % of real DDoS flows; the label alone is unusable at 2 s windows; live capture without Npcap returns the driver error through the status endpoint and stops the session; "
           "the interface setting accepts a 5,000-character string; the landing page shows the synthetic 99.71 % figure without a caveat; and quarantine drops no real packets.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para(f"SentinelFlow closes the detection-to-mitigation loop on a commodity host with an explainable severity layer, a self-recovering quarantine, a SQLite history and a React console, and it passes {F.PYTEST_PASSED} tests. "
           f"Of the six objectives, dataset handling, classifier, dashboard and evaluation were met; live capture is implemented but untested here, and mitigation is a denylist rather than enforcement. "
           f"The key finding is a data gap: {pc(K['ship_acc'])} % on synthetic data became {pc(K['shipreal_acc'])} % on real flows, while the same forest retrained on real flows reached {pc(K['rr_acc'][0], 2)} %. "
           "Limits are one attack type, flow-level data, label noise, a simulator-driven demonstration and a CPU-saturated host for timings.")
    P.table("Objectives against outcomes",
            ["Objective", "Outcome"],
            [["Dataset and features", "Partly: shipped model synthetic; real file mapped and tested"],
             ["Live capture, same features", "Implemented; not tested live (no Npcap)"],
             ["Train classifier", f"Met on real flows after retraining ({pc(K['rr_acc'][0], 2)} %)"],
             ["Adaptive mitigation", "Partly: self-recovering quarantine; no enforcement"],
             ["Dashboard", "Met: nine-page React console"],
             ["Accuracy, FPR, time to mitigation", "Met for accuracy, FPR; latency is decision time"]],
            [1.45, 1.95], size=6.4)
    P.para("Future work: retrain on the full CICIDS2017 and CIC-DDoS2023 data and test across datasets; enforce quarantine through the operating-system firewall or an SDN controller with explicit opt-in; "
           "test live capture and real carpet-bombing traffic on a testbed; set n_jobs=1 and window-aware calibration; add authentication to the API; and compare Banzhaf selection and voting ensembles on the same flows.")

    P.references()
    P.save(path)
    return path
