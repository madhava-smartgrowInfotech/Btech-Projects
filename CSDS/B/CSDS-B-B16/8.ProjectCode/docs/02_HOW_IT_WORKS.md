# RetinaGuard - How it works

## 1. Image pipeline (`backend/app/services/preprocess.py`, `wavelet.py`)

1. **Crop and square** - the black border around the circular field of view is cropped and the image padded to a square,
   then resized to 512 x 512 for display.
2. **Green channel** - vessels and lesions have the best contrast in the green channel.
3. **CLAHE** - contrast-limited adaptive histogram equalisation (clip 2.0, 8 x 8 tiles); pixels outside the field of
   view are zeroed.
4. **Resize and normalise** - 256 x 256, per-image zero mean / unit variance.
5. **Quality check** - inside the field of view: variance of the Laplacian (sharpness, min 150), mean green intensity
   (brightness, 20-180) and the share of clipped pixels (max 25%). The limits were set from the training images
   (1st-percentile sharpness is about 310), so a Gaussian blur with sigma >= 5 or a strongly under-exposed photo fails.
   A failed check is shown as a warning and printed on the report; the analysis still runs.
6. **Haar wavelets** - a 2-level `pywt.dwt2(..., "haar")`: level 1 gives LL/LH/HL/HH at 128 x 128, level 2 at 64 x 64.
   LH, HL and HH carry horizontal, vertical and diagonal edges (vessel walls, haemorrhage borders, exudates).

## 2. Retinopathy model (`services/lenet.py`, `ml/train_retina.py`)

- **Input** - 8 channels at 128 x 128: the 4 level-1 bands plus the 4 level-2 bands upsampled, each standardised.
- **LeNet** - conv5(16) -> pool -> conv5(32) -> pool -> conv3(48) -> pool -> FC 120 -> FC 84 -> 1 logit
  (batch-norm and dropout added for stability on a small dataset). About 1 M parameters, so it trains on a CPU in
  about 4 minutes.
- **Training** - stratified 70/15/15 split (seed 42), random flip / rotation (+-20 deg) / scale / brightness
  augmentation, Adam (lr 1e-3, weight decay 1e-4), cosine schedule, class-weighted BCE, 60 epochs. The epoch with
  the best validation ROC-AUC is kept; the decision threshold is chosen on the validation split (Youden's J).
- **Grad-CAM** - gradients of the logit with respect to the last conv block give channel weights; the weighted
  activation map is upsampled and overlaid on the fundus.
- **Frangi vessel map** - `skimage.filters.frangi` (sigmas 1-5, dark ridges) on the CLAHE image. It also gives
  **vessel density** (share of vessel pixels) and a **mean vessel width** proxy (twice the mean distance transform
  over vessel pixels).

## 3. Heart-disease model (`services/heart.py`, `ml/train_heart.py`)

- 13 clinical inputs: age, sex, chest-pain type, resting BP, cholesterol, fasting sugar, resting ECG, max heart rate,
  exercise angina, ST depression, ST slope, number of major vessels, thallium test.
- **Data cleaning** - the Kaggle CSV has 1025 rows but only 302 unique patients, so duplicates are removed before
  splitting; otherwise the same patient lands in train and test and scores look near-perfect.
- **Label fix** - every one of the 302 rows was matched against the UCI Cleveland file: the Kaggle `target` column
  is inverted (`target = 1` means *no* disease). RetinaGuard trains on `disease = 1 - target`.
- **Code mapping** (Kaggle code -> meaning, checked against UCI):

  | Field | Codes |
  |-------|-------|
  | cp | 0 asymptomatic, 1 atypical angina, 2 non-anginal pain, 3 typical angina |
  | restecg | 0 LV hypertrophy, 1 normal, 2 ST-T abnormality |
  | slope | 0 downsloping, 1 flat, 2 upsloping |
  | thal | 1 fixed defect, 2 normal, 3 reversible defect |

- **Model** - Random Forest, 300 trees, max depth 6, min 3 samples per leaf; stratified 75/25 split (seed 42).
- **SHAP** - `shap.TreeExplainer` gives each input's contribution to the predicted probability; the six largest are
  shown and printed on the report.

## 4. Combined risk stage (`services/staging.py`)

Each side scores 0-3 points:

| Points | Retina (probability) | Heart (probability) |
|--------|----------------------|---------------------|
| +1 | >= 0.30 | >= 0.30 |
| +1 | >= model threshold (~0.52) | >= 0.50 |
| +1 | >= 0.80 | >= 0.75 |

Total 0-1 = **Low**, 2-3 = **Moderate**, 4-5 = **High**, 6 = **Very high**. A resting BP of 180 mmHg or more raises
the stage to at least High. Each stage has its own follow-up recommendations, plus extra lines when the retinal or
cardiac side is positive.

## 5. Evaluation (`ml/eval.py` -> `experiments/eval/metrics.json`)

Held-out test sets that were never used for training or model selection:

| Model | Test cases | Accuracy | Sensitivity | Specificity | F1 | ROC-AUC |
|-------|-----------:|---------:|------------:|------------:|---:|--------:|
| LeNet on Haar wavelets (retinopathy) | 107 | 64.5% | 65.9% | 63.5% | 60.4% | 0.725 |
| Random Forest (heart disease) | 76 | 81.6% | 80.0% | 82.9% | 80.0% | 0.885 |

Confusion matrices: retinopathy TN 40 / FP 23 / FN 15 / TP 29; heart TN 34 / FP 7 / FN 7 / TP 28.
Heart-model 5-fold cross-validated ROC-AUC on the training part: 0.918.

The retinopathy task is hard: images are graded only as present or absent, and early hypertensive changes are
subtle. A small CPU-trained LeNet reaches an AUC of about 0.72, so its output should be read as a screening signal
that supports clinical judgement. A 25-epoch run is kept for comparison in `experiments/retina/metrics_25ep.json`
(AUC 0.715).

## 6. Data sources and licences

| Dataset | Source | Licence | What is committed |
|---------|--------|---------|-------------------|
| Hypertension & Hypertensive Retinopathy Dataset (HRDC), task 2: 712 fundus images, 292 with retinopathy | https://www.kaggle.com/datasets/harshwardhanfartale/hypertension-and-hypertensive-retinopathy-dataset | CC BY-NC 4.0 | 20 labelled sample images from the test split (10 per class) in `data/sample/fundus/` plus `labels.csv`, built by `scripts/make_sample.py`. The full ~1 GB set is downloaded by `scripts/download_data.py` into `data/raw/` (git-ignored). |
| Heart Disease Dataset (1025 rows, 302 unique; UCI Cleveland origin) | https://www.kaggle.com/datasets/johnsmith88/heart-disease-dataset (UCI: https://archive.ics.uci.edu/dataset/45/heart+disease) | Kaggle page: not stated; UCI source: CC BY 4.0 | Full CSV at `data/heart/heart.csv` |

Trained models: `models/lenet_hr.pt` (+ `lenet_hr.json` with the threshold) and `models/heart_rf.joblib`.
Training metrics and splits: `experiments/retina/`, `experiments/heart/`. Everything is seeded (seed 42).

## 7. API

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/login` | Email + password -> JWT |
| GET | `/api/auth/me` | Current user |
| GET / POST | `/api/patients` | List (search `?q=`) / register |
| GET | `/api/patients/{id}` | Patient with screening history |
| POST | `/api/screenings/image` | Multipart `patient_id`, `eye`, `file` -> quality, steps, wavelets, retinopathy, heatmap, vessels |
| POST | `/api/screenings/{id}/clinical` | Clinical JSON -> heart risk, SHAP, combined stage |
| GET | `/api/screenings`, `/api/screenings/{id}` | Recent list / full result |
| GET | `/api/screenings/{id}/report` | PDF report |
| GET | `/api/samples`, `/api/samples/{name}` | Labelled sample images |
| GET | `/api/metrics` | Evaluation results |
| GET | `/api/health` | Status and model availability |

Interactive API docs: http://localhost:8216/docs
