"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for VeriVision AI from facts.py (experiments/cifake/metrics.json,
docs/metrics/*.json), the paper figures (paper_figs.py) and the real screenshots.

    python -m scripts.docs.build_paper            # from 8.ProjectCode, system python
"""

import os

from . import facts as F
from . import paper_figs
from .paper import Paper
from .refs import CITE, REFS

pct, f2, f3, f4 = F.pct, F.f2, F.f3, F.f4

# references that appear in the paper (global numbers from refs.py); every one is cited below, in this set only
USED = ["base", "hedge", "empirical", "cifake", "ldm", "wang2020", "ojha2023", "frank2020", "corvi2023", "efficientnet", "resnet",
        "mobilenetv3", "focal", "adamw", "imagenet", "calibration", "gradcam", "pytorch_grad_cam", "pytorch", "bootstrap"]


def r(*keys):
    """Citation marker understood by Paper.expand: {r:1,2} -> [n], [m] numbered by first appearance."""
    return "{r:" + ",".join(str(CITE[k]) for k in keys) + "}"


def build(path):
    figs = paper_figs.make_all()
    E, B, A1 = F.ENS, F.BR, F.BR["a1"]
    ci = F.CI
    ab = F.VARIANTS
    nog = ab["no_gates"]
    rob = F.ROB
    xd = F.XD["ensemble"]
    sw = {round(s["threshold"], 1): s for s in F.SWEEP}
    lat = F.LATENCY
    wrong = F.ERR["n_wrong"]
    ece = F.ECE

    H = F.HIST
    VAL = {"va1": f3(max(H["a1"]["val_f1"])), "va2": f3(max(H["a2"]["val_f1"])), "vb": f3(max(H["b"]["val_f1"])), "vc": f3(max(H["c"]["val_f1"])), "eb": H["b"]["val_f1"].index(max(H["b"]["val_f1"])) + 1}

    P = Paper()
    authors = [[n, f"Roll No. {rn}", "Dept. of Computer Science and Engineering", F.COLLEGE, "[CITY], India", "[EMAIL]"] for n, rn in F.STUDENTS]
    authors.append([F.GUIDE, f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", F.COLLEGE, "[CITY], India", "[EMAIL]"])
    P.title_block("VeriVision AI: Detecting AI-Generated Images with a CNN Ensemble and Grad-CAM Explanations", authors)
    P.begin_two_columns()

    P.abstract(
        "Images produced by generative models are now hard to tell from photographs, yet most detectors return a bare score, are trained on a single generator and lose accuracy after resizing or compression. "
        "This paper presents VeriVision AI, a local web application that classifies an uploaded image as real or AI-generated with four ImageNet-pretrained CNN routes (two EfficientNet-B0 variants, ResNet50 and MobileNetV3-Large). "
        "The routes are fused in logit space with fixed weights and two gating rules, and every verdict is accompanied by Grad-CAM heat maps and a robustness re-check. "
        f"Trained on a class-balanced 6,000-image subset of CIFAKE and evaluated on 2,000 held-out images on a CPU-only machine, the ensemble reaches {pct(E['accuracy'], 2)} accuracy, {f4(E['f1'])} F1 and {f4(E['roc_auc'])} ROC-AUC, "
        "within the confidence interval of its best single route. The gates did not improve the result, resizing and blur lower accuracy to about 60 %, and a probe on full-resolution photographs is at chance. "
        "The work demonstrates a transparent, explainable pipeline rather than a detector that generalises across generators.",
        ["AI-generated image detection", "convolutional neural networks", "ensemble learning", "explainable AI", "Grad-CAM", "image forensics", "robustness"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Generative models can now synthesise images that human observers cannot reliably tell from photographs. Latent diffusion models produce high-resolution pictures from a text prompt on consumer hardware "
           + r("ldm") + ", so fabricated images can be used for misinformation, fraud and reputational harm at almost no cost. An analyst today has three options: inspect the image by eye for artefacts, "
           "run a single detector that returns one real-or-fake score, or use a large foundation-model detector that needs a GPU and often a cloud service. The first no longer works, the second hides disagreement "
           "between models and gives no reasons, and the third costs hardware and sends the image to a third party.")
    P.para("Detectors also generalise poorly. A classifier trained on one generator usually degrades on another " + r("wang2020", "ojha2023", "empirical") + ", and resizing or recompression on social platforms removes many of the cues "
           "it relies on " + r("frank2020", "hedge") + ". A verdict with no visual justification is hard to defend in a dispute, which makes class-activation maps attractive " + r("gradcam") + ". The base paper " + r("base")
           + " learns a one-class representation of authentic faces for deepfake detection; it is aimed at faces rather than general images and was trained for about 16 hours on two V100 GPUs.")
    P.para("VeriVision AI addresses this gap on a small scale. It is a local application that pairs a heterogeneous CNN ensemble, whose fusion follows the logit-weighting-with-gating idea of HEDGE " + r("hedge")
           + ", with Grad-CAM heat maps and a robustness re-check, and it runs on a CPU. The contributions are: (1) four complementary CNN routes fused by fixed weights and two deterministic gates and served through a Flask API and a React interface; "
           "(2) per-route votes, Grad-CAM overlays and a JPEG, resize and blur consistency check shown next to every verdict; (3) a measured evaluation with bootstrap intervals, a fusion ablation, a threshold sweep, "
           "degraded inputs and a cross-domain probe; and (4) a plain account of what the measurements do not support. Section II reviews related work, Section III describes the data, models and application, "
           "Section IV reports results and Section V concludes. The project has six objectives: assemble real and generated data, preprocess and augment it, train CNN classifiers, evaluate across generators, apply Grad-CAM and deploy the result; "
           "Section V states which were met.")
    P.sub("A", "System Hardware")
    P.para("Every measurement was taken on one machine: an Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB of RAM, no GPU, running Windows 11. The machine was shared with other jobs during training, so training times are upper bounds.")
    P.sub("B", "Software Requirements")
    P.para("Python 3.11.9, PyTorch 2.14.1 (CPU build) " + r("pytorch") + ", torchvision 0.29.1, pytorch-grad-cam 1.5.7 " + r("pytorch_grad_cam") + ", scikit-learn 1.9.1 for the metrics, Flask 3.1.3 for the API, "
           "and a React and Vite interface built with Node 24. A modern browser is the only client requirement.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("The base paper " + r("base") + " (Larue et al., CTrue) trains a one-class detector: only authentic faces, 720 pristine FaceForensics++ videos, are used for training, and manipulated examples are synthesised as pseudo-fakes. "
           "A hybrid-curvature representation separates authentic from manipulated faces on an EfficientNet-B4 backbone of 19.3 M parameters and 4.4 GFLOPs, trained for 200 epochs on two V100 GPUs (about 16 hours). "
           "It reports 98.9 % AUC on FaceForensics++ and, in an ablation with the curvature weight set to 1, 77.0 % AUC on DFDC, and runs at 74 frames per second on an RTX 3060. Its strengths are generalisation without "
           "seeing real fakes and a light inference model; its limits for this project are the face-only domain, the video setting, the AUC-only metric and the compute used to train it.")
    P.para("Work on general image forensics shows both the promise and the fragility of learned detectors. A ResNet-50 trained on one GAN transferred to other CNN generators when blur and JPEG augmentation were used " + r("wang2020")
           + ", frequency analysis exposes spectral artefacts that fade after resizing " + r("frank2020") + ", and frozen CLIP features with a linear probe transfer better to unseen generators but need a large backbone " + r("ojha2023")
           + ". Diffusion images are harder to detect than GAN images, and detectors lose accuracy on new diffusion generators " + r("corvi2023") + ". An empirical study of ten detectors on seven GAN and diffusion datasets finds strong in-distribution accuracy "
           "but weak cross-model transfer and uses Grad-CAM to inspect them " + r("empirical") + ". CIFAKE " + r("cifake") + " supplies 60,000 real and 60,000 Stable Diffusion 1.4 images at 32 px with a CNN baseline and Grad-CAM, which makes it practical on a CPU.")
    P.para("HEDGE " + r("hedge") + " combines three heterogeneous routes (DINOv3 with progressive training, a higher-resolution route and a MetaCLIP2 route), fuses their logits with fixed weights and adds dual gating; it placed fourth in the NTIRE 2026 robust detection challenge "
           "and reports 98.3 % average balanced accuracy on five benchmarks, with the gates adding 0.37 robust-F1 points in its ablation, but it was trained on eight H800 GPUs. The routes here use compact backbones: EfficientNet " + r("efficientnet")
           + ", ResNet " + r("resnet") + " and MobileNetV3 " + r("mobilenetv3") + ", with focal loss " + r("focal") + " on one route and Grad-CAM " + r("gradcam") + " for explanation.")
    P.para("Two practical lessons from this literature shape the design. First, reported accuracy is tied to the evaluation protocol: in-distribution scores are high almost everywhere, so a detector should also be tested on degraded inputs and on a source it was not trained on, "
           "and the AUC and accuracy of a method should be read together with its data and compute budget. Second, explanation methods such as Grad-CAM show where a network looked, but a heat map is not a guarantee of faithfulness, "
           "so it is best shown beside the per-route votes and a robustness check, as the application does, rather than as stand-alone evidence.")
    P.table("Summary of the surveyed work",
            ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [[f"CTrue {r('base')}", "One-class, pseudo-fakes, curvature", "FF++, DFDC faces", "AUC 98.9 % FF++; 77.0 % DFDC", "Faces only; 2 V100 GPUs"],
             [f"HEDGE {r('hedge')}", "3 routes, logit fusion, gates", "5 benchmarks", "98.3 % balanced acc.", "8 H800 GPUs"],
             [f"Study {r('empirical')}", "10 detectors, Grad-CAM", "7 GAN/diffusion sets", "Strong in-domain", "Weak transfer"],
             [f"CIFAKE {r('cifake')}", "CNN, Grad-CAM baseline", "120,000 images, 32 px", "Benchmark released", "One generator"],
             [f"Wang {r('wang2020')}", "ResNet-50 on one GAN", "CNN generators", "Transfers with augmentation", "GAN era only"],
             [f"Ojha {r('ojha2023')}", "CLIP features, linear probe", "Unseen generators", "Better transfer", "Large backbone"],
             [f"Corvi {r('corvi2023')}", "Detectors vs diffusion", "Diffusion images", "Harder than GANs", "Drops on new models"]],
            widths=[0.55, 0.78, 0.62, 0.8, 0.65], size=6.3)
    P.para("The gap is therefore threefold: the base paper targets face deepfakes with a one-class model, strong ensembles with gating need large GPU-trained backbones, and cross-generator claims are rarely re-measured next to a robustness "
           "check and a visual explanation in a tool that a student team can run on a laptop CPU.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Data")
    P.para("The real data are a class-balanced subset of CIFAKE " + r("cifake") + ", which pairs 60,000 CIFAR-10 photographs with 60,000 Stable Diffusion 1.4 images at 32 x 32 px (copy: Hugging Face mirror). Because training is CPU-only, "
           "the subset holds 3,000 real and 3,000 AI-generated training images, 600 + 600 validation images drawn without overlap from the official training split, and 1,000 + 1,000 test images from the official test split "
           "(seed 42). A cross-domain probe adds 300 real photographs (about 640 px) and 300 AI-generated 1,024 px images from a second public source, re-saved as JPEG at quality 95. The models shipped earlier were trained on "
           "synthetic demonstration images and scored 100 % on everything, which says nothing, so all reported results use the CIFAKE-trained models.")
    P.para("Every image is converted to RGB, resized to the input size of the route (224 px, or 320 px for B) and normalised with the ImageNet mean and standard deviation " + r("imagenet") + ". The 32 px CIFAKE images are therefore "
           "enlarged seven to ten times, so the networks see interpolated pixels, not the native detail of the generator; this is a property of the benchmark and one reason why conclusions do not carry over to modern high-resolution output. "
           "Labels are 0 for real and 1 for AI-generated, and the augmentation differs by route: A1 uses random-resized crops, flips and colour jitter, A2 adds rotation, blur, noise, JPEG and down-up resizing, and B and C use moderate blur and JPEG "
           "(quality 50–95) with probability 0.35.")
    P.sub("B", "Routes and training")
    P.para("Route A1 is EfficientNet-B0 at 224 px with cross-entropy and standard augmentation, A2 the same network trained with distortion-hardened augmentation (stronger crop, rotation, blur, noise, JPEG, down-up resize), "
           "B a ResNet50 at 320 px with horizontal-flip test-time augmentation, and C a MobileNetV3-Large at 224 px with focal loss (gamma = 2) " + r("focal") + ". All start from ImageNet weights " + r("imagenet")
           + " and fine-tune only the upper blocks (1.1 M, 3.2 M, 15.0 M and 2.2 M trainable parameters). Training uses AdamW " + r("adamw") + " with weight decay 1e-4, cosine decay, learning rate 3e-4 (2e-4 for B), batch size 32 (16 for B) "
           "and early stopping on validation F1 (patience 3); A1, A2 and C ran 5 epochs and B 3, with seeds 42-45. The best validation F1 was {va1} (A1), {va2} (A2), {vb} (B, kept from epoch {eb}) and {vc} (C); training took about 24, 22, 53 and 13 minutes on the CPU. "
           "Four routes with different architectures, input sizes, augmentation and losses were chosen so that their errors are partly independent, which is what fusion can exploit.".format(**VAL))
    P.sub("C", "Logit fusion and gating")
    P.para("Each route k returns a pair of logits z for the real and the fake class, and its margin is the fake logit minus the real logit. With fixed weights w = (0.35, 0.15, 0.25, 0.25) for A1, A2, B and C, the fused logits and the class probabilities are")
    P.eq("z = (Σ_k w_k z_k) / (Σ_k w_k),    p = softmax(z)")
    P.para("Working on raw logits rather than probabilities keeps a very confident route from saturating the average. Gate 1 removes route B and renormalises the weights when the margin of B is at least 2.5 and all three other routes point the "
           "opposite way. Gate 2 adds δ = 0.75 to the logit of the B and C class and subtracts δ/2 from the other when B and C agree with margins of at least 2.5 while the fused direction differs. HEDGE " + r("hedge")
           + " uses the same two ideas with a second gate of τ1 = 8, τ2 = 3 and δ = 2.5 on much larger models; the values here (2.5, 2.5, 0.75) are engineering defaults that were not tuned. The confidence is max(p), worded High at 0.85 or above, Moderate at 0.60 or above and Low otherwise.")
    P.sub("D", "Explanation and robustness check")
    P.para("Grad-CAM " + r("gradcam") + " weights each channel c of a convolutional activation map A by the spatial average of the gradient of the predicted-class score y and keeps the positive part of the weighted sum,")
    P.eq("L = ReLU(Σ_c α_c A_c),    α_c = (1/Z) Σ_i Σ_j ∂y/∂A_c(i,j)")
    P.para("where Z is the number of spatial positions. It is computed from the last feature block of A1 and C and from the last block of the fourth stage of B through the pytorch-grad-cam library " + r("pytorch_grad_cam")
           + ", with the predicted class as target, and the map is overlaid on the input. The robustness check re-runs the full pipeline on the original, a JPEG q60 copy, a half-size down-up resize and a 5 x 5 Gaussian blur "
           "and reports how many of the four variants keep the verdict (consistency k/4). A low value flags an image whose verdict depends on fragile detail.")
    P.figure(figs["arch"], "System architecture of VeriVision AI: web app, Flask API, PyTorch inference and local files.")
    P.figure(figs["flow"], "Main flow of one analysis request (POST /api/analyze).")
    P.sub("E", "Application, reproducibility and evaluation protocol")
    P.para("A React and Vite interface on port 5414 talks to a Flask API on port 8414. A demo sign-in issues a signed 12-hour bearer token; uploads are limited to PNG, JPEG or WebP files up to 10 MB that decode as RGB and are at least "
           "8 x 8 px; there is no database, and images are decoded in memory and discarded. The classification test set is scored with accuracy, precision, recall, F1 and ROC-AUC, 95 % bootstrap intervals from 2,000 resamples " + r("bootstrap")
           + ", and expected calibration error " + r("calibration") + " with 15 bins. Robustness uses the first 1,000 test images in every condition. Single runs only: one seed per route. Errors are returned as JSON with status 400 (bad upload), 401 (missing token), 413 (file too large), 500 or 503 (models not loaded), and the Status page lists any missing checkpoint. "
           "A 19-test pytest suite covers preprocessing, weight normalisation, fusion, both gates, the response structure and the API error paths, and a 29-step smoke test drives the live API and the web proxy. The sign-in is a demonstration account and not production authentication, and the original Flask pages remain available beside the React interface.")
    P.para("Every number in Section IV is produced by scripts in the repository: a subset builder (seed 42), one training script per route, an experiment script that stores the test logits and writes the metrics, bootstrap intervals, ablation, threshold sweep, "
           "robustness runs and probe results to one JSON file, and a latency script. Because the logits of all test images are stored, fusion variants and thresholds can be re-evaluated in seconds without running the networks again, "
           "which is how the ablation of Section IV-B was carried out. The Insights page of the application reads metric files published from the same run.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.sub("A", "Test conditions")
    P.para(f"All numbers come from the {E['n_samples']:,} held-out CIFAKE test images (32 px, Stable Diffusion 1.4 against CIFAR-10), a single run per model, on the CPU machine of Section I-A. "
           "The threshold analysis and the fusion ablation reuse the same test logits, so any operating point chosen from them is optimistic. Measurements of speed use the API on 127.0.0.1 with the models already loaded, eight runs each, on an idle machine.")
    P.sub("B", "Classification performance")
    rows = []
    for k in ("a1", "a2", "b", "c", "ensemble"):
        m = E if k == "ensemble" else B[k]
        name = {"a1": "EffNet-B0 A1", "a2": "EffNet-B0 A2", "b": "ResNet50 B", "c": "MobileNetV3 C", "ensemble": "Ensemble"}[k]
        rows.append([f"**{name}**" if k == "ensemble" else name, f4(m["accuracy"]), f4(m["precision"]), f4(m["recall"]), f4(m["f1"]), f4(m["roc_auc"]), f"{ci[k][0]:.3f}–{ci[k][1]:.3f}"])
    P.table("Held-out performance (n = 2000, CIFAKE subset)", ["Model", "Acc.", "Prec.", "Rec.", "F1", "AUC", "95 % CI (acc.)"], rows,
            widths=[0.82, 0.38, 0.38, 0.38, 0.38, 0.38, 0.66], size=6.3, align=["l", "c", "c", "c", "c", "c", "c"])
    P.para(f"The ensemble reaches {pct(E['accuracy'], 2)} accuracy, {f4(E['f1'])} F1 and {f4(E['roc_auc'])} AUC, but its accuracy interval ({ci['ensemble'][0]:.3f}–{ci['ensemble'][1]:.3f}) overlaps that of A1 "
           f"({ci['a1'][0]:.3f}–{ci['a1'][1]:.3f}), so the 0.55-point advantage over the best single route is not statistically distinguishable; the AUC gain (0.9865 against 0.9749) is clearer. "
           f"The errors are lopsided: the false-positive rate is {pct(E['fpr'])} against a false-negative rate of {pct(E['fnr'])}, and the ensemble predicts AI-generated for {pct(E['predicted_fake_rate'])} of the images although half are fake. "
           f"In practice about one image in eight that is flagged as AI-generated is real (precision {f3(E['precision'])}), while only about one fake in forty-five is missed. Route B is the most biased (recall {f3(B['b']['recall'])}, precision {f3(B['b']['precision'])}). Calibration is good for the ensemble (ECE {f3(ece)}) and worst for C ({f3(F.M['ece_branches']['c'])}).")
    P.para(f"Among the single routes, A1 is best on accuracy and F1. Route B has the lowest accuracy ({pct(B['b']['accuracy'], 1)}) but the best single-route AUC ({f4(B['b']['roc_auc'])}): its scores rank the images well, while its 0.5 operating point sits too far towards fake. "
           f"Route C has the lowest AUC ({f4(B['c']['roc_auc'])}). Route A2, trained with distortion-hardened augmentation, is below A1 on clean images ({pct(B['a2']['accuracy'], 1)} against {pct(B['a1']['accuracy'], 1)}), the usual price of hardened augmentation, and Section IV-C shows that it bought no robustness here.")
    P.para(f"The routes agree with the final label on {pct(F.AGREE['a1'])} (A1), {pct(F.AGREE['a2'])} (A2), {pct(F.AGREE['b'])} (B) and {pct(F.AGREE['c'])} (C) of the images, and all four are unanimous on {pct(F.UNANIMOUS)}. "
           "Unanimity is common because the four networks share the same pretrained features and the same 6,000 training images, so they make correlated errors; this limits what fusion can add and is consistent with the small gain over A1.")
    P.para(f"The gates did not help. Gate 1 fired on {E['gate1_fired']} of 2,000 images and Gate 2 on {E['gate2_fired']}; without gates the same logits give {pct(nog['accuracy'], 2)} accuracy, {(nog['accuracy'] - E['accuracy']) * 100:.2f} points more, "
           f"and probability averaging scores {pct(ab['prob_avg']['accuracy'], 2)} with a lower AUC ({f4(ab['prob_avg']['roc_auc'])}), and majority voting reaches {pct(ab['majority']['accuracy'], 2)} with an AUC of {f4(ab['majority']['roc_auc'])} because it discards the margins. "
           "Equal weights with the gates give 92.15 %, so the configured weights are no better than a simple rule; they are the product's defaults and were not optimised.")
    P.figure(figs["results"], "(a) Accuracy with 95 % bootstrap intervals and ROC-AUC of each route and the ensemble. (b) Accuracy under JPEG q60, half-size resize, 5 x 5 blur and Gaussian noise (1,000 images).")
    P.sub("C", "Robustness and cross-domain probe")
    P.para(f"JPEG q60 and noise cost the ensemble about 4–5 points ({pct(rob['jpeg']['ensemble']['accuracy'])} and {pct(rob['noise']['ensemble']['accuracy'])}), but resizing and blur are damaging: "
           f"{pct(rob['resize']['ensemble']['accuracy'])} and {pct(rob['blur']['ensemble']['accuracy'])}, with the ensemble then calling only {pct(rob['resize']['ensemble']['predicted_fake_rate'])} and {pct(rob['blur']['ensemble']['predicted_fake_rate'])} of the images fake. "
           f"Route B holds up best ({pct(rob['resize']['branches']['b']['accuracy'])} after resizing), and the distortion-hardened route A2 was not more robust than A1. On the cross-domain probe of full-resolution photographs and AI images from another source the ensemble "
           f"scores {pct(xd['accuracy'])} accuracy and {f3(xd['roc_auc'])} AUC, which is chance: A2, B and C call almost every image AI-generated and A1 is a coin flip. Resolution and content shift as well as generator shift here, "
           "so the probe cannot separate them, but cross-generator generalisation, an objective of the project, was measured and not achieved.")
    P.para(f"The way the ensemble fails under resizing and blur is systematic, not random. After a half-size resize its false-negative rate is {pct(rob['resize']['ensemble']['fnr'])} against a false-positive rate of {pct(rob['resize']['ensemble']['fpr'])}, "
           f"and after blur {pct(rob['blur']['ensemble']['fnr'])} against {pct(rob['blur']['ensemble']['fpr'])}: smoothing removes the high-frequency detail the routes read as a sign of generation, so generated images start to look real. "
           f"The ranking survives better than the verdict, with ROC-AUC still {f3(rob['resize']['ensemble']['roc_auc'])} after resizing and {f3(rob['blur']['ensemble']['roc_auc'])} after blur, which suggests that part of the loss is a shifted operating point; "
           "no recalibration for degraded inputs was tried. JPEG compression and noise move the error the other way, towards false positives (21.4 % and 25.0 %).")
    P.para("The cross-domain result is equally one-sided. Of the 300 real photographs the routes keep as real only 170 (A1), 4 (A2), 1 (B) and 20 (C), while they find 134, 283, 291 and 293 of the 300 AI-generated images; "
           "the fused ensemble keeps 163 real photographs and finds 143 AI images. A network that calls every unfamiliar, high-resolution image fake gets a high recall for the wrong reason, which is why accuracy and AUC are reported together with the counts.")
    P.sub("D", "Output screens, speed and failures")
    P.para("The web application shows the result as a verdict card, a table of branch votes with the weight each route carried, the robustness check and a Grad-CAM panel with one tab per route. "
           "Fig. 4 is the verdict card for a generated test image (fused AI-generated probability 99.2 %, all four routes agreeing), Fig. 5 the Grad-CAM panel, which highlights the regions that drove the EfficientNet route, "
           "and Fig. 6 the votes and the robustness check for the same image. All four routes call it AI-generated, yet the half-size resize variant flips to real and the consistency reads 3/4, so the interface warns that the verdict is sensitive to compression; "
           "this is the failure mode that the resize and blur results of Fig. 3(b) describe.")
    P.figure(figs["verdict"], "Output screen: verdict card for a generated image, with confidence and agreement count.")
    P.figure(figs["gradcam"], "Output screen: Grad-CAM panel (original image and EfficientNet heat map).")
    P.figure(figs["votes"], "Output screen: branch votes with fusion weights and the robustness check (consistency 3/4).")
    P.para(f"Through the API on the same machine, /api/predict takes a median {lat['predict_cifake_32px']['median']:.2f} s and /api/analyze, with three heat maps and three robustness variants, {lat['analyze_cifake_32px']['median']:.2f} s for a 32 px image "
           f"and {lat['analyze_photo_1024px']['median']:.2f} s for a 1,024 px photograph; batched offline inference of all four routes costs {F.M['inference_seconds_per_image_batched'] * 1000:.0f} ms per image. "
           f"{wrong} of the 2,000 test images are wrong; their mean fused margin is {F.ERR['mean_abs_margin_wrong']:.2f} against {F.ERR['mean_abs_margin_correct']:.2f} for correct ones, "
           "so errors sit near the decision boundary and the confidence word carries information. The Grad-CAM maps were inspected by eye only and no faithfulness test (such as deletion or insertion) was run, so they show where the models looked, "
           "not proof that those regions are the cause of the verdict. Not measured: several seeds, a GPU run, load or concurrency, adversarial attacks and a user study.")
    P.sub("E", "Threshold, calibration and errors")
    P.para(f"The deployed threshold on the fused AI-generated probability is 0.5. Sweeping it on the test logits (Fig. 7) shows that accuracy is flat between 0.6 and 0.8 and peaks at {pct(sw[0.8]['accuracy'])}: at 0.7 accuracy is {pct(sw[0.7]['accuracy'])} with a false-positive rate of "
           f"{pct(sw[0.7]['fpr'])} and a recall of {pct(sw[0.7]['recall'])}, and at 0.9 the false-negative rate climbs to {pct(sw[0.9]['fnr'])}. Because these thresholds were picked on the test images they are optimistic and would need a separate validation set; "
           "the sweep is useful mainly for showing the trade-off an operator can choose, which here is fewer false alarms against more missed fakes. "
           f"The confusion matrix at 0.5 is {E['confusion_matrix'][0][0]} true negatives, {E['confusion_matrix'][0][1]} false positives, {E['confusion_matrix'][1][0]} false negatives and {E['confusion_matrix'][1][1]} true positives. "
           f"Expected calibration error is {f3(ece)} for the ensemble, {f3(F.M['ece_branches']['a1'])} for A1 and A2, {f3(F.M['ece_branches']['b'])} for B and {f3(F.M['ece_branches']['c'])} for C, so the confidence shown to the user is a usable "
           "guide only for the ensemble and the EfficientNet routes; the focal-loss route C is over-confident.")
    P.figure(figs["threshold"], "Accuracy, false-positive rate and false-negative rate against the decision threshold (test logits; the 0.5 default is deployed).")
    P.para("Three threats to validity apply to all of the above. The benchmark images are 32 px and from one generator, so the numbers describe CIFAKE and not the wild. The models are single runs from one seed each, so the ranking of routes carries "
           "run-to-run uncertainty that the bootstrap interval, which resamples only the test images, does not capture. And the subset (6,000 of 100,000 training images, 3–5 epochs) was set by CPU time, so a full-data run would probably score higher.")
    P.sub("F", "Comparison with the base paper")
    P.para("The comparison is indicative only. CTrue " + r("base") + " is a one-class face-deepfake detector trained on 720 FaceForensics++ videos for 200 epochs on two V100 GPUs and scored by AUC; VeriVision AI is a supervised general-image detector trained "
           f"on 6,000 CIFAKE images for 3–5 epochs on a CPU. The only like-for-like figure is in-domain AUC: {pct(E['roc_auc'], 2)} here against 98.9 % there. Cross-dataset, CTrue reports 77.0 % AUC on DFDC and this project {pct(xd['roc_auc'])}. "
           "The datasets, tasks and training budgets differ, so neither number shows one method to be better. HEDGE " + r("hedge") + " reports 98.3 % balanced accuracy with large backbones; its gates added 0.37 robust-F1 points whereas ours lowered accuracy by 0.10 points.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para(f"VeriVision AI delivers the project's working parts: four CNN routes, a gated logit ensemble, Grad-CAM overlays and a robustness check behind a local web application that answers in about 0.3 s (verdict) or 1.7–2.0 s (verdict, three heat maps, robustness check) on a CPU. "
           f"On 2,000 held-out CIFAKE images the ensemble scores {pct(E['accuracy'], 2)} accuracy and {f4(E['roc_auc'])} AUC. Of the six objectives, four are met (preprocessing and augmentation, CNN classifiers, Grad-CAM, deployment), the dataset objective is only partly met because it holds a single generator, and cross-generator generalisation is not met. "
           "The key findings are that the ensemble is not distinguishable from its best single route in accuracy, that the gates were inactive or harmful here, that resizing and blur remove the detectable cue at 32 px, and that the models are at chance on other sources. "
           "Limitations are one seed per route, 6 % of the training data, 32 px images, a single generator, a test-selected threshold, qualitative-only Grad-CAM checks and no user study.")
    P.para("Future work should train on full-resolution images from several generators with a held-out generator split, tune the gates and the decision threshold on a separate validation set, quantify the heat maps with deletion and insertion tests, "
           "report several seeds, and add a confidence value that falls when the robustness check disagrees.")

    P.references()
    assert set(P.order) == {CITE[k] for k in USED}, sorted(set(P.order) ^ {CITE[k] for k in USED})
    return P.save(path)


def main():
    path = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    build(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
