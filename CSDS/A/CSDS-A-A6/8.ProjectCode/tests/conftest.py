"""Shared fixtures. No test calls the Gemini API: embeddings and generated text are replaced by
deterministic stubs, and every API test runs against a throw-away SQLite database."""
from __future__ import annotations

import hashlib
import sys
import uuid
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

DIM = 24


def fake_embedding(text: str) -> list[float]:
    """Deterministic pseudo-embedding: the same text always gives the same vector."""
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
    return np.random.default_rng(seed).normal(size=DIM).astype("float32").tolist()


SAMPLE_CONTRACT = """FREELANCE SERVICES AGREEMENT

1. Scope of Services
The Consultant shall provide software development services to the Company as described in Schedule A.

2. Term and Termination
The Company may terminate this Agreement at any time, without cause or notice, at its sole discretion, and the Consultant shall have no right to object or claim compensation for unfinished work.

3. Fees and Refunds
The Company shall pay the Consultant a monthly fee of Rs. 60,000. All payments made under this Agreement are non-refundable under any circumstances, including early termination by the Company.

4. Penalty for Delay
If the Consultant delays delivery of any milestone, the Consultant shall pay a penalty of Rs. 25,000 per day of delay, irrespective of the actual loss suffered by the Company.

5. Governing Law
This Agreement shall be governed by and construed in accordance with the laws of India, and the courts at Bengaluru shall have exclusive jurisdiction.
"""


@pytest.fixture()
def docx_bytes():
    import io

    from docx import Document

    def build(text: str = SAMPLE_CONTRACT) -> bytes:
        doc = Document()
        for line in text.split("\n"):
            doc.add_paragraph(line)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    return build


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """FastAPI TestClient on a fresh SQLite file with Gemini replaced by stubs."""
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app import db as app_db
    from app.main import app
    from app.routes import contracts as contracts_routes
    from app.services import classification, gemini_client

    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    app_db.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[app_db.get_session] = override
    monkeypatch.setattr(contracts_routes, "gemini_configured", lambda: True)
    monkeypatch.setattr(contracts_routes, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(gemini_client, "embed_text", lambda text, task_type="RETRIEVAL_DOCUMENT": fake_embedding(text))

    def fake_json(prompt, retries=3):
        if "plain_summary" in prompt:
            return {"plain_summary": "A freelance agreement with one-sided terms.", "key_obligations": ["Deliver the milestones", "Keep information confidential"]}
        return {"reason": "This clause favours the other party.", "provision": "at any time", "safer_wording": "Either party may terminate on 30 days' notice."}

    monkeypatch.setattr(gemini_client, "generate_json", fake_json)
    rng = np.random.default_rng(0)
    cats = ["Governing Law", "Termination For Convenience", "Liquidated Damages", "Other Category"]
    monkeypatch.setattr(classification, "_CENTROIDS_CACHE", (cats, rng.normal(size=(len(cats), DIM)).astype("float32")))
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth(client):
    """Registers a fresh user and returns (headers, email)."""
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "secret-pass-1"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}, email
