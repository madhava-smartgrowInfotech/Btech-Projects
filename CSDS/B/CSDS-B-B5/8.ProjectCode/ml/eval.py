"""Evaluate SignBridge end to end on CPU -> experiments/eval/metrics.json (+ confusion-matrix plots).

    python -m ml.eval

Covers the objectives: recognition accuracy (words + fingerspelling), continuous signing through the
live segmenter, sentence formation, speech-to-text quality, and latency of every stage.
"""
import io
import json
import random
import statistics
import time
import wave
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import numpy as np
import onnxruntime as ort

from ml.features import letter_features, word_features
from ml.train import augment_seq, load_letters, load_words
from ml.vocab import LETTERS, WORD_GLOSSES

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "eval"
SEED = 7


def softmax(z):
    e = np.exp(z - z.max(1, keepdims=True))
    return e / e.sum(1, keepdims=True)


def session(name):
    return ort.InferenceSession(str(ROOT / "models" / name), providers=["CPUExecutionProvider"])


def stats(values):
    v = sorted(values)
    return {"mean": round(statistics.mean(v), 2), "p50": round(v[len(v) // 2], 2),
            "p95": round(v[max(0, int(len(v) * 0.95) - 1)], 2), "n": len(v)}


def classification_block(y, probs, labels):
    pred = probs.argmax(1)
    n = len(labels)
    cm = np.zeros((n, n), int)
    for a, b in zip(y, pred):
        cm[a, b] += 1
    per = []
    for i, lab in enumerate(labels):
        tp = cm[i, i]
        p = tp / cm[:, i].sum() if cm[:, i].sum() else 0.0
        r = tp / cm[i].sum() if cm[i].sum() else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        per.append({"label": lab, "precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4), "support": int(cm[i].sum())})
    top3 = np.mean([y[i] in np.argsort(probs[i])[::-1][:3] for i in range(len(y))])
    present = [p for p in per if p["support"]]
    return {"accuracy": round(float((pred == y).mean()), 4), "top3_accuracy": round(float(top3), 4),
            "macro_f1": round(float(np.mean([p["f1"] for p in present])), 4), "n_test": int(len(y)),
            "labels": labels, "confusion": cm.tolist(), "per_class": per}


def plot_confusion(block, name, title):
    cm = np.array(block["confusion"], float)
    cm = cm / np.maximum(cm.sum(1, keepdims=True), 1)
    n = len(block["labels"])
    fig, ax = plt.subplots(figsize=(0.22 * n + 2, 0.22 * n + 1.5))
    ax.imshow(cm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(block["labels"], rotation=90, fontsize=6); ax.set_yticklabels(block["labels"], fontsize=6)
    ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(f"{title} - accuracy {block['accuracy']:.1%}")
    fig.tight_layout(); fig.savefig(OUT / f"confusion_{name}.png", dpi=120); plt.close(fig)


def edit_distance(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev, d[j] = d[j], cur
    return d[-1]


# ---------------------------------------------------------------- recognition
def eval_words(data, wm):
    X, y = data["test"]
    feats = np.stack([word_features(s) for s in X])
    probs = softmax(wm.run(None, {"x": feats})[0])
    block = classification_block(y, probs, WORD_GLOSSES)
    rng = np.random.default_rng(SEED)
    pert = np.stack([word_features(augment_seq(s, rng)) for s in X])
    mirr = np.stack([word_features(s, mirror=True) for s in X])
    robust = {"word_accuracy_perturbed": round(float((wm.run(None, {"x": pert})[0].argmax(1) == y).mean()), 4),
              "word_accuracy_mirrored": round(float((wm.run(None, {"x": mirr})[0].argmax(1) == y).mean()), 4)}
    live = None
    if "video_test" in data:
        Xv, yv = data["video_test"]
        pv = wm.run(None, {"x": np.stack([word_features(s) for s in Xv])})[0].argmax(1)
        classes = sorted(set(yv.tolist()))
        ref = np.isin(y, classes)
        live = {"accuracy": round(float((pv == yv).mean()), 4), "n_test": int(len(yv)), "n_classes": len(classes),
                "same_clips_reference_accuracy": round(float((probs.argmax(1)[ref] == y[ref]).mean()), 4)}
    return block, robust, live


def eval_letters(lm):
    hands, n, y, test = load_letters()
    feats = np.stack([letter_features([h[i] for i in range(k)]) for h, k in zip(hands[test], n[test])])
    return classification_block(y[test], softmax(lm.run(None, {"x": feats})[0]), LETTERS)


def eval_continuous(data, n_seq=60, per_seq=3, fps=15.0):
    """Stream test signs frame by frame through the live segmenter, with a short rest between signs."""
    from backend.app.services.recognizer import Models, Recognizer, SessionState

    rec = Recognizer.__new__(Recognizer)
    rec.models = Models()
    X, y = data["test"]
    rng = random.Random(SEED)
    rest = np.full((49, 2), np.nan, np.float32)
    ok_signs = total = exact = errors = 0
    for _ in range(n_seq):
        idx = rng.sample(range(len(y)), per_seq)
        st, t, got = SessionState(), 0.0, []
        frames = []
        for i in idx:
            frames += [rest.copy()] * 10  # ~0.7 s with hands lowered
            base = X[i].copy()
            frames += list(base)
            rest = np.full((49, 2), np.nan, np.float32)
            rest[:7] = base[-1, :7]  # body stays, hands down
        frames += [rest.copy()] * 12
        for f in frames:
            t += 1 / fps
            events, _ = rec._words(st, f, None, t)
            got += [e["gloss"] for e in events if e["type"] == "sign"]
        want = [WORD_GLOSSES[i] for i in y[idx]]
        errors += edit_distance(want, got)
        total += len(want)
        exact += got == want
        ok_signs += sum(a == b for a, b in zip(want, got)) if len(got) == len(want) else 0
    return {"n_sequences": n_seq, "signs_per_sequence": per_seq, "sign_accuracy": round(ok_signs / total, 4),
            "word_error_rate": round(errors / total, 4), "sequence_exact": round(exact / n_seq, 4)}


# ---------------------------------------------------------------- sentences, speech, latency
SENTENCES = [
    (["HELLO", "HOW_ARE_YOU"], "Hello, how are you?"),
    (["HELLO", "HOW_ARE_YOU", "YOU"], "Hello, how are you?"),
    (["THANK_YOU"], "Thank you."),
    (["I", "SICK"], "I am sick."),
    (["TODAY", "MOTHER", "SICK"], "Today, my mother is sick."),
    (["I", "HOSPITAL"], "I need to go to the hospital."),
    (["SHE", "DOCTOR"], "She is a doctor."),
    (["HE", "MEDICINE"], "He needs medicine."),
    (["GOOD_MORNING", "HOW_ARE_YOU"], "Good morning, how are you?"),
    (["I", "HAPPY"], "I am happy."),
    (["WE", "SCHOOL"], "We go to the school."),
    (["TOMORROW", "I", "BANK"], "Tomorrow, I need to go to the bank."),
    (["FATHER", "COLD"], "My father is cold."),
    (["HELLO", "I", "RAVI"], "Hello. I am Ravi."),
    (["YOU", "GOOD"], "You are good."),
    (["THEY", "MONEY"], "They need money."),
]

PHRASES = [
    "Hello, how can I help you today?",
    "Please take a seat, the doctor will see you soon.",
    "Your appointment is tomorrow morning at ten.",
    "Do you need a glass of water?",
    "The train to Mumbai leaves from platform two.",
    "Thank you for waiting, your order is ready.",
    "Please show me your ticket.",
    "What is your name and phone number?",
]


def pcm16k(wav_bytes):
    with wave.open(io.BytesIO(wav_bytes)) as w:
        rate, ch = w.getframerate(), w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    if ch > 1:
        a = a.reshape(-1, ch).mean(1)
    t = np.arange(0, len(a) / rate, 1 / 16000)
    return np.interp(t, np.arange(len(a)) / rate, a).astype(np.int16).tobytes()


def norm_words(s):
    return "".join(c.lower() if c.isalnum() or c == " " else " " for c in s).split()


def eval_speech():
    from backend.app.services import tts
    from backend.app.services.stt import STT

    stt = STT()
    stt.loaded.wait(300)
    tts_ms, stt_ms, errors, words, audio_s = [], [], 0, 0, 0.0
    for p in PHRASES:
        wav, ms = tts.synth(p)
        tts_ms.append(ms)
        r = stt.transcribe(pcm16k(wav), "en")
        stt_ms.append(r["latency_ms"])
        audio_s += r["audio_seconds"]
        ref, hyp = norm_words(p), norm_words(r["text"])
        errors += edit_distance(ref, hyp)
        words += len(ref)
    return ({"n_phrases": len(PHRASES), "word_error_rate": round(errors / words, 4), "model": stt.size,
             "real_time_factor": round(sum(stt_ms) / 1000 / audio_s, 3)}, stats(stt_ms), stats(tts_ms))


def eval_latency(wm, lm, data):
    import cv2

    from backend.app.services.landmarks import Extractor
    from backend.app.services.sentence import rule_sentence

    ext, lm_ms, frames = Extractor(), [], []
    for clip in sorted((ROOT / "data" / "sample" / "word_videos").glob("*.MOV")):
        cap = cv2.VideoCapture(str(clip))
        while True:
            ok, img = cap.read()
            if not ok:
                break
            frames.append(cv2.resize(img, (480, 480)))
    for img in frames[:150]:
        t = time.perf_counter(); ext.frame(img); lm_ms.append((time.perf_counter() - t) * 1000)
    X = data["test"][0]
    w_ms, l_ms, s_ms = [], [], []
    for s in X[:100]:
        t = time.perf_counter(); wm.run(None, {"x": word_features(s)[None]}); w_ms.append((time.perf_counter() - t) * 1000)
    hands, n, _, _ = load_letters()
    for h, k in zip(hands[:200], n[:200]):
        t = time.perf_counter(); lm.run(None, {"x": letter_features([h[i] for i in range(k)])[None]}); l_ms.append((time.perf_counter() - t) * 1000)
    for g, _ in SENTENCES * 10:
        t = time.perf_counter(); rule_sentence(g); s_ms.append((time.perf_counter() - t) * 1000)
    frame_total = [a + b for a, b in zip(lm_ms, w_ms * 2)]
    return {"landmarks_ms": stats(lm_ms), "word_model_ms": stats(w_ms), "letter_model_ms": stats(l_ms),
            "frame_total_ms": stats(frame_total), "sentence_rules_ms": stats(s_ms),
            "max_fps": round(1000 / statistics.mean(frame_total), 1)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wm, lm = session("word_model.onnx"), session("letter_model.onnx")
    data = load_words()
    print("words ...")
    words, robust, live = eval_words(data, wm)
    print("letters ...")
    letters = eval_letters(lm)
    print("continuous ...")
    continuous = eval_continuous(data)
    from backend.app.services.sentence import rule_sentence

    sent_ok = sum(rule_sentence(g) == ref for g, ref in SENTENCES)
    print("latency ...")
    latency = eval_latency(wm, lm, data)
    print("speech ...")
    speech, stt_lat, tts_lat = eval_speech()
    latency["speech_to_text_ms"], latency["text_to_speech_ms"] = stt_lat, tts_lat
    metrics = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "words": words, "letters": letters, "words_live_pipeline": live, "robustness": robust,
        "continuous": continuous, "latency": latency, "speech": speech,
        "sentence": {"n": len(SENTENCES), "exact_match": sent_ok,
                     "examples": [{"gloss": g, "reference": r, "output": rule_sentence(g)} for g, r in SENTENCES]},
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=1))
    plot_confusion(words, "words", "Word signs")
    plot_confusion(letters, "letters", "Fingerspelling")
    print(json.dumps({"word_accuracy": words["accuracy"], "word_top3": words["top3_accuracy"],
                      "letter_accuracy": letters["accuracy"], "live_pipeline": live, "robustness": robust,
                      "continuous": continuous, "sentence_exact": f"{sent_ok}/{len(SENTENCES)}", "speech": speech,
                      "frame_ms": latency["frame_total_ms"], "stt_ms": stt_lat, "tts_ms": tts_lat}, indent=1))


if __name__ == "__main__":
    main()
