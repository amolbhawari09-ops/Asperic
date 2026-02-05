import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ReasoningDecision:
    """
    Immutable reasoning depth decision.
    """
    depth: str                 # NONE | LIGHT | STRUCTURED | RIGOROUS
    confidence: float          # 0.0 – 1.0
    signals: List[str]
    controller_version: str


class ReasoningController:
    """
    Asperic Semantic Reasoning Controller (v2.0)
    --------------------------------------------
    PURPOSE (UPDATED):
    - Decide reasoning depth from SEMANTIC STATE
    - Never rely on keywords
    - Never hallucinate certainty
    - Fail safely if semantic data missing
    """

    VERSION = "v2.0-semantic-depth"

    DEPTHS = {"NONE", "LIGHT", "STRUCTURED", "RIGOROUS"}

    # -------------------------
    # INIT
    # -------------------------
    def __init__(self):
        pass  # No API calls needed here anymore

    # -------------------------
    # PUBLIC ENTRY
    # -------------------------
    def decide(
        self,
        query: str,
        semantic_profile: Optional[Dict[str, float]] = None
    ) -> ReasoningDecision:
        """
        Decide reasoning depth based on semantic profile.

        semantic_profile expected keys (0.0–1.0):
        - confusion
        - decision_intent
        - technicality
        - novelty
        """

        signals: List[str] = []

        # ---------- FAIL SAFE ----------
        if not semantic_profile or not isinstance(semantic_profile, dict):
            return self._decision(
                depth="LIGHT",
                confidence=0.4,
                signals=["fallback:no_semantic_profile"]
            )

        # ---------- EXTRACT SIGNALS ----------
        confusion = float(semantic_profile.get("confusion", 0.0))
        decision_intent = float(semantic_profile.get("decision_intent", 0.0))
        technicality = float(semantic_profile.get("technicality", 0.0))
        novelty = float(semantic_profile.get("novelty", 0.0))

        # ---------- SEMANTIC INTERPRETATION ----------
        if confusion > 0.75:
            signals.append("semantic:high_confusion")

        if decision_intent > 0.65:
            signals.append("semantic:decision_intent")

        if technicality > 0.7:
            signals.append("semantic:high_technicality")

        if novelty > 0.6:
            signals.append("semantic:novel_query")

        # ---------- DEPTH LOGIC (CORE INTELLIGENCE) ----------
        # 1. Confused users should NOT get deep reasoning
        if confusion > 0.75:
            depth = "LIGHT"

        # 2. Decision-making requires rigor
        elif decision_intent > 0.65:
            depth = "RIGOROUS"

        # 3. Novel but understandable topics benefit from structure
        elif novelty > 0.6 and confusion < 0.4:
            depth = "STRUCTURED"

        # 4. Low signal = trivial
        elif max(confusion, decision_intent, novelty, technicality) < 0.25:
            depth = "NONE"

        # 5. Default safe behavior
        else:
            depth = "LIGHT"

        confidence = self._confidence_from_signals(
            confusion, decision_intent, novelty
        )

        return self._decision(
            depth=depth,
            confidence=confidence,
            signals=signals
        )

    # -------------------------
    # INTERNAL
    # -------------------------
    def _confidence_from_signals(
        self,
        confusion: float,
        decision_intent: float,
        novelty: float
    ) -> float:
        """
        Confidence reflects signal clarity, NOT correctness.
        """
        clarity = max(decision_intent, novelty, confusion)
        return round(min(1.0, max(0.4, clarity)), 2)

    def _decision(
        self,
        depth: str,
        confidence: float,
        signals: List[str]
    ) -> ReasoningDecision:
        if depth not in self.DEPTHS:
            depth = "LIGHT"

        return ReasoningDecision(
            depth=depth,
            confidence=confidence,
            signals=signals,
            controller_version=self.VERSION
        )