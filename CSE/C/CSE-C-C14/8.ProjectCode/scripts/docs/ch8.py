"""Chapter 8: Results and output screens (VeriVision AI). Every number is read from facts.py (experiments/cifake/metrics.json,
docs/metrics/*.json). The same blocks feed the full report and, without the chapter heading, 14.RESULTS.docx."""

from . import facts as F
from .blocks import B, FIG, H1, H2, N, P, PAIR, TAB
from .refs import CITE as R

SH = F.shot
BR_ORDER = ["a1", "a2", "b", "c"]
NAME = F.BRANCH_NAME


def pc(x, d=1):
    return f"{x * 100:.{d}f}%"


def S(name, caption, base=5.6, max_h=2.6):
    """Screenshot figure whose width keeps the picture short enough to share a page with text."""
    return FIG(SH(name), caption, F.shot_w(SH(name), base, max_h))


def _setup():
    m = F.LATENCY.get("machine", {})
    return [
        H2("8.1 Experimental Set-up"),
        P("Every measurement in this chapter was made on one machine: an Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory, no GPU, Windows 11, Python 3.11.9, PyTorch 2.14.1 (CPU build), "
          "torchvision 0.29.1, Flask 3.1.3 and scikit-learn 1.9.1. The screens of Section 8.2 were captured from the running application at 1440 x 900 pixels "
          "after the four routes had been retrained on real data. The models that the repository originally shipped had been trained on synthetic demo images and scored 100% on every metric, which says nothing about real images; "
          "they are kept only in `models/demo_backup/` and none of their numbers is used below."),
        TAB("Evaluation set-up used for every result in this chapter",
            ["Item", "Setting"],
            [["Training data", "CIFAKE subset [8]: 3,000 real (CIFAR-10 [9]) + 3,000 Stable Diffusion v1.4 [10] images, 32 x 32 px; 6% of the 100,000 official training images"],
             ["Validation data", "600 + 600 images from the official training split, disjoint from the training subset; used for early stopping"],
             ["Held-out test", f"1,000 real + 1,000 AI-generated images from the official test split (n = {F.N_TEST:,}); never used for training"],
             ["Robustness subset", "First 500 real + 500 AI-generated test images (1,000), the same images in every condition"],
             ["Cross-domain probe", "300 real photographs + 300 AI-generated images from another public source (full resolution, about 640 px and 1024 px); generators not named by the source"],
             ["Training", "AdamW, cosine decay, early stopping on validation F1; epochs A1 5, A2 5, C 5, B 3; seeds 42 to 45; single run per route"],
             ["Metrics", "Accuracy, precision, recall, F1, ROC-AUC, balanced accuracy, confusion matrix, 95% bootstrap interval (2,000 resamples), expected calibration error (15 bins)"]],
            widths=[1.4, 5.0], align=["l", "l"], size=9.5),
        P("The test subset is balanced, so accuracy and balanced accuracy coincide. All images are 32-pixel JPEG thumbnails: a well-known public benchmark, but nothing in this chapter says how the models behave on modern high-resolution generators."),
    ]


def _screens():
    return [
        H2("8.2 Output Screens"),
        P("The screens below were captured from the running application with real data in it: the test images `fake_00000.png` and `real_00000.png` from the CIFAKE test subset, and two full-resolution images from the cross-domain probe. "
          f"The web app is served on port {F.WEB_PORT} and talks to the Flask API on port {F.API_PORT}; the demo account is `{F.DEMO_EMAIL}`."),
        PAIR([(SH("01_landing_light.png"), "Landing page (light theme): the four routes with their input sizes and fusion weights, read live from the API."),
              (SH("03_login.png"), "Sign-in page: the demo account is shown beside the form; images are analysed locally.")], 3.15),
        PAIR([(SH("07_result_verdict.png"), "Result for `fake_00000.png`: \"Likely AI-generated\", 99.25% (High confidence), 4/4 branches agree; the bar splits the fused probability into Real 0.8% and AI-generated 99.2%."),
              (SH("17_result_real.png"), "Result for `real_00000.png`: \"Likely a real image\", 97.17% (High confidence), Real 97.2% / AI-generated 2.8%, 4/4 branches agree, robustness consistency 4/4 (green).")], 3.15),
        S("08_result_votes_robustness.png",
          "Branch votes and robustness check for the same image. All four routes vote AI-generated (99.3%, 100.0%, 99.4%, 89.9%) with fusion weights 35, 15, 25 and 25%. "
          "The re-test agrees on the original, JPEG and blur variants but reads the 2x resized copy as Real, giving consistency 3/4 and an amber warning."),
        PAIR([(SH("09_result_gradcam.png"), "Grad-CAM tab for route A1 (EfficientNet): the activation concentrates on the right edge of the subject."),
              (SH("10_result_gradcam_resnet.png"), "Grad-CAM tab for route B (ResNet50) on the same image: activation spreads over most of the subject.")], 3.15),
        PAIR([(SH("18_result_hires_ai.png"), "Cross-domain AI-generated image (`fake_0000.jpg`, 1024 px): correctly called AI-generated with 100.00% confidence, but the robustness check agrees on only 3/4 variants."),
              (SH("19_result_hires_real.png"), "Cross-domain real photograph (`real_0000.jpg`): called AI-generated with 100.00% confidence and 4/4 consistency. This is a confident wrong answer.")], 3.15),
        P("The model is sure of both verdicts, yet the second is wrong, and the consistency check cannot flag it because every variant gives the same wrong answer. Section 8.6 measures how often this happens."),
        S("11_insights.png",
          "Model insights page: held-out ensemble metrics (accuracy 92.35%, precision 88.19%, recall 97.80%, F1 92.75%, ROC-AUC 98.65%, balanced accuracy 92.35%), the confusion matrix (869 / 131 / 22 / 978) and the clean-versus-degraded chart, all read from the evaluation files."),
        PAIR([(SH("12_models.png"), "How-it-works page with one card per route: backbone, input size, loss, fusion weight and F1."),
              (SH("13_status.png"), "System status page: the /health answer (models loaded, device cpu) and the upload rules.")], 3.15),
        P("Section 8.12 notes that the \"Validation F1\" rows of the how-it-works page show test-set F1 values. Further screens (dark theme, the page mid-animation, the landing page sections) are in Appendix C."),
    ]


def _perf():
    rows = []
    for b in BR_ORDER:
        m = F.BR[b]
        lo, hi = F.CI[b]
        rows.append([NAME[b], f"{m['accuracy']:.4f}", f"{m['precision']:.4f}", f"{m['recall']:.4f}", f"{m['f1']:.4f}", f"{m['roc_auc']:.4f}", f"{lo:.3f}-{hi:.3f}"])
    e = F.ENS
    lo, hi = F.CI["ensemble"]
    rows.append(["**Ensemble (deployed)**", f"{e['accuracy']:.4f}", f"{e['precision']:.4f}", f"{e['recall']:.4f}", f"{e['f1']:.4f}", f"{e['roc_auc']:.4f}", f"{lo:.3f}-{hi:.3f}"])
    cm_rows = []
    for b in BR_ORDER + ["ens"]:
        m = e if b == "ens" else F.BR[b]
        (tn, fp), (fn, tp) = m["confusion_matrix"]
        cm_rows.append([("**Ensemble**" if b == "ens" else NAME[b]), tn, fp, fn, tp, pc(m["fpr"]), pc(m["fnr"]), pc(m["predicted_fake_rate"])])
    ece = F.M["ece_branches"]
    h = F.HIST
    return [
        H2("8.3 Model Performance on the Held-out Test Set"),
        P(f"The first table below gives the held-out results of the four routes and the deployed ensemble on the {F.N_TEST:,} test images (single run, seed 42). "
          f"The ensemble reaches an accuracy of {pc(e['accuracy'], 2)}, an F1 of {pc(e['f1'], 2)} and a ROC-AUC of {pc(e['roc_auc'], 2)}. "
          f"The best single route, EfficientNet-B0 A1, reaches {pc(F.BR['a1']['accuracy'], 2)} accuracy and {pc(F.BR['a1']['roc_auc'], 2)} ROC-AUC, and its bootstrap interval ({F.CI['a1'][0]:.3f}-{F.CI['a1'][1]:.3f}) overlaps that of the ensemble "
          f"({F.CI['ensemble'][0]:.3f}-{F.CI['ensemble'][1]:.3f}). The 0.55-point accuracy advantage of the ensemble over A1 is therefore not statistically distinguishable on this sample; "
          "its higher ROC-AUC (0.9865 against 0.9749) and a lower false-negative rate (2.2% against 4.7%) are the clearer gains. ResNet50 B has the highest single-route ROC-AUC (0.9828) but the lowest accuracy (0.8660), "
          "because its threshold sits too far toward AI-generated: it finds 99.1% of the fakes and wrongly flags 25.9% of the real images."),
        TAB("Held-out performance of the four routes and the ensemble (n = 2,000)", ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "95% CI (accuracy)"], rows,
            widths=[2.0, 0.75, 0.8, 0.7, 0.65, 0.75, 1.0], align=["l", "c", "c", "c", "c", "c", "c"], size=9.5),
        PAIR([(F.fig("f03_confusion_matrix.png"), "Confusion matrix of the deployed ensemble: counts (left) and row-normalised (right)."),
              (F.fig("f05_roc.png"), "ROC curves of the four routes and the ensemble on the held-out test set.")], 3.2),
        TAB("Confusion-matrix counts and error rates (positive class: AI_GENERATED)", ["Model", "TN", "FP", "FN", "TP", "FPR", "FNR", "Predicted fake"], cm_rows,
            widths=[2.0, 0.55, 0.55, 0.55, 0.55, 0.7, 0.7, 1.0], align=["l", "c", "c", "c", "c", "c", "c", "c"], size=9.5),
        P(f"Every route and the ensemble predict AI-generated more often than the true 50% share (the ensemble 55.5%). The ensemble makes {F.ERR['n_wrong']} errors in 2,000: 131 real images flagged as AI-generated (false-positive rate 13.1%) and 22 fakes missed (2.2%). "
          "In a forensic setting the first kind of error, calling a genuine photograph fake, is the costly one, and it is the more frequent one here."),
        FIG(F.fig("f04_training_curves.png"), "Training and validation curves of the four routes (route B stopped after three epochs; C uses focal loss, so its loss scale differs).", 5.6),
        P(f"Validation accuracy of A1 was still rising at epoch 5 ({pc(max(h['a1']['val_acc']), 2)}); A2 and C ended at {pc(max(h['a2']['val_acc']), 2)} and {pc(max(h['c']['val_acc']), 2)}, "
          f"and B reached its best validation F1 ({max(h['b']['val_f1']):.4f}) at epoch 2 of 3. With only 3 to 5 epochs on 6,000 images (CPU-only hardware) these are not converged models; a longer run on the full 100,000 images would probably score higher."),
        PAIR([(F.fig("f10_calibration.png"), f"Reliability diagram of the ensemble (expected calibration error {F.ECE:.3f}); bin sizes are printed under the points."),
              (F.fig("f11_margin_hist.png"), "Fused logit margin of correct (green) and wrong (red) predictions on the test set.")], 3.1),
        P(f"The ensemble is well calibrated on this test set: its expected calibration error is {F.ECE:.3f}, close to the best single routes (A1 {ece['a1']:.3f}, A2 {ece['a2']:.3f}) and far below route C ({ece['c']:.3f}) and route B ({ece['b']:.3f}). "
          "The reliability curve lies slightly above the diagonal in the middle bins (a little under-confident), and 1,127 of the 2,000 images fall in the top bin. "
          "Calibration holds only on the training distribution; Section 8.6 shows that confidence does not survive a change of domain."),
    ]


def _fusion():
    v = F.VARIANTS
    names = [("full", "Deployed: weights + Gate 1 + Gate 2"), ("no_gates", "Weights only (no gates)"), ("gate1_only", "Gate 1 only"), ("gate2_only", "Gate 2 only"),
             ("equal_weights", "Equal weights + gates"), ("prob_avg", "Probability averaging (weights)"), ("majority", "Majority vote (ties to weighted)")]
    rows = [[n, f"{v[k]['accuracy']:.4f}", f"{v[k]['f1']:.4f}", f"{v[k]['roc_auc']:.4f}"] for k, n in names]
    sw = {round(r["threshold"], 1): r for r in F.SWEEP}
    return [
        H2("8.4 Fusion Rules and Decision Threshold"),
        P(f"The fusion rule of Chapter 6 was tested by replacing it, on the same cached logits, with simpler variants. The ablation table below shows that the two gates did not improve the result: Gate 1 fired on {v['full']['gate1_fired']} of 2,000 images and Gate 2 on none, "
          "and removing both gates scores 0.9245 against 0.9235 for the deployed rule, a difference of two images. "
          "Probability averaging scores slightly higher in accuracy (0.9260) but lower in ROC-AUC (0.9846), and majority voting loses ranking quality (ROC-AUC 0.9383) presumably because its score takes only a few distinct values. "
          f"The gate design follows HEDGE [{R['hedge']}], whose own ablation gained 0.37 robust-F1 points from its gates on a different, much harder benchmark; here the thresholds (2.5, 2.5, 0.75) are engineering defaults that were never tuned, and the finding is that the gates are inactive on this data."),
        TAB("Fusion-rule ablation on the held-out test set (same logits)", ["Variant", "Accuracy", "F1", "ROC-AUC"], rows, widths=[3.2, 1.0, 1.0, 1.0], align=["l", "c", "c", "c"], size=10),
        PAIR([(F.fig("f06_fusion_ablation.png"), "Accuracy and F1 of the fusion variants; the vertical axis starts at 0.905, which magnifies differences of a few images."),
              (F.fig("f07_threshold_sweep.png"), "Precision, recall, F1 and accuracy of the ensemble as the decision threshold on the fused fake probability moves from 0.1 to 0.9.")], 3.2),
        P(f"The deployed threshold is 0.5. Raising it to 0.7 or 0.8 lowers the false-positive rate to {pc(sw[0.7]['fpr'])} and {pc(sw[0.8]['fpr'])} at a cost in recall ({pc(sw[0.7]['recall'])} and {pc(sw[0.8]['recall'])}), and accuracy peaks at {pc(sw[0.7]['accuracy'])} to {pc(sw[0.8]['accuracy'])}. "
          "That gain is optimistic: the threshold was read off the test subset, and a fair choice would need a separate validation set. The sweep does show the trade-off an operator would face, "
          "since the model's error is asymmetric and a higher threshold protects real images at the price of missing more fakes."),
    ]


def _robust():
    rows = []
    lab = [("clean_subset", "Clean (1,000-image subset)"), ("jpeg", "JPEG quality 60"), ("resize", "Resize to 1/2 and back"), ("blur", "Gaussian blur 5x5, sigma 1"), ("noise", "Gaussian noise, sigma 6")]
    for k, n in lab:
        r = F.ROB[k]
        rows.append([n] + [pc(r["branches"][b]["accuracy"]) for b in BR_ORDER] + [pc(r["ensemble"]["accuracy"]), f"{r['ensemble']['roc_auc']:.3f}", pc(r["ensemble"]["predicted_fake_rate"])])
    return [
        H2("8.5 Robustness to Compression, Resizing, Blur and Noise"),
        P("The same 1,000 test images were degraded and re-scored by every route (table and chart below). JPEG compression and noise cost the ensemble about 4 to 5 accuracy points. "
          "Resizing and blur are far more damaging: ensemble accuracy falls to 61.0% and 58.3%, close to chance, and the models stop calling images AI-generated (only 12.2% and 8.9% of images are predicted fake against 55% on clean images). "
          "The ranking information is only partly lost, since ROC-AUC stays at 0.801 and 0.865: the decision threshold moves rather than the scores becoming random. "
          "Route B, trained at 320 pixels with flip augmentation, holds up best against resizing and blur (68.6% and 69.1%), but it is the least robust to JPEG (80.3%) and noise (74.6%)."),
        TAB("Accuracy under degradation (1,000 images, same images in every condition)", ["Condition", "A1", "A2", "B", "C", "Ensemble", "Ens. AUC", "Ens. pred. fake"], rows,
            widths=[1.9, 0.6, 0.6, 0.6, 0.6, 0.8, 0.75, 0.9], align=["l"] + ["c"] * 7, size=9.5),
        FIG(F.fig("f08_robustness.png"), "Accuracy of each route and the ensemble on the clean subset and four degradations (dashed line: chance).", 5.2),
        P("Route A2 was trained with blur, noise, JPEG and resampling augmentation precisely to resist these conditions, yet it is not more robust than A1 to resizing (53.3% against 59.1%) or blur (54.6% against 59.8%); "
          "its only visible benefit is on noise (87.4% against 84.1%). "
          "The same fragility appears in the application: the robustness check of the sample result in Section 8.2 flipped the verdict of the sample image under the resize variant, and a consistency below full agreement is the application's own warning to treat the result with caution."),
    ]


def _xdomain():
    rows = []
    for b in BR_ORDER:
        m = F.XD["branches"][b]
        (tn, fp), (fn, tp) = m["confusion_matrix"]
        rows.append([NAME[b], pc(m["accuracy"]), f"{m['roc_auc']:.3f}", f"{tn}/300", f"{tp}/300"])
    m = F.XD["ensemble"]
    (tn, fp), (fn, tp) = m["confusion_matrix"]
    rows.append(["**Ensemble**", pc(m["accuracy"]), f"{m['roc_auc']:.3f}", f"{tn}/300", f"{tp}/300"])
    return [
        H2("8.6 Cross-domain Probe"),
        P("Objective 4 asked for cross-generator evaluation. The probe set contains 300 real photographs and 300 AI-generated images from another public source, at full resolution and with different content (food, animals, illustrations, fantasy scenes) from the CIFAKE objects. "
          "The generators are not named by the source, so the probe tests transfer to some unseen generator and domain, not to a specific model. Because resolution, content and generator all change together, the probe cannot say which of them causes the failure."),
        TAB("Cross-domain probe, 600 images (models trained on CIFAKE only)", ["Model", "Accuracy", "ROC-AUC", "Real kept REAL", "AI found"], rows,
            widths=[2.2, 0.9, 0.9, 1.2, 1.0], align=["l", "c", "c", "c", "c"], size=10),
        FIG(F.fig("f09_cross_domain.png"), "Cross-domain accuracy (left) and per-class recall (right) of each route and the ensemble; the dashed line is chance.", 5.4),
        P(f"The result is a clear failure to generalise. The ensemble scores {pc(m['accuracy'])} with a ROC-AUC of {m['roc_auc']:.3f}, which is chance; A2, B and C call almost every image AI-generated (B keeps only 1 of 300 real photographs as real), and A1 is close to a coin flip. "
          "ROC-AUC below 0.5 for route B (0.215) means its scores are inverted on this data. The deployed confidence is meaningless here: the last pair of screens in Section 8.2 shows a real photograph called AI-generated with 100.00% confidence. "
          "Objective 4 was therefore measured and not achieved. This agrees with the literature on cross-generator transfer [3], [12], [13], but this project did not train on several generators or at several resolutions, so it cannot offer a remedy."),
    ]


def _expl():
    return [
        H2("8.7 Grad-CAM Explanations"),
        P("Grad-CAM was run on the predicted class for routes A1, B and C with the same code that the application uses. The figure below shows the first three correctly classified real images and the first three correctly classified AI-generated images of the test set, "
          "so the examples are typical and not chosen for neat heat maps."),
        FIG(F.fig("f14_gradcam_examples.png"), "Grad-CAM overlays of routes A1, B and C on the first three real (top) and first three AI-generated (bottom) correctly classified test images.", 4.2),
        P("The maps are coarse blobs, because the target layers have a 7 x 7 to 10 x 10 spatial grid that is upsampled to the image. They usually sit on the main object, but different routes pick different parts of it (for the green frog, A1 and C focus on the head, B on the body), "
          "and on the real images the maps are as strong as on the fakes. No map points to a recognisable artefact; the maps show where the evidence is, not what it is. "
          "Grad-CAM was judged by eye only (no deletion or insertion test), so the maps are not proof that the model uses a particular region."),
        FIG(F.fig("f15_gradcam_xdomain.png"), "Grad-CAM overlays on the cross-domain probe: two real photographs (both called AI-generated, 100%) and two AI images (the second called REAL, 100%).", 4.4),
        P("On the cross-domain images the maps look as confident as on CIFAKE even where the verdict is wrong (the real bread and cat photographs are called AI-generated, with maps on the food and the cat), so a heat map says nothing about whether the verdict can be trusted."),
    ]


def _compare():
    return [
        H2("8.8 Comparison with the Base Paper and the Design Reference"),
        P(f"The batch's base paper is the CTrue detector of Larue et al. [{R['base']}], a one-class face-deepfake detector; this project does not implement it. The design of the heterogeneous routes and gates follows HEDGE [{R['hedge']}]. "
          "The three works differ in task, data and compute, so the table below lists them side by side and the only like-for-like number is the ROC-AUC on data of the work's own domain."),
        TAB("Comparison with the base paper and the design reference",
            ["Aspect", "CTrue (base paper)", "HEDGE (design reference)", "This project"],
            [["Task", "Face deepfake detection, one-class", "AI-generated image detection in the wild", "Real vs AI-generated, general 32-px images"],
             ["Training data", "720 pristine FaceForensics++ videos plus pseudo-fakes", "Not itemised in this report", "6,000 CIFAKE images (6% of the set)"],
             ["Backbone", "EfficientNet-B4 (19.3 M parameters)", "DINOv3 and MetaCLIP2 based routes", "Four small CNNs, 4.0 M to 23.5 M parameters"],
             ["Compute", "Two V100 GPUs, 200 epochs, about 16 h", "8 H800 GPUs", "One CPU, 3 to 5 epochs, 13 to 53 min per route"],
             ["Headline", "AUC 98.9% on FF++ (in-domain)", "Balanced accuracy 98.3% on five benchmarks", "AUC 98.65%, accuracy 92.35% on CIFAKE (in-domain)"],
             ["Cross-dataset", "AUC 77.0% on DFDC (lambda = 1 ablation)", "Robust F1 80.52, 80.89 with gates (competition set)", "AUC 49.9%, accuracy 51.0% (cross-domain probe)"],
             ["Gates / fusion", "Not used (single model)", "Logit fusion plus dual gating", "Logit fusion plus two gates (no gain here)"]],
            widths=[1.0, 1.8, 1.8, 1.8], align=["l", "l", "l", "l"], size=9),
        P("In-domain, the project's ROC-AUC (98.65%) is close to the base paper's FaceForensics++ figure (98.9%), but the two numbers measure different tasks on different data, with a very different training budget, and they are not evidence that one method is better. "
          "Cross-dataset, the base paper's DFDC AUC of 77.0% is well below its in-domain value yet well above this project's 49.9%; the base paper was designed for generalisation and this project was not. "
          "The CTrue cross-dataset table is an image in the PDF and is not quoted. The comparison with HEDGE is about design only: the idea of logit fusion with gates is reused, and the ablation of Section 8.4 finds that the gates add nothing on CIFAKE."),
    ]


def _samples():
    lat = F.LATENCY
    return [
        H2("8.9 Sample Inputs and Outputs, Speed and Testing"),
        TAB("Sample analyses captured from the application", ["Input", "True class", "Verdict", "Confidence", "Branches agree", "Consistency", "Correct"],
            [["`fake_00000.png` (32 px)", "AI-generated", "Likely AI-generated", "99.25%", "4/4", "3/4", "Yes"],
             ["`real_00000.png` (32 px)", "Real", "Likely a real image", "97.17%", "4/4", "4/4", "Yes"],
             ["`fake_0000.jpg` (1024 px)", "AI-generated", "Likely AI-generated", "100.00%", "4/4", "3/4", "Yes"],
             ["`real_0000.jpg` (about 640 px)", "Real", "Likely AI-generated", "100.00%", "4/4", "4/4", "**No**"]],
            widths=[1.6, 0.9, 1.3, 0.8, 0.7, 0.8, 0.6], align=["l", "l", "l", "c", "c", "c", "c"], size=9),
        P("Each `POST /api/analyze` response carries the verdict and confidence word, the fused probabilities, a record per route, the Grad-CAM overlays as data URLs, the agreement count, the gate decisions and the robustness outcomes with the consistency string. "
          "Invalid input returns a JSON error (400 unsupported, empty, corrupt or tiny file; 401 no token; 413 above 10 MB; 503 model files missing)."),
        TAB("Response time of the running API (median of 8 runs, 127.0.0.1, idle machine)", ["Endpoint", "32 px image", "1024 px image"],
            [["`GET /health`", f"{lat['health']['median'] * 1000:.0f} ms", "-"],
             ["`GET /api/insights`", f"{lat['insights']['median'] * 1000:.0f} ms", "-"],
             ["`POST /api/predict` (four routes + fusion)", f"{lat['predict_cifake_32px']['median']:.2f} s", f"{lat['predict_photo_1024px']['median']:.2f} s"],
             ["`POST /api/analyze` (adds Grad-CAM x3 and robustness x4)", f"{lat['analyze_cifake_32px']['median']:.2f} s", f"{lat['analyze_photo_1024px']['median']:.2f} s"]],
            widths=[3.6, 1.3, 1.3], align=["l", "c", "c"], size=10),
        P(f"The full analysis takes under two seconds on the CPU, so the 10 to 60 seconds assumed in the first README was too pessimistic for this machine. Model loading happens once at start and is not timed; batched offline inference in the evaluation script costs {F.M['inference_seconds_per_image_batched'] * 1000:.0f} ms per image for all four routes. "
          f"The pytest suite ({F.PYTEST_TOTAL} tests) passed {F.PYTEST_PASSED} of {F.PYTEST_TOTAL} in {F.PYTEST_SECONDS:.0f} s, the end-to-end smoke test passed {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks, and the capture script walked every screen with a clean browser console. "
          "Unit tests for the Grad-CAM and robustness modules, load tests and a GPU run were not done."),
    ]


def _cases():
    return [
        H2("8.10 Success and Failure Analysis"),
        P(f"Where the ensemble succeeds. All four routes agree on {pc(F.UNANIMOUS)} of the test images; on those 1,624 images the fused label is right 96.2% of the time, against 76.3% on the other 376 (computed from the cached route logits with the weighted sum, which differs from the deployed rule on two images). Correct predictions have a mean fused margin of {F.ERR['mean_abs_margin_correct']:.2f} logit units against {F.ERR['mean_abs_margin_wrong']:.2f} for wrong ones (figure in Section 8.3): "
          "the errors are concentrated near the decision boundary, so the confidence value carries real information on CIFAKE-like images."),
        FIG(F.fig("f13_route_agreement.png"), "Agreement of each route with the final label (the vertical axis starts at 0.87).", 3.6),
        P("Where it fails. The figure below shows the first six false positives and six false negatives. The false positives are real thumbnails (a truck, a bird, an aeroplane, a car, a sailing boat, a dog) with fake probabilities from 0.51 to 0.89; "
          "the false negatives are AI-generated images with natural-looking subjects (a cat, a dog, a sailing boat, a horse) and fake probabilities from 0.07 to 0.40. Nothing in these thumbnails lets a person tell which is which either, "
          "so the errors are plausibly cases where the generator's output matches natural statistics at 32 pixels; the project did not test that explanation. Agreement with the final label is highest for A1 (96.5%) and lowest for B (91.6%), consistent with B's bias toward AI-generated."),
        FIG(F.fig("f12_failure_cases.png"), "First six false positives (real images called AI-generated, top) and first six false negatives (AI images called real, bottom) with the ensemble's fake probability.", 5.4),
        P("Two failure modes matter for use. A resized or blurred image is read as real, so a fake re-saved at a smaller size is likely to pass; and on images from outside CIFAKE the model is confidently wrong, as the real photograph of Section 8.2 shows. "
          "Neither is caught by the visible safeguards (consistency check, Grad-CAM), so the application's own wording, \"AI estimate, not proof\", is the right framing."),
    ]


def _limits():
    return [
        H2("8.11 Limitations of the Results"),
        B("**Single run per route.** Seeds 42 to 45 and one training run each: the ranking of the routes carries run-to-run uncertainty that the bootstrap interval, which resamples only the test set, does not capture.",
          "**Small training subset.** 6,000 of 100,000 CIFAKE images and 3 to 5 epochs, chosen for CPU time; a full-data run would probably score higher.",
          "**Tiny images, one generator.** CIFAKE images are 32 x 32 JPEG from one generator (Stable Diffusion 1.4). The results do not transfer to modern high-resolution generators, and there is no per-generator breakdown.",
          "**Optimistic operating point.** The threshold sweep and the fusion ablation were evaluated on the test subset itself; the deployed gate thresholds and weights are engineering defaults that were not tuned.",
          "**Qualitative explanations.** Grad-CAM maps were inspected by eye; there is no faithfulness test.",
          "**Not measured.** A user study, GPU timing, load testing, adversarial attacks, and unit tests of the explanation and robustness modules."),
    ]


def _objectives():
    return [
        H2("8.12 Objectives versus Outcomes"),
        TAB("Objectives of the project against what was measured", ["No.", "Objective", "Outcome", "Status"],
            [["1", "Assemble a dataset of real and AI-generated images", "CIFAKE subset (real CIFAR-10 + one generator) with a 6,000 / 1,200 / 2,000 split and a 600-image probe from another source; several generators were not assembled", "Partly met"],
             ["2", "Preprocess and augment for robustness", "Per-route augmentation implemented; the distortion-hardened route A2 was not more robust to resize or blur than A1", "Met, with limited effect"],
             ["3", "Train a CNN classifier", "Four routes and a fused ensemble: 92.35% accuracy, F1 92.75%, ROC-AUC 98.65% on the held-out CIFAKE test set", "Met"],
             ["4", "Evaluate cross-generator performance", "Measured on 600 full-resolution images: ensemble 51.0% accuracy, ROC-AUC 0.499 (chance)", "Measured, not achieved"],
             ["5", "Apply Grad-CAM to explain classifications", "Grad-CAM on three routes in the application and in the figures of Section 8.7; judged qualitatively only", "Met (qualitative)"],
             ["6", "Deploy behind an interface with verdict, confidence and explanation", "Flask API (8414) and React app (5414); full analysis in 1.7 to 2.0 s on CPU; 19/19 tests and 29/29 smoke checks passed", "Met"]],
            widths=[0.4, 1.9, 3.3, 1.0], align=["c", "l", "l", "l"], size=9),
        P("Note on the interface. The how-it-works page labels the held-out test F1 of each route as \"Validation F1\", and the `validation` block of `models/model_metadata.json` holds the same test-set values, not the validation F1 recorded during training (A1 0.927, A2 0.905, B 0.890, C 0.911). "
          "The numbers on screen are correct as test-set results; only the label is wrong, and the README may still describe the earlier demo-data scores."),
    ]


def blocks():
    return ([H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS"),
             P("This chapter reports what the system actually does. It starts with the experimental set-up and the output screens of the running application, then gives the model results on the held-out test set, "
               "the fusion and threshold analysis, robustness to degradation, the cross-domain probe, the Grad-CAM explanations, the comparison with the base paper, sample inputs and outputs, success and failure cases, limitations, and the objectives measured against outcomes. "
               "Several results are negative, and they are reported as findings.")]
            + _setup() + _screens() + _perf() + _fusion() + _robust() + _xdomain() + _expl() + _compare() + _samples() + _cases() + _limits() + _objectives())
