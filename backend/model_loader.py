# model_loader.py — SINGLETON EMBEDDING PROVIDER
# Ensures the SentenceTransformer model is loaded ONLY ONCE across the entire application.

from sentence_transformers import SentenceTransformer

class EmbeddingProvider:
    """
    Singleton pattern for embedding model.
    Prevents multiple 90MB model loads that cause slow startup and memory bloat.
    """
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingProvider, cls).__new__(cls)
        return cls._instance

    @property
    def model(self):
        """Lazy load: model is loaded on first access, not import."""
        if self._model is None:
            print("🧠 LOADING EMBEDDING MODEL (SINGLETON): all-MiniLM-L6-v2 ...")
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            print("✅ EMBEDDING MODEL READY (384-dim vectors).")
        return self._model

    def embed(self, text: str) -> list[float]:
        """Generate 384-dimension embedding vector."""
        return self.model.encode(text).tolist()


# Export singleton instance for use across the application
embedding_provider = EmbeddingProvider()
