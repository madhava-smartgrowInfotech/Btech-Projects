from flask import Flask, render_template, request
import joblib
import numpy as np
import json
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

with open(os.path.join(MODELS_DIR, "training_report.json")) as f:
    TRAINING_REPORT = json.load(f)


def load_bundle(disease):
    model = joblib.load(os.path.join(MODELS_DIR, f"{disease}_model.pkl"))
    scaler = joblib.load(os.path.join(MODELS_DIR, f"{disease}_scaler.pkl"))
    features = joblib.load(os.path.join(MODELS_DIR, f"{disease}_features.pkl"))
    return model, scaler, features


BUNDLES = {d: load_bundle(d) for d in ["diabetes", "heart", "liver", "kidney"]}

# Field metadata: label shown to user + help text + input type
FIELD_META = {
    "diabetes": {
        "Pregnancies": ("Number of Pregnancies", "e.g. 2", "number"),
        "Glucose": ("Glucose Level (mg/dL)", "e.g. 120", "number"),
        "BloodPressure": ("Blood Pressure (mm Hg)", "e.g. 72", "number"),
        "SkinThickness": ("Skin Thickness (mm)", "e.g. 20", "number"),
        "Insulin": ("Insulin Level (mu U/ml)", "e.g. 80", "number"),
        "BMI": ("BMI", "e.g. 28.5", "number"),
        "DiabetesPedigreeFunction": ("Diabetes Pedigree Function", "e.g. 0.5", "number"),
        "Age": ("Age", "e.g. 35", "number"),
    },
    "heart": {
        "age": ("Age", "e.g. 52", "number"),
        "sex": ("Sex (1 = Male, 0 = Female)", "0 or 1", "number"),
        "cp": ("Chest Pain Type (0-3)", "0 to 3", "number"),
        "trestbps": ("Resting Blood Pressure (mm Hg)", "e.g. 130", "number"),
        "chol": ("Serum Cholesterol (mg/dl)", "e.g. 240", "number"),
        "fbs": ("Fasting Blood Sugar > 120 mg/dl (1=Yes, 0=No)", "0 or 1", "number"),
        "restecg": ("Resting ECG Result (0-2)", "0 to 2", "number"),
        "thalach": ("Max Heart Rate Achieved", "e.g. 150", "number"),
        "exang": ("Exercise Induced Angina (1=Yes, 0=No)", "0 or 1", "number"),
        "oldpeak": ("ST Depression (oldpeak)", "e.g. 1.2", "number"),
        "slope": ("Slope of ST Segment (0-2)", "0 to 2", "number"),
        "ca": ("Number of Major Vessels (0-3)", "0 to 3", "number"),
        "thal": ("Thalassemia (0-2)", "0 to 2", "number"),
    },
    "liver": {
        "Age": ("Age", "e.g. 45", "number"),
        "Gender": ("Gender (1 = Male, 0 = Female)", "0 or 1", "number"),
        "Total_Bilirubin": ("Total Bilirubin", "e.g. 1.0", "number"),
        "Direct_Bilirubin": ("Direct Bilirubin", "e.g. 0.3", "number"),
        "Alkaline_Phosphotase": ("Alkaline Phosphotase", "e.g. 290", "number"),
        "Alamine_Aminotransferase": ("Alamine Aminotransferase (ALT)", "e.g. 45", "number"),
        "Aspartate_Aminotransferase": ("Aspartate Aminotransferase (AST)", "e.g. 50", "number"),
        "Total_Protiens": ("Total Proteins", "e.g. 6.5", "number"),
        "Albumin": ("Albumin", "e.g. 3.2", "number"),
        "Albumin_and_Globulin_Ratio": ("Albumin and Globulin Ratio", "e.g. 1.0", "number"),
    },
    "kidney": {
        "age": ("Age", "e.g. 45", "number"),
        "blood_pressure": ("Blood Pressure (mm Hg)", "e.g. 76", "number"),
        "specific_gravity": ("Urine Specific Gravity", "e.g. 1.015", "number"),
        "albumin": ("Albumin (0-4)", "0 to 4", "number"),
        "sugar": ("Sugar (0-4)", "0 to 4", "number"),
        "blood_glucose_random": ("Random Blood Glucose", "e.g. 148", "number"),
        "blood_urea": ("Blood Urea", "e.g. 45", "number"),
        "serum_creatinine": ("Serum Creatinine", "e.g. 1.2", "number"),
        "sodium": ("Sodium", "e.g. 137", "number"),
        "potassium": ("Potassium", "e.g. 4.4", "number"),
        "hemoglobin": ("Hemoglobin", "e.g. 12.5", "number"),
        "packed_cell_volume": ("Packed Cell Volume", "e.g. 38", "number"),
    },
}

DISEASE_TITLES = {
    "diabetes": "Diabetes Risk Prediction",
    "heart": "Heart Disease Risk Prediction",
    "liver": "Liver Disease Risk Prediction",
    "kidney": "Kidney Disease Risk Prediction",
}


@app.route("/")
def home():
    accuracies = {}
    for disease, info in TRAINING_REPORT.items():
        best = info["best_model"]
        accuracies[disease] = {
            "model": best,
            "accuracy": info["all_results"][best]["accuracy"],
        }
    return render_template("index.html", accuracies=accuracies, titles=DISEASE_TITLES)


def handle_prediction(disease):
    model, scaler, features = BUNDLES[disease]
    fields = FIELD_META[disease]
    result = None
    probability = None
    submitted_values = {}

    if request.method == "POST":
        try:
            values = []
            for feat in features:
                raw = request.form.get(feat, "0")
                submitted_values[feat] = raw
                values.append(float(raw))
            X = np.array(values).reshape(1, -1)
            X_scaled = scaler.transform(X)
            pred = model.predict(X_scaled)[0]
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(X_scaled)[0]
                probability = round(float(max(proba)) * 100, 2)
            result = "Positive (High Risk)" if pred == 1 else "Negative (Low Risk)"
        except Exception as e:
            result = f"Error: please check your inputs ({e})"

    best_model_name = TRAINING_REPORT[disease]["best_model"]
    best_acc = TRAINING_REPORT[disease]["all_results"][best_model_name]["accuracy"]

    return render_template(
        "predict.html",
        disease=disease,
        title=DISEASE_TITLES[disease],
        features=features,
        fields=fields,
        result=result,
        probability=probability,
        submitted_values=submitted_values,
        model_name=best_model_name,
        accuracy=best_acc,
    )


@app.route("/diabetes", methods=["GET", "POST"])
def diabetes():
    return handle_prediction("diabetes")


@app.route("/heart", methods=["GET", "POST"])
def heart():
    return handle_prediction("heart")


@app.route("/liver", methods=["GET", "POST"])
def liver():
    return handle_prediction("liver")


@app.route("/kidney", methods=["GET", "POST"])
def kidney():
    return handle_prediction("kidney")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
