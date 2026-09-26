"""
Random live facial challenge verified with MediaPipe Face Mesh landmarks.

The student is asked to perform a random action (turn head left, open mouth, ...).
We capture a *neutral* frame and a *challenge* frame and compare head-pose /
expression metrics derived from the 468 face-mesh landmarks. A printed photo
or a replayed video cannot respond to a challenge chosen at random a moment
earlier, which is what makes this a liveness check.

Supports both MediaPipe APIs:
  * legacy  `mp.solutions.face_mesh`  (mediapipe <= 0.10.21, model bundled)
  * tasks   `FaceLandmarker`          (mediapipe >= 0.10.30, needs a .task model
                                       file - see README)
"""
from __future__ import annotations

import math
import os
import random
import threading
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

import config

# ---- MediaPipe Face Mesh landmark indices ---------------------------------- #
NOSE_TIP = 1
CHIN = 152
FOREHEAD = 10
FACE_LEFT = 234    # image-left cheek edge
FACE_RIGHT = 454   # image-right cheek edge
L_EYE_OUTER, L_EYE_INNER, L_EYE_TOP, L_EYE_BOTTOM = 33, 133, 159, 145
R_EYE_OUTER, R_EYE_INNER, R_EYE_TOP, R_EYE_BOTTOM = 263, 362, 386, 374
MOUTH_LEFT, MOUTH_RIGHT, LIP_TOP, LIP_BOTTOM = 61, 291, 13, 14

CHALLENGES = {
    "TURN_LEFT": ("Turn your head to your LEFT", "⬅️"),
    "TURN_RIGHT": ("Turn your head to your RIGHT", "➡️"),
    "LOOK_UP": ("Tilt your face UP (look at the ceiling)", "⬆️"),
    "LOOK_DOWN": ("Tilt your face DOWN (look at the floor)", "⬇️"),
    "TILT_LEFT": ("Tilt your head sideways to your LEFT shoulder", "↙️"),
    "TILT_RIGHT": ("Tilt your head sideways to your RIGHT shoulder", "↘️"),
    "OPEN_MOUTH": ("Open your mouth wide", "😮"),
    "CLOSE_EYES": ("Close both eyes", "😌"),
}


def random_challenge(rng: random.Random | None = None) -> str:
    return (rng or random).choice(list(CHALLENGES))


def describe(challenge: str) -> tuple[str, str]:
    return CHALLENGES[challenge]


# ---- Face metrics ----------------------------------------------------------- #
@dataclass
class FaceMetrics:
    n_faces: int
    yaw: float = 0.0        # -0.5 .. 0.5   (nose position between cheeks)
    pitch: float = 0.0      # ~0.3 .. 0.7   (nose position between eyes and chin)
    roll_deg: float = 0.0   # eye-line angle in degrees
    mar: float = 0.0        # mouth aspect ratio
    ear: float = 0.0        # eye aspect ratio (mean of both eyes)
    bbox: tuple[int, int, int, int] | None = None  # x, y, w, h in pixels

    @property
    def ok(self) -> bool:
        return self.n_faces == 1


def _dist(a, b) -> float:
    return float(math.hypot(a[0] - b[0], a[1] - b[1]))


def metrics_from_landmarks(pts: np.ndarray, n_faces: int = 1) -> FaceMetrics:
    """
    Compute pose/expression metrics from an (N, 2) array of normalised landmark
    coordinates (x, y in 0..1). Pure numpy so it is unit-testable without MediaPipe.
    """
    nose, chin = pts[NOSE_TIP], pts[CHIN]
    fl, fr = pts[FACE_LEFT], pts[FACE_RIGHT]
    x_left, x_right = min(fl[0], fr[0]), max(fl[0], fr[0])
    yaw = (nose[0] - x_left) / max(x_right - x_left, 1e-6) - 0.5

    l_eye_c = (pts[L_EYE_OUTER] + pts[L_EYE_INNER]) / 2
    r_eye_c = (pts[R_EYE_OUTER] + pts[R_EYE_INNER]) / 2
    eyes_mid = (l_eye_c + r_eye_c) / 2
    pitch = (nose[1] - eyes_mid[1]) / max(chin[1] - eyes_mid[1], 1e-6)

    # image-left eye -> image-right eye angle
    left_eye, right_eye = (l_eye_c, r_eye_c) if l_eye_c[0] < r_eye_c[0] else (r_eye_c, l_eye_c)
    roll_deg = math.degrees(math.atan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]))

    mar = _dist(pts[LIP_TOP], pts[LIP_BOTTOM]) / max(_dist(pts[MOUTH_LEFT], pts[MOUTH_RIGHT]), 1e-6)

    ear_l = _dist(pts[L_EYE_TOP], pts[L_EYE_BOTTOM]) / max(_dist(pts[L_EYE_OUTER], pts[L_EYE_INNER]), 1e-6)
    ear_r = _dist(pts[R_EYE_TOP], pts[R_EYE_BOTTOM]) / max(_dist(pts[R_EYE_OUTER], pts[R_EYE_INNER]), 1e-6)
    ear = (ear_l + ear_r) / 2

    return FaceMetrics(n_faces=n_faces, yaw=float(yaw), pitch=float(pitch), roll_deg=float(roll_deg),
                       mar=float(mar), ear=float(ear))


# ---- Landmark detector (lazy singleton) ------------------------------------ #
class _LandmarkDetector:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._legacy = None
        self._tasks = None
        self.backend = "none"
        self._init()

    def _init(self) -> None:
        import mediapipe as mp

        if hasattr(mp, "solutions"):
            self._legacy = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True, max_num_faces=3, refine_landmarks=True,
                min_detection_confidence=0.5,
            )
            self.backend = "mediapipe.solutions.face_mesh"
            return

        # Newer MediaPipe: Tasks API needs a model file.
        model_path = os.getenv("AM_FACE_LANDMARKER_MODEL", str(Path(config.BASE_DIR) / "assets" / "face_landmarker.task"))
        if not Path(model_path).exists():
            raise RuntimeError(
                "MediaPipe 'solutions' API not available and no FaceLandmarker model found. "
                "Either `pip install mediapipe==0.10.21` or download face_landmarker.task "
                f"to {model_path} (see README)."
            )
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        opts = vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.IMAGE, num_faces=3,
        )
        self._tasks = vision.FaceLandmarker.create_from_options(opts)
        self._mp = mp
        self.backend = "mediapipe.tasks.FaceLandmarker"

    def detect(self, image_bgr: np.ndarray) -> list[np.ndarray]:
        """Return a list of (N, 2) normalised landmark arrays, one per detected face."""
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        with self._lock:
            if self._legacy is not None:
                res = self._legacy.process(rgb)
                faces = res.multi_face_landmarks or []
                return [np.array([[lm.x, lm.y] for lm in f.landmark], dtype=np.float32) for f in faces]
            mp_img = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
            res = self._tasks.detect(mp_img)
            return [np.array([[lm.x, lm.y] for lm in f], dtype=np.float32) for f in res.face_landmarks]


_detector: _LandmarkDetector | None = None
_detector_lock = threading.Lock()


def get_detector() -> _LandmarkDetector:
    global _detector
    with _detector_lock:
        if _detector is None:
            _detector = _LandmarkDetector()
    return _detector


def analyze(image_bgr: np.ndarray) -> FaceMetrics:
    """Detect faces and compute metrics for the (single) detected face."""
    faces = get_detector().detect(image_bgr)
    if len(faces) != 1:
        return FaceMetrics(n_faces=len(faces))
    pts = faces[0]
    m = metrics_from_landmarks(pts, n_faces=1)
    h, w = image_bgr.shape[:2]
    xs, ys = pts[:, 0] * w, pts[:, 1] * h
    m.bbox = (int(xs.min()), int(ys.min()), int(xs.max() - xs.min()), int(ys.max() - ys.min()))
    return m


# ---- Challenge verification ------------------------------------------------- #
@dataclass
class LivenessResult:
    passed: bool
    score: float
    reason: str
    neutral: FaceMetrics | None = None
    challenge: FaceMetrics | None = None


def check_neutral(m: FaceMetrics) -> str | None:
    """Return an error message if the neutral frame is not a usable frontal face."""
    if m.n_faces == 0:
        return "No face detected. Make sure your face is well lit and fully inside the frame."
    if m.n_faces > 1:
        return f"{m.n_faces} faces detected. Only one person may be in the frame."
    if abs(m.yaw) > config.NEUTRAL_MAX_YAW:
        return "Please look straight at the camera for the first photo."
    if m.mar > config.NEUTRAL_MAX_MAR:
        return "Please keep your mouth closed for the first photo."
    return None


def verify_challenge(challenge: str, neutral: FaceMetrics, chal: FaceMetrics) -> LivenessResult:
    """Compare the challenge frame against the neutral frame for the requested action."""
    if err := check_neutral(neutral):
        return LivenessResult(False, 0.0, f"Neutral photo problem: {err}", neutral, chal)
    if chal.n_faces == 0:
        return LivenessResult(False, 0.0, "No face detected in the challenge photo.", neutral, chal)
    if chal.n_faces > 1:
        return LivenessResult(False, 0.0, "More than one face in the challenge photo.", neutral, chal)

    # In a mirrored (selfie) image the student's left is the image's left, so a
    # LEFT turn moves the nose to smaller x (negative yaw). Non-mirrored flips it.
    direction = -1.0 if config.CAMERA_MIRRORED else 1.0

    d_yaw = chal.yaw - neutral.yaw
    d_pitch = chal.pitch - neutral.pitch
    d_roll = chal.roll_deg - neutral.roll_deg

    def result(measured: float, threshold: float, label: str) -> LivenessResult:
        measured = float(measured)
        score = max(0.0, min(1.0, measured / threshold)) if threshold > 0 else 0.0
        passed = bool(measured >= threshold)
        reason = (f"{label}: measured {measured:.3f}, required {threshold:.3f} — "
                  + ("PASS" if passed else "not enough movement, try a bigger motion"))
        return LivenessResult(passed, round(score, 3), reason, neutral, chal)

    if challenge == "TURN_LEFT":
        return result(direction * d_yaw, config.LIVENESS_YAW_DELTA, "Head turn left")
    if challenge == "TURN_RIGHT":
        return result(-direction * d_yaw, config.LIVENESS_YAW_DELTA, "Head turn right")
    if challenge == "LOOK_UP":
        return result(-d_pitch, config.LIVENESS_PITCH_DELTA, "Look up")
    if challenge == "LOOK_DOWN":
        return result(d_pitch, config.LIVENESS_PITCH_DELTA, "Look down")
    if challenge == "TILT_LEFT":
        return result(direction * d_roll, config.LIVENESS_ROLL_DEG, "Tilt left")
    if challenge == "TILT_RIGHT":
        return result(-direction * d_roll, config.LIVENESS_ROLL_DEG, "Tilt right")
    if challenge == "OPEN_MOUTH":
        return result(chal.mar, config.LIVENESS_MOUTH_OPEN_MAR, "Mouth open ratio")
    if challenge == "CLOSE_EYES":
        # Lower EAR = more closed. Score by how far below the threshold we are.
        measured = config.LIVENESS_EYES_CLOSED_EAR - chal.ear + config.LIVENESS_EYES_CLOSED_EAR
        r = result(measured, config.LIVENESS_EYES_CLOSED_EAR, "Eyes closed")
        r.reason = (f"Eyes closed: eye-aspect-ratio {chal.ear:.3f}, must be below "
                    f"{config.LIVENESS_EYES_CLOSED_EAR:.3f} — " + ("PASS" if r.passed else "eyes still open"))
        return r
    return LivenessResult(False, 0.0, f"Unknown challenge {challenge}", neutral, chal)


# ---- Image helpers ---------------------------------------------------------- #
def decode_image(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image.")
    # keep inference fast on phone photos
    h, w = img.shape[:2]
    if max(h, w) > 1280:
        scale = 1280 / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img
