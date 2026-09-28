# How MediQueue works

## Architecture

```
Phone / browser (React + Vite :5215, Tailwind, Leaflet/OSM)
      |  /api (REST)  +  /api/ws (WebSocket)     <- Vite proxy; Cloudflare quick tunnel for HTTPS on a phone
FastAPI (:8215)
  routes/    auth, hospitals (+ triage, recommend), bookings, console, referrals, dashboard
  services/  triage.py      symptom model + weights + red flags, Gemini text mapping
             noshow.py      calibrated no-show probability
             scheduling.py  OP limits, emergency quota, PuLP day allocation
             recommend.py   hospital ranking
             queue.py       ordering, position, wait estimate, WebSocket hub
SQLite (data/app.db, created and seeded on first start)
models/  triage_model.joblib, noshow_model.joblib
```

## Data model

- `hospitals` - OSM id, name, location, specialties, emergency capability, `op_limit`, `emergency_quota`,
  `avg_consult_min`, `op_start`.
- `users` - patient / staff (linked to one hospital) / admin; bcrypt password hashes, JWT sessions.
- `bookings` - hospital, patient, date and requested date, token, kind (op / emergency), severity, priority,
  symptoms, AI condition + specialty, no-show probability, status (waiting / called / done / no_show / referred).
- `referrals` - booking, from / to hospital, specialty, reason, JSON summary, consent + time, status, new booking.

## 1. Severity classification (F3)

1. **Symptom input.** Patients pick from 131 symptoms, or type free text. Free text goes to Gemini
   (`gemini-flash-latest` by default, with backup models if it is busy; JSON mode) with the exact vocabulary; only vocabulary keys are accepted. Without a key or if
   the call fails, a keyword + synonym matcher is used (the UI says which one ran).
2. **Symptom model.** `ml/train_triage.py` trains a multinomial logistic regression on multi-hot symptom vectors
   from the Disease Symptom Prediction dataset (41 conditions). Unique symptom combinations are split 80/20; the
   training rows are augmented with random symptom subsets because patients rarely report every symptom.
3. **Severity** = the highest of
   - the symptom-weight band: sum of `Symptom-severity.csv` weights (1-7) -> <8 mild, 8-14 moderate, 15-23 severe, 24+ critical;
   - the likely condition's baseline acuity (`data/disease_acuity.csv`) when the model is at least 50% confident;
   - red-flag rules: coma, confusion, one-sided weakness, slurred speech, stomach bleeding, acute liver failure ->
     critical; chest pain with breathlessness or sweating -> critical; blood in sputum / stool, breathlessness with
     fast heart rate, high fever with stiff neck -> severe.
4. **Department** comes from the condition -> specialist table in the Doctor's Specialty Recommendation dataset
   (normalised to 14 departments); low confidence falls back to General Medicine.
5. Critical results show emergency advice, only emergency-capable hospitals are suggested, and a same-day booking
   uses the hospital's emergency quota.

## 2. Hospital recommendation (F2, objective 4)

For each hospital: distance score `exp(-km / 8)`, specialty match (1, 0.5 for General Medicine on mild/moderate
cases), availability on the chosen day (`free OP slots / OP limit`) and emergency capability. Weights depend on
severity - mild cases weigh free slots, severe cases weigh the specialty, critical cases weigh distance and
emergency capability. Moderate/severe cases are never sent to a hospital without the department. Top 3 are shown on
the map with the reasons.

## 3. Limits, quotas and no-show-aware allocation (F4, objective 2)

The no-show model (`ml/train_noshow.py`) is gradient-boosted trees with isotonic calibration on the Medical
Appointment No Shows dataset (age, gender, lead days, weekday, SMS reminder, ...). Every booking stores its
calibrated no-show probability `p`.

For a booking request on day `d0`, `services/scheduling.py` builds a small integer programme over the next 7 days:

- binary `x_d`, exactly one day chosen;
- `x_d * (E_d + 1 - p_new) <= op_limit` where `E_d = sum(1 - p)` of bookings already on day d (expected attendance);
- `x_d * (n_d + 1) <= floor(op_limit * 1.15)` - controlled overbooking cap;
- minimise `urgency_weight * days_of_delay + 5 * bookings_over_the_limit` (urgency weight 3 mild ... 100 critical).

So a day with predicted no-shows can take a few extra bookings, urgent patients accept an overbooked slot today,
and mild patients - or anyone when a day is full - move automatically to the next day with room. PuLP's CBC solver
runs per booking (a few ms). Critical same-day bookings first use the emergency quota; walk-in emergencies added at
the desk are always admitted and counted against the quota.

## 4. Live queue and waiting time (F5, objective 5)

- Order: emergencies, then critical, then severe, then moderate/mild; token order within each group.
- Estimated wait for a patient = `sum over patients ahead of (1 - p_noshow) * consult_minutes`.
- `consult_minutes` starts at the hospital's setting and blends in the mean of the last 10 real consultation
  times today (called -> done) once there are at least 3.
- Every change (booking, call next, done, no-show, emergency, referral, settings) sends a `queue_changed` event over
  `WS /api/ws/hospital/{id}`; token pages, consoles and the dashboard (channel 0) refetch immediately.

## 5. Referrals (F7, objective 6)

1. The treating hospital (desk or admin) picks a patient -> department -> suggested receiving hospitals (same
   ranking, from the referring hospital's location) -> reason and clinical notes.
2. A JSON summary is stored (symptoms, AI severity and condition marked as decision support, notes). For patients
   with an app account the status is `pending_consent`, and the receiving hospital sees neither the name nor the
   summary until the patient consents in the app. Walk-in patients' consent is confirmed by the desk.
3. The receiving hospital accepts -> a token is booked there automatically (same allocation rules) and appears in
   the patient's My tokens -> completed. Access is limited to the two hospitals, the patient and the district admin.

## 6. District dashboard (F8)

Per hospital: bookings vs OP limit (load %), waiting count, average and maximum estimated wait, emergencies vs quota,
severity mix; district totals, bookings moved to a later day, referral status counts; a load map (green -> red).

## Data sources and licences

| Data | Source | Licence | Committed |
|---|---|---|---|
| Disease Symptom Prediction (incl. `Symptom-severity.csv`) | kaggle.com/datasets/itachi9604/disease-symptom-description-dataset | CC BY-SA 4.0 | Full dataset, `data/disease_symptom/` |
| Doctor's Specialty Recommendation | kaggle.com/datasets/ebrahimelgazar/doctor-specialist-recommendation-system | CC BY-SA 4.0 | Full dataset, `data/doctor_specialist/` |
| Medical Appointment No Shows | kaggle.com/datasets/joniarroba/noshowappointments | CC BY-NC-SA 4.0 | Full dataset (10 MB), `data/noshow/` |
| Hyderabad hospitals | OpenStreetMap via Overpass (`scripts/fetch_hospitals.py`) | ODbL, (c) OpenStreetMap contributors | `data/hospitals_osm.csv` (973 raw), `data/hospitals_network.csv` (60 selected) |

Generated data, all from committed seeded scripts:

- `data/hospitals_network.csv` - `scripts/build_network.py` (seed 2024) keeps named general / multi-specialty
  hospitals, derives departments from OSM tags and names, and seeds OP limits (40-250), emergency quotas (8-15%)
  and consultation times (3-4.5 min).
- `data/disease_acuity.csv` - baseline acuity per condition used by the severity rules (reference table).
- Sample patients - `backend/app/seed.py` fills today's queues with patients named "Sample patient N" (seeded by
  date, marked "sample data" in the console) so the network shows realistic load.

## Evaluation method (`ml/eval.py`, seed 7)

- **Severity:** held-out symptom combinations with 3 reported symptoms; agreement with the reference acuity table,
  under-triage rate, and critical recall on red-flag cases.
- **Network simulation:** 1,200 patients over 3 days from random Hyderabad locations, OP limits scaled to 4% so
  demand exceeds capacity; each patient takes the first suggestion that can place them. Audits capacity, expected
  attendance and quota constraints; compares load spread with a "nearest hospital with the department" policy.
- **Queue:** 150 queues of 60 real held-out appointments (real no-show outcomes, model probabilities), consultation
  times drawn from a gamma distribution (mean 4 min); compares the estimate with actual waits.
- **Overbooking:** 300 days, OP limit 40, real held-out appointments; fixed booking vs calibrated overbooking.
- **Referrals:** 200 random referring hospitals and departments; receiving hospital department match and distance.
