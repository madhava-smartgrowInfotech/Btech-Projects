# Testing

| Check | How | Result |
|---|---|---|
| Backend tests | `venv\Scripts\python -m pytest` | **61 passed** |
| Web app type check and production build | `cd frontend && npm run build` | builds without errors |
| ESP32 firmware | compiled for "ESP32 Dev Module" with `arduino-cli` (all warnings on), with and without GPS/BLE/modem | compiles without warnings; 1.35 MB with BLE (Huge APP partition) |
| End-to-end demo scenario | browser automation of phone, engineer and admin (below) | passed, no console errors |
| Accessibility | axe-core on every page, light and dark, 360 px and desktop | no serious or critical issues |
| Responsive layout | every page at 360 px width | no horizontal scrolling |

---

## 1. Backend tests

```
venv\Scripts\python -m pytest            # all tests, about a minute
venv\Scripts\python -m pytest -k complaints    # only tests whose name matches
venv\Scripts\python -m pytest backend/tests/test_ml.py -v
```

The tests run against a temporary SQLite database, with the real trained models. Sample data, the simulator and notifications are switched off (`backend/tests/conftest.py`). They never touch `data/app.db` and never send email or Telegram messages.

| File | Tests | What they prove |
|---|---|---|
| `test_auth.py` | 11 | health; demo accounts and roles; wrong password rejected; register → sign in → profile; password and email validation; protected routes need a token; admin routes need the admin role; an admin cannot demote themselves; demo passwords cannot be changed; connection info; unknown API paths return a JSON 404 |
| `test_ingest.py` | 9 | a phone batch is classified and a re-sent batch is skipped (idempotent); out-of-range readings are rejected, not stored; missing or wrong device key; an ESP32 node uses its fixed position and uploads its offline buffer; radio readings use the trained model; field users see only their own readings; CSV export; key rotation; probe endpoints and carrier detection; forwarded addresses trusted only from this PC |
| `test_ml.py` | 21 | worst metric wins; explanations and no-service handling; invalid values ignored; vectorised labels match scalar ones; network-type families; feature columns and the 30 s window; device profiles blank the right metrics; probe service bands; Wi-Fi ranges; suggestions point towards better signal; "already strong" and "no data" cases; predicted surface probabilities; trained models load and classify; probe readings get a measured class plus a radio estimate |
| `test_coverage.py` | 4 | hexagons and heat per operator; the hour filter uses the viewer's time zone; summary, points and nodes; the live stream needs sign-in |
| `test_complaints.py` | 6 | **a dead zone is detected → registered after the persistence time → resolved → verified by new strong readings**; a failed fix reopens the complaint; a recovered zone is dismissed; notes, assignment, evidence exports and counts; a user report is registered with evidence; admin settings, presets and channel status |
| `test_suggest.py` | 2 | suggestions from phone speed tests; the answer when there is no nearby data |
| `test_analytics.py` | 4 | summary and trends; worst areas, time of day, operators, funnel; model performance and field validation; public landing-page stats need no sign-in |
| `test_opencellid.py` | 3 | tower lookup is off without a key; nearest first, with the serving cell marked and the area cached; API errors are reported |
| `test_field_export.py` | 1 | the field sample is anonymised (rounded positions and times, pseudonyms, no identifiers) and repeatable |

## 2. Web app

```
cd frontend
npm run build        # TypeScript check (tsc -b) + production build + service worker
```

`run.bat` rebuilds `frontend/dist` automatically when the sources have changed, because phones load the built app through the tunnel.

## 3. Model checks

The training scripts are also checks. Each writes its metrics, baselines and plots, and `train_classifier.py` keeps temperature scaling only if it improves calibration on the validation traces. A fast smoke run of every script:

```
venv\Scripts\python ml\train_classifier.py --quick
venv\Scripts\python ml\train_throughput_model.py --quick
venv\Scripts\python ml\train_gp.py --quick
```

`--quick` never changes `models/`. The full results are in [05_MODELS_AND_TRAINING.md](05_MODELS_AND_TRAINING.md) and on the **Model performance** page.

---

## 4. End-to-end demo scenario

This is the scenario the product must run smoothly from a fresh `run.bat`, adapted to the browser probe. It was automated with Playwright and Chrome: an emulated Android phone with moving GPS and switchable connectivity, an engineer, and an admin. The phone's requests carried a mobile-network address, as they do through the tunnel.

| Step | What happened | Result |
|---|---|---|
| 1 | Admin: **Settings → Demo thresholds** | 4 readings, 10 min window, 2 min persistence, 3 readings to verify |
| 2 | Phone signs in via `/login?next=/probe`, registers, starts measuring every 5 s, and walks a strong area for 50 s | Readings appear live; a **Strong** zone for Airtel on the map |
| 3 | The phone walks about 550 m away and loses its connection | Live tab: **Dead**, "offline", and **"Better signal 528 m SW"** (from the phone's own strong readings, without a connection) |
| 4 | It stays in the dead spot for 2 min 10 s, still offline | 28 readings queued on the phone (Sync tab badge) |
| 5 | Connection returns | Queue synced with the original times; complaint **SS-2026-000043** is **registered** (Dead) within 6 s, with 28 readings, 100% bad share, and "nearest measured strong spot is 535 m SW" |
| 6 | Engineer: **Operator desk** → complaint → **Acknowledge → Start work → Mark resolved** | Status `resolved`; verification waiting for readings |
| 7 | The phone measures the zone again, now with good service | **Verified** automatically: 3 of 3 new readings Strong |
| - | Console errors across all three browsers | **0** |

Screenshots from the run, such as the complaint with its full timeline from *Detected* to *Verified*, look like the ones in [07_USER_GUIDE.md](07_USER_GUIDE.md).

Issues found during the walkthrough and fixed:

- Signing in from a probe link could land on the dashboard instead of the probe.
- The Live tab did not point to better signal in a dead zone.
- Speed tiles showed an old speed test without saying so.
- The map zoomed out to show every area at once.
- Forwarded addresses were trusted from any client.

## 5. Try it yourself with a phone (about 10 minutes)

1. Start `run.bat`. Sign in as `admin@signalscout.demo` / `Scout@2026` and click **Settings → Demo thresholds**.
2. **Connect a phone** → scan the QR code with an Android phone (Chrome).
   - Turn **Wi-Fi off**, so the mobile network is measured.
   - Sign in as `user@signalscout.demo`, allow location and tap **Register and continue**.
   - In the probe's **Settings**, set "Reading every" to 5 seconds. Tap **Start measuring**.
3. Walk for a minute where service is good. On the PC, open **Coverage map**: points appear live, then a zone.
4. **Airplane mode on**, to act as a dead spot. GPS keeps working. Keep the screen on and stay within about 100 m for 2-3 minutes, so the readings fall in one zone.
   - The Live tab shows **Dead** and **Better signal … m**, pointing back to where you had signal.
   - The **Sync** tab counts the waiting readings.
5. **Airplane mode off.** The readings sync with their original times.
   - Within seconds a complaint appears on the **Operator desk** (sign in as `engineer@signalscout.demo` in another browser).
   - The desk email and Telegram chat are notified, if configured.
6. As the engineer: open the complaint → **Acknowledge → Start work → Mark resolved**.
7. On the phone, measure at the same place again with service on. After 3 readings the complaint turns **Verified**. If the readings were still bad, it would be **reopened** instead.

## 6. Accessibility and responsive checks

- **axe-core 4.10** ran on every page (landing, sign-in, dashboard, map, analytics, model performance, complaints, desk, complaint detail, devices, connect, profile, settings, users, probe, not found). It ran in light and dark themes at 360 px and 1366 px. Serious and critical findings were fixed:
  - contrast of tinted badges and avatars;
  - names for icon-only buttons, switches and selects;
  - keyboard access to scrollable tables;
  - map markers without names;
  - a tab list without panels.
- There is a **Skip to content** link, and focus rings on every control.
- **Reduced motion:** with the OS setting on, the landing animations become a still frame, smooth scrolling is off, and page transitions do not move.
- **No horizontal scrolling at 360 px** on any page. Wide tables scroll inside their own box.
