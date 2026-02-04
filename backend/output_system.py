import re
import datetime
from typing import Dict, Any, Optional


class OutputSystem:
    """
    Asperic Universal Output System (v3.1 – Hardened)
    ------------------------------------------------
    • Stable JSON schema
    • No risk re-inference
    • Frontend-safe typing
    • Audit-friendly
    """

    VERSION = "3.1-output-contract"

    def __init__(self, audience: str = "CONSUMER"):
        self.audience = audience.upper()

    # =========================
    # PUBLIC ENTRY
    # =========================
    def assemble(
        self,
        response: Dict[str, Any],
        user_query: str = "",
        decision_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Always returns JSON.
        Schema is stable.
        """

        if not isinstance(response, dict):
            return self._error_payload("Invalid response object", decision_id)

        status = response.get("status", "CONDITIONAL")

        if status == "REFUSED":
            return self._refusal_payload(
                response.get("refusal", {}),
                decision_id
            )

        # -------- Core fields --------
        payload = {
            "answer": self._clean(response.get("answer", "")),
            "status": status,
            "confidence": self._normalize_confidence(response.get("confidence")),
            "reasoning_depth": response.get("reasoning_depth"),
            "assumptions": response.get("assumptions", []),
            "limits": response.get("limits", []),
            "next_steps": response.get("next_steps", []),
            "decision_id": decision_id,
            "timestamp": self._timestamp(),
            "version": self.VERSION
        }

        # -------- Enterprise metadata --------
        payload["enterprise"] = (
            {
                "ruleset": "strict",
                "audit": True
            }
            if self.audience == "ENTERPRISE"
            else None
        )

        return payload

    # =========================
    # REFUSAL
    # =========================
    def _refusal_payload(
        self,
        refusal: Dict[str, Any],
        decision_id: Optional[str]
    ) -> Dict[str, Any]:
        return {
            "answer": None,
            "status": "REFUSED",
            "reason": refusal.get("reason"),
            "needed": refusal.get("needed", []),
            "why_it_matters": refusal.get("why_it_matters"),
            "confidence": 0.0,
            "reasoning_depth": None,
            "assumptions": [],
            "limits": [],
            "next_steps": [],
            "decision_id": decision_id,
            "timestamp": self._timestamp(),
            "version": self.VERSION
        }

    # =========================
    # ERROR
    # =========================
    def _error_payload(
        self,
        message: str,
        decision_id: Optional[str]
    ) -> Dict[str, Any]:
        return {
            "answer": None,
            "status": "ERROR",
            "error": message,
            "confidence": 0.0,
            "decision_id": decision_id,
            "timestamp": self._timestamp(),
            "version": self.VERSION
        }

    # =========================
    # UTILITIES
    # =========================
    def _timestamp(self) -> str:
        return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    def _normalize_confidence(self, value) -> float:
        try:
            v = float(value)
            return max(0.0, min(1.0, round(v, 2)))
        except Exception:
            return 0.5

    def _clean(self, text: str) -> str:
        if not text:
            return ""
        # Minimal safety clean only
        return re.sub(r"\s{2,}", " ", text).strip()