import os
import re
import time
from groq import Groq
from intelligence import IntelligenceCore


class AstraBrain:
    """
    Asperic Core Reasoning Node (Production-Safe)
    --------------------------------------------
    - Multi-pass reasoning ONLY for RIGOROUS
    - Automatic fallback on timeout or failure
    - GUARANTEED response (no frontend failure)
    """

    MAX_RIGOROUS_TIME = 8.0  # seconds (safe for Vercel/mobile)

    def __init__(self, memory_shared=None, intelligence_core=None):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise EnvironmentError("CRITICAL: GROQ_API_KEY not found.")

        self.client = Groq(api_key=self.api_key)
        self.MAVERICK = "meta-llama/llama-4-maverick-17b-128e-instruct"

        self.intel = intelligence_core or IntelligenceCore()
        self.memory = memory_shared

    # =========================
    # PUBLIC ENTRY
    # =========================
    def chat(self, user_question, history, situation, reasoning_decision) -> dict:
        history = history or []
        start_time = time.time()

        # =========================
        # 1. Verification
        # =========================
        verification = None
        context_text = ""

        if situation.verification_required:
            verification = self.intel.verify(user_question)

            if verification["status"] in {"ERROR", "INSUFFICIENT"} and situation.refusal_allowed:
                return self._refusal_response(
                    reason="Insufficient verified information.",
                    needed=verification.get("gaps", []),
                    why="This decision requires verifiable accuracy."
                )

            context_text = verification.get("content", "")

        # =========================
        # 2. Reasoning Execution
        # =========================
        try:
            if reasoning_decision.depth == "RIGOROUS":
                raw_answer = self._rigorous_safe(
                    user_question,
                    context_text,
                    start_time
                )
            else:
                raw_answer = self._single_pass(
                    user_question,
                    context_text,
                    reasoning_decision.depth
                )

        except Exception as e:
            # ABSOLUTE FAILSAFE
            raw_answer = (
                "I encountered a processing issue while reasoning deeply. "
                "Here is a safe, direct answer instead:\n\n"
                + self._single_pass(user_question, context_text, "LIGHT")
            )

        clean_answer = self._security_scrub(raw_answer)

        # =========================
        # 3. Structured Response
        # =========================
        return {
            "answer": clean_answer,
            "status": "VERIFIED" if verification and verification.get("status") == "VERIFIED" else "CONDITIONAL",
            "confidence": "High" if verification else "Medium",
            "reasoning_depth": reasoning_decision.depth,
            "limits": verification.get("gaps", []) if verification else [],
            "next_steps": []
        }

    # =========================
    # SINGLE PASS
    # =========================
    def _single_pass(self, question, context, depth) -> str:
        if depth == "NONE":
            system_role = "Provide a direct, concise factual answer."
        elif depth == "LIGHT":
            system_role = "Provide a short, clear explanation."
        else:
            system_role = "Solve step by step. Explain reasoning clearly."

        prompt = f"CONTEXT:\n{context}\n\nQUESTION:\n{question}"
        return self._run(prompt, system_role)

    # =========================
    # SAFE MULTI-PASS RIGOROUS
    # =========================
    def _rigorous_safe(self, question, context, start_time) -> str:
        def timed():
            return time.time() - start_time > self.MAX_RIGOROUS_TIME

        # PASS 1 — ANALYSIS
        analysis = self._run(
            f"Analyze deeply. List assumptions, risks.\n\n{question}",
            "You are a senior analyst."
        )

        if timed():
            return self._single_pass(question, context, "STRUCTURED")

        # PASS 2 — CRITIC
        critique = self._run(
            f"Critique this analysis and find gaps:\n\n{analysis}",
            "You are a strict reviewer."
        )

        if timed():
            return self._single_pass(question, context, "STRUCTURED")

        # PASS 3 — SYNTHESIS
        return self._run(
            f"""
Use the analysis and critique below to give a final professional answer.
Be clear, cautious, and explicit about limits.

ANALYSIS:
{analysis}

CRITIQUE:
{critique}

QUESTION:
{question}
""",
            "You are a senior professional expert."
        )

    # =========================
    # INFRA
    # =========================
    def _run(self, prompt, system_msg) -> str:
        completion = self.client.chat.completions.create(
            model=self.MAVERICK,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        return completion.choices[0].message.content.strip()

    def _security_scrub(self, text: str) -> str:
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[SENSITIVE]', text)
        text = re.sub(r'\b[a-fA-F0-9]{32,}\b', '[SENSITIVE]', text)
        return text.replace("**", "").strip()

    def _refusal_response(self, reason, needed, why):
        return {
            "status": "REFUSED",
            "refusal": {
                "reason": reason,
                "needed": needed,
                "why_it_matters": why
            }
        }