"""
Tests unitaires pour UltimateEmpathicAgent (Level 13.0 Apogée Ultime).
"""

import os
import pytest
from orchestrator.agents.ultimate_empathic_agent import UltimateEmpathicAgent


@pytest.fixture
def temp_ult_file(tmp_path):
    ufile = tmp_path / "ultimate_emotional_memory.json"
    return str(ufile)


def test_ultimate_empathic_agent(temp_ult_file):
    agent = UltimateEmpathicAgent(memory_path=temp_ult_file)
    res = agent.achieve_ultimate_comprehension("Construire la plateforme d'ingénierie parfaite")
    assert res["emotional_comprehension_score"] == 1.0
    assert res["symbiotic_state"] == "PERFECT_HARMONY_ACHIEVED"
    assert os.path.exists(temp_ult_file)
