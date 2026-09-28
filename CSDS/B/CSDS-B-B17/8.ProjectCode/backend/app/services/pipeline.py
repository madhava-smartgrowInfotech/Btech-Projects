"""The call-analysis pipeline and its background worker (one call at a time, CPU)."""
import queue
import threading
import traceback
from datetime import datetime

from ..db import Call, SessionLocal
from . import analysis, nlp, speech
from .summary import SummaryError, summarise

SR = speech.SR
_q: "queue.Queue[int]" = queue.Queue()
_started = False


def _set(call_id, **fields):
    with SessionLocal() as db:
        c = db.get(Call, call_id)
        if c is None:
            return
        for k, v in fields.items():
            setattr(c, k, v)
        db.commit()


def analyse(path, progress=lambda stage: None):
    """Run the full pipeline on one recording and return the fields to store."""
    progress("Decoding audio")
    mono, stereo = speech.load_audio(path)
    duration = round(len(mono) / SR, 2)
    progress("Transcribing (faster-whisper)")
    if stereo is not None:
        segments, agent_channel, activity = speech.transcribe_stereo(*stereo)
        mode = f"stereo channels (agent on {agent_channel})"
        sources = {"agent": stereo[0 if agent_channel == "left" else 1],
                   "customer": stereo[1 if agent_channel == "left" else 0]}
    else:
        segments = speech.transcribe_mono(mono)
        activity = speech.activity_from_segments(segments)
        mode = "turn split (mono)"
        sources = {"agent": mono, "customer": mono}
    if not segments:
        raise ValueError("No speech was found in this recording")

    progress("Text sentiment")
    for s, sent in zip(segments, nlp.sentiment_batch([s["text"] for s in segments])):
        s["sentiment"] = sent
    progress("Voice emotion")
    for s in segments:
        clip = sources[s["speaker"]][int(s["start"] * SR): int(s["end"] * SR)]
        s["voice"] = speech.voice_emotion(clip)
    analysis.fuse(segments)

    progress("Intent, topic and keywords")
    customer_turns = [s["text"] for s in segments if s["speaker"] == "customer"]
    intent = nlp.classify_intent(customer_turns) or {}
    text = " ".join(s["text"] for s in segments)
    kws = nlp.keywords(text)

    progress("Scorecard")
    stats = analysis.talk_stats(activity, duration)
    card, change = analysis.scorecard(segments, stats)
    card["speaker_mode"] = mode
    flags = analysis.flags(segments, stats["gaps"])
    cust_vals = [s["valence"] for s in segments if s["speaker"] == "customer"]

    progress("Summary (Gemini)")
    summary, summary_error = None, ""
    try:
        summary = summarise(segments, intent.get("intent"))
    except SummaryError as e:
        summary_error = str(e)

    return {
        "duration": duration, "channels": 2 if stereo is not None else 1, "segments": segments,
        "transcript_text": "\n".join(f"{s['speaker']}: {s['text']}" for s in segments),
        "intent": intent.get("intent"), "intent_confidence": intent.get("confidence"),
        "intent_top": {"top": intent.get("top", []), "evidence": intent.get("evidence")},
        "topic": intent.get("topic"), "keywords": kws,
        "sentiment": round(sum(cust_vals) / len(cust_vals), 3) if cust_vals else None,
        "sentiment_change": change, "flags": flags, "scorecard": card, "score": card["total"],
        "summary": summary, "summary_error": summary_error,
    }


def process(call_id):
    with SessionLocal() as db:
        c = db.get(Call, call_id)
        if c is None:
            return
        path = c.audio_path
    _set(call_id, status="processing", stage="Starting", error="")
    try:
        result = analyse(path, progress=lambda st: _set(call_id, stage=st))
        _set(call_id, **result, status="done", stage="", processed_at=datetime.utcnow())
    except Exception as e:  # keep the worker alive and show the reason on the call
        traceback.print_exc()
        _set(call_id, status="failed", stage="", error=f"{type(e).__name__}: {e}"[:1000])


def resummarise(call_id):
    with SessionLocal() as db:
        c = db.get(Call, call_id)
        segs, intent = c.segments, c.intent
    try:
        _set(call_id, summary=summarise(segs, intent), summary_error="")
    except SummaryError as e:
        _set(call_id, summary_error=str(e))
        raise


def _worker():
    while True:
        cid = _q.get()
        try:
            process(cid)
        finally:
            _q.task_done()


def enqueue(call_id):
    _q.put(call_id)


def queue_size():
    return _q.qsize()


def start_worker():
    """Start the worker and re-queue calls that were waiting when the server stopped."""
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_worker, daemon=True, name="call-pipeline").start()
    with SessionLocal() as db:
        for c in db.query(Call).filter(Call.status.in_(["queued", "processing"])).order_by(Call.id):
            c.status = "queued"
            _q.put(c.id)
        db.commit()


def warm_up():
    """Load models in the background so the first call does not pay the start-up cost."""
    def run():
        try:
            speech.whisper()
            speech.emotion_model()
        except Exception:
            traceback.print_exc()
    threading.Thread(target=run, daemon=True, name="warm-up").start()
