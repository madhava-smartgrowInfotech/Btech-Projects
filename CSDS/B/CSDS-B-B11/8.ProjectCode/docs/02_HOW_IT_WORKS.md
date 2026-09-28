# NutriSense - How It Works

## Architecture

```
React + Vite (port 5211)  --/api proxy-->  FastAPI (port 8211)  -->  SQLite  data/app.db
                                              |-- targets.py     BMI, BMR, target, macros, condition limits
                                              |-- planner.py     PuLP / CBC weekly optimiser + swaps
                                              |-- foods.py       food database, safety filter, search, K-Means features
                                              |-- gemini.py      recipe steps + photo recognition (Gemini)
                                              |-- usda.py        USDA FoodData Central ingredient lookup
                                              |-- guardrails.py  allergen / diet scan of AI output
                                              `-- progress.py    adherence score + adaptive recalculation
```

**Tables:** `users`, `profiles`, `target_history`, `plans` (week stored as JSON), `food_logs`, `weight_logs`, `recipe_cache`.

## Data

| Dataset | Licence | Used for | Committed |
|---|---|---|---|
| [Indian Food Nutritional Values Dataset (2025)](https://www.kaggle.com/datasets/batthulavinay/indian-food-nutrition) | CC BY-SA 4.0 | Per-100 g nutrients (energy, protein, carbs, fat, fibre, free sugar, sodium, calcium, iron) for about 1,000 Indian dishes. This is the source of every nutrient value. | Yes, `data/raw/indian_food_nutrition/` (88 KB) |
| [Nutritional & Carbon Footprint Data of Indian Diet](https://www.kaggle.com/datasets/umangsinghal5/nutritional-and-carbon-footprint-data-of-indian-diet) | CC BY 4.0 | Meal-type, region, veg/non-veg and allergy labels, matched to dishes by name | Yes, `data/raw/indian_diet_carbon/` (181 KB) |
| [South Asian Recipes with Nutrition & Steps](https://www.kaggle.com/datasets/ahsanneural/10k-south-asian-recipes-with-nutrition-and-steps) | CC BY-SA 4.0 | Typical cooking time per dish name (Indian subset) | Yes, `data/raw/south_asian_recipes/` (10 MB) |
| Wikimedia Commons photos | CC BY 2.0 / CC BY-SA 3.0 | Test images for photo logging, see `data/sample/photos/ATTRIBUTION.md` | Yes |

All three datasets are small, so they are committed in full. `scripts/download_data.py` re-downloads them with `kagglehub`.

**Data quality decisions:**
- The South Asian recipes set has ingredient lists and course labels that do not match the dish names (e.g. dal with shrimp, labelled "dessert"). Its nutrition is therefore not used, only median cooking times.
- 115 INDB rows report more than 40 g fat per 100 g for dishes that are not naturally fat-dense (kofta curry, poori, bhatura). They appear to count the whole frying oil, so `ml/build_foods.py` drops them. 890 dishes remain.

### Building the food database (`ml/build_foods.py`)
Each dish gets:
- **Meal role:** breakfast main, drink, staple (roti/rice), curry/dal, one-dish meal (biryani, khichdi), side (raita, salad, soup), snack, dessert or other. Assigned by ordered keyword rules; the carbon dataset's meal type fills gaps.
- **Diet type:** vegetarian, eggetarian or non-vegetarian, plus a vegan flag, from ingredient keywords and carbon labels.
- **Allergens:** peanut, tree nut, dairy, gluten, egg, soy, fish, shellfish, sesame. Keywords are conservative: dishes that usually contain an allergen are flagged, e.g. poha and sabudana for peanut, korma for tree nut. Carbon allergy labels are merged in.
- **Cuisine:** north, south, continental or Indo-Chinese.
- **Glycaemic index class:** food-group estimates from published Indian GI ranges (white rice ~70, chapati ~60, legumes ~32, dairy ~30). Glycaemic load = GI x carbs / 100.
- **Fried / rich flags:** used to exclude dishes for high cholesterol.
- **Default serving size** by role (e.g. curry 150 g, chapati 80 g, drink 200 ml).

The output `data/processed/foods.csv` is committed and fully reproducible.

## F2 - Requirements (`services/targets.py`)
- **BMI** with WHO Asia-Pacific cut-offs (overweight from 23, obese from 25).
- **BMR** (Mifflin-St Jeor): `10 x kg + 6.25 x cm - 5 x age + 5` (men) or `- 161` (women).
- **Maintenance (TDEE)** = BMR x activity factor (1.2 / 1.375 / 1.55 / 1.725 / 1.9).
- **Target** = TDEE + goal adjustment (lose: -500 kcal, capped at 25 % of TDEE; gain: +400 kcal) + adaptive correction. Clamped to the safety floor (1200 kcal women / 1500 kcal men) and rounded to 10 kcal.
- **Macros:** base 20/50/30 % (protein/carbs/fat), 25/45/30 % for weight loss.
  - Diabetes: carbs 40 %.
  - High cholesterol: fat 25 % (28 % if also diabetic).
  - Protein never below 0.8 g/kg.
- **Condition limits:**

| Condition | Sodium | Free sugar | Glycaemic load | Other |
|---|---|---|---|---|
| none | <= 2300 mg | <= 10 % kcal | - | fibre >= 14 g / 1000 kcal (min 25 g) |
| diabetes | - | <= 5 % kcal | <= 55 per 1000 kcal per day | fibre >= 30 g |
| hypertension | <= 1500 mg | - | - | - |
| high cholesterol | - | - | - | fat <= 25 %, no fried or cream/butter-rich dishes |

The demo profile (female, 28 y, 164 cm, 66 kg, moderately active, weight loss) gives BMR 1384, TDEE 2145 and a **1650 kcal** target.

## F3 - Meal plan optimiser (`services/planner.py`)
Each of the 7 days is one mixed-integer linear programme solved with CBC (via PuLP).
1. **Hard safety filter first.** Dishes that clash with the diet type or allergies, or with cholesterol exclusions, are removed before optimisation, so they can never be chosen.
2. **Candidate pools.** Dishes are sampled per meal role (e.g. 45 curries, 40 breakfast mains), weighted towards the preferred cuisine. Variety rule: a dish appears at most twice per week (staples 4 times) and never on consecutive days.
3. **Decision variables.** Binary `y` (dish chosen for a slot) and integer `k` (portion in quarter servings, 0.5 to 2.0 servings when chosen).
4. **Meal structure constraints:**
   - Breakfast: one main, plus an optional drink.
   - Lunch and dinner: a staple with a curry, or a one-dish meal, plus an optional side.
   - Snack: one snack or drink.
   - A dish is used at most once per day.
5. **Hard nutrition constraints:**
   - Calories within +-4 % of target, never below the floor.
   - Meal calorie shares: breakfast 18-32 %, lunch 28-42 %, snack 5-18 %, dinner 22-38 %.
   - Sodium, free sugar and glycaemic load at or below 99 % of their caps (the margin absorbs rounding).
   - Fibre at least 60 % of target.
6. **Objective.** Minimise the weighted relative deviation from calorie, protein, carb and fat targets, plus the fibre shortfall. Small penalties apply to fried or rich dishes and non-preferred cuisine, and a seeded random term varies the week.
7. **Fallback.** If a day is infeasible the pool is enlarged, and the calorie band relaxes to +-5 % and then +-8 %; the day is annotated when that happens. Condition limits are never relaxed.
8. **Post-check.** Every generated day is re-checked (allowed dishes, floor, sodium, glycaemic load) before it is saved.

**Recipes:** Gemini writes ingredients and steps for the exact portion and is told the diet, allergies and condition rules (e.g. at most 1 tsp oil for high cholesterol).
- The answer is scanned for allergen and diet words (`guardrails.py`). On a hit, Gemini is asked once more.
- If the answer is still unsafe, offending lines are removed and a warning is shown.
- Recipes are cached per dish, portion and profile signature.

## F4 - Smart swaps (K-Means)
`ml/train_swaps.py` clusters all dishes on portion-independent nutrient features:
- protein, carb and fat energy shares
- fibre and sugar per 100 kcal
- log sodium per 100 kcal
- log energy density

Features are standardised and k is chosen by silhouette score over k = 6-30 (k = 20 selected). The model is saved to `models/swap_kmeans.joblib`; training metrics are in `experiments/metrics.json`.

For a swap, candidates must have the same meal role, pass the user's safety filter, not already be in that day, and keep the day within its sodium and glycaemic-load caps. They are ranked same-cluster first, then by feature distance. The portion is re-sized to match the original dish's calories (0.5-2 servings).

## F5 - Food logging
- **Dish search:** fuzzy matching (substring, token prefix and similarity ratio) over names and alternate names. Warnings flag dishes that clash with your profile.
- **USDA ingredients:** FoodData Central search (Foundation + SR Legacy). The server re-fetches the item by id when logging, so values are always USDA's per-100 g figures.
- **Photo:** the image goes to Gemini, which returns dish names, confidence and estimated grams. Each name is matched to the food database and you confirm the match (and grams) before anything is logged. Nutrients always come from the database, not from the model.

## F6 - Progress and adaptation (`services/progress.py`)
- **Adherence score (0-100, last 7 days):** for each day, 70 % for calories (full marks within 5 % of target, falling to 0 at 55 % off) plus 30 % for protein reached. Unlogged days score 0.
- **Weekly recalculation:**
  - Runs automatically once at least 4 new weigh-ins spanning 7 days have been logged since the last calculation, or on demand.
  - Fits a least-squares weight trend over the last 14 days and compares it with the planned rate (-0.5 / 0 / +0.25 kg per week).
  - Applies half of the gap as a calorie correction (`-0.5 x gap x 7700 / 7` kcal/day), capped at +-250 kcal per week and +-500 kcal in total.
  - Recomputes BMR from the latest weight and applies the floor again. Every change is stored in `target_history` with its reason.

## F7 - Safety guardrails (summary)
| Guardrail | Where |
|---|---|
| Calorie floor 1200 / 1500 kcal; deficit <= 25 % of TDEE | `targets.py`, optimiser lower bound, post-check |
| Allergens and diet type hard-blocked | `FoodDB.allowed` before optimisation, re-checked after, on swaps and on logging (warnings) |
| Sodium / sugar / glycaemic-load caps | optimiser constraints, post-check, swap filter |
| No fried or rich dishes for high cholesterol | `FoodDB.allowed` |
| AI recipe output scanned for allergens and meat/egg/dairy | `guardrails.py` + one retry + removal with warning |
| Disclaimer | dashboard, plan, profile result, landing page |

## Evaluation (`ml/eval.py`)
Seeded evaluation covering every objective. Results are written to `experiments/eval/metrics.json` and summarised in the README.
