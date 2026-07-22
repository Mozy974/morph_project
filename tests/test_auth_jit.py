"""
Tests unitaires pour la gestion des jetons éphémères JIT et la détection d'accès suspects (tests/test_auth_jit.py).
"""

import pytest
import time
from orchestrator.auth import generate_ephemeral_token, verify_ephemeral_token


def test_ephemeral_token_valid():
    token = generate_ephemeral_token("user_dev_01", role="operator", ttl_seconds=60)
    res = verify_ephemeral_token(token)
    assert res["valid"] is True
    assert res["payload"]["sub"] == "user_dev_01"
    assert res["payload"]["role"] == "operator"


def test_ephemeral_token_expired():
    token = generate_ephemeral_token("user_dev_02", role="operator", ttl_seconds=-10)
    res = verify_ephemeral_token(token)
    assert res["valid"] is False
    assert "expiré" in res["reason"]


def test_ephemeral_token_tampered():
    token = generate_ephemeral_token("user_dev_03", role="operator", ttl_seconds=60)
    tampered_token = token[:-5] + "XXXXX"
    res = verify_ephemeral_token(tampered_token)
    assert res["valid"] is False
    assert "invalide" in res["reason"] or "malformé" in res["reason"]
