"""Fixed emotion taxonomy shared by training and inference. Keys/order must match API_CONTRACT.md."""

BASIC_EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]

# Du, Tao & Martinez compound facial-expression taxonomy: each compound label is
# composed of two basic emotions that co-occur in the expression.
COMPOUND_EMOTIONS = [
    "happily_surprised",
    "happily_disgusted",
    "sadly_fearful",
    "sadly_angry",
    "sadly_surprised",
    "sadly_disgusted",
    "fearfully_angry",
    "fearfully_surprised",
    "angrily_surprised",
    "angrily_disgusted",
    "disgustedly_surprised",
]

COMPOUND_COMPONENTS = {
    "happily_surprised": ("happy", "surprise"),
    "happily_disgusted": ("happy", "disgust"),
    "sadly_fearful": ("sad", "fear"),
    "sadly_angry": ("sad", "angry"),
    "sadly_surprised": ("sad", "surprise"),
    "sadly_disgusted": ("sad", "disgust"),
    "fearfully_angry": ("fear", "angry"),
    "fearfully_surprised": ("fear", "surprise"),
    "angrily_surprised": ("angry", "surprise"),
    "angrily_disgusted": ("angry", "disgust"),
    "disgustedly_surprised": ("disgust", "surprise"),
}

ALL_LABELS = BASIC_EMOTIONS + COMPOUND_EMOTIONS  # 18 total, fixed order = model output order
NUM_BASIC = len(BASIC_EMOTIONS)
NUM_COMPOUND = len(COMPOUND_EMOTIONS)
NUM_LABELS = len(ALL_LABELS)

BASIC_INDEX = {name: i for i, name in enumerate(BASIC_EMOTIONS)}
COMPOUND_INDEX = {name: NUM_BASIC + i for i, name in enumerate(COMPOUND_EMOTIONS)}
LABEL_INDEX = {name: i for i, name in enumerate(ALL_LABELS)}


def display_label(key: str) -> str:
    return key.replace("_", " ").title()


def basic_index_of(key: str) -> int:
    return BASIC_INDEX[key]
