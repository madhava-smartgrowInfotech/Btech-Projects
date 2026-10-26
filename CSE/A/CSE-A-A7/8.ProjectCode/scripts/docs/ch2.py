"""Chapter 2: Literature survey."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def blocks():
    b = _full()
    if not F.REPORT:
        return b
    from .ch1 import trim
    keep_rel = lambda r: not any(n in r[0] for n in ("Xie", "Cheng"))
    return trim(
        b,
        drop=("Two further observations come from", "Explanation and calibration are treated here"),
        drop_sections=("2.3.5",),
        table_rows={"Related work compared": keep_rel},
    )


def _full():
    bp = F.BASE_PAPER_RESULTS
    base = R["base"]
    abl, comp = F.ABL, F.COMP
    base_rows = [
        ["Task", f"Classify the disease category (ICD-10) of a patient from the symptoms, examination findings and a few laboratory results of a medical history; {bp['classes']} classes ({bp['classes_ped']} paediatric, {bp['classes_int']} internal medicine)"],
        ["Data", f"{bp['cases']:,} authentic clinical cases from electronic records ({bp['internal']} internal medicine, {bp['pediatrics']:,} paediatrics); {bp['parameters']} clinical parameters (65 reported symptoms, 386 examination signs, 28 laboratory and imaging values); mean feature completeness 74.91 % (paediatrics) and 82.31 % (internal medicine)"],
        ["Training data", "Rule-based synthetic cases generated from ICD-10 criteria and symptom co-occurrence patterns, with partial feature shifting, adaptive noise and synthetic combinations; evaluation on the authentic cases"],
        ["Algorithms", f"{bp['algorithms']} classifiers in five families (tree-based, ensemble, linear and probabilistic, distance and kernel based, neural network), each tuned per specialty by Optuna TPE with a median pruner, {bp['trials']} trials for standard models"],
        ["Missing data", "No imputation: a symptom that is not documented is set to 0 (absent); histogram gradient boosting handles missing values natively"],
        ["Uncertainty", f"Two-stage TOP-1 / TOP-3 ranking from class probabilities; a confidence threshold of {bp['threshold']:.2f} marks a diagnosis as highly probable; entropy of the probability distribution as an uncertainty measure"],
        ["Explanation", "SHAP (KernelExplainer, k-means background) and LIME; top-feature agreement between the two of 43.1 % (GB) and 31.9 % (MLP); physician review of SHAP heatmaps"],
        ["Statistics", "McNemar paired tests with exact p-values; bootstrap 95 % confidence intervals with 1,000 resamples"],
        ["Headline results", f"TOP-1: {bp['best_int'][0]} {bp['best_int'][1] * 100:.2f} % (internal medicine), {bp['best_ped'][0]} {bp['best_ped'][1] * 100:.2f} % (paediatrics); mean TOP-3 {bp['top3_mean_int'] * 100:.2f} % and {bp['top3_mean_ped'] * 100:.2f} %; best TOP-3 {bp['top3_best_int'] * 100:.2f} % and {bp['top3_best_ped'] * 100:.2f} %"],
        ["External validation", f"{bp['ext_cases']} cases from another facility: TOP-1 {bp['ext_top1_int'] * 100:.2f} % / {bp['ext_top1_ped'] * 100:.2f} %, TOP-3 {bp['ext_top3_int'] * 100:.2f} % / {bp['ext_top3_ped'] * 100:.2f} % (internal medicine / paediatrics); treated by the authors as the primary benchmark"],
        ["Deployment", f"Core module of the PARROT AI multimodal medical assistant [{R['plaza']}]; REST API, real-time and batch prediction modes"],
    ]
    keep_rows = [
        ["Probability ranking instead of a bare label", "TOP-1 and TOP-3 lists with class probabilities",
         f"Calibrated probabilities for all five priorities; Top-2 accuracy {F.pct(F.TOP2)} reported beside exact accuracy {F.pct(F.ACC)}"],
        ["High-confidence threshold", f"{bp['threshold']:.2f}, with a sensitivity analysis from 0.70 to 0.95",
         f"Same sweep on the synthetic hold-out: at 0.85 coverage {F.pct(F.thr_row(0.85)['coverage'])} and accuracy {F.pct(F.thr_row(0.85)['accuracy'])}"],
        ["Absent symptom is 0, no imputation", "Binary indicators default to 0", "Every report flag defaults to 0 when the reader does not find it; robustness to dropped flags measured"],
        ["Several algorithms compared", f"{bp['algorithms']} classifiers", f"{len(comp)} models on the same split (Chapter 8); XGBoost kept for calibration and SHAP, not because it won"],
        ["SHAP explanation", "KernelExplainer, global heatmaps per ICD-10 group", "TreeExplainer, one list per patient beside the decision"],
        ["Input data", "Typed symptom indicators and a few laboratory values", "A scanned report read by OCR and a lexicon, fused with eight vitals"],
        ["Target", "ICD-10 diagnosis, 87 classes", "Five-level triage priority with a risk level"],
        ["Training data", "Rule-based synthetic training, real evaluation", "Rule-based synthetic training and synthetic evaluation: weaker evidence"],
        ["Workflow", "Decision-support module after the consultation", "Clinician accept-or-change loop with a stored reason, live queue, summary PDF"],
        ["Not carried over", "Optuna tuning, LIME, dynamic ensemble, McNemar tests, external validation", "Not done; listed as future work"],
    ]
    rel_rows = [
        [f"Mlodawski et al. [{base}] (base paper)", "19 classifiers, TOP-1 / TOP-3, SHAP and LIME", f"GB {bp['best_int'][1] * 100:.2f} %, MLP {bp['best_ped'][1] * 100:.2f} % TOP-1", "Typed indicators; no scanned input; no timing"],
        [f"Fernandes et al. [{R['fernandes']}]", "Review of intelligent triage support", "Contributions from better triage to critical-care prediction", "Many studies never reached implementation"],
        [f"Hinson et al. [{R['hinson']}]", "Review of triage scale performance", "182 eligible studies; sensitivity for critical illness below 80 %", "Describes the scales, proposes no model"],
        [f"Hong et al. [{R['hong']}]", "Logistic regression, XGBoost, deep nets", "560,486 visits; triage-only AUC about 0.87, full about 0.92", "Predicts admission, not priority"],
        [f"Levin et al. [{R['levin']}]", "Random-forest e-triage", "172,726 visits; AUC 0.73 to 0.92; matched or beat ESI", "Predicts outcomes; structured fields"],
        [f"Raita et al. [{R['raita']}]", "Lasso, forest, boosting, deep net", "135,470 visits; deep net AUC 0.86 against 0.74 for ESI", "Structured fields only"],
        [f"Xie et al. [{R['xie']}]", "Public MIMIC-IV-ED benchmark", "Three prediction tasks on public records", "No scanned reports; figures not quoted here"],
        [f"Cheng et al. [{R['cheng']}]", "Multi-agent LLM matching under uncertainty", "Read from the title only", "Text-only agents; no vitals fusion"],
    ]
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The survey covers four strands of work that meet in this project: triage in the emergency department and how well it performs, machine-learning models trained on "
          "triage data, clinical decision support that reads clinical text, and the explanation and calibration techniques that make a model's output usable at the bedside. "
          f"The batch literature survey lists five works, led by the base paper [{base}]. Of the other four, one [{R['s_acmj']}] is a prospective comparison of two triage scales "
          f"in a Turkish hospital and one [{R['s_nepal']}] is a questionnaire study of how much patients' attendants know about triage in Nepal; neither uses a model. A third, on identifying the high-risk "
          f"obstetric patient at triage [{R['s_obst']}], could not be located in any index searched, so it is listed but not used as evidence, and the fourth [{R['s_horse']}] is a chapter of a book on "
          "emergency triage of the horse, which is veterinary and outside the human-triage domain of this project. The review therefore leans on the base paper's own analysis and on "
          "the triage and decision-support literature found and checked for this report. Results quoted below are the authors' own claims; none was reproduced."),

        H2("2.2 Base Paper Analysis"),
        H3("2.2.1 Problem and approach"),
        P(f"The base paper, by Mlodawski et al. [{base}], addresses a problem that every decision-support system meets in practice: clinical data are incomplete. A history may omit symptoms "
          "that were not asked about, laboratory tests that were not ordered, and details the clinician had no time to record. The authors classify the kinds of incompleteness (systemic, "
          "cognitive, procedural, temporal, semantic and disproportionate) and argue that a system should work directly on incomplete records, without imputation, and should keep a broad "
          "list of diagnostic hypotheses instead of a single answer."),
        P(f"Their system takes the symptoms, examination findings and laboratory results of an internal-medicine or paediatric consultation, encodes them as binary indicators, and passes "
          f"them to {bp['algorithms']} trained classifiers. Each classifier returns a probability for each ICD-10 category. The top-ranked category is the TOP-1 answer; the three most probable "
          "categories form the TOP-3 list, which formalises the differential diagnosis a physician keeps in mind. For high-risk disease categories a higher probability threshold is "
          "required before the TOP-1 answer is accepted alone; otherwise the system falls back on the TOP-3 list. The processing chain is a pipeline: user interface, orchestrator, "
          "symptom encoder, dataset converter, feature engineering, trainers, an Optuna hyper-parameter optimiser, an evaluation module, a packaging and reporting layer, and "
          "a deployment layer with a REST API, real-time prediction and batch prediction."),
        H3("2.2.2 Evaluation protocol and reported numbers"),
        P("Because real records were scarce for 87 diagnostic classes, the authors trained on rule-based synthetic cases generated from ICD-10 diagnostic criteria and symptom co-occurrence "
          f"patterns, and evaluated on {bp['cases']:,} authentic cases. They add that this synthetic-to-real route is a feasibility approach, not a substitute for real training data. The table below "
          "summarises the design and the numbers as printed in the paper."),
        TAB("The base paper at a glance", ["Item", "As reported in the paper"], base_rows, widths=[1.5, 4.8], align=["l", "l"], size=10),
        P("Two points in the paper's own discussion matter for this project. The authors state that the internal-set accuracies reflect synthetic-to-real transfer and may be inflated by "
          "the shared ICD-10 framework, and therefore treat the external validation (73.33 % and 78.33 % TOP-1) as the primary benchmark. They also write that no claim of clinical utility "
          "can be substantiated without an adequately powered prospective study on real data from several facilities."),
        H3("2.2.3 Strengths"),
        B("A broad, fair comparison: 19 algorithms, tuned with the same sampler and seed, with McNemar tests and bootstrap confidence intervals to separate real differences from noise.",
          "A realistic treatment of missing data: no imputation, absent symptoms set to zero, and an algorithm family (histogram boosting) that handles gaps natively.",
          "The TOP-3 mechanism, which turns a single fallible answer into a ranked differential, together with a confidence threshold and a sensitivity analysis of that threshold.",
          "Explanation checked by physicians: SHAP heatmaps per ICD-10 category were reviewed for consistency, and a referral-feature ablation showed the models do not lean on referrals as a proxy for the label.",
          "Candour about limits: external validation on 120 cases from another region, a reported fall in TOP-1 accuracy, and an explicit warning about synthetic-to-real evaluation."),
        H3("2.2.4 Limitations"),
        B("The input is a list of typed binary indicators. Nothing in the system reads a scanned or photographed report, although much of the information in real records lives there.",
          "The target is an ICD-10 diagnosis, not an urgency. A system that names a probable diagnosis does not say who must be seen first.",
          "Vital signs enter only as binary examination findings such as normal blood pressure, not as measured values; the 479 parameters are symptoms, examination signs and a few laboratory and imaging results.",
          f"The data come from one healthcare system; the external set is only {bp['ext_cases']} cases; rare diseases were excluded by the three-case minimum, and the low-prevalence classes are called exploratory by the authors.",
          "The paper reports accuracy, precision, F1 and TOP-3 but no processing time per patient and no description of how a clinician would act on a prediction.",
          "SHAP and LIME agree on only 31.9 % to 43.1 % of top features, which the authors explain as methodological complementarity but which leaves the explanation partly unsettled."),
        H3("2.2.5 What this project keeps from the base paper and what it changes"),
        P("ATHENA reuses the ideas of the base paper that carry over to triage, and changes the input, the target and the workflow. The table below sets the two side by side. "
          "The tasks and data differ, so no accuracy in this report is set against the base paper's as a competing figure."),
        TAB("Base paper compared with this project", ["Aspect", "Base paper", "This project"], keep_rows, widths=[1.5, 2.2, 2.6], align=["l", "l", "l"], size=9.5),

        H2("2.3 Related Work"),
        H3("2.3.1 Triage scales and their performance"),
        P(f"Emergency triage is organised around a small number of five-level scales: the Emergency Severity Index [{R['esi']}], the Canadian Triage and Acuity Scale, the Manchester "
          f"Triage System and the Australasian Triage Scale. The systematic review of Hinson et al. [{R['hinson']}] searched four databases through 2016, found 6,160 publications and "
          "analysed 50 with sufficient data. The three most studied scales showed similar performance; most studies found high sensitivity for identifying patients who died in the "
          "emergency department, but sensitivity for identifying critical illness was below 80 %, and a substantial proportion of patients who die after the encounter or are critically ill "
          "were not designated as high acuity at triage."),
        P(f"A prospective study in a Turkish state hospital [{R['s_acmj']}] triaged 6,000 patients with ESI and 6,000 with the Manchester system and compared clinical outcomes, patient satisfaction "
          "and risk management; its authors favour expanding the use of ESI. It is a process study with no learning component, which makes it useful as evidence that the five-level target "
          "is the one the field already uses."),
        H3("2.3.2 Machine learning on emergency-department triage data"),
        P(f"Hong, Haimovich and Taylor [{R['hong']}] trained logistic regression, XGBoost and deep neural networks on 560,486 visits from one academic and two community emergency "
          "departments to predict hospital admission. Models using only triage information reached a test AUC of about 0.87 and models with the full variable set about 0.91 to 0.92, "
          f"so history added measurable information. Levin et al. [{R['levin']}] built a random-forest electronic triage on 172,726 visits that used vital signs, chief complaint and "
          "history to predict critical care, an emergency procedure and hospitalisation; AUCs ranged from 0.73 to 0.92 and the model matched or outperformed ESI."),
        P(f"Raita et al. [{R['raita']}] compared Lasso regression, random forest, gradient-boosted trees and a deep neural network on 135,470 adult visits from the NHAMCS survey, with "
          "an ESI-based logistic regression as reference. For critical care all four learned models beat the reference; the deep network reached an AUC of 0.86 against 0.74. "
          f"Xie et al. [{R['xie']}] released a benchmark built on MIMIC-IV-ED so that such models can be compared on public records. The review of Fernandes et al. [{R['fernandes']}] "
          "covers this body of work and notes that several studies lack an implementation phase and that the impact on quality of care still has to be assessed."),
        P("Two further observations come from this group of papers. The prediction target is almost always an outcome (admission, critical care), not the five-level priority that a nurse "
          "assigns; and the inputs are structured fields. Neither choice is wrong, but together they leave open the question this project asks: what changes when the target is the "
          "priority itself and a scanned report is among the inputs."),
        H3("2.3.3 Clinical text, language models and OCR"),
        P(f"Clinical language models such as BioBERT [{R['biobert']}] are pre-trained on biomedical text and improve information extraction from clinical notes. The base paper itself points to "
          f"a coding system that combines a deep contextualised language model with rule-based methods for ICD-10 coding [{R['chen_icd']}], where the combination of a pre-trained model "
          f"with expert rules was credited for the result, and to a multimodal medical assistant that integrates documentation and decision support [{R['plaza']}]. Reading a scan "
          f"first requires optical character recognition; PP-OCR [{R['ppocr']}] is a practical lightweight system whose family of models is available through ONNX Runtime and is used in this "
          "project through the RapidOCR package. A systematic review of generative AI against physicians "
          f"[{R['takita']}] and a review of clinician performance with decision-support systems [{R['vasey']}] are cited by the base paper in its discussion of how AI diagnosis compares with physicians and how decision support is evaluated; they are used here to argue for careful "
          "evaluation."),
        H3("2.3.4 Explanation and calibration"),
        P(f"SHAP [{R['shap']}] assigns each input an additive contribution to one prediction, and the TreeExplainer algorithm [{R['treeshap']}] computes exact values for tree ensembles quickly "
          f"enough to run inside a request. LIME [{R['lime']}] fits a local linear surrogate. The base paper reports that the two agree on only part of the top features and recommends a "
          "consolidated view, with SHAP as the primary explanation. For probabilities, isotonic regression "
          f"[{R['zadrozny']}] and other methods [{R['niculescu']}] map raw scores to frequencies, and the observation that modern models are often over-confident [{R['guo']}] explains why a "
          "calibration stage is worth its cost in a clinical setting. Explanation and calibration are treated here as part of the product, not as an afterthought: the result screen "
          "shows the SHAP list and the calibrated confidence together."),
        H3("2.3.5 The batch survey entries and what the survey implies for the design"),
        P(f"Among the five works of the batch survey, only the base paper and the Turkish scale comparison [{R['s_acmj']}] bear directly on the design. The Nepalese questionnaire study "
          f"[{R['s_nepal']}] supports the observation that triage depends on people who need clear information; the obstetric item [{R['s_obst']}] could not be verified; and the equine "
          f"chapter [{R['s_horse']}] is outside the domain. The wider literature adds the companion reference paper on multi-agent triage under uncertainty [{R['cheng']}], read from its title only, "
          f"and an archived second candidate base paper on explainable risk prediction on medical time series with language models [{R['jang']}], also read from its title only."),
        P("Four design decisions follow from the survey as a whole. The target is the five-level priority, because that is what the scales and the nurse use. The inputs are the vitals "
          "that every triage model uses plus the content of the scanned report, because that is the information the structured-field models miss. The model returns calibrated probabilities "
          "and an explanation, because the base paper and the reviews agree that a ranked, explained output is what a clinician can use. And the evaluation reports weaknesses openly, "
          "because the reviews of intelligent triage systems show how rarely claims have been tested in practice."),

        H2("2.4 Datasets and Algorithms Used in This Project"),
        TAB("Datasets and algorithms of this project", ["Element", "Choice", "Why"], [
            ["Training and test data", f"Seeded synthetic dataset, {F.ROWS:,} rows, seven archetypes, 36 inputs, five priorities (`ml/make_data.py`, seed {F.SEED})",
             "No real patient records were available to the team; the synthetic set is reproducible and carries a known rule and noise level"],
            ["Intended real source", "Kaggle 'Hospital Triage and Patient History Data' (licence not stated); `scripts/download_data.py` exists but was never run",
             "Would give clinician-recorded outcomes; not used, so no real-data claim is made"],
            ["Sample reports", "12 generated reports (8 two-page PDFs, 4 PNG scans) with expected findings", "Demonstrate both intake paths; they test the pipeline, not real-world scan variety"],
            ["Report reading", "pypdf text layer; RapidOCR for images; lexicon of 22 flags with negation; six lab parsers", "Offline, no key, inspectable; a medical language model was beyond the data and time available"],
            ["Triage model", "XGBoost, 220 trees, depth 4, learning rate 0.1 [" + str(R['xgboost']) + "]", "Strong on tabular data [" + str(R['grinsztajn']) + "], native TreeSHAP, fast on CPU"],
            ["Calibration", "Isotonic regression on a separate 20 % calibration split [" + str(R['zadrozny']) + "]", "Makes the displayed confidence a probability"],
            ["Explanation", "SHAP TreeExplainer on the same trees [" + str(R['treeshap']) + "]", "Exact, per patient, cheap enough for one request"],
            ["Comparison models", "Logistic regression, decision tree, random forest, extra trees, k-NN, MLP, histogram boosting [" + str(R['sklearn']) + "], [" + str(R['breiman']) + "]", "Same split, to show what the shipped choice costs or gains"],
        ], widths=[1.3, 2.7, 2.3], align=["l", "l", "l"], size=9.5),

        H2("2.5 Strengths and Limitations of the Surveyed Work"),
        TAB("Related work compared", ["Work", "Approach", "Reported result", "Limitation for this project"], rel_rows, widths=[1.3, 1.7, 1.9, 1.4], align=["l", "l", "l", "l"], size=9),
        P("Taken together, the surveyed work is strong on scale: hundreds of thousands of visits, statistical tests, external validation. It is weaker on three counts that matter here. "
          "It rarely uses the content of scanned documents; it rarely targets the five-level priority; and it seldom reports what the whole path costs in time or how a clinician's "
          "agreement with the model would be recorded."),

        H2("2.6 Research Gap"),
        P("The gap identified by the batch survey is that the surveyed models are evaluated on single-modality structured data, and that a pipeline fusing scanned-report reading, "
          "clinical text and tabular vitals, and exposing the reasoning behind each decision, is missing. The survey of this report refines it into five points:"),
        N(*[g for g in lit.GAPS]),
        P("ATHENA addresses these points on a small scale and under an honest limit: it fuses a scanned report with the vitals, targets the five-level priority, shows a per-patient "
          "explanation with a calibrated confidence, stores the clinician's decision, and measures time per patient; and it does so on synthetic data, so it demonstrates the pipeline "
          "and not clinical performance."),
    ]
