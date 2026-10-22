"""Generate synthetic Smart Campus Placement dataset.
Adapted from base paper (GradCafe 13k records) -> placement domain.
Deterministic with seed 42. ~3000 students + 30 companies.
"""
import numpy as np
import pandas as pd
import os

SEED = 42
rng = np.random.default_rng(SEED)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

BRANCHES = ["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL"]
ROLES = ["SDE", "Data Analyst", "ML Engineer", "QA Engineer",
         "DevOps", "Support Engineer", "Embedded Engineer", "Design Engineer"]
LOCATIONS = ["Hyderabad", "Bangalore", "Chennai", "Pune", "Mumbai", "Noida"]

COMPANIES = [
    # name, tier(1=dream,2=core,3=mass), cgpa_cutoff, apt_cutoff, tech_cutoff, package, location, type, hiring_rate
    ("Google", 1, 8.5, 85, 85, 28.0, "Bangalore", "MNC", 0.12),
    ("Microsoft", 1, 8.2, 82, 82, 24.0, "Hyderabad", "MNC", 0.15),
    ("Amazon", 1, 7.8, 78, 78, 20.0, "Hyderabad", "MNC", 0.22),
    ("Adobe", 1, 8.0, 80, 82, 22.0, "Noida", "MNC", 0.14),
    ("Goldman Sachs", 1, 8.0, 85, 75, 21.0, "Mumbai", "MNC", 0.13),
    ("TCS Digital", 2, 7.0, 65, 65, 9.5, "Chennai", "MNC", 0.45),
    ("Infosys", 3, 6.0, 55, 50, 4.2, "Mysore", "MNC", 0.55),
    ("Wipro", 3, 6.0, 55, 52, 4.0, "Bangalore", "MNC", 0.52),
    ("Tech Mahindra", 3, 6.2, 58, 55, 4.5, "Pune", "MNC", 0.50),
    ("HCLTech", 3, 6.0, 55, 50, 4.3, "Noida", "MNC", 0.53),
    ("Zoho", 2, 7.2, 70, 72, 11.0, "Chennai", "Startup", 0.25),
    ("Flipkart", 2, 7.5, 72, 74, 14.0, "Bangalore", "Startup", 0.20),
    ("Swiggy", 2, 7.0, 68, 68, 12.0, "Bangalore", "Startup", 0.24),
    ("L&T", 2, 6.8, 62, 60, 7.5, "Mumbai", "Core", 0.35),
    ("Siemens", 2, 7.0, 65, 66, 8.5, "Pune", "Core", 0.30),
    ("Bosch", 2, 7.0, 64, 65, 8.0, "Bangalore", "Core", 0.32),
    ("Tata Motors", 2, 6.5, 60, 58, 7.0, "Pune", "Core", 0.38),
    ("Accenture", 3, 6.2, 58, 55, 5.5, "Hyderabad", "MNC", 0.50),
    ("Cognizant", 3, 6.0, 56, 53, 5.0, "Chennai", "MNC", 0.51),
    ("Capgemini", 3, 6.1, 57, 54, 5.2, "Pune", "MNC", 0.49),
    ("Deloitte", 2, 7.3, 70, 65, 10.5, "Hyderabad", "MNC", 0.28),
    ("JPMorgan", 1, 7.8, 80, 74, 18.0, "Mumbai", "MNC", 0.16),
    ("Oracle", 2, 7.4, 70, 72, 13.0, "Hyderabad", "MNC", 0.22),
    ("Samsung R&D", 2, 7.5, 72, 74, 13.5, "Bangalore", "Core", 0.21),
    ("Qualcomm", 1, 7.8, 78, 80, 19.0, "Hyderabad", "Core", 0.15),
    ("Hyundai", 2, 6.5, 60, 58, 7.2, "Chennai", "Core", 0.36),
    ("Zeta", 2, 7.1, 68, 70, 12.5, "Hyderabad", "Startup", 0.23),
    ("Freshworks", 2, 6.9, 66, 68, 10.0, "Chennai", "Startup", 0.27),
    ("ValueLabs", 3, 6.0, 55, 52, 4.8, "Hyderabad", "MNC", 0.54),
    ("Cyient", 2, 6.6, 60, 60, 6.5, "Hyderabad", "Core", 0.40),
]

comp_df = pd.DataFrame(COMPANIES, columns=[
    "Company", "Tier", "CGPA_Cutoff", "Apt_Cutoff", "Tech_Cutoff",
    "Package_LPA", "Location", "Company_Type", "Hiring_Rate"])
comp_df.to_csv(os.path.join(DATA, "companies.csv"), index=False)
print(f"Saved companies.csv: {len(comp_df)} companies")

N = 3000
# --- student academics (competitive skew like paper Fig.3, mean CGPA ~7.9, skew left) ---
cgpa = np.clip(rng.beta(3.5, 2.5, N) * 3.8 + 5.6, 5.0, 10.0).round(2)
tenth = np.clip(cgpa * 9.0 + rng.normal(0, 4, N), 45, 100).round(1)
twelfth = np.clip(cgpa * 8.6 + rng.normal(0, 5, N), 40, 100).round(1)
apt = np.clip(40 + (cgpa - 5) * 9 + rng.normal(0, 9, N), 20, 100).round(1)
tech = np.clip(38 + (cgpa - 5) * 10 + rng.normal(0, 10, N), 15, 100).round(1)
comm = np.clip(50 + rng.normal(0, 12, N) + (tech - 60) * 0.1, 20, 100).round(1)
dsa = np.clip(tech * 0.9 + rng.normal(0, 10, N), 10, 100).round(1)
projects = rng.poisson(1.8, N).clip(0, 6)
internships = rng.poisson(0.9, N).clip(0, 4)
certs = rng.poisson(1.5, N).clip(0, 6)
backlogs = rng.choice([0, 0, 0, 0, 1, 1, 2, 3, 4], N)
branch = rng.choice(BRANCHES, N, p=[0.32, 0.14, 0.18, 0.10, 0.14, 0.12])
degree = rng.choice(["BTech", "MTech"], N, p=[0.82, 0.18])
stype = rng.choice(["Regular", "Lateral"], N, p=[0.72, 0.28])
year = rng.choice([2023, 2024, 2025, 2026], N, p=[0.2, 0.25, 0.3, 0.25])

# target company weighted by hiring rate (mass companies get more applicants)
w = comp_df["Hiring_Rate"].astype(float).values
w = w / w.sum()
tgt_idx = rng.choice(len(comp_df), N, p=w)
tgt_company = comp_df.iloc[tgt_idx]["Company"].values
tgt_tier = comp_df.iloc[tgt_idx]["Tier"].values
tgt_role = rng.choice(ROLES, N)

df = pd.DataFrame({
    "CGPA": cgpa, "Tenth_Percent": tenth, "Twelfth_Percent": twelfth,
    "Aptitude_Score": apt, "Technical_Score": tech,
    "Communication_Score": comm, "DSA_Score": dsa,
    "Projects": projects, "Internships": internships, "Certifications": certs,
    "Backlogs": backlogs, "Branch": branch, "Degree_Type": degree,
    "Student_Type": stype, "Placement_Year": year,
    "Target_Company": tgt_company, "Target_Role": tgt_role, "Target_Tier": tgt_tier,
})

# merge cutoffs for label generation
m = df.merge(comp_df, left_on="Target_Company", right_on="Company", how="left")
skill_index = (0.4 * m["Technical_Score"] + 0.3 * m["Aptitude_Score"]
               + 0.15 * m["Communication_Score"] + 0.15 * m["DSA_Score"]) / 100.0
cgpa_gap = m["CGPA"] - m["CGPA_Cutoff"]
apt_gap = m["Aptitude_Score"] - m["Apt_Cutoff"]
tech_gap = m["Technical_Score"] - m["Tech_Cutoff"]
# logistic-style score: university quality (tier/cutoff) matters most like paper finding
# tuned for ~55-60% placement rate (balanced like paper 51/49)
logit = (1.4 * cgpa_gap + 0.035 * apt_gap + 0.045 * tech_gap
         + 1.0 * (skill_index - 0.68)
         + 0.35 * m["Internships"] + 0.18 * m["Projects"] + 0.12 * m["Certifications"]
         - 0.9 * m["Backlogs"]
         + np.where(m["Branch"].isin(["CSE", "IT"]), 0.25, 0.0)
         + np.where(m["Tier"] == 1, -1.6, np.where(m["Tier"] == 2, -0.7, -0.1))
         - 0.55
         + rng.normal(0, 0.8, N))
prob = 1 / (1 + np.exp(-logit))
placed = (rng.random(N) < prob).astype(int)
df["Placed"] = placed
# balance check ~ paper had 51/49
print(df["Placed"].value_counts(normalize=True))

df.to_csv(os.path.join(DATA, "placement_dataset.csv"), index=False)
print(f"Saved placement_dataset.csv: {df.shape}")
