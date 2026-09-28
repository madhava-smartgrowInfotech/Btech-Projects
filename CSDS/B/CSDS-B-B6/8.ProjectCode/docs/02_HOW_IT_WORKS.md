# UniHealth - How it works

## Architecture
```
Browser (React, :5206) --/api--> UniHealth platform API (FastAPI, :8206, data/app.db)
                                   |  service JWT, SMART-style scopes (system/*.read, system/*.write)
                                   +--> Northbridge General Hospital  FHIR R4  :12061  data/hospital_a.db
                                   +--> Riverside Medical Center      FHIR R4  :12062  data/hospital_b.db
                                   +--> Lakeview Clinic               FHIR R4  :12063  data/hospital_c.db
Hospital --POST /api/sync (FHIR summary Bundle, system/Bundle.write)--> platform
Platform --> Gemini API (assistant)       Platform --> models/*.joblib (risk)
```
The platform never copies a hospital's database. It asks each hospital over FHIR REST at the time of access, and
keeps only what hospitals choose to push (post-treatment summaries).

## 1. Hospitals (F1)
`hospitals/hospital_app.py` is one FastAPI app started three times with `HOSPITAL_KEY=A|B|C`. Each has its own SQLite
file and its own ID scheme (`NBG-`, `RMC-`, `LVC-`). Endpoints: `GET /fhir/metadata` (CapabilityStatement),
`GET /fhir/Patient?name=&birthdate=`, `GET /fhir/{Type}?patient=`, `GET /fhir/{Type}/{id}`, `POST /fhir`
(transaction Bundle) and `POST /fhir/Patient/{id}/$sync-summary`. Every call except metadata needs a bearer JWT whose
audience is that hospital and whose scope covers the action; every written resource is validated with `fhir.resources`.

`scripts/seed_hospitals.py` (seed 42) takes 60 living Synthea patients: 8 are treated at all three hospitals, 16 at
two, 36 at one. A person's last 30 encounters are split chronologically between their hospitals, and each linked
resource (conditions, medications, lab/vital observations, lab reports, allergies) goes with its encounter. At the
second and third hospital the demographics are re-typed with realistic errors - family/first-name typos, a dropped
middle name, a different phone format or missing phone, and occasionally a day/month swap in the birth date. The
ground truth is saved to `data/sample/mpi_truth.json`.

## 2. Master Patient Index (F2)
The platform pulls every hospital's Patient list (PDQ-style query) and scores pairs from different hospitals within
the same birth year:

`score = 0.40 x name + 0.30 x birth date + 0.10 x gender + 0.20 x phone`

- name = 0.6 x similarity(family) + 0.4 x similarity(first given) (rapidfuzz ratio)
- birth date = 1 exact, 0.8 day/month transposed, 0.4 same year and month-or-day
- phone = 1 same digits, 0.5 missing on either side, partial otherwise

Pairs at or above **0.80** are merged strongest first with union-find. A person never gets two records from the same
hospital. Each link keeps its confidence (best pairwise score). Person IDs (`UH-...`) come from the anchor record, so
they stay stable when linkage is re-run.

## 3. Consent and the ledger (F3)
A patient grants one hospital access to chosen categories (encounters, conditions, medications, labs, allergies), with
an optional expiry. It is stored as a FHIR R4 `Consent` (scope patient-privacy, provision permit, actor = the
hospital, class = allowed resource types) and validated. Granting again replaces the active consent. Revoking sets
the status to `inactive`.

Every consent change, record access (allowed or denied), export, risk assessment, assistant use, sync and login is
appended to the ledger. Each entry stores `SHA-256(ts, actor, action, person, detail, prev_hash)`, so changing,
deleting or reordering any entry breaks the chain. `GET /api/audit/verify` recomputes it.

## 4. Secure retrieval and the unified record (F4, F6)
Doctor request -> `POST /api/access/request` -> consent check for the doctor's hospital. With no consent the platform
returns 403, logs `access.denied` and queues the request on the patient's consent screen. With consent it looks up the
person's links in the MPI and runs FHIR searches **in parallel** (hospital x resource type), limited to the consented
categories. It merges results with synced-summary copies, de-duplicates by resource id and sorts into one timeline.
If a hospital is offline, the last pushed summary is shown and the source is flagged. `GET /api/records/{id}/bundle`
returns the same data as a validated FHIR `Bundle` (collection).

## 5. Post-treatment sync (F5)
Records staff record a visit in the hospital console. The platform sends a transaction Bundle (Encounter, Condition,
MedicationRequest, CarePlan for the follow-up) to that hospital, which stores it. The hospital then builds a summary
Bundle: patient, last three encounters, active problems, active medications, latest 12 observations and active care
plans. It signs it with its own token and POSTs it to `/api/sync`. The platform validates it, maps the local patient
to a person via the MPI, keeps the copy and creates reminders. The original stays at the hospital.

## 6. Risk prediction (F7)
`ml/train.py` trains two `RandomForestClassifier(300 trees, depth 6)` models on CPU in seconds. They use only
features that can be read from a FHIR record:

| Model | Dataset | Features (LOINC source) |
|---|---|---|
| Heart disease | UCI Cleveland (303 rows) | age, sex, systolic BP (8480-6), total cholesterol (2093-3), glucose > 120 (2339-0) |
| Diabetes | Pima Indians (768 rows) | pregnancies (condition count), glucose (2339-0), diastolic BP (8462-4), BMI (39156-5), age |

At scoring time the latest value of each code is read from the merged record. A missing value is replaced by the
training median and labelled as such. **Top factors** come from occlusion: each value is replaced by the median and
the model re-scored, so the change in probability shows how much that value raises or lowers this patient's risk.

## 7. Assistant and reminders (F8)
`services/assistant.py` sends Gemini (`GEMINI_MODEL`, default `gemini-flash-latest`) a compact, structured extract of
the record and asks for an answer in the chosen language (English, Telugu, Hindi, and others). There are three actions:
- Explain a lab report. It uses the report's result values, or the latest lipid panel.
- Summarise treatment across hospitals.
- Answer a question, including general medication guidance.

A system instruction forbids diagnoses and prescription changes. If the main model is rate-limited or overloaded, the
models in `GEMINI_FALLBACK_MODEL` are tried in order, with a 45 s limit on each. If the key is missing or every model is busy, the
API returns a clear error; nothing is faked. Reminders are created from active MedicationRequests (daily medication) and active
CarePlans (follow-up dates) when the patient opens their record or a hospital syncs a summary. Patients can add
their own reminders and tick them off.

## Data sources and licences
| Data | Source | Licence | Committed |
|---|---|---|---|
| Synthea sample patients, FHIR R4 (`synthea_sample_data_fhir_latest.zip`, 29.6 MB, ~108 patients) | https://synthea.mitre.org/downloads | Apache-2.0 (synthetic, no real patients) | Yes - `data/synthea/` (whole zip). Hospital databases are generated from it by the seeded script (git-ignored) |
| Heart Disease (UCI, Cleveland processed file, 303 rows) | https://archive.ics.uci.edu/dataset/45/heart+disease (also on Kaggle) | CC BY 4.0 | Yes - `data/heart/heart.csv` (header added, `?` = missing, target = num > 0) |
| Pima Indians Diabetes (768 rows) | https://www.kaggle.com/datasets/kumargh/pimaindiansdiabetescsv | CC0 | Yes - `data/diabetes/diabetes.csv` (header added) |

All datasets are small, so they are committed in full. No `download_data.py` is needed.

## Platform tables
`users`, `persons`, `mpi_links`, `consents`, `access_requests`, `ledger`, `synced_summaries`, `reminders`
(SQLite `data/app.db`, created on first run). Hospital tables: `resources(type, id, patient_id, date, json)`.
