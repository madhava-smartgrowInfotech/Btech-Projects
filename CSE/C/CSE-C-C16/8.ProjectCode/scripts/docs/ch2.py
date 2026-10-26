"""Chapter 2: Literature Survey. Numbers about other papers come from the PDFs read (Foliagen, PD36-C, Kanakala and Ningappa, PlantDoc); see refs.py."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import cite

MB, C = F.MB, F.C


def blocks():
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The survey has four parts. First the base paper named in the batch documents, Foliagen " + cite("base") + ", is analysed in depth. Then related work is grouped by "
          "theme: datasets, leaf classification with convolutional networks, data generation and generalisation, and efficient models with transfer learning. The datasets and "
          "algorithms that matter for this project are then summarised, and the strengths and limits of the approaches are set against what a farmer needs. The chapter ends with "
          "the research gap that the project addresses."),
        P("Every figure quoted below was read from the paper concerned (the PDFs of the base paper, of PD36-C and of the multi-crop CNN-LSTM paper are in the batch folder; the PlantDoc "
          "paper was read from its arXiv copy). Four further sources named in the batch literature survey could not be located by web search; they are listed in Section 2.7 "
          "and no result is taken from them."),
        H2("2.2 Base Paper Analysis: Foliagen"),
        P("**Reference.** N. Pakka, T. Wilkerson, L. Chen and N.-F. Tzeng, *Foliagen: Framework for Crop Foliage Image Generation from Individual Leaf Images*, IEEE Access, 2026 "
          "(DOI 10.1109/ACCESS.2026.3727421) " + cite("base") + ". The authors are from the University of Louisiana at Lafayette and Mississippi State University."),
        H3("2.2.1 Problem the paper solves"),
        P("Most machine learning classifiers for crop disease are trained on photographs of single leaves, but practical monitoring, for example with cameras on unmanned aerial "
          "vehicles, produces photographs of whole foliage. Properly annotated foliage datasets are scarce because every leaf must be annotated by an experienced agronomist. The "
          "authors know of one public annotated soybean foliage set (MH-SoyaHealthVision, with two disease categories) and no public tomato foliage set. Generative models "
          "(Pixel-CNN, RDCGAN, DDPM) produce foliage that is ill-structured and differs from field images, so the paper proposes a structure-based generator instead."),
        H3("2.2.2 Method"),
        P("Foliagen works in three levels (leaf, plant, foliage). Background is removed from each single-leaf photograph with the open-source tool rembg. A configuration file fixes "
          "the crop, the disease type, the leaf structure, the number of leaves and the disease rate gamma, the share of diseased leaves in each image. A spiral phyllotactic generator "
          "places leaves around a stem following the way real plants arrange leaves, plants are combined into foliage over soil-image backgrounds, and every image is annotated "
          "by design. Each generated set holds about 1,000 foliage images per disease category plus a similar number of healthy ones, with gamma between 1 % and 20 %; the "
          "natural soybean set has gamma between 12 % and 18 % (mean about 15 %), which is the value used in most experiments."),
        H3("2.2.3 Data"),
        P("For soybean, 10,722 single-leaf images covering seven diseases come from ASDID, plus 132 images (22 mosaic virus, 110 sudden death syndrome) from a Kaggle set; tomato "
          "images come from PlantVillage. Each generated dataset covers nine primary disease categories. The natural foliage set used for testing is MH-SoyaHealthVision."),
        H3("2.2.4 Experiments and results"),
        P("Five classifiers were trained on two workstations with two NVIDIA RTX 6000 Ada GPUs each: VGG19, ResNet50, DenseNet121, Swin Transformer and CBAM-ConvNeXt (Adam, "
          "learning rate 1e-4, batch size 8, up to 100 epochs, early stopping with patience 5). The paper reports four results. (1) Dataset validation: the accuracy vectors of the "
          "five classifiers on generated and natural foliage have a cosine similarity of 0.9914 (F1: 0.9997), so the generated set behaves like the real one. (2) On the natural "
          "set alone the best classifier stays below 91.5 % accuracy. (3) Mixing generated data with only 5 % of the natural set reaches up to 98.5 % accuracy (ResNet50) on the "
          "remaining 85 % and improves accuracy by up to 34 % over using the 5 % alone. (4) Pre-training on generated foliage and fine-tuning on 5 % of the natural set gives "
          "88.0 % to 95.8 % accuracy across the five classifiers. An ablation shows that removing the plant-level structure, using random copy-paste or leaving the images "
          "unprocessed lowers accuracy substantially."),
        H3("2.2.5 Strengths and limits"),
        B("**Strengths.** A creative answer to the scarcity of annotated foliage data; annotation is free by design; the framework is validated numerically against a real set and "
          "ablated; code and data are released.",
          "**Limits stated by the authors.** Effectiveness depends on the quality and variety of the single-leaf images; crops with overlapping canopies or complex branching "
          "need crop-specific structure; disease appearance that changes with growth stage or neighbouring leaves needs better disease-distribution models.",
          "**Limits for this project.** The paper stops at a trained classifier. It contains no application, no treatment or fertiliser advice, no farmer interface and no multilingual "
          "support; it covers soybean and tomato only; and it needs GPU workstations."),
        H3("2.2.6 What this project takes from it, and what it does not"),
        P("The batch document states that the base paper \"establishes the core technique for this problem domain\" and that the project \"extends it to the specific scope described "
          "in the abstract\". In practice this project does not implement Foliagen, because it works on single-leaf photographs of 14 crops, not on foliage images. What it takes "
          "from the paper is its diagnosis of the problem: classifiers trained on clean single-leaf images do not transfer to field photographs, small annotated sets need help "
          "(augmentation, pre-training, fine-tuning), and results must be reported per scenario. The project's own measurements reproduce that diagnosis on PlantDoc (Chapter 8) "
          "and its transfer-learning reference follows the same pre-train-then-fine-tune idea with ImageNet weights instead of generated foliage."),
        H2("2.3 Related Work by Theme"),
        H3("2.3.1 Datasets and benchmarks"),
        P("PlantVillage " + cite("plantvillage") + " is the collection behind most published leaf-disease results: laboratory photographs on plain backgrounds. Mohanty et al. " +
          cite("mohanty") + " trained AlexNet and GoogLeNet on 54,306 PlantVillage images of 14 crops and 26 diseases and reached 99.35 %, and warned that accuracy falls on images taken under "
          "other conditions. PlantDoc " + cite("plantdoc") + " was built to test exactly that: 2,598 web-scraped photographs of 13 plants and 27 classes, with real backgrounds, "
          "varied resolution and lighting. Other field datasets named in the base paper are FieldPlant " + cite("fieldplant") + " and TomatoVillage " + cite("tomatovillage") +
          ". PlantDoc is the dataset used for every measurement in this project because it is the only one with field photographs whose labels map onto the 38-class knowledge "
          "base and which could be obtained and processed on the available hardware."),
        H3("2.3.2 Leaf-disease classification with CNNs"),
        P("Ferentinos " + cite("ferentinos") + " compared five architectures on 87,848 images of 25 plants and 58 classes and reports 99.53 % for the best. PD36-C " + cite("pd36c") +
          " is a compact 18-layer network with 1,250,694 parameters (4.77 MB) trained on the 87 k-image New Plant Diseases Dataset (38 classes) with a desktop application for "
          "offline inference; it reports 99.53 % average test accuracy, 99.697 % training accuracy, perfect precision and recall for many classes, and lower precision (97.77 %) "
          "and recall (0.9634) for corn Cercospora leaf spot. The authors themselves note that adverse weather, low-quality images and leaves with several diseases degrade performance. "
          "Kanakala and Ningappa " + cite("lstm") + " compare a CNN and an LSTM on 70,295 training and 17,572 validation images (38 classes): the CNN reaches 99.1 % training and 96.4 % "
          "validation accuracy after ten epochs, the LSTM 93.43 % validation accuracy, and the validation loss of the CNN fluctuates, which the authors read as possible over-fitting. "
          "Wu et al. " + cite("convnext") + " apply an improved ConvNeXt to soybean leaf diseases."),
        H3("2.3.3 Data generation and generalisation"),
        P("Abbas et al. " + cite("cgan") + " train a conditional GAN to synthesise tomato leaves and use them for transfer learning. Foliagen " + cite("base") + " goes further and builds "
          "foliage images by structure rather than by a generative network. Barbedo " + cite("barbedo") + " analyses the factors that limit deep learning for plant disease "
          "recognition: backgrounds, variation in symptoms, small training sets and uncontrolled image conditions. The common message of this theme is that the benchmark "
          "scores of Section 2.3.2 are not what a farmer will get with a phone."),
        H3("2.3.4 Efficient models and transfer learning"),
        P("Edge use needs small networks. MobileNetV2 " + cite("mobilenet") + " (inverted residuals with linear bottlenecks) and EfficientNet " + cite("efficientnet") +
          " are the usual choices, and depthwise-separable convolutions " + cite("xception") + " are the building block of the compact CNN in this project's training script. "
          "Pre-training on ImageNet " + cite("imagenet") + " and fine-tuning is the standard remedy for small datasets, and the PlantDoc authors show that it matters: "
          "ImageNet-only pre-training gives 44.5 % to 49.0 % on cropped PlantDoc leaves, and adding PlantVillage pre-training lifts InceptionResNetV2 to 70.5 %."),
        H3("2.3.5 Explanation and advice"),
        P("Visual explanation of a prediction, for example Grad-CAM heat maps " + cite("gradcam") + ", is used in several leaf-disease papers (the PlantDoc paper shows saliency and "
          "activation maps for corn leaf blight and tomato bacterial spot) to show that the network looks at lesions rather than at the background. Advice on what to do after the "
          "diagnosis is almost absent from the classification papers; where it is present it is part of an application, not of the learning method. This project implements advice "
          "as a knowledge base and leaves heat maps to future work, because the engine in the application is not a neural network."),
        TAB("PlantDoc benchmark results reported by its authors (cropped leaves, 80/20 split, 100 x 100 px)", ["Model", "ImageNet only: train and test on PlantDoc", "PlantVillage only: test on PlantDoc", "ImageNet + PlantVillage, then PlantDoc"],
            [["VGG16", "44.52 %", "19.73 %", "60.41 %"], ["InceptionV3", "46.67 %", "30.78 %", "62.06 %"], ["InceptionResNetV2", "49.04 %", "39.87 %", "70.53 %"]],
            widths=[1.6, 1.8, 1.7, 1.6], align=["l", "c", "c", "c"], size=9.5),
        P("The middle column is the instructive one: networks trained on the laboratory-style PlantVillage collection reach only 19.7 % to 39.9 % on PlantDoc photographs. "
          "That is the generalisation failure the base paper's introduction describes for single-leaf datasets, and it is the reason why this project measures on PlantDoc and "
          "does not quote PlantVillage-style scores as its own."),
        H2("2.4 Summary Table of Related Work"),
        TAB("Related work reviewed (all figures as reported by the papers)", ["Work", "Approach", "Data", "Reported result", "Limitation"], lit.LIT_TABLE,
            widths=[1.1, 1.7, 1.2, 1.5, 1.1], align=["l", "l", "l", "l", "l"], size=8.5),
        TAB("The base paper, PD36-C and this project compared", ["Aspect", "Foliagen " + cite("base"), "PD36-C " + cite("pd36c"), "AgriVision (this project)"],
            [["Task", "Generate foliage images to train classifiers", "Classify single-leaf images", "Diagnose a leaf photograph and return advice"],
             ["Crops", "Soybean, tomato", "38 PlantVillage classes (14 crops)", "38 classes, 14 crops; PlantDoc covers 13 crops"],
             ["Data", "Generated foliage + MH-SoyaHealthVision", "87 k laboratory-style images", f"PlantDoc field photographs, {F.NTRAIN:,} + {F.NTEST}"],
             ["Hardware", "Two workstations, 2 x RTX 6000 Ada each", "Desktop application for offline inference", "One Core i5-12500 PC, CPU only"],
             ["Best accuracy", "Up to 98.5 % (generated + 5 % natural foliage)", "99.53 %", f"{F.pm(MB)} (MobileNetV2 reference); {F.pct(F.HC['accuracy']['mean'])} (shipped engine)"],
             ["Advice for the farmer", "None", "None", "Treatments, prevention, severity for 38 classes"],
             ["Language", "English", "English", "Interface in English, Hindi, Marathi"]],
            widths=[1.2, 1.9, 1.7, 1.9], align=["l", "l", "l", "l"], size=9),
        P("The table shows that the three works are not competitors. The base paper solves a data problem, PD36-C a model-size problem, and this project an application problem "
          "that the other two leave open. The accuracy row must not be read as a ranking: the datasets, class sets and conditions differ completely."),
        H2("2.5 Datasets and Algorithms Used in This Project"),
        TAB("Datasets and algorithms and where they appear in this project", ["Item", "Source", "Used for"],
            [["PlantDoc", "Singh et al. " + cite("plantdoc") + ", CC-BY-4.0", f"All measurements: {F.NTRAIN:,} training and {F.NTEST} test photographs, 28 class folders"],
             ["38-class label set", "PlantVillage / PD36-C " + cite("pd36c"), "Knowledge base and API labels; PlantDoc folders are mapped onto it"],
             ["Colour and texture heuristic", "this project (original Flask product)", "The engine shipped in the application"],
             ["Compact depthwise-separable CNN", "train.py, in the spirit of PD36-C " + cite("pd36c", "xception"), f"Trained here: {F.pm(C)} accuracy"],
             ["MobileNetV2 transfer learning", "Sandler et al. " + cite("mobilenet") + ", ImageNet weights", f"Reference experiment: {F.pm(MB)} accuracy"],
             ["Random forest, logistic regression", "Breiman " + cite("rf") + ", scikit-learn " + cite("sklearn"), "Hand-made colour and texture features baseline"],
             ["Adam, batch normalisation, augmentation", cite("adam", "bn"), "Training of the CNNs"]],
            widths=[1.8, 2.2, 2.6], align=["l", "l", "l"], size=9.5),
        H2("2.6 Strengths and Limitations of the Surveyed Approaches"),
        B("**Accuracy on curated data is not the problem.** Several works report 96 % to 99.5 % on PlantVillage-style collections " + cite("mohanty", "ferentinos", "pd36c", "lstm") +
          ". That is high enough to make a diagnosis tool useful if the photographs resemble the training images.",
          "**Field photographs are.** The PlantDoc authors report 13.7 % to 29.7 % for VGG16 on raw photographs and 44.5 % to 70.5 % on cropped leaves " + cite("plantdoc") +
          "; this project measures 50.3 % with MobileNetV2 on raw test photographs (Chapter 8).",
          "**Compact networks make edge deployment plausible** " + cite("pd36c", "mobilenet") + " but are reported only on laboratory-style data.",
          "**Almost none of the surveyed work goes beyond a class label.** Treatment advice, language, history of scans, exports and a deployed interface are outside the papers; "
          "PD36-C comes closest, with a desktop application, but offers no advice."),
        H2("2.7 Sources Named in the Batch Survey That Could Not Be Verified"),
        P("The batch literature survey (5.LITERATURE SURVEY.docx) lists, besides the base paper, four sources by title, year and venue only. A web search did not locate them, so "
          "their authors and findings are not known to the project team and nothing is claimed from them; they appear in the reference list as entries " +
          cite("s1", "s2", "s3", "s4") + " with a note."),
        TAB("Sources listed in the batch survey and not verified", ["No.", "Title (as listed)", "Year", "Venue (as listed)"],
            [["1", "Leaf Based Crop Disease Detection", "2026", "International Journal of Research Publication and Reviews"],
             ["2", "Explainable CNN framework for accurate crop disease detection using plant leaf images", "2026", "Scientific Reports"],
             ["3", "AI-Driven Plant Disease Detection: Leveraging Deep Learning for Accurate Plant Disease Detection from Leaf Images", "2024", "International Journal of Science and Research (IJSR)"],
             ["4", "Plant Leaf Disease Detection: Review Report", "2025", "International Journal of Science and Research (IJSR)"]],
            widths=[0.5, 3.4, 0.6, 2.1], align=["c", "l", "c", "l"], size=9.5),
        H2("2.8 Research Gap"),
        P(lit.GAP),
        P("Stated as requirements, the gap has four parts that the project tries to close: (a) a classification that is measured on field photographs, not only on laboratory images; "
          "(b) a mapping from each recognised class to treatment, prevention and severity information a farmer can act on; (c) delivery through an interface a non-expert can use, "
          "in more than one language; and (d) an honest account of the distance between the benchmark scores in the literature and what the delivered system achieves. "
          "Parts (b) and (c) are delivered; part (a) is measured and shows a large gap; part (d) is the content of Chapters 7 and 8."),
    ]
