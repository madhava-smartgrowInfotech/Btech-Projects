"""Chapter 2: Literature Survey (VeriVision AI)."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, P, TAB
from .refs import CITE as R


def blocks():
    xd = F.XD["ensemble"]
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        P("This chapter reviews the literature that frames the project: the base paper assigned to the batch, the heterogeneous-ensemble paper whose design the system follows, an empirical "
          "comparison of detectors, the work on detecting images from generative adversarial networks and diffusion models, the datasets used in this area, and the explainability method. "
          "It ends with the research gap that the project tries to address. Every figure quoted from a paper was read from the paper itself; where a table in a paper could not be read as text, no number is quoted."),

        H2("2.1 Overview"),
        P(f"Early work on detecting generated images studied images from generative adversarial networks [{R['gan']}]. Wang et al. [{R['wang2020']}] trained a ResNet-50 classifier on images from one GAN "
          "and found that, with suitable augmentation, it recognised many other GANs; Frank et al. "
          f"[{R['frank2020']}] showed that GAN images carry visible traces in the frequency domain, and Gragnaniello et al. [{R['gragnaniello2021']}] analysed how well the state of the art really works "
          f"under realistic conditions. Diffusion models changed the picture: Corvi et al. [{R['corvi2023']}] studied the detection of diffusion-generated images, and Ojha et al. [{R['ojha2023']}] proposed "
          "using the features of a large pre-trained vision-language model with a simple classifier on top so that the detector transfers to generators it has not seen. "
          f"In parallel, face manipulation datasets such as FaceForensics++ [{R['ffpp']}] and Celeb-DF [{R['celebdf']}] drove a separate line of deepfake detection research, to which the base paper belongs."),
        P("Across these studies two difficulties recur. The first is generalisation: a classifier that is accurate on the generator it was trained on is often much weaker on another. The second is fragility: "
          "post-processing such as JPEG compression and resizing alters or removes the cues the classifier uses. A third concern, important for practical use, is that a score alone does not justify "
          "a decision, which is why explainable AI is increasingly paired with detection."),

        H2("2.2 Base Paper Analysis"),
        P(f"The base paper given to the batch is N. Larue, V. Struc, P. Peer and N.-S. Vu, \"Learning the manifold of authenticity: hybrid-curvature representation learning for generalizable deepfake detection,\" "
          f"IEEE Access, vol. 14, 2026 [{R['base']}]. Its setting and contribution, as read from the paper, are summarised below."),
        B("**Problem.** Generalisable deepfake detection on face images and video frames: a detector must work on manipulations it was not trained on.",
          "**One-class training.** Only authentic faces are used for training, together with synthesised pseudo-fakes, so that the model learns what authentic data looks like rather than the signature of particular manipulations (the title's *manifold of authenticity*).",
          "**Representation.** A hybrid-curvature representation on an EfficientNet-B4 backbone (19.3 million parameters, 4.4 GFLOPs).",
          "**Data and compute.** 720 pristine FaceForensics++ videos; 200 epochs on two V100 GPUs, about 16 hours; 74 frames per second at inference on an RTX 3060.",
          "**Reported results.** An AUC of 98.9% on FaceForensics++ and 77.0% on DFDC in the lambda = 1 ablation. The paper's cross-dataset comparison table is an image in the PDF and its values are not quoted here."),
        P("The paper is relevant to this project because it makes generalisation to unseen manipulations the central question, which is also Objective 4 of the batch. It differs from the project in four ways that "
          "matter for any comparison. Its domain is human faces in video frames, whereas this project classifies general still images. It is trained one-class without any real fake examples, whereas this project "
          "trains supervised classifiers on labelled real and generated images. Its backbone and compute budget (EfficientNet-B4, two V100 GPUs, 200 epochs) are much larger than the CPU-only fine-tuning "
          "of four small networks used here. Finally, it reports AUC on face benchmarks, whereas this project reports accuracy, F1 and AUC on a different dataset. "
          "The project therefore adopts the paper's *question* (does the detector generalise beyond its training data?) and tests it, but it does not implement the paper's method; "
          "Chapter 8 compares the two only where a like-for-like quantity (AUC) exists and says plainly that the datasets differ."),

        H2("2.3 Related Work"),
        H2("2.3.1 Heterogeneous ensembles and gating"),
        P(f"HEDGE, by Wu et al. [{R['hedge']}], was a fourth-place entry in the NTIRE 2026 robust AI-generated image detection challenge. It combines three routes: a DINOv3-based route trained progressively, "
          "a route working at higher resolution, and a MetaCLIP2-based route. The route outputs are fused in logit space with weights of 7:3 in two steps, and two gating rules correct the fusion when a "
          "route is an outlier or when two routes agree strongly against the fused direction (the second gate uses thresholds tau1 = 8 and tau2 = 3 and a correction delta = 2.5). "
          "The paper reports an average balanced accuracy of 98.3% on five standard benchmarks (97.8% under JPEG compression and 98.4% under resizing). Its ablation on the competition set reports a robust F1 of 80.52 for the full fusion and "
          "80.89 when the gates are added, a gain of 0.37 points. The models were trained on 8 H800 GPUs. VeriVision AI keeps the idea of heterogeneous routes, logit-space weighted fusion and two gates, but "
          "replaces the large backbones with four small CNNs that run on a CPU; the gate thresholds are the product's own engineering defaults and were not tuned."),
        H2("2.3.2 Empirical comparison of detectors"),
        P(f"Tasnim et al. [{R['empirical']}] evaluated ten forensic methods on seven GAN and diffusion datasets with accuracy, average precision and AUC, and added a Grad-CAM and confidence-curve analysis. "
          "Their finding is that methods are strong on the distribution they were trained on and weaker across generators. This is the benchmark framing "
          "adopted for the project's own evaluation: a held-out test, degraded variants and a probe from a different source."),
        H2("2.3.3 Detection of GAN and diffusion images"),
        P(f"Wang et al. [{R['wang2020']}] showed that a standard CNN classifier trained on one generator can generalise to others when the training uses blur and JPEG augmentation, which "
          "is the motivation for the distortion-hardened route A2 in this project. Frank et al. "
          f"[{R['frank2020']}] used a discrete cosine transform to expose spectral artefacts, a cue that is easily damaged by resizing. Corvi et al. [{R['corvi2023']}] examined the detection of diffusion-generated images, a different generator family from the GANs most earlier detectors were built for. Gragnaniello et al. [{R['gragnaniello2021']}] gave a critical analysis of detectors under realistic post-processing. "
          f"Ojha et al. [{R['ojha2023']}] avoided training a dedicated real-versus-fake feature extractor and used a frozen CLIP feature space with a linear classifier, which transfers better to unseen generators but depends on a large pre-trained model."),
        H2("2.3.4 Face-forgery detection"),
        P(f"FaceForensics++ [{R['ffpp']}] provides over a thousand original videos manipulated by several face-forgery methods, and Celeb-DF [{R['celebdf']}] provides higher-quality forged celebrity videos. "
          "Detectors for these datasets, including the base paper, exploit face-specific structure. They are not directly usable for general photographs, which is the case this project addresses."),
        H2("2.3.5 Explainable detection"),
        P(f"Grad-CAM [{R['gradcam']}] weights the feature maps of a chosen convolutional layer by the gradient of the class score and overlays the result on the image. "
          f"It works with any CNN without retraining. The open-source library pytorch-grad-cam [{R['pytorch_grad_cam']}] implements it, and it is the implementation used here. "
          f"Bird and Lotfi [{R['cifake']}] paired a CNN detector with Grad-CAM on the CIFAKE data, which makes their setting the closest match to this project's data and to its explanation method. "
          "Heat maps show where the network looked, not why that region matters, so they are read here as supporting evidence and not as proof."),
        P("The survey list recorded for the batch also names four 2025 items (a deepfake and AI-generated image detection system, a deepfake tweet detection study, a multimodal deepfake detection paper "
          "and a deep-learning deepfake detection approach). Their bibliographic details could not be confirmed online during this work, so they appear in the reference list marked as unverified and no claim or number in this report depends on them."),
        TAB("Comparison of the surveyed work", ["Work", "Year", "Approach", "Finding / limitation"], lit.LIT_TABLE, widths=[1.55, 0.5, 2.15, 2.1], align=["l", "c", "l", "l"], size=9),

        H2("2.4 Datasets and Algorithms Used in This Area"),
        P(f"**Datasets.** FaceForensics++ [{R['ffpp']}] and Celeb-DF [{R['celebdf']}] cover face forgeries. CIFAKE [{R['cifake']}] contains 60,000 real images from CIFAR-10 [{R['cifar10']}] and 60,000 images generated with "
          f"Stable Diffusion v1.4 [{R['ldm']}] at 32 x 32 pixels, split into 100,000 training and 20,000 test images; it is small enough to train on a CPU and is the data used here. "
          "The benchmarks in HEDGE and in the empirical study cover many more generators and larger images."),
        P(f"**Algorithms.** The detectors in the literature are CNN classifiers fine-tuned from ImageNet weights [{R['resnet']}], [{R['efficientnet']}], frozen foundation-model features with a linear probe [{R['ojha2023']}], "
          f"frequency-domain classifiers [{R['frank2020']}], one-class models [{R['base']}] and ensembles [{R['hedge']}]. Training uses cross-entropy or focal loss [{R['focal']}] with AdamW [{R['adamw']}]; probability quality is "
          f"measured by calibration error [{R['calibration']}]. Grad-CAM [{R['gradcam']}] provides the explanation. The project uses the CNN fine-tuning, ensemble and gating and Grad-CAM elements."),

        H2("2.5 Strengths and Limitations of the Existing Approaches"),
        TAB("Strengths and limitations by approach", ["Approach", "Strength", "Limitation"], [
            ["Single CNN classifier [12], [8]", "Simple, fast, strong in-distribution", "One opinion, weak on other generators, no reason given"],
            ["Frequency-domain cues [14]", "Exposes GAN spectral artefacts", "Damaged by resizing and compression"],
            ["Frozen foundation features [13]", "Better transfer to unseen generators", "Needs a large pre-trained model"],
            ["One-class face detector [1]", "No fake examples needed; generalisation as the aim", "Faces and video only; heavy training"],
            ["Heterogeneous ensemble with gates [2]", "Complementary routes, robust fusion", "Large backbones and GPU clusters"],
            ["Grad-CAM explanation [26]", "Model-agnostic, visual, no retraining", "Qualitative; faithfulness not guaranteed"],
        ], widths=[1.9, 2.1, 2.3], align=["l", "l", "l"], size=10),

        H2("2.6 Research Gap"),
        P("The survey shows that detection of generated images is well studied but that deployable, explained and honestly evaluated tools are scarce. The gaps this project addresses are:"),
        B(*lit.GAPS),
        P(f"The project does not close the generalisation gap. Its contribution is to build the missing tool, to make its disagreement and instability visible, and to measure them: in-domain accuracy of {F.pct(F.ENS['accuracy'])}, "
          f"a drop to 58-61% under resizing and blur, and a result at chance ({F.pct(xd['accuracy'])}) on images from another source."),
    ]
