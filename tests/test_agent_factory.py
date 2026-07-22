"""
Tests unitaires pour AgentFactory et DynamicAgent (Level 6.0 Auto-Évolution).
"""

import os
import pytest
from orchestrator.agents.agent_factory import AgentFactory, DynamicAgent


@pytest.fixture
def temp_registry(tmp_path):
    reg_file = tmp_path / "test_registry.json"
    return str(reg_file)


def test_agent_factory_instantiation(temp_registry):
    factory = AgentFactory(registry_path=temp_registry)
    assert factory.registry == {}


def test_dynamic_agent_execution():
    agent = DynamicAgent(
        name="TestAgent",
        role="Test Role",
        system_prompt="Tu es un agent de test.",
        domain="testing"
    )
    assert agent.nom == "TestAgent"
    assert agent.domain == "testing"
