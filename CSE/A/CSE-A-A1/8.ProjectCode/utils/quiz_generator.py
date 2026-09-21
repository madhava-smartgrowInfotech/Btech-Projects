"""
Generates simple multiple-choice quiz questions automatically from a
document's chunks, using key-term blanking. No external model needed.
"""
import random
import re
from sklearn.feature_extraction.text import TfidfVectorizer


def _candidate_terms(text, top_n=25):
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            token_pattern=r"(?u)\b[A-Za-z][A-Za-z\-]{3,}\b",
            max_features=200,
        )
        mat = vectorizer.fit_transform([text])
        scores = mat.toarray()[0]
        terms = vectorizer.get_feature_names_out()
        ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
        return [t for t, s in ranked[:top_n] if s > 0]
    except ValueError:
        return []


def generate_quiz(chunks, num_questions=5, subject="General"):
    """
    chunks: list of raw text chunks (strings) from one or more documents.
    Returns a list of question dicts:
      {question, options: [...], answer_index, topic}
    """
    full_text = " ".join(chunks)
    terms = _candidate_terms(full_text, top_n=40)
    if len(terms) < 4:
        return []

    sentences = []
    for chunk in chunks:
        for s in re.split(r"(?<=[.!?])\s+", chunk):
            s = s.strip()
            if 25 < len(s) < 220:
                sentences.append(s)

    random.shuffle(sentences)
    questions = []
    used_terms = set()

    for sentence in sentences:
        if len(questions) >= num_questions:
            break
        lower_sentence = sentence.lower()
        found_term = None
        for term in terms:
            if term in used_terms:
                continue
            # match whole word/phrase, case-insensitive
            pattern = r"\b" + re.escape(term) + r"\b"
            if re.search(pattern, lower_sentence):
                found_term = term
                break
        if not found_term:
            continue

        used_terms.add(found_term)
        pattern = re.compile(re.escape(found_term), re.IGNORECASE)
        blanked = pattern.sub("_____", sentence, count=1)

        distractors = [t for t in terms if t != found_term]
        random.shuffle(distractors)
        options = [found_term] + distractors[:3]
        while len(options) < 4:
            options.append("none of the above")
        random.shuffle(options)
        answer_index = options.index(found_term)

        questions.append({
            "question": f"Fill in the blank: {blanked}",
            "options": options,
            "answer_index": answer_index,
            "topic": found_term,
            "subject": subject,
        })

    return questions
