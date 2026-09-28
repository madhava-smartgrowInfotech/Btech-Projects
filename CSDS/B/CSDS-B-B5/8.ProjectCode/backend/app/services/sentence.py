"""Gloss sequence -> English sentence. Rules always work offline; Gemini polishes when online."""
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

from ml.vocab import WORD_TEXT

from ..config import GEMINI_API_KEY, GEMINI_MODEL

GREETINGS = {"HELLO": "Hello", "GOOD_MORNING": "Good morning", "GOOD_NIGHT": "Good night",
             "THANK_YOU": "Thank you", "PLEASED": "Pleased to meet you", "ALRIGHT": "Alright"}
PRONOUNS = {"I": "am", "YOU": "are", "WE": "are", "THEY": "are", "HE": "is", "SHE": "is"}
ADJECTIVES = {"GOOD", "BAD", "HAPPY", "SAD", "SICK", "HOT", "COLD", "NEW", "FAST", "SLOW"}
TIME = {"TODAY", "TOMORROW", "YESTERDAY", "MORNING", "NIGHT"}
PEOPLE = {"MOTHER", "FATHER", "BROTHER", "SISTER", "FRIEND", "FAMILY", "BABY", "DOCTOR", "TEACHER", "POLICE"}
ROLES = {"DOCTOR", "TEACHER", "POLICE"}
PLACES = {"HOSPITAL", "HOUSE", "SCHOOL", "MARKET", "BANK", "OFFICE", "RESTAURANT", "BATHROOM"}
THINGS = {"MEDICINE", "MONEY", "BOOK", "TIME"}


def _word(g):
    if g in WORD_TEXT:
        return WORD_TEXT[g]
    return g.capitalize()  # fingerspelled name / word


def _clause(tokens):
    """One statement without greetings -> sentence text (no final punctuation)."""
    if not tokens:
        return ""
    time_words = [t for t in tokens if t in TIME]
    rest = [t for t in tokens if t not in TIME]
    words, i = [], 0
    while i < len(rest):
        t = rest[i]
        nxt = rest[i + 1] if i + 1 < len(rest) else None
        if t in PRONOUNS or t in PEOPLE:
            subj = _word(t) if t in PRONOUNS else f"my {_word(t)}"
            verb = PRONOUNS.get(t, "is")
            if nxt in ADJECTIVES:
                words += [subj, verb, _word(nxt)]; i += 2; continue
            if nxt in ROLES and t in PRONOUNS:
                words += [subj, verb, "a", _word(nxt)]; i += 2; continue
            if nxt in PLACES:
                go = "go" if t in ("I", "YOU", "WE", "THEY") else "goes"
                words += [subj, "need to" if t == "I" else "", "go" if t == "I" else go, "to the", _word(nxt)]
                i += 2; continue
            if nxt in THINGS:
                need = "need" if t in ("I", "YOU", "WE", "THEY") else "needs"
                words += [subj, need, _word(nxt)]; i += 2; continue
            if nxt is not None and nxt not in WORD_TEXT and t in PRONOUNS:  # fingerspelled name
                words += [subj, verb, _word(nxt)]; i += 2; continue
            words.append(subj if not words else subj.replace("my ", "the ")); i += 1; continue
        words.append(_word(t)); i += 1
    if time_words:
        tw = " ".join(_word(t) for t in time_words)
        words = [tw + ","] + words if words else [tw]
    text = " ".join(w for w in words if w).replace(" ,", ",")
    return text


def rule_sentence(glosses):
    # collapse repeats and the redundant YOU often signed after HOW_ARE_YOU
    gl = []
    for g in glosses:
        if gl and (g == gl[-1] or (g == "YOU" and gl[-1] == "HOW_ARE_YOU")):
            continue
        gl.append(g)
    parts, clause = [], []
    for g in gl:
        if g in GREETINGS or g == "HOW_ARE_YOU":
            if clause:
                parts.append(("stmt", _clause(clause))); clause = []
            parts.append(("greet" if g != "HOW_ARE_YOU" else "q", GREETINGS.get(g, "how are you")))
        else:
            clause.append(g)
    if clause:
        parts.append(("stmt", _clause(clause)))
    out = ""
    for k, (kind, text) in enumerate(parts):
        nxt = parts[k + 1][0] if k + 1 < len(parts) else None
        if not out or out.endswith((".", "?", "!")):
            text = text[:1].upper() + text[1:]
        if kind == "greet":
            out += text + ("," if nxt in ("q",) else ".") + " "
        elif kind == "q":
            out += text + "? "
        else:
            out += text + ". "
    return out.strip().replace(" i ", " I ")


# ---------------------------------------------------------------- online polish
_online = {"t": 0.0, "ok": False}


def is_online():
    if time.time() - _online["t"] < 20:
        return _online["ok"]
    try:
        socket.create_connection(("generativelanguage.googleapis.com", 443), timeout=1.5).close()
        ok = True
    except OSError:
        ok = False
    _online.update(t=time.time(), ok=ok)
    return ok


_client = None
FALLBACK_MODELS = [GEMINI_MODEL, "gemini-flash-lite-latest"]
POLISH_BUDGET_S = 5.0  # never keep the conversation waiting longer than this
_cooldown: dict[str, float] = {}  # model -> time until which it is skipped (quota / overload)
_pool = ThreadPoolExecutor(2)


def gemini_sentence(glosses, draft):
    global _client
    from google import genai
    from google.genai import types

    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = (
        "You turn Indian Sign Language gloss sequences into one short, natural English sentence "
        "as the signer would say it. Keep the meaning; do not add new facts. Names that are "
        "fingerspelled stay as names. Reply with the sentence only.\n"
        f"Gloss: {' '.join(glosses)}\nRule-based draft: {draft}"
    )
    last = None
    for model in dict.fromkeys(FALLBACK_MODELS):
        if _cooldown.get(model, 0) > time.time():
            continue
        try:
            r = _client.models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=80,
                                                   http_options=types.HttpOptions(timeout=12000),
                                                   automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)),
            )
            text = (r.text or "").strip().strip('"')
            if text:
                return text.splitlines()[0], model
        except Exception as e:  # try the next model
            last = e
            if any(k in str(e) for k in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")):
                _cooldown[model] = time.time() + 300
    raise RuntimeError(f"Gemini unavailable: {last}")


def build_sentence(glosses, use_gemini=True):
    t = time.perf_counter()
    draft = rule_sentence(glosses)
    result = {"sentence": draft, "draft": draft, "source": "rules", "online": False}
    if use_gemini and GEMINI_API_KEY and glosses and is_online():
        result["online"] = True
        try:
            result["sentence"], result["model"] = _pool.submit(gemini_sentence, glosses, draft).result(POLISH_BUDGET_S)
            result["source"] = "gemini"
        except FutureTimeout:
            result["note"] = "Online polish took too long - used the offline sentence"
        except Exception as e:
            result["note"] = str(e)[:200]
    result["latency_ms"] = round((time.perf_counter() - t) * 1000, 1)
    return result
