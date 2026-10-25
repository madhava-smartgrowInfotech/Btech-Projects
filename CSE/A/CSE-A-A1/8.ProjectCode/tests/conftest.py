"""Shared fixtures. The database and the upload folder are redirected to a temporary directory BEFORE the app
modules are imported, so the suite never touches instance/app.db or uploads/."""
import os
import sys
import tempfile
import uuid

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

_TMP = tempfile.mkdtemp(prefix="alip_tests_")
from config import Config  # noqa: E402

Config.DATABASE = os.path.join(_TMP, "test.db")
Config.UPLOAD_FOLDER = os.path.join(_TMP, "uploads")
Config.ANTHROPIC_API_KEY = ""

from fastapi.testclient import TestClient  # noqa: E402
from backend.main import app as api_app  # noqa: E402

SAMPLE = os.path.join(ROOT, "sample_data", "sample_notes_data_structures.txt")


@pytest.fixture(scope="session")
def tmp_root():
    return _TMP


@pytest.fixture()
def client():
    with TestClient(api_app) as c:
        yield c


@pytest.fixture()
def user(client):
    """A freshly registered and logged-in user (unique name per test)."""
    name = "u_" + uuid.uuid4().hex[:10]
    assert client.post("/api/auth/register", json={"username": name, "password": "Pass#1234"}).status_code == 201
    r = client.post("/api/auth/login", json={"username": name, "password": "Pass#1234"})
    assert r.status_code == 200
    return {"name": name, "id": r.json()["id"], "client": client}


def upload(client, content, filename="notes.txt", subject="Data Structures"):
    return client.post("/api/documents", files={"document": (filename, content, "application/octet-stream")},
                       data={"subject": subject})


@pytest.fixture()
def sample_bytes():
    with open(SAMPLE, "rb") as f:
        return f.read()


def minimal_pdf(text):
    """Smallest valid one-page PDF carrying `text` (empty text = a page with no text layer, like a scan)."""
    stream = ("BT /F1 12 Tf 72 720 Td (%s) Tj ET" % text).encode("latin-1") if text else b""
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += ("%d 0 obj\n" % i).encode() + o + b"\nendobj\n"
    xref = len(out)
    out += ("xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)).encode()
    for off in offsets:
        out += ("%010d 00000 n \n" % off).encode()
    out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (len(objs) + 1, xref)).encode()
    return out
