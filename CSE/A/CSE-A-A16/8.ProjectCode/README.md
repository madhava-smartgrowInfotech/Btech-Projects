# Sign Language Recognition System (CNN-based)

CSE-A · Batch 16

An end-to-end, pure-Python desktop application that recognizes American
Sign Language (ASL) alphabet gestures live from a webcam using a
Convolutional Neural Network, and speaks the resulting sentence aloud.

Built from the project abstract (`2.ABSTRACT.docx`) and base paper
reference (`3.BASE PAPER.docx`, *MAG-KD*, IEEE Access 2026).

## Pipeline

1. Webcam captures live video.
2. A region of interest (ROI) box crops the hand.
3. Grayscale conversion.
4. Noise reduction (Gaussian blur).
5. Segmentation (Otsu binary threshold isolates the hand silhouette).
6. Normalization (resize to 64×64, scale to `[0, 1]`).
7. A CNN classifies the gesture (26 letters + `space` + `del` + `nothing`).
8. Predictions are debounced/smoothed across frames and typed into a
   sentence.
9. The sentence can be spoken aloud (offline text-to-speech).

## Project layout

```
sign_language_app/
  config.py          constants (paths, image size, classes, thresholds)
  preprocessing.py   grayscale -> blur -> segmentation -> normalization
  camera.py          threaded webcam capture
  model.py           CNN architecture (Keras)
  dataset.py         loads collected images into train/val/test splits
  train.py           training loop, saves model + labels + report
  recognizer.py       loads the trained model, smooths live predictions
  tts.py              offline text-to-speech (pyttsx3)
  gui/
    app.py            main window, sidebar navigation
    recognize_tab.py   live recognition + sentence + speak
    collect_tab.py      webcam data collection (per-class capture)
    train_tab.py         hyperparameters + live training chart
    about_tab.py          abstract / pipeline / base paper reference
data/                 collected training images, one folder per class
models/               trained model, labels.json, training report
run.py                entry point
```

## Setup

```bash
pip install -r requirements.txt
```

(Tested with Python 3.10, TensorFlow 2.15, OpenCV, customtkinter, pyttsx3.)

## Usage

```bash
python run.py
```

The app opens with four tabs in the sidebar:

1. **Collect Data** — pick a class (A–Z, `space`, `del`, `nothing`), start
   the camera, place your hand in the cyan ROI box, and capture images
   either one at a time or in a burst (e.g. 100 at once). Aim for ~150–250
   images per class, varying hand angle/distance slightly, against a
   plain, well-lit background. You need at least 2 classes with images to
   train.

   Alternatively, drop an existing dataset (e.g. the public Kaggle "ASL
   Alphabet" dataset) into `data/<CLASS>/*.jpg` — the folder names must
   match the class labels (`A`-`Z`, `space`, `del`, `nothing`).

2. **Train Model** — review the dataset counts, set epochs / batch size /
   learning rate (sensible defaults are pre-filled), and click **Start
   Training**. Training runs on a background thread; accuracy/val-accuracy
   update live on the chart. The best model (by validation accuracy) is
   saved to `models/asl_cnn_model.keras`, with `labels.json` and a
   `classification_report.txt`.

3. **Recognize** — start the camera, place your hand in the ROI box. The
   predicted letter, a confidence bar, and the live segmented mask are
   shown. Holding a sign steady for about a second commits it to the
   sentence box automatically; `space` and `del` gestures work as expected
   (or use the on-screen Space / Backspace / Clear buttons). Click **Speak
   Sentence** to hear it read aloud.

4. **About** — the project abstract, the full preprocessing pipeline, and
   the base paper this project builds on.

## Notes

- No external dataset is bundled — you either collect your own via the
  **Collect Data** tab or supply one in the layout described above.
- Segmentation mode defaults to grayscale + Otsu threshold
  (`config.SEGMENTATION_MODE = "threshold"`); a skin-color (YCrCb) mode is
  also implemented in `preprocessing.segment_skin` and can be selected by
  changing that constant if your background is too textured for clean
  threshold segmentation.
- This was developed and smoke-tested (imports, dataset/model wiring,
  syntax) in an environment without a physical webcam attached; run it on
  your machine with a webcam connected to collect data, train, and use
  live recognition.

## Web app (SignSpeak)

A React + FastAPI front end for the same pipeline lives in `frontend/` and `backend/` (the desktop app above is unchanged).
Run `run.bat` and open http://localhost:5316 - details in `docs/03_HOW_TO_RUN.md`, screens and API in `docs/FRONTEND_PLAN.md`.
The browser reads the webcam; `backend/main.py` is a thin layer over `preprocessing`, `recognizer`, `dataset`, `train` and `tts`.
