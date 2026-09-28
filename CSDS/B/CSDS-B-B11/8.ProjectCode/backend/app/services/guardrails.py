"""Ingredient-level allergen scan applied to AI-generated recipes."""
import re

INGREDIENT_WORDS = {
    "peanut": ["peanut", "groundnut", "moongfali", "mungfali", "shengdana", "peanut oil", "arachis"],
    "tree_nut": ["cashew", "kaju", "almond", "badam", "pistachio", "pista", "walnut", "akhrot", "hazelnut", "pecan", "macadamia", "chironji"],
    "dairy": ["milk", "paneer", "curd", "dahi", "yogurt", "yoghurt", "cheese", "butter", "ghee", "cream", "malai", "khoa", "khoya", "mawa", "buttermilk", "whey", "condensed milk"],
    "gluten": ["wheat", "atta", "maida", "semolina", "sooji", "suji", "rava", "barley", "rye", "bread", "breadcrumb", "vermicelli", "seitan", "soy sauce"],
    "egg": ["egg", "eggs", "mayonnaise", "albumen"],
    "soy": ["soy", "soya", "tofu", "edamame", "tempeh", "miso", "soy sauce"],
    "fish": ["fish", "anchovy", "tuna", "salmon", "sardine", "mackerel", "pomfret", "fish sauce"],
    "shellfish": ["prawn", "shrimp", "crab", "lobster", "squid", "clam", "mussel", "oyster"],
    "sesame": ["sesame", "til", "gingelly", "tahini"],
}
# words that contain an allergen word but are safe
SAFE_PHRASES = ["coconut milk", "almond-free", "dairy-free", "peanut-free", "nut-free", "egg-free", "eggplant",
                "butternut", "cocoa butter", "without", "free of", "instead of", "substitute", "replace", "avoid",
                "vegan butter", "vegan cheese", "plant milk", "oat milk", "soy-free", "gluten-free"]


def scan(text: str, allergies: list[str]) -> list[str]:
    """Return allergen words found in text for this user's allergies."""
    t = text.lower()
    for s in SAFE_PHRASES:
        t = t.replace(s, " ")
    hits = []
    for a in allergies:
        for w in INGREDIENT_WORDS.get(a, []):
            if re.search(r"\b" + re.escape(w) + r"s?\b", t):
                hits.append(w)
    return sorted(set(hits))

DIET_WORDS = {
    "meat": ["chicken", "mutton", "lamb", "goat", "beef", "pork", "bacon", "ham", "keema", "meat", "sausage",
             "fish", "prawn", "shrimp", "crab", "anchovy", "tuna", "salmon", "gelatin"],
    "egg": ["egg", "eggs", "mayonnaise"],
    "dairy": INGREDIENT_WORDS["dairy"],
}


def diet_scan(text: str, diet_type: str) -> list[str]:
    groups = {"vegetarian": ["meat", "egg"], "eggetarian": ["meat"], "vegan": ["meat", "egg", "dairy"]}.get(diet_type, [])
    t = text.lower()
    for s in SAFE_PHRASES:
        t = t.replace(s, " ")
    hits = []
    for g in groups:
        for w in DIET_WORDS[g]:
            if re.search(r"\b" + re.escape(w) + r"s?\b", t):
                hits.append(w)
    return sorted(set(hits))
