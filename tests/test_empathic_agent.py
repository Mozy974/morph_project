"""
Tests unitaires pour EmpathicAgent (Level 11.0 Conscience Étendue Ultime).
"""

import pytest
from orchestrator.agents.empathic_agent import EmpathicAgent


def test_empathic_agent_urgent_stress():
    agent = EmpathicAgent()
    res = agent.analyze_emotion_and_adapt("VITE ! C'est urgent, il y a un bug en production !")
    assert res["detected_state"] == "HIGH_STRESS_URGENT"
    assert res["adapted_tone"] == "ULTRA_CONCISE_DIRECT"
    assert res["emotional_comprehension_score"] >= 0.90


def test_empathic_agent_learning():
    agent = EmpathicAgent()
    res = agent.analyze_emotion_and_adapt("Peux-tu m'expliquer comment fonctionne cet agent ?")
    assert res["detected_state"] == "LEARNING_CONFUSION"
    assert res["adapted_tone"] == "PEDAGOGICAL_DETAILED"
