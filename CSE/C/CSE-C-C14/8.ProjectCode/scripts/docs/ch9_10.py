"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10) of VeriVision AI."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    import os

    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


def c(*keys):
    """Citation string such as [1], [6] from CITE keys."""
    return "[" + ", ".join(str(R[k]) for k in keys) + "]"


def _v():
    """Frequently quoted measured values, read from the facts module."""
    e, br = F.ENS, F.BR
    sw = {round(r["threshold"], 1): r for r in F.SWEEP}
    best = max(F.SWEEP, key=lambda r: r["accuracy"])
    rob = {k: v["ensemble"]["accuracy"] for k, v in F.ROB.items()}
    rob_b = {k: v["branches"]["b"]["accuracy"] for k, v in F.ROB.items()}
    var = F.VARIANTS
    return {
        "acc": F.pct(e["accuracy"], 2), "acc1": F.pct(e["accuracy"], 1), "f1": F.f4(e["f1"]), "auc": F.f4(e["roc_auc"]), "auc_pct": F.pct(e["roc_auc"], 2),
        "prec": F.f4(e["precision"]), "rec": F.f4(e["recall"]),
        "ci": f"{F.pct(F.CI['ensemble'][0], 1)} to {F.pct(F.CI['ensemble'][1], 1)}",
        "a1_acc": F.pct(F.BR["a1"]["accuracy"], 2), "a1_ci": f"{F.pct(F.CI['a1'][0], 1)} to {F.pct(F.CI['a1'][1], 1)}",
        "fpr": F.pct(e["fpr"], 1), "fnr": F.pct(e["fnr"], 1), "pfr": F.pct(e["predicted_fake_rate"], 1),
        "g1": e["gate1_fired"], "g2": e["gate2_fired"], "ng_acc": F.pct(var["no_gates"]["accuracy"], 2),
        "pavg_acc": F.pct(var["prob_avg"]["accuracy"], 2), "pavg_auc": F.f4(var["prob_avg"]["roc_auc"]),
        "maj_auc": F.f4(var["majority"]["roc_auc"]), "eq_acc": F.pct(var["equal_weights"]["accuracy"], 2),
        "ece": F.f4(F.ECE), "n": F.N_TEST,
        "best_thr": best["threshold"], "best_acc": F.pct(best["accuracy"], 2),
        "t07_fpr": F.pct(sw[0.7]["fpr"], 1), "t08_fpr": F.pct(sw[0.8]["fpr"], 1), "t07_acc": F.pct(sw[0.7]["accuracy"], 2), "t08_acc": F.pct(sw[0.8]["accuracy"], 2),
        "r_clean": F.pct(rob["clean_subset"], 1), "r_jpeg": F.pct(rob["jpeg"], 1), "r_resize": F.pct(rob["resize"], 1), "r_blur": F.pct(rob["blur"], 1), "r_noise": F.pct(rob["noise"], 1),
        "rb_resize": F.pct(rob_b["resize"], 1), "rb_blur": F.pct(rob_b["blur"], 1),
        "xd_acc": F.pct(F.XD["ensemble"]["accuracy"], 1), "xd_auc": F.f3(F.XD["ensemble"]["roc_auc"]),
        "xd_a1": F.pct(F.XD["branches"]["a1"]["accuracy"], 1),
        "unan": F.pct(F.UNANIMOUS, 1), "wrong": F.ERR["n_wrong"], "m_ok": F.f2(F.ERR["mean_abs_margin_correct"]), "m_bad": F.f2(F.ERR["mean_abs_margin_wrong"]),
        "pred_s": f"{F.LATENCY['predict_cifake_32px']['median']:.2f}", "pred_hi": f"{F.LATENCY['predict_photo_1024px']['median']:.2f}",
        "an_s": f"{F.LATENCY['analyze_cifake_32px']['median']:.2f}", "an_hi": f"{F.LATENCY['analyze_photo_1024px']['median']:.2f}",
    }


# ------------------------------------------------------------------ document 9
def novelty_blocks():
    v = _v()
    return [
        P(f"This section sets VeriVision AI against the base paper chosen for the batch, Larue et al. (CTrue) {c('base')}, and against HEDGE {c('hedge')}, the heterogeneous-ensemble detector whose "
          "fusion-and-gating idea the project follows. The comparison is meant to be exact about what is new, because most of the components are standard and the value of the work lies in how they are "
          "combined, measured and explained."),
        H2("2.1 What the base paper does and what this project does differently"),
        P(f"CTrue is a one-class face-deepfake detector: it is trained only on 720 pristine FaceForensics++ videos, creates pseudo-fakes during training, learns a hybrid-curvature representation on an "
          f"EfficientNet-B4 backbone, and is evaluated with ROC-AUC on face-forgery benchmarks {c('base')}. VeriVision AI addresses a neighbouring problem. It classifies general images as real or AI-generated "
          "with a supervised, two-class decision, it uses four small ImageNet-pretrained CNNs rather than one large backbone, it trains on CPU in minutes per route, and it adds an explanation and a robustness "
          "check to every verdict. The project does not implement CTrue's curvature representation or its one-class training, and none of its results are reproduced here."),
        TAB("Comparison of the base paper, the design reference and this project",
            ["Aspect", f"CTrue {c('base')}", f"HEDGE {c('hedge')}", "VeriVision AI (this project)"],
            [["Task", "Face deepfake detection", "AI-generated image detection in the wild", "AI-generated image detection (general images)"],
             ["Training signal", "One-class: authentic only + pseudo-fakes", "Progressive training", "Supervised, two-class, CIFAKE subset"],
             ["Backbones", "EfficientNet-B4 (19.3 M parameters)", "DINOv3 and MetaCLIP2 routes", "EfficientNet-B0 x2, ResNet50, MobileNetV3-Large"],
             ["Fusion", "Single model", "Logit-space weighted fusion, dual gating", "Logit-space weighted fusion, two gates"],
             ["Compute", "Two V100 GPUs, 200 epochs", "8 H800 GPUs", "One i5-12500 CPU, 3-5 epochs per route"],
             ["Explanation", "Not assessed here", "Not assessed here", "Grad-CAM on three routes in the app"],
             ["Robustness", "Not assessed here", "JPEG and resize results reported", "Per-image JPEG / resize / blur consistency"],
             ["Main metric", "ROC-AUC", "Balanced accuracy, F1", "Accuracy, F1, ROC-AUC, with 95% CI"]],
            widths=[1.2, 1.55, 1.55, 1.9], size=9, align=["l", "l", "l", "l"]),
        H2("2.2 Genuinely new in this project"),
        P("The following items are new in the sense that they do not appear in the two papers as read, or that they are put to a different use. None of them is a new learning algorithm."),
        N("**A deployable, CPU-only heterogeneous ensemble.** HEDGE fuses routes built on large foundation-model backbones trained on eight GPUs. Here the same fuse-in-logit-space idea is realised "
          f"with four small CNNs, and the whole analysis (four routes, fusion) runs in a median {v['pred_s']} s on one desktop CPU."),
        N("**A measured ablation of the fusion rules.** The same held-out logits were fused seven ways (deployed weights and gates, no gates, each gate alone, equal weights, probability averaging, majority vote). "
          f"The result is reported even though it is unflattering: the gates fired on {v['g1']} of {v['n']:,} images (Gate 1) and {v['g2']} (Gate 2) and removing them gave {v['ng_acc']} instead of {v['acc']}."),
        N("**A per-image robustness-consistency check.** Every analysis re-tests the image after JPEG q=60, a half-size resample and a 5x5 Gaussian blur and shows how many of the four outcomes agree. "
          "The same three degradations were applied to 1,000 test images to measure how far the cue survives, which is what makes the on-screen number interpretable."),
        N("**Explanations placed next to the votes.** Grad-CAM heat maps for the predicted class are produced for three routes and shown beside the per-route votes, the weights actually used and the gate "
          "messages, so that disagreement between routes is visible rather than averaged away."),
        N(f"**A cross-domain probe that is reported as a failure.** Models trained on CIFAKE were tested on 600 full-resolution images from a different source; the ensemble scored {v['xd_acc']} (ROC-AUC {v['xd_auc']}). "
          "Reporting this keeps the in-domain numbers from being read as general ability."),
        N("**A complete, tested application.** The Flask JSON API, the React interface, the upload guards, the status page and the 19 unit tests plus 29 smoke checks turn the experiment into a tool that "
          "another person can run with one command."),
        H2("2.3 Standard components used as they are"),
        P(f"The backbones (EfficientNet {c('efficientnet')}, ResNet {c('resnet')}, MobileNetV3 {c('mobilenetv3')}), the ImageNet initialisation, AdamW {c('adamw')} with cosine decay, the focal loss {c('focal')}, "
          f"Grad-CAM {c('gradcam')} through the pytorch-grad-cam library {c('pytorch_grad_cam')}, the bootstrap interval {c('bootstrap')} and the calibration measure {c('calibration')} are all taken from the literature "
          "without modification. The fusion weights and gate thresholds are engineering defaults, not tuned values, and the datasets are public (CIFAKE for training, a Hugging Face real/AI set for the probe)."),
        H2("2.4 What the measurements say about the novelty"),
        P(f"The ensemble reached {v['acc']} accuracy and ROC-AUC {v['auc']} on the {v['n']:,}-image held-out subset, against {v['a1_acc']} for the best single route on accuracy. The two 95% bootstrap intervals "
          f"({v['ci']} and {v['a1_ci']}) overlap, so a gain in accuracy cannot be claimed; the higher ROC-AUC ({v['auc']} against {F.f4(F.BR['a1']['roc_auc'])}) is the clearer benefit of combining routes. "
          "The comparison with the base paper is therefore a comparison of design, not of scores: the task, the data, the training regime and the metric emphasis all differ (Chapter 8 of the full report)."),
    ]


def contribution_blocks():
    v = _v()
    return [
        P("The contributions of the project, in the order in which they appear in the report, are:"),
        N("A four-route heterogeneous CNN ensemble for real versus AI-generated image detection (EfficientNet-B0 with normal and distortion-hardened augmentation, ResNet50 at 320 px with flip test-time "
          "augmentation, MobileNetV3-Large with focal loss), trained from ImageNet weights on a CPU-only machine."),
        N("A logit-space weighted fusion with two deterministic gates, implemented in `app/ensemble.py`, with every gate decision returned to the user as text."),
        N(f"A reproducible evaluation on a class-balanced CIFAKE subset ({F.DATA['train_real'] + F.DATA['train_fake']:,} train, {F.DATA['val_real'] + F.DATA['val_fake']:,} validation, {F.DATA['test_real'] + F.DATA['test_fake']:,} test images): "
          f"accuracy {v['acc']}, F1 {v['f1']}, ROC-AUC {v['auc']}, with bootstrap intervals, expected calibration error ({v['ece']}), a threshold sweep and a fusion ablation."),
        N(f"A robustness study (JPEG, resize, blur, noise) and a cross-domain probe that show where the models fail: resize and blur reduce the ensemble to {v['r_resize']} and {v['r_blur']}, and the probe is at chance ({v['xd_acc']})."),
        N("Grad-CAM explanations on three routes, generated per request from real gradients, and a per-image robustness-consistency score shown with the verdict."),
        N("A working application: Flask JSON API (`/api/analyze`, `/api/predict`, `/api/insights`, `/api/config`, health and sign-in), a React web interface with analysis, insights, model and status pages, "
          "upload validation and consistent JSON errors."),
        N("A verification record: 19 pytest tests, 29 smoke-test checks, measured latency on an idle machine, and a documented list of what was not measured."),
    ]


# ------------------------------------------------------------------ document 10
def scope_blocks():
    v = _v()
    return [
        P("The scope states what the delivered system covers and, just as importantly, what it deliberately leaves out. Everything under \"in scope\" was built and measured; items under \"out of scope\" "
          "were not attempted and no result is claimed for them."),
        H2("1.1 In scope"),
        B("Binary classification of a single still image as REAL or AI_GENERATED, with a probability and a confidence word (High at 0.85 or above, Moderate at 0.60 or above, otherwise Low).",
          "Four CNN routes (EfficientNet-B0 A1 and A2, ResNet50 B, MobileNetV3-Large C) fine-tuned from ImageNet weights, fused in logit space with two gates.",
          "Grad-CAM heat maps for three routes (A1, B, C) on the predicted class, shown as overlays on the uploaded image.",
          "A robustness check: the image is re-classified after JPEG q=60, a half-size resample and a Gaussian blur, and the agreement k/n is reported.",
          "A local web application: Flask JSON API on port 8414, React interface on port 5414, a demo sign-in with a signed 12-hour token, PNG, JPG, JPEG and WEBP uploads up to 10 MB.",
          "Training and evaluation scripts, a class-balanced CIFAKE subset, a cross-domain probe set, and the metric artifacts that the Insights page displays."),
        H2("1.2 Out of scope"),
        B("Video, audio and face-swap detection. The base paper's domain (faces in video) is not covered.",
          "Identifying which generator produced an image, localising edited regions inside a real photograph, or detecting partially generated (inpainted) images.",
          "Training on the full 100,000-image CIFAKE training set, on several generators, or on high-resolution images; only a 6,000-image training subset was used.",
          "Multi-user accounts, a database, per-user history, hosting on a public server, or processing of images in bulk.",
          "GPU training or inference, quantisation, and mobile deployment.",
          "Legal or forensic certification: the output is a statistical estimate and not proof of origin."),
        H2("1.3 Users and environment"),
        P(f"The intended user is an analyst, student or fact-checker who runs the tool locally and uploads an image to obtain a second opinion with an explanation. All measurements were made on one machine "
          "(Intel Core i5-12500, 6 cores and 12 threads, 15.7 GB RAM, no GPU, Windows 11, Python 3.11.9, torch 2.14.1 for CPU). The upload limit is 10 MB and images smaller than 8 x 8 pixels are refused."),
    ]


def assumption_blocks():
    return [
        P("The results and the design rest on the following assumptions. A reader who cannot accept one of them should treat the corresponding result with caution."),
        N("CIFAKE labels are correct: 60,000 CIFAR-10 photographs are taken as REAL and 60,000 Stable Diffusion v1.4 images as AI_GENERATED, as published by the dataset authors " + c("cifake") + "."),
        N("A class-balanced random subset (seed 42) represents the full dataset well enough to rank the routes; the validation and test subsets are disjoint from the training subset."),
        N("The uploaded image is a single, unedited still in RGB; images with an alpha channel or palette are converted to RGB before analysis."),
        N("The deployed models are the checkpoints produced by the documented training run; the fusion weights (0.35, 0.15, 0.25, 0.25) and the gate settings (2.5, 2.5, 0.75) are fixed defaults."),
        N("The user runs the application on a trusted local machine; the demo sign-in is a convenience and not an access-control mechanism for a shared server."),
        N("Test-time degradations (JPEG q=60, half-size resample, 5x5 blur, Gaussian noise sigma 6) stand in for what social platforms do to images; they were not copied from any particular platform."),
    ]


def limitation_blocks():
    v = _v()
    return [
        P("The limitations below are those that most affect how the reported numbers should be read. They are stated as findings, not apologies."),
        N(f"**Small, low-resolution, single-generator data.** The models saw 6,000 of the 100,000 CIFAKE training images, for three to five epochs, because training is CPU-only. CIFAKE images are 32 x 32 JPEG and "
          "come from one generator (Stable Diffusion v1.4). The in-domain accuracy cannot be taken as evidence about modern high-resolution generators."),
        N(f"**No cross-domain generalisation.** On 600 full-resolution images from another source the ensemble scored {v['xd_acc']} (ROC-AUC {v['xd_auc']}) and route A1 {v['xd_a1']}; three routes labelled almost "
          "every image AI-generated. The probe changes resolution and content as well as generator, so the cause cannot be separated, but the practical conclusion is plain: Objective 4 was measured and not achieved."),
        N(f"**Fragile to resizing and blur.** On 32 px images a half-size resample or a 5x5 blur reduced the ensemble to {v['r_resize']} and {v['r_blur']}; JPEG q=60 and noise cost about four to five points. "
          "The distortion-hardened route A2 was not more robust than A1."),
        N(f"**Bias toward the AI-generated class.** The false-positive rate is {v['fpr']} and the false-negative rate {v['fnr']}; the ensemble predicts AI-generated for {v['pfr']} of images although the true share is 50%. "
          "A real photograph is therefore more likely to be flagged than a fake is to be missed."),
        N(f"**Gates and weights are untuned and did not help.** The gate thresholds and fusion weights are engineering defaults. Gate 1 fired on {v['g1']} images and Gate 2 on {v['g2']}; the ensemble without gates "
          f"scored {v['ng_acc']}, two images better."),
        N(f"**Optimistic threshold analysis.** The sweep that shows accuracy peaking at {v['best_acc']} (threshold {v['best_thr']}) was computed on the test subset. A threshold chosen there is optimistic; a separate "
          "validation set would be needed to set the operating point. The deployed threshold remains 0.5."),
        N("**One run per route.** Each route was trained once (seeds 42 to 45). No seed study was run, so the ranking of the routes carries run-to-run uncertainty beyond the bootstrap interval."),
        N("**Explanations are qualitative.** Grad-CAM maps were inspected by eye. No deletion or insertion test, localisation benchmark or user study checks that the highlighted regions are faithful or useful."),
        N("**Calibration varies by route.** The ensemble's expected calibration error is " + v["ece"] + ", but route C reached 0.122 and route B 0.058, so the per-route probabilities shown in the interface should not be read as reliable likelihoods."),
        N("**Demo security only.** The sign-in uses one fixed demo account whose credentials are returned by `/api/config`, and the token-signing key defaults to a development value unless an environment variable overrides it. "
          "This is acceptable for a local demonstration and unsuitable for a shared deployment."),
        N("**No database and no history.** The application stores no uploads and no results; this protects privacy but means that an analysis cannot be reopened or audited later."),
        N("**Faces and video are not addressed.** The base paper's domain was not implemented; the comparison with it is a comparison of approach only."),
    ]


def not_measured_blocks():
    return [
        P("Some things that a complete evaluation would include were not measured. They are listed so that the absence of a number is not mistaken for a good result."),
        B("A seed study: repeated training with different seeds and the spread of every metric.",
          "Training on the full CIFAKE training set, and on other generators (GAN, newer diffusion models) or higher resolutions, and a per-generator accuracy breakdown.",
          "A quantitative faithfulness test for Grad-CAM (deletion/insertion curves) and any user study of whether the heat maps help an analyst.",
          "Unit tests of `explainability.py` and `robustness.py`; load or concurrency testing of the API; behaviour under adversarial perturbations or attacks designed to fool the detector.",
          "GPU timing and the effect of quantisation; latency on machines other than the one described.",
          "A validated operating threshold, and calibration of the fused probability (for example temperature scaling).",
          "A like-for-like comparison with the base paper's method on its own datasets: the CTrue cross-dataset table is an image in the paper and was not quoted, and CTrue was not re-implemented."),
    ]


# ------------------------------------------------------------------ document 12
def walkthrough_blocks():
    v = _v()
    return [
        P("This section walks through the code that carries the design. The listings are copied from the repository in the state in which the results were measured."),
        H2("3.1 Upload validation and decoding"),
        CODE(src("app/preprocessing.py", 28, 45), 8.5),
        CODE(src("app/preprocessing.py", 48, 65), 8.5),
        P("`validate_upload` refuses a missing file, a file whose extension is not png, jpg, jpeg or webp, an empty body and a body larger than the configured 10 MB limit. `decode_image` opens the bytes twice: "
          "once with `verify()` to reject corrupt data and once to convert to RGB, and then refuses images smaller than 8 x 8 pixels. All failures raise `PreprocessingError`, which the API turns into a 400 response with a "
          "readable message. The image is decoded in memory and nothing is written to disk."),
        H2("3.2 Four routes and test-time augmentation"),
        CODE(src("app/inference.py", 69, 87), 8.5),
        P("The image is resized separately for each route (224 px for A1, A2 and C, 320 px for B) and normalised with the ImageNet mean and standard deviation. Route B is evaluated twice, on the image and on its "
          "horizontal flip, and the two logit pairs are averaged. The function returns raw logits, not probabilities, because the fusion operates on logits. The four models are loaded once under a lock and "
          f"kept in memory; the complete `/api/predict` call took a median of {v['pred_s']} s on a 32 px image and {v['pred_hi']} s on a 1,024 px image."),
        H2("3.3 Logit fusion and the two gates"),
        CODE(src("app/ensemble.py", 23, 35), 8.5),
        CODE(src("app/ensemble.py", 50, 70), 8.5),
        CODE(src("app/ensemble.py", 73, 102), 8.5),
        P("`fuse_logits` normalises the weights and returns the weighted sum of the logit pairs. Gate 1 looks at route B only: if its margin (the difference between its two logits) is at least 2.5 and all three other routes "
          "point the other way, B is dropped and the remaining weights are renormalised. Gate 2 compares B and C: if they agree on a class with margins of at least 2.5 each and the fused direction differs, the fused logits "
          "are moved by 0.75 toward that class (and by half of that, in the opposite direction, for the other logit). Both gates return an explanatory string that the interface shows. "
          f"On the test subset Gate 1 changed the result on {v['g1']} of {v['n']:,} images and Gate 2 on {v['g2']}, which is why the ablation could not show a benefit."),
        H2("3.4 Grad-CAM on the predicted class"),
        CODE(src("app/explainability.py", 17, 25), 8.5),
        CODE(src("app/explainability.py", 38, 69), 8.5),
        P("The target layer is the last convolutional block of each network (`features[-1]` for EfficientNet and MobileNetV3, `layer4[-1]` for ResNet50). The gradient of the predicted class score with respect to that layer "
          "gives a coarse grey-scale map, which is blended onto the resized image and returned as a PNG data URL. The hooks are released in a `finally` block so that repeated requests do not accumulate hooks. "
          "Maps are produced for A1, B and C; A2 shares its architecture with A1 and is not drawn separately."),
        H2("3.5 Robustness variants and the consistency score"),
        CODE(src("app/robustness.py", 9, 34), 8.5),
        CODE(src("app/inference.py", 129, 143), 8.5),
        P("`make_variants` returns the original plus a JPEG copy at quality 60, a half-size copy scaled back up, and a 5 x 5 Gaussian blur with sigma 1. `predict_with_robustness` classifies each with the full ensemble and "
          "counts how many outcomes equal the original's; the interface shows the result as k/n. Because a degraded copy is classified by the same models, this score measures label stability and says nothing about "
          f"correctness. The 1,000-image study showed why it matters: resize and blur drop the ensemble to {v['r_resize']} and {v['r_blur']} on 32 px images."),
        H2("3.6 The analysis endpoint"),
        CODE(src("app/api.py", 115, 140), 8.5),
        CODE(src("app/routes.py", 72, 100), 8.5),
        P("`/api/analyze` requires the bearer token. Models are loaded on first use; a missing checkpoint gives a 503 whose message names the missing files, and any other loading failure gives a generic 500. "
          "Validation and decoding errors become a 400, HTTP errors such as 413 pass through to the JSON-aware handler, and unexpected exceptions are logged and returned without internal detail. "
          "`_run_analysis` calls the prediction, builds one entry per route, runs Grad-CAM for A1, B and C (a failure on one route yields `null` for that map rather than failing the request) and the robustness check, "
          f"and assembles the response. The whole call took a median of {v['an_s']} s on a 32 px image and {v['an_hi']} s on a 1,024 px image; the difference to `/api/predict` is the cost of the three heat maps and the three extra classifications."),
    ]


def decision_blocks():
    v = _v()
    rows = [
        ["Four heterogeneous routes instead of one larger model",
         "Different architectures and resolutions make different errors; small models train on CPU",
         f"Ensemble ROC-AUC {v['auc']} against 0.9749 to 0.9828 for single routes; accuracy gain over A1 (0.55 points) is within the intervals"],
        ["Fusion in logit space",
         "Logits keep the strength of each vote; probabilities saturate near 0 and 1",
         f"Probability averaging scored {v['pavg_acc']} accuracy but ROC-AUC {v['pavg_auc']}; majority vote ROC-AUC {v['maj_auc']}; logit fusion kept the highest AUC"],
        ["Fixed weights 0.35 / 0.15 / 0.25 / 0.25",
         "A1 was expected to be strongest; weights are transparent and configurable",
         f"Equal weights gave {v['eq_acc']}, a 0.2-point difference (4 images): the weights are not shown to matter"],
        ["Two deterministic gates",
         "Guard against one over-confident outlier route and against a strong B+C consensus overruled by the average",
         f"Fired on {v['g1']} and {v['g2']} images; no gain. Kept because they are cheap, logged and explainable, but the evidence does not support them on this data"],
        ["Distortion-hardened twin (A2)",
         "Train one EfficientNet with blur, noise, JPEG and resampling augmentation to resist social-media processing",
         f"A2 was not more robust than A1 (resize 53.3% against 59.1%); it did show a slightly higher ROC-AUC (0.9769 against 0.9749)"],
        ["ImageNet weights, upper blocks fine-tuned",
         "CPU-only training; pre-trained features transfer to the new task",
         "Trainable parameters 1.1 M to 15.0 M of 4.0 M to 23.5 M; best validation F1 0.8902 to 0.9270 after three to five epochs"],
        ["Focal loss (gamma 2) on MobileNetV3",
         "Give a different training signal to the lightweight route",
         "Route C had the highest calibration error (0.122); the effect of the loss was not isolated by a separate run"],
        ["Horizontal-flip test-time augmentation on ResNet50 only",
         "B is the high-resolution route; flip averaging steadies its logits at a small cost",
         "B was the most biased toward AI-generated (recall 0.991, precision 0.793); the TTA effect was not isolated"],
        ["Grad-CAM on A1, B and C, predicted class",
         "Gradient maps need no retraining and work for all three architectures; A2 duplicates A1's architecture",
         "Maps judged qualitatively; heat maps and robustness add about 1.45 s to the 0.25 s verdict"],
        ["Per-image robustness consistency (k/n)",
         "Tell the user whether the verdict survives the processing an image normally undergoes",
         f"Justified by the study: resize and blur cut the ensemble to {v['r_resize']} and {v['r_blur']}"],
        ["Decision threshold kept at 0.5",
         "A threshold tuned on the test set would be optimistic",
         f"Sweep on the test subset peaks at {v['best_acc']} ({v['best_thr']}); FPR falls from {v['fpr']} to {v['t07_fpr']} at 0.7 - a possible gain once a validation set is used"],
        ["Local, file-based, no database; demo token",
         "Images stay on the machine; the system has no user data to store",
         "Privacy and simplicity gained; no history or audit trail"],
        ["Additive JSON API beside the original pages",
         "Let the React interface use the models without changing the classic Jinja pages and `/predict`",
         "Both interfaces run on the same functions; 19 tests and 29 smoke checks pass"],
    ]
    return [
        P("Each decision below is stated with the reason for it and with what the measurements later showed. Where the measurements did not support a decision, that is said."),
        TAB("Implementation decisions, reasons and measured outcomes", ["Decision", "Reason", "What the measurements showed"], rows,
            widths=[1.6, 2.1, 2.7], size=9, align=["l", "l", "l"]),
        P("Taken together the table shows a design that is sound in structure but that was not tuned: the decisions that rest on engineering judgement (weights, gates, thresholds) are neither confirmed nor refuted by "
          "a statistically meaningful difference, and the decisions that depend on generalisation are limited by the data."),
    ]


# ------------------------------------------------------------------ chapter 9 (and document 15, part 1)
def _objective_rows():
    v = _v()
    return [
        ["1", "Assemble a dataset of real photographs and AI-generated images", "Partly met",
         "CIFAKE subset (one generator, 32 px) plus a 600-image full-resolution probe from another source; not several generators"],
        ["2", "Preprocess and augment the images", "Met",
         "Per-route resizing, ImageNet normalisation and augmentation; the distortion-hardened route did not improve resize/blur robustness"],
        ["3", "Train CNN classifiers", "Met",
         f"Four routes; ensemble accuracy {v['acc']}, F1 {v['f1']}, ROC-AUC {v['auc']} on {v['n']:,} held-out images"],
        ["4", "Evaluate cross-generator performance", "Measured, not achieved",
         f"Cross-domain probe: accuracy {v['xd_acc']}, ROC-AUC {v['xd_auc']} (chance level); generator and domain shift not separable"],
        ["5", "Apply Grad-CAM", "Met (qualitative)",
         "Heat maps for three routes in every analysis; faithfulness not measured"],
        ["6", "Deploy an interface with verdict, confidence and explanation", "Met",
         f"Flask API + React app; `/api/analyze` median {v['an_s']} s on CPU; 19/19 tests, 29/29 smoke checks"],
    ]


def conclusion_blocks():
    v = _v()
    return [
        H2("9.1 Summary of the work"),
        P("The project set out to detect AI-generated images with convolutional neural networks and to explain each decision with Grad-CAM. The result is VeriVision AI: four ImageNet-pretrained CNN routes "
          "(EfficientNet-B0 with two augmentation regimes, ResNet50 at 320 px and MobileNetV3-Large), fused in logit space with two deterministic gates, together with Grad-CAM heat maps, a per-image robustness "
          "check and a Flask and React application that runs entirely on the user's machine. The shipped models were first trained on synthetic demonstration images, whose perfect scores carry no meaning; "
          "they were replaced for this report by models trained on a real data subset, and every number in the report comes from those models."),
        P(f"On a class-balanced subset of the CIFAKE benchmark {c('cifake')} (6,000 training, 1,200 validation and 2,000 held-out test images) the ensemble reached an accuracy of {v['acc']} (95% interval {v['ci']}), "
          f"F1 {v['f1']} and ROC-AUC {v['auc']}. A single analysis through the API takes a median of {v['pred_s']} s for the verdict alone and {v['an_s']} s with the heat maps and the robustness check, on a desktop CPU."),
        H2("9.2 Objectives achieved"),
        TAB("Objectives of the project against the measured outcome", ["No.", "Objective", "Status", "Evidence"], _objective_rows(),
            widths=[0.4, 1.9, 1.0, 3.1], size=9, align=["c", "l", "l", "l"]),
        H2("9.3 Key findings"),
        N(f"The ensemble is the best model by ROC-AUC ({v['auc']}), but its accuracy advantage over the best single route (A1, {v['a1_acc']}) is not statistically distinguishable: the two bootstrap intervals overlap."),
        N(f"The fusion gates did not help. Gate 1 fired on {v['g1']} of {v['n']:,} images and Gate 2 on {v['g2']}; the ensemble without gates scored {v['ng_acc']}. Logit-space fusion matched probability averaging on accuracy "
          f"and beat it, and majority voting, on ROC-AUC."),
        N(f"Errors lean toward the AI-generated class (false-positive rate {v['fpr']}, false-negative rate {v['fnr']}). Wrong answers lie close to the decision boundary (mean fused margin {v['m_bad']} against {v['m_ok']} for correct answers), "
          f"and all four routes agree on {v['unan']} of images."),
        N(f"Resizing and blurring remove the detectable cue on 32 px images: the ensemble falls to {v['r_resize']} and {v['r_blur']}, while JPEG q=60 and noise cost about four to five points. Distortion-hardened training did not change this."),
        N(f"The models do not transfer: on 600 full-resolution images from another source the ensemble scored {v['xd_acc']} (ROC-AUC {v['xd_auc']}). Strong in-domain scores on CIFAKE therefore say little about modern generators."),
        N(f"Compared with the base paper {c('base')} the only like-for-like figure is ROC-AUC: {v['auc_pct']} here in-domain on CIFAKE against 98.9% on FaceForensics++ in the paper. The paper's DFDC figure (77.0%) and this project's "
          f"cross-domain figure ({F.pct(F.XD['ensemble']['roc_auc'], 1)}) both fall when the data change, but the tasks, data and training regimes differ, so neither is evidence that one method is better."),
        H2("9.4 Practical applications"),
        P("As built, the tool suits teaching and demonstration: it shows how an ensemble, an explanation and a robustness check can be combined into one interface that runs offline. For an analyst it is a second opinion "
          "on small, compressed images similar to its training data, to be read together with the per-route votes, the heat map and the consistency score. It should not be used to decide a dispute on its own."),
        H2("9.5 Known limitations"),
        P(f"The limits that matter most are the small low-resolution single-generator training data, the chance-level cross-domain result, the fragility to resizing and blur, the bias toward the AI-generated class, "
          "the untuned gates and thresholds, the single training run per route, the qualitative explanations and the demonstration-grade sign-in. They are discussed in Chapters 1 and 8 and in the scope and limitations "
          "document, and the items that were not measured are listed there."),
    ]


def chapter9_blocks():
    return [H1("CHAPTER 9: CONCLUSION")] + conclusion_blocks()


# ------------------------------------------------------------------ chapter 10 (and document 15, part 2)
def future_blocks():
    v = _v()
    return [
        H2("10.1 Improvements to the existing system"),
        N("**Train on the full data and on more generators.** Use all 100,000 CIFAKE training images and add GAN and newer diffusion generators at several resolutions, then report accuracy per generator. "
          f"This is the direct remedy for the chance-level cross-domain result ({v['xd_acc']})."),
        N("**Tune the operating point on a validation set.** Choose the decision threshold, the fusion weights and the gate thresholds on held-out validation data, not on the test set. The sweep suggests that a threshold "
          f"of 0.7 would lower the false-positive rate from {v['fpr']} to {v['t07_fpr']}; this must be confirmed on separate data."),
        N("**Add features that survive resizing.** Frequency-domain inputs " + c("frank2020") + " or frozen foundation-model features with a linear probe " + c("ojha2023") + " transfer better across generators in the literature "
          "and could be added as a fifth route; whether they survive the half-size resample that defeated the CNNs here is an experiment to run."),
        N("**Calibrate the probabilities.** Apply temperature scaling per route and to the fused logits so that the confidence words (High, Moderate, Low) correspond to measured accuracy " + c("calibration") + "."),
        N("**Run a seed study.** Repeat training with five or more seeds, report mean and spread, and re-test whether the ensemble gain and the A2 result survive."),
        H2("10.2 Additional features"),
        B("A per-generator or per-source breakdown on the Insights page once data from several generators exist.",
          "Batch upload and a downloadable report (verdict, votes, heat maps, robustness) for an analyst's case file.",
          "A saved-analysis history with per-user accounts and a database, with an explicit retention policy.",
          "Heat maps for route A2 and a switch between Grad-CAM variants, together with a short plain-language reading of each map.",
          "A \"cannot decide\" outcome when the routes disagree or when the image is far from the training resolution, instead of always returning a label."),
        H2("10.3 Scalability and deployment"),
        P(f"The analysis is CPU-bound and takes a median of {v['an_s']} s with explanations. A deployment for several users would run the API behind a production WSGI server with a request queue, move the heat-map "
          "and robustness work to a background job, load models once per worker and cache results by image hash. A GPU would shorten training from hours to minutes and allow larger backbones and the full dataset. "
          "Before any shared deployment the demo account must be replaced with real authentication, the secret key must be set through the environment, and the demo credentials must no longer be returned by `/api/config`."),
        H2("10.4 Further research"),
        N("**Quantitative faithfulness of the explanations.** Test the Grad-CAM maps with deletion and insertion curves and with a small user study, and compare them with other attribution methods."),
        N("**Separating generator shift from domain shift.** Build a probe in which the real and fake images share content and resolution but differ in generator, so that the cause of the cross-domain failure can be identified."),
        N("**Adversarial and post-processing robustness.** Measure the detector under compression chains, screenshots, resizing pipelines and deliberate attacks designed to remove generation traces."),
        N("**One-class and pseudo-fake training for general images.** The base paper's one-class idea " + c("base") + " was developed for faces; testing whether pseudo-fake training helps a general-image detector to generalise is an open question that this project did not address."),
    ]


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + future_blocks()
