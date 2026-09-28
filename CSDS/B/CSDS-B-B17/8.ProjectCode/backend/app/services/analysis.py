"""Emotion timeline, escalation flags and the agent QA scorecard (transparent rules with evidence)."""
import re

import numpy as np

TEXT_W, VOICE_W = 0.75, 0.25
ESCALATION = re.compile(r"\b(manager|supervisor|complaint|complain|unacceptable|ridiculous|worst|lawyer|cancel my account|"
                        r"never again|terrible|disgusting|fed up|speak to someone else)\b", re.I)


def voice_valence(v):
    if not v:
        return None
    return v.get("happy", 0) - v.get("angry", 0) - 0.5 * v.get("sad", 0)


def fuse(segments):
    """Adds valence (-1..1) and an emotion label to every segment, from text sentiment + voice emotion."""
    seen_negative = {"agent": False, "customer": False}
    for s in segments:
        vv = voice_valence(s.get("voice"))
        val = s["sentiment"]["score"] if vv is None else TEXT_W * s["sentiment"]["score"] + VOICE_W * vv
        s["valence"] = round(float(val), 3)
        angry_voice = (s.get("voice") or {}).get("angry", 0) >= 0.6
        if val <= -0.3:
            label = "angry" if angry_voice and s["sentiment"]["label"] == "negative" and val <= -0.5 else "frustrated"
        elif val < -0.1:
            label = "concerned"
        elif val < 0.2:
            label = "neutral"
        else:
            label = "relieved" if seen_negative[s["speaker"]] else "satisfied"
        if val <= -0.1:
            seen_negative[s["speaker"]] = True
        s["emotion"] = label
    return segments


def flags(segments, gaps):
    out = []
    streak = 0
    for s in segments:
        if s["speaker"] != "customer":
            continue
        m = ESCALATION.search(s["text"])
        if m:
            out.append({"t": s["start"], "type": "escalation_language", "severity": "high",
                        "text": f"Customer said \"{m.group(0)}\": {s['text'][:140]}"})
        if s["valence"] <= -0.45:
            out.append({"t": s["start"], "type": "strong_negative_emotion", "severity": "medium",
                        "text": f"Customer {s['emotion']} (valence {s['valence']:+.2f})"})
        streak = streak + 1 if s["valence"] <= -0.1 else 0
        if streak == 3:
            out.append({"t": s["start"], "type": "sustained_frustration", "severity": "high",
                        "text": "Customer negative for three turns in a row"})
    for start, length in gaps:
        if length >= 5:
            out.append({"t": start, "type": "long_silence", "severity": "medium",
                        "text": f"{length:.1f}s of silence / hold"})
    return sorted(out, key=lambda f: f["t"])


def _total(iv):
    return sum(e - s for s, e in iv)


def talk_stats(activity, duration):
    a, c = activity.get("agent", []), activity.get("customer", [])
    merged = sorted(a + c)
    gaps, end = [], merged[0][0] if merged else 0.0
    for s, e in merged:
        if s - end > 0:
            gaps.append((round(end, 2), round(s - end, 2)))
        end = max(end, e)

    def interrupts(first, second):  # `second` starts talking while `first` is mid-sentence
        n = 0
        for s, _ in second:
            if any(fs + 0.3 < s < fe - 0.3 for fs, fe in first):
                n += 1
        return n

    at, ct = _total(a), _total(c)
    return {
        "agent_talk": round(at, 1), "customer_talk": round(ct, 1),
        "agent_share": round(at / (at + ct), 3) if at + ct else None,
        "silence_total": round(sum(g for _, g in gaps if g >= 3), 1),
        "gaps": [g for g in gaps if g[1] >= 3],
        "longest_silence": round(max([g for _, g in gaps], default=0), 1),
        "agent_interruptions": interrupts(c, a), "customer_interruptions": interrupts(a, c),
        "duration": duration,
    }


GREETING = re.compile(r"\b(thank(s| you) for calling|hello|hi|good (morning|afternoon|evening)|welcome)\b", re.I)
INTRO = re.compile(r"\b(my name is|this is \w+|speaking|you are speaking with|you're speaking with)\b", re.I)
EMPATHY = re.compile(r"\b(sorry|apologi[sz]e|i understand|i can imagine|frustrating|i appreciate|your concern|"
                     r"happy to help|glad i could help|no problem at all|i know how)\b", re.I)
DONE = re.compile(r"\b(i have|i've|has been|is now|was)\s+(now\s+)?(issued|processed|cancell?ed|updated|changed|sent|"
                  r"submitted|generated|emailed|reset|fixed|resolved|refunded|credited|reversed)\b", re.I)
HANDOFF = re.compile(r"\b(raise a ticket|ticket is raised|pass (the|your|it|this)|will contact you|escalat\w+|"
                     r"call you back|look at it within)\b", re.I)
CLOSING = re.compile(r"\b(anything else|is there anything|other questions)\b", re.I)


def _clip(x):
    return float(min(1.0, max(0.0, x)))


def scorecard(segments, stats):
    agent = [s for s in segments if s["speaker"] == "agent"]
    cust = [s for s in segments if s["speaker"] == "customer"]
    items = []

    first = agent[0]["text"] if agent else ""
    g, i = GREETING.search(first), INTRO.search(first)
    items.append({"key": "greeting", "label": "Greeting & introduction", "weight": 10,
                  "score": _clip((0.6 if g else 0) + (0.4 if i else 0)),
                  "evidence": f"Opening: \"{first[:140]}\"" if first else "Agent did not speak",
                  "detail": ("greeting" if g else "no greeting") + ", " + ("introduced self" if i else "no introduction")})

    hits = [(s["start"], m.group(0)) for s in agent for m in EMPATHY.finditer(s["text"])]
    items.append({"key": "empathy", "label": "Empathy", "weight": 15,
                  "score": 0.0 if not hits else 0.6 if len(hits) == 1 else 1.0,
                  "evidence": "; ".join(f"{t:.0f}s \"{p}\"" for t, p in hits[:4]) or "No empathy statements found",
                  "detail": f"{len(hits)} empathy statement(s)"})

    share = stats["agent_share"]
    if share is None:
        tl = 0.0
    elif 0.35 <= share <= 0.6:
        tl = 1.0
    else:
        tl = _clip(1 - (0.35 - share) / 0.2) if share < 0.35 else _clip(1 - (share - 0.6) / 0.25)
    items.append({"key": "talk_listen", "label": "Talk / listen ratio", "weight": 15, "score": tl,
                  "evidence": f"Agent {stats['agent_talk']}s vs customer {stats['customer_talk']}s "
                              f"({round((share or 0) * 100)}% agent; target 35-60%)",
                  "detail": f"{round((share or 0) * 100)}% agent talk"})

    over = sum(max(0.0, g - 3) for _, g in stats["gaps"])
    items.append({"key": "silence", "label": "Dead air / silence", "weight": 10, "score": _clip(1 - over / 8),
                  "evidence": "; ".join(f"{g:.1f}s at {t:.0f}s" for t, g in stats["gaps"]) or "No pause longer than 3s",
                  "detail": f"longest pause {stats['longest_silence']}s"})

    ai, ci = stats["agent_interruptions"], stats["customer_interruptions"]
    items.append({"key": "interruptions", "label": "Interruptions", "weight": 10, "score": _clip(1 - 0.35 * ai - 0.2 * ci),
                  "evidence": f"Agent interrupted {ai}x, customer talked over agent {ci}x",
                  "detail": f"{ai + ci} overlap(s)"})

    late = agent[len(agent) // 3:] if agent else []
    done = next((s for s in late if DONE.search(s["text"])), None)
    hand = next((s for s in late if HANDOFF.search(s["text"])), None)
    closing = next((s for s in agent if CLOSING.search(s["text"])), None)
    end_val = float(np.mean([s["valence"] for s in cust[-2:]])) if cust else 0.0
    action = 1.0 if done else 0.4 if hand else 0.0
    res = _clip(0.5 * action + 0.3 * (1.0 if end_val >= 0.1 else 0.5 if end_val > -0.1 else 0.0) + 0.2 * (1 if closing else 0))
    ev = []
    if done:
        ev.append(f"Action taken: \"{DONE.search(done['text']).group(0)}\" ({done['start']:.0f}s)")
    elif hand:
        ev.append(f"Handed off: \"{HANDOFF.search(hand['text']).group(0)}\" ({hand['start']:.0f}s)")
    else:
        ev.append("No completed action found")
    ev.append(f"customer ends {'positive' if end_val >= 0.1 else 'neutral' if end_val > -0.1 else 'negative'} ({end_val:+.2f})")
    ev.append("offered further help" if closing else "no closing check")
    items.append({"key": "resolution", "label": "Resolution", "weight": 25, "score": res, "evidence": "; ".join(ev),
                  "detail": "resolved" if res >= 0.8 else "partly resolved" if res >= 0.45 else "unresolved"})

    if cust:
        k = max(1, len(cust) // 3)
        start_v = float(np.mean([s["valence"] for s in cust[:k]]))
        end_v = float(np.mean([s["valence"] for s in cust[-k:]]))
    else:
        start_v = end_v = 0.0
    change = end_v - start_v
    items.append({"key": "sentiment_change", "label": "Customer sentiment change", "weight": 15,
                  "score": _clip(0.5 + 0.5 * end_v + 0.5 * change),
                  "evidence": f"Customer valence {start_v:+.2f} at start -> {end_v:+.2f} at end ({change:+.2f})",
                  "detail": f"{change:+.2f}"})

    for it in items:
        it["score"] = round(it["score"], 3)
        it["points"] = round(it["score"] * it["weight"], 1)
    total = round(sum(it["points"] for it in items))
    return {"total": total, "items": items, "stats": stats}, round(change, 3)
