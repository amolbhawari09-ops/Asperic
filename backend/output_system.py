
import re

class OutputSystem:
    def __init__(self):
        self.HEADERS = {
            "PURPOSE": ["why", "what is", "who is", "define"],
            "SUMMARY": ["how", "explain", "summarize", "tl;dr"],
            "ANALYSIS": ["analyze", "compare", "review", "assess", "critique"],
            "DECISION": ["should i", "recommend", "pick", "choose"],
            "EXECUTION PLAN": ["plan", "steps", "guide", "tutorial", "walkthrough"],
            "ASSESSMENT": ["diagnosis", "debug", "fix"]
        }
        
        self.FOOTERS = {
            "default": "— Ready for next instruction",
            "analysis": "— End of analysis",
            "decision": "— Execution complete",
            "plan": "— Ready to execute"
        }
        
    def route_intent(self, user_query):
        """
        Determines the Intent, Header, and Complexity based on user input.
        Returns: dict
        """
        q = user_query.lower().strip()
        
        # 1. Determine Header
        header = "PURPOSE" # Default
        for key, keywords in self.HEADERS.items():
            if any(k in q for k in keywords):
                header = key
                break
                
        # 2. Determine Complexity
        # Simple heuristic: Question length and trigger words
        complexity = "low"
        if len(q.split()) > 10 or any(w in q for w in ["detailed", "deep", "comprehensive", "full"]):
             complexity = "high"
        elif any(w in q for w in ["quick", "short", "brief"]):
             complexity = "low"
        elif header in ["ANALYSIS", "EXECUTION PLAN"]:
             complexity = "medium"
             
        # Override for specific types
        if header == "DECISION": complexity = "medium"
             
        return {
            "intent": header.lower(),
            "header": header,
            "complexity": complexity
        }

    def assemble_final_output(self, body_content, router_data):
        """
        Wraps the raw model body with Header, Footer, and Hook.
        """
        header = router_data["header"]
        complexity = router_data["complexity"]
        
        # Clean Body (Step 9: Remove old patterns)
        clean_body = self._clean_patterns(body_content)
        
        # Select Footer
        footer = self.FOOTERS.get("default")
        if header == "ANALYSIS": footer = self.FOOTERS["analysis"]
        if header == "EXECUTION PLAN": footer = self.FOOTERS["plan"]
        
        # Select Feedback Hook
        hook = ""
        if complexity != "low":
            if header == "ANALYSIS": hook = "Proceed deeper or change scope."
            elif header == "EXECUTION PLAN": hook = "Refine or apply."
            elif header == "SUMMARY": hook = "Refine or apply."
            else: hook = "Proceed deeper."
            
        # Assembly
        final_output = f"{header}\n\n{clean_body}\n\n{footer}"
        if hook:
            final_output += f"\n{hook}"
            
        return final_output

    def _clean_patterns(self, text):
        """Removes banned conversational fillers."""
        patterns = [
            r"I am", r"As an AI", r"This response", r"According to", 
            r"Why it works", r"Risks", r"Next action"
        ]
        for p in patterns:
            text = re.sub(p, "", text, flags=re.IGNORECASE)
        return text.strip()
