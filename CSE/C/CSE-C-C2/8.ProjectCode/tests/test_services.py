"""Unit tests for the pure parts of StoryVox (text, audio and metric helpers, the offline composer) and extra API edge cases."""
from __future__ import annotations

import numpy as np
import pytest

from tests.test_api import client  # noqa: F401  (re-use the isolated-app fixture)


# ----------------------------------------------------------------------------- text helpers
def test_word_count_and_times():
    from app.utils import listening_time_minutes, reading_time_minutes, word_count

    assert word_count("Once upon a time") == 4
    assert word_count("") == 0
    assert reading_time_minutes("word " * 200) == 1.0
    assert listening_time_minutes(90.0) == 1.5
    assert listening_time_minutes(0.0, "word " * 150) == 1.0


def test_chunk_text_respects_limit_and_sentence_boundaries():
    from app.utils import chunk_text

    text = " ".join(f"This is sentence number {i}." for i in range(60))
    chunks = chunk_text(text, max_chars=120)
    assert len(chunks) > 5
    assert all(len(c) <= 120 for c in chunks)
    assert " ".join(chunks).split() == text.split()           # nothing lost or reordered
    assert chunk_text("   ") == []


def test_chunk_text_splits_one_long_sentence():
    from app.utils import chunk_text

    chunks = chunk_text("x" * 1000, max_chars=380)
    assert [len(c) for c in chunks] == [380, 380, 240]


def test_chunk_text_splits_on_devanagari_danda():
    from app.utils import chunk_text

    text = ("यह पहला वाक्य है। " * 30).strip()
    assert len(chunk_text(text, max_chars=100)) > 1


def test_sanitize_filename_and_unique_names():
    from app.utils import sanitize_filename, unique_audio_filename

    assert sanitize_filename("Héllo wörld / story?!") == "hello_world_story"
    assert sanitize_filename("???") == "storyvox"
    a, b = unique_audio_filename(1), unique_audio_filename(1)
    assert a != b and a.endswith(".wav")


# ----------------------------------------------------------------------------- audio helpers
def test_audio_helpers_round_trip(tmp_path):
    from app.utils.audio import audio_duration_seconds, concat_wav_segments, is_silent, read_wav_mono, rms_energy, write_wav_mono

    sr = 16000
    t = np.linspace(0, 1, sr, endpoint=False)
    tone = (0.5 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    path = tmp_path / "t.wav"
    write_wav_mono(path, tone, sr)
    back, sr2 = read_wav_mono(path, target_sr=sr)
    assert sr2 == sr and abs(len(back) - sr) <= 1
    assert not is_silent(back)
    assert is_silent(np.zeros(1000, dtype=np.float32))
    assert rms_energy(np.zeros(0)) == 0.0
    joined = concat_wav_segments([tone, tone], sample_rate=sr, pause_seconds=0.25)
    assert audio_duration_seconds(joined, sr) == pytest.approx(2.25, abs=0.01)
    assert concat_wav_segments([], sr).size == 0


def test_read_wav_resamples_to_target(tmp_path):
    from app.utils.audio import read_wav_mono, write_wav_mono

    path = tmp_path / "s.wav"
    write_wav_mono(path, np.sin(np.linspace(0, 200, 22050)).astype(np.float32) * 0.4, 22050)
    audio, sr = read_wav_mono(path, target_sr=16000)
    assert sr == 16000 and abs(len(audio) - 16000) <= 2


# ----------------------------------------------------------------------------- metrics
def test_wer_cer_known_values():
    from app.utils.metrics import cer, wer

    assert wer("the cat sat", "the cat sat") == 0.0
    assert wer("the cat sat", "the dog sat") == pytest.approx(1 / 3)
    assert wer("a b c d", "") == 1.0
    assert cer("abcd", "abxd") == pytest.approx(0.25)


def test_rouge_and_tfidf_bounds():
    from app.utils.metrics import rouge_l_f1, tfidf_cosine

    assert rouge_l_f1("a kind robot helps", "a kind robot helps") == 1.0
    assert 0.0 <= rouge_l_f1("a kind robot", "completely different words") <= 1.0
    assert tfidf_cosine("", "text") == 0.0
    assert tfidf_cosine("a b", "c d") == 0.0


# ----------------------------------------------------------------------------- story generator (offline parts)
def test_build_prompt_contains_all_controls():
    from app.services import story_generator as sg

    p = sg.build_prompt("a dragon who bakes", "Hindi", "Funny", "Long")
    assert "funny" in p and "Hindi" in p and "8 short paragraphs" in p and "a dragon who bakes" in p


def test_parse_model_output_title_forms():
    from app.services.story_generator import _parse_model_output

    assert _parse_model_output("Title: The Lamp\n\nBody text here.") == ("The Lamp", "Body text here.")
    title, body = _parse_model_output("A Short Heading\nFirst real line of the tale.")
    assert title == "A Short Heading" and body == "First real line of the tale."
    assert _parse_model_output("")[0] == "Untitled Story"


def test_token_budgets_follow_length():
    from app.services import story_generator as sg

    short, medium, long_ = (sg.max_tokens_for_length(x) for x in ("Short", "Medium", "Long"))
    assert short < medium < long_
    assert [sg.target_paragraphs(x) for x in ("Short", "Medium", "Long")] == [3, 5, 8]


def test_local_composer_is_prompt_conditioned_in_every_language():
    from app.config import LANGUAGE_MAP
    from app.services.story_generator import local_fallback_story

    for code, lang in LANGUAGE_MAP.items():
        title, body = local_fallback_story("a lighthouse keeper befriends a storm", code, lang["name"], "Mystery", "Medium")
        assert "lighthouse keeper befriends a storm" in body
        assert len(body.split("\n\n")) == 5


def test_generate_story_text_validation_errors():
    from app.services import story_generator as sg

    with pytest.raises(ValueError):
        sg.generate_story_text("hello", "xx")
    with pytest.raises(ValueError):
        sg.generate_story_text("hello", "en", style="Nope")
    with pytest.raises(ValueError):
        sg.generate_story_text("hello", "en", length_option="Huge")
    with pytest.raises(ValueError):
        sg.generate_story_text("   ", "en")


# ----------------------------------------------------------------------------- configuration
def test_language_table_is_consistent():
    from app.config import LANGUAGE_MAP, SUPPORTED_LANGUAGES, SUPPORTED_LENGTHS, SUPPORTED_STYLES

    assert len(SUPPORTED_LANGUAGES) == 15 == len(LANGUAGE_MAP)
    assert len(SUPPORTED_STYLES) == 8 and len(SUPPORTED_LENGTHS) == 3
    assert all(l["tts_checkpoint"].startswith("facebook/mms-tts-") for l in SUPPORTED_LANGUAGES)


# ----------------------------------------------------------------------------- API edge cases
def test_unknown_story_and_audio_are_404(client):
    assert client.get("/api/stories/999").status_code == 404
    assert client.delete("/api/stories/999").status_code == 404
    assert client.post("/api/stories/999/synthesize").status_code == 404
    assert client.get("/api/audio/999").status_code == 404


def test_prompt_too_long_and_bad_options_rejected(client):
    base = {"prompt": "a gentle idea", "language_code": "en", "style": "Adventure", "length_option": "Short"}
    assert client.post("/api/stories/generate", json={**base, "prompt": "x" * 2001}).status_code == 422
    assert client.post("/api/stories/generate", json={**base, "style": "Horror"}).status_code == 422
    assert client.post("/api/stories/generate", json={**base, "length_option": "Epic"}).status_code == 422
    assert client.post("/api/stories/generate", json={"language_code": "en"}).status_code == 422


def test_generate_with_narration_links_audio_and_streams_it(client):
    created = client.post("/api/stories/generate", json={"prompt": "a robot learns to sing", "language_code": "fr", "style": "Funny", "length_option": "Short"})
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["language_name"] == "French" and body["audio"]["tts_model"] == "test-tts-model"
    audio = client.get(body["audio"]["file_path"])
    assert audio.status_code == 200 and audio.headers["content-type"] == "audio/wav" and audio.content[:4] == b"RIFF"
    listed = client.get("/api/stories").json()
    assert listed[0]["has_audio"] is True and listed[0]["audio_id"] == body["audio"]["id"]


def test_delete_removes_audio_file_and_rows(client):
    from pathlib import Path

    created = client.post("/api/stories/generate", json={"prompt": "a map that draws itself", "language_code": "en", "style": "Fantasy", "length_option": "Short"}).json()
    audio_id = created["audio"]["id"]
    assert client.get(f"/api/audio/{audio_id}").status_code == 200
    assert client.delete(f"/api/stories/{created['id']}").status_code == 200
    assert client.get(f"/api/audio/{audio_id}").status_code == 404
    assert client.get("/api/stories").json() == []


def test_meta_and_unknown_api_path(client):
    meta = client.get("/api/meta").json()
    assert "Bedtime" in meta["styles"] and meta["lengths"] == ["Short", "Medium", "Long"]
    assert client.get("/api/nothing-here").status_code == 404


def test_evaluation_rejects_unknown_language(client):
    assert client.post("/api/evaluations/run", json={"samples": 1, "language_code": "xx"}).status_code == 422
    assert client.post("/api/evaluations/run", json={"samples": 0}).status_code == 422
