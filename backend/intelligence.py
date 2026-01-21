import os
import re
from tavily import TavilyClient
from groq import Groq

class IntelligenceCore:
    def __init__(self):
        # 1. INFRASTRUCTURE: KEY MANAGEMENT
        # Professional standard: No hardcoded fallbacks. Keys must reside in Environment.
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        if not self.tavily_api_key or not self.groq_api_key:
            raise EnvironmentError("CRITICAL: Search or Inference API keys missing from Environment.")

        self.tavily = TavilyClient(api_key=self.tavily_api_key)
        self.client = Groq(api_key=self.groq_api_key)
        
        # Llama 4 Model Routing
        self.SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"
        self.MAVERICK = "meta-llama/llama-4-maverick-17b-128e-instruct"

    def live_research(self, query):
        """
        Gathers multi-source web data and performs deterministic sanitization.
        """
        print(f"📡 SCANNING DATA SOURCES: '{query}'...")
        try:
            # Advanced search depth for high-fidelity grounding
            search_result = self.tavily.search(
                query=query, 
                search_depth="advanced", 
                max_results=5,
                include_raw_content=True 
            )
            
            # Extract content snippets
            raw_context = "\n".join([r['content'] for r in search_result['results']])
            
            # Layer 1: Extract technical facts only (Noise Reduction)
            factual_payload = self._extract_facts(raw_context)
            
            # Layer 2: Deterministic Data Scrubbing (Security)
            return self._sanitize_context(factual_payload)
            
        except Exception as e:
            print(f"⚠️ Research Link Failure: {e}")
            return "ERROR_DATA_RECON_FAILED"

    def _extract_facts(self, raw_data):
        """Uses Scout to distill raw HTML/text into clean data points."""
        # NO instructions about tone or articles. Only the task.
        completion = self.client.chat.completions.create(
            model=self.SCOUT,
            messages=[
                {"role": "system", "content": "Distill the provided text into a technical list of facts. Remove marketing language."},
                {"role": "user", "content": raw_data}
            ],
            temperature=0.0 # Mathematical consistency
        )
        return completion.choices[0].message.content.strip()

    def _sanitize_context(self, text):
        """
        Deterministic Masking: Prevents external data from leaking internal patterns.
        Uses Regex to ensure zero hallucinations of security.
        """
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_ENTITY]', text)
        text = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[REDACTED_ENTITY]', text)
        text = re.sub(r'\b[a-fA-F0-9]{32,}\b', '[REDACTED_ENTITY]', text)
        return text

    def verify_facts(self, research_data):
        """
        Maverick-level validation of data integrity.
        """
        if not research_data or "ERROR" in research_data:
            return "SIGNAL_INSUFFICIENT: Technical verification failed due to lack of source data."

        print("⚖️ DATA VALIDATION: Executing logical audit...")
        
        # Shifted from "Auditor" persona to "Logic Processor"
        # This prevents the model from explaining its own existence.
        validation_prompt = (
            "Analyze the data for technical contradictions. "
            "Return a clean, factual summary. Do not use formatting symbols."
        )
        
        completion = self.client.chat.completions.create(
            model=self.MAVERICK,
            messages=[
                {"role": "system", "content": validation_prompt},
                {"role": "user", "content": f"DATA: {research_data}"}
            ],
            temperature=0.0
        )
        
        return completion.choices[0].message.content.strip()