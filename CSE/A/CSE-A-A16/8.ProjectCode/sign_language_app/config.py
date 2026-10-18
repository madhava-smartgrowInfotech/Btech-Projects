"""Central configuration for the Sign Language Recognition System."""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODELS_DIR / "asl_cnn_model.keras"
LABELS_PATH = MODELS_DIR / "labels.json"
HISTORY_PATH = MODELS_DIR / "training_history.json"
REPORT_PATH = MODELS_DIR / "classification_report.txt"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Classes (matches the folder layout of the public Kaggle "ASL Alphabet"
# dataset, so an externally downloaded dataset can be dropped into DATA_DIR
# without renaming anything)
# ---------------------------------------------------------------------------
LETTER_CLASSES = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
CONTROL_CLASSES = ["space", "del", "nothing"]
CLASSES = LETTER_CLASSES + CONTROL_CLASSES

# ---------------------------------------------------------------------------
# Image / preprocessing parameters
# ---------------------------------------------------------------------------
ROI_BOX_SIZE = 300          # size (px) of the square region-of-interest box
RAW_SAVE_SIZE = 200         # size raw collected images are saved at (color)
IMG_SIZE = 64                # size fed into the CNN (IMG_SIZE x IMG_SIZE)
MODEL_CHANNELS = 1           # grayscale / segmented mask input

# Segmentation mode used by preprocessing.segment_hand():
#   "threshold" -> grayscale + blur + Otsu binary threshold (default, matches
#                  the abstract's literal preprocessing order)
#   "skin"      -> YCrCb skin-color mask (more robust to cluttered backgrounds)
SEGMENTATION_MODE = "threshold"

# ---------------------------------------------------------------------------
# Webcam
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0
FRAME_WIDTH = 960
FRAME_HEIGHT = 540

# ---------------------------------------------------------------------------
# Recognition smoothing
# ---------------------------------------------------------------------------
PREDICTION_HISTORY_LEN = 15   # frames used for majority-vote smoothing
STABLE_FRAMES_TO_COMMIT = 18  # consecutive stable frames before auto-typing
CONFIDENCE_THRESHOLD = 0.75    # minimum softmax confidence to accept a prediction

# ---------------------------------------------------------------------------
# Training defaults
# ---------------------------------------------------------------------------
DEFAULT_EPOCHS = 25
DEFAULT_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 1e-3
VALIDATION_SPLIT = 0.15
TEST_SPLIT = 0.15
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Data collection defaults
# ---------------------------------------------------------------------------
CAPTURE_DELAY_MS = 60   # delay between burst-captured frames
