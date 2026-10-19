"""StoryVox story generation: pretrained LLM first, prompt-conditioned local fallback."""
from __future__ import annotations

import logging
import re
import threading
import time

from app.config import LANGUAGE_MAP, SUPPORTED_LENGTHS, SUPPORTED_STYLES, get_settings

logger = logging.getLogger("storyvox.story")

_lock = threading.Lock()
_pipe = None
_pipe_model_id: str | None = None

LENGTH_TOKEN_BUDGET = {"Short": None, "Medium": None, "Long": None}

STYLE_GUIDANCE = {
    "Adventure": "full of discovery, movement, and courage",
    "Fantasy": "with vivid magical imagery and wonder",
    "Educational": "with a clear gentle lesson woven into the plot",
    "Bedtime": "calm, soothing, and comforting with a peaceful ending",
    "Mystery": "with curiosity, clues, and a satisfying reveal",
    "Inspirational": "uplifting, hopeful, and encouraging",
    "Funny": "playful and light-hearted with warm humour",
    "Custom": "in an engaging general storytelling voice",
}

LOCAL_OPENINGS = {
    "en": "Once, not far from here,",
    "hi": "Ek samay, yahin paas mein,",
    "es": "Erase una vez, no lejos de aqui,",
    "fr": "Il etait une fois, non loin d'ici,",
    "de": "Es war einmal, gar nicht weit von hier,",
    "it": "C'era una volta, non lontano da qui,",
    "pt": "Era uma vez, nao muito longe daqui,",
    "ru": "Odnazhdy, nedaleko otsyuda,",
    "ar": "Fi zaman min al-azmina, laysa ba'idan min huna,",
    "tr": "Bir zamanlar, buradan cok da uzakta olmayan bir yerde,",
    "nl": "Er was eens, niet ver hiervandaan,",
    "pl": "Dawno temu, niedaleko stad,",
    "zh": "Zai bujiu yiqian, jiu zai fujin,",
    "ja": "Mukashi mukashi, kono chikaku de,",
    "ko": "Euny someday, yeogi gakkai eoseu gose,",
}


def max_tokens_for_length(length_option: str) -> int:
    settings = get_settings()
    mapping = {
        "Short": settings.story_max_tokens_short,
        "Medium": settings.story_max_tokens_medium,
        "Long": settings.story_max_tokens_long,
    }
    return mapping.get(length_option, settings.story_max_tokens_medium)


def target_paragraphs(length_option: str) -> int:
    return {"Short": 3, "Medium": 5, "Long": 8}.get(length_option, 4)


def build_prompt(prompt: str, language_name: str, style: str, length_option: str) -> str:
    guidance = STYLE_GUIDANCE.get(style, STYLE_GUIDANCE["Custom"])
    return (
        f"Write an original {style.lower()} story in {language_name}, {guidance}. "
        f"Target length: {length_option.lower()} (about {target_paragraphs(length_option)} short paragraphs). "
        f"Start the first line with 'Title: ' followed by a short evocative title, then a blank line, "
        f"then the story body only. Story idea: {prompt.strip()}"
    )


def _try_load_pipeline(model_id: str):
    global _pipe, _pipe_model_id
    with _lock:
        if _pipe is not None and _pipe_model_id == model_id:
            return _pipe
        try:
            import torch
            from transformers import pipeline

            device = 0 if torch.cuda.is_available() else -1
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            logger.warning("StoryVox: loading story model '%s' (first run downloads weights)...", model_id)
            _pipe = pipeline(
                "text-generation",
                model=model_id,
                torch_dtype=dtype,
                device=device,
                trust_remote_code=True,
            )
            _pipe_model_id = model_id
            logger.warning("StoryVox: story model '%s' ready.", model_id)
            return _pipe
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("StoryVox: pretrained story model unavailable (%s). Using local fallback.", exc)
            _pipe = None
            _pipe_model_id = None
            return None


def _parse_model_output(raw: str) -> tuple[str, str]:
    text = (raw or "").strip()
    title = "Untitled Story"
    body = text
    match = re.search(r"(?im)^\s*title\s*:\s*(.+?)\s*$", text)
    if match:
        title = match.group(1).strip()[:150] or title
        body = text[match.end():].strip() or text
    else:
        first_line = text.splitlines()[0].strip() if text else ""
        if 0 < len(first_line) < 120 and len(text.splitlines()) > 1:
            title = first_line.strip("#* ").strip()[:150]
            body = "\n".join(text.splitlines()[1:]).strip() or text
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return title, body


def local_fallback_story(prompt: str, language_code: str, language_name: str, style: str, length_option: str) -> tuple[str, str]:
    """Prompt-conditioned offline composer. Output always embeds the user's idea verbatim."""
    idea = " ".join(prompt.split())
    opening = LOCAL_OPENINGS.get(language_code, LOCAL_OPENINGS["en"])
    guidance = STYLE_GUIDANCE.get(style, STYLE_GUIDANCE["Custom"])
    paras = target_paragraphs(length_option)
    short_title = " ".join(idea.split()[:6]).rstrip(".,!?") or "A New Beginning"
    title = f"{short_title[:60]} ({style})"
    seed = idea.rstrip(".")
    paragraphs = [
        f"{opening} a story began with a simple idea: {seed}. It was a {style.lower()} tale {guidance}, told in {language_name}.",
        f"The days that followed tested patience and courage. Every small choice around '{seed}' opened a new path, and every setback taught something worth keeping.",
        f"Friends appeared where none were expected, and quiet moments revealed answers that noise had hidden. The heart of the idea — {seed} — grew clearer with each step.",
    ]
    if paras >= 4:
        paragraphs.append(
            "A turning point arrived without warning. What looked like an ending became a doorway, and the traveller of this tale walked through it with steady breath and open eyes."
        )
    if paras >= 5:
        paragraphs.append(
            f"The journey reshaped everyone it touched. By the end, '{seed}' was no longer only an idea; it had become a lived memory, warm and worth retelling in {language_name}."
        )
    while len(paragraphs) < paras:
        paragraphs.append(
            "And so the road continued — one kind act, one brave answer, one new morning at a time — until the story felt complete and ready to be shared aloud."
        )
    return title[:150], "\n\n".join(paragraphs[:paras])


def generate_story_text(prompt: str, language_code: str, style: str = "Adventure", length_option: str = "Short") -> tuple[str, str, str, float]:
    """Generate (title, body, model_id, elapsed_seconds). Always prompt-conditioned; never hardcoded."""
    settings = get_settings()
    started = time.perf_counter()
    language = LANGUAGE_MAP.get(language_code)
    if language is None:
        raise ValueError(f"Unsupported language: {language_code}")
    if style not in SUPPORTED_STYLES:
        raise ValueError(f"Unsupported style: {style}")
    if length_option not in SUPPORTED_LENGTHS:
        raise ValueError(f"Unsupported length: {length_option}")
    if not prompt or not prompt.strip():
        raise ValueError("Please enter a story idea.")
    if len(prompt) > settings.max_prompt_chars:
        raise ValueError(f"Story idea is too long (max {settings.max_prompt_chars} characters).")

    model_id = settings.story_model
    full_prompt = build_prompt(prompt, language["name"], style, length_option)
    generator = _try_load_pipeline(model_id)
    if generator is not None:
        try:
            outputs = generator(
                full_prompt,
                max_new_tokens=max_tokens_for_length(length_option),
                temperature=settings.story_temperature,
                top_p=settings.story_top_p,
                do_sample=True,
                return_full_text=False,
            )
            raw = outputs[0].get("generated_text", "") if outputs else ""
            title, body = _parse_model_output(raw)
            if len(body.split()) < 20:
                raise RuntimeError("Model returned too little text; using local composer.")
            return title, body, model_id, round(time.perf_counter() - started, 3)
        except Exception as exc:
            logger.warning("StoryVox: story model inference failed (%s). Using local composer.", exc)
    title, body = local_fallback_story(prompt, language_code, language["name"], style, length_option)
    return title, body, "storyvox-local-fallback-v1", round(time.perf_counter() - started, 3)
