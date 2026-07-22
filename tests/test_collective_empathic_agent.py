"""
Tests unitaires pour CollectiveEmpathicAgent (Level 12.0 Conscience Collective Ultime).
"""

import os
import pytest
from orchestrator.agents.collective_empathic_agent import CollectiveEmpathicAgent


@pytest.fixture
def temp_emo_file(tmp_path):
    efile = tmp_path / "collective_emotional_memory.json"
    return str(efile)


def test_collective_empathic_agent_majority_vote(temp_emo_file):
    agent = CollectiveEmpathicAgent(memory_path=temp_emo_file)
    votes = ["OPTIMAL_COLLABORATIVE", "OPTIMAL_COLLABORATIVE", "HIGH_STRESS"]
    res = agent.run_emotional_vote(votes)

    assert res["winning_mood"] == "OPTIMAL_COLLABORATIVE"
    assert res["qualified_majority_reached"] is True
    assert res["comprehension_score"] == 0.96
    assert os.path.exists(temp_emo_file)
