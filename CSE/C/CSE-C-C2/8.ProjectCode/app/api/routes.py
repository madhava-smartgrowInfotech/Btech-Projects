"""StoryVox REST API routes."""
from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import LANGUAGE_MAP, SUPPORTED_LANGUAGES, SUPPORTED_LENGTHS, SUPPORTED_STYLES, get_settings
from app.database import get_session_factory
from app.models import AudioOutput, Evaluation, Story
from app.schemas import (
    AudioResponse,
    EvaluationRunRequest,
    EvaluationSummary,
    LanguageInfo,
    StoryGenerateRequest,
    StoryListItem,
    StoryResponse,
)
from app.services import story_generator, tts_service
from app.utils import listening_time_minutes, reading_time_minutes, word_count

logger = logging.getLogger("storyvox.api")
router = APIRouter(prefix="/api")


def get_db():
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


def _audio_to_schema(a: AudioOutput) -> AudioResponse:
    return AudioResponse(
        id=a.id, story_id=a.story_id, file_path=f"/api/audio/{a.id}",
        duration_seconds=a.duration_seconds, sample_rate=a.sample_rate,
        tts_model=a.tts_model, synthesis_time_seconds=a.synthesis_time_seconds,
        rtf=a.rtf, created_at=a.created_at,
    )


def _story_to_schema(s: Story, latest_audio: AudioOutput | None = None) -> StoryResponse:
    audio_schema = _audio_to_schema(latest_audio) if latest_audio else None
    listen_min = listening_time_minutes(latest_audio.duration_seconds if latest_audio else 0.0, s.story_text)
    return StoryResponse(
        id=s.id, prompt=s.prompt, title=s.title, story_text=s.story_text,
        language_code=s.language_code, language_name=s.language_name, style=s.style,
        length_option=s.length_option, word_count=s.word_count,
        reading_time_minutes=reading_time_minutes(s.story_text),
        listening_time_minutes=listen_min, generation_time_seconds=s.generation_time_seconds,
        created_at=s.created_at, audio=audio_schema,
    )


@router.get("/health")
def health():
    try:
        import torch

        cuda = bool(torch.cuda.is_available())
    except Exception:
        cuda = False
    return {"status": "ok", "app": "StoryVox", "cuda": cuda, "time": time.time()}


@router.get("/languages", response_model=list[LanguageInfo])
def list_languages():
    return SUPPORTED_LANGUAGES


@router.get("/meta")
def meta():
    settings = get_settings()
    return {
        "app": "StoryVox",
        "styles": SUPPORTED_STYLES,
        "lengths": SUPPORTED_LENGTHS,
        "story_model": settings.story_model,
        "asr_model": settings.asr_model,
    }


@router.post("/stories/generate", response_model=StoryResponse)
def generate_story(payload: StoryGenerateRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    if not payload.prompt.strip():
        raise HTTPException(status_code=422, detail="Please enter a story idea.")
    if len(payload.prompt) > settings.max_prompt_chars:
        raise HTTPException(status_code=422, detail=f"Story idea is too long (max {settings.max_prompt_chars} characters).")
    if payload.language_code not in LANGUAGE_MAP:
        raise HTTPException(status_code=422, detail="This language is not currently supported for narration.")
    if payload.style not in SUPPORTED_STYLES:
        raise HTTPException(status_code=422, detail="Unsupported story style.")
    if payload.length_option not in SUPPORTED_LENGTHS:
        raise HTTPException(status_code=422, detail="Unsupported story length.")
    try:
        title, body, _model_id, gen_time = story_generator.generate_story_text(
            payload.prompt, payload.language_code, payload.style, payload.length_option
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("StoryVox: story generation failed")
        raise HTTPException(status_code=500, detail="Story generation failed. Check the server log for details.")
    lang = LANGUAGE_MAP[payload.language_code]
    story = Story(
        prompt=payload.prompt.strip(), title=title, story_text=body,
        language_code=payload.language_code, language_name=lang["name"],
        style=payload.style, length_option=payload.length_option,
        word_count=word_count(body), generation_time_seconds=gen_time,
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    latest_audio = None
    if payload.synthesize:
        try:
            rel, dur, sr, tts_model, synth_t, rtf = tts_service.synthesize_story_narration(body, payload.language_code)
            record = AudioOutput(story_id=story.id, file_path=rel if isinstance(rel, str) else str(rel),
                                 duration_seconds=dur, sample_rate=sr, tts_model=tts_model,
                                 synthesis_time_seconds=synth_t, rtf=rtf)
            db.add(record)
            db.commit()
            db.refresh(record)
            latest_audio = record
        except (ValueError, RuntimeError) as exc:
            logger.warning("StoryVox: narration skipped: %s", exc)
        except Exception:
            logger.exception("StoryVox: narration failed")
    return _story_to_schema(story, latest_audio)


@router.post("/stories/{story_id}/synthesize", response_model=AudioResponse)
def synthesize_story(story_id: int, db: Session = Depends(get_db)):
    story = db.get(Story, story_id)
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found.")
    try:
        rel, dur, sr, tts_model, synth_t, rtf = tts_service.synthesize_story_narration(story.story_text, story.language_code)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception:
        logger.exception("StoryVox: narration failed")
        raise HTTPException(status_code=500, detail="Narration could not be generated. Check the server log for details.")
    record = AudioOutput(story_id=story.id, file_path=str(rel), duration_seconds=dur,
                         sample_rate=sr, tts_model=tts_model, synthesis_time_seconds=synth_t, rtf=rtf)
    db.add(record)
    db.commit()
    db.refresh(record)
    return _audio_to_schema(record)


@router.get("/stories", response_model=list[StoryListItem])
def list_stories(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)):
    stories = db.query(Story).order_by(Story.created_at.desc()).limit(limit).all()
    items = []
    for s in stories:
        audios = db.query(AudioOutput).filter(AudioOutput.story_id == s.id).order_by(AudioOutput.created_at.desc()).all()
        items.append(StoryListItem(id=s.id, title=s.title, language_code=s.language_code,
                                   language_name=s.language_name, style=s.style, word_count=s.word_count,
                                   created_at=s.created_at, has_audio=bool(audios),
                                   audio_id=audios[0].id if audios else None))
    return items


@router.get("/stories/{story_id}", response_model=StoryResponse)
def get_story(story_id: int, db: Session = Depends(get_db)):
    story = db.get(Story, story_id)
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found.")
    latest = db.query(AudioOutput).filter(AudioOutput.story_id == story.id).order_by(AudioOutput.created_at.desc()).first()
    return _story_to_schema(story, latest)


@router.delete("/stories/{story_id}")
def delete_story(story_id: int, db: Session = Depends(get_db)):
    story = db.get(Story, story_id)
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found.")
    audios = db.query(AudioOutput).filter(AudioOutput.story_id == story.id).all()
    for a in audios:
        try:
            abs_path = tts_service.resolve_audio_abs_path(a.file_path)
            audio_dir = get_settings().resolved_audio_dir.resolve()
            if audio_dir in abs_path.parents and abs_path.exists():
                abs_path.unlink()
        except Exception:
            logger.warning("StoryVox: could not remove audio file for story %s", story_id)
    db.delete(story)
    db.commit()
    return {"status": "deleted", "id": story_id}


@router.get("/audio/{audio_id}")
def stream_audio(audio_id: int, db: Session = Depends(get_db)):
    record = db.get(AudioOutput, audio_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Audio not found.")
    try:
        abs_path = tts_service.resolve_audio_abs_path(record.file_path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Stored audio path is invalid.")
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="Audio file is missing on disk.")
    return FileResponse(str(abs_path), media_type="audio/wav", filename=f"storyvox_narration_{audio_id}.wav")


@router.get("/evaluations", response_model=list[EvaluationSummary])
def list_evaluations(db: Session = Depends(get_db)):
    rows = db.query(Evaluation).order_by(Evaluation.created_at.desc()).limit(50).all()
    if rows:
        return [EvaluationSummary(id=r.id, evaluation_type=r.evaluation_type, language_code=r.language_code,
                                  sample_count=r.sample_count, metrics_json=r.metrics_json, created_at=r.created_at) for r in rows]
    # Fall back to files on disk so fresh evaluation runs are visible even before DB sync.
    from app.services import evaluation_service

    summaries = []
    for idx, item in enumerate(evaluation_service.list_saved_evaluations()[:20]):
        payload = item["payload"]
        summaries.append(EvaluationSummary(id=100000 + idx, evaluation_type=str(payload.get("evaluation_type", "storyvox-pipeline")),
                                           language_code=",".join(payload.get("languages", [])[:4]) or "mixed",
                                           sample_count=int(payload.get("sample_count", 0)),
                                           metrics_json=payload, created_at=payload.get("created_at", "")))
    return summaries


@router.post("/evaluations/run")
def run_evaluation(payload: EvaluationRunRequest, db: Session = Depends(get_db)):
    from app.services import evaluation_service

    if payload.language_code and payload.language_code not in LANGUAGE_MAP:
        raise HTTPException(status_code=422, detail="This language is not currently supported for narration.")
    try:
        metrics = evaluation_service.run_evaluation(samples=payload.samples, language_code=payload.language_code,
                                                    skip_tts=payload.skip_tts, skip_story=payload.skip_story)
    except Exception:
        logger.exception("StoryVox: evaluation failed")
        raise HTTPException(status_code=500, detail="Evaluation failed. Check the server log for details.")
    record = Evaluation(evaluation_type=str(metrics.get("evaluation_type", "storyvox-pipeline")),
                        language_code=payload.language_code or "mixed",
                        sample_count=int(metrics.get("sample_count", 0)), metrics_json=metrics)
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "metrics": metrics}
