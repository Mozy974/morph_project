"""
Tests unitaires pour TokenBudgetController (Level 8.0 Auto-Évolution Collective).
"""

import pytest
from orchestrator.memory.token_budget_controller import TokenBudgetController, TokenBudgetExceededError


def test_token_budget_controller_ok():
    controller = TokenBudgetController(max_calls_per_job=5, max_tokens_per_job=10000)
    res = controller.check_and_consume("job_test", guild="ENGINEERING_GUILD", estimated_tokens=1000)
    assert res is True
    stats = controller.get_job_stats("job_test")
    assert stats["consumed_calls"] == 1
    assert stats["consumed_tokens"] == 1000
    assert stats["guild_calls"]["ENGINEERING_GUILD"] == 1


def test_token_budget_controller_exceeded_calls():
    controller = TokenBudgetController(max_calls_per_job=2, max_tokens_per_job=10000)
    controller.check_and_consume("job_test_2", estimated_tokens=100)
    controller.check_and_consume("job_test_2", estimated_tokens=100)

    with pytest.raises(TokenBudgetExceededError):
        controller.check_and_consume("job_test_2", estimated_tokens=100)
