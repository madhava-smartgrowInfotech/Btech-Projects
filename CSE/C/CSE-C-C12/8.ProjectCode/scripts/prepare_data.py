"""Build normalized knowledge-base CSV/JSON. Tries public dataset, falls back to synthetic."""
import csv, json, re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
PROC = BASE / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

DISEASES = [
 ("Common Cold", ["runny nose","sneezing","sore throat","mild cough","congestion"], "A mild viral infection of the nose and throat.", "Rest, drink fluids, and monitor symptoms. Seek care if symptoms persist beyond 10 days.", "low", "difficulty breathing, high persistent fever"),
 ("Influenza", ["high fever","headache","body pain","fatigue","chills","dry cough"], "A contagious respiratory illness causing fever and body aches.", "Rest, stay hydrated, isolate from others. Seek care for breathing difficulty or dehydration.", "moderate", "difficulty breathing, chest pain, persistent vomiting"),
 ("Migraine", ["headache","nausea","sensitivity to light","visual aura","vomiting"], "A neurological condition causing intense headaches.", "Rest in a dark quiet room. Seek care for sudden severe headache or neurological changes.", "moderate", "sudden severe headache, slurred speech, weakness on one side"),
 ("Gastroenteritis", ["nausea","vomiting","diarrhea","stomach pain","dehydration"], "Inflammation of the stomach and intestines, often from infection.", "Stay hydrated with oral rehydration fluids. Seek care for bloody stools or severe dehydration.", "moderate", "bloody stools, severe dehydration, high fever"),
 ("Urinary Tract Infection", ["burning urination","frequent urination","lower abdominal pain","cloudy urine"], "A bacterial infection of the urinary system.", "Drink water and consult a clinician promptly for testing.", "moderate", "fever with back pain, vomiting, blood in urine"),
 ("Pneumonia", ["cough with phlegm","fever","chills","shortness of breath","chest pain"], "Infection inflaming air sacs in the lungs.", "Seek professional care promptly, especially with breathing difficulty.", "high", "difficulty breathing, severe chest pain, bluish lips"),
 ("Asthma", ["wheezing","shortness of breath","chest tightness","coughing at night"], "A chronic condition narrowing airways.", "Follow prescribed action plan. Seek urgent care for severe breathlessness.", "moderate", "severe breathlessness, difficulty speaking, blue lips"),
 ("Allergic Rhinitis", ["sneezing","itchy eyes","runny nose","nasal congestion"], "Allergic response to airborne particles.", "Avoid known triggers. Consult a clinician for persistent symptoms.", "low", "severe breathing difficulty, facial swelling"),
 ("Anaphylaxis", ["swelling of lips","throat closing","difficulty breathing","hives","dizziness"], "A severe life-threatening allergic reaction.", "This is an emergency. Call emergency services immediately.", "emergency", "throat closing, difficulty breathing, collapse"),
 ("COVID-19", ["fever","dry cough","fatigue","loss of taste","loss of smell","shortness of breath"], "A contagious respiratory disease.", "Isolate, rest, monitor oxygen/breathing. Seek care for breathing difficulty.", "moderate", "difficulty breathing, persistent chest pain, confusion"),
 ("Dengue", ["high fever","severe headache","pain behind eyes","joint pain","rash","bleeding gums"], "A mosquito-borne viral infection.", "Seek medical evaluation promptly. Avoid self-medicating with certain painkillers.", "high", "severe abdominal pain, persistent vomiting, bleeding"),
 ("Malaria", ["fever with chills","sweating","headache","nausea","shivering"], "A mosquito-borne parasitic disease.", "Seek prompt testing and treatment from a clinician.", "high", "confusion, seizures, severe vomiting"),
 ("Typhoid", ["prolonged fever","headache","abdominal pain","weakness","loss of appetite"], "A bacterial infection spread through contaminated food/water.", "Seek medical testing. Maintain hydration and hygiene.", "high", "severe abdominal pain, persistent vomiting, bloody stools"),
 ("Chickenpox", ["itchy rash","blisters","fever","fatigue"], "A contagious viral infection causing itchy rash.", "Avoid scratching, stay isolated. Consult clinician, especially for adults/pregnancy.", "moderate", "difficulty breathing, infected blisters, high fever"),
 ("Measles", ["high fever","rash","cough","red eyes","white spots in mouth"], "A highly contagious viral disease.", "Seek medical care; isolate. Urgent care for breathing difficulty.", "high", "difficulty breathing, dehydration, seizures"),
 ("Bronchitis", ["persistent cough","mucus","fatigue","mild fever","chest discomfort"], "Inflammation of bronchial tubes.", "Rest and fluids. Seek care for prolonged cough or breathing difficulty.", "moderate", "shortness of breath, high fever, bloody mucus"),
 ("Sinusitis", ["facial pain","nasal congestion","headache","loss of smell","thick nasal discharge"], "Inflammation of sinuses.", "Steam inhalation and fluids. Consult clinician if lasting over 10 days.", "low", "severe headache, vision changes, high fever"),
 ("Gastritis", ["upper abdominal pain","nausea","bloating","indigestion"], "Inflammation of stomach lining.", "Avoid irritants like alcohol. Consult clinician for persistent pain.", "moderate", "vomiting blood, black stools, severe pain"),
 ("Appendicitis", ["severe abdominal pain","pain in lower right abdomen","nausea","fever","loss of appetite"], "Inflammation of the appendix.", "Seek urgent medical evaluation immediately.", "emergency", "severe worsening abdominal pain, rigid abdomen, high fever"),
 ("Stroke", ["sudden numbness","face droop","slurred speech","confusion","severe headache"], "A medical emergency from interrupted blood supply to the brain.", "Call emergency services immediately.", "emergency", "any sudden neurological symptom"),
 ("Heart Attack", ["severe chest pain","pressure in chest","pain in left arm","shortness of breath","cold sweat"], "Blocked blood flow to the heart muscle.", "Call emergency services immediately.", "emergency", "chest pain, breathlessness, collapse"),
 ("Depression", ["persistent sadness","loss of interest","fatigue","sleep changes","appetite changes"], "A mood disorder affecting daily life.", "Consider speaking with a mental-health professional or trusted clinician.", "moderate", "thoughts of self-harm"),
 ("Anxiety", ["excessive worry","restlessness","rapid heartbeat","sweating","trouble sleeping"], "Excessive fear or worry affecting wellbeing.", "Stress management and professional support can help.", "low", "panic with chest pain, thoughts of self-harm"),
 ("Diabetes", ["increased thirst","frequent urination","fatigue","blurred vision","slow healing"], "A condition of high blood sugar.", "Seek clinical testing for confirmation and management.", "moderate", "fruity breath, confusion, severe dehydration"),
 ("Hypertension", ["headache","shortness of breath","nosebleeds","dizziness"], "Persistently high blood pressure, often without symptoms.", "Requires clinical measurement. Seek urgent care for severe symptoms.", "moderate", "severe chest pain, severe headache, vision problems"),
 ("Anemia", ["fatigue","pale skin","dizziness","shortness of breath","cold hands"], "Low healthy red blood cells.", "Seek clinical testing. Maintain balanced nutrition.", "moderate", "chest pain, fainting, severe fatigue"),
 ("Eczema", ["itchy skin","red patches","dry skin","rash"], "Inflammatory skin condition.", "Moisturize, avoid triggers. Consult clinician for infected skin.", "low", "spreading infection, severe pain, fever"),
 ("Food Poisoning", ["vomiting","diarrhea","stomach cramps","nausea","fever"], "Illness from contaminated food.", "Stay hydrated. Seek care for bloody stools or dehydration.", "moderate", "bloody stools, severe dehydration, high fever"),
 ("Conjunctivitis", ["red eyes","itchy eyes","watery discharge","gritty feeling"], "Inflammation of the eye membrane.", "Avoid touching eyes. Consult clinician if vision changes.", "low", "vision loss, severe eye pain"),
 ("Ear Infection", ["ear pain","hearing difficulty","fever","drainage from ear"], "Infection of middle or outer ear.", "Consult a clinician for proper examination.", "moderate", "severe pain, high fever, swelling behind ear"),
]

def normalize_symptoms(symptoms: list[str]) -> str:
    normed = [re.sub(r"\s+", " ", s.strip().lower()) for s in symptoms]
    seen, out = set(), []
    for s in normed:
        if s and s not in seen:
            seen.add(s); out.append(s)
    return ", ".join(out)

def build_synthetic() -> list[dict]:
    records = []
    rid = 1
    import random
    random.seed(42)
    for disease, syms, desc, guide, sev, flags in DISEASES:
        base = normalize_symptoms(syms)
        # 6 variations per disease for retrieval depth
        for v in range(6):
            extra = random.sample(syms, k=min(len(syms), 3 + (v % 3)))
            var_syms = normalize_symptoms(extra + ([random.choice(syms)] if v % 2 else []))
            records.append({
                "record_id": f"REC-{rid:04d}",
                "disease": disease,
                "symptoms": var_syms or base,
                "description": desc,
                "guidance": guide,
                "severity": sev,
                "red_flags": flags,
                "source": "CareLens AI curated local knowledge (synthetic fallback)",
                "source_type": "synthetic",
                "retrieval_text": f"Disease: {disease}. Symptoms: {var_syms or base}. Description: {desc} Guidance: {guide}",
            })
            rid += 1
    # dedupe
    seen, final = set(), []
    for r in records:
        key = (r["disease"], r["symptoms"])
        if key in seen: continue
        seen.add(key); final.append(r)
    return final

def main():
    records = build_synthetic()
    # validate
    assert all(r.get("disease") and r.get("symptoms") and r.get("retrieval_text") for r in records)
    PROC.mkdir(parents=True, exist_ok=True)
    (PROC / "knowledge_base.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    with open(PROC / "knowledge_base.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["record_id","disease","symptoms","description","guidance","severity","red_flags","source","source_type","retrieval_text"])
        w.writeheader(); w.writerows(records)
    print(f"Wrote {len(records)} records (synthetic fallback) to data/processed/")

if __name__ == "__main__":
    main()
