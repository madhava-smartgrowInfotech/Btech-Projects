# UniHealth - Overview

## The problem
- Patient records are scattered across hospitals, each with its own system and its own patient number.
- A doctor at a new hospital rarely sees the history from the previous one, so tests are repeated and decisions are delayed.
- Patients cannot see - or understand - their complete health information, and have no say in who reads it.

## What UniHealth does
UniHealth is one patient-controlled health record across hospitals. Hospitals keep their own records and exchange
them in the HL7 FHIR R4 standard. A Master Patient Index works out which hospital records belong to the same person.
The patient grants and revokes access per hospital and data category, and every access is written to a tamper-evident
ledger. An assistant turns the record into plain-language explanations, risk estimates and reminders.

## Who uses it
| User | What they do |
|---|---|
| Patient | Sees one timeline from every hospital, controls consent, asks the assistant, gets reminders |
| Doctor | Finds a patient in the MPI, requests their history (blocked until consented), sees the merged record and risk panel |
| Hospital records staff | Records a treatment episode at their hospital and pushes a FHIR summary to the platform |
| Administrator | Monitors the hospital FHIR servers, re-runs record linkage, reviews the full audit ledger |

## Features
| # | Feature | Where |
|---|---|---|
| F1 | Three simulated hospitals - independent FHIR R4 servers, own SQLite databases and patient IDs, overlapping Synthea patients | `hospitals/`, `scripts/seed_hospitals.py` |
| F2 | Master Patient Index - fuzzy matching on name, DOB, gender and phone with a confidence score | `backend/app/services/mpi.py` |
| F3 | Consent management - grant/revoke per hospital and category, stored as FHIR `Consent`, hash-chained ledger | `routes/consents.py`, `services/ledger.py` |
| F4 | Secure retrieval - consent check, then parallel FHIR REST searches merged into one timeline; every access audited | `routes/records.py`, `services/records.py` |
| F5 | Post-treatment sync - hospital pushes a FHIR summary Bundle; the original stays at the hospital | `hospital_app.py` `$sync-summary`, `POST /api/sync` |
| F6 | Unified patient record - encounters, conditions, medications, labs, allergies in one timeline, downloadable as a FHIR Bundle | Patient and Doctor screens |
| F7 | Health-risk prediction - Random Forest models (heart disease, diabetes) reading values from the record, with top factors | `ml/train.py`, `services/risk.py` |
| F8 | AI assistant and reminders - Gemini explains reports and summarises treatment in the patient's language; medication and follow-up reminders | `services/assistant.py`, `services/reminders.py` |

## Screens
Landing - Login - Patient (timeline, consents, assistant, reminders) - Doctor (search, access request, merged record,
risk panel) - Hospital console (servers, patients, record visit and sync, MPI for admins) - Audit and consent log.

## Safety
UniHealth is clinical decision support. Every AI or risk output is shown as an aid for a qualified professional, with a
short disclaimer, and never as a final diagnosis. All patient data in this build is synthetic sample data (Synthea).
