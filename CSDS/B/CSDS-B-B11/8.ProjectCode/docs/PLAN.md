# NutriSense - Build Plan

**Architecture:** React + Vite SPA (port 5211, proxies `/api`) -> FastAPI (port 8211) -> SQLite (`data/app.db`).
Core services: targets (Mifflin-St Jeor + condition rules), PuLP/CBC meal optimiser, K-Means swap model,
Gemini (recipe steps + photo recognition), USDA FoodData Central (ingredient lookup).

**Food database:** `ml/build_foods.py` turns the Kaggle INDB dish table (per 100 g nutrients) into
`data/processed/foods.csv`, adding meal role, diet type, cuisine, allergens, GI class and fried flag
(keyword rules + labels matched from the Indian-diet carbon dataset). `ml/train_swaps.py` trains
K-Means on nutrient profiles -> `models/swap_kmeans.joblib` + `experiments/metrics.json`.

**Endpoints (`/api`):** auth/register, auth/login, me | profile GET/PUT, targets GET |
plans POST (generate week), plans/latest GET, plans/{id}/swap-options GET, plans/{id}/swap POST |
recipes/{food_id} GET | foods/search, foods/usda GET | logs GET/POST/DELETE, logs/photo POST |
weights POST, progress GET, progress/recalculate POST | health.

**Tables:** users, profiles, plans (JSON week), food_logs, weight_logs, target_history, recipe_cache.

**Screens:** Landing, Login/Register, Profile wizard, Dashboard, Weekly plan (swaps + recipes),
Food log (search / USDA / photo), Progress charts (weight, intake vs target, adherence, target history).

**Guardrails:** calorie floor (F 1200 / M 1500), deficit <= 25% of TDEE, allergens hard-blocked before
optimisation and re-checked after, sodium cap (1500 mg hypertension), glycaemic-load cap (diabetes),
fat cap + no fried/rich dishes (high cholesterol), Gemini output scanned for allergen words, disclaimer.

**Datasets:** INDB Indian Food Nutrition (CC BY-SA 4.0), South Asian Recipes (CC BY-SA 4.0),
Indian Diet Carbon Footprint (CC BY 4.0) - all small, committed under `data/raw/`.

**Tests:** `scripts/smoke_test.py` (full flow on the live API) + `npm run build`; `ml/eval.py` for metrics.
