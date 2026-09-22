# CivicPulse - Overview

CivicPulse is decision support for public grievance offices. It reads citizen complaints written in
English, Hindi or Hinglish, suggests a category, the responsible department, a priority and an expected
resolution time, and explains every suggestion. Grievance officers accept or override each suggestion;
their overrides become training data, and the models retrain in one click.

## The problem

- Officers analyse, prioritise and route large volumes of complaints by hand.
- Prioritisation is inconsistent, so urgent civic issues wait.
- Resolution times and staffing are not planned from data.
- Existing tools give no reasons for their suggestions, so officers cannot trust or check them.

## Who uses it

| Role | What they do in CivicPulse |
|---|---|
| Citizen | Files a complaint (text, photo, map pin), gets a tracking ID, follows the status timeline and reads replies. |
| Grievance officer | Works the triage queue, reviews AI suggestions with their explanations, accepts or overrides with a reason, updates status, sends replies, retrains the model. |
| Administrator | Everything an officer can do, plus editing department SLAs. |

Field teams are represented by the officer status updates (In Progress / Resolved); a separate field-staff
app is out of scope for this release.

## Features

| # | Feature | What it does |
|---|---|---|
| F1 | Complaint intake | Web form with free text in any of the three languages, an optional photo and a map location. Issues a tracking ID and a citizen status page with a live timeline. |
| F2 | Classification | 15 categories and 8 departments predicted by TF-IDF + Logistic Regression. Gemini extracts place, issue, affected people, hazards and duration as schema-validated fields. |
| F3 | Priority | Low / Medium / High / Critical from the text, multilingual urgency cues and the category (XGBoost). |
| F4 | Resolution time | Expected days to resolve, learned from ~290k real NYC 311 service requests, with an SLA-breach flag per department. |
| F5 | Explanations | LIME shows the words that drove the category; SHAP shows the factors behind priority and time. |
| F6 | Officer workbench | Accept or override category, department and priority; an override needs a reason and is stored as a new label. One click retrains and shows before / after metrics. |
| F7 | Hotspots & analytics | Ward hotspot map, recurring issues per ward, SLA compliance by department, weekly category trends, AI acceptance rate. Refreshes every 20 seconds. |
| F8 | Draft reply | Gemini drafts a status reply in the citizen's language; the officer edits and sends it. |

## Screens

1. **Landing** - what CivicPulse does, entry points for citizens and officers.
2. **Login** - log in or create a citizen account; demo accounts are one click away.
3. **File a complaint** - text, photo, map pin (or "use my location").
4. **My complaints** - list, tracking-ID search, status timeline and replies.
5. **Triage queue** - complaints ranked by priority, with the AI suggestion, SLA risk and key words.
6. **Complaint detail** - explanations, Gemini fields, accept / override, status updates, reply, retrain.
7. **Hotspots & analytics** - map, recurring issues, SLA table (admins edit SLAs), trends, model performance.

## How officers stay in control

Nothing is routed automatically. A complaint stays in "Awaiting review" until an officer confirms or
changes the suggestion. Every decision is logged (who, when, AI value, officer value, reason), the citizen
only sees a department and expected date after an officer confirms them, and the model only learns from
officer decisions when an officer asks it to retrain.

## Not in this release

- Fine-tuning a multilingual transformer (MuRIL / IndicBERT / XLM-R); the TF-IDF model plus Gemini
  extraction reaches ~83-85% accuracy on all three languages and trains on a laptop CPU.
- A dedicated field-staff app.
- Duplicate-complaint clustering.
