import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_normalize_and_expand():
    from app.rag.query_expansion import expand_query_hyde
    r = expand_query_hyde("I have high fever, headache and body pain")
    assert "fever" in r["normalized"]
    assert "Medical symptom presentation" in r["hypothetical"]

def test_safety_emergency():
    from app.rag.safety import check_safety
    assert check_safety("severe chest pain and difficulty breathing")["flag"] == "emergency"
    assert check_safety("I have a mild headache")["flag"] in ("routine", "caution")

def test_safety_filter_removes_dosage():
    from app.rag.safety import apply_safety_filter
    assert "removed" in apply_safety_filter("take antibiotics daily")

def test_password_hashing():
    from app.auth import hash_password, verify_password
    h = hash_password("Secret123")
    assert h != "Secret123" and verify_password("Secret123", h) and not verify_password("x", h)

def test_hybrid_fuse():
    from app.rag.hybrid_retriever import fuse
    rec = {"retrieval_text": "x"}
    fused = fuse([(0.9, rec, 0), (0.1, {"retrieval_text": "y"}, 1)], [(0.2, rec, 0)], k=2)
    assert fused[0]["idx"] == 0

def test_generator_fallback():
    from app.rag.generator import Generator
    g = Generator.__new__(Generator)
    g.available = False; g.pipe = None
    ans = g.fallback_answer("fever", [{"record": {"disease": "Influenza", "symptoms": "fever", "guidance": "Rest."}}])
    assert "not a diagnosis" in ans.lower()

def test_auth_and_history_isolation():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import init_db
    init_db()
    with TestClient(app) as c:
        import uuid
        e1, e2 = f"a{uuid.uuid4().hex[:8]}@x.com", f"b{uuid.uuid4().hex[:8]}@x.com"
        c.post("/api/auth/register", json={"email": e1, "password": "Password1"})
        r = c.post("/api/chat", json={"query": "I have fever and cough"})
        assert r.status_code == 200, r.text
        cid = r.json()["consultation_id"]
        c.post("/api/auth/logout")
        c.post("/api/auth/register", json={"email": e2, "password": "Password1"})
        assert c.get(f"/api/history/{cid}").status_code == 404

def test_api_validation():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import init_db
    init_db()
    with TestClient(app) as c:
        import uuid as _uuid
        c.post("/api/auth/register", json={"email": f"v{_uuid.uuid4().hex[:8]}@example.com", "password": "Password1"})
        assert c.post("/api/chat", json={"query": "hi"}).status_code in (400, 422)
        assert c.post("/api/chat", json={"query": "x" * 5000}).status_code in (400, 422)

def test_retrieval_roundtrip():
    from app.rag.pipeline import get_pipeline
    pipe = get_pipeline()
    res = pipe.answer("high fever, headache and body pain", top_k=3)
    assert len(res["evidence"]) > 0 and res["top_condition"]
