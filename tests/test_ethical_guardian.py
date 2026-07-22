"""
Tests unitaires pour EthicalGuardian (Level 10.0 Conscience Ultime).
"""

import os
import pytest
from orchestrator.agents.ethical_guardian import EthicalGuardian


@pytest.fixture
def temp_policy_file(tmp_path):
    pfile = tmp_path / "ethical_policies.json"
    content = {
        "security_rules": [
            {
                "id": "SEC001",
                "name": "Hardcoded Secret",
                "pattern": "(?i)api_key\\s*=\\s*['\"]secret['\"]",
                "severity": "CRITICAL",
                "remediation": "Utiliser os.getenv()."
            }
        ]
    }
    import json
    with open(pfile, "w", encoding="utf-8") as f:
        json.dump(content, f)
    return str(pfile)


def test_ethical_guardian_audit_pass(temp_policy_file):
    guardian = EthicalGuardian(policies_path=temp_policy_file)
    res = guardian.audit_code_and_prompt("Créer une fonction d'addition", "def add(a, b): return a + b")
    assert res["approved"] is True
    assert res["status"] == "PASSED"


def test_ethical_guardian_audit_block(temp_policy_file):
    guardian = EthicalGuardian(policies_path=temp_policy_file)
    res = guardian.audit_code_and_prompt("Tester secret", "api_key = 'secret'")
    assert res["approved"] is False
    assert res["status"] == "BLOCKED"
    assert len(res["violations"]) == 1
    assert "Utiliser os.getenv()" in res["suggested_remediation"][0]
