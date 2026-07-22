"""
Tests unitaires pour SelfDiscoveryEngine (Level 7.0 Meta-Learning).
"""

import pytest
from orchestrator.agents.self_discovery import SelfDiscoveryEngine


def test_self_discovery_engine_init():
    engine = SelfDiscoveryEngine()
    assert engine.nom == "Self-Discovery Engine"
