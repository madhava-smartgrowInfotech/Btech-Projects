# NutriSense

Personalised Indian meal plans that hit your calorie and nutrient targets, respect your allergies and health conditions, and adapt as you make progress.

## Features
- **Profile and goals:** age, gender, height, weight, activity, diet type, North/South cuisine, 9 allergens, diabetes / hypertension / high cholesterol, and a lose / maintain / gain goal.
- **Requirements:** BMI (Asia-Pacific cut-offs), BMR (Mifflin-St Jeor), daily calorie target, macro split, fibre target, sodium, sugar and glycaemic-load limits.
- **7-day meal plan:** a linear-programming optimiser (PuLP / CBC) over 890 Indian dishes.
  - Calories within +-5 % and macros and fibre on target every day.
  - Allergens hard-blocked and variety enforced.
  - Gemini writes recipe steps for your allergies and conditions.
- **Smart swaps:** alternatives come from a K-Means-clustered food database, with the portion re-sized to match calories.
- **Food logging:** dish search, USDA FoodData Central ingredient lookup, or a photo: Gemini recognises the dish and you confirm it.
- **Progress:** weight chart, intake-vs-target chart, adherence score and an automatic weekly target recalculation from your real weight trend.
- **Safety guardrails:** calorie floor, condition limits inside the optimiser and re-checked afterwards, AI output scanned for allergens, and a clear disclaimer.

## Quick start (Windows)
1. Install Python 3.11+ and Node.js LTS.
2. Double-click `setup.bat`.
3. Put your Gemini key in `.env` (`GEMINI_API_KEY=...`). Get one at https://aistudio.google.com/apikey.
4. Double-click `run.bat`. The browser opens http://localhost:5211 (API on port 8211).

**Demo login:** `demo@nutrisense.app` / `Demo@1234`. This sample account is a 28-year-old woman, vegetarian, with a peanut allergy and a weight-loss goal, giving a 1650 kcal target.

Full instructions and a demo walkthrough: [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md).

## Evaluation results
Produced by `venv\Scripts\python ml\eval.py` (seeded). Raw numbers are in [experiments/eval/metrics.json](experiments/eval/metrics.json).

| Objective | Metric | Result |
|---|---|---|
| Calculate requirements | BMR vs independent Mifflin-St Jeor (500 random profiles), max error | 0.5 kcal (rounding) |
| | Calorie floor respected | 100 % |
| | Demo profile target | 1650 kcal |
| Generate meal plans | Plans built for 30 random profiles (all diets, allergies and conditions) | 30 / 30 |
| | Days within +-5 % of calorie target (210 days) | **100 %** |
| | Mean / max absolute calorie error | 0.61 % / 3.86 % |
| | Mean absolute error: protein / carbs / fat | 11.5 % / 2.6 % / 3.2 % |
| | Days meeting at least 90 % of the fibre target | 100 % |
| | Different dishes per week | 34.8 |
| | Solve time per week (CPU) | 7.0 s |
| Respect allergies and conditions | Allergen violations | **0** |
| | Diet-type or cholesterol-exclusion violations | 0 |
| | Sodium-cap violations | 0 |
| | Glycaemic-load-cap violations (49 diabetic days) | 0 |
| Smart swaps | Options per swap / unsafe suggestions | 4.8 / 0 |
| | Median calorie difference after portioning | 3.2 % (mean 17.9 %: portions are capped at 0.5-2 servings) |
| | Suggestions from the same K-Means cluster | 63.6 % |
| Swap model | K-Means k / silhouette / Davies-Bouldin | 20 / 0.28 / 1.11 |
| Photo logging | Dish-name matcher on perturbed names, top-1 / top-3 | 95.0 % / 96.0 % |
| Track progress and adapt | Weekly rate error vs goal, simulated users with true needs 85-115 % of estimate | 0.071 kg/wk adaptive vs 0.168 static (**-58 %**) |

Notes:
- Protein error is the largest because many vegetarian Indian dishes are carbohydrate-dense, so protein is optimised but not forced.
- Gemini's visual recognition needs an API key and labelled photos. The table measures the database-matching step that follows it; `scripts/smoke_test.py` exercises the full photo path when a key is set.

## Tech stack
- **Frontend:** React + Vite (JavaScript), Tailwind CSS, react-router-dom, axios, lucide-react
- **Backend:** FastAPI + Uvicorn, SQLAlchemy 2 + SQLite, PyJWT + bcrypt, python-dotenv
- **Intelligence:** PuLP (CBC) optimiser, scikit-learn K-Means, Google Gemini (recipes + photos), USDA FoodData Central

## Project layout
```
backend/app/     main.py, db.py, auth.py, routes/, services/
frontend/src/    pages/, components/, api.js
ml/              build_foods.py, train_swaps.py, eval.py
scripts/         smoke_test.py, download_data.py
data/            raw/ (Kaggle datasets), processed/foods.csv, sample/photos/
models/          swap_kmeans.joblib
experiments/     metrics.json (training), eval/metrics.json (evaluation)
docs/            01_OVERVIEW.md, 02_HOW_IT_WORKS.md, 03_HOW_TO_RUN.md
```

## Documentation
| Document | Contents |
|---|---|
| [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) | Problem, users, features, screens |
| [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) | Architecture, data sources and licences, targets, optimiser, swaps, guardrails, adaptation |
| [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) | Setup, running, demo walkthrough, checks, troubleshooting |
| [docs/PLAN.md](docs/PLAN.md) | Build plan (endpoints, tables, screens) |

## Data and licences
- Indian Food Nutritional Values Dataset (CC BY-SA 4.0)
- South Asian Recipes with Nutrition & Steps (CC BY-SA 4.0)
- Nutritional & Carbon Footprint Data of Indian Diet (CC BY 4.0)
- Sample photos from Wikimedia Commons (CC BY 2.0 / CC BY-SA 3.0)

Details are in [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md).

## Disclaimer
NutriSense gives general nutrition guidance, not medical advice. People with medical conditions, who are pregnant or who take medication should check their plan with a doctor or registered dietitian.
