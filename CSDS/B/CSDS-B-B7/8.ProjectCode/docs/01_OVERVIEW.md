# HospiSense - Overview

HospiSense predicts how long each patient will stay, forecasts bed and ICU occupancy for the next 14 days, and recommends how to
allocate beds, nurses and equipment - with the reasons behind every number.

## The problem

- Hospitals cannot reliably forecast admissions, length of stay and resource demand.
- Overcrowding and shortages of beds, staff and equipment delay patient care.
- Decisions are made under time pressure with incomplete information.
- Existing predictions rarely explain themselves or turn into concrete actions.

## Who uses it

| User | Uses HospiSense to |
|---|---|
| Hospital administrators and bed managers | watch occupancy and ICU warnings, run the optimiser, accept or edit plans |
| Doctors and nurse managers | record admissions, see predicted stay and its drivers, check staffing per shift |
| Operations planners | review 14-day forecasts, staff and equipment demand, and measured model accuracy |

Two roles are built in: **admin** (everything) and **doctor** (admissions, forecasts, plans read-only, performance).

## Features

| # | Feature | What it does |
|---|---|---|
| F1 | Length-of-stay prediction | Expected days, an 80% range and a short/long-stay class (long = over 5 days) at admission, with SHAP reasons in days. |
| F2 | Occupancy forecast | Census per facility and ward for the next 14 days from current patients' predicted stays plus forecast admissions, with a 90% band. |
| F3 | ICU demand forecast | Expected ICU beds per facility; an early warning on the first day demand can pass ICU capacity. |
| F4 | Staff and equipment demand | Nurses needed per shift at safe ratios, and ventilators, cardiac monitors, infusion pumps and dialysis machines, against what is rostered or in stock. |
| F5 | Allocation recommendations | OR-Tools integer programmes recommend bed conversions, admission diversions, nurse floats, extra shifts and equipment transfers, each with a reason and an overall trade-off summary. |
| F6 | Decision dashboard | KPIs, alerts and forecasts; administrators accept a plan as is or edit quantities first, and accepted plans update capacity, rosters and stock. |
| F7 | Evaluation | LOS MAE/R2, forecast error against naive baselines, ICU alert recall, and resource shortfall versus the static allocation. |

## Screens

1. **Landing** - what the product does.
2. **Login** - admin and doctor accounts.
3. **Dashboard** - occupancy, ICU, 7-day peak, admissions forecast, alerts, facility table, latest plan.
4. **Admissions and predictions** - admission form (or a sample record from the dataset), prediction with SHAP bars, list of admissions.
5. **Occupancy and ICU forecasts** - ward charts per facility, ICU charts for all facilities, staff and equipment tables.
6. **Allocation recommendations** - run the optimiser, review actions and reasons, edit quantities, accept.
7. **Model performance** - held-out evaluation results.

## Default hospital structure

- 5 facilities (A-E, from the source data) with 5 wards each: General, Surgical, Maternity, Paediatric, ICU.
- Nurse-to-patient ratios (day / evening / night): General 1:6/1:6/1:8, Surgical 1:5/1:5/1:7, Maternity and
  Paediatric 1:4/1:4/1:5, ICU 1:2 on every shift.
- Bed capacity per ward = 90th percentile of its daily census over the history; nurse rosters = the average census of the
  last 90 days; equipment stock = the average 90-day demand + 15%. This is the "current (static) allocation" that the
  optimiser is compared with.

## Clinical safety

Every prediction and recommendation is decision support for qualified staff. It supports, and does not replace, their
judgement; the admission screen and the allocation screen both say so.
