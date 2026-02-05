from typing import Dict, List
from model_loader import embedding_provider
import math


class SemanticEngine:
    """
    Asperic Semantic Engine (v1.0)
    ------------------------------
    PURPOSE:
    - Convert raw text into semantic signals
    - NO policy decisions
    - NO reasoning depth decisions
    - NO LLM calls

    Output:
    {
        "confusion": float (0–1),
        "decision_intent": float (0–1),
        "technicality": float (0–1),
        "novelty": float (0–1)
    }
    """

    VERSION = "v1.0-semantic-core"

    # -------------------------
    # INIT
    # -------------------------
    def __init__(self):
        self.embedder = embedding_provider

        # ----- SEMANTIC ANCHORS -----
        self.ANCHORS = {
            "confusion": [
                "I don't understand this",
                "this is too technical",
                "I'm confused",
                "this doesn't make sense",
                "I'm lost"
            ],
            "decision_intent": [
                "should I do this",
                "which option is better",
                "what should I choose",
                "is it a good idea",
                "should I use this"
            ],
            "technicality": [
                "system architecture",
                "machine learning model",
                "deployment pipeline",
                "neural network embeddings",
                "distributed system design"
            ]
        }

        # Pre-embed anchors once
        self.anchor_vectors = {
            key: [self.embedder.embed(t) for t in texts]
            for key, texts in self.ANCHORS.items()
        }

    # =========================
    # PUBLIC ENTRY
    # =========================
    def analyze(self, text: str) -> Dict[str, float]:
        """
        Main semantic analysis entrypoint.
        """

        text_vec = self.embedder.embed(text)

        confusion = self._similarity_score(
            text_vec, self.anchor_vectors["confusion"]
        )

        decision_intent = self._similarity_score(
            text_vec, self.anchor_vectors["decision_intent"]
        )

        technicality = self._similarity_score(
            text_vec, self.anchor_vectors["technicality"]
        )

        novelty = self._novelty_score(text_vec)

        return {
            "confusion": round(confusion, 2),
            "decision_intent": round(decision_intent, 2),
            "technicality": round(technicality, 2),
            "novelty": round(novelty, 2)
        }

    # =========================
    # INTERNALS
    # =========================
    def _similarity_score(
        self,
        vector: List[float],
        anchor_vectors: List[List[float]]
    ) -> float:
        """
        Returns max cosine similarity to anchor set.
        """
        scores = [
            self._cosine_similarity(vector, a_vec)
            for a_vec in anchor_vectors
        ]
        return max(scores) if scores else 0.0

    def _novelty_score(self, vector: List[float]) -> float:
        """
        Simple novelty proxy.
        High novelty = far from all known anchors.
        """
        all_anchor_vecs = [
            v for group in self.anchor_vectors.values() for v in group
        ]

        if not all_anchor_vecs:
            return 0.5

        similarities = [
            self._cosine_similarity(vector, a_vec)
            for a_vec in all_anchor_vecs
        ]

        avg_similarity = sum(similarities) / len(similarities)

        # Novelty = inverse similarity
        return max(0.0, min(1.0, 1.0 - avg_similarity))

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        return dot / (norm1 * norm2 + 1e-8)