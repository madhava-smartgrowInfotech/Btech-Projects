"""Daily requirements: BMI, BMR (Mifflin-St Jeor), calorie target, macro split and condition limits."""

ACTIVITY_FACTORS = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
GOAL_RATE_KG_WEEK = {"lose": -0.5, "maintain": 0.0, "gain": 0.25}
CALORIE_FLOOR = {"female": 1200, "male": 1500, "other": 1200}
CONDITIONS = ["diabetes", "hypertension", "high_cholesterol"]
DISCLAIMER = ("NutriSense gives general nutrition guidance, not medical advice. If you have diabetes, hypertension, "
              "high cholesterol, kidney disease, are pregnant or take medication, check your plan with a doctor or "
              "registered dietitian before changing your diet.")


def bmr_mifflin(gender: str, weight_kg: float, height_cm: float, age: int) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if gender == "male":
        return base + 5
    if gender == "female":
        return base - 161
    return base - 78  # midpoint of the male and female constants


def bmi_category(bmi: float) -> str:
    # WHO Asia-Pacific cut-offs, recommended for Indian adults
    if bmi < 18.5:
        return "Underweight"
    if bmi < 23:
        return "Normal"
    if bmi < 25:
        return "Overweight"
    return "Obese"


def macro_split(goal: str, conditions: list) -> tuple:
    p, c, f = {"lose": (25, 45, 30), "gain": (20, 50, 30)}.get(goal, (20, 50, 30))
    diabetic = "diabetes" in conditions
    if diabetic:
        c = 40
        p = max(p, 25)
        f = 100 - c - p
    fat_cap = 28 if diabetic else 25  # with diabetes, carbs cannot absorb all of the fat reduction
    if "high_cholesterol" in conditions and f > fat_cap:
        excess = f - fat_cap
        f = fat_cap
        if diabetic:
            p = min(p + excess, 30)
            c = 100 - p - f
        else:
            c += excess
    return p, c, f


def compute_targets(profile) -> dict:
    """profile: object or dict with age, gender, height_cm, weight_kg, activity, goal, conditions, adaptive_adjust."""
    g = profile if isinstance(profile, dict) else profile.__dict__
    age, gender = int(g["age"]), g["gender"]
    h, w = float(g["height_cm"]), float(g["weight_kg"])
    goal = g.get("goal", "maintain")
    conditions = list(g.get("conditions") or [])
    adaptive = float(g.get("adaptive_adjust") or 0.0)

    bmi = w / (h / 100) ** 2
    bmr = bmr_mifflin(gender, w, h, age)
    tdee = bmr * ACTIVITY_FACTORS.get(g.get("activity", "sedentary"), 1.2)
    notes = []
    if goal == "lose":
        goal_adjust = -min(500.0, 0.25 * tdee)
        notes.append(f"Weight loss: {abs(goal_adjust):.0f} kcal/day below maintenance (about 0.5 kg/week).")
    elif goal == "gain":
        goal_adjust = 400.0
        notes.append("Weight gain: 400 kcal/day above maintenance (about 0.25 kg/week).")
    else:
        goal_adjust = 0.0
        notes.append("Maintenance: calories match your estimated daily energy use.")
    if adaptive:
        notes.append(f"Adaptive correction from your weight trend: {adaptive:+.0f} kcal/day.")

    raw = tdee + goal_adjust + adaptive
    floor = CALORIE_FLOOR.get(gender, 1200)
    floor_applied = raw < floor
    if floor_applied:
        notes.append(f"Safety floor applied: target never goes below {floor} kcal/day.")
    kcal = round(max(raw, floor) / 10) * 10

    p_pct, c_pct, f_pct = macro_split(goal, conditions)
    protein_g = kcal * p_pct / 100 / 4
    min_protein = 0.8 * w
    if protein_g < min_protein:
        needed_pct = min(35.0, min_protein * 4 / kcal * 100)
        c_pct -= needed_pct - p_pct
        p_pct = needed_pct
        protein_g = kcal * p_pct / 100 / 4
    carbs_g = kcal * c_pct / 100 / 4
    fat_g = kcal * f_pct / 100 / 9

    diabetic = "diabetes" in conditions
    fibre_g = max(30.0 if diabetic else 25.0, 14 * kcal / 1000)
    sodium_max = 1500 if "hypertension" in conditions else 2300
    sugar_max = kcal * (0.05 if diabetic else 0.10) / 4
    gl_max = round(55 * kcal / 1000) if diabetic else None
    if diabetic:
        notes.append(f"Diabetes: carbs capped at {c_pct:.0f}% of energy, daily glycaemic load <= {gl_max}, free sugar <= {sugar_max:.0f} g.")
    if "hypertension" in conditions:
        notes.append("Hypertension: sodium capped at 1500 mg/day.")
    if "high_cholesterol" in conditions:
        notes.append(f"High cholesterol: fat <= {f_pct:.0f}% of energy; fried and cream/butter-rich dishes excluded.")

    return {
        "bmi": round(bmi, 1),
        "bmi_category": bmi_category(bmi),
        "bmr": round(bmr),
        "tdee": round(tdee),
        "goal_adjust": round(goal_adjust),
        "adaptive_adjust": round(adaptive),
        "kcal": kcal,
        "calorie_floor": floor,
        "floor_applied": floor_applied,
        "macros_pct": {"protein": round(p_pct, 1), "carbs": round(c_pct, 1), "fat": round(f_pct, 1)},
        "protein_g": round(protein_g),
        "carbs_g": round(carbs_g),
        "fat_g": round(fat_g),
        "fibre_g": round(fibre_g),
        "sodium_max_mg": sodium_max,
        "sugar_max_g": round(sugar_max),
        "gl_max": gl_max,
        "exclude_fried_rich": "high_cholesterol" in conditions,
        "goal_rate_kg_week": GOAL_RATE_KG_WEEK.get(goal, 0.0),
        "notes": notes,
        "disclaimer": DISCLAIMER,
    }
