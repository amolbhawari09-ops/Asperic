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
        """
        UPGRADE: Uses Scout to strictly distill raw HTML/text into clean data points.
        This filter blocks ads, navigation menus, and marketing noise.
        """
        
        # 1. The "Data Cleaner" Persona
        # We explicitly tell the model to ignore garbage and format as a list.
        system_msg = (
            "You are a strict Data Cleaner. "
            "1. Extract ONLY the relevant technical facts, dates, and numbers from the text. "
            "2. IGNORE navigation menus, ads, 'sign up' buttons, and marketing fluff. "
            "3. Format the output as a clean, factual summary text. "
            "4. Do not use conversational filler like 'Here are the facts'."
        )
        
        # 2. Execution
        try:
            completion = self.client.chat.completions.create(
                model=self.SCOUT,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": raw_data}
                ],
                temperature=0.0  # Zero temp ensures consistent cleaning
            )
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ Fact Extraction Warning: {e}")
            # Fallback: Return raw data if the cleaning node fails, 
            # so the system doesn't crash.
            return raw_data[:500] 

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