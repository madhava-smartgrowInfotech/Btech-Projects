"""
app.py
------
Flask web application for the Pneumonia Detection Using Deep Learning
project (proposed system).

Pipeline per upload:
    1. Accept a chest X-ray image (jpg/png).
    2. Preprocess it (resize -> CLAHE enhancement -> normalize).
    3. Run the CNN classifier -> Normal / Bacterial Pneumonia / Viral Pneumonia.
    4. Generate a Grad-CAM heatmap highlighting the affected lung regions.
    5. Persist the result (SQLite) and render it to the user.
"""

import os
import uuid
import json

import numpy as np
import cv2
from flask import Flask, render_template, request, redirect, url_for, flash

from model.preprocess import load_and_preprocess_image, preprocess_for_display
from model.model_builder import build_custom_cnn, find_last_conv_layer, CLASS_NAMES
from model.gradcam import make_gradcam_heatmap, overlay_heatmap
from database.db import init_db, insert_prediction, get_prediction, get_all_predictions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
HEATMAP_FOLDER = os.path.join(BASE_DIR, "static", "heatmaps")
SAVED_MODEL_DIR = os.path.join(BASE_DIR, "saved_models")
MODEL_PATH = os.path.join(SAVED_MODEL_DIR, "pneumonia_model.h5")
CLASS_MAP_PATH = os.path.join(SAVED_MODEL_DIR, "class_indices.json")
ALLOWED_EXT = {"png", "jpg", "jpeg"}

app = Flask(__name__)
app.secret_key = "pneumonia-detection-secret-key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HEATMAP_FOLDER, exist_ok=True)
os.makedirs(SAVED_MODEL_DIR, exist_ok=True)

# ---------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------
_model = None
_class_names = CLASS_NAMES
_last_conv_layer = None
_demo_mode = False


def get_model():
    """
    Lazily load the trained model. If no trained weights are found on
    disk (saved_models/pneumonia_model.h5), fall back to an untrained
    (randomly initialized) network so the *full pipeline* still runs
    end-to-end for demonstration -- clearly flagged as DEMO MODE in the UI.
    Train a real model with model/train.py on a labeled dataset before
    using this for anything beyond a pipeline demo.
    """
    global _model, _class_names, _last_conv_layer, _demo_mode

    if _model is not None:
        return _model

    from tensorflow.keras.models import load_model

    if os.path.exists(MODEL_PATH):
        _model = load_model(MODEL_PATH)
        if os.path.exists(CLASS_MAP_PATH):
            with open(CLASS_MAP_PATH) as f:
                idx_to_class = json.load(f)
            _class_names = [idx_to_class[str(i)] for i in range(len(idx_to_class))]
        _demo_mode = False
        print("Loaded trained model from", MODEL_PATH)
    else:
        _model = build_custom_cnn(num_classes=3)
        _class_names = CLASS_NAMES
        _demo_mode = True
        print("WARNING: no trained model found at", MODEL_PATH)
        print("Running in DEMO MODE with an untrained network.")
        print("Run: python model/train.py --data_dir <dataset> to train a real model.")

    _last_conv_layer = find_last_conv_layer(_model)
    return _model


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", demo_mode=_demo_mode)


@app.route("/predict", methods=["POST"])
def predict():
    model = get_model()  # ensures _demo_mode flag is set

    if "xray_image" not in request.files:
        flash("No file part in the request.")
        return redirect(url_for("index"))

    file = request.files["xray_image"]
    if file.filename == "":
        flash("Please choose an X-ray image to upload.")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Unsupported file type. Please upload a JPG or PNG image.")
        return redirect(url_for("index"))

    # Save the original upload with a unique name
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_id = uuid.uuid4().hex[:12]
    saved_name = f"{unique_id}.{ext}"
    saved_path = os.path.join(UPLOAD_FOLDER, saved_name)
    file.save(saved_path)

    # ---- Preprocess ----
    preprocessed = load_and_preprocess_image(saved_path)          # (224,224,3) float32 [0,1]
    display_img = preprocess_for_display(saved_path)               # (224,224,3) uint8
    batch = np.expand_dims(preprocessed, axis=0)

    # ---- Predict ----
    probs = model.predict(batch, verbose=0)[0]
    pred_idx = int(np.argmax(probs))
    prediction_label = _class_names[pred_idx]
    confidence = float(probs[pred_idx])

    prob_map = {name: float(p) for name, p in zip(_class_names, probs)}

    # ---- Grad-CAM heatmap ----
    heatmap, _ = make_gradcam_heatmap(batch, model, _last_conv_layer, pred_index=pred_idx)
    overlay = overlay_heatmap(display_img, heatmap, alpha=0.4)

    heatmap_name = f"{unique_id}_heatmap.png"
    heatmap_path = os.path.join(HEATMAP_FOLDER, heatmap_name)
    cv2.imwrite(heatmap_path, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

    # ---- Persist ----
    pred_id = insert_prediction(
        filename=file.filename,
        original_path=f"uploads/{saved_name}",
        heatmap_path=f"heatmaps/{heatmap_name}",
        prediction=prediction_label,
        confidence=confidence,
        prob_normal=prob_map.get("Normal", 0.0),
        prob_bacterial=prob_map.get("Bacterial Pneumonia", 0.0),
        prob_viral=prob_map.get("Viral Pneumonia", 0.0),
    )

    return redirect(url_for("result", pred_id=pred_id))


@app.route("/result/<int:pred_id>")
def result(pred_id):
    record = get_prediction(pred_id)
    if record is None:
        flash("Prediction not found.")
        return redirect(url_for("index"))
    return render_template("result.html", record=record, demo_mode=_demo_mode)


@app.route("/history")
def history():
    records = get_all_predictions()
    return render_template("history.html", records=records)


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    init_db()
    get_model()  # warm up model + print demo-mode warning at startup
    app.run(debug=True, host="0.0.0.0", port=5000)
