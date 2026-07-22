"""
Tests unitaires pour MetaConsciousnessAgent (Level 10.0 Conscience Ultime).
"""

import pytest
from orchestrator.agents.meta_consciousness import MetaConsciousnessAgent


def test_meta_consciousness_init():
    agent = MetaConsciousnessAgent()
    assert agent.nom == "Meta-Consciousness Agent"
