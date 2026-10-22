"""Shared text preprocessing: cleaning, TF-IDF, stylometric features."""
import re
import string
import numpy as np

_URL = re.compile(r"https?://\S+|www\.\S+")
_MENTION = re.compile(r"[@#]\w+")
_NON_ALPHA = re.compile(r"[^a-zA-Z\s]")
_WS = re.compile(r"\s+")

STOPWORDS = {
    'i','me','my','myself','we','our','ours','ourselves','you','your','yours',
    'yourself','yourselves','he','him','his','himself','she','her','hers',
    'herself','it','its','itself','they','them','their','theirs','themselves',
    'what','which','who','whom','this','that','thatll','these','those','am',
    'is','are','was','were','be','been','being','have','has','had','having',
    'do','does','did','doing','a','an','the','and','but','if','or','because',
    'as','until','while','of','at','by','for','with','about','against',
    'between','into','through','during','before','after','above','below','to',
    'from','up','down','in','out','on','off','over','under','again','further',
    'then','once','here','there','when','where','why','how','all','any',
    'both','each','few','more','most','other','some','such','no','nor','not',
    'only','own','same','so','than','too','very','s','t','can','will','just',
    'don','should','now'
}

LABELS = ["REAL", "PARTIALLY TRUE", "FAKE"]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    t = text.lower()
    t = _URL.sub(" ", t)
    t = _MENTION.sub(" ", t)
    t = t.replace("\n", " ")
    t = _NON_ALPHA.sub(" ", t)
    t = _WS.sub(" ", t).strip()
    tokens = [w for w in t.split() if w not in STOPWORDS and len(w) > 2]
    return " ".join(tokens)


def stylometric_features(raw_texts):
    """25 lightweight handcrafted features per document."""
    feats = []
    for t in raw_texts:
        if not isinstance(t, str):
            t = ""
        words = t.split()
        chars = len(t)
        n_words = max(len(words), 1)
        n_sent = max(len(re.split(r"[.!?]+", t)), 1)
        upper = sum(1 for w in words if w.isupper() and len(w) > 1)
        exclaim = t.count("!")
        question = t.count("?")
        digits = sum(c.isdigit() for c in t)
        urls = len(_URL.findall(t))
        avg_wlen = float(np.mean([len(w) for w in words])) if words else 0.0
        uniq_ratio = len(set(words)) / n_words
        stop_ratio = sum(1 for w in words if w.lower() in STOPWORDS) / n_words
        # sentiment-lexicon proxies (tiny built-in lists -> zero dependency)
        pos_lex = {"true","great","excellent","verified","confirmed","official",
                   "evidence","proven","real","accurate","trust"}
        neg_lex = {"shocking","secret","unbelievable","miracle","hoax","conspiracy",
                   "exposed","urgent","breaking","viral","click","banned","hidden"}
        sens_lex = {"shocking","unbelievable","secret","exposed","urgent","breaking",
                    "miracle","banned","hidden","viral","you wont believe"}
        wl = [w.lower() for w in words]
        pos = sum(1 for w in wl if w in pos_lex) / n_words
        neg = sum(1 for w in wl if w in neg_lex) / n_words
        sens = sum(1 for w in wl if w in sens_lex) / n_words
        caps_ratio = upper / n_words
        punct_ratio = sum(1 for c in t if c in string.punctuation) / max(chars, 1)
        words_per_sent = n_words / n_sent
        long_word_ratio = sum(1 for w in words if len(w) > 6) / n_words
        short_word_ratio = sum(1 for w in words if len(w) <= 3) / n_words
        digit_ratio = digits / max(chars, 1)
        exclaim_flag = 1.0 if exclaim > 2 else 0.0
        question_flag = 1.0 if question > 1 else 0.0
        url_flag = 1.0 if urls > 0 else 0.0
        first_person = sum(1 for w in wl if w in {"i","we","us","our","my"}) / n_words
        superlative = sum(1 for w in wl if w.endswith("est") and len(w) > 5) / n_words
        feats.append([chars, n_words, n_sent, avg_wlen, uniq_ratio, stop_ratio,
                      pos, neg, sens, caps_ratio, upper, exclaim, question,
                      punct_ratio, words_per_sent, long_word_ratio,
                      short_word_ratio, digit_ratio, exclaim_flag,
                      question_flag, url_flag, urls, first_person, superlative,
                      neg - pos])
    return np.array(feats, dtype=float)
