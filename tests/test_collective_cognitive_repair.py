"""
Tests unitaires pour CollectiveCognitiveRepair (Level 12.0 Conscience Collective Ultime).
"""

import pytest
from orchestrator.agents.collective_cognitive_repair import CollectiveCognitiveRepair


def test_collective_cognitive_repair():
    repair = CollectiveCognitiveRepair()
    fleet_logs = {
        "Codeur": ["Certain que le code est parfait"],
        "Analyste": ["Étape 1", "Étape 2"]
    }
    res = repair.repair_swarm_biases(fleet_logs)
    assert res["total_biases_found"] == 2
    assert res["bias_reduction_score"] == 0.98

    assert res["fleet_corrections"]["Codeur"]["status"] == "DEBIASED"
