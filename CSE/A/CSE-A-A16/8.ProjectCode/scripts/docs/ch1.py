"""Chapter 1: Introduction."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, N, P, TAB


def blocks():
    t = F.T
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P("This chapter introduces the domain of the project, the motivation for building SignSpeak, the problem it addresses, the objectives set for it, the scope that "
          "was actually delivered, the contributions, and the limitations and assumptions that govern every result reported later. It closes with a map of the rest of the report."),

        H2("1.1 Domain and Background"),
        P("Sign languages are complete natural languages that use the shape, position and movement of the hands, together with the face and body, to carry meaning. For many "
          "people with hearing or speech impairment a sign language is the primary means of communication, and it is the way they take part in family life, education and "
          "work. Most hearing people, however, never learn a sign language, so a signer who has no interpreter at hand meets a communication barrier in ordinary "
          "situations such as a shop counter, a bank queue or a clinic reception [2], [3]."),
        P("Sign language recognition (SLR) is the branch of computer vision that tries to remove this barrier automatically: a camera observes the signer and software "
          "turns the signs into text or speech. Research covers three levels of difficulty [3]. The first is isolated static signs, such as the hand shapes of the manual "
          "alphabet. The second is isolated dynamic signs, usually whole words, which need the motion of the hands over time. The third is continuous signing and its "
          "translation into sentences of a spoken language [16]. Static recognition is the simplest of the three, but it is also the part that cannot be avoided: names, "
          "places and technical terms that have no established sign are spelled out letter by letter with the manual alphabet, called fingerspelling."),
        P("This project works at the first level. American Sign Language (ASL) has a manual alphabet of 26 letters, of which 24 are static hand shapes and two (J and Z) "
          "are traced in the air. SignSpeak recognises the 26 letters plus three control signs (space, delete and an empty-hand state called nothing) from a live webcam, "
          "assembles the letters into a sentence on screen and can read the sentence aloud. The recogniser is a convolutional neural network (CNN), a model family that has "
          "been the standard tool for image classification since the work of LeCun et al. [7] and the large-scale results of Krizhevsky et al. [8]."),

        H2("1.2 Motivation"),
        P("Three observations motivate the project. First, a human interpreter is not available for every conversation: interpreters are scarce and costly, and everyday "
          "spontaneous interaction cannot be scheduled in advance. A tool that runs on an ordinary computer with a webcam can cover the many short exchanges for which an "
          "interpreter is out of proportion."),
        P("Second, the manual alphabet is a practical entry point. A recogniser that reads fingerspelling can already help a signer say a name or a word that has no sign, "
          "and it can be trained from a modest number of labelled images, in contrast to word-level video recognition that needs large video corpora [14], [15]. "
          "The base paper chosen for this batch, MAG-KD [1], targets the harder video-based problem on edge devices; its concern with real-time operation on modest hardware is "
          "shared by SignSpeak, which also aims to run live without a graphics processor."),
        P("Third, published systems often stop at a trained model and an accuracy number in a notebook. A working application - one that captures the camera, shows what the "
          "model sees, lets a user collect new images, retrain, inspect the results and hear the output - is what turns a classifier into an assistive tool. The team "
          "therefore decided to deliver the whole chain from camera to speech and to measure each link honestly."),

        H2("1.3 Problem Statement"),
        P(lit.PROBLEM_STATEMENT),
        P("The project's own problem analysis lists four difficulties that the design must respect:"),
        B(*lit.PROBLEM_POINTS),

        H2("1.4 Need for the Project"),
        P("A usable recogniser has to satisfy several needs at once, and existing work tends to satisfy only some of them. It must be fast enough to follow a signer, which means "
          "a response of a few tens of milliseconds per frame and a frame rate of more than ten per second. It must be accurate enough that a typed letter can be trusted, which "
          "requires both a good classifier and a rule that refuses to type when the classifier is unsure. It must be robust to ordinary changes in lighting and background, and "
          "it must be usable by a person who is not a machine-learning engineer. Finally, it must be reproducible: the dataset, the preprocessing, the training run and the "
          "measurements have to be inspectable and repeatable."),
        P("The survey of the literature in Chapter 2 shows that the field has moved towards skeleton-based and knowledge-distillation methods for accuracy and efficiency [1], "
          "while the gap named in the batch survey is an accessible end-to-end system that recognises signs live and renders them as both text and speech. SignSpeak is built to "
          "close that gap for the fingerspelling case, and to report plainly where it does not."),

        H2("1.5 Objectives"),
        P("The six objectives approved for the project are:"),
        N(*lit.OBJECTIVES),
        P("Chapter 8 measures each objective against the outcome. In short, objectives 2, 3 and 5 were met, objectives 4 and 6 only in part and objective 1 only for the "
          "alphabet: the recogniser covers letters and control signs, not common words, and no evaluation on signers who were absent from the training data could be made, "
          "because the dataset carries no signer identifiers."),

        H2("1.6 Scope"),
        P("In scope are the following items, all of which exist in the delivered code base:"),
        B("a dataset of 29 classes (A-Z, space, del, nothing): a working set of 7,250 images drawn from the public Kaggle ASL Alphabet archive [25], plus in-application collection of new images from the webcam;",
          "a preprocessing pipeline of region-of-interest cropping, grayscale conversion, Gaussian blur, Otsu thresholding [17], morphological clean-up and resizing to 64 x 64 pixels;",
          f"a three-block CNN with {F.MODEL['parameters']:,} parameters, trained with augmentation and evaluated on a held-out split;",
          "live recognition with confidence thresholding, majority-vote smoothing and a stable-frame rule that decides when a letter is typed;",
          "a sentence builder and speech output (an offline engine on the host with a browser-voice fallback);",
          "a FastAPI service with 16 endpoints and a React web interface with a landing page and six application screens, in addition to the original desktop application;",
          f"{F.PYTEST_TOTAL} automated tests, a {F.SMOKE_TOTAL}-check smoke test and a measurement script that regenerates every number in this report."),
        P("Out of scope are word-level and sentence-level recognition, the motion letters J and Z as motion (they are read from a single frame), two-handed or two-way translation, "
          "mobile deployment, user accounts and a clinical or educational field trial."),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow of SignSpeak from the camera to the spoken sentence.", 5.6),

        H2("1.7 Contributions"),
        P("The contributions of the work are practical and are stated at the level the evidence supports:"),
        N("An end-to-end, runnable system for ASL fingerspelling - camera, segmentation, CNN, smoothing, sentence builder and speech - in two forms that share one code path: "
          "a desktop application and a web application.",
          f"A measured baseline for a compact CNN on this task: {F.pct(t['accuracy'], 2)} accuracy, macro F1 {F.f3(t['macro_f1'])} and top-3 accuracy {F.pct(t['top3_accuracy'])} on a held-out "
          f"split of {t['n']:,} images, with per-class scores, a confusion matrix and the most frequent confusions.",
          f"A quantified accept-or-reject rule: at the confidence threshold of 0.75 the system accepts {F.pct(F.thr_row(0.75)['coverage'])} of frames and is right on "
          f"{F.pct(F.thr_row(0.75)['accuracy_on_accepted'])} of those, which is what makes typed output trustworthy.",
          f"Measured latency on a CPU-only machine: a median of {F.LAT['server_side_total_per_frame']['median_ms']:.1f} ms per frame on the server and "
          f"{F.LAT['http_recognize_frame_round_trip']['median_ms']:.1f} ms over HTTP (about {F.LAT['http_round_trip_fps_sequential']} frames per second).",
          "A robustness study (brightness, noise, blur and rotation) and a frank analysis of the dataset's near-duplicate frames, so that readers know which numbers are optimistic.",
          "Complete documentation and a verification script that checks the documents against the code and the measurements."),

        H2("1.8 Limitations and Assumptions"),
        P("The main limitations are stated here once and repeated where they matter:"),
        B("The dataset is made of frames taken from video of a few recordings; neighbouring frames are near-duplicates and no signer identifier is given. The held-out split is "
          "therefore a random split of the same recordings and is not an unseen-signer test.",
          "The Otsu mask often contains background structure, so the CNN partly learns the scene; accuracy on a new background or a new signer is expected to be lower than reported.",
          f"The model is sensitive to hand orientation: a rotation of 10 degrees lowers accuracy from {F.pct(F.ROB['clean'])} to about {F.pct(F.ROB['rotate +10 deg'], 0)}.",
          "Only static letters are recognised; there is no word vocabulary and no motion modelling.",
          "The end-to-end browser test used Chromium's fake camera fed with real photographs; the live webcam path was not exercised on a physical camera on the build machine."),
        P("The assumptions are that the signer shows a single hand inside the on-screen box, that the lighting is ordinary indoor lighting, that the background behind the hand is "
          "plain, and that the user runs the system on a personal computer with a webcam. The system is a research and teaching prototype and is not a certified assistive device."),

        H2("1.9 Organisation of the Report"),
        TAB("Organisation of the report", ["Chapter", "Title", "Content"], [
            ["1", "Introduction", "Domain, motivation, problem, objectives, scope, contributions, limitations"],
            ["2", "Literature Survey", "Base paper analysis, related work by theme, datasets and algorithms, research gap"],
            ["3", "Feasibility Study", "Technical, economic, operational and schedule feasibility"],
            ["4", "System Requirements and Analysis", "Existing and proposed system, functional and non-functional requirements, environment"],
            ["5", "System Design", "Architecture, workflow, data-flow diagrams, UML, storage design, modules, interface"],
            ["6", "Methodology and Software Implementation", "Dataset, preprocessing, CNN, training, decision logic, API, security, installation"],
            ["7", "System Testing", "Strategy and results of unit, integration, functional, security and performance tests"],
            ["8", "Results and Output Screens", "Measured results, comparison with the base paper, screens, failures, objectives versus outcome"],
            ["9", "Conclusion", "Summary, findings, applications, known limitations"],
            ["10", "Future Scope", "Improvements, features, scalability, research directions"],
        ], widths=[0.7, 2.2, 3.3], align=["c", "l", "l"]),
        P("References and three appendices (important code, installation and user guide, additional screens) follow Chapter 10."),
    ]
