import os
import re
from groq import Groq
from intelligence import IntelligenceCore


class AstraBrain:
    """
    Asperic Core Reasoning Node (Final)
    ----------------------------------
    Responsibilities:
    - Professional reasoning ONLY
    - Obey declared SituationDecision
    - Consume structured verification results
    - NEVER infer situation, stakes, or persona
    """

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
        # 2. Verification (policy-gated)
        # =========================
        verification = None
        context_text = ""

        if situation.verification_required:
            verification = self.intel.verify(user_question)

            if verification["status"] == "ERROR":
                if situation.refusal_allowed:
                    return self._refusal_response(
                        reason="Verification process failed.",
                        needed=["Retry later", "Provide alternative sources"],
                        why="This situation requires verified correctness."
                    )

            if verification["status"] == "INSUFFICIENT":
                if situation.refusal_allowed:
                    return self._refusal_response(
                        reason="Insufficient verified information.",
                        needed=verification.get("gaps", []),
                        why="This decision requires verifiable accuracy."
                    )

            context_text = verification.get("content", "")

        # =========================
        # 3. Core reasoning
        # =========================
        raw_answer = self._generate_logic(
            question=user_question,
            context=context_text,
            thinking=thinking
        )

        clean_answer = self._security_scrub(raw_answer)

        # =========================
        # 4. Structured response
        # =========================
        return self._build_response(
            answer=clean_answer,
            situation=situation,
            verification=verification
        )

    # =========================
    # CORE REASONING
    # =========================
    def _generate_logic(self, question: str, context: str, thinking: str) -> str:
        if thinking == "analytical":
            system_role = (
                "You are a senior professional expert. "
                "Provide a correct, defensible answer. "
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

        return self._run_inference(user_msg, system_role)

    # =========================
    # RESPONSE BUILDING
    # =========================
    def _build_response(self, answer: str, situation, verification: dict | None) -> dict:
        verified = verification and verification.get("status") == "VERIFIED"

        return {
            "answer": answer,
            "status": "VERIFIED" if verified else "CONDITIONAL",
            "confidence": "High" if verified else "Medium",
            "assumptions": (
                ["External data assumed correct"]
                if verified
                else []
            ),
            "reasons": (
                ["Based on verified external sources"]
                if verified
                else []
            ),
            "limits": (
                verification.get("gaps", [])
                if verification and verification.get("gaps")
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