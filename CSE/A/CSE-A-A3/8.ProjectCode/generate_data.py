"""
Generates realistic, rule-based synthetic clinical datasets for:
Diabetes, Heart Disease, Liver Disease, Kidney Disease.

Each dataset uses medically-informed feature ranges and logical
risk rules (plus noise) so trained models reflect genuine patterns
instead of random labels.
"""

import numpy as np
import pandas as pd
import os

np.random.seed(42)
os.makedirs("data", exist_ok=True)

N = 2000


def add_noise_labels(risk_score, noise=0.08):
    """Convert a continuous risk score into a binary label with some label noise."""
    prob = 1 / (1 + np.exp(-risk_score))
    flip = np.random.rand(len(prob)) < noise
    labels = (prob > 0.5).astype(int)
    labels[flip] = 1 - labels[flip]
    return labels


# ---------------------------------------------------------------
# 1) DIABETES DATASET
# ---------------------------------------------------------------
def generate_diabetes(n=N):
    age = np.random.randint(18, 80, n)
    pregnancies = np.random.randint(0, 10, n)
    glucose = np.random.normal(120, 30, n).clip(60, 250)
    blood_pressure = np.random.normal(72, 12, n).clip(40, 130)
    skin_thickness = np.random.normal(20, 10, n).clip(0, 60)
    insulin = np.random.normal(80, 60, n).clip(0, 400)
    bmi = np.random.normal(30, 7, n).clip(15, 55)
    dpf = np.random.normal(0.47, 0.3, n).clip(0.05, 2.5)

    risk = (
        0.04 * (glucose - 120)
        + 0.06 * (bmi - 30)
        + 0.02 * (age - 40)
        + 1.5 * dpf
        + 0.03 * (blood_pressure - 72)
        - 1.4
    )
    outcome = add_noise_labels(risk)

    df = pd.DataFrame({
        "Pregnancies": pregnancies,
        "Glucose": glucose.round(1),
        "BloodPressure": blood_pressure.round(1),
        "SkinThickness": skin_thickness.round(1),
        "Insulin": insulin.round(1),
        "BMI": bmi.round(1),
        "DiabetesPedigreeFunction": dpf.round(3),
        "Age": age,
        "Outcome": outcome,
    })
    return df


# ---------------------------------------------------------------
# 2) HEART DISEASE DATASET
# ---------------------------------------------------------------
def generate_heart(n=N):
    age = np.random.randint(29, 80, n)
    sex = np.random.randint(0, 2, n)  # 1 = male, 0 = female
    cp = np.random.randint(0, 4, n)  # chest pain type
    trestbps = np.random.normal(131, 17, n).clip(90, 200)  # resting BP
    chol = np.random.normal(246, 51, n).clip(120, 450)  # cholesterol
    fbs = (np.random.rand(n) < 0.15).astype(int)  # fasting blood sugar >120
    restecg = np.random.randint(0, 3, n)
    thalach = np.random.normal(150, 23, n).clip(70, 210)  # max heart rate
    exang = (np.random.rand(n) < 0.33).astype(int)  # exercise induced angina
    oldpeak = np.random.exponential(1.0, n).clip(0, 6)
    slope = np.random.randint(0, 3, n)
    ca = np.random.randint(0, 4, n)  # number of major vessels
    thal = np.random.randint(0, 3, n)

    risk = (
        0.035 * (age - 50)
        + 0.9 * sex
        + 0.5 * cp
        + 0.02 * (trestbps - 130)
        + 0.01 * (chol - 240)
        + 0.8 * exang
        + 0.5 * oldpeak
        + 0.6 * ca
        - 0.02 * (thalach - 150)
        - 1.9
    )
    target = add_noise_labels(risk)

    df = pd.DataFrame({
        "age": age,
        "sex": sex,
        "cp": cp,
        "trestbps": trestbps.round(1),
        "chol": chol.round(1),
        "fbs": fbs,
        "restecg": restecg,
        "thalach": thalach.round(1),
        "exang": exang,
        "oldpeak": oldpeak.round(2),
        "slope": slope,
        "ca": ca,
        "thal": thal,
        "target": target,
    })
    return df


# ---------------------------------------------------------------
# 3) LIVER DISEASE DATASET
# ---------------------------------------------------------------
def generate_liver(n=N):
    age = np.random.randint(18, 85, n)
    gender = np.random.randint(0, 2, n)  # 1 = male, 0 = female
    total_bilirubin = np.random.exponential(1.5, n).clip(0.1, 20)
    direct_bilirubin = (total_bilirubin * np.random.uniform(0.2, 0.6, n)).clip(0.1, 10)
    alk_phosphotase = np.random.normal(290, 150, n).clip(60, 1200)
    alamine_aminotransferase = np.random.exponential(45, n).clip(5, 500)
    aspartate_aminotransferase = np.random.exponential(50, n).clip(5, 500)
    total_proteins = np.random.normal(6.5, 1.0, n).clip(3, 9)
    albumin = np.random.normal(3.2, 0.8, n).clip(1, 5.5)
    ag_ratio = (albumin / (total_proteins - albumin + 0.1)).clip(0.2, 3)

    risk = (
        0.35 * total_bilirubin
        + 0.02 * (alk_phosphotase - 290)
        + 0.015 * (alamine_aminotransferase - 45)
        + 0.01 * (aspartate_aminotransferase - 50)
        - 0.8 * albumin
        + 0.015 * (age - 45)
        - 0.3
    )
    dataset = add_noise_labels(risk)  # 1 = liver disease present

    df = pd.DataFrame({
        "Age": age,
        "Gender": gender,
        "Total_Bilirubin": total_bilirubin.round(2),
        "Direct_Bilirubin": direct_bilirubin.round(2),
        "Alkaline_Phosphotase": alk_phosphotase.round(1),
        "Alamine_Aminotransferase": alamine_aminotransferase.round(1),
        "Aspartate_Aminotransferase": aspartate_aminotransferase.round(1),
        "Total_Protiens": total_proteins.round(2),
        "Albumin": albumin.round(2),
        "Albumin_and_Globulin_Ratio": ag_ratio.round(2),
        "Dataset": dataset,
    })
    return df


# ---------------------------------------------------------------
# 4) KIDNEY DISEASE DATASET
# ---------------------------------------------------------------
def generate_kidney(n=N):
    age = np.random.randint(2, 90, n)
    blood_pressure = np.random.normal(76, 13, n).clip(50, 180)
    specific_gravity = np.random.choice([1.005, 1.010, 1.015, 1.020, 1.025], n)
    albumin = np.random.randint(0, 5, n)
    sugar = np.random.randint(0, 5, n)
    blood_glucose_random = np.random.normal(148, 70, n).clip(50, 490)
    blood_urea = np.random.exponential(45, n).clip(10, 300)
    serum_creatinine = np.random.exponential(1.5, n).clip(0.3, 15)
    sodium = np.random.normal(137, 8, n).clip(110, 160)
    potassium = np.random.normal(4.4, 1.0, n).clip(2.5, 8)
    hemoglobin = np.random.normal(12.5, 2.5, n).clip(3, 18)
    packed_cell_volume = np.random.normal(38, 8, n).clip(15, 55)

    risk = (
        0.02 * (age - 45)
        + 0.02 * (blood_pressure - 76)
        - 40 * (specific_gravity - 1.015)
        + 0.6 * albumin
        + 0.35 * sugar
        + 0.01 * (blood_glucose_random - 148)
        + 0.02 * (blood_urea - 45)
        + 0.6 * (serum_creatinine - 1.5)
        - 0.35 * (hemoglobin - 12.5)
        - 1.2
    )
    classification = add_noise_labels(risk)  # 1 = CKD present

    df = pd.DataFrame({
        "age": age,
        "blood_pressure": blood_pressure.round(1),
        "specific_gravity": specific_gravity,
        "albumin": albumin,
        "sugar": sugar,
        "blood_glucose_random": blood_glucose_random.round(1),
        "blood_urea": blood_urea.round(1),
        "serum_creatinine": serum_creatinine.round(2),
        "sodium": sodium.round(1),
        "potassium": potassium.round(2),
        "hemoglobin": hemoglobin.round(2),
        "packed_cell_volume": packed_cell_volume.round(1),
        "classification": classification,
    })
    return df


if __name__ == "__main__":
    generate_diabetes().to_csv("data/diabetes.csv", index=False)
    generate_heart().to_csv("data/heart.csv", index=False)
    generate_liver().to_csv("data/liver.csv", index=False)
    generate_kidney().to_csv("data/kidney.csv", index=False)
    print("All datasets generated successfully in ./data/")
