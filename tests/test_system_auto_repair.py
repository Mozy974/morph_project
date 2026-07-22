"""
Tests unitaires pour SystemAutoRepair (Level 9.0 Conscience Collective).
"""

import pytest
from orchestrator.agents.system_auto_repair import SystemAutoRepair


def test_system_auto_repair_safe_action():
    repair = SystemAutoRepair()
    res = repair.evaluate_and_repair("REDIS_RECONNECT", {})
    assert res["status"] == "AUTONOMOUSLY_RESOLVED"
    assert res["requires_hitl"] is False


def test_system_auto_repair_critical_action():
    repair = SystemAutoRepair()
    res = repair.evaluate_and_repair("POSTGRES_SCHEMA_MIGRATION", {})
    assert res["status"] == "PENDING_HITL"
    assert res["requires_hitl"] is True
