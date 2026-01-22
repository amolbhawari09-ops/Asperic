import json
from model_loader import groq_client  # ✅ shared Groq singleton


class Predictor:
    def __init__(self):
        # Model used for intent classification
        self.SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"

        # Deterministic routing table
        self.INTENT_MAP = {
            1: "FAST_MODE",      # Simple queries / greetings
            2: "RESEARCH_MODE",  # Web-grounded synthesis
            3: "PROJECT_MODE",   # Local context / code analysis
            4: "REFLECT_MODE"    # Multi-pass logic audit
        }

    def predict(self, text):
        """
        DETERMINISTIC INTENT PIPELINE:
        1. Hard-coded Sovereignty Gate (PII/Security)
        2. Numeric Classification (Non-Prose)
        3. Returns (mode, confidence)
        """
        # --- PHASE 1: HARD SAFETY GATE ---
        if "[SENSITIVE" in text or "[DATA_MASK]" in text:
            return "PROJECT_MODE", 1.0

        # --- PHASE 2: NUMERIC CLASSIFICATION ---
        analysis = self._get_numeric_intent(text)

        intent_code = analysis.get("code", 1)
        mode = self.INTENT_MAP.get(intent_code, "FAST_MODE")
        confidence = analysis.get("conf", 0.0)

        print(f"🧭 ROUTER SIGNAL: Code {intent_code} -> {mode} ({confidence})")
        return mode, confidence

    def _get_numeric_intent(self, text):
        """
        Forces the LLM to return ONLY numeric intent classification.
        """
        system_msg = (
            "Classify intent into a numeric code. "
            "1:General, 2:WebSearch, 3:LocalData, 4:DeepLogic. "
            "Return ONLY JSON: {'code': int, 'conf': float}"
        )

        try:
            completion = groq_client.chat.completions.create(
                model=self.SCOUT,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": text}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            print(f"⚠️ Prediction Node Failure: {e}")
            return {"code": 1, "conf": 0.0}
