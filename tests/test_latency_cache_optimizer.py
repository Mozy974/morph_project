"""
Tests unitaires pour LatencyCacheOptimizer (Level 10.0 Conscience Ultime).
"""

import os
import pytest
from orchestrator.agents.latency_cache_optimizer import LatencyCacheOptimizer


@pytest.fixture
def temp_cache_file(tmp_path):
    cfile = tmp_path / "latency_cache.json"
    return str(cfile)


def test_latency_cache_store_and_get(temp_cache_file):
    optimizer = LatencyCacheOptimizer(cache_path=temp_cache_file)
    prompt = "Combien font 2 + 2 ?"
    response = "4"

    assert optimizer.get_cached_response(prompt) is None

    optimizer.store_cached_response(prompt, response)
    cached = optimizer.get_cached_response(prompt)
    assert cached == "4"
