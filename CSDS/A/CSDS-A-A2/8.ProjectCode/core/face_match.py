"""
Face identity + duplicate-face checks using InsightFace (ArcFace embeddings).

* `embed()`         -> 512-d L2-normalised embedding of the single face in a frame
* identity check    -> live capture vs. the student's enrolled reference face
* duplicate check   -> live capture vs. every face already recorded in the session
                       (one physical person cannot mark several roll numbers)
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field

import numpy as np

import config


# --------------------------------------------------------------------------- #
# Embedding model (lazy singleton)
# --------------------------------------------------------------------------- #
class _Embedder:
    def __init__(self) -> None:
        from insightface.app import FaceAnalysis

        self.app = FaceAnalysis(
            name=config.INSIGHTFACE_MODEL,
            allowed_modules=["detection", "recognition"],
            providers=["CPUExecutionProvider"],
        )
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        self._lock = threading.Lock()

    def faces(self, image_bgr: np.ndarray):
        with self._lock:
            return self.app.get(image_bgr)


_embedder: _Embedder | None = None
_lock = threading.Lock()


def get_embedder() -> _Embedder:
    global _embedder
    with _lock:
        if _embedder is None:
            _embedder = _Embedder()
    return _embedder


# --------------------------------------------------------------------------- #
# Public helpers
# --------------------------------------------------------------------------- #
class FaceError(Exception):
    pass


def embed(image_bgr: np.ndarray) -> np.ndarray:
    """Return the normalised embedding of the single face in the image."""
    faces = get_embedder().faces(image_bgr)
    if len(faces) == 0:
        raise FaceError("No face detected for recognition. Face the camera in good light.")
    if len(faces) > 1:
        # Use the largest face only if the others are tiny background faces.
        faces = sorted(faces, key=lambda f: -(f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        w0 = faces[0].bbox[2] - faces[0].bbox[0]
        w1 = faces[1].bbox[2] - faces[1].bbox[0]
        if w1 > 0.5 * w0:
            raise FaceError("More than one face detected. Only the student may be in frame.")
    emb = faces[0].normed_embedding.astype(np.float32)
    return emb / (np.linalg.norm(emb) + 1e-9)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = a / (np.linalg.norm(a) + 1e-9)
    b = b / (np.linalg.norm(b) + 1e-9)
    return float(np.dot(a, b))


def to_bytes(emb: np.ndarray) -> bytes:
    return emb.astype(np.float32).tobytes()


def from_bytes(data: bytes) -> np.ndarray:
    return np.frombuffer(data, dtype=np.float32)


@dataclass
class MatchResult:
    passed: bool
    reason: str
    identity_similarity: float | None = None
    max_duplicate_similarity: float | None = None
    duplicate_of: str | None = None
    frame_consistency: float | None = None
    details: dict = field(default_factory=dict)


def verify_faces(
    live_embedding: np.ndarray,
    enrolled_embedding: np.ndarray | None,
    session_embeddings: list[tuple[str, np.ndarray]],
    second_frame_embedding: np.ndarray | None = None,
) -> MatchResult:
    """
    1. Both captured frames must be the same person (no swapping people mid-check).
    2. Live face must match the enrolled reference face (identity).
    3. Live face must NOT match any face already recorded in this session under
       another roll number (duplicate / proxy check).
    """
    consistency = None
    if second_frame_embedding is not None:
        consistency = cosine(live_embedding, second_frame_embedding)
        if consistency < config.FRAME_CONSISTENCY_THRESHOLD:
            return MatchResult(
                False,
                f"The two photos appear to be different people (similarity {consistency:.2f}).",
                frame_consistency=consistency,
            )

    identity = None
    if enrolled_embedding is not None:
        identity = cosine(live_embedding, enrolled_embedding)
        if identity < config.IDENTITY_THRESHOLD:
            return MatchResult(
                False,
                f"Face does not match the enrolled reference face for this roll number "
                f"(similarity {identity:.2f}, required ≥ {config.IDENTITY_THRESHOLD:.2f}).",
                identity_similarity=identity,
                frame_consistency=consistency,
            )
    elif config.REQUIRE_ENROLLMENT:
        return MatchResult(False, "No enrolled reference face. Please enrol your face first.",
                           frame_consistency=consistency)

    max_dup, dup_of = 0.0, None
    for roll, emb in session_embeddings:
        s = cosine(live_embedding, emb)
        if s > max_dup:
            max_dup, dup_of = s, roll
    if dup_of is not None and max_dup >= config.DUPLICATE_THRESHOLD:
        return MatchResult(
            False,
            f"This face has already marked attendance in this session as {dup_of} "
            f"(similarity {max_dup:.2f}). Proxy attendance blocked.",
            identity_similarity=identity,
            max_duplicate_similarity=max_dup,
            duplicate_of=dup_of,
            frame_consistency=consistency,
        )

    return MatchResult(
        True,
        "Face verified: identity matched and no duplicate in this session.",
        identity_similarity=identity,
        max_duplicate_similarity=max_dup if session_embeddings else None,
        frame_consistency=consistency,
    )
