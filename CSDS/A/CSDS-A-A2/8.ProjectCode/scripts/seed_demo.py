"""
Seed demo accounts so the app can be demonstrated immediately.

    python scripts/seed_demo.py

Creates:
  faculty  → username: faculty@college.edu   password: faculty123
  students → roll numbers of batch A2, password: student123 (faces NOT enrolled -
             each student enrols their own face at registration/first login, or set
             AM_REQUIRE_ENROLLMENT=false to allow check-in without a reference face).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.db import init_db  # noqa: E402
from core import services  # noqa: E402

STUDENTS = [
    ("23K91A6706", "A. Greeshma"),
    ("23K91A6740", "B. Vinay"),
    ("23K91A6757", "G. Sriram"),
    ("24K95A6704", "B. Sai Kumar"),
]


def main() -> None:
    init_db()
    try:
        services.register_user("faculty", "faculty@college.edu", "Project Guide", "faculty123")
        print("created faculty  faculty@college.edu / faculty123")
    except services.ServiceError as exc:
        print("faculty:", exc)
    for roll, name in STUDENTS:
        try:
            services.register_user("student", roll, name, "student123", roll_number=roll)
            print(f"created student  {roll} / student123  ({name})")
        except services.ServiceError as exc:
            print(f"{roll}:", exc)


if __name__ == "__main__":
    main()
