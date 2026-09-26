"""Generate the SeatWise sample dataset and the import templates.

    venv\\Scripts\\python scripts\\generate_sample_data.py            # seed 2026 (the committed data)
    venv\\Scripts\\python scripts\\generate_sample_data.py --seed 7   # a different, equally valid dataset

Writes:
    data/sample/courses.csv, candidates.csv, halls.csv, timetable.csv
    data/sample/seatwise_sample_workbook.xlsx   (all four in one workbook)
    data/templates/*_template.xlsx / *_template.csv and seatwise_import_template.xlsx

Everything is derived from the seed, so the same seed always recreates the
same files. All people in the sample are fictional.
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.importer.spec import KINDS, SPECS  # noqa: E402
from app.services.importer.templates import template_csv, template_xlsx, workbook_xlsx  # noqa: E402

DEPARTMENTS = [
    ("ACF", "Accounting & Finance", ["Principles of Accounting", "Business Mathematics", "Microeconomics",
                                     "Financial Reporting", "Corporate Finance", "Auditing and Assurance", "Taxation"]),
    ("SWE", "Software Engineering", ["Programming Fundamentals", "Discrete Mathematics", "Computer Organisation",
                                     "Algorithms", "Database Systems", "Cloud Platforms", "Mobile Development"]),
    ("DAN", "Data Analytics", ["Statistics I", "Spreadsheet Modelling", "Data Literacy",
                               "Machine Learning Foundations", "Database Systems", "Data Visualisation", "Big Data Tools"]),
    ("MCD", "Mechanical Design", ["Engineering Drawing", "Materials Science", "Statics",
                                  "Thermodynamics", "Machine Design", "CAD and CAM", "Robotics"]),
    ("ELS", "Electrical Systems", ["Circuit Theory", "Electronic Devices", "Applied Mathematics",
                                   "Power Systems", "Control Systems", "Renewable Energy", "Embedded Systems"]),
    ("BMG", "Business Management", ["Principles of Management", "Business Communication", "Organisational Behaviour",
                                    "Marketing Management", "Operations Management", "Human Resource Management",
                                    "Entrepreneurship"]),
    ("HCA", "Healthcare Administration", ["Healthcare Systems", "Medical Terminology", "Health Informatics",
                                          "Hospital Operations", "Health Economics", "Quality and Patient Safety",
                                          "Healthcare Law"]),
]
LEVELS = ["101", "102", "103", "201", "202", "203", "204"]
# Courses that share one question paper (and so must never sit next to each other).
PAPER_GROUPS = {"SWE-202": "DB-COMMON", "DAN-202": "DB-COMMON"}

HALLS = [
    # code, name, building, floor, rows, columns, blocked, accessible, aisles after
    ("MB-G01", "Main Hall A", "Main Building", "Ground", 10, 12, "E6;E7", "A1;A12", "4;8"),
    ("MB-G02", "Main Hall B", "Main Building", "Ground", 10, 10, "", "A1;A10", "5"),
    ("MB-101", "Room 101", "Main Building", "1", 8, 8, "", "", "4"),
    ("MB-102", "Room 102", "Main Building", "1", 8, 8, "C1", "", "4"),
    ("MB-103", "Room 103", "Main Building", "1", 8, 8, "", "", "4"),
    ("MB-104", "Room 104", "Main Building", "1", 8, 8, "", "", "4"),
    ("EW-201", "East Wing 201", "East Wing", "2", 6, 8, "", "", "4"),
    ("EW-202", "East Wing 202", "East Wing", "2", 6, 8, "", "", "4"),
    ("EW-203", "East Wing 203", "East Wing", "2", 6, 8, "F8", "", "4"),
    ("EW-204", "East Wing 204", "East Wing", "2", 6, 8, "", "", "4"),
    ("EW-205", "East Wing Lecture Room", "East Wing", "2", 8, 10, "D5", "A1;A2;A10", "5"),
    ("AX-01", "Annex Room 1", "Annex", "Ground", 6, 6, "", "A1", ""),
    ("AX-02", "Annex Room 2", "Annex", "Ground", 6, 6, "", "", ""),
    ("AX-03", "Annex Studio", "Annex", "Ground", 7, 8, "", "", "4"),
]

FIRST_NAMES = [
    "Aarav", "Abena", "Adele", "Ahmed", "Aiko", "Alejandro", "Amara", "Ananya", "Andrei", "Anika", "Arjun", "Astrid",
    "Ayesha", "Bianca", "Caleb", "Camila", "Chen", "Chloe", "Dara", "David", "Diego", "Divya", "Elena", "Elif", "Emeka",
    "Emma", "Farah", "Felix", "Fatima", "Gabriel", "Hana", "Hannah", "Hiro", "Ibrahim", "Imani", "Irene", "Isaac",
    "Ishaan", "Jae", "Jasmine", "Javier", "Joao", "Julia", "Kavya", "Kofi", "Lara", "Leila", "Leon", "Liam", "Lina",
    "Lucia", "Mateo", "Mei", "Mira", "Mohammed", "Nadia", "Naveen", "Nia", "Noah", "Nora", "Omar", "Oscar", "Paulo",
    "Rahul", "Rania", "Rhea", "Rosa", "Rohan", "Sakura", "Samir", "Sara", "Sebastian", "Sipho", "Sofia", "Tariq",
    "Tessa", "Theo", "Uma", "Victor", "Wei", "Yara", "Yusuf", "Zara", "Zoe",
]
LAST_NAMES = [
    "Abara", "Adeyemi", "Alvarez", "Andersen", "Banerjee", "Barros", "Bauer", "Castillo", "Chandra", "Chowdhury",
    "Costa", "Dimitrov", "Dubois", "Eriksen", "Farouk", "Fischer", "Fonseca", "Gallagher", "Garcia", "Haddad",
    "Hansen", "Hoang", "Ibrahim", "Iyer", "Jansen", "Kamau", "Kaur", "Kim", "Kowalski", "Kumar", "Lambert", "Larsen",
    "Lopez", "Mahmoud", "Marino", "Mehta", "Mensah", "Moreau", "Mwangi", "Nakamura", "Nair", "Novak", "Nwosu",
    "Okafor", "Oliveira", "Osei", "Park", "Patel", "Pereira", "Petrov", "Quinn", "Rao", "Reyes", "Rossi", "Sato",
    "Schmidt", "Sen", "Silva", "Singh", "Sokolov", "Suzuki", "Tanaka", "Torres", "Tran", "Varga", "Verma", "Wagner",
    "Walsh", "Wang", "Yilmaz", "Zhang", "Zhou",
]

SESSION_SLOTS = [("09:30", "12:30"), ("14:00", "17:00")]


def build(seed: int, start: date) -> dict[str, list[dict]]:
    rng = np.random.default_rng(seed)
    courses, candidates, timetable = [], [], []

    for code, name, titles in DEPARTMENTS:
        for level, title in zip(LEVELS, titles):
            courses.append({"course_code": f"{code}-{level}", "course_name": title,
                            "department_code": code, "department_name": name})

    # Six sittings over three days; every department has one exam in every sitting.
    days = [start + timedelta(days=i) for i in range(3)]
    sessions = [(d, s, e) for d in days for s, e in SESSION_SLOTS]
    exam_slots = {"101": 0, "201": 1, "102": 2, "202": 3, "103": 4, "203": 5, "204": 5}
    schedule: dict[str, int] = {}
    for index, (code, _, _) in enumerate(DEPARTMENTS):
        for level, offset in exam_slots.items():
            schedule[f"{code}-{level}"] = (index + offset) % len(sessions)
    schedule["DAN-202"] = schedule["SWE-202"]  # a common paper is written in the same sitting
    for course in courses:
        d, s, e = sessions[schedule[course["course_code"]]]
        timetable.append({"session_date": d.isoformat(), "start_time": s, "end_time": e,
                          "course_code": course["course_code"],
                          "paper_group": PAPER_GROUPS.get(course["course_code"], "")})
    timetable.sort(key=lambda r: (r["session_date"], r["start_time"], r["course_code"]))

    used_names: set[str] = set()
    for code, _, _ in DEPARTMENTS:
        for cohort, levels in (("24", ["201", "202"]), ("25", ["101", "102", "103"])):
            size = int(rng.integers(55, 76))
            serial = 0
            for _ in range(size):
                serial += 1 + int(rng.random() < 0.06)  # occasional gaps: withdrawn roll numbers
                while True:
                    first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
                    if f"{first} {last}" not in used_names:
                        break
                used_names.add(f"{first} {last}")
                picked = [f"{code}-{lv}" for lv in levels]
                if cohort == "24":
                    picked.append(f"{code}-{'203' if rng.random() < 0.55 else '204'}")
                year = (2003 if cohort == "24" else 2004) + int(rng.integers(0, 3))
                born = date(year, 1, 1) + timedelta(days=int(rng.integers(0, 365)))
                candidates.append({
                    "roll_no": f"{code}{cohort}{serial:03d}",
                    "full_name": f"{first} {last}",
                    "department_code": code,
                    "course_codes": ";".join(picked),
                    "needs_accessible_seat": "yes" if rng.random() < 0.012 else "no",
                    "email": f"{first.lower()}.{last.lower()}{serial}@example.com",
                    "date_of_birth": born.isoformat(),
                })

    halls = [{"hall_code": c, "hall_name": n, "building": b, "floor": f, "rows": r, "columns": cols,
              "blocked_seats": bl, "accessible_seats": ac, "aisles_after_columns": ai}
             for c, n, b, f, r, cols, bl, ac, ai in HALLS]
    return {"courses": courses, "candidates": candidates, "halls": halls, "timetable": timetable}


def write_csv(path: Path, kind: str, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[c.name for c in SPECS[kind]], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the SeatWise sample dataset and import templates.")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--start", type=date.fromisoformat, default=date(2026, 10, 12), help="first exam day")
    args = parser.parse_args()

    data = build(args.seed, args.start)
    sample_dir, template_dir = ROOT / "data" / "sample", ROOT / "data" / "templates"
    sample_dir.mkdir(parents=True, exist_ok=True)
    template_dir.mkdir(parents=True, exist_ok=True)

    for kind in KINDS:
        write_csv(sample_dir / f"{kind}.csv", kind, data[kind])
        (template_dir / f"{kind}_template.xlsx").write_bytes(template_xlsx(kind))
        (template_dir / f"{kind}_template.csv").write_bytes(template_csv(kind))
    about = (f"Sample data from the SeatWise seeded generator (scripts/generate_sample_data.py, seed {args.seed}). "
             "All people are fictional.")
    (sample_dir / "seatwise_sample_workbook.xlsx").write_bytes(workbook_xlsx(data, about))
    (template_dir / "seatwise_import_template.xlsx").write_bytes(workbook_xlsx(None))

    sessions = {(r["session_date"], r["start_time"]) for r in data["timetable"]}
    print(f"Seed {args.seed}: {len(data['courses'])} courses, {len(data['candidates'])} candidates, "
          f"{len(data['halls'])} halls, {len(sessions)} sittings")
    print(f"Wrote {sample_dir} and {template_dir}")


if __name__ == "__main__":
    main()
