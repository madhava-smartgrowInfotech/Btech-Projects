# UniHealth - Build Plan

**Architecture:** React (5206) -> FastAPI platform (8206) -> 3 hospital FHIR R4 servers (12061 Northbridge General, 12062 Riverside Medical Center, 12063 Lakeview Clinic), each a FastAPI app with its own SQLite file and its own patient IDs. Platform holds users, MPI, consents, hash-chained audit ledger, synced summaries, reminders. The platform calls hospitals over FHIR REST with a short-lived service JWT (SMART-style scope `system/*.read`).

**Data:** Synthea FHIR R4 sample (`synthea_sample_data_fhir_latest.zip`, ~30 MB) -> seeded script picks ~60 patients, splits across hospitals with ~20 overlapping (renamed IDs, small name/phone typos so linkage is really fuzzy). UCI Heart Disease (Cleveland, 303 rows) and Pima Indians Diabetes (768 rows) CSVs committed under `data/`.

**Endpoints (platform `/api`):**
- `POST /auth/login`, `GET /auth/me` (roles: patient, doctor, admin, staff)
- `GET /mpi/search?q=` , `POST /mpi/rebuild`, `GET /mpi/{person_id}` (links + confidence)
- `GET/POST /consents`, `POST /consents/{id}/revoke` (FHIR Consent JSON stored; ledger entry)
- `POST /access/request` (doctor) -> consent check -> FHIR fetch/merge; `GET /records/{person_id}` timeline
- `GET /records/{person_id}/bundle` (FHIR Bundle download)
- `POST /sync` (hospital pushes a FHIR summary Bundle), `GET /sync`
- `GET /risk/{person_id}` (heart + diabetes RF, top factors)
- `POST /assistant/explain`, `POST /assistant/summary`, `POST /assistant/ask` (Gemini, language param)
- `GET/POST /reminders`, `GET /audit`, `GET /audit/verify`
- Hospital FHIR: `/fhir/metadata`, `/fhir/Patient`, `/fhir/{Type}?patient=`, `/fhir/Bundle` (POST)

**Tables:** users, persons, mpi_links, consents, ledger (prev_hash, hash), synced_summaries, reminders. Hospitals: resources(id, type, patient_id, json).

**Screens:** Landing, Login, Patient (timeline, consents, assistant, reminders), Doctor (search, access request, merged record, risk panel), Hospital console (patients, push summary), Audit & consent log (verify chain).

**ML:** scikit-learn RandomForest (200 trees) for heart and diabetes; metrics in `experiments/`; eval script measures model AUC/accuracy, MPI linkage precision/recall/F1 vs seeded ground truth, consent enforcement and ledger tamper detection.
