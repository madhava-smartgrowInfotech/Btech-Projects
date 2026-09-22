"""Scam-pattern rules for Indian UPI fraud messages in English, Hindi and Telugu (native + romanised).

Each rule has a weight (how strongly it signals a scam on its own), an optional scam category
and one or more regular expressions. Rules are combined with the NLP model as a noisy-OR, so a
single weak cue (for example "today") never makes a message a scam by itself.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

FLAGS = re.IGNORECASE | re.UNICODE

# Words that turn "share your OTP" into the genuine advice "never share your OTP".
NEGATION = re.compile(
    r"(never|do not|don't|dont|not|no one|mat|na karein|nahi|न करें|मत|कभी नहीं|వద్దు|cheyyakandi|adagadu|evaritho)\W*(\w+\W+){0,4}$",
    FLAGS,
)


@dataclass(frozen=True)
class Rule:
    id: str
    weight: float
    category: str | None
    patterns: tuple[re.Pattern, ...]
    negatable: bool = False


def _r(*patterns: str) -> tuple[re.Pattern, ...]:
    return tuple(re.compile(p, FLAGS) for p in patterns)


RULES: list[Rule] = [
    Rule(
        "kyc_expiry",
        0.5,
        "kyc_fraud",
        _r(
            r"\bKYC\b.{0,40}?(expir|update|pending|verif|block|suspend|deactivat)",
            r"(PAN|Aadhaar)[- ]?KYC",
            r"(KYC|केवाईसी).{0,30}?(समाप्त|अपडेट|सत्यापन|ब्लॉक|बंद)",
            r"(KYC|కేవైసీ).{0,30}?(ముగుస్తుంది|అప్‌డేట్|ధృవీకరణ|బ్లాక్|నిలిపి)",
            r"KYC\s+(update|band|block)",
        ),
    ),
    Rule(
        "account_block_threat",
        0.35,
        "kyc_fraud",
        _r(
            r"(account|a/c|UPI ID).{0,40}?(will be|is|has been)\s+(blocked|suspended|deactivated|closed|frozen)",
            r"\b(SUSPENDED|BLOCKED)\b",
            r"(खाता|अकाउंट).{0,25}?(बंद|ब्लॉक)",
            r"(ఖాతా|అకౌంట్).{0,25}?(బ్లాక్|నిలిపివేయ)",
            r"account.{0,20}?(band ho|block avutundi|block ho)",
        ),
    ),
    Rule(
        "pin_to_receive",
        0.65,
        "collect_request",
        _r(
            r"(PIN|पिन).{0,50}?(to receive|to get|to withdraw|to credit|receive it|पाने|पाएँ|निकालने)",
            r"(to receive|to get|to withdraw|पैसा पाने|పొందడానికి|తీసుకోవడానికి|raavadaniki|receive karne|paane ke liye).{0,60}?(PIN|पिन)",
            r"(PIN).{0,40}?(ఎంటర్|ఇవ్వండి|daalein|enter cheyandi)",
        ),
    ),
    Rule(
        "approve_to_receive",
        0.6,
        "collect_request",
        _r(
            r"(approve|accept|स्वीकार|ఆమోది|approve karein|accept karke|accept chesi|approve chesi).{0,70}?(receive|get|credit|refund|money back|रिफंड|पैसा|जमा|పొంద|జమ|డబ్బు|wapas|dabbu)",
            r"(receive|get|refund|पाने|पैसा|పొంద|raavadaniki|paane).{0,60}?(approve|accept|स्वीकार|ఆమోది)",
            r"collect request",
            r"कलेक्ट अनुरोध|కలెక్ట్ అభ్యర్థన",
        ),
    ),
    Rule("refund_cashback", 0.2, "refund_scam", _r(r"\b(refund|cashback)\b", r"रिफंड|कैशबैक|రీఫండ్|క్యాష్‌బ్యాక్|paisa wapas")),
    Rule(
        "prize_lottery",
        0.45,
        "lottery_prize",
        _r(
            r"\b(won|winner|WINNER|lottery|lucky draw|jackpot|you are selected|claim (your|now|before))\b",
            r"जीते|इनाम|लॉटरी|लकी ड्रॉ|बधाई हो",
            r"గెలుచుకున్నారు|బహుమతి|లాటరీ|లక్కీ డ్రా",
            r"\b(inaam|jeeta|gelicharu|lottery gelicharu)\b",
        ),
    ),
    Rule(
        "fee_before_payout",
        0.35,
        "loan_fee",
        _r(
            r"(processing|registration|file|clearance|insurance|redelivery|verification)\s+(fee|charge)",
            r"(प्रोसेसिंग|रजिस्ट्रेशन|फ़ाइल|क्लियरेंस)\s*(फीस|चार्ज)",
            r"(ప్రాసెసింగ్|రిజిస్ట్రేషన్|ఫైల్|క్లియరెన్స్)\s*(ఫీజు|చార్జ్)",
            r"(file charge|fees bharein|fee kattandi|deposit bhejein|deposit pampandi)",
        ),
    ),
    Rule(
        "share_otp_pin",
        0.6,
        "otp_pin_request",
        _r(
            r"(share|tell|send|reply with|give|provide)\b.{0,25}?\b(OTP|UPI PIN|PIN)\b",
            r"(OTP|PIN).{0,30}?(बताएँ|बताइए|batayein|bataiye|చెప్పండి|cheppandi)",
            r"मिला OTP|వచ్చిన OTP",
        ),
        negatable=True,
    ),
    Rule(
        "urgency",
        0.12,
        None,
        _r(
            r"\b(urgent|urgently|immediately|within \d+ ?(hours|hrs|minutes|mins)|today|tonight|right now|avoid permanent)\b",
            r"तुरंत|अभी|आज रात|जल्दी|ज़रूरी",
            r"వెంటనే|ఈ రోజు|ఈ రాత్రి|అర్జెంట్",
            r"\b(turant|ventane|jaldi)\b",
        ),
    ),
    Rule(
        "suspicious_link",
        0.4,
        None,
        _r(
            r"https?://[^\s]*\.(top|xyz|click|online|site|info|cc|link|buzz|live|icu)\b",
            r"https?://[^\s]*(verify|kyc|refund|reward|claim|secure-bank|update|parcel|lucky)[^\s]*",
        ),
    ),
    Rule("any_link", 0.08, None, _r(r"https?://\S+|www\.\S+")),
    Rule(
        "power_disconnection",
        0.5,
        "bill_disconnection",
        _r(
            r"(electricity|power|current|connection).{0,50}?(disconnect|cut|will be cut)",
            r"(बिजली).{0,30}?(काट|कट)",
            r"(కరెంట్).{0,30}?(కట్)",
            r"(bijli|current).{0,30}?(kaat|cut avutundi)",
        ),
    ),
    Rule(
        "job_task_offer",
        0.45,
        "job_task",
        _r(
            r"(part[- ]time job|work from home|liking videos|daily payment|task commission|prepaid task|unlock tasks|earn Rs)",
            r"पार्ट टाइम|घर बैठे|टास्क",
            r"పార్ట్ టైమ్|ఇంటి నుండే|టాస్క్",
            r"(ghar baithe|intlo nunde|task unlock|task kosam)",
        ),
    ),
    Rule("customs_parcel", 0.45, "courier_customs", _r(r"(held at customs|customs|clearance fee|delivery failed)", r"कस्टम", r"కస్టమ్స్")),
    Rule(
        "instant_loan",
        0.35,
        "loan_fee",
        _r(r"(pre-approved|instant loan|loan is sanctioned|loan approve|without documents)", r"लोन मंज़ूर|बिना कागज़ात", r"లోన్ ఆమోదం|డాక్యుమెంట్లు లేకుండా"),
    ),
    Rule(
        "wrong_transfer_return",
        0.5,
        "wrong_transfer",
        _r(
            r"(by mistake).{0,60}?(return|refund|send back)",
            r"(गलती से).{0,60}?(वापस)",
            r"(పొరపాటున).{0,60}?(తిరిగి)",
            r"(galti se|porapatuna).{0,60}?(wapas|tirigi)",
        ),
    ),
    Rule(
        "impersonation",
        0.45,
        "impersonation",
        _r(
            r"(this is my new number|my phone broke|new number)",
            r"(police|cyber cell|arrest|Aadhaar is linked to a crime)",
            r"नया नंबर|गिरफ्तार|साइबर सेल",
            r"కొత్త నంబర్|అరెస్ట్|సైబర్ సెల్",
            r"(cyber cell|arrest avvakunda|arrest se)",
        ),
    ),
    Rule(
        "investment_doubling",
        0.45,
        "investment",
        _r(
            r"(double your money|guaranteed|\d{2,3}% returns|crypto plan|stock tips)",
            r"दोगुना|पक्का पाएँ",
            r"రెట్టింపు|ఖచ్చితంగా పొందండి",
            r"(paisa double|dabbu double)",
        ),
    ),
    Rule(
        "pay_to_upi_id",
        0.1,
        None,
        _r(r"(send|pay|refund|return)\b.{0,40}?[a-z0-9._-]{2,}@[a-z]{2,}", r"[a-z0-9._-]{2,}@[a-z]{2,}.{0,20}?(पर भेजें|కి పంపండి|pampandi|bhejein)"),
    ),
]

RULE_BY_ID = {r.id: r for r in RULES}

UPI_RE = re.compile(r"\b[a-zA-Z0-9._-]{2,64}@[a-zA-Z]{2,32}(?![.\w@])")
URL_RE = re.compile(r"https?://[^\s,]+|www\.[^\s,]+", FLAGS)
PHONE_RE = re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)")
AMOUNT_RE = re.compile(r"(?:Rs\.?|INR|₹)\s?([\d,]+(?:\.\d{1,2})?)", FLAGS)

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
TELUGU = re.compile(r"[ఀ-౿]")
HINGLISH = re.compile(r"\b(aapka|aapke|aapne|karein|karke|hai|hain|paisa|bhej|bhejein|turant|nahi|ke liye|mein|daalein|kijiye|jayega|raha|gaya)\b", FLAGS)
TENGLISH = re.compile(r"\b(cheyandi|meeru|mee|meeku|avutundi|pampandi|dabbu|ventane|kosam|undi|ayindi|nundi|chesi|ee roju)\b", FLAGS)


def detect_language(text: str) -> tuple[str, str]:
    """Returns (language, script): language en|hi|te, script native|latin."""
    if TELUGU.search(text):
        return "te", "native"
    if DEVANAGARI.search(text):
        return "hi", "native"
    te, hi = len(TENGLISH.findall(text)), len(HINGLISH.findall(text))
    if te >= 2 and te >= hi:
        return "te", "latin"
    if hi >= 2:
        return "hi", "latin"
    return "en", "latin"


def _negated(text: str, start: int) -> bool:
    return bool(NEGATION.search(text[max(0, start - 40) : start]))


def match_rules(text: str) -> list[dict]:
    """All rule hits with character spans."""
    hits: list[dict] = []
    for rule in RULES:
        spans = []
        for pattern in rule.patterns:
            for m in pattern.finditer(text):
                if rule.negatable and _negated(text, m.start()):
                    continue
                spans.append((m.start(), m.end()))
        if spans:
            hits.append({"rule": rule.id, "weight": rule.weight, "category": rule.category, "spans": sorted(set(spans))})
    return hits


def rules_score(hits: list[dict]) -> float:
    remaining = 1.0
    for h in hits:
        remaining *= 1.0 - h["weight"]
    return min(0.95, 1.0 - remaining)


def extract_entities(text: str) -> dict:
    upi_ids = sorted({m.group(0).lower() for m in UPI_RE.finditer(text) if not m.group(0).lower().endswith((".com", ".in"))})
    urls = sorted({m.group(0).rstrip(".") for m in URL_RE.finditer(text)})
    phones = sorted({re.sub(r"\D", "", m.group(0))[-10:] for m in PHONE_RE.finditer(text)})
    amounts = []
    for m in AMOUNT_RE.finditer(text):
        try:
            amounts.append(float(m.group(1).replace(",", "")))
        except ValueError:
            continue
    return {"upi_ids": upi_ids, "urls": urls, "phones": phones, "amounts": sorted(set(amounts))}
