# PulmoVision - build plan

**Architecture:** React + Vite (5212) -> `/api` proxy -> FastAPI (8212) -> SQLite + encrypted file store (`data/store/*.enc`, Fernet) -> PyTorch pipeline (CPU) + Gemini REST.

**Pipeline:** load PNG/JPG/DICOM -> modality check (grayscale stats + a small modality head: xray / ct / other) -> preprocessing (resize 224, CLAHE, bilateral denoise, normalise; each step saved as an image) -> U-Net lung mask (X-ray) -> EfficientNet-B0 classifier (X-ray: COVID-19, viral pneumonia, lung opacity, tuberculosis, normal; CT: adenocarcinoma, large-cell, squamous-cell, normal) -> Grad-CAM -> severity = share of the lung area with high CAM activation (none / mild / moderate / severe).

**Endpoints:** `POST /api/auth/login`, `GET /api/auth/me`, `GET/POST /api/patients`, `GET /api/patients/{id}`, `POST /api/scans` (upload + full analysis), `GET /api/scans/{id}`, `GET /api/scans/{id}/image/{kind}`, `POST /api/scans/{id}/assistant`, `GET /api/scans/{id}/report?lang=en|hi|te`, `GET /api/audit` (doctor only), `GET /api/metrics`, `GET /api/health`.

**Tables:** users (email, name, role doctor|technician, password hash), patients (name/phone encrypted, age, sex), scans (patient, modality, prediction, probabilities, severity, file ids), chat_messages, audit_log.

**Roles:** technician = register patients and upload scans; doctor = everything plus assistant, reports and the audit log.

**Screens:** Landing, Login, New scan, Result, Report, Patients & history, Model performance.

**Data:** COVID-19 Radiography DB (4 classes + lung masks), TB Chest X-ray DB (TB + normal), Chest CT-Scan Images (4 classes). The pneumonia dataset is dropped (deferred). Sample images committed in `data/sample/`, full sets via `scripts/download_data.py`.

**Training:** no local GPU, so small configs train on CPU (`ml/train_*.py`, balanced subsets, 224 px, a few epochs); `notebooks/pulmovision_kaggle.ipynb` runs the same code with larger subsets on a Kaggle GPU. The Gemini assistant falls back to `gemini-flash-lite-latest` when the main model's quota runs out.
