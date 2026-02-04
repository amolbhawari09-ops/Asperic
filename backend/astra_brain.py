import os
import re
from groq import Groq
from intelligence import IntelligenceCore


class AstraBrain:
    """
    Asperic Core Reasoning Node (Upgraded)
    -------------------------------------
    Responsibilities:
    - Execute reasoning based on declared cognitive depth
    - Obey SituationDecision (policy, risk)
    - Consume verification results (as input, not guesswork)
    - NEVER infer stakes, persona, or depth
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
        situation,
        reasoning_decision
    ) -> dict:
        """
        Professional reasoning entrypoint.

        Inputs are DECLARED:
        - situation (policy / risk)
        - reasoning_decision (cognitive depth)

        AstraBrain does NOT infer anything.
        """

        history = history or []

        # =========================
        # 1. Verification (policy-gated)
        # =========================
        verification = None
        context_text = ""

        if situation.verification_required:
            verification = self.intel.verify(user_question)

            if verification["status"] == "ERROR" and situation.refusal_allowed:
                return self._refusal_response(
                    reason="Verification process failed.",
                    needed=["Retry later", "Provide alternative sources"],
                    why="This situation requires verified correctness."
                )

            if verification["status"] == "INSUFFICIENT" and situation.refusal_allowed:
                return self._refusal_response(
                    reason="Insufficient verified information.",
                    needed=verification.get("gaps", []),
                    why="This decision requires verifiable accuracy."
                )

            context_text = verification.get("content", "")

        # =========================
        # 2. Execute reasoning by DEPTH
        # =========================
        raw_answer = self._execute_reasoning(
            question=user_question,
            context=context_text,
            depth=reasoning_decision.depth
        )

        clean_answer = self._security_scrub(raw_answer)

        # =========================
        # 3. Structured response
        # =========================
        return self._build_response(
            answer=clean_answer,
            situation=situation,
            verification=verification,
            reasoning_decision=reasoning_decision
        )

    # =========================
    # REASONING EXECUTION
    # =========================
    def _execute_reasoning(self, question: str, context: str, depth: str) -> str:
        """
        Executes reasoning strictly according to cognitive depth.
        """

        if depth == "NONE":
            system_role = (
                "Provide a direct, concise factual answer. "
                "No explanation unless strictly necessary."
            )

        elif depth == "LIGHT":
            system_role = (
                "Provide a short, clear explanation. "
                "Avoid deep analysis or assumptions."
            )

        elif depth == "STRUCTURED":
            system_role = (
                "Solve the problem step by step. "
                "Explain reasoning clearly and sequentially."
            )

        elif depth == "RIGOROUS":
            system_role = (
                "You are a senior professional expert.\n"
                "Follow this strict reasoning process:\n"
                "1. Define the problem precisely\n"
                "2. State assumptions explicitly\n"
                "3. Identify constraints and risks\n"
                "4. Reason step by step\n"
                "5. Reach a defensible conclusion\n"
                "6. State limits and uncertainty\n"
                "Avoid speculation. No skipped steps."
            )

        else:
            # Fail-safe
            system_role = (
                "Provide a clear and accurate answer."
            )

        user_msg = (
            f"--- CONTEXT ---\n{context}\n--- END CONTEXT ---\n\n"
            f"QUESTION:\n{question}"
        )

        return self._run_inference(user_msg, system_role)

    # =========================
    # RESPONSE BUILDING
    # =========================
    def _build_response(
        self,
        answer: str,
        situation,
        verification: dict | None,
        reasoning_decision
    ) -> dict:
        verified = verification and verification.get("status") == "VERIFIED"

        return {
            "answer": answer,
            "status": "VERIFIED" if verified else "CONDITIONAL",
            "confidence": "High" if verified else "Medium",
            "reasoning_depth": reasoning_decision.depth,
            "assumptions": (
                ["External data assumed correct"]
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