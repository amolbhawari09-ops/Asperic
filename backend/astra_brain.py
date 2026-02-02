import os
import re
from groq import Groq
from intelligence import IntelligenceCore


class AstraBrain:
    """
    Asperic Core Reasoning Node (Upgraded)
    -------------------------------------
    Responsibilities:
    - Professional reasoning ONLY
    - Obey declared SituationDecision
    - Produce structured, auditable decisions
    - NEVER infer context or persona
    """

    def __init__(self, memory_shared=None, intelligence_core=None):
        # === INFRASTRUCTURE ===
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise EnvironmentError("CRITICAL: GROQ_API_KEY not found.")

        self.client = Groq(api_key=self.api_key)

        self.MAVERICK = "meta-llama/llama-4-maverick-17b-128e-instruct"

        # Dependency injection (testable & controllable)
        self.intel = intelligence_core or IntelligenceCore()
        self.memory = memory_shared

    # =========================
    # PUBLIC ENTRY
    # =========================
    def chat(
        self,
        user_question: str,
        history: list,
        situation
    ) -> dict:
        """
        Professional reasoning entrypoint.
        Situation is DECLARED, not inferred.
        """

        history = history or []

        # =========================
        # 1. Determine reasoning strictness
        # =========================
        thinking = (
            "analytical"
            if situation.ruleset == "strict"
            else "practical"
        )

        # =========================
        # 2. Context gathering (policy-gated)
        # =========================
        context = ""

        if situation.verification_required:
            context = self.intel.verify_facts(
                self.intel.live_research(user_question)
            )

            if not context or "ERROR" in context or "INSUFFICIENT" in context:
                if situation.refusal_allowed:
                    return self._refusal_response(
                        reason="Insufficient verified information to answer safely.",
                        needed=["Provide missing details", "Clarify constraints"],
                        why="This situation requires verifiable correctness."
                    )
                else:
                    context = ""  # continue without verified context

        # =========================
        # 3. Core reasoning
        # =========================
        raw_answer = self._generate_logic(
            question=user_question,
            context=context,
            thinking=thinking
        )

        clean_answer = self._security_scrub(raw_answer)

        # =========================
        # 4. Structured response
        # =========================
        return self._build_response(
            answer=clean_answer,
            situation=situation,
            used_verification=bool(context)
        )

    # =========================
    # CORE REASONING
    # =========================
    def _generate_logic(self, question: str, context: str, thinking: str) -> str:
        """
        Pure reasoning engine.
        No mode logic. No situation inference.
        """

        if thinking == "analytical":
            system_role = (
                "You are a senior professional expert. "
                "Produce a correct, defensible answer. "
                "Explicitly state assumptions, constraints, and uncertainties. "
                "If information is missing, say so clearly. "
                "Avoid speculation."
            )
        else:
            system_role = (
                "You are a knowledgeable professional assistant. "
                "Provide a clear, accurate explanation using safe defaults. "
                "Do not invent facts or over-speculate."
            )

        user_msg = (
            f"--- CONTEXT ---\n{context}\n--- END CONTEXT ---\n\n"
            f"QUESTION:\n{question}"
        )

        return self._run_inference(
            prompt=user_msg,
            system_msg=system_role
        )

    # =========================
    # RESPONSE BUILDING
    # =========================
    def _build_response(self, answer: str, situation, used_verification: bool) -> dict:
        """
        Policy-aware response constructor.
        """

        status = (
            "VERIFIED"
            if situation.situation in ["LOW_STAKES", "INFORMATIONAL"]
            else "CONDITIONAL"
        )

        confidence = (
            "High"
            if situation.situation in ["LOW_STAKES", "INFORMATIONAL"]
            else "Medium"
        )

        return {
            "answer": answer,
            "status": status,
            "confidence": confidence,
            "assumptions": (
                ["External data assumed correct"]
                if used_verification
                else []
            ),
            "reasons": (
                ["Based on verified external sources"]
                if used_verification
                else []
            ),
            "limits": (
                ["Limited by available verified data"]
                if situation.verification_required and not used_verification
                else []
            ),
            "next_steps": []
        }

    # =========================
    # REFUSAL
    # =========================
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
    # INFRA
    # =========================
    def _run_inference(self, prompt: str, system_msg: str) -> str:
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