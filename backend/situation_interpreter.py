from dataclasses import dataclass
from typing import List, Dict


@dataclass(frozen=True)
class SituationDecision:
    """
    Immutable situation declaration passed to AstraBrain.
    """
    situation: str                     # LOW_STAKES | INFORMATIONAL | DECISION_SUPPORT | ACCOUNTABILITY_REQUIRED
    ruleset: str                       # relaxed | standard | strict
    verification_required: bool
    refusal_allowed: bool
    explanation_required: bool
    policy_version: str
    signals: List[str]


class SituationInterpreter:
    """
    Asperic Situation Interpreter
    ------------------------------
    Purpose:
    - Translate predictor signals into an explicit operating situation
    - Enforce policy-driven behavior (not intelligence)
    - Eliminate guessing inside AstraBrain
    """

    POLICY_VERSION = "v1.0-stable"

    # ---- Canonical Situations ----
    LOW_STAKES = "LOW_STAKES"
    INFORMATIONAL = "INFORMATIONAL"
    DECISION_SUPPORT = "DECISION_SUPPORT"
    ACCOUNTABILITY_REQUIRED = "ACCOUNTABILITY_REQUIRED"

    def __init__(self):
        """
        Policy rules are intentionally static and explicit.
        Any evolution must be versioned and deliberate.
        """

        # Mapping from situation → behavior contract
        self.SITUATION_RULES: Dict[str, Dict] = {
            self.LOW_STAKES: {
                "ruleset": "relaxed",
                "verification_required": False,
                "refusal_allowed": False,
                "explanation_required": False,
            },
            self.INFORMATIONAL: {
                "ruleset": "standard",
                "verification_required": False,
                "refusal_allowed": False,
                "explanation_required": True,
            },
            self.DECISION_SUPPORT: {
                "ruleset": "strict",
                "verification_required": True,
                "refusal_allowed": True,
                "explanation_required": True,
            },
            self.ACCOUNTABILITY_REQUIRED: {
                "ruleset": "strict",
                "verification_required": True,
                "refusal_allowed": True,
                "explanation_required": True,
            },
        }

    # =========================
    # PUBLIC ENTRY
    # =========================
    def interpret(self, predictor_output: Dict) -> SituationDecision:
        """
        Input: predictor_output (dict)
        Output: SituationDecision (immutable)

        predictor_output expected schema:
        {
            "route": str,
            "confidence": float,
            "signals": [str],
            "version": str
        }
        """

        route = predictor_output.get("route", self.INFORMATIONAL)
        signals = predictor_output.get("signals", [])
        confidence = predictor_output.get("confidence", 0.0)

        # ---- HARD POLICY OVERRIDES ----
        # Certain signals always escalate situation

        if "regulatory_context" in signals:
            route = self.ACCOUNTABILITY_REQUIRED

        if "user_accountability" in signals:
            route = self.ACCOUNTABILITY_REQUIRED

        if "decision_request" in signals and route == self.INFORMATIONAL:
            route = self.DECISION_SUPPORT

        # ---- CONFIDENCE GUARD ----
        # Low confidence → safer handling

        if confidence < 0.4 and route in {
            self.DECISION_SUPPORT,
            self.ACCOUNTABILITY_REQUIRED
        }:
            route = self.ACCOUNTABILITY_REQUIRED

        # ---- FINAL POLICY LOOKUP ----
        rules = self.SITUATION_RULES.get(route)

        if not rules:
            # Absolute fail-safe (should never happen)
            route = self.INFORMATIONAL
            rules = self.SITUATION_RULES[self.INFORMATIONAL]

        return SituationDecision(
            situation=route,
            ruleset=rules["ruleset"],
            verification_required=rules["verification_required"],
            refusal_allowed=rules["refusal_allowed"],
            explanation_required=rules["explanation_required"],
            policy_version=self.POLICY_VERSION,
            signals=signals
        )