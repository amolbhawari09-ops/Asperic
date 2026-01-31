import re
import uuid
import datetime


class OutputSystem:
    """
    Asperic Universal Output System (v2)
    -----------------------------------
    • Adapts output to RISK, not question type
    • Consumer-first by default
    • Enterprise metadata is OPTIONAL, not forced
    • No system internals leaked to normal users
    """

    def __init__(self, audience: str = "CONSUMER"):
        # audience = CONSUMER | ENTERPRISE
        self.audience = audience.upper()

        self.HIGH_STAKES_TRIGGERS = [
            "should", "deploy", "production", "invest", "legal",
            "tax", "finance", "security", "risk", "decide"
        ]

    # =========================
    # PUBLIC ENTRY
    # =========================
    def assemble(self, response: dict, user_query: str = "") -> str:
        status = response.get("status", "CONDITIONAL")

        # --- REFUSAL IS FIRST-CLASS ---
        if status == "REFUSED":
            return self._render_refusal(response.get("refusal", {}))

        # --- SIMPLE FACT ANSWER ---
        if self._is_low_risk(user_query, response):
            return self._clean(response.get("answer", ""))

        blocks = []

        # --- CORE ANSWER ---
        blocks.append(self._clean(response.get("answer", "")))

        # --- CONDITIONS (only if needed) ---
        assumptions = response.get("assumptions") or []
        if assumptions:
            blocks.append(self._conditions_block(assumptions))

        # --- LIMITS (high-stakes only) ---
        limits = response.get("limits") or []
        if limits and self._is_high_stakes(user_query):
            blocks.append(self._limits_block(limits))

        # --- ENTERPRISE METADATA (OPTIONAL) ---
        if self.audience == "ENTERPRISE":
            blocks.append(self._enterprise_metadata(response))

        return "\n\n".join(blocks)

    # =========================
    # RENDER BLOCKS
    # =========================
    def _render_refusal(self, refusal: dict) -> str:
        blocks = []

        blocks.append("I can’t answer this yet.")

        reason = refusal.get("reason")
        if reason:
            blocks.append(reason)

        needed = refusal.get("needed", [])
        if needed:
            blocks.append(
                "To move forward, I need:\n" +
                "\n".join(f"- {self._clean(n)}" for n in needed)
            )

        why = refusal.get("why_it_matters")
        if why:
            blocks.append(why)

        if self.audience == "ENTERPRISE":
            blocks.append(self._decision_metadata())

        return "\n\n".join(blocks)

    def _conditions_block(self, assumptions: list) -> str:
        return (
            "This holds if:\n" +
            "\n".join(f"- {self._clean(a)}" for a in assumptions)
        )

    def _limits_block(self, limits: list) -> str:
        return (
            "Be aware:\n" +
            "\n".join(f"- {self._clean(l)}" for l in limits)
        )

    # =========================
    # ENTERPRISE ONLY
    # =========================
    def _enterprise_metadata(self, response: dict) -> str:
        return (
            "--\n"
            f"Status: {response.get('status')}\n"
            f"Confidence: {response.get('confidence', 'N/A')}\n"
            f"Decision ID: {self._generate_decision_id()}\n"
            f"Time: {self._timestamp()}"
        )

    def _decision_metadata(self) -> str:
        return (
            "--\n"
            f"Decision ID: {self._generate_decision_id()}\n"
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