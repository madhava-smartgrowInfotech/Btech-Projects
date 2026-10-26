"""Chapter 1: Introduction (VeriVision AI)."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, N, P, TAB
from .refs import CITE as R


def blocks():
    e, ci = F.ENS, F.CI["ensemble"]
    a1 = F.BR["a1"]
    d = F.DATA
    n_train = d["train_real"] + d["train_fake"]
    n_val = d["val_real"] + d["val_fake"]
    n_test = d["test_real"] + d["test_fake"]
    xd_ens = F.XD["ensemble"]
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P(f"This chapter introduces the domain of the project, the motivation for building {F.PRODUCT}, the problem it addresses, the objectives set for it, the scope that "
          "was actually delivered, the contributions, and the limitations and assumptions that govern every result reported later. It closes with a map of the rest of the report."),

        H2("1.1 Domain and Background"),
        P("The project belongs to computer vision, deep learning and explainable artificial intelligence, with a link to digital image forensics. Image forensics asks whether a picture is what it "
          "claims to be. For most of the history of the field the question concerned manipulation of a real photograph: splicing, cloning or retouching. Since generative adversarial networks "
          f"[{R['gan']}] and, more recently, latent diffusion models [{R['ldm']}], the question has widened to whether the image was ever photographed at all. A generator can now produce a picture from a short text prompt, "
          "and the result is realistic enough that casual inspection no longer separates it from a camera image."),
        P("A convolutional neural network (CNN) is a natural tool for this task. It learns filters directly from pixel data, so it can pick up the faint statistical regularities that "
          f"generation leaves behind, which are invisible to the eye. Pretrained backbones such as EfficientNet [{R['efficientnet']}], ResNet [{R['resnet']}] and MobileNetV3 [{R['mobilenetv3']}] "
          f"already encode general visual features learned on ImageNet [{R['imagenet']}], so a detector can be built by fine-tuning rather than by training from scratch. "
          "Explainable AI (XAI) adds a second layer: instead of a bare label, the system shows which regions of the image drove the decision. Gradient-weighted class "
          f"activation mapping (Grad-CAM) [{R['gradcam']}] produces such a heat map from the gradients that flow into the last convolutional layer, without changing the network."),
        P(f"The base paper chosen for this batch, Larue et al. [{R['base']}], studies a related but different problem: generalisable deepfake detection on face images, with a one-class model "
          f"that sees only authentic faces and synthesised pseudo-fakes. It is discussed in detail in Chapter 2. The heterogeneous ensemble and gating design of HEDGE [{R['hedge']}], which "
          f"combines several detectors through weighted logit fusion and two gating rules, supplied the architecture pattern used here, and the empirical study of Tasnim et al. [{R['empirical']}] "
          "supplied a comparison of detector families and a Grad-CAM analysis."),

        H2("1.2 Motivation"),
        B("**Realism.** Generated images are used for misinformation, fraud, fabricated evidence and reputational harm, and people cannot reliably tell them from photographs.",
          "**Fragile detectors.** A detector trained on one generator often fails on images from another, and the cues it relies on are weakened by the resizing and compression that "
          "social platforms apply to every upload.",
          "**Unexplained verdicts.** A score without a reason is hard to defend in a dispute. An analyst needs to see where the model looked and whether several independent models agree.",
          "**Access.** The strongest published detectors rely on large foundation-model backbones and GPU clusters. A student-built tool that runs on a laptop CPU and keeps the uploaded image on the machine "
          "is a useful complement for education and for preliminary screening."),

        H2("1.3 Problem Statement"),
        P("Synthetic images are realistic enough to deceive human observers. Detectors trained on one generator degrade sharply on images from another. Compression and resizing remove many "
          "detectable artefacts, and a verdict without visual justification is not credible in a dispute. The problem addressed by this project is to build a CNN-based detector that "
          "classifies an uploaded image as real or AI-generated, reports a confidence and the agreement between its component models, explains the decision with Grad-CAM heat maps, "
          "checks how stable the answer is under common degradations, and measures honestly how well all of this works."),

        H2("1.4 Need for the System"),
        B("A single model gives a single opinion; four heterogeneous routes expose disagreement, and the fusion rule makes the combination explicit and inspectable.",
          "Explanations must travel with the verdict, so the interface shows the votes, the heat map and the robustness check on one screen.",
          "A local application keeps sensitive images off third-party servers and needs no GPU.",
          "Claims of generalisation must be tested rather than assumed, so the project includes held-out, degraded and cross-domain evaluations and reports the failures."),

        H2("1.5 Objectives"),
        P("The six objectives of the batch, taken from the objectives document, and what became of each, are listed below."),
        TAB("Objectives and their status", ["No.", "Objective", "Status"], [
            ["1", lit.OBJECTIVES[0], f"Partly met. Real images from CIFAR-10 and images from one generator (Stable Diffusion v1.4) in CIFAKE [{R['cifake']}]; a 600-image second-source set was used for a probe only."],
            ["2", lit.OBJECTIVES[1], "Met. Per-route augmentation (crop, flip, colour jitter, blur, noise, JPEG, resize) and ImageNet normalisation."],
            ["3", lit.OBJECTIVES[2], f"Met. Four CNN routes trained; ensemble accuracy {F.pct(e['accuracy'])} on {F.N_TEST:,} held-out images."],
            ["4", lit.OBJECTIVES[3], f"Measured, not achieved. Ensemble accuracy {F.pct(xd_ens['accuracy'])} (ROC-AUC {F.f3(xd_ens['roc_auc'])}) on a different-source probe, i.e. chance."],
            ["5", lit.OBJECTIVES[4], "Met. Grad-CAM overlays for three routes, judged qualitatively; no quantitative faithfulness test."],
            ["6", lit.OBJECTIVES[5], f"Met. Flask API on port {F.API_PORT}, React interface on port {F.WEB_PORT}, verdict, confidence, votes, heat maps and robustness check."],
        ], widths=[0.5, 2.7, 3.1], align=["c", "l", "l"], size=10),

        H2("1.6 Scope"),
        P(f"The delivered system is a working web application and the experiments behind it. In scope are: image upload and validation (PNG, JPEG, WebP, up to {F.UPLOAD_LIMIT_MB} MB); four fine-tuned CNN routes; "
          "logit-space fusion with two gating rules; confidence wording; Grad-CAM overlays; a robustness re-check under JPEG compression, down-and-up resizing and Gaussian blur; a demo sign-in; "
          "an insights page that reads the stored evaluation; training and evaluation scripts; and the automated tests. "
          "Out of scope are: video and audio; face-specific deepfake detection as in the base paper; attribution of an image to a particular generator; detection of partial edits and inpainting; "
          "a multi-user account system and database; and deployment as a hosted service. Chapter 10 of the report lists directions beyond this scope."),

        H2("1.7 Contributions"),
        N(f"A working end-to-end detector that serves four CNN routes through one Flask API and one React interface on a CPU-only machine, with a median response of {F.LATENCY['predict_s']:.2f} s for a verdict and {F.LATENCY['analyze_s']:.1f} s for a full analysis.",
          "A transparent fusion design: weighted logit combination with two deterministic gates, every parameter in one configuration file, and per-route votes shown with the verdict.",
          "A combined explanation panel: Grad-CAM heat maps for three routes plus a robustness consistency score (k of n variants agreeing).",
          f"A measured evaluation on {F.N_TEST:,} held-out images with bootstrap confidence intervals, a fusion ablation, a threshold sweep, calibration, robustness tests and a cross-domain probe.",
          "An honest set of negative findings: the gates did not help, the ensemble gain over the best single route is not statistically distinguishable, and generalisation to other sources failed."),

        H2("1.8 Summary of Results"),
        P(f"On the held-out CIFAKE subset the deployed ensemble reaches an accuracy of {F.pct(e['accuracy'])} (95% bootstrap interval {F.pct(ci[0])} to {F.pct(ci[1])}), "
          f"an F1 score of {F.f3(e['f1'])} and a ROC-AUC of {F.f4(e['roc_auc'])}. The best single route, A1, scores {F.pct(a1['accuracy'])}; the two intervals overlap, so the ensemble's advantage in accuracy is not "
          f"statistically distinguishable on this sample, although its ROC-AUC is higher ({F.f4(e['roc_auc'])} against {F.f4(a1['roc_auc'])}). The ensemble leans toward the AI-generated class (false-positive rate "
          f"{F.pct(e['fpr'])}, false-negative rate {F.pct(e['fnr'])}). Resizing and blur reduce the 32-pixel images to about 58 to 61% accuracy, and on full-resolution images from other sources the ensemble is at "
          f"chance ({F.pct(xd_ens['accuracy'])}). These numbers are reported in Chapter 8 together with their limits."),
        FIG(F.fig("f01_dataset_split.png"), f"Class-balanced CIFAKE subset used here: {n_train:,} training, {n_val:,} validation and {n_test:,} test images.", 4.6),

        H2("1.9 Limitations and Assumptions"),
        B(f"**Data.** Training used {n_train:,} of the {d['pool_train']:,} CIFAKE training images and 3 to 5 epochs because the machine has no GPU. The images are 32 x 32 pixels from a single generator.",
          "**Single run.** Each route was trained once (seeds 42 to 45); the ranking of routes carries run-to-run uncertainty beyond the bootstrap interval.",
          "**Test-set choices.** The threshold sweep and the fusion ablation were evaluated on the test subset, so any operating point picked from them is optimistic.",
          "**Explanations.** Grad-CAM maps were inspected by eye; there is no deletion or insertion test of their faithfulness.",
          "**Not measured.** User study, GPU timing, load testing and adversarial attacks.",
          "**Assumptions.** The user uploads a single still image; the machine has about 16 GB of RAM; the demo account is for local use only; the verdict is decision support, not proof of origin."),

        H2("1.10 Organisation of the Report"),
        TAB("Organisation of the report", ["Chapter", "Content"], [
            ["1", "Introduction: domain, motivation, problem, objectives, scope, contributions, limitations."],
            ["2", "Literature survey: the base paper, related work by theme, datasets and algorithms, research gap."],
            ["3", "Feasibility study: technical, economic, operational and schedule feasibility."],
            ["4", "System requirements and analysis: existing and proposed system, requirements, hardware, software, users."],
            ["5", "System design: architecture, workflow, data flow diagrams, UML, data model, modules, user interface."],
            ["6", "Methodology and implementation: data, preprocessing, models, training, fusion, explanation, API, security, installation."],
            ["7", "System testing: strategy, unit, integration, functional, security, performance and the limits of the testing."],
            ["8", "Results and output screens: model performance, ablation, robustness, cross-domain probe, screens, objectives versus outcomes."],
            ["9", "Conclusion: summary, objectives achieved, key findings, applications, limitations."],
            ["10", "Future scope: improvements, features, scalability and further research."],
        ], widths=[0.9, 5.4], align=["c", "l"], size=10.5),
        P("The report ends with the reference list and three appendices: important code, the installation and user guide, and additional screens."),
    ]
