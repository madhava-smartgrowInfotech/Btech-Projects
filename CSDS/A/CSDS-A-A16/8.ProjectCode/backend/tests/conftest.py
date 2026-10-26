import io
import pickle
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data" / "test.pt"


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 't.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def _db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


def _png(arr) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(scope="session")
def face_png() -> bytes:
    """A real FER2013 test face, upscaled 3x so the Haar detector can find it."""
    if not DATA.exists():
        pytest.skip("FER2013 test pickle not present")
    items = pickle.load(DATA.open("rb"))
    from app.ml.face import detect_largest_face
    for ex in items[:300]:
        g = np.array(Image.open(io.BytesIO(ex["img_bytes"])).convert("L"))
        g = cv2.resize(g, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        if detect_largest_face(cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)) is not None:
            return _png(g)
    pytest.skip("no detectable face in sample")


@pytest.fixture(scope="session")
def blank_png() -> bytes:
    return _png(np.full((200, 200, 3), 127, np.uint8))
