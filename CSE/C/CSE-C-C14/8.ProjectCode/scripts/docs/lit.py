"""Literature and framing data for the decks (Review 1, Review 2 and the final deck) of VeriVision AI (CSE-C-C14).

Every literature fact traces to docs/REPORT_FACTS.md section 12 and to the PDFs in Documentary/ and archived_base_papers/;
reference numbers match scripts/docs/refs.py. No number from the unverified survey items (refs 4-7) is used.
"""

from .refs import CITE as R

BASE_PAPER_TITLE = "Learning the Manifold of Authenticity: Hybrid-Curvature Representation Learning for Generalizable Deepfake Detection"
BASE_PAPER_VENUE = "N. Larue, V. Struc, P. Peer, N.-S. Vu - IEEE Access, vol. 14, 2026"

# [work, year, approach, finding / limitation]   (each cell <= 90 characters)
LIT_TABLE = [
    [f"Larue et al. CTrue [{R['base']}] (base paper)", "2026", "One-class face-deepfake detector, EfficientNet-B4, pseudo-fakes, hybrid curvature",
     "AUC 98.9% FF++, 77.0% DFDC (lambda=1); faces only, 2 V100 GPUs, 200 epochs"],
    [f"Wu et al. HEDGE [{R['hedge']}]", "2026", "Three heterogeneous routes, logit fusion and dual gating, DINOv3 / MetaCLIP2",
     "Balanced acc. 98.3% on five benchmarks; gates add 0.37 F1; 8 H800 GPUs"],
    [f"Tasnim et al. [{R['empirical']}]", "2025", "Ten forensic detectors on seven GAN/diffusion sets, Grad-CAM analysis",
     "Strong in-distribution, weaker transfer across generators"],
    [f"Bird & Lotfi CIFAKE [{R['cifake']}]", "2024", "CNN on 60,000 real vs 60,000 Stable Diffusion images (32 px), Grad-CAM",
     "Small-image benchmark; one generator; used as this project's data"],
    [f"Wang et al. [{R['wang2020']}]", "2020", "ResNet-50 trained on one GAN, tested on many",
     "Generalises with augmentation; GAN-era generators only"],
    [f"Ojha et al. [{R['ojha2023']}]", "2023", "Frozen CLIP features with a linear probe for universal detection",
     "Better transfer to unseen generators; needs a large pre-trained backbone"],
    [f"Frank et al. [{R['frank2020']}]", "2020", "Frequency-domain (DCT) analysis of GAN images",
     "Spectral artefacts are visible; fragile after resizing or compression"],
    [f"Corvi et al. [{R['corvi2023']}]", "2023", "Detectors for diffusion-generated images",
     "Diffusion images are harder; detectors lose accuracy on new generators"],
    [f"Selvaraju et al. Grad-CAM [{R['gradcam']}]", "2017", "Gradient-weighted class activation maps for any CNN",
     "Qualitative heat maps; no guarantee of faithfulness"],
]

OBJECTIVES = [
    "Assemble a dataset of real photographs and AI-generated images",
    "Preprocess and augment the images to improve robustness across sources",
    "Train CNN classifiers that separate real images from generated ones",
    "Evaluate cross-generator performance to test generalisation",
    "Apply Grad-CAM to highlight the regions driving each classification",
    "Deploy the models behind an interface returning verdict, confidence and explanation",
]

PROBLEM_STATEMENT = [
    "Synthetic images are realistic enough to deceive human observers",
    "Detectors trained on one generator degrade sharply on images from another",
    "Compression and resizing on social platforms remove detectable artefacts",
    "A verdict without a visual justification is not credible in a dispute",
    "Need: a detector that identifies AI-generated images and explains its decision",
]

GAPS = [
    "The base paper targets face deepfakes with a one-class model, not general images",
    "Most detectors report a verdict only; Grad-CAM pairing is rare in deployable tools",
    "Cross-generator generalisation is claimed often but rarely re-measured on other sources",
    "Heterogeneous ensembles with gating exist (HEDGE) but need large GPU-trained backbones",
    "Robustness to JPEG, resizing and blur is seldom reported next to the verdict",
    "No student-deployable CPU tool joins four CNN routes, Grad-CAM and a robustness check",
]

EXISTING_SYSTEM = [
    "Manual inspection of artefacts such as hands, text and lighting",
    "Single-model detectors that return only a real/fake score",
    "Large foundation-model detectors that need GPUs and cloud services",
    "Metadata and watermark checks that fail once the image is re-saved",
]

LIMITATIONS_EXISTING = [
    "Human eyes can no longer separate modern generated images reliably",
    "A single score hides disagreement between models and gives no reasons",
    "Detectors trained on one generator fail on another (cross-domain drop)",
    "Resize, blur and compression remove the cues many detectors rely on",
    "Uploading images to a remote service conflicts with privacy for sensitive content",
]

PROPOSED_APPROACH = [
    "Four ImageNet-pretrained CNN routes: EfficientNet-B0 x2, ResNet50, MobileNetV3-Large",
    "Fuse the route logits with weights 0.35 / 0.15 / 0.25 / 0.25 and two gating rules",
    "Explain each verdict with Grad-CAM heat maps on three routes",
    "Re-test every image under JPEG, resize and blur and report a consistency score",
    "Serve it locally: Flask API on 8414 and React web app on 5414, CPU only",
]

EXPECTED_OUTCOMES = [
    "A working web app from image upload to verdict, votes, heat map and robustness check",
    "Measured accuracy, F1 and ROC-AUC on a held-out test set with confidence intervals",
    "Honest robustness and cross-domain measurements, including where the models fail",
    "Explanations an analyst can inspect next to the per-route votes",
    "A decision aid: the verdict is evidence, not proof of origin",
]

BASE_PAPER_POINTS = [
    "One-class training: only authentic faces plus synthesised pseudo-fakes",
    "Hybrid-curvature representation learning on an EfficientNet-B4 backbone",
    "720 pristine FaceForensics++ videos; 200 epochs on two V100 GPUs (about 16 h)",
    "AUC 98.9% on FF++ and 77.0% on DFDC (lambda = 1 ablation); 74 fps on an RTX 3060",
    "Domain is faces and video frames, not general images",
    "Metric is AUC; this project reports accuracy, F1 and AUC on a different dataset",
]

SUPPORT_EVIDENCE = [
    f"HEDGE: three routes, logit fusion and dual gating reached 98.3% average balanced accuracy on five benchmarks [{R['hedge']}]",
    f"HEDGE ablation: adding the gates lifted robust F1 from 80.52 to 80.89 on the competition set [{R['hedge']}]",
    f"Empirical study: ten detectors on seven datasets are strong in-distribution but transfer weakly [{R['empirical']}]",
    f"CIFAKE: 60,000 real and 60,000 Stable Diffusion v1.4 images at 32 px, a CNN baseline with Grad-CAM [{R['cifake']}]",
    f"Grad-CAM gives class-specific heat maps for any CNN without retraining [{R['gradcam']}]",
]
