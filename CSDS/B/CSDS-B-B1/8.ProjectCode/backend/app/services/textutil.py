"""Language detection and multilingual urgency cues (English / Hindi / Hinglish)."""
import re

# Tokens are runs of anything that is not whitespace or punctuation, so Hindi words
# keep their vowel signs (regex \w would split them).
TOKEN_PATTERN = r"[^\s\.,!?।:;()\[\]\"'/\-|]+"
SPLIT_RE = re.compile(TOKEN_PATTERN)

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
LATIN = re.compile(r"[A-Za-z]")
HINGLISH_MARKERS = {
    "hai", "hain", "nahi", "nahin", "mein", "se", "ka", "ki", "ke", "ko", "kar", "karo", "kare", "karein",
    "raha", "rahi", "rahe", "gaya", "gayi", "hua", "hui", "ho", "bahut", "kya", "kyon", "jab", "tak",
    "hamare", "humare", "hum", "log", "aur", "par", "pe", "kripya", "kripaya", "bhi", "din", "mahine",
    "sadak", "paani", "pani", "bijli", "kachra", "ilaake", "ilake", "jaldi", "turant", "sarkar",
}


def detect_language(text: str) -> str:
    """Return 'Hindi', 'Hinglish' or 'English'."""
    deva = len(DEVANAGARI.findall(text))
    latin = len(LATIN.findall(text))
    if deva and deva >= latin:
        return "Hindi"
    words = [w.lower() for w in re.findall(r"[A-Za-z]+", text)]
    hits = sum(w in HINGLISH_MARKERS for w in words)
    if deva or (words and hits >= max(2, 0.12 * len(words))):
        return "Hinglish"
    return "English"


# Each cue group is a named, human-readable factor for the priority model (SHAP explains these).
CUES = {
    "Hazard / accident risk": [
        "danger", "dangerous", "accident", "hazard", "hazardous", "fire", "burning", "smoke", "collapse",
        "collapsed", "sinkhole", "cave in", "cave-in", "open manhole", "manhole", "live wire", "sparking",
        "short circuit", "electric shock", "electrocut", "explosion", "injured", "injury", "death", "died",
        "fatal", "deep pit", "flooding", "flood", "life threatening", "critical",
        "khatra", "khatarnak", "khatarnaak", "durghatna", "haadsa", "hadsa", "aag", "dhuan", "gir gaya",
        "girne", "ghayal", "maut", "current", "jaan",
        "खतरा", "खतरनाक", "दुर्घटना", "हादसा", "आग", "धुआं", "धुआँ", "गिर", "घायल", "मौत", "करंट", "जान",
        "मैनहोल", "बाढ़",
    ],
    "Health risk": [
        "dengue", "malaria", "epidemic", "contaminated", "contamination", "sewage overflow", "raw sewage",
        "toxic", "disease", "sick", "illness", "mosquito", "infection", "stench", "foul smell",
        "bimari", "beemari", "beemar", "machhar", "machar", "ganda pani", "dushit", "badbu",
        "डेंगू", "मलेरिया", "बीमारी", "बीमार", "मच्छर", "दूषित", "गंदा पानी", "संक्रमण", "बदबू",
    ],
    "Urgent language": [
        "urgent", "urgently", "asap", "immediately", "emergency", "at the earliest", "please help",
        "jaldi", "turant", "fauran", "jald",
        "तुरंत", "जल्द", "जल्दी", "फौरन", "आपात",
    ],
    "Vulnerable people": [
        "children", "child", "kids", "school", "elderly", "senior citizen", "old age", "women", "ladies",
        "pregnant", "patients", "hospital", "disabled",
        "bachche", "bacche", "bachon", "bujurg", "mahila", "mahilaye", "mahilaon", "marij", "mareez",
        "बच्चे", "बच्चों", "बुजुर्ग", "महिला", "महिलाओं", "स्कूल", "मरीज", "अस्पताल",
    ],
    "Service outage": [
        "not working", "no water", "no power", "power cut", "outage", "shortage", "not collected",
        "blocked", "overflowing", "no electricity", "no supply", "not functioning",
        "band hai", "nahi aa raha", "nahi aa rahi", "nahi aata", "kharab", "gayab", "nahi hua",
        "बंद", "नहीं आ रहा", "नहीं आ रही", "खराब", "गायब", "कटौती",
    ],
    "Long pending": [
        "days", "weeks", "months", "since", "year", "years", "long time",
        "din se", "hafte", "hafton", "mahine", "mahino", "saal",
        "दिन", "हफ्ते", "सप्ताह", "महीने", "महीनों", "साल",
    ],
    "Wide area affected": [
        "entire", "whole", "all residents", "colony", "locality", "everyone", "many people", "whole area",
        "neighbourhood", "neighborhood", "pura", "poora", "puri", "sabhi", "sab log", "mohalla",
        "पूरे", "पूरा", "पूरी", "सभी", "सब लोग", "मोहल्ले", "कॉलोनी", "इलाके",
    ],
    "Repeated complaint": [
        "again", "repeatedly", "multiple complaints", "many times", "already complained", "still not",
        "several times", "no action", "baar baar", "phir se", "kai baar", "ab tak", "abhi tak",
        "बार-बार", "बार बार", "फिर से", "कई बार", "अब तक", "अभी तक", "कोई कार्रवाई नहीं",
    ],
}
CUE_NAMES = list(CUES)


def cue_counts(text: str) -> dict:
    t = " " + text.lower() + " "
    return {name: sum(t.count(k) for k in keys) for name, keys in CUES.items()}


def cue_hits(text: str) -> dict:
    """Which words of each cue group actually appear (for the explanation panel)."""
    t = text.lower()
    return {name: [k for k in keys if k in t] for name, keys in CUES.items() if any(k in t for k in keys)}
