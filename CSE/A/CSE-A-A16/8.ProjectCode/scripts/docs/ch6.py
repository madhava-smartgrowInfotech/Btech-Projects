"""Chapter 6: Methodology and Software Implementation. methodology_blocks() feeds document 9, application_blocks() feeds document 12."""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB

SEED_NOTE = "seed 42"


def methodology_blocks():
    T = F.T
    b = []
    b += [H2("6.1 Overall methodology"),
          P("The method is an ordinary supervised image-classification pipeline, built so that the same code path serves three purposes. Hand images are cropped to a fixed region, reduced to a binary hand mask by "
            "classical image processing, resized to 64x64 and fed to a small convolutional network that outputs a probability for each of 29 classes: the 26 letters A-Z and three control signs "
            "(`space`, `del`, `nothing`). During live use a short temporal filter turns the stream of per-frame predictions into typed letters. The steps are:"),
          N("**Collect or import** labelled hand images (own captures through the Collect screen, or the public Kaggle ASL Alphabet images).",
            "**Preprocess** each image: ROI crop, grayscale, Gaussian blur, Otsu threshold, morphology, resize to 64x64, scale to [0, 1].",
            "**Split** the images 70/15/15 into training, validation and test sets with a stratified split (seed 42).",
            "**Train** the CNN with augmentation, the Adam optimiser and early stopping on validation accuracy.",
            "**Evaluate** once on the held-out test split: accuracy, per-class precision/recall/F1, confusion matrix, threshold behaviour, robustness and latency.",
            "**Recognise live**: send browser frames to the server, classify, apply the confidence threshold, vote over 15 frames and commit a letter after 18 stable frames.",
            "**Speak** the finished sentence with an offline text-to-speech voice."),
          FIG(F.diag("12_training_pipeline.png"), "Training pipeline used for the saved model.", 5.6)]

    b += [H2("6.2 Dataset"),
          P("The working dataset is a subset of the public Kaggle *ASL Alphabet* collection [25]. The archive on disk holds 87,000 training images (29 classes of 3,000 each, 200x200 colour JPEG) and 28 official test images (one per "
            "letter except `del`, plus `space` and `nothing`). A script (`scripts/prepare_data.py`) copies an evenly spaced subset of **250 images per class, 7,250 in all**, into `data/`; on a CPU machine this keeps "
            f"loading to {F.DS['load_and_preprocess_seconds']:.0f} s and an epoch to about {F.TRAIN_SPEED['seconds_per_epoch']} s. The images are split with a stratified 70/15/15 split (seed 42) into "
            f"**{F.DS['train']:,} training, {F.DS['validation']:,} validation and {F.DS['test']:,} test images** (37-38 test images per class)."),
          FIG(F.fig("f08_dataset_split.png"), "Class counts and the train/validation/test split.", 5.4),
          FIG(F.fig("f09_dataset_samples.png"), "Sample images from the working dataset (one row of letters).", 5.4),
          P("Two properties of the data decide how its results must be read. First, the images are frames cut from short videos of a few recordings, so neighbouring frames are near-duplicates; second, the archive "
            "carries no signer identifier. A random split therefore puts near-identical frames on both sides of the split, and the test accuracy measures how well the model reads *held-out frames of the "
            "recorded signers and scenes*, not how well it reads a new person in a new room. This is stated again wherever a number is quoted (Chapters 7 to 10). The archive does not bundle a licence file; "
            "its terms should be read on the dataset's Kaggle page before any redistribution, and the images are not redistributed with this submission.")]

    b += [H2("6.3 Preprocessing"),
          P("Preprocessing is one function (`preprocess_roi`) used by collection previews, training and live recognition, in the order given by the project abstract: region of interest, grayscale, noise reduction, "
            "segmentation, normalisation."),
          TAB("Preprocessing steps and their reasons", ["Step", "Operation (parameters)", "Reason"],
              [["1  ROI crop", "300x300 box at x 620-920, y 90-390 of the 960x540 frame", "Fixed box on the right of the frame: the signer places the hand in it; background elsewhere is ignored."],
               ["2  Grayscale", "BGR to gray", "Hand shape, not colour, carries the letter; one channel is 3x cheaper."],
               ["3  Noise reduction", "Gaussian blur 7x7", "Suppresses sensor noise and JPEG blocks before thresholding."],
               ["4  Segmentation", "Otsu threshold; invert if the mask mean exceeds 127", "Chooses the threshold automatically per frame; the inversion keeps the hand as the bright region on bright and dark backgrounds."],
               ["5  Morphology", "Opening x1, closing x2, 3x3 kernel", "Removes specks and closes small holes in the silhouette."],
               ["6  Normalise", "Resize to 64x64 (area interpolation), divide by 255", "Fixed small input; values in [0, 1] for stable training."]],
              widths=[1.25, 2.55, 2.8], align=["l", "l", "l"], size=10),
          FIG(F.fig("f10_preprocessing_stages.png"), "Preprocessing stages on real dataset images: colour crop, grayscale, blur, Otsu mask and the final 64x64 input.", 5.6),
          P("The figure also shows the method's main weakness. Otsu's method finds the best single grey-level threshold, not the hand; where the background has structure of a similar brightness the mask contains "
            "background shapes next to the hand. The network can therefore partly learn the scene of the training recordings, which is one reason why the held-out accuracy of Chapter 8 should not be read as accuracy for "
            "a new user. A skin-colour mask (`segment_skin`, YCrCb) exists in the code as an alternative; it was not evaluated and the default is Otsu.")]

    b += [H2("6.4 Algorithm choice and justification"),
          P("**Why a CNN.** A convolutional network learns local shape features (edges, finger contours) and combines them hierarchically with far fewer parameters than a fully connected network on the same pixels [7], [8]. "
            "For a 64x64 binary mask this needs only three convolution blocks, which trains in about ten seconds per epoch on a CPU and answers in about 50 ms per frame."),
          P("**Why a binary mask instead of the colour image.** The mask removes skin tone, clothing and most lighting differences, so a small network and a small dataset suffice. The cost is that errors of the "
            "segmentation step reach the network unchanged."),
          P("**Why not skeleton or landmark input.** The base paper [1] works on 2D skeletons from a pose estimator (such as MediaPipe [13]) and a graph convolutional network, which is robust to background and "
            "suits moving word signs. It needs a pose-estimation stage in front of the classifier and, for its distillation, labels for a mask and several teacher models. For static fingerspelling letters on a CPU "
            "the direct image route is simpler and its 50 ms latency leaves no need for a second network; we did not test a landmark-based alternative, so we make no claim about which is more accurate."),
          P("**Why batch normalisation, dropout and augmentation.** Batch normalisation [19] stabilises training of the deeper layers; dropout [20] (0.25 after blocks 2 and 3, 0.4 before the output) limits over-fitting of the "
            "2.1-million-weight dense layer; random rotation, shift, zoom and shear [22] stand in for the variety that a small dataset lacks."),
          P("**Why a temporal filter.** A single frame is noisy: the hand moves between letters and individual frames are misread. Thresholding the confidence (0.75), taking the majority of the last 15 predictions and "
            "requiring 18 consecutive stable frames before typing a letter converts noisy frame-level output into deliberate keystrokes, at the price of a short delay (about a second at the measured frame rate).")]

    b += [H2("6.5 Mathematical formulation"),
          P("For an input mask *x* of size 64x64, a convolution layer with kernels *w* and bias *b* computes, for output channel *k* at position (*i*, *j*):"),
          EQ("y[i,j,k] = ReLU( b_k + Σ_c Σ_u Σ_v  w[u,v,c,k] · x[i+u, j+v, c] ),   ReLU(z) = max(0, z)"),
          P("Batch normalisation [19] rescales each channel over a mini-batch with mean μ_B and variance σ_B², then applies a learned scale γ and shift β:"),
          EQ("x̂ = (x − μ_B) / √(σ_B² + ε),   y = γ · x̂ + β"),
          P("The last layer turns the 29 logits *z* into probabilities, and the network is trained to minimise the categorical cross-entropy over *N* training images with one-hot targets *t*:"),
          EQ("p_k = exp(z_k) / Σ_j exp(z_j)"),
          EQ("L = − (1/N) Σ_n Σ_k  t[n,k] · log p[n,k]"),
          P("The Adam optimiser [21] keeps running averages of the gradient *g* and its square and updates the weights θ with learning rate α = 10⁻³ (Keras defaults β₁ = 0.9, β₂ = 0.999):"),
          EQ("m_t = β₁ m_{t−1} + (1−β₁) g_t,   v_t = β₂ v_{t−1} + (1−β₂) g_t²,   θ_t = θ_{t−1} − α · m̂_t / (√v̂_t + ε)"),
          P("The segmentation step uses Otsu's criterion [17]: the threshold *t** that maximises the between-class variance of the grey-level histogram, with class weights ω₀, ω₁ and means μ₀, μ₁ of the pixels below and above *t*:"),
          EQ("σ_B²(t) = ω₀(t) · ω₁(t) · [μ₀(t) − μ₁(t)]²,   t* = argmax_t σ_B²(t)"),
          P("The decision rule of the recogniser is as follows. With τ = 0.75 the accepted label of frame *t* is a_t = argmax_k p_k if max_k p_k ≥ τ, and `nothing` otherwise. The smoothed label m_t is the most frequent "
            "of the last 15 accepted labels. If m_t has been the same for *s* consecutive frames, the letter m_t is committed when s ≥ 18, m_t ≠ `nothing` and m_t differs from the last committed letter; "
            "a smoothed label of `nothing` clears the last committed letter. Evaluation uses accuracy, precision P = TP/(TP+FP), recall R = TP/(TP+FN), F1 = 2PR/(P+R) per class, "
            "their unweighted mean (macro F1) and top-3 accuracy (the true class among the three most probable).")]

    b += [H2("6.6 Model architecture and training"),
          P("The architecture (Chapter 5, with its layer table) has 2,199,453 parameters and a 26.48 MB model file. The table below lists the training configuration. The saved model was trained for 30 epochs "
            f"(the interface default is 25); the best validation accuracy, {F.pct(F.RUN['best_val_accuracy'])}, was reached at the last epoch, so the run ended because it hit its epoch cap, not because early stopping fired, "
            "and accuracy was still slowly rising."),
          TAB("Training configuration", ["Setting", "Value"],
              [["Optimiser / loss", "Adam, learning rate 1e-3 / categorical cross-entropy"], ["Batch size / steps per epoch", "32 / 158 (5,075 training images // 32)"],
               ["Epochs", "30 in the saved run (default 25, allowed 1-500)"], ["Split", "70 / 15 / 15 stratified, seed 42"],
               ["Augmentation (training only)", "rotation 12 deg, width/height shift 10 %, zoom 12 %, shear 8 %, nearest fill"],
               ["Early stopping", "monitor validation accuracy, patience 6, restore best weights"], ["Checkpoint", "best validation accuracy kept in `models/asl_cnn_model.keras`"],
               ["Hardware", f"{F.ENV['cpu']}, {F.ENV['ram_gb']} GB RAM, no GPU; about {F.TRAIN_SPEED['seconds_per_epoch']} s per epoch (2-epoch benchmark)"],
               ["Software", f"Python {F.ENV['python']}, TensorFlow {F.ENV['tensorflow']}, OpenCV {F.ENV['opencv']}, NumPy {F.ENV['numpy']}"]],
              widths=[2.2, 4.4], align=["l", "l"], size=10),
          FIG(F.fig("f01_training_curves.png"), "Training and validation accuracy and loss over the 30 epochs of the saved run.", 5.6),
          P(f"The curves show training accuracy ({F.pct(F.RUN['final_train_accuracy'])} at the end) below validation accuracy ({F.pct(F.RUN['final_val_accuracy'])}). That is expected here: dropout and augmentation act only on "
            f"the training pass, so the training figures are measured on harder inputs. The validation loss spikes in the first epochs (BatchNorm statistics are still warming up) and settles by epoch 6. The wall-clock time of "
            "the 30-epoch run itself was not recorded; the per-epoch figure comes from a separate 2-epoch benchmark on the same machine.")]
    return b


def application_blocks():
    b = []
    b += [H2("6.7 Application architecture and implementation"),
          P("**Server.** `backend/main.py` creates one `SignRecognizer` that owns the Keras model, loaded on a background thread at start-up so that the first page loads at once. Each browser tab opens a *session*: "
            "a new `SignRecognizer` that shares the loaded model and labels but has its own history, stable counter and last committed letter, so two tabs cannot disturb each other's smoothing. "
            "At most 20 sessions are kept (the oldest is dropped). Keras inference is not re-entrant, so every prediction and every model reload runs under one lock. Training runs in `TrainJob` on a daemon thread; "
            "the job's state (loading, training, done, error), epoch and history live in a lock-guarded dictionary that `/api/train/status` returns, and the model is reloaded before the state becomes *done*."),
          P("**Browser.** The Recognize page (`pages/Recognize.tsx` with `lib/camera.ts`) opens the camera with `getUserMedia`, draws each video frame to a canvas after a 16:9 cover crop and a horizontal mirror, "
            "exports a 960x540 JPEG at quality 0.8 (about 27 KB) and posts it. A new request is sent only after the previous one has returned and at least 60 ms after it was sent, so the loop cannot queue "
            "frames. The result updates the large letter, the confidence bar and the mask preview; a committed letter is appended to the sentence. The Speak button posts the text to the server voice and falls back to the "
            "browser's speech synthesis if the server voice fails. TanStack Query caches the data of the other pages (dataset counts, model report, training status, which is polled while a run is active), and Recharts draws the charts."),
          P("**Desktop application.** The original customtkinter application (`python run.py`) was kept; it uses the same modules directly and a threaded OpenCV camera. The web version was added because a browser "
            "camera needs no native camera code and gives a better interface; the two share every line of recognition logic."),
          H3("6.7.1 Key code: the recogniser"),
          CODE("""    def predict_frame(self, roi_bgr):
        model_input, mask = preprocess_roi(roi_bgr)
        probs = self.model.predict(np.expand_dims(model_input, 0), verbose=0)[0]
        top_idx = int(np.argmax(probs)); confidence = float(probs[top_idx])
        label = self.labels[top_idx]
        accepted = label if confidence >= config.CONFIDENCE_THRESHOLD else "nothing"
        self._history.append(accepted)                      # deque(maxlen=15)
        majority_label, _ = Counter(self._history).most_common(1)[0]
        if majority_label == self._stable_label: self._stable_count += 1
        else: self._stable_label, self._stable_count = majority_label, 1
        committed = None
        if (self._stable_count >= config.STABLE_FRAMES_TO_COMMIT and majority_label != "nothing"
                and majority_label != self._last_committed):
            committed, self._last_committed, self._stable_count = majority_label, majority_label, 0
        elif majority_label == "nothing":
            self._last_committed = None
        return {"label": label, "confidence": confidence, "mask": mask,
                "stable_label": majority_label, "committed": committed}""", 8.5),
          P("The function is a direct transcription of the flowchart in Chapter 5. It returns the raw label and confidence (so the interface can show what the network sees this instant) and the smoothed "
            "result (what is typed).")]

    b += [H2("6.8 Security and error handling"),
          B("**Input validation.** Class names are checked against the 29-name whitelist (404 otherwise); stored-image names must match `[\\w\\-. ]+\\.(png|jpe?g)` and are looked up inside the class folder only, so they cannot leave it; "
            "uploads must decode as images (400); training parameters are range-checked (epochs 1-500, batch 1-1,024, learning rate 1e-6 to 1) and at least two classes must have images (409); speech text is limited to 2,000 characters.",
            "**State protection.** One model lock; one collection lock so that two frames in the same millisecond get different file names; training refuses to start while another run is active (409); a session cap of 20.",
            "**Failure messages.** Every error is a JSON message the interface shows to the user (for example *No trained model is loaded. Train one first*); the interface also explains camera-permission and no-camera states.",
            "**What is not protected.** The API has no authentication and allows all origins, because it is designed for one user on one machine. It must not be exposed to a network as it stands. Uploaded frames are processed in memory and are not stored "
            "except by the explicit Collect action."),
          P("The 27 API tests of Chapter 7 exercise these checks.")]

    b += [H2("6.9 Installation and execution"),
          P("**Quick start (Windows).** Install Python 3.10 or 3.11 and Node.js 18 or newer and double-click `run.bat`. On first run it creates the virtual environment, installs the Python packages from `requirements.txt` "
            "(TensorFlow 2.15.0 is large; allow several minutes) and the frontend packages, starts the API on port 8316 in its own window, starts the web application on port 5316 and opens the browser. "
            "Ports can be changed in `.env`. Use Chrome or Edge on `localhost`: browsers allow webcam access only there or on HTTPS."),
          CODE("""python -m venv .venv && .venv\\Scripts\\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8316     # terminal 1
cd frontend && npm install && npm run dev                           # terminal 2
python run.py                                                       # original desktop app
python scripts/prepare_data.py [archive_dir] [per_class]            # copy a 250-per-class subset into data/
python -m pytest tests                                              # 52 tests
python scripts/smoke_test.py                                        # 26 live API checks in a temp copy""", 9),
          P("**First use.** The repository ships neither the dataset nor the trained model. The user either captures images in the Collect screen (150-250 per class is a good target) or imports a dataset into "
            "`data/<CLASS>/`, then opens the Train screen (at least two classes are needed) and, when it finishes, the Recognize screen. Appendix B gives the full user guide.")]
    return b


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
