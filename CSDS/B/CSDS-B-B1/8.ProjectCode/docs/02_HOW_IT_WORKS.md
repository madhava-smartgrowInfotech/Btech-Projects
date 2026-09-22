# How CivicPulse works

## Architecture

```
Browser (React + Vite, :5201) --/api proxy--> FastAPI (:8201) --> SQLite  data/app.db
                                                  |--> models/*.joblib  (scikit-learn, XGBoost; LIME / SHAP)
                                                  |--> Gemini API      (extraction, draft replies)
```

| Folder | Contents |
|---|---|
| `backend/app/` | `main.py` (app + startup seeding), `db.py` (tables), `auth.py` (JWT + bcrypt), `routes/`, `services/` |
| `backend/app/services/` | `taxonomy.py` (categories, departments, dataset mappings), `datasets.py`, `training.py`, `predictor.py` (inference + LIME / SHAP), `gemini.py`, `textutil.py` (language detection, urgency cues), `seed.py` (sample data) |
| `frontend/src/` | `pages/` (7 screens), `components/`, `api.js`, `auth.jsx` |
| `ml/` | `train.py` (train everything), `eval.py` (objective evaluation) |
| `scripts/` | `download_data.py`, `smoke_test.py` |
| `models/`, `experiments/` | trained models, `metrics.json`, per-version runs, `eval/metrics.json` |

## What happens when a complaint is filed

1. **Intake** - the citizen submits text, an optional photo (JPG / PNG / WebP up to 8 MB) and a map pin.
   The ward is the nearest ward centre to the pin. The language is detected from the script and common
   Hinglish words.
2. **Category and department** - one TF-IDF vectoriser (word 1-2 grams + character 2-4 grams, so Hindi
   words keep their vowel signs and Hinglish spelling variants still match) feeds two Logistic Regression
   models: category (15 classes) and department (8 classes).
3. **Priority** - an XGBoost classifier on named, explainable features:
   - text-urgency probabilities from a Logistic Regression on the same TF-IDF features (trained out-of-fold
     so XGBoost sees honest scores),
   - counts of multilingual urgency cues in 8 groups (hazard / accident, health risk, urgent language,
     vulnerable people, service outage, long pending, wide area, repeated complaint),
   - the category and the length of the complaint.
4. **Resolution time** - an XGBoost regressor with an absolute-error objective (it predicts the typical,
   median time) on category, priority, weekday and hour filed. The SLA-breach flag is raised when the
   expected days exceed the department's SLA.
5. **Explanations** - LIME perturbs the text (400 samples) and reports the 8 words that most moved the
   category probability. SHAP (TreeExplainer) splits the priority and time predictions into per-factor
   contributions; the 15 category indicators are summed into one "Category" factor. Time contributions are in
   days.
6. **Gemini extraction** runs in the background after the tracking ID is issued, so a slow or unavailable
   API never blocks intake. The response is constrained to a JSON schema and validated with Pydantic
   (`place`, `issue`, `affected_people`, `hazards`, `duration`, `summary_en`). If it fails, the complaint
   shows the error and the officer can re-run it.

Median intake latency (prediction + all explanations) is ~80 ms on a laptop CPU.

## Officer decisions and retraining

- The officer confirms or changes category, department and priority. A change without a reason is rejected.
  Each field is stored in the `feedback` table with the AI value, the officer value, `accept` / `override`
  and the reason.
- If the category or priority changes, the expected days are re-estimated for the officer's values.
- **Retrain** (`POST /api/model/retrain`) takes the latest officer value per complaint and field as labels,
  weights each one like 10 dataset rows, and refits the category / department models (warm-started from the
  current weights) and the priority model. The vocabulary and the resolution-time model stay fixed. The
  new models are evaluated on the same held-out test set, saved as a new version
  (`experiments/runs/vNNN.json`) and hot-swapped into the running API. The response shows before / after
  accuracy and how often the model now agrees with officer labels. It takes 10-70 s depending on the machine
  and whether the feature cache (`data/cache/`, rebuilt automatically) exists.

## Analytics

All analytics are computed live from the database on each request; the page polls every 20 seconds.
Hotspots group complaints by ward over 7 / 30 / 90 days; a *recurring issue* is one category reported
3 or more times in one ward in that window. SLA compliance is the share of resolved complaints closed within
the department's SLA. Trends are counts per rolling 7-day window over 12 weeks.

## Data

| Source | Licence | What it is | Used for | Committed |
|---|---|---|---|---|
| [CivicComp-HiEn](https://www.kaggle.com/datasets/shyamtripathi373/civiccomp-hien-hindienglish-civic-complaints) | CC BY-SA 4.0 | 16,000 real Bengaluru civic complaints, each in English, Hindi and Hinglish, with categories and severity | category, department, priority; sample texts | `data/raw/civiccomp_hien.csv.gz` (annotated CSV, 5 MB). The dataset's 1.1 GB of model weights are not needed and not downloaded. |
| [Citizen Grievance Dataset](https://www.kaggle.com/datasets/abhisheksingh016/citizen-grievance-dataset) | CC0 | 3,100 + 614 template-holdout Hindi / Hinglish / English grievances by department | category, department (adds revenue, pension, ration, corruption); sample texts | `data/raw/citizen_grievance*.csv` (full) |
| [Indian Citizen Complaint](https://www.kaggle.com/datasets/shebinsam2004/indian-citizen-complaint) | MIT | 2,000 English complaint write-ups | category, department (first 700 characters of each) | `data/raw/indian_citizen_complaint.csv.gz` (full) |
| [NYC 311 Service Requests](https://data.cityofnewyork.us/resource/erm2-nwe9.json) | NYC Open Data | ~304k closed requests (Mar 2025 - Feb 2026), sampled up to 700 per complaint type per month | resolution-time model | `data/raw/nyc311_resolution.csv.gz` (4 MB) |
| Workflow data | generated | wards, departments, SLAs, accounts, 700 sample complaint histories | demo database | generated by `backend/app/services/seed.py` (seed 42) on first start |

`python scripts/download_data.py` re-downloads everything (Kaggle through `kagglehub`; public datasets need
no token).

**Label mapping.** Every source category maps to one of 15 CivicPulse categories, and each category to one
of 8 departments (`taxonomy.py`). Education complaints (no matching department), CivicComp's mixed "Others"
and the essay-style "Economics" rows are dropped. Priority comes from CivicComp severity: LOW -> Low,
MEDIUM -> Medium, HIGH -> High, and HIGH with severity score >= 11 (2.4% of rows) -> Critical.

**NYC 311 mapping.** Each category maps to the closest 311 complaint types (for example Roads & Footpaths ->
Street / Sidewalk / Curb / Highway Condition; Streetlights -> Street Light Condition). The three Revenue
categories have no 311 equivalent, so casework-style types are used as proxies: Consumer Complaint for Land &
Certificates and Welfare & Pensions, Investigations and Discipline for Corruption & Bribery.

**Splits.** CivicComp is split 80/20 by complaint ID, so the three translations of one complaint never
straddle train and test. The grievance and write-up sets are split 80/20 at random (seed 42); the grievance
template holdout is kept as a separate harder test. NYC 311 is split by time: requests filed from January
2026 onward are the test set.

**Sample data.** On first start the backend creates 8 departments, 24 Bengaluru wards, demo accounts, one
sample desk account per department, 40 sample citizens and 700 sample complaints over the last 90 days. The
texts come from the held-out test splits (the models never trained on them). Each category recurs in 3
wards more often, which gives the hotspot map structure. Historical decisions use the dataset's reference
labels, and resolution times are drawn from the real NYC 311 distribution of the same category. The 12 most
recent are left awaiting review. Every generated row is flagged `is_sample` and shown with a "Sample" badge.

## Database

`users`, `departments` (SLA days), `wards`, `complaints` (text, language, photo, location, status, the AI
suggestion with its explanations as JSON, Gemini extraction, the officer's final values), `events` (status
timeline, replies, internal decision notes), `feedback` (officer accept / override per field), `model_runs`
(metrics of each retrain).

## API

| Method | Path | Who |
|---|---|---|
| POST | `/api/auth/login`, `/api/auth/register` | anyone |
| GET | `/api/auth/me`, `/api/meta`, `/api/health` | any / public |
| POST | `/api/complaints` (multipart: text, lat, lng, photo) | citizen |
| GET | `/api/complaints/mine`, `/api/complaints/track/{tracking_id}` | citizen (own) / staff |
| GET | `/api/officer/queue?status=&department=&priority=&q=` | officer, admin |
| GET | `/api/complaints/{id}` | officer, admin |
| POST | `/api/complaints/{id}/decision`, `/status`, `/extract`, `/draft-reply`, `/reply` | officer, admin |
| GET / POST | `/api/model/metrics`, `/api/model/retrain` | officer, admin |
| GET | `/api/analytics/summary`, `/hotspots`, `/sla`, `/trends` | officer, admin |
| PUT | `/api/departments/{id}` (SLA days) | admin |

Interactive docs: http://localhost:8201/docs while the backend runs.

## Evaluation

`python ml/eval.py` writes `experiments/eval/metrics.json`. Results for model v1 on held-out data:

| Objective | Measure | Result |
|---|---|---|
| Classify complaints | category accuracy / macro-F1 (9,459 test complaints) | **82.9% / 0.786** (majority-class baseline 35.9%) |
| | by language: English / Hindi / Hinglish | 82.7% / 82.8% / 83.3% |
| | harder template holdout (566) | 73.1% |
| Recommend department | top-1 / top-3 accuracy | **84.9% / 98.0%** |
| Predict priority | accuracy / macro-F1 (8,533) | **79.7% / 0.681**; within one level 99.0%; Critical recall 75.7% |
| | text-only model it builds on | 78.0% |
| Estimate resolution time | typical (median) error, 48,218 held-out NYC requests | **1.10 days** vs 1.24 for a per-category median |
| | mean error | 8.89 vs 8.95 days (long-tail requests dominate the mean) |
| | SLA-breach flag correct | 76.8% (per-category median: 78.8%) |
| Explain recommendations | confidence drop when the top-3 LIME words are removed vs 3 random words | **0.51 vs 0.02**; the prediction flips 60% vs 2% of the time |
| | SHAP additivity (contributions + base = model output) | max error 5e-6 |
| Officers in control | 100 simulated officer corrections of wrong departments, then retrain | agreement on corrected cases 0% -> **99%**; rest of the test set 85.8% -> 85.8% (no regression) |
| Real-time support | intake latency with all explanations | median **82 ms**, p95 230 ms |

## Known limitations

- Resolution times are learned from New York service requests. They give realistic per-category patterns,
  not Bengaluru-specific times. Replace `data/raw/nyc311_resolution.csv.gz` with the office's own closed
  complaints to localise them.
- CivicComp severity labels were produced from keywords, so the priority model partly learns keyword
  patterns. Officer overrides are the path to better labels.
- In simulation, retraining fixed the exact complaints officers corrected but carried over to only 6% of
  similar unseen errors. Many consistent overrides are needed before routing behaviour shifts broadly.
- The SLA-breach flag is slightly less accurate than a per-category median rule, because the model predicts
  the typical time and breaches come from the long tail.
