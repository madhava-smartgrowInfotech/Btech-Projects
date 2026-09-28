"""Master Patient Index: probabilistic record linkage across hospitals (IHE PIX/PDQ style).

Each hospital's patients are pulled over FHIR (Patient search). Records from different
hospitals are compared on name, date of birth, gender and phone; pairs above the
threshold are merged (never two records from the same hospital in one person).
"""
import hashlib
import re
from itertools import combinations

from rapidfuzz import fuzz
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..config import HOSPITALS
from ..db import MpiLink, Person
from . import fhir_client

WEIGHTS = {"name": 0.40, "dob": 0.30, "gender": 0.10, "phone": 0.20}
THRESHOLD = 0.80


def record_from_patient(hkey: str, p: dict) -> dict:
    n = (p.get("name") or [{}])[0]
    given = n.get("given", [])
    phone = next((t["value"] for t in p.get("telecom", []) if t.get("system") == "phone"), "")
    return {"hospital": hkey, "local_id": p["id"], "given": given, "family": n.get("family", ""),
            "name": " ".join(given + [n.get("family", "")]).strip(), "birth_date": p.get("birthDate", ""),
            "gender": p.get("gender", ""), "phone": phone}


def phone_digits(p: str) -> str:
    return re.sub(r"\D", "", p)[-10:]


def dob_score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ya, ma, da = a.split("-")
    yb, mb, db_ = b.split("-")
    if ya == yb and ma == db_ and da == mb:  # day/month transposed at data entry
        return 0.8
    if ya == yb and (ma == mb or da == db_):
        return 0.4
    return 0.0


def phone_score(a: str, b: str) -> float:
    a, b = phone_digits(a), phone_digits(b)
    if not a or not b:
        return 0.5  # missing: neither evidence for nor against
    return 1.0 if a == b else fuzz.ratio(a, b) / 100 * 0.5


def name_score(a: dict, b: dict) -> float:
    family = fuzz.ratio(a["family"].lower(), b["family"].lower()) / 100
    first = fuzz.ratio((a["given"] or [""])[0].lower(), (b["given"] or [""])[0].lower()) / 100
    return 0.6 * family + 0.4 * first


def match_score(a: dict, b: dict) -> dict:
    parts = {"name": name_score(a, b), "dob": dob_score(a["birth_date"], b["birth_date"]),
             "gender": 1.0 if a["gender"] == b["gender"] else 0.0, "phone": phone_score(a["phone"], b["phone"])}
    parts["total"] = round(sum(WEIGHTS[k] * parts[k] for k in WEIGHTS), 4)
    return parts


def link_records(records: list[dict], threshold: float = THRESHOLD) -> list[list[tuple[int, float]]]:
    """Cluster records into persons. Returns clusters of (record index, confidence)."""
    pairs = []
    for i, j in combinations(range(len(records)), 2):
        a, b = records[i], records[j]
        if a["hospital"] == b["hospital"] or a["birth_date"][:4] != b["birth_date"][:4]:
            continue  # blocking: other hospital, same birth year
        s = match_score(a, b)["total"]
        if s >= threshold:
            pairs.append((s, i, j))
    parent = list(range(len(records)))
    members = {i: {records[i]["hospital"]} for i in range(len(records))}
    best = {i: 0.0 for i in range(len(records))}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for s, i, j in sorted(pairs, reverse=True):
        ri, rj = find(i), find(j)
        if ri == rj or members[ri] & members[rj]:
            continue  # one person has at most one record per hospital
        parent[rj] = ri
        members[ri] |= members.pop(rj)
        best[i], best[j] = max(best[i], s), max(best[j], s)

    clusters: dict[int, list] = {}
    for i in range(len(records)):
        clusters.setdefault(find(i), []).append(i)
    return [[(i, best[i] if len(c) > 1 else 1.0) for i in c] for c in clusters.values()]


def fetch_all_records() -> tuple[list[dict], list[str]]:
    records, errors = [], []
    for hkey in HOSPITALS:
        try:
            bundle = fhir_client.get(hkey, "/Patient", scope="system/Patient.read", _count=5000)
            records += [record_from_patient(hkey, p) for p in fhir_client.bundle_resources(bundle)]
        except fhir_client.HospitalError as e:
            errors.append(str(e))
    return records, errors


def person_id_for(rec: dict) -> str:
    return "UH-" + hashlib.sha1(f"{rec['hospital']}:{rec['local_id']}".encode()).hexdigest()[:10].upper()


def rebuild(db: Session) -> dict:
    records, errors = fetch_all_records()
    if errors and not records:
        raise fhir_client.HospitalError("; ".join(errors))
    clusters = link_records(records)
    db.execute(delete(MpiLink))
    db.execute(delete(Person))
    for cluster in clusters:
        recs = [records[i] for i, _ in cluster]
        anchor = min(recs, key=lambda r: (r["hospital"], r["local_id"]))  # stable ID across rebuilds
        best = max(recs, key=lambda r: (bool(r["phone"]), len(r["name"])))
        pid = person_id_for(anchor)
        db.add(Person(id=pid, display_name=best["name"], birth_date=best["birth_date"], gender=best["gender"]))
        for i, conf in cluster:
            r = records[i]
            db.add(MpiLink(person_id=pid, hospital_key=r["hospital"], local_id=r["local_id"], name=r["name"],
                           birth_date=r["birth_date"], gender=r["gender"], phone=r["phone"], score=round(conf, 3)))
    db.commit()
    return {"records": len(records), "persons": len(clusters),
            "linked_persons": sum(1 for c in clusters if len(c) > 1), "errors": errors}


def ensure(db: Session) -> None:
    if db.scalar(select(Person.id).limit(1)) is None:
        rebuild(db)


def person_for_local(db: Session, hkey: str, local_id: str) -> str | None:
    ensure(db)
    return db.scalar(select(MpiLink.person_id).where(MpiLink.hospital_key == hkey, MpiLink.local_id == local_id))


def links(db: Session, person_id: str) -> list[MpiLink]:
    return list(db.scalars(select(MpiLink).where(MpiLink.person_id == person_id).order_by(MpiLink.hospital_key)))


def search(db: Session, q: str, birth_date: str = "") -> list[dict]:
    ensure(db)
    out = []
    for p in db.scalars(select(Person)):
        if birth_date and p.birth_date != birth_date:
            continue
        ls = links(db, p.id)
        score = max(fuzz.partial_ratio(q.lower(), l.name.lower()) for l in ls) if q else 100
        if score >= 75:
            out.append({"person_id": p.id, "name": p.display_name, "birth_date": p.birth_date, "gender": p.gender,
                        "match": score, "hospitals": [{"key": l.hospital_key, "name": HOSPITALS[l.hospital_key]["name"],
                                                       "local_id": l.local_id, "confidence": l.score} for l in ls]})
    return sorted(out, key=lambda r: -r["match"])[:25]
