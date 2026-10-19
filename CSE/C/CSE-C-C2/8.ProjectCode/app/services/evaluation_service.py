"""StoryVox evaluation service: real computed metrics only."""
from __future__ import annotations

import csv
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.utils.metrics import cer, rouge_l_f1, tfidf_cosine, wer

logger = logging.getLogger("storyvox.eval")


def default_eval_prompts() -> list[dict]:
    return [
        {"prompt": "Tell a story about a young inventor who discovers a hidden library.", "language_code": "en", "style": "Adventure", "length_option": "Short"},
        {"prompt": "A kind robot helps a village during a storm.", "language_code": "en", "style": "Bedtime", "length_option": "Short"},
        {"prompt": "Un jardin secret cache une porte vers les etoiles.", "language_code": "fr", "style": "Fantasy", "length_option": "Short"},
        {"prompt": "Ein mutiger Baecker rettet sein Dorf mit warmem Brot.", "language_code": "de", "style": "Inspirational", "length_option": "Short"},
        {"prompt": "Una nina sigue a una luciérnaga hasta un bosque magico.", "language_code": "es", "style": "Mystery", "length_option": "Short"},
    ]


def _try_semantic_similarity(a: str, b: str, lang: str) -> tuple[float, str]:
    try:
        from sentence_transformers import SentenceTransformer
        import torch

        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        with torch.no_grad():
            emb = model.encode([a, b], normalize_embeddings=True)
        import numpy as np

        sim = float(np.dot(emb[0], emb[1]))
        return round(max(-1.0, min(1.0, sim)), 4), "paraphrase-multilingual-MiniLM-L12-v2 cosine"
    except Exception:
        return tfidf_cosine(a, b), "tf-idf cosine (offline similarity proxy)"


def run_evaluation(samples: int = 5, language_code: str | None = None, skip_tts: bool = False, skip_story: bool = False) -> dict:
    """Run the measurable pipeline and persist JSON+CSV. Returns the metrics payload."""
    from app.services import story_generator, tts_service

    settings = get_settings()
    prompts = default_eval_prompts()
    if language_code:
        filtered = [p for p in prompts if p["language_code"] == language_code]
        prompts = filtered or prompts
    prompts = prompts[: max(1, samples)]

    per_sample: list[dict] = []
    wers: list[float] = []
    cers: list[float] = []
    sims: list[float] = []
    rouge: list[float] = []
    story_lat: list[float] = []
    tts_lat: list[float] = []
    rtfs: list[float] = []

    for item in prompts:
        row: dict = {"prompt": item["prompt"], "language_code": item["language_code"], "style": item["style"]}
        t0 = time.perf_counter()
        if skip_story:
            title, body, model_id = "Evaluation story (skipped generation)", item["prompt"], "skipped"
            gen_time = 0.0
        else:
            title, body, model_id, gen_time = story_generator.generate_story_text(
                item["prompt"], item["language_code"], item["style"], item["length_option"]
            )
        row.update({"title": title, "model": model_id, "story_time_s": gen_time, "story_words": len(body.split())})
        story_lat.append(gen_time)
        sim, sim_name = _try_semantic_similarity(item["prompt"], body, item["language_code"])
        row["prompt_story_similarity"] = sim
        row["similarity_method"] = sim_name
        sims.append(sim)
        rl = rouge_l_f1(item["prompt"], body)
        row["rougeL_prompt_vs_story"] = rl
        rouge.append(rl)
        if not skip_tts:
            try:
                rel, dur, sr, tts_model, synth_t, rtf = tts_service.synthesize_story_narration(body, item["language_code"])
                row.update({"tts_model": tts_model, "tts_time_s": synth_t, "audio_duration_s": dur, "rtf": rtf})
                tts_lat.append(synth_t)
                rtfs.append(rtf)
                # Transcribe for intelligibility
                try:
                    from app.services.asr_service import transcribe_wav
                    from app.services.tts_service import resolve_audio_abs_path

                    hyp = transcribe_wav(resolve_audio_abs_path(rel), item["language_code"])
                    row["asr_transcription"] = hyp[:500]
                    w = wer(body, hyp)
                    c = cer(body, hyp)
                    row["wer"] = w
                    row["cer"] = c
                    wers.append(w)
                    cers.append(c)
                except Exception as exc:
                    row["asr_error"] = str(exc)[:300]
            except Exception as exc:
                row["tts_error"] = str(exc)[:300]
        row["total_time_s"] = round(time.perf_counter() - t0, 3)
        per_sample.append(row)

    def _mean(values: list[float]) -> float | None:
        return round(sum(values) / len(values), 4) if values else None

    metrics = {
        "evaluation_type": "storyvox-pipeline",
        "sample_count": len(per_sample),
        "languages": sorted({r["language_code"] for r in per_sample}),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "averages": {
            "prompt_story_similarity": _mean(sims),
            "rougeL_prompt_vs_story": _mean(rouge),
            "wer": _mean(wers),
            "cer": _mean(cers),
            "story_time_s": _mean(story_lat),
            "tts_time_s": _mean(tts_lat),
            "rtf": _mean(rtfs),
        },
        "metric_notes": {
            "prompt_story_similarity": "Cosine similarity between prompt and generated story (multilingual sentence model when available, otherwise TF-IDF proxy). Higher means the story stayed on-topic.",
            "rougeL_prompt_vs_story": "ROUGE-L F1 overlap between prompt and story; low values are normal since stories expand on prompts.",
            "wer": "Word Error Rate between story text and ASR transcription of narration. Lower is clearer. Computed only when TTS+ASR both ran.",
            "cer": "Character Error Rate, same comparison as WER but character-level.",
            "story_time_s": "Mean story-generation latency per sample.",
            "tts_time_s": "Mean narration synthesis latency per sample.",
            "rtf": "Real-time factor = synthesis_time / audio_duration. Below 1.0 means faster than real time.",
        },
        "asr_model": settings.asr_model,
        "story_model": settings.story_model,
        "samples": per_sample,
    }
    _persist(metrics)
    return metrics


def _persist(metrics: dict) -> Path:
    settings = get_settings()
    out_dir = settings.resolved_eval_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"storyvox_evaluation_{stamp}.json"
    json_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    csv_path = out_dir / f"storyvox_evaluation_{stamp}.csv"
    rows = metrics.get("samples", [])
    if rows:
        keys = sorted({k for r in rows for k in r.keys()})
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=keys)
            writer.writeheader()
            for r in rows:
                writer.writerow({k: (str(r.get(k, ""))[:800]) for k in keys})
    logger.warning("StoryVox: evaluation saved to %s", json_path.name)
    return json_path


def list_saved_evaluations() -> list[dict]:
    settings = get_settings()
    out_dir = settings.resolved_eval_dir
    if not out_dir.exists():
        return []
    results = []
    for path in sorted(out_dir.glob("storyvox_evaluation_*.json"), reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            results.append({"file": path.name, "payload": payload})
        except Exception:
            continue
    return results
