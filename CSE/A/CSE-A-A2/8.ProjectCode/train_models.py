"""
ResQAI - Model Training Script
--------------------------------
Generates a synthetic sensor-event dataset (accelerometer + gyroscope +
speed features) that mimics normal driving, harsh-braking, and crash
events, then trains two models:

  1. accident_detector  -> binary classifier (accident / no-accident)
  2. severity_predictor -> multi-class classifier (0=None,1=Minor,2=Moderate,3=Severe)

Both models are saved with joblib into the models/ folder so app.py
can load them at runtime without needing to retrain.

Run once before starting the Flask app:
    python train_models.py
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import joblib
import os

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

N_SAMPLES = 12000
FEATURE_NAMES = [
    "acc_x", "acc_y", "acc_z", "acc_magnitude",
    "gyro_x", "gyro_y", "gyro_z", "gyro_magnitude",
    "speed_before", "speed_change", "jerk"
]


def make_event(kind):
    """Generate one synthetic sensor sample for a given event kind."""
    g = 9.81

    if kind == "normal":
        acc_x = np.random.normal(0, 0.4)
        acc_y = np.random.normal(0, 0.4)
        acc_z = np.random.normal(g, 0.3)
        gyro_x = np.random.normal(0, 0.15)
        gyro_y = np.random.normal(0, 0.15)
        gyro_z = np.random.normal(0, 0.15)
        speed_before = np.random.uniform(0, 80)
        speed_change = np.random.normal(0, 2)
        jerk = np.random.normal(0, 0.5)
        accident = 0
        severity = 0

    elif kind == "harsh_brake":
        acc_x = np.random.normal(-4.5, 1.2)
        acc_y = np.random.normal(0, 0.6)
        acc_z = np.random.normal(g, 0.5)
        gyro_x = np.random.normal(0, 0.3)
        gyro_y = np.random.normal(0, 0.3)
        gyro_z = np.random.normal(0, 0.4)
        speed_before = np.random.uniform(20, 100)
        speed_change = -np.random.uniform(10, 35)
        jerk = np.random.normal(6, 2)
        accident = 0
        severity = 0

    elif kind == "minor_crash":
        mag = np.random.uniform(15, 28)
        theta = np.random.uniform(0, 2 * np.pi)
        acc_x = mag * np.cos(theta) + np.random.normal(0, 1.5)
        acc_y = mag * np.sin(theta) + np.random.normal(0, 1.5)
        acc_z = np.random.normal(g, 2.0)
        gyro_x = np.random.normal(0, 1.5)
        gyro_y = np.random.normal(0, 1.5)
        gyro_z = np.random.normal(0, 1.5)
        speed_before = np.random.uniform(10, 60)
        speed_change = -np.random.uniform(10, 40)
        jerk = np.random.normal(20, 5)
        accident = 1
        severity = 1

    elif kind == "moderate_crash":
        mag = np.random.uniform(28, 45)
        theta = np.random.uniform(0, 2 * np.pi)
        acc_x = mag * np.cos(theta) + np.random.normal(0, 2)
        acc_y = mag * np.sin(theta) + np.random.normal(0, 2)
        acc_z = np.random.normal(g, 3.0)
        gyro_x = np.random.normal(0, 2.5)
        gyro_y = np.random.normal(0, 2.5)
        gyro_z = np.random.normal(0, 2.5)
        speed_before = np.random.uniform(30, 90)
        speed_change = -np.random.uniform(25, 55)
        jerk = np.random.normal(35, 8)
        accident = 1
        severity = 2

    else:  # severe_crash
        mag = np.random.uniform(45, 80)
        theta = np.random.uniform(0, 2 * np.pi)
        acc_x = mag * np.cos(theta) + np.random.normal(0, 3)
        acc_y = mag * np.sin(theta) + np.random.normal(0, 3)
        acc_z = np.random.normal(g, 5.0)
        gyro_x = np.random.normal(0, 4.0)
        gyro_y = np.random.normal(0, 4.0)
        gyro_z = np.random.normal(0, 4.0)
        speed_before = np.random.uniform(40, 140)
        speed_change = -np.random.uniform(45, 100)
        jerk = np.random.normal(60, 12)
        accident = 1
        severity = 3

    acc_magnitude = np.sqrt(acc_x ** 2 + acc_y ** 2 + acc_z ** 2)
    gyro_magnitude = np.sqrt(gyro_x ** 2 + gyro_y ** 2 + gyro_z ** 2)

    return {
        "acc_x": acc_x, "acc_y": acc_y, "acc_z": acc_z,
        "acc_magnitude": acc_magnitude,
        "gyro_x": gyro_x, "gyro_y": gyro_y, "gyro_z": gyro_z,
        "gyro_magnitude": gyro_magnitude,
        "speed_before": speed_before, "speed_change": speed_change,
        "jerk": abs(jerk),
        "accident": accident,
        "severity": severity,
    }


def generate_dataset(n=N_SAMPLES):
    # class proportions: mostly normal driving, some braking, few crashes
    kinds = np.random.choice(
        ["normal", "harsh_brake", "minor_crash", "moderate_crash", "severe_crash"],
        size=n,
        p=[0.60, 0.20, 0.10, 0.06, 0.04],
    )
    rows = [make_event(k) for k in kinds]
    return pd.DataFrame(rows)


def main():
    os.makedirs("models", exist_ok=True)
    print("Generating synthetic sensor-event dataset...")
    df = generate_dataset()
    print(f"Dataset shape: {df.shape}")
    print(df[["accident", "severity"]].value_counts())

    X = df[FEATURE_NAMES].values
    y_accident = df["accident"].values
    y_severity = df["severity"].values

    X_train, X_test, y_acc_train, y_acc_test, y_sev_train, y_sev_test = train_test_split(
        X, y_accident, y_severity, test_size=0.2, random_state=RANDOM_STATE, stratify=y_accident
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ---- Accident detector (binary) ----
    print("\nTraining accident detector...")
    accident_clf = RandomForestClassifier(
        n_estimators=200, max_depth=10, random_state=RANDOM_STATE, class_weight="balanced"
    )
    accident_clf.fit(X_train_scaled, y_acc_train)
    acc_pred = accident_clf.predict(X_test_scaled)
    print("Accident detector accuracy:", round(accuracy_score(y_acc_test, acc_pred), 4))
    print(classification_report(y_acc_test, acc_pred, target_names=["No Accident", "Accident"]))

    # ---- Severity predictor (multi-class, trained on all data incl. non-accidents as class 0) ----
    print("\nTraining severity predictor...")
    severity_clf = RandomForestClassifier(
        n_estimators=250, max_depth=12, random_state=RANDOM_STATE, class_weight="balanced"
    )
    severity_clf.fit(X_train_scaled, y_sev_train)
    sev_pred = severity_clf.predict(X_test_scaled)
    print("Severity predictor accuracy:", round(accuracy_score(y_sev_test, sev_pred), 4))
    print(classification_report(
        y_sev_test, sev_pred,
        target_names=["None", "Minor", "Moderate", "Severe"],
        zero_division=0
    ))

    joblib.dump(accident_clf, "models/accident_detector.pkl")
    joblib.dump(severity_clf, "models/severity_predictor.pkl")
    joblib.dump(scaler, "models/feature_scaler.pkl")
    joblib.dump(FEATURE_NAMES, "models/feature_names.pkl")

    print("\nSaved models to models/ :")
    print(" - accident_detector.pkl")
    print(" - severity_predictor.pkl")
    print(" - feature_scaler.pkl")
    print(" - feature_names.pkl")


if __name__ == "__main__":
    main()
