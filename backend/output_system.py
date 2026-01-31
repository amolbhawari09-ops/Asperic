import re
import uuid
import datetime


class OutputSystem:
    """
    Asperic Adaptive Decision Response (ADR)
    Output authority only. No reasoning here.
    """

    def __init__(self):
        self.HIGH_STAKES_TRIGGERS = [
            "should", "decide", "recommend", "risk", "compare",
            "legal", "tax", "finance", "security", "production"
        ]

    def assemble(self, response: dict, user_query: str = "") -> str:
        decision_id = self._generate_decision_id()
        timestamp = self._timestamp()

        if response.get("status") == "REFUSED":
            return self._render_refusal(
                response.get("refusal", {}),
                decision_id,
                timestamp
            )

        blocks = []

        blocks.append(self._section("ANSWER", response.get("answer", "")))

        trust = response.get("status", "CONDITIONAL")
        confidence = response.get("confidence")
        if confidence:
            trust = f"{trust} | Confidence: {confidence}"

        blocks.append(self._section("TRUST", trust))

        assumptions = response.get("assumptions") or []
        if assumptions:
            blocks.append(self._list_section("VALID IF", assumptions))

        reasons = response.get("reasons") or []
        if reasons:
            blocks.append(self._list_section("WHY THIS HOLDS", reasons))

        limits = response.get("limits") or []
        if limits and self._is_high_stakes(user_query):
            blocks.append(self._list_section("LIMITS", limits))

        next_steps = response.get("next_steps") or []
        if next_steps:
            blocks.append(self._list_section("NEXT STEP", next_steps))

        blocks.append(self._metadata(decision_id, timestamp))

        return "\n\n".join(blocks)

    def _render_refusal(self, refusal: dict, decision_id: str, timestamp: str) -> str:
        blocks = []
        blocks.append(self._section("STATUS", "Cannot answer yet"))
        blocks.append(self._section(
            "WHY",
            refusal.get("reason", "Unsafe or insufficient input.")
        ))

        needed = refusal.get("needed", [])
        if needed:
            blocks.append(self._list_section("WHAT IS NEEDED", needed))

        why = refusal.get("why_it_matters")
        if why:
            blocks.append(self._section("WHY IT MATTERS", why))

        blocks.append(self._metadata(decision_id, timestamp))
        return "\n\n".join(blocks)

    def _section(self, title: str, content: str) -> str:
        return f"{title}\n{self._clean(content)}"

    def _list_section(self, title: str, items: list) -> str:
        lines = [f"- {self._clean(i)}" for i in items if i]
        return f"{title}\n" + "\n".join(lines)

    def _metadata(self, decision_id: str, timestamp: str) -> str:
        return f"--\nDecision ID: {decision_id}\nTime: {timestamp}"

    def _is_high_stakes(self, query: str) -> bool:
        q = (query or "").lower()
        return any(k in q for k in self.HIGH_STAKES_TRIGGERS)

    def _generate_decision_id(self) -> str:
        return f"ASP-{uuid.uuid4().hex[:8].upper()}"

    def _timestamp(self) -> str:
        return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    def _clean(self, text: str) -> str:
        if not text:
            return ""
        for p in ["As an AI", "I am", "According to"]:
            text = re.sub(p, "", text, flags=re.IGNORECASE)
        return text.strip()