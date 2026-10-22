"""7.Review_1_PPT.pptx: 16 slides, problem identification and research. Built from D:\\abstracts\\Templates\\Review_1_PPT.pptx."""

import os

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K
from .lit import GAP, LIT_TABLE, NEED, OBJECTIVES, PROBLEM_POINTS, PROBLEM_STATEMENT
from .refs import REFS

TEMPLATE = r"D:\abstracts\Templates\Review_1_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"


def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    # layout footer text carries the template's deck title
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.keywords = "; ".join(F.KEYWORDS)
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


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 1")
    S = list(prs.slides)
    assert len(S) == 16, len(S)
    notes = {}

    # ---- 1 title
    title_slide(S[0], "A TF-IDF and stylometric pipeline reduced by PCA, tuned by the Firefly algorithm and classified by an RBF multi-class SVM, with a PARTIALLY TRUE class",
                "REVIEW 1  ·  PROBLEM IDENTIFICATION AND RESEARCH")
    notes[1] = ("Introduce the team and the title. One sentence: the system reads a news statement and returns REAL, PARTIALLY TRUE or FAKE with a confidence, "
                "using a light pipeline (PCA, Firefly, multi-class SVM) instead of a heavy neural network.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Abstract and overview"), ("02", "Base paper"), ("03", "Literature survey"), ("04", "Existing approaches and limitations"),
               ("05", "Research gap"), ("06", "Problem statement and objectives"), ("07", "Proposed approach and architecture"),
               ("08", "Expected outcomes"), ("09", "References")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda. This review is about why the problem matters and what is missing in current work; measured results come in the later reviews."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract: a light, optimised classifier for fake news")
    wipe(s)
    W, H = 3.85, 4.9
    for i, (t, body, col, gl) in enumerate([
        ("The problem", "Misinformation spreads through news portals and social media faster than it can be fact-checked. Many detectors are heavy, tune poorly, and treat news as only real or fake, ignoring partially true items.", K.ORANGE, "!"),
        ("Our idea", "Turn text into TF-IDF and stylometric features, reduce them with Principal Component Analysis, let the Firefly algorithm pick the features and the SVM parameters, and classify with a multi-class SVM.", K.BLUE, "i"),
        ("The deliverable", "A working application, TruthGlow: a verdict of REAL, PARTIALLY TRUE or FAKE with confidence for one article or a whole CSV, model analytics, and retraining on the user's own labelled data.", K.GREEN, "✓"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, H, t, body, col, gl, body_size=18)
    notes[3] = "Three points: the problem, the PCA + Firefly + MSVM idea, and the deliverable: a complete application, not only a model script."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base paper")
    wipe(s)
    K.box(s, 0.6, 1.4, 12.13, 1.1, fill=K.CARD)
    K.text(s, 0.82, 1.48, 11.7, 0.95, F.BASE_PAPER, size=13, color=K.INK, anchor="m")
    cw = 3.85
    cards = [
        ("Method", "CAMeLBERT contextual embeddings feed a neural network classifier. Class weighting in the loss handles imbalance and is compared with undersampling, oversampling and SMOTE; four Arabic transformers are compared.", K.BLUE, "M"),
        ("Data and reported results", "7,474 Arabic news articles, binary real or fake, 80/20 split. Reported: F1 96.19 %, accuracy 95.52 %, precision 95.48 %, recall 96.90 % on a Tesla T4 GPU; TF-IDF + NN baseline accuracy 90.97 %.", K.GREEN, "R"),
        ("What we take, what differs", "Taken: class weighting, several metrics, comparison with baselines. Different: classical features with PCA and a metaheuristic instead of transformer embeddings; English; three classes; CPU only.", K.ORANGE, "L"),
    ]
    for i, (t, b_, col, gl) in enumerate(cards):
        K.card(s, 0.6 + i * (cw + 0.29), 2.75, cw, 4.0, t, b_, col, gl, body_size=15)
    notes[4] = ("Read the citation. The base paper builds an Arabic binary detector on transformer embeddings. Our project keeps its ideas of class weighting and fair baselines "
                "but chooses a computationally light route. The two sets of numbers will not be comparable: language, task and hardware differ.")

    # ---- 5 literature survey table
    s = S[4]
    set_title(s, "Literature survey")
    wipe(s)
    rows = [["Work", "Approach", "Data", "Reported result / role"]]
    short = {
        0: ["Saad et al. 2026 [1] (base)", "CAMeLBERT embeddings + NN with class weights", "7,474 Arabic articles, binary", "F1 96.19 %, accuracy 95.52 % (GPU)"],
        1: ["Dell'Oglio et al. 2026 [2]", "12 approaches compared (ML, deep, transformers, LLMs)", "10 English datasets incl. LIAR-PLUS", "LIAR-PLUS hardest: F1 0.56 (LR), 0.57 (SVM)"],
        2: ["Huang et al. 2025 [3]", "TF-IDF + Transformer BiGRU + Bayesian optimisation", "Fake/real news corpus", "99.73 % test accuracy (binary)"],
        3: ["Xu and Kechadi 2024 [4]", "Fuzzy deep hybrid network; releases LIAR2", "LIAR2: 18,369 / 2,297 / 2,296 statements", "Benchmark used in this project"],
        4: ["Wang 2017 [5]", "LIAR: short PolitiFact statements, six truth labels", "About 12.8 k statements", "Text-only models score far lower"],
        5: ["Ahmed et al. 2017 [19]", "N-gram TF-IDF with classical classifiers", "News article corpora", "Linear SVM among the strongest"],
    }
    for i in range(6):
        rows.append(short[i])
    K.table(s, 0.6, 1.4, [2.6, 3.9, 2.9, 2.73], rows, font_size=12, row_h=0.72, header_size=13)
    notes[5] = ("The pattern: transformer and neural detectors report very high scores on binary data; the cross-dataset comparison finds fine-grained fact-checking data much harder. "
                "Where a work's figures were not checked they are not quoted. The batch survey also lists four 2024-2025 papers whose authors were not recorded; they appear in the report's reference list with that caveat.")

    # ---- 6 supporting evidence (chart)
    s = S[5]
    set_title(s, "Supporting evidence: the task sets the number")
    wipe(s)
    gf = K.bar_chart(s, 0.6, 1.4, 7.6, 5.3,
                     ["Base paper\nTF-IDF + NN\n(Arabic, binary)\naccuracy", "Base paper\nCAMeLBERT + NN\n+ class weights\naccuracy", "Survey [2]\nLogistic regr.\nLIAR-PLUS\n(binary) F1", "Survey [2]\nSVM\nLIAR-PLUS\n(binary) F1"],
                     [("Reported score", [0.9097, 0.9552, 0.56, 0.57])], colors=[K.BLUE], number_format="0.00", font_size=12, max_value=1.1)
    for idx in (2, 3):
        pt = gf.chart.plots[0].series[0].points[idx]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = K.ORANGE
    K.card(s, 8.5, 1.45, 4.23, 2.6, "Takeaway", "Binary Arabic news is detected with accuracy above 0.90, but on LIAR-PLUS, a fact-checking dataset with six truth levels, even good classical models reach F1 near 0.56.", K.GREEN, "↑", body_size=14)
    K.card(s, 8.5, 4.2, 4.23, 2.5, "Caveat", "Blue bars are accuracies on Arabic data, orange bars are F1 on English data as reported in the papers. They are not comparable and no ranking is implied. Our own results come in later reviews.", K.ORANGE, "!", body_size=14)
    notes[6] = ("Values are quoted from the papers: 90.97 % and 95.52 % accuracy from the base paper, and LR 0.56 and SVM 0.57 F1 on LIAR-PLUS from the comparison paper. "
                "The point: protocol and label granularity decide the number, so a project that includes a PARTIALLY TRUE class should expect lower scores than binary benchmarks.")

    # ---- 7 existing system
    s = S[6]
    set_title(s, "Existing system and current approaches")
    wipe(s)
    K.flow(s, 0.6, 1.55, 12.13, 1.1, [("Article published", K.NAVY), ("Shared widely", K.NAVY), ("Fact-checker reviews", K.NAVY), ("Verdict published later", K.NAVY)], size=16, gap=0.5)
    K.card(s, 0.6, 3.1, 5.95, 3.55, "Manual fact-checking", "Accurate, but slow and limited in volume: the fact-check usually appears after the item has already reached a large audience, and only a fraction of items is ever checked.", K.BLUE, "1", body_size=17)
    K.card(s, 6.78, 3.1, 5.95, 3.55, "Automatic detectors", "Machine-learning and deep-learning classifiers label items real or fake. Many are heavy, are tuned by hand and report accuracy without cost, and most ignore the partially true middle.", K.ORANGE, "2", body_size=17)
    notes[7] = "Today's path is manual fact-checking, which cannot match volume or speed. Automatic detectors exist, but they are often heavy, binary and weakly tuned."

    # ---- 8 limitations
    s = S[7]
    set_title(s, "Limitations of existing methods")
    wipe(s)
    items = [
        ("Slow, limited manual checking", "Fabricated news reaches large audiences before any fact-check is published.", K.ORANGE, "1"),
        ("High-dimensional features", "Sparse text features make classifiers slow and prone to overfitting if left unreduced.", K.BLUE, "2"),
        ("Default parameters", "Untuned classifier parameters give suboptimal accuracy on noisy news text.", K.GREEN, "3"),
        ("Cost and nuance ignored", "Many detectors report accuracy only, say nothing of computational cost, and have no class for partially true items.", K.PURPLE, "4"),
    ]
    for i, (t, b_, col, gl) in enumerate(items):
        r, c = divmod(i, 2)
        K.card(s, 0.6 + c * 6.18, 1.5 + r * 2.7, 5.95, 2.5, t, b_, col, gl, body_size=17)
    notes[8] = "Four limitations, taken from the project's problem statement and the survey. Each maps to a design decision: PCA, Firefly tuning, a PARTIALLY TRUE class, and honest reporting of cost."

    # ---- 9 research gap
    s = S[8]
    set_title(s, "Research gap")
    wipe(s)
    gaps = [("Light pipeline", "Surveyed work applies neural and transformer models; a computationally light pipeline is less explored."),
            ("Feature reduction", "PCA can cut dimensionality, but how much accuracy it keeps on real news text needs measuring."),
            ("Metaheuristic tuning", "Firefly search for the feature subset and SVM parameters is proposed; its gain over default or random tuning must be tested."),
            ("Partially true class", "Binary labels hide the middle ground; a third class makes the task harder and more useful."),
            ("Honest evaluation", "Scores are rarely given with baselines, per-class results, cost and latency in one place.")]
    for i, (k, v) in enumerate(gaps):
        y = 1.45 + i * 1.08
        K.box(s, 0.6, y, 2.6, 0.9, fill=K.NAVY, line=None, radius=0.06)
        K.text(s, 0.6, y, 2.6, 0.9, k, size=16, color=K.WHITE, bold=True, align="c", anchor="m")
        K.text(s, 3.5, y, 9.2, 0.9, v, size=17, color=K.INK, anchor="m")
    notes[9] = ("The batch survey states the gap as: a computationally light pipeline where feature reduction and metaheuristic parameter tuning deliver comparable accuracy at lower cost. "
                "The project tests that claim rather than assuming it.")

    # ---- 10 problem statement
    s = S[9]
    set_title(s, "Problem statement")
    wipe(s)
    K.box(s, 0.6, 1.45, 12.13, 2.75, fill=K.CARD)
    K.text(s, 0.95, 1.6, 11.45, 2.5, PROBLEM_STATEMENT, size=19, color=K.INK, anchor="m")
    for i, (t, b_) in enumerate([("Input", "News headline or article text, one item or a CSV of items"), ("Output", "REAL, PARTIALLY TRUE or FAKE, confidence, class probabilities, cue words"), ("Record", "Trained model, accuracy, macro-F1, confusion matrix, Firefly curve")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 4.5, 3.85, 1.5)
        K.text(s, x + 0.25, 4.62, 3.4, 0.4, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 5.1, 3.4, 0.8, b_, size=14, color=K.TXT)
    K.text(s, 0.6, 6.2, 12.13, 0.5, "Need: " + NEED, size=14, color=K.TXT, italic=True)
    notes[10] = "Read the statement slowly. Input is text, output is a three-way verdict with confidence, and the system keeps a model and its measured statistics that can be inspected."

    # ---- 11 objectives
    s = S[10]
    set_title(s, "Objectives")
    wipe(s)
    K.text(s, 0.6, 1.4, 12.13, 5.3, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate(OBJECTIVES, 1)], size=22, color=K.INK)
    notes[11] = "The six objectives from the proposal. The later reviews report which were met; stemming (objective 2) is a known gap, and the accuracy and cost objective is judged on measured data."

    # ---- 12 proposed approach
    s = S[11]
    set_title(s, "Proposed approach")
    wipe(s)
    cw = 2.88
    for i, (t, b_, col, gl) in enumerate([
        ("Featurise", "Clean the text, build TF-IDF (1-2 grams) and add 25 stylometric signals such as capitals, exclamation marks and lexicon ratios.", K.BLUE, "1"),
        ("Reduce", "Standardise, then PCA keeps up to 95 % of the variance with at most 300 components.", K.GREEN, "2"),
        ("Optimise", "Firefly algorithm selects PCA components and tunes C and gamma, scoring candidates by cross-validated macro-F1.", K.ORANGE, "3"),
        ("Classify", "RBF multi-class SVM with balanced class weights outputs REAL, PARTIALLY TRUE or FAKE with probabilities.", K.PURPLE, "4"),
    ]):
        K.card(s, 0.6 + i * (cw + 0.2), 1.45, cw, 3.4, t, b_, col, gl, body_size=16)
    K.box(s, 0.6, 5.1, 12.13, 1.5)
    K.circle(s, 0.85, 5.4, 0.7, K.NAVY, "W", 18)
    K.text(s, 1.8, 5.3, 10.7, 0.5, "Application", size=17, color=K.INK, bold=True)
    K.text(s, 1.8, 5.8, 10.7, 0.75, "TruthGlow: React web interface over a FastAPI service and a Python library. Detect one article, screen a CSV, view analytics and retrain on your own labelled data.", size=15, color=K.TXT)
    notes[12] = "Four stages from text to verdict, and the application around them. A separate baseline without Firefly is kept so the optimiser's benefit can be measured."

    # ---- 13 architecture
    s = S[12]
    set_title(s, "High-level proposed architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 3.0, 1.3, 7.3, 5.3)
    K.text(s, 0.6, 6.62, 12.13, 0.3, "Browser UI, FastAPI service, the PCA + Firefly + MSVM library, and the saved model bundle", size=12, color=K.TXT, align="c", italic=True)
    notes[13] = "Follow the diagram: the browser sends text to the FastAPI service, which calls the library; the fitted model is one saved bundle on disk and there is no database."

    # ---- 14 expected outcomes
    s = S[13]
    set_title(s, "Expected outcomes and contributions")
    wipe(s)
    outs = [("Working classifier", "A trained PCA + Firefly + MSVM model with three verdict classes.", K.BLUE, "1"),
            ("Measured comparison", "Accuracy, precision, recall and F1 against unoptimised and simpler baselines.", K.GREEN, "2"),
            ("Cost reported", "Training time and prediction latency stated next to accuracy.", K.ORANGE, "3"),
            ("Complete tool", "Detect, batch, analytics and retrain from one application.", K.PURPLE, "4"),
            ("Reproducibility", "Scripts write every metric to JSON; figures are regenerated from it.", K.BLUE, "5"),
            ("Quality", "Automated tests for the API, library and edge cases.", K.GREEN, "6")]
    for i, (t, b_, col, gl) in enumerate(outs):
        r, c = divmod(i, 3)
        K.card(s, 0.6 + c * 4.14, 1.5 + r * 2.7, 3.85, 2.5, t, b_, col, gl, body_size=16)
    notes[14] = "These are targets, not results. We will report whatever the held-out test data shows, including if the optimiser gives no gain."

    # ---- 15 references
    s = S[14]
    set_title(s, "References")
    wipe(s)
    idx = [1, 2, 3, 4, 5, 6, 8, 10, 19]
    K.text(s, 0.6, 1.35, 12.13, 5.5, [(f"[{n}] {REFS[n - 1]}", {"space_after": 5}) for n in idx], size=13, color=K.INK)
    notes[15] = "Selected references; the complete numbered list is in the project report."

    # ---- 16 thank you
    thank_you(S[15])
    notes[16] = "Likely questions: why SVM and PCA rather than a transformer; why Firefly; what PARTIALLY TRUE means; how the label comes from the six LIAR labels."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "7.Review_1_PPT.pptx")))
