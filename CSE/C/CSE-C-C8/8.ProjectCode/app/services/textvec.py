"""PeerScope combined TF-IDF vectorizer (importable so joblib pickles resolve)."""
from __future__ import annotations


class CombinedVectorizer:
    def __init__(self, w, c):
        self.w, self.c = w, c

    def transform(self, texts):
        from scipy.sparse import hstack as _h

        return _h([self.w.transform(texts), self.c.transform(texts)])
