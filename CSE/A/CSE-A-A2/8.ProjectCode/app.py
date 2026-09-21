"""
ResQAI - AI-Based Accident Detection, Severity Assessment
and Intelligent Emergency Response System

Flask backend serving:
  - the dashboard UI
  - /api/predict     : sensor reading -> accident + severity prediction
  - /api/hospitals    : nearest hospitals to a given lat/lon
  - /api/emergency    : simulate dispatching an emergency alert
  - /api/simulate     : generate one synthetic "live sensor" reading
"""

import json
import math
import os
import random
import time
from datetime import datetime

import joblib
import numpy as np
from flask import Flask, jsonify, render_template, request

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(APP_DIR, "models")
DATA_DIR = os.path.join(APP_DIR, "data")

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Load trained models (run `python train_models.py` first if these are missing)
# ---------------------------------------------------------------------------
try:
    accident_model = joblib.load(os.path.join(MODELS_DIR, "accident_detector.pkl"))
    severity_model = joblib.load(os.path.join(MODELS_DIR, "severity_predictor.pkl"))
    scaler = joblib.load(os.path.join(MODELS_DIR, "feature_scaler.pkl"))
    FEATURE_NAMES = joblib.load(os.path.join(MODELS_DIR, "feature_names.pkl"))
    MODELS_LOADED = True
except FileNotFoundError:
    MODELS_LOADED = False
    FEATURE_NAMES = [
        "acc_x", "acc_y", "acc_z", "acc_magnitude",
        "gyro_x", "gyro_y", "gyro_z", "gyro_magnitude",
        "speed_before", "speed_change", "jerk",
    ]

SEVERITY_LABELS = {0: "None", 1: "Minor", 2: "Moderate", 3: "Severe"}

with open(os.path.join(DATA_DIR, "hospitals.json"), "r") as f:
    HOSPITAL_DATA = json.load(f)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points, in kilometres."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def build_feature_vector(payload):
    """Turn an incoming sensor JSON payload into the ordered feature vector
    expected by the models, deriving magnitudes/jerk if not supplied."""
    acc_x = float(payload.get("acc_x", 0))
    acc_y = float(payload.get("acc_y", 0))
    acc_z = float(payload.get("acc_z", 9.81))
    gyro_x = float(payload.get("gyro_x", 0))
    gyro_y = float(payload.get("gyro_y", 0))
    gyro_z = float(payload.get("gyro_z", 0))
    speed_before = float(payload.get("speed_before", 0))
    speed_change = float(payload.get("speed_change", 0))
    jerk = float(payload.get("jerk", 0))

    acc_magnitude = payload.get("acc_magnitude")
    if acc_magnitude is None:
        acc_magnitude = math.sqrt(acc_x ** 2 + acc_y ** 2 + acc_z ** 2)

    gyro_magnitude = payload.get("gyro_magnitude")
    if gyro_magnitude is None:
        gyro_magnitude = math.sqrt(gyro_x ** 2 + gyro_y ** 2 + gyro_z ** 2)

    feature_map = {
        "acc_x": acc_x, "acc_y": acc_y, "acc_z": acc_z,
        "acc_magnitude": acc_magnitude,
        "gyro_x": gyro_x, "gyro_y": gyro_y, "gyro_z": gyro_z,
        "gyro_magnitude": gyro_magnitude,
        "speed_before": speed_before, "speed_change": speed_change,
        "jerk": abs(jerk),
    }
    vector = [feature_map[name] for name in FEATURE_NAMES]
    return np.array(vector).reshape(1, -1), feature_map


def rule_based_fallback(feature_map):
    """Simple threshold-based fallback used only if trained models are
    unavailable, so the app always returns a sensible response."""
    mag = feature_map["acc_magnitude"]
    if mag < 15:
        return 0, 0, 0.05
    if mag < 28:
        return 1, 1, 0.6
    if mag < 45:
        return 1, 2, 0.8
    return 1, 3, 0.95


def predict_from_features(feature_map, X):
    if MODELS_LOADED:
        X_scaled = scaler.transform(X)
        accident_pred = int(accident_model.predict(X_scaled)[0])
        accident_proba = float(accident_model.predict_proba(X_scaled)[0][1])
        severity_pred = int(severity_model.predict(X_scaled)[0])
        # if the accident detector disagrees with "no accident" severity, trust
        # the stronger signal (max of the two) for the alerting logic
        if accident_pred == 0:
            severity_pred = 0
        return accident_pred, severity_pred, accident_proba
    return rule_based_fallback(feature_map)


def nearest_hospitals(lat, lon, k=3):
    hospitals = HOSPITAL_DATA["hospitals"]
    scored = []
    for h in hospitals:
        d = haversine_km(lat, lon, h["lat"], h["lon"])
        scored.append({**h, "distance_km": round(d, 2)})
    scored.sort(key=lambda h: h["distance_km"])
    return scored[:k]


def random_nearby_point(lat, lon, radius_km=6):
    """Jitter a point randomly within ~radius_km, used to simulate a live
    GPS fix for the demo (real deployment would use the phone's GPS)."""
    r = radius_km / 111.0
    u, v = random.random(), random.random()
    w = r * math.sqrt(u)
    t = 2 * math.pi * v
    return lat + w * math.cos(t), lon + w * math.sin(t)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    default_loc = HOSPITAL_DATA["default_location"]
    return render_template("index.html", default_loc=default_loc, models_loaded=MODELS_LOADED)


@app.route("/api/predict", methods=["POST"])
def api_predict():
    payload = request.get_json(force=True) or {}
    X, feature_map = build_feature_vector(payload)
    accident_pred, severity_pred, confidence = predict_from_features(feature_map, X)

    response = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "accident_detected": bool(accident_pred),
        "severity_level": severity_pred,
        "severity_label": SEVERITY_LABELS[severity_pred],
        "confidence": round(confidence, 4),
        "features_used": feature_map,
        "model_source": "trained_ml_model" if MODELS_LOADED else "rule_based_fallback",
    }
    return jsonify(response)


@app.route("/api/simulate", methods=["GET"])
def api_simulate():
    """Generate one synthetic 'live sensor' reading for demo purposes.
    scenario = normal | brake | minor | moderate | severe | random
    """
    scenario = request.args.get("scenario", "random")
    g = 9.81

    def normal():
        return dict(
            acc_x=random.gauss(0, 0.4), acc_y=random.gauss(0, 0.4), acc_z=random.gauss(g, 0.3),
            gyro_x=random.gauss(0, 0.15), gyro_y=random.gauss(0, 0.15), gyro_z=random.gauss(0, 0.15),
            speed_before=random.uniform(0, 80), speed_change=random.gauss(0, 2), jerk=abs(random.gauss(0, 0.5)),
        )

    def brake():
        return dict(
            acc_x=random.gauss(-4.5, 1.2), acc_y=random.gauss(0, 0.6), acc_z=random.gauss(g, 0.5),
            gyro_x=random.gauss(0, 0.3), gyro_y=random.gauss(0, 0.3), gyro_z=random.gauss(0, 0.4),
            speed_before=random.uniform(20, 100), speed_change=-random.uniform(10, 35),
            jerk=abs(random.gauss(6, 2)),
        )

    def crash(mag_range, speed_change_range, jerk_mean):
        mag = random.uniform(*mag_range)
        theta = random.uniform(0, 2 * math.pi)
        return dict(
            acc_x=mag * math.cos(theta) + random.gauss(0, 1.5),
            acc_y=mag * math.sin(theta) + random.gauss(0, 1.5),
            acc_z=random.gauss(g, 2.0),
            gyro_x=random.gauss(0, 1.5), gyro_y=random.gauss(0, 1.5), gyro_z=random.gauss(0, 1.5),
            speed_before=random.uniform(10, 90),
            speed_change=-random.uniform(*speed_change_range),
            jerk=abs(random.gauss(jerk_mean, 6)),
        )

    generators = {
        "normal": normal,
        "brake": brake,
        "minor": lambda: crash((15, 28), (10, 40), 20),
        "moderate": lambda: crash((28, 45), (25, 55), 35),
        "severe": lambda: crash((45, 80), (45, 100), 60),
    }

    if scenario not in generators:
        scenario = random.choices(
            ["normal", "brake", "minor", "moderate", "severe"],
            weights=[0.65, 0.18, 0.09, 0.05, 0.03],
        )[0]

    reading = generators[scenario]()
    reading["acc_magnitude"] = math.sqrt(reading["acc_x"] ** 2 + reading["acc_y"] ** 2 + reading["acc_z"] ** 2)
    reading["gyro_magnitude"] = math.sqrt(reading["gyro_x"] ** 2 + reading["gyro_y"] ** 2 + reading["gyro_z"] ** 2)
    reading["scenario"] = scenario
    return jsonify(reading)


@app.route("/api/hospitals", methods=["GET"])
def api_hospitals():
    default_loc = HOSPITAL_DATA["default_location"]
    lat = float(request.args.get("lat", default_loc["lat"]))
    lon = float(request.args.get("lon", default_loc["lon"]))
    k = int(request.args.get("k", 3))
    return jsonify({"origin": {"lat": lat, "lon": lon}, "hospitals": nearest_hospitals(lat, lon, k)})


@app.route("/api/emergency", methods=["POST"])
def api_emergency():
    """Simulate raising an emergency alert: resolve location, pick nearest
    hospital, and draft the emergency message that would be sent to
    responders / emergency contacts in a real deployment."""
    payload = request.get_json(force=True) or {}
    default_loc = HOSPITAL_DATA["default_location"]

    lat = payload.get("lat")
    lon = payload.get("lon")
    if lat is None or lon is None:
        lat, lon = random_nearby_point(default_loc["lat"], default_loc["lon"])

    severity_label = payload.get("severity_label", "Severe")
    confidence = payload.get("confidence", 0.9)

    hospitals = nearest_hospitals(lat, lon, k=3)
    nearest = hospitals[0] if hospitals else None

    message = (
        f"ResQAI EMERGENCY ALERT\n"
        f"Severity: {severity_label} (confidence {round(float(confidence) * 100)}%)\n"
        f"Location: {lat:.5f}, {lon:.5f}\n"
        f"Google Maps: https://www.google.com/maps?q={lat:.5f},{lon:.5f}\n"
    )
    if nearest:
        message += (
            f"Nearest hospital: {nearest['name']} "
            f"({nearest['distance_km']} km away, {nearest['phone']})\n"
        )
    message += "No response received from occupant. Please dispatch assistance."

    response = {
        "status": "dispatched",
        "alert_id": f"RQ-{int(time.time())}",
        "location": {"lat": lat, "lon": lon},
        "nearest_hospitals": hospitals,
        "message": message,
        "national_emergency_number": "112",
        "ambulance_number": "108",
    }
    return jsonify(response)


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "models_loaded": MODELS_LOADED})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
