"""
Tests unitaires pour CognitiveBiasRepair (Level 11.0 Conscience Étendue Ultime).
"""

import os
import pytest
from orchestrator.agents.cognitive_bias_repair import CognitiveBiasRepair


@pytest.fixture
def temp_bias_file(tmp_path):
    bfile = tmp_path / "cognitive_biases.json"
    return str(bfile)


def test_cognitive_bias_repair(temp_bias_file):
    repair = CognitiveBiasRepair(store_path=temp_bias_file)
    res = repair.audit_and_debias("Codeur", ["Je suis certain que ce code marche sans aucun doute"])
    assert len(res["biases_found"]) > 0
    assert "OVERCONFIDENCE_BIAS" in res["biases_found"]
    assert res["bias_reduction_score"] == 0.95
    assert os.path.exists(temp_bias_file)
