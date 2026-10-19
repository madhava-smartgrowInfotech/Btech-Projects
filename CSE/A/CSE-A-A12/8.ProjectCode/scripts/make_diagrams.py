"""
Draws every design diagram used in the project documents (matplotlib only, 150 dpi).

    python scripts/make_diagrams.py            # -> docs/diagrams/*.png

Each diagram mirrors what the code does:
  backend/main.py (FastAPI routes), app.py (model loader, Flask UI), model/*.py, database/db.py.
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "diagrams")
os.makedirs(OUT, exist_ok=True)

NAVY, INK, SLATE = "#1B2A41", "#0F172A", "#475569"
ORANGE, BLUE, GREEN, PURPLE, GOLD = "#EB6834", "#2A78D6", "#1BAF7A", "#6B52D6", "#E8A317"
PAPER, LINE = "#F6F8FB", "#9AA8BD"
plt.rcParams["font.family"] = "DejaVu Sans"


def canvas(w, h, title=None, ty=99):
    """Work in a 100 x 100 coordinate space; the figure is cropped to its content when saved."""
    top = ty + 2
    fig, ax = plt.subplots(figsize=(w, w * top / 100))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, top)
    ax.axis("off")
    ax.set_aspect("equal")
    if title:
        ax.text(1, ty, title, fontsize=13, fontweight="bold", color=NAVY, va="top")
    return fig, ax


def box(ax, x, y, w, h, text, fc=PAPER, ec=LINE, tc=INK, fs=9.5, bold=False, lw=1.3, rounding=1.2, ls="-"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rounding}", fc=fc, ec=ec, lw=lw, ls=ls)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc,
            fontweight="bold" if bold else "normal", linespacing=1.25)
    return (x, y, w, h)


def arrow(ax, p, q, label=None, color=SLATE, lw=1.4, ls="-", fs=8, off=(0, 1.2), rad=0.0, head="-|>", lab_ha="center", lp=None):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle=head, color=color, lw=lw, ls=ls,
                                                    connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))
    if label:
        lx, ly = lp if lp else ((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1])
        ax.text(lx, ly, label, fontsize=fs, color=color,
                ha=lab_ha, va="center", bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path)


def mid(b, side):
    x, y, w, h = b
    return {"l": (x, y + h / 2), "r": (x + w, y + h / 2), "t": (x + w / 2, y + h), "b": (x + w / 2, y)}[side]


# ---------------------------------------------------------------- 01 architecture
def architecture():
    fig, ax = canvas(11, 7.4, "System architecture", ty=76)
    for x, w, label in ((1, 22, "Presentation tier"), (26, 26, "Application tier"), (55, 21, "Inference tier"), (79, 20, "Data tier")):
        ax.add_patch(Rectangle((x, 8), w, 62, fc="#FBFCFE", ec="#D5DCE6", lw=1))
        ax.text(x + w / 2, 67.6, label, ha="center", fontsize=9.5, color=SLATE, fontweight="bold")
    spa = box(ax, 3, 40, 18, 16, "React SPA\nVite dev server\nport 5312\n(Landing, Sign in,\nDashboard, Detect,\nResult, History, About)", fc="#E8F0FC", ec=BLUE, fs=8)
    flask_ui = box(ax, 3, 14, 18, 12, "Original Flask UI\nJinja templates\nport 5000", fc="#FFF1EA", ec=ORANGE, fs=8)
    api = box(ax, 28, 40, 22, 22, "FastAPI service\nbackend/main.py\nport 8312\n\nsigned-cookie auth\nupload validation\nREST + file routes\nsaves original +\noverlay images", fc="#E6F6EF", ec=GREEN, fs=8.2)
    app = box(ax, 28, 14, 22, 12, "app.py\nget_model(), allowed_file,\nupload / heatmap folders", fc="#EFEBFC", ec=PURPLE, fs=8)
    pre = box(ax, 57, 44, 17, 11, "model/preprocess.py\nresize, CLAHE, blur,\nnormalise", fc=PAPER, ec=NAVY, fs=8)
    cnn = box(ax, 57, 29, 17, 11, "model/model_builder.py\nCNN, softmax(3)\n(Keras / TensorFlow)", fc=PAPER, ec=NAVY, fs=8)
    cam = box(ax, 57, 14, 17, 11, "model/gradcam.py\nGrad-CAM heatmap\n+ overlay (OpenCV)", fc=PAPER, ec=NAVY, fs=8)
    dbm = box(ax, 81, 58, 16, 9, "database/db.py\nsqlite3 wrapper", fc=PAPER, ec=NAVY, fs=8)
    sql = box(ax, 81, 45, 16, 9, "pneumonia_app.db\ntable: predictions", fc="#FFF8E5", ec=GOLD, fs=8)
    wts = box(ax, 81, 29, 16, 10, "saved_models/\n.h5 + class_indices.json", fc="#FFF8E5", ec=GOLD, fs=7.6)
    files = box(ax, 81, 14, 16, 11, "static/uploads\nstatic/heatmaps\n(image files)", fc="#FFF8E5", ec=GOLD, fs=8)
    arrow(ax, (21, 49), (28, 49), "JSON +\nmultipart", color=BLUE, off=(0, 3.4), fs=7.4)
    arrow(ax, (21, 20), (28, 20), None, color=ORANGE)
    arrow(ax, (39, 40), (39, 26), "get_model()", off=(6.5, 0), fs=7.8)
    arrow(ax, (50, 49.5), (57, 49.5), None, color=GREEN)
    arrow(ax, (50, 61), (81, 63), "insert / read rows", off=(0, 2.3), color=GREEN, fs=7.8)
    arrow(ax, (65.5, 44), (65.5, 40))
    arrow(ax, (65.5, 29), (65.5, 25))
    arrow(ax, (89, 58), (89, 54))
    arrow(ax, (74, 34), (81, 34), "load", ls="--", off=(0, 2.0), fs=7.6)
    arrow(ax, (74, 19.5), (81, 19.5), "overlay\nPNG", off=(0, 3.2), fs=7.4)
    ax.text(50, 3.2, "Dashed = optional at start-up. With no trained weights the app builds an untrained network (Demo Mode).",
            ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "01_system_architecture.png")


# ---------------------------------------------------------------- 02 workflow
def workflow():
    fig, ax = canvas(11, 4.6, "High-level workflow of one scan", ty=48)
    steps = [
        ("1  Sign in", "demo account\nsigned cookie", NAVY),
        ("2  Upload", "PNG / JPG\nup to 8 MB", BLUE),
        ("3  Validate", "name, type,\nsize, decodable", ORANGE),
        ("4  Preprocess", "224x224, CLAHE,\nblur, [0,1]", PURPLE),
        ("5  Classify", "CNN softmax:\nNormal / Bacterial / Viral", GREEN),
        ("6  Explain", "Grad-CAM overlay\non last conv layer", GOLD),
        ("7  Store", "SQLite row +\n2 image files", NAVY),
        ("8  Review", "result, history,\ndashboard, CSV", BLUE),
    ]
    w, gap = 10.6, 1.9
    x = 1.5
    for i, (t, s, c) in enumerate(steps):
        row_y = 26 if i < 4 else 6
        xx = 1.5 + (i % 4) * (w + gap + 12.3)
        b = box(ax, xx, row_y, w + 12.3, 14, "", fc="white", ec=c, lw=2)
        ax.add_patch(Rectangle((xx, row_y + 9.6), w + 12.3, 4.4, fc=c, ec=c))
        ax.text(xx + (w + 12.3) / 2, row_y + 11.8, t, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        ax.text(xx + (w + 12.3) / 2, row_y + 4.6, s, ha="center", va="center", color=INK, fontsize=9, linespacing=1.3)
        if i % 4 != 3:
            arrow(ax, (xx + w + 12.3, row_y + 6), (xx + w + 12.3 + gap, row_y + 6))
    arrow(ax, (1.5 + 3 * (w + gap + 12.3) + (w + 12.3) / 2, 26), (1.5 + 3 * (w + gap + 12.3) + (w + 12.3) / 2, 22), rad=0)
    ax.plot([1.5 + 3 * (w + gap + 12.3) + (w + 12.3) / 2] * 2, [22, 22], color=SLATE)
    ax.annotate("", xy=(1.5 + (w + 12.3) / 2, 20), xytext=(1.5 + 3 * (w + gap + 12.3) + (w + 12.3) / 2, 22),
                arrowprops=dict(arrowstyle="-|>", color=SLATE, lw=1.4, connectionstyle="angle,angleA=180,angleB=90,rad=0"))
    ax.text(50, 41.6, "Failure at step 3 or 4 returns a clear JSON error (400 / 413) and stores nothing.", ha="center",
            fontsize=8.5, color=SLATE, style="italic")
    save(fig, "02_high_level_workflow.png")


# ---------------------------------------------------------------- DFD helpers
def process(ax, cx, cy, r, text, num, fs=8):
    ax.add_patch(Circle((cx, cy), r, fc="#E8F0FC", ec=BLUE, lw=1.6))
    ax.text(cx, cy + r * 0.42, num, ha="center", va="center", fontsize=8.5, fontweight="bold", color=BLUE)
    ax.text(cx, cy - r * 0.12, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)
    return (cx, cy, r)


def entity(ax, x, y, w, h, text):
    ax.add_patch(Rectangle((x, y), w, h, fc="#FFF1EA", ec=ORANGE, lw=1.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, color=INK, fontweight="bold", linespacing=1.2)
    return (x, y, w, h)


def store(ax, x, y, w, h, text, tag):
    ax.add_patch(Rectangle((x, y), w, h, fc="#FFF8E5", ec="none"))
    ax.plot([x, x + w], [y + h, y + h], color=GOLD, lw=1.8)
    ax.plot([x, x + w], [y, y], color=GOLD, lw=1.8)
    ax.plot([x, x], [y, y + h], color=GOLD, lw=1.8)
    ax.text(x + 1.3, y + h / 2, tag, ha="left", va="center", fontsize=8.5, fontweight="bold", color=GOLD)
    ax.text(x + w / 2 + 2.5, y + h / 2, text, ha="center", va="center", fontsize=8.5, color=INK, linespacing=1.2)
    return (x, y, w, h)


# ---------------------------------------------------------------- 03 DFD 0
def dfd0():
    fig, ax = canvas(11, 5.2, "Data flow diagram, level 0 (context)", ty=56)
    user = entity(ax, 3, 28, 17, 14, "User\n(clinician /\nstudent)")
    sysc = process(ax, 50, 35, 15, "Pneumonia\nDetection\nSystem", "0", fs=9.5)
    d1 = store(ax, 74, 40, 24, 8, "predictions table (SQLite)", "D1")
    d2 = store(ax, 74, 24, 24, 8, "uploads and heatmaps (files)", "D2")
    d3 = store(ax, 74, 8, 24, 8, "trained model weights", "D3")
    arrow(ax, (20, 38.5), (35.3, 38.5), "credentials,\nX-ray image,\nhistory / delete requests", off=(0, 5.2), fs=7.8)
    arrow(ax, (35.3, 31), (20, 31), "result: class, confidence,\nprobabilities, Grad-CAM,\nhistory, statistics", off=(0, -5.5), fs=7.8)
    arrow(ax, (63, 40), (74, 44), "scan record", off=(0, 2.4), fs=7.8)
    arrow(ax, (74, 45.2), (63.7, 41.6), None, rad=0.0)
    arrow(ax, (64, 33), (74, 29), "images", off=(-0.4, 2.5), fs=7.8)
    arrow(ax, (74, 27), (64.2, 31.2), None)
    arrow(ax, (74, 12), (58, 23), "weights", off=(2.4, -1), fs=7.8)
    save(fig, "03_dfd_level0.png")


# ---------------------------------------------------------------- 04 DFD 1
def dfd1():
    fig, ax = canvas(11, 7.2, "Data flow diagram, level 1", ty=96)
    entity(ax, 1.5, 45, 12.5, 14, "User")
    process(ax, 29, 82, 8, "Authenticate", "1.0")
    process(ax, 29, 52, 7.4, "Validate\nupload", "2.0")
    process(ax, 50, 52, 8.6, "Preprocess,\nclassify and\nexplain", "3.0", fs=7.4)
    process(ax, 71, 52, 7.4, "Store\nresult", "4.0")
    process(ax, 50, 17, 8.6, "Manage history\n(list, stats,\ndelete)", "5.0", fs=7.2)
    store(ax, 52, 78, 30, 8, "session cookie", "D0")
    store(ax, 34, 30, 32, 8, "model weights", "D3")
    store(ax, 83, 52, 16, 8, "predictions", "D1")
    store(ax, 83, 31, 16, 8, "uploads /\nheatmaps", "D2")
    arrow(ax, (14, 58), (23.5, 76.5), "login", off=(-3.2, 0.5), fs=7.6)
    arrow(ax, (37, 82), (52, 82), "signed cookie", off=(0, 2.4), fs=7.6)
    arrow(ax, (14, 52), (21.6, 52), "image", off=(0, 2.4), fs=7.6)
    arrow(ax, (36.4, 52), (41.4, 52), "valid\nfile", off=(0, 3.4), fs=7.0)
    arrow(ax, (58.6, 52), (63.6, 52), "label,\nprobs", off=(0, 3.4), fs=7.0)
    arrow(ax, (78.4, 54.5), (83, 55), "row", off=(0, 2.4), fs=7.6)
    arrow(ax, (76.5, 47), (83, 38), "images", lp=(85.5, 44.5), fs=7.6)
    arrow(ax, (50, 38), (50, 43.4), "weights", off=(5.2, 0), fs=7.6)
    arrow(ax, (10, 45), (42.5, 20.5), "list / stats / delete", lp=(33, 40.5), fs=7.6, rad=0.22)
    arrow(ax, (41.4, 13.5), (12.5, 44.5), "history, stats", lp=(15, 22.5), fs=7.6, rad=0.22)
    arrow(ax, (58.6, 20), (83, 53), "rows", lp=(74, 41.5), fs=7.6)
    arrow(ax, (58.2, 14), (83, 32), "remove files", off=(4, -4.4), fs=7.6)
    ax.text(50, 3.0, "Every process except 1.0 requires a valid session (HTTP 401 otherwise).", ha="center", fontsize=8.3, color=SLATE, style="italic")
    save(fig, "04_dfd_level1.png")


# ---------------------------------------------------------------- 05 DFD 2
def dfd2():
    fig, ax = canvas(11, 6.4, "Data flow diagram, level 2: process 3.0 expanded", ty=94)
    store(ax, 2, 62, 20, 8, "uploaded image", "D2")
    labels = [
        ("3.1", "Decode\nto grayscale"), ("3.2", "Resize\n224 x 224"), ("3.3", "CLAHE\nclip 2.5, 8x8"),
        ("3.4", "Gaussian\nblur 3x3"), ("3.5", "Gray to RGB,\ndivide by 255"),
    ]
    xs = [11, 28, 45, 62, 79]
    for (n, t), x in zip(labels, xs):
        process(ax, x, 84, 7.6, t, n, fs=7.2)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.6, 84), (b - 7.6, 84), None)
    arrow(ax, (11, 70), (11, 76.4), "bytes", off=(3.8, 0), fs=7.6)
    process(ax, 79, 58, 8, "CNN\nforward\nsoftmax", "3.6", fs=7.4)
    process(ax, 57, 58, 8, "argmax,\nconfidence", "3.7", fs=7.4)
    process(ax, 57, 32, 8, "Grad-CAM\non last_conv", "3.8", fs=7.2)
    process(ax, 34, 32, 8, "Overlay\nalpha 0.4", "3.9", fs=7.4)
    entity(ax, 2, 4, 22, 14, "Result record\nlabel, confidence,\nprobabilities,\noverlay PNG")
    store(ax, 62, 6, 36, 8, "model weights (loaded once)", "D3")
    arrow(ax, (79, 76.4), (79, 66), "tensor\n224x224x3", off=(-8.2, 0), fs=7.4)
    arrow(ax, (71, 58), (65, 58), "3 probs", off=(0, 2.4), fs=7.4)
    arrow(ax, (57, 50), (57, 40), "class index", off=(5.8, 0), fs=7.4)
    arrow(ax, (49, 32), (42, 32), "heatmap\n14 x 14", off=(0, 3.6), fs=7.2)
    arrow(ax, (26, 28), (20, 17), "overlay", off=(-2.6, 1.4), fs=7.4)
    arrow(ax, (50, 53), (22, 17), "label, confidence,\nprobabilities", off=(8.4, 4.4), fs=7.4)
    arrow(ax, (92, 14), (86, 51), "weights", off=(5.6, 0), fs=7.4)
    arrow(ax, (68, 14), (61, 25), "layers", off=(-3.6, -0.6), fs=7.4)
    ax.text(50, 0.2, "3.9 also receives the 224 x 224 display image produced by preprocess_for_display().", ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "05_dfd_level2.png")


# ---------------------------------------------------------------- 06 UML class
def uml_class(ax, x, y, w, name, attrs, methods, stereo=None, color=BLUE, fs=7.6):
    lh = 2.15
    h = 4.6 + lh * (len(attrs) + len(methods)) + (1.2 if attrs and methods else 0)
    ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=color, lw=1.6))
    ax.add_patch(Rectangle((x, y - 4.6), w, 4.6, fc=color, ec=color))
    if stereo:
        ax.text(x + w / 2, y - 1.1, f"<<{stereo}>>", ha="center", va="center", color="white", fontsize=6.8)
        ax.text(x + w / 2, y - 3.1, name, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold")
    else:
        ax.text(x + w / 2, y - 2.3, name, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold")
    cy = y - 4.6 - 1.2
    for a in attrs:
        ax.text(x + 1, cy, a, fontsize=fs, va="center", color=INK, family="monospace")
        cy -= lh
    if attrs and methods:
        ax.plot([x, x + w], [cy + 0.2, cy + 0.2], color=color, lw=0.8)
        cy -= 1.0
    for m in methods:
        ax.text(x + 1, cy, m, fontsize=fs, va="center", color=INK, family="monospace")
        cy -= lh
    return (x, y - h, w, h)


def class_diagram():
    fig, ax = canvas(12, 8.6, "UML class diagram (modules drawn as classes; the code base is function-oriented)", ty=96)
    uml_class(ax, 2, 90, 30, "ApiService", ["-SESSION_SECRET : bytes", "-COOKIE : str", "-_predict_lock : Lock"],
              ["+login(Login)", "+logout() / me()", "+predict(UploadFile)", "+list_predictions(limit)", "+get_prediction(id)",
               "+delete_prediction(id)", "+stats()", "+files(kind, name)", "+make_token(email)", "+read_token(tok)"],
              "module backend.main", GREEN)
    uml_class(ax, 2, 48, 30, "Login", ["+email : str", "+password : str"], [], "pydantic BaseModel", GREEN)
    uml_class(ax, 2, 30, 30, "Keras Model", ["+input (224,224,3)", "+output softmax(n)"], ["+predict(batch)", "+get_layer(name)"], "TensorFlow", SLATE)
    uml_class(ax, 38, 90, 30, "FlaskApp", ["-_model : Model", "-_class_names : list", "-_last_conv_layer : str", "-_demo_mode : bool",
                                           "-ALLOWED_EXT : set"],
              ["+get_model() : Model", "+allowed_file(name)", "+index()", "+predict()", "+result(id)", "+history()", "+about()"],
              "module app", ORANGE)
    uml_class(ax, 38, 50, 30, "ModelBuilder", ["+CLASS_NAMES : list[3]", "+INPUT_SHAPE = (224,224,3)"],
              ["+build_custom_cnn(n, lr)", "+build_transfer_model(backbone)", "+find_last_conv_layer(model)"],
              "module model.model_builder", PURPLE)
    uml_class(ax, 38, 28, 30, "Database", ["+DB_PATH : str"],
              ["+get_connection()", "+init_db()", "+insert_prediction(...)", "+get_prediction(id)", "+get_all_predictions(limit)"],
              "module database.db", NAVY)
    uml_class(ax, 74, 90, 25, "Preprocess", ["+IMG_SIZE = (224, 224)"],
              ["+apply_clahe(gray)", "+load_and_preprocess_image(src)", "+preprocess_for_display(src)", "+get_train_augmentor()", "+get_val_augmentor()"],
              "module model.preprocess", PURPLE)
    uml_class(ax, 74, 64, 25, "GradCAM", [], ["+make_gradcam_heatmap(img,", "    model, layer, idx)", "+overlay_heatmap(img, map, a)"],
              "module model.gradcam", PURPLE)
    uml_class(ax, 74, 46, 25, "Prediction", ["+id : int", "+filename : str", "+original_path : str", "+heatmap_path : str", "+prediction : str",
                                             "+confidence : float", "+prob_normal : float", "+prob_bacterial : float", "+prob_viral : float", "+created_at : str"],
              [], "table row", GOLD)

    def link(p, q, label=None, head="-|>", ls="-", lp=None):
        arrow(ax, p, q, label, color=SLATE, lw=1.2, ls=ls, fs=7.4, head=head, lp=lp)

    link((32, 80), (38, 80), "uses", lp=(35, 82.2))
    link((68, 80), (74, 80), "imports", lp=(71, 82.2))
    link((53, 58.4), (53, 50.4), "builds / loads", lp=(60.5, 54.4))
    link((68, 42), (74, 58), "target layer", lp=(68.5, 52.6))
    link((32, 62), (38, 24), "persist", ls="--", lp=(35, 45))
    link((68, 20), (74, 30), "rows", ls="--", lp=(70, 25.6))
    link((17, 48), (17, 56.2), "request body", head="-|>", lp=(25, 52.2))
    link((38, 38), (32, 24), "builds", ls="--", lp=(35, 31.6))
    ax.text(2, 4, "Solid arrows: calls / imports.  Dashed: data or instance relationships.", fontsize=8, color=SLATE, style="italic")
    save(fig, "06_uml_class_diagram.png")


# ---------------------------------------------------------------- 07 sequence
def sequence():
    fig, ax = canvas(11.5, 8.2, "Sequence diagram: analysing one X-ray", ty=90)
    actors = [("User", 9), ("React SPA", 25), ("FastAPI\n/api/predict", 41), ("Preprocess", 57), ("CNN +\nGrad-CAM", 72), ("SQLite +\nfiles", 88)]
    top = 74
    for n, x in actors:
        box(ax, x - 7, top, 14, 7, n, fc=NAVY, ec=NAVY, tc="white", fs=8.2, bold=True)
        ax.plot([x, x], [top, 14], color=LINE, lw=1, ls=(0, (4, 3)))
    X = dict(actors)
    seq = [
        ("User", "React SPA", "choose file, press Analyse", 70, False),
        ("React SPA", "React SPA", "client check: type, size", 66.4, False),
        ("React SPA", "FastAPI\n/api/predict", "POST multipart xray_image (cookie)", 62.5, False),
        ("FastAPI\n/api/predict", "FastAPI\n/api/predict", "verify cookie, validate name/type/size", 58.5, False),
        ("FastAPI\n/api/predict", "Preprocess", "load_and_preprocess_image(path)", 54.5, False),
        ("Preprocess", "FastAPI\n/api/predict", "tensor 224x224x3", 51.2, True),
        ("FastAPI\n/api/predict", "CNN +\nGrad-CAM", "predict(batch), make_gradcam_heatmap()", 47.5, False),
        ("CNN +\nGrad-CAM", "FastAPI\n/api/predict", "probabilities, heatmap", 44, True),
        ("FastAPI\n/api/predict", "SQLite +\nfiles", "save overlay PNG, insert_prediction()", 40.2, False),
        ("SQLite +\nfiles", "FastAPI\n/api/predict", "row id", 36.8, True),
        ("FastAPI\n/api/predict", "React SPA", "201 JSON record", 33.2, True),
        ("React SPA", "React SPA", "navigate to /app/result/:id", 29.5, False),
        ("React SPA", "FastAPI\n/api/predict", "GET prediction and image URLs", 25.8, False),
        ("FastAPI\n/api/predict", "React SPA", "JSON + original and heatmap images", 22.2, True),
        ("React SPA", "User", "badge, confidence, bars, side-by-side", 18.4, True),
    ]
    for a, b, label, y, ret in seq:
        xa, xb = X[a], X[b]
        if a == b:
            ax.add_patch(Rectangle((xa, y - 1.2), 4, 2.4, fc="#E8F0FC", ec=BLUE, lw=1))
            ax.text(xa + 5, y, label, fontsize=7.6, va="center", color=INK)
        else:
            arrow(ax, (xa, y), (xb, y), None, color=BLUE if not ret else GREEN, ls="--" if ret else "-", lw=1.4)
            ax.text((xa + xb) / 2, y + 1.4, label, fontsize=7.6, ha="center", color=INK,
                    bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))
    ax.add_patch(Rectangle((2, 56.5), 94, 0.001, fc="none"))
    ax.text(50, 9, "Alternative: on any validation failure the API answers 400 / 413 / 401 with {\"detail\": ...} and nothing is saved.",
            ha="center", fontsize=8.2, color=SLATE, style="italic")
    save(fig, "07_sequence_diagram.png")


# ---------------------------------------------------------------- 08 use case
def use_case():
    fig, ax = canvas(11, 7.4, "Use-case diagram", ty=76)
    ax.add_patch(Rectangle((24, 4), 52, 66, fc="#FBFCFE", ec="#D5DCE6", lw=1.4))
    ax.text(50, 67.2, "Pneumonia Detection System", ha="center", fontsize=10, fontweight="bold", color=NAVY)
    cases = [
        ("Sign in with demo account", 59), ("Upload chest X-ray", 53), ("View class, confidence\nand probabilities", 47),
        ("Inspect Grad-CAM\n(side by side / blend)", 41), ("Browse history\nsearch, filter, sort", 35),
        ("Export history as CSV", 29), ("View dashboard statistics", 23), ("Print report / download heatmap", 17), ("Delete a scan", 11),
    ]
    pos = {}
    for t, y in cases:
        ax.add_patch(Ellipse((50, y), 38, 4.9, fc="#E8F0FC", ec=BLUE, lw=1.3))
        ax.text(50, y, t, ha="center", va="center", fontsize=7.8, color=INK, linespacing=1.1)
        pos[t] = y
    # actor 1
    def actor(x, y, label, color):
        ax.add_patch(Circle((x, y + 8), 2.2, fc="white", ec=color, lw=1.8))
        ax.plot([x, x], [y + 5.8, y + 1.2], color=color, lw=1.8)
        ax.plot([x - 3, x + 3], [y + 4.2, y + 4.2], color=color, lw=1.8)
        ax.plot([x, x - 2.5], [y + 1.2, y - 2.6], color=color, lw=1.8)
        ax.plot([x, x + 2.5], [y + 1.2, y - 2.6], color=color, lw=1.8)
        ax.text(x, y - 5, label, ha="center", fontsize=8.6, fontweight="bold", color=INK, linespacing=1.15)
    actor(10, 36, "User\n(clinician / student)", ORANGE)
    for t, y in cases:
        ax.plot([13, 31], [42, y], color=LINE, lw=0.9)
    # actor 2 (developer, outside the web UI)
    actor(90, 24, "Developer", PURPLE)
    box(ax, 79, 6, 19, 6, "Train / export model\n(scripts, outside UI)", fc="#EFEBFC", ec=PURPLE, fs=7.2)
    ax.plot([90, 90], [18.5, 12], color=PURPLE, lw=1)
    ax.text(50, 1.2, "Every case except 'Sign in' needs a valid session.", ha="center", fontsize=8.2, color=SLATE, style="italic")
    save(fig, "08_use_case_diagram.png")


# ---------------------------------------------------------------- 09 ER
def er():
    fig, ax = canvas(11, 6.4, "Entity-relationship diagram of the stored data", ty=70)
    # predictions table
    x, y, w = 31, 61, 38
    cols = [("id", "INTEGER", "PK, autoincrement"), ("filename", "TEXT", "NOT NULL"), ("original_path", "TEXT", "NOT NULL"), ("heatmap_path", "TEXT", "NOT NULL"),
            ("prediction", "TEXT", "NOT NULL"), ("confidence", "REAL", "NOT NULL"), ("prob_normal", "REAL", ""), ("prob_bacterial", "REAL", ""),
            ("prob_viral", "REAL", ""), ("created_at", "TEXT", "NOT NULL, ISO-8601 UTC")]
    lh = 3.4
    h = 5 + lh * len(cols)
    ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=NAVY, lw=1.8))
    ax.add_patch(Rectangle((x, y - 5), w, 5, fc=NAVY, ec=NAVY))
    ax.text(x + w / 2, y - 2.5, "predictions", ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    for i, (n, t, c) in enumerate(cols):
        yy = y - 5 - lh * (i + 0.5)
        ax.text(x + 1.2, yy, ("PK  " if n == "id" else "     ") + n, fontsize=8, va="center", family="monospace", color=INK, fontweight="bold" if n == "id" else "normal")
        ax.text(x + 19.5, yy, t, fontsize=7.6, va="center", family="monospace", color=BLUE)
        ax.text(x + 27, yy, c.replace("autoincrement", "auto").replace("NOT NULL, ISO-8601 UTC", "NOT NULL"), fontsize=6.6, va="center", color=SLATE)
    up = box(ax, 3, 36, 22, 12, "static/uploads/\n<12-hex-id>.jpg|png\n(original X-ray)", fc="#FFF8E5", ec=GOLD, fs=8)
    hm = box(ax, 3, 14, 22, 12, "static/heatmaps/\n<12-hex-id>_heatmap.png\n(Grad-CAM overlay)", fc="#FFF8E5", ec=GOLD, fs=8)
    us = box(ax, 76, 36, 21, 14, "User (demo)\nemail, name, role\nfrom .env,\nnot persisted\nsigned cookie only", fc="#FFF1EA", ec=ORANGE, fs=8, ls="--")
    cl = box(ax, 76, 14, 21, 12, "Class label set\nNormal | Bacterial\nPneumonia | Viral\nPneumonia", fc="#EFEBFC", ec=PURPLE, fs=8, ls="--")
    arrow(ax, (25, 42), (31, 49.5), "original_path", off=(-1, 3), fs=7.8, head="-")
    arrow(ax, (25, 20), (31, 41), "heatmap_path", off=(-4.8, -1.5), fs=7.8, head="-")
    arrow(ax, (76, 43), (69, 49), "creates (via API)", off=(0, 3.2), fs=7.8, head="-", ls="--")
    arrow(ax, (76, 20), (69, 40), "prediction in set", off=(8.2, -3.2), fs=7.8, head="-", ls="--")
    ax.text(26.5, 52.4, "1", fontsize=9, color=NAVY, fontweight="bold")
    ax.text(27, 31.5, "1", fontsize=9, color=NAVY, fontweight="bold")
    ax.text(3, 3.4, "One physical table. Each row owns exactly one original image and one heatmap file (1 : 1 : 1).\nDashed boxes are logical entities that are not stored as tables.",
            fontsize=8, color=SLATE, style="italic", linespacing=1.4)
    save(fig, "09_er_diagram.png")


# ---------------------------------------------------------------- 10 flowchart
def diamond(ax, cx, cy, w, h, text, fc="#FFF8E5", ec=GOLD, fs=8):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], closed=True, fc=fc, ec=ec, lw=1.5))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.1)


def flowchart():
    fig, ax = canvas(10.5, 9.6, "Flowchart of the core algorithm (POST /api/predict)", ty=104)
    cx = 36
    def term(y, t):
        box(ax, cx - 11, y - 2.2, 22, 4.4, t, fc=NAVY, ec=NAVY, tc="white", fs=8.4, bold=True, rounding=2.2)
    def step(y, t, c=BLUE, w=30):
        box(ax, cx - w / 2, y - 2.8, w, 5.6, t, fc="#F4F8FE", ec=c, fs=8)
    ys = [96, 88.5, 80, 71.5, 63, 54.5, 46, 37.5, 29, 20.5, 12]
    term(ys[0], "Start: upload received")
    diamond(ax, cx, ys[1], 30, 7.4, "session cookie\nvalid?")
    diamond(ax, cx, ys[2], 30, 7.4, "file present, named,\nextension jpg / jpeg / png?")
    diamond(ax, cx, ys[3], 30, 7.4, "size <= 8 MB?")
    step(ys[4], "save original as <12-hex-id>.<ext>")
    diamond(ax, cx, ys[5], 30, 7.4, "decodable\nas an image?")
    step(ys[6], "grayscale, resize 224, CLAHE,\nGaussian blur, divide by 255", PURPLE, 34)
    step(ys[7], "probs = model.predict(batch)\nidx = argmax(probs),  conf = probs[idx]", GREEN, 34)
    step(ys[8], "Grad-CAM on last_conv for class idx\noverlay (alpha 0.4), write heatmap PNG", GOLD, 34)
    step(ys[9], "INSERT row into predictions", NAVY)
    term(ys[10], "Return 201 + JSON record")
    for a, b in zip(ys[:-1], ys[1:]):
        gap = 2.2 if a == ys[0] else (3.7 if a in (ys[1], ys[2], ys[3], ys[5]) else 2.8)
        top = b + (2.2 if b == ys[10] else (3.7 if b in (ys[1], ys[2], ys[3], ys[5]) else 2.8))
        arrow(ax, (cx, a - gap), (cx, top), None, lw=1.3)
    for y, lab in ((ys[1], "401"), (ys[2], "400"), (ys[3], "413"), (ys[5], "400")):
        arrow(ax, (cx + 15, y), (cx + 24, y), None, color=ORANGE, lw=1.3)
        box(ax, cx + 24, y - 2.4, 21, 4.8, f"{lab} error JSON\n(nothing stored)" if lab != "400" or y == ys[2] else "400, delete saved file", fc="#FFF1EA", ec=ORANGE, fs=7.6)
        ax.text(cx + 19.5, y + 1.6, "no", fontsize=7.6, color=ORANGE, ha="center")
    for y in (ys[1], ys[2], ys[3], ys[5]):
        ax.text(cx + 1.3, y - 4.7, "yes", fontsize=7.6, color=GREEN)
    save(fig, "10_core_algorithm_flowchart.png")


def main():
    for fn in (architecture, workflow, dfd0, dfd1, dfd2, class_diagram, sequence, use_case, er, flowchart):
        fn()


if __name__ == "__main__":
    main()
