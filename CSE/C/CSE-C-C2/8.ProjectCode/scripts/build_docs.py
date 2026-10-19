"""Generate the StoryVox product documentation PDF."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def latest_eval_summary() -> str:
    from app.config import get_settings

    d = get_settings().resolved_eval_dir
    files = sorted(d.glob("storyvox_evaluation_*.json"), reverse=True)
    if not files:
        return "Evaluation has not been run yet. Run POST /api/evaluations/run or python scripts/evaluate.py --samples 5 to populate this section with measured values."
    try:
        payload = json.loads(files[0].read_text(encoding="utf-8"))
        avg = payload.get("averages", {})
        return (
            f"Latest evaluation file: {files[0].name} | samples: {payload.get('sample_count')} | "
            f"WER: {avg.get('wer')} | CER: {avg.get('cer')} | similarity: {avg.get('prompt_story_similarity')} | "
            f"story latency: {avg.get('story_time_s')}s | TTS latency: {avg.get('tts_time_s')}s | RTF: {avg.get('rtf')}"
        )
    except Exception:
        return "Evaluation files exist but could not be parsed."


SECTIONS: list[tuple[str, str]] = [
    ("1. Product overview", "StoryVox is a local-first multilingual storytelling application. A user enters a story idea, chooses a language, style and length, and StoryVox writes an original story with a pretrained language model and narrates it with a pretrained multilingual speech model. Stories, narration audio and evaluation results are stored locally in SQLite and on disk."),
    ("2. Key features", "Story creator with language/style/length selection; automatic narration with playback and download; regenerate-narration action; searchable history with view/play/download/delete; measurable evaluation dashboard (WER, CER, similarity, latency, RTF); lazy model loading with CPU support; local storage and privacy note."),
    ("3. User workflow", "1) Enter a story idea. 2) Select language, style and length. 3) Press Generate Story. 4) Read the story, play or download the narration. 5) Revisit or delete items in History. 6) Run and review Evaluation for measured pipeline quality."),
    ("4. Technology stack", "Python, FastAPI, Uvicorn, SQLite + SQLAlchemy, Pydantic, Hugging Face Transformers + PyTorch (Qwen3 story models, MMS multilingual TTS checkpoints, Whisper ASR), soundfile/numpy audio handling, HTML/CSS/JavaScript frontend served by FastAPI, pytest for tests."),
    ("5. Architecture summary", "Single FastAPI service on 127.0.0.1. Layers: REST API -> services (story_generator, tts_service behind a TTSProvider interface, asr_service, evaluation_service) -> SQLite persistence + WAV files under data/audio. Models load lazily and are cached in memory; CUDA is used when available, otherwise CPU."),
    ("6. Story-generation pipeline", "The user prompt is combined with target language, style guidance and length budget into an instruction prompt. A pretrained Qwen3 instruction model generates a title plus story body (temperature/top-p/max-tokens configurable). Output is parsed into title/body, word counts and timings are recorded, and the record is stored in the stories table."),
    ("7. Multilingual TTS pipeline", "Story text is chunked at sentence boundaries, synthesized per chunk with the language-matched MMS checkpoint (VITS), normalized to 16 kHz mono, concatenated with short pauses, validated for non-silence, and written as WAV. Synthesis time, duration and RTF (synthesis_time / audio_duration) are stored in audio_outputs. An offline OS speech fallback is used only when the pretrained checkpoint cannot load, and the actual model id is always recorded."),
    ("8. Database design", "stories(id, prompt, title, story_text, language_code, language_name, style, length_option, word_count, created_at, generation_time_seconds); audio_outputs(id, story_id, file_path relative, duration_seconds, sample_rate, tts_model, synthesis_time_seconds, rtf, created_at); evaluations(id, evaluation_type, language_code, sample_count, metrics_json, created_at). Deleting a story removes its rows and audio files."),
    ("9. Evaluation methodology", "scripts/evaluate.py generates stories from fixed prompts, synthesizes narration, transcribes it with Whisper, and computes WER/CER against the story text, prompt-story similarity (multilingual sentence model when available, otherwise TF-IDF cosine), ROUGE-L overlap, plus story/TTS latency and RTF. Results are saved as JSON and CSV under data/evaluations and shown in the UI. No values are pre-filled; unevaluated states display 'Evaluation has not been run yet.'"),
    ("10. Actual results/metrics", "RESULT_PLACEHOLDER"),
    ("11. How to run", "Method A: double-click run.bat, wait for dependency install and first-time model downloads, open http://localhost:8000. Method B: Docker via run-docker.bat. Method C: create a venv, pip install -r requirements.txt, run uvicorn app.main:app --host 127.0.0.1 --port 8000. Full steps are in HOW_TO_RUN.md."),
    ("12. Limitations", "CPU inference is slower than GPU; first runs download model weights; narration quality depends on the selected checkpoint and language; offline fallback voices are more robotic; very long stories are capped by token budgets; evaluation transcription adds runtime cost."),
    ("13. Future improvements", "Streaming generation progress, per-story voice selection where the TTS model supports it, background evaluation jobs, export of stories to e-book formats, and optional objective naturalness scoring when a lightweight compatible model is available."),
]


def main() -> None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception as exc:
        print(f"reportlab unavailable ({exc}); writing markdown fallback.")
        out_md = Path("StoryVox_Product_Documentation.md")
        text = "# StoryVox Product Documentation\n\n" + "\n\n".join(f"## {t}\n\n{b}" for t, b in SECTIONS)
        out_md.write_text(text.replace("RESULT_PLACEHOLDER", latest_eval_summary()), encoding="utf-8")
        return
    from app.config import BASE_DIR

    out = BASE_DIR / "StoryVox_Product_Documentation.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, title="StoryVox Product Documentation")
    styles = getSampleStyleSheet()
    story = [Paragraph("StoryVox — Product Documentation", styles["Title"]), Spacer(1, 12)]
    for title, body in SECTIONS:
        if "RESULT_PLACEHOLDER" in body:
            body = latest_eval_summary()
        story += [Paragraph(title, styles["Heading2"]), Paragraph(body, styles["BodyText"]), Spacer(1, 8)]
    doc.build(story)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
