"""Server-side input validation for FinSight AI."""
from flask import request

WORKCLASS = ["Private", "Self-emp-not-inc", "Self-emp-inc", "Federal-gov",
             "Local-gov", "State-gov", "Without-pay", "Never-worked"]
EDUCATION = ["Preschool", "1st-4th", "5th-6th", "7th-8th", "9th", "10th", "11th",
             "12th", "HS-grad", "Some-college", "Assoc-voc", "Assoc-acdm",
             "Bachelors", "Masters", "Prof-school", "Doctorate"]
EDU_NUM_MAP = {"Preschool": 1, "1st-4th": 2, "5th-6th": 3, "7th-8th": 4,
               "9th": 5, "10th": 6, "11th": 7, "12th": 8, "HS-grad": 9,
               "Some-college": 10, "Assoc-voc": 11, "Assoc-acdm": 12,
               "Bachelors": 13, "Masters": 14, "Prof-school": 15, "Doctorate": 16}
MARITAL = ["Married-civ-spouse", "Divorced", "Never-married", "Separated",
           "Widowed", "Married-spouse-absent", "Married-AF-spouse"]
OCCUPATION = ["Tech-support", "Craft-repair", "Other-service", "Sales",
              "Exec-managerial", "Prof-specialty", "Handlers-cleaners",
              "Machine-op-inspct", "Adm-clerical", "Farming-fishing",
              "Transport-moving", "Priv-house-serv", "Protective-serv",
              "Armed-Forces"]
RELATIONSHIP = ["Wife", "Own-child", "Husband", "Not-in-family",
                "Other-relative", "Unmarried"]
RACE = ["White", "Asian-Pac-Islander", "Amer-Indian-Eskimo", "Other", "Black"]
SEX = ["Female", "Male"]
COUNTRIES = ["United-States", "Cambodia", "England", "Puerto-Rico", "Canada",
             "Germany", "Outlying-US(Guam-USVI-etc)", "India", "Japan", "Greece",
             "South", "China", "Cuba", "Iran", "Honduras", "Philippines",
             "Italy", "Poland", "Jamaica", "Vietnam", "Mexico", "Portugal",
             "Ireland", "France", "Dominican-Republic", "Laos", "Ecuador",
             "Taiwan", "Haiti", "Colombia", "Hungary", "Guatemala",
             "Nicaragua", "Scotland", "Thailand", "Yugoslavia", "El-Salvador",
             "Trinadad&Tobago", "Peru", "Hong", "Holand-Netherlands"]


def _get(data, key, default=""):
    if isinstance(data, dict):
        return data.get(key, default)
    return data.get(key, default)


def validate_assessment(data) -> tuple:
    """Validate assessment input. Returns (cleaned_dict, errors_list)."""
    errors = []
    cleaned = {}

    def req_cat(key, allowed, label):
        raw = str(_get(data, key, "")).strip()
        if not raw:
            errors.append(f"{label} is required.")
            return None
        if raw not in allowed:
            errors.append(f"{label} has an invalid value.")
            return None
        return raw

    def req_num(key, label, lo, hi, integer=False):
        raw = str(_get(data, key, "")).strip()
        if raw == "":
            errors.append(f"{label} is required.")
            return None
        try:
            v = int(raw) if integer else float(raw)
        except ValueError:
            errors.append(f"{label} must be a number.")
            return None
        if v < lo or v > hi:
            errors.append(f"{label} must be between {lo} and {hi}.")
            return None
        return v

    cleaned["age"] = req_num("age", "Age", 16, 100, integer=True)
    cleaned["workclass"] = req_cat("workclass", WORKCLASS, "Employment type")
    cleaned["education"] = req_cat("education", EDUCATION, "Education")
    cleaned["marital-status"] = req_cat("marital-status", MARITAL, "Marital status")
    cleaned["occupation"] = req_cat("occupation", OCCUPATION, "Occupation")
    cleaned["relationship"] = req_cat("relationship", RELATIONSHIP, "Household relationship")
    cleaned["race"] = req_cat("race", RACE, "Race")
    cleaned["sex"] = req_cat("sex", SEX, "Sex")
    cleaned["native-country"] = req_cat("native-country", COUNTRIES, "Country")
    cleaned["capital-gain"] = req_num("capital-gain", "Investment gains", 0, 1000000)
    cleaned["capital-loss"] = req_num("capital-loss", "Investment losses", 0, 1000000)
    cleaned["hours-per-week"] = req_num("hours-per-week", "Hours worked per week", 1, 99, integer=True)

    if cleaned.get("education") in EDU_NUM_MAP:
        cleaned["education-num"] = EDU_NUM_MAP[cleaned["education"]]
    else:
        cleaned["education-num"] = None
        if cleaned.get("education") is not None:
            errors.append("Education level is invalid.")

    # drop Nones for error check
    if errors:
        return {}, errors
    return cleaned, []
