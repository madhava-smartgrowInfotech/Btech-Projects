import sys
from pathlib import Path

def test_health():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.get("/api/health")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"

def test_dataset():
    from app.ml.dataset import load_dataset
    df, meta = load_dataset()
    assert len(df) > 200
    assert "status" in df.columns

def test_preprocessing():
    from app.ml.dataset import load_dataset
    from app.ml.preprocessing import prepare_frame, build_preprocessor
    df_raw, _ = load_dataset()
    df = prepare_frame(df_raw.head(200))
    assert "label" in df.columns and df["label"].isin([0, 1]).all()
    pre = build_preprocessor()
    X = pre.fit_transform(df)
    assert X.shape[0] == len(df)
    # missing-value handling
    df2 = df.copy()
    df2.loc[df2.index[0], "funding_total_usd"] = None
    X2 = pre.transform(df2.head(10))
    import numpy as np
    assert not np.isnan(np.asarray(X2.todense() if hasattr(X2, "todense") else X2)).any()

def test_embeddings_and_fusion():
    from app.ml.embeddings import embed_texts, l2norm
    from app.ml.retrieval import fuse
    import numpy as np
    vecs, backend = embed_texts(["A software platform for retailers.", "A fintech app for consumers."])
    assert vecs.shape[1] == 384
    S = np.random.default_rng(0).normal(size=(2, 10))
    F = fuse(S, vecs)
    assert F.shape == (2, 394)

def test_retrieval_balanced():
    import numpy as np, pandas as pd
    from app.ml.retrieval import fuse, retrieve_similar
    rng = np.random.default_rng(1)
    Ft = rng.normal(size=(60, 20)).astype(np.float32)
    df = pd.DataFrame({"label": [1] * 30 + [0] * 30, "outcome": ["SUCCESS"] * 30 + ["FAILURE"] * 30,
                       "industry_type": "Software", "state": "CA", "funding_total_usd": 1e6,
                       "funding_rounds": 2, "relationships": 3, "milestones": 2, "description": "case"})
    out = retrieve_similar(Ft[0], Ft, df, k=10)
    assert len(out) == 10
    assert set(out["label"].tolist()) == {0, 1}
    assert (out["similarity"] <= 1.0 + 1e-6).all()

def test_predict_and_api():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    payload = {"funding_total_usd": 2000000, "funding_rounds": 2, "description": "A subscription software platform for retailers with growing revenue.", "k": 10}
    r = c.post("/predict", json=payload)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["outcome"] in ("SUCCESS", "FAILURE")
    assert len(j["similar"]) == 10
    assert all("similarity" in s for s in j["similar"])
    # invalid input
    r2 = c.post("/predict", json={"funding_total_usd": -5, "description": "", "k": 999})
    assert r2.status_code in (400, 422)

def test_pages():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    for p in ["/", "/predict", "/performance", "/insights"]:
        r = c.get(p)
        assert r.status_code == 200, p
