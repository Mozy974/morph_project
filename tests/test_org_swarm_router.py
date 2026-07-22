"""
Tests unitaires pour OrgSwarmRouter (Level 8.0 Auto-Évolution Collective).
"""

import pytest
from orchestrator.agents.org_swarm_router import OrgSwarmRouter


def test_org_swarm_router_init():
    router = OrgSwarmRouter()
    assert router.nom == "Org Swarm Router"
    assert "ENGINEERING_GUILD" in router.GUILDS
