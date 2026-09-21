"""
Trains Random Forest, Decision Tree, SVM, and Logistic Regression
for each disease dataset, evaluates them, and saves the best
performing model (+ scaler) for use by the Flask app.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

os.makedirs("models", exist_ok=True)

RANDOM_STATE = 42

DISEASES = {
    "diabetes": {
        "csv": "data/diabetes.csv",
        "target": "Outcome",
        "features": [
            "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age",
        ],
    },
    "heart": {
        "csv": "data/heart.csv",
        "target": "target",
        "features": [
            "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
            "thalach", "exang", "oldpeak", "slope", "ca", "thal",
        ],
    },
    "liver": {
        "csv": "data/liver.csv",
        "target": "Dataset",
        "features": [
            "Age", "Gender", "Total_Bilirubin", "Direct_Bilirubin",
            "Alkaline_Phosphotase", "Alamine_Aminotransferase",
            "Aspartate_Aminotransferase", "Total_Protiens", "Albumin",
            "Albumin_and_Globulin_Ratio",
        ],
    },
    "kidney": {
        "csv": "data/kidney.csv",
        "target": "classification",
        "features": [
            "age", "blood_pressure", "specific_gravity", "albumin", "sugar",
            "blood_glucose_random", "blood_urea", "serum_creatinine",
            "sodium", "potassium", "hemoglobin", "packed_cell_volume",
        ],
    },
}

MODEL_BUILDERS = {
    "Logistic Regression": lambda: LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
    "Decision Tree": lambda: DecisionTreeClassifier(max_depth=6, random_state=RANDOM_STATE),
    "Random Forest": lambda: RandomForestClassifier(n_estimators=200, max_depth=8, random_state=RANDOM_STATE),
    "SVM": lambda: SVC(kernel="rbf", C=1.0, probability=True, random_state=RANDOM_STATE),
}

report = {}

for disease, cfg in DISEASES.items():
    print(f"\n{'='*60}\nTraining models for: {disease.upper()}\n{'='*60}")
    df = pd.read_csv(cfg["csv"])
    X = df[cfg["features"]].values
    y = df[cfg["target"]].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    results = {}
    fitted_models = {}
    for name, builder in MODEL_BUILDERS.items():
        model = builder()
        model.fit(X_train_s, y_train)
        preds = model.predict(X_test_s)
        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        results[name] = {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
        }
        fitted_models[name] = model
        print(f"  {name:22s} | Acc: {acc:.4f}  Prec: {prec:.4f}  Rec: {rec:.4f}  F1: {f1:.4f}")

    best_name = max(results, key=lambda n: results[n]["f1"])
    best_model = fitted_models[best_name]
    print(f"  --> Best model: {best_name} (F1={results[best_name]['f1']})")

    joblib.dump(best_model, f"models/{disease}_model.pkl")
    joblib.dump(scaler, f"models/{disease}_scaler.pkl")
    joblib.dump(cfg["features"], f"models/{disease}_features.pkl")

    report[disease] = {
        "best_model": best_name,
        "all_results": results,
        "features": cfg["features"],
    }

with open("models/training_report.json", "w") as f:
    json.dump(report, f, indent=2)

print("\nAll models trained and saved to ./models/")
print("Summary written to models/training_report.json")
