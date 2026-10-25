"""Chapter 2: Literature Survey."""

from . import facts as F
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def c(*keys):
    return ", ".join(f"[{R[k]}]" for k in keys)


def blocks():
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        P("This chapter reviews the work on which ResQAI builds and against which it is placed. It begins with an overview of the literature in this area, analyses the base paper in detail, "
          "groups the related work by theme, summarises the datasets and algorithms involved, sets out strengths and limitations, and closes with the research gap that the project addresses. "
          "Every bibliographic entry quoted here was checked against the PDF of the paper or a publisher page, except four titles taken from the batch survey, which are named as such."),

        H2("2.1 Overview"),
        P("Three bodies of work meet in this project. The first is automatic crash detection and notification, which is largely a hardware and Internet-of-Things literature: a sensor, a microcontroller or phone, a positioning module "
          f"and a messaging channel {c('greenbox', 'dashora', 'karthik', 'anilkumar', 'uma', 'sharma')}. The second is vision-based accident detection from camera frames, represented here by CIRS {c('cirs')}. "
          f"The third is accident severity prediction, which applies statistical and machine-learning models to recorded crash data {c('lin', 'chen', 'sameen', 'zheng', 'hamdan', 'pei')} and, in the base paper, a multi-task transformer {c('base')}."),
        P("The batch literature survey lists five papers: the base paper, and four recent papers on machine-learning prediction of road accident severity (two journal papers, one ITSC 2024 and one INDICON 2024 conference paper). "
          "Their titles, years and sources are recorded in the batch file; web searches carried out for this report did not locate any of the four, so their authors, data and results could not be verified and none of them is cited here for a claim. "
          "They are listed in the reference section with a note to that effect. The survey's own conclusion is that they predict severity from recorded datasets after the event, "
          "and none closes the loop from live sensing through severity grading to automated hospital dispatch."),

        H2("2.2 Base Paper Analysis"),
        P(f"The base paper is Y. Wang, Z. Liang and Y. He, \"Multi-Task FT-Transformer: A High-Performance and Interpretable Framework for Traffic Accident Severity Prediction,\" IEEE Access, vol. 14, 2026 {c('base')}. "
          "It was received on 6 January 2026 and published on 28 January 2026, and it was read in full for this report."),
        H3("2.2.1 What the paper does"),
        P(f"The authors predict three outcomes of a traffic accident at once: injury severity (five classes), fatal-accident severity (five classes) and property-loss severity (six classes). They argue that the three are interdependent, "
          f"so a single multi-task model can share information between them. The model is an FT-Transformer, a transformer that turns each tabular feature into a token {c('gorishniy')}, with a loss in which the weight of each task is set by its learned uncertainty {c('kendall')}. "
          f"Class imbalance is handled with SMOTE on the training split only {c('smote')}, and the predictions are explained with SHAP {c('shap')}."),
        H3("2.2.2 Data and set-up"),
        P("The data are proprietary, police-reported crash records of the city of Dongguan, China, for 2019 to 2023, accessed under a data-use agreement. The three splits hold 19,483 training, 4,871 validation and 6,088 test samples, a total of 30,442 records. "
          "The inputs are driver, vehicle, road and environmental attributes. Training used the Adam optimiser at a learning rate of 1e-4, a batch size of 500 and early stopping after 30 epochs without improvement. "
          "Eight baselines were trained on each task: XGBoost, LightGBM, CatBoost, a multilayer perceptron, a decision tree, a random forest, a support-vector machine and k-nearest neighbours."),
        H3("2.2.3 Reported results"),
        TAB("Results reported by the base paper on its own Dongguan test split",
            ["Task", "Accuracy", "Precision", "Recall", "F1"],
            [["Injury severity (5 classes)", "70.31%", "60.16%", "70.31%", "64.48%"],
             ["Fatal-accident severity (5 classes)", "90.38%", "87.19%", "90.38%", "86.71%"],
             ["Property-loss severity (6 classes)", "80.79%", "78.98%", "80.79%", "79.18%"]],
            widths=[2.6, 0.9, 0.9, 0.9, 0.9], align=["l", "c", "c", "c", "c"], size=10),
        P("The paper reports that the model beat all eight baselines on accuracy for all three tasks, and that it beat a multi-task CNN of an earlier study, which scored 0.58, 0.82 and 0.62 on the same three tasks."),
        H3("2.2.4 Strengths and limits stated by the authors"),
        P("The paper's strengths are a large, real, multi-year dataset, a principled treatment of task interdependence, and interpretability through SHAP. "
          "The authors themselves state the limits: the data come from a single city, so the numbers should be read as performance on Dongguan data and not as a general level; injury severity is the number of injured people, "
          "used as a proxy because clinical scores were not available; the ordinal nature of severity is not modelled; and training and inference cost against tree baselines was not compared."),
        H3("2.2.5 Relation to ResQAI"),
        P("The base paper and ResQAI share a theme, the grading of accident severity, and almost nothing else. The base paper is a post-event analytics model on recorded tabular reports; it does not detect a crash, "
          "use phone sensors, locate a crash or dispatch anything. ResQAI works on a sensor reading at the moment of impact, uses two random forests on eleven motion features, "
          "and connects the result to a confirmation step and a located alert. ResQAI therefore adopts from the base paper only the idea of grading severity and the habit of reporting accuracy, precision, recall and F1 per class. "
          "It does not use the FT-Transformer, the dataset, SMOTE or SHAP. Because the data, the task and the label definitions differ completely, the base paper's percentages cannot be compared with ResQAI's, and this report makes no such comparison as a ranking."),

        H2("2.3 Related Work by Theme"),
        H3("2.3.1 Sensor-based crash detection and notification"),
        P(f"GreenBox {c('greenbox')} is the closest in aim. It is an Arduino Uno prototype with a SIM7600 GSM and GPS shield, four push-buttons acting as impact sensors, an MPU-6050 inertial sensor for rollover detection above 70 degrees "
          "of inclination, two water-level sensors and a relay that cuts the engine. On detection it sends an SMS with the vehicle location and last known speed to preset contacts, and the owner can cancel a false detection by SMS. "
          "Its evaluation is qualitative: the alerts arrived \"in a matter of seconds\" and the GPS position and speed matched the car's speedometer; no accuracy, precision or latency figures are given, and no machine learning is used."),
        P(f"The works that GreenBox itself cites describe a family of designs of the same kind. Dashora et al. {c('dashora')} use an accelerometer to monitor speed change in frontal and rear-end collisions and send data over Wi-Fi; "
          f"GreenBox notes that sudden braking can cause false positives in such a design. Karthik et al. {c('karthik')} combine an Arduino, a GSM module, a vibration sensor and an accelerometer for automatic messaging. "
          f"Anil Kumar et al. {c('anilkumar')} describe a vehicle black box that records acceleration, detects alcohol and tracks location. Uma and Eswari {c('uma')} use IoT and machine learning for driver safety, "
          f"and Sharma and Sebastian {c('sharma')} add a seat-belt heart-rate sensor to the accelerometer, GPS and GSM chain. All of these are described here only by approach, because the numbers in them were not read for this report."),
        H3("2.3.2 Vision-based accident detection"),
        P(f"CIRS {c('cirs')} is a multi-agent framework in which a YOLOv11 detector classifies camera frames as accident or non-accident, a vision-language model (VideoLLaMA3) describes the scene, and further agents handle localisation and dispatch. "
          "On a custom dataset of 5,200 accident and 4,800 non-accident frames YOLOv11 reached a top-1 accuracy of 86.5%, with precision 0.866, recall 0.856 and F1 0.861 for the accident class; 128 of 1,044 non-accident test frames were classified as accidents. "
          "The paper is candid that a false-positive rate of this size is tolerable only where missing a real accident matters more. Its sensing modality, fixed cameras, is different from a phone in the vehicle, and its numbers describe frames, not motion readings."),
        H3("2.3.3 Accident severity prediction from recorded data"),
        P(f"The severity literature is large. Lin et al. {c('lin')} applied random forest and XGBoost to 8,859 crashes involving teen drivers on rural West Texas roads, and Chen and Chen {c('chen')} compared logistic regression, "
          "a decision tree and a random forest on 9,472 crashes in Taiwan, finding the random forest most effective (both counts as stated in the base paper). "
          f"Sameen and Pradhan {c('sameen')} used recurrent neural networks, which the base paper reports reached 73.76% accuracy, ahead of CNN and feed-forward models, and Zheng et al. {c('zheng')} mapped crash records to grey images for a CNN. "
          f"Two recent surveys and studies extend the picture: Hamdan and Sipos {c('hamdan')} review machine-learning models for severity, comparing random forest, XGBoost and support-vector machines and covering ensembles and crash-type-specific models, "
          f"and Pei et al. {c('pei')} propose a framework for risk prediction and key-factor identification with explainable deep learning. The review states no numeric result in its abstract and none is quoted here."),
        P("All of these models take a recorded record as input and return a severity class. None of them is attached to a sensor, a confirmation step or an alert."),
        H3("2.3.4 The remaining titles of the batch survey"),
        P("The batch survey also lists a 2025 journal paper on machine-learning prediction of road accident severity, an ITSC 2024 paper on deep-learning severity prediction, an INDICON 2024 paper on improving severity prediction rates, "
          "and a 2026 review of machine learning and explainable AI for severity prediction. Their content could not be checked, so they are treated only as evidence that the topic is active, and not as a source of numbers."),

        H3("2.3.5 Why a sensor chain and not recorded data"),
        P("The reviewed severity models are evaluated by splitting a recorded dataset and measuring how well the held-out part is classified. That is the right test for planning and policy, where the question is which factors make a crash severe. "
          "It is not the right test for an emergency system, where the question is whether a particular event, seen for the first time, is a crash, how bad it is, and what to do within seconds. "
          "The inputs differ too: a police report carries driver, vehicle, road and weather attributes that are known only after the event, whereas a sensor chain has the physical signature of the impact itself. "
          "A system built for response must therefore take the sensor signature as its input, which is what ResQAI does, and must be judged also on false alarms and delay, which severity papers do not report."),
        H3("2.3.6 Evaluation measures used in the literature"),
        P("The papers read report accuracy, precision, recall and the F1 score, and the base paper defines them from the counts of true and false positives and negatives. ResQAI uses the same four measures for its detector and, for its four-class severity model, reports accuracy, per-class precision, recall and F1, and macro-F1, "
          "which averages the per-class F1 values without weighting by class size and so does not hide a weak rare class. Two measures are added because the application needs them: the false-alarm rate (the share of non-accidents flagged) "
          "and the alert-trigger rate (the share of events that would start the 15-second confirmation), together with latency of the alert path. The camera-based CIRS paper reports a count of false positives in the same spirit."),

        H2("2.4 Datasets and Algorithms Used in the Literature"),
        TAB("Datasets and algorithms of the principal works, as read for this report",
            ["Work", "Input data", "Algorithm", "Reported result"],
            [[f"Wang et al. {c('base')}", "30,442 police crash records, Dongguan, 2019-2023", "Multi-task FT-Transformer, uncertainty-weighted loss, SMOTE, SHAP", "Accuracy 70.31% / 90.38% / 80.79% (injury / fatal / property)"],
             [f"GreenBox {c('greenbox')}", "Push-buttons, MPU-6050, water sensors, GPS (live prototype)", "Fixed thresholds, SMS over GSM", "Qualitative only: SMS in seconds"],
             [f"CIRS {c('cirs')}", "5,200 accident + 4,800 non-accident camera frames", "YOLOv11, VideoLLaMA3, multi-agent dispatch", "Top-1 accuracy 86.5%, F1 0.861"],
             [f"Chen and Chen {c('chen')}", "9,472 crashes, Taiwan", "Logistic regression, decision tree, random forest", "Random forest most effective (per base paper)"],
             [f"Sameen and Pradhan {c('sameen')}", "Crash records", "RNN against CNN and feed-forward", "73.76% accuracy (per base paper)"],
             [f"ResQAI (this project)", f"{F.N_TOTAL:,} synthetic sensor events", "Two random forests on 11 motion features", f"Detector accuracy {F.f4(F.DET['accuracy'])}, severity accuracy {F.f5(F.SEVM['accuracy'])} (synthetic)"]],
            widths=[1.3, 1.8, 1.8, 1.6], align=["l", "l", "l", "l"], size=9),
        P(f"Two algorithms are central to ResQAI. The random forest {c('breiman')} averages many decorrelated decision trees and returns class probabilities, which the project uses as the accident confidence. "
          f"The haversine formula {c('haversine')} gives the great-circle distance between two latitude-longitude points and is used to rank hospitals. Both are standard and are not claimed as contributions."),

        P(f"The base paper's own comparison shows the role of the random forest in this literature: it appears as one of eight baselines and, on the Dongguan data, scores below the FT-Transformer on every task. "
          f"That finding concerns noisy, mixed categorical records of past crashes. ResQAI's input is low-dimensional and numeric, with large physical differences between classes, and on such data the forest is an appropriate, fast and explainable choice; "
          f"Chapter 8 shows, however, that a gradient-boosted model ties the forest and a depth-10 decision tree comes within a fraction of a point on the synthetic data, so the choice of forest is a matter of convenience and probabilities and not a measured superiority."),

        H2("2.5 Strengths and Limitations of the Existing Work"),
        TAB("Strengths and limitations of the existing approaches",
            ["Approach", "Strengths", "Limitations"],
            [["IoT prototypes (GreenBox and its relatives)", "Low cost, direct sensing, SMS alert with location, owner can cancel", "Fixed thresholds and dedicated hardware; no severity grade; no quantitative evaluation in the work read"],
             ["Camera-based detection (CIRS)", "Real image data, quantified results, scene description", "Needs fixed cameras; moderate false-positive count; not available on every road"],
             ["Severity models on records (base paper and others)", "Large real datasets, careful comparison, interpretability", "Post-event; no sensing, confirmation or alert; single-city data; severity proxies"],
             ["ResQAI", "Joins sensing, grading, confirmation, location and alert; runs on a laptop; fully tested interface", "Synthetic data; road-surface events not modelled; nothing transmitted; ten-hospital directory"]],
            widths=[1.8, 2.3, 2.4], align=["l", "l", "l"], size=9.5),


        H2("2.6 Research Gap"),
        P("The survey shows three gaps, and the project addresses the first and, partly, the second and third."),
        N("**Loop closure.** Severity prediction papers work on recorded datasets after the event. None of the work reviewed closes the loop from live sensing, through severity grading, to a prioritised, located alert.",
          "**False-alarm handling.** Threshold-based prototypes report impacts but separate crashes from braking and road-surface shocks only by fixed thresholds, with no confirmation window and no learned grade. "
          "ResQAI adds a learned detector, a severity grade and a 15-second cancel window; its handling of potholes and speed breakers is not demonstrated.",
          "**Quantified evaluation of the whole chain.** Prototype papers report qualitative success. ResQAI reports detection and severity metrics, false-alarm rates, noise robustness and the latency of the alert path, with the limits of synthetic data stated."),
        P("The gap that remains is evidence on real recordings; Chapter 10 returns to it."),
    ]
