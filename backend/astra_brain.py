import os
import re
from groq import Groq
from intelligence import IntelligenceCore


class AstraBrain:
    """
    Asperic Core Reasoning Node
    ---------------------------
    Responsible ONLY for reasoning and structured decision output.
    NEVER formats final user-facing text.
    """

    def __init__(self, memory_shared=None):
        # === INFRASTRUCTURE & SECURITY ===
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise EnvironmentError("CRITICAL: GROQ_API_KEY not found.")

        self.client = Groq(api_key=self.api_key)

        self.MAVERICK = "meta-llama/llama-4-maverick-17b-128e-instruct"
        self.SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"

        self.intel = IntelligenceCore()
        self.memory = memory_shared

    # =========================
    # PUBLIC ENTRY
    # =========================
    def chat(
        self,
        user_question,
        history=None,
        mode="RESEARCH_MODE",
        thinking="practical"
    ):
        history = history or []

        # ---- SIMPLE QUERY FAST PATH ----
        if self._is_simple_query(user_question):
            text = self._run_inference(
                user_question,
                "Provide a brief, factual answer. No filler.",
                self.SCOUT
            )
            return self._verified_response(text)

        # ---- CONTEXT GATHERING ----
        context = self._gather_context(user_question, mode)

        if self._context_insufficient(context):
            return self._refusal_response(
                reason="Insufficient verified context to answer safely.",
                needed=["Clarify scope", "Provide required details"],
                why="Asperic does not guess when critical data is missing."
            )

        # ---- REASONING ----
        raw_answer = self._generate_logic(
            q=user_question,
            context=context,
            hist=history,
            mode=mode,
            thinking=thinking
        )

        clean_answer = self._security_scrub(raw_answer)

        return self._conditional_response(clean_answer, context, thinking)

    # =========================
    # RESPONSE BUILDERS
    # =========================
    def _verified_response(self, answer: str) -> dict:
        return {
            "answer": answer,
            "status": "VERIFIED",
            "confidence": "High",
            "assumptions": [],
            "reasons": [],
            "limits": [],
            "next_steps": []
        }

    def _conditional_response(self, answer: str, context: str, thinking: str) -> dict:
        assumptions = (
            self._extract_assumptions(context)
            if thinking == "analytical"
            else []
        )

        return {
            "answer": answer,
            "status": "CONDITIONAL" if assumptions else "VERIFIED",
            "confidence": "Medium" if assumptions else "High",
            "assumptions": assumptions,
            "reasons": self._extract_reasons(context),
            "limits": self._extract_limits(context),
            "next_steps": []
        }

    def _refusal_response(self, reason, needed, why) -> dict:
        return {
            "status": "REFUSED",
            "refusal": {
                "reason": reason,
                "needed": needed,
                "why_it_matters": why
            }
        }

    # =========================
    # CORE LOGIC
    # =========================
    def _generate_logic(self, q, context, hist, mode, thinking):
        """
        thinking:
          - practical   → fast, default-safe reasoning
          - analytical  → deep, assumption-aware reasoning
        """

        if thinking == "analytical":
            system_role = (
                "You are a senior technical expert. "
                "Reason carefully. Explicitly evaluate assumptions, edge cases, "
                "and tradeoffs. Avoid speculation. If data is missing, say so."
            )
        else:
            system_role = (
                "You are a senior practitioner. "
                "Provide a clear, actionable answer using safe defaults. "
                "Avoid unnecessary theory or exploration."
            )

        if mode == "PROJECT_MODE":
            system_role += (
                " Provide production-grade guidance suitable for real systems."
            )

        user_msg = (
            f"--- CONTEXT ---\n{context}\n--- END CONTEXT ---\n\n"
            f"QUESTION: {q}"
        )

        return self._run_inference(user_msg, system_role, self.MAVERICK)

    # =========================
    # UTILITIES
    # =========================
    def _is_simple_query(self, text):
        simple = {"hi", "hello", "thanks", "hey"}
        return text.lower().strip() in simple

    def _context_insufficient(self, context):
        if not context:
            return True
        if "ERROR" in context or "INSUFFICIENT" in context:
            return True
        return False

    def _extract_assumptions(self, context):
        assumptions = []
        lc = context.lower()
        if "jurisdiction" in lc:
            assumptions.append("Jurisdiction-specific rules assumed")
        if "time" in lc:
            assumptions.append("Time-sensitive data assumed current")
        return assumptions

    def _extract_reasons(self, context):
        return ["Based on verified external data"] if context else []

    def _extract_limits(self, context):
        limits = []
        if "approx" in context.lower():
            limits.append("Values may be approximate")
        return limits

    def _run_inference(self, prompt, system_msg, model):
        completion = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        return completion.choices[0].message.content.strip()

    def _gather_context(self, query, mode):
        if mode == "PROJECT_MODE" and self.memory:
            return self.memory.search(query)
        if mode == "RESEARCH_MODE":
            return self.intel.verify_facts(
                self.intel.live_research(query)
            )
        return ""

    def _security_scrub(self, text):
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[SENSITIVE]', text)
        text = re.sub(r'\b[a-fA-F0-9]{32,}\b', '[SENSITIVE]', text)
        return text.replace("**", "").strip()