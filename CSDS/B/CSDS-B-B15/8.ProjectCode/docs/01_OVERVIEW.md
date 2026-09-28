# MediQueue - Overview

MediQueue is district-wide outpatient (OP) booking for Hyderabad. It grades how urgent a patient's symptoms are,
suggests the hospitals that can see them, spreads load across the network and shows a live queue position with
an estimated waiting time.

## The problem

- OP registration means long queues and crowded waiting halls.
- Limited daily slots leave many patients without a same-day consultation.
- Critical cases are not prioritised.
- Coordination and referrals between hospitals are slow.

## Who uses it

| User | What they do in MediQueue |
|---|---|
| Patient (phone) | Describe or pick symptoms, see severity and advice, choose a suggested hospital, book a token, watch the live position |
| OP desk staff / doctor | Run today's queue: call next, mark done or no-show, insert emergencies, set daily limits and quotas, refer patients |
| Referral coordinator (receiving hospital) | Accept consented referrals (auto-books a token), mark them completed |
| District health administrator | Watch load, waiting times, severity mix and referrals across all hospitals live |

## Features

| # | Feature | What it does |
|---|---|---|
| F1 | District hospital network | 60 Hyderabad hospitals from OpenStreetMap with specialties, daily OP limits and emergency quotas (seeded, editable in the console) |
| F2 | Patient booking | Symptoms picked or typed (free text mapped by Gemini) -> severity -> 3 ranked hospitals on a map -> token |
| F3 | Severity classification | Mild / moderate / severe / critical from a trained symptom model + symptom severity weights + red-flag rules. Critical -> emergency advice and the emergency quota |
| F4 | Limits, quotas, overflow | Daily OP limits and emergency quotas; an integer programme places each booking on the best day, using predicted no-shows for controlled overbooking and moving to the next day when a day is full |
| F5 | Live queue | Position and estimated wait pushed over WebSockets whenever a patient is called, marked, or an emergency is inserted |
| F6 | Hospital console | Today's queue, call next, done / no-show, add emergency, limits and departments |
| F7 | Referrals | Doctor refers to another hospital; the summary is shared only after patient consent; tracked pending consent -> sent -> accepted -> completed |
| F8 | District dashboard | Load map, per-hospital load and waits, severity mix, next-day moves, referral status - live |

## Objectives and how they are met

| Objective | Where |
|---|---|
| 1. Online OP booking across hospitals in a district | Book a visit screen, `POST /api/bookings` |
| 2. Manage daily OP limits and emergency quotas automatically | `services/scheduling.py` (ILP), console Limits panel |
| 3. Classify disease severity from symptoms using AI | `services/triage.py`, `ml/train_triage.py` |
| 4. Recommend hospitals by severity, location and specialty | `services/recommend.py` |
| 5. Dynamic queue positions and waiting-time estimates | `services/queue.py`, WebSocket `/api/ws/hospital/{id}` |
| 6. Secure inter-hospital referrals and record sharing | `routes/referrals.py`, Referrals screen |

Measured results for each objective are in the README and `experiments/eval/metrics.json`.

## Clinical safety

Every AI output is decision support for a qualified clinician, never a diagnosis. The UI shows a disclaimer next
to severity results and in referral summaries, and critical results always show "call 108 / go to the nearest
emergency department".
