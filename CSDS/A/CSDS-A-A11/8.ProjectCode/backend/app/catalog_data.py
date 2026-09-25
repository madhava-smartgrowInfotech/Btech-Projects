"""Source vocabulary the catalogue generator composes products from.

Everything here is original merchandising copy for the Nuvara own-label range.
"""

# Product-line names reused across the range, the way an own-label house brand
# reuses a family name across categories.
LINES = [
    "Aria", "Lumen", "Halden", "Nori", "Veda", "Orin", "Caldera", "Sable",
    "Pell", "Marrow", "Juniper", "Bask", "Torrid", "Cove", "Ashen", "Prism",
    "Wren", "Solace", "Kesta", "Drift", "Fable", "Mirren", "Otto", "Linden",
    "Quill", "Rove", "Saffron", "Tamar", "Vela", "Wisp", "Alto", "Brim",
]

CATEGORIES = {
    "Audio": {
        "slug": "audio",
        "subcategories": ["Headphones", "Earbuds", "Speakers", "Turntables", "Studio"],
        "nouns": [
            "Over-Ear Headphones", "Wireless Earbuds", "Bookshelf Speaker",
            "Portable Speaker", "Studio Monitor", "Belt-Drive Turntable",
            "Open-Back Headphones", "Sport Earbuds", "Soundbar",
            "Desktop DAC", "Conference Mic", "Field Recorder",
        ],
        "tags": [
            "noise-cancelling", "hi-res", "bluetooth", "long-battery", "bass-heavy",
            "studio-grade", "lightweight", "travel", "spatial-audio", "wired",
        ],
        "materials": ["anodised aluminium", "recycled ABS", "walnut veneer", "vegan leather", "steel mesh"],
        "price_range": (49, 640),
        "phrases": [
            "a 40mm bio-cellulose driver tuned for an even midrange",
            "adaptive noise cancellation that samples the room 400 times a second",
            "a transparency mode that keeps conversation intelligible without removing the fit",
            "USB-C fast charge that returns four hours of playback in ten minutes",
            "multipoint pairing that holds a laptop and a phone at the same time",
        ],
    },
    "Home & Living": {
        "slug": "home-living",
        "subcategories": ["Lighting", "Textiles", "Storage", "Decor", "Air"],
        "nouns": [
            "Table Lamp", "Floor Lamp", "Linen Throw", "Wool Rug", "Ceramic Vase",
            "Storage Basket", "Air Purifier", "Diffuser", "Wall Shelf",
            "Cotton Duvet", "Picture Frame", "Room Divider",
        ],
        "tags": [
            "handmade", "natural-fibre", "warm-light", "dimmable", "minimal",
            "oeko-tex", "modular", "quiet", "compact", "scandi",
        ],
        "materials": ["oiled oak", "belgian linen", "glazed stoneware", "powder-coated steel", "rattan"],
        "price_range": (24, 520),
        "phrases": [
            "a stepless dimmer that holds its warmth down to five percent brightness",
            "a stonewashed finish that softens with every wash rather than pilling",
            "a weighted base that stays put on uneven shelving",
            "joinery assembled without visible fixings",
            "a HEPA stack rated for a 38 square metre room on its lowest setting",
        ],
    },
    "Wearables": {
        "slug": "wearables",
        "subcategories": ["Smartwatches", "Trackers", "Rings", "Bands", "Accessories"],
        "nouns": [
            "Smartwatch", "Fitness Tracker", "Sleep Ring", "Woven Watch Band",
            "Leather Watch Strap", "Heart-Rate Band", "GPS Watch",
            "Charging Dock", "Screen Guard", "Titanium Watch",
        ],
        "tags": [
            "sleep-tracking", "heart-rate", "gps", "water-resistant", "long-battery",
            "titanium", "lightweight", "always-on", "coach", "travel",
        ],
        "materials": ["grade-5 titanium", "sapphire glass", "fluoroelastomer", "recycled nylon", "brushed steel"],
        "price_range": (29, 720),
        "phrases": [
            "an optical stack that logs resting heart rate every two minutes overnight",
            "dual-band GNSS that holds a lock under tree cover",
            "seven days of battery with the always-on display left enabled",
            "a case machined from a single titanium billet",
            "recovery scoring built from heart-rate variability rather than step count",
        ],
    },
    "Kitchen": {
        "slug": "kitchen",
        "subcategories": ["Coffee", "Cookware", "Prep", "Storage", "Small Appliances"],
        "nouns": [
            "Pour-Over Kettle", "Burr Grinder", "Espresso Machine", "Cast Iron Skillet",
            "Chef's Knife", "Cutting Board", "Storage Canister", "Stand Mixer",
            "French Press", "Saucepan", "Mixing Bowl Set", "Immersion Blender",
        ],
        "tags": [
            "dishwasher-safe", "induction-ready", "pro-grade", "gooseneck", "stainless",
            "hand-forged", "temperature-control", "compact", "gift", "everyday",
        ],
        "materials": ["tri-ply stainless", "seasoned cast iron", "japanese steel", "end-grain walnut", "borosilicate glass"],
        "price_range": (18, 890),
        "phrases": [
            "variable temperature control in single-degree steps from 40 to 100",
            "conical burrs held in a stepped collar for repeatable grind settings",
            "a flat lid that doubles as a trivet",
            "a hand-forged bevel taken to 15 degrees per side",
            "a pre-seasoned surface that needs no oven curing before first use",
        ],
    },
    "Outdoor": {
        "slug": "outdoor",
        "subcategories": ["Packs", "Shelter", "Lighting", "Hydration", "Apparel"],
        "nouns": [
            "Daypack", "Trekking Pack", "Two-Person Tent", "Camp Lantern",
            "Insulated Bottle", "Rain Shell", "Sleeping Pad", "Trail Stove",
            "Packable Blanket", "Headlamp", "Dry Bag", "Camp Chair",
        ],
        "tags": [
            "waterproof", "packable", "lightweight", "ripstop", "insulated",
            "trail", "cold-weather", "recycled", "high-visibility", "three-season",
        ],
        "materials": ["recycled ripstop nylon", "dyneema composite", "18/8 stainless", "ethically-sourced down", "waxed canvas"],
        "price_range": (22, 640),
        "phrases": [
            "a 20-denier ripstop face fabric with fully taped seams",
            "a frame that carries load on the hips rather than the shoulders",
            "double-wall vacuum insulation rated for 24 hours cold",
            "a pitch that goes up fly-first so the inner stays dry",
            "a beam that throws 180 metres on high and still runs 60 hours on low",
        ],
    },
    "Desk & Office": {
        "slug": "desk-office",
        "subcategories": ["Lighting", "Seating", "Desktop", "Cable", "Paper"],
        "nouns": [
            "Desk Lamp", "Monitor Arm", "Laptop Stand", "Task Chair", "Desk Mat",
            "Cable Tray", "Mechanical Keyboard", "Standing Desk Converter",
            "Notebook Set", "Pen Cup", "Document Tray", "Footrest",
        ],
        "tags": [
            "ergonomic", "adjustable", "warm-light", "minimal", "cable-management",
            "aluminium", "quiet", "hot-swap", "compact", "work-from-home",
        ],
        "materials": ["extruded aluminium", "full-grain leather", "cork composite", "powder-coated steel", "PET felt"],
        "price_range": (16, 760),
        "phrases": [
            "a 95 CRI panel that keeps skin tones honest on video calls",
            "gas-spring tension that holds a 9kg display without drift",
            "a lumbar shelf that adjusts independently of the backrest angle",
            "hot-swap sockets so switches change without a soldering iron",
            "a stitched edge that stops the mat curling at the corners",
        ],
    },
    "Beauty": {
        "slug": "beauty",
        "subcategories": ["Skincare", "Haircare", "Tools", "Fragrance", "Body"],
        "nouns": [
            "Hydrating Serum", "Daily Moisturiser", "Cleansing Balm", "Retinol Night Cream",
            "Scalp Tonic", "Ionic Hair Dryer", "Jade Roller", "Eau de Parfum",
            "Body Oil", "Lip Treatment", "Mineral Sunscreen", "Clay Mask",
        ],
        "tags": [
            "fragrance-free", "vegan", "dermatologist-tested", "sensitive-skin", "spf",
            "refillable", "night-routine", "brightening", "barrier-repair", "travel",
        ],
        "materials": ["post-consumer glass", "aluminium refill", "bamboo cap", "recycled PET", "airless pump"],
        "price_range": (12, 190),
        "phrases": [
            "a 2% encapsulated retinaldehyde that releases over six hours",
            "five weights of hyaluronic acid so hydration sits at different depths",
            "a mineral filter that finishes clear rather than chalky on deeper skin",
            "a refill system that keeps the pump and replaces only the cartridge",
            "a pH held at 5.5 so the barrier is not stripped",
        ],
    },
    "Fitness": {
        "slug": "fitness",
        "subcategories": ["Strength", "Recovery", "Yoga", "Cardio", "Apparel"],
        "nouns": [
            "Adjustable Dumbbell", "Kettlebell", "Resistance Band Set", "Yoga Mat",
            "Foam Roller", "Massage Gun", "Jump Rope", "Suspension Trainer",
            "Weight Bench", "Grip Trainer", "Training Sandbag", "Balance Board",
        ],
        "tags": [
            "home-gym", "recovery", "grip", "non-slip", "space-saving",
            "beginner", "pro-grade", "travel", "quiet", "adjustable",
        ],
        "materials": ["cast urethane", "natural rubber", "cork", "knurled steel", "ballistic nylon"],
        "price_range": (14, 690),
        "phrases": [
            "a dial that steps from 2 to 24kg without changing plates",
            "a urethane shell that will not chip a floor when set down hard",
            "a closed-cell surface that stays grippy once sweat is on it",
            "a brushless motor held under 45 decibels at full stall force",
            "knurling cut deep enough to hold chalk-free",
        ],
    },
}

COLORWAYS = [
    "Graphite", "Bone", "Sage", "Terracotta", "Midnight", "Oat", "Slate",
    "Clay", "Fog", "Ink", "Moss", "Sand", "Ember", "Chalk", "Pine",
]

REVIEW_NAMES = [
    "Mara T.", "Devan R.", "Priya N.", "Callum W.", "Ines O.", "Theo L.",
    "Nadia S.", "Rafe M.", "Yuki H.", "Owen B.", "Lila F.", "Jonas K.",
    "Amara D.", "Petra V.", "Emil G.", "Rosa C.", "Nils A.", "Iris P.",
    "Kofi A.", "Sana J.", "Bruno E.", "Cleo W.", "Hugo Z.", "Tess Q.",
]

REVIEW_TEMPLATES = {
    5: [
        ("Exceeded what I paid for", "Ordered this expecting to send it back and it has not left my {place} since. The {material} finish still looks new after {weeks} weeks."),
        ("Now my default", "I have bought three of these for family. {detail} It is the detail nobody mentions and the one that matters daily."),
        ("Worth the upgrade", "Replaced a cheaper one that lasted eight months. The difference is obvious in the first minute of use."),
    ],
    4: [
        ("Very good, one small gripe", "Does everything well. The only thing I would change is the packaging, which is more layered than it needs to be."),
        ("Solid buy", "Build quality is genuinely good for the price. Took me a couple of days to get used to the sizing but no complaints now."),
        ("Happy with it", "Arrived quickly and matches the photos. Loses a star only because the instructions are thin."),
    ],
    3: [
        ("Fine, not remarkable", "It works. Nothing about it is bad, nothing is memorable either. If it goes on sale it is an easy yes."),
        ("Mixed", "Love the feel, less keen on how it performs after a long session. Middle of the road for me."),
    ],
    2: [
        ("Not for me", "Quality is there but the sizing runs small and the return window is tight. Would suit someone else better."),
        ("Underwhelmed", "Expected more at this price. Works, but I have used cheaper things that did the same job."),
    ],
    1: [
        ("Stopped working", "Failed after five weeks of normal use. Support replaced it without argument, but I would rather it had not happened."),
    ],
}

REVIEW_PLACES = ["kitchen counter", "desk", "living room", "gym bag", "bedside table", "hallway"]
REVIEW_DETAILS = [
    "The weight distribution is right.",
    "It powers on instantly every time.",
    "Cleaning it takes ten seconds.",
    "It is quiet in a way the listing undersells.",
    "It packs down smaller than I expected.",
]

# Shopper segments. Each carries a taste bias used to build the hidden latent
# vector that drives both the generated behaviour stream and twin simulation.
SEGMENTS = [
    {
        "name": "Audio Purist",
        "bias": {"Audio": 0.95, "Desk & Office": 0.45, "Wearables": 0.35},
        "tag_bias": {"hi-res": 0.9, "studio-grade": 0.8, "noise-cancelling": 0.7, "wired": 0.6},
        "price_affinity": 0.72,
    },
    {
        "name": "Home Curator",
        "bias": {"Home & Living": 0.95, "Kitchen": 0.5, "Beauty": 0.4},
        "tag_bias": {"handmade": 0.9, "natural-fibre": 0.8, "minimal": 0.75, "scandi": 0.7},
        "price_affinity": 0.58,
    },
    {
        "name": "Performance Tracker",
        "bias": {"Fitness": 0.9, "Wearables": 0.85, "Outdoor": 0.4},
        "tag_bias": {"heart-rate": 0.85, "recovery": 0.8, "gps": 0.75, "home-gym": 0.7},
        "price_affinity": 0.65,
    },
    {
        "name": "Kitchen Builder",
        "bias": {"Kitchen": 0.95, "Home & Living": 0.45, "Desk & Office": 0.2},
        "tag_bias": {"pro-grade": 0.85, "induction-ready": 0.7, "hand-forged": 0.75, "everyday": 0.6},
        "price_affinity": 0.68,
    },
    {
        "name": "Trail Regular",
        "bias": {"Outdoor": 0.95, "Fitness": 0.5, "Wearables": 0.45},
        "tag_bias": {"waterproof": 0.85, "packable": 0.8, "lightweight": 0.8, "trail": 0.85},
        "price_affinity": 0.6,
    },
    {
        "name": "Desk Optimiser",
        "bias": {"Desk & Office": 0.95, "Audio": 0.5, "Home & Living": 0.4},
        "tag_bias": {"ergonomic": 0.9, "cable-management": 0.75, "adjustable": 0.7, "work-from-home": 0.8},
        "price_affinity": 0.63,
    },
    {
        "name": "Routine Minimalist",
        "bias": {"Beauty": 0.95, "Home & Living": 0.4, "Wearables": 0.25},
        "tag_bias": {"fragrance-free": 0.85, "refillable": 0.8, "sensitive-skin": 0.8, "barrier-repair": 0.7},
        "price_affinity": 0.45,
    },
    {
        "name": "Value Hunter",
        "bias": {"Kitchen": 0.5, "Home & Living": 0.5, "Fitness": 0.45, "Audio": 0.45, "Outdoor": 0.4},
        "tag_bias": {"gift": 0.7, "compact": 0.65, "everyday": 0.7, "beginner": 0.6, "travel": 0.6},
        "price_affinity": 0.2,
    },
]

PERSONA_BLURBS = {
    "Audio Purist": "Compares driver specs before breakfast and owns three pairs of headphones.",
    "Home Curator": "Buys slowly, keeps things for a decade, cares how a room feels at 7pm.",
    "Performance Tracker": "Trains five days a week and reads every recovery metric the band gives back.",
    "Kitchen Builder": "Rebuilding the kitchen one properly-made tool at a time.",
    "Trail Regular": "Out most weekends, counts grams, distrusts anything that is not seam-taped.",
    "Desk Optimiser": "Has opinions about monitor height and a drawer full of cable ties.",
    "Routine Minimalist": "Four products, no fragrance, will not be talked into a fifth step.",
    "Value Hunter": "Waits for the price to move, then buys two.",
}

FIRST_NAMES = [
    "Maya", "Dev", "Priyanka", "Callum", "Ines", "Theo", "Nadia", "Rafe",
    "Yuki", "Owen", "Lila", "Jonas", "Amara", "Petra", "Emil", "Rosa",
    "Nils", "Iris", "Kofi", "Sana", "Bruno", "Cleo", "Hugo", "Tess",
    "Anya", "Mateo", "Freya", "Idris", "Lina", "Oscar", "Zara", "Pablo",
    "Noor", "Ravi", "Elsa", "Jun", "Marta", "Silas", "Adaeze", "Enzo",
    "Kira", "Tomas", "Leilani", "Boris", "Nia", "Viktor", "Suri", "Aldo",
    "Rhea", "Casper",
]

LAST_NAMES = [
    "Ahluwalia", "Bergstrom", "Costa", "Dattani", "Eriksen", "Farrow",
    "Guzman", "Halloran", "Ibori", "Jansen", "Kovac", "Lindqvist",
    "Moreau", "Nakamura", "Okafor", "Petrov", "Quintero", "Rahman",
    "Silva", "Tveit", "Ueda", "Vargas", "Whelan", "Ximenes", "Yilmaz",
    "Zubair",
]

SEARCH_TERMS = [
    "noise cancelling", "warm desk lamp", "cast iron", "running watch",
    "linen throw", "pour over", "trail pack", "retinol", "foam roller",
    "bookshelf speaker", "standing desk", "sleep tracker", "kettlebell",
    "mineral sunscreen", "waterproof shell", "mechanical keyboard",
]
