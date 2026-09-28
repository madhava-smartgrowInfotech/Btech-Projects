# HospiSense - How it works

```
 Admission form ──► LOS model (XGBoost + SHAP) ──► predicted stay ─┐
                                                                   ▼
 Patient history ─► in-house patients + remaining-stay survival ──► census forecast (mean + 90% band)
 Daily admissions ─► admissions model (XGBoost, lag features) ────┘        │
                                                                           ├─► ICU / ward warnings
                                                                           ├─► nurses per shift, equipment
                                                                           ▼
                                             optimiser (OR-Tools SCIP) ──► plan ──► accept / edit ──► DB
```

Stack: FastAPI + SQLAlchemy/SQLite (`backend/`), React + Vite + Tailwind (`frontend/`), XGBoost, SHAP, OR-Tools.

## 1. Data

| Dataset | Source | Licence | Committed | Used for |
|---|---|---|---|---|
| Hospital Length of Stay (Microsoft) | https://www.kaggle.com/datasets/aayushchou/hospital-length-of-stay-dataset-microsoft | see the Kaggle dataset page | `data/raw/los/LengthOfStay.csv` (12 MB, full) | 100k stays with admission/discharge dates, facility, 11 conditions, labs and vitals: LOS models, census history, admissions history |
| AV: Healthcare Analytics II | https://www.kaggle.com/datasets/nehaprabhavalkar/av-healthcare-analytics-ii | see the Kaggle dataset page | `data/raw/av/train_data.csv` + dictionary (27 MB, full labelled file) | share of patients aged 0-20 -> Paediatric ward share (7.2%) |
| Hospital Beds Management | https://www.kaggle.com/datasets/jaderz/hospital-beds-management | CC0 | `data/raw/beds/services_weekly.csv` | ICU (11.1%) and surgical (28.8%) share of admissions |

`scripts/download_data.py` re-downloads all three with `kagglehub`. From Beds Management only `services_weekly.csv` is used and
committed; the per-person files (patients, staff, schedules) are not needed and are left out. The unlabelled AV test file is
not used.

**Preparation (`ml/prepare_data.py`, seed 42).**
- Dates become day indices (day 0 = first admission). The operating day ("today") is day 365, the last admission day, and the
  app shows every date shifted by a fixed multiple of 7 days so that it falls on **2026-09-28** (weekdays are preserved).
- The source has no ward, so each stay gets one: ICU goes to the most severe 11.1% within each facility (score from
  conditions, secondary diagnoses, abnormal sodium, creatinine, pulse, respiration, urea, readmissions, plus seeded noise).
  The rest are Paediatric (7.2%), Maternity (12% of admissions, female patients only), Surgical (28.8% overall) or General,
  drawn at random with the seed. ICU stays average 6.3 days against about 3.7 elsewhere.
- Output: `data/processed/patients.csv.gz` and `models/hospital_config.json` (ward mix, capacity, roster, stock, equipment
  usage rates).

## 2. Length of stay (F1) - `ml/train.py`

- Features: readmissions, sex, 11 conditions, hematocrit, neutrophils, sodium, glucose, urea, creatinine, BMI, pulse,
  respiration, secondary diagnoses, facility (28 in total).
- **Temporal split:** admissions from January to September train (74,481); October to December are held out (25,256).
- XGBoost regressor (days) and classifier (stay > 5 days), 400 trees, depth 6, CPU, about 5 seconds.
- **SHAP** `TreeExplainer` on the regressor: each reason is the number of days that factor adds to or removes from the
  average stay. The 80% range comes from the held-out residual distribution.

## 3. Admissions and census forecast (F2, F3)

- **Admissions model:** one XGBoost Poisson model for all 25 facility x ward series, direct multi-horizon (1-14 days), with
  lag features: mean of the last 7 and 28 days, the same weekday in the last 4 weeks, yesterday, weekday and horizon.
- **Census on day d:**
  `E[census] = sum over in-house patients of P(still in bed on day d) + sum over future days t of E[admissions_t] x S(d - t)`.
  - In-house patient: the predicted stay plus the empirical residuals gives a stay distribution (rounded to whole days),
    conditioned on the days already spent.
  - Forecast admissions: `S(k)` = share of stays longer than k days for that facility and ward.
  - Variance = Bernoulli variance of in-house patients + Poisson variance of admissions -> 90% band (z = 1.645).
- Patients admitted in HospiSense are added as in-house patients with their predicted stay.
- **Alerts:** *over capacity* when the expected census passes capacity; *early warning* when mean + 1.0 sd passes it
  (about a 1-in-6 chance). The threshold was chosen on the back-tests: it catches 80% of ICU overruns in the next 7 days.

## 4. Staff and equipment (F4)

- Nurses per shift = ceil(expected patients / ratio) for each ward and shift.
- Equipment = sum over wards of expected patients x usage rate per occupied bed. Rates: ventilators = share of ICU patients
  with pneumonia plus the share with respiration < 4 (0.097); dialysis machines = share with end-stage renal disease (from the data); cardiac
  monitors (ICU 1.0, Surgical 0.3, others 0.1) and infusion pumps (ICU 2.0, Surgical 0.8, General/Paediatric 0.5,
  Maternity 0.4) are default structure values.

## 5. Allocation optimiser (F5) - `backend/app/services/optimizer.py`

Plans for the peak of each facility x ward over the horizon (expected, or the 90% upper band). Three small mixed-integer
programmes are solved with OR-Tools (SCIP) in sequence, each minimising shortfall first and action cost second:

1. **Beds:** convert beds between compatible wards in a facility (General <-> Surgical / Maternity / Paediatric;
   Surgical -> ICU, at most +25% of ICU beds), then divert admissions to another facility's same ward.
2. **Nurses:** per facility and shift, float nurses from over-rostered wards (never non-ICU staff into ICU), then add extra
   shifts.
3. **Equipment:** transfer units between facilities.

Costs: a patient without a bed 1000 > a nurse shift short 400 > an equipment unit short 300 > a diversion 150 > an extra
shift 12 > a transfer 5 > a bed conversion 4 > a float 3. Each action gets a plain-language reason, and the plan gets a
before/after shortfall and a trade-off summary. Accepting a plan (optionally with edited quantities) writes the new bed
capacity, rosters and stock to the database. Solve time is about 0.15 s.

## 6. Evaluation (F7) - `ml/eval.py` -> `experiments/eval/metrics.json`

All numbers are on held-out data (October to December), which training never saw.

| Measure | Result |
|---|---|
| LOS MAE / RMSE / R2 | 0.31 d / 0.42 d / 0.968 (predicting the average: MAE 1.91 d) |
| Within 1 day | 97.4% |
| Long stay accuracy / F1 / AUC | 96.6% / 0.934 / 0.996 |
| Admissions MAE (per series per day) | 2.36 vs 2.48 (7-day mean) and 3.24 (yesterday) |
| Census MAE, 20 forecast dates x 25 wards x 14 days | 4.48 beds vs 5.91 persistence (-24.1%) and 5.01 28-day mean (-10.5%) |
| Census MAE by horizon, day 1 / 3 / 7 / 14 | 2.59 / 3.88 / 4.84 / 4.92 (persistence 3.27 / 5.14 / 6.37 / 6.62) |
| 90% band coverage | 89.2% |
| ICU early warning (next 7 days) | recall 80%, precision 27% (12 caught, 3 missed, 33 false alarms) |

**Resource use.** For each of the 20 back-test dates the optimiser planned from the forecast, and both plans were scored on
the census that actually happened over the next 7 days:

| | Static allocation | HospiSense plan | Change |
|---|---|---|---|
| Patient-days without a bed | 1,083 | 919 | -15.1% |
| Nurse shifts short of safe ratio | 4,610 | 2,446 | -46.9% |
| Equipment unit-days short | 239 | 165 | -31.0% |
| Nurse shifts rostered | 110,740 | 116,655 | +5.3% |
| Nurse shifts above need | 6,814 | 10,568 | +55.1% |

The plan covers the 7-day peak, so shortages fall at the cost of more rostered shifts on quieter days.

## 7. Database (`data/app.db`, created on first run)

`users`, `admissions`, `ward_capacity`, `nurse_roster`, `equipment_inventory`, `allocation_plans`. Delete the file to go back
to the default structure.

## 8. API

| Method | Path | Role |
|---|---|---|
| POST | `/api/auth/login`, GET `/api/auth/me` | any |
| GET | `/api/meta`, `/api/dashboard`, `/api/metrics` | any |
| GET | `/api/admissions/sample?profile=long\|short\|any&ward=` | any |
| POST | `/api/admissions/predict`, `/api/admissions`; GET `/api/admissions` | any |
| GET | `/api/forecast?facility=&days=`, `/api/forecast/icu`, `/api/forecast/resources?facility=&days=` | any |
| POST | `/api/allocation/run`, `/api/allocation/plans/{id}/accept` | admin |
| GET | `/api/allocation/plans`, `/api/allocation/plans/{id}` | any |

Interactive docs: http://127.0.0.1:8207/docs
