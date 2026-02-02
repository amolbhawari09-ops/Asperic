import json
import re
from model_loader import groq_client


class Predictor:
    """
    Asperic Consequence-Aware Predictor
    -----------------------------------
    Purpose:
    - Estimate consequence of being wrong
    - Signal responsibility & verification needs
    - Route queries safely (NOT compute-based)
    """

    def __init__(self):
        self.SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"

        # High-risk domains (deterministic guardrails)
        self.HIGH_RISK_KEYWORDS = [
            "legal", "law", "contract", "tax", "gst", "compliance",
            "finance", "investment", "money", "loan",
            "medical", "health", "diagnosis",
            "production", "deploy", "security", "authentication",
            "immigration", "visa", "exam", "certificate"
        ]

        # System evolution metadata
        self.PREDICTOR_VERSION = "v2.0-consequence-aware"

    # =========================
    # PUBLIC ENTRY
    # =========================
    def predict(self, text: str) -> dict:
        """
        Returns a routing decision object.

        Output schema:
        {
            "route": "LOW_STAKES" | "INFORMATIONAL" | "DECISION_SUPPORT" | "ACCOUNTABILITY_REQUIRED",
            "confidence": float,
            "signals": [str],
            "version": str
        }
        """

        signals = []

        # --- PHASE 1: DETERMINISTIC RISK HEURISTICS ---
        lowered = text.lower()

        if self._contains_sensitive_mask(text):
            signals.append("sensitive_data_present")

        if self._contains_high_risk_keywords(lowered):
            signals.append("high_risk_domain")

        # --- PHASE 2: LLM CONSEQUENCE ESTIMATION ---
        llm_result = self._llm_consequence_estimate(text)

        route = llm_result.get("route", "INFORMATIONAL")
        confidence = llm_result.get("confidence", 0.5)
        llm_signals = llm_result.get("signals", [])

        signals.extend(llm_signals)

        # --- PHASE 3: HARD ESCALATION RULES ---
        if "high_risk_domain" in signals:
            route = "ACCOUNTABILITY_REQUIRED"

        if "decision_request" in signals and route == "INFORMATIONAL":
            route = "DECISION_SUPPORT"

        return {
            "route": route,
            "confidence": round(confidence, 2),
            "signals": list(set(signals)),
            "version": self.PREDICTOR_VERSION
        }

    # =========================
    # INTERNAL HELPERS
    # =========================
    def _contains_sensitive_mask(self, text: str) -> bool:
        return "[SENSITIVE" in text or "[DATA_MASK]" in text

    def _contains_high_risk_keywords(self, text: str) -> bool:
        return any(k in text for k in self.HIGH_RISK_KEYWORDS)

    def _llm_consequence_estimate(self, text: str) -> dict:
        """
        LLM estimates consequence of being wrong.
        DOES NOT decide persona or refusal.
        """

        system_msg = (
            "You are a risk classifier for a professional AI system.\n"
            "Classify the USER QUERY by consequence of being wrong.\n\n"
            "Return ONLY JSON with this schema:\n"
            "{\n"
            "  \"route\": \"LOW_STAKES\" | \"INFORMATIONAL\" | "
            "\"DECISION_SUPPORT\" | \"ACCOUNTABILITY_REQUIRED\",\n"
            "  \"confidence\": float (0.0 - 1.0),\n"
            "  \"signals\": [\"decision_request\", \"external_dependency\", "
            "\"regulatory_context\", \"user_accountability\"]\n"
            "}\n\n"
            "Definitions:\n"
            "- LOW_STAKES: Casual, no impact if wrong\n"
            "- INFORMATIONAL: Learning or explanation\n"
            "- DECISION_SUPPORT: User may act on this\n"
            "- ACCOUNTABILITY_REQUIRED: Legal, financial, safety, production impact\n"
        )

        try:
            completion = groq_client.chat.completions.create(
                model=self.SCOUT,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": text}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            return json.loads(completion.choices[0].message.content)

        except Exception as e:
            print(f"⚠️ Predictor LLM failure: {e}")

            # Safe fallback: informational, low confidence
            return {
                "route": "INFORMATIONAL",
                "confidence": 0.3,
                "signals": ["llm_uncertain"]
            }