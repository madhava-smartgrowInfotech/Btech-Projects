"""Build the district hospital network from the cached OpenStreetMap hospitals (seeded, deterministic).

Keeps named general/multi-specialty hospitals (drops eye, dental, fertility, ayurveda clinics, etc.),
assigns specialties from OSM tags and the hospital name, and seeds daily OP limits, emergency quotas
and average consultation times. Output: data/hospitals_network.csv (editable later in the app).
"""
import csv
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "hospitals_osm.csv"
OUT = ROOT / "data" / "hospitals_network.csv"
SEED = 2024
TARGET = 60

ALL_SPECS = ["General Medicine", "Pulmonology", "Cardiology", "Neurology", "Gastroenterology", "Hepatology",
             "Endocrinology", "Dermatology", "ENT", "Rheumatology", "Gynecology", "Pediatrics", "Allergy",
             "Vascular Surgery"]
EXCLUDE = re.compile(r"eye|dental|dentist|ivf|fertility|ayurved|homoeo|homeo|unani|veterinar|vision|nethra|"
                     r"netra|laser|sight|physio|diagnostic|clinic|skin|hair|cosmetic|rehab|de-addiction|"
                     r"psychiatr|mental|cancer|oncology|dialysis|blood bank|nature cure|yoga", re.I)
NAME_SPECS = [
    (r"chest|tb |tuberculosis|pulmo|lung", ["Pulmonology"]),
    (r"heart|cardi", ["Cardiology", "Vascular Surgery"]),
    (r"neuro|brain", ["Neurology"]),
    (r"gastro|liver|aig|digestive", ["Gastroenterology", "Hepatology"]),
    (r"\bent\b|e\.n\.t", ["ENT"]),
    (r"ortho|bone|joint|arthri", ["Rheumatology"]),
    (r"maternity|women|mother|gyn", ["Gynecology"]),
    (r"child|kids|paediatric|pediatric|niloufer|rainbow", ["Pediatrics"]),
    (r"diabet|endocrin|thyroid", ["Endocrinology"]),
]
TAG_SPECS = {"pulmo": "Pulmonology", "cardio": "Cardiology", "neuro": "Neurology", "gastro": "Gastroenterology",
             "dermat": "Dermatology", "ent": "ENT", "ortho": "Rheumatology", "gyn": "Gynecology",
             "paediatr": "Pediatrics", "pediatr": "Pediatrics", "endocrin": "Endocrinology",
             "internal medicine": "General Medicine", "general": "General Medicine"}
BIG = re.compile(r"government|govt|general|osmania|gandhi|nims|nizam|apollo|yashoda|kims|care hosp|"
                 r"continental|aig|medicover|sunshine|star hosp|global|century|virinchi|chest", re.I)


def main():
    rng = random.Random(SEED)
    rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
    seen = set()
    for r in rows:
        parts = [x.strip() for x in r["name"].split(";")]
        name = next((x for x in parts if re.search(r"hospital", x, re.I)), parts[0])
        name, _, tail = name.partition(",")
        r["name"] = re.sub(r"\s+", " ", name).strip()
        r["addr"] = r["addr"] or tail.strip()
        key = r["name"].lower()
        r["dup"] = key in seen
        seen.add(key)
    rows = [r for r in rows if not r["dup"]]
    cands = [r for r in rows if re.search(r"hospital|nims|institute of medical", r["name"], re.I)
             and not EXCLUDE.search(r["name"]) and len(r["name"]) > 6]

    def rank(r):
        big = bool(BIG.search(r["name"]))
        return (0 if r["emergency_tag"] == "yes" else 1, 0 if big else 1, 0 if r["speciality_tag"] else 1, r["name"])

    cands.sort(key=rank)
    top = cands[:40]
    rest = cands[40:]
    rng.shuffle(rest)
    chosen = sorted(top + rest[:TARGET - len(top)], key=lambda r: r["name"])

    out = []
    for r in chosen:
        name, tag = r["name"], r["speciality_tag"].lower()
        big = bool(BIG.search(name)) or "multi" in tag or r["emergency_tag"] == "yes"
        specs = {"General Medicine"}
        for pat, ss in NAME_SPECS:
            if re.search(pat, name, re.I):
                specs.update(ss)
        for key, spec in TAG_SPECS.items():
            if key in tag:
                specs.add(spec)
        focused = (len(specs) > 1 and not big) or bool(re.search(r"child|kids|maternity|mother|women", name, re.I))
        if not focused:
            extra = [s for s in ALL_SPECS if s not in specs]
            k = rng.randint(6, 10) if big else rng.randint(1, 3)
            specs.update(rng.sample(extra, min(k, len(extra))))
        ownership = "government" if re.search(r"government|govt|osmania|gandhi|nizam's institute|niloufer|area hospital|chest",
                                               name, re.I) else "private"
        op_limit = rng.randint(120, 250) if big else rng.randint(40, 110)
        out.append({
            "osm_id": r["osm_id"], "name": name, "lat": r["lat"], "lon": r["lon"], "address": r["addr"],
            "ownership": ownership,
            "specialties": ",".join(s for s in ALL_SPECS if s in specs),
            "has_emergency": int(big or r["emergency_tag"] == "yes"),
            "op_limit": op_limit,
            "emergency_quota": max(3, round(op_limit * rng.uniform(0.08, 0.15))),
            "avg_consult_min": round(rng.uniform(3.0, 4.5), 1),
            "op_start": "09:00",
        })
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"saved {len(out)} hospitals -> {OUT}")
    print("with Pulmonology:", sum("Pulmonology" in o["specialties"] for o in out),
          "| with emergency:", sum(o["has_emergency"] for o in out))


if __name__ == "__main__":
    main()
