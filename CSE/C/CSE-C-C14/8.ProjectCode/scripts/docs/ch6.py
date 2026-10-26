"""Chapter 6: Methodology and Software Implementation (VeriVision AI).

methodology_blocks() feeds document 9, application_blocks() feeds document 12, blocks() is the full chapter of the report.
All numbers come from facts.py (experiments/cifake/metrics.json) or from the code.
"""

from . import facts as F
from .blocks import B, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def c(*keys):
    return "[" + ", ".join(str(R[k]) for k in keys) + "]"


def _hist(b):
    h = F.HIST.get(b, {})
    f1 = h.get("val_f1", [])
    acc = h.get("val_acc", [])
    if not f1:
        return 0, 0, 0.0, 0.0
    i = max(range(len(f1)), key=lambda k: f1[k])
    return len(f1), i + 1, f1[i], acc[i]


# =====================================================================================================================
def methodology_blocks():
    d = F.DATA
    tr, va, te = d.get("train_real", 3000), d.get("val_real", 600), d.get("test_real", 1000)
    return [
        H2("6.1 Overall Methodology"),
        P("The methodology has two halves: an offline half that builds the four detectors and measures them, and an online half that serves one image at a time. "
          "The offline half takes a class-balanced subset of a public benchmark, fine-tunes four ImageNet-pretrained CNNs with different augmentation, loss and resolution, and evaluates each route and the "
          "fused ensemble on a held-out test set, on degraded copies of it and on a probe set from other sources. The online half validates an upload, runs the four routes, fuses their logits, explains "
          "the verdict with Grad-CAM and re-tests the image under three degradations. The stages are:"),
        N("**Data preparation.** A class-balanced CIFAKE subset is written to train, validation and test folders; a cross-domain probe set is prepared separately.",
          "**Preprocessing and augmentation.** Each route has its own training augmentation and a common evaluation transform (resize and ImageNet normalisation).",
          "**Route training.** Four routes are fine-tuned from ImageNet weights with AdamW, cosine decay and early stopping on the validation F1.",
          "**Evaluation.** Per-route and ensemble metrics, fusion ablations, a threshold sweep, bootstrap intervals, calibration, robustness and cross-domain tests are computed from cached logits.",
          "**Deployment.** The checkpoints, a metadata file and the metric artifacts are written where the Flask service reads them.",
          "**Inference and explanation.** For each upload: four route logits, fusion with two gates, a verdict with a confidence word, three Grad-CAM overlays and a robustness consistency score."),

        H2("6.2 Dataset"),
        P(f"The data are drawn from CIFAKE {c('cifake')}, a benchmark of 60,000 real images taken from CIFAR-10 {c('cifar10')} and 60,000 synthetic images generated with Stable Diffusion v1.4 {c('ldm')}, "
          "all 32 x 32 pixels, with an official split of 100,000 training and 20,000 test images. The copy used here is the Hugging Face mirror dragonintelligence/CIFAKE-image-dataset (parquet, JPEG, "
          "mirror labels 0 = FAKE and 1 = REAL; the dataset card has no licence field, while the Kaggle original and other copies are tagged MIT). The labels are remapped to the product's convention, "
          "0 = REAL and 1 = AI_GENERATED."),
        P(f"The full dataset was not used, because the models are trained on a CPU. A class-balanced subset was drawn with seed 42: {tr:,} real and {tr:,} generated images for training and {va:,} of each for "
          f"validation, both from the official training split and without overlap, and {te:,} of each for testing, from the official test split only. The test set therefore never overlaps with training, "
          "but the training subset is only 6 % of the official training split and the test set is 10 % of the official test split, and every conclusion about accuracy carries that limit."),
        TAB("Data splits used in this project", ["Set", "Source", "Real", "AI-generated", "Total", "Used for"], [
            ["Train", "CIFAKE official train split", f"{tr:,}", f"{tr:,}", f"{2 * tr:,}", "Fine-tuning the four routes"],
            ["Validation", "CIFAKE official train split (no overlap)", f"{va:,}", f"{va:,}", f"{2 * va:,}", "Early stopping, best checkpoint"],
            ["Test", "CIFAKE official test split", f"{te:,}", f"{te:,}", f"{2 * te:,}", "All reported metrics, ablations, threshold sweep"],
            ["Robustness subset", "First 500 per class of the test set", "500", "500", "1,000", "JPEG, resize, blur and noise tests"],
            ["Cross-domain probe", "Hugging Face Parveshiiii/AI-vs-Real (MIT)", "300", "300", "600", "Transfer to other photographs and generators"],
        ], widths=[1.0, 1.9, 0.6, 0.8, 0.6, 1.5], size=9, align=["l", "l", "c", "c", "c", "l"]),
        P("The cross-domain probe uses 300 real photographs of about 640 pixels and 300 generated images of 1,024 x 1,024 pixels, re-saved as JPEG at quality 95. The dataset card does not name the generators, "
          "so the probe measures transfer to some unseen generator and content domain, not to a specific model. Before this run the shipped models had been trained on deterministic synthetic demo images "
          "(500 / 100 / 100 per class); that data was replaced and is kept only as a backup."),
        FIG(F.fig("f01_dataset_split.png"), "Class counts of the train, validation, test, robustness and cross-domain sets.", 4.4),

        H2("6.3 Preprocessing and Augmentation"),
        P("At inference time every route uses the same transform: the image is converted to RGB, resized with bilinear interpolation to the route's square input size (224 x 224 for A1, A2 and C, 320 x 320 for B) "
          f"without keeping the aspect ratio, converted to a tensor and normalised with the ImageNet mean (0.485, 0.456, 0.406) and standard deviation (0.229, 0.224, 0.225) {c('imagenet')}. "
          "CIFAKE images are 32 x 32, so they are enlarged by a factor of 7 or 10; the networks therefore see smooth, up-sampled pictures, which matters for the results in Chapter 8."),
        P("Training uses a different augmentation for each route, so that the routes learn different invariances. Route A1 uses the mildest, A2 the strongest, which imitates the degradations of social-media "
          "sharing, and B and C a moderate mixture."),
        TAB("Training augmentation per route (scripts/common.py)", ["Route", "Augmentation"], [
            ["A1", "Random resized crop (scale 0.8-1.0), horizontal flip, colour jitter (brightness 0.15, contrast 0.15, saturation 0.1)"],
            ["A2", "Random resized crop (0.6-1.0), flip, rotation up to 12 degrees, colour jitter (0.3, 0.3, 0.2, hue 0.05), Gaussian blur (3 x 3, sigma 0.1-1.5), Gaussian noise (std 3-12, p 0.4), JPEG (quality 40-90, p 0.5), down-up resize (scale 0.4-0.8, p 0.4)"],
            ["B and C", "Random resized crop (0.75-1.0), flip, rotation up to 8 degrees, colour jitter (0.2, 0.2, 0.15), Gaussian blur (3 x 3, sigma 0.1-1.2), JPEG (quality 50-95, p 0.35)"],
        ], widths=[0.8, 5.5], size=9.5, align=["c", "l"]),

        H2("6.4 Algorithm Choice and Justification"),
        P("**Convolutional networks with transfer learning.** Generated images leave local statistical traces, and convolutional networks learn such traces directly from pixels. Fine-tuning ImageNet-pretrained "
          f"backbones is the practical choice on a CPU: only the upper blocks are trained, which keeps training to minutes per route. The backbones are EfficientNet-B0 {c('efficientnet')}, ResNet50 {c('resnet')} "
          f"and MobileNetV3-Large {c('mobilenetv3')}; they differ in design (compound-scaled mobile blocks, residual blocks, neural-architecture-searched blocks), which gives the ensemble different error patterns."),
        P("**Heterogeneous ensemble with logit fusion and gates.** The design follows HEDGE " + c("hedge") + ", which fuses three routes in logit space and adds two gating rules, but replaces its large foundation-model "
          "backbones (DINOv3 and MetaCLIP2, trained on eight H800 GPUs) with small CNNs. Fusing logits keeps the strength of each route's evidence, which a majority vote throws away and a probability average "
          "compresses. The gates are cheap deterministic rules that need no training data. Chapter 8 tests each of these choices on the same logits instead of assuming them."),
        P("**Grad-CAM for explanation.** Grad-CAM " + c("gradcam") + " produces a class-specific heat map for any CNN from the gradients of the output with respect to the last convolutional feature map, without retraining or "
          "changing the architecture. It was chosen because the project goal is an interpretable verdict and because the batch's own abstract names it. It is an explanation aid: a heat map shows where the "
          "gradient signal is strong, not a proof that those pixels are manufactured."),
        P("**Relation to the base paper.** The batch's base paper, CTrue " + c("base") + ", is a one-class face-deepfake detector that trains only on authentic faces plus synthesised pseudo-fakes, on an EfficientNet-B4 "
          "backbone with a hybrid-curvature representation. This project does not implement it. It addresses general images, trains a supervised binary classifier and adds an explanation and a deployed interface; "
          "the comparison in Chapter 8 states where the two differ."),

        H2("6.5 Mathematical Formulation"),
        P("Let z_k = (z_k,real, z_k,fake) be the raw logit pair of route k (A1, A2, B or C), w_k its weight (normalised to sum to 1), and d_k = argmax z_k its predicted direction (0 = REAL, 1 = AI_GENERATED). "
          "The margin of a route is the absolute difference of its two logits."),
        EQ("m_k = | z_k,fake - z_k,real |"),
        P(f"Gate 1 removes Route B when it is a confident outlier: B's margin reaches tau_B = {F.GATE_TAU_B} and every one of the other three routes points to the other class. The remaining weights are renormalised."),
        EQ("exclude B  if  m_B >= tau_B  and  d_k != d_B for each of A1, A2, C"),
        P("The fused logits are the weighted sum over the active routes, and Gate 2 then checks the consensus of B and C."),
        EQ("z_fused = sum_k w_k * z_k   (over active routes)"),
        P(f"Gate 2 applies when B and C agree on a class c, both margins reach tau_B and tau_C = {F.GATE_TAU_C}, and the fused direction is the other class. With delta = {F.GATE_CORR}, the logit of class c is raised by delta and "
          "the other logit is lowered by delta / 2."),
        EQ("z_fused,c += delta ;  z_fused,other -= delta / 2   if  d_B = d_C != d_fused,  m_B >= tau_B,  m_C >= tau_C"),
        P(f"The probabilities and the verdict follow from a softmax. The confidence is the larger probability, reported as High when it is at least {F.CONF_HIGH}, Moderate when it is at least {F.CONF_MOD} and Low below that."),
        EQ("p_c = exp(z_c) / (exp(z_real) + exp(z_fake)) ;  verdict = argmax p ;  confidence = max p"),
        P(f"Route C is trained with the focal loss {c('focal')}, which down-weights examples that are already classified well. With p_t the probability of the true class and gamma = 2:"),
        EQ("FL(p_t) = (1 - p_t)^gamma * ( - log p_t )"),
        P("Grad-CAM weights each feature map A^k of the target layer by the average gradient of the class score y^c and keeps only the positive evidence:"),
        EQ("alpha_k^c = (1 / Z) * sum_i sum_j  dy^c / dA^k_ij ;   L^c = ReLU( sum_k alpha_k^c * A^k )"),
        P("The evaluation uses accuracy, precision, recall, F1, balanced accuracy and the area under the ROC curve (AUC), computed with scikit-learn " + c("sklearn") + ". The expected calibration error (ECE) "
          f"{c('calibration')} bins the winning-class probability into 15 equal bins between 0.5 and 1 and averages the gap between accuracy and confidence, weighted by bin size. Accuracy intervals are 95 % percentile "
          f"bootstrap intervals from 2,000 resamples of the test set {c('bootstrap')}."),
        EQ("ECE = sum_b ( n_b / n ) * | acc_b - conf_b |"),

        H2("6.6 Model Architecture and Training"),
        P("All four routes replace the ImageNet classifier by a two-class head. A1 and A2 use EfficientNet-B0 with dropout 0.3 and a linear layer; B uses ResNet50 with a linear layer; C uses MobileNetV3-Large "
          "with a 1,280-unit hidden layer, Hard-Swish and dropout 0.2. Only the upper blocks are fine-tuned and the rest stay frozen at their ImageNet values, which is why the trainable parameter counts "
          "are much smaller than the totals."),
        TAB("Routes and training configuration", ["", "A1", "A2", "B", "C"], [
            ["Backbone", "EfficientNet-B0", "EfficientNet-B0", "ResNet50", "MobileNetV3-Large"],
            ["Input size", "224", "224", "320 (+ flip TTA)", "224"],
            ["Loss", "Cross-entropy", "Cross-entropy", "Cross-entropy", "Focal, gamma 2"],
            ["Fine-tuned blocks", "features 7-8, head", "features 6-8, head", "layer4, fc", "features 15-16, head"],
            ["Trainable / total parameters", "1,131,954 / 4,010,110", "3,158,302 / 4,010,110", "14,968,834 / 23,512,130", "2,185,522 / 4,204,594"],
            ["Learning rate / batch", "3e-4 / 32", "3e-4 / 32", "2e-4 / 16", "3e-4 / 32"],
            ["Planned epochs / seed", "5 / 42", "5 / 43", "3 / 44", "5 / 45"],
            ["Epochs run / best epoch", "%d / %d" % _hist("a1")[:2], "%d / %d" % _hist("a2")[:2], "%d / %d" % _hist("b")[:2], "%d / %d" % _hist("c")[:2]],
            ["Best validation accuracy / F1", "%.4f / %.4f" % (_hist("a1")[3], _hist("a1")[2]), "%.4f / %.4f" % (_hist("a2")[3], _hist("a2")[2]),
             "%.4f / %.4f" % (_hist("b")[3], _hist("b")[2]), "%.4f / %.4f" % (_hist("c")[3], _hist("c")[2])],
            ["Training time (CPU, upper bound)", "about 24 min", "about 22 min", "about 53 min", "about 13 min"],
        ], widths=[1.6, 1.2, 1.2, 1.3, 1.3], size=9, align=["l", "c", "c", "c", "c"]),
        P(f"All routes use AdamW {c('adamw')} with weight decay 1e-4, a cosine-annealing learning-rate schedule over the planned epochs, and early stopping on the validation F1 with a patience of three epochs; the "
          "checkpoint with the best validation F1 is kept. Seeds are fixed for Python, NumPy and PyTorch. Training ran on the CPU of the development machine (Intel Core i5-12500, 6 cores / 12 threads, 15.7 GB of memory, "
          "no GPU) with PyTorch " + c("pytorch") + " 2.14.1. The times are wall-clock times from file timestamps on a PC that was shared with other jobs, so they are upper bounds. Route B, the most expensive, was planned for only 3 epochs; "
          "its best validation F1 came at epoch 2 and that checkpoint was kept."),
        FIG(F.fig("f04_training_curves.png"), "Training and validation curves of the four routes.", 5.4),

        H2("6.7 Evaluation Protocol"),
        P("The evaluation was designed so that every reported number can be recomputed. The four routes are run once over each evaluation set and the raw logits are cached; every later analysis (the "
          "fusion variants, the threshold sweep, the intervals and the calibration) is computed from those cached logits, so that the variants differ only in the fusion rule and not in the model outputs. "
          "Route B is evaluated with the same horizontal-flip averaging that the application uses."),
        TAB("Experiments run on the cached logits", ["Experiment", "Data", "What it answers"], [
            ["Clean evaluation", "2,000 test images", "Accuracy, precision, recall, F1, balanced accuracy, AUC and confusion matrix of each route and of the deployed ensemble"],
            ["Fusion ablation", "Same logits", "Do the weights and the two gates help? Variants: no gates, Gate 1 only, Gate 2 only, equal weights, probability averaging, majority vote"],
            ["Threshold sweep", "Same logits", "How do precision, recall and F1 move as the decision threshold on the fused fake probability changes from 0.1 to 0.9?"],
            ["Bootstrap intervals", "Same logits", "Is a difference in accuracy larger than sampling noise? 2,000 resamples, 95 % percentile interval"],
            ["Calibration", "Same logits", "Do the confidence values match accuracy? Expected calibration error with 15 bins"],
            ["Robustness", "1,000-image subset", "Accuracy after JPEG quality 60, half-size resample, 5 x 5 Gaussian blur (sigma 1) and Gaussian noise (sigma 6)"],
            ["Cross-domain probe", "600 images from another source", "Do the models transfer to full-resolution photographs and other generators?"],
            ["Failure analysis", "Same logits", "Which images are wrong, how large is their margin, which routes disagree?"],
        ], widths=[1.4, 1.5, 3.4], size=9, align=["l", "l", "l"]),
        P("The protocol has known weaknesses. The ensemble weights and gate values were fixed before the test set was scored, but the threshold sweep and the ablations are evaluated on the same test set, so any "
          "operating point chosen from them is optimistic. A single training run per route was made, so no run-to-run variance is available beyond the bootstrap interval. The robustness conditions are applied "
          "to 32-pixel images, where a half-size resample leaves a 16-pixel picture."),
    ]


# =====================================================================================================================
def application_blocks():
    return [
        H2("6.8 Application Architecture"),
        P(f"The application is a Flask service {c('flask')} with two blueprints and a React front end. app/__init__.py builds the Flask object, registers the blueprints and installs a JSON-aware handler for "
          "requests that exceed the upload limit. run.py reads an optional .env file (real environment variables win), tries to load the four models at start so the first request is fast, and starts the server "
          f"on 127.0.0.1:{F.API_PORT}; if the checkpoints are missing it still starts and reports the problem on /health."),
        P("Models are loaded lazily and once. inference.ensure_models_loaded checks that all four checkpoint files exist, builds each architecture, loads its weights, puts it in evaluation mode and stores it in a "
          "module-level dictionary under a lock, so concurrent first requests load only once. The device is CUDA when available and the CPU otherwise. Settings (ports, upload limit, file locations, weights, gate values, "
          "confidence thresholds, seed and demo credentials) live in app/config.py and can be overridden by VERIVISION_* environment variables."),
        P(f"The React application is built with Vite and served on port {F.WEB_PORT}. Its dev server proxies /api, /health and /artifacts to the Flask service, so the browser talks to a single origin and no "
          "cross-origin configuration is needed. The bearer token returned by the sign-in is kept in the browser's local storage and attached by a small fetch client; a 401 answer clears it and returns the user "
          "to the sign-in page. A Dockerfile and a compose file run the same two services with both ports published on 127.0.0.1 only."),

        H2("6.9 Explanation and Robustness Modules"),
        P("app/explainability.py wraps the pytorch-grad-cam library " + c("pytorch_grad_cam") + ". For a route and a predicted class it builds a GradCAM object on the route's target layer, computes the map for the "
          "one input image, blends it over the resized original with the library's overlay function and returns the overlay as a PNG data URL. The target layer is the last block of the feature extractor: "
          "features[-1] for the two EfficientNet routes and MobileNetV3, and layer4[-1] for ResNet50. The class used is the ensemble's predicted class, so the map explains the answer that was given; "
          "the hooks are released after each call. The overlays are produced for routes A1, B and C."),
        P("app/robustness.py produces three variants of the uploaded image in addition to the original: JPEG compression at quality 60, a bilinear half-size down-sampling followed by up-sampling to the "
          "original size, and a Gaussian blur with a 5 x 5 kernel and sigma 1.0. inference.predict_with_robustness runs the complete prediction on each variant, including the fusion, and reports the verdict of "
          "each plus a consistency string, the number of variants that agree with the original verdict over the number of valid variants (for example 3/4). The check is a stability indicator for the user; "
          "a low consistency means the verdict depends on fine detail that ordinary re-saving removes."),
        TAB("Configuration variables (app/config.py)", ["Variable", "Default", "Meaning"], [
            ["VERIVISION_HOST, VERIVISION_PORT", "127.0.0.1, 8414", "Address and port of the Flask service"],
            ["VERIVISION_MAX_UPLOAD_MB", "10", "Upload size limit"],
            ["VERIVISION_MODEL_A1, _A2, _B, _C", "models/*.pt", "Checkpoint file of each route"],
            ["VERIVISION_W_A1, _A2, _B, _C", "0.35, 0.15, 0.25, 0.25", "Fusion weights (normalised at run time)"],
            ["VERIVISION_GATE_TAU_B, _TAU_C, _CORRECTION", "2.5, 2.5, 0.75", "Gate thresholds and correction size"],
            ["VERIVISION_SEED", "42", "Random seed for data preparation and training"],
            ["VERIVISION_SECRET_KEY", "development string", "Signing key of the session token"],
            ["VERIVISION_DEMO_EMAIL, _PASSWORD, _NAME", "demo account", "Credentials of the demo sign-in"],
        ], widths=[2.3, 1.5, 2.5], size=9, align=["l", "l", "l"]),

        H2("6.10 API Design"),
        P("The API has nine endpoints, listed below. The three analysis endpoints take the image as a multipart form field named image. All errors on /api paths are JSON objects with an error message."),
        TAB("Endpoints of the VeriVision AI API", ["Method and path", "Token", "Request", "Success response", "Errors"], [
            ["GET /health", "no", "-", "status, models_loaded, device, error", "503 when models are missing"],
            ["GET /api/config", "no", "-", "max_mb, extensions, weights, routes, gates, confidence thresholds, model metadata, demo account", "-"],
            ["GET /api/insights", "no", "-", "available, ensemble, models, robustness, confusion_exists", "-"],
            ["GET /artifacts/confusion_matrix.png", "no", "-", "PNG image", "404 JSON if absent"],
            ["POST /api/auth/login", "no", "JSON email, password", "token, user", "401"],
            ["GET /api/auth/me", "yes", "Authorization: Bearer", "user", "401"],
            ["POST /api/analyze", "yes", "multipart image", "verdict, votes, Grad-CAM, robustness (below)", "400, 401, 413, 500, 503"],
            ["POST /api/predict", "no", "multipart image", "label, probabilities, confidence, confidence word, route labels, agreement", "400, 500, 503"],
            ["GET /, POST /predict, GET /insights", "no", "form upload", "Classic server-rendered pages", "error page: 400, 413, 500, 503"],
        ], widths=[1.6, 0.5, 1.1, 2.2, 1.0], size=8.5, align=["l", "c", "l", "l", "l"]),
        P("The /api/analyze response is a single JSON object: filename; the original image as a data URL; predicted_label, confidence, confidence_pct, confidence_word, prob_real and prob_fake; a branches list with "
          "key, name, label and the two probabilities of each route; cams with the Grad-CAM overlay of routes a1, b and c as data URLs (null for a route whose overlay failed); agreement_count; excluded_branch, "
          "gate1_reason, gate2_applied, gate2_reason and active_weights; robustness with the outcome of each variant and a consistency string such as 3/4; the device; and a note stating that the heat map is an "
          "explanation aid and not proof. /api/predict returns only the verdict fields and needs no token, which keeps the original JSON contract of the first version."),

        H2("6.11 Security and Error Handling"),
        P("The system is designed for local use and its security is proportionate to that. Access to /api/analyze needs a bearer token. The token is created with itsdangerous' URLSafeTimedSerializer, "
          "which signs the e-mail and issue time with the application secret and a fixed salt; it is valid for 12 hours and is rejected if it is missing, altered or expired. Sign-in compares the e-mail and "
          "the password with hmac.compare_digest, which takes the same time whatever the input, and gives the same message for a wrong e-mail and a wrong password. The credentials come from configuration "
          "(a demo account) and are not stored in a database."),
        P(f"Uploads are validated before any decoding. The file must be present and have an allowed extension (png, jpg, jpeg or webp), must not be empty and must not exceed {F.UPLOAD_LIMIT_MB} MB (enforced twice: "
          "by Flask's MAX_CONTENT_LENGTH, which answers 413, and by a size check). The bytes are then opened with Pillow and verified; a file that does not decode is refused, and so is an image smaller than 8 x 8 pixels. "
          "The image is held in memory only and is never written to disk by the API path, and the analysis is returned to the caller and not stored."),
        TAB("Error handling", ["Situation", "HTTP status", "Message shown to the user"], [
            ["Missing, forged or expired token", "401", "Please sign in to analyze images."],
            ["Wrong e-mail or password", "401", "Email or password is not correct."],
            ["No file, wrong extension, empty file, undecodable or tiny image", "400", "A specific sentence for each case (for example 'Unsupported file type')"],
            ["Upload larger than the limit", "413", "Image exceeds the 10 MB size limit."],
            ["Checkpoint file missing", "503", "Lists the missing files and points to the training workflow"],
            ["Unexpected inference or loading error", "500", "Generic message; the traceback goes to the server log only"],
        ], widths=[2.6, 0.9, 2.8], size=9.5, align=["l", "c", "l"]),
        P("Known limits of the security design are stated plainly. The demo account and its password are returned by /api/config so that the sign-in page can fill them; the default signing secret is a fixed "
          "development string unless VERIVISION_SECRET_KEY is set; /api/predict is open; there is no rate limiting, no HTTPS and no account management. The service binds to 127.0.0.1 by default, and the "
          "Docker files publish the ports on 127.0.0.1 only, so these limits are acceptable for a local demonstration but not for a public deployment."),

        H2("6.12 Installation and Execution"),
        P("The system runs on Windows 10 or 11 with Python 3.10 or newer (3.11 was used) and, for the web application, Node.js 20 or newer. No GPU is needed. The dependencies are pinned in requirements.txt "
          "(Flask 3.1.3, torch 2.14.1, torchvision 0.29.1, Pillow 13.0.0, numpy 2.4.6, scikit-learn 1.9.1, opencv-python-headless 5.0.0.93, grad-cam 1.5.7, pytest 9.1.1 and others); about 3 GB of disk space is needed "
          "for the packages and model files. There are three ways to run it."),
        N("**Automatic.** Double-click run.bat. It checks Python, creates .venv, installs the requirements, trains the models if no checkpoint exists, copies .env.example to .env, installs the web packages once, "
          f"starts the API on port {F.API_PORT} and the web application on port {F.WEB_PORT} in two windows and opens the browser. The demo login is {F.DEMO_EMAIL} / {F.DEMO_PASSWORD}.",
          "**Manual.** Create a virtual environment, install requirements.txt, prepare the data, run scripts/train_a1.py, train_a2.py, train_b.py and train_c.py, run scripts/evaluate.py, then python run.py; "
          "in a second terminal run npm install and npm run dev inside frontend/.",
          f"**Docker.** docker compose up --build starts the API and the web application with ports {F.API_PORT} and {F.WEB_PORT} published on 127.0.0.1; the models and artifacts folders are mounted into the container."),
        P("For this project's measured results the four routes were trained with scripts/prepare_cifake.py followed by the four training scripts with --epochs 5, 5, 5 and 3 and --data-root data/cifake, evaluated with "
          "scripts/run_cifake_experiments.py and installed with scripts/publish_cifake_models.py, which writes the checkpoints, the metadata and the metric files in the format the Insights page reads. "
          "Appendix B gives the full user guide."),
    ]


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
