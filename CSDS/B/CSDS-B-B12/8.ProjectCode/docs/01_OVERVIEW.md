# PulmoVision - Overview

PulmoVision is an explainable screening aid for chest X-rays and chest CT scans. It segments the lungs, flags seven pulmonary conditions (plus normal), shows the evidence behind each result, estimates severity and gives clinicians and patients a report in English, Hindi or Telugu.

> Clinical decision support only. Every AI result is an aid for a qualified professional, never a final diagnosis.

## The problem

- Pulmonary diseases need early detection, but radiologists are scarce, especially in rural clinics.
- Most screening models detect a single disease, on a single imaging modality.
- Predictions rarely come with an explanation or a severity estimate.
- Reports are technical and usually only in English.

## Who uses it

| User | What they do |
|---|---|
| Radiologist / physician (role **doctor**) | Reviews results, heatmaps and severity, asks the clinical assistant, downloads reports, reviews the audit log |
| Technician / diagnostic centre staff (role **technician**) | Registers patients, uploads scans, views results |
| Patient | Receives the PDF report in their own language |

## Features

| # | Feature | What it does |
|---|---|---|
| F1 | Upload + modality check | PNG / JPG / DICOM. Rejects colour photos, non-images and non-chest images; routes chest images to the X-ray or CT model |
| F2 | Preprocessing | Resize -> non-local-means denoising -> CLAHE -> normalisation, each step shown in the UI |
| F3 | Lung segmentation | U-Net (MobileNetV2 encoder) lung mask overlaid on X-rays; intensity-based lung field for CT |
| F4 | Classification | EfficientNet-B0 transfer learning. X-ray: COVID-19, viral pneumonia, lung opacity, tuberculosis, normal. CT: adenocarcinoma, large-cell carcinoma, squamous-cell carcinoma, normal |
| F5 | Explanation + severity | Grad-CAM heatmap, temperature-calibrated confidence, severity (none / mild / moderate / severe) from the share of the lung covered by high activation |
| F6 | Assistant + multilingual report | Gemini clinical assistant per scan; PDF report in English, Hindi or Telugu with an AI-written patient-friendly explanation |
| F7 | Secure records | JWT login, doctor / technician roles, Fernet encryption of patient names, phone numbers and every stored image, audit log |
| F8 | Evaluation | Dice / IoU for segmentation; accuracy, macro-F1, per-class sensitivity and confusion matrices for both classifiers; modality-check accuracy |

## Screens

Landing - Login - New scan - Result (mask, heatmap, severity, preprocessing, assistant) - Report preview / download - Patients and history - Model performance - Audit log (doctors).
