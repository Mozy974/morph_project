"""
Tests unitaires pour FleetEthicsConsensus (Level 12.0 Conscience Collective Ultime).
"""

import pytest
from orchestrator.agents.fleet_ethics_consensus import FleetEthicsConsensus


def test_fleet_ethics_consensus_approved():
    engine = FleetEthicsConsensus()
    reports = [
        {"agent_name": "AgentCodeur", "flagged_invariant": None},
        {"agent_name": "AgentSecurity", "flagged_invariant": None}
    ]
    res = engine.evaluate_fleet_consensus(reports)
    assert res["consensus_approved"] is True
    assert res["veto_applied"] is False


def test_fleet_ethics_unilateral_veto():
    engine = FleetEthicsConsensus()
    reports = [
        {"agent_name": "AgentCodeur", "flagged_invariant": None},
        {"agent_name": "AgentSecurity", "flagged_invariant": "NO_CREDENTIAL_LEAKAGE"}
    ]
    res = engine.evaluate_fleet_consensus(reports)
    assert res["consensus_approved"] is False
    assert res["veto_applied"] is True
    assert res["veto_by"] == "AgentSecurity"
    assert res["flagged_invariant"] == "NO_CREDENTIAL_LEAKAGE"
