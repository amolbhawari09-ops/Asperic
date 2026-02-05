"""
Asperic Semantic Anchors (v1.0)
------------------------------
This file defines canonical meaning references used by the SemanticEngine.

RULES:
- Anchors describe MEANING, not keywords
- Anchors are short, natural phrases
- No logic, no embeddings, no imports
"""

ANCHORS = {
    # ---------------------------------
    # USER CONFUSION / OVERLOAD
    # ---------------------------------
    "confusion": [
        "I don't understand this",
        "this is too complicated",
        "this is too technical",
        "I'm confused",
        "I'm lost",
        "this doesn't make sense to me",
        "can you explain this simply"
    ],

    # ---------------------------------
    # DECISION / CHOICE INTENT
    # ---------------------------------
    "decision_intent": [
        "should I do this",
        "what should I choose",
        "is this a good idea",
        "which option is better",
        "should I use this",
        "should I avoid this"
    ],

    # ---------------------------------
    # TECHNICAL / ENGINEERING CONTENT
    # ---------------------------------
    "technicality": [
        "system architecture",
        "machine learning model",
        "neural network embeddings",
        "deployment pipeline",
        "distributed system",
        "backend infrastructure",
        "API design",
        "database schema"
    ],

    # ---------------------------------
    # LEARNING / EXPLORATION
    # ---------------------------------
    "learning_intent": [
        "explain how this works",
        "I want to learn this",
        "teach me this concept",
        "how does this work internally",
        "break this down for me"
    ]
}

VERSION = "v1.0"