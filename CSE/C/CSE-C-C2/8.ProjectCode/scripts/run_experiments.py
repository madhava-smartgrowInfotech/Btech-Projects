"""StoryVox measured experiments (documentation run).

Runs the application's own services (app.services.*) on fixed inputs and writes
metrics.json files under experiments/. Nothing here is estimated: every number in
the project documents comes from these files.

    python -u scripts/run_experiments.py tts_asr     # 15 languages x 10 FLEURS sentences
    python -u scripts/run_experiments.py story       # 3 story conditions x 17 prompts + length scaling
    python -u scripts/run_experiments.py all

ffmpeg must be on PATH (Whisper reads WAV files through it); audio goes to a scratch dir, not data/.
"""
from __future__ import annotations

import json
import os
import re
import statistics as st
import sys
import tempfile
import time
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path(os.environ.get("STORYVOX_EXP_SCRATCH", Path(tempfile.gettempdir()) / "storyvox_exp"))
SCRATCH.mkdir(parents=True, exist_ok=True)
os.environ["STORYVOX_AUDIO_DIR"] = str(SCRATCH / "audio")
os.environ["STORYVOX_DB_PATH"] = str(SCRATCH / "exp.db")
os.environ["STORYVOX_EVAL_DIR"] = str(SCRATCH / "evals")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
sys.path.insert(0, str(ROOT))

import torch  # noqa: E402  (torch first: other imports can break its DLL load on this machine)
import jiwer  # noqa: E402

from app.config import LANGUAGE_MAP, get_settings  # noqa: E402
from app.utils import word_count  # noqa: E402
from app.utils.metrics import cer as app_cer, rouge_l_f1, wer as app_wer  # noqa: E402

FLEURS = {
    "en": "en_us", "hi": "hi_in", "es": "es_419", "fr": "fr_fr", "de": "de_de", "it": "it_it",
    "pt": "pt_br", "ru": "ru_ru", "ar": "ar_eg", "tr": "tr_tr", "nl": "nl_nl", "pl": "pl_pl",
    "zh": "cmn_hans_cn", "ja": "ja_jp", "ko": "ko_kr",
}
NO_SPACES = {"zh", "ja"}  # no word boundaries: word error rate is not meaningful
OUT = ROOT / "experiments"


def save(name: str, payload: dict) -> None:
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "metrics.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[saved] experiments/{name}/metrics.json", flush=True)


def norm(text: str, lang: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] not in ("P", "S"))
    text = " ".join(text.split())
    return text.replace(" ", "") if lang in NO_SPACES else text


def fleurs_sentences(lang: str, n: int = 10) -> list[str]:
    cache = SCRATCH / f"fleurs_{FLEURS[lang]}_test.tsv"
    if not cache.exists():
        url = f"https://huggingface.co/datasets/google/fleurs/resolve/main/data/{FLEURS[lang]}/test.tsv"
        cache.write_bytes(urllib.request.urlopen(url, timeout=60).read())
    out, seen = [], set()
    for line in cache.read_text(encoding="utf-8").splitlines():
        cols = line.split("\t")
        if len(cols) < 3:
            continue
        text = cols[2].strip()
        size = len(text) if lang in NO_SPACES else len(text.split())
        lo, hi = (12, 70) if lang in NO_SPACES else (6, 30)
        if lo <= size <= hi and text not in seen:
            seen.add(text)
            out.append(text)
        if len(out) == n:
            break
    return out


PROBE_ONLY = {"zh", "ja"}   # no MMS checkpoint exists; the OS fallback has no Chinese/Japanese voice, so probe once instead of 10 times


def probe_narration(lang: str, sentence: str, timeout_s: int = 120) -> dict:
    """Try the app's narration once in a child process with a hard timeout (the OS engine can hang on unsupported scripts)."""
    import subprocess

    code = """
import torch, sys, json, time
sys.path.insert(0, ROOT_DIR)
from app.services import tts_service
t = time.perf_counter()
try:
    r = tts_service.synthesize_story_narration(sys.argv[1], sys.argv[2])
    print(json.dumps({"ok": True, "model": r[3], "duration_s": r[1]}))
except Exception as e:
    print(json.dumps({"ok": False, "error": str(e)[:160], "seconds": round(time.perf_counter() - t, 1)}))
""".replace("ROOT_DIR", repr(str(ROOT)))
    t0 = time.perf_counter()
    try:
        out = subprocess.run([sys.executable, "-c", code, sentence, lang], capture_output=True, text=True, timeout=timeout_s, encoding="utf-8", errors="replace")
        line = [l for l in out.stdout.splitlines() if l.startswith("{")][-1]
        res = json.loads(line)
        return {"probe_only": True, "narration_ok": res["ok"], "probe_result": res, "probe_seconds": round(time.perf_counter() - t0, 1),
                "note": "tts-asr scoring skipped: " + ("narration succeeded once but was not scored" if res["ok"] else "the application produced no narration for this language")}
    except subprocess.TimeoutExpired:
        return {"probe_only": True, "narration_ok": False, "probe_result": {"ok": False, "error": f"no result after {timeout_s} s (OS speech engine hung)"},
                "probe_seconds": float(timeout_s), "note": "tts-asr scoring skipped: the application's narration call did not return"}


def mean(v):
    return round(sum(v) / len(v), 4) if v else None


# --------------------------------------------------------------------------- TTS + ASR
def run_tts_asr() -> None:
    from app.services import asr_service, tts_service
    from app.utils import chunk_text  # noqa: F401

    results = {"experiment": "tts_asr_roundtrip", "dataset": "google/fleurs test split (CC BY 4.0), first 10 sentences per language within a length window",
               "tts_models": "app default chain (facebook/mms-tts-* then OS fallback)", "asr_model": get_settings().asr_model,
               "device": "cuda" if torch.cuda.is_available() else "cpu", "torch": torch.__version__, "languages": {}}
    try:
        import pyttsx3
        results["system_voices"] = [{"name": v.name, "languages": [str(x) for x in getattr(v, "languages", [])]} for v in pyttsx3.init().getProperty("voices")]
    except Exception as exc:  # pragma: no cover
        results["system_voices_error"] = str(exc)

    # Whisper load time (first transcription pays it)
    t0 = time.perf_counter()
    asr_service._load_asr(get_settings().asr_model)
    results["asr_load_s"] = round(time.perf_counter() - t0, 2)

    prior = OUT / "tts_asr" / "metrics.json"
    if os.environ.get("STORYVOX_RESUME") and prior.exists():   # continue a run that already scored some languages
        results["languages"] = json.loads(prior.read_text(encoding="utf-8"))["languages"]
        results["system_voices"] = json.loads(prior.read_text(encoding="utf-8")).get("system_voices", results.get("system_voices"))
    for lang in LANGUAGE_MAP:
        if lang in results["languages"]:
            continue
        print(f"== {lang}", flush=True)
        sents = fleurs_sentences(lang)
        entry = {"checkpoint": LANGUAGE_MAP[lang]["tts_checkpoint"], "n": len(sents), "sentences": []}
        if lang in PROBE_ONLY:
            entry.update(probe_narration(lang, sents[0]))
            results["languages"][lang] = entry
            save("tts_asr", results)
            continue
        # model load time measured separately from synthesis
        load_s = None
        try:
            t0 = time.perf_counter()
            tts_service.MMSTTSProvider()._load(LANGUAGE_MAP[lang]["tts_checkpoint"])
            load_s = round(time.perf_counter() - t0, 2)
        except Exception as exc:
            entry["mms_load_error"] = str(exc).splitlines()[0][:160]
        entry["mms_load_s"] = load_s
        refs, hyps, refs_n, hyps_n = [], [], [], []
        for s in sents:
            row = {"text": s}
            try:
                rel, dur, sr, model_id, synth_t, rtf = tts_service.synthesize_story_narration(s, lang)
                row.update(tts_model=model_id, duration_s=dur, synth_s=synth_t, rtf=rtf)
                try:
                    t0 = time.perf_counter()
                    hyp = asr_service.transcribe_wav(tts_service.resolve_audio_abs_path(rel), lang)
                    row["asr_s"] = round(time.perf_counter() - t0, 3)
                    row["hyp"] = hyp
                    row["wer_raw"] = round(app_wer(s, hyp), 4)
                    row["cer_raw"] = round(app_cer(s, hyp), 4)
                    rn, hn = norm(s, lang), norm(hyp, lang)
                    row["cer_norm"] = round(jiwer.cer(rn, hn), 4) if rn else None
                    if lang not in NO_SPACES:
                        row["wer_norm"] = round(jiwer.wer(rn, hn), 4) if rn else None
                    refs.append(s); hyps.append(hyp); refs_n.append(rn); hyps_n.append(hn)
                except Exception as exc:
                    row["asr_error"] = str(exc)[:200]
            except Exception as exc:
                row["tts_error"] = str(exc)[:200]
            entry["sentences"].append(row)
        ok = [r for r in entry["sentences"] if "rtf" in r]
        # the first sentence can still be cold for the fallback engine; report all and warm-only
        entry["models_used"] = sorted({r["tts_model"] for r in ok})
        entry["mean_duration_s"] = mean([r["duration_s"] for r in ok])
        entry["mean_synth_s"] = mean([r["synth_s"] for r in ok])
        entry["mean_rtf"] = mean([r["rtf"] for r in ok])
        entry["median_rtf"] = round(st.median([r["rtf"] for r in ok]), 4) if ok else None
        entry["scored"] = len(refs_n)
        if refs_n:
            entry["cer_norm_corpus"] = round(jiwer.cer(refs_n, hyps_n), 4)
            entry["cer_raw_mean"] = mean([r["cer_raw"] for r in ok if "cer_raw" in r])
            entry["wer_raw_mean"] = mean([r["wer_raw"] for r in ok if "wer_raw" in r])
            if lang not in NO_SPACES:
                entry["wer_norm_corpus"] = round(jiwer.wer(refs_n, hyps_n), 4)
        results["languages"][lang] = entry
        save("tts_asr", results)  # incremental
    save("tts_asr", results)


def run_cjk() -> None:
    """zh and ja have no MMS checkpoint. Score what the application's OS fallback actually produces, one child process per sentence
    (the OS speech engine can hang on text it has no voice for, so every call gets a hard timeout)."""
    import subprocess

    from app.services import asr_service

    path = OUT / "tts_asr" / "metrics.json"
    results = json.loads(path.read_text(encoding="utf-8"))
    asr_service._load_asr(get_settings().asr_model)
    child = """
import torch, sys, json
sys.path.insert(0, ROOT_DIR)
from app.services import tts_service
try:
    r = tts_service.synthesize_story_narration(sys.argv[1], sys.argv[2])
    print(json.dumps({"ok": True, "rel": str(r[0]), "duration_s": r[1], "model": r[3], "synth_s": r[4], "rtf": r[5]}))
except Exception as e:
    print(json.dumps({"ok": False, "error": str(e)[:160]}))
""".replace("ROOT_DIR", repr(str(ROOT)))
    for lang in ("zh", "ja"):
        print(f"== {lang} (fallback voice)", flush=True)
        sents = fleurs_sentences(lang)
        entry = {"checkpoint": LANGUAGE_MAP[lang]["tts_checkpoint"], "n": len(sents), "mms_load_error": "checkpoint does not exist on the Hugging Face Hub", "mms_load_s": None,
                 "sentences": [], "per_sentence_subprocess": True}
        refs_n, hyps_n = [], []
        from app.services import tts_service
        for sent in sents:
            row = {"text": sent}
            try:
                out = subprocess.run([sys.executable, "-c", child, sent, lang], capture_output=True, text=True, timeout=90, encoding="utf-8", errors="replace")
                res = json.loads([l for l in out.stdout.splitlines() if l.startswith("{")][-1])
            except subprocess.TimeoutExpired:
                res = {"ok": False, "error": "no result after 90 s (OS speech engine hung)"}
            if not res["ok"]:
                row["tts_error"] = res["error"]
            else:
                row.update(tts_model=res["model"], duration_s=res["duration_s"], synth_s=res["synth_s"], rtf=res["rtf"])
                hyp = asr_service.transcribe_wav(tts_service.resolve_audio_abs_path(res["rel"]), lang)
                row["hyp"] = hyp
                row["cer_raw"] = round(app_cer(sent, hyp), 4)
                rn, hn = norm(sent, lang), norm(hyp, lang)
                row["cer_norm"] = round(jiwer.cer(rn, hn), 4)
                refs_n.append(rn); hyps_n.append(hn)
            entry["sentences"].append(row)
            print(lang, {k: v for k, v in row.items() if k not in ("text", "hyp")}, flush=True)
        ok = [r for r in entry["sentences"] if "rtf" in r]
        entry["narrated"] = len(ok)
        entry["models_used"] = sorted({r["tts_model"] for r in ok})
        entry["mean_duration_s"] = mean([r["duration_s"] for r in ok])
        entry["mean_synth_s"] = mean([r["synth_s"] for r in ok])
        entry["mean_rtf"] = mean([r["rtf"] for r in ok])
        entry["median_rtf"] = round(st.median([r["rtf"] for r in ok]), 4) if ok else None
        entry["scored"] = len(refs_n)
        if refs_n:
            entry["cer_norm_corpus"] = round(jiwer.cer(refs_n, hyps_n), 4)
            entry["cer_raw_mean"] = mean([r["cer_raw"] for r in ok])
        results["languages"][lang] = entry
        path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print("[saved]", lang, flush=True)


# --------------------------------------------------------------------------- stories
INSTR = re.compile(r"(?i)\b(the story should|should be|should include|must be|the first line|blank line|title:|story idea|write (an?|the) |in english|the title should)\b")
LD_MAP = {"zh-cn": "zh", "zh-tw": "zh"}


def lang_ok(text: str, code: str) -> bool | None:
    try:
        from langdetect import DetectorFactory, detect

        DetectorFactory.seed = 0
        got = detect(text)
        return LD_MAP.get(got, got) == code
    except Exception:
        return None


def distinct2(text: str) -> float:
    toks = text.split() if " " in text else list(text)
    bg = list(zip(toks, toks[1:]))
    return round(len(set(bg)) / len(bg), 4) if bg else 0.0


def instruction_echo(text: str) -> float:
    sents = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
    return round(sum(1 for s in sents if INSTR.search(s)) / len(sents), 4) if sents else 0.0


def run_story() -> None:
    from sentence_transformers import SentenceTransformer

    from app.services import story_generator as sg
    from app.services import tts_service

    settings = get_settings()
    idea = "A young inventor discovers a hidden library."
    items = [("en", "Adventure"), ("en", "Bedtime"), ("en", "Mystery")] + [(c, "Adventure") for c in LANGUAGE_MAP if c != "en"]
    sim_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    def sim(a: str, b: str) -> float:
        e = sim_model.encode([a, b], normalize_embeddings=True)
        return round(float((e[0] * e[1]).sum()), 4)

    res = {"experiment": "story_generation", "story_model": settings.story_model, "idea": idea, "length": "Short",
           "max_new_tokens": sg.max_tokens_for_length("Short"), "temperature": settings.story_temperature, "top_p": settings.story_top_p,
           "device": "cuda" if torch.cuda.is_available() else "cpu", "torch": torch.__version__, "seed": 0, "conditions": {}}

    t0 = time.perf_counter()
    pipe = sg._try_load_pipeline(settings.story_model)
    res["model_load_s"] = round(time.perf_counter() - t0, 2)
    res["pipeline_loaded"] = pipe is not None
    tok = pipe.tokenizer

    def metrics(prompt, lang, style, title, body, model_id, secs) -> dict:
        ntok = len(tok.encode(body)) if body else 0
        return {"language": lang, "style": style, "title": title, "model": model_id, "latency_s": secs, "words": word_count(body),
                "chars": len(body), "new_tokens_body": ntok, "tok_per_s": round(ntok / secs, 2) if secs > 0 else None,
                "language_match": lang_ok(body, lang), "instruction_echo_ratio": instruction_echo(body), "distinct_2": distinct2(body),
                "prompt_story_similarity": sim(idea, body), "rougeL_prompt_vs_story": rouge_l_f1(idea, body), "text": body}

    # A: the app's own generate_story_text (raw prompt, no chat template)
    # B: same prompt through the Qwen3 chat template with thinking disabled (experimental variant, not shipped)
    # C: the shipped offline composer (storyvox-local-fallback-v1)
    for cond in ("A_app_raw_prompt", "B_chat_template", "C_local_composer"):
        res["conditions"][cond] = []
    for i, (lang, style) in enumerate(items):
        name = LANGUAGE_MAP[lang]["name"]
        print(f"== {i + 1}/{len(items)} {lang} {style}", flush=True)
        torch.manual_seed(0)
        title, body, mid, secs = sg.generate_story_text(idea, lang, style, "Short")
        res["conditions"]["A_app_raw_prompt"].append(metrics(idea, lang, style, title, body, mid, secs))
        torch.manual_seed(0)
        t0 = time.perf_counter()
        full = sg.build_prompt(idea, name, style, "Short")
        chat = tok.apply_chat_template([{"role": "user", "content": full}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        out = pipe(chat, max_new_tokens=sg.max_tokens_for_length("Short"), temperature=settings.story_temperature,
                   top_p=settings.story_top_p, do_sample=True, return_full_text=False)[0]["generated_text"]
        secs = round(time.perf_counter() - t0, 3)
        title, body = sg._parse_model_output(out)
        res["conditions"]["B_chat_template"].append(metrics(idea, lang, style, title, body, settings.story_model + " (chat template)", secs))
        t0 = time.perf_counter()
        title, body = sg.local_fallback_story(idea, lang, name, style, "Short")
        secs = round(time.perf_counter() - t0, 5)
        res["conditions"]["C_local_composer"].append(metrics(idea, lang, style, title, body, "storyvox-local-fallback-v1", secs))
        save("story_generation", res)

    # summary per condition
    summ = {}
    for cond, rows in res["conditions"].items():
        lm = [r["language_match"] for r in rows if r["language_match"] is not None]
        summ[cond] = {"n": len(rows), "mean_latency_s": mean([r["latency_s"] for r in rows]), "mean_words": mean([r["words"] for r in rows]),
                      "mean_tok_per_s": mean([r["tok_per_s"] for r in rows if r["tok_per_s"]]),
                      "language_match_rate": round(sum(lm) / len(lm), 4) if lm else None,
                      "mean_instruction_echo": mean([r["instruction_echo_ratio"] for r in rows]),
                      "mean_distinct_2": mean([r["distinct_2"] for r in rows]),
                      "mean_similarity": mean([r["prompt_story_similarity"] for r in rows]),
                      "mean_rougeL": mean([r["rougeL_prompt_vs_story"] for r in rows])}
    res["summary"] = summ
    save("story_generation", res)

    # length scaling: chat-template English story + MMS narration
    scale = []
    for length in ("Short", "Medium", "Long"):
        print(f"== length {length}", flush=True)
        torch.manual_seed(0)
        t0 = time.perf_counter()
        full = sg.build_prompt(idea, "English", "Adventure", length)
        chat = tok.apply_chat_template([{"role": "user", "content": full}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        out = pipe(chat, max_new_tokens=sg.max_tokens_for_length(length), temperature=settings.story_temperature, top_p=settings.story_top_p,
                   do_sample=True, return_full_text=False)[0]["generated_text"]
        gen_s = round(time.perf_counter() - t0, 3)
        _, body = sg._parse_model_output(out)
        rel, dur, sr, mid, synth_t, rtf = tts_service.synthesize_story_narration(body, "en")
        scale.append({"length": length, "max_new_tokens": sg.max_tokens_for_length(length), "gen_s": gen_s, "words": word_count(body),
                      "audio_s": dur, "tts_s": synth_t, "rtf": rtf, "total_s": round(gen_s + synth_t, 2), "tts_model": mid})
        res["length_scaling"] = scale
        save("story_generation", res)
    save("story_generation", res)


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "all"
    if phase in ("tts_asr", "all"):
        run_tts_asr()
    if phase == "cjk":
        run_cjk()
    if phase in ("story", "all"):
        run_story()
