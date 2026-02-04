import re
import uuid
import datetime
from typing import Dict, Any


class OutputSystem:
    """
    Asperic Universal Output System (v3.0)
    -------------------------------------
    • Always JSON output (frontend-safe)
    • Risk-aware rendering
    • LIGHT vs PROFESSIONAL adaptive formatting
    • No silent failures
    """

    def __init__(self, audience: str = "CONSUMER"):
        self.audience = audience.upper()
        self.decision_id = self._generate_decision_id()

        self.HIGH_STAKES_TRIGGERS = [
            "should", "production", "invest", "legal",
            "tax", "finance", "security", "risk", "decide"
        ]

    # =========================
    # PUBLIC ENTRY
    # =========================
    def assemble(self, response: Dict[str, Any], user_query: str = "") -> Dict[str, Any]:
        """
        Always returns JSON.
        NEVER returns plain text.
        """

        if not isinstance(response, dict):
            return self._error_payload("Invalid response type")

        status = response.get("status", "CONDITIONAL")

        if status == "REFUSED":
            return self._refusal_payload(response.get("refusal", {}))

        answer = self._clean(response.get("answer", ""))

        payload = {
            "answer": answer,
            "status": status,
            "confidence": response.get("confidence", "Medium"),
            "decision_id": self.decision_id,
            "timestamp": self._timestamp(),
        }

        # -------------------------
        # Optional fields
        # -------------------------
        if response.get("assumptions"):
            payload["assumptions"] = response["assumptions"]

        if self._is_high_stakes(user_query) and response.get("limits"):
            payload["limits"] = response["limits"]

        if self.audience == "ENTERPRISE":
            payload["enterprise"] = {
                "ruleset": "strict",
                "audit": True
            }

        return payload

    # =========================
    # REFUSAL
    # =========================
    def _refusal_payload(self, refusal: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "answer": "I can’t answer this yet.",
            "status": "REFUSED",
            "reason": refusal.get("reason", ""),
            "needed": refusal.get("needed", []),
            "why_it_matters": refusal.get("why_it_matters", ""),
            "decision_id": self.decision_id,
            "timestamp": self._timestamp()
        }

    # =========================
    # ERROR FALLBACK
    # =========================
    def _error_payload(self, message: str) -> Dict[str, Any]:
        return {
            "answer": "",
            "status": "ERROR",
            "error": message,
            "decision_id": self.decision_id,
            "timestamp": self._timestamp()
        }

    # =========================
    # RISK LOGIC
    # =========================
    def _is_high_stakes(self, query: str) -> bool:
        q = (query or "").lower()
        return any(k in q for k in self.HIGH_STAKES_TRIGGERS)

    # =========================
    # UTILITIES
    # =========================
    def _generate_decision_id(self) -> str:
        return f"ASP-{uuid.uuid4().hex[:8].upper()}"

    def _timestamp(self) -> str:
        return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    def _clean(self, text: str) -> str:
        if not text:
            return ""
        for p in ["As an AI", "I am", "According to", "Based on"]:
            text = re.sub(p, "", text, flags=re.IGNORECASE)
        return text.strip()