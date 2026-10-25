import random
import re

from utils.quiz_generator import generate_quiz
from utils.text_extraction import chunk_text, clean_text


def sample_chunks():
    return chunk_text(clean_text(open("sample_data/sample_notes_data_structures.txt", encoding="utf-8").read()))


def test_quiz_has_requested_number_and_valid_structure():
    random.seed(1)
    qs = generate_quiz(sample_chunks(), num_questions=5, subject="DS")
    assert len(qs) == 5
    for q in qs:
        assert q["question"].startswith("Fill in the blank:") and "_____" in q["question"]
        assert len(q["options"]) == 4 and len(set(q["options"])) == 4
        assert q["options"][q["answer_index"]] == q["topic"] and q["subject"] == "DS"


def test_blanked_term_no_longer_in_the_stem():
    random.seed(2)
    for q in generate_quiz(sample_chunks(), num_questions=5):
        stem = q["question"].split("blank:", 1)[1]
        # only the first occurrence is blanked; the stem must contain the blank itself
        assert "_____" in stem
        assert not re.match(r"\s*" + re.escape(q["topic"]) + r"\b", stem, re.I)


def test_too_little_text_returns_empty():
    assert generate_quiz(["short text"], num_questions=5) == []
    assert generate_quiz([], num_questions=5) == []


def test_terms_are_not_reused_within_one_quiz():
    random.seed(3)
    qs = generate_quiz(sample_chunks(), num_questions=5)
    assert len({q["topic"] for q in qs}) == len(qs)
