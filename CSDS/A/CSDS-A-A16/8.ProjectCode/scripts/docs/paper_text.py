"""Text of 19.IEEE_Paper.docx (Mosaic). Every number is read from facts.py (experiments/**/metrics.json).

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
    fig, ax = _canvas(3.5, 3.1, 100, 89)
    _box(ax, 1, 76, 98, 11, "Browser: Next.js 16 + React 19 (port 3000)\nLanding · Login · Register · Analyze (upload / webcam) · History", "blue", 5.2, True)
    _arrow(ax, 50, 76, 50, 72.5, "<|-|>")
    _box(ax, 1, 58, 98, 13, "FastAPI service (port 8000): 8 endpoints\n/api/auth  /api/analyze  /api/history  /api/health\nJWT (HS256, 7 days) + bcrypt; optional auth on analyze", "purple", 5.2, True)
    _arrow(ax, 50, 58, 50, 54.5)
    _box(ax, 1, 36, 98, 17, "", "teal")
    ax.text(50, 50.2, "ML modules (PyTorch CPU + OpenCV)", ha="center", va="center", fontsize=5.2, fontweight="bold", color=NAVY)
    for x, t in ((3, "Haar\nface\ncrop"), (27, "resize 64,\nscale\n[-1, 1]"), (51, "EmotionCNN\n18 sigmoid\noutputs"), (75, "sort + argmax\n= dominant")):
        _box(ax, x, 38, 21, 9, t, "teal", 4.9)
    for x in (24.5, 48.5, 72.5):
        _arrow(ax, x, 42.5, x + 2.3, 42.5)
    _arrow(ax, 50, 36, 50, 32.5, "<|-|>")
    _box(ax, 1, 17, 30, 14, "mosaic.db\nusers,\nanalyses (JSON)", "grey", 5.0)
    _box(ax, 35, 17, 30, 14, "checkpoints/\nclassifier_final.pt\nstage1, generator", "grey", 5.0)
    _box(ax, 69, 17, 30, 14, "media/thumbs/\ncropped faces\n(.jpg)", "grey", 5.0)
    _box(ax, 1, 2, 98, 11, "Offline: FER2013 -> backbone -> cEmoGAN -> synthetic faces -> final CNN", "orange", 4.6)
    return _save(fig, "paper_arch.png")


def fig_flow():
    plt.rcParams["font.family"] = "DejaVu Serif"
    fig, ax = _canvas(3.5, 2.7, 100, 78)
    ax.text(1, 75, "(A) one request", fontsize=5.8, fontweight="bold", color=NAVY)
    steps = ["upload\nJPEG/PNG", "Haar\ndetect", "crop\n64x64", "CNN\nforward", "sigmoid\n18 scores", "rank +\ndominant"]
    w = 15
    for i, t in enumerate(steps):
        x = 1 + i * 16.4
        _box(ax, x, 56, w, 14, t, "blue" if i < 2 else "teal", 5.0)
        if i:
            _arrow(ax, x - 1.5, 63, x, 63)
    _box(ax, 1, 40, 47, 10, "signed in: INSERT analysis + save thumbnail", "purple", 5.0)
    _box(ax, 52, 40, 47, 10, "no face: 200, empty result", "red", 5.0)
    _arrow(ax, 60, 56, 25, 50.5)
    _arrow(ax, 85, 56, 85, 50.5)
    ax.text(1, 34, "(B) offline training (python -m app.ml.run_pipeline)", fontsize=5.8, fontweight="bold", color=NAVY)
    off = ["FER2013\n28,709 / 7,178", "stage 1\nbackbone\n(7-way CE)", "cEmoGAN\n10 epochs", "synthesise\n11 x 200\nfaces", "final CNN\n18 outputs\n(BCE)"]
    for i, t in enumerate(off):
        x = 1 + i * 19.8
        _box(ax, x, 6, 17, 21, t, "orange" if i in (0, 1) else "teal", 4.9)
        if i:
            _arrow(ax, x - 2.4, 16.5, x, 16.5)
    return _save(fig, "paper_flow.png")


def fig_results():
    plt.rcParams["font.family"] = "DejaVu Serif"
    fig, axs = plt.subplots(1, 2, figsize=(3.5, 2.15), gridspec_kw={"width_ratios": [1.35, 1]})
    ax = axs[0]
    ro, sy = F.abl_vals("real_only", "accuracy"), F.abl_vals("synth", "accuracy")
    names = ["always\nhappy", "stage-1\nbaseline", "final\n(shipped)", "real\nonly", "real +\nsynth."]
    vals = [F.DATA["test_majority_baseline"], F.BASE["accuracy"], F.FIN["accuracy"], float(np.mean(ro)), float(np.mean(sy))]
    errs = [0, 0, 0, float(np.std(ro, ddof=1)), float(np.std(sy, ddof=1))]
    cols = [GREY, GREY, TEAL, BLUE, ORANGE]
    ax.bar(range(5), [v * 100 for v in vals], yerr=[e * 100 for e in errs], color=cols, capsize=2, width=0.65, error_kw={"lw": 0.7})
    for i, v in enumerate(vals):
        ax.text(i, v * 100 + errs[i] * 100 + 1.2, f"{v * 100:.1f}", ha="center", fontsize=5.2)
    ax.set_xticks(range(5), names, fontsize=4.6)
    ax.set_ylim(0, 72)
    ax.set_ylabel("FER2013 test accuracy (%)", fontsize=5.4)
    ax.tick_params(axis="y", labelsize=5)
    ax.set_title("(a) basic emotions", fontsize=5.6)
    ax = axs[1]
    labels = ["compound\nROC-AUC", "GAN condition\naccuracy"]
    auc = F.SYN["final_model"]["0.5"]["compound_roc_auc_macro"]
    gan = F.GAN["mean_basic_conditional_accuracy"]
    ax.bar([0, 1], [auc, gan], color=[PURPLE, RED], width=0.55)
    ax.plot([-0.4, 0.4], [0.5, 0.5], color=NAVY, ls="--", lw=0.8)
    ax.plot([0.6, 1.4], [1 / 7, 1 / 7], color=NAVY, ls="--", lw=0.8)
    ax.text(0, auc + 0.03, f"{auc:.2f}", ha="center", fontsize=5.4)
    ax.text(1, gan + 0.03, f"{gan:.2f}", ha="center", fontsize=5.4, color=NAVY)
    ax.text(0, 0.62, "chance 0.50", fontsize=4.6, color=NAVY, ha="center")
    ax.text(1, 0.33, "chance 0.14", fontsize=4.6, color=NAVY, ha="center")
    ax.set_xticks([0, 1], labels, fontsize=4.6)
    ax.set_ylim(0, 1)
    ax.tick_params(axis="y", labelsize=5)
    ax.set_title("(b) generation diagnostics", fontsize=5.6)
    for a in axs:
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.4)
    return _save(fig, "paper_results.png")


def shot_crop(name, box=None, width=700):
    im = Image.open(F.shot(name)).convert("RGB")
    if box:
        im = im.crop(box)
    im.thumbnail((width, width * 3))
    return im


def pair_image(a, b, out, height=520):
    """Two crops side by side, scaled to a common height."""
    ims = []
    for im in (a, b):
        r = height / im.size[1]
        ims.append(im.resize((int(im.size[0] * r), height)))
    gap = 14
    canvas = Image.new("RGB", (ims[0].size[0] + ims[1].size[0] + gap, height), "white")
    canvas.paste(ims[0], (0, 0))
    canvas.paste(ims[1], (ims[0].size[0] + gap, 0))
    p = os.path.join(F.FIGS, out)
    canvas.save(p, optimize=True)
    return p


def stack_image(a, b, out, width=800):
    """Two crops stacked vertically, scaled to a common width."""
    ims = [im.resize((width, int(im.size[1] * width / im.size[0]))) for im in (a, b)]
    gap = 10
    canvas = Image.new("RGB", (width, ims[0].size[1] + ims[1].size[1] + gap), "white")
    canvas.paste(ims[0], (0, 0))
    canvas.paste(ims[1], (0, ims[0].size[1] + gap))
    p = os.path.join(F.FIGS, out)
    canvas.save(p, optimize=True)
    return p


# ----------------------------------------------------------------------------- the paper
def build(path):
    D, B, N, G, S, T, A = F.DATA, F.BASE, F.FIN, F.GAN, F.SYN, F.DET, F.APIM
    ro_acc, sy_acc = F.abl_vals("real_only", "accuracy"), F.abl_vals("synth", "accuracy")
    ro_f1, sy_f1 = F.abl_vals("real_only", "macro_f1"), F.abl_vals("synth", "macro_f1")
    ro_auc = [F.ABL[f"real_only_s{s}"]["synthetic_holdout_thr0.5"].get("compound_roc_auc_macro") for s in (1, 2, 3)]
    sy_auc = [F.ABL[f"synth_s{s}"]["synthetic_holdout_thr0.5"]["compound_roc_auc_macro"] for s in (1, 2, 3)]
    sy_auc_m = float(np.mean(sy_auc))
    ro_auc_m = float(np.mean([v for v in ro_auc if v]))
    lat = {l["label"]: l for l in A["latency"]}
    la = lat["POST /api/analyze anonymous (face)"]
    lp = lat["POST /api/analyze authenticated (face, persisted)"]
    ll = lat["POST /api/auth/login (bcrypt)"]
    cr = N["compound_on_real_test"]
    sh = S["final_model"]["0.5"]
    fr = G["frechet_distance_stage1_features"]
    pcls = N["per_class"]

    def pc(x, d=1):
        return f"{x * 100:.{d}f}"

    figs = {"arch": fig_arch(), "flow": fig_flow(), "results": fig_results()}
    box_res = (858, 92, 1342, 900)
    fig4 = pair_image(shot_crop("08_result_happy.png", box_res, 600), shot_crop("14_result_gan_happily_surprised.png", box_res, 600), "paper_shots_a.png")
    fig5 = stack_image(shot_crop("16_result_no_face.png", (858, 92, 1342, 260), 800), shot_crop("17_history.png", (256, 56, 1340, 430), 800), "paper_shots_b.png")

    P = Paper()
    authors = [[n, f"Roll No. {r}", "Dept. of CSE (Data Science)", F.COLLEGE_SHORT, "[CITY], India", "[email]"] for n, r in F.STUDENTS_UPPER]
    authors.append([F.GUIDE, f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of CSE (Data Science)", F.COLLEGE_SHORT, "[CITY], India", "[email]"])
    P.title_block("Mosaic: Basic and Compound Emotion Recognition from Facial Images with a Conditional GAN and a Multi-Label CNN", authors)
    P.begin_two_columns()

    P.abstract(
        "Most facial-emotion recognisers assign one basic label to a face, although real expressions often blend emotions and labelled blends are scarce. "
        "This paper documents Mosaic, a working implementation of the analysis-by-synthesis idea of the base paper: a conditional GAN trained on FER2013 synthesises faces for eleven compound emotions, "
        f"and a {N['parameters'] / 1000:.0f}k-parameter CNN with eighteen sigmoid outputs (seven basic, eleven compound) is trained on real and synthetic faces and served by a FastAPI and Next.js application with face detection, accounts and history. "
        f"On the {D['n_test']:,}-image FER2013 test set the multi-label model reaches {pc(N['accuracy'])} % basic-emotion accuracy against {pc(B['accuracy'])} % for a single-label baseline, "
        f"but a three-seed ablation shows the gain comes from additional training, not from the synthetic images ({F.mstd(ro_acc, 1)} % without them, {F.mstd(sy_acc, 1)} % with them). "
        f"The compound outputs stay near zero on real faces and cannot rank synthetic compound classes (ROC-AUC {sh['compound_roc_auc_macro']:.2f}), and the generator follows its condition at chance level. "
        "We report these negative results, the serving defects found and the limits of the evidence.",
        ["compound emotions", "conditional GAN", "data augmentation", "facial expression recognition", "FER2013", "multi-label classification"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para(f"Facial expressions are a main cue to emotional state, and automatic recognition serves driver monitoring, well-being applications and human-computer interaction {c('lideng')}. "
           f"Most systems classify one of the six basic emotions of Ekman and Friesen plus neutral {c('ekman')}, and on unconstrained data they do so modestly: a lightweight CNN reaches only 51.6 % on FER2013 {c('galkaduwa')}. "
           f"The single label is also a simplification. Du et al. showed that people reliably produce and recognise compound expressions such as happily surprised or sadly fearful {c('du2014')}, "
           "yet a one-label classifier must force such a face into one class and cannot say that two emotions are present.")
    P.para(f"The cost of the usual practice is therefore twofold: mixed emotions are invisible, and the data needed to learn them are scarce. Real compound labels exist only in small, licensed collections such as the compound subset of RAF-DB {c('rafdb')}, "
           f"and recent compound-recognition work trains ensembles on them and reaches an F1 of about 52-55 % on seven compound classes {c('abaw7')}. "
           f"The base paper of this project {c('base')} proposes analysis by synthesis: generate identity-preserving mixed-emotion faces with conditioned GANs, then train a multi-label CNN on them. "
           "Its recogniser, however, is scored on images produced by its own generator, and recognition on real photographs is shown only qualitatively. "
           "The gap addressed here is an open, end-to-end implementation of that pipeline in which the effect of the synthetic images is isolated with a control on a real test set.")
    P.para("The contributions are: (1) Mosaic, a tested application with eighteen outputs (seven basic, eleven compound), a conditional GAN, Haar face detection, JWT accounts, a SQLite history and a web console; "
           "(2) a seeded ablation that separates the effect of synthetic compound faces from the effect of additional training; "
           "(3) diagnostics for the generator (conditional fidelity, feature-space Fréchet distance) and for the compound outputs (real-face behaviour, ROC-AUC on a synthetic hold-out); and "
           "(4) a list of serving defects and an honest statement of what the evidence does not show. Section II surveys related work, Section III gives the method, Section IV the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("Everything was trained and measured on one CPU-only desktop: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11, no GPU. "
           "Other jobs shared the processor during training and timing, so the durations reported here are upper bounds. The final classifier trained in about 10.6 minutes for five epochs.")
    P.sub("B", "Software Requirements")
    P.para(f"Python 3.11, PyTorch 2.14 (CPU) {c('pytorch')}, OpenCV 4.11, scikit-learn 1.5 for metrics, FastAPI 0.143 with pydantic 2.14, SQLAlchemy 2.0, python-jose, bcrypt 4.0.1 (pinned in requirements.txt because bcrypt 5 breaks passlib), "
           "pytest 8.2, and Next.js 16.3 with React 19 and Recharts for the console. The repository pins older library versions in requirements.txt; the versions above are those used in this run.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para(f"**Base paper.** Khine et al. {c('base')} introduce Conditioned Emotion GANs (cEmoGANs). An encoder maps an image to a latent code that carries identity, "
           "and a conditional generator receives that code plus a six-dimensional multi-hot label (anger, disgust, fear, happiness, sadness, surprise), so that setting two bits yields a compound expression of the same person. "
           "The generator is trained with learning rates of 1e-4 (generator) and 1e-5 (discriminator). Ground truth for compound faces is built by morphing pairs of expression images from CK+, JAFFE and MUG; "
           "15,000 generated images are split 7:3 to train and test a small multi-label CNN with sigmoid outputs. Generation quality is measured with an Inception-style score, "
           "Fréchet distance and BRISQUE, identity preservation with a face-recognition embedding (98 %, 94 % and 99 % of generated faces above a cosine similarity of 0.7), "
           "and recognition with the f-beta score and the exact-match ratio (EMR). The reported f-beta is 0.99, 0.99 and 0.80 and the EMR 100 %, 99 % and 68.7 % on CK+, JAFFE and MUG, against 0.45, 0.60 and 0.51 for EfficientNet-B0. "
           "These recognition numbers are measured on the generator's own output; real unconstrained photographs are shown only as qualitative examples.")
    P.para(f"**GANs for expression recognition.** Conditional GANs {c('cgan')} extend the original GAN {c('gan')} by feeding a label to both networks, and convolutional generators {c('dcgan')} made image-scale generation practical; "
           f"multi-domain translation and facial-animation GANs can edit expressions but change identity or need action-unit supervision {c('stargan')}. "
           f"Recent recognition work therefore uses GANs mainly to remove identity from expression features: contrastive disentangled GANs {c('cdgan')}, style-transfer GANs tested on CK+, FER-2013 and JAFFE {c('nstgan')}, "
           f"and a face-cycle GAN for cross-domain recognition {c('facecycle')} (the last known to us by title only). All of them still output a single basic label.")
    P.para(f"**Datasets and baselines.** FER2013 holds 35,887 48x48 grayscale faces in seven classes and is the usual in-the-wild benchmark {c('fer2013')}; accuracy on it is far below that on laboratory sets. "
           f"A recent comparison finds HOG with an SVM at 44.0 %, LBP with logistic regression at 25.0 % and a small CNN at 51.6 % on FER2013 {c('galkaduwa')}. "
           f"Compound labels come from RAF-DB {c('rafdb')}, and ensembles of vision transformers and CNNs reach an F1 of 51.5-55.4 % on its seven compound classes {c('abaw7')}. "
           f"Because a face may carry several emotions, the natural formulation is multi-label learning {c('multilabel')}, evaluated with per-label and exact-match measures rather than single-label accuracy.")
    P.para(f"**Generation metrics.** GAN output is usually judged with the Inception score and the Fréchet distance between feature distributions {c('fid')}. We cannot use the Inception network on 64x64 grayscale faces without changing the task, "
           "so Section IV uses the Fréchet distance in the feature space of our own stage-1 CNN, which is not comparable with published values.")
    P.table("Selected related work",
            ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [[f"Khine {c('base')}", "cEmoGANs + CNN, multi-label", "CK+, JAFFE, MUG (morphed)", "f-beta 0.99/0.99/0.80", "Scored on generated faces"],
             [f"Liu {c('cdgan')}", "Identity/expression disentangling", "Lab and field sets", "Comparable to SOTA", "Single basic label"],
             [f"Khemakhem {c('nstgan')}", "Style-transfer GAN", "CK+, FER-2013, JAFFE", "Above baselines (abstract)", "Single basic label"],
             [f"Galkaduwa {c('galkaduwa')}", "HOG+SVM vs. light CNN", "FER-2013, CK+, KDEF", "CNN 51.6 % on FER-2013", "Basic labels only"],
             [f"Liu {c('abaw7')}", "ViT/PosterV2/ResNet ensemble", "RAF-DB compound, 7 classes", "F1 51.5-55.4 %", "Needs real compound labels"],
             [f"Li, Deng {c('lideng')}", "Survey of deep FER", "Many datasets", "Taxonomy of methods", "Mostly single-label"],
             ["This work", "cEmoGAN + 18-output CNN", "FER2013 (7 basic labels)", "Section IV", "No real compound labels"]],
            [0.55, 0.68, 0.68, 0.7, 0.68], size=6.0)
    P.para("**Research gap.** Recognition of compound emotions needs either scarce real labels or synthetic data; the literature shows synthetic data only scored on itself. "
           "What is missing is an open implementation that trains on synthetic compound faces, evaluates on real faces against a no-synthesis control, and reports what does not work.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Data and Preprocessing")
    P.para(f"The data are the FER2013 pickles of a public Hugging Face mirror (tagged apache-2.0 there): {D['n_train']:,} training and {D['n_test']:,} test faces, 48x48 grayscale, seven classes. "
           f"The classes are imbalanced: happy has {D['class_counts']['train']['happy']:,} training faces, disgust only {D['class_counts']['train']['disgust']:,} ({D['class_counts']['train']['disgust'] / D['n_train'] * 100:.1f} %). "
           f"Always predicting happy would score {pc(D['test_majority_baseline'])} % on the test set. Faces are resized to 64x64 and scaled to [-1, 1]. "
           "FER2013 has no compound labels, so the eleven compound outputs have no real test labels at all: compound training data come only from the generator, and compound recognition on real faces cannot be scored.")
    P.sub("B", "Backbone and Conditional GAN")
    P.para("Stage 1 trains a CNN with four Conv-BatchNorm-ReLU-MaxPool blocks (32, 64, 128, 128 channels) and a head of FC 2048-256, dropout 0.4 and a seven-way output "
           f"with class-weighted cross-entropy, Adam {c('adam')} at 1e-3, batch 256 and five epochs. The same body with eighteen outputs is the final classifier ({N['parameters']:,} parameters). "
           f"The cEmoGAN of this implementation is a conditional DCGAN-style pair: the generator maps noise z (100-d) and a 7-d condition vector c through five transposed convolutions to a 64x64 image ({G['generator_parameters']:,} parameters); "
           "the discriminator scores an image and a projected condition. Training uses 400 real faces per class (2,800), Adam 2e-4 with beta1 0.5, batch 64, ten epochs, one-hot conditions and a real-label target of 0.9:")
    P.eq("L_D = BCE(D(x|c), 0.9) + BCE(D(G(z|c)|c), 0)")
    P.eq("L_G = BCE(D(G(z|c)|c), 0.9)")
    P.para(f"The final discriminator and generator losses were {0.7731} and {3.7240} (the product's training log). Unlike the base paper, there is no encoder, so identity preservation is not implemented here.")
    P.sub("C", "Compound Synthesis and Multi-Label Classifier")
    P.para("For each of eleven compound classes (a subset of the categories of Du et al. {r}) the generator receives a condition with 0.5 on each of the two component emotions and is sampled 200 times, giving 2,200 synthetic faces. ".replace("{r}", c("du2014")) +
           "Each synthetic face has three active targets: its two basic emotions and the compound; each real face has one active basic target. The final classifier is initialised with the convolutional weights of the backbone and trained on the 28,709 real plus 2,200 synthetic faces with binary cross-entropy over the eighteen logits z (index k):")
    P.eq("L = -(1/18) Σ_k [ y_k log σ(z_k) + (1 - y_k) log(1 - σ(z_k)) ]")
    P.para("Adam 5e-4, batch 256, five epochs. At inference the dominant emotion is the arg max over all eighteen sigmoid outputs, and the basic and compound lists are returned sorted. "
           "No decision threshold is applied: the code has a threshold parameter that is never used.")
    P.sub("D", "Application and Serving Path")
    P.para(f"A request carries a JPEG or PNG. The OpenCV Haar cascade {c('viola')} (scale factor 1.1, five neighbours, minimum 40x40 px) finds faces, the largest is cropped in grayscale, resized and classified. "
           "A signed-in user's result and cropped-face thumbnail are stored; an anonymous call returns the result only. Passwords are hashed with bcrypt, tokens are HS256 JWTs valid for seven days and history is private per user. "
           "If no face is found the API still answers 200 with face_detected false, although its contract says 422.")
    P.figure(figs["arch"], "Mosaic architecture: browser, FastAPI service, ML modules and local files.", 3.3)
    P.figure(figs["flow"], "Main flow: (A) one analysis request and (B) the offline training pipeline.", 3.3)
    P.sub("E", "Implementation Notes")
    P.para("The console offers an upload tab and a webcam tab (a captured frame is posted like an uploaded file). The result view shows the dominant emotion with its confidence, a Recharts bar chart of the seven basic scores and horizontal bars for the six highest of the eleven compound scores. "
           "The access token is persisted in the browser by a small zustand store, history is paged by limit and offset, and every analysis row keeps the seven basic scores, the eleven compound scores and the dominant emotion as JSON, so a history entry can be redrawn exactly. "
           "Classifier, generator and backbone checkpoints are plain PyTorch state dictionaries loaded with the model in evaluation mode; the model is loaded once when the server starts, and the health endpoint reports whether that succeeded. "
           "The final classifier had never been trained when this project was received, so the API reported that no model was loaded until stage 3 of the pipeline was run unchanged.")
    P.sub("F", "Evaluation Protocol")
    P.para("Basic-emotion accuracy and macro-F1 are computed on the FER2013 test set by arg max over the seven basic outputs. A three-seed ablation retrains the final classifier from the same backbone with and without the synthetic faces; "
           "the GAN is fixed. Compound behaviour is examined in two ways that need no real compound labels: the compound scores of real test faces, and a hold-out of 1,100 freshly generated compound faces scored with micro-F1, exact-match ratio and macro ROC-AUC over the eleven compound columns. "
           "Generator fidelity is the accuracy of the stage-1 CNN on 500 generated faces per condition and the Fréchet distance between 256-d stage-1 features of generated and real faces.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.sub("A", "Test Conditions")
    P.para(f"All numbers come from the {D['n_test']:,}-image FER2013 test set unless stated; the test set was also printed per epoch but never used to select a model. "
           f"The ablation used seeds 1-3 and five epochs per run (about nine minutes each on the shared CPU). {F.TESTS['tests']} automated tests (pytest) pass. Latencies are medians over HTTP on 127.0.0.1.")
    P.table("Basic-emotion results on FER2013 test (7,178 images)",
            ["Model", "Accuracy %", "Macro-F1"],
            [["Always predict happy", pc(D["test_majority_baseline"], 2), "-"],
             ["Stage-1 single-label CNN (shipped)", pc(B["accuracy"], 2), f"{B['macro_f1']:.3f}"],
             ["Final 18-output CNN (shipped)", pc(N["accuracy"], 2), f"{N['macro_f1']:.3f}"],
             ["18 outputs, real faces only (3 seeds)", F.mstd(ro_acc), f"{np.mean(ro_f1):.3f} ± {np.std(ro_f1, ddof=1):.3f}"],
             ["18 outputs, real + synthetic (3 seeds)", F.mstd(sy_acc), f"{np.mean(sy_f1):.3f} ± {np.std(sy_f1, ddof=1):.3f}"]],
            [1.95, 0.8, 0.65], size=6.4, align=["l", "c", "c"])
    P.sub("B", "Basic Emotions and the Ablation")
    P.para(f"The shipped multi-label model scores {pc(N['accuracy'])} % against {pc(B['accuracy'])} % for the single-label stage-1 network (macro-F1 {N['macro_f1']:.3f} against {B['macro_f1']:.3f}), "
           f"in line with the 51.6 % that a lightweight CNN reached on FER2013 in {c('galkaduwa')} under its own protocol. The gain, however, is not a synthetic-data effect. "
           f"A model trained on real faces only, with the same initialisation and epochs, scores {F.mstd(ro_acc)} % over three seeds, and adding the synthetic faces gives {F.mstd(sy_acc)} %: the difference is within one standard deviation of the unsynthesised runs, "
           f"and macro-F1 is slightly lower with synthetic faces ({np.mean(sy_f1):.3f} against {np.mean(ro_f1):.3f}). The extra five epochs of fine-tuning, not the GAN, explain the improvement over the baseline. "
           f"Per class, happy ({pc(pcls['happy']['f1'], 1)} F1) and surprise ({pc(pcls['surprise']['f1'], 1)}) are recognised best; disgust has perfect precision but only {pc(pcls['disgust']['recall'], 1)} % recall because it is 1.5 % of the training data; fear is confused with sad and angry.")
    P.figure(figs["results"], "(a) Basic-emotion accuracy with the no-synthesis control; error bars are one standard deviation over three seeds. (b) Compound ROC-AUC on the synthetic hold-out and generator condition accuracy, each against chance.", 3.4)
    cm = N["confusion_matrix"]
    P.table("Per-class results of the shipped final model",
            ["Emotion", "Test n", "Precision", "Recall", "F1", "Baseline F1"],
            [[k.capitalize(), f"{pcls[k]['support']:,}", f"{pcls[k]['precision']:.3f}", f"{pcls[k]['recall']:.3f}", f"{pcls[k]['f1']:.3f}", f"{B['per_class'][k]['f1']:.3f}"] for k in F.BASIC],
            [0.62, 0.5, 0.58, 0.5, 0.45, 0.62], size=6.4, align=["l", "c", "c", "c", "c", "c"])
    P.para(f"The confusion matrix shows where the single-label errors lie: {cm[2][4]} of the {pcls['fear']['support']:,} fearful faces are read as sad and {cm[2][0]} as angry, "
           f"{cm[6][4]} of {pcls['neutral']['support']:,} neutral faces as sad, and {cm[0][4]} of {pcls['angry']['support']} angry faces as sad. These are the neighbouring negative emotions that compound categories combine, "
           "so a model that cannot yet separate the basic classes cleanly (macro-F1 around 0.5) is a weak base for compound recognition regardless of the synthetic data. "
           "Disgust illustrates the imbalance problem that synthetic augmentation was meant to ease: it has 111 test faces, precision 1.000 and recall 0.189, and the GAN was not used to oversample it.")
    P.sub("C", "Compound Emotions and Generator Fidelity")
    P.para(f"On the {cr['n']:,} real test faces the largest compound probability averages {cr['mean_top_compound_confidence']:.5f}, no face has any compound output above 0.3, and the dominant emotion is never a compound. "
           f"The mean compound score is the same whether or not the true basic label is a component of the compound ({cr['mean_score_true_basic_is_component']:.6f} against {cr['mean_score_true_basic_not_component']:.6f}). "
           f"On the synthetic hold-out the final model's macro ROC-AUC is {sh['compound_roc_auc_macro']:.3f} ({sy_auc_m:.3f} averaged over the three ablation runs with synthetic faces; {ro_auc_m:.3f} for the controls without them), "
           f"the exact-match ratio is {sh['exact_match_ratio']:.3f} and compound recall at the 0.5 threshold is {pc(sh['compound_recall'], 1)} %. "
           f"The classifier has learned at most that generated faces differ from real ones (the requested compound gets {sh['mean_compound_prob_on_true_compound']:.2f} on average), but not which compound was requested.")
    P.para(f"The generator explains part of this. Reading 500 faces per one-hot condition with the stage-1 CNN gives {pc(G['mean_basic_conditional_accuracy'], 1)} % agreement with the condition on average (chance 14.3 %), "
           f"from {pc(G['basic']['sad']['stage1_accuracy_on_generated'], 0)} % for sad to {pc(G['basic']['happy']['stage1_accuracy_on_generated'], 0)} % for happy and {pc(G['basic']['surprise']['stage1_accuracy_on_generated'], 0)} % for surprise. "
           f"For compound conditions the stage-1 top label lies in the requested pair {pc(G['mean_compound_top1_in_pair'], 1)} % of the time (chance {pc(G['chance_top1_in_pair'], 1)} %) and the top two labels equal the pair {pc(G['mean_compound_top2_equals_pair'], 1)} % (chance {pc(G['chance_top2_equals_pair'], 1)} %). "
           f"The Fréchet distance to real training faces is {fr['generated_basic_vs_real_train_subset']:.0f} for generated faces against {fr['real_test_vs_real_train_subset']:.1f} for real test faces. "
           "Ten epochs on 2,800 faces were not enough for the generator to learn expression control; the samples are blurred face-like patterns (Fig. 4b).")
    P.table("Diagnostics of the compound pipeline",
            ["Measurement", "Value"],
            [["Max compound prob. on real faces (mean)", f"{cr['mean_top_compound_confidence']:.5f}"],
             ["Compound ROC-AUC, synthetic hold-out", f"{sh['compound_roc_auc_macro']:.3f}  (chance 0.5)"],
             ["GAN condition accuracy, one-hot", f"{pc(G['mean_basic_conditional_accuracy'], 1)} %  (chance 14.3 %)"],
             ["Fréchet dist., generated vs. real", f"{fr['generated_basic_vs_real_train_subset']:.0f}  (real test: {fr['real_test_vs_real_train_subset']:.1f})"],
             ["Haar detection, native 48 px / 2x / 3x", f"{pc(T['haar_detection_rate_scale_1x'], 0)} % / {pc(T['haar_detection_rate_scale_2x'], 0)} % / {pc(T['haar_detection_rate_scale_3x'], 0)} %"],
             [f"Accuracy on {T['detected_at_3x']} detected faces: Haar crop vs. direct", f"{pc(T['accuracy_via_haar_crop_on_detected'])} % vs. {pc(T['accuracy_direct_64px_on_same_images'])} %"]],
            [2.2, 1.2], size=6.2, align=["l", "c"])
    P.sub("D", "Serving Path and Interface")
    P.para(f"The Haar detector finds {pc(T['haar_detection_rate_scale_1x'], 0)} % of native 48x48 FER2013 faces (its minimum window is 40 px) and about {pc(T['haar_detection_rate_scale_3x'], 0)} % after 3x upscaling, so a photo must be larger than the training images. "
           f"Even where it succeeds there is a train/serve mismatch: through the Haar crop the same faces are classified with {pc(T['accuracy_via_haar_crop_on_detected'])} % accuracy against {pc(T['accuracy_direct_64px_on_same_images'])} % for a direct resize, because training faces are aligned FER crops. "
           f"An anonymous analysis takes a median of {la['p50_ms']:.0f} ms ({la['p95_ms']:.0f} ms at the 95th percentile) and a persisted one {lp['p50_ms']:.0f} ms; login is dominated by bcrypt at {ll['p50_ms']:.0f} ms. "
           f"All {A['probes_total']} malformed-input probes were handled as intended or characterised, and the service stayed healthy; defects found are an HTTP 500 for undecodable uploads, no e-mail validation, a result thumbnail whose URL is not resolved against the API origin (a broken image in Fig. 4), a history-detail route that nothing links to, and a hard reload of a protected page that returns to the login screen.")
    P.figure(fig4, "Result screens: (a) a real FER2013 face (dominant: Happy 47 %; all compound bars 0 %) and (b) a cEmoGAN-generated happily-surprised face (dominant: Sad 53 %; compound bars about 1 %).", 3.4)
    P.figure(fig5, "(a) A native 48x48 face is not detected (empty result); (b) history list of one user's analyses.", 3.4)
    P.sub("E", "Threats to Validity")
    P.para("Three threats limit the conclusions. The test set doubles as the validation set printed during training, although no model was selected on it and every number reported is the last epoch; "
           "with three seeds, a difference of 0.8 accuracy points between the ablation arms cannot be called significant, and the opposite claim (that synthetic data hurt macro-F1) is equally unsupported. "
           "FER2013 labels are noisy and the mirror's licence tag is that of the uploader rather than of the original competition data. Finally, the stage-1 CNN used to judge the generator is itself only 50.6 % accurate, "
           "so the fidelity figures are conservative; they show that the generator is not conditionally accurate, not how far it is from a good one.")
    P.sub("F", "Comparison with the Base Paper and Limits")
    P.para(f"The base paper reports f-beta 0.99, 0.99 and 0.80 and an exact-match ratio of 100 %, 99 % and 68.7 % {c('base')}, but on a 30 % split of 15,000 faces generated by its own cEmoGANs from laboratory datasets (CK+, JAFFE, MUG) with morphing-derived labels. "
           "Our setting differs in every respect: real in-the-wild FER2013 test faces with basic labels only, a different generator without an identity encoder, and no compound ground truth. The numbers are therefore not comparable and we do not claim to match or beat them; "
           "the one analogous measurement we can make, recognition of generated compound faces, is at chance level. The base paper's unconstrained-photo examples were judged by eye, and we have no equivalent quantitative evidence either. "
           "Further limits are a short training budget (five epochs, 2,800 GAN faces), grayscale 64x64 inputs, a single dataset with known label noise, a shared CPU for all timings, and no test of the webcam path.")

    P.para("A caution on use: a facial expression is an outward signal, not a measurement of an inner state, and cultural display rules differ; the base paper makes the same point and notes demographic bias as a risk. "
           "Mosaic stores only a cropped grayscale face for signed-in users, never the uploaded photograph, and its generator is used only inside the training scripts, but any deployment on real people would need informed consent and an evaluation on the target population. "
           f"With the measured accuracy of {pc(N['accuracy'])} % and a seven-class macro-F1 near {N['macro_f1']:.2f}, its basic-emotion output is best read as a rough indication, and its compound output should not be presented to users at all until the compound head is retrained and validated.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para(f"Mosaic delivers a working basic-emotion service: {pc(N['accuracy'])} % on FER2013, accounts, history, a web console, {F.TESTS['tests']} passing tests and a median analysis time of {la['p50_ms']:.0f} ms. "
           "Against the five objectives, the interface (5) is met, a multi-label classifier (3) and a single-label comparison (4) are implemented and measured, enlargement of the dataset with generated images (2) was done but did not help, "
           "and identity-preserving generation (1) was not achieved: there is no encoder and the generator does not follow its condition. "
           f"The key finding is negative and specific: synthetic compound faces produced by a briefly trained cGAN neither improved basic accuracy ({F.mstd(sy_acc)} % against {F.mstd(ro_acc)} %) nor taught the classifier to separate compound classes (ROC-AUC {sh['compound_roc_auc_macro']:.2f}), "
           "so the compound outputs are inert on real faces. Honest limits remain: no real compound labels, one dataset, a short training budget and a train/serve framing mismatch.")
    P.para("Future work: train the generator far longer, with an encoder for identity and a perceptual or classifier-guided loss; evaluate on a labelled compound set such as RAF-DB compound; weight or curriculum the synthetic faces and calibrate a threshold per compound class; "
           "and train on face crops produced by the same detector that serves requests.")
    P.references()
    return P.save(path)


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "19.IEEE_Paper.docx")))
