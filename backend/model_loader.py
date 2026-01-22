# model_loader.py
# Centralized singleton providers for models (Embedding + Groq)

import os
from sentence_transformers import SentenceTransformer
from groq import Groq


# -------------------------
# GROQ CLIENT (SINGLETON)
# -------------------------

_groq_api_key = os.getenv("GROQ_API_KEY")
if not _groq_api_key:
    raise EnvironmentError("CRITICAL: GROQ_API_KEY missing from environment")

groq_client = Groq(api_key=_groq_api_key)


# -------------------------
# EMBEDDING PROVIDER
# -------------------------

class EmbeddingProvider:
    """
    Singleton embedding model loader.
    Prevents multiple heavy model loads.
    """
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self):
        if self._model is None:
            print("🧠 LOADING EMBEDDING MODEL (SINGLETON): all-MiniLM-L6-v2 ...")
            self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            print("✅ EMBEDDING MODEL READY (384-dim vectors).")
        return self._model

    def embed(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()


# Export singleton instance
embedding_provider = EmbeddingProvider()
