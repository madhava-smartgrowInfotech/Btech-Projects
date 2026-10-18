"""Second half of the diagram set (DFD 1/2, UML class, sequence, use case, flowchart, CNN, training)."""

from __future__ import annotations

from pathlib import Path

from dgm_lib import *  # noqa: F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"


def dfd1():
    fig, ax = canvas(10, 7.4, 100, 74)
    R = 7.6
    box(ax, 50, 68, 12, 6, "User", WHITE, tc=INK, ec=NAVY, fs=9.5, bold=True)
    box(ax, 50, 8, 12, 6, "User", WHITE, tc=INK, ec=NAVY, fs=9.5, bold=True)
    box(ax, 7, 44, 11, 7, "Webcam", WHITE, tc=INK, ec=NAVY, fs=9.5, bold=True)
    box(ax, 7, 8, 11, 7, "Speaker", WHITE, tc=INK, ec=NAVY, fs=9.5, bold=True)
    circle(ax, 26, 54, R, "1.0\nCollect\nsamples", BLUE, fs=8.5)
    circle(ax, 74, 54, R, "2.0\nTrain\nmodel", BLUE, fs=8.5)
    circle(ax, 26, 31, R, "3.0\nRecognise\nsigns", BLUE, fs=8.3)
    circle(ax, 26, 8, R - 0.6, "4.0\nSpeak\nsentence", BLUE, fs=8)
    circle(ax, 74, 8, R, "5.0\nReport\nmodel", BLUE, fs=8.5)
    store(ax, 50, 54, 15, 7, "D1  Image dataset\ndata/<CLASS>", fs=7.8)
    store(ax, 50, 31, 17, 7, "D2  Model files\n.keras + labels.json", fs=7.6)
    store(ax, 74, 31, 18, 7, "D3  Training logs\nhistory, report, CM", fs=7.6)
    arrow(ax, (46, 65), (30, 59.5), "class choice", lo=(-5.5, 2.2), fs=7.8)
    arrow(ax, (54, 65), (70, 59.5), "epochs, batch, LR", lo=(7.5, 2.2), fs=7.8)
    arrow(ax, (78.5, 60.2), (56, 67), "training status", lo=(8, 4.4), fs=7.6, rad=-0.15)
    arrow(ax, (12.7, 46.5), (20, 50), "frames", lo=(-4.2, 3.2), fs=7.8)
    arrow(ax, (12.7, 41.5), (20, 35), "frames", lo=(-4.4, -2.6), fs=7.8)
    arrow(ax, (33.6, 54), (42.5, 54), "images", lo=(0, 2.4), fs=7.8)
    arrow(ax, (57.5, 54), (66.4, 54), "images", lo=(0, 2.4), fs=7.8)
    arrow(ax, (69, 48.4), (56, 34.8), "model, labels", lo=(9, 2.2), fs=7.8)
    arrow(ax, (75, 46.4), (75, 34.6), "history,\nreport, CM", lo=(7.5, 0), fs=7.6)
    arrow(ax, (41.5, 31), (33.6, 31), "model", lo=(0, 2.4), fs=7.8)
    arrow(ax, (55, 27.5), (68.8, 13.2), "model info", lo=(4.5, 3.2), fs=7.8)
    arrow(ax, (76, 27.5), (76, 15.6), "history,\nreport", lo=(6.6, 0), fs=7.6)
    arrow(ax, (31, 24.6), (45, 11.2), "letters, sentence", lo=(-4.0, 3.2), fs=7.8)
    arrow(ax, (44, 8), (32.6, 8), "speak command", lo=(0, 2.4), fs=7.8)
    arrow(ax, (66.4, 8), (56, 8), "metrics, charts", lo=(0, 2.4), fs=7.8)
    arrow(ax, (18.8, 8), (12.8, 8), "audio", lo=(0, 2.4), fs=7.8)
    save(fig, OUT / "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(10, 5.2, 100, 52)
    xs = [10, 26, 42, 58, 74, 90]
    labels = ["3.1\nDecode\nframe", "3.2\nCrop\nROI", "3.3\nSegment\nhand", "3.4\nNormalise\n64x64", "3.5\nClassify\n(CNN)", "3.6\nSmooth,\ncommit"]
    for x, t in zip(xs, labels):
        circle(ax, x, 28, 6.6, t, BLUE, fs=7.8)
    flows = ["JPEG frame", "960x540\nBGR frame", "300x300\nROI", "binary\nmask", "64x64x1\ntensor"]
    for a, b, f in zip(xs[:-1], xs[1:], flows):
        arrow(ax, (a + 6.6, 28), (b - 6.6, 28), f, fs=7.4, lo=(0, 6.2))
    store(ax, 66, 8.5, 20, 6.4, "D2  Model files\n(loaded once)", fs=8)
    arrow(ax, (72, 11.7), (74, 21.4), "weights", lo=(5.5, 0), fs=8)
    store(ax, 91, 8.5, 15, 6.4, "Session\nhistory (15)", fs=8)
    arrow(ax, (90, 11.7), (90, 21.4), "votes", lo=(-4.5, 0), fs=8)
    box(ax, 10, 46, 17, 6, "Browser\n(Recognize)", WHITE, tc=INK, ec=NAVY, fs=8.5, bold=True)
    arrow(ax, (10, 42.9), (10, 34.8), "POST frame", lo=(7, 0), fs=8)
    box(ax, 90, 46, 17, 6, "Browser\n(Recognize)", WHITE, tc=INK, ec=NAVY, fs=8.5, bold=True)
    arrow(ax, (90, 34.8), (90, 42.9), "label, confidence,\nstable, committed,\nmask", lo=(-10.5, 0.4), fs=8, ha="center")
    ax.text(50, 49.5, "Level 2 expansion of process 3.0 (Recognise signs)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    save(fig, OUT / "05_dfd_level2.png")


def class_diagram():
    fig, ax = canvas(10, 7.4, 100, 74)
    a = uml_class(ax, 1, 72, 30, "backend.main", ["_base: SignRecognizer", "_sessions: OrderedDict", "_model_lock: Lock", "job: TrainJob"],
                  ["recognize_frame()", "collect(cls)", "train_start(body)", "model_info()"], stereotype="FastAPI app")
    b = uml_class(ax, 1, 40, 30, "TrainJob", ["_state: dict", "_stop: Event", "_thread: Thread", "_on_finished: Callable"],
                  ["start(epochs, bs, lr)", "request_stop()", "snapshot()", "_run()"], hdr=TEAL)
    c = uml_class(ax, 39, 72, 30, "SignRecognizer", ["model: keras.Model", "labels: list[str]", "_history: deque(15)", "_stable_label", "_stable_count", "_last_committed"],
                  ["load() -> bool", "predict_frame(roi)"], hdr=PURPLE)
    d = uml_class(ax, 39, 41, 30, "Dataset", ["x_train, y_train", "x_val, y_val", "x_test, y_test", "labels: list[str]"], [], hdr=ORANGE, stereotype="dataclass")
    e = uml_class(ax, 39, 14.5, 30, "StreamingCallback", ["epoch_cb", "stop_flag"], ["on_epoch_end()"], hdr=TEAL, stereotype="keras Callback")
    f = uml_class(ax, 74, 72, 25, "preprocessing", [], ["get_roi_box()", "crop_roi()", "segment_hand()", "normalize_for_model()", "preprocess_roi()"], hdr=BLUE, stereotype="module")
    g = uml_class(ax, 74, 46, 25, "config", ["CLASSES (29)", "IMG_SIZE = 64", "ROI_BOX_SIZE = 300", "CONFIDENCE_THRESHOLD", "STABLE_FRAMES_TO_COMMIT"], [], hdr=GREY, stereotype="module")
    arrow(ax, (31, 62), (39, 62), None, color=NAVY, lw=1.4)
    ax.text(35, 64.4, "1 + 0..20", fontsize=7.2, ha="center")
    arrow(ax, (16, a[1]), (16, 40.2), "owns 1", fs=7.6, lo=(4.2, 0), color=NAVY)
    arrow(ax, (31, 29), (39, 29), None, ls="--", color=NAVY)
    ax.text(35, 31.2, "train_model()", fontsize=7, ha="center")
    ax.text(35, 26.2, "loads", fontsize=7, ha="center")
    arrow(ax, (31, 20), (39, 11), None, ls="--", color=NAVY)
    ax.text(30.5, 12.2, "attaches", fontsize=7, ha="center")
    arrow(ax, (69, 63), (74, 63), None, ls="--", color=NAVY)
    ax.text(71.5, 65.2, "uses", fontsize=7.2, ha="center")
    arrow(ax, (69, 50), (74, 47.5), None, ls="--", color=NAVY)
    ax.text(71.5, 52.6, "reads", fontsize=7.2, ha="center")
    save(fig, OUT / "06_class_diagram.png")


def sequence_diagram():
    fig, ax = canvas(10, 10.6, 100, 106)
    names = ["User", "React UI", "Camera\nhook", "FastAPI\n/api", "Sign\nRecognizer", "Keras\nCNN", "pyttsx3\nTTS"]
    xs = [6, 20, 34, 50, 66, 81, 94]
    top = 103
    for x, n in zip(xs, names):
        box(ax, x, top, 11.5, 6, n, NAVY, fs=8.2, bold=True)
        ax.plot([x, x], [top - 3, 1], color="#9AA7B8", lw=1.1, ls="--", zorder=1)
    y = [top - 8.5]

    def msg(i, j, text, ret=False, gap=4.7, left=None):
        arrow(ax, (xs[i], y[0]), (xs[j], y[0]), None, color=(GREY if ret else BLUE), ls="--" if ret else "-", lw=1.4)
        lo, hi = sorted((xs[i], xs[j]))
        ax.text(left if left is not None else (lo + hi) / 2, y[0] + 1.15, text, ha="left" if left is not None else "center", fontsize=7.6, va="bottom", color=INK,
                bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
        y[0] -= gap

    def self_call(i, text):
        yy = y[0]
        ax.plot([xs[i], xs[i] + 3.2, xs[i] + 3.2, xs[i]], [yy + 0.9, yy + 0.9, yy - 2.1, yy - 2.1], color=BLUE, lw=1.3, zorder=4)
        arrow(ax, (xs[i] + 3.2, yy - 2.1), (xs[i], yy - 2.1), None, color=BLUE, lw=1.3)
        ax.text(xs[i] + 4.2, yy - 0.6, text, fontsize=7.6, ha="left", va="center", color=INK)
        y[0] -= 6.0

    msg(0, 1, "1  Start camera")
    msg(1, 2, "2  getUserMedia()")
    msg(1, 3, "3  POST /recognize/session")
    msg(3, 1, "4  session_id, model_loaded", ret=True, gap=6.8)
    loop_top = y[0] + 2.4
    ax.text(11.5, y[0] + 0.2, "loop  while the camera runs (one request at a time, at least 60 ms apart)", fontsize=8, color=ORANGE, fontweight="bold", va="center")
    y[0] -= 5.6
    msg(2, 1, "5  grab(): cover-crop 16:9, mirror, JPEG 960x540", ret=True)
    msg(1, 3, "6  POST /recognize/frame (frame, session_id)")
    msg(3, 4, "7  crop_roi(); predict_frame(roi)")
    self_call(4, "8  segment_hand(); normalise to 64x64")
    msg(4, 5, "9  predict(1x64x64x1)")
    msg(5, 4, "10  29 softmax probabilities", ret=True)
    self_call(4, "11  threshold 0.75, vote of 15, stable count")
    msg(4, 3, "12  label, confidence, stable_label, committed, mask", ret=True)
    msg(3, 1, "13  JSON response", ret=True, gap=4.2)
    msg(1, 0, "14  letter, confidence; committed letter appended", ret=True, gap=5.2, left=7)
    loop_bot = y[0] + 2.6
    ax.add_patch(Rectangle((11, loop_bot), 86, loop_top - loop_bot, fc="none", ec=ORANGE, lw=1.4, zorder=1))
    y[0] -= 2.4
    msg(0, 1, "15  Speak")
    msg(1, 3, "16  POST /tts/speak {text}")
    msg(3, 6, "17  speak_async(text) on a daemon thread")
    msg(6, 0, "18  audio from the speakers", ret=True)
    save(fig, OUT / "07_sequence_recognition.png")


def use_case():
    fig, ax = canvas(10, 7.0, 100, 70)
    ax.add_patch(Rectangle((30, 0.4), 40, 68.4, fc="#FAFBFD", ec=NAVY, lw=1.6, zorder=0))
    ax.text(50, 67.0, "SignSpeak web application", ha="center", fontsize=11, color=NAVY, fontweight="bold")
    names = ["UC1  Start / stop camera", "UC2  Recognise signs live", "UC3  Build sentence\n(space, back, clear)", "UC4  Speak sentence", "UC5  Collect samples\n(single / burst)",
             "UC6  Train model\n(set hyper-parameters)", "UC7  View model performance", "UC8  Read about the project"]
    ys = [60.5, 51.5, 44, 36.5, 29, 21.5, 14, 7.2]
    for t, y in zip(names, ys):
        ellipse(ax, 50, y, 34, 6.2, t, fs=8)

    def actor(x, y, name):
        ax.add_patch(Circle((x, y + 6.5), 1.6, fc="white", ec=NAVY, lw=1.6, zorder=3))
        ax.plot([x, x], [y + 4.9, y + 1.0], color=NAVY, lw=1.6)
        ax.plot([x - 3, x + 3], [y + 3.8, y + 3.8], color=NAVY, lw=1.6)
        ax.plot([x, x - 2.6], [y + 1.0, y - 2.2], color=NAVY, lw=1.6)
        ax.plot([x, x + 2.6], [y + 1.0, y - 2.2], color=NAVY, lw=1.6)
        ax.text(x, y - 5.0, name, ha="center", fontsize=9.5, fontweight="bold", color=INK)
    actor(11, 31, "User")
    actor(90, 50, "Webcam\n(browser)")
    actor(90, 28, "Speaker\n(server voice)")
    for y in ys:
        arrow(ax, (15, 34), (33, y), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    arrow(ax, (86, 54), (67, 59), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    arrow(ax, (86, 53), (67, 51.5), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    arrow(ax, (86, 31), (67, 36.5), None, color="#9AA7B8", lw=1.0, style="-", z=1)
    arrow(ax, (50, 54.6), (50, 57.4), None, color=GREY, lw=1.2, ls="--")
    ax.text(51.5, 56.0, "<<include>>", fontsize=7.4, color=GREY, style="italic")
    ax.text(50, 1.9, "UC2 and UC5 both include UC1 (the camera must be running)", ha="center", fontsize=7.8, color=GREY)
    save(fig, OUT / "08_use_case.png")


def flowchart():
    fig, ax = canvas(10, 10.6, 100, 106)
    L, Rr = 20, 73

    def step(cx, cy, t, c=NAVY, w=34, h=7, fs=8.2):
        box(ax, cx, cy, w, h, t, c, fs=fs)

    ax.text(L, 103.5, "A. Image pipeline", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    ax.text(Rr, 103.5, "B. Decision logic", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    box(ax, L, 98, 24, 5, "Start: frame received", GREY, fs=8.4, bold=True, r=2.4)
    step(L, 89, "Decode JPEG, resize to\n960x540 if needed", BLUE)
    step(L, 80, "Crop ROI box 300x300", BLUE)
    step(L, 71, "Grayscale, then\nGaussian blur 7x7", TEAL)
    step(L, 62, "Otsu threshold", TEAL)
    diamond(ax, L, 51, 30, 11, "mask mean\n> 127 ?", fs=8)
    step(L + 17, 40, "Invert mask", TEAL, w=14, h=5, fs=7.8)
    step(L, 33, "Open (1x), close (2x)\n3x3 morphology", TEAL)
    step(L, 23.5, "Resize 64x64, divide by 255", TEAL)
    step(L, 14, "CNN forward pass\nprobs[29]", PURPLE)
    step(L, 4.6, "label = argmax, conf = max", PURPLE, h=6)
    for a_, b_ in [(95.5, 92.5), (85.5, 83.5), (76.5, 74.5), (67.5, 65.5), (58.5, 56.6)]:
        arrow(ax, (L, a_), (L, b_), None, color=NAVY)
    arrow(ax, (L + 12, 50.2), (L + 16, 42.6), "yes", lo=(3.2, 1.8), fs=7.8, color=ORANGE)
    arrow(ax, (L + 16, 37.4), (L + 8, 35.4), None, color=NAVY)
    arrow(ax, (L, 45.4), (L, 36.5), "no", lo=(2.2, 2.5), fs=7.8, color=ORANGE)
    arrow(ax, (L, 29.5), (L, 27.0), None, color=NAVY)
    arrow(ax, (L, 20), (L, 17.5), None, color=NAVY)
    arrow(ax, (L, 10.5), (L, 7.6), None, color=NAVY)
    # A feeds B: elbow from the last step to the first decision
    ax.plot([L + 17, 47, 47], [4.6, 4.6, 98], color=NAVY, lw=1.5, zorder=4)
    arrow(ax, (47, 98), (Rr - 17.2, 98), None, color=NAVY)
    ax.text(48.2, 50, "label +\nconfidence", fontsize=7.4, color=GREY, ha="left", va="center")
    # right column
    diamond(ax, Rr, 98, 34, 10, "confidence\n>= 0.75 ?", fs=8)
    step(Rr - 12, 85, "accepted =\nlabel", NAVY, w=18, h=6)
    step(Rr + 12, 85, "accepted =\n'nothing'", ORANGE, w=18, h=6)
    box(ax, Rr, 74, 40, 7, "Append accepted to history (last 15)\nmajority = most common entry", NAVY, fs=8)
    diamond(ax, Rr, 61, 34, 11, "majority ==\nstable label ?", fs=8)
    step(Rr - 12, 47.5, "stable count += 1", NAVY, w=19, h=5)
    step(Rr + 12, 47.5, "stable = majority\ncount = 1", NAVY, w=19, h=6)
    diamond(ax, Rr, 33, 42, 14, "count >= 18 and majority\n!= 'nothing' and\n!= last committed ?", fs=7.4)
    step(Rr - 12, 15.5, "committed = majority\nlast = majority\ncount = 0", PURPLE, w=22, h=8, fs=7.6)
    step(Rr + 12, 15.5, "committed = None\n(majority 'nothing':\nlast = None)", GREY, w=22, h=8, fs=7.6)
    box(ax, Rr, 4.6, 46, 6, "Return label, confidence, stable_label, committed, mask", GREY, fs=7.8, bold=True, r=2.4)
    arrow(ax, (Rr - 7, 93.6), (Rr - 11, 88.2), "yes", lo=(-4.5, 0.5), fs=7.8, color=ORANGE)
    arrow(ax, (Rr + 7, 93.6), (Rr + 11, 88.2), "no", lo=(4.5, 0.5), fs=7.8, color=ORANGE)
    arrow(ax, (Rr - 12, 81.8), (Rr - 6, 77.7), None, color=NAVY)
    arrow(ax, (Rr + 12, 81.8), (Rr + 6, 77.7), None, color=NAVY)
    arrow(ax, (Rr, 70.4), (Rr, 66.7), None, color=NAVY)
    arrow(ax, (Rr - 10, 57), (Rr - 12, 50.2), "yes", lo=(-4.2, 0.5), fs=7.8, color=ORANGE)
    arrow(ax, (Rr + 10, 57), (Rr + 12, 50.7), "no", lo=(4.2, 0.5), fs=7.8, color=ORANGE)
    arrow(ax, (Rr - 12, 44.8), (Rr - 6, 38.8), None, color=NAVY)
    arrow(ax, (Rr + 12, 44.4), (Rr + 6, 38.8), None, color=NAVY)
    arrow(ax, (Rr - 10, 27.5), (Rr - 12, 19.8), "yes", lo=(-4.2, 0.4), fs=7.8, color=ORANGE)
    arrow(ax, (Rr + 10, 27.5), (Rr + 12, 19.8), "no", lo=(4.2, 0.4), fs=7.8, color=ORANGE)
    arrow(ax, (Rr - 12, 11.4), (Rr - 8, 7.7), None, color=NAVY)
    arrow(ax, (Rr + 12, 11.4), (Rr + 8, 7.7), None, color=NAVY)
    save(fig, OUT / "10_core_algorithm_flowchart.png")


def cnn_architecture():
    fig, ax = canvas(11, 3.9, 110, 39)
    blocks = [("Input", "64x64x1", "mask in [0, 1]", GREY, 9), ("Conv 3x3 x32\nBN - ReLU", "64x64x32", "MaxPool 2x2\n-> 32x32x32", BLUE, 13), ("Conv 3x3 x64\nBN - ReLU", "32x32x64", "MaxPool 2x2, drop 0.25\n-> 16x16x64", BLUE, 13),
              ("Conv 3x3 x128\nBN - ReLU", "16x16x128", "MaxPool 2x2, drop 0.25\n-> 8x8x128", BLUE, 13), ("Flatten", "8192", "", TEAL, 9), ("Dense 256\nBN, drop 0.4", "256", "ReLU", TEAL, 11), ("Dense 29", "29", "softmax", PURPLE, 9)]
    x = 2.0
    centers = []
    for t, shape, note, c, w in blocks:
        h = 15 if "Conv" in t else 12
        box(ax, x + w / 2, 19, w, h, t, c, fs=8)
        ax.text(x + w / 2, 19 + h / 2 + 2.6, shape, ha="center", fontsize=8, color=INK, fontweight="bold")
        if note:
            ax.text(x + w / 2, 19 - h / 2 - 4.4, note, ha="center", fontsize=7.2, color=INK, va="center", linespacing=1.2)
        centers.append((x, w))
        x += w + 3.3
    for (a, wa), (b, wb) in zip(centers[:-1], centers[1:]):
        arrow(ax, (a + wa, 19), (b, 19), None, color=NAVY, lw=1.3)
    ax.text(55, 36.2, "SignSpeak CNN: tensor shape after each stage (Keras Sequential 'asl_cnn')", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    save(fig, OUT / "11_cnn_architecture.png")


def training_pipeline():
    fig, ax = canvas(10, 3.9, 100, 39)
    steps = [("Collect or\nimport images\ndata/<CLASS>", BLUE), ("Segment each\nimage\n(same 5 steps)", TEAL), ("Stratified split\n70 / 15 / 15\nseed 42", TEAL), ("Augment train set\nrot 12, shift 10%\nzoom 12%, shear 8%", PURPLE),
             ("Fit CNN\nAdam 1e-3\nbatch 32", PURPLE), ("EarlyStopping\nval_acc, patience 6\n+ best checkpoint", NAVY), ("Evaluate on\ntest split", NAVY), ("Save model, labels,\nhistory, report,\nconfusion matrix", ORANGE)]
    xs = [6.5 + i * 12.4 for i in range(8)]
    for x, (t, c) in zip(xs, steps):
        box(ax, x, 23, 11.2, 14, t, c, fs=7.0)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 5.7, 23), (b - 5.7, 23), None, color=NAVY, lw=1.3)
    box(ax, 50, 6, 92, 7, "API wrapper (TrainJob) runs the same train_model() on a thread, streams epoch metrics, reloads the model, then reports 'done'", WHITE, tc=INK, ec=NAVY, fs=8)
    ax.text(50, 36, "Training pipeline (sign_language_app.train.train_model)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    save(fig, OUT / "12_training_pipeline.png")


def all_more():
    dfd1()
    dfd2()
    class_diagram()
    sequence_diagram()
    use_case()
    flowchart()
    cnn_architecture()
    training_pipeline()
