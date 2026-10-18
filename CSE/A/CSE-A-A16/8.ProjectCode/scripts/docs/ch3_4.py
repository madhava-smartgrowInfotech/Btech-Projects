"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB


def blocks():
    return chapter3() + chapter4()


def chapter3():
    lat = F.LAT
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether a project can be built and used with the resources at hand. For SignSpeak the question was answered partly by analysis and partly by "
          "building the system and measuring it, so most entries below carry a measured value rather than an estimate."),

        H2("3.1 Technical Feasibility"),
        P("The technical risk of the project lay in three places: whether a CNN small enough to train on an ordinary CPU could separate 29 classes well enough, whether the whole "
          "recognition chain could run fast enough for live use without a graphics processor, and whether a browser could supply the camera frames reliably to a Python "
          "service. The development machine is a desktop with an Intel Core i5-12500 (6 cores, 12 threads) and 15.7 GB of RAM and no GPU. On that machine:"),
        TAB("Technical feasibility checks and what was measured", ["Question", "Measurement", "Verdict"], [
            ["Can the data be loaded and preprocessed quickly?", f"7,250 images loaded and preprocessed in {F.DS['load_and_preprocess_seconds']:.0f} s", "Feasible"],
            ["Can the CNN be trained on a CPU?", f"about {F.TRAIN_SPEED['seconds_per_epoch']} s per epoch (2-epoch benchmark); the saved run used 30 epochs", "Feasible"],
            ["Is the accuracy useful?", f"{F.pct(F.T['accuracy'], 2)} on a held-out split of {F.T['n']:,} images; {F.pct(F.thr_row(0.75)['accuracy_on_accepted'])} on the frames accepted at threshold 0.75", "Feasible, with a rejection rule"],
            ["Is the chain fast enough?", f"server time {lat['server_side_total_per_frame']['median_ms']:.1f} ms median per frame; HTTP round trip {lat['http_recognize_frame_round_trip']['median_ms']:.1f} ms (about {lat['http_round_trip_fps_sequential']} frames per second)", "Feasible"],
            ["Can a browser feed the service?", "getUserMedia capture, 960 x 540 JPEG of about 27 KB per frame, one request in flight", "Feasible"],
            ["Is the model small enough to ship?", f"{F.MODEL['parameters']:,} parameters, {F.MODEL['file_size_mb']} MB file", "Feasible"],
        ], widths=[2.1, 3.0, 1.2], size=10, align=["l", "l", "l"]),
        P("Where the checks are weakest is generalisation. Because the dataset has no signer identifiers, the technical feasibility of recognition for a new signer or a new "
          "background could not be established, and Chapter 8 reports that gap rather than hiding it. A second, smaller risk is the dependency chain: TensorFlow 2.15 has to be "
          "imported before scikit-learn on Windows, otherwise the native libraries fail to initialise, and the project pins the version and imports in that order."),

        H2("3.2 Economic Feasibility"),
        P("The whole software stack is open source: Python, TensorFlow and Keras, OpenCV, NumPy, scikit-learn, FastAPI, Uvicorn, React, Vite and Tailwind CSS. There is no licence "
          "cost, and no cloud service is needed at run time because the model and the speech engine run locally. The dataset is a public download; it carries a licence "
          "that must be checked on the dataset page before the images are redistributed, since the archive does not bundle it."),
        P("The only hardware requirement is a computer and a webcam. We did not record purchase prices and do not quote cost figures. The recurring cost of running the "
          "system is the electricity of a desktop for the few seconds of training per epoch and the interactive use. Since no data leaves the machine, there is also no per-call "
          "cost and no privacy exposure to a third party."),

        H2("3.3 Operational Feasibility"),
        P("A user starts the whole system with one script, run.bat, which creates the virtual environment on the first run, installs the dependencies, starts the API on port 8316 "
          "and the web interface on port 5316, and opens the browser. The interface has a landing page and six screens (Dashboard, Recognize, Collect, Train, Model, About). "
          "A first-time user can recognise signs immediately if a trained model is present, and can collect their own images and retrain from the same interface if it is not. "
          "Retraining on the 7,250-image working set takes minutes on the development machine."),
        P("Maintenance is simple because the application is a thin layer over the original modules: the API contains no recognition logic and calls the same functions as the desktop "
          "interface, so a fix in preprocessing or in the recogniser reaches both. Operationally, the main requirement is that the signer keeps one hand inside the on-screen box "
          "with a plain background; the interface shows the segmentation mask so that the user can see and correct a poor set-up."),

        H2("3.4 Schedule Feasibility"),
        P("The calendar dates of the work were not recorded in the project artefacts, so we do not give dates. The work was organised in dependent phases, listed in order "
          "with what each produced; the order is the order in which the artefacts exist in the repository."),
        TAB("Project phases and their products", ["Phase", "Work", "Product"], [
            ["1", "Literature survey, base paper study, problem and objectives", "Batch documents 2-6"],
            ["2", "Dataset acquisition, class layout, preprocessing", "preprocessing.py, dataset.py, 7,250-image working set"],
            ["3", "CNN design, training and evaluation", "model.py, train.py, saved model and reports"],
            ["4", "Live recognition, smoothing, sentence and speech", "recognizer.py, tts.py, desktop application"],
            ["5", "API layer and web interface", "backend/ (16 endpoints), frontend/ (landing and six screens)"],
            ["6", "Testing and measurement", f"{F.PYTEST_TOTAL} pytest tests, smoke test, measure_metrics.py"],
            ["7", "Documentation", "Decks, chapter documents, report, paper"],
        ], widths=[0.7, 3.2, 2.4], size=10.5, align=["c", "l", "l"]),

        H2("3.5 Advantages and Constraints"),
        H3("Advantages"),
        B("Runs entirely offline on a normal computer; no cloud account, no GPU and no licence fee.",
          "Fast enough for live use: about 18 frames per second end to end on a CPU.",
          "Transparent: the user sees the segmentation mask, the confidence and the smoothing state, and can retrain the model.",
          "Reproducible: one script regenerates every measurement in this report."),
        H3("Constraints"),
        B("Static letters only; no words and no motion.",
          "Accuracy for new signers and backgrounds is unknown and expected to be lower than the reported figures.",
          "One hand in a fixed on-screen box; sensitivity to rotation of about 10 degrees.",
          "A desktop or laptop is required; mobile deployment was not attempted (the phone-width layout of the interface was checked, but the recogniser runs on the host)."),
    ]


def chapter4():
    lat = F.LAT
    env = F.ENV
    fr = [
        ["FR-1", "Show the live camera in the browser with a box marking the hand region", "getUserMedia capture; ROI 300 x 300 at x 620-920, y 90-390 of a 960 x 540 frame", "Recognize screen"],
        ["FR-2", "Segment the hand and show the mask to the user", "POST /api/preview returns the 128 x 128 mask", "Recognize, Collect"],
        ["FR-3", "Recognise the letter in the box for each frame", "POST /api/recognize/frame; CNN over 29 classes", "Recognize"],
        ["FR-4", "Reject low-confidence frames", "confidence below 0.75 becomes nothing", "recognizer.py"],
        ["FR-5", "Smooth predictions over time", "majority vote over the last 15 frames", "recognizer.py"],
        ["FR-6", "Type a letter only when it is stable", "18 consecutive stable frames, not nothing, different from the last typed letter", "recognizer.py"],
        ["FR-7", "Support space and delete as control signs", "space and del are committed labels", "Recognize"],
        ["FR-8", "Show and edit the sentence, and speak it", "POST /api/tts/speak (2,000-character limit); offline engine with browser fallback", "Recognize"],
        ["FR-9", "Collect new labelled images from the camera", "POST /api/collect/{class}; images saved under data/<class>/", "Collect"],
        ["FR-10", "Show the dataset (counts, thumbnails)", "GET /api/dataset, /api/dataset/{class}/images", "Dashboard, Collect"],
        ["FR-11", "Train the CNN with chosen epochs, batch size and learning rate; stop it; follow progress", "POST /api/train/start, /stop; GET /api/train/status", "Train"],
        ["FR-12", "Show model performance: accuracy, per-class scores, confusion matrix, curves", "GET /api/model", "Model"],
        ["FR-13", "Reload the model after training without restarting", "POST /api/recognize/reload; automatic after a finished run", "Train, Recognize"],
        ["FR-14", "Explain the project", "GET /api/about (abstract, pipeline, base paper)", "About"],
    ]
    nfr = [
        ["NFR-1 Latency", "Server time per frame below 100 ms", f"median {lat['server_side_total_per_frame']['median_ms']:.1f} ms, p95 {lat['server_side_total_per_frame']['p95_ms']:.1f} ms", "Met"],
        ["NFR-2 Throughput", "More than 10 frames per second end to end", f"{lat['http_round_trip_fps_sequential']} frames per second sequential", "Met"],
        ["NFR-3 Accuracy", "Reported on a held-out split with per-class scores", f"{F.pct(F.T['accuracy'], 2)} on {F.T['n']:,} images", "Reported"],
        ["NFR-4 Reliability of typing", "Typed letters should be mostly right", f"{F.pct(F.thr_row(0.75)['accuracy_on_accepted'])} on accepted frames at 0.75", "Met by the rule"],
        ["NFR-5 Robustness", "Tolerate lighting, noise and blur", f"clean {F.pct(F.ROB['clean'])}; noise s=25 {F.pct(F.ROB['gaussian noise s=25'])}; blur {F.pct(F.ROB['blur 5x5'])}; rotation +/-10 deg about {F.pct(F.ROB['rotate +10 deg'], 0)}", "Partly met"],
        ["NFR-6 Input validation", "Bad input returns a clear error and changes nothing", "400, 404, 409 responses; epochs 1-500, batch 1-1,024, learning rate 1e-6 to 1", "Met (tested)"],
        ["NFR-7 Usability", "Usable by a non-expert; readable at phone width", "one start script; screens checked at 360, 768 and 1,440 px, light and dark", "Met"],
        ["NFR-8 Portability", "Runs on a normal Windows PC", "Python 3.11, TensorFlow 2.15 CPU; run.bat", "Met on Windows only"],
        ["NFR-9 Maintainability", "No logic duplicated between desktop and web", "API calls the same modules as the desktop GUI", "Met"],
        ["NFR-10 Testability", "Automated tests", f"{F.PYTEST_TOTAL} pytest tests; {F.SMOKE_TOTAL}-check smoke test", "Met"],
    ]
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),

        H2("4.1 Existing System and Its Limitations"),
        P("Today a deaf or hard-of-hearing person who needs to communicate with a hearing person who does not sign relies on a human interpreter, on writing, or on lip reading. "
          "Interpreters are scarce and costly, and are rarely available for the everyday, spontaneous exchange. Writing and typing are slow compared with signing and exclude "
          "people for whom the written language is a second language."),
        P("On the technical side, research systems exist for each part of the problem [2], [3]: depth-camera fingerspelling readers [5], CNN classifiers trained on alphabet "
          "images [6], and video and skeleton recognisers for words [1], [14], [15]. Their limitations, as the survey in Chapter 2 shows, are that they usually stop at a trained "
          "model, are not packaged for a user, need special sensors or heavy computation, and seldom report latency, a rejection rule or the effect of rotation and lighting."),
        P("The project began from an earlier desktop application, written with customtkinter, which already contained the preprocessing, training and recognition modules. It "
          "was usable only on the machine it ran on, had a single window, and had no measurement tooling. That application is kept unchanged and is the basis of the web system."),

        H2("4.2 Proposed System and Its Advantages"),
        P("SignSpeak keeps the desktop modules and adds a service layer and a web interface. In the browser the user sees the camera with a hand box, the segmentation mask and the "
          "recognised letter; the sentence appears below and can be spoken. The same interface lets the user collect images, start and watch a training run, and inspect the "
          "resulting model. The processing is identical to the desktop application because the API calls the same functions."),
        B("Complete: camera to speech in one tool, with data collection, training and evaluation in the same place.",
          "Trustworthy output: a confidence threshold, a majority vote and a stable-frame rule decide when a letter is typed.",
          "Measured: accuracy, per-class scores, confusion matrix, threshold trade-off, robustness and latency are produced by a script and shown in the interface.",
          "Private and free: it runs locally, with no cloud dependency or licence cost.",
          "Extensible: a new class or a new signer's images can be added by collecting and retraining."),

        H2("4.3 Functional Requirements"),
        TAB("Functional requirements and how they are realised", ["ID", "Requirement", "Realisation in SignSpeak", "Where"], fr,
            widths=[0.55, 2.2, 2.5, 1.05], size=9.5, align=["c", "l", "l", "l"]),

        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements and the measured outcome", ["Requirement", "Target", "Measured / evidence", "Status"], nfr,
            widths=[1.2, 1.9, 2.5, 0.7], size=9.5, align=["l", "l", "l", "c"]),
        P("The accuracy requirement is stated as a reporting requirement, not as a target number: the dataset carries no signer identifiers, so a target such as \"95 % for any signer\" "
          "could not be tested honestly."),

        H2("4.5 Hardware Requirements"),
        P("The system was developed and measured on one machine; we report its specification rather than an invented minimum. A smaller machine may work but was not tested."),
        TAB("Hardware used for development and measurement", ["Item", "Specification"], [
            ["Processor", env["cpu"]],
            ["Memory", f"{env['ram_gb']} GB RAM"],
            ["Graphics processor", "none used (CPU-only TensorFlow)"],
            ["Camera", "a webcam is required for live use; the build-machine tests used Chromium's fake camera"],
            ["Storage", f"model file {F.MODEL['file_size_mb']} MB; working set of 7,250 images; the full archive is 87,000 images"],
            ["Operating system", "Windows 11 (Windows-10.0.26200)"],
        ], widths=[1.7, 4.6], size=10.5, align=["l", "l"]),

        H2("4.6 Software Requirements"),
        TAB("Software used", ["Component", "Version / package", "Role"], [
            ["Python", env["python"], "language of the recogniser and the API"],
            ["TensorFlow / Keras", env["tensorflow"], "CNN definition, training, inference [23], [26]"],
            ["OpenCV", env["opencv"], "image decoding, thresholding, morphology [24]"],
            ["NumPy", env["numpy"], "array computation"],
            ["scikit-learn", "latest compatible", "split, metrics"],
            ["FastAPI and Uvicorn", "latest compatible", "web service, 16 endpoints [27]"],
            ["customtkinter, pyttsx3", "latest compatible", "desktop interface; offline speech"],
            ["Node.js toolchain", "Vite 8, TypeScript 5.9", "build of the web interface"],
            ["React and routing", "React 18.3, React Router 7", "web interface"],
            ["Tailwind CSS", "4.x", "styling"],
            ["TanStack Query, Recharts", "5.x, 3.x", "data fetching, charts"],
            ["pytest, Playwright", "installed in the environment", "tests, screenshots"],
        ], widths=[1.8, 1.9, 2.6], size=10.5, align=["l", "l", "l"]),

        H2("4.7 User Roles"),
        P("The system has a single role: the local user, who may be the signer or a helper. There are no accounts, passwords or permissions, because the application runs on the "
          "user's own computer and serves only that computer. The consequence is that anyone with access to the machine can collect images, retrain the model and replace it; "
          "multi-user operation would need authentication and is listed under future scope."),

        H2("4.8 Constraints and Assumptions"),
        N("The signer shows one hand inside the on-screen box; two-handed signs are out of scope.",
          "The background behind the hand is plain and the lighting is ordinary indoor lighting; Otsu thresholding does not isolate a hand on a cluttered background.",
          "Only the static letters, the two control signs and the empty state are recognised; J and Z are read from one frame.",
          "The training data are the public ASL Alphabet frames or images the user collects; they have no signer labels, so generalisation to a new signer is not guaranteed.",
          "TensorFlow is imported before scikit-learn, as required by the Windows native libraries."),
    ]
