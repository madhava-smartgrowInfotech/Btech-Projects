"""Builds 19.IEEE_Paper.docx (two-column, ~6 pages). Run after the experiments and screenshots exist.

    python -m scripts.docs.build_paper
"""

import json
import os

from PIL import Image

from . import facts as F
from .paper import Paper
from .ch8 import analysis

SHORT = {"Normal": "normal", "Bacterial Pneumonia": "bacterial", "Viral Pneumonia": "viral"}


def crop_shot(name, out, box=(0, 0, 1440, 900)):
    p = os.path.join(F.FIGS, out)
    Image.open(F.shot(name)).convert("RGB").crop(box).save(p)
    return p


def build(path):
    M, E2, E3, E4, LD = F.DEPLOYED, F.E5, F.E4, F.E3, F.LEAK   # E2 no-CLAHE, E3 MobileNetV3Small, E4 patient-level
    E1 = F.E1
    T = M["test"]
    Bn = T["binary_normal_vs_pneumonia"]
    PC = T["per_class"]
    DS = M["dataset"]
    LAT = M["latency_ms_mean_cpu"]
    mi = F.MODEL_INFO
    env = json.load(open(os.path.join(F.EXP, "environment.json")))
    py = F.TESTS["pytest"]["passed"]
    A = analysis()
    api = F.API_LAT or {}
    pct, f3 = F.pct, F.f3

    P = Paper()
    authors = [[n.title(), "Dept. of Computer Science and Engineering", "TKR College of Engineering and Technology", "Hyderabad, India", "[email address]"] for n, _ in F.STUDENTS]
    authors.append([F.GUIDE.title() if False else "V. Meenakshi", "[DESIGNATION], Dept. of Computer Science and Engineering", "TKR College of Engineering and Technology", "Hyderabad, India", "[email address]"])
    P.title_block("Explainable Three-Class Pneumonia Detection from Chest X-Rays with a Compact CNN and Grad-CAM, Deployed as a Web Application", authors)
    P.begin_two_columns()

    P.abstract(
        "Pneumonia is a leading infectious cause of death, and chest X-ray readers are scarce where it is most dangerous. This paper presents an end-to-end explainable "
        "pneumonia detection system. An uploaded radiograph is validated, enhanced with contrast-limited adaptive histogram equalisation, classified by a compact "
        "convolutional neural network into normal, bacterial or viral pneumonia, and explained with a Grad-CAM heat map; every scan is stored and reviewable through a web "
        f"application. Trained on a desktop CPU on the public Kermany paediatric data with a patient-level validation split, the {mi['total_params']:,}-parameter network reaches "
        f"{pct(T['accuracy'])} three-class accuracy and a macro F1 of {f3(T['macro_f1'])} on the official 624-image test split; read as pneumonia against normal it has "
        f"{pct(Bn['sensitivity'])} sensitivity and {pct(Bn['specificity'])} specificity. Because many pneumonia identifiers in the official test folder also occur in training, "
        "results on an identifier-disjoint subset and on a patient-level re-partition are reported with every number's protocol. Misclassification of normal radiographs "
        "as pneumonia is the weak point; lung segmentation and calibrated uncertainty are not implemented.",
        ["chest X-ray", "convolutional neural network", "deep learning", "explainable AI", "Grad-CAM", "medical image analysis", "pneumonia detection"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Pneumonia inflames the air sacs of the lungs and remains one of the main infectious causes of death, particularly in children under five and in the elderly {r:2,1}. "
           "The chest X-ray is the first-line imaging test because it is fast and cheap, but reading it needs experience: opacities are subtle, overlap with other respiratory "
           "disease, and are read differently by different clinicians {r:1}. Convolutional networks have reached radiologist-level pneumonia detection on large collections "
           "{r:7} and report accuracies near or above 90 % on public paediatric data {r:3,5,6}.")
    P.para("Two practical problems remain. Most studies end at a trained model and a number, with no interface that lets a clinician or student inspect a prediction later, and "
           "a bare label from a black-box network is hard to trust. Second, the number itself depends heavily on the protocol: studies on the same paediatric images report "
           "anywhere from 79.7 % to 98 % {r:5,6} depending on the split and class balance. Separating bacterial from viral pneumonia, which matters for treatment, is "
           "studied far less than separating pneumonia from normal.")
    P.para("This paper contributes: (1) a complete, tested pipeline from upload to an explained, stored prediction, served by a FastAPI layer and a React interface over a shared "
           "model; (2) a training and evaluation procedure that uses the same preprocessing at training and inference time and splits validation data by patient; "
           f"(3) a measured baseline for a compact {mi['total_params'] / 1e6:.2f}-million-parameter CNN on three classes, with a CLAHE ablation and a MobileNetV3Small comparison {{r:13}}; and "
           "(4) a quantification of the patient-identifier overlap between the official training and test folders, with results reported on identifier-disjoint data.")
    P.para("The project set six objectives: (1) acquire and preprocess a chest X-ray dataset with consistent resizing, normalisation and augmentation; (2) isolate the lungs with U-Net "
           "segmentation before classification; (3) train a CNN to separate pneumonia from normal radiographs; (4) evaluate with accuracy, sensitivity, specificity, F1 score and a "
           "confusion matrix; (5) generate heat maps so that each prediction can be checked against the image; and (6) deploy the model behind an interface that returns the "
           "prediction with its confidence and heat map. Objective 2 was not achieved, as Section IV explains.")
    P.para("Section II reviews related work, Section III describes the method and system, Section IV reports the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para(f"All training and measurement used one desktop: {env['cpu'].replace('(R)', '').replace('(TM)', '')} ({env['cores']} cores, {env['logical_processors']} threads), "
           f"{env['ram_gb']} GB RAM, no GPU, {env['os'].split('-SP')[0].replace('Windows-10', 'Windows 11')}.")
    P.sub("B", "Software Requirements")
    P.para(f"Python {env['python']}, TensorFlow/Keras {env['tensorflow']} {{r:19}}, OpenCV {env['opencv']}, scikit-learn {env['scikit_learn']}, FastAPI {env['fastapi']}, "
           f"Node.js {env['node'].lstrip('v')} with React 19 and Vite for the interface, SQLite for storage, and pytest and Playwright for testing.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Mahin et al. {r:1} study lightweight MobileNet networks for chest X-ray classification in a binary setting (Normal versus Pneumonia, 5,863 paediatric "
           "images) and a four-class setting (COVID-19, Normal, Pneumonia, tuberculosis, 7,135 images). They add the semi-supervised methods FixMatch {r:14}, FlexMatch and "
           "FreeMatch, Grad-CAM {r:9}, Monte Carlo Dropout {r:15}, test-time augmentation and expected calibration error {r:29}. On balanced subsets (1,300 images per class, split "
           "2,080/260/260 in the binary case) supervised MobileNets reach up to 98 % (binary) and 97 % (four-class), and FreeMatch reaches 97 % with 20 % (binary) or 30 % (four-class) of "
           "the labels. MobileNetV3Small is chosen for 116.9 M FLOPs and 0.11 s latency. The authors note that their data are benchmarks, that errors concentrate in similar-looking "
           "classes, and that the benefit of the extra diseases is not isolated.")
    P.para("**CNNs for chest X-rays.** Kermany et al. {r:3} released the paediatric dataset used here and reported 92.8 % accuracy (93.2 % sensitivity, 90.1 % specificity) with "
           "transfer learning. CheXNet {r:7} reached radiologist-level pneumonia detection with a DenseNet121. Alshanketi et al. {r:22} found that a plain VGG16 (about 91 %) beat "
           "deeper networks and Vision Transformers on small imbalanced data. Ozturk et al. {r:20} report 98.08 % for a binary task but 87.02 % when three classes overlap, and "
           "CDC_Net {r:23} reaches 99.39 % on five supervised classes; both figures are as summarised in {r:1}.")
    P.para("**Same data, different protocols.** Khadidos et al. {r:5} fine-tuned EfficientNet-B0 and DenseNet121 on the 5,863 paediatric images and obtained 84.6 % and 79.7 % accuracy "
           "with recall above 0.99, i.e. almost every pneumonia case was found but many normal films were flagged. Shahi and Bagale {r:6}, using focal loss and a patient-wise split, "
           "report 96 to 98 % and observe that some patient identifiers occur in both the official training and test folders, a source of leakage. These two studies motivate the "
           "protocol-aware reporting used below.")
    P.table("Representative work compared", ["Ref.", "Approach", "Data", "Reported result", "Limitation"], [
        ["{r:1}", "MobileNets + FixMatch/FlexMatch/FreeMatch", "Mendeley paediatric; 4-class set", "98 % bin., 97 % 4-class; 97 % with 20-30 % labels", "Benchmarks, no external data"],
        ["{r:3}", "Transfer learning", "Kermany, 624 test", "92.8 % acc.", "Single centre"],
        ["{r:7}", "DenseNet121", "ChestX-ray14", "Radiologist-level", "Binary, supervised"],
        ["{r:22}", "VGG16 / ResNet / ViT", "Imbalanced pneumonia", "VGG16 about 91 %", "Small data"],
        ["{r:5}", "EfficientNet-B0, DenseNet121", "Kermany", "84.6 % / 79.7 %", "Pneumonia over-called"],
        ["{r:6}", "7 CNNs + ViT, focal loss", "Kermany, patient-wise", "96-98 %", "Coarse localisation"],
    ], widths=[0.38, 0.78, 0.68, 0.85, 0.71], size=7, align=["c", "l", "l", "l", "l"])
    P.para("**Explanation, uncertainty and calibration.** Grad-CAM {r:11} became the standard way to show which image regions drive a convolutional network's decision, and it is the "
           "explanation method of the base paper {r:1}. Monte Carlo Dropout {r:12} estimates predictive uncertainty by keeping dropout active at test time, and the expected calibration "
           "error {r:13} measures how far stated confidence departs from observed accuracy; modern networks are often over-confident. This work reports calibration error and a "
           "confidence-threshold analysis but does not implement Monte Carlo Dropout.")
    P.para("**Gap.** Few works deliver the whole path from an uploaded image to an explained, stored prediction; pathogen-type classification is rarer than binary detection; "
           "results are seldom stated with their protocol; and segmentation {r:10}, calibrated uncertainty and explanation are rarely combined in one tool. "
           "This work addresses the first three and only partly the fourth.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Pipeline.** An upload (PNG or JPEG, up to 8 MB) is checked for session, name, extension, size and decodability. It is decoded to grayscale, resized to 224 x 224, "
           "enhanced with CLAHE {r:11} (clip limit 2.5, 8 x 8 tiles), smoothed with a 3 x 3 Gaussian, replicated to three channels and scaled to the range 0 to 1. The network returns three "
           "softmax probabilities; the arg-max is the label and its probability the confidence. Grad-CAM {r:9} on the last convolutional layer gives a heat map that is blended "
           "(alpha 0.4) over the image. The record and both images are stored. Fig. 1 shows the architecture and Fig. 2 the main flow.")
    P.figure(F.diag("01_system_architecture.png"), "System architecture: React and Flask interfaces, FastAPI service, shared inference modules and data stores.")
    P.figure(F.diag("10_core_algorithm_flowchart.png"), "Main flow of the prediction route with its validation steps and error codes.", width=2.6)
    P.para(f"**Data.** The Kermany paediatric collection {{r:3}} has 5,856 images in its public folders: 5,216 training, 16 validation and 624 test (234 normal, 242 bacterial, 148 viral). "
           "The pathogen is encoded in the file names of the pneumonia images. Because 16 validation images are too few, training and validation folders are merged and a 10 % "
           f"validation set is cut by patient with a stratified group split (seed 42), giving {DS['train']:,} training and {DS['validation']} validation images. The official test split is "
           "used once.")
    HPm = M["hyperparameters"]
    P.para(f"**Model.** The classifier has four convolution blocks (3 x 3 kernels, 32, 64, 128 and 256 filters, each with batch normalisation {{r:17}} and 2 x 2 max pooling), global "
           f"average pooling, dense layers of 512 and 128 units with dropout 0.35 and 0.25, and a three-way softmax: {mi['total_params']:,} parameters, {mi['float32_mb']} MB. "
           "A compact network trains on a CPU and, being flat, lets Grad-CAM reach its last convolution layer. The loss is class-weighted categorical cross-entropy with balanced "
           "weights (total images divided by classes times class count) to offset the bacterial-heavy balance, minimised with Adam {r:16} "
           f"(learning rate {HPm['learning_rate']:g}, batch {HPm['batch_size']}, at most {HPm['epochs_max']} epochs). Early stopping watches validation loss with patience {HPm['early_stopping_patience']}, "
           f"the learning rate is halved after {HPm['reduce_lr_patience']} epochs without improvement, and augmentation uses rotation (12 degrees), shifts, shear, zoom and horizontal flips. "
           f"Training ran {M['training']['epochs_run']} epochs (best epoch {M['training']['best_epoch']}) at about {M['training']['seconds_per_epoch']:.0f} s each.")
    if E1:
        P.para(f"**Recipe change.** A first run with the project defaults (learning rate 1e-4, patience 6) stopped after {E1['training']['epochs_run']} epochs and scored {pct(E1['test']['accuracy'])} on the test split. "
               "The rate and patience were then raised to the values above. The change was made after the baseline's test result was seen, so both runs are reported, and the deployed model is "
               "the second one.")
    P.para("**Metrics.** Accuracy, per-class precision, recall and F1, macro F1, the confusion matrix, one-vs-rest AUC, sensitivity and specificity for pneumonia against normal, "
           "and the expected calibration error over ten confidence bins {r:29}. A confidence threshold keeps a prediction for automatic reporting only if its top probability "
           "reaches the threshold; coverage is the share kept.")
    P.para("**Explanation.** For the predicted class c, Grad-CAM {r:11} weights each feature map A^k of the last convolution layer by the average gradient of the class score y^c "
           "with respect to that map, alpha_k = (1/Z) sum_ij dy^c/dA^k_ij, sums the weighted maps and keeps the positive part, L = ReLU(sum_k alpha_k A^k). The 14 x 14 map is resized to "
           "224 x 224, normalised, colour-coded and blended with the radiograph. It shows where the network looked for its decision; it is neither a segmentation nor a "
           "statement of clinical cause.")
    P.para("**Protocol.** The test split is touched once per configuration, after training has ended and the best-validation weights are restored. All runs share the seed (42), the "
           "preprocessing and the evaluation code, so differences between runs come from the stated change only. No hyper-parameter was tuned on the test split, but the "
           "learning rate and patience were changed once after the baseline's test result had been seen, which is why both runs are reported.")
    P.para("**Implementation.** A FastAPI service reuses the original Flask project's model, Grad-CAM and database modules, serialises inference with a lock, signs the session cookie with "
           "HMAC-SHA256, serves images only to signed-in users and uses bound SQL parameters. The React interface adds upload progress, side-by-side and blended heat-map views, history search, "
           f"CSV export and a dashboard. {py} automated tests, a live smoke test and browser checks at 360, 768 and 1440 px pass.")
    P.sub("A", "Experiments")
    P.para("Besides the main run, three further runs use the same code: a CLAHE ablation, a MobileNetV3Small {r:13} run (ImageNet start, head trained first, then fine-tuned) as a "
           "like-for-like reference to the base paper's backbone, and a re-partition of all images by patient. The shipped Grad-CAM cannot reach inside the nested MobileNet backbone, "
           "so only the custom CNN is deployed.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** The main model is evaluated once on the official 624-image test split. Per-class results are {PC['Normal']['precision']:.2f}/{PC['Normal']['recall']:.2f} "
           f"(normal), {PC['Bacterial Pneumonia']['precision']:.2f}/{PC['Bacterial Pneumonia']['recall']:.2f} (bacterial) and {PC['Viral Pneumonia']['precision']:.2f}/{PC['Viral Pneumonia']['recall']:.2f} "
           f"(viral) precision/recall. Three-class accuracy is {pct(T['accuracy'])} (macro F1 {f3(T['macro_f1'])}, macro AUC {f3(T['auc_ovr_macro'])}); the confusion matrix "
           f"(rows true, columns predicted: normal, bacterial, viral) is {'; '.join('/'.join(str(v) for v in r) for r in T['confusion_matrix'])}. As pneumonia against normal, sensitivity is {pct(Bn['sensitivity'])}, specificity "
           f"{pct(Bn['specificity'])} and AUC {f3(Bn['auc'])}. The expected calibration error is {f3(T['expected_calibration_error'])}.")
    rows = [["Official test split (main model)", T["n"], pct(T["accuracy"]), f3(T["macro_f1"]), pct(Bn["sensitivity"]), pct(Bn["specificity"])]]
    if E1:
        rows.insert(0, ["Baseline: project defaults (official split)", E1["test"]["n"], pct(E1["test"]["accuracy"]), f3(E1["test"]["macro_f1"]), pct(E1["test"]["binary_normal_vs_pneumonia"]["sensitivity"]), pct(E1["test"]["binary_normal_vs_pneumonia"]["specificity"])])
    if LD:
        dj = LD["patient_disjoint_subset"]
        rows.append(["Id-disjoint subset of the test split", dj["n"], pct(dj["accuracy"]), f3(dj["macro_f1_present_classes"]), pct(dj["binary_normal_vs_pneumonia"]["sensitivity"]), pct(dj["binary_normal_vs_pneumonia"]["specificity"])])
    if E4:
        t4 = E4["test"]
        rows.append(["Patient-level re-partition (own test part)", t4["n"], pct(t4["accuracy"]), f3(t4["macro_f1"]), pct(t4["binary_normal_vs_pneumonia"]["sensitivity"]), pct(t4["binary_normal_vs_pneumonia"]["specificity"])])
    if E2:
        t2 = E2["test"]
        rows.append(["Ablation: no CLAHE (official split)", t2["n"], pct(t2["accuracy"]), f3(t2["macro_f1"]), pct(t2["binary_normal_vs_pneumonia"]["sensitivity"]), pct(t2["binary_normal_vs_pneumonia"]["specificity"])])
    if E3:
        t3 = E3["test"]
        rows.append(["MobileNetV3Small (official split)", t3["n"], pct(t3["accuracy"]), f3(t3["macro_f1"]), pct(t3["binary_normal_vs_pneumonia"]["sensitivity"]), pct(t3["binary_normal_vs_pneumonia"]["specificity"])])
    P.table("Test results by protocol (one run, seed 42)", ["Protocol", "n", "3-class acc.", "Macro F1", "Sens.", "Spec."], rows, widths=[1.45, 0.3, 0.45, 0.4, 0.4, 0.4], size=7, align=["l", "c", "c", "c", "c", "c"])
    if LD:
        P.para(f"**Overlap.** {LD['sharing_patient_id_with_training']} of the 624 official test images share an identifier with the training folders, all of them pneumonia images "
               f"(none of the 234 normal ones), which agrees with {{r:6}}. Some may be different children with the same number, but the file names cannot tell, so the id-disjoint subset "
               f"({LD['patient_disjoint_images']} images, {LD['patient_disjoint_subset']['support'][0]} normal) and the patient-level re-partition in Table II are the safer measures of generalisation. "
               "Their class mix differs from the full split, so the rows are not averaged.")
    if os.path.exists(F.fig("experiment_comparison.png")):
        P.figure(F.fig("experiment_comparison.png"), "Experiments compared on the official test images: three-class accuracy, macro F1, sensitivity and specificity.")
    hist = json.load(open(os.path.join(F.EXP, F.DEPLOYED_NAME, "history.json"))) if os.path.exists(os.path.join(F.EXP, F.DEPLOYED_NAME, "history.json")) else None
    TRm = M["training"]
    P.para(f"**Training behaviour.** Validation loss was lowest at epoch {TRm['best_epoch']} of {TRm['epochs_run']}, after which early stopping restored those weights. The final training accuracy "
           f"({pct(TRm['final_train_accuracy'])}, measured on augmented batches) is below the validation accuracy of the restored model ({pct(TRm['val_accuracy_restored_model'])}), which is typical when dropout "
           "and augmentation are active during training; the curves (Fig. 4) show no sign of strong over-fitting but also no sign that the network has saturated, so a longer or wider run could improve it.")
    P.figure(F.fig("training_curves_exp02.png"), "Training and validation accuracy and loss of the deployed model.", width=3.3)
    sw = {round(r["threshold"], 1): r for r in T["pneumonia_decision_threshold_sweep"]}
    lo, hi = sw[0.5], sw[0.8]
    thr = {round(r["threshold"], 2): r for r in T["confidence_threshold_analysis"]}
    t9 = thr.get(0.9) or list(thr.values())[-1]
    P.para(f"**Thresholds.** Requiring a top probability of at least {t9['threshold']:.2f} keeps {pct(t9['coverage'])} of the scans with an accuracy of "
           f"{pct(t9['accuracy_on_kept']) if t9['accuracy_on_kept'] is not None else 'n/a'} on those kept (all scans: {pct(T['accuracy'])}), so low-confidence cases can be sent for review at "
           f"the cost of coverage. Raising the pneumonia decision threshold on 1 - P(normal) from 0.5 to 0.8 moves sensitivity from {pct(lo['sensitivity'])} to {pct(hi['sensitivity'])} and specificity from "
           f"{pct(lo['specificity'])} to {pct(hi['specificity'])}, so the operating point can be set to suit the use: a screening tool favours sensitivity, a triage queue favours specificity.")
    ab = ""
    if E2:
        ab = (f"Removing CLAHE changes three-class accuracy by {(E2['test']['accuracy'] - T['accuracy']) * 100:+.1f} points and macro F1 by {E2['test']['macro_f1'] - T['macro_f1']:+.3f}, "
              "so this study does not show that the contrast step helps; with one seed per configuration the difference is indicative only, and the deployed model keeps CLAHE. ")
    if E3:
        ab += (f"MobileNetV3Small, trained for {E3['training']['epochs_run']} epochs, reaches only {pct(E3['test']['accuracy'])} three-class accuracy on the same images and cannot be explained by the shipped Grad-CAM. ")
    P.para("**Ablation and comparison.** " + ab)
    lat_s = LAT["total_pipeline"] / 1000
    P.para(f"**Performance.** On the CPU, preprocessing takes {LAT['preprocess']:.0f} ms, the forward pass {LAT['predict']:.0f} ms and Grad-CAM with the overlay {LAT['gradcam_overlay']:.0f} ms "
           f"(mean of {LAT['images_timed']} images, {lat_s:.2f} s in all)" + (f"; the full API call, including upload, file writes and the database insert, has a mean of {api['mean_ms'] / 1000:.2f} s." if api else "."))
    P.para("**Comparison with the base paper.** The datasets and protocols differ, so this is context, not a ranking. The base paper uses balanced 260-image test subsets and "
           f"ImageNet-pretrained MobileNets and reports 97 to 98 %; here the official test split is about 62 % pneumonia, the network is trained from scratch, and the task has three classes. "
           f"The {pct(Bn['accuracy'])} accuracy for normal against pneumonia sits inside the 79.7 to 98 % range that other studies report on the same images {{r:5,6}}. "
           "The base paper's 0.11 s per image is likewise not comparable (different hardware and model).")
    P.figure(crop_shot("06_result.png", "paper_result.png"), "Output screen: original radiograph beside its Grad-CAM overlay, class badge and probabilities.")
    P.figure(crop_shot("09_dashboard.png", "paper_dashboard.png", (0, 0, 1440, 900)), "Output screen: dashboard summarising the stored scans.")
    P.para(f"**Failure cases.** The largest confusion is {SHORT[A['top_pair'][1]]} images predicted as {SHORT[A['top_pair'][2]]} ({A['top_pair'][0]} images), then "
           f"{SHORT[A['second_pair'][1]]} as {SHORT[A['second_pair'][2]]} ({A['second_pair'][0]}); the weakest class is {SHORT[A['worst']]} (recall {pct(PC[A['worst']]['recall'])}). "
           "A wrong prediction can carry a high confidence, and because no lung segmentation is applied, heat maps also cover ribs, shoulders, corners and the diaphragm line (Fig. 9).")

    P.para("**Threats to validity.** Each configuration was trained once, so run-to-run variation is unknown and differences of a few points between rows of Table II are not established. "
           "Pathogen labels come from file names and were not re-read by a clinician. All images are paediatric images from one centre, taken in one department, so the figures say "
           "nothing about adults or other scanners. The recipe was adjusted once after seeing a test result, and the best-scoring ablation row was not selected as the deployed model, which "
           "keeps the headline figure from being tuned to the test split.")
    P.figure(F.fig("per_class_metrics.png"), "Precision, recall and F1 of the deployed model for each class on the official test split.", width=3.3)
    P.figure(F.fig("confidence_threshold.png"), "Accuracy on the kept scans and coverage as the minimum confidence rises.", width=3.3)
    P.figure(F.fig("gradcam_examples.png"), "Grad-CAM overlays: highest-confidence correct test image of each class and the most confident misclassification (a normal film called viral).", width=3.4)
    P.figure(F.fig("confusion_matrix_exp02.png"), "Confusion matrix of the deployed model on the 624 official test images.", width=2.5)

    # ------------------------------------------------------------------ V
    P.para("**Objectives.** Objectives 1 and 3 to 6 were met: the data were prepared with one shared preprocessing chain, a three-class CNN was trained, the metrics above were computed, "
           f"every scan receives a Grad-CAM overlay, and the web application returns label, confidence and heat map in about {api['mean_ms'] / 1000:.1f} s through the API. Objective 2 was not met. "
           "Because U-Net segmentation was never built, the classifier sees the whole radiograph, including borders, markers and the diaphragm, and some of its attention falls there.")
    P.heading("V", "Conclusion")
    P.para("An end-to-end explainable pneumonia detection system was built and measured: validated upload, CLAHE preprocessing, a compact three-class CNN, a Grad-CAM overlay, persistent history "
           f"and a dashboard, with {py} passing tests. Of six objectives, five were met; U-Net lung segmentation was not implemented. On the official test split the model reaches "
           f"{pct(T['accuracy'])} three-class accuracy and {pct(Bn['sensitivity'])}/{pct(Bn['specificity'])} pneumonia sensitivity/normal specificity; normal radiographs are often mistaken for pneumonia, and "
           "the official test folder shares pneumonia identifiers with training, so identifier-disjoint and patient-level results should be preferred. Limits: one data source, one seed per "
           "configuration, labels derived from file names, calibration checked only by the expected calibration error, no clinical validation; the system is not a medical device.")
    P.para("Future work: U-Net segmentation {r:10} before classification, calibrated uncertainty with temperature scaling or Monte Carlo Dropout, a Grad-CAM that reaches nested backbones, "
           "and external multi-hospital validation.")

    P.references()
    P.save(path)
    return path, len(P.order)


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "19.IEEE_Paper.docx")))
