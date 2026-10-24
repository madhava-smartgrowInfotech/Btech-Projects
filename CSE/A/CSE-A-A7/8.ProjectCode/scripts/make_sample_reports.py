"""Generate SAMPLE scanned reports (synthetic, clearly labelled) into data/sample_reports/.

Eight text PDFs (two pages each) and four image scans (PNG) so both intake paths can be demonstrated.
Each file has an entry in expected.json (flags a correct reading must find) used by scripts/eval_extraction.py.
Seeded and deterministic.
"""
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sample_reports"
SEED = 7307

# name: (page1 lines, page2 lines, expected flags, vitals for the demo form)
CASES = {
    "report_01_chest_pain_stemi": (
        ["Presenting complaint: 58 year old with crushing chest pain radiating to the left arm for 40 minutes.",
         "Associated shortness of breath and sweating. Denies fever.",
         "History: hypertension, type 2 diabetes. Prior stent placed in 2021."],
        ["ECG: ST elevation in leads II, III and aVF.", "Troponin I: 0.62 ng/mL", "Lactate: 2.6 mmol/L",
         "Glucose: 214 mg/dL", "Impression: inferior STEMI."],
        ["chest_pain", "dyspnea", "hypertension", "diabetes", "cardiac_hx", "st_elevation", "lab_troponin_high",
         "lab_lactate_high"],
        dict(age=58, heart_rate=112, sbp=96, dbp=60, spo2=93, temp_c=36.9, resp_rate=22, arrival_mode="ambulance")),
    "report_02_stroke": (
        ["Presenting complaint: 71 year old with sudden left sided weakness and slurred speech since this morning.",
         "Family reports confusion. No chest pain.", "History: hypertension, atrial fibrillation on warfarin."],
        ["CT head: acute intracranial haemorrhage in the right basal ganglia.", "Glucose: 142 mg/dL",
         "Creatinine: 1.1 mg/dL", "Impression: haemorrhagic stroke."],
        ["stroke_signs", "altered_mental", "hypertension", "cardiac_hx", "anticoagulant", "ct_hemorrhage"],
        dict(age=71, heart_rate=88, sbp=196, dbp=108, spo2=96, temp_c=36.7, resp_rate=18, arrival_mode="ambulance")),
    "report_03_pneumonia": (
        ["Presenting complaint: 66 year old with 4 days of fever, productive cough and shortness of breath.",
         "History: COPD, diabetes."],
        ["Chest X-ray: right lower lobe consolidation.", "WBC: 17.8 x10^9/L", "Lactate: 3.1 mmol/L",
         "Glucose: 188 mg/dL", "Impression: community acquired pneumonia."],
        ["fever", "dyspnea", "copd", "diabetes", "infiltrate", "lab_wbc_high", "lab_lactate_high"],
        dict(age=66, heart_rate=118, sbp=104, dbp=64, spo2=89, temp_c=39.1, resp_rate=28, arrival_mode="ambulance")),
    "report_04_fracture": (
        ["Presenting complaint: 34 year old fell from a ladder with right wrist pain and swelling.",
         "No head injury. Denies loss of consciousness. No bleeding."],
        ["X-ray right wrist: distal radius fracture.", "Haemoglobin: 13.8 g/dL", "Impression: closed fracture."],
        ["trauma", "fracture"],
        dict(age=34, heart_rate=84, sbp=128, dbp=80, spo2=99, temp_c=36.6, resp_rate=16, arrival_mode="walk-in")),
    "report_05_abdominal": (
        ["Presenting complaint: 27 year old with right lower quadrant pain and vomiting for 12 hours.",
         "Low grade fever. No history of diabetes."],
        ["WBC: 14.2 x10^9/L", "Creatinine: 0.8 mg/dL", "Impression: probable acute appendicitis."],
        ["abd_pain", "vomiting", "fever", "lab_wbc_high"],
        dict(age=27, heart_rate=96, sbp=122, dbp=78, spo2=98, temp_c=38.0, resp_rate=18, arrival_mode="walk-in")),
    "report_06_trauma_bleeding": (
        ["Presenting complaint: 45 year old road traffic collision, driver, unrestrained.",
         "Abdominal pain and bleeding from scalp laceration. Brief syncope at scene."],
        ["FAST scan: free abdominal fluid in Morison pouch.", "Haemoglobin: 8.4 g/dL", "Lactate: 4.2 mmol/L",
         "Impression: suspected splenic injury."],
        ["trauma", "abd_pain", "bleeding", "syncope", "free_fluid", "lab_hgb_low", "lab_lactate_high"],
        dict(age=45, heart_rate=134, sbp=82, dbp=48, spo2=94, temp_c=36.2, resp_rate=26, arrival_mode="ambulance")),
    "report_07_minor_cold": (
        ["Presenting complaint: 22 year old with sore throat and runny nose for 3 days.",
         "Denies fever, denies shortness of breath. No chest pain. No vomiting."],
        ["WBC: 7.1 x10^9/L", "Impression: viral upper respiratory infection."],
        [],
        dict(age=22, heart_rate=74, sbp=118, dbp=74, spo2=99, temp_c=36.8, resp_rate=15, arrival_mode="walk-in")),
    "report_08_sepsis": (
        ["Presenting complaint: 79 year old with fever, rigors and new confusion for 2 days.",
         "History: diabetes, hypertension. Vomiting since yesterday."],
        ["WBC: 21.4 x10^9/L", "Lactate: 4.8 mmol/L", "Creatinine: 2.4 mg/dL", "Glucose: 296 mg/dL",
         "Impression: sepsis, urinary source."],
        ["fever", "altered_mental", "vomiting", "diabetes", "hypertension", "lab_wbc_high", "lab_lactate_high",
         "lab_creatinine_high", "lab_glucose_abn"],
        dict(age=79, heart_rate=124, sbp=86, dbp=50, spo2=91, temp_c=39.4, resp_rate=27, arrival_mode="transfer")),
    "scan_09_asthma": (
        ["Presenting complaint: 19 year old with wheeze and shortness of breath after exercise.",
         "History: asthma. No fever."],
        ["Chest X-ray: no consolidation.", "WBC: 8.0 x10^9/L"],
        ["dyspnea", "copd"],
        dict(age=19, heart_rate=102, sbp=118, dbp=72, spo2=95, temp_c=36.7, resp_rate=22, arrival_mode="walk-in")),
    "scan_10_headache": (
        ["Presenting complaint: 40 year old with sudden severe headache and vomiting.",
         "Denies trauma. History: hypertension."],
        ["CT head: subarachnoid haemorrhage.", "Glucose: 118 mg/dL", "Impression: subarachnoid haemorrhage."],
        ["severe_headache", "vomiting", "hypertension", "ct_hemorrhage"],
        dict(age=40, heart_rate=92, sbp=178, dbp=104, spo2=97, temp_c=36.8, resp_rate=18, arrival_mode="ambulance")),
    "scan_11_syncope": (
        ["Presenting complaint: 68 year old fainted at home, brief loss of consciousness.",
         "History: coronary artery disease. On clopidogrel. No chest pain."],
        ["Troponin: 0.02 ng/mL", "Haemoglobin: 12.9 g/dL", "Impression: syncope, observe."],
        ["syncope", "cardiac_hx", "anticoagulant"],
        dict(age=68, heart_rate=58, sbp=108, dbp=66, spo2=97, temp_c=36.6, resp_rate=16, arrival_mode="ambulance")),
    "scan_12_sprain": (
        ["Presenting complaint: 29 year old twisted ankle playing football, pain on walking.",
         "No fracture suspected. Denies other injury."],
        ["X-ray ankle: no fracture seen.", "Impression: ankle sprain."],
        ["trauma"],
        dict(age=29, heart_rate=78, sbp=122, dbp=76, spo2=99, temp_c=36.7, resp_rate=15, arrival_mode="walk-in")),
}


def header(name):
    return f"CITY GENERAL EMERGENCY - CLINICAL REPORT (SAMPLE DATA) - {name}"


def make_pdf(name, p1, p2):
    c = canvas.Canvas(str(OUT / f"{name}.pdf"), pagesize=A4)
    for page in (p1, p2):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, 800, header(name))
        c.setFont("Helvetica", 11)
        y = 770
        for line in page:
            words, cur = line.split(), ""
            for w in words:
                if len(cur) + len(w) > 90:
                    c.drawString(40, y, cur)
                    y -= 16
                    cur = w
                else:
                    cur = (cur + " " + w).strip()
            c.drawString(40, y, cur)
            y -= 22
        c.showPage()
    c.save()


def make_png(name, lines, rng):
    img = Image.new("RGB", (1240, 900), (246, 244, 238))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
        small = ImageFont.truetype("arialbd.ttf", 22)
    except OSError:
        font = ImageFont.load_default(size=26)
        small = ImageFont.load_default(size=22)
    d.text((50, 40), header(name), fill=(40, 40, 40), font=small)
    y = 110
    for line in lines:
        words, cur = line.split(), ""
        for w in words:
            if len(cur) + len(w) > 60:
                d.text((50, y), cur, fill=(20, 20, 20), font=font)
                y += 38
                cur = w
            else:
                cur = (cur + " " + w).strip()
        d.text((50, y), cur, fill=(20, 20, 20), font=font)
        y += 50
    img = img.rotate(rng.uniform(-0.6, 0.6), fillcolor=(246, 244, 238)).filter(ImageFilter.GaussianBlur(0.5))
    img.save(OUT / f"{name}.png")


def main():
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    expected = {}
    for name, (p1, p2, flags, vitals) in CASES.items():
        if name.startswith("scan_"):
            make_png(name, p1 + p2, rng)
            expected[f"{name}.png"] = {"flags": flags, "vitals": vitals}
        else:
            make_pdf(name, p1, p2)
            expected[f"{name}.pdf"] = {"flags": flags, "vitals": vitals}
    (OUT / "expected.json").write_text(json.dumps(expected, indent=2))
    print(f"wrote {len(expected)} sample reports to {OUT}")


if __name__ == "__main__":
    main()
