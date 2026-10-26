"""Chapter 6: Methodology and Software Implementation (also the methodology part of document 9 and the implementation part of document 12)."""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, PAIR, TAB
from .refs import cite

C, MB, BL = F.C, F.MB, F.BL


def _class_table_rows():
    names = F.DS["classes"]
    tr, te = F.DS["counts"]["train"], F.DS["counts"]["test"]
    short = lambda n: n.replace("_leaf", "").replace("_", " ")
    half = (len(names) + 1) // 2
    rows = []
    for i in range(half):
        a = names[i]
        row = [short(a), str(tr[a]), str(te[a])]
        if i + half < len(names):
            b = names[i + half]
            row += [short(b), str(tr[b]), str(te[b])]
        else:
            row += ["", "", ""]
        rows.append(row)
    return rows


def methodology_blocks():
    cnn_params = int(C["params"]["mean"])
    mb_params = int(MB["params"]["mean"])
    return [
        H2("6.1 Overall methodology"),
        P("The work has two parts that meet at one function. The first part is a web application that accepts a leaf photograph and a crop, asks `inference.predict()` for the three most likely classes, "
          "turns the top class into advice with the knowledge base and keeps a history for the user. The second part is an offline study that measures how well engines of increasing strength can "
          "do the job that `predict()` is meant to do, on one public field-photograph benchmark and under one protocol. The study was necessary because the product, as inherited, contained no "
          "trained network and no measurement of any kind."),
        N("**Data.** Take the PlantDoc images as released (2,342 training and 236 test photographs), map their 28 folder names to the 38-class label set of the knowledge base.",
          "**Pre-processing.** Resize (256 x 256 for the heuristic, 224 x 224 for networks), scale pixel values, and, for training only, augment with flips, small rotations, zoom and contrast changes.",
          "**Engines.** (a) The shipped colour and texture heuristic; (b) the compact depthwise-separable CNN of `train.py`; (c) a MobileNetV2 with ImageNet weights, head trained then top layers fine-tuned; (d) a random forest and a logistic regression on hand-made colour and texture features.",
          "**Protocol.** 10 % stratified validation split from the training folder for early stopping, three seeds, the test folder touched only for the final scores; five hash seeds for the heuristic.",
          "**Metrics.** Accuracy, top-3 accuracy, macro-F1, per-class precision, recall and F1, confusion matrix, crop-level and healthy-versus-diseased accuracy, CPU latency.",
          "**Advice.** The predicted class selects a knowledge-base card: symptoms, lifecycle, severity, three treatments (chemical, organic, cultural) and prevention, shown in the interface language chrome.",
          "**Application.** FastAPI over the original modules, React front end, SQLite history, CSV and PDF reports, dashboard and analytics."),
        H2("6.2 Dataset"),
        P(f"PlantDoc {cite('plantdoc')} is a set of web-scraped photographs of diseased and healthy leaves taken in real conditions: mixed backgrounds, hands, soil, several leaves per photograph and widely "
          f"varying resolution (189 to 4,000 pixels wide). It is released under CC-BY-4.0. The copy used here is the HF mirror `geraldmc/plantdoc-full`, stored as folders in `datasets/plantdoc-images` "
          f"(445 MB, not committed). It holds {F.NTRAIN:,} training and {F.NTEST} test photographs in 28 class folders; the test folder has 27 classes because `Tomato_two_spotted_spider_mites_leaf` has "
          f"two training photographs and none for testing. Ten folders are healthy leaves (90 test photographs) and 18 are diseases (146 test photographs, 61.9 %)."),
        TAB("PlantDoc class sizes (train and test photographs per folder)", ["Class folder", "Train", "Test", "Class folder", "Train", "Test"], _class_table_rows(),
            widths=[1.9, 0.5, 0.5, 2.3, 0.5, 0.5], align=["l", "c", "c", "l", "c", "c"], size=8.5),
        FIG(F.fig("f09_class_distribution.png"), "Number of photographs per PlantDoc class in the train and test folders.", 4.6),
        P("The data are small and unbalanced (two to 180 training photographs per class; Corn leaf blight is the largest test class with 12 photographs, 5.1 %), which limits every number in this report. "
          "Class names are not the 38 labels of the application: `PLANTDOC_MAP` in `inference.py` maps each of the 28 folders to one canonical label (for example `Tomato_leaf_late_blight` to "
          "`Tomato___Late_blight`). The mapping is one-to-one, so ten canonical classes (such as Apple black rot, Grape esca and Tomato target spot) have no PlantDoc photograph at all and can never be "
          "scored as correct in the study."),
        H2("6.3 Pre-processing"),
        H3("6.3.1 Heuristic engine"),
        P("The heuristic converts the image to RGB, resizes it to 256 x 256 and scales pixels to [0, 1] with `r`, `g`, `b` the channels. It then measures six numbers on the whole picture: the share "
          "of green pixels (`g > r + 0.03` and `g > b + 0.01`), brown pixels (`r > 0.35`, `0.15 < g < 0.55`, `r - g > 0.08`), yellow pixels (`r > 0.5`, `g > 0.5`, `b < 0.4`), dark pixels (mean of the "
          "three channels below 0.25), white pixels (minimum of the three channels above 0.72) and the standard deviation of all values. Nothing is learnt: the thresholds were chosen by hand."),
        CODE(F.src("agrivision/inference.py", 87, 99), 8),
        H3("6.3.2 Training pipeline"),
        P("For the networks, `run_experiments.py data` decodes every photograph once with Pillow (the `draft` option makes large JPEG files quick), converts to RGB, resizes to 224 x 224 with bilinear "
          "interpolation, and stores the result as an unsigned 8-bit array in `cache224.npz`. Labels are the folder indices of the 28 training folders. The stratified validation split takes "
          "`round(0.10 n)` photographs from every class that has at least five (none from the two-photograph class), for each seed separately. Augmentation is part of the network, so it is active only during training:"),
        TAB("Augmentation layers", ["Layer", "Setting", "Used by"],
            [["RandomFlip", "horizontal", "compact CNN, MobileNetV2"], ["RandomRotation", "factor 0.08 (up to about 29 degrees either way)", "compact CNN, MobileNetV2"],
             ["RandomZoom", "factor 0.1", "compact CNN, MobileNetV2"], ["RandomContrast", "factor 0.1", "compact CNN only"],
             ["Rescaling", "1/255 (CNN) or 1/127.5 - 1 (MobileNetV2)", "both"]],
            widths=[1.6, 3.0, 2.1], align=["l", "l", "l"], size=9.5),
        H3("6.3.3 Hand-made features for the classical baselines"),
        P("The random forest and the logistic regression see 43 numbers per photograph: a 16-bin hue histogram, an 8-bin saturation histogram and an 8-bin value histogram (32 numbers), the mean and "
          "standard deviation of the grey level and of the Sobel gradient magnitude and the share of strong gradients (5 numbers), and the mean and standard deviation of each RGB channel (6 numbers)."),
        H2("6.4 Algorithm choice and justification"),
        TAB("Engines compared and why each is in the study", ["Engine", "What it is", "Why it is here"],
            [["Heuristic (shipped)", "Hand-written scores on six colour and texture shares; no training", "It is what the product actually runs. Measuring it is the only honest way to report the system's accuracy."],
             [f"Compact CNN of `train.py` ({cnn_params:,} parameters)", "Five depthwise-separable convolution blocks, batch normalisation, global average pooling, dense head", f"It is the model the original product intended to ship; separable convolutions {cite('xception')} keep it small enough for CPU training. Its recipe is measured exactly as written."],
             [f"MobileNetV2 ({mb_params:,} parameters)", "ImageNet-pre-trained inverted-residual network, new 28-way head, top 30 layers fine-tuned", f"PlantDoc is small; transfer learning from ImageNet {cite('imagenet')} is the standard remedy and MobileNetV2 {cite('mobilenet')} is light enough for a phone or a laptop CPU. It shows what the data can support."],
             ["Random forest and logistic regression", "Classical classifiers on 43 hand-made features", f"A cheap, interpretable yardstick {cite('rf')}: any network should beat colour and texture statistics learnt from the data, and the hand-set heuristic should not lose to them."]],
            widths=[1.7, 2.3, 2.7], align=["l", "l", "l"], size=9),
        P("Heavier networks (ResNet, EfficientNet, vision transformers) were not trained: the aim was an engine that runs in about a second on the machine that serves the application, and the "
          "comparison already shows that the limiting factor is the data, not the backbone. The base paper's own models (VGG19, ResNet50, DenseNet121, Swin, CBAM-ConvNeXt) need GPUs of the class used in that "
          f"paper {cite('base')} and are outside the compute available here."),
        H2("6.5 Model architecture and training configuration"),
        H3("6.5.1 Compact CNN of train.py"),
        TAB("Layers of the compact CNN (input 224 x 224 x 3, 28 outputs)", ["Layer", "Output size", "Parameters"],
            [["Rescaling 1/255 + augmentation", "224 x 224 x 3", "0"], ["SeparableConv2D 32, 3x3, stride 2, ReLU", "112 x 112 x 32", "155"], ["BatchNorm, MaxPool 2, Dropout 0.15", "56 x 56 x 32", "128"],
             ["SeparableConv2D 64, stride 1, ReLU", "56 x 56 x 64", "2,400"], ["BatchNorm, MaxPool 2, Dropout 0.15", "28 x 28 x 64", "256"],
             ["SeparableConv2D 128, stride 2, ReLU", "14 x 14 x 128", "8,896"], ["BatchNorm, MaxPool 2, Dropout 0.15", "7 x 7 x 128", "512"],
             ["SeparableConv2D 256, stride 2, ReLU", "4 x 4 x 256", "34,176"], ["BatchNorm, MaxPool 2, Dropout 0.15", "2 x 2 x 256", "1,024"],
             ["SeparableConv2D 256, stride 1, ReLU", "2 x 2 x 256", "68,096"], ["BatchNorm, MaxPool 2, Dropout 0.15", "1 x 1 x 256", "1,024"],
             ["GlobalAveragePooling, Dropout 0.3", "256", "0"], ["Dense 256, ReLU", "256", "65,792"], ["Dense 28, softmax", "28", "7,196"],
             ["**Total**", "", f"**{cnn_params:,}**"]],
            widths=[3.5, 1.8, 1.4], align=["l", "c", "r"], size=9),
        P(f"The measured size is {cnn_params:,} parameters (about 2.4 MB as a `.keras` file), not the 'about 1.1 M' written in the docstring of `train.py` (defect D6). The comparable network PD36-C {cite('pd36c')} "
          "has 1,250,694 parameters. Its last feature map is only 1 x 1, so spatial detail is discarded early: five max-pooling layers follow five strided or unstrided convolutions."),
        H3("6.5.2 Training configurations"),
        TAB("Training configuration of every trained model", ["Item", "Compact CNN", "MobileNetV2"],
            [["Input", "224 x 224 RGB, uint8 cache", "224 x 224 RGB, uint8 cache"], ["Loss", "sparse categorical cross-entropy", "sparse categorical cross-entropy"],
             ["Optimiser", "Adam, learning rate 1e-3, ReduceLROnPlateau (factor 0.5, patience 2, on validation loss)", "Adam 1e-3 for the head (up to 20 epochs), then Adam 1e-4 with the top 30 backbone layers unfrozen (up to 12 epochs)"],
             ["Batch size", "32", "32"], ["Epochs (maximum)", "60; the shipped-protocol and tuned variants use 60 and 100", "20 + 12"],
             ["Early stopping", "validation accuracy, patience 8, restore best weights", "validation accuracy, patience 4 (head) and 3 (fine-tune), restore best"],
             ["Validation", "10 % stratified split of the training folder", "same split for the same seed"], ["Seeds", "42, 43, 44", "42, 43, 44"],
             ["Regularisation", "dropout 0.15 and 0.3, batch normalisation, augmentation", "dropout 0.3, augmentation"],
             ["Hardware", "CPU only (i5-12500); other jobs shared the CPU", "same"]],
            widths=[1.3, 2.7, 2.7], align=["l", "l", "l"], size=9),
        FIG(F.diag("11_experiment_protocol.png"), "Offline experiment protocol: the test folder is used only for the final scores.", 5.0),
        H3("6.5.3 Classical baselines and the heuristic"),
        P("The random forest has 300 trees with balanced class weights and seed 42; the logistic regression uses standardised features, C = 1 and up to 3,000 iterations. The heuristic needs no training; "
          "its hash-seeded jitter depends on Python's `PYTHONHASHSEED`, so it was evaluated with five values (0 to 4), and the value 0 used by `run.bat` is reported separately."),
        H2("6.6 Mathematical formulation"),
        P("Heuristic score. With `g`, `b`, `y`, `d`, `w` the shares of green, brown, yellow, dark and white pixels and `sigma` the standard deviation of the pixel values, the score of a class is, for a healthy class,"),
        EQ("s_healthy = 3 g - 4 (b + y) - 1.5 d + (0.25 - |sigma - 0.18|)"),
        P("and for a disease class"),
        EQ("s_disease = 3.2 b + 2.4 y + 1.2 d + 1.6 w + 1.5 max(0, 0.5 - g) + bonus(name)"),
        P("where the bonus depends on words in the class name: mildew or mould add 2.0 w, rust adds 1.5 b, blight, spot or scorch add 1.2 (b + y), mosaic, curl or greening add 1.8 y, mite adds (y + w). A "
          "deterministic jitter is added so that the order is stable per image:"),
        EQ("s = s_class + 0.35 j,   j = ((h XOR hash(class)) mod 1000) / 1000"),
        P("with `h` the integer made of the first eight hexadecimal digits of the MD5 hash of the file. The three best scores are kept; the displayed confidence of the first and the fractions shown for the other two are"),
        EQ("c1 = min(0.99, max(0.62, 0.62 + 0.22 min(1.6, s*))),   c2 = c1 (0.04 + ((h >> 3) mod 8)/100),   c3 = c1 (0.01 + ((h >> 6) mod 4)/100)"),
        P("so c1 saturates at 0.972 for any s* of 1.6 or more (the 97.2 % seen on most result screens) and the three numbers do not sum to one. Networks output a softmax distribution over K classes,"),
        EQ("p_k = exp(z_k) / sum_j exp(z_j)"),
        P("and are trained by minimising the average cross-entropy over N photographs with the Adam optimiser " + cite("adam") + ":"),
        EQ("L = -(1/N) sum_i log p_(i, y_i)"),
        P("Reported metrics, per class `c` with true positives TP, false positives FP and false negatives FN: precision = TP / (TP + FP), recall = TP / (TP + FN), F1 = 2 precision recall / (precision + recall). "
          "Macro-F1 is the mean of the F1 of the classes that occur in the test folder (27); accuracy is the share of correct top-1 answers; top-3 accuracy is the share of photographs whose true class is among "
          "the three highest scores. Crop-level accuracy asks only whether the predicted class belongs to the right crop, and healthy-versus-diseased accuracy whether the healthy flag matches."),
        P("The same formulas as they are written in `inference.py`:"),
        CODE(F.src("agrivision/inference.py", 114, 145), 7.5),
        P("Session token. The service signs `payload = base64url(JSON{uid, exp})` with HMAC-SHA256 and a server secret and sends `payload.signature`; verification recomputes the signature with a "
          "constant-time comparison and then checks `exp` against the clock."),
    ]


def application_blocks():
    return [
        H2("6.7 Application architecture"),
        P("The runtime has two processes (Figure 12 of the diagram set). The FastAPI process imports `config`, `inference`, `disease_db` and `app.init_db` from `agrivision/` by adding that folder to "
          "`sys.path`, so there is exactly one implementation of detection, of the knowledge base and of the tables. Environment variables `AGRIVISION_DB`, `AGRIVISION_UPLOADS` and `AGRIVISION_SECRET` can "
          "redirect the database, the upload folder and the token secret; the tests use the first two to work on a throw-away copy. Each request opens its own SQLite connection (`get_db`) and closes it "
          "afterwards. On the browser side, axios sends every call to `/api`, which Vite proxies to port 8416; TanStack Query caches the results of reads, and a mutation that creates or deletes a scan "
          "invalidates the dashboard, history and analytics queries."),
        H3("6.7.1 Diagnosis request"),
        P("`detect()` is the heart of the service. It rejects a missing or empty file (400), an extension outside jpg, jpeg, png and webp (400) and a body above 10 MB (413), calls `predict()`, looks up the card "
          "of the predicted class, writes the image under a random UUID name, inserts the row and returns the summary. The excerpt shows the code as shipped, including the broad `except` that turns any "
          "engine exception into 400 UNREADABLE_IMAGE (defect D1). The full listing is in Appendix A.2."),
        H3("6.7.2 Engine hook for a trained model"),
        P("`try_load_model()` runs once when `inference` is imported. If `models/plantdoc_cnn.h5` and `labels.json` (written by `train.py`) exist, TensorFlow is imported, the model is loaded without its "
          "optimiser and `predict()` takes the network branch: resize to the model's input size, scale to [0, 1], `predict`, take the three largest outputs and translate PlantDoc names to canonical labels with "
          "`PLANTDOC_MAP`. `/api/health` then reports `trained_model: true` and the interface changes its wording. No code outside `inference.py` needs to change."),
        H2("6.8 API design in the code"),
        P("Routes are plain FastAPI functions. Authentication is a dependency (`current_user`) shared by every protected route, so a route cannot forget it. Ownership is checked by `owned()`, which selects "
          "with both the scan id and the user id and answers 404 for anything else. History filters (search text, crop, healthy or diseased) are applied in Python over the user's rows, the same rule as the "
          "Flask page, which is adequate for hundreds of scans and would have to move into SQL for tens of thousands. Exports are generated on the fly: `csv` from the standard library and a one-page PDF per "
          "scan with reportlab. A single exception handler turns every `HTTPException` into `{error, message, detail}`."),
        CODE(F.src("backend/main.py", 94, 110), 7.5),
        H2("6.9 Security and error handling"),
        TAB("Security measures in the code and their limits", ["Concern", "Implementation", "Limit found by the tests"],
            [["Passwords", "Salted hash by `werkzeug.security` (scrypt); minimum 6 characters; never returned", "No complexity rule, no lock-out (defect D4)"],
             ["Sessions", "HMAC-SHA256 bearer token with 7-day expiry, compared in constant time; forged, malformed and expired tokens give 401", "Default secret `agrivision-dev-secret-change-me` is public: a token signed with it is accepted unless `AGRIVISION_SECRET` is set (D3); no revocation list"],
             ["Authorisation", "Every scan query includes `user_id`; other users get 404 on read, export and delete", "Uploaded images are served without a token; the random file name is the only protection"],
             ["Uploads", "Extension whitelist, 10 MB limit, empty-file check, random server-side file name; a path inside the file name does not escape the folder", "The file content is not checked separately: a text file renamed .jpg is refused only because Pillow cannot open it (400 UNREADABLE_IMAGE)"],
             ["Injection", "All SQL uses `?` parameters; search text is compared in Python", "None found"],
             ["Cross-origin", "CORS allows only `http(s)://localhost` and `127.0.0.1` origins", "A deployment on another host must edit the pattern"],
             ["Errors", "One JSON error shape; the client shows `message`; a 401 on a signed-in call drops the token and returns to sign-in", "The broad `except` in `detect()` reports every engine failure as an unreadable image"]],
            widths=[1.1, 3.2, 2.4], align=["l", "l", "l"], size=9),
        P("On the client, `validate()` in the Detect page repeats the extension and size checks before upload and shows the sentence returned by the service when a request fails; a progress bar follows the "
          "upload; and an expired token is removed from storage and the sign-in page is shown."),
        H2("6.10 Installation and execution"),
        N("Install Python 3.10 or newer and Node.js 20 or newer.",
          "Double-click `run.bat` in `8.ProjectCode`. It sets `PYTHONHASHSEED=0`, creates or rebuilds `.venv`, installs `backend/requirements.txt` (FastAPI, uvicorn, python-multipart, Flask, Pillow, NumPy, reportlab) and runs `npm install` in `frontend/`.",
          "It starts the API on port 8416 (waits for `/api/health`) and the Vite server on port 5416 and opens `http://localhost:5416`. Ports come from `.env`.",
          "Sign in with the demo account `demo@agrivision.ai` / `demo1234` or register.",
          "To use a network: `pip install tensorflow`, run `python agrivision/train.py` (it needs `datasets/plantdoc-images`), then restart the API."),
        P(f"Checks: `python scripts/smoke_test.py` ({F.N_SMOKE} API checks, own server and throw-away database), `python scripts/edge_tests.py` ({F.N_EDGE} unit and API checks), `python scripts/ui_checks.py` "
          f"({F.N_UI} browser checks, both servers needed) and `python scripts/run_experiments.py` for the measurements. Appendix B gives the step-by-step guide."),
    ]


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
