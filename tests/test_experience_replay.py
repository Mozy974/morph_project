"""
Tests unitaires pour ExperienceReplayStore (Level 6.0 Auto-Évolution).
"""

import os
import pytest
from orchestrator.memory.experience_replay import ExperienceReplayStore


@pytest.fixture
def temp_exp_store(tmp_path):
    store_file = tmp_path / "test_experience.json"
    return str(store_file)


def test_experience_replay_record_and_search(temp_exp_store):
    store = ExperienceReplayStore(store_path=temp_exp_store)

    store.record_experience(
        error_traceback="KeyError: 'user_id'",
        failing_code="data['user_id']",
        patch_applied="data.get('user_id')",
        resolved=True,
        keywords=["KeyError"]
    )

    assert len(store.experiences) == 1

    similar = store.find_similar_experiences("KeyError: missing key in dictionary")
    assert len(similar) == 1
    assert similar[0]["patch_applied"] == "data.get('user_id')"

    few_shot = store.get_few_shot_prompt_context("KeyError: 'user_id'")
    assert "FEW-SHOT REPLAY" in few_shot
    assert "data.get('user_id')" in few_shot
