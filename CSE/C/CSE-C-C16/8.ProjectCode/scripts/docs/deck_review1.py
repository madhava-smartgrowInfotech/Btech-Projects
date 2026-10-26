"""7.Review_1_PPT.pptx: 16 slides, problem identification and research. Built from D:\\abstracts\\Templates\\Review_1_PPT.pptx."""

import os

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K
from .lit import GAP, NEED, OBJECTIVES, PROBLEM_STATEMENT
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
                K.replace_text(sh, f"{F.PRODUCT}  \u00b7  {review_label}")
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
            K.replace_text(sh, F.TITLE, 28)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 18)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS), 14)
        elif nm == "Text 6":
            K.replace_text(sh, f"{F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  \u00b7  Batch {F.BATCH_NO} ({F.SECTION})  \u00b7  {F.YEAR}")


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
    title_slide(S[0], "A leaf-photograph diagnosis web application with knowledge-based treatment advice in English, Hindi and Marathi",
                "REVIEW 1  \u00b7  PROBLEM IDENTIFICATION AND RESEARCH")
    notes[1] = ("Introduce the team and the title. One sentence: a farmer photographs a leaf, chooses the crop and receives the likely disease, how severe it is, "
                "and what to do about it, in a web application that also runs on a modest laptop.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Abstract and overview"), ("02", "Base paper"), ("03", "Literature survey and evidence"), ("04", "Existing approaches and limitations"),
               ("05", "Research gap"), ("06", "Problem statement and objectives"), ("07", "Proposed approach and architecture"),
               ("08", "Expected outcomes"), ("09", "References")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda. This review is about why the problem matters and what is missing in current work; measured results come in the later reviews."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract: from a leaf photograph to treatment advice")
    wipe(s)
    W = 3.85
    for i, (t, body, col, gl) in enumerate([
        ("The problem", "Crop disease cuts yield and income, and farmers often cannot identify it early. Expert advice is not at hand when the decision is needed, and many tools only classify the disease or speak only English.", K.ORANGE, "!"),
        ("Our idea", "Let the farmer upload a leaf photo and choose the crop. A diagnosis engine names the disease, and a knowledge base returns severity, chemical, organic and cultural treatment and prevention advice.", K.BLUE, "i"),
        ("The deliverable", "AgriVision: a web application with sign-in, scan history, CSV and PDF reports, a dashboard and analytics, a disease guide for 38 classes, and an interface in English, Hindi and Marathi.", K.GREEN, "\u2713"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.9, t, body, col, gl, body_size=20)
    notes[3] = "Three points: the problem, the diagnose-then-advise idea, and the deliverable, a complete application and not only a model script."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base paper")
    wipe(s)
    K.box(s, 0.6, 1.4, 12.13, 1.1, fill=K.CARD)
    K.text(s, 0.82, 1.48, 11.7, 0.95, F.BASE_PAPER, size=14, color=K.INK, anchor="m")
    cw = 3.85
    cards = [
        ("Method", "Foliagen builds annotated foliage images from single-leaf photos: background removal, leaves placed by plant structure, a chosen share of diseased leaves. The images train and fine-tune known classifiers.", K.BLUE, "M"),
        ("Data and reported results", "Soybean and tomato, from ASDID, a Kaggle soybean set and PlantVillage. Adding 5 % of a natural foliage set to the generated data reaches up to 98 % accuracy on natural foliage; trained on GPUs.", K.GREEN, "R"),
        ("What we take, what differs", "Taken: the point that field images matter and that data scarcity is the obstacle. Different: we do not generate images; we join classification to actionable, multilingual advice in an application.", K.ORANGE, "L"),
    ]
    for i, (t, b_, col, gl) in enumerate(cards):
        K.card(s, 0.6 + i * (cw + 0.29), 2.75, cw, 4.1, t, b_, col, gl, body_size=17)
    notes[4] = ("Read the citation. The base paper is about creating training data for in-field classification, not about advice. The batch note states the gap we address: "
                "reliable classification joined to treatment and fertiliser advice in the farmer's language. Numbers will not be comparable with ours: task, crops, data and hardware differ.")

    # ---- 5 literature survey table
    s = S[4]
    set_title(s, "Literature survey")
    wipe(s)
    rows = [["Work", "Approach", "Data", "Reported result"],
            ["Pakka et al. 2026 [1] (base)", "Foliagen: generated foliage images train classifiers", "Soybean and tomato leaf sets, UAV foliage set", "Up to 98 % accuracy with 5 % real foliage added"],
            ["Sherifi et al. 2026 [2]", "PD36-C: compact 1.25 M-parameter CNN, offline desktop app", "87 k lab-style images, 38 classes", "99.53 % test accuracy"],
            ["Kanakala and Ningappa 2025 [3]", "CNN and LSTM leaf classifiers", "70,295 train / 17,572 validation, 38 classes", "CNN 96.4 % validation, LSTM 93.43 %"],
            ["Singh et al. 2020 [4]", "PlantDoc: field photographs, benchmark CNNs", "2,598 web photos, 27 classes", "44.5 to 70.5 % (cropped), 13.7 to 29.7 % (raw)"],
            ["Mohanty et al. 2016 [6]", "AlexNet, GoogLeNet on PlantVillage", "54 k lab images, 38 classes", "99.35 % on held-out lab images"],
            ["Barbedo 2018 [8]", "Why deep models fail on new conditions", "Review and tests", "Accuracy drops without varied training data"]]
    K.table(s, 0.6, 1.4, [2.7, 3.9, 3.0, 2.53], rows, font_size=12, row_h=0.72, header_size=13)
    notes[5] = ("The pattern: models on clean laboratory images report 96 to 99 percent; the one field-photo benchmark, PlantDoc, shows far lower numbers. "
                "None of the surveyed works delivers treatment advice in several languages. Four further 2024 to 2026 sources named in the batch survey could not be verified and are listed as such in the report.")

    # ---- 6 supporting evidence (chart)
    s = S[5]
    set_title(s, "Supporting evidence: field photographs are much harder")
    wipe(s)
    gf = K.bar_chart(s, 0.6, 1.4, 7.9, 5.4,
                     ["PlantVillage\nGoogLeNet / AlexNet\n[6]", "PD36-C\n87 k lab-style\n[2]", "CNN validation\n70 k images\n[3]", "PlantDoc\ncropped leaves\nbest [4]", "PlantDoc\nraw photos\nVGG16 best [4]"],
                     [("Reported accuracy, %", [99.35, 99.53, 96.4, 70.53, 29.73])], colors=[K.BLUE], number_format="0.0", font_size=12, max_value=115)
    for idx in (3, 4):
        pt = gf.chart.plots[0].series[0].points[idx]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = K.ORANGE
    K.card(s, 8.8, 1.45, 3.93, 2.65, "Takeaway", "Laboratory-style leaf images give accuracy near 99 %. The same kind of model on web-scraped field photos falls to 30 to 70 %, so a farmer-facing tool must be judged on field photos.", K.GREEN, "\u2191", body_size=14)
    K.card(s, 8.8, 4.25, 3.93, 2.55, "Caveat", "Figures are as printed in each paper, on different data and splits; they are not a ranking. Our own measurements follow in the later reviews.", K.ORANGE, "!", body_size=14)
    notes[6] = ("Values quoted from the papers: 99.35 percent (Mohanty), 99.53 (PD36-C), 96.4 validation (Kanakala and Ningappa), 70.53 and 29.73 (PlantDoc benchmark). "
                "The point is that the data decides the number, so we plan to evaluate on PlantDoc, the field-photo set.")

    # ---- 7 existing system
    s = S[6]
    set_title(s, "Existing system and current approaches")
    wipe(s)
    K.flow(s, 0.6, 1.55, 12.13, 1.1, [("Spots appear on leaves", K.NAVY), ("Farmer guesses or waits", K.NAVY), ("Expert visit, if any", K.NAVY), ("Treatment, often late", K.NAVY)], size=16, gap=0.5)
    K.card(s, 0.6, 3.1, 5.95, 3.7, "Visual scouting and expert advice", "Accurate when an agronomist is present, but experts are rarely available at the right place and time, and the delay lets the disease spread through the field.", K.BLUE, "1", body_size=17)
    K.card(s, 6.78, 3.1, 5.95, 3.7, "Automatic leaf classifiers", "CNN classifiers name the disease from a photo, but most stop there: no treatment guidance, English-only text, and training on clean laboratory images.", K.ORANGE, "2", body_size=17)
    notes[7] = "Today's path is scouting and occasional expert visits. Automatic classifiers exist, but they classify and do not advise."

    # ---- 8 limitations
    s = S[7]
    set_title(s, "Limitations of existing methods")
    wipe(s)
    items = [
        ("Late identification", "Farmers cannot identify disease early enough to prevent yield loss.", K.ORANGE, "1"),
        ("No expert at hand", "Agricultural expertise is not available at the time and place the decision is needed.", K.BLUE, "2"),
        ("Classification only", "Existing tools classify disease but provide no treatment guidance.", K.GREEN, "3"),
        ("Language and field gap", "Advice only in English is unusable for many farmers, and models trained on laboratory images do not carry over to field photographs.", K.PURPLE, "4"),
    ]
    for i, (t, b_, col, gl) in enumerate(items):
        r, c = divmod(i, 2)
        K.card(s, 0.6 + c * 6.18, 1.5 + r * 2.7, 5.95, 2.5, t, b_, col, gl, body_size=17)
    notes[8] = "Four limitations from the problem statement and the survey. Each maps to a design decision: diagnosis plus advice, a three-language interface, and honest testing on field photos."

    # ---- 9 research gap
    s = S[8]
    set_title(s, "Research gap")
    wipe(s)
    gaps = [("Advice, not just labels", "Surveyed work addresses leaf image generation and classification; treatment and fertiliser advice is left out."),
            ("Local language", "Interfaces and advice are usually English only; Hindi and Marathi readers are not served."),
            ("Field photographs", "Reliable classification on web or phone photographs is much harder than on laboratory sets and must be measured."),
            ("One usable tool", "Diagnosis, advice, history and reports are rarely joined in one application that runs on modest hardware."),
            ("Honest evaluation", "Scores are rarely given per class, with baselines, seeds and the cost of running the system.")]
    for i, (k, v) in enumerate(gaps):
        y = 1.45 + i * 1.08
        K.box(s, 0.6, y, 2.8, 0.9, fill=K.NAVY, line=None, radius=0.06)
        K.text(s, 0.6, y, 2.8, 0.9, k, size=16, color=K.WHITE, bold=True, align="c", anchor="m")
        K.text(s, 3.7, y, 9.0, 0.9, v, size=17, color=K.INK, anchor="m")
    notes[9] = "The batch survey states the gap as: " + GAP

    # ---- 10 problem statement
    s = S[9]
    set_title(s, "Problem statement")
    wipe(s)
    K.box(s, 0.6, 1.45, 12.13, 2.75, fill=K.CARD)
    K.text(s, 0.95, 1.6, 11.45, 2.5, PROBLEM_STATEMENT, size=18, color=K.INK, anchor="m")
    for i, (t, b_) in enumerate([("Input", "One leaf photo (JPG, PNG, WEBP, up to 10 MB) and the crop"), ("Output", "Disease or healthy, top-3 list, severity, treatments, prevention"), ("Record", "Scan history, CSV and PDF reports, dashboard and analytics")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 4.5, 3.85, 1.5)
        K.text(s, x + 0.25, 4.62, 3.4, 0.4, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 5.1, 3.4, 0.8, b_, size=14, color=K.TXT)
    K.text(s, 0.6, 6.2, 12.13, 0.7, "Need: " + NEED, size=14, color=K.TXT, italic=True)
    notes[10] = "Read the statement slowly. Input is one photo and a crop; output is a diagnosis with advice; and the system keeps a history. The last clause matters: we promise to report accuracy on field photographs honestly."

    # ---- 11 objectives
    s = S[10]
    set_title(s, "Objectives")
    wipe(s)
    K.text(s, 0.6, 1.4, 12.13, 5.4, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate(OBJECTIVES, 1)], size=21, color=K.INK)
    notes[11] = "The six objectives from the proposal. The later reviews report which were met."

    # ---- 12 proposed approach
    s = S[11]
    set_title(s, "Proposed approach")
    wipe(s)
    cw = 2.88
    for i, (t, b_, col, gl) in enumerate([
        ("Capture", "The farmer uploads a leaf photo (or uses the camera) and picks the crop, which narrows the candidate diseases.", K.BLUE, "1"),
        ("Diagnose", "A diagnosis engine scores the 38 classes of the label set and returns a top-3 list. A CNN trained on PlantDoc is the planned engine.", K.GREEN, "2"),
        ("Advise", "A knowledge base returns symptoms, lifecycle, severity, and chemical, organic and cultural treatment with prevention.", K.ORANGE, "3"),
        ("Deliver", "A web interface in English, Hindi and Marathi with history, CSV and PDF export, dashboard and analytics.", K.PURPLE, "4"),
    ]):
        K.card(s, 0.6 + i * (cw + 0.2), 1.45, cw, 3.6, t, b_, col, gl, body_size=15)
    K.box(s, 0.6, 5.3, 12.13, 1.5)
    K.circle(s, 0.85, 5.6, 0.7, K.NAVY, "W", 18)
    K.text(s, 1.8, 5.5, 10.7, 0.5, "Application", size=17, color=K.INK, bold=True)
    K.text(s, 1.8, 6.0, 10.7, 0.75, "AgriVision: a React web app over a FastAPI service, a Python diagnosis module and a SQLite database. One command (run.bat) starts it on a Windows laptop with no GPU.", size=15, color=K.TXT)
    notes[12] = "Four steps from photo to advice, and the application around them. The diagnosis engine is the part to be measured honestly; the advice comes from a curated knowledge base."

    # ---- 13 architecture
    s = S[12]
    set_title(s, "High-level proposed architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 2.9, 1.3, 7.5, 5.3)
    K.text(s, 0.6, 6.62, 12.13, 0.3, "Browser UI, FastAPI service, the diagnosis and knowledge modules, SQLite and the image store", size=12, color=K.TXT, align="c", italic=True)
    notes[13] = "Follow the diagram: the browser calls the FastAPI service, which uses the diagnosis and knowledge modules and stores scans in SQLite and images on disk."

    # ---- 14 expected outcomes
    s = S[13]
    set_title(s, "Expected outcomes and contributions")
    wipe(s)
    outs = [("Working application", "Sign-in, diagnosis, advice, history, exports and analytics running locally.", K.BLUE, "1"),
            ("Advice for 38 classes", "A knowledge base of symptoms, severity and treatments for the label set.", K.GREEN, "2"),
            ("Trained classifier", "A CNN trained on PlantDoc, scored on a held-out test split, per class and over several seeds.", K.ORANGE, "3"),
            ("Three-language interface", "English, Hindi and Marathi interface strings; advice text may stay English at first.", K.PURPLE, "4"),
            ("Honest evaluation", "Baselines, per-class scores and run cost reported, including any shortfall.", K.BLUE, "5"),
            ("Tested code", "Automated tests of the API, the knowledge base and the edge cases.", K.GREEN, "6")]
    for i, (t, b_, col, gl) in enumerate(outs):
        r, c = divmod(i, 3)
        K.card(s, 0.6 + c * 4.14, 1.5 + r * 2.7, 3.85, 2.5, t, b_, col, gl, body_size=16)
    notes[14] = "These are targets, not results. Field-photo accuracy is expected to be much lower than the laboratory numbers in the literature, and we will report whatever the held-out test data shows."

    # ---- 15 references
    s = S[14]
    set_title(s, "References")
    wipe(s)
    idx = [1, 2, 3, 4, 5, 6, 8, 9]
    K.text(s, 0.6, 1.35, 12.13, 5.5, [(f"[{n}] {REFS[n - 1]}", {"space_after": 5}) for n in idx], size=13, color=K.INK)
    notes[15] = "Selected references; the complete numbered list is in the project report."

    # ---- 16 thank you
    thank_you(S[15])
    notes[16] = "Likely questions: why a heuristic or CNN; why PlantDoc; how the advice is validated; why only three interface languages."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "7.Review_1_PPT.pptx")))
