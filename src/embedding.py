import os
import pickle
import numpy as np
from typing import List
from langchain_core.embeddings import Embeddings
from sklearn.feature_extraction.text import TfidfVectorizer

VECTORIZER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vectorizer.pkl")


class LocalTfidfEmbeddings(Embeddings):
    """本地 TF-IDF embedding，无需外部 API"""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 4),
            max_features=1024,
            sublinear_tf=True
        )
        self._fitted = False
        self._load_vectorizer()

    def _load_vectorizer(self):
        """Load saved vectorizer if available."""
        if os.path.exists(VECTORIZER_PATH):
            try:
                with open(VECTORIZER_PATH, "rb") as f:
                    self.vectorizer = pickle.load(f)
                self._fitted = True
                print("[embedding] Loaded saved vectorizer")
            except Exception:
                pass

    def _save_vectorizer(self):
        """Save vectorizer for reuse."""
        try:
            with open(VECTORIZER_PATH, "wb") as f:
                pickle.dump(self.vectorizer, f)
        except Exception:
            pass

    def _ensure_fitted(self, texts: List[str]):
        if not self._fitted:
            self.vectorizer.fit(texts)
            self._fitted = True
            self._save_vectorizer()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self._ensure_fitted(texts)
        vectors = self.vectorizer.transform(texts).toarray()
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        if not self._fitted:
            self.vectorizer.fit([text])
            self._fitted = True
        vector = self.vectorizer.transform([text]).toarray()[0]
        return vector.tolist()


def get_embedding_function() -> LocalTfidfEmbeddings:
    return LocalTfidfEmbeddings()
