"""Shared feature definitions: the fused patient record is vitals + report-derived flags."""

VITALS = ["age", "heart_rate", "sbp", "dbp", "spo2", "temp_c", "resp_rate", "arrival_code"]

ARRIVAL_CODES = {"walk-in": 0, "transfer": 1, "ambulance": 2}

VITAL_LABELS = {
    "age": "Age",
    "heart_rate": "Heart rate",
    "sbp": "Systolic BP",
    "dbp": "Diastolic BP",
    "spo2": "SpO2",
    "temp_c": "Temperature",
    "resp_rate": "Respiratory rate",
    "arrival_code": "Arrival mode",
}

# flag name -> (category, label)
REPORT_FLAGS = {
    "chest_pain": ("symptom", "Chest pain"),
    "dyspnea": ("symptom", "Shortness of breath"),
    "altered_mental": ("symptom", "Altered mental state"),
    "syncope": ("symptom", "Syncope"),
    "fever": ("symptom", "Fever"),
    "abd_pain": ("symptom", "Abdominal pain"),
    "bleeding": ("symptom", "Bleeding"),
    "stroke_signs": ("symptom", "Focal weakness / speech change"),
    "severe_headache": ("symptom", "Severe headache"),
    "vomiting": ("symptom", "Vomiting"),
    "trauma": ("symptom", "Trauma / injury"),
    "st_elevation": ("finding", "ST elevation on ECG"),
    "infiltrate": ("finding", "Lung infiltrate"),
    "fracture": ("finding", "Fracture"),
    "free_fluid": ("finding", "Free abdominal fluid"),
    "ct_hemorrhage": ("finding", "Intracranial haemorrhage"),
    "diabetes": ("history", "Diabetes"),
    "hypertension": ("history", "Hypertension"),
    "cardiac_hx": ("history", "Cardiac disease"),
    "copd": ("history", "COPD / asthma"),
    "prior_stroke": ("history", "Prior stroke"),
    "anticoagulant": ("history", "On anticoagulant"),
    "lab_troponin_high": ("lab", "Troponin raised"),
    "lab_lactate_high": ("lab", "Lactate raised"),
    "lab_wbc_high": ("lab", "WBC raised"),
    "lab_glucose_abn": ("lab", "Glucose abnormal"),
    "lab_creatinine_high": ("lab", "Creatinine raised"),
    "lab_hgb_low": ("lab", "Haemoglobin low"),
}

FLAGS = list(REPORT_FLAGS)
FEATURES = VITALS + FLAGS

PRIORITY_NAMES = {
    1: "Critical",
    2: "Emergent",
    3: "Urgent",
    4: "Less urgent",
    5: "Non-urgent",
}


def risk_level(priority: int) -> str:
    if priority <= 2:
        return "High"
    if priority == 3:
        return "Moderate"
    return "Low"


def label_for(name: str) -> str:
    if name in VITAL_LABELS:
        return VITAL_LABELS[name]
    return REPORT_FLAGS[name][1]


def fuse(vitals: dict, flags: dict) -> dict:
    """One patient representation: vitals plus report flags, in model column order."""
    row = {}
    for v in VITALS:
        if v == "arrival_code":
            mode = vitals.get("arrival_mode", "walk-in")
            row[v] = ARRIVAL_CODES.get(mode, 0)
        else:
            row[v] = float(vitals[v])
    for f in FLAGS:
        row[f] = 1 if flags.get(f) else 0
    return row
