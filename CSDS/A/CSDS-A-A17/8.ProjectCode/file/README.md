# Automated Plastic Waste Detection in Oceans Using Artificial Intelligence

AI-powered detection and localisation of plastic waste in ocean images, built
as a B.Tech Data Science final-year project. A YOLO object-detection model
identifies plastic waste in uploaded ocean/water images, draws bounding
boxes with confidence scores, and presents results through an interactive
Streamlit dashboard.

## Table of Contents
1. [Description](#description)
2. [Problem Statement](#problem-statement)
3. [Objectives](#objectives)
4. [Features](#features)
5. [Architecture](#architecture)
6. [Technologies](#technologies)
7. [Dataset Requirements](#dataset-requirements)
8. [Installation](#installation)
9. [Virtual Environment Setup](#virtual-environment-setup)
10. [Model Training](#model-training)
11. [Model Evaluation](#model-evaluation)
12. [Running the Application](#running-the-application)
13. [GitHub Upload Instructions](#github-upload-instructions)
14. [Expected Output](#expected-output)
15. [Limitations](#limitations)
16. [Future Scope](#future-scope)

## Description
Plastic pollution in oceans is a growing environmental crisis. This project
builds a computer-vision pipeline — preprocessing, YOLO-based detection,
evaluation, and a Streamlit web interface — to automatically detect and
localise plastic waste in ocean images, with an architecture kept extensible
for future video, drone and robotic applications.

## Problem Statement
Plastic waste in oceans harms marine ecosystems. Manual monitoring is slow,
costly and limited in coverage. Classification-only approaches do not
localise individual plastic objects. This system automatically detects and
localises plastic waste in ocean images.

## Objectives
1. Collect and annotate a dataset of ocean images containing plastic waste.
2. Preprocess images to handle lighting, reflections and turbidity.
3. Train a deep-learning object detector for plastic waste.
4. Localise each plastic item with bounding boxes and confidence scores.
5. Provide a prototype interface to upload images and view detections.
6. Evaluate detection accuracy using precision, recall and mAP.

## Features
- Upload JPG/JPEG/PNG ocean images
- Underwater-aware preprocessing pipeline (colour correction, denoising, CLAHE)
- YOLO-based object detection with adjustable confidence threshold (0.1–0.9)
- Bounding boxes, per-object confidence scores, and detection counts
- Downloadable annotated image and JSON detection report
- SQLite-backed detection history with a clear-history option
- Dashboard with aggregate stats and charts
- Evaluation page showing real Precision/Recall/mAP/confusion-matrix results
- GPU auto-detection with automatic CPU fallback

## Architecture
```
User
  ↓
Streamlit Interface
  ↓
Image Upload
  ↓
Image Preprocessing
  ↓
YOLO Object Detection Model
  ↓
Bounding Box + Confidence
  ↓
Post Processing
  ↓
Results Dashboard
  ↓
Database / Download Report
```

### Project Structure
```
plastic-waste-detection/
│
├── app.py                  # Streamlit Home page (entry point)
├── train.py                # Training pipeline
├── evaluate.py              # Evaluation script (Precision/Recall/mAP)
├── predict.py                # CLI single-image inference
│
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   ├── images/{train,val,test}/
│   ├── labels/{train,val,test}/
│   └── data.yaml
│
├── models/
│   └── best.pt              # produced by train.py (not included)
│
├── src/
│   ├── __init__.py
│   ├── model.py              # model loading, caching, device selection
│   ├── preprocessing.py      # preprocess_image() pipeline
│   ├── detection.py          # run_detection() + annotation drawing
│   ├── database.py           # SQLite detection history
│   └── utils.py               # shared helpers
│
├── pages/
│   ├── 1_🔍_Detection.py
│   ├── 2_📊_Dashboard.py
│   ├── 3_📈_Evaluation.py
│   └── 4_ℹ️_About.py
│
├── results/                  # evaluation plots, eval_summary.json
├── reports/                   # per-run JSON detection reports
└── assets/
```

## Technologies
- **Backend:** Python 3.10+, OpenCV, NumPy, Pandas, PyTorch
- **Model:** Ultralytics YOLO (YOLOv8) — see the in-app *About* page for the
  YOLOv7 base-paper comparison
- **Frontend:** Streamlit
- **Visualization:** Matplotlib, Plotly
- **Storage:** Local filesystem, SQLite (detection history)

## Dataset Requirements
**REQUIRED USER INPUT** — no dataset is bundled with this project.

Place your annotated dataset as:
```
data/images/train/*.jpg
data/images/val/*.jpg
data/images/test/*.jpg
data/labels/train/*.txt
data/labels/val/*.txt
data/labels/test/*.txt
```
Each label `.txt` uses YOLO format, one line per object:
```
class_id x_center y_center width height
```
All coordinates normalised to `[0, 1]`. Class names are configured in
`data/data.yaml` (defaults to a single `plastic` class — extend this if your
dataset has multiple plastic categories).

Suggested starting points (verify licensing before use): the TACO (Trash
Annotations in Context) dataset, or marine-litter/plastic datasets on
Roboflow Universe or Kaggle.

## Installation

### Virtual Environment Setup
```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Model Training
```bash
python train.py --epochs 50 --img-size 640 --batch-size 16
```
This performs transfer learning starting from COCO-pretrained YOLOv8
weights. On completion it saves `models/best.pt` and copies training plots
(loss curves, confusion matrix, etc.) into `results/`. Epochs, image size
and batch size are configurable via CLI flags — the defaults above are
starting points, not guaranteed optimal values.

## Model Evaluation
```bash
python evaluate.py --weights models/best.pt --data data/data.yaml --split val
```
Computes Precision, Recall, mAP@0.5 and mAP@0.5:0.95 from the actual trained
model (never fabricated), saves `results/eval_summary.json`, and copies the
confusion matrix / PR curve plots into `results/` for the Evaluation page.

## Running the Application
```bash
streamlit run app.py
```
Then open the local URL Streamlit prints (typically `http://localhost:8501`).
Use the sidebar to navigate between Home, Detection, Dashboard, Evaluation
and About.

### CLI inference (optional)
```bash
python predict.py --image path/to/image.jpg --conf 0.5 --save-history
```

## GitHub Upload Instructions
```bash
git init
git add .
git commit -m "Initial project setup"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```
For ongoing development, commit regularly with descriptive messages, e.g.:
```bash
git add .
git commit -m "Add preprocessing pipeline for underwater images"
git push
```
Committing after each meaningful change (a new script, a bug fix, a training
run) creates a clean history useful for demonstrating project progress
during a review or internship.

## Expected Output
- **Detection page:** original image next to an annotated image with green
  bounding boxes, a confidence score per object (e.g. `Plastic 1 → 91.4%`),
  a detection table, and download buttons for the image and JSON report.
- **Dashboard:** summary cards (total images analysed, total objects
  detected, average/highest confidence) and charts built from real logged
  history — empty until you run at least one detection.
- **Evaluation page:** Precision/Recall/mAP metrics and plots — empty with a
  clear message until `evaluate.py` has been run on a trained model.

## Limitations
- No dataset or trained weights are bundled — detection accuracy depends
  entirely on the dataset you collect/annotate and the training you run.
- Without a trained model, the app falls back to a general COCO-pretrained
  model (clearly flagged in the UI) that will not reliably detect "plastic"
  as a class.
- Single-image inference only in this version; no video/stream support yet.
- Confidence/mAP values are only as reliable as the underlying dataset size
  and annotation quality.

## Future Scope
- Real-time video detection
- Drone-based monitoring
- Underwater camera integration
- Robotic waste collection (path-planning, as in the base paper)
- Mobile application
- Cloud deployment
- Edge AI (on-device inference)
- GPS-based pollution mapping
- Plastic-type classification (bottle, bag, net, styrofoam, etc.)
- Real-time ocean monitoring networks
