"""Combine the retinal result and the clinical heart risk into one risk stage."""

STAGES = ["Low", "Moderate", "High", "Very high"]

RECOMMENDATIONS = {
    "Low": [
        "Routine fundus screening every 12 months.",
        "Keep blood pressure below 130/80 mmHg with a healthy diet and regular activity.",
    ],
    "Moderate": [
        "Repeat fundus screening in 6 months.",
        "Review blood pressure, lipids and glucose with a physician within 1-3 months.",
        "Lifestyle changes: reduce salt, stop smoking, increase physical activity.",
    ],
    "High": [
        "Refer to an ophthalmologist for a dilated fundus examination within 4 weeks.",
        "Physician or cardiology review within 2-4 weeks: ECG, lipid profile and blood pressure control.",
        "Start or intensify antihypertensive treatment as clinically indicated.",
    ],
    "Very high": [
        "Urgent ophthalmology and cardiology referral (within 1 week).",
        "Check for hypertensive emergency signs (severe headache, visual loss, chest pain).",
        "Close blood-pressure monitoring and treatment review.",
    ],
}


def _points(p: float, cuts: tuple) -> int:
    return sum(p >= c for c in cuts)


def combine(retina_prob: float, heart_prob: float, retina_threshold: float = 0.5, bp: float | None = None) -> dict:
    """Each side scores 0-3 points; the sum maps to a stage (0-1 Low, 2-3 Moderate, 4-5 High, 6 Very high)."""
    r_pts = _points(retina_prob, (0.3, retina_threshold, 0.8))
    h_pts = _points(heart_prob, (0.3, 0.5, 0.75))
    score = r_pts + h_pts
    stage = "Low" if score <= 1 else "Moderate" if score <= 3 else "High" if score <= 5 else "Very high"
    reasons = [
        f"Retinal score {r_pts}/3 (retinopathy probability {retina_prob:.0%}).",
        f"Clinical score {h_pts}/3 (heart-disease probability {heart_prob:.0%}).",
    ]
    if bp is not None and bp >= 180 and STAGES.index(stage) < 2:
        stage = "High"
        reasons.append("Resting blood pressure is 180 mmHg or higher, so the stage is raised to at least High.")
    recs = list(RECOMMENDATIONS[stage])
    if retina_prob >= retina_threshold:
        recs.append("Retinal changes found: repeat imaging at follow-up to track progression.")
    if heart_prob >= 0.5:
        recs.append("Clinical profile suggests raised cardiovascular risk: consider further cardiac work-up as advised by a cardiologist.")
    return {
        "stage": stage,
        "level": STAGES.index(stage),
        "score": score,
        "retina_points": r_pts,
        "heart_points": h_pts,
        "reasons": reasons,
        "recommendations": recs,
    }
