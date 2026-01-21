from sentence_transformers import SentenceTransformer

class LocalEmbeddingProvider:
    DIM = 384

    def __init__(self):
        print("🧠 LOADING LOCAL EMBEDDING MODEL: all-MiniLM-L6-v2 ...")
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("✅ MODEL LOADED. 384-DIMENSION VECTORS READY.")

    def embed(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()
