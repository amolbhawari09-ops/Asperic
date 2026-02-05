"""
Asperic Self-Check Module (v1.0)
--------------------------------
Purpose:
- Detect semantic drift between user input and AI output
- Reduce hallucination and off-topic verbosity
- Allow ONE corrective retry only

This module NEVER decides policy or depth.
"""

from typing import Optional
from model_loader import embedding_provider
import math


class SelfCheck:
    """
    Semantic self-check and correction engine.
    """

    VERSION = "v1.0-drift-control"

    # Conservative threshold
    MIN_SIMILARITY = 0.55

    def __init__(self):
        self.embedder = embedding_provider

    # =========================
    # PUBLIC ENTRY
    # =========================
    def validate(
        self,
        question: str,
        answer: str,
        retry_callback: Optional[callable] = None
    ) -> str:
        """
        Validate semantic alignment between question and answer.

        If similarity is too low:
        - Call retry_callback ONCE to regenerate a simpler answer
        - Otherwise return original answer

        retry_callback MUST be a callable that returns a string.
        """

        try:
            similarity = self._semantic_similarity(question, answer)

            if similarity < self.MIN_SIMILARITY and retry_callback:
                # One controlled retry
                return retry_callback()

            return answer

        except Exception:
            # Absolute safety: never block output
            return answer

    # =========================
    # INTERNAL
    # =========================
    def _semantic_similarity(self, t1: str, t2: str) -> float:
        v1 = self.embedder.embed(t1)
        v2 = self.embedder.embed(t2)

        return self._cosine_similarity(v1, v2)

    def _cosine_similarity(self, v1, v2) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        return dot / (norm1 * norm2 + 1e-8)