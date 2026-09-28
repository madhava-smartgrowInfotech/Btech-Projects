"""Evaluate CallSense end to end and write experiments/eval/metrics.json.

1. Intent - Bitext held-out split (utterance level) and the full pipeline on the 10 sample calls (call level).
2. Sentiment - text model on the scripted sample-call lines, on the transcribed customer turns (end to end), and
   on the 20 real call-centre transcripts (call-level labels).
3. Transcription - word error rate of faster-whisper on the sample calls and on the 20 real recordings, plus
   speaker-attribution accuracy on the stereo sample calls.
4. Voice emotion - the pretrained wav2vec2 model on the committed RAVDESS + CREMA-D sample (4 emotions).
Summaries are not generated here (no Gemini calls). Usage: python ml/eval.py  (about 15-25 minutes on CPU)
"""
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services import nlp, pipeline, speech  # noqa: E402

OUT = ROOT / "experiments" / "eval"
SAMPLES = ROOT / "data" / "sample" / "calls"
CC = ROOT / "data" / "call_center"
EMO = ROOT / "data" / "sample" / "emotion"

# ---------- text normalisation for WER ----------
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen " \
       "eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def num_words(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + num_words(n % 100))
    return num_words(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + num_words(n % 1000))


def normalise(text):
    t = text.lower()
    t = re.sub(r"\$(\d+)", r"\1 dollars", t)
    t = re.sub(r"(\d+)\s*-\s*(\d+)", r"\1 to \2", t)
    # long digit strings are read digit by digit (order / account numbers), short ones as numbers
    t = re.sub(r"\d{4,}", lambda m: " ".join(ONES[int(d)] for d in m.group(0)), t)
    t = re.sub(r"\d+", lambda m: num_words(int(m.group(0))), t)
    t = t.replace("'", "")
    t = re.sub(r"[^a-z ]+", " ", t)
    return t.split()


def edit_distance(ref, hyp):
    d = np.arange(len(hyp) + 1)
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r != h))
            prev, d[j] = d[j], cur
    return int(d[len(hyp)])


def wer(pairs):
    errs = sum(edit_distance(normalise(r), normalise(h)) for r, h in pairs)
    words = sum(len(normalise(r)) for r, _ in pairs)
    return round(errs / max(words, 1), 4)


def f1(y, p, labels=("negative", "neutral", "positive")):
    return {"n": len(y), "accuracy": round(accuracy_score(y, p), 4),
            "macro_f1": round(f1_score(y, p, labels=list(labels), average="macro", zero_division=0), 4)}


def eval_sample_calls():
    rows, line_y, line_p, turn_y, turn_p, speaker_hits, speaker_n, wer_pairs = [], [], [], [], [], 0, 0, []
    for meta_path in sorted(SAMPLES.glob("*.json")):
        meta = json.loads(meta_path.read_text())
        t0 = time.time()
        r = pipeline.analyse(meta_path.with_suffix(".flac"), with_summary=False)
        segs, ref = r["segments"], meta["lines"]
        wer_pairs.append((" ".join(l["text"] for l in ref), " ".join(s["text"] for s in segs)))
        # speaker attribution: each reference line vs the transcribed turn that overlaps it most
        for l in ref:
            ov = [(min(l["end"], s["end"]) - max(l["start"], s["start"]), s) for s in segs]
            best = max(ov, key=lambda x: x[0], default=(0, None))
            speaker_n += 1
            speaker_hits += bool(best[1] and best[0] > 0 and best[1]["speaker"] == l["speaker"])
            if l["speaker"] == "customer" and best[1] is not None and best[0] > 0:
                turn_y.append(l["sentiment"])
                turn_p.append(best[1]["sentiment"]["label"])
        for l, s in zip(ref, nlp.sentiment_batch([l["text"] for l in ref])):
            line_y.append(l["sentiment"])
            line_p.append(s["label"])
        cust = [s["emotion"] for s in segs if s["speaker"] == "customer"]
        ref_c = [l["sentiment"] for l in ref if l["speaker"] == "customer"]
        rows.append({"call": meta["id"], "intent_true": meta["intent"], "intent_pred": r["intent"],
                     "intent_confidence": r["intent_confidence"], "score": r["score"],
                     "customer_emotions": cust, "script_customer_sentiment": ref_c,
                     "wer": wer([wer_pairs[-1]]), "seconds": round(time.time() - t0, 1)})
        print(f"  {meta['id']}: intent {r['intent']} (true {meta['intent']}), score {r['score']}, "
              f"WER {rows[-1]['wer']}, {rows[-1]['seconds']}s")
    y = [r["intent_true"] for r in rows]
    p = [r["intent_pred"] for r in rows]
    return {
        "calls": rows,
        "intent_call_level": {"n": len(y), "accuracy": round(accuracy_score(y, p), 4),
                              "macro_f1": round(f1_score(y, p, labels=sorted(set(y)), average="macro", zero_division=0), 4)},
        "sentiment_script_lines": f1(line_y, line_p),
        "sentiment_customer_turns_end_to_end": f1(turn_y, turn_p),
        "wer": wer(wer_pairs),
        "speaker_attribution_accuracy": round(speaker_hits / max(speaker_n, 1), 4),
    }


CC_MAP = {"Angry": "negative", "Frustrated": "negative", "Happy": "positive", "Neutral": "neutral", "Confused": "neutral"}


def eval_call_center():
    df = pd.read_csv(CC / "call_recordings.csv")
    pairs, y, p, p_asr = [], [], [], []
    for _, row in df.iterrows():
        audio, _ = speech.load_audio(CC / f"{row['id']}.wav")
        hyp = " ".join(s["text"] for s in speech.transcribe_mono(audio))
        ref = str(row["Transcript"]).replace("...", " ")
        pairs.append((ref, hyp))
        y.append(CC_MAP.get(row["Sentiment"], "neutral"))
        p.append(nlp.sentiment_batch([ref])[0]["label"])
        p_asr.append(nlp.sentiment_batch([hyp])[0]["label"] if hyp else "neutral")
    print(f"  call-centre recordings: {len(pairs)} transcribed")
    return {"n": len(pairs), "wer": wer(pairs), "sentiment_on_reference_transcripts": f1(y, p),
            "sentiment_on_asr_transcripts": f1(y, p_asr),
            "label_mapping": CC_MAP}


RAV = {"01": "neutral", "03": "happy", "04": "sad", "05": "angry"}
CRE = {"NEU": "neutral", "HAP": "happy", "SAD": "sad", "ANG": "angry"}


def eval_voice_emotion():
    from faster_whisper.audio import decode_audio
    out = {}
    labels = ["neutral", "happy", "sad", "angry"]
    for name, pattern, lab in (("ravdess", "*.wav", lambda f: RAV[f.stem.split("-")[2]]),
                               ("cremad", "*.wav", lambda f: CRE[f.stem.split("_")[2]])):
        y, p = [], []
        for f in sorted((EMO / name).glob(pattern)):
            probs = speech.voice_emotion(decode_audio(str(f), sampling_rate=16000))
            if probs:
                y.append(lab(f))
                p.append(max(probs, key=probs.get))
        out[name] = {"n": len(y), "accuracy": round(accuracy_score(y, p), 4),
                     "macro_f1": round(f1_score(y, p, labels=labels, average="macro", zero_division=0), 4)}
        print(f"  {name}: {out[name]}")
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    train = json.loads((ROOT / "experiments" / "metrics.json").read_text())
    print("Voice emotion (RAVDESS + CREMA-D sample)...")
    emo = eval_voice_emotion()
    print("Sample calls (full pipeline)...")
    sample = eval_sample_calls()
    print("Real call-centre recordings...")
    cc = eval_call_center()
    metrics = {
        "intent": {"bitext_holdout": {k: train["intent"][k] for k in ("test_size", "accuracy", "macro_f1")},
                   "sample_calls_end_to_end": sample["intent_call_level"]},
        "sentiment": {"airline_holdout": {k: train["sentiment"][k] for k in ("test_size", "accuracy", "macro_f1")},
                      "sample_call_script_lines": sample["sentiment_script_lines"],
                      "sample_call_customer_turns_end_to_end": sample["sentiment_customer_turns_end_to_end"],
                      "call_center_reference_transcripts": cc["sentiment_on_reference_transcripts"],
                      "call_center_asr_transcripts": cc["sentiment_on_asr_transcripts"]},
        "transcription": {"model": f"faster-whisper {speech.WHISPER_MODEL} ({speech.WHISPER_COMPUTE_TYPE}, CPU)",
                          "wer_sample_calls": sample["wer"], "wer_call_center_recordings": cc["wer"],
                          "speaker_attribution_accuracy_sample_calls": sample["speaker_attribution_accuracy"]},
        "voice_emotion": {"model": speech.EMOTION_MODEL, **emo},
        "sample_calls": sample["calls"],
        "notes": "Sample calls are synthetic (offline voices) and clearly labelled; call-centre recordings are real "
                 "audio from the Call Center Transcripts dataset. WER uses lower-case text without punctuation, "
                 "with digits spelled out.",
        "runtime_seconds": round(time.time() - t0),
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps({k: v for k, v in metrics.items() if k != "sample_calls"}, indent=2))


if __name__ == "__main__":
    main()
