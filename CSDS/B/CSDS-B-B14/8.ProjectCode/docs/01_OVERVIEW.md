# AquaVision - Overview

AquaVision is water-utility intelligence without heavy IoT. It predicts water quality and demand, and detects
leaks, distribution imbalances and abnormal consumption on a digital twin of the city distribution network.
It needs only a few low-cost pressure loggers, zone inlet meters and the customer meters a utility already reads.

## The problem

- Water-quality testing is manual, slow and infrequent.
- Leaks and unequal distribution waste water and leave some areas with low pressure.
- Existing ML tools focus only on water-quality prediction.
- Water managers lack integrated, data-driven decision support.

## Who uses it

| Role | What they do in AquaVision |
|---|---|
| Network engineer (`engineer`) | Runs leak scenarios on the twin, reads the ranked suspects, tests rebalancing plans, checks lab samples |
| Distribution / operations manager (`manager`) | Watches NRW, pressure, quality, equity and alerts; reviews forecasts and rebalancing plans (cannot inject leaks) |
| Laboratory staff | Enter lab samples on the water-quality screen (using either account) |

## Features

| # | Feature | What it does |
|---|---|---|
| F1 | Water-quality prediction | Stacking ensemble (Random Forest, XGBoost, Gradient Boosting, Decision Tree -> logistic meta-learner) predicts potable / not potable from 9 parameters, with exact SHAP reasons over the whole ensemble and per-parameter guideline checks (WHO / US EPA) |
| F2 | Network model | A city network simulated with WNTR (EPANET): 48 demand junctions in 5 zones, 85 pipes, a treatment-plant reservoir, a pump and a service tank, with pressure-driven demand and pressure-dependent background leakage. It is shown on a Leaflet map |
| F3 | Demand forecasting | 7-day forecast per zone from consumption history plus live Open-Meteo weather (XGBoost, recursive) |
| F4 | Leak detection | A leak is injected into the twin. A RandomForest decides from logger residuals whether there is a leak, and sensitivity-signature matching ranks the likely pipes |
| F5 | Distribution imbalance | Supply vs demand per zone, pressure adequacy, an equity score and a rebalancing plan that is tested on the twin (what-if) |
| F6 | Abnormal consumption | IsolationForest on per-meter daily features. Flags bursts, continuous night flow and suspected theft |
| F7 | Dashboard | KPIs (NRW, pressure, quality, equity, leaks, meters), the network map, charts and the alert list |
| F8 | Evaluation | Accuracy / F1 / ROC-AUC for quality, MAPE for demand, precision / recall plus top-3 localisation for leaks, and more (see README) |

## Screens

1. Landing
2. Login (engineer, manager)
3. Operations dashboard
4. Water-quality check
5. Network map, including the distribution-imbalance view with what-if
6. Demand forecast
7. Leaks and anomalies

## Why it is low-cost

- 16 pressure loggers and 5 zone inlet meters cover 48 junctions. Leak detection is model-based (twin residuals), not sensor-dense.
- Weather comes from the free Open-Meteo API.
- Everything runs on one CPU machine: SQLite, FastAPI and scikit-learn / XGBoost models that train in under a minute.
