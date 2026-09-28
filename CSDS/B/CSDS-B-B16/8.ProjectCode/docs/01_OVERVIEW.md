# RetinaGuard - Overview

## The problem

- Hypertensive retinopathy progresses silently until vision is affected.
- Manual fundus screening is slow and needs specialists.
- Eye and heart risks are usually evaluated separately.
- Screening tools rarely give one overall health-risk stage.

## What RetinaGuard does

RetinaGuard screens a retinal fundus photograph for hypertensive retinopathy, scores the patient's clinical profile
for heart-disease risk, and combines both into a single risk stage (Low / Moderate / High / Very high) with
recommendations and a PDF report. Every AI result is explained (Grad-CAM heatmap, vessel map, SHAP factors) and is
presented as decision support for a qualified professional, never as a final diagnosis.

## Who uses it

- Ophthalmologists and optometrists
- Physicians and cardiologists screening hypertensive patients
- Eye clinics and screening camps with fundus cameras

Two roles sign in: **clinician** and **technician**. Both can register patients, run screenings and open reports;
the role is recorded on each screening and printed on the report.

## Features

| # | Feature | What you see |
|---|---------|--------------|
| F1 | Fundus upload and preprocessing | Original -> green channel -> CLAHE -> resized and normalised, plus a sharpness / brightness / exposure quality check |
| F2 | Haar wavelet features | 2-level Haar sub-bands (LL, LH, HL, HH) at both levels |
| F3 | Hypertensive retinopathy detection | LeNet CNN on the 8 wavelet sub-bands -> probability and decision |
| F4 | Explanation | Grad-CAM heatmap over the fundus, Frangi vessel map with vessel density and mean width |
| F5 | Heart-disease risk | 13-field clinical form -> Random Forest probability with the top SHAP factors |
| F6 | Combined risk stage | Low / Moderate / High / Very high with reasons and recommendations |
| F7 | Screening report | One-page PDF with images, findings, SHAP table, stage and recommendations |
| F8 | Evaluation | Accuracy, sensitivity, specificity, F1, ROC-AUC, confusion matrices and ROC curves for both models |

## Screens

1. **Landing** - what the product does.
2. **Login** - clinician or technician.
3. **New screening** - pick or register a patient, upload a fundus image (or a labelled sample), fill the clinical form.
4. **Result** - quality check, preprocessing steps, wavelet sub-bands, retinopathy probability, heatmap, vessel map,
   heart risk with SHAP factors, overall stage and recommendations.
5. **Report** - PDF preview and download.
6. **Patients and history** - search patients, see every screening and its stage.
7. **Model performance** - test-set metrics, confusion matrices and ROC curves.

## Architecture

```
Browser (React + Vite, :5216) --/api--> FastAPI (:8216) --> SQLite (data/app.db)
                                           |
      preprocess -> Haar wavelet -> LeNet (PyTorch CPU) -> Grad-CAM, Frangi
      clinical form -> Random Forest -> SHAP
      staging -> risk stage + recommendations -> ReportLab PDF
```

Tables: `users`, `patients`, `screenings` (images of each screening are stored under `data/uploads/<id>/`).
