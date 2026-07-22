"""
Tests unitaires pour MetaLearnerAgent (Level 7.0 Meta-Learning).
"""

import pytest
from orchestrator.agents.meta_learner import MetaLearnerAgent


@pytest.fixture
def temp_meta_store(tmp_path):
    store_file = tmp_path / "test_meta_learning.json"
    return str(store_file)


def test_meta_learner_no_logs(temp_meta_store):
    agent = MetaLearnerAgent(store_path=temp_meta_store)
    res = agent.analyze_fleet_performance([])
    assert res["status"] == "NO_DATA"


def test_meta_learner_initialization(temp_meta_store):
    agent = MetaLearnerAgent(store_path=temp_meta_store)
    assert agent.nom == "Meta-Learner Omega"
