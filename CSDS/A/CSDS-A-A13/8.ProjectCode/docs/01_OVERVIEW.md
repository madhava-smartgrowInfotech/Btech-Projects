# SeatWise - Overview

**SeatWise produces constraint-optimised, cheat-resistant exam seating plans in seconds.**

An exam office uploads its candidates, courses, halls and timetable. For every sitting, SeatWise seats every candidate so that no two neighbours write the same paper, close roll numbers are kept apart and accessible seats go to the people who need them. Among all the plans that satisfy those rules, it picks a random one from a recorded seed. It then prints the seating charts and lists, runs attendance on a tablet at the hall door, and answers every candidate's question: *where do I sit?*

---

## The problem

- Seating plans are usually built by hand or in spreadsheets. That is slow, and mistakes are easy to make.
- Predictable patterns - seating in roll-number order, or simply alternating subjects - put candidates who know each other, or who write the same paper, side by side. That invites malpractice.
- Several rules apply at once: hall capacity, which papers share a sitting, roll-number spacing, departments and accessible seating. Satisfying all of them by hand is hard.
- Candidates and staff have no reliable digital way to find out who sits where.

## Who uses it

| User | What they do in SeatWise |
|---|---|
| **Exam controller / administrator** | Imports data, sets the rules, generates and reviews plans, moves seats, publishes, prints, and follows attendance and analytics. |
| **Invigilator** | Sees the halls they supervise, opens the seat map, marks attendance on a tablet (tap or scan a slip) and submits the register. |
| **Candidate** | Looks up their hall and seat by candidate ID on the public page and downloads a seat slip with a QR code. |

## Features

| # | Feature | What it does |
|---|---|---|
| F1 | **Data import** | Excel/CSV templates for courses, halls (rows x columns, blocked and accessible seats, aisles), candidates and the timetable. Every row is validated - unknown codes, duplicates, bad seat labels, timetable clashes - before anything is saved. |
| F2 | **Constraint-optimised allocation** | OR-Tools CP-SAT: hall capacity, no same-paper neighbours (8 neighbours including diagonals, or 4), roll-number spacing, department mix and accessible seats. |
| F3 | **Randomised, fair plans** | A seeded random choice among valid plans. The seed, rules and fingerprints of the inputs and result are stored, and **Verify** re-runs the engine to prove the plan was not hand-picked. |
| F4 | **Visual hall grid** | A seat map per hall, colour-coded by paper. Drag a candidate (or tap then tap) to move or swap; every target seat shows live whether the move keeps the rules, and why not. |
| F5 | **Outputs** | Seating charts (PDF), hall-wise lists with a roll-order door list (Excel), invigilator sheets (PDF), seat slips with QR codes (PDF) and an attendance report (Excel). |
| F6 | **Hall attendance** | A tablet-first register: tap a seat or a row, scan a slip with a hand-held scanner or camera, mark the rest absent, submit and lock. |
| F7 | **Seat lookup and QR slip** | A public page: enter a candidate ID, see hall, building, seat and a map of where it is, and download a slip whose QR code opens the same page. |
| F8 | **Analytics** | Dashboard and analytics: seats filled, rules met, conflicts avoided compared with roll-order seating, department mix, attendance, solve times, and the engine's benchmark results. |

Also included: a live audit trail, team management (invigilators request accounts, administrators approve them), editable default rules, light and dark themes, and layouts that work from a 360 px phone up to a desktop.

## Rules at a glance (defaults)

| Rule | Default | Type |
|---|---|---|
| Neighbours never write the same paper | 8 neighbours, including diagonals; aisles separate seats | always enforced |
| Roll-number gap between neighbours | 5 (same roll-number prefix) | always enforced |
| Accessible seats | honoured for everyone who needs one; 2 per hall when a hall file lists none | always enforced |
| Subject combinations | no candidate sits two papers in one sitting; courses sharing a question paper count as one paper | checked at import |
| Department mix | spread departments across halls, minimise same-department neighbours | preference |
| Hall usage | fewest halls (compact) or every hall evenly (balanced) | preference |

## How good is it?

On the committed benchmark (8 scenarios x 3 seeds - see [05_MODELS_AND_TRAINING.md](05_MODELS_AND_TRAINING.md)):

- **Every plan met every hard rule.** There were 0 same-paper neighbours in all 24 runs, against 1,253 for roll-order seating in a typical 600-candidate sitting.
- **About 2.4 seconds** for 600 candidates and **4.8 seconds** for 2,000 candidates on a 12-thread desktop.
- **Unpredictable:** the correlation between roll number and seat is 0.06, and only 1% of neighbour pairs repeat when the plan is regenerated with a new seed.

## Where to go next

- Run it: [03_HOW_TO_RUN.md](03_HOW_TO_RUN.md)
- Use it: [07_USER_GUIDE.md](07_USER_GUIDE.md)
- Understand it: [02_ARCHITECTURE.md](02_ARCHITECTURE.md)
