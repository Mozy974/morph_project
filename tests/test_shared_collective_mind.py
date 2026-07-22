"""
Tests unitaires pour SharedCollectiveMind (Level 9.0 Conscience Collective).
"""

import os
import pytest
from orchestrator.agents.shared_collective_mind import SharedCollectiveMind


@pytest.fixture
def temp_mind_file(tmp_path):
    mfile = tmp_path / "collective_mind_state.json"
    return str(mfile)


def test_shared_collective_mind_update(temp_mind_file):
    mind = SharedCollectiveMind(store_path=temp_mind_file)
    res = mind.update_mind_state(
        focus="TDD Code Execution",
        belief_updates=["Strict typing PEP 484 is active"],
        context_data={"job_id": "test_job_9"}
    )
    assert res["collective_focus"] == "TDD Code Execution"
    assert "Strict typing PEP 484 is active" in res["active_beliefs"]
    assert os.path.exists(temp_mind_file)
