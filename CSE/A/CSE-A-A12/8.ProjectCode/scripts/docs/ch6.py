"""Chapter 6: Methodology and software implementation."""

import json

from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

LAYER_ROWS = None


def _layers():
    """Layer table rows from experiments/model_summary.json (written by scripts/collect_env.py)."""
    info = F.MODEL_INFO
    rows = []
    if not info:
        return rows
    for l in info["layers"]:
        shp = "x".join(str(x) for x in l["output_shape"]) if l["output_shape"] else "-"
        rows.append([l["name"], l["type"], shp, f"{l['params']:,}"])
    return rows


def methodology_blocks():
    e = F.DEPLOYED or {}
    tr = e.get("training", {})
    hp = e.get("hyperparameters", {})
    sec_epoch = tr.get("seconds_per_epoch")
    return [
        H2("6.1 Overall methodology"),
        P("The method has two phases that share one preprocessing function. In the **training phase** the public chest X-ray data are listed, labelled from their "
          "folder and file names, preprocessed, split by patient into training and validation parts, augmented and used to fit the CNN; the best weights are "
          "evaluated once on the untouched test split and every number is written to JSON. In the **inference phase** an uploaded image goes through the same "
          "preprocessing, the saved network returns three probabilities, Grad-CAM explains the arg-max class, and the result is stored and displayed."),
        FIG(F.diag("02_high_level_workflow.png"), "Overall workflow used at inference time (the same preprocessing is used for training)", 5.8),
        H2("6.2 Dataset"),
        P(f"The data are the Chest X-Ray Images (Pneumonia) collection of Kermany et al. {n(3, 4)}: paediatric (one to five years) anterior-posterior chest "
          "radiographs from the Guangzhou Women and Children's Medical Center, released under CC BY 4.0. The version used has 5,856 JPEG images in the official "
          "folders train (5,216), val (16) and test (624). Pneumonia images carry the pathogen in the file name (`person12_bacteria_34.jpeg`, "
          "`person7_virus_21.jpeg`), which gives the three project classes."),
        TAB("Official folders and the three project classes", ["Folder", "Normal", "Bacterial", "Viral", "Total"], [
            ["train", "1,341", "2,530", "1,345", "5,216"],
            ["val", "8", "-", "-", "16 (8 normal, 8 pneumonia)"],
            ["test", "234", "242", "148", "624"],
        ], widths=[1.2, 1.0, 1.0, 1.0, 2.2], align=["l", "c", "c", "c", "c"]),
        P("The official validation folder holds only 16 images, too few to guide training. The experiment script therefore merges `train` and `val` and cuts a "
          "validation set of about 10 % by **patient** (a stratified group split, seed 42), so that images of one patient never appear on both sides. The official "
          "`test` folder is used once, for the final evaluation. A further check (Section 8.4) shows that many pneumonia file ids in the test folder also occur in "
          "the training folders, a property of the public data that earlier work has also reported; the report therefore also gives results on the part of the test "
          "split that shares no id with training and on a fully patient-disjoint re-partition."),
        FIG(F.fig("dataset_distribution.png"), "Images per class in the training, validation and test sets used by the main experiment", 5.0),
        H2("6.3 Preprocessing"),
        P("The function `load_and_preprocess_image` in `model/preprocess.py` is used unchanged by the training script, the Flask route and the FastAPI route:"),
        N("Decode the file as a single-channel grayscale image (`cv2.imread` or `cv2.imdecode`); a file that cannot be decoded raises `ValueError`, which the API turns into HTTP 400.",
          "Resize to 224 x 224 with area interpolation, the input size of the network and of the ImageNet backbones.",
          f"Apply CLAHE, contrast-limited adaptive histogram equalisation {n(11)}, with clip limit 2.5 and 8 x 8 tiles, to bring out lung markings.",
          "Apply a 3 x 3 Gaussian blur to suppress scanner and JPEG noise.",
          "Replicate the channel three times and divide by 255 to obtain a float32 tensor in [0, 1] of shape 224 x 224 x 3."),
        FIG(F.fig("preprocessing_steps.png"), "Preprocessing steps applied to a normal and a pneumonia radiograph (public-domain sample images)", 5.8),
        P("During training, augmentation is applied on top of the preprocessed image: rotation up to 12 degrees, horizontal and vertical shifts of 8 %, shear of 8 %, "
          "zoom of 12 % and horizontal flips, with nearest-neighbour filling. These are the ranges of `get_train_augmentor` in the original code. The base paper "
          f"disables flips to preserve anatomical orientation {n(1)}; the project's augmentor keeps them, which is recorded as a design difference."),
        H2("6.4 Algorithm choice and justification"),
        TAB("Choices and reasons", ["Decision", "Choice", "Reason"], [
            ["Model family", "CNN written for the project (4 convolution blocks)", "Small (0.59 M parameters), trains on a CPU, no external weights, easy to explain; a transfer-learning builder is also provided"],
            ["Normalisation", "Batch normalisation after each convolution", f"Stabilises training of a network trained from scratch {n(17)}"],
            ["Pooling before the head", "Global average pooling", "Fewer parameters than flattening and keeps spatial meaning for Grad-CAM"],
            ["Regularisation", "Dropout 0.35 and 0.25, data augmentation, early stopping", f"Small data and a risk of over-fitting {n(18)}"],
            ["Loss", "Categorical cross-entropy with balanced class weights", "Bacterial images are about twice as frequent as the other classes"],
            ["Optimiser", "Adam, learning rate 3e-4 (baseline run: 1e-4)", f"Adaptive and robust for a first experiment {n(16)}"],
            ["Explanation", "Grad-CAM on the last convolution layer", f"Works on any CNN without changing it {n(9)}; the layer is named `last_conv`"],
            ["Contrast step", "CLAHE", f"Standard for radiographs {n(11)}; its effect is measured by an ablation (Chapter 8)"],
        ], widths=[1.3, 2.1, 2.9], size=9.5),
        H2("6.5 Mathematical formulation"),
        P("**Convolution block.** For the input feature map A(l-1), learned kernels W(l) and biases b(l), each block applies a convolution, the ReLU "
          "non-linearity, batch normalisation and 2 x 2 max pooling."),
        EQ("A(l) = MaxPool( BN( ReLU( W(l) * A(l-1) + b(l) ) ) ),   ReLU(x) = max(0, x)"),
        EQ("BN(x) = γ · (x − μB) / √(σB² + ε) + β"),
        P("**Classifier.** Global average pooling turns each of the 256 final feature maps into one number; two dense layers follow and the output layer produces "
          "three logits z, which the softmax converts into probabilities. The predicted class is the arg-max and the reported confidence is its probability."),
        EQ("gk = (1 / HW) · Σi Σj Ak(i, j)"),
        EQ("pc = exp(zc) / Σj=1..3 exp(zj),     ĉ = argmax pc,     confidence = pĉ"),
        P("**Loss.** With balanced class weights (N images, K = 3 classes, nc images in class c) the weighted cross-entropy over a batch of B images is:"),
        EQ("wc = N / (K · nc)"),
        EQ("L = − (1 / B) · Σi=1..B  w(yi) · Σc yic · log pic"),
        P("**Optimiser.** Adam keeps exponential moving averages of the gradient (mt) and of its square (vt) and updates the parameters with learning rate η (3 × 10-4 for the deployed model, 10-4 for the baseline run):"),
        EQ("θt = θt-1 − η · m̂t / ( √v̂t + ε )"),
        P("**Grad-CAM.** For class c and the last convolutional feature maps Ak, the channel weights are the spatially averaged gradients of the class score, and the map is the "
          "rectified weighted sum of the feature maps, normalised by its maximum, resized to 224 x 224, coloured with the JET colour map H and blended with the display image I "
          "(code: `overlay_heatmap`, alpha 0.4):"),
        EQ("αkc = (1 / Z) · Σi Σj ∂yc / ∂Ak(i, j),     Lc = ReLU( Σk αkc · Ak )"),
        EQ("O = 0.6 · I + 0.4 · H"),
        P("**Metrics.** From the confusion matrix, with TP, TN, FP and FN counted for the class (or for pneumonia against normal in the binary view):"),
        EQ("accuracy = (TP + TN) / N,   precision = TP / (TP + FP),   recall = sensitivity = TP / (TP + FN)"),
        EQ("specificity = TN / (TN + FP),   F1 = 2 · precision · recall / (precision + recall),   macro-F1 = mean of the three class F1"),
        P(f"Calibration is summarised by the expected calibration error with M = 10 equal-width confidence bins {n(29)}, where acc(Bm) and conf(Bm) are the accuracy "
          "and mean confidence of the images in bin m. A confidence threshold τ keeps a prediction for automatic reporting only if its confidence is at least τ; "
          "coverage is the share of scans kept:"),
        EQ("ECE = Σm=1..M (|Bm| / n) · | acc(Bm) − conf(Bm) |,     coverage(τ) = #{ i : pĉ,i ≥ τ } / n"),
        H2("6.6 Model architecture and training"),
        P("The deployed architecture is `build_custom_cnn` from `model/model_builder.py`. The input is 224 x 224 x 3. Four convolution blocks (3 x 3 kernels with 32, "
          "64, 128 and 256 filters, each followed by batch normalisation and 2 x 2 max pooling) are followed by global average pooling, a 512-unit dense layer with "
          "batch normalisation and dropout 0.35, a 128-unit dense layer with dropout 0.25 and a three-unit softmax output. The last convolution layer is named "
          "`last_conv` so that Grad-CAM can find it."),
        TAB("Layers of the deployed network", ["Layer", "Type", "Output shape", "Parameters"], _layers() or [["(run scripts/collect_env.py)", "", "", ""]], widths=[1.9, 2.0, 1.4, 1.0], size=9, align=["l", "l", "c", "r"]),
        P(f"The network has {F.MODEL_INFO['total_params']:,} parameters ({F.MODEL_INFO['trainable']:,} trainable), about {F.MODEL_INFO['float32_mb']} MB in 32-bit floats." if F.MODEL_INFO else ""),
        P("The original `model/train.py` fits the same network with a Keras directory generator and rescaling only. The experiment script `scripts/train_experiment.py` "
          "(used for every number in this report) differs in four ways: it applies the inference preprocessing (CLAHE and blur) during training, so the network is "
          "trained on what it will see in service; it splits validation data by patient; it uses balanced class weights; and it records metrics, predictions and figures."),
        TAB("Training configuration of the main experiment", ["Setting", "Value"], [
            ["Architecture", "`build_custom_cnn(num_classes=3)`"],
            ["Input", "224 x 224 x 3, CLAHE + blur preprocessing"],
            ["Optimiser / loss", f"Adam, learning rate {hp.get('learning_rate', 1e-4)}; categorical cross-entropy with balanced class weights"],
            ["Batch size / maximum epochs", f"{hp.get('batch_size', 32)} / {hp.get('epochs_max', 25)}"],
            ["Callbacks", f"Early stopping on validation loss (patience {hp.get('early_stopping_patience', 10)}, best weights restored); learning rate halved after {hp.get('reduce_lr_patience', 3)} epochs without improvement"],
            ["Augmentation", "Rotation 12, shift 0.08, shear 0.08, zoom 0.12, horizontal flip"],
            ["Random seed", str(hp.get("seed", 42))],
            ["Hardware", "Intel Core i5-12500 CPU, no GPU; about " + (f"{sec_epoch:.0f} seconds per epoch" if sec_epoch else "four minutes per epoch")],
        ], widths=[2.0, 4.3], size=10),
        P("**Baseline run and recipe change (disclosure).** The first run used the project's defaults (Adam 1e-4, early-stopping patience 6, at most 25 epochs). It stopped after 12 epochs with its best "
          "validation loss at epoch 6: the validation loss of a batch-normalised network trained from scratch is noisy, early stopping fired before the network had converged, and training accuracy was only "
          "about 74 %. The recipe was then changed to a higher learning rate (3e-4), a longer patience (10) and up to 40 epochs. This change was made after the baseline's test result had been seen, "
          "so both runs are reported side by side (Section 8.5); the choice of the deployed model between them rests on the validation set, not on the test split."),
        P("**Transfer-learning option and a limitation found while testing it.** `build_transfer_model` offers DenseNet201, DenseNet121, ResNet152V2 and EfficientNetB0 backbones. "
          "When a backbone is nested inside the model, `make_gradcam_heatmap` cannot connect the nested feature tensor to the outer input and raises an error; "
          "the shipped Grad-CAM therefore works only with the flat custom CNN, which is why the custom CNN is the deployed model. Chapter 8 includes a MobileNetV3Small experiment "
          "(the base paper's backbone) for comparison, without Grad-CAM."),
    ]


def application_blocks():
    return [
        H2("6.7 Application architecture"),
        P("`backend/main.py` creates a FastAPI application (`api`) whose start-up hook initialises the database and loads the model in a background thread so the first "
          "request does not pay the loading cost. It imports `app.py` and calls `get_model()` so that the Flask and FastAPI interfaces share one loader, one set of folders "
          "and one `_demo_mode` flag. A threading lock allows only one TensorFlow inference at a time. Cross-origin requests are accepted only from the front-end origin "
          "(`http://localhost:5312`). The React application talks to `/api/*` through the Vite proxy, so the browser sees one origin and the session cookie is first-party."),
        P("The front end is a single-page application built with React 19 and Vite. Routes are code-split and lazy-loaded (the chart library is loaded only by the dashboard). "
          "`lib/api.js` wraps `fetch`, turns every error response into an `ApiError` with the server's message and uses an XMLHttpRequest for uploads so the progress bar "
          "can show real upload progress; a 401 anywhere returns the user to the sign-in page."),
        H2("6.8 API design"),
        P("Section 5.7 lists the ten endpoints. The prediction route validates in a fixed order (no file, empty name, unsupported extension, size above 8 MB, unreadable image), "
          "saves the original under a random 12-character name, preprocesses, runs the network and Grad-CAM under the lock, writes the overlay, inserts the database row and returns the "
          "stored record with status 201. The record contains the probabilities as an object keyed by class name, image URLs under `/api/files/`, an ISO timestamp with a trailing Z and the "
          "`demo_mode` flag."),
        CODE('''@api.post("/api/predict", status_code=201)
def predict(xray_image: UploadFile = File(None), user=Depends(current_user)):
    if xray_image is None:            bad(400, "No file part in the request.")
    if not xray_image.filename:       bad(400, "Please choose an X-ray image to upload.")
    if not flask_app.allowed_file(xray_image.filename):
                                      bad(400, "Unsupported file type. Please upload a JPG or PNG image.")
    data = xray_image.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:         bad(413, "File is too large. The limit is 8 MB.")
    ...
    with _predict_lock:
        probs = model.predict(batch, verbose=0)[0]
        pred_idx = int(np.argmax(probs))
        heatmap, _ = make_gradcam_heatmap(batch, model, flask_app._last_conv_layer, pred_index=pred_idx)
    ...
    return serialize(db.get_prediction(pred_id))'''),
        H2("6.9 Security and error handling"),
        TAB("Controls", ["Threat or fault", "Control in the code"], [
            ["Unauthenticated access", "Every route except health, login, logout and `/api/auth/me` depends on `current_user`, which reads a signed cookie and answers 401"],
            ["Cookie forgery or tampering", "Cookie = base64 payload + HMAC-SHA256 signature checked with `hmac.compare_digest`; payload carries an expiry (12 h)"],
            ["Script access to the session", "Cookie set `HttpOnly` and `SameSite=Lax`"],
            ["Path traversal on file routes", "Only `uploads` and `heatmaps` are served and the name must equal its own basename"],
            ["SQL injection", "All SQL uses bound parameters"],
            ["Hostile or huge uploads", "Extension allow-list, 8 MB limit read incrementally (413), decode check (400) with deletion of the saved file"],
            ["Concurrent inference", "A lock serialises TensorFlow calls"],
            ["Cross-site requests", "CORS limited to the front-end origin, credentials allowed only for it"],
            ["Credentials in source control", "`.env` is git-ignored; `.env.example` documents the variables; the demo password is shown on the sign-in page because it is a demonstration account"],
            ["Unreadable or missing model", "The loader builds an untrained network and the interface shows a Demo Mode warning on every relevant screen"],
        ], widths=[1.8, 4.5], size=9.5),
        P("Known weaknesses are stated in Section 1.8: the demo account is shared, the transport is plain HTTP on localhost, and the original Flask application keeps a fixed secret key and no login."),
        H2("6.10 Installation and execution"),
        P("`run.bat` reads the ports from `.env` (API 8312, UI 5312), creates a `.venv` if needed, installs `requirements.txt` and `requirements-api.txt`, runs `npm install` in `frontend/` "
          "on first use, opens two console windows (the API and the UI) and then the browser. `stop.bat` closes them. `run.bat flask` starts the original Flask interface on port 5000. "
          "Appendix B gives the full user guide and the manual commands."),
    ]


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
