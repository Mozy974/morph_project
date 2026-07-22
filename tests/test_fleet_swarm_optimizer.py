"""
Tests unitaires pour FleetSwarmOptimizer (Level 8.0 Auto-Évolution Collective).
"""

import pytest
from orchestrator.agents.fleet_swarm_optimizer import FleetSwarmOptimizer


def test_fleet_swarm_optimizer():
    optimizer = FleetSwarmOptimizer()
    res = optimizer.optimize_fleet_telemetry({"active_jobs": 12, "error_rate": 0.02})
    assert res["strategy"] == "HIGH_THROUGHPUT"
    assert res["recommended_concurrency"] == 8

    res_err = optimizer.optimize_fleet_telemetry({"active_jobs": 2, "error_rate": 0.25})
    assert res_err["strategy"] == "HIGH_PRECISION"
    assert res_err["model_tier"] == "PREMIUM"
