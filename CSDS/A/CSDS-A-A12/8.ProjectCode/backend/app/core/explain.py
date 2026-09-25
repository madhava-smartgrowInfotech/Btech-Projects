"""Turns a raw model prediction + per-feature contributions into a plain-language
explanation and actionable recommendations.

This is the "advisory" layer of the product: instead of a bare probability, the
grower gets a ranked account of *why* the model reached its conclusion (grounded
in the real per-feature additive contributions XGBoost produces for that exact
sample) plus concrete next steps. Templates are parameterised by the actual
input values and contribution magnitudes so two different samples with the
same verdict still read as distinct, specific writeups.
"""
import numpy as np

from app.core.config import SEED_TYPES

# Agronomic reference ranges used purely to phrase recommendations; these are
# broad, defensible ranges for small millets rather than a single crop's spec.
OPTIMAL = {
    "soil_moisture": (55.0, 75.0, "%"),
    "temperature": (22.0, 32.0, "°C"),
    "humidity": (50.0, 80.0, "%"),
    "rainfall": (20.0, 150.0, "mm"),
    "soil_ph": (5.5, 7.5, ""),
}

FACTOR_GROUPS = {
    "soil_moisture": "Soil Moisture",
    "temperature": "Temperature",
    "humidity": "Humidity",
    "rainfall": "Rainfall",
    "soil_ph": "Soil pH",
}


def _group_contribs(feature_names: list[str], contribs: np.ndarray) -> dict:
    """Aggregate raw per-column contributions into human-meaningful groups."""
    groups = {
        "Soil Moisture": 0.0,
        "Temperature": 0.0,
        "Humidity": 0.0,
        "Rainfall": 0.0,
        "Soil pH": 0.0,
        "Seed Variety": 0.0,
        "Seed Shape": 0.0,
        "Seed Color": 0.0,
        "Visual Pattern Signal": 0.0,
    }
    for name, value in zip(feature_names, contribs[:-1]):  # last entry is bias
        if name in FACTOR_GROUPS:
            groups[FACTOR_GROUPS[name]] += float(value)
        elif name.startswith("seed_type_"):
            groups["Seed Variety"] += float(value)
        elif name in ("seed_area", "seed_perimeter", "seed_aspect_ratio", "seed_circularity"):
            groups["Seed Shape"] += float(value)
        elif name in ("seed_red", "seed_green", "seed_blue", "seed_color_std"):
            groups["Seed Color"] += float(value)
        elif name.startswith("embedding_"):
            groups["Visual Pattern Signal"] += float(value)
    return groups


def _range_phrase(name: str, value: float) -> tuple[str, bool]:
    lo, hi, unit = OPTIMAL[name]
    if value < lo:
        return f"below the favourable range ({lo:.0f}-{hi:.0f}{unit})", False
    if value > hi:
        return f"above the favourable range ({lo:.0f}-{hi:.0f}{unit})", False
    return f"within the favourable range ({lo:.0f}-{hi:.0f}{unit})", True


def _detail_for_factor(factor: str, inputs: dict, morph: dict) -> str:
    if factor == "Soil Moisture":
        phrase, _ = _range_phrase("soil_moisture", inputs["soil_moisture"])
        return f"Recorded soil moisture is {inputs['soil_moisture']:.1f}%, {phrase}."
    if factor == "Temperature":
        phrase, _ = _range_phrase("temperature", inputs["temperature"])
        return f"Ambient temperature is {inputs['temperature']:.1f}°C, {phrase}."
    if factor == "Humidity":
        phrase, _ = _range_phrase("humidity", inputs["humidity"])
        return f"Relative humidity is {inputs['humidity']:.1f}%, {phrase}."
    if factor == "Rainfall":
        phrase, _ = _range_phrase("rainfall", inputs["rainfall"])
        return f"Recent rainfall is {inputs['rainfall']:.1f}mm, {phrase}."
    if factor == "Soil pH":
        phrase, _ = _range_phrase("soil_ph", inputs["soil_ph"])
        return f"Soil pH is {inputs['soil_ph']:.2f}, {phrase}."
    if factor == "Seed Variety":
        return f"{inputs['seed_type']} carries its own baseline germination tendency in the training data."
    if factor == "Seed Shape":
        return (
            f"Segmented seed shows aspect ratio {morph['aspect_ratio']:.2f} and circularity "
            f"{morph['circularity']:.2f}, consistent with {'a well-formed, viable-looking' if morph['circularity'] > 0.6 else 'an irregular or damaged-looking'} grain."
        )
    if factor == "Seed Color":
        r, g, b = morph["mean_color_rgb"]
        return f"Average seed colour reads RGB({r:.0f}, {g:.0f}, {b:.0f}) with colour uniformity std {morph['color_std']:.1f}."
    if factor == "Visual Pattern Signal":
        return "The image encoder detected fine-grained visual patterns in the seed surface texture that correlate with germination outcomes in similar samples."
    return ""


def _recommendation_for(factor: str, inputs: dict) -> str | None:
    if factor == "Soil Moisture":
        lo, hi, unit = OPTIMAL["soil_moisture"]
        v = inputs["soil_moisture"]
        if v < lo:
            return f"Increase irrigation to bring soil moisture up toward {lo:.0f}-{hi:.0f}%; the current level is limiting water uptake."
        if v > hi:
            return f"Improve drainage or reduce irrigation frequency — moisture above {hi:.0f}% raises the risk of seed rot before germination."
    if factor == "Temperature":
        lo, hi, unit = OPTIMAL["temperature"]
        v = inputs["temperature"]
        if v < lo:
            return f"Consider delaying sowing or using row covers until soil temperature rises above {lo:.0f}°C."
        if v > hi:
            return f"Sow during cooler hours or provide partial shading — temperatures above {hi:.0f}°C can stress emerging embryos."
    if factor == "Soil pH":
        lo, hi, unit = OPTIMAL["soil_ph"]
        v = inputs["soil_ph"]
        if v < lo:
            return f"Apply agricultural lime to raise soil pH toward the {lo:.1f}-{hi:.1f} range."
        if v > hi:
            return f"Incorporate organic matter or elemental sulfur to lower soil pH toward the {lo:.1f}-{hi:.1f} range."
    if factor == "Humidity":
        lo, hi, unit = OPTIMAL["humidity"]
        v = inputs["humidity"]
        if v < lo:
            return "Mulch the seedbed to retain surface humidity during the critical germination window."
        if v > hi:
            return "Ensure adequate airflow around the seedbed to limit fungal pressure from excess humidity."
    if factor == "Seed Shape":
        return "Screen the seed batch to remove shrivelled or misshapen grains before sowing — shape irregularity is dragging down this prediction."
    if factor == "Seed Variety":
        return f"Cross-check {inputs['seed_type']}-specific sowing depth and spacing guidance, since variety is a material factor here."
    return None


def generate_explanation(
    feature_names: list[str],
    contribs: np.ndarray,
    probability_germinate: float,
    inputs: dict,
    morph: dict,
) -> dict:
    groups = _group_contribs(feature_names, contribs)
    ranked = sorted(groups.items(), key=lambda kv: abs(kv[1]), reverse=True)
    ranked = [(name, val) for name, val in ranked if abs(val) > 1e-4][:5]

    if not ranked:
        ranked = [("Visual Pattern Signal", 0.0)]

    max_abs = max(abs(v) for _, v in ranked) or 1.0
    key_factors = []
    for name, val in ranked:
        key_factors.append({
            "factor": name,
            "impact": "positive" if val >= 0 else "negative",
            "weight": round(min(abs(val) / max_abs, 1.0), 3),
            "detail": _detail_for_factor(name, inputs, morph),
        })

    verdict = "likely to germinate" if probability_germinate >= 0.5 else "unlikely to germinate under these conditions"
    top_name, top_val = ranked[0]
    driver_phrase = "primarily driven by" if abs(top_val) / max_abs > 0.5 else "influenced most by"

    confidence_pct = round((probability_germinate if probability_germinate >= 0.5 else 1 - probability_germinate) * 100)
    summary = (
        f"This {inputs['seed_type'].lower()} sample is {verdict}, with {confidence_pct}% model confidence, "
        f"{driver_phrase} {top_name.lower()}. "
        f"{_detail_for_factor(top_name, inputs, morph)}"
    )
    if len(ranked) > 1:
        second_name, _ = ranked[1]
        summary += f" {second_name} also contributed to this assessment."

    recommendations = []
    for name, val in ranked:
        if val < 0:
            rec = _recommendation_for(name, inputs)
            if rec and rec not in recommendations:
                recommendations.append(rec)
        if len(recommendations) >= 4:
            break

    if not recommendations:
        recommendations.append(
            f"Conditions are broadly favourable for {inputs['seed_type']} — maintain current soil moisture and temperature through the germination window."
        )
    recommendations.append(
        "Re-test a fresh sample from the same batch after 48 hours if environmental conditions change materially."
    )

    return {
        "summary": summary,
        "key_factors": key_factors,
        "recommendations": recommendations[:4],
    }
