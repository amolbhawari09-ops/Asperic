import os
import json
from groq import Groq

class Predictor:
    def __init__(self):
        # 1. INFRASTRUCTURE & SECURITY
        # Mandatory environment variable usage; hardcoded keys are a tier-1 violation.
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise EnvironmentError("CRITICAL: GROQ_API_KEY not found in environment.")
            
        self.client = Groq(api_key=self.api_key)
        self.SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"
        
        # DETERMINISTIC ROUTING TABLE
        # We use numeric codes to ensure the LLM cannot 'hallucinate' a mode name.
        self.INTENT_MAP = {
            1: "FAST_MODE",      # Simple queries/greetings
            2: "RESEARCH_MODE",  # Web-grounded synthesis
            3: "PROJECT_MODE",   # Local context/Code analysis
            4: "REFLECT_MODE"    # Multi-pass logic audit
        }

    def predict(self, text):
        """
        DETERMINISTIC INTENT PIPELINE:
        1. Hard-coded Sovereignty Gate (PII/Security)
        2. Numeric Classification (Non-Prose)
        3. Returns Code + Confidence
        """
        # --- PHASE 1: HARD-CODED SOVEREIGNTY GATE ---
        # Immediate local routing for PII safety without LLM latency.
        if "[SENSITIVE" in text or "[DATA_MASK]" in text:
            return "PROJECT_MODE", 1.0

        # --- PHASE 2: NUMERIC CLASSIFICATION ---
        # Scout acts as a logic gate, returning ONLY a code.
        analysis = self._get_numeric_intent(text)
        
        # Map the numeric code back to a system mode
        intent_code = analysis.get("code", 1)
        mode = self.INTENT_MAP.get(intent_code, "FAST_MODE")
        confidence = analysis.get("conf", 0.0)

        print(f"🧭 ROUTER SIGNAL: Code {intent_code} -> {mode} ({confidence})")
        return mode, confidence

    def _get_numeric_intent(self, text):
        """
        Forces the LLM to behave like a piece of hardware (returning bits/codes).
        User never sees this; it is a hidden system logic step.
        """
        # Strictly constrained system prompt to prevent 'talking'.
        system_msg = (
            "Classify intent into a numeric code: "
            "1:General, 2:WebSearch, 3:LocalData, 4:DeepLogic. "
            "Return ONLY JSON: {'code': int, 'conf': float}"
        )
        
        try:
            completion = self.client.chat.completions.create(
                model=self.SCOUT,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": text}
                ],
                temperature=0.0, # Mathematical precision
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            # Failure results in a safe fallback (Fast Mode).
            print(f"⚠️ Prediction Node Failure: {e}")
            return {"code": 1, "conf": 0.0}