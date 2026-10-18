# Pneumonia Detection Using Deep Learning

A Flask web application implementing the **proposed system** from the project
abstract: upload a chest X-ray image and get an AI-assisted classification
into **Normal / Bacterial Pneumonia / Viral Pneumonia**, with a Grad-CAM
heatmap highlighting the lung regions that drove the prediction.

This builds on top of (and does not remove) the existing project artefacts:
the abstract, the review presentation (Introduction, Domain Knowledge,
Technology Awareness, Existing System & its limitations) — this codebase is
the working implementation of the **Proposed System** section referenced
there.

## Tech stack (matches the "Technology Awareness" slide)

| Layer     | Tools |
|-----------|-------|
| Front end | HTML, CSS, JavaScript, Bootstrap 5, Flask (Jinja2) templates |
| Back end  | Python, Flask, OpenCV, TensorFlow / Keras |
| Database  | SQLite (prediction history) |

## New React front end (V2 Neo Brutal Grid)

A rebuilt interface lives in `frontend/` and talks to a thin FastAPI layer in `backend/` that reuses the same model, Grad-CAM and SQLite code. The original Flask app (`app.py`, `templates/`) is untouched and still works.

- Start everything with `run.bat` (UI on http://localhost:5312, API on 8312). Demo login: `demo@pneumodetect.ai` / `Pneumo@123`.
- Screens: landing, sign-in, dashboard, new scan, result, history, about. Screenshots are in `docs/screenshots/`.
- Details: `docs/03_HOW_TO_RUN.md` and `docs/FRONTEND_PLAN.md`.

## Project structure

```
pneumonia_detection_system/
├── app.py                     # Flask app: upload -> predict -> Grad-CAM -> history
├── requirements.txt
├── model/
│   ├── preprocess.py          # Resize, CLAHE enhancement, normalization, augmentation
│   ├── model_builder.py       # Custom CNN + transfer-learning (DenseNet/ResNet/EfficientNet) options
│   ├── gradcam.py             # Grad-CAM heatmap generation
│   └── train.py                # Training script (run against a real dataset)
├── database/
│   └── db.py                  # SQLite persistence layer
├── templates/                 # Bootstrap-based HTML (index, result, history, about)
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   ├── uploads/                # Saved original X-rays
│   └── heatmaps/                # Saved Grad-CAM overlays
└── saved_models/               # Trained model (.h5) + class_indices.json go here
```

## 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Train the model (recommended before real use)

Download a chest X-ray dataset, e.g. the Kaggle "Chest X-Ray Images
(Pneumonia)" dataset referenced in the paper, and arrange it as:

```
dataset/
  train/{NORMAL,BACTERIA,VIRUS}/*.jpeg
  val/{NORMAL,BACTERIA,VIRUS}/*.jpeg
  test/{NORMAL,BACTERIA,VIRUS}/*.jpeg
```

(If your dataset only has NORMAL/PNEUMONIA folders, the training script
still works — it just becomes a 2-class model; `app.py` reads the classes
dynamically from `class_indices.json`.)

Then run:

```bash
# from-scratch custom CNN (no internet / pretrained weights required)
python model/train.py --data_dir dataset --backbone custom --epochs 30

# OR transfer learning with a pretrained backbone (best accuracy,
# matches the reference paper's DenseNet201 result of ~99.7%)
python model/train.py --data_dir dataset --backbone densenet201 --epochs 20
```

This saves:
- `saved_models/pneumonia_model.h5` — the trained model
- `saved_models/class_indices.json` — class name mapping
- `saved_models/training_curves.png`, `confusion_matrix.png`, `classification_report.txt`

## 3. Run the web app

```bash
python app.py
```

Visit **http://localhost:5000**.

- If no trained model is found yet, the app still runs end-to-end in
  **Demo Mode** (clearly labeled in the UI) using an untrained network,
  so you can verify the full pipeline before training.
- Once `saved_models/pneumonia_model.h5` exists, it's loaded automatically
  and demo mode turns off.

## How the proposed-system pipeline works

1. **Upload** — user submits a chest X-ray (jpg/png) via drag-and-drop or file picker.
2. **Preprocess** (`model/preprocess.py`) — resize to 224×224, CLAHE contrast
   enhancement, Gaussian denoise, normalize to [0,1].
3. **Classify** (`model/model_builder.py`) — CNN predicts Normal / Bacterial
   Pneumonia / Viral Pneumonia with per-class confidence.
4. **Explain** (`model/gradcam.py`) — Grad-CAM overlay shows which lung
   regions most influenced the prediction.
5. **Persist** (`database/db.py`) — every prediction (image paths, label,
   confidences, timestamp) is stored in SQLite and viewable on the
   **History** page.

## Disclaimer

This is an academic / research prototype for computer-aided screening
support only. It is **not** a certified medical device and must not be
used as the sole basis for clinical diagnosis or treatment decisions.
