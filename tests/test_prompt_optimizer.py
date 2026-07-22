"""
Tests unitaires pour PromptOptimizerAgent (Level 6.0 Auto-Évolution).
"""

import os
import json
import pytest
from orchestrator.agents.prompt_optimizer import PromptOptimizerAgent


@pytest.fixture
def temp_store(tmp_path):
    store_file = tmp_path / "test_prompts.json"
    return str(store_file)


def test_prompt_optimizer_no_failures(temp_store):
    optimizer = PromptOptimizerAgent(store_path=temp_store)
    res = optimizer.optimize_prompt(
        agent_name="TestAgent",
        current_prompt="Initial prompt",
        execution_failures=[]
    )
    assert res["mutation_applied"] is False
    assert res["optimized_prompt"] == "Initial prompt"


def test_prompt_optimizer_fallback_get_active_prompt(temp_store):
    optimizer = PromptOptimizerAgent(store_path=temp_store)
    active = optimizer.get_active_prompt("UnknownAgent", "Default Prompt")
    assert active == "Default Prompt"
