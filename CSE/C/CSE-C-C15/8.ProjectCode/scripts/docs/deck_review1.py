"""7.Review_1_PPT.pptx: 16 slides, problem identification and research. Built from D:\\abstracts\\Templates\\Review_1_PPT.pptx.

Slide text comes from facts.py, lit.py and refs.py; Review 1 states the problem, the literature and the plan - measured results are in Review 2.
    python -m scripts.docs.deck_review1        # from 8.ProjectCode
"""

import os
import tempfile
import time

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import lit
from . import pptkit as K
from .refs import CITE as R
from .refs import REFS

TEMPLATE = r"D:\abstracts\Templates\Review_1_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"


# ------------------------------------------------------------------ helpers (shared with deck_review2)
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
    cp.keywords = "DDoS detection, Random Forest, CICIDS2017, Scapy, adaptive mitigation, carpet-bombing"
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


def title_slide(s, subtitle, label, title_size=30):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE, title_size)
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


def trim(path, tag, wait=60):
    """Copy of a diagram or chart with its white margins removed (written to the temp folder, source untouched)."""
    from PIL import Image, ImageChops

    t0 = time.time()
    while not os.path.exists(path):
        if time.time() - t0 > wait:
            raise FileNotFoundError(path)
        time.sleep(3)
    with Image.open(path) as im:
        im = im.convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            pad = 12
            bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.size[0]), min(bbox[3] + pad, im.size[1]))
            im = im.crop(bbox)
        out = os.path.join(tempfile.gettempdir(), f"sf_deck_{tag}.png")
        im.save(out)
    return out


def render(path, outdir):
    """Export every slide to PNG with PowerPoint COM (absolute path; serialised with the other builders)."""
    import win32com.client

    from .comlock import com_lock

    os.makedirs(outdir, exist_ok=True)
    with com_lock():
        app = win32com.client.DispatchEx("PowerPoint.Application")
        try:
            pres = app.Presentations.Open(os.path.abspath(path), True, False, False)
            pres.SaveAs(os.path.abspath(outdir), 18)
            pres.Close()
        finally:
            app.Quit()


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 1")
    S = list(prs.slides)
    assert len(S) == 16, len(S)
    notes = {}
    C = [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE]
    bp = F.BP

    # ---- 1 title
    title_slide(S[0], F.SUBTITLE, "REVIEW 1  ·  PROBLEM IDENTIFICATION AND RESEARCH", 28)
    notes[1] = ("Introduce the team and the title. One sentence: the batch asks for a framework that detects DDoS traffic in real time and mitigates it without blocking legitimate users; "
                "the base paper is a resource-aware ensemble detector for SDN, and SentinelFlow is the working product that closes the loop from detection to mitigation.")

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
    set_title(s, "Abstract: detection is not enough")
    wipe(s)
    W, H = 3.85, 5.0
    for i, (t, body, col, gl) in enumerate([
        ("The problem", "A DDoS attack sends traffic from many sources and leaves legitimate users without the service. Signature rules miss new patterns, detection without action leaves the service down, and blocking a legitimate source is itself a denial of service.", K.ORANGE, "!"),
        ("Our idea", "Capture traffic in rolling windows, reduce each window to ten flow features, classify it with a Random Forest, score how widely the traffic is spread over sources and destinations, rate its severity, and quarantine the worst sources for a short time.", K.BLUE, "i"),
        ("The deliverable", "SentinelFlow: Scapy or a safe simulator feeding a Random Forest, an explainable severity layer, temporary quarantine with automatic recovery, a SQLite history and a React console, evaluated on CICIDS2017.", K.GREEN, "✓"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, H, t, body, col, gl, body_size=19)
    notes[3] = ("Three points: why detection alone is not enough, what the pipeline does, and what is delivered. "
                "Mitigation here means a temporary application-level quarantine; the operating-system firewall is never changed.")

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base paper")
    wipe(s)
    K.box(s, 0.6, 1.4, 12.13, 1.1, fill=K.CARD)
    K.text(s, 0.82, 1.48, 11.7, 0.95, F.BASE_PAPER, size=13, color=K.INK, anchor="m")
    cw = 3.85
    cards = [
        ("Method", "A hybrid feature selector that combines Random Forest importance with the Banzhaf Power Index; seven classifiers (XGBoost, RF, Gradient Boosting, SVM, kNN, AdaBoost, Naive Bayes) and four hard-voting ensembles for DDoS detection in software-defined networks.", K.BLUE, "M"),
        ("Reported results", "All four ensembles reach 100 % accuracy, precision, recall and F1 on an SDN flow dataset (104,345 records) and a CIC-DDoS2023 subset (1,754,109 rows). Training time, inference time, memory and model size are profiled: the SVM and kNN ensembles are slow.", K.GREEN, "R"),
        ("Relevance and limits", "Same family of method as SentinelFlow (Random Forest on flow features). The paper evaluates offline; mitigation, online learning and live testbeds are listed as future work. This project builds that missing live loop.", K.ORANGE, "L"),
    ]
    for i, (t, b_, col, gl) in enumerate(cards):
        K.card(s, 0.6 + i * (cw + 0.29), 2.75, cw, 4.1, t, b_, col, gl, body_size=16)
    notes[4] = ("Read the citation. All figures on this slide are printed in the paper's text. Its own future work (online learning, testbeds, production traces, mitigation actions such as throttling) "
                "is where this project starts. Batch records name this paper as the base paper.")

    # ---- 5 literature survey table
    s = S[4]
    set_title(s, "Literature survey")
    wipe(s)
    keep = [r for r in lit.LIT_TABLE if f"[{R['s_ijesat']}]" not in r[0] and f"[{R['s_ijarcce']}]" not in r[0]]
    rows = [["Work", "Year", "Approach", "Reported result / limitation"]] + keep
    K.table(s, 0.6, 1.2, [2.55, 0.6, 4.7, 4.28], rows, font_size=11, row_h=0.52, header_size=11.5, align=["l", "c", "l", "l"])
    K.text(s, 0.6, 6.95, 12.13, 0.35, f"Batch survey items [{R['s_ijesat']}] and [{R['s_ijarcce']}] are known by title and record only; their results could not be verified and are not quoted.", size=11, color=K.TXT, italic=True)
    notes[5] = ("The batch survey contains the base paper plus four recent works; the table adds the papers found in the archived folder and the dataset audit. "
                "Results are quoted only where we read them in the paper, in the abstract, or in the base paper's own related-work section.")

    # ---- 6 supporting evidence (chart + list)
    s = S[5]
    set_title(s, "Supporting evidence from the literature")
    wipe(s)
    cats = ["Base paper\nensembles", "Swileh\nRAG + LLM", "Becerra-\nSuarez", "Alduailij", "WISNE\nXGBoost", "WISNE\nKNN", "Rahman\nSVM", "Rahman\nDT", "Rahman\nLR"]
    vals = [100.0, 99.94, 99.97, 99.0, 100.0, 97.0, 97.1, 82.7, 59.3]
    gf = K.bar_chart(s, 0.6, 1.35, 7.0, 4.95, cats, [("Reported accuracy, %", vals)], colors=[K.BLUE], number_format="0.0", font_size=10, max_value=110, label_size=9)
    for idx in (7, 8):
        pt = gf.chart.plots[0].series[0].points[idx]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = K.ORANGE
    K.text(s, 0.6, 6.35, 7.0, 0.7, "Accuracy as reported by each source on its own data; the datasets differ, so the bars are not a ranking. Rahman's logistic regression and decision tree show a weak model on the same data.", size=11.5, color=K.TXT, italic=True)
    K.text(s, 7.9, 1.45, 4.85, 5.4, [
        ("**What the literature shows**", {"space_after": 8}),
        (f"Tree-based learners reach 97-100 % on public DDoS data [{R['base']}], [{R['s_wisne']}], [{R['rahman']}].", {"bullet": True, "space_after": 8}),
        (f"A retrieval-and-LLM detector reaches 99.94 % on carpet-bombing traffic but needs about 2 s per request and an LLM service [{R['carpet']}].", {"bullet": True, "space_after": 8}),
        (f"The heaviest ensembles (SVM, kNN) take over 4,000 s to train or 150 s to classify one test set [{R['base']}].", {"bullet": True, "space_after": 8}),
        (f"CICIDS2017 itself has labelling problems that affect reported scores [{R['engelen']}].", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[6] = ("These numbers motivate the choice of a light tree ensemble that runs on a laptop. They come from different datasets and protocols, so they are not compared with each other. "
                "Our own measurements start in Review 2.")

    # ---- 7 existing system
    s = S[6]
    set_title(s, "Existing system and current approaches")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.1, [("Network traffic", K.NAVY), ("Signature or threshold IDS, or offline ML classifier", K.NAVY), ("Alert to an operator", K.NAVY), ("Manual response", K.NAVY)], size=14, gap=0.5)
    K.card(s, 0.6, 2.95, 5.95, 3.8, "Rules, thresholds and classical ML",
           f"Early SDN detectors count flows or packet rates against thresholds [{R['braga']}]; supervised learners (SVM, decision trees, Random Forest) classify flow records [{R['rahman']}], [{R['zaman']}], [{R['alduailij']}].\nTaxonomies of attack and defence are in [{R['mirkovic']}].", K.BLUE, "1", body_size=17)
    K.card(s, 6.78, 2.95, 5.95, 3.8, "Ensembles, deep and LLM-based detectors",
           f"Ensembles and feature selection raise accuracy [{R['base']}], [{R['hossain']}], [{R['becerra']}]; online ensembles add mitigation in SDN [{R['alashhab']}]; a retrieval-augmented LLM targets carpet bombing [{R['carpet']}].\nMost are evaluated offline or inside an emulated SDN.", K.ORANGE, "2", body_size=17)
    notes[7] = "Today's systems either alert a human or run inside an SDN controller testbed. Few run a capture, classify, act and recover loop on an ordinary host."

    # ---- 8 limitations
    s = S[7]
    set_title(s, "Limitations of existing methods")
    wipe(s)
    heads = ["Offline evaluation", "Detection without action", "Heavy models", "Dataset caveats"]
    bodies = [
        f"Reported 99-100 % scores come from offline splits of one dataset at a time; the base paper itself lists live testbeds and production traces as future work [{R['base']}].",
        f"A classifier that only raises an alert leaves the service down; the base paper describes a sidecar that could throttle flows but does not implement it [{R['base']}].",
        f"SVM and kNN ensembles need thousands of seconds to train or minutes to classify [{R['base']}]; the LLM detector needs about 2 s per request and a hosted model [{R['carpet']}].",
        f"CICIDS2017 has known labelling and flow-construction problems [{R['engelen']}]; models trained on closed-world data degrade on real traffic [{R['sommer']}].",
    ]
    for i in range(4):
        r, c = divmod(i, 2)
        K.card(s, 0.6 + c * 6.18, 1.45 + r * 2.35, 5.95, 2.15, heads[i], bodies[i], C[i], str(i + 1), body_size=16)
    K.box(s, 0.6, 6.25, 12.13, 0.75, fill=K.CARD)
    K.text(s, 0.85, 6.25, 11.7, 0.75, f"A false positive on a legitimate source is itself a denial of service, yet the cost of false alarms is rarely reported next to accuracy. Survey items known by title only are not quoted [{R['s_ijesat']}], [{R['s_ijarcce']}].", size=13, color=K.INK, anchor="m")
    notes[8] = "The first three come from the base paper and the related work; the fourth is a reminder that high accuracy on one dataset is not evidence for deployment."

    # ---- 9 research gap
    s = S[8]
    set_title(s, "Research gap")
    wipe(s)
    for i, g in enumerate(lit.GAPS):
        y = 1.4 + i * 1.75
        K.circle(s, 0.6, y + 0.35, 0.7, C[i % 4], str(i + 1), 20)
        K.text(s, 1.6, y, 11.1, 1.6, g, size=17, color=K.INK, anchor="m")
    K.box(s, 0.6, 6.5, 12.13, 0.6, fill=K.FHEAD, line=None)
    K.text(s, 0.85, 6.5, 11.6, 0.6, "Gap addressed here: a measured capture, classify, assess, act and recover loop with false-positive cost reported.", size=14, color=K.INK, anchor="m", bold=True)
    notes[9] = ("Gap 1 is the batch survey's own statement. Gaps 2 and 3 come from comparing the papers: scores are offline, one dataset at a time, and false-positive cost and carpet-bombing spread are seldom measured.")

    # ---- 10 problem statement
    s = S[9]
    set_title(s, "Problem statement")
    wipe(s)
    K.box(s, 0.6, 1.45, 12.13, 3.1, fill=K.CARD)
    K.text(s, 0.95, 1.6, 11.45, 2.85, [(p, {"bullet": True, "space_after": 8}) for p in lit.PROBLEM_STATEMENT], size=18, color=K.INK, anchor="m")
    for i, (t, b_) in enumerate([("Input", "Packets on a network interface (or simulated packets), grouped into rolling windows of 2-120 s, ten flow features per window"),
                                 ("Output", "Benign or Attack with a confidence, a severity from Low to Critical with its factors, and a temporary quarantine of the worst sources"),
                                 ("Measures", "Accuracy, precision, recall, F1, false-positive rate and time from detection to mitigation")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 4.8, 3.85, 1.95)
        K.text(s, x + 0.25, 4.9, 3.4, 0.4, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 5.35, 3.4, 1.35, b_, size=15, color=K.TXT)
    notes[10] = f"Read the statement slowly. The need, in the batch's words: {lit.NEED}"

    # ---- 11 objectives
    s = S[10]
    set_title(s, "Objectives")
    wipe(s)
    K.text(s, 0.6, 1.4, 12.13, 4.9, [(f"{i}.  {o}", {"space_after": 14}) for i, o in enumerate(lit.OBJECTIVES, 1)], size=21, color=K.INK)
    K.text(s, 0.6, 6.35, 12.13, 0.7, "How far each objective was met is reported in Review 2 and the final review, including the parts that were only partly achieved.", size=14, color=K.TXT, italic=True)
    notes[11] = "The six objectives from the proposal. Review 2 reports honestly which were met: live capture, for instance, could not be tested end to end on the development machine."

    # ---- 12 proposed approach
    s = S[11]
    set_title(s, "Proposed approach")
    wipe(s)
    cw = 2.88
    for i, (t, b_, col, gl) in enumerate([
        ("Capture", "Scapy sniffs a chosen interface for a rolling window (10 s by default); a built-in simulator generates benign, flood, carpet-bombing and slow traffic for demonstrations without sending any packets.", K.BLUE, "1"),
        ("Classify", "Ten features per window (packets, bytes, rates, average sizes, sent and received) go to a 200-tree Random Forest trained on CICIDS2017-style flows.", K.GREEN, "2"),
        ("Assess", "A transparent score of source and destination spread, rate and baseline deviation, then a severity with its listed factors.", K.ORANGE, "3"),
        ("Act", "High and Critical windows quarantine the top three sources for 40 s (80 s for Critical); quarantines expire and recover by themselves.", K.PURPLE, "4"),
    ]):
        K.card(s, 0.6 + i * (cw + 0.2), 1.45, cw, 3.7, t, b_, col, gl, body_size=15)
    K.box(s, 0.6, 5.35, 12.13, 1.4)
    K.circle(s, 0.85, 5.65, 0.7, K.NAVY, "UI", 16)
    K.text(s, 1.8, 5.5, 10.7, 0.45, "Flask API + SQLite history + React console (9 pages)", size=16, color=K.INK, bold=True)
    K.text(s, 1.8, 5.95, 10.7, 0.75, "Defensive only: no attack generation, no scanning, and the operating-system firewall is never changed by the application.", size=14, color=K.TXT)
    notes[12] = "Four stages and the console that wraps them. Mitigation is an application-level denylist inside SentinelFlow, which is the safe choice for a student prototype."

    # ---- 13 architecture
    s = S[12]
    set_title(s, "High-level proposed architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "r1_01"), 0.5, 1.2, 8.4, 5.9)
    K.text(s, 9.1, 1.5, 3.7, 5.2, [
        ("**Four tiers**", {"space_after": 8}),
        (f"Browser: React and Vite console (port {F.WEB_PORT}).", {"bullet": True}),
        (f"Flask API (port {F.API_PORT}), twelve JSON endpoints, input checks.", {"bullet": True}),
        ("Pipeline: capture or simulator, aggregator, Random Forest, distributed risk, severity, mitigation.", {"bullet": True}),
        ("State: SQLite database, model file and result files; nothing leaves the machine.", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[13] = "Follow the diagram top to bottom: the console calls the API, the API runs the shared per-window pipeline, and results are stored locally."

    # ---- 14 expected outcomes
    s = S[13]
    set_title(s, "Expected outcomes and contributions")
    wipe(s)
    heads = ["Working product", "Honest evaluation", "Explainable response", "Safe demonstration", "Stated limits"]
    bodies = [
        "A console that shows live or simulated windows, detections, health, quarantines and model metrics, backed by a tested API.",
        "Accuracy, precision, recall, F1 and false-positive rate on real CICIDS2017 flows, kept separate from synthetic results.",
        "Every severity comes with its contributing factors and a recommended action; quarantines recover automatically.",
        "Simulation Mode runs the identical pipeline without emitting traffic and is always labelled as simulation.",
        "Live capture needs Npcap and Administrator rights; mitigation is application-level; each limit is documented, not hidden.",
    ]
    for i, (h, b_) in enumerate(zip(heads, bodies)):
        if i < 3:
            K.card(s, 0.6 + i * 4.14, 1.5, 3.85, 2.65, h, b_, C[i % 4], str(i + 1), body_size=17)
        else:
            K.card(s, 0.6 + (i - 3) * 6.18, 4.35, 5.95, 2.4, h, b_, C[i % 4], str(i + 1), body_size=18)
    notes[14] = "These are the outcomes we committed to. The measured results, including where they are weaker than the headline numbers suggest, are presented in Review 2."

    # ---- 15 references
    s = S[14]
    set_title(s, "References")
    wipe(s)
    idx = [R[k] for k in ("base", "s_wisne", "s_ddqn", "carpet", "rahman", "cicids", "engelen", "sommer", "breiman", "alashhab")]
    K.text(s, 0.6, 1.25, 12.13, 5.8, [(f"[{n}] {REFS[n - 1]}".replace("*", ""), {"space_after": 6}) for n in idx], size=13, color=K.INK)
    notes[15] = "Selected references; the complete numbered list, with notes on how each entry was checked, is in the project report."

    # ---- 16 thank you
    thank_you(S[15])
    notes[16] = ("Likely questions: why a Random Forest rather than the base paper's ensembles (light, fast, explainable); why mitigation is a quarantine inside the application; "
                 "what data the model is trained on (this is answered in Review 2: the shipped model used a synthetic fallback and was re-checked on real flows).")

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "7.Review_1_PPT.pptx")))
