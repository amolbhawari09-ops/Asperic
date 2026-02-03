import os
import re
from groq import Groq
from intelligence import IntelligenceCore


class AstraBrain:
    """
    Asperic Core Reasoning Node (Professional-Grade)
    ------------------------------------------------
    - Executes reasoning by declared cognitive depth
    - Multi-pass reasoning ONLY for RIGOROUS depth
    - No inference of stakes, persona, or depth
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
        # 2. Execute reasoning
        # =========================
        if reasoning_decision.depth == "RIGOROUS":
            raw_answer = self._rigorous_multi_pass(
                question=user_question,
                context=context_text
            )
        else:
            raw_answer = self._single_pass(
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
    # SINGLE PASS (NON-RIGOROUS)
    # =========================
    def _single_pass(self, question: str, context: str, depth: str) -> str:
        if depth == "NONE":
            system_role = "Provide a direct, concise factual answer."
        elif depth == "LIGHT":
            system_role = "Provide a short, clear explanation."
        else:  # STRUCTURED
            system_role = (
                "Solve step by step. "
                "Explain reasoning clearly and sequentially."
            )

        user_msg = (
            f"--- CONTEXT ---\n{context}\n--- END CONTEXT ---\n\n"
            f"QUESTION:\n{question}"
        )

        return self._run_inference(user_msg, system_role)

    # =========================
    # MULTI-PASS RIGOROUS MODE
    # =========================
    def _rigorous_multi_pass(self, question: str, context: str) -> str:
        # -------- PASS 1: ANALYSIS --------
        analysis_prompt = (
            "You are performing internal professional analysis.\n"
            "Do NOT write a final answer.\n"
            "Break the problem down, list assumptions, constraints, risks.\n"
            "Be precise and critical.\n\n"
            f"CONTEXT:\n{context}\n\nQUESTION:\n{question}"
        )

        analysis = self._run_inference(
            analysis_prompt,
            system_msg="You are a senior analyst."
        )

        # -------- PASS 2: CRITIC --------
        critique_prompt = (
            "You are a critical reviewer.\n"
            "Review the following analysis.\n"
            "Identify logical gaps, missing assumptions, risks, or weak reasoning.\n"
            "Suggest corrections.\n\n"
            f"ANALYSIS:\n{analysis}"
        )

        critique = self._run_inference(
            critique_prompt,
            system_msg="You are a strict professional reviewer."
        )

        # -------- PASS 3: SYNTHESIS --------
        synthesis_prompt = (
            "You are a senior professional.\n"
            "Using the analysis and critique below, produce a final answer.\n"
            "The answer must be:\n"
            "- Clear\n"
            "- Defensible\n"
            "- Professionally worded\n"
            "- Free of internal analysis\n"
            "- Explicit about limits and uncertainty\n\n"
            f"ANALYSIS:\n{analysis}\n\n"
            f"CRITIQUE:\n{critique}\n\n"
            f"QUESTION:\n{question}"
        )

        return self._run_inference(
            synthesis_prompt,
            system_msg="You are a senior professional expert."
        )

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