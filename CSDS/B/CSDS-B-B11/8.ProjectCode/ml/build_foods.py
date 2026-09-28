"""Build the NutriSense food database from the raw Kaggle files.

Input
  data/raw/indian_food_nutrition/Indian_Food_Nutrition_Processed.csv  (nutrients per 100 g)
  data/raw/indian_diet_carbon/nutrition_cf - Sheet5.csv                (meal type / region / allergy labels)
  data/raw/south_asian_recipes/recipes_master.csv                      (typical cooking times)

Output
  data/processed/foods.csv - one row per dish with per-100 g nutrients, a default serving,
  meal role, diet type, cuisine, allergens, estimated glycaemic index and a fried/rich flag.

Deterministic: running it twice gives the same file.
"""
import difflib
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "foods.csv"


def has(text, words):
    """True if any keyword occurs as a whole word (or word prefix for multi-letter stems)."""
    for w in words:
        if re.search(r"\b" + re.escape(w) + r"\b", text):
            return True
    return False


# ---------------------------------------------------------------- meal roles
BEV = ["tea", "chai", "coffee", "juice", "shake", "milkshake", "lassi", "drink", "sherbet", "sharbat",
       "punch", "lemonade", "smoothie", "cooler", "soda", "squash", "water", "thandai", "buttermilk",
       "chaas", "chhach", "cocoa", "kadha", "mocktail", "panna", "nimbu pani", "shikanji", "milk", "cold coffee",
       "espreso", "espresso", "cappuccino", "latte", "frappe", "jaljeera", "aam panna", "sattu drink", "kokum",
       "lem-o-gin", "cocktail", "horlicks", "bournvita", "sol kadhi", "neer mor", "mor", "ginger ale"]
DESSERT = ["halwa", "kheer", "payasam", "burfi", "barfi", "ladoo", "laddoo", "laddu", "ladu", "jalebi",
           "gulab jamun", "rasgulla", "rasgolla", "rasmalai", "cake", "pudding", "ice cream", "kulfi",
           "custard", "pie", "tart", "mousse", "souffle", "trifle", "sandesh", "peda", "mithai", "cookie",
           "cookies", "brownie", "pastry", "chikki", "shrikhand", "phirni", "firni", "jelly", "doughnut",
           "murabba", "jam", "gajak", "rabri", "rabdi", "basundi", "modak", "malpua", "rousse", "meringue",
           "fudge", "toffee", "candy", "gujiya", "mysore pak", "soan papdi", "kalakand", "cham cham",
           "petha", "imarti", "balushahi", "shakarpara", "sheera", "kesari", "falooda", "sundae", "muffin",
           "halva", "sweet", "pantua", "mishti", "gajar ka halwa", "shahi tukda", "double ka meetha",
           "coconut barfi", "til ladoo", "sevaiyan kheer", "sewai", "ras malai", "cheesecake", "compote",
           "caramel", "crumble", "strudel", "eclair", "macaroon", "profiterole", "chocolate", "praline",
           "meetha", "mawa", "khoa", "kaju katli", "boondi", "rewri", "revdi", "chena"]
BF = ["idli", "dosa", "dosai", "uttapam", "uthappam", "upma", "uppuma", "poha", "cheela", "chilla", "chila",
      "oats", "porridge", "dalia", "daliya", "omelette", "omlette", "omelet", "sandwich", "toast", "pancake",
      "pongal", "appam", "puttu", "pesarattu", "adai", "idiyappam", "sevai", "vada", "vadai", "cornflakes",
      "muesli", "bhurji", "scrambled", "french toast", "waffle", "cereal", "granola", "akki roti",
      "thalipeeth", "misal", "sabudana khichdi", "sabudana", "semiya", "vermicelli upma", "rava",
      "boiled egg", "poached egg", "fried egg", "scrambled egg", "baked egg", "deviled egg", "dhokla", "handvo", "muthia", "paniyaram",
      "kuzhi paniyaram", "neer dosa", "set dosa", "ragi dosa", "ragi malt", "oatmeal", "khakhra"]
ONEDISH = ["biryani", "biriyani", "pulao", "pulav", "pilaf", "khichdi", "khichri", "khichadi", "fried rice",
           "bisi bele", "bisibele", "lemon rice", "curd rice", "tamarind rice", "puliyogare", "puliyodarai",
           "coconut rice", "tomato rice", "vegetable rice", "mint rice", "noodles", "pasta", "spaghetti",
           "macaroni", "chowmein", "chow mein", "hakka", "risotto", "pizza", "burger", "wrap", "frankie",
           "roll", "pav bhaji", "chole bhature", "rajma chawal", "dal dhokli", "thali", "lasagne", "lasagna",
           "vangi bath", "vangibath", "bath", "chitranna", "tahiri", "tehri", "kadhi chawal", "dal baati",
           "baati", "bolognese", "haleem", "taco", "burrito", "quesadilla", "shawarma", "hot dog",
           "sevai biryani", "ven pongal", "bhel", "chaat", "fettuccine", "penne", "ravioli", "gnocchi",
           "rice pulao", "yakhni", "sadam", "saadam", "annam", "bhaat", "pakhala", "rice"]
STAPLE = ["roti", "chapati", "chapatti", "phulka", "paratha", "parantha", "parotta", "naan", "nan", "kulcha",
          "poori", "puri", "bhatura", "bhature", "rice", "bread", "thepla", "bhakri", "bhakhri", "rumali",
          "missi", "makki", "tandoori roti", "sheermal", "luchi", "kachori", "dhebra", "rotla", "pav", "bun",
          "idiyappam", "jolada rotti", "rotti", "tortilla", "pita", "bagel"]
SIDE = ["raita", "salad", "soup", "chutney", "pickle", "achar", "papad", "papadum", "kachumber",
        "koshambari", "kosambari", "pachadi", "sprouts", "shorba", "dip", "hummus", "thuvayal",
        "thogayal", "podi", "gunpowder", "relish", "coleslaw", "salsa", "yoghurt", "yogurt", "curd", "dahi",
        "cucumber", "sundal", "broth", "consomme", "rasam"]
SNACK = ["pakora", "pakoda", "bhajia", "bhajji", "bajji", "samosa", "cutlet", "tikki", "chaat", "bhel",
         "pani puri", "golgappa", "sev", "namkeen", "chips", "fries", "nuggets", "kebab", "kabab", "tikka",
         "momos", "momo", "spring roll", "patties", "patty", "mathri", "chakli", "murukku", "makhana",
         "roasted chana", "popcorn", "biscuit", "khandvi", "finger", "croquette", "nachos", "bruschetta",
         "canape", "chivda", "chiwda", "mixture", "bonda", "fritter", "tempura", "seekh", "shami",
         "galouti", "vada pav", "dabeli", "puff", "sabudana vada", "kathi", "falafel", "cheese balls",
         "corn", "peanuts", "trail mix", "nuts", "dry fruits", "banana", "apple", "papaya", "guava",
         "orange", "mango", "watermelon", "pear", "grapes", "pomegranate", "fruit", "chana chaat",
         "ragda", "manchurian", "chilli paneer", "chilli chicken", "crackers", "bar", "energy balls"]
CURRY = ["curry", "dal", "daal", "dhal", "sambar", "sambhar", "sabzi", "subzi", "sabji", "masala", "korma",
         "kurma", "kofta", "makhani", "gravy", "stew", "kadhi", "kadi", "bharta", "bhartha", "jalfrezi",
         "do pyaza", "dopiaza", "keema", "kheema", "vindaloo", "saag", "sag", "palak", "chole", "chhole",
         "chana", "rajma", "poriyal", "kootu", "avial", "aviyal", "thoran", "usal", "usli", "paneer", "aloo",
         "gobhi", "gobi", "bhindi", "baingan", "brinjal", "matar", "mutter", "mushroom", "chicken",
         "mutton", "lamb", "fish", "prawn", "prawns", "shrimp", "egg curry", "stir fry", "fry", "roast",
         "tandoori", "rogan josh", "nihari", "kuzhambu", "kulambu", "molee", "moilee", "xacuti", "ghassi",
         "gassi", "kalan", "olan", "erissery", "pulissery", "mor kuzhambu", "dalma", "ghugni", "chorchori",
         "shukto", "undhiyu", "kadai", "karahi", "handi", "tawa", "bhuna", "lababdar", "pasanda", "qorma",
         "salan", "mirchi ka salan", "baghare", "kaddu", "lauki", "tinda", "karela", "arbi", "methi",
         "beans", "cabbage", "cauliflower", "potato", "pumpkin", "gourd", "vegetable", "vegetables",
         "sprouts curry", "soya chunks", "tofu", "lobia", "moong", "masoor", "urad", "toor", "arhar",
         "kidney beans", "chickpea", "chickpeas", "black gram", "horse gram", "kulthi", "pitla",
         "zunka", "jhol", "kalia", "bhaji", "dum aloo", "posto", "pappu", "majjige huli", "huli",
         "gojju", "saaru", "kosha", "chettinad", "pepper chicken", "keerai", "koot", "kara kuzhambu"]

# checked before everything else (specific phrases that the generic lists would misfile)
PRE_RULES = [("other", ["bread sauce", "stock", "icing", "preserves", "frosting"]),
             ("staple", ["boiled rice", "plain rice", "steamed rice", "brown rice", "jeera rice", "cumin rice"]),
             ("snack", ["murukku", "murmura", "namak paras", "mixture", "chakli", "mathri", "kachori", "biscuit"]),
             ("bf", ["rice flakes", "cornflakes", "flattened rice"]),
             ("dessert", ["swiss roll", "ginger bread", "sweet rice", "boondi raita", "ice cream", "sorbet",
                          "alaska", "coffee drops"]),
             ("bev", ["nog"])]
ROLE_RULES = [("bev", BEV), ("dessert", DESSERT), ("bf", BF), ("onedish", ONEDISH),
              ("staple", STAPLE), ("side", SIDE), ("snack", SNACK), ("curry", CURRY)]

# ---------------------------------------------------------------- cuisine
SOUTH = ["idli", "dosa", "dosai", "uttapam", "uthappam", "sambar", "sambhar", "rasam", "appam", "avial",
         "aviyal", "pongal", "upma", "uppuma", "vada", "vadai", "puttu", "kootu", "poriyal", "thoran",
         "bisi bele", "bisibele", "curd rice", "lemon rice", "tamarind rice", "puliyogare", "coconut rice",
         "pesarattu", "adai", "idiyappam", "paniyaram", "kuzhambu", "kulambu", "molee", "moilee", "olan",
         "kalan", "erissery", "pulissery", "payasam", "chettinad", "neer dosa", "set dosa", "ragi",
         "pachadi", "koshambari", "kosambari", "thuvayal", "thogayal", "podi", "vangi bath", "chitranna",
         "akki roti", "gojju", "saaru", "huli", "majjige", "keerai", "mysore", "kerala", "malabar",
         "andhra", "hyderabadi", "tamil", "karnataka", "udupi", "pappu", "pulihora", "gongura", "avakaya",
         "sundal", "murukku", "mor", "parotta", "kurma", "meen", "chemmeen", "coorg", "mangalorean",
         "kesari", "sevai", "semiya", "rava", "sadam", "saadam", "annam", "pitla", "kara", "pepper rasam"]
CONTINENTAL = ["pasta", "spaghetti", "macaroni", "pizza", "burger", "sandwich", "cake", "pie", "toast",
               "pancake", "waffle", "souffle", "bolognese", "au gratin", "gratin", "lasagne", "lasagna",
               "risotto", "mousse", "custard", "baked", "white sauce", "cheese sauce", "french", "mexican",
               "italian", "taco", "burrito", "quesadilla", "nachos", "bruschetta", "canape", "coleslaw",
               "salsa", "muffin", "brownie", "pudding", "trifle", "tart", "croquette", "meringue", "rousse",
               "cornflakes", "muesli", "cereal", "granola", "oatmeal", "hot dog", "fettuccine", "penne",
               "ravioli", "gnocchi", "cheesecake", "eclair", "strudel", "crumble", "hummus", "falafel",
               "shawarma", "pita", "bagel", "tortilla", "stroganoff", "goulash", "casserole", "chowder",
               "minestrone", "espreso", "espresso", "cappuccino", "latte", "frappe", "iced tea", "lemonade"]
INDO_CHINESE = ["manchurian", "chowmein", "chow mein", "hakka", "fried rice", "chilli paneer",
                "chilli chicken", "spring roll", "momos", "momo", "schezwan", "szechuan", "sweet corn soup",
                "hot and sour", "manchow", "american chopsuey", "chopsuey", "noodles"]

# ---------------------------------------------------------------- diet
MEAT = ["chicken", "mutton", "lamb", "goat", "meat", "keema", "kheema", "pork", "beef", "ham", "bacon",
        "sausage", "salami", "liver", "gosht", "murgh", "murg", "turkey", "duck", "nihari", "haleem",
        "rogan josh", "gushtaba", "rista", "yakhni", "kosha mangsho", "mangsho", "boti", "paya", "raan",
        "brain", "kidney", "trotters", "pepperoni", "bolognese", "galouti", "shami", "seekh", "kalia"]
FISH = ["fish", "machli", "machhi", "macher", "maach", "meen", "tuna", "salmon", "sardine", "sardines",
        "mackerel", "pomfret", "rohu", "surmai", "bangda", "hilsa", "ilish", "katla", "anchovy", "bombil",
        "kingfish", "cod", "tilapia", "basa", "seer", "fish fingers", "karimeen"]
SHELLFISH = ["prawn", "prawns", "shrimp", "shrimps", "jhinga", "jhinge", "crab", "crabs", "lobster", "squid",
             "clam", "clams", "mussel", "mussels", "oyster", "oysters", "kolambi", "chemmeen", "calamari",
             "chingri", "seafood"]
EGG = ["egg", "eggs", "anda", "omelette", "omlette", "omelet", "mayonnaise", "mayo", "meringue", "souffle",
       "mousse", "french toast", "pancake", "pancakes", "waffle", "muffin", "brownie", "cake", "cakes",
       "cheesecake", "eclair", "custard tart", "rousse", "doughnut", "cookie", "cookies", "macaroon",
       "egg bhurji", "scrambled"]
EGGLESS = ["eggless", "egg less", "without egg", "egg free"]

# ---------------------------------------------------------------- allergens
PEANUT = ["peanut", "peanuts", "groundnut", "groundnuts", "moongfali", "mungfali", "moongphali",
          "shengdana", "chikki", "satay", "kung pao", "bhel", "chivda", "chiwda", "poha", "sabudana",
          "mixture", "trail mix", "pulihora", "puliyogare", "tamarind rice", "gongura", "chikkis",
          "shengdane", "nilakadalai", "verkadalai", "palli"]
TREE_NUT = ["cashew", "cashews", "kaju", "almond", "almonds", "badam", "badami", "pista", "pistachio",
            "pistachios", "walnut", "walnuts", "akhrot", "hazelnut", "hazelnuts", "nuts", "dry fruit",
            "dry fruits", "dryfruit", "korma", "kurma", "qorma", "shahi", "navratan", "navrattan",
            "malai kofta", "pasanda", "mughlai", "kheer", "payasam", "phirni", "firni", "kulfi", "falooda",
            "thandai", "panjiri", "praline", "marzipan", "macaroon", "pesto", "nut", "chikki", "halwa",
            "ladoo", "laddoo", "laddu", "barfi", "burfi", "biryani", "kaju katli", "trail mix",
            "energy balls", "granola", "muesli", "sheer khurma", "badam milk"]
DAIRY = ["milk", "paneer", "curd", "dahi", "yogurt", "yoghurt", "cheese", "butter", "ghee", "cream", "malai",
         "khoa", "khoya", "mawa", "lassi", "raita", "kheer", "payasam", "kulfi", "ice cream", "shake",
         "milkshake", "buttermilk", "chaas", "chhach", "makhani", "rabri", "rabdi", "basundi", "rasgulla",
         "rasgolla", "rasmalai", "ras malai", "sandesh", "shrikhand", "custard", "kadhi", "kadi",
         "curd rice", "mor", "mor kuzhambu", "majjige", "pachadi", "gulab jamun", "peda", "barfi", "burfi",
         "kalakand", "cake", "pudding", "white sauce", "cheese sauce", "au gratin", "gratin", "pizza",
         "naan", "korma", "kurma", "qorma", "malai kofta", "phirni", "firni", "falooda", "thandai",
         "cheesecake", "latte", "cappuccino", "frappe", "cold coffee", "horlicks", "bournvita", "chena",
         "chhena", "cham cham", "mishti doi", "neer mor", "tzatziki", "lababdar", "shahi", "sheer khurma",
         "halwa", "ladoo", "sundae", "mousse", "souffle", "trifle", "eclair", "muffin", "brownie",
         "lasagne", "lasagna", "creamy", "kesari", "sheera", "malpua", "rabadi", "dahi vada", "dahi bhalla"]
GLUTEN = ["wheat", "atta", "maida", "roti", "chapati", "chapatti", "phulka", "paratha", "parantha",
          "parotta", "naan", "nan", "kulcha", "poori", "puri", "bhatura", "bhature", "bread", "bun", "buns",
          "pav", "toast", "sandwich", "pasta", "spaghetti", "macaroni", "noodles", "vermicelli", "semiya",
          "sevai", "seviyan", "sewai", "suji", "sooji", "semolina", "rava", "rawa", "upma", "dalia", "daliya",
          "broken wheat", "barley", "jau", "oats", "oatmeal", "biscuit", "biscuits", "cookie", "cookies",
          "cake", "pastry", "pie", "pizza", "burger", "samosa", "kachori", "mathri", "thepla", "khakhra",
          "dhokli", "baati", "manchurian", "spring roll", "momos", "momo", "cutlet", "croquette",
          "breadcrumb", "rusk", "khari", "shakarpara", "gujiya", "malpua", "jalebi", "balushahi", "tortilla",
          "wrap", "frankie", "roll", "kathi", "lasagne", "lasagna", "muffin", "brownie", "doughnut",
          "waffle", "pancake", "french toast", "puff", "patties", "patty", "rumali", "missi", "sheermal",
          "luchi", "halwa", "kesari", "sheera", "chowmein", "chow mein", "hakka", "falooda", "dabeli",
          "vada pav", "pita", "bagel", "cornflakes", "muesli", "granola", "cereal", "fettuccine", "penne",
          "ravioli", "gnocchi", "eclair", "strudel", "crumble", "tart", "trifle", "cheesecake", "golgappa",
          "pani puri", "sev puri", "papdi", "dahi puri", "bhel", "haleem", "soy sauce", "soya sauce",
          "dhebra", "khasta", "shahi tukda", "double ka meetha", "horlicks", "bournvita"]
SOY = ["soy", "soya", "tofu", "nutrela", "soyabean", "soybean", "edamame", "manchurian", "chowmein",
       "chow mein", "hakka", "fried rice", "chilli paneer", "chilli chicken", "schezwan", "szechuan",
       "spring roll", "soya chunks", "tempeh", "miso", "manchow", "chopsuey"]
SESAME = ["sesame", "til", "gingelly", "tahini", "gajak", "rewri", "revdi", "hummus", "ellu", "nuvvula",
          "til ladoo", "til chikki"]

ALLERGEN_RULES = {"peanut": PEANUT, "tree_nut": TREE_NUT, "dairy": DAIRY, "gluten": GLUTEN, "egg": EGG,
                  "soy": SOY, "fish": FISH, "shellfish": SHELLFISH, "sesame": SESAME}
# carbon-dataset allergy words -> our allergen codes
CARBON_ALLERGY_MAP = {"dairy": "dairy", "gluten": "gluten", "nut": "tree_nut", "soy": "soy", "egg": "egg",
                      "fish": "fish", "peanut": "peanut", "shellfish": "shellfish", "seafood": "shellfish",
                      "sesame": "sesame"}

# ---------------------------------------------------------------- health flags
FRIED = ["fried", "fry", "pakora", "pakoda", "bhajia", "bhajji", "bajji", "samosa", "kachori", "poori",
         "puri", "bhatura", "bhature", "vada", "vadai", "jalebi", "fries", "chips", "tempura", "fritter",
         "fritters", "bonda", "murukku", "chakli", "mathri", "namkeen", "malpua", "balushahi",
         "gulab jamun", "imarti", "crispy", "deep", "luchi", "golgappa", "pani puri", "papdi", "mixture",
         "sev", "chivda", "chiwda", "shakarpara", "gujiya", "doughnut", "nuggets", "croquette", "puff",
         "kachauri", "khasta", "vada pav", "dabeli", "bhel"]
RICH = ["butter", "cream", "creamy", "malai", "makhani", "ghee", "cheese", "mayonnaise", "mayo", "korma",
        "kurma", "qorma", "shahi", "lababdar", "khoa", "khoya", "mawa", "rabri", "rabdi", "liver", "brain",
        "paya", "nihari", "bacon", "sausage", "salami", "pepperoni"]

# ---------------------------------------------------------------- glycaemic index (food-group estimates)
# Values follow published GI ranges for Indian foods (e.g. white rice ~73, chapati ~62, legumes ~30).
GI_RULES = [
    (["sugar", "jalebi", "gulab jamun", "rasgulla", "sweet", "candy", "toffee", "jam", "squash", "cola",
      "soda", "sherbet", "sharbat", "punch", "lemonade", "juice"], 70),
    (["potato", "aloo", "fries", "chips", "sabudana", "cornflakes", "rice flakes", "puffed rice", "murmura",
      "bhel", "poha", "watermelon"], 75),
    (["rice", "biryani", "pulao", "pulav", "idli", "dosa", "dosai", "uttapam", "appam", "puttu", "idiyappam",
      "noodles", "bread", "naan", "pav", "bun", "maida", "kulcha", "bhatura", "pizza", "burger", "toast",
      "sandwich", "upma", "rava", "sooji", "suji", "semolina", "cake", "biscuit", "pongal", "sevai",
      "semiya", "vermicelli", "pasta", "spaghetti", "macaroni", "parotta", "luchi", "poori", "puri"], 70),
    (["roti", "chapati", "chapatti", "phulka", "paratha", "parantha", "thepla", "missi", "wheat", "atta",
      "bhakri", "makki", "ragi", "jowar", "bajra", "millet", "khichdi", "khichri", "khichadi", "banana",
      "mango", "papaya", "pineapple", "raisin", "honey"], 60),
    (["oats", "oatmeal", "dalia", "daliya", "barley", "quinoa", "muesli", "apple", "orange", "pear",
      "guava", "grapes", "pomegranate", "fruit", "corn"], 50),
    (["dal", "daal", "dhal", "sambar", "sambhar", "chana", "chole", "chhole", "rajma", "moong", "masoor",
      "urad", "toor", "arhar", "lobia", "chickpea", "chickpeas", "kidney beans", "sprouts", "besan",
      "cheela", "chilla", "pesarattu", "adai", "dhokla", "soy", "soya", "tofu", "sundal", "kulthi",
      "horse gram", "peanut", "nuts", "almond", "cashew", "walnut"], 32),
    (["milk", "curd", "dahi", "yogurt", "yoghurt", "paneer", "cheese", "lassi", "raita", "buttermilk",
      "chaas", "egg", "omelette", "chicken", "mutton", "fish", "prawn", "meat", "keema"], 30),
]
DEFAULT_GI = 45  # mixed vegetable dishes

# ---------------------------------------------------------------- servings (grams)
def serving_grams(role, t):
    if role == "bev":
        return 200
    if role == "dessert":
        return 80
    if role == "bf":
        if has(t, ["egg", "boiled egg", "omelette", "omlette", "bhurji"]):
            return 100
        if has(t, ["toast", "sandwich"]):
            return 120
        return 150
    if role == "onedish":
        return 250
    if role == "staple":
        if has(t, ["rice"]):
            return 150
        if has(t, ["poori", "puri", "luchi", "bhatura", "bhature", "kachori"]):
            return 70
        if has(t, ["paratha", "parantha", "parotta", "thepla", "naan", "nan", "kulcha"]):
            return 100
        if has(t, ["bread", "pav", "bun"]):
            return 60
        return 80
    if role == "side":
        if has(t, ["soup", "shorba", "rasam", "broth"]):
            return 200
        if has(t, ["chutney", "dip", "podi", "thuvayal", "thogayal", "relish", "salsa", "hummus"]):
            return 30
        if has(t, ["pickle", "achar", "papad", "papadum"]):
            return 15
        return 100
    if role == "snack":
        if has(t, ["banana", "apple", "papaya", "guava", "orange", "mango", "watermelon", "pear", "grapes",
                   "pomegranate", "fruit"]):
            return 150
        if has(t, ["nuts", "peanuts", "makhana", "trail mix", "dry fruits", "roasted chana", "popcorn",
                   "chips", "biscuit"]):
            return 30
        return 80
    return 150  # curry / other


def normalise(name):
    s = name.lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def display_name(name):
    main = re.sub(r"\(.*?\)", "", name).strip(" ,-")
    main = re.sub(r"\s+", " ", main)
    main = main[:1].upper() + main[1:]
    alt = " ".join(re.findall(r"\((.*?)\)", name))
    return main, alt


BEV_NO_MILK = [w for w in BEV if w != "milk"]


def classify_role(t):
    for role, words in PRE_RULES:
        if has(t, words):
            return role
    for role, words in ROLE_RULES:
        if role == "bev":
            if has(t, ["soup"]):
                continue
            if has(t, BEV_NO_MILK):
                return "bev"
            # "milk" alone means a drink only when nothing else describes the dish
            if has(t, ["milk"]) and not any(has(t, w) for r, w in ROLE_RULES if r != "bev"):
                return "bev"
            continue
        if has(t, words):
            return role
    return "other"


# naturally energy-dense foods that may legitimately exceed 40 g fat / 100 g
DENSE_OK = ["nut", "nuts", "peanut", "almond", "cashew", "walnut", "butter", "ghee", "oil", "chocolate",
            "cheese", "mayonnaise", "coconut", "seeds", "til", "sesame", "makhana"]


def main():
    ind = pd.read_csv(RAW / "indian_food_nutrition" / "Indian_Food_Nutrition_Processed.csv")
    ind.columns = ["dish", "kcal", "carbs", "protein", "fat", "sugar", "fibre", "sodium", "calcium",
                   "iron", "vit_c", "folate"]
    carbon = pd.read_csv(RAW / "indian_diet_carbon" / "nutrition_cf - Sheet5.csv")
    carbon["norm"] = carbon["Food"].astype(str).map(normalise)
    carbon_norms = carbon["norm"].tolist()
    recipes = pd.read_csv(RAW / "south_asian_recipes" / "recipes_master.csv")
    recipes = recipes[recipes["cuisine"] == "Indian"]
    recipes["norm"] = recipes["recipe_name"].astype(str).map(normalise)
    rec_time = recipes.groupby("norm")["total_time_minutes"].median().to_dict()

    rows = []
    seen = set()
    dropped = []
    for i, r in ind.iterrows():
        name, alt = display_name(str(r["dish"]))
        key = normalise(name)
        if not key or key in seen:
            continue
        seen.add(key)
        text = (str(r["dish"]) + " " + alt).lower()
        text = re.sub(r"[/,\-]", " ", text)
        # quality filter: rows whose fat looks like it counts the whole frying oil
        if float(r["fat"]) > 40 and not has(text, DENSE_OK):
            dropped.append(name)
            continue
        role = classify_role(text)

        # labels from the carbon dataset when the dish name matches closely
        match = difflib.get_close_matches(key, carbon_norms, n=1, cutoff=0.88)
        c = carbon[carbon["norm"] == match[0]].iloc[0] if match else None
        regions = str(c["Region"]).lower() if c is not None else ""
        if role == "other" and c is not None:
            ctype = str(c["Type"]).lower()
            if "breakfast" in ctype:
                role = "bf"
            elif "beverage" in ctype:
                role = "bev"
            elif "snack" in ctype or "appetizer" in ctype:
                role = "snack"
            elif "curry" in ctype or "gravy" in ctype or "lunch" in ctype or "dinner" in ctype:
                role = "curry"

        # diet type
        if has(text, MEAT + FISH + SHELLFISH):
            diet = "non_vegetarian"
        elif has(text, EGG) and not has(text, EGGLESS):
            diet = "eggetarian"
        else:
            diet = "vegetarian"
        if c is not None and diet == "vegetarian":
            cat = str(c["Category"]).lower()
            if cat == "non-veg":
                diet = "non_vegetarian"
            elif cat == "eggetarian":
                diet = "eggetarian"

        # allergens
        allergens = set()
        for code, words in ALLERGEN_RULES.items():
            if has(text, words):
                allergens.add(code)
        if "egg" in allergens and has(text, EGGLESS):
            allergens.discard("egg")
        if diet == "eggetarian":
            allergens.add("egg")
        if c is not None:
            for a in str(c["Allergy"]).lower().replace(".", "").split(","):
                a = a.strip()
                if a in CARBON_ALLERGY_MAP:
                    allergens.add(CARBON_ALLERGY_MAP[a])
        vegan = diet == "vegetarian" and not ({"dairy", "egg"} & allergens) and not has(text, ["honey"])

        # cuisine
        if has(text, INDO_CHINESE):
            cuisine = "indo_chinese"
        elif has(text, CONTINENTAL):
            cuisine = "continental"
        elif has(text, SOUTH) or ("south" in regions and "north" not in regions):
            cuisine = "south"
        elif "continental" in regions and "north" not in regions and "south" not in regions:
            cuisine = "continental"
        else:
            cuisine = "north"

        gi = DEFAULT_GI
        for words, value in GI_RULES:
            if has(text, words):
                gi = value
                break

        rows.append({
            "food_id": len(rows) + 1,
            "name": name,
            "alt_names": alt,
            "role": role,
            "diet": diet,
            "vegan": vegan,
            "cuisine": cuisine,
            "allergens": "|".join(sorted(allergens)),
            "fried": has(text, FRIED),
            "rich": has(text, RICH),
            "gi": gi,
            "serving_g": serving_grams(role, text),
            "kcal": round(float(r["kcal"]), 2),
            "protein": round(float(r["protein"]), 2),
            "carbs": round(float(r["carbs"]), 2),
            "fat": round(float(r["fat"]), 2),
            "fibre": round(float(r["fibre"]), 2),
            "sugar": round(float(r["sugar"]), 2),
            "sodium": round(float(r["sodium"]), 2),
            "calcium": round(float(r["calcium"]), 2),
            "iron": round(float(r["iron"]), 2),
            "typical_minutes": int(rec_time[key]) if key in rec_time else "",
            "label_source": "rules+carbon" if c is not None else "rules",
        })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {len(df)} dishes -> {OUT.relative_to(ROOT)}")
    print("roles:", df["role"].value_counts().to_dict())
    print("diet:", df["diet"].value_counts().to_dict())
    print("cuisine:", df["cuisine"].value_counts().to_dict())
    print("carbon-labelled:", int((df["label_source"] == "rules+carbon").sum()))
    print(f"dropped {len(dropped)} rows by the fat quality filter")


if __name__ == "__main__":
    main()
