"""
Tests unitaires pour TeamCoordinatorAgent (Level 7.0 Meta-Learning).
"""

import pytest
from orchestrator.agents.team_coordinator import TeamCoordinatorAgent


def test_team_coordinator_init():
    coordinator = TeamCoordinatorAgent()
    assert coordinator.nom == "Team Coordinator"
