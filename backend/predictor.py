import json
from model_loader import groq_client


class Predictor:
    """
    Asperic Consequence-Aware Predictor (v3.0)
    ------------------------------------------
    Sole responsibility:
    - Estimate consequence of being wrong
    - Output conservative, monotonic-safe routing
    """

    VERSION = "v3.0-consequence-safe"

    ROUTES = {
        "LOW_STAKES",
        "INFORMATIONAL",
        "DECISION_SUPPORT",
        "ACCOUNTABILITY_REQUIRED",
    }

    def __init__(self):
        self.SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"

        # Deterministic domain indicators (ANNOTATION only)
        self.HIGH_RISK_KEYWORDS = [
            "legal", "law", "contract", "tax", "gst", "compliance",
            "finance", "investment", "money", "loan",
            "medical", "health", "diagnosis",
            "production", "deploy", "security", "authentication",
            "immigration", "visa", "exam", "certificate"
        ]

    # =========================
    # PUBLIC ENTRY
    # =========================
    def predict(self, text: str) -> dict:
        """
        Output schema (stable):
        {
            "route": str,
            "confidence": float,   # routing certainty
            "signals": [str],
            "version": str
        }
        """

        signals = []

        # ---------- PHASE 1: DETERMINISTIC ANNOTATION ----------
        lowered = text.lower()

        if self._contains_high_risk_keywords(lowered):
            signals.append("heuristic:high_risk_domain")

        # ---------- PHASE 2: LLM RISK ESTIMATION ----------
        llm_result = self._llm_consequence_estimate(text)

        route = llm_result.get("route", "ACCOUNTABILITY_REQUIRED")
        confidence = llm_result.get("confidence", 0.5)
        llm_signals = llm_result.get("signals", [])

        # Namespace LLM signals
        signals.extend([f"llm:{s}" for s in llm_signals])

        # ---------- PHASE 3: HARD SAFETY ESCALATION ----------
        if "heuristic:high_risk_domain" in signals:
            route = "ACCOUNTABILITY_REQUIRED"

        if route not in self.ROUTES:
            route = "ACCOUNTABILITY_REQUIRED"
            signals.append("system:invalid_route_corrected")

        return {
            "route": route,
            "confidence": round(self._normalize_confidence(confidence), 2),
            "signals": sorted(set(signals)),
            "version": self.VERSION
        }

    # =========================
    # INTERNAL
    # =========================
    def _contains_high_risk_keywords(self, text: str) -> bool:
        return any(k in text for k in self.HIGH_RISK_KEYWORDS)

    def _llm_consequence_estimate(self, text: str) -> dict:
        """
        LLM estimates consequence of being wrong.
        Failure MUST bias toward safety.
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
            "}\n"
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

            # FAIL CLOSED (safe)
            return {
                "route": "ACCOUNTABILITY_REQUIRED",
                "confidence": 0.2,
                "signals": ["llm:failure"]
            }

    def _normalize_confidence(self, value) -> float:
        try:
            v = float(value)
            return max(0.0, min(1.0, v))
        except Exception:
            return 0.5