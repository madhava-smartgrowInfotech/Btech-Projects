"""Chapter 6: Methodology and Software Implementation.

methodology_blocks() feeds document 9 (and the first half of chapter 6); application_blocks() feeds document 12 (and the second half).
Every measured number is read from facts.py (experiments/**/metrics.json); nothing measured is typed in by hand.
"""

import re

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def c(*keys):
    return "[" + ", ".join(str(R[k]) for k in keys) + "]"


def _txt(blk):
    k = blk[0]
    if k in ("p", "eq", "h1", "h2", "h3", "code"):
        return blk[1]
    if k == "fig":
        return blk[2]
    if k == "tab":
        return blk[1]
    if k in ("b", "n"):
        return " ".join(blk[1])
    return ""


def _drop(b, *needles):
    """Report mode only: remove blocks whose text contains one of the needles (each must match something)."""
    out = list(b)
    for n in needles:
        hit = [x for x in out if n in _txt(x)]
        assert hit, f"ch6 trim needle not found: {n}"
        out = [x for x in out if n not in _txt(x)]
    return out


def _renumber_h3(b):
    out, sec, k = [], None, 0
    for x in b:
        if x[0] == "h2":
            sec, k = re.match(r"(\d+\.\d+)", x[1]).group(1), 0
        elif x[0] == "h3" and sec:
            k += 1
            x = ("h3", f"{sec}.{k} " + re.sub(r"^\d+\.\d+\.\d+\s+", "", x[1]))
        out.append(x)
    return out


def methodology_blocks():
    X = F.COMP["XGBoost (shipped config)"]
    LR = F.COMP["Logistic regression"]
    ab = F.ABL
    cal = F.CAL
    t85, t70 = F.thr_row(0.85), F.thr_row(0.7)
    p10, p30 = F.rob_row(0.1), F.rob_row(0.3)
    b = []

    # ---------------------------------------------------------------- 6.1
    b += [H2("6.1 Overall methodology"),
          P("ATHENA was built in eight stages, each producing a file or a measurement that the next stage uses. The stages are the same for the documents and for the code, so "
            "every claim in this report can be traced to a script."),
          TAB("Stages of the methodology", ["Stage", "What is done", "Output"], [
              ["1 Problem framing", "read the batch objectives and the base paper; decide the target (five-level priority) and the inputs (report + vitals)", "36-input fused record, priority 1 to 5"],
              ["2 Data", "generate a seeded synthetic dataset of 6,000 patients (no real records were available)", "`data/sample/triage_synthetic.csv`"],
              ["3 Report reading", "PDF text layer or local OCR, then a clinical lexicon with negation and lab limits", "28 report flags with page numbers"],
              ["4 Fusion", "append the eight vitals to the flags in a fixed column order", "one record per patient"],
              ["5 Model", "train XGBoost, calibrate its probabilities with isotonic regression on a separate split", "`models/triage_model.joblib`"],
              ["6 Explanation", "SHAP tree attribution for the chosen priority, strongest first", "per-patient factor list"],
              ["7 Serving", "FastAPI services, SQLite storage, React screens, clinician accept-or-change loop", "running application"],
              ["8 Evaluation", "hold-out metrics, model comparison, ablation, calibration, robustness, reader stress test, tests and timing", "`experiments/**/metrics.json`"],
          ], widths=[1.3, 3.7, 1.5], size=9.3, align=["l", "l", "l"]),
          FIG(F.diag("02_high_level_workflow.png"), "Overall workflow of ATHENA from a scanned report and vitals to a clinician-approved priority.", 5.4),
          P("The methodology follows the base paper in three respects: several algorithms are compared on the same split before one is chosen, a probability (not only a label) is "
            f"reported together with a confidence threshold analysis, and a symptom that is not documented is treated as absent without imputation {c('base')}. It departs from the base paper "
            "in the input (a scanned report fused with vitals instead of a typed symptom checklist), in the target (five triage priorities instead of ICD-10 diagnoses) and in the data "
            "(synthetic, where the base paper uses real clinical records)."),
          ]

    # ---------------------------------------------------------------- 6.2
    ps = F.PRIO_SHARE
    b += [H2("6.2 Dataset"),
          H3("6.2.1 Why the data is synthetic"),
          P("The batch plan named a public Kaggle dataset of hospital triage and patient history records. Accessing it needs a personal Kaggle token and its licence is not stated, so it was not "
            "used; the download script `scripts/download_data.py` exists but was never run or tested. The model is therefore trained on a seeded synthetic dataset, and **every accuracy "
            "figure in this report is measured on that synthetic data**. It measures how well the model recovers a known rule, not how well it agrees with clinicians."),
          H3("6.2.2 How the dataset is generated"),
          P(f"`ml/make_data.py` (seed {F.SEED}) simulates {F.ROWS:,} patients. For each patient an archetype is drawn, then age, vitals, report flags and the arrival mode are sampled from "
            "that archetype, a severity score is computed from clinical rules, Gaussian noise is added, and the score is cut into a priority. The priority plays the role of the "
            "clinician-recorded outcome."),
          TAB("Clinical archetypes (shares are measured on the generated data)", ["Archetype", "Share", "Report flags and their probability", "Vital shifts (HR, SBP, SpO2, T, RR)"], [
              ["minor", F.pct(F.ARCH_SHARE["minor"]), "fever .12, trauma .12, hypertension .15, vomiting .08, abdominal pain .08, diabetes .08", "none"],
              ["cardiac", F.pct(F.ARCH_SHARE["cardiac"]), "chest pain .80, dyspnoea .35, ST elevation .22, troponin raised .35, cardiac history .50, hypertension .50", "+8, +5, -1, 0, +2"],
              ["respiratory", F.pct(F.ARCH_SHARE["respiratory"]), "dyspnoea .90, fever .40, infiltrate .40, COPD .50, WBC raised .30", "+10, 0, -5, +0.5, +7"],
              ["neuro", F.pct(F.ARCH_SHARE["neuro"]), "stroke signs .50, headache .45, altered mental state .35, haemorrhage on CT .12, hypertension .60", "0, +22, -1, 0, +1"],
              ["trauma", F.pct(F.ARCH_SHARE["trauma"]), "trauma .95, fracture .45, bleeding .35, Hb low .12, free fluid .08", "+12, -6, -1, 0, +3"],
              ["infection", F.pct(F.ARCH_SHARE["infection"]), "fever .85, WBC raised .65, lactate raised .22, altered mental state .15, diabetes .25", "+18, -12, -2, +1.4, +5"],
              ["abdominal", F.pct(F.ARCH_SHARE["abdominal"]), "abdominal pain .95, vomiting .55, WBC raised .30, fever .20, free fluid .12", "+8, -3, 0, +0.3, +2"],
          ], widths=[0.9, 0.6, 3.6, 1.4], size=8.8, align=["l", "c", "l", "l"]),
          P("Vitals are drawn from normal distributions and clipped to physical limits: age from a gamma distribution (shape 4.2, scale 11, plus 3, clipped to 1-98), heart rate "
            "N(82 + shift, 14), systolic pressure N(124 + shift + 0.25 (age - 45), 17), SpO2 N(97.5 + shift, 2), temperature N(36.8 + shift, 0.5), respiratory rate N(16 + shift, 3), and "
            "diastolic pressure 0.62 times systolic plus N(0, 7). The arrival mode is walk-in, ambulance or transfer with probabilities .55 / .35 / .10 for minor and abdominal "
            "patients and .25 / .60 / .15 for the others. A flag that an archetype does not list has probability .01 (.02 for the six lab flags, .06 for hypertension and diabetes)."),
          H3("6.2.3 The severity rule and the labels"),
          P("The severity score s is the sum of the terms below plus a weight for each report flag that is present; noise from N(0, 0.4) is added, and s is cut into priorities."),
          TAB("Severity score terms", ["Term", "Contribution to s"], [
              ["Heart rate", "+2 above 130; +1 above 110; +1.5 below 45"],
              ["Systolic pressure", "+3 below 90; +1.5 below 100; +1 above 180"],
              ["SpO2", "+3.5 below 90; +1.5 below 94"],
              ["Temperature", "+1.5 above 39.5 or below 35; +0.7 above 38.3"],
              ["Respiratory rate", "+2 above 28; +1 above 22"],
              ["Age and arrival", "+0.8 above 75; transfer +0.5; ambulance +0.8"],
              ["Report flags (weight each)", "ST elevation 4, haemorrhage on CT 4, focal weakness 3, altered mental state 2.5, troponin raised 2.5, lactate raised 2.5, free fluid 2, "
                                              "dyspnoea 1.5, syncope 1.5, bleeding 1.5, chest pain 1.2, trauma 1, infiltrate 1, glucose abnormal 1, Hb low 1, fracture 0.8, severe headache 0.8, creatinine raised 0.8, "
                                              "WBC raised 0.7, abdominal pain 0.6, cardiac history 0.5, anticoagulant 0.5, COPD 0.4, fever 0.4, diabetes 0.3, prior stroke 0.3, "
                                              "hypertension 0.2, vomiting 0.2"],
          ], widths=[1.7, 4.8], size=9.2, align=["l", "l"]),
          EQ("priority = 1 if s ≥ 8;   2 if 5.2 ≤ s < 8;   3 if 3.0 ≤ s < 5.2;   4 if 1.2 ≤ s < 3.0;   5 otherwise"),
          P(f"The generated priorities are {F.pct(ps[0])} / {F.pct(ps[1])} / {F.pct(ps[2])} / {F.pct(ps[3])} / {F.pct(ps[4])} for priorities 1 to 5. The label noise has a consequence that "
            f"matters when the results are read: a model that knew the exact severity score would still disagree with the stored label on {F.pct(1 - F.CEILING, 1)} of the rows, so exact accuracy cannot "
            f"exceed about {F.pct(F.CEILING, 1)} on this data (Chapter 8)."),
          FIG(F.fig("f11_priority_distribution.png"), "Distribution of priorities and archetypes in the synthetic dataset.", 5.2),
          H3("6.2.4 Splits and sample reports"),
          P(f"The data is split with stratification on the priority: 80% training pool and 20% test ({F.N_TEST:,} cases), then the training pool is split 80/20 into {F.N_TRAIN:,} rows for fitting the "
            f"model and {F.N_CAL:,} rows for fitting the calibrator. The test cases are never used for fitting or calibration. Twelve sample reports (eight two-page PDFs and four PNG scans, "
            "`scripts/make_sample_reports.py`) were generated with the same seed and are stored with the flags and vitals a correct reading must find; they are used for the demonstration and to "
            "test the reader, and they are written in the vocabulary of the lexicon, which makes them an easy test."),
          ]

    # ---------------------------------------------------------------- 6.3
    b += [H2("6.3 Preprocessing and fusion"),
          H3("6.3.1 Reading the report"),
          P("A PDF page is read with its text layer (`pypdf`); a page with fewer than 20 characters is treated as a scan and its first embedded image is sent to OCR. An image upload is sent to "
            f"OCR directly. The OCR engine is RapidOCR, which runs PaddleOCR-family text detection and recognition models on ONNX Runtime {c('ppocr')}: it is installed as one Python package, "
            "needs no separate download and no network. Images with a longer side under 2,000 pixels are enlarged by 1.6, and the recognised boxes are sorted into lines and then left to right. "
            "Lines that were wrapped mid-sentence (45 characters or more and no closing punctuation) are re-joined, and the text is split into sentences."),
          TAB("The report lexicon: 22 text flags in three groups", ["Group", "Flags (examples of phrases matched)"], [
              ["Symptoms (11)", "chest pain (chest pressure, tightness, angina); shortness of breath (dyspnoea, breathless, SOB); altered mental state (confusion, drowsy, lethargic, unresponsive); "
                                "syncope (collapsed, passed out); fever (febrile, chills, rigors); abdominal pain; bleeding (haematemesis, melaena, haematuria); stroke signs (facial droop, slurred speech, "
                                "one-sided weakness); severe headache (worst, sudden, thunderclap); vomiting; trauma (fall from, road traffic, laceration, head injury)"],
              ["Findings (5)", "ST elevation (STEMI); lung infiltrate (consolidation, pneumonia, effusion); fracture; free abdominal fluid; intracranial haemorrhage (subdural, subarachnoid)"],
              ["History (6)", "diabetes (T2DM, DM2); hypertension (HTN); cardiac disease (CAD, prior MI, heart failure, atrial fibrillation, stent, CABG); COPD or asthma; prior stroke (TIA); "
                              "anticoagulant (warfarin, apixaban, clopidogrel, heparin)"],
          ], widths=[1.2, 5.3], size=9, align=["l", "l"]),
          P("Each sentence is tested against all 22 expressions. Two rules reduce false matches. A match is discarded when a negation word (*no, denies, denied, without, negative for, absence of, not, nil, free of, "
            "ruled out*) occurs within 45 characters before it in the same sentence, so \"denies chest pain\" produces nothing. A bleed described as intracranial, subarachnoid, cerebral or subdural "
            "is recorded as the finding *haemorrhage on CT* and not as the symptom *bleeding*. Spaces inside phrases match zero or more white-space characters because OCR often drops them "
            "(\"shortnessofbreath\"). Every item keeps the page it came from."),
          TAB("Lab values read from the report", ["Lab", "Abnormal when", "Unit"], [
              ["Troponin", "above 0.04", "ng/mL"], ["Lactate", "above 2.0", "mmol/L"], ["White cell count", "above 11.0", "x10^9/L"],
              ["Glucose", "below 70 or above 250", "mg/dL"], ["Creatinine", "above 1.3", "mg/dL"], ["Haemoglobin", "below 10.0", "g/dL"],
          ], widths=[2.0, 2.6, 1.6], size=9.5, align=["l", "l", "l"]),
          P("A lab is recognised by its name followed by a number; repeated readings of the same lab on the same page are listed once, and an abnormal value sets the lab flag. "
            "The result of reading is the 28 flags (22 text flags and 6 lab flags) together with the list of items, labs and pages shown to the nurse."),
          H3("6.3.2 Fusion with the vitals"),
          P("The fused record is a vector of 36 numbers in a fixed order that `features.py` defines for training, serving and the tests: age, heart rate, systolic pressure, diastolic "
            "pressure, SpO2, temperature, respiratory rate and the arrival code (walk-in 0, transfer 1, ambulance 2), followed by the 28 flags, each 0 or 1. A flag the report does not "
            "mention is 0; there is no imputation, as in the base paper. Vitals are validated on entry (age 0-120, heart rate 20-250, systolic 40-300, diastolic 20-200, SpO2 50-100, "
            "temperature 30-44 degrees Celsius, respiratory rate 4-70). Tree models are invariant to monotone rescaling, so the vitals are used unscaled."),
          ]

    # ---------------------------------------------------------------- 6.4
    b += [H2("6.4 Algorithm choice and justification"),
          P(f"Eight classifiers were trained on the same {F.N_TRAIN:,} fitting rows and scored on the same {F.N_TEST:,} test cases (all on the synthetic data), in the spirit of the base paper's "
            f"comparison of 19 algorithms {c('base')}. The shipped model is XGBoost with isotonic calibration; the table gives the uncalibrated XGBoost so that the comparison is like for like."),
          TAB("Eight models on the same split (synthetic hold-out)", ["Model", "Accuracy", "Within one", "Macro F1", "QWK", "Top-2"],
              [[k, F.pct(v["accuracy"]), F.pct(v["within_one"]), F.f3(v["macro_f1"]), F.f3(v["qwk"]), F.pct(v["top2"])] for k, v in F.COMP.items()],
              widths=[2.3, 0.9, 0.9, 0.9, 0.7, 0.8], size=9.3, align=["l", "c", "c", "c", "c", "c"]),
          FIG(F.fig("f03_model_comparison.png"), "Accuracy and macro F1 of the eight models on the synthetic hold-out.", 5.2),
          P(f"The result does not favour the shipped model. Logistic regression is the most accurate ({F.pct(LR['accuracy'])}) and XGBoost sits in the middle ({F.pct(X['accuracy'])}); "
            f"five-fold cross-validation on all {F.ROWS:,} rows gives {F.pct(F.CV5['Logistic regression']['mean'])} for logistic regression, {F.pct(F.CV5['Random forest']['mean'])} for the random forest "
            f"and {F.pct(F.CV5['XGBoost (shipped config)']['mean'])} for XGBoost, with standard deviations of one to two points, so the three are close. The reason is in the data: the labels come from an "
            "additive severity score, which a linear model recovers almost exactly. The single decision tree (depth 8) and k-nearest neighbours are clearly worse."),
          P("XGBoost was kept for four reasons, and only the first three are supported by this study. (1) It gives probabilities that can be calibrated and used as a confidence. (2) SHAP's tree "
            f"explainer computes exact attributions for it in milliseconds {c('treeshap')}. (3) It handles the 0/1 flags and the numeric vitals without scaling. (4) On real tabular data "
            f"tree ensembles usually keep an edge over linear and neural models {c('grinsztajn')}; this is an **assumption** carried over from the literature, not something this study showed, and with real "
            "records the choice should be repeated."),
          TAB("Value of fusing the two sources (XGBoost, same split)", ["Inputs", "Count", "Accuracy", "Within one", "Macro F1", "Top-2"],
              [[k, str(v["inputs"]), F.pct(v["accuracy"]), F.pct(v["within_one"]), F.f3(v["macro_f1"]), F.pct(v["top2"])] for k, v in ab.items()],
              widths=[2.3, 0.7, 0.9, 0.9, 0.9, 0.8], size=9.3, align=["l", "c", "c", "c", "c", "c"]),
          P(f"The ablation measures the gap named in the literature survey. Vitals alone reach {F.pct(ab['Vitals only (8)']['accuracy'])}, the report alone {F.pct(ab['Report only (28)']['accuracy'])} and the fused record "
            f"{F.pct(ab['Fused (36)']['accuracy'])}: fusion adds {(ab['Fused (36)']['accuracy'] - ab['Vitals only (8)']['accuracy']) * 100:.1f} points over vitals alone and "
            f"{(ab['Fused (36)']['accuracy'] - ab['Report only (28)']['accuracy']) * 100:.1f} over the report alone. Because the synthetic severity rule puts large weights on report flags, the size of the "
            "gain is partly a property of the generator, but its direction is what the design assumed."),
          P("Two components named in the batch abstract were not built. BioBERT would replace the lexicon with a learned reader " + c('biobert') + "; it needs labelled clinical text that was "
            "not available and a GPU-class model on a CPU-only workstation. Retrieval-augmented generation and a multi-agent orchestration (the companion paper " + c('cheng') + ") were left as future work."),
          ]

    # ---------------------------------------------------------------- 6.5
    b += [H2("6.5 Mathematical formulation"),
          P("Let x in R^36 be the fused record and K = 5 the number of priorities. XGBoost builds an additive model of regression trees, one score per class:"),
          EQ("F(x, k) = Σ f(t, k; x) over t = 1 … 220,      p(k | x) = exp F(x, k) / Σ exp F(x, j) over j = 1 … 5"),
          P("Each tree f(t, k) is a function of depth at most 4 that is fitted greedily to the gradient of the multi-class log loss, with learning rate 0.1, row sampling 0.9 and column sampling 0.9 "
            f"{c('xgboost')}. The softmax gives raw probabilities p(k | x), which are usually too confident or not confident enough. Calibration learns, for every class, a non-decreasing function g(k) "
            f"on a separate split by isotonic regression {c('zadrozny')}, and the calibrated probabilities are renormalised:"),
          EQ("g(k) = non-decreasing map that minimises Σ [ 1(y = k) − g(p(k | x)) ]² over the calibration rows;     q(k | x) = g(p(k | x)) / Σ g(p(j | x)) over j"),
          P("The priority, the confidence and the risk level follow directly:"),
          EQ("priority(x) = 1 + argmax over k of q(k | x);     confidence(x) = max over k of q(k | x);     risk = High if priority ≤ 2, Moderate if priority = 3, Low otherwise"),
          P(f"The explanation is a Shapley attribution {c('shap', 'treeshap')}. For the chosen class k, the score F(x, k) is decomposed into a base value and one contribution per input, "
            "and the contributions are listed in descending absolute value:"),
          EQ("F(x, k) = φ0 + Σ φi over i = 1 … 36,      φi = Σ over S ⊆ N∖{i} of  [ |S|! (36 − |S| − 1)! / 36! ] · [ F(S ∪ {i}, k) − F(S, k) ]"),
          P("A positive φi raises the score of the chosen priority and a negative one lowers it (the API words this as raises or lowers urgency, which reads the wrong way round when the chosen priority is 4 or 5; see Chapter 7). The explainer attributes the uncalibrated tree scores, so the bars explain the model's raw "
            "preference for a priority, while the confidence shown beside them is the calibrated probability. The metrics used in Chapter 8 are defined as follows, with n test cases, "
            "true priority y_i and predicted priority a_i:"),
          EQ("accuracy = (1/n) Σ 1(a = y);     within-one = (1/n) Σ 1(|a − y| ≤ 1);     macro-F1 = (1/5) Σ F1(k) over k = 1 … 5"),
          EQ("QWK = 1 − Σ w(i,j) O(i,j) / Σ w(i,j) E(i,j),   w(i,j) = (i − j)² / 16;     ECE = Σ ( |Bm| / n ) · | acc(Bm) − conf(Bm) | over bins m"),
          P("The quadratic weighted kappa (QWK) compares the observed confusion matrix O with the matrix E expected by chance and penalises a miss by the square of its distance, which suits an "
            "ordinal scale; the expected calibration error (ECE) groups predictions into ten confidence bins Bm and measures the gap between confidence and accuracy " + c('guo') + "."),
          ]

    # ---------------------------------------------------------------- 6.6
    b += [H2("6.6 Model architecture and training configuration"),
          FIG(F.diag("12_model_architecture.png"), "Architecture of the triage model: fused record, XGBoost, isotonic calibration, arg-max, SHAP.", 5.4),
          TAB("Training configuration (`ml/train.py`)", ["Item", "Value"], [
              ["Inputs / classes", "36 / 5 (priorities 1 to 5)"],
              ["Rows: fit / calibration / test", f"{F.N_TRAIN:,} / {F.N_CAL:,} / {F.N_TEST:,} (stratified, seed {F.SEED})"],
              ["Classifier", "XGBClassifier, objective multi:softprob, eval metric mlogloss"],
              ["Trees / depth / learning rate", "220 / 4 / 0.1"],
              ["Row and column sampling", "0.9 and 0.9"],
              ["Calibration", "CalibratedClassifierCV(FrozenEstimator(base), method=\"isotonic\") fitted on the calibration split"],
              ["Explainer", "shap.TreeExplainer on the base trees"],
              ["Training time (CPU)", f"{F.TRAIN_SEC:.2f} s"],
              ["Model time per patient", f"about {F.MODEL_SEC * 1000:.3f} ms in a batch of {F.N_TEST:,}; {F.lat('create_patient'):.1f} ms median for the whole POST /patients request including SHAP"],
              ["Hardware", F.MACHINE],
              ["Libraries", "scikit-learn, XGBoost, SHAP, pandas, NumPy (Python 3.11)"],
          ], widths=[2.2, 4.3], size=9.3, align=["l", "l"]),
          P("No hyper-parameter search was run: the configuration is the first reasonable setting, as the dataset is small and the labels are noisy. The base paper tuned each of its 19 models with "
            f"{F.BASE_PAPER_RESULTS['trials']} Optuna trials {c('base')}; doing the same here is listed as future work."),
          H3("6.6.1 Shipped model on the synthetic hold-out"),
          P(f"On the {F.N_TEST:,} held-out synthetic cases the shipped model reaches an accuracy of {F.pct(F.ACC, 2)}, a within-one accuracy of {F.pct(F.W1, 2)}, a macro F1 of {F.f3(F.MF1)}, a quadratic "
            f"weighted kappa of {F.f3(F.QWK)} and a top-2 accuracy of {F.pct(F.TOP2, 1)}. Recall for priorities 1 to 5 is " + " / ".join(F.pct(r, 0) for r in F.REC) +
            ". Almost every error is a neighbouring priority, and the sickest class is the hardest. The full results, with the confusion matrix, are in Chapter 8."),
          H3("6.6.2 Calibration and confidence"),
          P(f"Isotonic calibration lowers the expected calibration error from {F.f4(cal['ece_uncalibrated'])} to {F.f4(cal['ece_isotonic'])} and the multi-class Brier score from {F.f4(cal['brier_uncalibrated'])} to "
            f"{F.f4(cal['brier_isotonic'])}: a modest gain. The mean confidence rises from {F.f3(cal['mean_confidence_uncalibrated'])} to {F.f3(cal['mean_confidence_isotonic'])}, close to the accuracy of {F.pct(F.ACC)}. "
            f"Confidence is informative: predictions with a confidence of at least 0.70 cover {F.pct(t70['coverage'])} of cases and are right {F.pct(t70['accuracy'])} of the time, and at 0.85 "
            f"(the threshold the base paper uses {c('base')}) they cover {F.pct(t85['coverage'])} of cases at {F.pct(t85['accuracy'])} accuracy. The product shows the confidence to the clinician; it does not yet "
            "use a threshold to route cases."),
          H3("6.6.3 Handling a report that is read badly"),
          P(f"A reading error reaches the model as a missing flag. To measure the cost, each positive flag was removed at random with a given probability before scoring the test set. Accuracy falls from "
            f"{F.pct(F.ACC)} to {F.pct(p10['accuracy'])} at 10% dropped and {F.pct(p30['accuracy'])} at 30% dropped, and to {F.pct(F.rob_row(1.0)['accuracy'])} with no report at all; within-one accuracy is still "
            f"{F.pct(p30['within_one'], 0)} at 30% lost. The reader's recall on the hand-written stress set ({F.pct(F.STRESS['recall'])}) therefore puts the system in the region where one report finding "
            "in six is missed, which the evaluation chapter reports as a limitation."),
          H3("6.6.4 Stability of the estimates"),
          P(f"The shipped split (seed {F.SEED}) is a slightly unlucky one: with five other split seeds the same recipe gives a mean accuracy of {F.pct(F.SEEDS['accuracy_mean'])} with a standard deviation of "
            f"{F.pct(F.SEEDS['accuracy_std'])} and a mean macro F1 of {F.f3(F.SEEDS['macro_f1_mean'])}, against {F.pct(F.ACC)} and {F.f3(F.MF1)} for the shipped split. The headline figures in the product "
            "are those of the shipped split, and this report quotes them as they are."),
          ]
    if F.REPORT:
        b = _drop(b, "Overall workflow of ATHENA from a scanned report")
        b = _renumber_h3(b)
    return b


def application_blocks():
    b = []
    # ---------------------------------------------------------------- 6.7
    b += [H2("6.7 Application architecture"),
          P(f"ATHENA is two processes behind a browser. The browser tier is a React 19 single-page application built with Vite on port {F.WEB_PORT}; its API client (`lib/api.js`) adds the bearer "
            "token to every request and turns failures into a typed error with the server's message. The application tier is a FastAPI application (`backend/app/main.py`) served by "
            f"Uvicorn on port {F.API_PORT}. At start-up it creates the tables, runs one prediction to warm the model and the SHAP explainer (the first call is otherwise noticeably slow), loads the "
            "OCR engine in a background thread, seeds the two demo users and, if the patients table is empty, twelve labelled sample cases."),
          TAB("Modules and their responsibilities", ["Module", "Responsibility"], [
              ["backend/app/main.py", "application factory, start-up warm-up, user and sample-queue seeding, CORS for the two local origins"],
              ["backend/app/routes/api.py", "all 13 routes, request schemas, patient serialisation, queue ordering, override rules, metrics aggregation"],
              ["backend/app/db.py", "SQLAlchemy engine (SQLite, `DATABASE_URL` overridable), session dependency, User, Patient and Override models"],
              ["backend/app/auth.py", "bcrypt hashing, HS256 token creation and checking, `current_user` dependency"],
              ["backend/app/services/extract.py", "PDF text, OCR, sentence splitting, lexicon and negation, lab parsing, per-page items"],
              ["backend/app/services/features.py", "the 36-input definition, labels, arrival codes, priority names, risk level, `fuse`"],
              ["backend/app/services/triage.py", "cached model bundle, calibrated prediction, SHAP attribution and display values"],
              ["backend/app/services/pdf.py", "triage summary PDF with ReportLab"],
              ["ml/", "`make_data.py` (dataset), `train.py` (model and metrics), `eval.py` (reading and end-to-end timing)"],
              ["frontend/src/", "pages (Landing, Login, NewPatient, PatientResult, Queue, Performance), the design-kit components, auth and theme"],
              ["scripts/ and tests/", "sample reports, smoke test, screenshots, responsive check, experiments, timing, stress test; 47 pytest tests"],
          ], widths=[2.4, 4.1], size=9.3, align=["l", "l"]),
          P("State lives in three places. The model file `models/triage_model.joblib` and the evaluation reports are read when needed; the SQLite file `data/app.db` holds users, patients and "
            "overrides; the browser keeps only the token and the theme in local storage. The model bundle and the SHAP explainer are cached in memory after their first use. Nothing else is kept "
            "between requests, so the API can be restarted at any time without losing a patient."),
          FIG(F.diag("01_system_architecture.png"), "Layered architecture of ATHENA.", 5.4),
          ]

    # ---------------------------------------------------------------- 6.8
    b += [H2("6.8 API design"),
          P("The API is JSON over HTTP, plus one multipart upload and one PDF download. The table lists every route with its request, its successful response and its errors."),
          TAB("API routes of ATHENA (all under /api)",
              ["Method and path", "Request", "Success response", "Errors"],
              [["GET /health", "-", "status, model present", "-"],
               ["GET /public/stats", "-", "data note, accuracy, within-one, macro F1, n_test, model seconds", "-"],
               ["POST /auth/login", "email, password", "access_token, user (id, name, email, role)", "401 wrong credentials"],
               ["GET /auth/me", "token", "current user", "401"],
               ["GET /samples", "token", "items: filename, vitals, kind (pdf or image)", "401"],
               ["GET /samples/{file}", "token", "the generated sample file (PDF or PNG)", "404 unknown or outside the folder"],
               ["POST /reports/extract", "multipart file, at most 15 MB", "symptoms, findings, history, labs (each with page), flags (28), pages, text, seconds", "400 empty, 413 too large, 422 unreadable"],
               ["POST /patients", "name, vitals (8 fields), report flags, ocr_seconds", "patient: priority, risk, confidence, probabilities, SHAP list, fused record, timings", "422 invalid vitals or arrival mode, 503 no model"],
               ["GET /patients", "token", "queue items ordered by priority then arrival, with top three drivers", "401"],
               ["GET /patients/{id}", "token", "full record with overrides", "404"],
               ["GET /patients/{id}/summary.pdf", "token", "triage summary (application/pdf)", "404"],
               ["POST /patients/{id}/override", "priority 1-5, reason", "updated patient with the new override", "404, 422 change without a reason or priority out of range"],
               ["GET /metrics", "token", "offline metrics and live counts (patients, reviews, changes, agreement rate, mean seconds, distribution)", "401"]],
              widths=[1.7, 1.5, 2.3, 1.3], align=["l", "l", "l", "l"], size=8.6),
          P("The *extract* route only reads the file and returns what it found; nothing is stored, so a nurse can inspect the reading before committing a patient. The *patients* route takes "
            "the flags from the report object and ignores anything else in it, builds the fused record, calls the model and stores the patient with its timings: the OCR time sent by the "
            "browser, the model time and the total. The *override* route decides between **accept** (the posted priority equals the current one) and **change** (it does not), requires a "
            "reason for a change, writes an override row with the user's name, replaces the patient's current priority, recomputes the risk level and leaves `model_priority` untouched, "
            "which is what lets the performance page report how often clinicians kept the model's suggestion."),
          P("The queue route returns every patient ordered by current priority and then by arrival time. The metrics route combines the stored offline evaluation with live counts: patients, "
            "reviews, changed priorities, the agreement rate (one minus the share of reviewed patients whose priority was changed), the mean seconds per live patient and, for the sample cases "
            "that carry a recorded priority, the share the model matched.")]

    # ---------------------------------------------------------------- 6.9
    b += [H2("6.9 Security and error handling"),
          H3("6.9.1 What the design protects"),
          B("**Access.** Every patient, queue, report and metrics route requires a signed bearer token (HS256, valid for 12 hours); passwords are stored as bcrypt hashes; a 401 from the API signs the user out in the browser.",
            "**Input.** Vitals are range-checked by Pydantic, the arrival mode must be one of three values, uploads are limited to 15 MB and refused when empty or unreadable, and the sample-file route checks that the resolved path is inside the samples folder and has a PDF or PNG suffix.",
            "**Database.** All queries go through the SQLAlchemy ORM; no request value is placed in SQL text.",
            "**Accountability.** Each decision is stored with the user, time, old and new priority, action and reason, and the model's own suggestion is never overwritten.",
            "**Failures.** Errors are returned with a status code and a short message; a missing model gives 503 and a start-up warning instead of a crash."),
          H3("6.9.2 What it does not protect"),
          B("**Default secret.** When `JWT_SECRET` is not set the token key is the literal `dev-secret-change-me` (PyJWT warns that it is shorter than 32 bytes), so tokens can be forged by anyone who reads the source.",
            "**Roles.** The user's role is stored and put in the token, but no route checks it: a clinician can call every route an administrator can.",
            "**Transport and abuse.** The service speaks plain HTTP, has no rate limiting and no account lock-out, and the two demo accounts have a published password.",
            "**Data protection.** Patient data is stored unencrypted in one SQLite file; there is no retention policy, no export or erase function and no review against a health-data regulation.",
            "**The model.** The classifier has seen only synthetic data, the reader misses some wording, and nothing in the product stops a user from ignoring a High-risk result. It is decision support for a clinician who stays responsible."),
          TAB("Error handling in the API", ["Situation", "Response", "Where"], [
              ["Missing or invalid token", "401 with a message; the browser clears the token and shows the sign-in page", "`current_user`"],
              ["Wrong e-mail or password", "401 \"Email or password is wrong.\"", "login route"],
              ["Empty upload / larger than 15 MB / not a readable document", "400 / 413 / 422 with the reason", "extract route"],
              ["Vitals outside physical limits or unknown arrival mode", "422 with the field and limit", "Pydantic, patients route"],
              ["Priority change without a reason", "422 \"Give a reason when changing the priority.\"", "override route"],
              ["Unknown patient or sample", "404", "patient and sample routes"],
              ["Model file missing", "503 \"Model not trained yet\"; warm-up and seeding skipped with a log warning", "`triage._bundle`, start-up"],
              ["API unreachable from the browser", "single message \"Cannot reach the ATHENA API\"", "`lib/api.js`"],
          ], widths=[2.6, 2.9, 1.0], size=9.3, align=["l", "l", "l"]),
          ]

    # ---------------------------------------------------------------- 6.10
    b += [H2("6.10 Installation and execution"),
          P("The full step-by-step guide is Appendix B and `docs/03_HOW_TO_RUN.md`. The product runs in two ways."),
          N("**run.bat (Windows).** Checks the environment and, if needed, runs `setup.bat`: it creates the `venv/` Python environment and installs `requirements.txt`, generates the synthetic dataset and trains "
            "the model when `models/triage_model.joblib` is missing, generates the sample reports when missing, and runs `npm install` in `frontend/`. It then starts the API and the web application in two "
            f"minimised windows and opens http://localhost:{F.WEB_PORT}.",
            f"**Manual.** `python -m uvicorn backend.app.main:app --port {F.API_PORT}` from `8.ProjectCode`, and `npm run dev` in `frontend/`; the Vite server proxies `/api` to the API."),
          CODE("venv\\Scripts\\python ml\\make_data.py        # seeded synthetic dataset -> data\\sample\\\n"
               "venv\\Scripts\\python ml\\train.py            # model -> models\\, metrics -> experiments\\metrics.json\n"
               "venv\\Scripts\\python ml\\eval.py             # reading and timing -> experiments\\eval\\metrics.json\n"
               "venv\\Scripts\\python scripts\\smoke_test.py  # 17 checks against the running API\n"
               "venv\\Scripts\\python -m pytest tests         # 47 tests", 9),
          P(f"Ports are fixed: API {F.API_PORT}, web {F.WEB_PORT}. An optional `.env` may set `DATABASE_URL` and `JWT_SECRET`; otherwise a local SQLite file and the development secret are used. "
            f"Sign in with {F.DEMO_USER} and the demo password given in Appendix B. A new database starts with twelve labelled sample cases so that the queue and the performance page are not empty. "
            "Deleting `data/app.db` resets the queue and the review log."),
          P(f"Verification after installation is `python -m pytest tests` ({F.PYTEST_TOTAL} tests: {F.PYTEST_PASSED} pass and {F.PYTEST_XFAIL} documented expected failure, about {F.PYTEST_SECONDS} seconds) and "
            f"`scripts/smoke_test.py` ({F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks pass), described in Chapter 7. `scripts/capture_screens.py` regenerates the screenshots used in Chapters 7 and 8. "
            "The fresh-environment path of `setup.bat` and `scripts/download_data.py` were not exercised in the documentation run."),
          ]
    if F.REPORT:
        b = _drop(b, "Layered architecture of ATHENA", "Error handling in the API")
        b = _renumber_h3(b)
    return b


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
