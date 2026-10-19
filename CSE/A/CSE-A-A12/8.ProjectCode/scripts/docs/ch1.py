"""Chapter 1: Introduction (blocks are shared with the scope / limitations document)."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

OBJECTIVES = [
    "Acquire and preprocess a chest X-ray dataset with consistent resizing, normalisation and augmentation.",
    "Apply U-Net based lung segmentation to isolate the region of interest before classification.",
    "Train a CNN classifier to distinguish pneumonia-positive from normal chest X-rays.",
    "Evaluate using accuracy, sensitivity, specificity, F1-score and a confusion matrix.",
    "Generate heatmap visualisations so each prediction can be verified against the image.",
    "Deploy the model behind an interface that returns the prediction with its confidence and heatmap.",
]

SCOPE_IN = [
    "Three-way classification of a single frontal chest X-ray into Normal, Bacterial Pneumonia or Viral Pneumonia, with per-class probabilities.",
    "The preprocessing chain actually used in the code: grayscale decoding, resizing to 224 x 224, CLAHE contrast enhancement, light Gaussian smoothing and scaling to [0, 1].",
    "A convolutional network written for the project (four convolution blocks, global average pooling and a dense head), plus a transfer-learning builder for DenseNet, ResNet and EfficientNet backbones.",
    "A Grad-CAM heatmap overlay for the predicted class on every scan.",
    "A web application with a React front end, a FastAPI service and the original Flask interface, a signed-cookie demo login, SQLite history, a dashboard, CSV export and deletion of stored scans.",
    "A reproducible training and evaluation script, an automated test suite and the documentation set.",
]

SCOPE_OUT = [
    "U-Net lung segmentation. It is an objective of the project proposal, but no segmentation network is implemented, trained or evaluated; the classifier sees the whole radiograph.",
    "Clinical use. The system is a research prototype for screening support and has not been validated on patients, by radiologists or by any regulator.",
    "Any imaging modality other than frontal chest X-rays, any disease other than pneumonia, and adult or non-paediatric validation (the training data are paediatric).",
    "DICOM handling, PACS or hospital information system integration, multi-user accounts, role management and audit logging.",
    "Semi-supervised learning, Monte Carlo Dropout uncertainty and external multi-hospital validation, which the base paper studies and this project does not reproduce.",
    "Cloud deployment, containerisation and horizontal scaling.",
]

ASSUMPTIONS = [
    "The uploaded image is a frontal (PA or AP) chest radiograph in PNG or JPEG form and no larger than 8 MB.",
    "The public Kermany dataset is representative enough of paediatric chest X-rays to demonstrate the pipeline; its labels are taken as ground truth.",
    "Bacterial and viral labels are derived from the file names of the dataset (person*_bacteria_*, person*_virus_*), as the original authors encoded them.",
    "A single trusted user population: the demo login is a convenience, not an identity system.",
    "The machine running the system has Python 3.10 or 3.11, Node.js 18 or newer and about 2 GB of free disk for the Python environment.",
]

LIMITATIONS = [
    "**No U-Net segmentation.** One of the six stated objectives was not met; the model may use image regions outside the lungs, and the Grad-CAM maps in Chapter 8 show that it sometimes does.",
    "**Single data source.** All training and test images come from one paediatric centre. The official test split is known to differ in distribution from the training split, and no external hospital data were available, so the reported figures say little about performance elsewhere.",
    "**Modest absolute accuracy.** Normal radiographs are often called pneumonia and the two pneumonia types overlap on a radiograph alone; the confusion matrix in Chapter 8 shows where the model fails.",
    "**CPU-only training.** All training was run on a desktop CPU (no GPU), which limited the number of experiments and made large backbones impractical.",
    "**Class labels from file names.** Pathogen type is not independently verified by the authors of this project.",
    "**Uncalibrated probabilities.** Confidence is the raw softmax output; no temperature scaling or Monte Carlo Dropout is applied, so a high confidence is not a guarantee of correctness.",
    "**Security is demonstration-grade.** A single shared demo account, an HMAC-signed cookie and an HTTP-only transport; the original Flask application still uses a fixed secret key and offers no login.",
    "**Not a medical device.** Outputs must not be used as the sole basis for diagnosis or treatment.",
]

CONTRIBUTIONS = [
    "A complete, runnable pipeline from upload to explained prediction: validation, CLAHE-based preprocessing, a three-class CNN, a Grad-CAM overlay and persistent history.",
    "A training and evaluation procedure (`scripts/train_experiment.py`) that uses the same preprocessing function at training and inference time, splits validation data by patient to avoid leakage, and writes every metric to JSON.",
    "A measured baseline for the project's own architecture on the public Kermany test split, including a three-class confusion matrix, a Normal-versus-pneumonia view, calibration error, a confidence-threshold analysis and an ablation of the CLAHE step.",
    "A thin API layer and a new React front end over the existing Flask project, with a demo login, dashboard, history search, export and printable report, without changing the original model code.",
    "An automated test suite and design documentation (ten diagrams) that make the system reproducible and reviewable.",
]


def blocks():
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Domain overview"),
        P("Pneumonia is an infection that inflames the air sacs of one or both lungs. It remains one of the leading infectious causes of death, "
          f"particularly among children under five and elderly people {n(1, 2)}. The chest X-ray is the most widely used first-line imaging test for the disease "
          "because it is fast, inexpensive and available in almost every clinic. Interpreting it, however, requires an experienced reader: opacities can be "
          "subtle, their appearance overlaps with other respiratory illnesses, and the same film can be read differently by two clinicians."),
        P("Deep learning, and convolutional neural networks (CNNs) in particular, has become the dominant technique for automatic analysis of medical images "
          f"{n(28)}. On chest radiographs, CNNs have been shown to approach radiologist-level performance for pneumonia detection {n(7)} and a large body of "
          f"work now compares architectures, preprocessing choices and explanation methods on public datasets {n(1, 5, 6)}. The domain of this project is therefore "
          "Artificial Intelligence and Machine Learning applied to medical image analysis and clinical decision support."),
        H2("1.2 Background and motivation"),
        P("Radiologists are scarce in exactly the settings where pneumonia is most dangerous: rural clinics, paediatric wards in low-resource hospitals and "
          "emergency departments at night. A tool that gives a first opinion within seconds, and shows *why* it reached that opinion, could help a "
          "non-specialist decide whether a case needs urgent escalation. Two properties make such a tool credible. First, it must separate the clinically "
          "important classes: normal film, bacterial pneumonia (usually treated with antibiotics) and viral pneumonia (usually not). Second, it must be "
          "transparent: a bare label from a black-box network is not acceptable in a clinical workflow, whereas a heat map that highlights the lung regions "
          f"that drove the decision can be checked against the image {n(9)}."),
        P(f"The base paper for this project {n(1)} studies lightweight MobileNet networks, semi-supervised learning and uncertainty estimation for chest X-ray "
          "classification and uses Grad-CAM to confirm that predictions rely on clinically relevant regions. It targets research benchmarks. The motivation of "
          "this project is complementary: to build the whole path from an uploaded image to an explained, stored and reviewable prediction, and to measure "
          "honestly how well a compact CNN performs inside that path."),
        H2("1.3 Problem statement"),
        B("Radiologist shortage delays diagnosis in exactly the settings where pneumonia is most dangerous.",
          "Manual X-ray interpretation is subject to fatigue and inter-observer variation.",
          "Most published classifiers report accuracy alone and give no visual justification.",
          "A black-box prediction cannot be accepted into a clinical workflow without explanation."),
        P("The problem addressed here is: *given a single chest X-ray, classify it as Normal, Bacterial Pneumonia or Viral Pneumonia, report the probability "
          "of each class, show which image regions supported the decision, and keep a reviewable record, all through a web interface a non-expert can use.*"),
        H2("1.4 Need for the system"),
        P("The need is for an accurate pneumonia classifier that explains every prediction visually. Existing research code seldom provides an interface, "
          "a history of past scans or a way to inspect a prediction later; existing clinical software is closed and expensive. An open, inspectable "
          "implementation lets students, researchers and developers study the full pipeline, reproduce the numbers and extend it."),
        H2("1.5 Objectives"),
        P("The project was proposed with the following objectives. Chapter 8 reports, for each, whether it was achieved."),
        N(*OBJECTIVES),
        H2("1.6 Scope"),
        P("**In scope.**"),
        B(*SCOPE_IN),
        P("**Out of scope.**"),
        B(*SCOPE_OUT),
        H2("1.7 Contributions"),
        N(*CONTRIBUTIONS),
        H2("1.8 Limitations and assumptions"),
        P("**Assumptions.**"),
        B(*ASSUMPTIONS),
        P("**Limitations.**"),
        B(*LIMITATIONS),
        H2("1.9 Organisation of the report"),
        TAB("Organisation of this report", ["Chapter", "Content"], [
            ["1  Introduction", "Domain, motivation, problem, objectives, scope, contributions, limitations."],
            ["2  Literature Survey", "The base paper in depth, related work by theme, datasets and algorithms, research gap."],
            ["3  Feasibility Study", "Technical, economic, operational and schedule feasibility."],
            ["4  System Requirements and Analysis", "Existing and proposed system, functional and non-functional requirements, hardware, software, users."],
            ["5  System Design", "Architecture, workflow, data-flow diagrams, UML, database, modules, API and UI design."],
            ["6  Methodology and Software Implementation", "Dataset, preprocessing, model, mathematics, training, application, security, installation."],
            ["7  System Testing", "Strategy and results of unit, integration, functional, security, performance and edge-case tests."],
            ["8  Results and Output Screens", "Model performance, comparison with the base paper, output screens, failure analysis, objectives versus outcomes."],
            ["9  Conclusion", "Summary, achievements, findings, applications, known limitations."],
            ["10 Future Scope", "Improvements, features, deployment and research directions."],
            ["Appendices", "A: important code; B: installation and user guide; C: additional screens."],
        ], widths=[2.3, 3.9]),
    ]
