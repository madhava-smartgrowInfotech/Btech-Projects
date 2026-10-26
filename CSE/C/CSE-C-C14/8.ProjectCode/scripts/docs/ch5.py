"""Chapter 5: System Design (VeriVision AI). doc12 reuses blocks()[1:]; diagrams come from diagram_index / docs/diagrams."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, PAIR, TAB
from .diagram_index import DIAGRAMS
from .refs import CITE as R

_D = {k: (t, f, c, p) for k, t, f, c, p in DIAGRAMS}


def dfig(key, width=5.6, max_h=6.2):
    """Real diagram from diagram_index; width limited so that its height stays below max_h inches."""
    _, f, cap, _ = _D[key]
    path = F.diag(f)
    return FIG(path, cap, F.shot_w(path, width, max_h))


def pfig(key):
    _, f, cap, _ = _D[key]
    return (F.diag(f), cap)


def pshot(name, caption):
    return (F.shot(name), caption)


def blocks():
    return ([H1("CHAPTER 5: SYSTEM DESIGN")] + _goals() + _workflow() + _dataflow() + _uml() + _database() + _modules()
            + _algorithm() + _ui() + _decisions())


# =====================================================================================================================
def _goals():
    return [
        P("This chapter turns the requirements of Chapter 4 into a design. It gives the architecture, the workflow of one analysis, the data flow diagrams, the UML models, "
          "the data model, the module design, the design of the core algorithm, the interface design and the reasons for the main decisions. Every diagram was drawn from the code in the "
          "repository (app/, scripts/ and frontend/) and not from a plan; all eleven are listed again, with explanations, in the block-diagram document."),

        H2("5.1 Design Goals and Architecture"),
        P("Five goals shaped the design. The first is **an explanation with every verdict**: a bare label is not credible in a dispute, so each answer carries per-route votes, "
          "Grad-CAM heat maps and a robustness check. The second is **heterogeneity**: four routes that differ in backbone, input size, loss and augmentation are combined, in the spirit of the "
          f"heterogeneous ensemble and gating of HEDGE [{R['hedge']}], so that one route's blind spot can be outvoted. The third is **local operation**: an uploaded image is decoded in memory, "
          "analysed on the machine and discarded, and no external service is called. The fourth is **CPU-only operation**: the models are small enough to answer in about two seconds on a "
          "desktop processor. The fifth is **honest degradation**: when a checkpoint is missing the API answers 503 and the Status page names the problem instead of guessing."),
        P(f"The architecture has four tiers. The presentation tier is a React single-page application served by Vite on port {F.WEB_PORT}; it has a landing page, a sign-in page and four workspace pages, "
          f"and a client module, lib/api.js, that calls the API with fetch and keeps the bearer token. The application tier is a Flask service on port {F.API_PORT}; its routes are split between "
          "app/routes.py (classic HTML pages, health and the original JSON predict) and app/api.py (demo sign-in, configuration, insights and analyze). The inference tier is PyTorch: app/inference.py "
          "loads the four models once and runs them, app/ensemble.py fuses the logits, and app/explainability.py and app/robustness.py produce the Grad-CAM overlays and the degraded variants. "
          "The data tier is a set of local files: four checkpoints, one metadata file, the evaluation artifacts and the dataset folders."),
        dfig("arch", 4.8, 3.0),
        TAB("Tiers, technologies and responsibilities", ["Tier", "Technology", "Responsibility"], [
            ["Presentation", "React, React Router, Vite, Recharts, Framer Motion", "Pages, upload form, verdict card, heat-map selector, charts, light and dark theme"],
            ["Application", "Flask 3.1 blueprints, itsdangerous signed tokens", "Routes, upload guards, demo sign-in, JSON error handler (400, 401, 413, 500, 503)"],
            ["Inference", "PyTorch 2.14, torchvision, pytorch-grad-cam, OpenCV, Pillow", "Preprocessing, four route models, logit fusion with gates, Grad-CAM, robustness variants"],
            ["Data", "Checkpoint .pt files, JSON, PNG, image folders", "Model weights, model metadata, evaluation artifacts, train / validation / test images"],
        ], widths=[1.0, 2.5, 2.8], size=10, align=["l", "l", "l"]),
        P("The inference modules are plain Python files of functions, not a class hierarchy. Each stage takes data and returns a dictionary, so it can be tested on its own, replaced without touching "
          "the others, and the whole analysis can be returned as one JSON object. The UML diagram in Section 5.4 draws these modules as classes only to show their responsibilities. The classic "
          "server-rendered pages of the first version remain available on the API port as a fallback."),
    ]


# =====================================================================================================================
def _workflow():
    return [
        H2("5.2 High-Level Workflow"),
        P("The workflow of the system is the workflow of one POST /api/analyze request, and it has ten stages. The image is validated (extension, size, non-empty, decodable) and converted to RGB. "
          "It is resized for each route and normalised with ImageNet statistics. The four routes return a pair of logits each, Route B averaging the original and a horizontally flipped copy. "
          "The pairs are fused with the configured weights and two gates into a verdict, a probability pair and a confidence word. Grad-CAM overlays are produced for three routes on the predicted class. "
          "The image is then re-tested under JPEG compression, a half-size resample and a Gaussian blur, and the number of variants that keep the original verdict is reported. "
          "The result is returned as one JSON object and displayed as a verdict card with tabs."),
        dfig("flow", 5.0, 3.1),
        P("There is one failure path that matters. If a checkpoint file is missing, ensure_models_loaded raises an error that lists the missing files, the analyze and predict endpoints answer 503, "
          "and /health reports status 'degraded' with the same message, which the Status page shows. If Grad-CAM fails for one route, that overlay is returned as null and the others are unaffected; "
          "if the robustness check fails, the consistency is reported as 'n/a'."),
        P("A second workflow runs offline and prepares the models. A dataset script builds class-balanced train, validation and test folders; each route is fine-tuned from ImageNet weights with "
          "its own augmentation, AdamW with cosine decay and early stopping on the validation F1; and an evaluation script measures every route and the ensemble and writes the JSON artifacts "
          "that the Insights page reads (diagram 11 of the block-diagram document)."),
    ]


# =====================================================================================================================
def _dataflow():
    return [
        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0: context"),
        P("At the context level VeriVision AI is one process with two actors and no external service. The user sends an image and the demo login and receives the verdict, the confidence, the "
          "per-route votes, the Grad-CAM overlays and the robustness result. The developer sends training and evaluation commands and receives checkpoints and metrics. "
          "The process reads and writes the model files and metric artifacts and, in training, reads the image folders."),
        dfig("dfd0", 4.6, 2.2),
        H3("5.3.2 Level 1: main processes"),
        P("Level 1 divides the system into seven processes over three stores: D1, the model checkpoints; D2, the model metadata; and D3, the metric artifacts. "
          "Process 2.0 loads D1 and D2 once, on the first request."),
        TAB("Level 1 processes and their data", ["No.", "Process", "Inputs", "Outputs", "Stores"], [
            ["1.0", "Validate and authenticate", "Image, demo login, token", "RGB image, 400 / 401 / 413 errors", "-"],
            ["2.0", "Preprocess and route logits", "RGB image", "Four logit pairs", "D1, D2 (read)"],
            ["3.0", "Fuse and gate", "Logit pairs, weights, gate settings", "Verdict, probabilities, confidence", "-"],
            ["4.0", "Explain (Grad-CAM)", "Image, predicted class", "Three heat-map overlays", "D1 (read)"],
            ["5.0", "Robustness re-check", "Image", "Verdicts on JPEG, resize, blur variants", "D1 (read)"],
            ["6.0", "Report insights", "Stored metrics", "Insights JSON, confusion matrix image", "D3 (read)"],
            ["7.0", "Train and evaluate", "Developer commands, image folders", "Checkpoints, metadata, metrics", "D1, D2, D3 (write)"],
        ], widths=[0.5, 1.5, 1.6, 1.8, 0.9], size=9.5, align=["c", "l", "l", "l", "l"]),
        dfig("dfd1", 4.8, 2.7),
        H3("5.3.3 Level 2: preprocessing, route logits and fusion"),
        P("Level 2 expands processes 2.0 and 3.0 into the steps of app/inference.py and app/ensemble.py."),
        P("The sub-processes are: 2.1 decode and resize (preprocessing.decode_image, Resize in inference._transform_for); 2.2 normalise with the ImageNet mean and standard deviation; 2.3a to 2.3d the route logits "
          "of A1, A2, B (with the flipped copy) and C (inference.branch_logits, reading D1); 3.1 Gate 1 (ensemble.apply_gate1); 3.2 the weighted logit sum (ensemble.fuse_logits); 3.3 Gate 2 (ensemble.apply_gate2); "
          "and 3.4 the softmax and confidence wording (ensemble.softmax, inference.confidence_word)."),
        dfig("dfd2", 4.8, 2.8),
    ]


# =====================================================================================================================
def _uml():
    return [
        H2("5.4 UML Diagrams"),
        H3("5.4.1 Class diagram"),
        P("FlaskApp, the application factory in app/__init__.py, registers two blueprints: Routes (app/routes.py) and Api (app/api.py). The Api blueprint reuses the analysis routine _run_analysis "
          "of Routes so that the classic page and the JSON endpoint return identical results. Both call Inference, which uses Preprocessing for validation and decoding, Models for the four "
          "architectures and their checkpoints, Ensemble for fusion and gating, Explainability for Grad-CAM and Robustness for the degraded variants. Config holds every tunable setting and can be "
          "overridden by environment variables. The training scripts reuse the model builders of Models. The modules are files of functions; they are drawn as classes to show responsibilities."),
        dfig("uml", 4.8, 3.4),
        H3("5.4.2 Sequence diagram"),
        P("The sequence diagram follows one analysis. The browser posts the image with its bearer token; api.py verifies the token (401 if it is missing, forged or older than twelve hours), makes sure the "
          "models are loaded (503 if not), validates and decodes the upload (400 on failure) and calls predict_image. Inference runs the four forward passes and asks Ensemble for the fused result. "
          "api.py then asks Explainability for the three overlays and Inference for the robustness check, assembles one dictionary and returns it as JSON."),
        dfig("seq", 4.8, 3.0),
        H3("5.4.3 Use-case diagram"),
        P("There are two actors. The user signs in with the demo account, uploads an image, reads the verdict and confidence, inspects the per-route votes, opens the Grad-CAM heat map and checks the "
          "robustness consistency; the user can also read the model insights and the system status. The developer reads the same insights and status pages and prepares data, trains and evaluates the models "
          "with the scripts. The verdict, votes, heat map and robustness all depend on an uploaded image."),
        dfig("uc", 4.0, 2.7),
    ]


# =====================================================================================================================
def _database():
    return [
        H2("5.5 Data Model and Storage Design"),
        P("VeriVision AI has **no relational database**. The system keeps no user accounts (one demo account is configured), no history of analyses and no uploaded images, so a database would add a "
          "dependency without adding a capability. Everything that persists is a file, and the entity-relationship diagram below shows those files and their relations. The two entities at the bottom, "
          "SessionToken and UploadBuffer, exist only inside a request and are never stored."),
        dfig("er", 4.8, 2.5),
        TAB("Persisted and runtime data", ["Entity", "Where", "Content", "Written by", "Read by"], [
            ["ModelCheckpoint", "models/*.pt", "state_dict, best validation F1, training history, route, resolution", "scripts/common.train_one_model", "models.load_branch_model"],
            ["ModelMetadata", "models/model_metadata.json", "model name, branch, training dataset, resolution, class mapping, checkpoint path, scores", "scripts/evaluate.py or scripts/publish_cifake_models.py", "GET /api/config"],
            ["MetricsArtifact", "artifacts/metrics/", "model, ensemble and robustness JSON; confusion_matrix.png", "scripts/evaluate.py or scripts/publish_cifake_models.py", "GET /api/insights, /artifacts/confusion_matrix.png"],
            ["ImageSample", "data/train|val|test/real|fake", "PNG images; label 0 = REAL, 1 = AI_GENERATED from the folder name", "scripts/prepare_*.py", "scripts/common.collect_split"],
            ["SessionToken", "browser only", "email and issue time, signed, 12 h maximum age", "api.login", "api.login_required"],
            ["UploadBuffer", "RAM", "uploaded bytes and the decoded RGB image", "preprocessing", "inference, explainability"],
        ], widths=[1.1, 1.2, 2.0, 1.1, 1.1], size=9, align=["l", "l", "l", "l", "l"]),
        P("The class mapping 0 = REAL and 1 = AI_GENERATED is defined once, in app/config.py, and is used by training, inference, Grad-CAM and the interface. The scores stored in the "
          "metadata file and the metric files are written from the held-out test evaluation (by evaluate.py, or in this project by publish_cifake_models.py from experiments/cifake/metrics.json, in the same format), "
          "so the Insights and How-it-works pages read measured values and never typed ones."),
    ]


# =====================================================================================================================
def _modules():
    return [
        H2("5.6 Module Design"),
        P("The back end has eleven modules, each with one responsibility. The table lists them with their main functions and line counts, which show that the whole serving code is small enough to be read "
          "in one sitting."),
        TAB("Back-end modules (app/)", ["Module", "Lines", "Responsibility", "Main functions"], [
            ["__init__.py", "29", "Application factory; JSON-aware 413 handler", "create_app"],
            ["config.py", "69", "All settings, environment overrides, class mapping, weights, gates", "constants"],
            ["preprocessing.py", "88", "Upload validation and decoding", "validate_upload, decode_image, PreprocessingError"],
            ["models.py", "83", "Architectures and checkpoint loading", "build_efficientnet_b0, build_resnet50, build_mobilenetv3_large, load_branch_model"],
            ["inference.py", "143", "Model cache, route logits, flip TTA, verdict, robustness check", "ensure_models_loaded, branch_logits, predict_image, predict_with_robustness"],
            ["ensemble.py", "129", "Logit fusion and the two gates", "fuse_logits, apply_gate1, apply_gate2, ensemble_predict, softmax"],
            ["explainability.py", "80", "Grad-CAM overlays and data-URL helpers", "generate_gradcam_overlay, pil_to_data_url"],
            ["robustness.py", "34", "JPEG, resize and blur variants", "make_variants"],
            ["routes.py", "197", "Classic pages, health, original JSON predict, shared analysis", "health, predict, api_predict, insights, _run_analysis"],
            ["api.py", "140", "Demo sign-in, config, insights, protected analyze", "login, me, get_config, insights, analyze, login_required"],
            ["run.py", "-", "Entry point, .env reader, model pre-load, server start", "app.run on 127.0.0.1:8414"],
        ], widths=[1.2, 0.5, 2.3, 2.3], size=9, align=["l", "c", "l", "l"]),
        P("Around the serving code sit the scripts and the front end. The data scripts (prepare_dataset.py, prepare_cifake.py, prepare_xdomain.py) build the image folders; common.py and train_a1.py, "
          "train_a2.py, train_b.py and train_c.py hold the augmentation, the focal loss, the training loop with early stopping and the per-route freezing rules; evaluate.py, run_cifake_experiments.py and "
          "measure_latency.py produce the metrics, the ablations, the robustness and cross-domain results and the timings; smoke_test.py and two pytest files check the system. The front end has seven routes "
          "(landing, sign-in, four workspace pages and a fallback page) and a lib/ folder with the fetch client, the session, the analysis state and the theme."),
    ]


# =====================================================================================================================
def _algorithm():
    w = F.WEIGHTS
    return [
        H2("5.7 Design of the Core Algorithm"),
        P(f"The core algorithm is the fusion of the four route outputs. Each route returns a pair of raw logits. The weights are {w['a1']:.2f} for A1, {w['a2']:.2f} for A2, {w['b']:.2f} for B and "
          f"{w['c']:.2f} for C; they are normalised at run time so that any positive set works. Two deterministic gates operate on the logits and never on probabilities. "
          f"Gate 1 removes Route B when its margin |l_fake - l_real| is at least {F.GATE_TAU_B} and all three other routes point to the other class; the remaining weights are renormalised. "
          f"Gate 2 acts after the weighted sum: when B and C agree on a class with margins of at least {F.GATE_TAU_B} and {F.GATE_TAU_C}, and the fused direction is the opposite one, "
          f"the fused logits are nudged toward the B and C class by {F.GATE_CORR}, the winning logit rising by that amount and the other falling by half of it. A softmax then gives the probabilities; "
          f"the larger is the confidence, shown as High at {F.CONF_HIGH:.2f} or more, Moderate at {F.CONF_MOD:.2f} or more and Low below that."),
        dfig("flowchart", 4.4, 3.0),
        P("The design deliberately keeps every step visible. The response carries the per-route labels and probabilities, the active weights after Gate 1, a sentence for each gate "
          "saying whether it fired and why, and the number of routes that agree with the final label, so that a reader can reconstruct the verdict by hand. "
          f"The gate values are engineering defaults taken in the spirit of the dual gating in HEDGE [{R['hedge']}], not values tuned for this project; Chapter 8 reports that on the held-out test set "
          "Gate 1 fired on 7 of 2,000 images and Gate 2 on none."),
        P("Explanation follows the same rule. Grad-CAM [%d] is computed with the pytorch-grad-cam library [%d] on the last convolutional block of the route (features[-1] for A1 and C, layer4[-1] "
          "for B), for the class the ensemble predicted, and is blended over the input image. It is offered for three of the four routes: A2 shares its architecture with A1 and was left out to keep the "
          "response small. The interface states that a heat map is an explanation aid and not proof of authenticity." % (R["gradcam"], R["pytorch_grad_cam"])),
    ]


# =====================================================================================================================
def _ui():
    return [
        H2("5.8 User Interface Design"),
        P("The interface is a single-page React application with a fixed side navigation, a status chip showing whether the API is online and on which device it runs, a theme switch and a sign-out button. "
          "It was designed around the order of a user's questions: what is the answer, how sure is it, who voted, where did the models look, and how stable is the answer. "
          "The Analyze page therefore shows the verdict card first, then the branch votes next to the robustness check, then the Grad-CAM heat maps with one tab per route."),
        TAB("Pages of the web application", ["Page", "Route", "Purpose", "Data source"], [
            ["Landing", "/", "Introduction, headline measured numbers, how the system works", "GET /api/insights, /api/config"],
            ["Sign in", "/login", "Demo account sign-in with a button that fills the demo credentials", "POST /api/auth/login, GET /api/config"],
            ["Analyze image", "/app", "Upload, verdict, votes, Grad-CAM, robustness", "POST /api/analyze"],
            ["Model insights", "/app/insights", "Held-out metrics, confusion matrix, clean-versus-degraded chart", "GET /api/insights"],
            ["How it works", "/app/models", "The four routes: backbone, input size, loss, fusion weight, trained-on, validation F1", "GET /api/config"],
            ["System status", "/app/status", "Live /health answer: API, models loaded, device; upload rules", "GET /health, /api/config"],
        ], widths=[1.1, 0.8, 3.1, 1.3], size=9.5, align=["l", "l", "l", "l"]),
        PAIR([pshot("05_analyze_ready.png", "Analyze page with an image chosen and the four steps explained on the right."),
              pshot("09_result_gradcam.png", "Grad-CAM tab: original image beside the EfficientNet heat map.")], 2.9),
        P("Several choices keep the interface honest. Every number on the Insights and How-it-works pages is read from the API and so from the evaluation files. The verdict is worded as "
          "'Likely AI-generated' or 'Likely real', never as a certainty, and the confidence word is shown with the percentage. Errors from the API are shown as readable messages. "
          "Light and dark themes are both supported, and the upload area opens the file picker from the keyboard (Enter or Space)."),
    ]


# =====================================================================================================================
def _decisions():
    return [
        H2("5.9 Design Decisions and Their Reasons"),
        TAB("Principal design decisions", ["Decision", "Alternative", "Reason"], [
            ["Four small CNN routes, ImageNet-pretrained, upper blocks fine-tuned", "One large foundation-model detector", "Trainable on a CPU in minutes to under an hour per route; large backbones need GPUs (HEDGE used eight H800 cards)"],
            ["Heterogeneous routes (backbone, size, loss, augmentation)", "Four copies of one model", "Different inductive biases make errors less correlated; Chapter 8 measures how much this helps"],
            ["Fusion in logit space", "Averaging probabilities, majority vote", "Keeps the strength of each route's evidence; Chapter 8 compares all three on the same logits"],
            ["Two deterministic gates", "Learned meta-classifier", "No extra training data needed and the rule can be read in the response; the gates did not improve results here"],
            ["Robustness re-check in the response", "Report only the verdict", "Social-media compression removes cues; the user sees whether the verdict survives it"],
            ["File-based storage, no database", "A relational database", "Nothing needs to be stored between requests; images are never kept"],
            ["Flask API plus React front end, classic pages kept", "Single server-rendered app", "The React app gives the richer result view; the classic pages stay as a fallback and keep the original JSON contract"],
        ], widths=[2.0, 1.7, 2.6], size=9.5, align=["l", "l", "l"]),
        P("The design has known weaknesses that Chapters 7 and 8 make visible. The gates add complexity for no measured gain, the fusion weights were set by hand rather than fitted, the models see only "
          "a resized copy of the image and so cannot use full-resolution detail, and nothing in the design protects against an adversary who knows the models."),
    ]
