# ResQAI - Frontend Plan (Kit V2 - Neo Brutal Grid)

Ports: backend **8302** (Flask, `PORT` env), frontend **5302** (Vite, proxies `/api` to 8302).
Existing Flask UI (`templates/`, `static/`) is left untouched; the new React app lives in `frontend/`.

## 1. Backend endpoints (existing, unchanged)

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET  | `/` | - | Flask HTML dashboard (legacy UI) |
| GET  | `/api/health` | - | `{status, models_loaded}` |
| GET  | `/api/simulate?scenario=normal\|brake\|minor\|moderate\|severe\|random` | - | `{acc_x,acc_y,acc_z,acc_magnitude,gyro_x,gyro_y,gyro_z,gyro_magnitude,speed_before,speed_change,jerk,scenario}` |
| POST | `/api/predict` | JSON sensor reading (`acc_*`, `gyro_*`, `speed_before`, `speed_change`, `jerk`; magnitudes optional) | `{timestamp, accident_detected, severity_level 0-3, severity_label, confidence, features_used{...}, model_source}` |
| GET  | `/api/hospitals?lat&lon&k` | query | `{origin{lat,lon}, hospitals[{name,lat,lon,phone,emergency,distance_km}]}` |
| POST | `/api/emergency` | `{lat?, lon?, severity_label, confidence}` | `{status, alert_id, location, nearest_hospitals[], message, national_emergency_number, ambulance_number}` |

No new endpoints are needed. `default_location` (Hyderabad 17.385, 78.4867) is only exposed to the old template, so the
React app uses the same constants and calls `/api/hospitals` without lat/lon to obtain origin.

## 2. Existing features

1. Model status badge (trained ML vs rule-based fallback) - `/api/health`
2. Scenario buttons: Normal / Harsh Brake / Minor / Moderate / Severe - `/api/simulate` -> `/api/predict`
3. Live monitoring toggle (new random reading every 1.5 s)
4. Live sensor chart (acc magnitude + gyro magnitude, last 40 points)
5. Manual override form (acc x/y/z, gyro magnitude, speed before, speed change, jerk) -> `/api/predict`
6. Detection result panel (status, severity, accident probability bar, model source, last update)
7. Event log (last 25 events)
8. 15-second confirmation countdown for Moderate/Severe, with "I'm fine, cancel" and "Send alert now"
9. Emergency dispatch (browser geolocation, else server jitter) -> `/api/emergency`, dispatch message modal
10. Map with accident marker, nearest 3 hospitals, preview of 5 hospitals on load - `/api/hospitals`
11. Nearest hospital card (name, distance, tel link)
12. Emergency contacts (Ambulance 108, National 112, Traffic Police 103)

## 3. Screen map

| Route | Screen | Features covered |
|-------|--------|------------------|
| `/` | Landing page (Neo Brutal Grid hero, pipeline steps, live model status, CTA) | 1 |
| `/monitor` | Live Monitor: scenario buttons, live toggle, sensor chart, detection result, event log | 1,2,3,4,6,7,8 |
| `/manual` | Manual Override: sensor form with validation, result card | 5,6,7,8 |
| `/response` | Emergency Response: map, hospital list/nearest card, dispatch message, contacts | 9,10,11,12 |
| (overlay) | Countdown confirmation modal + dispatched-alert modal, available on every app screen | 8,9 |
| `*` | Not found | - |

Shared state (React context) keeps the event log, last result, and dispatch result across screens.

## 4. Verification checklist (ticked in Step 4)

- [x] 1 Model status badge
- [x] 2 Scenario buttons
- [x] 3 Live monitoring toggle
- [x] 4 Sensor chart
- [x] 5 Manual override
- [x] 6 Detection result panel
- [x] 7 Event log
- [x] 8 Countdown confirmation
- [x] 9 Emergency dispatch + message
- [x] 10 Map + hospitals
- [x] 11 Nearest hospital card
- [x] 12 Emergency contacts

## 5. Result

All 12 features verified in the browser on 2026-10-17 (Playwright, Chrome) at 360, 768 and 1440 px, light and dark,
with a clean console: `scripts/capture_screens.py` walks each screen, `scripts/smoke_test.py` covers the API flow.
Screenshots are in `docs/screenshots/`.

Decisions: no new backend endpoints. Moderate/Severe confirmation: Escape or "I'm fine" cancels, backdrop click does not;
live monitoring pauses while a confirmation is open. The kit copy was adapted (its Layout depended on an auth module
this product has no use for; added `lib/storage.js`, `lib/gsap.js`, `LineTrace` chart, Modal `dismissOnBackdrop`).

### Follow-up: scenario severity mismatch
The simulated "moderate" crash was rated Minor about 20% of the time (and "minor" rated Moderate about 30%). Cause: `/api/simulate`
drew speed, spin and jerk from ranges that differ from `train_models.py`, so the severity model was misled by cues it never saw
for that class. `app.py` `crash()` now uses the training ranges per severity; the models, `/api/predict` and every response
shape are unchanged. Measured over 1000 samples each: minor 99.2% Minor, moderate 99.1% Moderate, severe 99.5% Severe.
`scripts/smoke_test.py` now asserts this. The product has no login, so none was added.
