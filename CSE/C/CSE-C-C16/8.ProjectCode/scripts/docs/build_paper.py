"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for AgriVision (batch C16) from facts.py (experiments/plantdoc/*.json), the diagrams and the screenshots.
Format per DOCS_PROMPT.md section 7.

    python -m scripts.docs.build_paper            # from 8.ProjectCode, system python
"""

import os

from PIL import Image

from . import facts as F
from .paper import Paper

HC, HG, H0, C, CS, CT, MB, BL = F.HC, F.HG, F.H0, F.C, F.CS, F.CT, F.MB, F.BL
RF, LR = BL["random_forest"], BL["logistic_regression"]
NAVY, BLUE, TEAL, ORANGE, PURPLE, GREEN, GREY = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#2F8F4E", "#8A97A8"


def R(*n):
    """Citation marker understood by Paper.expand: R(1, 2) -> '{r:1,2}'."""
    return "{r:" + ",".join(str(x) for x in n) + "}"


def pc(x, d=1):
    return f"{x * 100:.{d}f} %"


# ------------------------------------------------------------------------------------------------ figures
def make_figures():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 7.5, "axes.spines.top": False, "axes.spines.right": False})
    out = {}

    def bx(ax, cx, cy, w, h, t, c, fs=6.2):
        ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=c, ec=c, zorder=2))
        ax.text(cx, cy, t, ha="center", va="center", color="white", fontsize=fs, zorder=3, linespacing=1.15)

    def ar(ax, x1, y1, x2, y2, c="#334455"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=c, lw=0.9, shrinkA=0, shrinkB=0), zorder=4)

    # --- Fig. 1 architecture
    fig, ax = plt.subplots(figsize=(3.4, 2.55))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 78)
    ax.axis("off")
    tiers = [(66, "Browser: React 18 + Vite, 12 page components", BLUE, ["Detect", "Result", "History", "Analytics"]),
             (41, "FastAPI service: 16 routes under /api", GREEN, ["/auth, /profile", "/detect/upload", "/history, export", "/dashboard"]),
             (16, "Original Flask product agrivision/", ORANGE, ["inference.py", "disease_db.py", "app.py init_db", "train.py (offline)"])]
    for cy, title, c, items in tiers:
        ax.add_patch(FancyBboxPatch((1, cy - 10), 98, 21, boxstyle="round,pad=0,rounding_size=1.5", fc="#F1F5FA", ec=c, lw=1.2, zorder=1))
        ax.text(3, cy + 7.5, title, fontsize=6.6, color="#14213D", fontweight="bold", va="center")
        for i, t in enumerate(items):
            bx(ax, 14 + i * 24, cy - 2, 21.5, 9, t, c, fs=5.8)
    ar(ax, 50, 55, 50, 52)
    ar(ax, 50, 30, 50, 27)
    ax.text(52, 53.5, "JSON / multipart over HTTP", fontsize=5.6, va="center")
    ax.text(52, 28.5, "Python imports", fontsize=5.6, va="center")
    ax.text(50, 1.2, "SQLite (users, results) + uploads/ image folder", fontsize=5.8, ha="center", va="center", color="#14213D")
    p = os.path.join(F.FIGS, "paper_arch.png")
    fig.savefig(p, dpi=220, bbox_inches="tight")
    plt.close(fig)
    out["arch"] = p

    # --- Fig. 2 main flow
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 74)
    ax.axis("off")
    row1 = [("Photo +\ncrop choice", BLUE), ("Checks:\ntoken, type,\n10 MB", GREEN), ("Resize 256,\ncolour and\ntexture\nfeatures", GREEN), ("Candidate\nclasses of\nthe crop", GREEN)]
    for i, (t, c) in enumerate(row1):
        bx(ax, 12.5 + i * 25, 58, 20.5, 19, t, c, fs=6)
        if i:
            ar(ax, 12.5 + i * 25 - 12.4, 58, 12.5 + i * 25 - 10.4, 58)
    row2 = [("Save scan\n+ image,\nshow result", NAVY), ("Knowledge\ncard: severity,\n3 treatments", PURPLE), ("Score, rank,\ntop-3 +\nconfidence", ORANGE)]
    for i, (t, c) in enumerate(row2):
        bx(ax, 12.5 + i * 25, 28, 20.5, 19, t, c, fs=6)
    for i in range(2):
        ar(ax, 12.5 + (i + 1) * 25 - 10.4, 28, 12.5 + (i + 1) * 25 - 12.4, 28)
    ar(ax, 87.5, 48.5, 62.5, 37.5, "#D9772F")
    bx(ax, 87.5, 28, 21, 19, "< 3 candidates:\nIndexError ->\nHTTP 400", "#B03A2E", fs=5.8)
    ax.text(50, 5.5, "Heuristic engine as shipped; a Keras model, if one is installed,\nreplaces the three middle boxes", ha="center", fontsize=5.8, color="#14213D")
    p = os.path.join(F.FIGS, "paper_flow.png")
    fig.savefig(p, dpi=220, bbox_inches="tight")
    plt.close(fig)
    out["flow"] = p

    # --- Fig. 3 results chart
    rows = [("Heuristic engine (crop chosen)", HC["accuracy"]["mean"], HC["accuracy"]["std"], GREY),
            ("Heuristic engine (crop 'general')", HG["accuracy"]["mean"], HG["accuracy"]["std"], GREY),
            ("Compact CNN of train.py", C["accuracy"]["mean"], C["accuracy"]["std"], ORANGE),
            ("Logistic regression (colour/texture)", LR["accuracy"], 0, TEAL),
            ("Random forest (colour/texture)", RF["accuracy"], 0, TEAL),
            ("MobileNetV2, head only", MB["head_only_accuracy"]["mean"], MB["head_only_accuracy"]["std"], PURPLE),
            ("MobileNetV2, fine-tuned", MB["accuracy"]["mean"], MB["accuracy"]["std"], PURPLE)]
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    n = len(rows)
    for i, (name, m, s, c) in enumerate(rows):
        y = n - 1 - i
        ax.barh(y, m * 100, color=c, height=0.62, xerr=s * 100 if s else None, error_kw=dict(lw=0.8, capsize=1.5))
        ax.text(m * 100 + s * 100 + 1.0, y, f"{m * 100:.1f}", va="center", fontsize=6.8)
    ax.axvline(F.H["chance_general"] * 100, color="#B03A2E", ls="--", lw=0.8)
    ax.axvline(F.H["majority_class_test"] * 100, color=NAVY, ls=":", lw=0.8)
    ax.set_yticks(range(n))
    ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=6.6)
    ax.set_xlim(0, 62)
    ax.set_xlabel("Top-1 accuracy on the 236 test photos, %  (dashed: chance 2.6; dotted: majority class 5.1)", fontsize=6.2)
    p = os.path.join(F.FIGS, "paper_results.png")
    fig.savefig(p, dpi=220, bbox_inches="tight")
    plt.close(fig)
    out["results"] = p

    # --- per-class F1 chart
    mbp, cnp = MB["first_run"]["per_class"], C["first_run"]["per_class"]
    names = sorted([n for n in mbp if mbp[n]["support"] > 0], key=lambda n: mbp[n]["f1"])
    short = lambda n: (n.replace("_leaf", "").replace("Tomato_", "Tom. ").replace("Potato_", "Pot. ").replace("Corn_", "Corn ").replace("Apple_", "Apple ").replace("Bell_pepper", "Pepper")
                       .replace("_", " ").replace("Squash Powdery mildew", "Squash mildew").replace("Soyabean", "Soybean").replace("Strawberry", "Strawb.").strip())
    fig, ax = plt.subplots(figsize=(3.4, 3.7))
    y = range(len(names))
    ax.barh([i + 0.2 for i in y], [mbp[n]["f1"] for n in names], 0.38, color=PURPLE, label="MobileNetV2")
    ax.barh([i - 0.2 for i in y], [cnp[n]["f1"] for n in names], 0.38, color=ORANGE, label="Compact CNN")
    ax.set_yticks(list(y))
    ax.set_yticklabels([short(n) or n for n in names], fontsize=5.2)
    ax.set_xlim(0, 1.0)
    ax.tick_params(axis="x", labelsize=6)
    ax.set_xlabel("F1 on the test photographs (seed 42)", fontsize=6.2)
    ax.legend(frameon=False, fontsize=6, loc="lower right")
    p2 = os.path.join(F.FIGS, "paper_perclass.png")
    fig.savefig(p2, dpi=220, bbox_inches="tight")
    plt.close(fig)
    out["perclass"] = p2

    # --- confidence vs correctness
    hc = F.HCONF
    fig, ax = plt.subplots(figsize=(3.4, 1.7))
    labels = ["0.80-0.90", "0.90-0.95", "0.95-1.00"]
    vals = hc["acc_by_bin"][1:]
    cnts = hc["count_by_bin"][1:]
    ax.bar(range(3), vals, color=ORANGE, width=0.55)
    for i, (v, c) in enumerate(zip(vals, cnts)):
        ax.text(i, v + 0.6, f"{v:.0f} %  (n={c})", ha="center", fontsize=6.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels(labels, fontsize=6.5)
    ax.set_ylim(0, 32)
    ax.set_ylabel("top-1 correct, %", fontsize=6.5)
    ax.set_xlabel("confidence displayed by the application", fontsize=6.5)
    ax.tick_params(axis="y", labelsize=6)
    p3 = os.path.join(F.FIGS, "paper_confidence.png")
    fig.savefig(p3, dpi=220, bbox_inches="tight")
    plt.close(fig)
    out["confidence"] = p3

    # --- Fig. 4 / 5 screenshot crops legible at column width
    s08 = Image.open(F.shot("08_result.png")).convert("RGB")
    leaf = s08.crop((290, 150, 838, 515)).resize((260, 173))
    card = s08.crop((860, 160, 1410, 640))
    w = 520
    card = card.resize((w, int(card.height * w / card.width)))
    canvas = Image.new("RGB", (w, 173 + 8 + card.height), "white")
    canvas.paste(leaf, ((w - 260) // 2, 0))
    canvas.paste(card, (0, 181))
    p = os.path.join(F.FIGS, "paper_shot_result.png")
    canvas.save(p)
    out["shot_result"] = p
    s16 = Image.open(F.shot("16_error_blueberry.png")).convert("RGB")
    a = s16.crop((470, 312, 1215, 400))
    b = s16.crop((470, 845, 1215, 900))
    cv = Image.new("RGB", (a.width, a.height + b.height + 6), "white")
    cv.paste(a, (0, 0))
    cv.paste(b, (0, a.height + 6))
    cv = cv.crop((0, 0, 560, cv.height))
    p = os.path.join(F.FIGS, "paper_shot_error.png")
    cv.save(p)
    out["shot_error"] = p
    return out


# ------------------------------------------------------------------------------------------------ paper
def build(path):
    figs = make_figures()
    P = Paper()
    dept = "Dept. of Computer Science and Engineering"
    authors = [[f"{n} ({r})", dept, "[College name]", "[City], India", "[email address]"] for n, r in F.STUDENTS]
    authors.append([f"{F.GUIDE} (guide)", f"{F.GUIDE_DESIGNATION}, {dept}", "[College name]", "[City], India", "[email address]"])
    P.title_block("AgriVision: Leaf-Photograph Crop Disease Diagnosis with Treatment Advice, and a Measured Study of What Works on Field Photographs", authors)
    P.begin_two_columns()

    P.abstract(
        "Crop diseases cost farmers a large share of their harvest, and an expert is rarely at the field in time. This paper presents AgriVision, a web application in which a farmer "
        "uploads a leaf photograph, names the crop and receives the most likely disease, its severity and chemical, organic and cultural treatment advice for 38 classes, with the "
        "interface in English, Hindi and Marathi. The application is measured, not only described. On the PlantDoc field-photograph benchmark, with 2,342 training and "
        f"{F.NTEST} test photos, the colour and texture heuristic that the shipped application uses names the correct class for {pc(HC['accuracy']['mean'])} of photos when the crop is chosen, and fails "
        f"outright on {pc(HC['failed_share']['mean'])}. The compact CNN of the training script reaches {pc(C['accuracy']['mean'])}; a MobileNetV2 with ImageNet weights reaches "
        f"{pc(MB['accuracy']['mean'])} accuracy and macro-F1 {MB['macro_f1']['mean']:.2f} over three seeds, but is not yet installed in the application. We report these results, seven defects found by "
        "testing and code review, and the parts of the original plan (fertiliser, yield and weather advice) that are not implemented.",
        ["computer vision", "crop disease detection", "leaf images", "MobileNetV2", "PlantDoc", "transfer learning", "treatment advice"])

    # ---------------------------------------------------------------- I
    P.heading("I", "Introduction")
    P.para(f"Plant diseases are estimated to cost the world about USD 220 billion a year {R(1, 2)}. A farmer who sees spots on a leaf needs to know quickly which disease it is and what to spray, "
           "but extension officers and plant pathologists are few and far from the field, so diagnosis is delayed and treatment is guessed. Convolutional networks classify leaf images "
           f"with accuracies above 99 % on laboratory collections such as PlantVillage {R(5, 6, 2)}, and compact networks suitable for ordinary computers exist {R(2)}. "
           f"Field photographs are harder: the PlantDoc authors show that models trained on laboratory images fail on photographs taken in the open {R(4)}, and Barbedo lists background, "
           f"symptom variation and small datasets as the main obstacles {R(8)}.")
    P.para("Most published work stops at the class label. A farmer also needs the severity, a treatment and prevention advice in a language they read. The base paper of this project, "
           f"Foliagen {R(1)}, addresses a different problem, the scarcity of annotated foliage images, by generating them from single-leaf photographs; it does not return advice to a farmer. "
           "The gap this project works on is the join between a diagnosis and an actionable, multilingual treatment recommendation.")
    P.para("The contributions are: (1) a complete, deployable web application (React interface, FastAPI service over the original Flask product, SQLite store) that diagnoses a leaf photograph, "
           "returns severity and three kinds of treatment from a 38-class knowledge base, keeps a history with CSV and PDF export and offers an English, Hindi and Marathi interface; "
           "(2) a seeded benchmark on PlantDoc that measures the engine the application actually ships, the compact CNN of its training script, a transfer-learning reference and "
           "classical baselines under one protocol; (3) the finding that the shipped heuristic does not diagnose (about chance) while transfer learning reaches about 50 %; and (4) a "
           "list of seven defects found by tests and code review, with an honest account of what is not built. Section II surveys related work, Section III describes the method, Section IV "
           "gives the results and Section V concludes.", indent=0.2)
    P.sub("A", "System Hardware")
    P.para(f"All measurements ran on one desktop computer: {F.HARDWARE}. Other jobs shared the processor during training, so training times are indicative.")
    P.sub("B", "Software Requirements")
    P.para(f"{F.SOFTWARE}. Networks were built with TensorFlow {R(20)} and classical models with scikit-learn {R(19)}.")

    # ---------------------------------------------------------------- II
    P.heading("II", "Literature Survey")
    P.para(f"**Base paper.** Pakka et al. {R(1)} observe that leaf classifiers work on single leaves while real use needs in-field foliage images, and that annotated foliage datasets are scarce. "
           "Foliagen generates them without a generative network: single-leaf photographs (10,722 soybean images of seven diseases plus 132 more, and PlantVillage tomato images) lose their "
           "background with an automatic remover, are arranged by a spiral phyllotactic generator that follows plant structure, and are placed on field backgrounds with a chosen share of diseased "
           "leaves (1 to 20 %, about 15 % for the natural soybean set). About 1,000 images per disease category are generated for soybean and tomato. VGG19, ResNet50, DenseNet121, Swin Transformer and "
           "CBAM-ConvNeXt are trained on two RTX 6000 Ada GPUs (Adam, batch 8, learning rate 1e-4, early stopping). Adding 5 % of a natural foliage set to generated data lets classifiers reach up to 98 % accuracy "
           "on the natural set, and pre-training on generated images followed by fine-tuning with few real ones also works. The authors note the approach depends on leaf-image quality and may need "
           "crop-specific structure for other crops. It covers two crops, produces data rather than a diagnosis, and has no recommendation step. This project does not implement Foliagen; it keeps its "
           "lesson that laboratory images transfer poorly to the field.")
    P.para(f"**Related work.** Datasets: PlantVillage {R(5)} holds laboratory images and is the basis of most reports; PlantDoc {R(4)} offers 2,598 web-scraped field photographs of 13 plants in 27 classes, "
           f"with a 2,342/236 split, and TomatoVillage {R(21)} adds real-world tomato images. CNN classifiers: Mohanty et al. {R(6)} and Ferentinos {R(7)} report 99 % or more on PlantVillage-style data; "
           f"PD36-C {R(2)} is an 18-layer network with 1,250,694 parameters and 99.53 % test accuracy on 87 thousand laboratory-style images, and Kanakala and Ningappa {R(3)} report 96.4 % validation "
           f"accuracy for a CNN on the same kind of collection. On PlantDoc the benchmark paper {R(4)} reaches 44.5 to 70.5 % on cropped leaves and 13.7 to 29.7 % on raw photographs. Efficient backbones such as "
           f"MobileNetV2 {R(9)} built on depthwise separable convolutions {R(10)} make training on a CPU feasible, and fine-tuning ImageNet weights {R(13)} is the usual remedy for small data.")
    P.para(f"**Position of this work.** The surveyed classifiers stop at a label, and the one that offers a desktop application {R(2)} works offline on laboratory-style images. Field studies stress that the "
           f"test data must differ from the training data in the way real use differs {R(8, 4)}. We therefore use PlantDoc, which is small and noisy but honest about field conditions, and we build the missing "
           "layer: severity and treatment advice, history and a three-language interface in one application, then measure how well the diagnosis inside it works.")
    rows = [["Pakka {r:1}", "Generated foliage images", "Soybean, tomato", "Up to 98 % with 5 % real", "Data only, 2 crops"],
            ["Sherifi {r:2}", "18-layer CNN, 1.25 M params", "87 k lab images", "99.53 % test", "Lab data, no advice"],
            ["Kanakala {r:3}", "CNN and LSTM", "87.9 k images, 38 cl.", "96.4 % val. (CNN)", "Random split"],
            ["Singh {r:4}", "VGG16, Inception on PlantDoc", "2,598 field photos", "13.7-70.5 %", "Small, hard"],
            ["Mohanty {r:6}", "AlexNet, GoogLeNet", "PlantVillage", "99.35 %", "Lab backgrounds"],
            ["Ferentinos {r:7}", "5 CNNs", "87.8 k images, 58 cl.", "99.53 %", "Mostly lab"],
            ["Barbedo {r:8}", "Factor analysis", "Public sets", "Accuracy falls off-lab", "No application"]]
    P.table("Related work: approach, data, reported result, limitation", ["Work", "Approach", "Data", "Reported result", "Limitation"], rows,
            widths=[0.62, 0.8, 0.72, 0.68, 0.58], size=6.5, align=["l", "l", "l", "l", "l"])
    P.para("Table I shows the gap: reported accuracies are high on laboratory data and low on field photographs, and none of the surveyed works returns treatment advice in several languages "
           "through an application. The figures come from different data and protocols and are not ranked here.")

    # ---------------------------------------------------------------- III
    P.heading("III", "Methodology")
    P.para("**Architecture.** Fig. 1 shows the three tiers. A React 18 interface with 12 page components (landing, sign-in, dashboard, detect, result, history, analytics, profile, disease guide) talks "
           "to a FastAPI service with 16 routes. The service imports the original Flask product unchanged: its inference module, its 38-class knowledge base and its database initialiser. One SQLite file "
           "holds two tables, users and results, and uploaded photographs are stored as files with random names. Sign-in returns an HMAC-signed bearer token valid for seven days; passwords are stored as salted hashes.")
    P.figure(figs["arch"], "System architecture: browser, FastAPI service and the original Flask modules, with the SQLite store and the image folder (full diagram: docs/diagrams/01).")
    P.para("**Main flow.** Fig. 2 follows one scan. The service refuses a request without a valid token, an extension other than JPG, PNG or WEBP, an empty file or a file above 10 MB. "
           "The inference module decodes the photograph, ranks the candidate classes, and the service attaches the knowledge card of the top class, stores the image and one row, and returns the top three "
           "classes with severity and treatments. The result screen, history list, CSV or PDF export and the analytics charts read the same rows.")
    P.figure(figs["flow"], "Main flow of one diagnosis in the shipped application, including the failure for crop options with fewer than three candidate classes.")
    P.para("**Heuristic engine.** The engine that the application ships uses no trained network. The photograph is resized to 256 × 256 and five pixel shares are computed: green g (green above red by 0.03 "
           "and above blue by 0.01), brown b, yellow y, dark d (mean below 0.25) and white w (minimum above 0.72), plus the standard deviation σ of all values. The candidate classes are those of the chosen "
           "crop (all 38 if the crop is 'general'). A healthy class scores")
    P.eq("s_h = 3g − 4(b + y) − 1.5d + 0.25 − |σ − 0.18|,")
    P.para(indent=0, text="a diseased class scores")
    P.eq("s_d = 3.2b + 2.4y + 1.2d + 1.6w + 1.5·max(0, 0.5 − g) + bonus,")
    P.para(indent=0, text="where the bonus adds a multiple of white, brown or yellow share for names containing mildew, rust, blight, mosaic or mite, and a jitter of up to 0.35 derived from a hash of the file "
                          "makes the order stable per image. The top class receives the displayed confidence")
    P.eq("c = min(0.99, max(0.62, 0.62 + 0.22·min(1.6, s))),")
    P.para(indent=0, text="so the confidence never falls below 0.62; the second and third scores are small fractions of c taken from the same hash. A crop with fewer than three candidate classes (10 of 19 options) "
                          "leaves the ranking short and raises an error, which the API reports as an unreadable image.")
    P.para(f"**Design rationale.** The heuristic was kept as the shipped engine because it needs no model file and answers in milliseconds on a laptop, which suited a first deployable version, and the "
           "knowledge base is kept apart from the engine so that a better classifier can be installed without touching the advice. The compact network follows the depthwise-separable design of mobile "
           f"models {R(10)} to stay small; MobileNetV2 is added as a reference because ImageNet pre-training {R(13)} is the standard answer to a training set of about two thousand photographs. "
           "No cropping or leaf detection is applied before classification, so the backgrounds of the web photographs reach the network.")
    P.para(f"**Knowledge base.** The 38 classes (14 crops, 12 healthy) carry a severity (12 high, 14 medium, 12 none), symptoms, life cycle, prevention and three treatments (chemical, organic, cultural) "
           "with cost text in rupees; 26 diseases have curated text and the remaining ones use generic text for their kind (fungal, bacterial, viral, pest). The interface strings, but not this text, are translated "
           "into Hindi and Marathi.")
    P.para(f"**Data and protocol.** PlantDoc {R(4)} (licence CC-BY-4.0) in the local folder layout has {F.NTRAIN:,} training photographs in 28 classes (2 to 180 per class) and {F.NTEST} test photographs in 27 "
           "classes. Photographs are resized to 224 × 224. A stratified 10 % of the training folder is held out for early stopping, so the test photographs never influence training or selection; the shipped "
           "script instead validates on the test folder. Every learned model is run with seeds 42, 43 and 44 and reported as mean ± standard deviation.")
    P.para(f"**Networks.** The compact CNN of the training script has five separable-convolution blocks {R(10)} of 32, 64, 128, 256 and 256 filters, each followed by batch normalisation {R(11)}, 2 × 2 max-pooling "
           "and dropout 0.15, then global average pooling, dropout 0.3, a dense layer of 256 units and a softmax over 28 classes: 189,655 parameters, with random flip, rotation, zoom and contrast in the model. It is trained "
           f"with Adam {R(12)} at 1e-3, batch 32, up to 60 epochs, early stopping on validation accuracy and learning-rate halving on plateau. The reference model is MobileNetV2 {R(9)} with ImageNet weights: "
           "a new softmax head is trained with the backbone frozen, then the top 30 layers are fine-tuned at 1e-4 (2,293,852 parameters). The loss is")
    P.eq("L = −(1/N) Σ_i log p_i(y_i).")
    P.para(indent=0, text=f"Two classical baselines use 43 hand-made features (HSV histograms, grey-level and gradient statistics): a random forest {R(18)} with 300 trees and a logistic regression.")
    P.para("**Metrics.** Top-1 accuracy is the share of photographs whose highest-ranked class is the labelled one; top-3 accuracy counts the label among the three displayed classes. For each class c, "
           "precision P and recall R give the F1 score, and macro-F1 averages it over the 27 classes present in the test folder, so every class counts equally however few photographs it has:")
    P.eq("F1_c = 2 P_c R_c / (P_c + R_c),   macro-F1 = (1/27) Σ_c F1_c.")
    P.para(indent=0, text="Two derived scores check whether the engine at least separates healthy from diseased leaves and finds the right crop: healthy-versus-diseased accuracy, from the class names, and crop accuracy. "
                          "Latency is the time from sending the upload to receiving the reply on the loopback address.")
    P.para("**Implementation and error handling.** The interface keeps the token in the browser, attaches it to every call and signs the user out on a 401 reply. Every error from the service has one JSON shape with "
           "an error code, a message and a detail string, so the interface can show the message to the farmer. A result belongs to one user: another user's request for it returns 404, deleting a result removes the "
           "row and the image file, and a single scan can be exported as CSV or PDF. Photographs are saved under random names, so the image address itself acts as the capability to view it. The launcher fixes "
           "the hash seed, which keeps the heuristic's jitter identical from run to run.")
    P.para(f"**Verification.** An end-to-end test of the API passes {F.N_SMOKE} checks. A second script adds {F.N_EDGE} unit and API checks (token forgery and expiry, upload limits, injection-style input, paging, "
           f"cross-origin requests): {F.N_EDGE_PASS} pass and {F.N_EDGE_DEFECT} reproduce defects of the product, listed in Section IV. A browser check script covers layout at three widths, language and theme switching; it passed "
           "55 checks in the earlier frontend session and was not re-run for this paper.")

    # ---------------------------------------------------------------- IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** All accuracies are on the {F.NTEST} official PlantDoc test photographs (27 classes present), never used for fitting. Macro-F1 averages the 27 class F1 values. The heuristic is "
           "run with five hash seeds (seed 0 is what the launcher sets), learned models with three training seeds. Chance is 2.6 % on 38 classes and 36 % if the crop is known; always answering the most frequent class "
           "gives 5.1 %.")
    rows = [["Heuristic, crop chosen", f"{HC['accuracy']['mean'] * 100:.1f}", f"{HC['macro_f1']['mean']:.3f}", f"{HC['top3_accuracy']['mean'] * 100:.1f}", f"{HC['healthy_vs_diseased_accuracy']['mean'] * 100:.1f}"],
            ["Heuristic, crop 'general'", f"{HG['accuracy']['mean'] * 100:.1f}", f"{HG['macro_f1']['mean']:.3f}", f"{HG['top3_accuracy']['mean'] * 100:.1f}", f"{HG['healthy_vs_diseased_accuracy']['mean'] * 100:.1f}"],
            ["Logistic regression", f"{LR['accuracy'] * 100:.1f}", f"{LR['macro_f1']:.3f}", f"{LR['top3_accuracy'] * 100:.1f}", f"{LR['healthy_vs_diseased_accuracy'] * 100:.1f}"],
            ["Random forest", f"{RF['accuracy'] * 100:.1f}", f"{RF['macro_f1']:.3f}", f"{RF['top3_accuracy'] * 100:.1f}", f"{RF['healthy_vs_diseased_accuracy'] * 100:.1f}"],
            ["Compact CNN (3 seeds)", F.pm(C, "accuracy").replace("%", ""), f"{C['macro_f1']['mean']:.3f}", f"{C['top3_accuracy']['mean'] * 100:.1f}", f"{C['healthy_vs_diseased_accuracy']['mean'] * 100:.1f}"],
            ["MobileNetV2, head only", F.pm(MB, "head_only_accuracy").replace("%", ""), f"{MB['head_only_macro_f1']['mean']:.3f}", "-", "-"],
            ["MobileNetV2, fine-tuned", F.pm(MB, "accuracy").replace("%", ""), f"{MB['macro_f1']['mean']:.3f}", f"{MB['top3_accuracy']['mean'] * 100:.1f}", f"{MB['healthy_vs_diseased_accuracy']['mean'] * 100:.1f}"]]
    P.table("Test results on PlantDoc (236 photos), percent unless stated", ["Engine", "Top-1", "Macro-F1", "Top-3", "Healthy / diseased"], rows,
            widths=[1.2, 0.72, 0.5, 0.45, 0.53], size=7, align=["l", "c", "c", "c", "c"])
    P.figure(figs["results"], "Top-1 accuracy of every engine measured on the PlantDoc test photographs (error bars: standard deviation over seeds).")
    P.para(f"**The shipped heuristic.** With the crop chosen it is correct on {F.pm(HC, 'accuracy')} of photographs ({pc(H0['accuracy'])} with hash seed 0) and has the right answer among its top three on "
           f"{F.mean_pct(HC, 'top3_accuracy')}, which is close to the 36 % expected by chance within a crop; with the crop left on 'general' it reaches {F.pm(HG, 'accuracy')}. It cannot tell healthy from diseased: "
           f"only {F.mean_pct(HC, 'healthy_recall')} of healthy leaves are called healthy, and its healthy-versus-diseased accuracy ({F.mean_pct(HC, 'healthy_vs_diseased_accuracy')}) is below the 61.9 % obtained by always saying "
           f"'diseased'. Its displayed confidence averages {F.HCONF['mean_conf'] * 100:.0f} % while top-1 is right on only {F.HCONF['acc_by_bin'][1]:.0f} %, {F.HCONF['acc_by_bin'][2]:.0f} % and "
           f"{F.HCONF['acc_by_bin'][3]:.0f} % of the photographs in the three confidence bins, and the three displayed scores add up to more than 102 % for {F.HCONF['share_sum_over_102'] * 100:.0f} % of them (up to "
           f"{F.HCONF['max_sum'] * 100:.0f} %). Fig. 4 plots this and Fig. 5 shows a late-blight leaf called healthy with 97.2 %.")
    P.figure(figs["confidence"], "Correctness of the heuristic engine by the confidence it displays (160 answerable test photographs): higher confidence is not more often right.")
    P.figure(figs["shot_result"], "Output screen (result): a PlantDoc tomato late-blight leaf diagnosed 'Tomato - healthy', 97.20 % by the heuristic engine; the note on the screen says the score is not a calibrated probability.", width=2.6)
    P.para(f"**Failure by design.** For {pc(HC['failed_share']['mean'])} of the test photographs the application gives no answer: the crop options blueberry, cherry, orange, peach, pepper, raspberry, soybean, squash and "
           "strawberry have fewer than three candidate classes, the ranking is too short, and the API replies HTTP 400 'could not be read as an image' to a valid photograph (Fig. 6). On the answered photographs the "
           f"accuracy is {F.pm(HC, 'accuracy_on_answered')}.")
    P.figure(figs["shot_error"], "Output screen (detect): crop 'Blueberry' with a valid leaf photograph; the application answers 'The diagnosis failed. That file could not be read as an image.'", width=2.6)
    P.para(f"**Learned models.** The compact CNN reaches {F.pm(C, 'accuracy')} (macro-F1 {C['macro_f1']['mean']:.3f}) and under-fits: its training accuracy is {F.pm(C, 'train_accuracy')}. Validating on the test folder as the "
           f"shipped script does gives {pc(CS['accuracy']['mean'])} and removing the learning-rate decay {pc(CT['accuracy']['mean'])}, so neither the selection leak nor the schedule explains the low value; with 2,342 photographs the "
           f"small network does not learn from scratch. A random forest on hand-made colour and texture features is better ({pc(RF['accuracy'])}), and MobileNetV2 with ImageNet weights is far better: head-only "
           f"{F.pm(MB, 'head_only_accuracy')}, fine-tuned {F.pm(MB, 'accuracy')}, top-3 {F.mean_pct(MB, 'top3_accuracy')}, healthy-versus-diseased {F.mean_pct(MB, 'healthy_vs_diseased_accuracy')}, at {MB['train_seconds']['mean']:.0f} s of CPU training "
           f"and a median of {MB['latency_ms_median']['mean']:.0f} ms per photograph. The best classes are strawberry (F1 1.00), grape black rot (0.93), grape (0.92) and corn rust (0.89); bell-pepper leaf spot, tomato bacterial spot "
           "and tomato mosaic virus are never recognised, visually similar diseases of the same crop being confused.")
    P.para("**Per class.** Fig. 7 shows that the fine-tuned network does best on classes with a distinctive look (strawberry, grape, raspberry, corn rust) and worst on the "
           "three tomato and pepper spot and virus classes whose symptoms resemble one another. The compact network recognises only a few classes at all, mostly tomato yellow leaf curl virus (F1 0.67 for seed 42) and "
           "strawberry (0.38). With 4 to 12 test photographs per class these per-class values are indicative only.")
    P.para(f"**Comparison with the base papers.** Foliagen's up to 98 % {R(1)} measures classifiers on soybean and tomato foliage with generated training data and GPUs; PD36-C's 99.53 % {R(2)} is on laboratory-style "
           f"images of 38 classes. Neither is comparable with the numbers above, which are for field photographs, 28 classes, 2,342 training images and a CPU. The nearest like-for-like figure is the PlantDoc paper's "
           f"13.7 to 29.7 % for raw photographs {R(4)}, which the fine-tuned MobileNetV2 exceeds, while the shipped heuristic and compact CNN do not.")
    P.figure(figs["perclass"], "Per-class F1 of MobileNetV2 and of the compact CNN on the 27 test classes (seed 42); several classes score zero.", width=3.3)
    P.para(f"**Application and tests.** On the local machine one diagnosis takes a median of {F.LAT['detect_client_ms']['median']:.0f} ms from upload to reply (95th percentile {F.LAT['detect_client_ms']['p95']:.0f} ms, 100 photographs) and the "
           "history and dashboard calls about 10 ms; no concurrent-load test was made. Testing and code review found seven defects (Table III); the first is the crop failure above, and the others "
           "are listed with their evidence.")
    rows = [["D1", "Crop options with fewer than 3 candidate classes raise an error (HTTP 400)", "10 of 19 crop keys; 32.2 % of test photos"],
            ["D2", "Three displayed scores add up to more than 100 %; confidence never below 0.62", "82 % of 160 photos above 102 %, max 112 %"],
            ["D3", "Default token-signing secret is public", "A token forged with it is accepted"],
            ["D4", "No rate limit on sign-in", "8 wrong passwords in 2.8 s all answered"],
            ["D5", "Training script validates on the test folder and mislabels the two grape classes", "27 test class names against a 28-class model"],
            ["D6", "Training script docstring claims about 1.1 M parameters", "Measured 189,655"],
            ["D7", "Reported latency includes a constant 40 ms", "Server median 47 ms against 23 ms measured by the client"]]
    P.table("Defects found by tests and code review", ["ID", "Defect", "Evidence"], rows, widths=[0.3, 1.75, 1.35], size=6.8, align=["c", "l", "l"])
    P.para(f"**Cost.** The compact CNN trains in {C['train_seconds']['mean']:.0f} s on the CPU and answers in a median of {C['latency_ms_median']['mean']:.0f} ms per photograph; MobileNetV2 needs {MB['train_seconds']['mean']:.0f} s "
           f"and {MB['latency_ms_median']['mean']:.0f} ms. The saved compact network is 2.4 MB. The heuristic costs about 20 ms in the process and needs no training, which is its only advantage. Fine-tuning gains only about "
           f"{(MB['accuracy']['mean'] - MB['head_only_accuracy']['mean']) * 100:.1f} points over the head alone, so on this small set most of the benefit comes from the pre-trained features.")
    P.para("**Threats to validity.** The test folder has 4 to 12 photographs per class, so single-class F1 values are noisy and a difference of one photograph changes them by 8 to 25 points. PlantDoc images are "
           "scraped from the web, and whether the same photograph appears in both folders was not checked. Hash seeds and training seeds vary only the sources of randomness we control; the split itself is fixed. "
           "The dosages in the knowledge base are curated text, not region-specific recommendations, and were not compared with local agronomic guidance.")
    P.para("**Objectives against outcomes.** (1) A labelled dataset was assembled from PlantDoc, not collected by the team. (2) Resizing and in-model augmentation were done; the shipped engine only resizes. "
           "(3) A CNN was trained, but it is inaccurate and not installed. (4) Treatment advice exists for all 38 classes; fertiliser advice does not. (5) The web interface exists with an interface-only "
           "translation. (6) Per-class accuracy was measured; the advice was not validated. The study is limited to one dataset of 236 test photographs, three seeds without a significance test, no field "
           "trial or user study, and no agronomist review.")

    # ---------------------------------------------------------------- V
    P.heading("V", "Conclusion and Future Scope")
    P.para(f"AgriVision works end to end as a web application: sign-in, photograph upload, a top-3 diagnosis with severity, treatment and prevention advice for 38 classes, history, exports, analytics and an "
           f"English, Hindi and Marathi interface, with {F.N_SMOKE} API checks passing. Against the objectives, the dataset, preprocessing, a CNN, the disease-to-treatment mapping, the web interface and per-class "
           "evaluation were done; the diagnosis engine in the application is not accurate, multilingual support covers only the interface, fertiliser, yield and weather advice are not built, and the advice has "
           f"not been checked by an agronomist. The key finding is that field photographs need transfer learning: MobileNetV2 reaches {pc(MB['accuracy']['mean'])} where the heuristic reaches {pc(HC['accuracy']['mean'])} "
           f"and the compact CNN {pc(C['accuracy']['mean'])}, and that confidence shown by the application cannot be trusted.")
    P.para("What this means for a farmer today: the treatment text for a class is usable reference material, but the class name the application proposes should be confirmed with an agricultural officer before "
           "spraying, as the on-screen note already says. The measured gap between the heuristic and the pre-trained network is large enough that replacing the engine is the first step, and the benchmark "
           "and tests built here show when that step has worked.")
    P.para("Future work: install the fine-tuned network in the application and calibrate its probabilities; fix the crop-option failure and the training script; crop leaves or detect them before "
           f"classification as the PlantDoc authors do {R(4)}; add Grad-CAM explanations {R(17)}; translate the treatment text; add fertiliser and weather advice; and test with farmers and with an agronomist.")

    P.references()
    P.save(path)
    return path, P.order


if __name__ == "__main__":
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    path, order = build(out)
    print(path, "refs:", len(order), order)
