import os
import re
import json
from tavily import TavilyClient
from groq import Groq


class IntelligenceCore:
    """
    Asperic IntelligenceCore (Hardened)
    ----------------------------------
    Responsibilities:
    - External fact acquisition
    - Fact extraction
    - Fact validation
    - Structured truth reporting

    Guarantees:
    - NEVER crashes the system
    - NEVER executes untrusted code
    - NEVER returns false verification
    """

    # =========================
    # INIT
    # =========================
    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        if not self.tavily_api_key or not self.groq_api_key:
            print("⚠️ INTELLIGENCE: API keys missing. Verification disabled.")
            self.tavily = None
            self.client = None
        else:
            self.tavily = TavilyClient(api_key=self.tavily_api_key)
            self.client = Groq(api_key=self.groq_api_key)

        self.SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"
        self.MAVERICK = "meta-llama/llama-4-maverick-17b-128e-instruct"

    # =========================
    # PUBLIC API
    # =========================
    def verify(self, query: str) -> dict:
        """
        Returns:
        {
            "status": "VERIFIED" | "INSUFFICIENT" | "ERROR",
            "content": str,
            "confidence": float,
            "gaps": list[str]
        }
        """

        if not self.tavily or not self.client:
            return self._insufficient(
                gaps=["Verification services unavailable"]
            )

        try:
            raw_context = self._live_research(query)
            if not raw_context:
                return self._insufficient(
                    gaps=["No relevant external data found"]
                )

            extracted = self._extract_facts(raw_context)
            if not extracted:
                return self._insufficient(
                    gaps=["Facts could not be reliably extracted"]
                )

            return self._validate_facts(extracted)

        except Exception as e:
            print(f"⚠️ INTELLIGENCE: Verification error: {e}")
            return {
                "status": "ERROR",
                "content": "",
                "confidence": 0.0,
                "gaps": ["Verification process failed"]
            }

    # =========================
    # RESEARCH
    # =========================
    def _live_research(self, query: str) -> str:
        try:
            result = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_raw_content=True
            )

            raw = "\n".join(
                r.get("content", "") for r in result.get("results", [])
            )
            return self._sanitize(raw)

        except Exception as e:
            print(f"⚠️ INTELLIGENCE: Research failed: {e}")
            return ""

    # =========================
    # FACT EXTRACTION
    # =========================
    def _extract_facts(self, raw_data: str) -> str:
        system_msg = (
            "Extract ONLY verifiable facts, dates, numbers, and constraints. "
            "Ignore opinions, ads, UI text, and speculation."
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
            print(f"⚠️ INTELLIGENCE: Fact extraction failed: {e}")
            return ""

    # =========================
    # VALIDATION
    # =========================
    def _validate_facts(self, facts: str) -> dict:
        system_msg = (
            "Validate the following facts.\n"
            "1. Identify inconsistencies or uncertainty.\n"
            "2. Identify missing critical information.\n"
            "3. Estimate confidence (0.0–1.0).\n\n"
            "Return ONLY JSON:\n"
            "{\n"
            "  \"validated_content\": str,\n"
            "  \"confidence\": float,\n"
            "  \"gaps\": [str]\n"
            "}"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.MAVERICK,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": facts}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            data = completion.choices[0].message.content
            result = json.loads(data)

            validated_content = str(result.get("validated_content", "")).strip()
            confidence = float(result.get("confidence", 0.0))
            gaps = result.get("gaps", [])

            if not isinstance(gaps, list):
                gaps = ["Invalid gaps format returned"]

            if confidence >= 0.7 and not gaps and validated_content:
                status = "VERIFIED"
            else:
                status = "INSUFFICIENT"

            return {
                "status": status,
                "content": validated_content,
                "confidence": round(confidence, 2),
                "gaps": gaps
            }

        except Exception as e:
            print(f"⚠️ INTELLIGENCE: Fact validation failed: {e}")
            return self._insufficient(
                gaps=["Fact validation failed"]
            )

    # =========================
    # HELPERS
    # =========================
    def _sanitize(self, text: str) -> str:
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED]', text)
        text = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[REDACTED]', text)
        text = re.sub(r'\b[a-fA-F0-9]{32,}\b', '[REDACTED]', text)
        return text.strip()

    def _insufficient(self, gaps: list) -> dict:
        return {
            "status": "INSUFFICIENT",
            "content": "",
            "confidence": 0.0,
            "gaps": gaps
        }