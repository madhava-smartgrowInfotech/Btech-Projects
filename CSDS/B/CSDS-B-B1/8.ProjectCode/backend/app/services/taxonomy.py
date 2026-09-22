"""Categories, departments and how each source dataset maps onto them."""

DEPARTMENTS = {  # name -> default SLA in days (editable by admins)
    "Roads": 7,
    "Water Supply": 3,
    "Sanitation": 3,
    "Electricity": 2,
    "Health": 3,
    "Revenue": 15,
    "Public Safety": 1,
    "Town Planning": 21,
}

CATEGORY_TO_DEPT = {
    "Roads & Footpaths": "Roads",
    "Traffic & Parking": "Public Safety",
    "Streetlights": "Electricity",
    "Power Supply": "Electricity",
    "Garbage & Waste": "Sanitation",
    "Drainage & Sewage": "Sanitation",
    "Water Supply": "Water Supply",
    "Water Leakage": "Water Supply",
    "Public Health": "Health",
    "Law & Order": "Public Safety",
    "Public Nuisance": "Public Safety",
    "Encroachment & Illegal Construction": "Town Planning",
    "Land & Certificates": "Revenue",
    "Welfare & Pensions": "Revenue",
    "Corruption & Bribery": "Revenue",
}
CATEGORIES = list(CATEGORY_TO_DEPT)
PRIORITIES = ["Low", "Medium", "High", "Critical"]

# CivicComp-HiEn: (primary, secondary) -> category. Secondary "Others" falls back to primary.
CIVICCOMP_SECONDARY = {
    "Road Damage & Potholes": "Roads & Footpaths",
    "Footpaths & Pedestrian Infrastructure": "Roads & Footpaths",
    "Parking Issues": "Traffic & Parking",
    "Traffic Management & Violations": "Traffic & Parking",
    "Traffic Rule Violations": "Traffic & Parking",
    "Surveillance & Policing": "Law & Order",
    "Public Transport Services": "Traffic & Parking",
    "Streetlights & Public Lighting": "Streetlights",
    "Power Supply Issues": "Power Supply",
    "Electrical Infrastructure": "Power Supply",
    "Garbage Dumping & Black Spots": "Garbage & Waste",
    "Garbage Collection": "Garbage & Waste",
    "Street Cleanliness": "Garbage & Waste",
    "Waste Segregation & Processing": "Garbage & Waste",
    "Construction & Debris Waste": "Garbage & Waste",
    "Mosquito & Pest Control": "Public Health",
    "Animal & Organic Waste": "Public Health",
    "Public Toilets": "Public Health",
    "Public Hygiene": "Public Health",
    "Drainage & Sewage": "Drainage & Sewage",
    "Water Supply Issues": "Water Supply",
    "Water Quality & Metering": "Water Supply",
    "Water Leakage & Wastage": "Water Leakage",
    "Water Pipeline & Infrastructure": "Water Leakage",
    "Public Nuisance": "Public Nuisance",
    "Fire Safety": "Law & Order",
    "Land & Property Encroachment": "Encroachment & Illegal Construction",
    "Unauthorized Construction": "Encroachment & Illegal Construction",
    "Lake & Public Space Encroachment": "Encroachment & Illegal Construction",
}
CIVICCOMP_PRIMARY = {
    "Road & Transportation": "Roads & Footpaths",
    "Electricity": "Streetlights",
    "Waste Management": "Garbage & Waste",
    "Health & Sanitation": "Drainage & Sewage",
    "Water Leakage": "Water Leakage",
    "Public Safety": "Law & Order",
    "Encroachment & Illegal Construction": "Encroachment & Illegal Construction",
    "Others": None,  # too mixed to label
}

# Citizen Grievance Dataset categories -> category (Education has no matching department)
GRIEVANCE = {
    "Roads & Infrastructure": "Roads & Footpaths",
    "Electricity": "Power Supply",
    "Water Supply": "Water Supply",
    "Sanitation & Garbage": "Garbage & Waste",
    "Healthcare & Hospitals": "Public Health",
    "Police & Law and Order": "Law & Order",
    "Land Records & Revenue": "Land & Certificates",
    "Municipal Certificates": "Land & Certificates",
    "Pension & Provident Fund": "Welfare & Pensions",
    "Ration & Public Distribution System": "Welfare & Pensions",
    "Banking & Financial Services": "Welfare & Pensions",
    "Employment & Labour": "Welfare & Pensions",
    "Corruption & Bribery": "Corruption & Bribery",
    "Education & Schools": None,
}

# Indian Citizen Complaint labels -> category ("Economics" essays are not civic complaints)
INDIAN = {
    "Electricity": "Power Supply",
    "Sanitation": "Garbage & Waste",
    "Public Healthcare": "Public Health",
    "Public Safety": "Law & Order",
    "Violence": "Law & Order",
    "Public Infrastructure": "Roads & Footpaths",
    "Economics": None,
}

# NYC 311 complaint types used to learn resolution-time patterns per category.
# The three Revenue categories have no 311 equivalent; the closest casework-style
# request types are used as proxies (documented in docs/02_HOW_IT_WORKS.md).
NYC_TYPES = {
    "Roads & Footpaths": ["Street Condition", "Sidewalk Condition", "Curb Condition", "Highway Condition"],
    "Traffic & Parking": ["Illegal Parking", "Blocked Driveway", "Traffic Signal Condition",
                          "Abandoned Vehicle", "Broken Parking Meter"],
    "Streetlights": ["Street Light Condition"],
    "Power Supply": ["ELECTRIC", "Electrical"],
    "Garbage & Waste": ["Dirty Condition", "Illegal Dumping", "Missed Collection",
                        "Residential Disposal Complaint"],
    "Drainage & Sewage": ["Sewer"],
    "Water Supply": ["Water System", "Water Quality", "Drinking Water"],
    "Water Leakage": ["WATER LEAK", "PLUMBING"],
    "Public Health": ["Rodent", "Food Establishment", "Unsanitary Animal Pvt Property", "Standing Water",
                      "Mosquitoes", "Food Poisoning", "Unsanitary Pigeon Condition", "Dead Animal"],
    "Law & Order": ["Non-Emergency Police Matter", "Drug Activity", "Illegal Fireworks", "Panhandling"],
    "Public Nuisance": ["Noise - Residential", "Noise - Street/Sidewalk", "Noise - Commercial",
                        "Noise - Vehicle", "Noise"],
    "Encroachment & Illegal Construction": ["Building/Use", "General Construction/Plumbing",
                                            "Special Projects Inspection Team (SPIT)", "Obstruction",
                                            "Vendor Enforcement"],
    "Land & Certificates": ["Consumer Complaint"],
    "Welfare & Pensions": ["Consumer Complaint"],
    "Corruption & Bribery": ["Investigations and Discipline (IAD)"],
}
