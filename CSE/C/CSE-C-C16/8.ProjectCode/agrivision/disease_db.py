"""AgriVision disease knowledge base — 38 PlantVillage / PD36-C classes."""
from __future__ import annotations

# Canonical 38 classes (PD36-C / PlantVillage)
CLASSES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]

def display_name(cls: str) -> str:
    crop, _, disease = cls.partition("___")
    crop = crop.replace("_", " ").replace("(including sour)", "").strip()
    crop = " ".join(w.capitalize() for w in crop.split())
    crop = crop.replace("Maize", "(Maize)").replace("Corn (Maize)", "Corn (Maize)")
    d = disease.replace("_", " ").strip()
    return f"{crop} — {d}"


def _crop_of(cls: str) -> str:
    return cls.split("___")[0].replace("_", " ").replace("(including sour)", "").strip().lower().replace("  ", " ")

# Curated detail overrides for the most agronomically important diseases.
_OVERRIDES: dict[str, dict] = {
    "Apple___Apple_scab": dict(severity="high", symptoms="Olive-green to black velvety spots on leaves and fruit; leaf yellowing and premature drop.",
        treatment_chemical="Mancozeb 75% WP @ 2.5 g/L or Captan 50% WP @ 2 g/L, 2–3 sprays at 12-day intervals.",
        prevention="Prune for airflow, remove fallen leaves, plant resistant varieties."),
    "Apple___Black_rot": dict(severity="high", symptoms="Purple leaf spots expanding with tan centres ('frog-eye'); fruit rot with black pycnidia rings.",
        treatment_chemical="Carbendazim 50% WP @ 1 g/L + pruning of cankers; Captan cover sprays.",
        prevention="Remove mummified fruit and cankers; avoid overhead irrigation."),
    "Apple___Cedar_apple_rust": dict(severity="medium", symptoms="Bright orange-yellow leaf spots; tube-like horns beneath leaf in humid weather.",
        treatment_chemical="Myclobutanil 10% WP @ 0.5 g/L at pink-bud stage.",
        prevention="Remove nearby juniper/cedar hosts; resistant cultivars."),
    "Corn_(maize)___Common_rust_": dict(severity="medium", symptoms="Small cinnamon-brown powdery pustules scattered on both leaf surfaces.",
        treatment_chemical="Propiconazole 25% EC @ 1 ml/L at first pustule appearance.",
        prevention="Early sowing, balanced N, tolerant hybrids."),
    "Corn_(maize)___Northern_Leaf_Blight": dict(severity="high", symptoms="Long cigar-shaped grey-green lesions turning tan, 3–15 cm, along midrib.",
        treatment_chemical="Azoxystrobin 23% SC @ 1 ml/L; Mancozeb @ 2.5 g/L.",
        prevention="Crop rotation, residue burial, resistant hybrids."),
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": dict(severity="high", symptoms="Rectangular grey lesions confined by veins; coalesce in heavy dew.",
        treatment_chemical="Pyraclostrobin + Epoxiconazole @ 1 ml/L.",
        prevention="Residue management, wider spacing, tolerant hybrids."),
    "Grape___Esca_(Black_Measles)": dict(severity="high", symptoms="Interveinal 'tiger-stripe' necrosis on leaves; black measle spots on berries; wood canker.",
        treatment_chemical="No cure — prune and protect wounds with Trichoderma / thiophanate paste.",
        prevention="Sanitary pruning, avoid vine stress, replant with clean grafts."),
    "Grape___Black_rot": dict(severity="high", symptoms="Circular brown leaf spots with black margins; berries mummify into black shrivelled clusters.",
        treatment_chemical="Mancozeb @ 2.5 g/L at bloom; Myclobutanil @ 0.5 g/L.",
        prevention="Remove mummies, canopy thinning, weed control."),
    "Orange___Haunglongbing_(Citrus_greening)": dict(severity="high", symptoms="Asymmetric blotchy mottle on leaves, yellow shoots, lopsided bitter fruit; spread by psyllids.",
        treatment_chemical="No cure — control psyllid with Imidacloprid/Dimethoate; remove infected trees.",
        prevention="Certified nursery stock, psyllid scouting, reflective mulch."),
    "Potato___Early_blight": dict(severity="high", symptoms="Concentric 'target-board' brown rings on older leaves; stem collar lesions.",
        treatment_chemical="Chlorothalonil 75% WP @ 2 g/L or Azoxystrobin @ 1 ml/L, alternate sprays.",
        prevention="Rotation with non-solanaceous crops, drip irrigation, destroy debris."),
    "Potato___Late_blight": dict(severity="high", symptoms="Water-soaked pale spots with white downy mildew beneath; rapid whole-field blighting in cool wet weather.",
        treatment_chemical="Metalaxyl + Mancozeb (Ridomil Gold) @ 2.5 g/L immediately; repeat at 7 days.",
        prevention="Certified seed, earthing-up, avoid overhead watering, forecast sprays."),
    "Tomato___Early_blight": dict(severity="high", symptoms="Target-like concentric rings on lower leaves, stem lesions, fruit rot at stem end.",
        treatment_chemical="Mancozeb @ 2.5 g/L alternate with Azoxystrobin @ 1 ml/L.",
        prevention="Mulching, staking, drip irrigation, remove lower leaves."),
    "Tomato___Late_blight": dict(severity="high", symptoms="Greasy water-soaked patches, white mould under leaf; brown firm fruit lesions.",
        treatment_chemical="Copper oxychloride @ 3 g/L + Metalaxyl mix; urgent action in wet season.",
        prevention="Resistant varieties (Arka Rakshak), spacing, avoid wet foliage."),
    "Tomato___Bacterial_spot": dict(severity="medium", symptoms="Small dark water-soaked leaf spots turning scabby; raised corky fruit spots.",
        treatment_chemical="Copper hydroxide @ 2 g/L + Streptocycline 0.15 g/L.",
        prevention="Seed treatment, drip irrigation, field sanitation."),
    "Tomato___Septoria_leaf_spot": dict(severity="medium", symptoms="Many small circular spots with grey centres and dark borders on lower leaves.",
        treatment_chemical="Chlorothalonil @ 2 g/L; Difenoconazole @ 0.5 ml/L.",
        prevention="Mulch, rotation, remove affected leaves first."),
    "Tomato___Leaf_Mold": dict(severity="medium", symptoms="Pale green-yellow blotches above; olive-green velvety mould below in humid polyhouse.",
        treatment_chemical="Azoxystrobin @ 1 ml/L; ventilate polyhouse.",
        prevention="Ventilation, spacing, resistant hybrids."),
    "Tomato___Spider_mites Two-spotted_spider_mite": dict(severity="medium", symptoms="Fine stippling/bronzing, webbing under leaves, leaf drying from edges.",
        treatment_chemical="Abamectin 1.9% EC @ 0.5 ml/L or Diafenthiuron; spray undersides.",
        prevention="Avoid dusty drought stress, conserve predatory mites, overhead wash."),
    "Tomato___Target_Spot": dict(severity="medium", symptoms="Bullseye lesions with concentric rings on leaves, stems and fruit shoulders.",
        treatment_chemical="Fluxapyroxad + Pyraclostrobin @ 1 ml/L.",
        prevention="Rotation, staking, residue removal."),
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": dict(severity="high", symptoms="Upward leaf curl, yellowing margins, stunting, flower drop; spread by whitefly.",
        treatment_chemical="No cure — whitefly control (Diafenthiuron/Imidacloprid) + uproot infected plants.",
        prevention="Yellow sticky traps, silver mulch, nylon nets, resistant hybrids."),
    "Tomato___Tomato_mosaic_virus": dict(severity="medium", symptoms="Mottled light/dark green mosaic, leaf distortion, reduced fruit set; seed & sap spread.",
        treatment_chemical="No cure — rogue infected plants, disinfect tools with 10% bleach.",
        prevention="Certified seed, no tobacco near field, tool sanitation."),
    "Pepper,_bell___Bacterial_spot": dict(severity="medium", symptoms="Angular water-soaked leaf spots turning brown; raised scabby fruit lesions.",
        treatment_chemical="Copper oxychloride @ 3 g/L + Streptocycline.",
        prevention="Seed treatment, crop rotation, drip irrigation."),
    "Peach___Bacterial_spot": dict(severity="medium", symptoms="Angular leaf spots with yellow halos, shot-holing; pitted fruit spots cracking open.",
        treatment_chemical="Copper sprays at leaf-fall; Oxytetracycline during bloom.",
        prevention="Resistant varieties, avoid overhead irrigation, orchard sanitation."),
    "Squash___Powdery_mildew": dict(severity="medium", symptoms="White powdery patches on upper leaves spreading to full coating; premature senescence.",
        treatment_chemical="Wettable sulphur @ 2.5 g/L or Myclobutanil @ 0.5 g/L; neem oil preventive.",
        prevention="Wide spacing, morning irrigation, resistant varieties."),
    "Strawberry___Leaf_scorch": dict(severity="medium", symptoms="Purple-red blotches coalescing to scorch leaf margins; weak fruiting.",
        treatment_chemical="Captan @ 2 g/L; remove scorched leaves.",
        prevention="Clean planting material, mulch, avoid overhead watering."),
    "Cherry_(including_sour)___Powdery_mildew": dict(severity="medium", symptoms="White powdery coating on young leaves and shoots; leaf curl and distortion.",
        treatment_chemical="Sulphur @ 2 g/L or Hexaconazole @ 1 ml/L.",
        prevention="Prune for airflow, remove infected shoots."),
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": dict(severity="medium", symptoms="Reddish-brown angular spots with dark borders; heavy defoliation in wet years.",
        treatment_chemical="Mancozeb @ 2.5 g/L; Copper oxychloride rotation.",
        prevention="Canopy management, leaf-litter removal."),
}

_GENERIC_TREATMENTS = {
    "healthy": (
        "No treatment needed — crop is healthy. Continue balanced nutrition and scouting every 7 days.",
        "Maintain schedule: neem oil 5 ml/L preventive every 15 days; ensure drainage and airflow.",
    ),
    "fungal": (
        "Mancozeb 75% WP @ 2.5 g/L or Copper oxychloride @ 3 g/L, 2 sprays 10 days apart.",
        "Neem oil 5 ml/L + Trichoderma viride soil application @ 2.5 kg/ha with FYM.",
    ),
    "bacterial": (
        "Copper hydroxide @ 2 g/L + Streptocycline 0.15 g/L; repeat after 10 days.",
        "Hot-water seed treatment, field sanitation, avoid working in wet fields.",
    ),
    "viral": (
        "No direct cure — remove and destroy infected plants; control vectors (whitefly/aphids) with Imidacloprid @ 0.5 ml/L.",
        "Yellow sticky traps, reflective mulch, certified virus-free seedlings, barrier crops.",
    ),
    "pest": (
        "Abamectin 1.9% EC @ 0.5 ml/L targeting leaf undersides; repeat after 7 days.",
        "Neem seed kernel extract 5%, conserve natural predators, overhead water wash.",
    ),
}

def _kind_of(cls: str) -> str:
    c = cls.lower()
    if "healthy" in c:
        return "healthy"
    if any(k in c for k in ("mosaic", "curl_virus", "greening", "haunglongbing")):
        return "viral"
    if "bacterial" in c:
        return "bacterial"
    if "mite" in c:
        return "pest"
    if any(k in c for k in ("mildew", "mold", "rust", "scab", "blight", "spot", "rot", "esca", "scorch")):
        return "fungal"
    return "fungal"

def get_disease_info(cls: str) -> dict:
    """Return full info card for a class label."""
    if cls not in CLASSES:
        cls = "Tomato___healthy"
    crop_raw, _, dis_raw = cls.partition("___")
    crop = display_name(cls).split(" — ")[0]
    disease = display_name(cls).split(" — ")[1]
    kind = _kind_of(cls)
    ov = _OVERRIDES.get(cls, {})
    healthy = kind == "healthy"
    severity = "none" if healthy else ov.get("severity", "medium")
    symptoms = ov.get("symptoms") or (
        "No visible symptoms. Uniform green colour, intact margins, normal vigour."
        if healthy else
        f"Typical {disease.lower()} lesions on foliage (spots/blight/mould pattern); "
        "reduced photosynthesis, premature leaf drop and yield loss if unmanaged."
    )
    chem, org = _GENERIC_TREATMENTS[kind]
    chemical = ov.get("treatment_chemical", chem)
    return {
        "class": cls,
        "name": display_name(cls),
        "crop": crop,
        "disease": "Healthy" if healthy else disease,
        "healthy": healthy,
        "severity": severity,
        "description": (
            f"{crop} crop showing no disease — leaf tissue is healthy." if healthy
            else f"{disease} is a {kind} disorder of {crop.lower()} causing foliar lesions and yield loss. Early detection and prompt treatment prevent spread."
        ),
        "symptoms": symptoms,
        "treatments": [
            {"name": chemical.split(";")[0][:90], "type": "chemical", "detail": chemical, "cost": "₹250–₹600 / acre / spray"},
            {"name": org.split(";")[0][:90], "type": "organic", "detail": org, "cost": "₹150–₹400 / acre"},
            {"name": "Cultural control", "type": "cultural",
             "detail": ov.get("prevention", "Crop rotation, clean seed, balanced fertilisation, drip irrigation, field sanitation, resistant varieties."),
             "cost": "Low / preventive"},
        ],
        "prevention": ov.get("prevention", "Use certified seed, rotate crops, avoid overhead irrigation, scout weekly, remove debris."),
        "lifecycle": (
            "N/A — healthy tissue." if healthy
            else "Pathogen survives on debris/seed or alternate hosts; spreads by wind, rain-splash, insects or sap; favoured by warm humid canopy. Break the cycle with sanitation + rotation."
        ),
        "urgent": severity == "high",
    }
