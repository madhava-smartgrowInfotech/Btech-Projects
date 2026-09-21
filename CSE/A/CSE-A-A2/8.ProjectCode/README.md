# ResQAI — AI-Based Accident Detection, Severity Assessment & Intelligent Emergency Response System

ResQAI is a Flask web application that demonstrates an end-to-end pipeline:

1. **Sensor input** — accelerometer / gyroscope / speed data (streamed live
   from a phone in a real deployment; simulated in this build so it runs
   anywhere without hardware).
2. **Accident detection** — a trained Random Forest model flags whether a
   sensor event looks like a crash.
3. **Severity assessment** — a second Random Forest predicts severity:
   `None / Minor / Moderate / Severe`.
4. **Confirmation mechanism** — on a Moderate/Severe detection, a 15-second
   countdown lets the user cancel a false alarm before an alert goes out.
5. **Emergency response** — if not cancelled, the app resolves the location,
   finds the nearest hospital, and drafts the emergency dispatch message.

---

## 1. Setup

```bash
cd ResQAI
python3 -m pip install -r requirements.txt
```

(Everything is standard PyPI packages: Flask, scikit-learn, numpy, pandas,
joblib.)

## 2. Train the models (creates the `models/*.pkl` files)

```bash
python3 train_models.py
```

This generates a synthetic sensor-event dataset (normal driving, harsh
braking, minor/moderate/severe crashes) and trains:

- `models/accident_detector.pkl` — binary accident / no-accident classifier
- `models/severity_predictor.pkl` — 4-class severity classifier
- `models/feature_scaler.pkl`, `models/feature_names.pkl` — supporting
  preprocessing artifacts

The trained `.pkl` files are already included in this ZIP, so this step is
optional unless you want to regenerate them.

## 3. Run the app

```bash
python3 app.py
```

Then open **http://127.0.0.1:5000** in a browser.

## 4. Using the dashboard

- **Scenario buttons** (Normal Driving / Harsh Brake / Minor / Moderate /
  Severe Crash) instantly feed a realistic synthetic sensor reading through
  the ML pipeline so you can demo every outcome on demand.
- **Start Live Monitoring** streams a new random reading every 1.5 seconds,
  like a phone continuously sampling its sensors.
- **Manual Override** sliders/fields let you type in your own
  accelerometer / gyroscope / speed values and run detection on them.
- When a **Moderate** or **Severe** event is detected, a confirmation
  dialog pops up with a 15-second countdown. Click **"I'm Fine, Cancel"**
  to suppress a false alarm, or let the timer run out (or click **"Send
  Alert Now"**) to see the full emergency response: location plotted on
  the map, nearest hospital identified, and the dispatch message that
  would be sent to responders/emergency contacts.

## Project structure

```
ResQAI/
├── app.py                  # Flask backend & REST API
├── train_models.py         # synthetic data generation + model training
├── requirements.txt
├── data/
│   └── hospitals.json      # demo hospital directory (name, lat/lon, phone)
├── models/                 # trained model artifacts (.pkl)
├── templates/
│   └── index.html          # dashboard UI
└── static/
    ├── css/style.css
    └── js/script.js        # chart, map, prediction & alert logic
```

## API endpoints

| Method | Endpoint          | Purpose                                             |
|--------|-------------------|------------------------------------------------------|
| GET    | `/`               | Dashboard UI                                         |
| POST   | `/api/predict`    | Sensor reading → accident + severity prediction      |
| GET    | `/api/simulate`   | Generate one synthetic sensor reading (`?scenario=`) |
| GET    | `/api/hospitals`  | Nearest hospitals to a given `lat`/`lon`             |
| POST   | `/api/emergency`  | Simulate dispatching an emergency alert              |
| GET    | `/api/health`     | Health check / model-load status                     |

## Notes

- Hospital data is a small demo directory (`data/hospitals.json`) — swap in
  a real API (e.g. Google Places) for production use.
- Location is taken from the browser's Geolocation API when available (the
  browser will prompt for permission); otherwise a location near the
  configured default is used so the demo still works.
- The ML models are trained on synthetic data crafted to resemble the
  documented sensor characteristics of real crashes (a large, brief
  acceleration/gyroscope spike, on top of normal driving and harsh-braking
  events) — swap in a labeled real-world dataset to move this from
  prototype to production grade.
