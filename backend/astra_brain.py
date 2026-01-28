import os
import datetime
import re
from groq import Groq
from intelligence import IntelligenceCore

class AstraBrain:
    def __init__(self, memory_shared=None):
        # 1. INFRASTRUCTURE & SECURITY
        # Mandatory environment variable usage; hardcoded keys are strictly prohibited.
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise EnvironmentError("CRITICAL: GROQ_API_KEY not found. System terminated.")
            
        self.client = Groq(api_key=self.api_key)
        self.MAVERICK = "meta-llama/llama-4-maverick-17b-128e-instruct"
        self.SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"
        
        # Core Intelligence & Retrieval Layers
        self.intel = IntelligenceCore()
        # DEPENDENCY INJECTION: Use shared memory if provided, else create own
        self.memory = memory_shared

    def chat(self, user_question, history=None, mode="FAST_MODE"):
        """
        DETERMINISTIC PIPELINE:
        Returns RAW BODY ONLY. Structural authority belongs to main.py.
        """
        # Fix for mutable default argument to prevent data bleeding between sessions.
        history = history or [] 
        
        # 1. LOW-COMPLEXITY ROUTING (Cost and latency optimization)
        if self._is_simple_query(user_question):
            raw_out = self._run_inference(user_question, "Provide a brief professional response.", self.SCOUT)
            return self.security_scrub(raw_out)  # RAW BODY ONLY

        # 2. CONTEXTUAL GROUNDING
        context_data = self._gather_context(user_question, mode)
        
        # 3. THE MAVERICK REASONING LAYER (Logic-Only Generation)
        # We strip personality from the prompt to ensure mathematical precision.
        raw_body = self._generate_logic(user_question, context_data, history)
        
        # 4. RETURN RAW BODY ONLY (No envelope here - main.py handles structure)
        return self.security_scrub(raw_body)

    def _is_simple_query(self, text):
        """Identifies conversational fillers to bypass high-level reasoning."""
        simple_triggers = {"hi", "hello", "thanks", "who are you", "hey"}
        return any(word in text.lower() for word in simple_triggers) and len(text.split()) < 5

            def _generate_logic(self, q, context, hist, mode="RESEARCH_MODE"):
        """
        UPGRADE: Dynamically switches 'Persona' based on the Mode.
        This ensures code looks like code, and chat looks like chat.
        """
        
        # 1. Default Persona (The Professional)
        system_role = (
            "You are a Senior Technical Consultant. "
            "Synthesize the context into clear, professional English. "
            "Focus on accuracy and readability."
        )

        # 2. Persona Switchboard
        if mode == "PROJECT_MODE": 
            # Needs to be a coder, not a consultant
            system_role = (
                "You are a Senior Software Architect. "
                "Analyze the code context. Provide specific, secure, and optimized code solutions. "
                "Explain your logic briefly, then provide the code block."
            )
        
        elif mode == "FAST_MODE":
            # Needs to be concise
            system_role = (
                "You are a helpful and efficient assistant. "
                "Answer directly and briefly. Do not use filler words."
            )

        elif "JSON" in q.upper() or "CODE" in q.upper():
             # Strict format override
             system_role += " OUTPUT RESTRICTION: Provide ONLY the requested code/JSON. No conversational filler."

        # 3. The Execution
        user_msg = (
            f"--- BEGIN CONTEXT ---\n{context}\n--- END CONTEXT ---\n\n"
            f"USER QUESTION: {q}"
        )
        
        return self._run_inference(user_msg, system_role, self.MAVERICK)


    def security_scrub(self, text):
        """Deterministic data redaction to prevent accidental PII leakage."""
        # Redact Sensitive Patterns (Emails, IPs, API Keys)
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[SENSITIVE_DATA]', text)
        text = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[SENSITIVE_DATA]', text)
        text = re.sub(r'\b[a-fA-F0-9]{32,}\b', '[SENSITIVE_DATA]', text)
        
        # Character Normalization: Removes LLM formatting artifacts.
        text = text.replace("**", "").replace("***", "")
        return text.strip()

    def assemble_output(self, body, mode):
        """
        THE PROFESSIONAL ENVELOPE (Mandatory Structure).
        This ensures answers are direct and respect the user's time.
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        header = f"ASPERIC RESPONSE | NODE: {mode} | TIME: {timestamp}\n" + ("=" * 45)
        footer = ("=" * 45) + "\n— Action required / Ready for instruction"
        
        return f"{header}\n\n{body}\n\n{footer}"

    def _run_inference(self, prompt, system_msg, model):
        """Standardized low-level execution layer with zero-temperature."""
        completion = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0 # Guaranteed repeatability for professional results.
        )
        return completion.choices[0].message.content.strip()

    def _gather_context(self, query, mode):
        if mode == "PROJECT_MODE": return self.memory.search(query)
        if mode == "RESEARCH_MODE": return self.intel.verify_facts(self.intel.live_research(query))
        return "N/A"