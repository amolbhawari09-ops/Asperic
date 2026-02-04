import re
import os
import json
from groq import Groq
from dataclasses import dataclass


@dataclass(frozen=True)
class ReasoningDecision:
    """
    Immutable reasoning depth decision.
    """
    depth: str                 # NONE | LIGHT | STRUCTURED | RIGOROUS
    confidence: float          # 0.0 – 1.0
    signals: list[str]
    controller_version: str


class ReasoningController:
    """
    Asperic Reasoning Depth Controller (Hardened)
    ---------------------------------------------
    Purpose:
    - Decide HOW MUCH thinking is required
    - Never crash the system
    - Degrades safely if LLM unavailable
    """

    VERSION = "v1.1-cognitive-depth"

    DEPTHS = {"NONE", "LIGHT", "STRUCTURED", "RIGOROUS"}

    # =========================
    # INIT
    # =========================
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")

        if not self.api_key:
            print("⚠️ REASONING: GROQ_API_KEY missing. LLM depth disabled.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)

        self.SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"

        # Deterministic linguistic cues
        self.RIGOROUS_TRIGGERS = [
            "should i", "decide", "architecture", "design",
            "strategy", "risk", "production", "deploy",
            "legal", "tax", "finance", "investment",
            "medical", "diagnosis"
        ]

        self.STRUCTURED_TRIGGERS = [
            "how do i", "steps", "process", "compare",
            "difference", "explain", "analyze"
        ]

    # =========================
    # PUBLIC ENTRY
    # =========================
    def decide(self, query: str) -> ReasoningDecision:
        signals = []

        # ---------- PHASE 1: FAST HEURISTICS ----------
        lowered = query.lower()

        if self._is_trivial(query):
            return self._decision(
                depth="NONE",
                confidence=0.9,
                signals=["trivial_query"]
            )

        if any(t in lowered for t in self.RIGOROUS_TRIGGERS):
            signals.append("high_stakes_language")

        if any(t in lowered for t in self.STRUCTURED_TRIGGERS):
            signals.append("procedural_language")

        # ---------- PHASE 2: LLM ASSESSMENT (OPTIONAL) ----------
        if self.client:
            llm_result = self._llm_assess_depth(query)
        else:
            llm_result = {}

        depth = llm_result.get("depth", "LIGHT")
        confidence = llm_result.get("confidence", 0.5)
        llm_signals = llm_result.get("signals", [])

        if isinstance(llm_signals, list):
            signals.extend(llm_signals)

        # ---------- PHASE 3: HARD OVERRIDES ----------
        if "high_stakes_language" in signals:
            depth = "RIGOROUS"

        if depth not in self.DEPTHS:
            depth = "LIGHT"

        confidence = self._clamp(confidence)

        return self._decision(
            depth=depth,
            confidence=confidence,
            signals=list(set(signals))
        )

    # =========================
    # INTERNAL HELPERS
    # =========================
    def _is_trivial(self, query: str) -> bool:
        short = len(query.split()) <= 5
        simple_pattern = bool(
            re.match(r"^(what is|define|meaning of)\b", query.lower())
        )
        return short and simple_pattern

    def _llm_assess_depth(self, query: str) -> dict:
        system_msg = (
            "You are a cognitive complexity classifier.\n"
            "Decide how much reasoning is REQUIRED to answer the query correctly.\n\n"
            "Return ONLY JSON:\n"
            "{\n"
            "  \"depth\": \"NONE\" | \"LIGHT\" | \"STRUCTURED\" | \"RIGOROUS\",\n"
            "  \"confidence\": float (0.0 - 1.0),\n"
            "  \"signals\": [\"decision\", \"analysis\", \"risk\", \"multi_step\"]\n"
            "}"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.SCOUT,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": query}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            data = completion.choices[0].message.content
            parsed = json.loads(data)

            return {
                "depth": parsed.get("depth"),
                "confidence": parsed.get("confidence"),
                "signals": parsed.get("signals", [])
            }

        except Exception as e:
            print(f"⚠️ REASONING: LLM assessment failed: {e}")
            return {}

    def _decision(self, depth: str, confidence: float, signals: list) -> ReasoningDecision:
        return ReasoningDecision(
            depth=depth,
            confidence=confidence,
            signals=signals,
            controller_version=self.VERSION
        )

    def _clamp(self, value) -> float:
        try:
            v = float(value)
            return max(0.0, min(1.0, round(v, 2)))
        except Exception:
            return 0.5