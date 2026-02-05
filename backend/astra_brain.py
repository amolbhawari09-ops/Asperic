import os
import re
from groq import Groq
from intelligence import IntelligenceCore
from model_loader import embedding_provider
from typing import Dict, Optional


class AstraBrain:
    """
    Asperic Core Reasoning Node (Semantic Executor)
    ----------------------------------------------
    Responsibilities:
    - Execute reasoning based on declared depth
    - Adapt explanation using semantic state
    - Obey SituationDecision strictly
    - Perform self-check to reduce drift / hallucination
    """

    VERSION = "v2.0-semantic-executor"

    # -------------------------
    # INIT
    # -------------------------
    def __init__(self, memory_shared=None, intelligence_core=None):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise EnvironmentError("CRITICAL: GROQ_API_KEY not found.")

        self.client = Groq(api_key=self.api_key)
        self.MAVERICK = "meta-llama/llama-4-maverick-17b-128e-instruct"

        self.intel = intelligence_core or IntelligenceCore()
        self.memory = memory_shared
        self.embedder = embedding_provider

    # =========================
    # PUBLIC ENTRY
    # =========================
    def chat(
        self,
        user_question: str,
        history: list,
        situation,
        reasoning_decision,
        semantic_profile: Optional[Dict[str, float]] = None
    ) -> dict:
        """
        Professional reasoning entrypoint.
        ALWAYS returns a response with an `answer`.
        """

        history = history or []

        # =========================
        # 1. VERIFICATION (POLICY-GATED)
        # =========================
        verification = None
        context_text = ""

        if situation.verification_required:
            verification = self.intel.verify(user_question)

            if verification["status"] == "ERROR" and situation.refusal_allowed:
                return self._refusal_response(
                    "Verification failed. Cannot answer safely.",
                    "Verification error",
                    verification.get("gaps", []),
                    "This situation requires verified correctness.",
                    reasoning_decision
                )

            if verification["status"] == "INSUFFICIENT" and situation.refusal_allowed:
                return self._refusal_response(
                    "Not enough verified information to answer safely.",
                    "Insufficient verification",
                    verification.get("gaps", []),
                    "This decision requires verifiable accuracy.",
                    reasoning_decision
                )

            context_text = verification.get("content", "")

        # =========================
        # 2. EXECUTE REASONING
        # =========================
        raw_answer = self._execute_reasoning(
            question=user_question,
            context=context_text,
            depth=reasoning_decision.depth,
            semantic_profile=semantic_profile
        )

        # =========================
        # 3. SELF-CHECK (ANTI-DRIFT)
        # =========================
        final_answer = self._self_check(
            user_question,
            raw_answer,
            semantic_profile
        )

        final_answer = self._security_scrub(final_answer)

        if not final_answer:
            final_answer = "I’m unable to produce a meaningful answer at this time."

        # =========================
        # 4. RESPONSE BUILDING
        # =========================
        return self._build_response(
            final_answer,
            verification,
            reasoning_decision
        )

    # =========================
    # REASONING EXECUTION
    # =========================
    def _execute_reasoning(
        self,
        question: str,
        context: str,
        depth: str,
        semantic_profile: Optional[Dict[str, float]]
    ) -> str:

        mode = self._select_explanation_mode(semantic_profile)

        system_role = self._system_prompt(depth, mode)

        user_msg = (
            f"--- CONTEXT ---\n{context}\n--- END CONTEXT ---\n\n"
            f"QUESTION:\n{question}"
        )

        return self._run_inference(user_msg, system_role)

    def _system_prompt(self, depth: str, mode: str) -> str:
        """
        Convert depth + mode into an execution contract.
        """

        if mode == "ELI5":
            return (
                "Explain this in the simplest possible way.\n"
                "Use at most ONE core idea.\n"
                "Avoid jargon completely.\n"
                "Assume the user is confused, not ignorant."
            )

        if depth == "NONE":
            return "Provide a direct, concise factual answer. No explanation."

        if depth == "LIGHT":
            return (
                "Provide a short, clear explanation.\n"
                "Avoid deep analysis and unnecessary details."
            )

        if depth == "STRUCTURED":
            return (
                "Explain step by step.\n"
                "Use simple structure and clear transitions."
            )

        if depth == "RIGOROUS":
            return (
                "You are a senior professional expert.\n"
                "Follow this strict reasoning process:\n"
                "1. Define the problem precisely\n"
                "2. State assumptions explicitly\n"
                "3. Identify constraints and risks\n"
                "4. Reason step by step\n"
                "5. Reach a defensible conclusion\n"
                "6. State limits and uncertainty\n"
                "Avoid speculation."
            )

        return "Provide a clear and accurate answer."

    # =========================
    # SEMANTIC MODE SELECTION
    # =========================
    def _select_explanation_mode(
        self,
        semantic_profile: Optional[Dict[str, float]]
    ) -> str:
        if not semantic_profile:
            return "NORMAL"

        confusion = semantic_profile.get("confusion", 0.0)
        technicality = semantic_profile.get("technicality", 0.0)

        if confusion > 0.75 or technicality > 0.8:
            return "ELI5"

        return "NORMAL"

    # =========================
    # SELF-CHECK (CORE COGNITION)
    # =========================
    def _self_check(
        self,
        question: str,
        answer: str,
        semantic_profile: Optional[Dict[str, float]]
    ) -> str:
        """
        Compare meaning of question vs answer.
        If drift is too large, simplify once.
        """

        try:
            q_vec = self.embedder.embed(question)
            a_vec = self.embedder.embed(answer)

            similarity = self._cosine_similarity(q_vec, a_vec)

            # Threshold chosen conservatively
            if similarity < 0.55:
                # Retry with forced simplification
                retry_prompt = (
                    "Your previous answer drifted from the question.\n"
                    "Simplify the answer and directly address the user’s intent."
                )
                return self._run_inference(
                    f"{retry_prompt}\n\nQUESTION:\n{question}",
                    "Provide a simpler, more direct answer."
                )

            return answer

        except Exception:
            # Never fail the system
            return answer

    def _cosine_similarity(self, v1, v2) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        return dot / (norm1 * norm2 + 1e-8)

    # =========================
    # RESPONSE BUILDING
    # =========================
    def _build_response(
        self,
        answer: str,
        verification: dict | None,
        reasoning_decision
    ) -> dict:
        verified = verification and verification.get("status") == "VERIFIED"

        return {
            "answer": answer,
            "status": "VERIFIED" if verified else "CONDITIONAL",
            "confidence": "High" if verified else "Medium",
            "reasoning_depth": reasoning_decision.depth,
            "assumptions": ["External data assumed correct"] if verified else [],
            "limits": verification.get("gaps", []) if verification else [],
            "next_steps": []
        }

    # =========================
    # REFUSAL
    # =========================
    def _refusal_response(
        self,
        answer: str,
        reason: str,
        needed: list,
        why: str,
        reasoning_decision
    ) -> dict:
        return {
            "answer": answer,
            "status": "REFUSED",
            "confidence": "Low",
            "reasoning_depth": reasoning_decision.depth,
            "refusal": {
                "reason": reason,
                "needed": needed,
                "why_it_matters": why
            },
            "assumptions": [],
            "limits": needed,
            "next_steps": needed
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