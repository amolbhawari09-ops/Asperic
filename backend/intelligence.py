import os
import re
from tavily import TavilyClient
from groq import Groq


class IntelligenceCore:
    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        if not self.tavily_api_key or not self.groq_api_key:
            raise EnvironmentError(
                "CRITICAL: Search or Inference API keys missing from Environment."
            )

        self.tavily = TavilyClient(api_key=self.tavily_api_key)
        self.client = Groq(api_key=self.groq_api_key)

        self.SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"
        self.MAVERICK = "meta-llama/llama-4-maverick-17b-128e-instruct"

    def live_research(self, query):
        print(f"SCANNING DATA SOURCES: {query}")
        try:
            search_result = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_raw_content=True
            )

            raw_context = "\n".join(r["content"] for r in search_result["results"])
            facts = self._extract_facts(raw_context)
            return self._sanitize_context(facts)

        except Exception as e:
            print(f"Research failure: {e}")
            return "ERROR_DATA_RECON_FAILED"

    def _extract_facts(self, raw_data):
        system_msg = (
            "Extract ONLY relevant technical facts, dates, and numbers. "
            "Ignore ads, UI elements, and marketing text."
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.SCOUT,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": raw_data}
                ],
                temperature=0.0
            )
            return completion.choices[0].message.content.strip()

        except Exception as e:
            print(f"Fact extraction failed: {e}")
            return raw_data[:500]

    def _sanitize_context(self, text):
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED]', text)
        text = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[REDACTED]', text)
        text = re.sub(r'\b[a-fA-F0-9]{32,}\b', '[REDACTED]', text)
        return text.strip()

    def verify_facts(self, research_data):
        if not research_data or "ERROR" in research_data:
            return "INSUFFICIENT_VERIFIED_DATA"

        completion = self.client.chat.completions.create(
            model=self.MAVERICK,
            messages=[
                {"role": "system", "content": "Validate and summarize the facts."},
                {"role": "user", "content": research_data}
            ],
            temperature=0.0
        )

        return completion.choices[0].message.content.strip()