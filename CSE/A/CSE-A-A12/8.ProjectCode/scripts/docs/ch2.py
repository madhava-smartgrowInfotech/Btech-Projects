"""Chapter 2: Literature survey. Every figure quoted here comes from the base paper's PDF, the two archived arXiv PDFs, or the cited work as summarised in the base paper."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

LIT_TABLE = [
    ["Mahin et al., 2026 [1] (base paper)", "MobileNet family with FixMatch, FlexMatch, FreeMatch; Grad-CAM; MC Dropout; ECE", "Mendeley pediatric CXR (5,863, 2 classes); merged COVID-19 / Normal / Pneumonia / TB set (7,135)", "Supervised up to 98 % (binary) and 97 % (4-class); FreeMatch 97 % with 20 % (binary) or 30 % (4-class) labels", "Curated benchmarks; no external validation; confusion among similar diseases"],
    ["Kermany et al., 2018 [3]", "Transfer learning on a pretrained network", "5,232 training and 624 test paediatric chest X-rays", "93.2 % sensitivity, 90.1 % specificity, 92.8 % accuracy (Normal vs pneumonia)", "Single paediatric centre"],
    ["Rajpurkar et al., 2017 [7] (CheXNet)", "DenseNet121 trained on ChestX-ray14", "ChestX-ray14 [8]", "Radiologist-level pneumonia detection (as summarised in [1])", "Binary formulation; fully supervised"],
    ["Ozturk et al., 2020 [20]", "DarkNet-based CNN", "COVID-19, pneumonia and normal X-rays", "98.08 % binary but 87.02 % three-class (as summarised in [1])", "Large drop when classes overlap"],
    ["Alshanketi et al., 2024 [22]", "VGG16, ResNet50, Vision Transformer on imbalanced data", "Pneumonia chest X-rays", "VGG16 about 91 %, ahead of deeper models under limited data (as summarised in [1])", "Small-data regime; imbalance"],
    ["Malik et al., 2023 [23] (CDC_Net)", "Residual and dilated convolutions, five classes", "COVID-19, pneumothorax, pneumonia, lung cancer, TB", "99.39 % accuracy (as summarised in [1])", "Fully supervised; no uncertainty or explanation focus"],
    ["Kumar et al., 2025 [24]", "Image enhancement + feature extraction + multi-model ensemble", "Pulmonary disease chest X-rays", "98.88 % accuracy (as summarised in [1])", "Curated data; no external test"],
    ["Khadidos et al., 2026 [5]", "DenseNet121 and EfficientNet-B0 fine-tuned; Grad-CAM and LIME", "Kermany pediatric set, 5,863 images", "EfficientNet-B0: accuracy 84.6 %, F1 0.8899, MCC 0.6849; DenseNet121: 79.7 %, 0.8597, 0.5852; recall above 0.99 for both", "High recall but modest accuracy: pneumonia over-predicted"],
    ["Shahi and Bagale, 2025 [6]", "Seven pretrained models incl. a ViT, focal loss, patient-wise split, Grad-CAM", "Chest X-rays with image-level labels", "96-98 % accuracy; ResNet-18 and EfficientNet-B0 best; MobileNet-V3 efficient", "Weak supervision gives coarse localisation only"],
]


def blocks():
    b = [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P(f"This chapter reviews the work that shaped the project. It begins with a close reading of the base paper {n(1)}, then groups related work by theme: "
          "convolutional networks and transfer learning for pneumonia, hybrid and ensemble approaches, explanation and uncertainty, and the two recent "
          f"studies on the same paediatric dataset that we compare against most directly {n(5, 6)}. It ends with the research gap that motivates this project. "
          "Where a figure is quoted from a work that was not read in full, the text says so and cites the document that reports it."),
        H2("2.2 Base paper analysis"),
        P(f"**Reference.** {F.BASE_PAPER}"),
        H3("2.2.1 Problem and approach"),
        P("The paper addresses chest X-ray diagnosis in two settings: a binary task (Normal versus Pneumonia) and a multiclass task "
          "(COVID-19, Normal, Pneumonia, Tuberculosis). Its argument is that pneumonia looks similar to COVID-19 and tuberculosis on a radiograph, that labelled "
          "images are expensive, and that clinical trust needs both explanation and a measure of uncertainty. It therefore combines lightweight MobileNet "
          "backbones with three modern pseudo-labelling methods, FixMatch, FlexMatch and FreeMatch, so that unlabelled images can contribute to training."),
        H3("2.2.2 Data and preprocessing"),
        P("The binary experiments use the Chest X-Ray Images (Pneumonia) dataset hosted on Mendeley Data, with 5,863 paediatric images from the Guangzhou "
          "Women and Children's Medical Center. The multiclass experiments use a merged Kaggle collection of 7,135 images in four classes. Both are "
          "heavily imbalanced, so the authors sample a controlled, balanced subset (1,300 images per class in the binary case, split 2,080 / 260 / 260 into "
          "training, validation and test). Images are resized to 224 x 224, converted to three channels and normalised with the MobileNetV3 "
          "pre-processing function. Training augmentation uses rotation, shift, zoom and shear; horizontal and vertical flips are switched off to preserve "
          "anatomical orientation. All stochastic steps use a fixed seed of 42."),
        H3("2.2.3 Models and learning methods"),
        P("MobileNet, MobileNetV2, MobileNetV3Small and MobileNetV3Large are initialised with ImageNet weights and given a classification head with global "
          "average pooling, dense layers, batch normalisation and dropout. MobileNet and MobileNetV3Small perform best; MobileNetV3Small is chosen for the "
          "semi-supervised experiments because it needs roughly ten times fewer floating-point operations (116.9 M against 1,147 M) and halves latency "
          f"(0.11 s against 0.23 s per prediction). FixMatch {n(14)} keeps a pseudo-label when the weakly augmented prediction exceeds a fixed confidence threshold; "
          "FlexMatch adapts the threshold per class; FreeMatch adapts it from the model's own learning status."),
        H3("2.2.4 Explanation and reliability"),
        P(f"Grad-CAM {n(9)} heat maps are overlaid on test images to show that predictions rest on lung regions. Reliability is assessed with Monte Carlo "
          f"Dropout {n(15)} (50 stochastic passes, predictive entropy, a threshold of 0.30 to flag cases for expert review), test-time augmentation and "
          f"Expected Calibration Error {n(29)}."),
        H3("2.2.5 Reported results and limits"),
        P("Supervised MobileNet models reach up to 98 % accuracy in the binary task and 97 % in the multiclass task. FreeMatch is the most stable "
          "semi-supervised method and reaches 97 % accuracy with only 20 % labelled data (binary) or 30 % (multiclass). The authors state their own "
          "limits: the datasets are benchmarks that may not reflect real clinical variability, the added COVID-19 and tuberculosis classes may help but this "
          "is not isolated experimentally, and errors concentrate in visually similar classes and in high-entropy samples."),
        H3("2.2.6 What this project takes from it"),
        B("The 224 x 224 input size, three-channel conversion and ImageNet-style transfer learning option.",
          "Grad-CAM as the explanation method, applied on the last convolutional layer.",
          "The idea of flagging low-confidence cases, realised here as a confidence-threshold analysis rather than Monte Carlo Dropout.",
          "The caution about orientation-changing augmentation: the project's shipped augmentor does use horizontal flips, which this report records as a design difference.",
          "MobileNetV3Small as the lightweight reference model for comparison."),
        H2("2.3 Related work by theme"),
        H3("A. Convolutional networks and transfer learning for pneumonia"),
        P(f"Kermany et al. {n(3)} showed that a transfer-learned network could separate paediatric pneumonia from normal chest X-rays with 92.8 % accuracy, "
          f"93.2 % sensitivity and 90.1 % specificity on a 624-image test set, and released the data that most later studies, including this one, use. "
          f"CheXNet {n(7)} trained a DenseNet121 on the large ChestX-ray14 collection {n(8)} and reported radiologist-level pneumonia detection. "
          f"A recent survey {n(25)} catalogues the many architectures tried since. Alshanketi et al. {n(22)} found that a plain VGG16 reached about 91 % "
          "and outperformed deeper networks and Vision Transformers when data were limited and imbalanced, a reminder that depth does not guarantee "
          "better results on small medical sets."),
        H3("B. Hybrid, ensemble and multi-disease frameworks"),
        P(f"Hashmi et al. {n(26)} fused deep features with handcrafted texture descriptors, and Vyas and Khadatkar {n(27)} fed deep features to classical "
          f"classifiers, reporting accuracies approaching 99.98 % on curated data. Multi-disease networks such as DarkNet-based {n(20)}, COVID-Net {n(21)} and "
          f"CDC_Net {n(23)} extend the label set; Ozturk et al. report 98.08 % for a binary COVID-19 task but 87.02 % when three classes overlap, which illustrates "
          f"how multiclass separation of similar-looking disease is harder than binary detection. Kumar et al. {n(24)} combine image enhancement with an ensemble "
          "to reach 98.88 %."),
        H3("C. Explanation and uncertainty"),
        P(f"Grad-CAM {n(9)} and Grad-CAM++ {n(37)} are the standard ways to show which region drove a CNN decision; COVID-Net {n(21)} demonstrated that attention "
          f"maps can accompany a clinical classifier without hurting accuracy. Monte Carlo Dropout {n(15)} approximates Bayesian uncertainty and calibration "
          f"error {n(29)} measures how closely confidence matches accuracy. The base paper observes that most frameworks treat explanation and uncertainty as "
          "separate post-hoc add-ons."),
        H3("D. Studies on the same paediatric dataset"),
        P(f"Khadidos et al. {n(5)} fine-tuned DenseNet121 and EfficientNet-B0 on the 5,863-image dataset and added Grad-CAM and LIME. EfficientNet-B0 reached "
          "84.6 % accuracy (F1 0.8899, MCC 0.6849) and DenseNet121 79.7 % (F1 0.8597, MCC 0.5852), with recall above 0.99 for both, which implies almost every "
          f"pneumonia case was found while many normal films were also flagged. Shahi and Bagale {n(6)} trained seven pretrained models, including a Vision "
          "Transformer, with focal loss and a patient-wise split to avoid leakage, and report 96 to 98 % accuracy under their protocol. The two papers "
          "differ by more than 10 points on the same image source, which shows how strongly the result depends on the split, the class balance and the "
          "evaluation protocol. This is why Chapter 8 states the protocol next to every number."),
        H3("E. Further entries recorded in the batch literature survey"),
        P(f"The batch literature survey also lists four 2025-2026 entries: a CNN-based pneumonia detector {n(30)}, a colormap-enhanced Vision Transformer for "
          f"tuberculosis and pneumonia {n(31)}, a chest X-ray pneumonia detection paper in the International Scientific Journal of Engineering and Management "
          f"{n(32)}, and a reproducibility and external threshold-transfer audit of transfer-learning CNNs for paediatric pneumonia {n(33)}. Only their titles and "
          "years were recorded; their results were not re-read for this report and are therefore not quoted. Their titles do point to the same themes "
          "(CNN classifiers, alternative backbones and, in the last case, how a decision threshold transfers to data from another source), which supports the "
          "research gap below."),
        TAB("Summary of the works compared", ["Work", "Approach", "Data", "Reported result", "Limitation"], LIT_TABLE,
            widths=[1.15, 1.25, 1.2, 1.5, 1.1], size=8.5),
        H2("2.4 Datasets and algorithms in the literature"),
        TAB("Datasets used in the surveyed work", ["Dataset", "Content", "Used by"], [
            ["Chest X-Ray Images (Pneumonia), Kermany et al. [3], [4]", "5,863 paediatric images, Normal and Pneumonia; pneumonia files carry bacterial / viral in the file name; CC BY 4.0", "[1], [3], [5], [6] and this project"],
            ["ChestX-ray14 / ChestX-ray8 [8]", "Large adult collection with 14 thoracic labels", "[7]"],
            ["Merged COVID-19 / Normal / Pneumonia / TB sets", "7,135 images in four classes (Kaggle merge of public sources)", "[1]"],
        ], widths=[2.3, 2.7, 1.2]),
        P("The algorithms fall into four families: (i) CNNs trained from scratch; (ii) ImageNet-pretrained backbones (VGG, ResNet, DenseNet, EfficientNet, "
          f"MobileNet {n(12, 13)}) fine-tuned for chest X-rays; (iii) Vision Transformers; and (iv) semi-supervised methods that add pseudo-labelling. Explanation is "
          "almost always Grad-CAM; uncertainty is Monte Carlo Dropout or calibration analysis."),
        H2("2.5 Strengths and limitations of the surveyed work"),
        B("**Strengths:** very high reported accuracy on curated benchmarks; mature, public datasets; effective transfer learning; established explanation tools.",
          "**Limitations:** results depend strongly on the split and class balance (the 84.6 % and 96-98 % figures on the same images); most studies evaluate on one source "
          "with no external site; multiclass separation of similar diseases is much weaker than binary detection; explanation and uncertainty are rarely joined "
          "to a usable application; and few papers describe a system a clinician could actually open."),
        H2("2.6 Research gap"),
        P("The batch survey summarises the gap as: *the surveyed work reports classification accuracy on public datasets; the gap is combining segmentation, "
          "calibrated uncertainty and visual explanation into a single deployable diagnostic aid.* Reading the literature in more detail sharpens it into four points:"),
        N("Most work stops at a trained model; very few present the complete path from uploaded image to explained, stored and reviewable prediction.",
          "Pathogen-type classification (bacterial against viral) is studied far less than Normal against Pneumonia, and is where reported numbers fall.",
          "Results are rarely stated together with their protocol, so numbers on the same dataset cannot be compared fairly.",
          "Segmentation to restrict the classifier to the lungs, calibrated uncertainty and explanation are discussed separately, not as one tool."),
        P("This project addresses points 1 to 3 directly. It builds the application, evaluates three-class classification on the public test split with the protocol "
          "stated, and reports where the model fails. Point 4 is only partly addressed: Grad-CAM is implemented, a confidence-threshold analysis is reported, "
          "but segmentation and calibrated uncertainty are not implemented and are listed as future work."),
    ]
    return b
