"""Chapter 6: Methodology and Software Implementation for Mosaic.

methodology_blocks()  - document 9 (H2/H3 only, renumbered by build_docs.renum)
application_blocks()  - document 12 (H2/H3 only)
blocks()              - the report chapter (H1 + both parts, numbered 6.1 ... by renum)
"""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB, renum
from .refs import CITE as R


def _ref(*keys):
    return ", ".join(f"[{R[k]}]" for k in keys)


def _pc(x, d=2):
    return f"{x * 100:.{d}f} %"


def _lat(label_part):
    """p50 / p95 of the API latency row whose label contains label_part (None when the API was not measured)."""
    if not F.APIM:
        return None
    for r in F.APIM["latency"]:
        if label_part in r["label"]:
            return r
    return None


def methodology_blocks():
    D, N7, G, B7 = F.DATA, F.FIN, F.GAN, F.BASE
    cc = D["class_counts"]
    b = []
    b += [H2("Overall Methodology"),
          P("The method follows the analysis-by-synthesis idea of the base paper " + _ref("base") + ": a generative model synthesises faces that carry two emotions at once, and a multi-label recogniser is trained on real and synthetic faces together. "
            "Mosaic realises the idea at a deliberately small scale so that every stage runs on a CPU in minutes. Training is offline and has three stages that share one label order (seven basic emotions followed by eleven compound ones, 18 outputs in all); "
            "serving is online and handles one uploaded image per request. The label order is defined once in `ml/taxonomy.py`, and training, synthesis, inference and the API all import it, so an output index means the same thing everywhere."),
          N("**Load the data** (offline): decode the 28,709 training and 7,178 test FER2013 faces, convert to grayscale, resize from 48 by 48 to 64 by 64 pixels.",
            "**Stage 1, backbone**: train a seven-class softmax CNN on the real faces with class-weighted cross-entropy (five epochs). It is the single-label baseline and later the initialiser of the final model.",
            "**Stage 2, cEmoGAN**: train a conditional GAN on a class-balanced subset of 400 real faces per class (2,800 faces, ten epochs); the condition is a seven-element emotion vector.",
            "**Stage 3a, synthesis**: for each of the eleven compound classes draw 200 noise vectors and condition the generator on its two component emotions at weight 0.5 each; label every synthetic face with both basic bits and the compound bit.",
            "**Stage 3b, final classifier**: train the 18-output CNN with binary cross-entropy on the 28,709 real faces (one basic bit each) plus the 2,200 synthetic faces, starting from the backbone's convolutional weights (five epochs).",
            "**Serve**: for each uploaded image, detect the largest face with a Haar cascade, crop it in grayscale, resize to 64 by 64, run the CNN, apply a sigmoid to the 18 logits, sort the basic and compound lists, and report the largest of all 18 scores as the dominant emotion.",
            "**Evaluate**: basic-emotion accuracy and macro-F1 on the FER2013 test set against the single-label baseline, a seeded ablation with and without the synthetic faces, diagnostics of the generator and of the compound outputs, and measurements of the API."),
          FIG(F.diag("11_flowchart_training.png"), "Training pipeline of Mosaic: backbone, cEmoGAN, compound synthesis and the final multi-label classifier.", 4.9),
          ]
    b += [H2("Dataset"),
          P(f"The data is FER2013 {_ref('fer2013')}, the 48 by 48 pixel grayscale facial-expression set collected for a 2013 machine-learning challenge, in the copy published on the Hugging Face Hub as `Jeneral/fer-2013` (tagged apache-2.0 there; the original competition terms are not restated by the mirror, so the licence should be checked before redistribution). "
            f"The product loads it from two pickled lists, `data/train.pt` and `data/test.pt`, whose items are a JPEG byte string and an emotion name. The split is the one shipped by the mirror: {D['n_train']:,} training and {D['n_test']:,} test images. "
            "There is no separate validation split; the test set is evaluated after every epoch for the log line but nothing is selected on it, because every run trains for a fixed number of epochs and keeps the last weights."),
          TAB("FER2013 class counts as loaded by the product", ["Split"] + [k.capitalize() for k in F.BASIC] + ["Total"],
              [["Train"] + [f"{cc['train'][k]:,}" for k in F.BASIC] + [f"{D['n_train']:,}"],
               ["Test"] + [f"{cc['test'][k]:,}" for k in F.BASIC] + [f"{D['n_test']:,}"]],
              widths=[0.8, 0.7, 0.7, 0.6, 0.7, 0.6, 0.8, 0.8, 0.7], align=["l"] + ["r"] * 8, size=9.5),
          P(f"Two properties of the data matter for everything that follows. First, the classes are imbalanced: disgust has {cc['train']['disgust']:,} training images (1.5 %) against {cc['train']['happy']:,} for happy, and always predicting happy would score {_pc(D['test_majority_baseline'], 1)} on the test set. "
            "Second, FER2013 carries **one basic label per image and no compound labels at all**. The eleven compound outputs therefore have no real ground truth anywhere in the project: they can be trained only from synthetic faces and can be checked only against synthetic faces. "
            f"The base paper used three small laboratory sets (CK+ {_ref('ckplus')}, JAFFE and MUG) and built its two-emotion ground truth by morphing pairs of peak frames, which Mosaic does not do; the datasets, the label sets and the evaluation therefore differ, and Chapter 8 compares the two only qualitatively."),
          ]
    b += [H2("Preprocessing"),
          H3("Training pipeline"),
          P("`ml/dataset.py` decodes each JPEG with Pillow into an 8-bit grayscale array, resizes it to 64 by 64 with OpenCV's default bilinear interpolation, and maps the label string to the product's own index. "
            "The mapping goes through the string, not through the dataset's integer codes, because the mirror's order (neutral before sad) differs from the product's order. Every training script then scales pixels to the range minus one to one, `x = (p / 255 - 0.5) / 0.5`, which matches the generator's `tanh` output. "
            "No augmentation (flips, crops, rotations) is applied. For the GAN, `cap_per_class=400` keeps the first 400 images of each class, giving 2,800 faces and a perfectly balanced set at the cost of discarding about 90 % of the data."),
          H3("Serving pipeline"),
          P("At request time the image is decoded with Pillow, converted to RGB and then to BGR for OpenCV, and passed to `detect_largest_face()`, which converts to grayscale and calls `CascadeClassifier.detectMultiScale` with scale factor 1.1, five neighbours and a minimum size of 40 by 40 pixels "
            f"{_ref('viola', 'opencv')}. The detection with the largest area is cropped from the grayscale image (no margin, no alignment, no histogram equalisation) and goes through the same resize and scaling as in training. "
            "The detector's minimum size of 40 pixels is almost as large as a native 48-pixel FER2013 image, so un-enlarged FER2013 faces are not found at all; the measurements in Chapter 8 quantify this and also show that a tight Haar crop is framed differently from the training faces. "
            "This training-serving mismatch is a limitation of the design, not of the data."),
          ]
    b += [H2("Algorithm Choice and Justification"),
          P("Every algorithm is the smallest one that does the job on the available hardware. The justifications below are the reasons recorded in the code and README, supplemented by the constraints of this project (a CPU-only machine, a one-hour training budget, no compound labels)."),
          TAB("Algorithms chosen, the reason and the alternative", ["Component", "Choice", "Why", "Alternative not used"],
              [["Face detection", "OpenCV Haar cascade", "ships with OpenCV, no extra download, fast on CPU", "MTCNN or a learned detector: more robust, heavier"],
               ["Recogniser", "4-block CNN, 770,130 parameters", "trains in minutes on CPU; same family as the base paper's small CNN", "ResNet or ViT transfer learning: stronger, needs pre-trained weights and more compute"],
               ["Basic-only baseline", "softmax + class-weighted cross-entropy", "the standard single-label formulation; weights counter the 1.5 % disgust class", "focal loss or re-sampling"],
               ["Multi-label head", "18 sigmoids + BCE", "a face may carry two emotions at once, so labels are not mutually exclusive", "softmax over 18 classes (forces one label)"],
               ["Generator", "conditional DCGAN (transposed convolutions)", "the condition vector lets one model produce every class, as in the base paper's cGAN part", "StyleGAN or the base paper's encoder + cGAN for identity-preserving latents"],
               ["Compound synthesis", "0.5 / 0.5 blend of two one-hot conditions", "needs no compound training data; mirrors the base paper's multi-hot condition", "morphing real pairs (base paper's ground truth)"],
               ["Optimiser", "Adam", "robust defaults for small CNNs and GANs " + _ref("adam"), "SGD with momentum"],
               ["Regularisation", "batch normalisation, dropout 0.4", "stabilise training, limit over-fitting of the 256-unit layer " + _ref("bn", "dropout"), "weight decay, data augmentation"]],
              widths=[1.1, 1.5, 2.2, 1.9], align=["l", "l", "l", "l"], size=9.0),
          P("One honest difference from the base paper deserves a sentence. The base paper's central contribution is an encoder that maps a face to a latent code so that identity is kept while the label changes the expression. "
            "Mosaic's generator takes a random noise vector and a label vector only; it has **no encoder and no identity-preservation mechanism**, so objective 1 of the batch (identity-preserving generation) is not implemented, and the synthetic faces are random faces with a requested expression, not edited versions of a given face."),
          ]
    b += [H2("Mathematical Formulation"),
          P("Notation: an image is `x`, the true basic class is `y`, there are K = 7 basic classes and L = 18 labels, `n_c` is the number of training images of class c, N is the training-set size and `z` is a noise vector with 100 elements."),
          H3("Stage 1: weighted softmax cross-entropy"),
          EQ("w_c = N / (K · n_c)"),
          EQ("p(c | x) = exp(s_c) / Σ_k exp(s_k),    L₁ = − w_y · log p(y | x)"),
          P(f"The class weights `w_c` are computed from the training labels (`class_weights()` in `ml/dataset.py`). With N = {D['n_train']:,} and K = 7 the weight of disgust is {D['n_train'] / (7 * cc['train']['disgust']):.2f} and that of happy "
            f"{D['n_train'] / (7 * cc['train']['happy']):.2f}, so a disgust image counts about {cc['train']['happy'] / cc['train']['disgust']:.1f} times as much as a happy one in the loss."),
          H3("Stage 3b: multi-label sigmoid and binary cross-entropy"),
          EQ("σ(s) = 1 / (1 + e^(−s)),    t ∈ {0, 1}^18"),
          EQ("L₃ = − (1/L) Σ_j [ t_j · log σ(s_j) + (1 − t_j) · log(1 − σ(s_j)) ]"),
          P("A real face has exactly one basic bit set in `t`; a synthetic face has the two basic bits of its compound and the compound bit set (three ones). The loss is the unweighted mean over the 18 outputs (`BCEWithLogitsLoss`, no positive weighting), so a rare positive label contributes little unless the model can separate it. "
            f"At serving time the score of label j is σ(s_j) and the dominant emotion is the arg-max over all 18 scores; the basic prediction used in the evaluation is the arg-max over the first seven. The multi-label formulation follows {_ref('multilabel')} and the base paper."),
          H3("Stage 2: the conditional GAN objective as implemented"),
          EQ("L_D = BCE(D(x | y), 0.9) + BCE(D(G(z | y) | y), 0)"),
          EQ("L_G = BCE(D(G(z | y) | y), 0.9)"),
          P(f"`BCE(·, t)` is binary cross-entropy with logits against the target `t`. Two details differ from the textbook minimax game {_ref('gan', 'cgan')}: the real-label target is smoothed to 0.9, and the generator minimises the non-saturating loss against the same smoothed target, not against 1. "
            "`D` receives the image and the condition, the condition being projected to 16 values and concatenated with the 4,096 image features. Both networks use Adam with learning rate 2·10⁻⁴ and β₁ = 0.5. "
            "During training the condition `y` is always a **one-hot** vector; the blended vector used for compound synthesis never appears in training, which is the weak point of the design analysed in Chapter 8."),
          H3("Compound condition and labels"),
          EQ("y(a, b) = 0.5 · e_a + 0.5 · e_b,    t(a, b) = e_a + e_b + e_(a·b)"),
          P("`e_a` is the one-hot vector of basic emotion a in the seven-element condition space and `e_(a·b)` the unit vector of the compound label in the 18-element target space. For example, `happily_surprised` uses the condition with 0.5 at happy and 0.5 at surprise and the target with ones at happy, surprise and happily_surprised."),
          H3("Evaluation quantities"),
          EQ("F1_c = 2 · P_c · R_c / (P_c + R_c),    macro-F1 = (1/K) Σ_c F1_c"),
          EQ("d²(μ₁, Σ₁; μ₂, Σ₂) = ‖μ₁ − μ₂‖² + Tr(Σ₁ + Σ₂ − 2 (Σ₁ Σ₂)^(1/2))"),
          P(f"Accuracy and macro-F1 are computed on the 7,178 test faces with scikit-learn. The second formula is the Fréchet distance between two Gaussians {_ref('fid')}; the project applies it to the 256-unit hidden layer of the stage-1 CNN, not to Inception features, to compare generated faces with real ones. "
            "It is a diagnostic of this project's own models and is not comparable with published FID values. The multi-label scores of the base paper (f-beta and exact-match ratio) are also computed on a synthetic hold-out set in `scripts/run_experiments.py`."),
          ]
    arch = [["1", "Conv 3×3, 1 → 32, BatchNorm, ReLU, MaxPool 2", "32 × 32 × 32", "384"],
            ["2", "Conv 3×3, 32 → 64, BatchNorm, ReLU, MaxPool 2", "64 × 16 × 16", "18,624"],
            ["3", "Conv 3×3, 64 → 128, BatchNorm, ReLU, MaxPool 2", "128 × 8 × 8", "74,112"],
            ["4", "Conv 3×3, 128 → 128, BatchNorm, ReLU, MaxPool 2", "128 × 4 × 4", "147,840"],
            ["5", "Flatten, Linear 2,048 → 256, ReLU, Dropout 0.4", "256", "524,544"],
            ["6", "Linear 256 → 18 (7 in the stage-1 backbone)", "18", "4,626"]]
    b += [H2("Model Architecture and Training"),
          H3("The recogniser"),
          P(f"`EmotionCNN` has four convolution blocks that halve the resolution each time (64 → 32 → 16 → 8 → 4) while growing the channel count from 1 to 128, followed by a 256-unit hidden layer and an output layer. "
            f"The same class serves as the 7-output backbone (767,303 parameters) and the 18-output final model ({N7['parameters']:,} parameters); only the last layer differs, so the backbone's `features.*` weights (240,960 parameters) can initialise the final model."),
          TAB("Layers of EmotionCNN with 18 outputs", ["#", "Layer", "Output shape", "Parameters"], arch + [["", "**Total**", "", f"{N7['parameters']:,}"]],
              widths=[0.4, 3.6, 1.4, 1.1], align=["c", "l", "c", "r"], size=9.5),
          H3("The generator and the discriminator"),
          P(f"The generator maps the 107-element input (100 noise values plus the 7-element condition, reshaped to 1 × 1) through five transposed convolutions to a 64 by 64 image with a `tanh` output: {G['generator_parameters']:,} parameters. "
            "The discriminator has four strided convolutions (32, 64, 128, 256 channels, LeakyReLU 0.2) whose 4,096 features are concatenated with the condition projected to 16 values and mapped to one logit: 694,257 parameters. Only the generator is used afterwards."),
          TAB("Layers of the conditional generator", ["Layer", "Output shape", "Parameters"],
              [["ConvTranspose 4×4, 107 → 256, BatchNorm, ReLU", "256 × 4 × 4", "438,528 + 512"],
               ["ConvTranspose 4×4 stride 2, 256 → 128, BatchNorm, ReLU", "128 × 8 × 8", "524,416 + 256"],
               ["ConvTranspose 4×4 stride 2, 128 → 64, BatchNorm, ReLU", "64 × 16 × 16", "131,136 + 128"],
               ["ConvTranspose 4×4 stride 2, 64 → 32, BatchNorm, ReLU", "32 × 32 × 32", "32,800 + 64"],
               ["ConvTranspose 4×4 stride 2, 32 → 1, Tanh", "1 × 64 × 64", "513"]],
              widths=[3.7, 1.3, 1.4], align=["l", "c", "r"], size=9.5),
          H3("Training configuration"),
          TAB("Training configuration copied from the defaults of the three training scripts", ["Item", "Stage 1 backbone", "Stage 2 cEmoGAN", "Stage 3 final classifier"],
              [["Script", "`train_classifier_stage1.py`", "`train_gan.py`", "`train_final_classifier.py`"],
               ["Training images", f"{D['n_train']:,} real", "2,800 real (400 per class)", f"{D['n_train']:,} real + 2,200 synthetic"],
               ["Targets", "class index (7)", "one-hot condition (7)", "multi-hot (18)"],
               ["Loss", "weighted cross-entropy", "BCE-with-logits, real label 0.9", "BCE-with-logits"],
               ["Optimiser", "Adam, lr 1·10⁻³", "Adam, lr 2·10⁻⁴, β = (0.5, 0.999)", "Adam, lr 5·10⁻⁴"],
               ["Batch size", "256", "64 (last partial batch dropped)", "256"],
               ["Epochs", "5", "10", "5"],
               ["Initialisation", "random", "random", "`features.*` from stage 1"],
               ["Seeds, augmentation", "not set, none", "not set, none", "not set, none"],
               ["Device", "CPU", "CPU", "CPU"],
               ["Logged result", "test accuracy 50.56 %", "final losses D 0.7731, G 3.7240", "test accuracy 58.14 % (basic outputs)"]],
              widths=[1.3, 1.6, 1.9, 1.9], align=["l", "l", "l", "l"], size=9.0),
          P("The product's own `training_log.txt` records those three result lines. Stage 3 had not been run when the project was received (the final checkpoint was missing and the API reported that no model was loaded), so it was run for this report with the unchanged script on the shared CPU-only Windows PC used for the work: "
            "epochs took 153, 126, 129, 115 and 97 seconds (10 minutes 37 seconds in total). The scripts do not set random seeds; to make the comparisons in Chapter 8 repeatable, `scripts/run_experiments.py` re-trains the final classifier with explicit seeds for the with-synthetic and without-synthetic variants."),
          H3("Evaluation protocol"),
          B("**Basic emotions:** accuracy, macro-F1, per-class precision, recall and F1 and the confusion matrix on the 7,178 test faces, for the stage-1 baseline and the final model (arg-max over the seven basic outputs).",
            "**Ablation:** the final classifier trained with and without the synthetic faces, same initialisation and epochs, several seeds, plus a sweep over the number of synthetic faces per compound class.",
            "**Compound outputs:** their scores on real test faces, and the multi-label metrics (micro- and macro-F1, exact-match ratio, ROC-AUC) on 1,100 freshly generated hold-out faces, with a real-data-only control. Because the hold-out comes from the same generator that produced the training faces, it measures whether the classifier learned the generator's labels, not whether it recognises real compound expressions.",
            "**Generator:** how often the stage-1 classifier reads a generated face as the requested emotion, and the Fréchet distance in its feature space.",
            "**Serving:** Haar detection rate by image size, accuracy through the serving path against direct resizing, API latency and malformed-input probes, and the automated tests."),
          ]
    return b


def application_blocks():
    t = F.TESTS
    an = _lat("anonymous")
    lg = _lat("login")
    b = []
    b += [H2("Application Architecture"),
          P("Mosaic is a two-process application: a FastAPI service " + _ref("fastapi") + " that wraps the models, and a Next.js console " + _ref("nextjs") + " that talks to it. They share nothing but the HTTP contract in `API_CONTRACT.md`. "
            "The service holds one loaded model in memory (loaded at start-up by `load_model()` and kept in a module-level variable) and keeps accounts and history in a SQLite file. No external service is called at run time."),
          FIG(F.diag("01_system_architecture.png"), "Application architecture of Mosaic: browser, FastAPI service, ML modules and local files.", 5.6),
          TAB("Backend modules", ["File", "Responsibility"],
              [["`app/main.py`", "creates the application, CORS middleware, mounts `/api/media/thumbs`, includes the four routers, loads the model on start-up (a missing checkpoint is tolerated)"],
               ["`app/config.py`", "secret key (environment variable `MOSAIC_SECRET_KEY`, otherwise a development default), HS256, token lifetime (7 days), SQLite URL, checkpoint and thumbnail folders, CORS origins"],
               ["`app/db.py`, `app/models.py`", "SQLAlchemy engine, session dependency, `User` and `Analysis` tables"],
               ["`app/security.py`, `app/deps.py`", "bcrypt hashing and verification, token creation and decoding, required and optional current-user dependencies"],
               ["`app/schemas.py`", "pydantic request and response models (password at least six characters)"],
               ["`app/routers/auth.py`", "register, login, me"],
               ["`app/routers/analyze.py`", "image upload, inference call, optional persistence and thumbnail"],
               ["`app/routers/history.py`", "paged list, single item, delete, all restricted to the owner"],
               ["`app/routers/health.py`", "status and whether the model is loaded"],
               ["`app/ml/*`", "taxonomy, face detection, preprocessing, CNN, GAN, dataset loading, training scripts, inference"]],
              widths=[1.9, 4.5], align=["l", "l"], size=9.0),
          P("The console is a Next.js 16 application written in TypeScript with Tailwind CSS. `lib/api.ts` wraps `fetch` and adds the Bearer token; `lib/store.ts` keeps the token and user in a persisted zustand store (`mosaic-auth` in local storage); "
            "`lib/taxonomy.ts` and `lib/emotionColors.ts` mirror the label set. The landing page uses a Three.js canvas, GSAP and Lenis smooth scrolling; the product screens are `/app` (upload or webcam capture and the result), `/app/history` and `/app/history/[id]`. "
            "`ResultsView` draws the dominant card, a Recharts bar chart of the seven basic scores and horizontal bars for the six highest compound scores; the backend still returns all eleven."),
          ]
    b += [H2("API Design"),
          P("The API is JSON over HTTP with one multipart endpoint. All paths start with `/api`. The contract fixes the 18 label keys, so the console never reformats snake_case itself: every item carries `key`, a display `label` and a `confidence` between 0 and 1."),
          TAB("Endpoints", ["Method and path", "Auth", "Request", "Success", "Errors"],
              [["POST /api/auth/register", "no", "JSON name, email, password", "201 token + user", "409 e-mail exists; 422 short password"],
               ["POST /api/auth/login", "no", "JSON email, password", "200 token + user", "401 invalid credentials"],
               ["GET /api/auth/me", "required", "-", "200 user", "401"],
               ["POST /api/analyze", "optional", "multipart field `image`", "200 analysis (stored when signed in)", "422 missing field; 500 undecodable file"],
               ["GET /api/history", "required", "`limit`, `offset`", "200 items + total", "401; 422 non-numeric"],
               ["GET /api/history/{id}", "required", "-", "200 analysis", "401; 404 not found or not owned"],
               ["DELETE /api/history/{id}", "required", "-", "204", "401; 404"],
               ["GET /api/health", "no", "-", "200 status, model_loaded", "-"]],
              widths=[1.7, 0.7, 1.4, 1.4, 1.4], align=["l", "c", "l", "l", "l"], size=8.8),
          P("Real responses captured from the running service follow. Registration returns the user and a signed token (shortened here):"),
          CODE('POST /api/auth/register   {"name":"Doc Sample","email":"ch6_87424a@example.com","password":"sample-pass-1"}\n'
               '201  {"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...",\n'
               '      "user":{"id":"12775519-0a87-4d43-9550-88957a261c21","name":"Doc Sample",\n'
               '              "email":"ch6_87424a@example.com","created_at":"2026-10-26T13:45:36.734980"}}', 7.5),
          P("Analysing a face with a Bearer token returns all seven basic and eleven compound scores sorted by confidence (only the top three of each list are shown), the dominant emotion and the thumbnail path; the row is stored and the cropped face is written to `media/thumbs`:"),
          CODE('POST /api/analyze  (multipart image=happy_01.jpg, Authorization: Bearer ...)\n'
               '200  {"id":"698f315f-dedd-498b-922d-1492cb523479","created_at":"2026-10-26T13:45:36.767207","face_detected":true,\n'
               '      "basic_emotions":[{"key":"happy","label":"Happy","confidence":0.4733},\n'
               '                        {"key":"surprise","label":"Surprise","confidence":0.4379},\n'
               '                        {"key":"fear","label":"Fear","confidence":0.1133}, ... 4 more],\n'
               '      "compound_emotions":[{"key":"angrily_disgusted","label":"Angrily Disgusted","confidence":1.9e-05},\n'
               '                           {"key":"happily_surprised","label":"Happily Surprised","confidence":1.6e-05}, ... 9 more],\n'
               '      "dominant":{"key":"happy","label":"Happy","confidence":0.4733,"kind":"basic"},\n'
               '      "thumbnail_url":"/api/media/thumbs/698f315f-dedd-498b-922d-1492cb523479.jpg"}', 7.5),
          P("The compound confidences in this real response, of the order of 10⁻⁵, are typical of real faces and are discussed in Chapter 8. When no face is found the service still answers 200:"),
          P("`API_CONTRACT.md` says that a missing face should return 422; the implementation returns 200 with `face_detected` false, and the console handles it by showing the message *No face was detected in that image*. "
            "Errors otherwise use FastAPI's standard `{\"detail\": ...}` body, for example `401 {\"detail\":\"Not authenticated\"}` and `409 {\"detail\":\"Email already registered\"}`."),
          ]
    b += [H2("Security and Error Handling"),
          TAB("Security measures and what they do not cover", ["Area", "Implementation", "Gap or caveat"],
              [["Passwords", "bcrypt through passlib; minimum six characters", "no complexity rule; `bcrypt` must stay at 4.0.1 (version 5 breaks passlib)"],
               ["Sessions", "HS256 JWT with `sub` and `exp`, 7-day lifetime; tampered, expired and foreign-key tokens are rejected as 401", "no refresh or revocation; the token lives in browser local storage"],
               ["Signing key", "read from `MOSAIC_SECRET_KEY`", "a development default is used when the variable is unset and must be replaced in any deployment"],
               ["Authorisation", "history queries filter on `user_id`; another user's id gives 404", "-"],
               ["Optional auth", "`/api/analyze` works without a token and then stores nothing", "unauthenticated users can consume CPU; no rate limit"],
               ["SQL injection", "all queries go through the SQLAlchemy ORM with bound parameters", "-"],
               ["CORS", "only `http://localhost:3000` and `http://127.0.0.1:3000` are admitted", "the list is hard-coded in `config.py`"],
               ["Uploads", "bytes are decoded in memory; the original photo is never written to disk", "no size limit and no content-type check"],
               ["E-mail", "stored as a plain string", "not validated: a value such as `not-an-email-ab12` is accepted"],
               ["Transport", "plain HTTP in development", "no TLS configuration is provided"]],
              widths=[1.1, 3.0, 2.4], align=["l", "l", "l"], size=9.0),
          P("Error handling is minimal and is described here exactly as it behaves. A request without a valid token to a protected route returns 401; an unknown route 404; a wrong method 405; a malformed body or a missing field 422. "
            "If no face is detected the response is a normal 200 (see above). If the uploaded bytes are not a decodable image (a text file, an empty file or a truncated JPEG), Pillow raises an exception inside `analyze_image_bytes()` and the request ends in **HTTP 500**; there is no handler. "
            "If the checkpoint file is missing, start-up succeeds, `/api/health` reports `model_loaded: false`, and the first request that contains a face raises `FileNotFoundError` (HTTP 500). "
            "The unused `threshold` parameter of `analyze_image_bytes()` has no effect."),
          ]
    tl = f"{t['tests']} tests, {t['failures']} failures" if t else "the pytest suite"
    perf = ""
    if an and lg:
        perf = (f" On this machine, over `127.0.0.1`, an anonymous analysis of a detected face takes {an['p50_ms']:.0f} ms (median) and {an['p95_ms']:.0f} ms (95th percentile), "
                f"and a login about {lg['p50_ms']:.0f} ms, dominated by bcrypt.")
    b += [H2("Installation and Execution"),
          P("The code defaults are port 8000 for the API and port 3000 for the console. The console reads the API address from the build-time variable `NEXT_PUBLIC_API_URL` (default `http://localhost:8000/api`). "
            "The backend needs Python 3.10 or newer and the packages of `requirements.txt` (FastAPI, SQLAlchemy, python-jose, passlib with `bcrypt==4.0.1`, PyTorch, OpenCV, Pillow, NumPy, pandas); the console needs Node.js and `npm install`. "
            "The sequence is: create a virtual environment, install the requirements, run `python -m app.ml.run_pipeline` once (the three training stages, about 30 to 60 minutes on a CPU, writing the checkpoints and the training log), start `uvicorn app.main:app --port 8000`, then `npm run dev` in `frontend/`. "
            "For the measurements and screenshots in this report port 8000 was in use by another program, so the API ran on port 8116 and the console was a production build (`npm run build`, `npm start`) with `NEXT_PUBLIC_API_URL` set accordingly. "
            "The repository contains no `run.bat`, `setup.bat` or `.env.example`; Appendix B lists the steps in full."),
          P(f"Automated checks live in `backend/tests`: {tl} (unit tests for the taxonomy, security helpers, network shapes, preprocessing and synthesis labels, and API tests with a temporary database that cover registration, login, analysis, history privacy and two characterised defects).{perf}"),
          ]
    return b


def blocks():
    return [H1("6. METHODOLOGY AND SOFTWARE IMPLEMENTATION"),
            P("This chapter explains how Mosaic is built and how it was evaluated: the overall method, the data, the preprocessing, the choice of algorithms, the formulas, the models and their training, the application, its security and its installation. "
              "Every number in it comes from the product's own training log or from the experiments in `experiments/`, run on the product's own modules; Chapter 8 reports what those experiments found.")
            ] + renum(methodology_blocks() + application_blocks(), "6")
