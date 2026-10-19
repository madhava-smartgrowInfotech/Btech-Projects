"""Chapters 9 and 10 and the sections reused by the scope, methodology, design and conclusion documents."""

from .appendix import source
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .ch1 import ASSUMPTIONS, CONTRIBUTIONS, LIMITATIONS, SCOPE_IN, SCOPE_OUT
from .refs import n
from . import facts as F


def _t():
    M = F.DEPLOYED or {}
    return M.get("test", {}), M.get("test", {}).get("binary_normal_vs_pneumonia", {})


# ------------------------------------------------------------------ methodology document extras
def novelty_blocks():
    T, Bn = _t()
    return [
        P(f"The base paper {n(1)} is a research study of lightweight networks and semi-supervised learning. This project does not try to beat its benchmark numbers; its contribution is of a different kind. "
          "The table separates what is new in this work from what is standard practice that it reuses."),
        TAB("Novelty against the base paper", ["Aspect", "Base paper", "This project", "Novel here?"], [
            ["Output classes", "Normal / Pneumonia, and a 4-class multi-disease set", "Normal / Bacterial / Viral pneumonia (pathogen type)", "Different task; pathogen type is harder and less studied"],
            ["Deliverable", "Experimental framework", "End-to-end web application: login, upload, prediction, heat map, history, dashboard, export, tests", "**Yes**: the main contribution"],
            ["Train/serve consistency", "Models pre-processed with the MobileNetV3 function", "One preprocessing function (CLAHE + blur) shared by training, Flask and FastAPI; the original `train.py` lacked CLAHE", "**Yes**: found and fixed in the experiment script"],
            ["Validation design", "Balanced random subsets, seed 42", "Patient-level validation split; second protocol re-partitions all data by patient", "Partly: adopts good practice from [6]"],
            ["Test-set hygiene", "Not discussed", "Counts how many official test images share an id with training and reports an id-disjoint subset", "**Yes** for this project; the issue itself was raised in [6]"],
            ["Uncertainty", "Monte Carlo Dropout, TTA, ECE", "ECE and a confidence-threshold analysis (no MC Dropout)", "Simpler; **not** a novelty"],
            ["Explanation", "Grad-CAM on test images", "Grad-CAM generated and stored for every scan, shown next to the image", "Application of a standard method"],
            ["Semi-supervised learning", "FixMatch, FlexMatch, FreeMatch", "Not used", "Not reproduced"],
            ["Architecture", "MobileNet family", "Compact custom CNN; MobileNetV3Small compared as a baseline", "Standard components"],
        ], widths=[1.1, 1.6, 2.2, 1.4], size=9),
        P("**What is not new.** CLAHE, batch-normalised CNNs, Grad-CAM, class-weighted cross-entropy and patient-level splitting are all established techniques, and the dataset is public. The project's "
          "value lies in combining them into one reproducible, tested and inspectable system, and in reporting its performance with the protocol stated."),
    ]


def contribution_blocks():
    T, Bn = _t()
    extra = []
    if T:
        extra = [f"A measured baseline: {F.pct(T['accuracy'])} three-class accuracy, {F.pct(Bn['sensitivity'])} pneumonia sensitivity and {F.pct(Bn['specificity'])} specificity on the official test split, with the patient-overlap caveat quantified."]
    return [P("The contributions of the project, in order of importance:"), N(*(CONTRIBUTIONS + extra))]


# ------------------------------------------------------------------ scope document
def scope_blocks():
    return [
        H2("1.1 In scope"),
        TAB("In scope", ["#", "Item"], [[str(i), s] for i, s in enumerate(SCOPE_IN, 1)], widths=[0.4, 5.9], align=["c", "l"], size=10.5),
        H2("1.2 Out of scope"),
        TAB("Out of scope", ["#", "Item"], [[str(i), s] for i, s in enumerate(SCOPE_OUT, 1)], widths=[0.4, 5.9], align=["c", "l"], size=10.5),
        P("The boundary is deliberate. The system is a screening-support prototype whose predictions are always accompanied by a heat map and a disclaimer; anything that would make it a clinical tool "
          "(regulatory approval, validation on patients, integration with hospital systems) is outside the project."),
    ]


def assumption_blocks():
    return [B(*ASSUMPTIONS)]


def limitation_blocks():
    T, Bn = _t()
    out = [B(*LIMITATIONS)]
    if T:
        out += [P(f"**Evidence from the measurements.** The three-class accuracy on the official test split is {F.pct(T['accuracy'])}, and the recall of the weakest class is "
                  f"{F.pct(min(v['recall'] for v in T['per_class'].values()))}. The expected calibration error is {F.f3(T['expected_calibration_error'])}. These figures come from one seed and one "
                  "data source and carry no confidence interval.")]
    out += [TAB("Risks and mitigations", ["Risk", "Mitigation in the project"], [
        ["Output mistaken for a diagnosis", "Disclaimer on every screen and in the README; Demo Mode alert for untrained models; heat map shown with every prediction"],
        ["Over-confident wrong prediction", "Confidence shown with the full probability bars; threshold analysis in Chapter 8; recommendation to review low-confidence scans"],
        ["Distribution shift (other hospitals, adults)", "Stated as a limitation; no claim beyond the public paediatric data"],
        ["Test-set overlap inflating results", "Patient-disjoint subset and patient-level re-partition reported beside the official split"],
        ["Unauthorised access", "Signed HttpOnly cookie, 401 on protected routes; demo account only, no real patient data should be loaded"],
    ], widths=[2.0, 4.3], size=10)]
    return out


def not_measured_blocks():
    return [
        P("The following were not measured and are therefore stated as gaps, not estimated:"),
        B("Run-to-run variation (confidence intervals): each configuration was trained once with seed 42.",
          "Performance on any data source other than the Kermany paediatric dataset.",
          "Agreement with radiologists, or any human-factors or usability study with clinicians.",
          "Load, concurrency and long-running behaviour of the API beyond the single-inference lock.",
          "The effect of U-Net segmentation, Monte Carlo Dropout or semi-supervised learning, which were not implemented.",
          "The effect of horizontal-flip augmentation (the base paper disables it); the shipped augmentor was used unchanged.",
          "Browsers other than Chromium and any assistive technology for the user-interface checks."),
    ]


# ------------------------------------------------------------------ design document extras
def walkthrough_blocks():
    s = source
    return [
        H2("3.1 Preprocessing: one function for training and serving"),
        P("`load_and_preprocess_image` accepts a path or raw bytes, so the API can decode an upload without writing it first and the training script can read from disk with the same code."),
        CODE(s("model/preprocess.py", "def load_and_preprocess_image", "def preprocess_for_display")),
        H2("3.2 Grad-CAM"),
        P("A second model maps the input to the last convolutional feature maps and the output; the gradient of the chosen class score with respect to those maps gives the channel weights. "
          "Because the function needs the feature tensor to be connected to the model input, it works on a flat network and fails on a nested backbone."),
        CODE(s("model/gradcam.py", "def make_gradcam_heatmap", "def overlay_heatmap")),
        H2("3.3 Prediction route"),
        P("The route validates in a fixed order, saves the upload under a random name, preprocesses, runs the network and Grad-CAM under a lock, writes the overlay and the row, and returns the stored record."),
        CODE(s("backend/main.py", '@api.post("/api/predict"', '@api.get("/api/predictions")')),
        H2("3.4 Signed session cookie"),
        P("The session is stateless: the cookie carries the e-mail and an expiry, signed with HMAC-SHA256, verified with a constant-time comparison."),
        CODE(s("backend/main.py", "def _sign", "class Login")),
        H2("3.5 Patient-level split in the training script"),
        CODE(s("scripts/train_experiment.py", "    if args.protocol == \"official\":", "    # how many test images share a patient id")),
    ]


def decision_blocks():
    return [
        TAB("Decisions and reasons", ["Decision", "Alternatives considered", "Reason", "Consequence"], [
            ["Keep the original Flask app untouched; add FastAPI beside it", "Rewrite the back end; port the model code", "No logic needed to change; both interfaces share one model loader", "Two entry points to maintain, one model implementation"],
            ["Signed HttpOnly cookie for the demo login", "Bearer token in `localStorage`", "`<img>` tags cannot send headers, and the images are behind the login; HttpOnly keeps the token away from scripts", "Needs a proxy or same-origin setup (provided by Vite)"],
            ["Custom CNN as the deployed model", "DenseNet / EfficientNet / MobileNetV3Small", "Small, CPU-trainable, flat so Grad-CAM works", "Lower ceiling than transfer learning"],
            ["CLAHE in training and inference", "No enhancement", "Standard for radiographs; the inference path already used it; ablation measures the effect", "Slight extra cost per image"],
            ["Patient-level validation split", "Random image split", "Several images belong to one patient; a random split leaks", "Slightly noisier validation"],
            ["Balanced class weights", "Resampling", "Bacterial images are twice as frequent; weights keep every image", "Loss values not comparable to unweighted runs"],
            ["Report on id-disjoint and patient-level protocols as well", "Report only the official test split", "The official split shares pneumonia ids with training", "More numbers to explain; fewer misleading ones"],
            ["SQLite with one table", "PostgreSQL, multiple tables", "One entity; zero administration", "Not built for many concurrent users"],
            ["Vite proxy for `/api`", "CORS-only, cross-origin cookies", "One origin, first-party cookie, simpler", "Production would need a reverse proxy"],
            ["Demo Mode when weights are missing", "Refuse to start", "Lets anyone run the pipeline; a banner states the limitation", "Predictions meaningless until trained"],
        ], widths=[1.5, 1.4, 2.2, 1.2], size=8.5),
    ]


# ------------------------------------------------------------------ chapters 9 and 10
def conclusion_blocks():
    T, Bn = _t()
    mi = F.MODEL_INFO or {}
    py = ((F.TESTS or {}).get("pytest") or {}).get("passed", 0)
    A = None
    from .ch8 import analysis

    A = analysis()
    out = [
        H1("CHAPTER 9: CONCLUSION"),
        H2("9.1 Summary"),
        P("The project set out to build an explainable pneumonia detection system and to measure it honestly. It delivers a working pipeline in which a chest X-ray is validated, enhanced with CLAHE, "
          "classified by a compact CNN into Normal, Bacterial or Viral pneumonia, explained with a Grad-CAM heat map and stored with its result, behind a FastAPI service, a React interface "
          "and the original Flask interface. A reproducible training script, a patient-aware evaluation, ten design diagrams and an automated test suite complete the work."),
        H2("9.2 Objectives achieved"),
        P("Five of the six objectives were met: data preparation, a trained CNN classifier, the requested evaluation, heat-map visualisation and deployment behind an interface (Section 8.11). "
          "The second objective, U-Net lung segmentation, was **not** achieved: no segmentation network was implemented, so the classifier sees the whole radiograph."),
    ]
    if T:
        out += [
            H2("9.3 Key findings"),
            B(f"A {mi.get('total_params', 0):,}-parameter CNN trained on a desktop CPU reaches {F.pct(T['accuracy'])} three-class accuracy and macro F1 {F.f3(T['macro_f1'])} on the official 624-image test split.",
              f"Viewed as pneumonia against normal, sensitivity is {F.pct(Bn['sensitivity'])} and specificity {F.pct(Bn['specificity'])}; {A['weak']}.",
              "The official test folder shares pneumonia ids with the training folders; the id-disjoint and patient-level results in Chapter 8 should be preferred when judging generalisation.",
              "Reported accuracy on the same public images varies from about 80 % to 98 % across studies with different protocols, so numbers must be quoted with their protocol.",
              "The shipped Grad-CAM works only on flat networks; transfer-learning backbones need a Grad-CAM that reaches nested layers.",
              f"The system is verified by {py} automated tests plus a live smoke test and browser checks."),
        ]
    out += [
        H2("9.4 Practical applications"),
        B("A teaching tool: students can upload a radiograph, see the probabilities and the heat map, and study where a CNN looks.",
          "A research scaffold: the training script, evaluation protocol and application can be reused with other chest X-ray datasets or models.",
          "A triage-support prototype: with proper validation, confidence thresholds could flag low-confidence scans for review."),
        H2("9.5 Known limitations"),
        B(*LIMITATIONS[:6]),
    ]
    return out


def chapter9_blocks():
    return conclusion_blocks()


def future_blocks():
    return [
        H1("CHAPTER 10: FUTURE SCOPE"),
        H2("10.1 Improvements to the model"),
        B(f"**U-Net lung segmentation** (objective 2): train a segmentation network {n(10)} on lung masks and classify only the lung region, which should also make Grad-CAM maps more specific.",
          "**Transfer learning with a Grad-CAM that reaches nested backbones** (for example by building a flat model from the backbone's layers), so that MobileNetV3Small, EfficientNet or DenseNet can be deployed with explanations.",
          f"**Calibrated uncertainty:** temperature scaling and Monte Carlo Dropout {n(15)} so that confidence tracks accuracy, and an automatic 'send for review' flag.",
          "**Orientation-safe augmentation:** remove horizontal flips, as the base paper does, and measure the effect.",
          "**Repeated runs and cross-validation** at patient level to give confidence intervals."),
        H2("10.2 Additional features"),
        B("Real user accounts and roles, an audit log of who analysed which scan, and per-user histories.",
          "DICOM input and metadata handling; batch upload; PDF report generation.",
          "A reviewer workflow in which a clinician confirms or corrects a prediction, feeding a labelled set for retraining.",
          "Multi-language interface and printable reports for the target clinics."),
        H2("10.3 Scalability and deployment"),
        B("Package the API and the built front end in containers behind a reverse proxy with HTTPS; replace SQLite by a server database and the local folders by object storage.",
          "Serve the model from a dedicated inference process or a GPU host with a queue, instead of the in-process lock.",
          "Add monitoring of latency, error rates and the distribution of predicted classes to detect drift."),
        H2("10.4 Further research"),
        B("External validation on adult and multi-hospital data and a prospective clinical study.",
          f"Semi-supervised learning with FixMatch, FlexMatch or FreeMatch {n(1, 14)} to use unlabelled radiographs.",
          "A study of how clinicians use the heat map, and whether it improves or biases their decisions.",
          "Joint modelling of segmentation, classification and uncertainty in one network."),
    ]


def chapter10_blocks():
    return future_blocks()
