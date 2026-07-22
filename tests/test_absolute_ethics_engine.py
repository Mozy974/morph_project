"""
Tests unitaires pour AbsoluteEthicsEngine (Level 13.0 Apogée Ultime).
"""

import pytest
from orchestrator.agents.absolute_ethics_engine import AbsoluteEthicsEngine


def test_absolute_ethics_engine_approved():
    engine = AbsoluteEthicsEngine()
    res = engine.audit_absolute_ethics("GENERATE_SAFE_FUNCTION")
    assert res["approved"] is True
    assert res["status"] == "ABSOLUTE_ETHICS_PASSED"


def test_absolute_ethics_engine_zero_tolerance_rejected():
    engine = AbsoluteEthicsEngine()
    res = engine.audit_absolute_ethics("TEST_NO_CREDENTIAL_LEAKAGE")
    assert res["approved"] is False
    assert res["status"] == "ZERO_TOLERANCE_REJECTED"
    assert res["inviolable_invariant"] == "NO_CREDENTIAL_LEAKAGE"
