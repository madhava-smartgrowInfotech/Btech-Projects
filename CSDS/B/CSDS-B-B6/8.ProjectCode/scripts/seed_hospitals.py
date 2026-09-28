"""Split Synthea FHIR R4 sample patients across the three simulated hospitals.

Seeded and repeatable. Some people are treated at two or three hospitals: each
hospital gets only the encounters that happened there, gives the person its own
local patient ID, and records the demographics slightly differently (typos,
phone format, dropped middle name) - exactly what a Master Patient Index must untangle.

Outputs:
  data/hospital_a.db, hospital_b.db, hospital_c.db   (git-ignored, rebuilt by setup)
  data/sample/mpi_truth.json                         (ground truth for linkage evaluation)
  data/sample/demo_patients.json                     (records used for demo patient logins)
  data/sample/seed_report.json                       (counts)
"""
import copy
import json
import random
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fhir.resources.R4B import construct_fhir_element  # noqa: E402

from backend.app.config import DATA_DIR, HOSPITALS  # noqa: E402
from hospitals.store import connect, upsert  # noqa: E402

SEED = 42
ZIP_PATH = DATA_DIR / "synthea" / "synthea_sample_data_fhir_latest.zip"
N_PATIENTS = 60
N_IN_THREE = 8
N_IN_TWO = 16
MAX_FILE_BYTES = 12_000_000
MAX_ENCOUNTERS = 30
KEEP_OBS_CATEGORIES = {"laboratory", "vital-signs"}

rng = random.Random(SEED)


def clean_name(s: str) -> str:
    return re.sub(r"\d+", "", s).strip()


def typo(s: str) -> str:
    if len(s) < 4:
        return s
    i = rng.randint(1, len(s) - 2)
    op = rng.choice(["swap", "drop", "double"])
    if op == "swap":
        return s[:i] + s[i + 1] + s[i] + s[i + 2:]
    if op == "drop":
        return s[:i] + s[i + 1:]
    return s[:i] + s[i] + s[i:]


def reformat_phone(p: str) -> str:
    digits = re.sub(r"\D", "", p)
    if len(digits) != 10:
        return p
    return rng.choice([
        f"({digits[:3]}) {digits[3:6]}-{digits[6:]}",
        f"{digits[:3]}.{digits[3:6]}.{digits[6:]}",
        f"+1 {digits[:3]} {digits[3:6]} {digits[6:]}",
    ])


def ref_id(ref: dict | None) -> str | None:
    if not ref or "reference" not in ref:
        return None
    return ref["reference"].split(":")[-1].split("/")[-1]


def obs_category(res: dict) -> str | None:
    for cat in res.get("category", []):
        for c in cat.get("coding", []):
            return c.get("code")
    return None


def is_lab_report(res: dict) -> bool:
    return any(c.get("code") == "LAB" for cat in res.get("category", []) for c in cat.get("coding", []))


def load_candidates():
    z = zipfile.ZipFile(ZIP_PATH)
    names = sorted(n for n in z.namelist()
                   if n.endswith(".json") and "Information" not in n
                   and z.getinfo(n).file_size <= MAX_FILE_BYTES)
    rng.shuffle(names)
    people = []
    for n in names:
        bundle = json.loads(z.read(n))
        by_type = defaultdict(list)
        for e in bundle["entry"]:
            by_type[e["resource"]["resourceType"]].append(e["resource"])
        patient = by_type["Patient"][0]
        if patient.get("deceasedDateTime") or not patient.get("birthDate"):
            continue
        people.append(extract(patient, by_type))
        if len(people) >= N_PATIENTS + 15:
            break
    return people


def extract(patient: dict, by_type: dict) -> dict:
    encounters = sorted(by_type["Encounter"], key=lambda r: r["period"]["start"])[-MAX_ENCOUNTERS:]
    enc_ids = {e["id"] for e in encounters}
    meds = {m["id"]: m for m in by_type.get("Medication", [])}
    keep = []
    for rtype in ("Condition", "MedicationRequest", "Observation", "DiagnosticReport", "AllergyIntolerance"):
        for r in by_type.get(rtype, []):
            enc = ref_id(r.get("encounter"))
            if enc is not None and enc not in enc_ids:
                continue
            if rtype == "Observation" and obs_category(r) not in KEEP_OBS_CATEGORIES:
                continue
            if rtype == "DiagnosticReport" and not is_lab_report(r):
                continue
            if rtype == "MedicationRequest" and "medicationReference" in r:
                med = meds.get(ref_id(r.pop("medicationReference")))
                r["medicationCodeableConcept"] = (med or {}).get("code", {"text": "Medication"})
            keep.append(r)
    has_lipid = any(r["resourceType"] == "Observation" and r["code"]["coding"][0]["code"] == "2093-3" for r in keep)
    age = 2026 - int(patient["birthDate"][:4])
    return {"patient": patient, "encounters": encounters, "resources": keep,
            "has_lipid": has_lipid, "age": age}


def rewrite_refs(obj, id_types: dict, synthea_pid: str, local_pid: str):
    """Turn Synthea urn:uuid references into local relative FHIR references."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "reference" and isinstance(v, str) and v.startswith("urn:uuid:"):
                rid = v.split(":")[-1]
                if rid == synthea_pid:
                    obj[k] = f"Patient/{local_pid}"
                elif rid in id_types:
                    obj[k] = f"{id_types[rid]}/{rid}"
            else:
                rewrite_refs(v, id_types, synthea_pid, local_pid)
    elif isinstance(obj, list):
        for v in obj:
            rewrite_refs(v, id_types, synthea_pid, local_pid)


def local_patient(src: dict, hkey: str, local_id: str, perturb: bool) -> dict:
    name = src["name"][0]
    family = clean_name(name.get("family", ""))
    given = [clean_name(g) for g in name.get("given", [])]
    phone = next((t["value"] for t in src.get("telecom", []) if t.get("system") == "phone"), "")
    birth = src["birthDate"]
    if perturb:
        if rng.random() < 0.45:
            family = typo(family)
        if rng.random() < 0.25 and given:
            given[0] = typo(given[0])
        if len(given) > 1 and rng.random() < 0.4:
            given = given[:1]
        if phone:
            phone = "" if rng.random() < 0.2 else reformat_phone(phone)
        y, m, d = birth.split("-")
        if rng.random() < 0.1 and int(d) <= 12 and d != m:
            birth = f"{y}-{d}-{m}"
    res = copy.deepcopy(src)
    res.pop("text", None)
    res["id"] = local_id
    res["identifier"] = [{
        "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}],
                 "text": "Medical Record Number"},
        "system": f"urn:unihealth:hospital:{hkey}:mrn", "value": local_id}]
    res["name"] = [{"use": "official", "family": family, "given": given}]
    res["telecom"] = [{"system": "phone", "value": phone, "use": "home"}] if phone else []
    res["birthDate"] = birth
    return res


def main():
    for h in HOSPITALS.values():
        if h["db"].exists():
            h["db"].unlink()
    conns = {k: connect(h["db"]) for k, h in HOSPITALS.items()}
    keys = list(HOSPITALS)

    people = load_candidates()
    # Put a well-documented adult first: they become the main demo patient (records in all three hospitals).
    demo_idx = next(i for i, p in enumerate(people) if p["has_lipid"] and 40 <= p["age"] <= 75 and len(p["encounters"]) >= 9)
    people.insert(0, people.pop(demo_idx))
    people = people[:N_PATIENTS]

    truth, demo, used_ids = [], [], set()
    counts, invalid = Counter(), Counter()
    for idx, person in enumerate(people):
        src = person["patient"]
        spid = src["id"]
        if idx < N_IN_THREE:
            order = rng.sample(keys, 3)
        elif idx < N_IN_THREE + N_IN_TWO:
            order = rng.sample(keys, 2)
        else:
            order = [keys[idx % 3]]
        home = order[-1]
        # Split encounters chronologically: the person moved between hospitals over time.
        encs = person["encounters"]
        chunk = max(1, -(-len(encs) // len(order)))
        enc_hosp = {e["id"]: order[min(i // chunk, len(order) - 1)] for i, e in enumerate(encs)}

        local_ids = {}
        for n, hkey in enumerate(order):
            while True:
                lid = f"{HOSPITALS[hkey]['prefix']}-{rng.randint(100000, 999999)}"
                if lid not in used_ids:
                    used_ids.add(lid)
                    break
            local_ids[hkey] = lid
            pres = local_patient(src, hkey, lid, perturb=n > 0)
            upsert(conns[hkey], pres, lid)
            counts[(hkey, "Patient")] += 1
            truth.append({"hospital": hkey, "local_id": lid, "person_key": spid})

        id_types = {r["id"]: r["resourceType"] for r in encs + person["resources"]}
        for r in encs + person["resources"]:
            enc = r["id"] if r["resourceType"] == "Encounter" else ref_id(r.get("encounter"))
            hkey = enc_hosp.get(enc, home)
            res = copy.deepcopy(r)
            res.pop("text", None)
            rewrite_refs(res, id_types, spid, local_ids[hkey])
            try:
                construct_fhir_element(res["resourceType"], res)
            except Exception:
                invalid[res["resourceType"]] += 1
                continue
            upsert(conns[hkey], res, local_ids[hkey])
            counts[(hkey, res["resourceType"])] += 1

        if idx in (0, N_IN_THREE, N_IN_THREE + N_IN_TWO):
            first = order[0]
            demo.append({"username": ["patient", "patient2", "patient3"][len(demo)],
                         "hospital": first, "local_id": local_ids[first],
                         "hospitals": order, "name": f"{clean_name(' '.join(src['name'][0]['given']))} {clean_name(src['name'][0]['family'])}"})

    for c in conns.values():
        c.commit()
        c.close()

    out = DATA_DIR / "sample"
    out.mkdir(parents=True, exist_ok=True)
    (out / "mpi_truth.json").write_text(json.dumps(truth, indent=1))
    (out / "demo_patients.json").write_text(json.dumps(demo, indent=1))
    report = {
        "seed": SEED, "source": ZIP_PATH.name, "patients": len(people),
        "in_three_hospitals": N_IN_THREE, "in_two_hospitals": N_IN_TWO,
        "resources_per_hospital": {k: {t: n for (h, t), n in sorted(counts.items()) if h == k} for k in keys},
        "failed_fhir_validation": dict(invalid),
    }
    (out / "seed_report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    print("demo patients:", json.dumps(demo))


if __name__ == "__main__":
    main()
