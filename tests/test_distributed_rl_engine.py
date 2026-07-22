"""
Tests unitaires pour DistributedRLEngine (Level 9.0 Conscience Collective).
"""

import pytest
from orchestrator.agents.distributed_rl_engine import DistributedRLEngine


def test_distributed_rl_engine_reward_calculation():
    engine = DistributedRLEngine(weight_tdd=0.8, weight_speed=0.2)

    # 1. Parfait : TDD pass au 1er coup + rapide
    res_perfect = engine.calculate_reward_score(tdd_passed=True, attempts=1, duration_sec=5.0)
    assert res_perfect["reward_score"] == 1.0

    # 2. Échec TDD : TDD score = 0.0
    res_fail = engine.calculate_reward_score(tdd_passed=False, attempts=3, duration_sec=10.0)
    assert res_fail["reward_score"] < 0.3
