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
    cp.keywords = "complex emotion recognition, cEmoGAN, conditional GAN, multi-label CNN, FER2013, facial expression"
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
        out = os.path.join(tempfile.gettempdir(), f"mosaic_deck_{tag}.png")
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
    notes[1] = ("Introduce the team and the title. One sentence: most face-emotion systems name one basic emotion, real faces mix emotions, and labelled mixed-emotion images are scarce; "
                "the base paper generates mixed-emotion faces with cEmoGANs and trains a multi-label CNN on them, and Mosaic is the working application built on that idea.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Abstract and overview"), ("02", "Base paper"), ("03", "Literature survey and evidence"), ("04", "Existing system and limitations"),
               ("05", "Research gap"), ("06", "Problem statement and objectives"), ("07", "Proposed approach and architecture"),
               ("08", "Expected outcomes"), ("09", "References")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda. This review explains why the problem matters and what is missing in current work; design details and measured results come in the later reviews."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract: one face, several emotions")
    wipe(s)
    W, H = 3.85, 5.0
    for i, (t, body, col, gl) in enumerate([
        ("The problem", "Most recognisers name one basic emotion per face. Real faces often mix emotions, such as happiness with surprise or sadness with fear. Labelled mixed-emotion images are scarce, and expression-editing GANs tend to distort the identity of the face.", K.ORANGE, "!"),
        ("Our idea", "Use a conditioned emotion GAN (cEmoGAN) to generate faces that show two emotions at once, use them to enlarge the scarce complex-emotion data, and train a CNN with one sigmoid output per emotion so that several emotions can be recognised in a single face.", K.BLUE, "i"),
        ("The deliverable", "Mosaic: face detection, a CNN with 7 basic and 11 compound outputs, a conditional GAN that synthesises compound-emotion training faces, a FastAPI service with accounts and history, and a web console, tested on FER2013 against a single-label baseline.", K.GREEN, "✓"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, H, t, body, col, gl, body_size=18)
    notes[3] = ("Three points: why single-label recognition is not enough, what the two-stage analysis-by-synthesis idea is, and what is delivered. "
                "At this stage these are the planned contributions; measurements come in Review 2.")

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base paper")
    wipe(s)
    K.box(s, 0.6, 1.4, 12.13, 1.1, fill=K.CARD)
    K.text(s, 0.82, 1.48, 11.7, 0.95, F.BASE_PAPER, size=13, color=K.INK, anchor="m")
    cw = 3.85
    cards = [
        ("Method", "cEmoGANs: an encoder gives latent codes that keep the face identity, and a conditional GAN takes a six-dimensional multi-hot emotion label to draw faces with two emotions at once. A small CNN with sigmoid outputs is then trained on the generated images (multi-label).", K.BLUE, "M"),
        ("Reported results", "On CK+, JAFFE and MUG the recogniser scores f-beta 0.99, 0.99 and 0.80 and exact-match ratios of 100 %, 99 % and 68.7 %, against 0.45, 0.60 and 0.51 for an EfficientNet-B0 baseline. Identity similarity above 0.7 holds for 98 %, 94 % and 99 % of generated faces.", K.GREEN, "R"),
        ("Relevance and limits", "Mosaic follows the same two stages. The scores are measured on images generated by the same cEmoGANs (7:3 split of 15,000), and real photographs are shown only qualitatively; the datasets are small laboratory sets. This project tests the idea on a larger, in-the-wild set.", K.ORANGE, "L"),
    ]
    for i, (t, b_, col, gl) in enumerate(cards):
        K.card(s, 0.6 + i * (cw + 0.29), 2.75, cw, 4.1, t, b_, col, gl, body_size=15)
    notes[4] = ("Read the citation. Every figure on this slide is printed in the paper (Table 5 and Section IV-B2). Note the evaluation protocol: the test split is drawn from generated images, "
                "so it measures how well the recogniser reads the generator's labels. The authors themselves flag demographic bias and multimodal cues as future work.")

    # ---- 5 literature survey table
    s = S[4]
    set_title(s, "Literature survey")
    wipe(s)
    keep = [r for r in lit.LIT_TABLE if f"[{R['migan']}]" not in r[0] and f"[{R['facecycle']}]" not in r[0] and f"[{R['su']}]" not in r[0]]
    rows = [["Work", "Year", "Approach", "Reported result / limitation"]] + keep
    K.table(s, 0.6, 1.2, [2.5, 0.6, 4.6, 4.43], rows, font_size=10.5, row_h=0.6, header_size=11.5, align=["l", "c", "l", "l"])
    K.text(s, 0.6, 6.55, 12.13, 0.35, f"Batch survey items [{R['migan']}] and [{R['facecycle']}] are known by title and record only; their results could not be verified and are not quoted.", size=11, color=K.TXT, italic=True)
    notes[5] = ("The batch survey lists the base paper plus four GAN-based recognisers; the table adds the papers kept in the archived folder and the sources of the compound categories and labels. "
                "Results are quoted only where we read them in the paper or its abstract.")

    # ---- 6 supporting evidence (chart + list)
    s = S[5]
    set_title(s, "Supporting evidence from the literature")
    wipe(s)
    gf = K.bar_chart(s, 0.6, 1.35, 7.0, 4.95, ["CK+", "JAFFE", "MUG"],
                     [("EfficientNet-B0 (basic-emotion baseline)", [0.45, 0.60, 0.51]), ("Same CNN, StyleGAN images", [0.42, 0.54, 0.53]), ("Same CNN, cEmoGAN images", [0.99, 0.99, 0.80])],
                     colors=[K.TXT, K.ORANGE, K.BLUE], number_format="0.00", font_size=11, max_value=1.15, label_size=10)
    K.text(s, 0.6, 6.35, 7.0, 0.7, "f-beta on the base paper's complex-emotion test sets (its Table 5). The test images are generated by each method itself, so the bars compare generators, not recognition on real photographs.", size=11.5, color=K.TXT, italic=True)
    K.text(s, 7.9, 1.45, 4.85, 5.4, [
        ("**What the literature shows**", {"space_after": 8}),
        (f"Training on cEmoGAN images beats StyleGAN images and a basic-emotion CNN on mixed labels [{R['base']}].", {"bullet": True, "space_after": 8}),
        (f"On unconstrained FER-2013 a light CNN reaches only 51.6 % accuracy, against 96.9 % on CK+ [{R['galkaduwa']}].", {"bullet": True, "space_after": 8}),
        (f"Real compound labels exist in RAF-DB; ViT, PosterV2 and ResNet reach 60-64 % accuracy on seven compound classes [{R['abaw7']}].", {"bullet": True, "space_after": 8}),
        (f"Mixed emotions follow the compound categories of Du, Tao and Martinez [{R['du2014']}].", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[6] = ("The chart is the base paper's headline result. The bullets give two sobering reference points: in-the-wild basic recognition is far from lab-set numbers, and real compound recognition is hard even with real labels.")

    # ---- 7 existing system
    s = S[6]
    set_title(s, "Existing system and current approaches")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.1, [("Face image", K.NAVY), ("Basic-emotion CNN trained on FER-2013 or CK+", K.NAVY), ("One label out of six or seven", K.NAVY), ("Mixed expression is lost", K.NAVY)], size=14, gap=0.5)
    K.card(s, 0.6, 2.95, 5.95, 3.8, "Single-label recognisers",
           f"Convolutional networks classify seven basic emotions on FER-2013-style data [{R['fer2013']}], [{R['galkaduwa']}]; surveys of the field are in [{R['lideng']}].\nAugmentation is usually flips, crops and rotations, which do not create new expressions.", K.BLUE, "1", body_size=17)
    K.card(s, 6.78, 2.95, 5.95, 3.8, "Generative and disentangling methods",
           f"GANs separate identity from expression or edit expressions [{R['cdgan']}], [{R['nstgan']}], [{R['stargan']}], [{R['ganimation']}]; the base paper adds conditional generation of mixed emotions [{R['base']}].\nMost still output a single basic label per image.", K.ORANGE, "2", body_size=17)
    notes[7] = "Today's deployed systems return one basic label. Generative work mostly improves single-label recognition or edits expressions; mixed-emotion generation for training is the base paper's contribution."

    # ---- 8 limitations
    s = S[7]
    set_title(s, "Limitations of existing methods")
    wipe(s)
    heads = ["Single label per face", "Scarce mixed-emotion data", "Basic augmentation", "Identity and real-world drift"]
    bodies = [
        "Systems cannot report mixed or complex emotions; a smile with raised brows is forced into one class.",
        f"Compound-labelled sets are small: RAF-DB has about 3,954 compound-expression images among roughly 30,000 [{R['abaw7']}].",
        "Flips, crops and rotations do not create new expressions, so the minority compound classes stay unseen.",
        f"Expression-editing GANs can distort the face, and accuracy falls from laboratory to in-the-wild data (51.6 % on FER-2013 for a light CNN) [{R['galkaduwa']}].",
    ]
    for i in range(4):
        r, c = divmod(i, 2)
        K.card(s, 0.6 + c * 6.18, 1.45 + r * 2.35, 5.95, 2.15, heads[i], bodies[i], C[i], str(i + 1), body_size=16)
    K.box(s, 0.6, 6.25, 12.13, 0.75, fill=K.CARD)
    K.text(s, 0.85, 6.25, 11.7, 0.75, f"Survey items known by title only are not quoted [{R['migan']}], [{R['facecycle']}]. Accuracy on a clean laboratory set is not evidence for performance on everyday photographs.", size=13, color=K.INK, anchor="m")
    notes[8] = "The first two limitations are the batch's own; the third and fourth are supported by the cited papers."

    # ---- 9 research gap
    s = S[8]
    set_title(s, "Research gap")
    wipe(s)
    for i, g in enumerate(lit.GAPS):
        y = 1.4 + i * 1.75
        K.circle(s, 0.6, y + 0.35, 0.7, C[i % 4], str(i + 1), 20)
        K.text(s, 1.6, y, 11.1, 1.6, g, size=17, color=K.INK, anchor="m")
    K.box(s, 0.6, 6.5, 12.13, 0.6, fill=K.FHEAD, line=None)
    K.text(s, 0.85, 6.5, 11.6, 0.6, "Gap addressed here: generate, train and serve compound-emotion recognition, and measure it against a single-label baseline.", size=14, color=K.INK, anchor="m", bold=True)
    notes[9] = "Gap 1 is the batch survey's own statement. Gaps 2 and 3 come from reading the base paper's protocol: scores on generated data and no isolation of the synthetic images' contribution."

    # ---- 10 problem statement
    s = S[9]
    set_title(s, "Problem statement")
    wipe(s)
    K.box(s, 0.6, 1.45, 12.13, 3.1, fill=K.CARD)
    K.text(s, 0.95, 1.6, 11.45, 2.85, [(p, {"bullet": True, "space_after": 8}) for p in lit.PROBLEM_STATEMENT], size=18, color=K.INK, anchor="m")
    for i, (t, b_) in enumerate([("Input", "A photograph (upload or webcam frame) containing a face"),
                                 ("Output", "Scores for 7 basic and 11 compound emotions, the dominant emotion, and a saved history for signed-in users"),
                                 ("Measures", "Accuracy and macro-F1 against a single-label baseline, per-class scores, and the effect of the synthetic images")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 4.8, 3.85, 1.95)
        K.text(s, x + 0.25, 4.9, 3.4, 0.4, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 5.35, 3.4, 1.35, b_, size=15, color=K.TXT)
    notes[10] = f"Read the statement slowly. The need, in the batch's words: {lit.NEED}"

    # ---- 11 objectives
    s = S[10]
    set_title(s, "Objectives")
    wipe(s)
    K.text(s, 0.6, 1.4, 12.13, 4.9, [(f"{i}.  {o}", {"space_after": 14}) for i, o in enumerate(lit.OBJECTIVES, 1)], size=22, color=K.INK)
    K.text(s, 0.6, 6.35, 12.13, 0.7, "How far each objective is met will be reported in Review 2 and the final review, including any that are only partly achieved.", size=14, color=K.TXT, italic=True)
    notes[11] = "The five objectives from the proposal. Later reviews report honestly which were met."

    # ---- 12 proposed approach
    s = S[11]
    set_title(s, "Proposed approach")
    wipe(s)
    cw = 2.88
    for i, (t, b_, col, gl) in enumerate([
        ("Detect", "An OpenCV Haar cascade finds the largest face in the photo and crops it to grayscale; no face means an empty result instead of a guess.", K.BLUE, "1"),
        ("Generate", "A conditional GAN, trained on real faces, is given two emotions at once to synthesise compound-emotion faces for the 11 compound classes.", K.GREEN, "2"),
        ("Recognise", "A CNN with 18 sigmoid outputs (7 basic + 11 compound) is trained on real basic-labelled faces plus the synthetic compound faces.", K.ORANGE, "3"),
        ("Serve", "A FastAPI service returns sorted basic and compound scores and the dominant emotion, and keeps a per-user history in SQLite.", K.PURPLE, "4"),
    ]):
        K.card(s, 0.6 + i * (cw + 0.2), 1.45, cw, 3.7, t, b_, col, gl, body_size=15)
    K.box(s, 0.6, 5.35, 12.13, 1.4)
    K.circle(s, 0.85, 5.65, 0.7, K.NAVY, "UI", 16)
    K.text(s, 1.8, 5.5, 10.7, 0.45, "Next.js console: upload or webcam, emotion charts, history", size=16, color=K.INK, bold=True)
    K.text(s, 1.8, 5.95, 10.7, 0.75, "Runs on a single CPU machine, uses public data (FER2013) and calls no external service; the GAN is used only to build training data.", size=14, color=K.TXT)
    notes[12] = "Four stages and the console that wraps them. The generator is a training-time tool; only the recogniser is served."

    # ---- 13 architecture
    s = S[12]
    set_title(s, "High-level proposed architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "r1_01"), 0.5, 1.2, 8.4, 5.9)
    K.text(s, 9.1, 1.5, 3.7, 5.2, [
        ("**Four tiers**", {"space_after": 8}),
        (f"Browser: Next.js console (port {F.WEB_PORT}).", {"bullet": True}),
        ("FastAPI service: accounts, analysis and history endpoints with token checks.", {"bullet": True}),
        ("ML modules: face detector, 18-output CNN, and a conditional GAN used only for training.", {"bullet": True}),
        ("State: SQLite database, model checkpoints and face thumbnails; nothing leaves the machine.", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[13] = "Follow the diagram top to bottom: the console calls the API, the API runs detection and classification, results are stored locally."

    # ---- 14 expected outcomes
    s = S[13]
    set_title(s, "Expected outcomes and contributions")
    wipe(s)
    heads = ["Working product", "Fair comparison", "Synthetic-data study", "Honest reporting", "Stated limits"]
    bodies = [
        "Target: a web application that analyses an uploaded photo and shows basic and compound emotion scores and a saved history.",
        "Target: accuracy and macro-F1 of the multi-label model compared with a single-label baseline on the FER2013 test set.",
        "Target: a controlled comparison with and without the generated compound faces, repeated over several seeds.",
        "Target: every figure measured on this project's own runs; gaps stated plainly, including where no real labels exist.",
        "Expected limits: FER2013 has no compound labels, the GAN is small and CPU-trained, and the face detector may miss small faces.",
    ]
    for i, (h, b_) in enumerate(zip(heads, bodies)):
        if i < 3:
            K.card(s, 0.6 + i * 4.14, 1.5, 3.85, 2.65, h, b_, C[i % 4], str(i + 1), body_size=16)
        else:
            K.card(s, 0.6 + (i - 3) * 6.18, 4.35, 5.95, 2.4, h, b_, C[i % 4], str(i + 1), body_size=17)
    notes[14] = "These are targets set at the proposal stage, not results. The measured results, including where they fall short, are presented in Review 2."

    # ---- 15 references
    s = S[14]
    set_title(s, "References")
    wipe(s)
    idx = [R[k] for k in ("base", "cdgan", "migan", "nstgan", "facecycle", "galkaduwa", "abaw7", "du2014", "fer2013", "lideng")]
    K.text(s, 0.6, 1.25, 12.13, 5.8, [(f"[{n}] {REFS[n - 1]}".replace("*", ""), {"space_after": 6}) for n in idx], size=13, color=K.INK)
    notes[15] = "Selected references; the complete numbered list, with notes on how each entry was checked, is in the project report."

    # ---- 16 thank you
    thank_you(S[15])
    notes[16] = ("Likely questions: why a small CNN rather than the base paper's encoder-decoder cEmoGANs (CPU-only training, public data); how compound outputs can be evaluated without compound labels "
                 "(this is reported honestly in Review 2); why FER2013 rather than CK+, JAFFE and MUG (open, larger, in-the-wild).")

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "7.Review_1_PPT.pptx")))
