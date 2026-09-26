"""Stage 1 - URL feature extraction.

Features are grouped exactly as the project objectives describe:
    * lexical    - counts and ratios computed over the raw URL string
    * structural - how the URL is put together (scheme, host type, depth...)
    * domain     - properties of the registered domain / TLD / subdomains

Everything here works offline: no DNS, WHOIS or HTTP is needed, so the
same code runs identically at training time and at real-time checking.
"""
from __future__ import annotations

import ipaddress
import math
import re
from collections import Counter
from urllib.parse import urlsplit, unquote

import numpy as np

# --------------------------------------------------------------------------- #
# Reference lists
# --------------------------------------------------------------------------- #
SUSPICIOUS_WORDS = [
    "login", "signin", "log-in", "sign-in", "verify", "verification", "secure",
    "security", "account", "update", "confirm", "bank", "banking", "wallet",
    "password", "credential", "billing", "invoice", "payment", "pay", "free",
    "bonus", "prize", "winner", "lucky", "alert", "suspend", "limited", "unlock",
    "recover", "support", "helpdesk", "webscr", "cmd", "admin", "wp-admin",
    "wp-includes", "wp-content", "cgi-bin", "auth", "session", "token",
]

BRAND_NAMES = [
    "paypal", "apple", "icloud", "microsoft", "office365", "outlook", "google",
    "gmail", "facebook", "instagram", "whatsapp", "amazon", "netflix", "ebay",
    "chase", "wellsfargo", "bankofamerica", "citibank", "hsbc", "barclays",
    "santander", "sbi", "hdfc", "icici", "axis", "dropbox", "linkedin",
    "twitter", "yahoo", "adobe", "dhl", "fedex", "usps", "irs", "steam",
    "coinbase", "binance", "metamask", "onedrive", "sharepoint", "docusign",
]

SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq", "xyz", "top", "zip", "mov", "click", "link",
    "work", "buzz", "rest", "icu", "cam", "surf", "monster", "quest", "loan",
    "download", "win", "bid", "stream", "review", "party", "racing", "date",
    "faith", "science", "cricket", "accountant", "men", "gdn", "pw", "cc",
    "info", "biz", "ru", "su", "cn",
}

COMMON_TLDS = {"com", "org", "net", "edu", "gov", "mil", "int"}

URL_SHORTENERS = {
    "bit.ly", "goo.gl", "tinyurl.com", "t.co", "ow.ly", "is.gd", "buff.ly",
    "cutt.ly", "rb.gy", "shorturl.at", "tiny.cc", "lnkd.in", "rebrand.ly",
    "t.ly", "s.id", "v.gd", "bl.ink", "short.io", "adf.ly", "bc.vc",
}

# Popular legitimate registered domains (a small offline stand-in for a
# Tranco/Alexa top-sites list). Used as a domain-reputation feature.
POPULAR_DOMAINS = {
    "google", "youtube", "facebook", "instagram", "whatsapp", "twitter", "x", "linkedin",
    "wikipedia", "amazon", "apple", "microsoft", "live", "outlook", "office", "netflix",
    "reddit", "yahoo", "bing", "github", "stackoverflow", "medium", "quora", "pinterest",
    "tumblr", "ebay", "paypal", "dropbox", "adobe", "zoom", "slack", "spotify", "twitch",
    "discord", "telegram", "signal", "mozilla", "cloudflare", "wordpress", "blogspot",
    "flipkart", "myntra", "snapdeal", "paytm", "phonepe", "irctc", "hdfcbank", "icicibank",
    "sbi", "onlinesbi", "axisbank", "kotak", "zomato", "swiggy", "ola", "uber", "airbnb",
    "booking", "expedia", "tripadvisor", "makemytrip", "nytimes", "bbc", "cnn", "reuters",
    "theguardian", "ndtv", "timesofindia", "hindustantimes", "indiatimes", "espn", "imdb",
    "coursera", "udemy", "khanacademy", "edx", "mit", "stanford", "harvard", "nasa",
    "nih", "who", "un", "gov", "nic", "chase", "wellsfargo", "bankofamerica", "citi",
    "hsbc", "barclays", "santander", "capitalone", "americanexpress", "visa", "mastercard",
    "coinbase", "binance", "steampowered", "epicgames", "xbox", "playstation", "nintendo",
    "samsung", "sony", "dell", "hp", "lenovo", "intel", "amd", "nvidia", "oracle", "ibm",
    "salesforce", "shopify", "etsy", "walmart", "target", "bestbuy", "costco", "ikea",
    "nike", "adidas", "fedex", "dhl", "ups", "usps", "indiapost", "bluedart", "aajtak",
    "godaddy", "namecheap", "vercel", "netlify", "heroku", "digitalocean", "anthropic",
    "openai", "huggingface", "kaggle", "arxiv", "ieee", "acm", "springer", "sciencedirect",
}

# Second-level public suffixes so "example.co.uk" -> domain "example"
TWO_LEVEL_SUFFIXES = {
    "co.uk", "org.uk", "ac.uk", "gov.uk", "me.uk", "net.uk", "co.in", "net.in",
    "org.in", "ac.in", "gov.in", "co.jp", "ne.jp", "or.jp", "ac.jp", "com.au",
    "net.au", "org.au", "edu.au", "gov.au", "com.br", "com.cn", "com.mx",
    "com.ar", "com.tr", "com.sg", "com.my", "com.hk", "co.za", "co.kr",
    "co.nz", "com.ng", "com.pk", "com.bd", "com.ph", "com.vn", "com.tw",
}

FEATURE_NAMES: list[str] = [
    # lexical
    "url_length", "host_length", "path_length", "query_length", "fragment_length",
    "num_dots", "num_hyphens", "num_underscores", "num_slashes", "num_digits",
    "digit_ratio", "num_special_chars", "has_at_symbol", "num_query_params",
    "num_equals", "num_ampersands", "num_percent", "url_entropy",
    "suspicious_word_count", "longest_token_length", "has_https_in_path_or_host",
    "has_encoded_chars", "letter_ratio",
    # structural
    "is_ip_host", "has_port", "nonstandard_port",
    "num_subdomains", "path_depth", "has_double_slash_in_path",
    "is_url_shortener", "has_file_extension", "has_executable_extension",
    # domain
    "domain_length", "domain_entropy", "domain_digit_count", "domain_hyphen_count",
    "domain_vowel_ratio", "domain_max_consonant_run", "tld_length",
    "is_suspicious_tld", "is_common_tld", "brand_in_domain", "brand_outside_domain",
    "subdomain_length", "subdomain_has_digit", "tld_in_subdomain", "is_popular_domain",
]

_SPECIAL_CHARS = set("@?=&%~#!$*+,;:'\"<>[]{}|\\^`")
_TOKEN_SPLIT = re.compile(r"[^A-Za-z0-9]+")
_BRAND_RE = re.compile("|".join(sorted(BRAND_NAMES, key=len, reverse=True)))
_SUSP_RE = re.compile("|".join(re.escape(w) for w in SUSPICIOUS_WORDS))
_EXEC_EXT = re.compile(r"\.(exe|scr|bat|cmd|msi|apk|jar|vbs|js|ps1|dll|zip|rar|7z)$", re.I)
_FILE_EXT = re.compile(r"\.[a-z0-9]{1,5}$", re.I)
_TLD_TOKENS = {"com", "net", "org", "co", "in", "uk", "gov", "edu"}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _safe_split(url: str):
    """urlsplit that never raises (malformed ports / brackets are common in the wild)."""
    try:
        parts = urlsplit(url)
        _ = parts.port, parts.hostname
        return parts
    except ValueError:
        cleaned = re.sub(r"[\[\]]", "", url)
        cleaned = re.sub(r"^([a-zA-Z][a-zA-Z0-9+.-]*://[^/?#]*?):[^0-9/?#][^/?#]*", r"\1", cleaned)
        try:
            parts = urlsplit(cleaned)
            _ = parts.port, parts.hostname
            return parts
        except ValueError:
            return urlsplit("http://invalid.invalid" + re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://[^/]*", "", cleaned))


def normalize_url(url: str) -> str:
    """Trim, lower-case the scheme/host, and make sure a scheme is present."""
    url = (url or "").strip().replace(" ", "%20")
    if not url:
        return url
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "http://" + url
    parts = _safe_split(url)
    host = (parts.hostname or "").lower()
    if host.startswith("www."):        # canonical form: the dataset stores hosts without www.
        host = host[4:]
    if parts.port:
        host = f"{host}:{parts.port}"
    if parts.username:
        cred = parts.username + (":" + parts.password if parts.password else "")
        host = f"{cred}@{host}"
    rebuilt = f"{parts.scheme.lower()}://{host}{parts.path or ''}"
    if parts.query:
        rebuilt += "?" + parts.query
    if parts.fragment:
        rebuilt += "#" + parts.fragment
    return rebuilt


def shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    n = len(text)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def split_host(host: str) -> tuple[str, str, str]:
    """Return (subdomain, registered_domain, tld) for a hostname."""
    host = host.lower().strip(".")
    labels = host.split(".")
    if len(labels) < 2:
        return "", host, ""
    last_two = ".".join(labels[-2:])
    if last_two in TWO_LEVEL_SUFFIXES and len(labels) >= 3:
        tld = last_two
        domain = labels[-3]
        sub = ".".join(labels[:-3])
    else:
        tld = labels[-1]
        domain = labels[-2]
        sub = ".".join(labels[:-2])
    return sub, domain, tld


def is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return bool(re.fullmatch(r"0x[0-9a-f]+|\d{8,10}", host or ""))


def _max_consonant_run(text: str) -> int:
    best = cur = 0
    for ch in text:
        if ch.isalpha() and ch not in "aeiou":
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


# --------------------------------------------------------------------------- #
# Main extractor
# --------------------------------------------------------------------------- #
def extract_features(url: str) -> dict[str, float]:
    """Compute the full feature dictionary for one URL."""
    norm = normalize_url(url)
    decoded = unquote(norm)
    parts = _safe_split(norm)
    host = (parts.hostname or "").lower()
    path = parts.path or ""
    query = parts.query or ""
    fragment = parts.fragment or ""
    lower = norm.lower()
    sub, domain, tld = split_host(host)
    ip_host = is_ip(host)

    tokens = [t for t in _TOKEN_SPLIT.split(lower) if t]
    digits = sum(c.isdigit() for c in norm)
    letters = sum(c.isalpha() for c in norm)
    length = max(len(norm), 1)

    brand_in_domain = int(bool(_BRAND_RE.search(domain))) if domain else 0
    brand_elsewhere = int(bool(_BRAND_RE.search(sub + path + query))) and not brand_in_domain

    f: dict[str, float] = {
        # ---- lexical -------------------------------------------------------
        "url_length": len(norm),
        "host_length": len(host),
        "path_length": len(path),
        "query_length": len(query),
        "fragment_length": len(fragment),
        "num_dots": norm.count("."),
        "num_hyphens": norm.count("-"),
        "num_underscores": norm.count("_"),
        "num_slashes": norm.count("/") - 2,       # ignore the scheme's //
        "num_digits": digits,
        "digit_ratio": digits / length,
        "num_special_chars": sum(c in _SPECIAL_CHARS for c in norm),
        "has_at_symbol": int("@" in norm),
        "num_query_params": len([p for p in query.split("&") if p]) if query else 0,
        "num_equals": norm.count("="),
        "num_ampersands": norm.count("&"),
        "num_percent": norm.count("%"),
        "url_entropy": shannon_entropy(lower),
        "suspicious_word_count": len(_SUSP_RE.findall(lower)),
        "longest_token_length": max((len(t) for t in tokens), default=0),
        "has_https_in_path_or_host": int("https" in host or "https" in path.lower()),
        "has_encoded_chars": int(decoded != norm),
        "letter_ratio": letters / length,
        # ---- structural ----------------------------------------------------
        "is_ip_host": int(ip_host),
        "has_port": int(parts.port is not None),
        "nonstandard_port": int(parts.port not in (None, 80, 443)),
        "num_subdomains": 0 if ip_host or not sub else sub.count(".") + 1,
        "path_depth": len([p for p in path.split("/") if p]),
        "has_double_slash_in_path": int("//" in path),
        "is_url_shortener": int(host in URL_SHORTENERS or f"{domain}.{tld}" in URL_SHORTENERS),
        "has_file_extension": int(bool(_FILE_EXT.search(path.split("/")[-1]))) if path else 0,
        "has_executable_extension": int(bool(_EXEC_EXT.search(path))),
        # ---- domain --------------------------------------------------------
        "domain_length": len(domain),
        "domain_entropy": shannon_entropy(domain),
        "domain_digit_count": sum(c.isdigit() for c in domain),
        "domain_hyphen_count": domain.count("-"),
        "domain_vowel_ratio": (sum(c in "aeiou" for c in domain) / len(domain)) if domain else 0.0,
        "domain_max_consonant_run": _max_consonant_run(domain),
        "tld_length": len(tld),
        "is_suspicious_tld": int(tld.split(".")[-1] in SUSPICIOUS_TLDS),
        "is_common_tld": int(tld.split(".")[-1] in COMMON_TLDS),
        "brand_in_domain": brand_in_domain,
        "brand_outside_domain": int(brand_elsewhere),
        "subdomain_length": len(sub),
        "subdomain_has_digit": int(any(c.isdigit() for c in sub)),
        "tld_in_subdomain": int(any(t in _TLD_TOKENS for t in sub.split(".") if t)),
        "is_popular_domain": int(domain in POPULAR_DOMAINS and not ip_host),
    }
    return f


def features_to_vector(feats: dict[str, float]) -> np.ndarray:
    return np.array([feats[name] for name in FEATURE_NAMES], dtype=np.float64)


def featurize_urls(urls) -> np.ndarray:
    """Vectorised extraction for a sequence of URLs -> (n, n_features) array."""
    rows = np.empty((len(urls), len(FEATURE_NAMES)), dtype=np.float64)
    for i, u in enumerate(urls):
        rows[i] = features_to_vector(extract_features(u))
    return rows


def explain_features(feats: dict[str, float]) -> list[str]:
    """Human-readable red flags derived from the extracted features."""
    flags = []
    if feats["is_ip_host"]:
        flags.append("Host is a raw IP address instead of a domain name")
    if feats["has_at_symbol"]:
        flags.append("Contains '@' - browsers ignore everything before it")
    if feats["brand_in_domain"] and not feats["is_popular_domain"]:
        flags.append("Registered domain imitates a well-known brand but is not the official site")
    if feats["brand_outside_domain"]:
        flags.append("A well-known brand name appears outside the registered domain")
    if feats["is_suspicious_tld"]:
        flags.append("Top-level domain is frequently abused by phishing campaigns")
    if feats["num_subdomains"] >= 3:
        flags.append(f"Unusually many subdomains ({int(feats['num_subdomains'])})")
    if feats["suspicious_word_count"] >= 2:
        flags.append(f"Contains {int(feats['suspicious_word_count'])} credential-related keywords")
    if feats["url_length"] > 75:
        flags.append(f"Very long URL ({int(feats['url_length'])} characters)")
    if feats["has_https_in_path_or_host"]:
        flags.append("'https' used inside the hostname/path to look secure")
    if feats["is_url_shortener"]:
        flags.append("URL shortener hides the real destination")
    if feats["has_executable_extension"]:
        flags.append("Points to an executable or archive file")
    if feats["domain_hyphen_count"] >= 2:
        flags.append("Registered domain contains multiple hyphens")
    if feats["tld_in_subdomain"]:
        flags.append("A TLD-like token (com/net/...) appears in the subdomain")
    if feats["has_encoded_chars"]:
        flags.append("Percent-encoded characters obscure the URL")
    if feats["nonstandard_port"]:
        flags.append("Uses a non-standard port")
    if feats["has_double_slash_in_path"]:
        flags.append("Contains '//' inside the path (redirection trick)")
    return flags
