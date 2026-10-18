"""Chapter 5: System Design. Also holds DIAGRAMS, the list used by 11. BLOCK DIAGRAMS ALL.docx."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB

# (key, title, file, caption, explanatory paragraph(s))
DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "System architecture of SignSpeak: presentation, application and domain tiers with the two file stores.",
     "The system has three tiers over two stores. The presentation tier is a React 18 + TypeScript application served by Vite on port 5316; it owns the webcam through "
     "the browser's `getUserMedia` call, cover-crops each frame to 16:9, mirrors it and uploads it as a 960x540 JPEG. The application tier is a thin FastAPI service on port 8316 "
     "(`backend/`): 16 endpoints under `/api`, a store of at most 20 recognition sessions, one lock around the Keras model and a background training thread. The domain tier is the original "
     "desktop application's package `sign_language_app` (preprocessing, model, dataset, train, recognizer, tts, config), reused unchanged, so the web and desktop versions cannot drift apart. "
     "Training images are kept in `data/<CLASS>/` and the trained model with its reports in `models/`. There is no SQL database."),
    ("workflow", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow from image collection to spoken sentence.",
     "The workflow has two halves. The offline half gathers labelled hand images (own captures in the Collect screen or the public ASL Alphabet set), preprocesses them with the same pipeline used at "
     "run time, trains the CNN with augmentation and early stopping, evaluates it on a held-out split and stores the model with its reports. The online half starts the camera, sends frames to "
     "the recogniser, smooths the predictions, appends a letter to the sentence when a sign has been held steadily, and speaks the sentence on request. Training and recognition share one "
     "preprocessing function, which removes a common source of train/serve mismatch."),
    ("dfd0", "Data flow diagram, level 0 (context)", "03_dfd_level0.png",
     "Level 0 data flow diagram: SignSpeak as a single process with four external entities.",
     "At the context level SignSpeak is one process. The user supplies class choices, hyper-parameters and commands and receives letters, the sentence, charts, reports and status "
     "messages. The browser webcam supplies video frames. A sample-image source (the user's own captures or the public ASL Alphabet images) supplies labelled hand images. The speaker receives synthesised speech."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "Level 1 data flow diagram: five processes and three data stores.",
     "Level 1 splits the system into five processes: 1.0 Collect samples (frames in, images to store D1), 2.0 Train model (images from D1, hyper-parameters from the user; writes the model "
     "to D2 and history, report and confusion matrix to D3), 3.0 Recognise signs (frames and the model in; letters and the sentence out), 4.0 Speak sentence (text to the speaker) and 5.0 Report model "
     "(history and report from D3, model information from D2, charts to the user). D1 is the image dataset, D2 the model files and D3 the training logs. The user appears twice only to keep the arrows from crossing."),
    ("dfd2", "Data flow diagram, level 2 (process 3.0)", "05_dfd_level2.png",
     "Level 2 data flow diagram: the six steps inside process 3.0, Recognise signs.",
     "Process 3.0 expands into six steps that mirror `SignRecognizer.predict_frame`: 3.1 decode the JPEG frame, 3.2 crop the 300x300 region of interest, 3.3 segment the hand "
     "(grayscale, blur, Otsu threshold, morphology), 3.4 normalise to a 64x64 tensor, 3.5 classify with the CNN loaded once from D2, and 3.6 smooth the result with the session's history of 15 "
     "votes and decide whether to commit a letter. The result returned to the browser holds the label, its confidence, the stable label, the committed letter and the mask image."),
    ("class", "UML class diagram", "06_class_diagram.png",
     "UML class diagram of the main classes and modules.",
     "The code base is mostly modules of functions, so the diagram shows the real classes and the modules they use. `backend.main` owns one base `SignRecognizer` (which holds the Keras "
     "model), up to 20 per-session recognisers that share its model and labels, a model lock and a `TrainJob`. `TrainJob` runs `train_model` on a thread; the training code loads a `Dataset` "
     "dataclass (train, validation and test arrays plus the label list) and attaches a `StreamingCallback` that forwards each epoch's metrics and honours the stop flag. "
     "`SignRecognizer` uses the `preprocessing` module and reads thresholds from `config`."),
    ("seq", "Sequence diagram: live recognition", "07_sequence_recognition.png",
     "Sequence diagram of live recognition and speech.",
     "The user starts the camera; the React page obtains the stream, opens a recognition session (steps 1-4) and then loops: grab a frame, post it, crop and preprocess it on the server, run the CNN, apply "
     "the threshold, vote and stable count, and return the result (steps 5-14). Only one request is in flight at a time and requests are at least 60 ms apart, so the loop cannot flood the server. "
     "Pressing Speak posts the sentence to `/api/tts/speak`, which starts the offline voice on a daemon thread (steps 15-18)."),
    ("uc", "Use case diagram", "08_use_case.png",
     "Use case diagram: eight use cases, one human actor and two system actors.",
     "The user can start and stop the camera (UC1), recognise signs live (UC2), build a sentence with space, back and clear (UC3), speak it (UC4), collect samples singly or in bursts (UC5), train a "
     "model with chosen hyper-parameters (UC6), view model performance (UC7) and read about the project (UC8). UC2 and UC5 include UC1 because the camera must be running. The webcam "
     "(through the browser) and the speaker (the server voice) are the system actors. There are no accounts or roles."),
    ("er", "Entity-relationship diagram (file store)", "09_er_diagram.png",
     "Entity-relationship diagram of the file-system data model; SignSpeak has no SQL database.",
     "SignSpeak stores no records in a database. The data model is the file system: a class folder (one of 29) holds many image files; images are read by a training run; a run produces one model "
     "artefact (the Keras file, `labels.json` and the reports); a recognition session, kept only in memory, uses the model artefact and yields transient per-frame predictions. The diagram is drawn "
     "in entity-relationship style so that the relationships are explicit, but every `PK` is a file or folder name rather than a table key."),
    ("flow", "Flowchart of the core algorithm", "10_core_algorithm_flowchart.png",
     "Flowchart of the core algorithm: (A) image pipeline and (B) decision logic.",
     "Part A is the image pipeline: decode, crop, grayscale and blur, Otsu threshold, inversion when more than half the mask is white, morphological opening and closing, resize to 64x64, "
     "scaling and the CNN forward pass. Part B is the decision logic: a prediction below 0.75 confidence is replaced by `nothing`; the result joins a history of the last 15; the majority label "
     "is compared with the stable label and a counter is kept; a letter is committed when the counter reaches 18, the majority is not `nothing` and it differs from the last committed letter. "
     "A majority of `nothing` re-arms the repeat guard so that the same letter can be typed twice after the hand has been lowered."),
    ("cnn", "CNN architecture", "11_cnn_architecture.png",
     "CNN architecture: three convolution blocks and a dense head (2,199,453 parameters).",
     "The network takes a 64x64x1 mask. Block 1 is a 3x3 convolution with 32 filters, batch normalisation and 2x2 max pooling; block 2 doubles the filters to 64 and adds dropout 0.25; block 3 "
     "uses 128 filters with dropout 0.25. The 8x8x128 map is flattened to 8,192 values, passed through a dense layer of 256 units with batch normalisation and dropout 0.4, and a softmax layer of 29 units."),
    ("train", "Training pipeline", "12_training_pipeline.png",
     "Training pipeline: load and preprocess, split, augment, fit with early stopping, evaluate, save.",
     "All images in `data/` are preprocessed once and cached in memory, then split 70/15/15 with a stratified split and seed 42. The training set is augmented on the fly "
     "(rotation 12 degrees, shifts 10 %, zoom 12 %, shear 8 %). Adam with learning rate 1e-3 minimises categorical cross-entropy; early stopping watches validation accuracy (patience 6, best weights restored) and "
     "the best model is checkpointed. After training the held-out test split gives the accuracy, the classification report and the confusion matrix, which are written next to the model."),
]


def _dg(key):
    for k, t, f, c, x in DIAGRAMS:
        if k == key:
            return t, f, c, x
    raise KeyError(key)


def _fig_text(key, width=5.6, with_text=True):
    t, f, c, x = _dg(key)
    out = [FIG(F.diag(f), c, width)]
    if with_text:
        out.append(P(x))
    return out


ENDPOINTS = [
    ["GET", "/api/health", "Liveness: status, model_loaded, model_file, training_state", "-"],
    ["GET", "/api/config", "Classes, frame size, ROI box, image size, thresholds, training defaults", "-"],
    ["GET", "/api/about", "Abstract, pipeline steps, base paper", "-"],
    ["GET", "/api/dataset", "Image count per class, total, trainable classes, ready_to_train", "-"],
    ["GET", "/api/dataset/{cls}/images", "Newest images of a class (limit 1-200)", "404 unknown class"],
    ["GET", "/api/dataset/{cls}/images/{name}", "One stored image file", "400 bad name, 404 unknown"],
    ["POST", "/api/preview", "Segmentation mask of the ROI of an uploaded frame", "400 empty / undecodable"],
    ["POST", "/api/collect/{cls}", "Save the ROI as a 200x200 PNG; returns count and mask", "404, 400"],
    ["POST", "/api/recognize/session", "Open a recognition session (at most 20 kept)", "-"],
    ["POST", "/api/recognize/frame", "Predict one frame: label, confidence, stable label, committed letter, mask", "409 no model, 404 session, 400"],
    ["POST", "/api/recognize/reload", "Reload the model from disk", "404 no model"],
    ["POST", "/api/tts/speak", "Speak text on the server (offline voice)", "400 empty or over 2,000 characters"],
    ["POST", "/api/train/start", "Start training with epochs, batch size, learning rate", "400 out of range, 409 busy / < 2 classes"],
    ["POST", "/api/train/stop", "Request an early stop", "-"],
    ["GET", "/api/train/status", "State, epoch, history and summary of the training job", "-"],
    ["GET", "/api/model", "Test accuracy and loss, per-class report, history, confusion matrix", "200 with trained = false when none"],
]

MODULES = [
    ["config.py", "69", "Paths, class list, image and ROI sizes, camera size, smoothing thresholds, training defaults", "`CLASSES`, `IMG_SIZE`, `CONFIDENCE_THRESHOLD`"],
    ["preprocessing.py", "102", "ROI box and crop, blur, Otsu and skin segmentation, normalisation", "`segment_hand`, `normalize_for_model`, `preprocess_roi`"],
    ["dataset.py", "109", "Class counts, loading and preprocessing images, 70/15/15 stratified split, label file", "`load_dataset`, `class_counts`"],
    ["model.py", "50", "The CNN architecture and its compilation", "`build_cnn`"],
    ["train.py", "121", "Augmentation, callbacks, fitting, evaluation, report and history files", "`train_model`, `StreamingCallback`"],
    ["recognizer.py", "86", "Model wrapper with confidence threshold, voting and auto-commit", "`SignRecognizer.predict_frame`"],
    ["tts.py", "31", "Offline speech on a short-lived engine thread", "`speak_async`"],
    ["camera.py, gui/ (desktop)", "60 + 1,019", "Threaded OpenCV camera and the customtkinter desktop interface (kept, not used by the web app)", "-"],
    ["backend/main.py", "367", "The 16 API endpoints, session store, model lock, report parsing", "`recognize_frame`, `collect`, `model_info`"],
    ["backend/train_job.py", "108", "Background training thread with a lock-guarded progress dictionary", "`TrainJob`"],
    ["backend/content.py", "55", "Text for the About screen (abstract, pipeline, base paper)", "-"],
    ["frontend/src", "5,268", "Seven pages, camera hook, data layer, charts, UI kit", "`Recognize.tsx`, `lib/camera.ts`, `lib/api.ts`"],
]

STORAGE = [
    ["`data/<CLASS>/*.png|jpg`", "Training images, 29 folders (A-Z, space, del, nothing)", "PNG 200x200 colour (own captures); JPEG 200x200 (public set)"],
    ["`models/asl_cnn_model.keras`", "Trained network (26.48 MB)", "Keras native format"],
    ["`models/labels.json`", "Class order used by the network output", "JSON list of 29 strings"],
    ["`models/training_history.json`", "Per-epoch loss and accuracy (train and validation)", "JSON, four lists"],
    ["`models/classification_report.txt`", "Test accuracy, test loss and per-class precision/recall/F1", "Text"],
    ["`models/confusion_matrix.json`", "Labels and the 29x29 test confusion matrix", "JSON"],
    ["Recognition sessions", "History of 15 votes, stable label and count, last committed letter", "In memory only, at most 20, lost on restart"],
]

SCREENS = [
    ["Landing", "/", "Pitch, how it works, live pipeline preview, call to action"],
    ["Dashboard", "/app", "Model status, image count, classes covered, accuracy, images per class, last run"],
    ["Recognize", "/app/recognize", "Camera, live letter and confidence, mask preview, sentence builder, speak"],
    ["Collect", "/app/collect", "Camera with ROI box, class picker, single and burst capture, recent images"],
    ["Train", "/app/train", "Dataset coverage, hyper-parameters, progress, live accuracy and loss charts"],
    ["Model", "/app/model", "Test accuracy, per-class table, confusion matrix, training curves"],
    ["About", "/app/about", "Abstract, pipeline steps and the base paper"],
]


def blocks():
    b = [H1("CHAPTER 5: SYSTEM DESIGN")]
    b += [H2("5.1 Design goals"),
          P("The design follows from the requirements of Chapter 4. It must (i) run the same preprocessing and model for collection, training and recognition; (ii) keep the heavy work "
            "(TensorFlow) in one process and the camera in the browser so that no native camera code is needed; (iii) respond fast enough for a signer to see a letter within a fraction of a second; "
            "(iv) work offline on one Windows PC with no GPU; and (v) leave the original desktop application untouched so that the web version is an addition and not a rewrite."),
          B("**Reuse over rewrite.** The FastAPI layer contains no recognition or training logic; every endpoint calls a function of `sign_language_app`.",
            "**Stateless where possible.** Only the recognition session (the smoothing history) and the training job carry state; everything else is read from files.",
            "**Fail loudly and politely.** Every endpoint validates its input and returns a clear message with a 4xx code instead of a stack trace.",
            "**Honest numbers.** The Model screen shows the true held-out accuracy of the saved model, not a figure typed into the interface.")]
    b += [H2("5.2 System architecture")] + _fig_text("arch", 5.2)
    b += [P("The browser-to-server contract is deliberately narrow: JSON for control and results, multipart JPEG for frames. In development the Vite server proxies `/api` to port 8316, so the "
            "interface never needs to know the API's address and CORS is not exercised; the API nevertheless allows cross-origin calls for other front ends.")]
    b += [H2("5.3 High-level workflow")] + _fig_text("workflow")
    b += [H2("5.4 Data flow diagrams"), H3("5.4.1 Level 0")] + _fig_text("dfd0", 4.8)
    b += [H3("5.4.2 Level 1")] + _fig_text("dfd1", 4.7)
    b += [H3("5.4.3 Level 2: recognising signs")] + _fig_text("dfd2", 5.6)
    b += [H2("5.5 UML diagrams"), H3("5.5.1 Class diagram")] + _fig_text("class", 5.0)
    b += [H3("5.5.2 Sequence diagram")] + _fig_text("seq", 4.2)
    b += [H3("5.5.3 Use case diagram")] + _fig_text("uc", 4.1)
    b += [H2("5.6 Database design"),
          P("A design chapter normally describes a database, so we state it plainly: SignSpeak has no SQL database. The reasons are practical. The only persistent data are image files and a "
            "model, both of which are naturally files; the user is single and local; and the session history is a transient 15-element queue. Adding a database would have added a dependency without adding a capability. "
            "The data model is therefore the file layout listed in the table below, drawn as an entity-relationship diagram after it."),
          TAB("Persistent and in-memory data of SignSpeak", ["Location", "Content", "Format"], STORAGE, widths=[2.0, 2.6, 2.0], align=["l", "l", "l"], size=10)]
    b += _fig_text("er", 5.0)
    b += [H2("5.7 Module design"),
          P("The table below lists the modules with their sizes (lines of code, measured with `wc -l`) and responsibilities. The desktop package is 1,648 lines, the API layer 530 lines, the web interface 5,268 lines "
            "of TypeScript and the test suite 398 lines."),
          TAB("Module breakdown", ["Module", "Lines", "Responsibility", "Key names"], MODULES, widths=[1.45, 0.6, 2.9, 1.65], align=["l", "c", "l", "l"], size=9.5)]
    b += [H2("5.8 Algorithm design"), H3("5.8.1 Core algorithm")] + _fig_text("flow", 4.0)
    b += [H3("5.8.2 Network architecture")] + _fig_text("cnn", 5.6)
    b += [TAB("Layers of the network", ["Layer", "Output shape", "Parameters"],
              [["Input", "64 x 64 x 1", "0"], ["Conv2D 3x3, 32, ReLU", "64 x 64 x 32", "320"], ["BatchNormalization", "64 x 64 x 32", "128"], ["MaxPooling 2x2", "32 x 32 x 32", "0"],
               ["Conv2D 3x3, 64, ReLU", "32 x 32 x 64", "18,496"], ["BatchNormalization", "32 x 32 x 64", "256"], ["MaxPooling 2x2 + Dropout 0.25", "16 x 16 x 64", "0"],
               ["Conv2D 3x3, 128, ReLU", "16 x 16 x 128", "73,856"], ["BatchNormalization", "16 x 16 x 128", "512"], ["MaxPooling 2x2 + Dropout 0.25", "8 x 8 x 128", "0"],
               ["Flatten", "8,192", "0"], ["Dense 256, ReLU", "256", "2,097,408"], ["BatchNormalization + Dropout 0.4", "256", "1,024"], ["Dense 29, softmax", "29", "7,453"],
               ["**Total**", "", "**2,199,453**"]],
              widths=[2.8, 1.6, 1.4], align=["l", "c", "r"], size=10),
          P("Of the 2,199,453 parameters, 960 are the non-trainable moving statistics of the four batch-normalisation layers. The dense layer after the flatten holds 2,097,408 of them (95 %), which is why "
            "the model file is 26.48 MB although the network is only three convolution blocks deep.")]
    b += [H3("5.8.3 Training pipeline")] + _fig_text("train", 5.6)
    b += [H2("5.9 API design"),
          P("The API is a JSON/REST interface under `/api`, documented automatically at `/docs` (Swagger UI). The table below lists all 16 endpoints. Frames travel as multipart form data (field `frame`, plus `session_id` for "
            "recognition) because that avoids base-64 inflation of the JPEG; masks come back as small PNG data URLs. Errors are always `{\"detail\": \"message\"}` with a status code, which the interface shows in a toast."),
          TAB("The 16 endpoints", ["Method", "Path", "Purpose", "Errors"], ENDPOINTS, widths=[0.6, 1.9, 2.6, 1.5], align=["c", "l", "l", "l"], size=9)]
    b += [H2("5.10 User interface design"),
          P("The interface is a single-page React application with a landing page and six working screens (table below). It follows one design system (dark and light themes, a fixed navigation shell, cards, "
            "badges and charts from one component kit), is responsive from 360 px phones to 1440 px desktops and respects the user's reduced-motion setting. The Recognize screen is the centre of the product: a mirrored "
            "camera view with the region-of-interest box, the current letter and its confidence, the segmentation mask the network actually sees, and the sentence with space, back, clear and speak controls."),
          TAB("Screens", ["Screen", "Route", "Content"], SCREENS, widths=[1.1, 1.4, 4.1], align=["l", "l", "l"], size=10),
          FIG(F.shot("01_landing_dark.png"), "Landing page of the web application (dark theme).", F.shot_w(F.shot("01_landing_dark.png"), 5.2, 3.6)),
          P("Chapter 8 shows every working screen with real data. The visual language was taken from a component kit; the original desktop interface was not changed.")]
    return b
