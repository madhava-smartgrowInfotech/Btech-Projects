"""Chapter 2: Literature survey. Every figure quoted here was read in the base paper's PDF, the two supplied arXiv PDFs, or a web page
named in docs/LIT_NOTES.md. Where only a title is known the text and the table say so."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

# [Work, Approach, Data, Reported result, Limitation]. Only results that were read are quoted; "not stated" otherwise.
LIT_TABLE = [
    ["Feng and Li, 2026 [1] (base paper)", "Six-point EAR and four-point EAR-4 from MediaPipe Face Mesh; head pose by PnP; Whisper-tiny voice; fuzzy belief rule-based fusion; personalised EAR threshold (> 300 frames)", "NTHU-DDD, four subjects, 65,834 frames (29,804 open, 36,030 closed), 80/20 split; Random Forest and XGBoost", "EAR-4 recall 0.894 (Subject 2, Random Forest; six-point EAR 0.856); 25 FPS on a Jetson Orin Nano 8 GB", "Targets drowsiness, not alcohol; split not subject-independent; four subjects"],
    ["Baroutian et al., 2025 [2]", "Facial landmark graph attention network fused with a 3D ResNet by learnable weighting", "202 YouTube videos (101 sober, 101 intoxicated), 3,542 shot clips, subject-independent 80/20 split", "Accuracy 95.82 %, precision 0.977, recall 0.97", "Web-scraped videos, not a controlled study; GPU model; sensitive to neutral expressions"],
    ["Deuber et al., 2026 [3] (preprint)", "Smartwatch accelerometer and heart-rate-variability signals; logistic regression and a two-tower 1D CNN", "Three-arm test-track study, 54 participants, leave-one-subject-out", "AUROC 0.88 (any alcohol), 0.86 (above 0.05 g/dL)", "Needs a worn device; under review; track not road"],
    ["Mehta et al., 2018 [4] (DIF)", "Audio-visual dataset of perceived intoxicated and sober people; CNN video and DNN audio baselines", "Videos gathered from online sources", "Not stated (dataset paper; baselines not read in full)", "Perceived, not measured, intoxication; many source videos no longer reachable [2]"],
    ["Acharya, 2024 [5]", "FLIR ONE thermal camera images; NasNetMobile and MobileNet classifiers", "50 volunteers, four drinking levels, augmented to over 1,200 images", "NasNetMobile 85.10 % (four levels); MobileNet 74.07 % (sober vs drunk)", "Neighbouring levels hard to separate; body temperature; repository record, abstract only"],
    ["Chai et al., 2025 [8]", "Thermal facial patterns; CNN and YOLO features; SVM, MLP, KNN, Random Forest", "Tufts Face Database plus self-collected thermal images", "MLP about 90 % accuracy", "Thermal camera needed; only the abstract was read"],
    ["Deiana et al., 2026 [6]", "Testing methodology for alcohol-intoxication detection systems; controlled intoxication protocols", "Pilot at the IDIADA proving ground, Spain", "Not stated (the abstract gives no numbers)", "A test framework, not a detector"],
    ["Soukupova and Cech, 2016 [9]", "Eye aspect ratio from six landmarks; SVM or hidden Markov model over a short window for blinks", "Three standard blink datasets", "Comparable with the state of the art (no figure read)", "Blink detection, not impairment; uses landmarks from the era's detectors"],
    ["Song et al., 2014 [12] (CEW)", "Eye closeness detection from still images with multi-scale histograms of principal oriented gradients", "2,423 faces: 1,192 eyes closed (Internet), 1,231 eyes open (LFW [13])", "Used here as test data; the paper's own results were not read", "Closed and open faces come from different sources"],
    ["ICOEI 2026 taxi paper [7]", "Title only: alcohol detection with vehicle immobilisation for taxi drivers", "not stated", "not stated (paper could not be located)", "not stated"],
]


def blocks():
    cew = F.CEW
    geo = F.GEO
    b = [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P(f"This chapter reviews the work that shaped the project. It begins with a close reading of the base paper {n(1)}, then groups related work by theme: eye-based drowsiness measures, "
          f"intoxication detection from facial video, from thermal images and from wearables, testing practice and road-safety context, and the datasets and tools used. The batch "
          f"literature survey lists five works; two further papers supplied with the batch folder {n(2, 3)} and the sources behind the eye measures were also read. Where a work was not read "
          "in full the text says so, and where only a title could be found no result is quoted."),
        H2("2.2 Base paper analysis"),
        P(f"**Reference.** {F.BASE_PAPER}"),
        H3("2.2.1 Problem and approach"),
        P("The paper builds an Adaptive Driver Monitoring and Assistance System (ADMAS) that watches for drowsiness, fatigue and distraction. Its premise is that single-signal "
          "monitors fail in real vehicles, and that most work ignores how the driver and the system communicate. It therefore fuses three inputs, the state of the eyes, the pose of the "
          f"head and the driver's voice commands, in a Fuzzy Belief Rule-Based (FBRB) inference engine, a form of belief rule base {n(30)} that can express uncertainty in IF-THEN rules. When the "
          "fuzzy output exceeds a risk threshold the system sounds a buzzer. The target is drowsiness and distraction; alcohol is not mentioned."),
        H3("2.2.2 Eye and head features"),
        P(f"Face landmarks come from the MediaPipe Face Mesh, which returns a mesh of 468 three-dimensional points {n(10, 11)}. The paper uses the conventional six-point eye aspect ratio "
          f"{n(9)} and proposes a modified four-point EAR-4 that uses only the upper eyelid, to cut computation and focus on the lid movement associated with fatigue. Head pose is obtained "
          "from six landmarks and a Perspective-n-Point solution, giving pitch, yaw and roll; pitch and yaw reveal nodding and looking away. The paper adds temporal features, blink duration and "
          "the proportion of sustained low-EAR segments, because an instantaneous EAR value is volatile. In its example trace the EAR stays below 0.18 for about 150 frames to mark a "
          "sustained closure."),
        H3("2.2.3 Calibration and voice"),
        P("Instead of one fixed EAR threshold, the system sets a personalised adaptive threshold for each driver in an initialisation phase that analyses more than 300 frames. The voice "
          f"module uses the Whisper-tiny recogniser {n(29)} with HTDemucs noise suppression and a voice-activity gate for wake words and predefined commands, so that the system can speak to the driver "
          "and accept commands without taking the driver's hands off the controls. The paper reports 0.17 GFLOPs and 37.18 million parameters for Whisper-tiny and 15.24 GFLOPs and 41.98 million "
          "parameters for the denoiser, and a word error rate of 28.8 % for Whisper-tiny on Common Voice 9, which it accepts as a trade-off for speed."),
        H3("2.2.4 Data, evaluation and reported results"),
        P(f"The eye-state experiments use four subjects of the NTHU Driver Drowsiness Detection dataset {n(14)}: 65,834 frames, 29,804 labelled open eyes and 36,030 closed, split 52,666 / 13,168 "
          "(about 80/20) across all subjects. Six-point EAR and EAR-4 are compared with a Random Forest and with XGBoost. EAR-4 improves accuracy, recall and F1 for most subjects; for "
          "Subject 2 with the Random Forest, recall rises from 0.8560 to 0.8940 and F1 from 0.8130 to 0.8452, and the abstract quotes 89.4 % recall. XGBoost generally gives higher recall and "
          "the Random Forest a better balance of precision and recall. The complete system runs on a Jetson Orin Nano (8 GB, 40 TOPS) at 25 frames per second, with the speech work "
          "in a low-priority thread so that it does not disturb the visual loop."),
        H3("2.2.5 Strengths and limits"),
        P("Strengths: personalised calibration, a temporal view of EAR, combination of eye and head cues, and real deployment on an embedded board. Limits, partly stated by the authors: "
          "the data split is a baseline in which the same subjects appear in training and test, subject-independent validation being left to future work; only four subjects are used; the "
          "evaluation is for open versus closed eyes, with drowsiness behaviour shown by example traces rather than by a rider study; and no alcohol-impaired data are involved."),
        H3("2.2.6 What this project takes from it, and where it differs"),
        B("**Taken:** MediaPipe landmarks; the six-point EAR; the idea of a personalised EAR threshold, realised here as 0.72 times the rider's median open-eye EAR over 8 to 15 seconds; "
          "temporal evidence (closure time, closed-eye fraction) instead of a single-frame threshold; a head-posture cue combined with low EAR.",
          "**Different:** plain duration rules with a stated reason replace the fuzzy belief engine; head posture is the image-plane roll angle only, not three-dimensional pose; EAR-4 is not "
          "implemented; there is no voice interface; quality gates and an explicit Unable to assess output are added; the evaluation uses a different dataset (CEW still images) and a laptop CPU "
          "instead of an embedded board. The comparison in Chapter 8 therefore uses the base paper's numbers as context and not as a benchmark."),
        H2("2.3 Related work by theme"),
        H3("A. Eye-based drowsiness measures"),
        P(f"The eye aspect ratio was introduced for blink detection from facial landmarks, classifying blinks from a short window of EAR values with an SVM or a hidden Markov model {n(9)}. "
          f"PERCLOS, the share of time that the eyes are at least 80 % closed, came out of driving-simulator studies in the 1990s, and a 1998 FHWA brief reported it as the most dependable "
          f"alertness indicator among the ocular measures tested {n(15)}. Stern, Boyer and Schroeder reviewed blink rate as a possible measure of fatigue, in particular how it changes with time on task "
          f"{n(16)}. Ji, Zhu and Lan combined visual cues of eyelid movement, gaze, head movement and facial expression in a real-time infrared-camera fatigue monitor with a probabilistic model {n(28)}. YawDD provides yawning video for the same kind of "
          f"driver-state work {n(27)}. These works establish the cues; none of them addresses alcohol."),
        H3("B. Intoxication from facial video"),
        P(f"The DIF dataset gathered audio-visual clips of intoxicated and sober people from online sources and gave CNN and DNN baselines {n(4)}. Its first version used a recurrent network over "
          f"eye gaze, face pose and expression features and found gaze and expression discriminative. The labels are perceived, not measured, intoxication. Baroutian et al. {n(2)} built a new "
          "dataset because many DIF videos were no longer accessible: 202 YouTube videos (101 sober, 101 intoxicated), cut into 3,542 shot-level clips, 1,771 per class, split 80/20 by subject. "
          "A graph attention network over 68 facial landmarks and a 3D ResNet over the frames are fused with a learned weight; the model reaches 95.82 % accuracy with precision 0.977 and recall "
          "0.97, ahead of a customised 3D-CNN (86.7 % in their table) and a VGGFace+LSTM baseline (56.0 %). Their heat-map analysis of the network reports that the model attends to the eyes, mouth and jawline, "
          "that participants showed prolonged eye closure, downward gaze or head tilting, and that missed cases were intoxicated people with neutral expressions and little movement. This is the "
          "closest published work to the batch title, and it supports the use of eye and head behaviour, but it needs a GPU and a trained network."),
        H3("C. Thermal imaging"),
        P(f"Thermal cameras see the skin temperature changes that alcohol causes. Acharya used a FLIR ONE thermal camera with 50 volunteers at four drinking levels and reported 85.10 % accuracy "
          f"with NasNetMobile on the four-level task and 74.07 % with MobileNet for sober versus drunk, noting that neighbouring levels are hard to separate {n(5)}. Chai et al. trained CNN and "
          f"YOLO feature extractors with SVM, MLP, KNN and Random Forest classifiers on the Tufts Face Database and self-collected images, with the MLP reaching about 90 % {n(8)}. Both need a "
          "thermal camera, which ordinary laptops and vehicles lack."),
        H3("D. Wearable sensing"),
        P(f"Deuber et al. studied 54 participants in a randomised, controlled three-arm test-track study and detected alcohol-related driving impairment from a consumer smartwatch's "
          f"accelerometer and heart-rate-variability signals, with a participant-averaged AUROC of 0.88 for any alcohol and 0.86 for driving above 0.05 g/dL under leave-one-subject-out validation {n(3)}. "
          "It is the strongest evidence in this survey because alcohol was administered and measured, but it needs a worn device and is a preprint under review."),
        H3("E. Testing practice, interlocks and road-safety context"),
        P(f"The standardised field sobriety tests used by police include an eye test, horizontal gaze nystagmus {n(18)}; they are applied by a trained officer, not continuously. The World Health "
          f"Organization counts 1.19 million road deaths a year, 21 % of them riders of powered two- and three-wheelers, and notes that only six countries have laws meeting its best practice for all "
          f"risk factors {n(17)}. For automated impairment detection, Deiana et al. describe a testing methodology piloted at a proving ground with controlled intoxication protocols, because developing "
          f"these systems needs data from people who have drunk alcohol and the testing raises safety and ethics issues {n(6)}. The batch survey also lists a taxi alcohol-detection and "
          f"vehicle-immobilisation paper from 2026 {n(7)}; only its title could be found, so nothing is said about its method or results beyond what the title states."),
        H3("F. Landmark tools"),
        P(f"The Face Mesh model produces a dense face mesh from one camera at very high speed on mobile GPUs {n(10)}, and MediaPipe is the framework that packages it {n(11)}. The current Face Landmarker "
          f"task exposes the same family of landmarks to Python {n(24)}. The base paper and this project both rely on it."),
        TAB("Summary of the works compared", ["Work", "Approach", "Data", "Reported result", "Limitation"], LIT_TABLE,
            widths=[1.1, 1.4, 1.3, 1.3, 1.2], size=8),
        H2("2.4 Datasets and algorithms in the literature"),
        TAB("Datasets in the surveyed work and in this project", ["Dataset", "Content", "Used by"], [
            ["NTHU-DDD [14]", "Driver drowsiness videos; the base paper uses four subjects, 65,834 labelled open/closed-eye frames", "[1]"],
            ["YawDD [27]", "Driver yawning videos", "driver-state work [27]"],
            ["DIF [4]", "Audio-visual clips of perceived intoxicated and sober people from online sources; many videos no longer accessible", "[2], [4]"],
            ["YouTube set of [2]", "202 videos (101 sober, 101 intoxicated), 3,542 shot clips, 1,771 per class", "[2]"],
            ["Thermal sets [5], [8]", "FLIR ONE images of 50 volunteers; Tufts Face Database plus self-collected images", "[5], [8]"],
            ["CEW [12] with LFW [13]", f"{cew['closed_images']:,} closed-eye faces from the Internet and {cew['open_images']:,} open-eye faces from LFW, 100 x 100 warped crops", "this project (EAR component only)"],
        ], widths=[1.5, 3.7, 1.1], size=9.5),
        P(f"The methods fall into four families: (i) geometric eye measures from landmarks with thresholds or small classifiers {n(1, 9)}; (ii) deep networks over facial video, with 3D convolutions or "
          f"recurrent layers {n(2, 4)}; (iii) thermal-image classifiers {n(5, 8)}; and (iv) wearable-signal models {n(3)}. Studies report accuracy, precision, recall and F1, often with ROC analysis; "
          f"these measures and their pitfalls are discussed in {n(25, 26)}. Most of them are evaluated on one source of data, and their numbers cannot be compared directly because the data, "
          "the labels and the split differ."),
        H2("2.5 Strengths and limitations of the surveyed work"),
        B("**Strengths:** the eye and head cues are cheap to measure and well understood; landmark detectors run in real time on a laptop; video and wearable studies show that intoxication leaves "
          "measurable traces; one study administered alcohol under control.",
          "**Limitations:** drowsiness work does not address alcohol; intoxication video work uses scraped data and GPU models, and its source dataset has partly disappeared; thermal work needs special "
          "cameras; the wearable study needs a worn device; almost none of it provides a runnable system, quality checks that refuse to guess, or an explanation of each decision."),
        H2("2.6 Research gap"),
        P("The batch survey summarises the gap as: *the surveyed work concentrates on drowsiness and embedded driver-state assessment; the gap is an intoxication-specific vision model coupled to a "
          "prevention action rather than a warning alone.* Reading the literature more closely sharpens it into four points:"),
        N("Eye-closure and head-posture monitors are mature for drowsiness but are not validated for alcohol impairment, and the cues overlap, so a drowsiness monitor cannot tell the cause.",
          "Intoxication-specific video models need labelled data from intoxicated people, which are scarce and, for the best-known public set, partly gone; no open dataset suitable for this team existed.",
          "Published work seldom gives a complete, runnable, explainable path from a webcam frame to a logged warning, with quality checks that refuse to assess in bad conditions.",
          "Coupling impairment detection to a prevention action, as the batch proposes, is rarely studied, and it carries safety risk if the detector is not validated."),
        P("This project addresses point 3 and part of point 1: it builds the complete explainable path with quality gates and measures what can be measured about the eye-closure component. It does "
          "not close points 2 and 4: it has no intoxication data, no trained intoxication model and no prevention action, and Chapters 8 to 10 say so."),
    ]
    return b
