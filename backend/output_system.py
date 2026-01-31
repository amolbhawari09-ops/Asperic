import re
import uuid
import datetime


class OutputSystem:
    """
    Asperic Adaptive Decision Response (ADR)
    ----------------------------------------
    This system is the SINGLE authority for output presentation.
    Logic decides content. OutputSystem decides structure.
    """

    def __init__(self):
        # Keywords that imply higher rigor
        self.HIGH_STAKES_TRIGGERS = [
            "should", "decide", "recommend", "risk", "compare",
            "legal", "tax", "finance", "security", "production"
        ]

    # =========================
    # PUBLIC ENTRY POINT
    # =========================
    def assemble(self, response: dict, user_query: str = "") -> str:
        """
        Builds the final Asperic response using ADR rules.

        Expected response dict keys (not all required):
        - answer (str)
        - status (str): VERIFIED | CONDITIONAL | REFUSED
        - confidence (str): High | Medium | Low
        - assumptions (list[str])
        - reasons (list[str])
        - limits (list[str])
        - next_steps (list[str])
        - refusal (dict)  # if status == REFUSED
        """

        decision_id = self._generate_decision_id()
        timestamp = self._timestamp()

        # ---------- REFUSAL PATH ----------
        if response.get("status") == "REFUSED":
            return self._render_refusal(response.get("refusal", {}), decision_id, timestamp)

        # ---------- NORMAL PATH ----------
        blocks = []

        # 1. ANSWER (ALWAYS)
        blocks.append(self._section("ANSWER", response.get("answer", "").strip()))

        # 2. TRUST (ALWAYS)
        trust_line = response.get("status", "CONDITIONAL")
        confidence = response.get("confidence")
        if confidence:
            trust_line = f"{trust_line} · Confidence: {confidence}"
        blocks.append(self._section("TRUST", trust_line))

        # 3. VALID IF (CONDITIONAL)
        assumptions = response.get("assumptions") or []
        if assumptions:
            blocks.append(self._list_section("VALID IF", assumptions))

        # 4. WHY THIS HOLDS (OPTIONAL)
        reasons = response.get("reasons") or []
        if reasons:
            blocks.append(self._list_section("WHY THIS HOLDS", reasons))

        # 5. LIMITS (OPTIONAL, HIGH STAKES ONLY)
        limits = response.get("limits") or []
        if limits and self._is_high_stakes(user_query):
            blocks.append(self._list_section("LIMITS", limits))

        # 6. NEXT STEP (OPTIONAL)
        next_steps = response.get("next_steps") or []
        if next_steps:
            blocks.append(self._list_section("NEXT STEP", next_steps))

        # 7. METADATA (ALWAYS, LIGHT)
        blocks.append(self._metadata_block(decision_id, timestamp))

        return "\n\n".join(blocks)

    # =========================
    # RENDER HELPERS
    # =========================
    def _render_refusal(self, refusal: dict, decision_id: str, timestamp: str) -> str:
        """
        First-class refusal renderer.
        Refusal is NOT an error. It is a safe completion.
        """
        blocks = []

        blocks.append(self._section("STATUS", "Cannot answer yet"))

        reason = refusal.get("reason", "Insufficient or unsafe information.")
        blocks.append(self._section("WHY", reason))

        needed = refusal.get("needed", [])
        if needed:
            blocks.append(self._list_section("WHAT’S NEEDED", needed))

        explanation = refusal.get("why_it_matters")
        if explanation:
            blocks.append(self._section("WHY IT MATTERS", explanation))

        blocks.append(self._metadata_block(decision_id, timestamp))

        return "\n\n".join(blocks)

    def _section(self, title: str, content: str) -> str:
        content = self._clean_text(content)
        return f"{title}\n{content}"

    def _list_section(self, title: str, items: list[str]) -> str:
        clean_items = [f"• {self._clean_text(i)}" for i in items if i]
        return f"{title}\n" + "\n".join(clean_items)

    def _metadata_block(self, decision_id: str, timestamp: str) -> str:
        return (
            "—\n"
            f"Decision ID: {decision_id}\n"
            f"Time: {timestamp}"
        )

    # =========================
    # UTILITIES
    # =========================
    def _is_high_stakes(self, query: str) -> bool:
        q = (query or "").lower()
        return any(k in q for k in self.HIGH_STAKES_TRIGGERS)

    def _generate_decision_id(self) -> str:
        return f"ASP-{uuid.uuid4().hex[:8].upper()}"

    def _timestamp(self) -> str:
        return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        patterns = [
            r"As an AI", r"I am", r"This response", r"According to"
        ]
        for p in patterns:
            text = re.sub(p, "", text, flags=re.IGNORECASE)
        return text.strip()