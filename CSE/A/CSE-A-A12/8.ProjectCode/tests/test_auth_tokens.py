"""Unit tests for the signed session cookie used by the demo login."""

import base64
import json
import time

from backend import main as m


def test_token_round_trip():
    data = m.read_token(m.make_token("demo@pneumodetect.ai"))
    assert data["e"] == "demo@pneumodetect.ai"


def test_tampered_payload_is_rejected():
    body, sig = m.make_token("demo@pneumodetect.ai").rsplit(".", 1)
    forged = base64.urlsafe_b64encode(json.dumps({"e": "admin@x", "x": int(time.time()) + 999}).encode()).decode()
    assert m.read_token(f"{forged}.{sig}") is None


def test_tampered_signature_is_rejected():
    body, _ = m.make_token("demo@pneumodetect.ai").rsplit(".", 1)
    assert m.read_token(f"{body}.{'0' * 64}") is None


def test_expired_token_is_rejected():
    body = base64.urlsafe_b64encode(json.dumps({"e": "demo@pneumodetect.ai", "x": int(time.time()) - 5}).encode()).decode()
    assert m.read_token(f"{body}.{m._sign(body)}") is None


def test_empty_and_malformed_tokens():
    assert m.read_token(None) is None
    assert m.read_token("") is None
    assert m.read_token("nodot") is None
