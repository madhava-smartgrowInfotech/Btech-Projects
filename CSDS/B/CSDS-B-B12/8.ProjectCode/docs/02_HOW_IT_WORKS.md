# PulmoVision - How it works

## Architecture

```
React + Vite (5212)  --/api proxy-->  FastAPI (8212)
                                         |-- SQLite (users, patients, scans, chat, audit)   data/app.db
                                         |-- Encrypted file store (Fernet)                  data/store/*.enc
                                         |-- PyTorch pipeline on CPU                        models/*.pt
                                         '-- Gemini REST API (assistant + report text, model fallback)
```

| Part | Files |
|---|---|
| API | `backend/app/main.py`, `routes/auth_routes.py`, `routes/patients.py`, `routes/scans.py`, `routes/metrics.py` |
| Security | `backend/app/auth.py` (bcrypt, JWT, roles, Fernet), `services/storage.py` (encrypted files), `db.py` (audit log) |
| Imaging pipeline | `services/imaging.py` (load / preprocess / overlays), `services/nets.py`, `services/pipeline.py` |
| AI text | `services/gemini.py`, `services/report.py` (ReportLab + Noto fonts + HarfBuzz shaping) |
| Training / evaluation | `ml/prepare_data.py`, `ml/train.py`, `ml/eval.py`, `notebooks/pulmovision_kaggle.ipynb` |

## The analysis pipeline (one upload)

1. **Load** - PNG / JPG via Pillow, DICOM via pydicom (VOI LUT / rescale, MONOCHROME1 inverted, middle frame of multi-frame files).
2. **Modality check** - (a) colour photographs are rejected by mean HSV saturation (> 0.12); (b) the image is embedded with an ImageNet EfficientNet-B0 and compared (cosine, mean of the top-5) with a reference bank of X-ray and CT training embeddings. The closer modality is chosen (a DICOM `Modality` tag of CT / CR / DX overrides it); if the best similarity is below the calibrated threshold the image is rejected as "not a chest X-ray or CT".
3. **Preprocessing** - resize to 224x224 (area interpolation) -> non-local-means denoising (h=5) -> CLAHE (clip 2.0, 8x8 tiles) -> scale 0-1 and ImageNet mean/std normalisation. Every intermediate image is stored and shown.
4. **Lung segmentation** - X-ray: U-Net (MobileNetV2 encoder, 1-channel 256x256 CLAHE input) trained on the expert lung masks of the COVID-19 Radiography Database; the two largest components are kept. CT: dark regions enclosed by the Otsu body outline (the U-Net is X-ray-only).
5. **Classification** - EfficientNet-B0 (ImageNet weights, fine-tuned). X-ray model: COVID-19, viral pneumonia, lung opacity, tuberculosis, normal. CT model: adenocarcinoma, large-cell carcinoma, squamous-cell carcinoma, normal. Logits are divided by a temperature fitted on the validation split (calibrated confidence).
6. **Grad-CAM** - on the last convolution (`conv_head`) for the predicted class, overlaid as a heatmap.
7. **Severity** - affected % = share of lung-mask pixels where the normalised Grad-CAM is >= 0.5. Normal -> None; otherwise < 15 % Mild, 15-35 % Moderate, >= 35 % Severe. This is a heuristic extent estimate from the explanation map, not a validated clinical severity score.
8. **Storage** - the upload and all derived images are Fernet-encrypted in `data/store/`; the scan row keeps the results and file keys.

## AI assistant and reports

- The assistant (doctors only) sends Gemini the scan findings (class probabilities, severity, patient age/sex - never the name) plus the chat history, with a system prompt that forbids definitive diagnoses. It can answer in English, Hindi or Telugu.
- Reports: Gemini writes a patient-friendly summary, explanation and next steps as JSON in the chosen language (cached per scan and language). ReportLab builds the PDF with Noto Sans / Devanagari / Telugu and HarfBuzz shaping for correct conjuncts; headings and class names are translated in code. If Gemini is unavailable the PDF is still produced with the model results and says the AI section is missing.
- `GEMINI_MODEL` is tried first, then each of `GEMINI_FALLBACK_MODELS` (e.g. when the free-tier daily quota is exhausted).

## Security

- bcrypt password hashes, 12-hour JWT bearer tokens.
- Roles: **technician** registers patients, uploads and views scans; **doctor** can also use the assistant, download reports and view the audit log.
- Encryption at rest (Fernet / AES-128-CBC + HMAC): patient name and phone columns, every uploaded and derived image.
- Audit log of sign-ins (including failures), patient creation / views, uploads (including rejected ones), scan views, assistant questions and report downloads.

## Database tables

`users`, `patients` (encrypted name/phone, age, sex), `scans` (modality, prediction, probabilities, severity, details, cached report text), `chat_messages`, `audit_log`.

## API

| Method | Path | Role |
|---|---|---|
| POST | `/api/auth/login`, GET `/api/auth/me` | - / any |
| GET, POST | `/api/patients`, GET `/api/patients/{id}` | any |
| POST | `/api/scans` (multipart `patient_id`, `file`) | any |
| GET | `/api/scans`, `/api/scans/{id}`, `/api/scans/{id}/image/{original,resized,denoised,enhanced,mask,heatmap}` | any |
| GET, POST | `/api/scans/{id}/assistant` | doctor |
| GET | `/api/scans/{id}/report?lang=en,hi,te` (PDF) | doctor |
| GET | `/api/audit` | doctor |
| GET | `/api/metrics`, `/api/metrics/figure/{name}.png` | any |
| GET | `/api/health` | - |

## Data and training

| Source | Licence | What is committed |
|---|---|---|
| COVID-19 Radiography Database (Kaggle, 778 MB, with lung masks) | Kaggle terms / cite authors | 30 sample X-rays + 6 image/mask pairs in `data/sample/`; full set via `scripts/download_data.py` |
| Tuberculosis (TB) Chest X-ray Database (Kaggle, 662 MB) | Kaggle terms / cite authors | Sample in `data/sample/xray/Tuberculosis`, `Normal`; full set via the script |
| Chest CT-Scan Images (Kaggle, 122 MB) | Kaggle terms | Whole dataset in `data/chest_ct/` |
| scikit-learn sample photos | BSD-3 | 2 non-chest test images in `data/sample/other/` |

Full credits: [04_DATASET.md](04_DATASET.md).

**Splits** (`ml/prepare_data.py`, seed 42, saved in `experiments/splits.json`):

- X-ray: per class 500 train / 100 val / 200 test (TB 400 / 100 / 200); "Normal" is drawn half from each database so the model cannot use the image source as a shortcut.
- Segmentation: 300 / 50 / 100 image-mask pairs per class, disjoint from the X-ray classification images.
- CT: the published train / valid / test split, with byte-identical duplicates removed within and across splits (153 files dropped).

**Training** (`ml/train.py`, CPU): EfficientNet-B0 with the stem and first two blocks frozen, AdamW + one-cycle LR, label smoothing 0.1, class-balanced loss, light rotation / scale / shift / brightness augmentation; best epoch chosen by validation macro-F1, then temperature scaling. U-Net: BCE + Dice loss. The same code runs on a Kaggle GPU through `notebooks/pulmovision_kaggle.ipynb` (generated by `scripts/make_notebook.py`) with larger configs.

**Evaluation** (`ml/eval.py`) writes `experiments/eval/metrics.json` and the confusion-matrix plots shown on the Model performance page.
