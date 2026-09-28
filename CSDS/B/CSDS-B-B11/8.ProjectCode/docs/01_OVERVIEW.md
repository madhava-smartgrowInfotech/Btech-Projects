# NutriSense - Overview

## The problem
- Generic diet charts ignore individual needs, goals and cuisine.
- Planning balanced meals is hard with a busy lifestyle.
- Most diet apps ignore allergies and medical conditions such as diabetes or hypertension.
- Professional nutrition advice is expensive and hard to access.

## What NutriSense does
NutriSense builds personalised Indian meal plans. Each plan hits your calorie and nutrient targets, respects your allergies, diet and health conditions, and adapts as you make progress.

| # | Feature | What it does |
|---|---|---|
| F1 | Profile and goals | Age, gender, height, weight, activity, diet type (vegetarian / eggetarian / non-vegetarian / vegan), cuisine (North / South / both), allergies (9 types), conditions (diabetes, hypertension, high cholesterol) and goal (lose / maintain / gain). |
| F2 | Requirements | BMI (Asia-Pacific cut-offs), BMR (Mifflin-St Jeor), maintenance calories, daily target, macro split, fibre target, sodium cap, free-sugar cap and glycaemic-load cap. |
| F3 | Meal plan generator | A 7-day plan from a mixed-integer linear programme (PuLP / CBC). It hits calories within +-5 % and meets macro and fibre targets. Allergens are hard-blocked and variety is enforced. Gemini writes recipe steps adapted to your allergies and conditions. |
| F4 | Smart swaps | Swap any dish for a nutritionally similar one. Candidates come from a K-Means-clustered food database, and the portion is re-sized to match calories. |
| F5 | Food logging | Search about 890 Indian dishes, look up raw ingredients in USDA FoodData Central, or log by photo: Gemini identifies the dish and you confirm the match. |
| F6 | Progress tracking | Weight chart, intake-vs-target chart and a 7-day adherence score. The target is recalculated weekly from your real weight trend. |
| F7 | Safety guardrails | Calorie floor (1200 kcal women / 1500 kcal men), deficit at most 25 % of maintenance, condition limits enforced inside the optimiser and re-checked afterwards, AI recipes scanned for allergens, and a clear disclaimer. |

## Who it is for
- People managing weight and everyday health
- People with diabetes, hypertension or high cholesterol
- Families planning meals together (one account per person)

## Screens
1. Landing
2. Login / register
3. Profile wizard (3 steps, then your targets)
4. Dashboard: targets, today's intake, today's plan
5. Weekly plan: day tabs, swap and recipe per dish
6. Food log: dish search, USDA ingredients, photo logging
7. Progress: weight chart, intake vs target, adherence, target history

## Background
NutriSense applies directions highlighted in *Artificial intelligence in personalized nutrition and food manufacturing: a comprehensive review of methods, applications, and future directions* (Frontiers in Nutrition, 2025, doi:10.3389/fnut.2025.1636980):
- constraint optimisation that guarantees nutrient targets
- LLM recipe generation with safety guardrails
- multimodal food-photo recognition
- adaptive plans that recalibrate from progress data
