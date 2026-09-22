# SignalScout: overview

**SignalScout finds where mobile service fails, shows it on a live map, points people to better signal nearby and turns persistent dead zones into complaints with evidence. It then checks the fix with new readings.**

---

## The problem

People lose calls and data in the same places every day: a market, a bus stand, the back rooms of a health centre. The places are well known locally, but not to the people who could fix them.

- **Coverage maps are optimistic.** They show predicted signal, not measured service, and they do not show time-of-day congestion.
- **Complaints are vague.** "No network near the market" gives an engineer nothing to act on: no position, operator, time or measurement.
- **Nobody checks the fix.** A complaint is closed when someone says it is fixed, not when service is measured to be fixed.
- **The people affected have no tools.** They cannot tell whether a better spot is 50 m away.

## What SignalScout does

1. **Measures, with any phone or a small sensor.**
   - The *field probe* runs in Chrome on an Android phone, with no app install. It measures round-trip time, loss and download/upload speed every few seconds, with GPS.
   - ESP32 *sensor nodes* watch a community Wi-Fi link around the clock.
   - Readings are stored on the device first and sync when a connection returns.
2. **Classifies every reading** as Strong, Weak or Dead, with a confidence score and the reasons.
3. **Maps coverage live.** Readings roll up into hexagons of about 0.1 km² per operator. They appear on a heat or hexagon map within seconds, filterable by operator, period and time of day.
4. **Suggests better signal.** A Gaussian Process predicts service around the user and points to the nearest spot that is probably strong, with distance and direction. This works offline too, from spots saved on the phone.
5. **Files complaints itself.** A zone that stays weak or dead becomes a complaint with its evidence attached: readings, measurements, times, map and summary. The operator desk is notified by email and Telegram.
6. **Verifies fixes.** When an engineer marks a complaint resolved, new readings from the zone confirm the fix, or reopen the complaint.
7. **Shows the patterns.** Analytics cover the worst areas, the hours when service fails, operator comparisons and how fast complaints are handled.

## Who uses it

| Role | Uses SignalScout to |
|---|---|
| **Field user** (resident, shop owner, community volunteer) | Measure with a phone, see the coverage map, find better signal, report a problem, follow their complaints |
| **Network engineer** (operator or tower company) | Work the complaint queue with evidence, assign and resolve, watch verification, study analytics and model performance |
| **Administrator** | Manage users and roles, tune detection thresholds, set up notifications, manage sample data |

## Features

| # | Feature | Where |
|---|---|---|
| F1 | **Phone field probe**: measures service in the browser, keeps working offline, detects the operator from the connection, saves strong spots for offline use | `/probe` on the phone; **Connect a phone** gives the link as a QR code |
| F2 | **ESP32 sensor node**: Wi-Fi/BLE signal, latency, loss, GPS, flash buffer; a built-in simulator stands in when there is no hardware | **Devices**; `firmware/esp32_node/` |
| F3 | **Zone classification**: Strong / Weak / Dead with confidence (service-quality rules, a trained classifier for radio metrics, Wi-Fi ranges) | badges everywhere; **Model performance** |
| F4 | **Coverage map**: heat and hexagon layers, live points, sensor nodes, complaints, predicted coverage, filters | **Coverage map** |
| F5 | **Better-signal suggestions**: nearest predicted strong spot, with direction and uncertainty, online and offline | probe **Better signal** tab; map panel |
| F6 | **Automatic complaints**: persistent bad zones become complaints with evidence; users can also report directly | **My complaints**, complaint page |
| F7 | **Auto-verification**: new readings confirm a fix or reopen the complaint | complaint page, desk |
| F8 | **Operator desk**: queue, assignment, lifecycle, notes, evidence exports, email and Telegram notifications | **Operator desk** |
| F9 | **Offline-first**: probe queue with background sync, cached dashboard, notification retry queue, node flash buffer | throughout |
| F10 | **Analytics**: trends, worst areas, time of day, operators, complaint funnel | **Dashboard**, **Analytics** |
| - | **Model performance**: training metrics, plots and live field validation for every model | **Model performance** |

## What it runs on

| Part | Technology |
|---|---|
| API | Python 3.11, FastAPI, SQLAlchemy, SQLite |
| Models | PyTorch, scikit-learn (including its Gaussian Process), XGBoost |
| Web app | React, TypeScript, Vite, Tailwind CSS, Leaflet with OpenStreetMap, Recharts |
| Phone probe | The same web app as an installable PWA (IndexedDB queue, service worker, Wake Lock) |
| Phone access | Free Cloudflare quick tunnel (HTTPS, required for GPS in the browser) |
| Sensor node | ESP32 Arduino firmware (optional; simulator included) |
| Notifications | Telegram Bot API, Gmail SMTP |

Everything runs on one Windows PC with `setup.bat` and `run.bat`. It uses its own ports (API 8202, dashboard 5202), so it can run alongside other software. Everything it depends on is free.

## Honest limits

- **A phone browser cannot read radio metrics** such as signal strength in dBm or the serving cell. The probe measures the **service** people actually get (round trip, loss, speed). This is what matters to them, but it also reflects network load, not only coverage. An estimate of the radio condition from speed tests is shown as supporting evidence, with its measured accuracy (about 50% per test, above both baselines), and never overrides the measured class.
- **The phone's screen must stay on** while measuring. The probe keeps it awake with the Wake Lock API.
- **The operator is detected from the phone's internet address.** Readings taken over Wi-Fi are kept separate and do not count towards mobile coverage.
- The zone classifier and the better-signal predictor were trained on public drive-test data from another country. The **Field validation** tab shows how they behave on your own readings.

## Documentation

| Document | Contents |
|---|---|
| [02_ARCHITECTURE.md](02_ARCHITECTURE.md) | Components, data flow and the main sequences |
| [03_HOW_TO_RUN.md](03_HOW_TO_RUN.md) | Installation, starting, the phone, stopping, resetting |
| [04_DATASET.md](04_DATASET.md) | Datasets, licences, cleaning, download guide |
| [05_MODELS_AND_TRAINING.md](05_MODELS_AND_TRAINING.md) | Models, training, results |
| [06_API_REFERENCE.md](06_API_REFERENCE.md) | Every endpoint with examples |
| [07_USER_GUIDE.md](07_USER_GUIDE.md) | Screen-by-screen walkthrough |
| [08_CONFIGURATION.md](08_CONFIGURATION.md) | Every setting and how to obtain keys |
| [09_TESTING.md](09_TESTING.md) | Tests and the demo scenario |
| [10_TROUBLESHOOTING.md](10_TROUBLESHOOTING.md) | Common problems and fixes |
| [11_PROJECT_STRUCTURE.md](11_PROJECT_STRUCTURE.md) | What is where |
