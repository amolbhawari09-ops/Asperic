import re
import uuid
import datetime


class OutputSystem:
    """
    Asperic Universal Output System (v2.1)
    -------------------------------------
    • Risk-based rendering
    • Consumer-first by default
    • Enterprise metadata is explicit, not accidental
    """

    def __init__(self, audience: str = "CONSUMER"):
        self.audience = audience.upper()
        self._decision_id = self._generate_decision_id()

        self.HIGH_STAKES_TRIGGERS = [
            "should", "production", "invest", "legal",
            "tax", "finance", "security", "risk", "decide"
        ]

    # =========================
    # PUBLIC ENTRY
    # =========================
    def assemble(self, response: dict, user_query: str = "") -> str:
        status = response.get("status", "CONDITIONAL")

        if status == "REFUSED":
            return self._render_refusal(response.get("refusal", {}))

        # --- LOW RISK: JUST ANSWER ---
        if self._is_low_risk(user_query, response):
            return self._clean(response.get("answer", ""))

        blocks = []

        # --- ANSWER ---
        blocks.append(self._clean(response.get("answer", "")))

        # --- SOFT TRUST SIGNAL (NON-INTRUSIVE) ---
        if self.audience == "CONSUMER" and response.get("confidence"):
            blocks.append(f"({response['confidence']} confidence)")

        # --- CONDITIONS ---
        assumptions = response.get("assumptions") or []
        if assumptions:
            blocks.append(self._conditions_block(assumptions))

        # --- LIMITS ---
        limits = response.get("limits") or []
        if limits and self._is_high_stakes(user_query):
            blocks.append(self._limits_block(limits))

        # --- ENTERPRISE METADATA ---
        if self.audience == "ENTERPRISE":
            blocks.append(self._enterprise_metadata(response))

        return "\n\n".join(blocks)

    # =========================
    # RENDER BLOCKS
    # =========================
    def _render_refusal(self, refusal: dict) -> str:
        blocks = ["I can’t answer this yet."]

        if refusal.get("reason"):
            blocks.append(refusal["reason"])

        needed = refusal.get("needed", [])
        if needed:
            blocks.append(
                "To move forward, I need:\n" +
                "\n".join(f"- {self._clean(n)}" for n in needed)
            )

        if refusal.get("why_it_matters"):
            blocks.append(refusal["why_it_matters"])

        if self.audience == "ENTERPRISE":
            blocks.append(self._decision_metadata())

        return "\n\n".join(blocks)

    def _conditions_block(self, assumptions: list) -> str:
        return "This holds if:\n" + "\n".join(
            f"- {self._clean(a)}" for a in assumptions
        )

    def _limits_block(self, limits: list) -> str:
        return "Be aware:\n" + "\n".join(
            f"- {self._clean(l)}" for l in limits
        )

    # =========================
    # ENTERPRISE
    # =========================
    def _enterprise_metadata(self, response: dict) -> str:
        return (
            "--\n"
            f"Status: {response.get('status')}\n"
            f"Confidence: {response.get('confidence', 'N/A')}\n"
            f"Decision ID: {self._decision_id}\n"
            f"Time: {self._timestamp()}"
        )

    def _decision_metadata(self) -> str:
        return (
            "--\n"
            f"Decision ID: {self._decision_id}\n"
            f"Time: {self._timestamp()}"
        )

    # =========================
    # RISK LOGIC
    # =========================
    def _is_low_risk(self, query: str, response: dict) -> bool:
        if not query:
            return True
        if response.get("assumptions"):
            return False
        return not self._is_high_stakes(query)

    def _is_high_stakes(self, query: str) -> bool:
        q = (query or "").lower()
        keyword_hit = any(k in q for k in self.HIGH_STAKES_TRIGGERS)
        return keyword_hit

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