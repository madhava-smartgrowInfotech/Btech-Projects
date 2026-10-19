"""StoryVox automated tests: API, persistence, validation, audio paths, eval serialization."""
from __future__ import annotations

import io
import json
import wave
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import app.config as config_mod
    import app.database as db_mod

    monkeypatch.setenv("STORYVOX_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STORYVOX_AUDIO_DIR", str(tmp_path / "audio"))
    monkeypatch.setenv("STORYVOX_EVAL_DIR", str(tmp_path / "evals"))
    monkeypatch.setenv("STORYVOX_DATASET_DIR", str(tmp_path / "datasets"))
    config_mod.get_settings.cache_clear()
    db_mod.reset_engine()

    from app.main import create_app
    from app.services import story_generator, tts_service

    def fake_story(prompt, language_code, style="Adventure", length_option="Short"):
        from app.config import LANGUAGE_MAP

        lang = LANGUAGE_MAP[language_code]
        idea = " ".join(prompt.split())
        return f"A Tale of {idea[:40]}", f"Story about {idea} told in {lang['name']} with care and wonder.", "test-story-model", 0.05

    def fake_narration(story_text, language_code):
        settings = config_mod.get_settings()
        audio_dir = Path(settings.audio_dir)
        audio_dir.mkdir(parents=True, exist_ok=True)
        sr = 16000
        t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
        voiced = (0.4 * np.sin(2 * np.pi * 220 * t) + 0.2 * np.sin(2 * np.pi * 330 * t)).astype(np.float32)
        target = audio_dir / "test_narration.wav"
        with wave.open(str(target), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes((np.clip(voiced, -1, 1) * 32767).astype(np.int16).tobytes())
        rel = str(target)
        return rel, 0.5, sr, "test-tts-model", 0.1, 0.2

    monkeypatch.setattr(story_generator, "generate_story_text", fake_story)
    monkeypatch.setattr(tts_service, "synthesize_story_narration", fake_narration)
    app = create_app()
    with TestClient(app) as client:
        yield client
    config_mod.get_settings.cache_clear()
    db_mod.reset_engine()


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_languages_only_supported(client):
    res = client.get("/api/languages")
    assert res.status_code == 200
    langs = res.json()
    assert len(langs) >= 10
    codes = {l["code"] for l in langs}
    assert {"en", "fr", "de", "es"}.issubset(codes)


def test_generate_validation_empty_prompt(client):
    res = client.post("/api/stories/generate", json={"prompt": "   ", "language_code": "en", "style": "Adventure", "length_option": "Short"})
    assert res.status_code in (400, 422)


def test_generate_rejects_bad_language(client):
    res = client.post("/api/stories/generate", json={"prompt": "hello world idea", "language_code": "xx", "style": "Adventure", "length_option": "Short"})
    assert res.status_code == 422


def test_full_story_workflow(client):
    created = client.post("/api/stories/generate", json={"prompt": "a young inventor discovers a hidden library", "language_code": "en", "style": "Adventure", "length_option": "Short", "synthesize": False})
    assert created.status_code == 200, created.text
    story_id = created.json()["id"]
    listed = client.get("/api/stories")
    assert any(s["id"] == story_id for s in listed.json())
    fetched = client.get(f"/api/stories/{story_id}")
    assert fetched.status_code == 200
    assert "inventor" in fetched.json()["story_text"]
    synth = client.post(f"/api/stories/{story_id}/synthesize")
    assert synth.status_code == 200, synth.text
    deleted = client.delete(f"/api/stories/{story_id}")
    assert deleted.status_code == 200
    assert client.get(f"/api/stories/{story_id}").status_code == 404


def test_audio_path_validation_rejects_escape():
    from app.config import get_settings
    from app.utils import ensure_within_directory

    base = Path(get_settings().resolved_audio_dir)
    with pytest.raises(ValueError):
        ensure_within_directory(base, base.parent / "evil.wav")


def test_metrics_are_real_computations():
    from app.utils.metrics import cer, tfidf_cosine, wer

    assert wer("hello world", "hello world") == 0.0
    assert wer("hello world", "hello") > 0.0
    assert cer("abc", "abc") == 0.0
    assert 0.0 <= tfidf_cosine("a story about a library", "a story about a library") <= 1.0
    assert tfidf_cosine("a story about a library", "a story about a library") == 1.0


def test_evaluation_serialization(client, monkeypatch):
    from app.services import evaluation_service

    def fake_run(samples=2, language_code=None, skip_tts=False, skip_story=False):
        return {"evaluation_type": "storyvox-pipeline", "sample_count": 2, "languages": ["en"],
                "averages": {"wer": 0.25, "cer": 0.1, "prompt_story_similarity": 0.6, "story_time_s": 0.2, "tts_time_s": 0.3, "rtf": 0.6},
                "samples": [{"prompt": "x", "wer": 0.25}]}

    monkeypatch.setattr(evaluation_service, "run_evaluation", fake_run)
    res = client.post("/api/evaluations/run", json={"samples": 2})
    assert res.status_code == 200
    assert res.json()["metrics"]["averages"]["wer"] == 0.25
    rows = client.get("/api/evaluations")
    assert rows.status_code == 200
    assert len(rows.json()) >= 1
