# ATHENA overview

**ATHENA** (Autonomous Triage and Healthcare Electronic Neural Assistant) is a decision-support tool for emergency departments. It reads a scanned clinical report together with the patient's vitals, assigns a triage priority from 1 (critical) to 5 (non-urgent), and shows which findings and vitals drove the decision. The clinician accepts or changes the priority, and the reason is stored.

## Who uses it
- Triage nurses and clinicians entering new arrivals
- Duty doctors who want the reasoning behind a priority before they accept it
- Administrators watching queue load and model performance

## The problem
Triage is subjective and varies with the experience of the person on duty. Tools that read only structured fields ignore the scanned report and the clinical narrative, and a prediction with no justification is not accepted into a clinical workflow.

## Features
| | Feature | What it does |
|---|---|---|
| F1 | Report intake | Upload a PDF or image. Symptoms, findings, history and lab values come back with the page each came from. |
| F2 | Vitals entry | Age, heart rate, blood pressure, SpO2, temperature, respiratory rate, arrival mode. |
| F3 | Fused record | Report features and vitals combined into one 36-input representation, shown side by side. |
| F4 | Triage model | Gradient-boosted trees give priority 1 to 5, a risk level and a calibrated confidence. |
| F5 | Why this priority | SHAP lists the factors that drove the priority, strongest first. |
| F6 | Clinician override | Accept or change with a reason. Every decision is stored with the case. |
| F7 | Queue and metrics | Live queue ordered by priority then arrival, and a performance page. |

## Screens
Landing, sign-in, New patient, Result, Triage queue, Model performance.

## Current limits
- The model is trained on a **seeded synthetic dataset**, not real patient records. The accuracy figures describe how well it learns that simulated rule, not clinical performance. See `02_HOW_IT_WORKS.md`.
- Report reading uses PDF text or a local OCR engine plus a clinical term lexicon. It handles negation ("denies chest pain") and lab reference ranges, but it is a rule-based reader and will miss unusual wording. The sample reports are generated, so a 100% score on them says the pipeline works, not that real scans are solved.
- It supports a clinician and never replaces one.
