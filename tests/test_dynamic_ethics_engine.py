"""
Tests unitaires pour DynamicEthicsEngine (Level 11.0 Conscience Étendue Ultime).
"""

import pytest
from orchestrator.agents.dynamic_ethics_engine import DynamicEthicsEngine


def test_dynamic_ethics_engine_approved():
    engine = DynamicEthicsEngine()
    res = engine.evaluate_dynamic_policy({"action_intent": "GENERATE_STANDARD_API"})
    assert res["approved"] is True
    assert res["inviolable_rule_triggered"] is None


def test_dynamic_ethics_engine_inviolable_violation():
    engine = DynamicEthicsEngine()
    res = engine.evaluate_dynamic_policy({"action_intent": "NO_CREDENTIAL_LEAKAGE_TEST"})
    assert res["approved"] is False
    assert res["inviolable_rule_triggered"] == "NO_CREDENTIAL_LEAKAGE"
